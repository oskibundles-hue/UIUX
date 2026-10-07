#!/usr/bin/env python3
"""track_mid.py -- run lib/track.py from an anchor frame in the MIDDLE of a shot, both ways.

track.py tracks forward from the box on f0. Many vlog targets are only sharp mid-shot (a whip or a
walk-in blurs the ends), so this wrapper tracks anchor->f1 and anchor->f0 (reversed) with the same
template tracker, runs each pass's own forward/backward check, and joins them into one entry of the
same JSON format track.py writes (frames ordered f0..f1).

  python3 lib/track_mid.py --video V --ffmpeg FF --name urusR --f0 236 --f1 300 --anchor 270 \
      --box 100,1010,440,240 [--scale-pen 0.2] --out lib/data/tracks.json
"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import track as T


def run_dir(frames, box, **kw):
    fwd = T.run(frames, box, **kw)
    bwd = T.run(frames[::-1], tuple(fwd[-1, :4]), **kw)[::-1]
    return fwd, bwd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True); ap.add_argument('--ffmpeg', default='ffmpeg')
    ap.add_argument('--name', required=True)
    ap.add_argument('--f0', type=int, required=True); ap.add_argument('--f1', type=int, required=True)
    ap.add_argument('--anchor', type=int, required=True)
    ap.add_argument('--box', required=True, help='x,y,w,h full-res px on the ANCHOR frame')
    ap.add_argument('--scale-pen', type=float, default=0.0)
    ap.add_argument('--half', type=int, default=4)
    ap.add_argument('--ds', type=int, default=2)
    ap.add_argument('--out', default='tracks.json')
    a = ap.parse_args()
    ds = a.ds
    frames, (W, H) = T.decode_gray(a.video, a.ffmpeg, a.f0, a.f1, ds)
    x, y, w, h = [float(v) / ds for v in a.box.split(',')]
    box = (x + w / 2, y + h / 2, w, h)
    k = a.anchor - a.f0
    kw = dict(scale_pen=a.scale_pen)
    fa, ba = run_dir(frames[k:], box, **kw)                 # anchor -> f1
    fb, bb = run_dir(frames[:k + 1][::-1], box, **kw)       # anchor -> f0 (reversed time)
    fwd = np.concatenate([fb[::-1][:-1], fa]); bwd = np.concatenate([bb[::-1][:-1], ba])
    diag = np.hypot(fwd[:, 2], fwd[:, 3])
    fbe = np.hypot(fwd[:, 0] - bwd[:, 0], fwd[:, 1] - bwd[:, 1]) / diag
    conf = np.clip(fwd[:, 4], 0, 1) * (0.5 + 0.5 * np.exp(-(fbe / 0.05) ** 2))
    cx, cy = fwd[:, 0] * ds, fwd[:, 1] * ds
    lw, lh = np.log(fwd[:, 2] * ds), np.log(fwd[:, 3] * ds)
    wt = 0.05 + conf
    scx, scy = T.smooth_series(cx, wt, a.half), T.smooth_series(cy, wt, a.half)
    slw, slh = np.exp(T.smooth_series(lw, wt, a.half)), np.exp(T.smooth_series(lh, wt, a.half))
    fr = []
    for i in range(len(fwd)):
        f = a.f0 + i
        fr.append(dict(f=f, t=round(f / T.FPS, 5), x=round(scx[i] - slw[i] / 2, 2), y=round(scy[i] - slh[i] / 2, 2),
                       w=round(slw[i], 2), h=round(slh[i], 2), conf=round(float(conf[i]), 3),
                       ncc=round(float(fwd[i, 4]), 3), fb=round(float(fbe[i]), 4)))
    res = dict(video=os.path.basename(a.video), fps=T.FPS, size=[W, H], f0=a.f0, f1=a.f1, anchor=a.anchor,
               method='template-mid', t0=round(a.f0 / T.FPS, 5), t1=round((a.f1 + 1) / T.FPS, 5), frames=fr)
    db = json.load(open(a.out)) if os.path.exists(a.out) else {}
    db[a.name] = res
    json.dump(db, open(a.out, 'w'), indent=1)
    c = [f['conf'] for f in fr]; e = [f['fb'] for f in fr]
    print(f"{a.name}: {len(c)} frames  conf min {min(c):.2f} mean {np.mean(c):.2f}  FB err max {max(e)*100:.1f}% of diag")


if __name__ == '__main__':
    main()
