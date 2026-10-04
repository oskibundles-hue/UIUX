"""Composite one style-frame direction: base -> FD glass panels (cut out of the picture: blurred + darkened, from the
layer's FX sidecar) -> vignette + grain -> the motion layer (premultiplied average from kcapture) on top.

  python3 compose30.py <A|B|C> video <layerdir>             raw RGB24 frames on stdout (pipe to ffmpeg)
  python3 compose30.py <A|B|C> still <layerdir> <name> <out.jpg>   one frame (name = kcapture 'at' name, e.g. t1.668)
  python3 compose30.py <A|B|C> frame <layerdir> <i> <out.png>      frame i of a 'seq' layer (the hero stills)

Base per direction: A = plate a33, C = plate c20 (graded R2, 1.0x). B = a dark ambient made from the clip on the
card nearest the lens (FX.amb = [[plate, weight], ...]): blurred 60 px, darkened to 22 %, so the space is lit by the footage.
"""
import json, math, os, sys
from functools import lru_cache
import numpy as np
import cv2

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{T}/lib")
import fx  # noqa: E402

W, H = 1080, 1920
OFPS = 30000 / 1001
PLATE = {"A": "a33", "C": "c20"}
GAMMA = json.load(open(f"{T}/.work/H/gamma.json"))["gamma"] if os.path.exists(f"{T}/.work/H/gamma.json") else {}


@lru_cache(maxsize=8)
def plate(key, k):
    k = max(0, min(89, k))
    img = cv2.imread(f"{T}/plates/{key}/{key}/{k:05d}.jpg")
    return img[..., ::-1].astype(np.float32) / 255.0


@lru_cache(maxsize=8)
def ambient(key, k):
    im = plate(key, k)
    sm = cv2.resize(im, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), 8)
    return cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR) * 0.22


def rrect_mask(x, y, w, h, r, feather=2.0):
    r = max(r, 1.5)                                    # v3 fix: r = 0 gave a 50 % mask (the v2 end lead-in half-darkened)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = np.clip(xx, x + r, x + w - r); cy = np.clip(yy, y + r, y + h - r)
    d = np.hypot(xx - cx, yy - cy) - r
    return np.clip(0.5 - d / feather, 0, 1)[..., None]


def glass(img, g):
    x, y, w, h = [int(round(g[k])) for k in ("x", "y", "w", "h")]
    pad = 80
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    sub = img[y0:y1, x0:x1]
    bl = cv2.GaussianBlur(sub, (0, 0), g.get("blur", 22)) * (1 - g.get("dark", 0.4))
    out = img.copy()
    m = rrect_mask(x, y, w, h, g.get("r", 16))[y0:y1, x0:x1]
    out[y0:y1, x0:x1] = sub * (1 - m) + bl * m
    # a hairline of light on the panel's top edge, faded at both ends (glass, not a border)
    yy = y
    if 0 <= yy < H:
        ramp = np.clip(np.minimum(np.arange(w) / 80.0, (w - np.arange(w)) / 80.0), 0, 1)[:, None] * 0.10 * (g.get("dark", .4) / .4)
        seg = out[yy, x:x + w]
        out[yy, x:x + w] = seg * (1 - ramp) + ramp
    return out


@lru_cache(maxsize=16)
def pplate(rel, k):
    img = cv2.imread(f"{T}/plates/{rel}/{k:05d}.jpg")
    return img[..., ::-1].astype(np.float32) / 255.0


@lru_cache(maxsize=12)
def pambient(rel, k):
    sm = cv2.resize(pplate(rel, k), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), 8)
    return cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR) * 0.22


@lru_cache(maxsize=1)
def endcard():
    im = cv2.imread(f"{T}/logos/fd_endcard__v4_nogrid_9x16.jpg")
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float32) / 255.0


def base(d, i, fxd):
    if d in ("F", "G", "H"):                           # full ads: FX tells the base per frame
        if fxd.get("card"):
            return endcard()
        if fxd.get("ground"):                          # the hook's black ground = the end card's ground #08080A
            return np.full((H, W, 3), np.float32([8, 8, 10]) / 255.0)
        if fxd.get("base"):
            img = pplate(fxd["base"][0], int(fxd["base"][1]))
            if d == "H":                               # v3: gentle per-shot exposure match (gamma only; black and white points kept)
                gm = GAMMA.get(fxd["base"][0].split("/")[-1], 1.0)
                if abs(gm - 1) > 1e-3:
                    img = np.power(np.clip(img, 0, 1), gm)
            return img
        img = np.zeros((H, W, 3), np.float32)
        for rel, wgt, k in fxd.get("amb", []):
            if wgt > 1e-3:
                img += pambient(rel, int(k)) * wgt
        return img
    if d in PLATE:
        return plate(PLATE[d], i)
    amb = fxd.get("amb") or [["b38", 1.0]]
    img = np.zeros((H, W, 3), np.float32)
    for key, wgt in amb:
        if wgt > 1e-3:
            img += ambient(key, i) * wgt
    return img


def finish(d, i, fxd, layer):
    img = base(d, i, fxd)
    if fxd.get("card"):                                # the approved end card itself: no vignette, no grain, no layer
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    if fxd.get("ground"):                              # clean black ground under the hook: no vignette or grain
        a = layer[..., 3:4].astype(np.float32) / 255.0 if layer is not None else 0
        if layer is not None:
            img = img * (1 - a) + (layer[..., :3].astype(np.float32) / 255.0) * a
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    for g in fxd.get("glass", []):
        if g.get("dark", 0) > 0.003:
            img = glass(img, g)
    img = fx.vignette(img, 0.30 if (d in PLATE or fxd.get("base")) else 0.18)
    img = fx.grain(img, i, amount=0.024)
    if layer is not None:
        a = layer[..., 3:4].astype(np.float32) / 255.0
        img = np.clip(img, 0, 1) * (1 - a) + (layer[..., :3].astype(np.float32) / 255.0) * a
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def load_layer(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im[..., [2, 1, 0, 3]]


def fx_of(p):
    return json.load(open(p)) if os.path.exists(p) else {}


if __name__ == "__main__":
    d, mode, L = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "video":
        n = len([f for f in os.listdir(L) if f.endswith(".png")])
        for i in range(n):
            nm = f"{i:05d}"
            sys.stdout.buffer.write(finish(d, i, fx_of(f"{L}/fx_{nm}.json"), load_layer(f"{L}/{nm}.png")).tobytes())
    elif mode == "frame":                                  # hero: the exact frame of the motion test, lossless PNG
        i, out = int(sys.argv[4]), sys.argv[5]; nm = f"{i:05d}"
        img = finish(d, i, fx_of(f"{L}/fx_{nm}.json"), load_layer(f"{L}/{nm}.png"))
        cv2.imwrite(out, img[..., ::-1]); print(out, "frame", i)
    else:
        name, out = sys.argv[4], sys.argv[5]
        i = int(round(float(name[1:]) * OFPS))
        img = finish(d, i, fx_of(f"{L}/fx_{name}.json"), load_layer(f"{L}/{name}.png"))
        cv2.imwrite(out, img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 93])
        print(out, "frame", i)
