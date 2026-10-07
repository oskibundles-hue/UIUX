#!/usr/bin/env python3
"""End-to-end ingest against the local single-use link server, playing the parent's part.

  test_ingest.py WORKDIR functional   real DJI clips + a faststart .MOV, 2 clips per link call so the NEED
                                      flow runs, one link pre-burnt so a failure and its recovery run too,
                                      whisper on
  test_ingest.py WORKDIR throughput BIGFILE [N]   N copies (default 5) of a big file, whisper off: filter +
                                      thumbnail throughput and CPU cost per GB
"""
import json
import os
import resource
import subprocess
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
sys.path.insert(0, ENGINE)
from rangeserver import RangeServer  # noqa: E402

S = os.environ.get('S', '/tmp/claude-0/-home-user-UIUX/2e2fc1bb-c45d-5ce1-ba97-afbf7647f193/scratchpad')


def tool_answer(srv, files, entries):
    """What the Dropbox download_link tool returns for `entries` (paths), with local single-use URLs."""
    out = []
    for p in entries:
        local = files[p]
        out.append({'download_url': srv.link(local), 'expiration_in_sec': 900, 'path': 'ns:1//' + p.lstrip('/'),
                    'path_display': p, 'name': os.path.basename(p), 'id': 'id:x', 'size': os.path.getsize(local),
                    'content_hash': '', 'mime_type': 'video/mp4'})
    return {'entries': out}


def parent(srv, day, files, stop, burn_first=None, delay=2.0, log=None):
    """Answer NEED.json like the parent would: call the tool, save the raw JSON as links/<n>.json."""
    k = 100
    while not stop.is_set():
        need = os.path.join(day, 'links', 'NEED.json')
        if os.path.exists(need):
            try:
                req = json.load(open(need))
            except ValueError:
                time.sleep(0.2)
                continue
            time.sleep(delay)   # the parent takes a moment
            ans = tool_answer(srv, files, req['entries'])
            if burn_first is not None and burn_first[0]:
                # consume one link before ingest sees it: its request will get 410 Gone
                urllib.request.urlopen(ans['entries'][0]['download_url']).read()
                burn_first[0] = False
                if log is not None:
                    log.append('burnt ' + ans['entries'][0]['path_display'])
            k += 1
            tmp = os.path.join(day, 'links', f'.batch_{k}.tmp')
            json.dump(ans, open(tmp, 'w'))
            os.replace(tmp, os.path.join(day, 'links', f'batch_{k}.json'))
            while os.path.exists(need) and not stop.is_set():
                try:
                    if json.load(open(need))['entries'] != req['entries']:
                        break
                except (ValueError, FileNotFoundError):
                    break
                time.sleep(0.2)
        time.sleep(0.2)


def run_ingest(day, extra):
    t0 = time.time()
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    p = subprocess.run([sys.executable, os.path.join(ENGINE, 'vlog.py'), 'ingest', day] + extra,
                       capture_output=True, text=True)
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    wall = time.time() - t0
    cpu = (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime)
    return p, wall, cpu


def functional(work):
    day = os.path.join(work, 'day_functional')
    subprocess.run(['rm', '-rf', day])
    src = os.path.join(work, 'src')
    os.makedirs(src, exist_ok=True)
    files = {
        '/raw footage/2026-09-15/DJI_20260915224027_0027_D.MP4': f'{S}/raw/keep/DJI_0027.MP4',
        '/raw footage/2026-09-15/DJI_20260915224905_0029_D.MP4': f'{S}/raw/keep/DJI_0029.MP4',
        '/Mobile Uploads/2026-09-15/2026-09-15 21.40.17 (IMG_9942).MOV': os.path.join(work, 'fs_0027.MOV'),
    }
    clips = os.path.join(work, 'clips_functional.txt')
    with open(clips, 'w') as f:
        for p, l in files.items():
            f.write(f'{p}\t{os.path.getsize(l)}\n')
    subprocess.run([sys.executable, os.path.join(ENGINE, 'vlog.py'), 'links', day, '--clips', clips,
                    '--clips-per-call', '1'], check=True)
    req = json.load(open(os.path.join(day, 'links', 'request.json')))
    srv = RangeServer()
    stop = threading.Event()
    # the parent answers the first call right away; ingest asks for the rest via NEED.json
    ans = tool_answer(srv, files, req['batches'][0]['entries'])
    json.dump(ans, open(os.path.join(day, 'links', 'batch_01.json'), 'w'))
    notes = []
    th = threading.Thread(target=parent, args=(srv, day, files, stop, [True], 1.0, notes), daemon=True)
    th.start()
    p, wall, cpu = run_ingest(day, ['--clips-per-call', '1', '--wait-links', '60'])
    stop.set()
    print(p.stdout[-6000:])
    print(p.stderr[-3000:])
    print('parent notes:', notes)
    rep = json.load(open(os.path.join(day, 'logs', 'ingest_report.json')))
    tok = srv.httpd.tokens
    codes = {}
    for x in srv.log:
        codes[x[2]] = codes.get(x[2], 0) + 1
    print('server: requests by status', codes, '| links issued but never used:', len(tok))
    ok = all(v['status'] == 'surveyed' and v['transcribed'] for v in rep['clips'].values())
    for cid, v in rep['clips'].items():
        kf = len([f for f in os.listdir(os.path.join(day, 'kf', cid)) if f.endswith('.jpg')])
        print(cid, v['status'], 'tr' if v['transcribed'] else '--', 'kf', kf,
              {k: v.get(k) for k in ('tail_s', 'stream_s', 'post_s', 'kf_s', 'kept_MB', 'done', 'asr')})
    print('sparse dir empty:', os.listdir(os.path.join(day, 'sparse')) == [])
    print(f'wall {wall:.1f}s, cpu {cpu:.1f}s', 'FUNCTIONAL OK' if ok else 'FUNCTIONAL FAILED')
    srv.stop()
    return ok


def throughput(work, big, n=5, extra=()):
    day = os.path.join(work, 'day_throughput')
    subprocess.run(['rm', '-rf', day])
    files = {f'/raw footage/2026-09-16/DJI_202609161{i:01d}0000_{90 + i:04d}_D.MP4': big for i in range(n)}
    clips = os.path.join(work, 'clips_throughput.txt')
    with open(clips, 'w') as f:
        for p, l in files.items():
            f.write(f'{p}\t{os.path.getsize(l)}\n')
    subprocess.run([sys.executable, os.path.join(ENGINE, 'vlog.py'), 'links', day, '--clips', clips], check=True,
                   capture_output=True)
    req = json.load(open(os.path.join(day, 'links', 'request.json')))
    srv = RangeServer()
    for b in req['batches']:
        json.dump(tool_answer(srv, files, b['entries']), open(os.path.join(day, 'links', f'batch_{b["batch"]:02d}.json'), 'w'))
    p, wall, cpu = run_ingest(day, ['--no-asr'] + list(extra))
    print(p.stdout[-4000:])
    rep = json.load(open(os.path.join(day, 'logs', 'ingest_report.json')))
    gb = sum(v['size'] for v in rep['clips'].values()) / 1e9
    print(f'{n} x {os.path.getsize(big) / 1e9:.2f} GB = {gb:.1f} GB in {wall:.1f}s wall -> {gb * 1000 / wall:.0f} MB/s; '
          f'CPU (ingest + ffmpeg + curl + thumbnail workers) {cpu:.1f}s = {cpu / gb:.2f} core-s per GB')
    for cid, v in sorted(rep['clips'].items()):
        print(cid, {k: v.get(k) for k in ('stream_s', 'post_s', 'kf_n', 'kf_s', 'kept_MB', 'done')})
    srv.stop()


if __name__ == '__main__':
    work = sys.argv[1]
    what = sys.argv[2]
    if what == 'functional':
        sys.exit(0 if functional(work) else 1)
    else:
        throughput(work, sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 5, sys.argv[5:])
