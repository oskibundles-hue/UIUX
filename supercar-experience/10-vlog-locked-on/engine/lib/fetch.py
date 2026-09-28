"""plan + fetch: from an edl.json to full-quality mezzanines, fetching only the bytes the cut uses.

plan  every source range the EDL touches (shots, dialog, audio_extra) + handles, merged per clip; each merged
      range -> a byte span from the saved moov (video from the sync sample before the in-point, audio with
      2 s of pre-roll); spans of one clip closer than 48 MB share a link. Keyframe-only shots (speed
      "keyframes": the timelapse) become a span whose download keeps only sync samples.
      -> DAY/fetch/fetchplan.json + DAY/fetch/request.json (one link per span, <=25 per call)
fetch spans download in parallel (one Range request per single-use link) into sparse files that hold the
      saved head + moov, so ffmpeg can seek them like the original. With a disk budget (plan --waves-gb, fetch
      --budget-gb) the spans come in waves: a download starts only when the disk can hold it next to the
      mezzanines still to be written, the next wave's links are asked for through links/NEED.json when the disk
      can take that wave, and a span's bytes are freed (hole punched) as soon as every cut that reads it is done.
      An audio-only span (plan --audio-only-vo) keeps only its audio samples on disk. A clip's cuts start as soon as its
      spans are in, longest first, one ffmpeg per core (-threads 1 decode, x264 threads=1): 4 cuts on
      4 cores beats 1 cut on 4 threads because HEVC 4K 10-bit decode does not scale well within one file.
Mezzanines (same as the approved v2): <src>_<t0>-<t1>.mov, display-rotated, long side 1920, native frame
rate (VFR phone clips -> 29.97 CFR), iPhone HLG tone-mapped to SDR BT.709, x264 High 10 CRF 13, PCM 24-bit.
Keyframe timelapse: <src>_timelapse.mov, the sync samples of the range at 29.97 fps, video only.

x264 preset (measured here on a DJI 4K 10-bit clip, one core, decode + lanczos scale + encode):
  faster (Sep 15) 3.2 fps, Y-PSNR 49.9 dB | superfast 4.7 fps, 50.8 dB | ultrafast 5.8 fps, 49.8 dB
superfast is the default: better than the approved mezzanines and 1.5x faster per core.
"""
import concurrent.futures as cf
import json
import os
import subprocess
import threading
import time

import numpy as np

from . import mp4, stream
from .common import FF, Day, free_disk, log, read_json, set_log, write_json
from .links import LinkPool, MAX_PER_CALL, request_batches, write_request

JOIN_BYTES = 48 << 20


def tstr(x):
    """Seconds as the Sep 15 mezzanine names spell them: 0, 1.2, 606.0, 98.15."""
    x = round(float(x), 2)
    return '0' if x == 0 else str(x)


def movie_of(day, cid):
    p = day.p('idx', cid + '.moov')
    if not os.path.exists(p):
        raise SystemExit(f'no saved moov for {cid} ({p}): survey that clip first')
    return mp4.parse_moov(open(p, 'rb').read())


def _sample_ranges(track, lo, hi):
    """merged byte ranges of the track's samples that lie inside [lo, hi)."""
    if track is None or not track.n:
        return []
    o = track.offsets.astype(np.int64); e = o + track.sizes.astype(np.int64)
    m = (o >= lo) & (e <= hi)
    return mp4.merge_ranges([[int(a), int(b)] for a, b in zip(o[m], e[m])])


def span_disk(movie, sp):
    """bytes a span leaves on disk: the whole range, only the audio samples (audio-only), or only the kept sync samples."""
    if sp['kind'] == 'audio':
        return int(sum(b - a for a, b in _sample_ranges(movie.audio, sp['lo'], sp['hi'])))
    if sp['kind'] == 'keyframes':
        v = movie.video
        return int(sum(int(v.sizes[i]) for i in sp['samples']))
    return sp['hi'] - sp['lo']


def assign_waves(spans, cap):
    """first-fit decreasing on disk bytes: wave numbers from 1, each wave's disk bytes <= cap (a bigger span gets its own)."""
    waves = []
    for s in sorted(spans, key=lambda s: -s['disk']):
        for w in waves:
            if w['disk'] + s['disk'] <= cap:
                w['disk'] += s['disk']; w['spans'].append(s); break
        else:
            waves.append({'disk': s['disk'], 'spans': [s]})
    for k, w in enumerate(waves):
        for s in w['spans']:
            s['wave'] = k + 1
    return [{'wave': k + 1, 'disk': w['disk'], 'download': sum(s['hi'] - s['lo'] for s in w['spans']), 'links': len(w['spans'])}
            for k, w in enumerate(waves)]


def make_plan(day_root, edl_path, out=None, handles=0.8, merge_gap=2.0, preroll=2.0, audio_only_vo=False, waves_gb=None):
    """audio_only_vo: dialog / audio_extra ranges that no shot shows on screen become audio-only jobs
    (<src>_<t0>-<t1>.wav, no 4K decode at all). Saves ~20% of the cut time on Sep 15; off by default because the
    v2 render reads dialog from the .mov mezzanines."""
    day = Day(day_root)
    out = out or day.p('fetch')
    os.makedirs(out, exist_ok=True)
    e = json.load(open(edl_path))
    ranges, tl, aud = {}, {}, {}

    def add(src, a, b, into):
        if src in ('card', None):
            return
        into.setdefault(src, []).append([max(0.0, a - handles), b + handles])
    for s in e.get('shots', []):
        if s.get('speed') == 'keyframes':
            tl.setdefault(s['src'], []).append([s['in'], s['out']])
        else:
            add(s['src'], s['in'], s['out'], ranges)
    for d in e.get('dialog', []) + e.get('audio_extra', []):
        add(d['src'], d['in'], d['out'], aud if audio_only_vo else ranges)
    audio_jobs = {}
    if audio_only_vo:
        for src, rs in aud.items():
            vid = mp4.merge_ranges(sorted(ranges.get(src, [])), gap=merge_gap)
            for a, b in mp4.merge_ranges(sorted(rs), gap=merge_gap):
                if not any(va <= a + 1e-6 and b <= vb + 1e-6 for va, vb in vid):
                    audio_jobs.setdefault(src, []).append([a, b])
    clips = day.clips
    legacy = {}
    for row in read_json(day.p('fetchrows.json'), []) or []:   # Sep 15 scratch layout: [src, i, dropbox path]
        legacy[row[0]] = row[2]
    plan = {'edl': os.path.abspath(edl_path), 'handles': handles, 'clips': {}, 'jobs': [], 'spans': []}
    total = 0
    for src in sorted(set(ranges) | set(tl) | set(audio_jobs)):
        mv = movie_of(day, src)
        meta = read_json(day.p('idx', src + '.json'), {})
        size = meta.get('size') or (clips.get(src) or {}).get('size')
        path = meta.get('path') or (clips.get(src) or {}).get('path') or legacy.get(src)
        dur = mv.video.duration()
        merged = mp4.merge_ranges(sorted([max(0, a), min(dur, b)] for a, b in ranges.get(src, [])), gap=merge_gap)
        spans = []
        for a, b in merged:
            lo, hi = mp4.span(mv, a, b)
            lo2, _ = mp4.span(mv, max(0.0, a - preroll), a)
            spans.append({'lo': min(lo, lo2), 'hi': hi, 'kind': 'range', 'jobs': [f'{src}_{tstr(a)}-{tstr(b)}.mov']})
            plan['jobs'].append({'src': src, 't0': round(a, 3), 't1': round(b, 3), 'kind': 'range',
                                 'out': f'{src}_{tstr(a)}-{tstr(b)}.mov'})
        for a, b in audio_jobs.get(src, []):
            a, b = max(0.0, a), min(dur, b)
            lo, hi = mp4.span(mv, a, b)
            name = f'{src}_{tstr(a)}-{tstr(b)}.wav'
            spans.append({'lo': lo, 'hi': hi, 'kind': 'audio', 'jobs': [name]})
            plan['jobs'].append({'src': src, 't0': round(a, 3), 't1': round(b, 3), 'kind': 'audio', 'out': name})
        # neighbouring spans share one link when the gap is small (one Range request per link)
        spans.sort(key=lambda s: s['lo'])
        joined = []
        for s in spans:
            if joined and s['lo'] - joined[-1]['hi'] <= JOIN_BYTES:
                joined[-1]['hi'] = max(joined[-1]['hi'], s['hi'])
                joined[-1]['jobs'] += s['jobs']
                if joined[-1]['kind'] != s['kind']:
                    joined[-1]['kind'] = 'range'         # a picture range and an audio-only range share one link
            else:
                joined.append(s)
        for a, b in tl.get(src, []):
            idx = mp4.sync_span_samples(mv, a, b)
            v = mv.video
            lo = int(min(v.offsets[i] for i in idx))
            hi = int(max(v.offsets[i] + v.sizes[i] for i in idx))
            name = f'{src}_timelapse.mov'
            joined.append({'lo': lo, 'hi': hi, 'kind': 'keyframes', 'samples': [int(i) for i in idx], 'jobs': [name]})
            plan['jobs'].append({'src': src, 't0': a, 't1': b, 'kind': 'keyframes', 'out': name, 'samples': [int(i) for i in idx]})
        for s in joined:
            s['src'] = src
            s['path'] = path
            s['disk'] = span_disk(mv, s)
            plan['spans'].append(s)
            total += s['hi'] - s['lo']
        plan['clips'][src] = {'size': size, 'path': path, 'duration': round(dur, 3)}
    # biggest downloads first; links are requested in the same order
    plan['spans'].sort(key=lambda s: -(s['hi'] - s['lo']))
    for i, s in enumerate(plan['spans']):
        s['i'] = i
    fps = {}
    for j in plan['jobs']:
        v = movie_of(day, j['src']).video
        fps[j['src']] = len(v.pts) / max(1e-3, v.duration())
        j['frames'] = int(len(j.get('samples', [])) if j['kind'] == 'keyframes' else
                          0 if j['kind'] == 'audio' else (j['t1'] - j['t0'] + 1.0) * fps[j['src']])
    plan['bytes'] = total
    plan['disk_bytes'] = sum(s['disk'] for s in plan['spans'])
    nfr = sum(j['frames'] for j in plan['jobs'])
    if waves_gb:
        plan['waves'] = assign_waves(plan['spans'], int(waves_gb * 1e9))
        plan['spans'].sort(key=lambda s: (s['wave'], -(s['hi'] - s['lo'])))
        for i, s in enumerate(plan['spans']):
            s['i'] = i
        write_json(os.path.join(out, 'fetchplan.json'), plan)
        calls = []
        for w in plan['waves']:
            b = request_batches([(s['path'], 1) for s in plan['spans'] if s['wave'] == w['wave']], per_call=MAX_PER_CALL)
            w['calls'] = len(b)
            calls += [{'batch': len(calls) + k + 1, 'wave': w['wave'], 'entries': e} for k, e in enumerate(b)]
        obj = {'tool': 'Dropbox download_link', 'expiration_in_sec': 900,
               'note': 'Waves: call download_link for the wave-1 batches now and save each raw answer as fetch/links/<n>.json. '
                       'Later waves are asked for through fetch/links/NEED.json when the disk can hold them (fetch --budget-gb).',
               'waves': plan['waves'], 'batches': [c for c in calls if c['wave'] == 1], 'all_batches': calls}
        write_json(os.path.join(out, 'request.json'), obj)
        write_json(os.path.join(out, 'fetchplan.json'), plan)
        log(f"plan: {len(plan['clips'])} clips, {len(plan['jobs'])} cuts, {len(plan['spans'])} spans = {len(plan['spans'])} links in "
            f"{len(plan['waves'])} wave(s) / {len(calls)} call(s), {total / 1e9:.2f} GB to download, {plan['disk_bytes'] / 1e9:.2f} GB "
            f"on disk at most {max(w['disk'] for w in plan['waves']) / 1e9:.2f} GB per wave, ~{nfr} source frames to decode -> {out}")
        for w in plan['waves']:
            log(f"  wave {w['wave']}: {w['links']} links in {w['calls']} call(s), download {w['download'] / 1e9:.2f} GB, disk {w['disk'] / 1e9:.2f} GB")
    else:
        write_json(os.path.join(out, 'fetchplan.json'), plan)
        batches = request_batches([(s['path'], 1) for s in plan['spans']], per_call=MAX_PER_CALL)
        # request order must equal span order: request_batches groups equal paths only when adjacent, which is fine
        write_request(out, batches, note='One link per span, in this order. Save each raw answer as fetch/links/<n>.json.')
        log(f"plan: {len(plan['clips'])} clips, {len(plan['jobs'])} cuts, {len(plan['spans'])} spans = {len(plan['spans'])} links "
            f"in {len(batches)} call(s), {total / 1e9:.2f} GB to fetch, ~{nfr} source frames to decode -> {out}")
    os.makedirs(os.path.join(out, 'links'), exist_ok=True)
    return plan


# ------------------------------------------------------------------ fetch
def init_sparse(day, src, size, sparse_dir):
    p = os.path.join(sparse_dir, src + '.mp4')
    if os.path.exists(p) and os.path.getsize(p) == size:
        return p
    meta = read_json(day.p('idx', src + '.json'), {})
    atoms = {a[0]: a for a in meta.get('atoms', [])}
    with open(p, 'wb') as f:
        f.truncate(size)
        head = open(day.p('idx', src + '.head'), 'rb').read()
        f.seek(0)
        f.write(head)
        moov = open(day.p('idx', src + '.moov'), 'rb').read()
        if 'moov' in atoms:
            f.seek(atoms['moov'][1])
        else:
            t = read_json(day.p('idx', src + '.tail.json'), {})
            f.seek(t['moov_offset'])
        f.write(moov)
    return p


def fetch_span(url, span, sparse_path, movie, progress=None):
    lo, hi = span['lo'], span['hi']
    fd = os.open(sparse_path, os.O_RDWR)
    try:
        if span['kind'] == 'range':
            pos = [lo]

            def sink(mv):
                os.pwrite(fd, mv, pos[0])
                pos[0] += len(mv)
                if progress is not None:
                    progress[span['i']] = pos[0] - lo
            got, secs = stream.http_stream(url, sink, expect_size=hi - lo, rng=(lo, hi))
        else:  # keyframes: only the sync samples inside the range; audio: only the audio samples
            v = movie.video
            if span['kind'] == 'audio':
                keep = _sample_ranges(movie.audio, lo, hi)
            else:
                keep = mp4.merge_ranges([[int(v.offsets[i]), int(v.offsets[i] + v.sizes[i])] for i in span['samples']])
            state = {'pos': lo, 'k': 0, 'w': 0}

            def sink(mv):
                a = state['pos']
                b = a + len(mv)
                k = state['k']
                while k < len(keep) and keep[k][1] <= a:
                    k += 1
                j = k
                while j < len(keep) and keep[j][0] < b:
                    x, y = max(a, keep[j][0]), min(b, keep[j][1])
                    if y > x:
                        os.pwrite(fd, mv[x - a:y - a], x)
                        state['w'] += y - x
                    if keep[j][1] <= b:
                        j += 1
                    else:
                        break
                state['k'] = j
                state['pos'] = b
                if progress is not None:
                    progress[span['i']] = state['w']
            got, secs = stream.http_stream(url, sink, expect_size=hi - lo, rng=(lo, hi))
    finally:
        os.close(fd)
    return got, secs


def video_filters(meta, movie, cfr=None):
    probe = meta.get('probe', '')
    vf = []
    if 'arib-std-b67' in probe or (meta.get('video') or {}).get('hlg'):
        vf.append('zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,'
                  'zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv')
    vf.append("scale='if(gte(iw,ih),1920,-2)':'if(gte(iw,ih),-2,1920)':flags=lanczos")
    if cfr:
        vf.append(f'fps={cfr}')
    vf.append('format=yuv420p10le')
    return vf


def is_vfr(movie):
    v = movie.video
    d = np.diff(v.dts[: min(len(v.dts), 2000)])
    return len(d) > 10 and (d.max() - d.min()) > 0.05 * np.median(d)


def hwaccel():
    """VLOG_HWACCEL=videotoolbox (the Mac setup sets it only after doctor.py found hardware decode bit-identical to
    software decode on this machine) decodes the HEVC sources on the media engine instead of a CPU core."""
    hw = os.environ.get('VLOG_HWACCEL', '').strip()
    return ['-hwaccel', hw] if hw else []


def cut_range(sparse_path, job, meta, movie, out_dir, crf, preset):
    out = os.path.join(out_dir, job['out'])
    tmp = os.path.join(out_dir, '.' + job['out'] + '.part.mov')
    vf = video_filters(meta, movie, '30000/1001' if is_vfr(movie) else None)
    a, b = job['t0'], job['t1']
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y', '-threads', '1'] + hwaccel() + ['-ss', str(a), '-i', sparse_path,
           '-t', str(round(b - a, 3)), '-map', '0:v:0', '-map', '0:a:0?', '-filter_threads', '1', '-vf', ','.join(vf),
           '-c:v', 'libx264', '-threads', '1', '-preset', preset, '-crf', str(crf), '-profile:v', 'high10',
           '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-f', 'mov', tmp]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-400:])
    os.replace(tmp, out)
    return out


def cut_audio(sparse_path, job, meta, movie, out_dir, crf=None, preset=None):
    out = os.path.join(out_dir, job['out'])
    tmp = os.path.join(out_dir, '.' + job['out'] + '.part.wav')
    a, b = job['t0'], job['t1']
    r = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(a), '-i', sparse_path, '-t', str(round(b - a, 3)),
                        '-map', '0:a:0', '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2', '-f', 'wav', tmp],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-400:])
    os.replace(tmp, out)
    return out


def cut_keyframes(sparse_path, job, meta, movie, out_dir, crf, preset):
    """Timelapse: the kept sync samples as a raw Annex-B stream -> ffmpeg at 29.97 fps."""
    v = movie.video
    out = os.path.join(out_dir, job['out'])
    tmp = os.path.join(out_dir, '.' + job['out'] + '.part.mov')
    hdr, nal = mp4.annexb_header(v)
    fmt = 'hevc' if v.codec in ('hvc1', 'hev1') else 'h264'
    rot = {90: ['transpose=1'], 270: ['transpose=2'], 180: ['transpose=1,transpose=1']}.get(v.rotation, [])
    vf = rot + video_filters(meta, movie)
    cmd = [FF, '-hide_banner', '-loglevel', 'error', '-y', '-threads', '1', '-f', fmt, '-framerate', '30000/1001',
           '-i', 'pipe:0', '-map', '0:v:0', '-filter_threads', '1', '-vf', ','.join(vf), '-r', '30000/1001',
           '-c:v', 'libx264', '-threads', '1', '-preset', preset, '-crf', str(crf), '-profile:v', 'high10',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-f', 'mov', tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(sparse_path, 'rb') as f:
        for i in job['samples']:
            f.seek(int(v.offsets[i]))
            p.stdin.write(hdr + mp4.to_annexb(f.read(int(v.sizes[i])), nal))
    p.stdin.close()
    err = p.stderr.read().decode(errors='replace')
    if p.wait():
        raise RuntimeError(err[-400:])
    os.replace(tmp, out)
    return out


def _cut_worker(args):
    sparse_path, job, meta, moov_path, out_dir, crf, preset = args
    movie = mp4.parse_moov(open(moov_path, 'rb').read())
    t = time.time()
    fn = {'keyframes': cut_keyframes, 'audio': cut_audio}.get(job['kind'], cut_range)
    fn(sparse_path, job, meta, movie, out_dir, crf, preset)
    return time.time() - t


def punch(path, lo, hi):
    """free the bytes [lo, hi) of a sparse file (the file keeps its size; reads there return zeros)."""
    r = subprocess.run(['fallocate', '--punch-hole', '--offset', str(lo), '--length', str(hi - lo), path], capture_output=True, text=True)
    return r.returncode == 0


def est_mezz_bytes(job):
    """a mezzanine's size, for the disk budget: x264 High 10 CRF 13 at 1920 on the long side, measured about 0.1 MB per
    source frame on Sep 15 (2 GB for the cut); 0.16 MB is used to stay on the safe side. PCM 24-bit stereo for audio."""
    if job['kind'] == 'audio':
        return int((job['t1'] - job['t0']) * 48000 * 6) + (1 << 16)
    return int(job['frames'] * 160e3) + int((job['t1'] - job['t0'] + 1) * 48000 * 6)


def run_fetch(day_root, plan_path, links, out, workers=4, crf=13, preset='superfast', streams=6, budget_gb=None,
              reserve_gb=0.6, wait_links=1800):
    """fetch + cut. budget_gb=None: every span as soon as its link is there (the original behaviour). budget_gb=X: the
    spans held on disk at once are kept under X GB and under what the disk can take (free space - reserve_gb - the
    mezzanines still to be written); the next wave's links are requested through links/NEED.json when it fits."""
    import multiprocessing as mp
    day = Day(day_root)
    wdir = os.path.dirname(os.path.abspath(plan_path)) if plan_path else day.p('fetch')
    plan_path = plan_path or os.path.join(wdir, 'fetchplan.json')
    plan = json.load(open(plan_path))
    set_log(os.path.join(wdir, 'fetch.log'))
    sparse_dir = os.path.join(wdir, 'sparse')
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    ldir = os.path.join(wdir, 'links')
    os.makedirs(ldir, exist_ok=True)
    if links and os.path.abspath(os.path.dirname(os.path.abspath(links))) != os.path.abspath(ldir):
        import shutil
        shutil.copy(links, os.path.join(ldir, os.path.basename(links)))
    pool = LinkPool(ldir)
    pool.scan()
    need_all = sum(s.get('disk', s['hi'] - s['lo']) for s in plan['spans'])
    if not budget_gb and free_disk(wdir) < need_all + (2 << 30):
        log(f'warning: {free_disk(wdir) / 1e9:.1f} GB free for {need_all / 1e9:.1f} GB of spans (use --budget-gb)')
    movies, metas, sparse = {}, {}, {}
    for src, c in plan['clips'].items():
        movies[src] = movie_of(day, src)
        metas[src] = read_json(day.p('idx', src + '.json'), {})
        sparse[src] = init_sparse(day, src, c['size'], sparse_dir)
    done_spans = set(read_json(os.path.join(wdir, 'spans_done.json'), []) or [])
    jobs = {j['out']: j for j in plan['jobs']}
    job_spans = {name: [s['i'] for s in plan['spans'] if name in s['jobs']] for name in jobs}
    span_by_i = {s['i']: s for s in plan['spans']}
    finished = {n for n in jobs if os.path.exists(os.path.join(out, n))}
    punched = set()
    disk = lambda s: s.get('disk', s['hi'] - s['lo'])  # noqa: E731
    t0 = time.time()
    lock = threading.Lock()
    fetched_bytes = [0]
    progress = {}
    errors = []

    def get(s, link):
        got, secs = fetch_span(link['url'], s, sparse[s['src']], movies[s['src']], progress)
        with lock:
            fetched_bytes[0] += got
        return s['i'], got, secs
    fex = cf.ThreadPoolExecutor(streams)
    cex = cf.ProcessPoolExecutor(workers, mp_context=mp.get_context('spawn'))
    pending = sorted([s for s in plan['spans'] if s['i'] not in done_spans and not all(n in finished for n in s['jobs'])],
                     key=lambda s: (s.get('wave', 1), -(s['hi'] - s['lo'])))
    ffuts, cfuts, started, cut_s = {}, {}, set(), {}
    need_path = os.path.join(ldir, 'NEED.json')
    need_since = None
    last_links = time.time()
    last_scan = 0.0
    retries = {}

    def room():
        """bytes a new download may still take: free space minus the reserve, the unwritten rest of the running
        downloads and the mezzanines not written yet."""
        inflight = sum(max(0, disk(s) - progress.get(s['i'], 0)) for s in ffuts.values())
        mezz = sum(est_mezz_bytes(jobs[n]) for n in jobs if n not in finished)
        r = free_disk(wdir) - int(reserve_gb * 1e9) - inflight - mezz
        if budget_gb:
            held = sum(disk(span_by_i[i]) for i in done_spans if i not in punched) + sum(disk(s) for s in ffuts.values())
            r = min(r, int(budget_gb * 1e9) - held)
        return r

    while pending or ffuts or cfuts:
        now = time.time()
        if now - last_scan > 2:
            last_scan = now
            if pool.scan():
                last_links = now
                if os.path.exists(need_path):
                    os.remove(need_path)
                need_since = None
                log(f'links: {len(pool.links)} known')
        # ---- downloads: in wave order, when there is a link and room on the disk
        for s in list(pending):
            if len(ffuts) >= streams:
                break
            if not pool.fresh(s['path']):
                continue
            if budget_gb is not None and disk(s) > room() and (ffuts or cfuts or done_spans - punched):
                continue                                   # wait for cuts to free space (never deadlock on an empty pipe)
            link = pool.take(s['path'], f"span{s['i']}")
            pending.remove(s)
            ffuts[fex.submit(get, s, link)] = s
        # ---- links for the next wave: asked for when the disk can hold that wave (so they cannot expire waiting)
        if pending and not os.path.exists(need_path):
            w = pending[0].get('wave', 1)
            wave = [s for s in pending if s.get('wave', 1) == w]
            have = {}
            for s in wave:
                have[s['path']] = have.get(s['path'], 0)
            want = []
            for s in wave:
                k = s['path']
                if len(pool.fresh(k)) > have[k]:
                    have[k] += 1
                else:
                    want.append(k)
            fits = budget_gb is None or sum(disk(s) for s in wave) <= room() or not (ffuts or cfuts)
            if want and fits and not ffuts:
                write_json(need_path, {'entries': want[:MAX_PER_CALL], 'wave': w, 'expiration_in_sec': 900,
                                       'note': f'fetch: links for wave {w} ({len(want)} span(s); '
                                               f'{sum(disk(s) for s in wave) / 1e9:.2f} GB on disk). Save the raw answer as links/<n>.json.'})
                need_since = now
                log(f'NEED.json: wave {w}, {min(len(want), MAX_PER_CALL)} link(s) (of {len(want)})')
        # ---- finished downloads
        for f in [f for f in ffuts if f.done()]:
            s = ffuts.pop(f)
            try:
                i, got, secs = f.result()
                done_spans.add(i)
                write_json(os.path.join(wdir, 'spans_done.json'), sorted(done_spans))
                log(f"span {i} {s['src']} (wave {s.get('wave', 1)}) {got / 1e6:.0f} MB in {secs:.1f}s ({got / max(secs, 1e-3) / 1e6:.0f} MB/s)")
            except Exception as e:
                retries[s['i']] = retries.get(s['i'], 0) + 1
                errors.append(f"span {s['i']} {s['src']}: {e}")
                log(f"span {s['i']} {s['src']} FAILED ({retries[s['i']]}): {e}")
                if retries[s['i']] < 3:
                    pending.insert(0, s)                   # a fresh link is asked for through NEED.json
        # ---- cuts, longest first, once all their spans are in
        ready = [n for n in jobs if n not in finished and n not in started and all(i in done_spans for i in job_spans[n])]
        ready.sort(key=lambda n: -jobs[n]['frames'])
        for n in ready:
            if len(cfuts) >= workers:
                break
            j = jobs[n]
            started.add(n)
            args = (sparse[j['src']], j, metas[j['src']], day.p('idx', j['src'] + '.moov'), out, crf, preset)
            cfuts[cex.submit(_cut_worker, args)] = n
        for f in [f for f in cfuts if f.done()]:
            n = cfuts.pop(f)
            try:
                cut_s[n] = f.result()
                finished.add(n)
                log(f'cut {n}: {jobs[n]["frames"]} frames in {cut_s[n]:.0f}s ({jobs[n]["frames"] / max(cut_s[n], 1e-3):.1f} fps)')
            except Exception as e:
                errors.append(f'cut {n}: {e}')
                log(f'cut {n} FAILED: {str(e)[:300]}')
                finished.add(n)                            # not retried here; reported as missing below
                open(os.path.join(wdir, 'cut_failed.txt'), 'a').write(n + '\n')
            # a span whose every cut is done is freed
            for i in job_spans[n]:
                sp = span_by_i[i]
                if i not in punched and all(m in finished for m in sp['jobs']):
                    if punch(sparse[sp['src']], sp['lo'], sp['hi']):
                        punched.add(i)
        if pending and not ffuts and not cfuts and not any(pool.fresh(s['path']) for s in pending):
            if now - last_links > wait_links:
                log(f'no links for {wait_links} s: stopping with {len(pending)} span(s) not fetched')
                break
        time.sleep(0.2)
    fex.shutdown()
    cex.shutdown()
    if os.path.exists(need_path) and not pending:
        os.remove(need_path)
    failed = set(open(os.path.join(wdir, 'cut_failed.txt')).read().split()) if os.path.exists(os.path.join(wdir, 'cut_failed.txt')) else set()
    missing = [n for n in jobs if not os.path.exists(os.path.join(out, n))]
    el = time.time() - t0
    log(f'fetch+cut done in {el:.0f}s: {len(jobs) - len(missing)}/{len(jobs)} mezzanines in {out}, fetched {fetched_bytes[0] / 1e9:.2f} GB'
        + (f'; missing: {missing}' if missing else ''))
    if not missing:
        import shutil
        shutil.rmtree(sparse_dir, ignore_errors=True)
    write_json(os.path.join(wdir, 'fetch_report.json'), {'wall_s': round(el, 1), 'cuts': cut_s, 'errors': errors,
                                                         'missing': missing, 'failed_cuts': sorted(failed)})
    return 0 if not missing else 1
