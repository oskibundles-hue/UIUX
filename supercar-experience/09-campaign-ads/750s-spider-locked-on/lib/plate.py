"""
plate.py -- the PLATE layer of "ROOF DOWN": frame-exact source sampling, a cohesive day grade, streaks,
pushes, whips, impacts and light leaks (lib/fx.py, the approved GT3 RS showcase library), the licence-plate
blur, and for the roof shot the SKY MATTE that puts the giant type behind the car (lib/sky.py).

    python3 lib/plate.py [--frames 0,113,300] [--workers 4] [--force]

Writes .work/plate/NNNNN.png (RGB) for every output frame and .work/matte/NNNNN.png (L, 255 = sky) for the
roof shot. Each frame is keyed to a signature of the code, config and its timeline row
(.work/plate.sig.json), so only changed frames re-render.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edl  # noqa: E402
import fx  # noqa: E402
import sky  # noqa: E402

WORK = os.path.join(HERE, '..', '.work')
OUT = os.path.join(WORK, 'plate')
MOUT = os.path.join(WORK, 'matte')
FPS = edl.FPS
DENSE_F0, DENSE_K = 0, 4
PLATE_PAD, PLATE_SIGMA = 16, 12

_SRC = _DENSE = None
_GRADES = {}
TL = edl.build()
PLATE_BOXES = {int(k): v for k, v in json.load(open(os.path.join(HERE, 'data', 'plate_track.json'))).items()}


def src():
    global _SRC, _DENSE
    if _SRC is None:
        _SRC = np.load(os.path.join(WORK, 'src.npy'), mmap_mode='r')
        dp = os.path.join(WORK, 'dense_roof.npy')
        _DENSE = np.load(dp, mmap_mode='r') if os.path.exists(dp) else None
    return _SRC, _DENSE


# ------------------------------------------------------------------------------------ sampling
def _at(p, B):
    """source picture at fractional source frame p (float RGB 0..1), clamped to the shot"""
    S, D = src()
    p = min(max(p, B['fa']), B['fb'])
    if B.get('roof') and D is not None:
        d = (p - DENSE_F0) * DENSE_K
        i = int(math.floor(d))
        f = d - i
        i = min(i, len(D) - 1)
        a = fx.to_f(D[i])
        return a if f < 1e-3 or i + 1 >= len(D) else a * (1 - f) + fx.to_f(D[i + 1]) * f
    i = int(math.floor(p))
    f = p - i
    a = fx.to_f(S[i])
    return a if f < 1e-3 or i >= B['fb'] else a * (1 - f) + fx.to_f(S[i + 1]) * f


def sample(p, span, B):
    """shutter average over [p - span/2, p + span/2] source frames (a 180-degree look at the plate's speed)"""
    n = int(math.ceil(span * 1.5))
    if n <= 1:
        return _at(p, B)
    acc = None
    for j in range(n):
        fr = _at(p - span / 2 + span * (j + 0.5) / n, B)
        acc = fr if acc is None else acc + fr
    return acc / n


# ------------------------------------------------------------------------------------ grade
class DayGrade:
    """One look for every shot of a sunlit desert clip that arrives already graded (the Dropbox index files
    these clips as finished grades): a gentle per-shot normalise (40 % toward the clip's own 0.3 / 99.7th
    luma percentiles, gamma to a common mid-grey), a soft filmic S, steel shadows / warm highlights, warm
    hues kept, blues calmed a touch, a soft shoulder. Blended at STRENGTH with the source."""
    STRENGTH = 0.8

    def __init__(self, lo, hi, gamma):
        self.lo, self.hi, self.gamma = lo, hi, gamma

    @classmethod
    def fit(cls, frames, mid=0.34, norm=0.4):
        sub = np.stack([f[::8, ::8] for f in frames]).astype(np.float32) / 255
        l = fx.luma(sub).ravel()
        lo, hi = np.percentile(l, 0.3) * norm, 1 - (1 - np.percentile(l, 99.7)) * norm
        med = np.clip((np.median(l) - lo) / max(hi - lo, 1e-3), .02, .98)
        return cls(lo, hi, min(max(math.log(mid) / math.log(med), 0.9), 1.15))

    def __call__(self, img):
        x = np.clip((img - self.lo) / (self.hi - self.lo), 0, None) ** self.gamma
        xc = np.clip(x, 0, 1)
        s = xc * xc * (3 - 2 * xc)
        x = np.where(x <= 1, xc + (s - xc) * 0.3, x)
        l = fx.luma(x)[..., None]
        x = x + np.array([-0.012, 0.002, 0.010], np.float32) * (1 - l) ** 3 * 2 \
            + np.array([0.014, 0.005, -0.012], np.float32) * l ** 2
        warm = np.clip((x[..., 0:1] - x[..., 2:3]) * 3, 0, 1)
        blue = np.clip((x[..., 2:3] - x[..., 0:1]) * 3, 0, 1)
        l = fx.luma(x)[..., None]
        x = l + (x - l) * (0.94 + 0.12 * warm - 0.06 * blue)
        x = 0.006 + 0.988 * x
        sh = 0.87
        x = np.where(x > sh, sh + (1 - sh) * np.tanh((x - sh) / (1 - sh)), x)
        return (img + (x - img) * self.STRENGTH).astype(np.float32)


def grade_for(B):
    if B['id'] not in _GRADES:
        S, _ = src()
        _GRADES[B['id']] = DayGrade.fit([S[i] for i in range(B['fa'], B['fb'] + 1, 3)])
    return _GRADES[B['id']]


# ------------------------------------------------------------------------------------ plate blur
def plate_box(p):
    ks = sorted(PLATE_BOXES)
    p = min(max(p, ks[0]), ks[-1])
    a = int(math.floor(p))
    b = min(a + 1, ks[-1])
    u = p - a
    return [PLATE_BOXES[a][k] * (1 - u) + PLATE_BOXES[b][k] * u for k in range(4)]


def blur_plate(img, p, span):
    """rounded-rect (r 8) box padded 16 px, 6 px feather, two gaussian passes at sigma 12 inside (the GT3 RS
    showcase recipe). The box covers the tag's travel across the frame's shutter span."""
    x0, y0, w, h = plate_box(p - span / 2)
    x1, y1, w1, h1 = plate_box(p + span / 2)
    X0, Y0 = min(x0, x1) - PLATE_PAD, min(y0, y1) - PLATE_PAD
    X1, Y1 = max(x0 + w, x1 + w1) + PLATE_PAD, max(y0 + h, y1 + h1) + PLATE_PAD
    m = 60
    cx0, cy0, cx1, cy1 = int(max(X0 - m, 0)), int(max(Y0 - m, 0)), int(min(X1 + m, 1080)), int(min(Y1 + m, 1920))
    crop = img[cy0:cy1, cx0:cx1]
    bl = fx.gauss(fx.gauss(crop, PLATE_SIGMA), PLATE_SIGMA)
    yy, xx = np.mgrid[cy0:cy1, cx0:cx1].astype(np.float32)
    r, fe = 8.0, 6.0
    qx = np.maximum(np.maximum(X0 + r - xx, xx - (X1 - r)), 0)
    qy = np.maximum(np.maximum(Y0 + r - yy, yy - (Y1 - r)), 0)
    dist = np.hypot(qx, qy) - r                       # <0 inside the rounded rect
    a = np.clip(0.5 - dist / fe, 0, 1)[..., None]
    out = img.copy()
    out[cy0:cy1, cx0:cx1] = crop * (1 - a) + bl * a
    return out


# ------------------------------------------------------------------------------------ per frame
def leak_amount(t):
    tot, side = 0.0, 'left'
    for c, peak, sd, sig in edl.LEAKS:
        a = peak * math.exp(-0.5 * ((t - c) * FPS / sig) ** 2)
        if a > tot:
            tot, side = a, sd
    return tot, side


_yy = np.linspace(0, 1, fx.H, dtype=np.float32)[:, None, None] * fx.H
GRAD = (1 - 0.40 * (1 - np.clip((_yy - 150) / 750, 0, 1) ** 2 * (3 - 2 * np.clip((_yy - 150) / 750, 0, 1)))).astype(np.float32)
SWEEP = (13.72, 14.32)          # light sweep across the car body while the picture is frozen in the tape stop


def light_sweep(img, matte, t):
    """a soft diagonal band of light that crosses the car (not the sky) once, inside the freeze"""
    a, b = SWEEP
    if not a <= t <= b:
        return img
    u = fx.smootherstep((t - a) / (b - a))
    yy, xx = np.mgrid[0:fx.H:4, 0:fx.W:4].astype(np.float32)
    d = (xx * 0.8 + yy * 0.6) - (-600 + u * 2400)
    band = np.exp(-(d / 140) ** 2) * math.sin(math.pi * u)
    band = fx.up(band[..., None], fx.H, fx.W)
    car = 1 - matte[..., None]
    l = np.clip(fx.luma(img), 0, 1)[..., None]
    return img + band * car * (0.10 + 0.35 * l) * 0.9


def roof_push(i):
    B = edl.beat(16)
    u = (i - B['i0']) / max(edl.NF - 1 - B['i0'], 1)
    return 1 + (edl.PUSH_ROOF - 1) * (1 - (1 - u) ** 2)       # outQuad: moves from the first frame, never stops


def base(i):
    """plate frame i before transitions / impacts / leaks; also returns the sky matte for the roof shot"""
    row = TL[i]
    B = edl.beat(row['beat'])
    if B.get('black'):
        return np.zeros((fx.H, fx.W, 3), np.float32), None
    img = sample(row['p'], row['span'], B)
    if B['id'] == 11:
        img = blur_plate(img, row['p'], row['span'])
    matte = None
    if B.get('roof'):
        s = roof_push(i)
        cx, cy = edl.PUSH_ROOF_C
        img = fx.transform(img, scale=s, cx=cx, cy=cy)
        matte = sky.matte(img)
    img = grade_for(B)(img)
    if B.get('streak'):
        img = fx.streaks(img, **B['streak'])
    if B.get('roof'):
        img = fx.streaks(img, thresh=0.88, point=0.15, point_radius=60, gain=0.35)
        # graduated ND on the sky (a car-ad staple): the top of frame is taken down ~40 %, so white and gold
        # type read against it; the car below y 900 is untouched
        img = img * GRAD
        img = light_sweep(img, matte, row['t'])
        # tape stop: the picture darkens and desaturates as the music winds down, recovering into the end card
        t = row['t']
        k = fx.smootherstep((t - edl.T_STOP0) / (edl.T_END - edl.T_STOP0)) * (1 - fx.smootherstep((t - edl.T_END) / 0.35))
        if k > 0:
            l = fx.luma(img)[..., None]
            img = (l + (img - l) * (1 - 0.2 * k)) * (1 - 0.15 * k)
    if B['id'] in (1, 2, 3):
        a, b, s0, s1 = edl.PUSH_HOOK
        u = min(max((row['t'] - a) / (b - a), 0), 1)
        img = fx.transform(img, scale=s0 + (s1 - s0) * (1 - (1 - u) ** 3))
    return img, matte


def finish_fx(img, i):
    t = i / FPS
    for f0, strength, seed, n in edl.IMPACTS:
        if f0 <= i < f0 + n:
            img = fx.impact(img, i - f0, strength=strength, seed=seed)
    amt, side = leak_amount(t)
    if amt > 0.004:
        img = fx.light_leak(img, t, strength=amt, side=side, seed=3 + int(t))
    return img


def render_group(frames):
    """frames: a whip group (both sides of a cut) or a single frame"""
    bases = {i: base(i) for i in frames}
    imgs = {i: bases[i][0] for i in frames}
    for b, d in edl.WHIPS:
        grp = list(range(b - edl.WHIP_K, b + edl.WHIP_K))
        if set(grp) <= set(frames):
            seq = fx.whip([imgs[i] for i in grp[:edl.WHIP_K]], [imgs[i] for i in grp[edl.WHIP_K:]], direction=d)
            for i, f in zip(grp, seq):
                imgs[i] = f
    for i in frames:
        out = finish_fx(imgs[i], i)
        Image.fromarray(fx.to_u8(out)).save(os.path.join(OUT, f'{i:05d}.png'), compress_level=1)
        m = bases[i][1]
        if m is not None:
            Image.fromarray((np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(
                os.path.join(MOUT, f'{i:05d}.png'), compress_level=1)
    return frames


def groups(frames):
    wg = []
    for b, _ in edl.WHIPS:
        wg.append(list(range(b - edl.WHIP_K, b + edl.WHIP_K)))
    fs, out = set(frames), []
    for g in wg:
        if fs & set(g):
            out.append(g)
            fs -= set(g)
    out += [[i] for i in sorted(fs)]
    return out


def signature(group):
    h = hashlib.sha1()
    for f in ('plate.py', 'edl.py', 'fx.py', 'sky.py', os.path.join('data', 'plate_track.json')):
        h.update(open(os.path.join(HERE, f), 'rb').read())
    h.update(json.dumps([TL[i] for i in group], sort_keys=True).encode())
    dp = os.path.join(WORK, 'dense_roof.npy')
    h.update(str(os.path.getmtime(dp) if os.path.exists(dp) else 0).encode())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', default='')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(MOUT, exist_ok=True)
    frames = [int(v) for v in a.frames.split(',')] if a.frames else list(range(edl.NF))
    sig_path = os.path.join(WORK, 'plate.sig.json')
    sigs = json.load(open(sig_path)) if os.path.exists(sig_path) else {}
    todo = []
    for g in groups(frames):
        s = signature(g)
        if a.force or any(sigs.get(str(i)) != s or not os.path.exists(os.path.join(OUT, f'{i:05d}.png')) for i in g):
            todo.append((g, s))
    print(f'plate: {len(todo)} groups to render ({sum(len(g) for g, _ in todo)} frames)', flush=True)
    done = 0
    with Pool(a.workers) as pool:
        for g in pool.imap_unordered(render_group, [g for g, _ in todo]):
            done += len(g)
            if done % 24 < len(g):
                print(f'  {done} frames', flush=True)
    for g, s in todo:
        for i in g:
            sigs[str(i)] = s
    json.dump(sigs, open(sig_path, 'w'))


if __name__ == '__main__':
    main()
