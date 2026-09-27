"""dense.py -- optical-flow in-betweens for the roof shot (S1, source f0-67), so its 0.3-0.55x slow motion
does not ghost the moving roof edges. ffmpeg minterpolate (mci / aobmc / bidir) at FACTOR x on the
frame-exact decode (.work/src.npy), written to .work/dense_roof.npy: dense index d = (p - F0) * FACTOR.

    python3 lib/dense.py [--ffmpeg ffmpeg]
"""
import argparse, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '..', '.work')
F0, F1, FACTOR = 0, 67, 4


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', 'ffmpeg'))
    a = ap.parse_args()
    src = np.load(os.path.join(WORK, 'src.npy'), mmap_mode='r')
    n_out = (F1 - F0) * FACTOR + 1
    out = np.lib.format.open_memmap(os.path.join(WORK, 'dense_roof.tmp.npy'), mode='w+', dtype=np.uint8,
                                    shape=(n_out, 1920, 1080, 3))
    fps = '24000/1001'
    cmd = [a.ffmpeg, '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', fps, '-i', '-',
           '-vf', f'minterpolate=fps={FACTOR * 24000}/1001:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    import threading
    def feed():
        for f in range(F0, F1 + 1):
            p.stdin.write(np.ascontiguousarray(src[f]).tobytes())
        p.stdin.close()
    th = threading.Thread(target=feed); th.start()
    fb = 1920 * 1080 * 3; k = 0
    while k < n_out:
        b = p.stdout.read(fb)
        if len(b) < fb:
            break
        out[k] = np.frombuffer(b, np.uint8).reshape(1920, 1080, 3); k += 1
    th.join(); p.wait()
    # minterpolate stops a few in-betweens short of the last input frame (265 of 269 here): keep what came
    # back; the edit only reaches source f64 (dense index 256)
    assert k >= (F1 - 3 - F0) * FACTOR, (k, n_out)
    # minterpolate keeps the originals on the grid; check the anchors match the decode
    for f in (F0, (F0 + F1) // 2, F0 + (k - 1) // FACTOR):
        d = np.abs(out[(f - F0) * FACTOR].astype(np.int16) - src[f].astype(np.int16)).mean()
        assert d < 1.0, ('dense anchor mismatch', f, d)
    out.flush()
    np.save(os.path.join(WORK, 'dense_roof.npy'), out[:k])
    del out
    os.remove(os.path.join(WORK, 'dense_roof.tmp.npy'))
    print('dense roof frames', k)


if __name__ == '__main__':
    main()
