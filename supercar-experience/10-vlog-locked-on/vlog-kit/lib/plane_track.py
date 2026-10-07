#!/usr/bin/env python3
"""plane_track.py -- planar (homography) track of a surface on the car, for the C5 surface lock.

Features (Shi-Tomasi) inside the surface polygon AND the car's Vision matte, tracked frame to frame with pyramidal
Lucas-Kanade and a forward-backward check; each step's homography comes from RANSAC and is chained out from the
anchor frame in both directions. Points are re-seeded every frame inside the current (tracked) polygon, so the track
does not starve as features leave. The quad is smoothed with a centred Gaussian over time (sigma in frames).

  python3 plane_track.py --frames DIR --mattes DIR --f0 280 --f1 332 --anchor 308 \
      --quad 455,1062,690,1035,690,1190,455,1232 --out plane.json --name urusSide [--qa qa.jpg]
"""
import argparse, glob, json, os
import cv2, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--frames'); ap.add_argument('--mattes'); ap.add_argument('--f0', type=int); ap.add_argument('--f1', type=int)
ap.add_argument('--anchor', type=int); ap.add_argument('--quad'); ap.add_argument('--region', default=None)
ap.add_argument('--out'); ap.add_argument('--name'); ap.add_argument('--qa'); ap.add_argument('--sigma', type=float, default=1.6)
ap.add_argument('--fps', default='60000/1001')
a = ap.parse_args()
Q0 = np.array([float(v) for v in a.quad.split(',')], np.float32).reshape(4, 2)
REG0 = np.array([float(v) for v in a.region.split(',')], np.float32).reshape(-1, 2) if a.region else Q0

def gray(f): return cv2.imread(os.path.join(a.frames, f'{f:04d}.jpg'), cv2.IMREAD_GRAYSCALE)
def matte(f):
    js = os.path.join(a.mattes, f'{f:04d}.json')
    if not os.path.exists(js): return None
    best = None
    for i in json.load(open(js))['instances']:
        m = cv2.imread(os.path.join(a.mattes, i['file']), cv2.IMREAD_GRAYSCALE)
        if best is None or m.sum() > best.sum(): best = m
    return best

def step_h(fa, fb, poly):
    """homography taking frame fa -> fb, from features in poly (frame fa coords) inside the car matte."""
    ga, gb = gray(fa), gray(fb)
    mask = np.zeros_like(ga); cv2.fillPoly(mask, [poly.astype(np.int32)], 255)
    m = matte(fa)
    if m is not None: mask = cv2.bitwise_and(mask, (m > 100).astype(np.uint8) * 255)
    mask = cv2.erode(mask, np.ones((9, 9), np.uint8))
    p0 = cv2.goodFeaturesToTrack(ga, 400, 0.004, 6, mask=mask, blockSize=7)
    if p0 is None or len(p0) < 8: raise SystemExit(f'too few features at {fa}')
    lk = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))
    p1, st, _ = cv2.calcOpticalFlowPyrLK(ga, gb, p0, None, **lk)
    pb, st2, _ = cv2.calcOpticalFlowPyrLK(gb, ga, p1, None, **lk)
    fb_err = np.linalg.norm(p0 - pb, axis=2).ravel()
    ok = (st.ravel() == 1) & (st2.ravel() == 1) & (fb_err < 1.0)
    H, inl = cv2.findHomography(p0[ok], p1[ok], cv2.RANSAC, 2.0)
    return H, int(ok.sum()), int(inl.sum()) if inl is not None else 0

frames = list(range(a.f0, a.f1 + 1))
Hs = {a.anchor: np.eye(3)}
stats = {}
for direction in (1, -1):
    f = a.anchor; H = np.eye(3)
    while a.f0 <= f + direction <= a.f1:
        poly = cv2.perspectiveTransform(REG0[None], H)[0]
        Hstep, n, ni = step_h(f, f + direction, poly)
        H = Hstep @ H; f += direction; Hs[f] = H; stats[f] = (n, ni)
quads = np.array([cv2.perspectiveTransform(Q0[None], Hs[f])[0] for f in frames])      # (N, 4, 2)
# temporal smoothing (Gaussian, edge-padded)
if a.sigma > 0:
    r = int(3 * a.sigma); k = np.exp(-0.5 * (np.arange(-r, r + 1) / a.sigma) ** 2); k /= k.sum()
    pad = np.concatenate([quads[:1].repeat(r, 0), quads, quads[-1:].repeat(r, 0)])
    quads = np.stack([np.tensordot(k, pad[i:i + 2 * r + 1], axes=(0, 0)) for i in range(len(frames))])
out = json.load(open(a.out)) if os.path.exists(a.out) else {}
num, den = (int(v) for v in a.fps.split('/'))
out[a.name] = {'f0': a.f0, 'fps': num / den, 'anchor': a.anchor, 'quad0': Q0.round(2).tolist(),
               'frames': [[round(float(v), 2) for v in q.ravel()] for q in quads],
               'inliers': [stats.get(f, (0, 0))[1] for f in frames]}
json.dump(out, open(a.out, 'w'))
print(a.name, len(frames), 'frames; inliers min', min(v[1] for v in stats.values()), 'median', int(np.median([v[1] for v in stats.values()])))
if a.qa:
    pick = frames[:: max(1, len(frames) // 8)][:8]
    tiles = []
    for f in pick:
        im = cv2.imread(os.path.join(a.frames, f'{f:04d}.jpg'))
        q = quads[frames.index(f)].astype(np.int32)
        cv2.polylines(im, [q], True, (1, 209, 251), 3)
        cv2.putText(im, str(f), (30, 900), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
        tiles.append(cv2.resize(im[800:1500], (540, 350)))
    rows = [np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]
    cv2.imwrite(a.qa, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
