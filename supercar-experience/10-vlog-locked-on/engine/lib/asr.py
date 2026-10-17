"""faster-whisper workers (separate processes, one model each) fed by the ingest scheduler or `vlog.py transcribe`.

Settings match the approved Sep 15 run: small.en, CPU int8, VAD on, beam 1, word timestamps, no conditioning on
previous text. Measured here: 1 thread per worker is the most CPU-efficient (150 s of dense speech: 23.4 s on
1 thread, 16.5 s on 2, 18.2 s on 4), so the scheduler runs several 1-thread workers and adds workers as the
download and thumbnail work frees cores. Batched inference was faster but dropped ~17% of the words: not used.

Outputs tr/<id>.json (segments with word timings, same schema as Sep 15) and tr/<id>.txt, written atomically.
"""
import json
import multiprocessing as mp
import os
import time
import traceback

MODEL = 'small.en'


def _fmt(t):
    return f'{int(t // 60):02d}:{t % 60:04.1f}'


def transcribe_file(model, audio_path, cid, out_dir):
    segs, info = model.transcribe(audio_path, language='en', vad_filter=True, beam_size=1, word_timestamps=True,
                                  condition_on_previous_text=False)
    out = []
    for s in segs:
        out.append({'start': round(s.start, 2), 'end': round(s.end, 2), 'text': s.text.strip(),
                    'avg_logprob': round(s.avg_logprob, 3), 'no_speech': round(s.no_speech_prob, 3),
                    'words': [[round(w.start, 2), round(w.end, 2), w.word, round(w.probability, 3)] for w in (s.words or [])]})
    obj = {'id': cid, 'duration': info.duration, 'model': MODEL, 'segments': out}
    js = os.path.join(out_dir, cid + '.json')
    tx = os.path.join(out_dir, cid + '.txt')
    with open(tx + '.tmp', 'w') as f:
        for s in out:
            f.write(f"[{_fmt(s['start'])}-{_fmt(s['end'])}] {s['text']}\n")
    os.replace(tx + '.tmp', tx)
    with open(js + '.tmp', 'w') as f:
        json.dump(obj, f)
    os.replace(js + '.tmp', js)   # the .json appearing is the "done" signal
    return info.duration, len(out)


def worker_main(wid, inq, outq, model_name, threads):
    os.environ.setdefault('OMP_NUM_THREADS', str(threads))
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device='cpu', compute_type='int8', cpu_threads=threads)
    except Exception as e:  # pragma: no cover
        outq.put(('dead', wid, None, repr(e)))
        return
    outq.put(('ready', wid, None, None))
    while True:
        job = inq.get()
        if job is None:
            break
        cid, audio_path, out_dir = job
        t0 = time.time()
        try:
            dur, n = transcribe_file(model, audio_path, cid, out_dir)
            outq.put(('done', wid, cid, {'secs': round(time.time() - t0, 1), 'audio_s': round(dur, 1), 'segments': n}))
        except Exception as e:
            outq.put(('error', wid, cid, repr(e) + ' ' + traceback.format_exc()[-300:]))


class AsrPool:
    """Lazily started worker processes; the caller decides how many may be busy at once (`target`)."""

    def __init__(self, out_dir, max_workers=4, threads=1, model=MODEL):
        self.ctx = mp.get_context('spawn')
        self.outq = self.ctx.Queue()
        self.out_dir = out_dir
        self.max_workers = max_workers
        self.threads = threads
        self.model = model
        self.workers = {}     # wid -> {'p', 'q', 'busy': cid|None, 'ready': bool, 't0'}
        self.queue = []       # [(priority, cid, path)]
        self.attempts = {}
        self.results = {}
        self.errors = {}
        self.paths = {}
        self.target = 1

    def start_worker(self):
        wid = len(self.workers)
        q = self.ctx.Queue()
        p = self.ctx.Process(target=worker_main, args=(wid, q, self.outq, self.model, self.threads), daemon=True)
        p.start()
        self.workers[wid] = {'p': p, 'q': q, 'busy': None, 'ready': False, 't0': None}

    def add(self, cid, path, priority=0.0):
        if any(c == cid for _, c, _ in self.queue) or any(w['busy'] == cid for w in self.workers.values()):
            return
        self.queue.append((priority, cid, path))
        self.queue.sort(key=lambda x: -x[0])

    @property
    def busy(self):
        return sum(1 for w in self.workers.values() if w['busy'])

    def pump(self, log=None):
        # collect results
        while True:
            try:
                kind, wid, cid, info = self.outq.get_nowait()
            except Exception:
                break
            w = self.workers.get(wid)
            if kind == 'ready':
                w['ready'] = True
            elif kind == 'dead':
                self.errors['worker%d' % wid] = info
                w['dead'] = True
            elif kind == 'done':
                w['busy'] = None
                self.results[cid] = info
                if log:
                    log(f'asr {cid}: {info["audio_s"]:.0f}s audio in {info["secs"]:.0f}s, {info["segments"]} segments')
            elif kind == 'error':
                w['busy'] = None
                n = self.attempts.get(cid, 0)
                if n < 3:
                    self.queue.append((-1e9 + n, cid, self.paths[cid]))  # retry last
                    if log:
                        log(f'asr {cid}: error (attempt {n}), will retry: {info[:160]}')
                else:
                    self.errors[cid] = info
                    if log:
                        log(f'asr {cid}: FAILED after {n} attempts: {info[:200]}')
        # start workers while there is queued work and room under the target
        live = [w for w in self.workers.values() if not w.get('dead')]
        want = min(self.max_workers, max(0, self.target))
        if self.queue and len(live) < want:
            self.start_worker()
        # dispatch
        for wid, w in self.workers.items():
            if not self.queue or self.busy >= self.target:
                break
            if w['ready'] and not w['busy'] and not w.get('dead'):
                pr, cid, path = self.queue.pop(0)
                if not os.path.exists(path):
                    continue
                self.attempts[cid] = self.attempts.get(cid, 0) + 1
                self.paths[cid] = path
                w['busy'] = cid
                w['q'].put((cid, path, self.out_dir))

    def idle(self):
        return not self.queue and self.busy == 0

    def stop(self):
        for w in self.workers.values():
            try:
                w['q'].put(None)
            except Exception:
                pass
        for w in self.workers.values():
            w['p'].join(timeout=5)
            if w['p'].is_alive():
                w['p'].terminate()
