"""dense.py -- optical-flow in-betweens for every shot that plays at a non-integer speed, so slow motion and
ramps never show a two-frame double exposure (review r1: a linear blend at 0.5x strobed the hook's headlight
strip into two bars on every other frame). ffmpeg minterpolate (mci / aobmc / bidir, scene-change detection
off) at FACTOR x, one pass PER SHOT so it never interpolates across a cut, on the frame-exact decode
(.work/src.npy). Each shot's last frame is fed twice more so the in-betweens reach it (minterpolate stops a
few short of the last input). Output: .work/dense_<f0>_<f1>.npy, dense index d = (p - f0) * FACTOR.

    python3 lib/dense.py [--ffmpeg ffmpeg]
"""
import argparse
import os
import subprocess
import threading

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '..', '.work')
FACTOR = 4
# (first, last) source frame of each shot that plays at a non-integer speed (see lib/edl.py)
RANGES = [(0, 67), (380, 392), (204, 225), (173, 203), (369, 379), (79, 95)]


def path(f0, f1):
    return os.path.join(WORK, f'dense_{f0}_{f1}.npy')


def make(ff, src, f0, f1):
    n_out = (f1 - f0) * FACTOR + 1
    cmd = [ff, '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '24000/1001', '-i', '-',
           '-vf', f'minterpolate=fps={FACTOR * 24000}/1001:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=none',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def feed():
        for f in list(range(f0, f1 + 1)) + [f1, f1]:
            p.stdin.write(np.ascontiguousarray(src[f]).tobytes())
        p.stdin.close()
    th = threading.Thread(target=feed)
    th.start()
    tmp = path(f0, f1) + '.tmp.npy'
    out = np.lib.format.open_memmap(tmp, mode='w+', dtype=np.uint8, shape=(n_out, 1920, 1080, 3))
    fb = 1920 * 1080 * 3
    k = 0
    while k < n_out:
        b = p.stdout.read(fb)
        if len(b) < fb:
            break
        out[k] = np.frombuffer(b, np.uint8).reshape(1920, 1080, 3)
        k += 1
    p.stdout.close()
    th.join()
    p.wait()
    assert k == n_out, (f0, f1, k, n_out)
    for f in (f0, (f0 + f1) // 2, f1):                 # minterpolate keeps the originals on the grid
        d = np.abs(out[(f - f0) * FACTOR].astype(np.int16) - src[f].astype(np.int16)).mean()
        assert d < 1.0, ('dense anchor mismatch', f0, f1, f, d)
    out.flush()
    del out
    os.replace(tmp, path(f0, f1))
    print(f'dense {f0}-{f1}: {n_out} frames', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', 'ffmpeg'))
    a = ap.parse_args()
    src = np.load(os.path.join(WORK, 'src.npy'), mmap_mode='r')
    todo = [r for r in RANGES if not os.path.exists(path(*r))]
    ths = []
    for r in todo:                                     # three passes at a time (minterpolate is single-threaded)
        th = threading.Thread(target=make, args=(a.ffmpeg, src, *r))
        th.start()
        ths.append(th)
        if len(ths) >= 3:
            ths.pop(0).join()
    for th in ths:
        th.join()


if __name__ == '__main__':
    main()
