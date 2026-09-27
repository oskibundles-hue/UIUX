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
import dense  # noqa: E402

DENSE_K = dense.FACTOR
PLATE_PAD, PLATE_SIGMA = 16, 12

_SRC = None
_DENSE = {}
_GRADES = {}
TL = edl.build()
PLATE_BOXES = {int(k): v for k, v in json.load(open(os.path.join(HERE, 'data', 'plate_track.json'))).items()}


def src():
    global _SRC
    if _SRC is None:
        _SRC = np.load(os.path.join(WORK, 'src.npy'), mmap_mode='r')
    return _SRC


def dense_for(B):
    """(f0, frames) of the optical-flow range that covers this beat's shot, or None"""
    for f0, f1 in dense.RANGES:
        if f0 <= B['fa'] and B['fb'] <= f1:
            if (f0, f1) not in _DENSE:
                _DENSE[(f0, f1)] = np.load(dense.path(f0, f1), mmap_mode='r')
            return f0, _DENSE[(f0, f1)]
    return None


# ------------------------------------------------------------------------------------ sampling
def _at(p, B):
    """source picture at fractional source frame p (float RGB 0..1), clamped to the shot. Beats that play at
    a non-integer speed sample the 4x optical-flow in-betweens (lib/dense.py), so no frame is ever a two-frame
    double exposure; the remaining blend is between in-betweens a quarter frame apart."""
    S = src()
    p = min(max(p, B['fa']), B['fb'])
    dn = dense_for(B)
    if dn is not None:
        f0, D = dn
        d = (p - f0) * DENSE_K
        i = min(int(math.floor(d)), len(D) - 1)
        f = d - i
        a = fx.to_f(D[i])
        return a if f < 1e-3 or i + 1 >= len(D) else a * (1 - f) + fx.to_f(D[i + 1]) * f
    i = int(math.floor(p))
    f = p - i
    a = fx.to_f(S[i])
    return a if f < 1e-3 or i >= B['fb'] else a * (1 - f) + fx.to_f(S[i + 1]) * f


def sample(p, span, B):
    """shutter average over [p - span/2, p + span/2] source frames (a 180-degree look at the plate's speed)"""
    k = DENSE_K if dense_for(B) is not None else 1
    if B.get('span_min'):
        # review r2: on the badge shot minterpolate falls back to blending on the fast-moving truss, so its
        # midpoint in-betweens are double exposures; averaging over a whole source frame on EVERY output frame
        # gives the truss one even motion blur (no 12 Hz strobe) while the near-static badge stays sharp
        span = max(span, B['span_min'])
    n = int(math.ceil(span * k))
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
        S = src()
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


def _smooth(y, a, b):
    x = np.clip((y - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


_yy = np.arange(fx.H, dtype=np.float32)[:, None, None]
# graduated ND on the sky, lighter since review r1 (0.40 -> 0.28): with the sky chroma lift below it keeps the
# roof shot's sky blue instead of slate, so the finale sits in the same world as the cobalt desert day before it
GRAD = (1 - 0.28 * (1 - _smooth(_yy, 150, 900))).astype(np.float32)
# end-card ND on the sky: up to 45 % down behind the top block and the price, eased in over the end-card hit, so
# the gold price reads by luminance, not hue. Review r2: it ramps in from above the frame (the sky stays
# monotonic: no light stripe over the logo) and fades out 760-820 at the ridge line; it is gated by a GROWN
# matte (mnd below), so the thin haze rim the type matte calls "hill" is darkened with the sky, not left as a
# bright outline along the ridge. Chroma is lifted with it, so the held sky stays blue, not slate.
ECARD_BAND = (_smooth(_yy, -200, 420) * (1 - _smooth(_yy, 760, 820))).astype(np.float32)
SKY_CHROMA = 0.45
ECARD_CHROMA = 0.5
CLUSTER = (270, 940, 740, 1095)   # badge shot: the instrument cluster (speed / limit readouts) is defocused
SWEEP = (13.62, 14.05)          # light sweep across the car body, inside the tape stop and its freeze
CAR_BELOW = _smooth(_yy, 780, 830).astype(np.float32)   # the sweep lights the car body only, never hills or sky


def light_sweep(img, matte, t):
    """a soft diagonal band of light that crosses the car (not the sky) once, inside the freeze"""
    a, b = SWEEP
    if not a <= t <= b:
        return img
    u = fx.smootherstep((t - a) / (b - a))
    yy, xx = np.mgrid[0:fx.H:4, 0:fx.W:4].astype(np.float32)
    d = (xx * 0.8 + yy * 0.6) - (200 + u * 1700)
    band = np.exp(-(d / 140) ** 2) * math.sin(math.pi * u)
    band = fx.up(band[..., None], fx.H, fx.W)
    car = (1 - matte[..., None]) * CAR_BELOW
    l = np.clip(fx.luma(img), 0, 1)[..., None]
    return img + band * car * (0.10 + 0.35 * l) * 0.9


# the sun's lens-flare orb on the roof shot, measured on the source: centre (279, 503) at src f10 drifting to
# (262, 475) by f60 (sky-model residual centroid), about 75 px across
ORB = ((10, 279.0, 503.0), (60, 262.0, 475.0), 46.0)


def orb_at(p, s, cx, cy):
    (p0, x0, y0), (p1, x1, y1), r = ORB
    u = (p - p0) / (p1 - p0)
    ox, oy = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return cx + (ox - cx) * s, cy + (oy - cy) * s, r * s


def push(img, s, cx=fx.W / 2, cy=fx.H / 2):
    """scale about (cx, cy) with a Lanczos resample of the matching source box (review r2: fx.transform's
    bilinear resample softened every pushed frame, and it skips scale 1.0, so frame 0 -- the poster -- was
    crisper than the frames after it). Scale 1.0 is an exact identity here too."""
    W, H = fx.W, fx.H
    box = (cx - cx / s, cy - cy / s, cx + (W - cx) / s, cy + (H - cy) / s)
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(img[..., c]), 'F')
                                .resize((W, H), Image.LANCZOS, box=box), np.float32) for c in range(3)], -1)


def blur_box(img, X0, Y0, X1, Y1, sigma=9, darken=1.0, fe=18.0):
    """defocus a rounded rect with a wide feather, so it reads as depth of field, not a patch"""
    m = 40
    cx0, cy0, cx1, cy1 = int(max(X0 - m, 0)), int(max(Y0 - m, 0)), int(min(X1 + m, fx.W)), int(min(Y1 + m, fx.H))
    crop = img[cy0:cy1, cx0:cx1]
    bl = fx.gauss(fx.gauss(crop, sigma), sigma) * darken
    yy, xx = np.mgrid[cy0:cy1, cx0:cx1].astype(np.float32)
    r = 8.0
    qx = np.maximum(np.maximum(X0 + r - xx, xx - (X1 - r)), 0)
    qy = np.maximum(np.maximum(Y0 + r - yy, yy - (Y1 - r)), 0)
    a = np.clip(0.5 - (np.hypot(qx, qy) - r) / fe, 0, 1)[..., None]
    out = img.copy()
    out[cy0:cy1, cx0:cx1] = crop * (1 - a) + bl * a
    return out


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
    if B['id'] == 4:
        # review r2: the instrument cluster reads 33-41 MPH next to a posted 25 on the frames the label does not
        # cover; defocus it (it is not the subject; the badge is)
        img = blur_box(img, *CLUSTER)
    matte = mnd = None
    if B.get('roof'):
        s = roof_push(i)
        cx, cy = edl.PUSH_ROOF_C
        img = push(img, s, cx, cy)
        matte = sky.matte(img, orb=orb_at(row['p'], s, cx, cy))
        mnd = np.clip(2.5 * fx.gauss(matte[..., None], 10), 0, 1)    # grown matte, for grading the sky only
    img = grade_for(B)(img)
    if B.get('lift'):
        img = np.clip(img, 0, None) ** B['lift']                     # review r2: shadow lift on the darkest plates
    if matte is not None:
        # sky chroma lift (review r1: the roof shot's hazy sky went slate under the ND)
        l = fx.luma(img)[..., None]
        img = l + (img - l) * (1 + SKY_CHROMA * mnd)
    if B.get('streak'):
        img = fx.streaks(img, **B['streak'])
    if B.get('roof'):
        img = fx.streaks(img, thresh=0.88, point=0.15, point_radius=60, gain=0.35)
        # graduated ND on the sky (a car-ad staple): the top of frame is taken down ~40 %, so white and gold
        # type read against it; the car below y 900 is untouched
        img = img * GRAD
        t = row['t']
        ke = fx.smootherstep((t - (edl.T_END - 0.12)) / 0.37)
        if ke > 0:
            img = img * (1 - 0.45 * ke * ECARD_BAND * mnd)
            l = fx.luma(img)[..., None]
            img = l + (img - l) * (1 + ECARD_CHROMA * ke * ECARD_BAND * mnd)
        img = light_sweep(img, matte, t)
        # tape stop: the picture darkens and desaturates as the music winds down, recovering into the end card
        k = fx.smootherstep((t - edl.T_STOP0) / (edl.T_END - edl.T_STOP0)) * (1 - fx.smootherstep((t - edl.T_END) / 0.35))
        if k > 0:
            l = fx.luma(img)[..., None]
            img = (l + (img - l) * (1 - 0.2 * k)) * (1 - 0.15 * k)
    if B['id'] in (1, 2, 3):
        a, b, s0, s1 = edl.PUSH_HOOK
        u = min(max((row['t'] - a) / (b - a), 0), 1)
        img = push(img, s0 + (s1 - s0) * (1 - (1 - u) ** 3))
    return img, matte


def impact(img, k, strength, seed):
    """fx.impact on a reflect-padded frame (review r1: its RGB split sampled black from outside the frame and
    wrapped with np.roll, drawing a lime border on the drop frames), with the 3.5 % scale floor eased out over
    k 9-14 instead of stepping to 1.0 on k 14. The vendored fx.py stays identical to the approved copy."""
    P = 48
    pad = np.pad(img, ((P, P), (P, P), (0, 0)), mode='reflect')
    out = fx.impact(pad, k, strength=strength, seed=seed)
    if 9 <= k < 14:                                   # fx.impact holds max(punch, 1.035) until k 14: ease it
        s = (1 + 0.035 * (1 - fx.smootherstep((k - 9) / 5))) / 1.035
        out = fx.transform(out, scale=s)             # before the crop, so the pad (not a mirror) fills the edges
    return out[P:-P, P:-P]


def finish_fx(img, i):
    t = i / FPS
    for f0, strength, seed, n in edl.IMPACTS:
        if f0 <= i < f0 + n:
            img = impact(img, i - f0, strength, seed)
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
    for f in ('plate.py', 'edl.py', 'fx.py', 'sky.py', 'dense.py', os.path.join('data', 'plate_track.json')):
        h.update(open(os.path.join(HERE, f), 'rb').read())
    h.update(json.dumps([TL[i] for i in group], sort_keys=True).encode())
    for r in dense.RANGES:
        dp = dense.path(*r)
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
