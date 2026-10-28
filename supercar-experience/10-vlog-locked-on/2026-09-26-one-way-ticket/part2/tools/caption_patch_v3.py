#!/usr/bin/env python3
"""caption_patch_v3.py -- redraw the caption over v2's own decoded picture, changing only the caption pixels.

Why: v3 round 2 (28 Oct) changes two captions that sit over shots whose plates are not rebuilt (0112, 0121: their sources are
not in the session and Omarie asked for v2's picture). v2's master is build.GRAPH: out = V(plate) * (1 - a) + C * a, with the
layer (C, a) from story.html. The old layer (v2's captions) and the new layer (v3's captions) are both captured with the
build's own code (build.capture), so for a pixel the layer change touches:
    V(plate) = (F - a_old * C_old) / (1 - a_old)           where a_old < AMAX (the plate shows through: the caption boxes are 0.86 black)
    V(plate) = filled from the recovered neighbours         where a_old >= AMAX (opaque ink: no plate information)
    new      = V(plate) * (1 - a_new) + C_new * a_new
and every other pixel keeps v2's decoded value exactly. The change mask M = the pixels where the old and new layer differ,
inside the caption band (BAND rows, so a capture difference elsewhere cannot leak in), dilated by DIL px; luma is pasted at M,
chroma at every 2x2 block that touches M. Where the plate is recovered through a 0.86 box (the box shrinks), its x7 gain
also lifts the compression noise, so that area is smoothed (SMOOTH px box blur) before compositing.

Limit (measured 28 Oct on shot 10, where the true plate is known): the plate recovered through a 0.86 box is off by
rms 22 (rms 11 after any blur), which shows as a blotchy ghost of the old words. So the patch is only used where the box
geometry is unchanged (the words move inside the same boxes, e.g. 0121 28.66 "GUYS YOU" -> "YOU GUYS"), and patch_rgb
refuses a frame where a box would be removed (EXPOSE_MAX). Where a box shrinks, the plate has to be rebuilt from the source
(lib/plate.py render_shot), as splice_v3.py does for shot 10.

    patch_rgb(F, old_png, new_png) -> (new RGB, mask, ink check);  paste_yuv(v2_yuv, new_yuv, mask) -> (yuv bytes, chroma mask)
"""
import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920
BAND = (1150, 1420)          # caption band rows (config layer.captions: yBottom 1372, two lines of 68 px Bebas)
AMAX = 0.87                  # the boxes are rgba(0,0,0,.86): anything more opaque is ink or its anti-aliased edge
INK_GROW = 2                 # ink edges: the capture's anti-aliasing is not v2's to the bit, so 2 px round the ink count as ink
DIL = 3
SMOOTH = 3
EXPOSE_MAX = 200             # pixels that were under a box in v2 and are bare plate in v3: above this, refuse


def _dilate(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def _fill(img, known, iters=400):
    """diffusion fill of the unknown pixels from the known ones (numpy only)."""
    x = img.copy(); k = known.astype(np.float32)[..., None]
    x[~known] = 0
    acc = x * k
    for _ in range(iters):
        if k.min() > 0:
            break
        s = sum(np.roll(np.roll(acc, dy, 0), dx, 1) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        n = sum(np.roll(np.roll(k, dy, 0), dx, 1) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        new = (n > 0) & (k == 0)
        acc = np.where(new, s / np.maximum(n, 1e-6), acc)
        k = np.where(new, 1.0, k)
    return acc


def layer(path):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(np.float32)
    return a[..., :3], a[..., 3:4] / 255.0


def change_mask(old_png, new_png, L=None):
    """the pixels the caption change touches: old and new layer differ, inside BAND, dilated by DIL (False elsewhere)."""
    y0, y1 = BAND
    Co, ao, Cn, an = L or (*layer(old_png), *layer(new_png))
    diff = np.zeros((H, W), bool)
    diff[y0:y1] = np.any(np.abs(np.concatenate([Co, ao * 255], 2) - np.concatenate([Cn, an * 255], 2))[y0:y1] > 0, axis=2)
    if not diff.any():
        return diff
    M = _dilate(diff, DIL); M[:y0] = False; M[y1:] = False
    return M


def patch_rgb(F, old_png, new_png):
    """F: v2 decoded frame, float RGB (H, W, 3). Returns (new RGB, mask of changed pixels, ink check)."""
    y0, y1 = BAND
    Co, ao = layer(old_png); Cn, an = layer(new_png)
    M = change_mask(old_png, new_png, (Co, ao, Cn, an))
    if not M.any():
        return F, M, None
    # work on the band only
    Fb, Cob, aob, Cnb, anb = F[y0:y1], Co[y0:y1], ao[y0:y1], Cn[y0:y1], an[y0:y1]
    exposed = int(((aob[..., 0] > 0.5) & (anb[..., 0] < 0.5)).sum())
    assert exposed <= EXPOSE_MAX, f'{exposed} px lose their caption box: the plate under them cannot be recovered from v2'
    known = ~_dilate(aob[..., 0] >= AMAX, INK_GROW)
    P = np.where(known[..., None], (Fb - aob * Cob) / np.maximum(1 - aob, 1e-3), 0)
    P = np.clip(P, 0, 255)
    P = _fill(P, known)
    # smooth where the plate was seen only through a box (gain > 2): the noise is lifted there
    gain_hi = (aob[..., 0] > 0.5) & known
    if gain_hi.any():
        sm = np.asarray(Image.fromarray(P.clip(0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(SMOOTH))).astype(np.float32)
        P = np.where(gain_hi[..., None], sm, P)
    Nb = P * (1 - anb) + Cnb * anb
    out = F.copy()
    mb = M[y0:y1]
    out[y0:y1][mb] = Nb[mb]
    # ink check: where the old layer is opaque ink, v2's pixel should be the layer's colour (the capture reproduces v2)
    ink = aob[..., 0] >= 0.999
    err = float(np.abs(Fb[ink] - Cob[ink]).mean()) if ink.any() else None
    return out, M, err


def paste_yuv(v2_yuv, new_yuv, M):
    """v2's yuv420p frame with new_yuv's samples pasted at M (luma) and at each 2x2 block touching M (chroma)."""
    ys = W * H; cs = ys // 4
    a = np.frombuffer(v2_yuv, np.uint8).copy(); b = np.frombuffer(new_yuv, np.uint8)
    Y = a[:ys].reshape(H, W); Yn = b[:ys].reshape(H, W)
    Y[M] = Yn[M]
    Mc = M.reshape(H // 2, 2, W // 2, 2).any(axis=(1, 3))
    for k in range(2):
        U = a[ys + k * cs: ys + (k + 1) * cs].reshape(H // 2, W // 2); Un = b[ys + k * cs: ys + (k + 1) * cs].reshape(H // 2, W // 2)
        U[Mc] = Un[Mc]
    return a.tobytes(), Mc
