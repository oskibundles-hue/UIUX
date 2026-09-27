"""
sky.py -- the matte that puts type BEHIND the car on the roof shot (source S1, locked-off).

The shot is locked off and the car sits against open sky, so no roto is needed: whatever is sky gets the
type, everything else (the car, the stowing roof, the far hills) stays in front of it. Per frame:

  1. seed: pixels that read as sky -- blue (b > r) and not dark, or the pale haze near the sun -- in the top
     third of the frame;
  2. sky model: a 2-D quadratic per RGB channel fitted to the seed (the sky is a smooth gradient);
  3. residual: colour distance of every pixel to the model -> soft sky alpha (full res, so the car's own
     anti-aliased silhouette becomes the matte edge);
  4. topology at 1/4 res: sky = connected to the top edge; foreground = connected to the bottom or side
     edges (car, roof, hills). Anything enclosed by sky (lens-flare orbs) is sky; sky reflections on the
     glossy roof are enclosed by the car, so they are not;
  5. alpha: the soft residual alpha only in a thin band around the foreground outline (it carries the
     car's own anti-aliased edge); 1 outside the band, 0 inside the car. The band masks are upsampled
     bilinearly, so the band edges are feathered.
  Inside the sun's lens-flare orb (a fixed disc on this locked-off shot) anything not darker than the sky
  model counts as sky before steps 3-4, so the orb can never be keyed as car where it touches a buttress.

matte(img) -> float32 (H, W), 1 = sky (type visible), 0 = car / hills (type hidden).
"""
import numpy as np

LO, HI = 0.035, 0.085            # residual distance: <= LO fully sky, >= HI fully foreground
DS = 4


def _design(xs, ys):
    x = xs / 1080.0 - 0.5
    y = ys / 1920.0 - 0.3
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], -1)


def _dilate(m):
    o = m.copy()
    o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    return o


def _reconstruct(seed, mask, iters=2000):
    """geodesic reconstruction: grow `seed` inside `mask` (4-connected) until stable"""
    cur = seed & mask
    for _ in range(iters):
        nxt = _dilate(cur) & mask
        if (nxt == cur).all():
            break
        cur = nxt
    return cur


def matte(img, orb=None):
    H, W = img.shape[:2]
    small = img[DS // 2::DS, DS // 2::DS].astype(np.float32)
    h, w = small.shape[:2]
    r, g, b = small[..., 0], small[..., 1], small[..., 2]
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx, mn = small.max(-1), small.min(-1)
    yy, xx = np.mgrid[0:h, 0:w]
    seed = (((b > r + 0.03) & (L > 0.22)) | ((L > 0.62) & (mx - mn < 0.3) & (b >= r - 0.02))) & (yy < h * 0.33)
    # fit the sky model on the seed (subsampled), two passes with outlier rejection
    ys_, xs_ = np.nonzero(seed)
    sel = np.arange(len(xs_))[::max(1, len(xs_) // 4000)]
    X = _design(xs_[sel] * DS + DS / 2, ys_[sel] * DS + DS / 2)
    Y = small[ys_[sel], xs_[sel]]
    for _ in range(2):
        coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
        res = np.linalg.norm(X @ coef - Y, axis=1)
        keep = res < max(np.percentile(res, 90), 0.02)
        X, Y = X[keep], Y[keep]
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)

    # residual + soft alpha at low res for the topology
    pred_s = _design(xx * DS + DS / 2.0, yy * DS + DS / 2.0) @ coef
    d_s = _flare_is_sky(small, pred_s, xx * DS + DS / 2.0, yy * DS + DS / 2.0, np.linalg.norm(small - pred_s, axis=-1), orb)
    sky_s = d_s < (LO + HI) / 2
    top = np.zeros_like(sky_s)
    top[0] = True
    conn = _reconstruct(top, sky_s)
    # fill holes: foreground not connected to the bottom / side edges below the sky is enclosed -> sky
    fg = ~conn
    edge = np.zeros_like(fg)
    edge[-1] = True
    edge[:, 0] = True
    edge[:, -1] = True
    fgc = _reconstruct(edge & fg, fg)                  # the real foreground: car, roof, hills (touch an edge)
    near = _dilate(_dilate(fgc))                         # a 2-px (low res) band either side of its outline
    core = ~_dilate(_dilate(~fgc))

    # full-res soft alpha only inside the band; beyond it the answer is certain (1 sky, 0 car), so sky
    # reflections on the glossy roof cannot leak and flare orbs in the sky cannot leave rings
    Y2, X2 = np.mgrid[0:H, 0:W]
    pred = (_design(X2.astype(np.float32), Y2.astype(np.float32)) @ coef).astype(np.float32)
    im = img.astype(np.float32)
    d = _flare_is_sky(im, pred, X2, Y2, np.linalg.norm(im - pred, axis=-1), orb)
    d = np.where((Y2 < 360) & (im[..., 2] > im[..., 0] + 0.02), 0.0, d)   # deep-blue zenith is always sky
    soft = np.clip((HI - d) / (HI - LO), 0, 1)
    # review r1: the band masks are upsampled bilinearly and feathered (nearest-neighbour left 4 px stair-steps
    # where the soft alpha was not already 0 at the band's inner edge)
    up = lambda m: _upf(m.astype(np.float32), H, W)
    a = up(core.astype(np.float32)), up(near.astype(np.float32))
    a = (1 - a[0]) * (a[1] * soft + (1 - a[1]))
    return np.clip(a, 0, 1).astype(np.float32)


def _upf(m, H, W):
    from PIL import Image
    im = Image.fromarray(np.ascontiguousarray(m), 'F').resize((m.shape[1] * DS, m.shape[0] * DS), Image.BILINEAR)
    return np.asarray(im, np.float32)[:H, :W]


def _flare_is_sky(img, pred, xs, ys, d, orb):
    """review r1: the sun's lens-flare orb is ADDED light on the sky. Where it touched the left buttress tip it
    keyed as car and punched a disc out of the P of SPIDER (frames 273-281). Inside the orb's disc (orb =
    (cx, cy, r) in this frame's pixels; the shot is locked off, so it hardly moves), any pixel that is not
    darker than the sky model counts as sky. The dark buttress is always darker, so the tip stays car. The
    rule is kept to the disc: a global version also keyed the buttress's bright glassy edge as sky."""
    if orb is None:
        return d
    cx, cy, r = orb
    inside = (xs - cx) ** 2 + (ys - cy) ** 2 < r * r
    brighter = (img - pred).min(-1) > -0.04
    return np.where(inside & brighter, 0.0, d)
