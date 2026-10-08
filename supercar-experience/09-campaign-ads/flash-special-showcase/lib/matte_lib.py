"""
matte_lib.py -- numpy/Pillow-only toolkit for "type behind the car" occlusion shots.

No OpenCV / scipy / torch. Everything here is plain numpy + Pillow so it runs in the
SE render container. Reusable pieces:

  load_clip(ffmpeg, src, t0, dur)          -> uint8 array (N,H,W,3) of decoded frames
  poly_mask(points, H, W, ss=4)            -> float32 0..1 anti-aliased polygon (supersampled)
  refine_alpha(img, hard, band=7, ...)     -> float32 alpha, edges snapped to the image with a
                                              local fg/bg colour-projection matte inside a trimap band
  track_translation(frames, ref, box)      -> (N,2) sub-pixel (dy,dx) of a rigid region vs ref frame
  shift(img, dy, dx)                       -> bilinear sub-pixel shift (works on HxW or HxWxC)
  inpaint_diffuse(img, hole, iters)        -> fills `hole` by multi-scale diffusion (clean plate
                                              behind the car, only needs to survive a thin sliver)
  scale_about(img, s, cx, cy)              -> bilinear zoom of a layer about an anchor (2.5D push)
  box_blur(img, r)                         -> separable box blur via cumulative sums

Workflow (see build_matte.py for the GT3 RS warehouse instance):
  1. hand-trace a silhouette polygon on ONE reference frame (+-5 px is enough)
  2. refine_alpha() snaps it to the real edge wherever there is contrast; falls back to the
     feathered polygon where the car is dark-on-dark (carbon roof on black warehouse)
  3. track_translation() on the car region gives per-frame offsets; the matte is shifted,
     not re-segmented, so it cannot flicker
  4. export: alpha PNG + track.json + clean background plate
"""
import json, subprocess
import numpy as np
from PIL import Image, ImageDraw


# ---------------------------------------------------------------- decode
def load_clip(ffmpeg, src, t0, dur, w=1080, h=1920):
    raw = subprocess.run([ffmpeg, '-v', 'error', '-ss', str(t0), '-i', src, '-t', str(dur),
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


# ---------------------------------------------------------------- basic ops
def box_blur(img, r):
    """Separable box blur, radius r (window 2r+1), edge-clamped. img float (H,W) or (H,W,C)."""
    if r <= 0:
        return img
    out = img.astype(np.float32)
    for ax in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[ax] = (r + 1, r)
        p = np.pad(out, pad, mode='edge')
        c = np.cumsum(p, axis=ax, dtype=np.float64)
        n = out.shape[ax]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax)
        lo = np.take(c, np.arange(0, n), axis=ax)
        out = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return out


def gauss_blur(img, sigma):
    """Approximate gaussian: 3 box passes."""
    if sigma <= 0:
        return img
    r = max(1, int(round(sigma * 0.87)))
    for _ in range(3):
        img = box_blur(img, r)
    return img


def dilate(mask, r):
    return (box_blur(mask.astype(np.float32), r) > 1e-3).astype(np.float32)


def erode(mask, r):
    return (box_blur(mask.astype(np.float32), r) > 1 - 1e-3).astype(np.float32)


def poly_mask(points, H, W, ss=4):
    """Anti-aliased polygon mask (float 0..1). points = [(x,y),...] in pixel coords."""
    im = Image.new('L', (W * ss, H * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in points], fill=255)
    im = im.resize((W, H), Image.BOX)
    return np.asarray(im, np.float32) / 255.0


# ---------------------------------------------------------------- matting
def refine_alpha(img, hard, band=7, win=9, lift=0.45, min_contrast=0.035, feather=1.2):
    """Snap a rough mask to real edges.

    img   : float32 RGB 0..1
    hard  : float32 0..1 rough mask (polygon)
    band  : half-width (px) of the unknown zone of the trimap
    win   : radius of the local window used to estimate fg / bg colours
    lift  : gamma applied before matting -- boosts dark-on-dark separation
    Returns alpha float32 0..1.

    For every band pixel: F = mean colour of sure-fg pixels nearby, B = mean of sure-bg pixels
    nearby, alpha = clamp(<I-B, F-B> / |F-B|^2). Where |F-B| is tiny (no contrast) the
    feathered polygon is used instead, weighted smoothly by contrast.
    """
    I = np.power(np.clip(img, 0, 1), lift)
    m = (hard > 0.5).astype(np.float32)
    fg = erode(m, band)
    bg = 1 - dilate(m, band)
    unk = 1 - fg - bg
    def local_mean(w):
        num = box_blur(I * w[..., None], win)
        den = box_blur(w, win)[..., None]
        return num / np.maximum(den, 1e-4), den[..., 0]
    # widen the sampling window progressively so every band pixel sees some fg and bg
    F, fd = local_mean(fg)
    B, bd = local_mean(bg)
    for k in (2, 4):
        F2, fd2 = (lambda r: (box_blur(I * fg[..., None], r) / np.maximum(box_blur(fg, r)[..., None], 1e-4), box_blur(fg, r)))(win * k)
        B2, bd2 = (lambda r: (box_blur(I * bg[..., None], r) / np.maximum(box_blur(bg, r)[..., None], 1e-4), box_blur(bg, r)))(win * k)
        F = np.where((fd < 1e-3)[..., None], F2, F); fd = np.where(fd < 1e-3, fd2, fd)
        B = np.where((bd < 1e-3)[..., None], B2, B); bd = np.where(bd < 1e-3, bd2, bd)
    d = F - B
    dd = (d * d).sum(-1)
    a = ((I - B) * d).sum(-1) / np.maximum(dd, 1e-6)
    a = np.clip(a, 0, 1)
    contrast = np.sqrt(dd)
    soft_poly = gauss_blur(hard, feather)
    w = np.clip((contrast - min_contrast) / (min_contrast * 2), 0, 1)
    a = w * a + (1 - w) * soft_poly
    # the colour projection is only trusted close to the drawn line
    a = np.where(unk > 0, a, m)
    # a touch of smoothing kills single-pixel chatter from compression noise
    a = 0.6 * a + 0.4 * gauss_blur(a, 0.7)
    return np.clip(a, 0, 1).astype(np.float32)


# ---------------------------------------------------------------- tracking
def _hann2(h, w):
    return np.outer(np.hanning(h), np.hanning(w)).astype(np.float32)


def phase_corr(a, b):
    """Sub-pixel shift (dy,dx) such that shift(b, dy, dx) ~= a."""
    win = _hann2(*a.shape)
    A = np.fft.fft2((a - a.mean()) * win)
    Bf = np.fft.fft2((b - b.mean()) * win)
    R = A * np.conj(Bf)
    R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    H, W = r.shape
    def para(m, c, p):
        den = m - 2 * c + p
        return 0.0 if abs(den) < 1e-12 else 0.5 * (m - p) / den
    oy = para(r[(iy - 1) % H, ix], r[iy, ix], r[(iy + 1) % H, ix])
    ox = para(r[iy, (ix - 1) % W], r[iy, ix], r[iy, (ix + 1) % W])
    dy = iy + oy; dx = ix + ox
    if dy > H / 2: dy -= H
    if dx > W / 2: dx -= W
    return dy, dx


def track_translation(frames, ref, box, smooth_deg=3):
    """Per-frame (dy,dx) of the rigid region `box`=(y0,y1,x0,x1) relative to frame `ref`.
    Returns raw and polynomial-smoothed tracks (smooth camera moves only)."""
    y0, y1, x0, x1 = box
    g = lambda f: np.asarray(f[y0:y1, x0:x1], np.float32).mean(-1)
    R = g(frames[ref])
    raw = np.array([phase_corr(g(f), R) for f in frames])
    t = np.arange(len(frames))
    sm = np.stack([np.polyval(np.polyfit(t, raw[:, k], smooth_deg), t) for k in (0, 1)], 1)
    sm -= sm[ref]
    return raw, sm


# ---------------------------------------------------------------- warps
def _affine(img, coeffs, W, H):
    """Pillow affine on float arrays (per channel, 'F' mode keeps precision)."""
    if img.ndim == 2:
        return np.asarray(Image.fromarray(img.astype(np.float32), 'F').transform(
            (W, H), Image.AFFINE, coeffs, resample=Image.BILINEAR), np.float32)
    return np.stack([_affine(img[..., c], coeffs, W, H) for c in range(img.shape[2])], -1)


def shift(img, dy, dx):
    H, W = img.shape[:2]
    return _affine(img, (1, 0, -dx, 0, 1, -dy), W, H)


def scale_about(img, s, cx, cy, dy=0.0, dx=0.0):
    """Zoom layer by s about (cx,cy), then translate by (dx,dy)."""
    H, W = img.shape[:2]
    # output (x,y) samples input ((x-dx-cx)/s+cx, ...)
    a = 1 / s
    return _affine(img, (a, 0, cx - (cx + dx) * a, 0, a, cy - (cy + dy) * a), W, H)


# ---------------------------------------------------------------- clean plate
def inpaint_diffuse(img, hole, levels=6):
    """Fill hole (1 = unknown) by coarse-to-fine normalised-convolution diffusion.
    Good enough for the few pixels a 2.5D push reveals behind the car."""
    img = img.astype(np.float32)
    known = (hole < 0.5).astype(np.float32)
    out = img * known[..., None]
    fill = np.zeros_like(img)
    for lv in range(levels, 0, -1):
        r = 2 ** lv
        num = box_blur(img * known[..., None], r)
        den = box_blur(known, r)[..., None]
        est = num / np.maximum(den, 1e-4)
        fill = np.where(den > 1e-3, est, fill)
    return out + fill * (1 - known)[..., None]


def save_gray(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def save_rgb(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


# ---------------------------------------------------------------- edge snapping
def _bilinear(img, xs, ys):
    H, W = img.shape
    xs = np.clip(xs, 0, W - 1.001); ys = np.clip(ys, 0, H - 1.001)
    x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
    fx = xs - x0; fy = ys - y0
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def snap_polygon(img, points, step=2.0, search=6.0, min_grad=0.02, lift=0.5, med=7, lock=()):
    """Densify a hand-traced polygon and slide every sample along its normal to the strongest
    luminance edge within +-search px (sub-pixel). Samples with no clear edge stay put.
    Offsets are median-filtered along the contour so compression noise cannot make it wiggle.
    lock: indices of original vertices whose adjacent segments must not move (e.g. dark-on-dark).
    Returns (dense_points, offsets)."""
    L = np.power(np.clip(img, 0, 1), lift).mean(-1).astype(np.float32)
    L = gauss_blur(L, 0.8)
    P = np.asarray(points, np.float64)
    n = len(P)
    pts, nrm, locked = [], [], []
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        seg = b - a; ln = np.hypot(*seg)
        if ln < 1e-6:
            continue
        t = seg / ln; nv = np.array([-t[1], t[0]])
        k = max(1, int(ln // step))
        for j in range(k):
            pts.append(a + seg * j / k); nrm.append(nv); locked.append(i in lock)
    pts = np.array(pts); nrm = np.array(nrm); locked = np.array(locked)
    offs = np.arange(-search, search + 0.01, 0.5)
    xs = pts[:, 0:1] + nrm[:, 0:1] * offs[None]
    ys = pts[:, 1:2] + nrm[:, 1:2] * offs[None]
    prof = _bilinear(L, xs, ys)
    g = np.abs(np.gradient(prof, axis=1)) / 0.5
    # prefer edges near the drawn line (mild prior)
    g_w = g * (1 - 0.35 * (np.abs(offs) / search)[None])
    idx = np.argmax(g_w, 1)
    best = offs[idx].astype(np.float64)
    ok = (g[np.arange(len(g)), idx] > min_grad) & ~locked
    best[~ok] = 0.0
    # circular median filter
    r = med // 2
    padded = np.concatenate([best[-r:], best, best[:r]])
    sm = np.array([np.median(padded[i:i + med]) for i in range(len(best))])
    dense = pts + nrm * sm[:, None]
    return [tuple(p) for p in dense], sm
