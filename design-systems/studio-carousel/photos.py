"""Real-photo helpers for the studio carousel: the photo build uses these instead of renders.

    python3 photos.py cuts <spec.json>   # cut out every entry in spec["cuts"] that isn't cut already

generate.py calls the rest from the spec (see README.md, "The photo build"). Everything here works on
photos already supplied: nothing is generated. Needs numpy, Pillow and scipy; `cuts` also needs rembg.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from scipy import ndimage

MAT = (246, 246, 248)   # the thin white mat round a framed photo
MAT_PX = 6


def photo(path):
    """Open a photo the way it was shot: phone photos carry their rotation in EXIF, not in the pixels."""
    return ImageOps.exif_transpose(Image.open(path)).convert('RGB')


def redact(im, box):
    """Cover a plate: collapse its box to a 6x3 colour field with a feathered edge.
    A Gaussian blur isn't enough, because the letters stay readable through it."""
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1)
    if x1 <= x0 or y1 <= y0:
        return im
    field = im.crop((x0, y0, x1, y1)).resize((6, 3), Image.BOX).resize((x1 - x0, y1 - y0), Image.BILINEAR)
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rectangle((x0, y0, x1, y1), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(max(4, (x1 - x0) // 25)))
    full = im.copy()
    full.paste(field, (x0, y0))
    return Image.composite(full, im, m)


def cover(im, w, h, focus=(0.5, 0.5)):
    """Scale to cover w x h and crop around the focus point (fractions of the photo)."""
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x = int(min(max(0, focus[0] * im.width - w / 2), im.width - w))
    y = int(min(max(0, focus[1] * im.height - h / 2), im.height - h))
    return im.crop((x, y, x + w, y + h))


def panel(img, pic, x, y, w, h, focus=(0.5, 0.5), shadow=True, shadow_col=(80, 80, 86)):
    """A clean framed photo on the studio backdrop: thin white mat, soft floor shadow.
    For shop photos a cutout would leave rough (lifts, clutter, people). Returns the frame's box."""
    p = cover(pic, w, h, focus)
    if shadow:
        sh = Image.new('L', img.size, 0)
        ImageDraw.Draw(sh).rectangle([x + 10, y + 28, x + w - 10, y + h + 18], fill=95)
        sh = sh.filter(ImageFilter.GaussianBlur(26))
        img.paste(Image.new('RGB', img.size, tuple(shadow_col)), (0, 0), sh)
    frame = [x - MAT_PX, y - MAT_PX, x + w + MAT_PX, y + h + MAT_PX]
    ImageDraw.Draw(img).rectangle([frame[0], frame[1], frame[2] - 1, frame[3] - 1], fill=MAT)
    img.paste(p, (x, y))
    return frame


def clean_cut(src, fade=0.0, cut_right=None, cut_top=0, solid=40):
    """Keep the largest solid piece of a rembg cutout (drops stray ghosts of lights and clutter).
    src: a path or an image.
    fade: share of the height faded out at the bottom (hides a flat crop edge).
    cut_right: (x, y0, y1), rows y0..y1 are trimmed at x with a short feathered edge (drops a ragged end).
    cut_top: rows cleared at the top (something loose running off the crop).
    solid: alpha below this is cleared (raise it to drop translucent haze)."""
    im = (Image.open(src) if isinstance(src, (str, os.PathLike)) else src).convert('RGBA')
    a = np.array(im.getchannel('A')).astype(np.float32)
    if cut_right:
        cx, y0, y1 = cut_right
        x = np.arange(a.shape[1])
        a[y0:y1] *= np.clip((cx - x) / 70.0, 0, 1)[None, :]
    if cut_top:
        a[:cut_top] = 0
    lab, k = ndimage.label(a > 60)
    if not k:
        raise ValueError('clean_cut: nothing solid left in the cutout')
    sizes = ndimage.sum(np.ones_like(a), lab, range(1, k + 1))
    keep = ndimage.binary_fill_holes(lab == (int(np.argmax(sizes)) + 1))
    a = np.where(keep, a, 0)
    a = np.where(a < solid, 0, a)
    if fade:
        ys = np.where(a.max(1) > 0)[0]
        top, bot = ys.min(), ys.max()
        start = bot - fade * (bot - top)
        ramp = np.clip((bot - np.arange(a.shape[0])) / max(1, bot - start), 0, 1)
        a = a * ramp[:, None] ** 1.4
    im.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    return im.crop(im.getchannel('A').getbbox())


def make_cuts(cuts, root='.', model='isnet-general-use'):
    """Cut subjects out of photos with rembg, once: entries whose `out` file exists are skipped.
    cuts: {name: {"file": photo path, "crop": [x0, y0, x1, y1] (optional), "out": cutout .png path}}.
    Paths are relative to root. Returns the names it cut."""
    def at(p):
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(root, p))

    need = [n for n, c in cuts.items() if not os.path.exists(at(c['out']))]
    if not need:
        return []
    from rembg import new_session, remove   # imported here so the rest runs without rembg installed
    ses = new_session(model)
    for n in need:
        c = cuts[n]
        im = photo(at(c['file']))
        if c.get('crop'):
            im = im.crop(tuple(c['crop']))
        os.makedirs(os.path.dirname(at(c['out'])), exist_ok=True)
        remove(im, session=ses).save(at(c['out']))
    return need


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != 'cuts':
        sys.exit(__doc__)
    with open(sys.argv[2]) as fh:
        spec_cuts = json.load(fh).get('cuts', {})
    print('cut', make_cuts(spec_cuts, os.path.dirname(os.path.abspath(sys.argv[2]))) or 'nothing new')
