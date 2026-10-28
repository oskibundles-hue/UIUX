#!/usr/bin/env python3
"""plan + fetch against the local single-use link server, on a day surveyed by test_ingest.py throughput.

usage: test_fetch.py DAY BIGFILE MEZZ_OUT
Writes a small EDL (shots, dialog merged into a shot, a nat-audio piece, a keyframe timelapse), plans it,
answers the link request with local links, fetches + cuts, then re-cuts one range from the full original
with the same command and checks the video frames are identical (the spans hold everything the cut needs).
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
sys.path.insert(0, ENGINE)
sys.path.insert(0, HERE)
from rangeserver import RangeServer  # noqa: E402
from test_ingest import tool_answer  # noqa: E402
from lib import fetch, mp4  # noqa: E402
from lib.common import FF, read_json  # noqa: E402


def main():
    day, big, mezz = sys.argv[1:4]
    edl = {'shots': [{'src': '0090', 'in': 10.0, 'out': 13.0, 'speed': 1.0},
                     {'src': '0091', 'in': 50.2, 'out': 52.7, 'speed': 1.0},
                     {'src': '0092', 'in': 100.0, 'out': 102.0, 'speed': 1.0},
                     {'src': '0094', 'in': 0.0, 'out': 60.0, 'speed': 'keyframes'}],
           'dialog': [{'src': '0090', 'in': 11.0, 'out': 12.5}],
           'audio_extra': [{'src': '0093', 'in': 30.0, 'out': 32.0, 'kind': 'nat'}]}
    ep = os.path.join(day, 'test_edl.json')
    json.dump(edl, open(ep, 'w'))
    subprocess.run(['rm', '-rf', os.path.join(day, 'fetch'), mezz])
    t = time.time()
    subprocess.run([sys.executable, os.path.join(ENGINE, 'vlog.py'), 'plan', day, '--edl', ep], check=True)
    print(f'plan {time.time() - t:.1f}s')
    req = json.load(open(os.path.join(day, 'fetch', 'request.json')))
    srv = RangeServer()
    files = {p: big for b in req['batches'] for p in b['entries']}
    for b in req['batches']:
        json.dump(tool_answer(srv, files, b['entries']), open(os.path.join(day, 'fetch', 'links', f'b{b["batch"]}.json'), 'w'))
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join(ENGINE, 'vlog.py'), 'fetch', day, '--out', mezz], capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-2000:])
    print(f'fetch+cut wall {time.time() - t:.1f}s')
    plan = json.load(open(os.path.join(day, 'fetch', 'fetchplan.json')))
    ok = r.returncode == 0
    for j in plan['jobs']:
        p = os.path.join(mezz, j['out'])
        info = subprocess.run([FF, '-hide_banner', '-i', p], capture_output=True, text=True).stderr
        dur = [x.strip() for x in info.splitlines() if 'Duration' in x]
        vid = [x.strip()[:110] for x in info.splitlines() if 'Video:' in x]
        print(j['out'], dur[0][:24] if dur else 'MISSING', vid[0] if vid else '')
        ok &= bool(dur)
    # identity: the same cut from the full original
    j = [j for j in plan['jobs'] if j['kind'] == 'range'][0]
    meta = read_json(os.path.join(day, 'idx', j['src'] + '.json'))
    movie = mp4.parse_moov(open(os.path.join(day, 'idx', j['src'] + '.moov'), 'rb').read())
    ref_dir = os.path.join(mezz, 'ref')
    os.makedirs(ref_dir, exist_ok=True)
    fetch.cut_range(big, j, meta, movie, ref_dir, 13, 'superfast')

    def md5s(p):
        return subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-i', p, '-map', '0:v:0', '-f', 'framemd5', '-'],
                              capture_output=True, text=True).stdout.split('\n', 8)[-1]
    same = md5s(os.path.join(mezz, j['out'])) == md5s(os.path.join(ref_dir, j['out']))
    print(f"{j['out']}: frames from the sparse file == frames from the full original: {same}")
    ok &= same
    print('FETCH OK' if ok else 'FETCH FAILED')
    srv.stop()


if __name__ == '__main__':
    main()
