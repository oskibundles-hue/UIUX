"""ingest: survey a day of footage straight from single-use Dropbox links, never holding an original on disk.

Per clip (2 links):
  link 1  tail Range request (last max(16 MB, size/1000)) -> moov -> sample tables   [idx/<id>.moov cached]
  link 2  one GET of the whole file through StreamFilter -> sparse/<id>.mp4 holding head + moov + all audio
          samples + one video sync sample every --kf-step seconds (a few % of the file)
  then    idx/<id>.head|.json, aud/<id>.m4a (stream copy, .part then rename), kf/<id>/*.jpg (+stats.json),
          sparse file deleted; the audio goes to the whisper pool.
Up to --streams clips download at once (largest first); tails for a whole batch run as soon as its links arrive.
The whisper pool grows as downloads and thumbnail decoding free cores (1 thread per worker).

Links: every *.json in DAY/links is read (raw Dropbox tool output). When the ingest is about to run out of
links it writes DAY/links/NEED.json with the next <=25 paths to request; saving the tool's answer as any new
DAY/links/<name>.json continues the run. A failed clip is reported and simply needs fresh links: re-running
ingest (or leaving it running) picks them up. Links are logged to links/used.log before use and never reused.
"""
import concurrent.futures as cf
import fcntl
import multiprocessing as mp
import os
import subprocess
import threading
import time

from . import mp4, stream, thumbs
from .asr import AsrPool
from .common import FF, Day, clock_from_movie, free_disk, log, name_clock, read_json, set_log, write_json
from .links import LinkPool, MAX_PER_CALL, request_batches


def stream_order(items, size_of, big_first=2):
    """The order clips are streamed (and their links requested): the `big_first` largest clips first, so the
    long downloads start at once, then everything else smallest first, so audio and thumbnails reach the
    CPU-bound work (whisper, keyframe decode) as early as possible. The network (~300-400 MB/s) outruns the
    4 cores; keeping the cores fed early is what shortens the day (see README, "Why this order")."""
    by_size = sorted(items, key=lambda x: -(size_of(x) or 0))
    return by_size[:big_first] + sorted(by_size[big_first:], key=lambda x: (size_of(x) or 0))


class Clip:
    def __init__(self, cid, rec):
        self.id = cid
        self.path = rec['path']
        self.name = rec.get('name')
        self.size = rec.get('size')
        self.status = 'need_tail'   # need_tail | tail | ready | stream | post | surveyed | failed
        self.moov = None
        self.moov_at_start = False
        self.tail_info = None
        self.error = None
        self.attempts = 0
        self.t = {}


class Ingest:
    def __init__(self, day_root, streams=5, kf_step=2.0, kf_workers=2, asr_max=4, asr=True, tail_mb=16,
                 spill_under=2 << 30, wait_links=900, clips_per_call=12, reserve_gb=2.0, cores=None, big_first=2):
        self.day = Day(day_root)
        set_log(self.day.p('logs', 'ingest.log'))
        self.streams = streams
        self.kf_step = kf_step
        self.kf_workers = kf_workers
        self.asr_on = asr
        self.tail_bytes = tail_mb << 20
        self.spill_under = spill_under
        self.wait_links = wait_links
        self.clips_per_call = clips_per_call
        self.reserve = int(reserve_gb * (1 << 30))
        self.cores = cores or os.cpu_count() or 4
        self.big_first = big_first
        self.pool = LinkPool(self.day.p('links'))
        self.clips = {}
        self.lock = threading.Lock()
        self.tail_ex = cf.ThreadPoolExecutor(6)
        self.stream_ex = cf.ThreadPoolExecutor(streams)
        self.post_ex = cf.ThreadPoolExecutor(2)
        self.kf_ex = cf.ProcessPoolExecutor(kf_workers, mp_context=mp.get_context('spawn'))
        self.asr = AsrPool(self.day.p('tr'), max_workers=asr_max, threads=1)
        self.inflight = {}      # future -> (kind, cid)
        self.kf_busy = 0
        self.bytes_streamed = 0
        self.stream_bytes_total = 0
        self.t_start = time.time()
        self.last_activity = time.time()
        self.stop = threading.Event()
        self.need_written = None
        self.timings = {}

    # ------------------------------------------------------------------ setup
    def load(self):
        self.pool.scan()
        entries = self.pool.entries()
        if entries:
            self.day.register(entries)
        reg = self.day.clips
        for cid, rec in reg.items():
            c = Clip(cid, rec)
            st = self.day.state(cid)
            c.attempts = st.get('attempts', 0)
            if st.get('surveyed') and os.path.exists(self.day.p('idx', cid + '.json')):
                c.status = 'surveyed'
            elif os.path.exists(self.day.p('idx', cid + '.moov')):
                c.moov = open(self.day.p('idx', cid + '.moov'), 'rb').read()
                c.status = 'ready'
            elif st.get('moov_at_start'):
                c.moov_at_start = True
                c.status = 'ready'
            self.clips[cid] = c
            if self.asr_on and c.status == 'surveyed' and not os.path.exists(self.day.p('tr', cid + '.json')):
                a = self.day.p('aud', cid + '.m4a')
                if os.path.exists(a):
                    meta = read_json(self.day.p('idx', cid + '.json'), {})
                    self.asr.add(cid, a, priority=meta.get('duration') or 0)
        self.stream_bytes_total = sum((c.size or 0) for c in self.clips.values() if c.status != 'surveyed')

    def refresh_links(self):
        if self.pool.scan():
            entries = self.pool.entries()
            reg = self.day.register(entries)
            for cid, rec in reg.items():
                if cid not in self.clips:
                    self.clips[cid] = Clip(cid, rec)
                    self.stream_bytes_total += rec.get('size') or 0
                elif not self.clips[cid].size and rec.get('size'):
                    self.clips[cid].size = rec['size']
            need = self.day.p('links', 'NEED.json')
            if os.path.exists(need):
                os.unlink(need)
                self.need_written = None
            log(f'links: {len(self.pool.links)} known, new file(s) read')
            self.last_activity = time.time()

    # ------------------------------------------------------------------ link 1: tail
    def do_tail(self, c, link):
        t0 = time.time()
        size = c.size or link.get('size')
        n = min(size, max(self.tail_bytes, size // 1000))
        tail = stream.http_range(link['url'], size - n, size)
        found = mp4.find_moov_in_tail(tail, size)
        dt = time.time() - t0
        if found:
            off, moov, rest = found
            tmp = self.day.p('idx', c.id + '.moov.part')
            with open(tmp, 'wb') as f:
                f.write(moov)
            os.replace(tmp, self.day.p('idx', c.id + '.moov'))
            write_json(self.day.p('idx', c.id + '.tail.json'), {'moov_offset': off, 'atoms_from_moov': rest, 'tail_bytes': n})
            return {'moov': moov, 'secs': dt, 'bytes': n}
        return {'moov': None, 'secs': dt, 'bytes': n}

    # ------------------------------------------------------------------ link 2: the stream
    def do_stream(self, c, link):
        size = c.size or link.get('size')
        sp_path = self.day.p('sparse', c.id + '.mp4')
        sp = stream.SparseFile(sp_path, size)
        movie = mp4.parse_moov(c.moov) if c.moov else None
        kf_step = self.kf_step
        filt = stream.StreamFilter(size, sp, lambda m: mp4.keep_ranges(m, kf_step), movie=movie,
                                   spill_under=self.spill_under)
        counted = [0]

        def sink(mv):
            filt.feed(mv)
            n = len(mv)
            counted[0] += n
            with self.lock:
                self.bytes_streamed += n
        try:
            total, secs = stream.http_stream(link['url'], sink, expect_size=size, stop=self.stop)
            res = filt.finish()
        except BaseException:
            sp.close()
            with self.lock:
                self.bytes_streamed -= counted[0]
            try:
                os.unlink(sp_path)
            except OSError:
                pass
            raise
        sp.close()
        res['secs'] = secs
        res['moov'] = filt.moov_bytes
        res['kept_sync'] = filt.kept_sync
        res['sparse'] = sp_path
        return res

    # ------------------------------------------------------------------ after the stream
    def do_post(self, c, res):
        """idx files, probe, audio copy. Runs in a thread (ffmpeg does the work)."""
        t0 = time.time()
        cid = c.id
        sp_path = res['sparse']
        moov = res['moov']
        head = stream.read_head(sp_path, res['head_end'])
        with open(self.day.p('idx', cid + '.head'), 'wb') as f:
            f.write(head)
        tmp = self.day.p('idx', cid + '.moov.part')
        with open(tmp, 'wb') as f:
            f.write(moov)
        os.replace(tmp, self.day.p('idx', cid + '.moov'))
        probe = subprocess.run([FF, '-hide_banner', '-i', sp_path], capture_output=True, text=True).stderr
        movie = mp4.parse_moov(moov)
        clock = name_clock(c.path) or clock_from_movie(movie)
        v = movie.video
        a = movie.audio
        meta = {'id': cid, 'name': c.name, 'path': c.path, 'size': c.size, 'atoms': res['atoms'], 'probe': probe,
                'clock': clock[1] if clock else None, 'date': clock[0] if clock else None,
                'duration': round(v.duration() if v else (a.duration() if a else 0), 3),
                'video': {'codec': v.codec, 'w': v.width, 'h': v.height, 'rotation': v.rotation,
                          'hlg': 'arib-std-b67' in probe, 'sync': len(v.sync_indices())} if v else None,
                'audio': {'codec': a.codec} if a else None,
                'survey': {'kf_step': self.kf_step, 'kept_bytes': res['kept_bytes'], 'kept_keyframes': len(res['kept_sync'] or []),
                           'spilled': res.get('spilled', False)}}
        write_json(self.day.p('idx', cid + '.json'), meta)
        clips = self.day.clips
        if cid in clips and clock:
            clips[cid]['clock'], clips[cid]['date'] = clock[1], clock[0]
            self.day.save_clips(clips)
        audio = None
        if a is not None and a.n:
            part = self.day.p('aud', f'.{cid}.m4a.part')
            r = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', sp_path, '-map', '0:a:0', '-c', 'copy',
                                '-f', 'ipod', part], capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(part) or os.path.getsize(part) < 1000:
                raise RuntimeError('audio copy failed: ' + r.stderr[-300:])
            audio = self.day.p('aud', cid + '.m4a')
            os.replace(part, audio)
        return {'audio': audio, 'secs': time.time() - t0, 'movie_dur': meta['duration']}

    # ------------------------------------------------------------------ scheduling
    def submit(self, fut, kind, cid):
        self.inflight[fut] = (kind, cid)

    def active(self, kind):
        return sum(1 for k, _ in self.inflight.values() if k == kind)

    def ordered(self):
        return stream_order(list(self.clips.values()), lambda c: c.size, self.big_first)

    def schedule(self):
        now = time.time()
        order = self.ordered()
        # tails: as soon as links are there
        for c in order:
            if c.status == 'need_tail' and self.active('tail') < 6:
                link = self.pool.take(c.path, 'tail')
                if link:
                    c.size = c.size or link.get('size')
                    c.status = 'tail'
                    c.t['tail_start'] = now
                    self.submit(self.tail_ex.submit(self.do_tail, c, link), 'tail', c.id)
        # streams, in stream_order
        for c in order:
            if self.active('stream') >= self.streams:
                break
            if c.status != 'ready' or not self.pool.fresh(c.path):
                continue
            est = (c.size or 0) * 0.06 + (c.size if (not c.moov and (c.size or 0) <= self.spill_under) else 0)
            if free_disk(self.day.root) - est < self.reserve:
                continue
            link = self.pool.take(c.path, 'stream')
            c.status = 'stream'
            c.t['stream_start'] = now
            self.submit(self.stream_ex.submit(self.do_stream, c, link), 'stream', c.id)
        # whisper pool size follows free cores
        stream_load = 1 if self.active('stream') else 0
        self.asr.target = max(1, min(self.asr.max_workers, self.cores - stream_load - self.kf_busy))
        self.asr.pump(log)

    def on_done(self, fut):
        kind, cid = self.inflight.pop(fut)
        c = self.clips[cid]
        self.last_activity = time.time()
        try:
            res = fut.result()
        except Exception as e:
            err = f'{type(e).__name__}: {e}'
            c.attempts += 1
            c.error = f'{kind}: {err}'
            if kind == 'tail':
                c.status = 'need_tail'
            elif kind == 'stream':
                c.status = 'ready' if (c.moov or c.moov_at_start) else 'need_tail'
                if isinstance(e, stream.NeedMoov):
                    c.status = 'failed'
            else:   # post / kf: not a link problem, a retry would fail the same way
                c.status = 'failed'
                if kind == 'kf':
                    self.kf_busy -= 1
                res = getattr(c, '_res', None)
                if res:
                    try:
                        os.unlink(res['sparse'])
                    except OSError:
                        pass
            if c.attempts >= 4:
                c.status = 'failed'
            self.day.set_state(cid, attempts=c.attempts, error=c.error, status=c.status)
            log(f'{cid}: {kind} FAILED ({err[:220]}) -> {c.status}' +
                (' (will continue with fresh links)' if c.status != 'failed' else ''))
            return
        if kind == 'tail':
            c.t['tail_s'] = round(res['secs'], 2)
            if res['moov']:
                c.moov = res['moov']
            else:
                c.moov_at_start = True   # not in the tail: moov at the front (or a spill for a small file)
            c.status = 'ready'
            self.day.set_state(cid, status='ready', moov_at_start=c.moov_at_start, tail_s=c.t['tail_s'])
        elif kind == 'stream':
            c.t['stream_s'] = round(res['secs'], 1)
            c.status = 'post'
            c.t['kept_MB'] = round(res['kept_bytes'] / 1e6, 1)
            log(f'{cid}: streamed {c.size / 1e9:.2f} GB in {res["secs"]:.0f}s ({c.size / res["secs"] / 1e6:.0f} MB/s), '
                f'kept {res["kept_bytes"] / 1e6:.0f} MB' + (' [spilled whole file]' if res.get('spilled') else ''))
            c._res = res
            self.submit(self.post_ex.submit(self.do_post, c, res), 'post', cid)
        elif kind == 'post':
            c.t['post_s'] = round(res['secs'], 1)
            if res['audio'] and self.asr_on:
                self.asr.add(cid, res['audio'], priority=res['movie_dur'])
            kept = c._res['kept_sync'] or []
            if kept:
                self.kf_busy += 1
                args = (c._res['sparse'], self.day.p('idx', cid + '.moov'), kept, self.day.p('kf', cid))
                self.submit(self.kf_ex.submit(thumbs.worker_thumbnails, args), 'kf', cid)
            else:
                self.finish_clip(c, {'n': 0, 'secs': 0})
        elif kind == 'kf':
            self.kf_busy -= 1
            self.finish_clip(c, res)

    def finish_clip(self, c, kf):
        try:
            os.unlink(c._res['sparse'])
        except OSError:
            pass
        c.t['kf_n'] = kf['n']
        c.t['kf_s'] = kf['secs']
        c.t['done'] = time.time() - self.t_start
        c.status = 'surveyed'
        c._res = None
        self.day.set_state(c.id, surveyed=True, status='surveyed', error=None, timings=c.t)
        log(f'{c.id}: surveyed ({kf["n"]} thumbnails in {kf["secs"]:.0f}s) at +{c.t["done"]:.0f}s')

    # ------------------------------------------------------------------ links running low
    def check_need(self):
        pending = [c for c in self.clips.values() if c.status in ('need_tail', 'ready')]
        need = []
        for c in [c for c in self.ordered() if c in pending]:
            k = (2 if c.status == 'need_tail' else 1) - len(self.pool.fresh(c.path))
            if k > 0:
                need.append((c.path, k))
        runway = sum(1 for c in pending if self.pool.fresh(c.path) and c.status == 'ready') + \
            sum(1 for c in pending if c.status == 'need_tail' and len(self.pool.fresh(c.path)) >= 2)
        path = self.day.p('links', 'NEED.json')
        if not need:
            if os.path.exists(path):
                os.unlink(path)
                self.need_written = None
            return need
        if runway >= self.streams:
            return need
        batch = request_batches(need, per_call=min(MAX_PER_CALL, 2 * self.clips_per_call))[0]
        if self.need_written != batch:
            write_json(path, {'why': f'{len(need)} clip(s) still need links; this is the next call',
                              'expiration_in_sec': 900, 'entries': batch,
                              'save_answer_as': 'DAY/links/<anything>.json (raw tool JSON)',
                              'written': time.strftime('%H:%M:%S')})
            self.need_written = batch
            log(f'NEED LINKS: {len(batch)} entries -> {path}')
        return need

    # ------------------------------------------------------------------ status
    def status_line(self):
        el = time.time() - self.t_start
        n = len(self.clips)
        done = sum(1 for c in self.clips.values() if c.status == 'surveyed')
        failed = [c.id for c in self.clips.values() if c.status == 'failed']
        tr = sum(1 for c in self.clips if os.path.exists(self.day.p('tr', c + '.json')))
        rate = self.bytes_streamed / max(1e-3, el) / 1e6
        return (f'+{el:4.0f}s  streamed {self.bytes_streamed / 1e9:6.1f}/{self.stream_bytes_total / 1e9:.1f} GB '
                f'({rate:.0f} MB/s avg, {self.active("stream")} live) | tails {self.active("tail")} | post {self.active("post")} '
                f'| kf {self.kf_busy} busy | surveyed {done}/{n} | asr {self.asr.busy} busy {len(self.asr.queue)} queued, '
                f'{tr} done | failed {len(failed)} | disk {free_disk(self.day.root) / 1e9:.1f} GB free')

    # ------------------------------------------------------------------ main
    def run(self):
        lockf = open(self.day.p('.ingest.lock'), 'w')
        try:
            fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            log('another ingest is running on this day (DAY/.ingest.lock); not starting a second one')
            return 3
        self.load()
        log(f'ingest {self.day.root}: {len(self.clips)} clips registered, '
            f'{sum(1 for c in self.clips.values() if c.status == "surveyed")} already surveyed, '
            f'{len(self.pool.links)} links known ({len(self.pool.used)} used before)')
        if self.asr_on:
            self.asr.target = 2
            self.asr.start_worker()   # warm up while the first bytes arrive
        last_status = 0
        try:
            while True:
                self.refresh_links()
                for fut in [f for f in list(self.inflight) if f.done()]:
                    self.on_done(fut)
                self.schedule()
                need = self.check_need()
                now = time.time()
                if now - last_status > 15:
                    log(self.status_line())
                    last_status = now
                busy = bool(self.inflight) or not self.asr.idle()
                open_clips = [c for c in self.clips.values() if c.status not in ('surveyed', 'failed')]
                if not busy and not open_clips:
                    break
                if not busy and open_clips and need and now - self.last_activity > self.wait_links:
                    log(f'no links for {len(open_clips)} clip(s) after waiting {self.wait_links}s; stopping. '
                        f'Request DAY/links/NEED.json and run ingest again.')
                    break
                time.sleep(0.25 if self.inflight else 1.0)
        except KeyboardInterrupt:
            log('interrupted; state is saved, re-run to continue')
            self.stop.set()
        finally:
            self.asr.pump(log)
            self.asr.stop()
            self.kf_ex.shutdown(wait=False, cancel_futures=True)
            for ex in (self.tail_ex, self.stream_ex, self.post_ex):
                ex.shutdown(wait=False, cancel_futures=True)
        return self.report()

    def report(self):
        el = time.time() - self.t_start
        rows = {}
        for c in self.clips.values():
            rows[c.id] = {'status': c.status, 'size': c.size, 'error': c.error, **c.t,
                          'transcribed': os.path.exists(self.day.p('tr', c.id + '.json'))}
            if c.id in self.asr.results:
                rows[c.id]['asr'] = self.asr.results[c.id]
        failed = {k: v['error'] for k, v in rows.items() if v['status'] == 'failed' or (v['status'] != 'surveyed')}
        rep = {'wall_s': round(el, 1), 'streamed_GB': round(self.bytes_streamed / 1e9, 2),
               'avg_MBps': round(self.bytes_streamed / max(el, 1e-3) / 1e6, 1), 'clips': rows,
               'not_done': failed, 'asr_errors': self.asr.errors}
        write_json(self.day.p('logs', 'ingest_report.json'), rep)
        log(self.status_line())
        log(f'ingest finished in {el:.0f}s: {sum(1 for r in rows.values() if r["status"] == "surveyed")}/{len(rows)} surveyed, '
            f'{sum(1 for r in rows.values() if r["transcribed"])} transcribed; not done: {sorted(failed) or "none"}')
        for k, v in sorted(failed.items()):
            log(f'  {k}: {v}')
        return 0 if not failed and not self.asr.errors else 1


def plan_links(day_root, clip_entries, clips_per_call=12, big_first=2):
    """Register clips and write DAY/links/request.json: batches of <=25 entries, 2 per clip, in stream order."""
    from .links import write_request
    day = Day(day_root)
    reg = day.register(clip_entries)
    todo = []
    for cid, rec in stream_order(list(reg.items()), lambda kv: kv[1].get('size'), big_first):
        st = day.state(cid)
        if st.get('surveyed'):
            continue
        k = 1 if os.path.exists(day.p('idx', cid + '.moov')) or st.get('moov_at_start') else 2
        todo.append((rec['path'], k))
    batches = request_batches(todo, per_call=min(MAX_PER_CALL, 2 * clips_per_call))
    obj = write_request(day.p('links'), batches,
                        note='Call download_link once per batch with these entries (expiration_in_sec 900) and save each '
                             'raw answer as DAY/links/batch_NN.json. Ingest reads them as they appear.')
    return reg, obj
