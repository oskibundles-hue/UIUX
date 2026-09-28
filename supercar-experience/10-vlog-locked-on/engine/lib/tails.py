"""tails: the smallest survey that lets `plan` and `fetch` run -- each clip's moov, a head and a probe, nothing else.

For rebuilding a finished cut on a machine where the day was never ingested (the index, the moovs and the transcripts
are gone), when the full ingest (one whole-file stream per clip) is not wanted. Per clip, one single-use link:

  tail   one Range request for the last max(tail_mb, size/1000) bytes -> the moov (DJI and most camera files keep it
         at the end). The head is then written as a 16-byte `mdat` atom header that spans the file from byte 0 to the
         moov, so ffmpeg reads a sparse file of the original size (this head + the moov + the fetched spans) like the
         original: every sample offset in the moov is absolute, and nothing before the moov is read except samples.
  head   (clips that are not DJI files, e.g. phone .MOV uploads: a second link) the first head_mb bytes: the real
         ftyp/wide/mdat header, and the moov itself when the file is fast-start (moov at the front).

    vlog.py tails DAY --clips LIST [--clips LIST2] --edl EDL     register every clip in the listings (ids like
                                                                   ingest: DJI counter, P<hhmm>[a-z] for phones) and
                                                                   write links/request.json for the clips EDL uses
    vlog.py tails DAY --run                                       read links/*.json, fetch, write idx/<id>.head .moov
                                                                   .json .tail.json (what plan / fetch read)

LIST: the Dropbox list_folder answer (raw JSON), or a text file of paths (optional TAB size).
"""
import json
import os
import struct
import subprocess
import time

from . import mp4, stream
from .common import FF, DJI_RE, Day, clock_from_movie, log, name_clock, read_json, set_log, write_json
from .links import LinkPool, MAX_PER_CALL, request_batches, write_request


def is_dji(path):
    return bool(DJI_RE.search(os.path.basename(path)))


def edl_sources(edl_path):
    e = json.load(open(edl_path))
    return sorted({x['src'] for k in ('shots', 'dialog', 'audio_extra') for x in e.get(k, []) if x.get('src') not in (None, 'card')})


def request(day_root, listings, edl_path, load_clip_list):
    """register all clips of the listings, write links/request.json for the ones the EDL uses."""
    day = Day(day_root)
    entries = []
    for f in listings:
        entries += load_clip_list(f)
    if not entries:
        raise SystemExit('tails: no clips in the listing(s)')
    reg = day.register(entries)
    want = edl_sources(edl_path)
    missing = [s for s in want if s not in reg]
    if missing:
        raise SystemExit(f'tails: the EDL uses clips that are not in the listing(s): {missing} (ids registered: {sorted(reg)})')
    need = [(reg[s]['path'], 1 if is_dji(reg[s]['path']) else 2) for s in want]
    batches = request_batches(need, per_call=MAX_PER_CALL)
    write_request(day.p('links'), batches, note='tails: one link per DJI clip (tail), two per other clip (tail + head). '
                                                'Save each raw answer as links/<name>.json.')
    write_json(day.p('tails_want.json'), want)
    n = sum(len(b) for b in batches)
    log(f'tails: {len(reg)} clips registered, {len(want)} used by the EDL -> {n} links in {len(batches)} call(s): {day.p("links", "request.json")}')
    for s in want:
        c = reg[s]
        log(f'  {s:7s} {c["path"]}  {(c.get("size") or 0) / 1e9:.2f} GB')
    return batches


def _top_atoms_prefix(buf):
    """top-level atoms from byte 0 of a file prefix: [(type, off, size, hdr)] until the prefix ends."""
    out, off = [], 0
    while off + 8 <= len(buf):
        size, typ = struct.unpack('>I4s', buf[off:off + 8]); hdr = 8
        if size == 1:
            if off + 16 > len(buf):
                break
            size = struct.unpack('>Q', buf[off + 8:off + 16])[0]; hdr = 16
        elif size == 0:
            size = None
        out.append((typ.decode('latin1'), off, size, hdr))
        if size is None or size < 8:
            break
        off += size
    return out


def survey_clip(day, cid, rec, pool, tail_mb=24, head_mb=8):
    size = rec.get('size')
    path = rec['path']
    t0 = time.time()
    link = pool.take(path, 'tail')
    if not link:
        raise RuntimeError('no fresh link (tail)')
    size = size or link.get('size')
    n = min(size, max(tail_mb << 20, size // 1000))
    tail = stream.http_range(link['url'], size - n, size)
    found = mp4.find_moov_in_tail(tail, size)
    head = None
    if not is_dji(path):
        hl = pool.take(path, 'head')
        if hl:
            head = stream.http_range(hl['url'], 0, min(size, head_mb << 20))
    atoms = None
    if found:
        moov_off, moov, rest = found
        if head:
            pre = _top_atoms_prefix(head)
            md = [a for a in pre if a[0] == 'mdat']
            if not md:
                raise RuntimeError(f'head of {cid}: no mdat atom in the first {head_mb} MB: {pre[:6]}')
            hb = head[:md[0][1] + md[0][3]]                       # everything up to and including the mdat header
            atoms = [[t, o, s] for t, o, s, h in pre if o <= md[0][1]] + [[t, o, s] for t, o, s in rest]
        else:
            hb = struct.pack('>I4sQ', 1, b'mdat', moov_off)       # one mdat atom from byte 0 to the moov
            atoms = [['mdat', 0, moov_off]] + [[t, o, s] for t, o, s in rest]
        write_json(day.p('idx', cid + '.tail.json'), {'moov_offset': moov_off, 'atoms_from_moov': rest, 'tail_bytes': n})
    else:
        if not head:
            raise RuntimeError(f'{cid}: no moov in the last {n >> 20} MB and no head link (a fast-start file needs one)')
        pre = _top_atoms_prefix(head)
        mv = [a for a in pre if a[0] == 'moov']
        if not mv or mv[0][1] + mv[0][2] > len(head):
            raise RuntimeError(f'{cid}: moov neither in the tail nor complete in the first {head_mb} MB: {pre[:6]}')
        t, o, s, h = mv[0]
        moov = head[o:o + s]
        md = [a for a in pre if a[0] == 'mdat']
        end = (md[0][1] + md[0][3]) if md else o + s
        hb = head[:end]
        atoms = [[t, o, s] for t, o, s, h in pre if o < end]
    movie = mp4.parse_moov(moov)
    open(day.p('idx', cid + '.head'), 'wb').write(hb)
    open(day.p('idx', cid + '.moov'), 'wb').write(moov)
    # probe: a sparse file of the original size holding only the head and the moov (ffmpeg reads the stream info)
    sp = day.p('sparse', cid + '.probe.mp4')
    with open(sp, 'wb') as f:
        f.truncate(size)
        f.seek(0); f.write(hb)
        mo = [a for a in atoms if a[0] == 'moov'][0][1]
        f.seek(mo); f.write(moov)
    probe = subprocess.run([FF, '-hide_banner', '-i', sp], capture_output=True, text=True).stderr
    os.remove(sp)
    if 'Stream #' not in probe:
        raise RuntimeError(f'{cid}: ffmpeg cannot read the head + moov: {probe[-300:]}')
    clock = name_clock(path) or clock_from_movie(movie)
    v, a = movie.video, movie.audio
    meta = {'id': cid, 'name': rec.get('name'), 'path': path, 'size': size, 'atoms': atoms, 'probe': probe,
            'clock': clock[1] if clock else None, 'date': clock[0] if clock else None,
            'duration': round(v.duration() if v else (a.duration() if a else 0), 3),
            'video': {'codec': v.codec, 'w': v.width, 'h': v.height, 'rotation': v.rotation,
                      'hlg': 'arib-std-b67' in probe, 'sync': len(v.sync_indices())} if v else None,
            'audio': {'codec': a.codec} if a else None,
            'survey': {'kind': 'tails', 'tail_bytes': n, 'head_bytes': len(head) if head else 0, 'head_synthesized': head is None}}
    write_json(day.p('idx', cid + '.json'), meta)
    return dict(cid=cid, s=round(time.time() - t0, 1), duration=meta['duration'], moov_mb=round(len(moov) / 2 ** 20, 2),
                where='tail' if found else 'head', video=meta['video'])


def run(day_root, tail_mb=24, head_mb=8, workers=6, wait=600):
    import concurrent.futures as cf
    day = Day(day_root)
    set_log(day.p('logs', 'tails.log'))
    want = read_json(day.p('tails_want.json'), []) or []
    reg = day.clips
    todo = [s for s in want if not os.path.exists(day.p('idx', s + '.json'))]
    pool = LinkPool(day.p('links'))
    t_end = time.time() + wait
    while True:
        pool.scan()
        ready = [s for s in todo if len(pool.fresh(reg[s]['path'])) >= (1 if is_dji(reg[s]['path']) else 2)]
        if len(ready) == len(todo) or time.time() > t_end:
            break
        log(f'tails: waiting for links ({len(ready)}/{len(todo)} clips have theirs)')
        time.sleep(5)
    errors = {}
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(survey_clip, day, s, reg[s], pool, tail_mb, head_mb): s for s in ready}
        for f in cf.as_completed(futs):
            s = futs[f]
            try:
                r = f.result()
                log(f"tails: {s} moov {r['moov_mb']} MB from the {r['where']}, {r['duration']} s, {r['video']['w']}x{r['video']['h']} "
                    f"{r['video']['codec']}{' HLG' if r['video']['hlg'] else ''} ({r['s']} s)")
            except Exception as e:
                errors[s] = str(e)[:300]
                log(f'tails: {s} FAILED: {errors[s]}')
    left = [s for s in want if not os.path.exists(day.p('idx', s + '.json'))]
    if left:
        need = request_batches([(reg[s]['path'], 1 if is_dji(reg[s]['path']) else 2) for s in left], per_call=MAX_PER_CALL)
        write_json(day.p('links', 'NEED.json'), {'entries': need[0], 'note': 'tails: fresh links for the clips that failed'})
        log(f'tails: {len(left)} clip(s) not surveyed: {left} -> links/NEED.json')
    write_json(day.p('logs', 'tails_report.json'), {'done': [s for s in want if s not in left], 'left': left, 'errors': errors})
    return 0 if not left else 1
