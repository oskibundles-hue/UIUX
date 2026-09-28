"""track_npy.py -- run track.py (the approved numpy template tracker) on the frame-exact 1080x1920 decode
in .work/src.npy instead of re-decoding the 4K .mov. Boxes are in 1080x1920 px.

    python3 lib/track_npy.py --name badge --f0 204 --f1 225 --box 446,1321,224,219 [--scale-pen 0.3]
"""
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import track  # noqa: E402

SRC = os.path.join(HERE, '..', '.work', 'src.npy')


def decode_gray_npy(video, ffmpeg, f0, f1, ds=2):
    src = np.load(SRC, mmap_mode='r')
    fr = []
    for f in range(f0, f1 + 1):
        x = src[f].astype(np.float32) / 255.0
        g = x[..., 0] * 0.2126 + x[..., 1] * 0.7152 + x[..., 2] * 0.0722
        h, w = g.shape[0] // ds * ds, g.shape[1] // ds * ds
        g = g[:h, :w].reshape(h // ds, ds, w // ds, ds).mean((1, 3))
        fr.append(g)
    return np.stack(fr).astype(np.float32), (1080, 1920)


track.decode_gray = decode_gray_npy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--f0', type=int, required=True); ap.add_argument('--f1', type=int, required=True)
    ap.add_argument('--box', required=True)
    ap.add_argument('--aspect', action='store_true')
    ap.add_argument('--scale-pen', type=float, default=0.0)
    ap.add_argument('--half', type=int, default=4)
    ap.add_argument('--out', default=os.path.join(HERE, 'data', 'tracks.json'))
    a = ap.parse_args()
    box = [float(v) for v in a.box.split(',')]
    res = track.track_shot('SCE_McLaren-750S_no-branding.mov', None, a.f0, a.f1, box, aspect=a.aspect, half=a.half,
                           scale_pen=a.scale_pen)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    db = json.load(open(a.out)) if os.path.exists(a.out) else {}
    db[a.name] = res
    json.dump(db, open(a.out, 'w'), indent=1)
    c = [f['conf'] for f in res['frames']]; fb = [f['fb'] for f in res['frames']]
    print(f"{a.name}: {len(c)} frames  conf min {min(c):.2f} mean {np.mean(c):.2f}  FB err max {max(fb) * 100:.1f}% of diag")


if __name__ == '__main__':
    main()
