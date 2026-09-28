#!/usr/bin/env python3
"""
track.py -- numpy-only planar object tracker for locked-on motion graphics.

WHAT IT DOES
  Given a video, a frame range (one shot, no cuts inside) and a starting box
  around an object, it follows the object frame by frame and writes per-frame
  boxes (x, y, w, h in FULL-RES pixels of the source, e.g. 1080x1920) plus a
  0..1 confidence, raw and smoothed, to JSON.  No OpenCV / scipy needed.

METHOD
  * Frames are decoded by ffmpeg as grey luma at 1/DS resolution (default 1/2)
    and a box-filter pyramid is built per frame (anti-aliased sampling).
  * The search region is resampled into the template's canonical frame for
    each candidate (scale, aspect), so scale change is handled by sampling,
    not by resizing the template.
  * Coarse-to-fine: a 32-px canonical pass over a wide window finds the peak,
    then a 96-px canonical pass over a +-4 px window refines it, both with
    zero-mean normalised cross-correlation (FFT + integral images), then a
    parabolic sub-pixel fit.
  * Two templates are scored together: the ANCHOR (first frame; stops drift)
    and the PREVIOUS frame's patch (follows perspective/lighting change).
    Anchor weight drops automatically as the anchor stops matching.
  * Constant-velocity prediction centres the search.
  * A backward pass (end -> start) gives a forward/backward consistency error;
    confidence = peak NCC x FB-consistency.
  * Smoothing: confidence-weighted local-quadratic regression (Savitzky-Golay
    style, zero phase: no lag) on cx, cy, log w, log h.  Removes jitter
    without dragging the box behind real motion.

  * --scale-pen P subtracts P*|log scale change| from the NCC score, so the box
    only grows/shrinks when the image really says so (stops scale drift on
    objects whose look changes, e.g. a headlight while the car turns).
  * --method points: alternative KLT-style tracker (48 small patches, robust
    affine fit).  Kept for experiments; on the Black Series turn it SHEARS
    (a 3-D car turning is not affine) -- see qa/FAIL_*.jpg.  Prefer template.

LESSONS (from the SE footage)
  * Pick a target that stays in frame and changes slowly.  The AMG grille
    leaves the right edge mid-shot and foreshortens ~50 %: every grille/fascia
    track failed; the near-side headlight tracks at conf >= 0.79 all shot.
  * Frame numbers must be exact.  ffmpeg -ss on these .movs lands ~2 frames
    off; select by frame number n (as here and in build.sh).

CLI
  python3 track.py --video V.mov --ffmpeg FFMPEG --name crest \
      --f0 79 --f1 108 --box 310,1020,446,516 [--aspect] [--out tracks.json]
  (--box is x,y,w,h in full-res px on frame f0; frames are 0-based indices.)
  Several runs can write into the same JSON; shots are keyed by --name.

PYTHON
  from track import track_shot
  res = track_shot(video, ffmpeg, f0, f1, (x,y,w,h), aspect=False)

JSON  (see lock.js for the consumer)
  {"<name>": {"video":..., "fps":23.976, "size":[1080,1920], "f0":79, "f1":108,
    "t0": f0/fps, "t1": (f1+1)/fps,
    "frames":[{"f":79,"t":3.2949,"x":..,"y":..,"w":..,"h":..,"conf":0.93,
               "raw":[x,y,w,h]}, ...]}}
  t is the PRESENTATION time of frame f (f / fps).  A frame is on screen for
  [t, t+1/fps).  Sample with lock.js TrackLock.at(track, t).
"""
import argparse, json, os, subprocess, sys
import numpy as np

FPS = 24000 / 1001


# ---------------------------------------------------------------- decoding
def probe_size(video, ffmpeg):
    out = subprocess.run([ffmpeg, '-hide_banner', '-i', video], capture_output=True, text=True).stderr
    import re
    m = re.search(r'Video:.*?(\d{3,5})x(\d{3,5})', out)
    return int(m.group(1)), int(m.group(2))


def decode_gray(video, ffmpeg, f0, f1, ds=2):
    W, H = probe_size(video, ffmpeg)
    w, h = W // ds, H // ds
    vf = f"select='between(n\\,{f0}\\,{f1})',scale={w}:{h}:flags=area,format=gray"
    raw = subprocess.run([ffmpeg, '-v', 'error', '-i', video, '-vf', vf, '-vsync', '0',
                          '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32) / 255.0
    assert len(fr) == f1 - f0 + 1, (len(fr), f1 - f0 + 1)
    return fr, (W, H)


# ---------------------------------------------------------------- sampling
def pyramid(img, levels=5):
    p = [img]
    for _ in range(levels - 1):
        a = p[-1]
        h, w = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
        a = a[:h, :w]
        p.append(0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]))
    return p


def bilinear(img, xs, ys):
    h, w = img.shape
    xs = np.clip(xs, 0, w - 1.001); ys = np.clip(ys, 0, h - 1.001)
    x0 = xs.astype(np.int32); y0 = ys.astype(np.int32)
    fx = xs - x0; fy = ys - y0
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def sample(pyr, cx, cy, bw, bh, tw, th, pad):
    """Resample image region centred (cx,cy) where the box is bw x bh (image px)
    into a canonical grid: template tw x th plus `pad` canonical px each side."""
    sx = bw / tw; sy = bh / th
    lvl = int(np.clip(np.floor(np.log2(max(min(sx, sy), 1.0))), 0, len(pyr) - 1))
    k = 2 ** lvl
    u = (np.arange(-pad, tw + pad) - tw / 2 + 0.5) * sx
    v = (np.arange(-pad, th + pad) - th / 2 + 0.5) * sy
    X = (cx + u[None, :]) / k - 0.5 * (k > 1) * (1 - 1 / k)
    Y = (cy + v[:, None]) / k - 0.5 * (k > 1) * (1 - 1 / k)
    X = np.broadcast_to(X, (len(v), len(u))); Y = np.broadcast_to(Y, (len(v), len(u)))
    return bilinear(pyr[lvl], X, Y)


# ---------------------------------------------------------------- NCC
def ncc(img, tpl):
    """Zero-mean normalised cross-correlation, 'valid' mode. img HxW, tpl hxw."""
    H, W = img.shape; h, w = tpl.shape
    t = tpl - tpl.mean(); tn = np.sqrt((t * t).sum()) + 1e-6
    F = np.fft.rfft2(img, s=(H, W)); T = np.fft.rfft2(t[::-1, ::-1], s=(H, W))
    num = np.fft.irfft2(F * T, s=(H, W))[h - 1:H, w - 1:W]
    ii = np.pad(img, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    i2 = np.pad(img * img, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    def box(a):
        return a[h:, w:] - a[:-h, w:] - a[h:, :-w] + a[:-h, :-w]
    s1 = box(ii); s2 = box(i2); n = h * w
    var = np.maximum(s2 - s1 * s1 / n, 0)
    return num / (np.sqrt(var) * tn + 1e-6)


def peak_subpix(r):
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    dx = dy = 0.0
    if 0 < ix < r.shape[1] - 1:
        a, b, c = r[iy, ix - 1], r[iy, ix], r[iy, ix + 1]; den = a - 2 * b + c
        dx = 0.5 * (a - c) / den if den < 0 else 0.0
    if 0 < iy < r.shape[0] - 1:
        a, b, c = r[iy - 1, ix], r[iy, ix], r[iy + 1, ix]; den = a - 2 * b + c
        dy = 0.5 * (a - c) / den if den < 0 else 0.0
    return ix + dx, iy + dy, float(r[iy, ix])


# ---------------------------------------------------------------- tracker
def canon_size(bw, bh, long_side):
    if bw >= bh:
        return long_side, max(8, int(round(long_side * bh / bw)))
    return max(8, int(round(long_side * bw / bh))), long_side


def run(frames, box, aspect=False, coarse=32, fine=96, search=0.35, scale_pen=0.0, scale_mom=0.6,
        scales=(0.94, 0.97, 1.0, 1.03, 1.06), aspects=(0.96, 1.0, 1.04)):
    """frames: list of 2-D float arrays (tracking resolution). box: (cx,cy,w,h)
    in the same resolution.  Returns array N x 5 (cx,cy,w,h,ncc)."""
    pyrs = [pyramid(f) for f in frames]
    cx, cy, bw, bh = box
    ctw, cth = canon_size(bw, bh, coarse); ftw, fth = canon_size(bw, bh, fine)
    anc_c = sample(pyrs[0], cx, cy, bw, bh, ctw, cth, 0)
    anc_f = sample(pyrs[0], cx, cy, bw, bh, ftw, fth, 0)
    prv_c, prv_f = anc_c, anc_f
    out = [(cx, cy, bw, bh, 1.0)]
    vx = vy = 0.0; vs = 1.0
    asp = aspects if aspect else (1.0,)
    for i in range(1, len(frames)):
        p = pyrs[i]
        pcx, pcy = cx + vx, cy + vy
        pbw, pbh = bw * vs, bh * vs
        # anchor weight: trust anchor while it still matches the previous patch
        wa = float(np.clip(np.corrcoef(anc_f.ravel(), prv_f.ravel())[0, 1], 0, 1)) ** 2 * 0.5
        # ---- coarse: wide window, scale x aspect grid
        pad = int(round(max(ctw, cth) * search)) + 2
        best = None
        for s in scales:
            for a in asp:
                sw, sh = pbw * s * a, pbh * s / a
                reg = sample(p, pcx, pcy, sw, sh, ctw, cth, pad)
                r = wa * ncc(reg, anc_c) + (1 - wa) * ncc(reg, prv_c)
                x, y, v = peak_subpix(r)
                v -= scale_pen * (abs(np.log(s)) + abs(np.log(a)))
                if best is None or v > best[0]:
                    best = (v, pcx + (x - pad) * sw / ctw, pcy + (y - pad) * sh / cth, sw, sh)
        _, ccx, ccy, cw, ch = best
        # ---- fine: small window, finer scale grid
        pad = 5; best = None
        for s in (0.985, 1.0, 1.015):
            for a in ((0.99, 1.0, 1.01) if aspect else (1.0,)):
                sw, sh = cw * s * a, ch * s / a
                reg = sample(p, ccx, ccy, sw, sh, ftw, fth, pad)
                ra = ncc(reg, anc_f); rp = ncc(reg, prv_f)
                r = wa * ra + (1 - wa) * rp
                x, y, v = peak_subpix(r)
                v -= scale_pen * (abs(np.log(s)) + abs(np.log(a)))
                if best is None or v > best[0]:
                    best = (v, ccx + (x - pad) * sw / ftw, ccy + (y - pad) * sh / fth, sw, sh)
        v, ncx, ncy, nbw, nbh = best
        vx = 0.6 * (ncx - cx); vy = 0.6 * (ncy - cy); vs = 1.0 + scale_mom * (nbw / bw - 1.0)
        cx, cy, bw, bh = ncx, ncy, nbw, nbh
        prv_c = sample(p, cx, cy, bw, bh, ctw, cth, 0)
        prv_f = sample(p, cx, cy, bw, bh, ftw, fth, 0)
        out.append((cx, cy, bw, bh, v))
    return np.array(out)


# ---------------------------------------------------------------- point / affine tracker
def corners_score(img, r=3):
    """Shi-Tomasi min-eigenvalue map (box window 2r+1)."""
    gy, gx = np.gradient(img)
    def boxf(a):
        k = 2 * r + 1
        ii = np.pad(a, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        o = ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k]
        return np.pad(o, ((r, r), (r, r)))
    a, b, c = boxf(gx * gx), boxf(gx * gy), boxf(gy * gy)
    return 0.5 * (a + c) - np.sqrt(0.25 * (a - c) ** 2 + b * b)


def pick_points(img, quad, n=48, spacing=10, margin=12, mask_bright=0.97):
    """Best-textured points inside the quad (4x2 array), spaced apart."""
    H, W = img.shape
    sc = corners_score(img)
    sc[img > mask_bright] = 0                       # skip blown highlights (headlight bloom)
    yy, xx = np.mgrid[0:H, 0:W]
    inside = np.ones_like(img, bool)
    for i in range(4):                              # convex quad test
        (x0, y0), (x1, y1) = quad[i], quad[(i + 1) % 4]
        inside &= ((x1 - x0) * (yy - y0) - (y1 - y0) * (xx - x0)) >= 0
    inside &= (xx > margin) & (xx < W - margin) & (yy > margin) & (yy < H - margin)
    sc = np.where(inside, sc, 0)
    pts = []
    order = np.argsort(sc.ravel())[::-1]
    thr = sc.max() * 0.02
    for k in order[:20000]:
        if sc.flat[k] <= thr or len(pts) >= n: break
        y, x = divmod(k, W)
        if all((x - px) ** 2 + (y - py) ** 2 >= spacing ** 2 for px, py in pts):
            pts.append((x, y))
    return np.array(pts, float).reshape(-1, 2)


def fit_affine(p, q, w=None, iters=4):
    """Robust (IRLS, Tukey) affine q ~ A p + b.  Returns 2x3 M and inlier weights."""
    n = len(p); w0 = np.ones(n) if w is None else w
    X = np.hstack([p, np.ones((n, 1))])
    wt = w0.copy()
    for _ in range(iters):
        Wm = X * wt[:, None]
        M = np.linalg.lstsq(Wm.T @ X + 1e-6 * np.eye(3), Wm.T @ q, rcond=None)[0].T
        r = np.linalg.norm(X @ M.T - q, axis=1)
        s = max(1.4826 * np.median(r), 0.5)
        u = r / (4.685 * s)
        wt = w0 * np.where(u < 1, (1 - u * u) ** 2, 0)
    return M, wt


def run_points(frames, box, patch=10, search=14, n=48, model='affine'):
    """KLT-style: many small NCC patches, robust affine fit per frame, box
    corners carried through the accumulated transform.  Handles perspective
    squeeze, partial exit from frame and partial occlusion.
    Returns N x 5 (cx,cy,w,h,quality) and the quads N x 4 x 2."""
    cx, cy, bw, bh = box
    quad = np.array([[cx - bw / 2, cy - bh / 2], [cx + bw / 2, cy - bh / 2],
                     [cx + bw / 2, cy + bh / 2], [cx - bw / 2, cy + bh / 2]])
    H, W = frames[0].shape
    pts = pick_points(frames[0], quad, n)
    out = [(cx, cy, bw, bh, 1.0)]; quads = [quad.copy()]
    Mv = np.array([[1, 0, 0], [0, 1, 0]], float)     # last inter-frame motion (prediction)
    for i in range(1, len(frames)):
        a, b = frames[i - 1], frames[i]
        pred = pts @ Mv[:, :2].T + Mv[:, 2]
        got, keep, sc = [], [], []
        for j, (p, pr) in enumerate(zip(pts, pred)):
            x0, y0 = int(round(p[0])), int(round(p[1]))
            px, py = int(round(pr[0])), int(round(pr[1]))
            if not (patch <= x0 < W - patch and patch <= y0 < H - patch): continue
            R = patch + search
            if not (R <= px < W - R and R <= py < H - R): continue
            t = a[y0 - patch:y0 + patch + 1, x0 - patch:x0 + patch + 1]
            if t.std() < 0.01: continue
            reg = b[py - R:py + R + 1, px - R:px + R + 1]
            r = ncc(reg, t)
            x, y, v = peak_subpix(r)
            if v < 0.6: continue
            got.append((px - search + x + (p[0] - x0), py - search + y + (p[1] - y0)))
            keep.append(j); sc.append(v)
        if len(keep) < 6:                         # lost: hold last motion
            M = Mv; qual = 0.0; inl = np.zeros(0)
            newpts = pred
        else:
            P = pts[keep]; Q = np.array(got)
            if model == 'similarity':
                M, inl = fit_affine(P, Q, np.array(sc) ** 2)
                # project to similarity
                A = M[:, :2]; s = np.sqrt(abs(np.linalg.det(A))); M[:, :2] = s * np.eye(2)
            else:
                M, inl = fit_affine(P, Q, np.array(sc) ** 2)
            qual = float((inl > 0.1).mean() * np.mean(sc)) * min(1.0, len(keep) / 12)
            newpts = Q[inl > 0.1]
        quad = quad @ M[:, :2].T + M[:, 2]
        Mv = M
        # re-seed when the point set thins out
        if len(newpts) < n * 0.6:
            fresh = pick_points(b, quad, n)
            pts = fresh if len(fresh) >= len(newpts) else newpts
        else:
            pts = np.asarray(newpts)
        x0, y0 = quad[:, 0].min(), quad[:, 1].min(); x1, y1 = quad[:, 0].max(), quad[:, 1].max()
        out.append(((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, qual))
        quads.append(quad.copy())
    return np.array(out), np.array(quads)


# ---------------------------------------------------------------- smoothing
def smooth_series(y, w, half=4, deg=2):
    """Confidence-weighted local polynomial regression (zero phase)."""
    n = len(y); out = np.empty(n)
    t = np.arange(n, dtype=float)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        tt = t[lo:hi] - i
        k = (1 - (np.abs(tt) / (half + 1)) ** 3) ** 3 * w[lo:hi]   # tricube x conf
        d = min(deg, hi - lo - 1)
        A = np.vander(tt, d + 1)
        AW = A * k[:, None]
        coef = np.linalg.lstsq(AW.T @ A + 1e-9 * np.eye(d + 1), AW.T @ y[lo:hi], rcond=None)[0]
        out[i] = coef[-1]
    return out


def track_shot(video, ffmpeg, f0, f1, box_full, method='template', aspect=False, ds=2, half=4, **kw):
    """method 'template' = whole-box NCC with scale search (rigid, sharp logos);
    method 'points' = many small patches + robust affine (object turns / squeezes /
    partly leaves frame).  Returns the JSON dict for one shot."""
    frames, (W, H) = decode_gray(video, ffmpeg, f0, f1, ds)
    x, y, w, h = [v / ds for v in box_full]
    quads = None
    if method == 'points':
        fwd, quads = run_points(frames, (x + w / 2, y + h / 2, w, h), **kw)
        bwd, _ = run_points(frames[::-1], tuple(fwd[-1, :4]), **kw)
        bwd = bwd[::-1]
    else:
        fwd = run(frames, (x + w / 2, y + h / 2, w, h), aspect=aspect, **kw)
        # backward pass from the forward end-state -> consistency check
        bwd = run(frames[::-1], tuple(fwd[-1, :4]), aspect=aspect, **kw)[::-1]
    diag = np.hypot(fwd[:, 2], fwd[:, 3])
    fb = np.hypot(fwd[:, 0] - bwd[:, 0], fwd[:, 1] - bwd[:, 1]) / diag     # relative
    fb_conf = np.exp(-(fb / 0.05) ** 2)          # 5 % of the box diagonal ~ 0.37
    conf = np.clip(fwd[:, 4], 0, 1) * (0.5 + 0.5 * fb_conf)
    # smooth in full-res units
    cx, cy = fwd[:, 0] * ds, fwd[:, 1] * ds
    lw, lh = np.log(fwd[:, 2] * ds), np.log(fwd[:, 3] * ds)
    wt = 0.05 + conf
    scx, scy = smooth_series(cx, wt, half), smooth_series(cy, wt, half)
    slw, slh = np.exp(smooth_series(lw, wt, half)), np.exp(smooth_series(lh, wt, half))
    sq = None
    if quads is not None:
        q = quads.reshape(len(quads), 8) * ds
        sq = np.stack([smooth_series(q[:, k], wt, half) for k in range(8)], 1).reshape(-1, 4, 2)
    fr = []
    for i in range(len(fwd)):
        f = f0 + i
        d = dict(f=f, t=round(f / FPS, 5),
                 x=round(scx[i] - slw[i] / 2, 2), y=round(scy[i] - slh[i] / 2, 2),
                 w=round(slw[i], 2), h=round(slh[i], 2), conf=round(float(conf[i]), 3),
                 ncc=round(float(fwd[i, 4]), 3), fb=round(float(fb[i]), 4),
                 raw=[round(cx[i] - np.exp(lw[i]) / 2, 2), round(cy[i] - np.exp(lh[i]) / 2, 2),
                      round(float(np.exp(lw[i])), 2), round(float(np.exp(lh[i])), 2)])
        if sq is not None:
            d['quad'] = [[round(float(a), 1), round(float(b), 1)] for a, b in sq[i]]
        fr.append(d)
    return dict(video=os.path.basename(video), fps=FPS, size=[W, H], f0=f0, f1=f1, method=method,
                t0=round(f0 / FPS, 5), t1=round((f1 + 1) / FPS, 5), frames=fr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True); ap.add_argument('--ffmpeg', default='ffmpeg')
    ap.add_argument('--name', required=True)
    ap.add_argument('--f0', type=int, required=True); ap.add_argument('--f1', type=int, required=True)
    ap.add_argument('--box', required=True, help='x,y,w,h full-res px on frame f0')
    ap.add_argument('--aspect', action='store_true', help='also search aspect ratio (perspective turn)')
    ap.add_argument('--method', default='template', choices=['template', 'points'])
    ap.add_argument('--scale-pen', type=float, default=0.0, help='NCC penalty per unit |log scale| change (resists scale drift)')
    ap.add_argument('--scale-mom', type=float, default=0.6, help='scale momentum for prediction')
    ap.add_argument('--half', type=int, default=4, help='smoothing half-window in frames')
    ap.add_argument('--out', default='tracks.json')
    a = ap.parse_args()
    box = [float(v) for v in a.box.split(',')]
    res = track_shot(a.video, a.ffmpeg, a.f0, a.f1, box, method=a.method, aspect=a.aspect, half=a.half,
                      **({'scale_pen': a.scale_pen, 'scale_mom': a.scale_mom} if a.method == 'template' else {}))
    db = json.load(open(a.out)) if os.path.exists(a.out) else {}
    db[a.name] = res
    json.dump(db, open(a.out, 'w'), indent=1)
    c = [f['conf'] for f in res['frames']]; fb = [f['fb'] for f in res['frames']]
    print(f"{a.name}: {len(c)} frames  conf min {min(c):.2f} mean {np.mean(c):.2f}  "
          f"FB err max {max(fb)*100:.1f}% of diag")


if __name__ == '__main__':
    main()
