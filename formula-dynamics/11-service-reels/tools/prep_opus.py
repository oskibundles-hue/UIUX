#!/usr/bin/env python3
"""Prepare media for scenes/p1-opus-carousel.html.

  python3 tools/prep_opus.py <src_dir>

<src_dir> holds the shop photos and the raw Higgsfield clips as pulled from
Dropbox:  <src>/tan/IMG_*.jpg, <src>/black/IMG_*.jpg,
          <src>/clips/tan_raw.mp4, <src>/clips/black_raw.mp4

Writes media/opus/ (git-ignored): 1600 px photos, the clip frames for the
moving slide, and manifest.js with each photo's product box so the scene can
frame the part without hand-tuned crops.
"""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "media", "opus")
FFMPEG = "/usr/bin/ffmpeg"
PHOTO_W = 1600

# Seedance multishot clips run in 3 s shots. Shots 6, 7 and 9 carry the red
# glow and sparks the approved ads cut, and shot 5 drifts off the part's shape
# (round, ribbed tips), so the moving slide uses one clean shot, trimmed 0.2 s
# inside each cut. Tan takes shot 2 (the turntable): in its shot 3 the OPUS
# engraving slides in cut off at the right edge from about 8 s.
CLIP_WINDOWS = {"tan": [(3.2, 5.8)], "black": [(6.2, 8.8)]}
CLIP_FPS = 24


def product_box(im):
    """Bounding box of the part against the light grey seamless.

    The dark pass finds the body; the tan finish and the inlet read lighter, so the top
    comes from a second pass with the backdrop's falloff fitted out, kept to the body's columns.
    """
    W, H = im.size
    sm = np.asarray(im.resize((W // 8, H // 8))).astype(float).mean(2)
    edge = np.concatenate([sm[:20].ravel(), sm[:, :20].ravel(), sm[:, -20:].ravel()])
    ys, xs = np.where(sm < np.median(edge) - 40)
    x0, x1 = np.percentile(xs, [0.5, 99.5])
    y0, y1 = np.percentile(ys, [0.5, 99.5])
    x0, y0, x1, y1 = x0 * 8, y0 * 8, x1 * 8, y1 * 8
    k = W / 400
    g = np.asarray(im.resize((400, round(H / k)))).astype(float).mean(2)
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]
    rim = np.zeros_like(g, bool); rim[:12] = rim[-12:] = True; rim[:, :12] = rim[:, -12:] = True
    A = np.stack([np.ones(rim.sum()), xx[rim], yy[rim], xx[rim] ** 2, yy[rim] ** 2, xx[rim] * yy[rim]], 1)
    co, *_ = np.linalg.lstsq(A, g[rim], rcond=None)
    bg = co[0] + co[1] * xx + co[2] * yy + co[3] * xx ** 2 + co[4] * yy ** 2 + co[5] * xx * yy
    off = np.abs(g - bg) > 18
    tops = [y for y in range(0, h - 15, 16) for x in range(0, w - 15, 16)
            if off[y:y + 16, x:x + 16].mean() > 0.5 and x0 - 64 * k <= x * k <= x1 + 64 * k]
    if tops:
        y0 = min(y0, min(tops) * k)
    return [int(x0), int(y0), int(x1), int(y1)]


def main(src):
    manifest = {}
    for colour in ("tan", "black"):
        d = os.path.join(OUT, colour)
        os.makedirs(os.path.join(d, "clip"), exist_ok=True)
        photos = {}
        for f in sorted(glob.glob(os.path.join(src, colour, "IMG_*.jpg"))):
            im = Image.open(f).convert("RGB")
            k = PHOTO_W / im.size[0]
            box = [round(v * k) for v in product_box(im)]
            im = im.resize((PHOTO_W, round(im.size[1] * k)), Image.LANCZOS)
            name = os.path.basename(f)
            im.save(os.path.join(d, name), quality=92)
            photos[name[:-4]] = {"w": im.size[0], "h": im.size[1], "box": box}
        for old in glob.glob(os.path.join(d, "clip", "*.jpg")):
            os.remove(old)
        sel = "+".join(f"between(t,{a},{b})" for a, b in CLIP_WINDOWS[colour])
        subprocess.run([FFMPEG, "-v", "error", "-y",
                        "-i", os.path.join(src, "clips", f"{colour}_raw.mp4"),
                        "-vf", f"select='{sel}',scale=1080:1920:flags=lanczos,unsharp=5:5:0.5",
                        "-vsync", "vfr", "-q:v", "3",
                        os.path.join(d, "clip", "f_%04d.jpg")], check=True)
        n = len(glob.glob(os.path.join(d, "clip", "*.jpg")))
        manifest[colour] = {"photos": photos, "clip": {"frames": n, "fps": CLIP_FPS}}
        print(f"{colour}: {len(photos)} photos, {n} clip frames")
    with open(os.path.join(OUT, "manifest.js"), "w") as fh:
        fh.write("window.OPUS_MEDIA = " + json.dumps(manifest, indent=1) + ";\n")


if __name__ == "__main__":
    main(sys.argv[1])
