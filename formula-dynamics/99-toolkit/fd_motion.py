#!/usr/bin/env python3
"""
Formula Dynamics - animated overlay components.

The existing overlay set is stills: one PNG, faded in and out. These four
are time-varying - each renders a frame for a given moment, so they get
written out as a PNG sequence and overlaid like any other clip.

The design language comes from the reference screen recording (a motion
piece with UI elements landing on a dense bed of sound effects). What was
taken is the *behaviour*:

    glow_burst   a mark scaling in behind a soft radial bloom
    type_on      text typed a character at a time with a block cursor
    scramble     letters resolving out of noise, left to right
    panel_rise   a card sliding up with a row of chips landing in sequence

Nothing from the reference is reproduced: no artwork, no wordmark, no
colour. Every component is drawn from fd_brand and set in Bebas Neue.

Each function takes a normalised progress p in 0..1 and returns an RGBA
image the size of the canvas.
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter

import fd_brand as B
import fd_render as R

GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/#*"


def _ease_out(p, power=3.0):
    return 1 - (1 - p) ** power


def _ease_in_out(p):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))


def _blank(canvas):
    return Image.new("RGBA", B.CANVASES[canvas], (0, 0, 0, 0))


# --------------------------------------------------------------------------
def glow_burst(canvas, p, text=None, y=0.42):
    """A red bloom opening behind the FD monogram, which scales into place.

    The bloom is drawn at a low resolution and scaled up - a real gaussian
    over a 1080x1920 frame costs about a second a frame, and the result is
    indistinguishable once it is this soft.
    """
    im = _blank(canvas)
    fw, fh = im.size
    e = _ease_out(p, 2.4)

    small = 96
    g = Image.new("RGBA", (small, small), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    r = small * 0.44 * (0.35 + 0.65 * e)
    cx = cy = small / 2
    steps = 22
    for i in range(steps, 0, -1):
        f = i / steps
        a = int(150 * (1 - f) ** 2.1 * min(1.0, p * 2.2))
        gd.ellipse([cx - r * f, cy - r * f, cx + r * f, cy + r * f],
                   fill=B.rgb(B.RED) + (a,))
    g = g.filter(ImageFilter.GaussianBlur(small * 0.06))
    side = int(fw * 1.25)
    im.alpha_composite(g.resize((side, side), Image.LANCZOS),
                       (int(fw / 2 - side / 2), int(fh * y - side / 2)))

    mark = R.logo("fd-icon-mark-only--white",
                  width=int(fw * 0.30 * (0.72 + 0.28 * e)))
    mark.putalpha(mark.getchannel("A").point(lambda v: int(v * min(1.0, p * 3))))
    R.paste(im, mark, fw // 2, int(fh * y), anchor="cm")

    if text and p > 0.45:
        q = min(1.0, (p - 0.45) / 0.4)
        lab = R.text(text, int(fh * 0.030), B.WHITE, tracking=0.16)
        lab.putalpha(lab.getchannel("A").point(lambda v: int(v * q)))
        R.paste(im, lab, fw // 2, int(fh * y + fw * 0.20 + fh * 0.012 * (1 - q)),
                anchor="ct")
    return im


# --------------------------------------------------------------------------
def type_on(canvas, p, text, y=0.44, size=0.052, color=B.WHITE, cursor=True):
    """Text typed one character at a time, with a block cursor.

    Held on the last character for the final 15% so the line can be read
    before whatever follows it.
    """
    im = _blank(canvas)
    fw, fh = im.size
    shown = text[:max(0, min(len(text), round(len(text) * min(1.0, p / 0.85))))]
    if not shown and not cursor:
        return im

    size_px = int(fh * size)
    body = R.text(shown, size_px, color, tracking=0.02) if shown else None
    w = body.width if body else 0
    if cursor and (p < 0.85 or int(p * 14) % 2 == 0):
        cw = int(size_px * 0.46)
        cur = Image.new("RGBA", (cw, int(size_px * 0.94)), B.rgb(B.RED) + (255,))
    else:
        cur = None

    total = w + (cur.width + int(size_px * 0.10) if cur else 0)
    x = fw // 2 - total // 2
    if body:
        R.paste(im, body, x, int(fh * y), anchor="lm")
    if cur:
        R.paste(im, cur, x + w + int(size_px * 0.10), int(fh * y), anchor="lm")
    return im


# --------------------------------------------------------------------------
def scramble(canvas, p, text, y=0.44, size=0.052, seed=11):
    """Letters resolving out of noise, left to right.

    Each character locks at its own moment, spread across the first 80% of
    the window; until it locks it is a random glyph in brand red, so the
    line reads as decoding rather than as a glitch.
    """
    im = _blank(canvas)
    fw, fh = im.size
    size_px = int(fh * size)
    rng = random.Random(seed + int(p * 90))

    locked, live = [], []
    for i, ch in enumerate(text):
        at = 0.80 * (i + 1) / max(1, len(text))
        (locked if p >= at else live).append(ch)
    line = "".join(locked) + "".join(
        ch if ch == " " else rng.choice(GLYPHS) for ch in live)

    a = R.text("".join(locked), size_px, B.WHITE, tracking=0.02) if locked else None
    b = R.text(line[len(locked):], size_px, B.RED, tracking=0.02) if live else None
    total = (a.width if a else 0) + (b.width if b else 0)
    x = fw // 2 - total // 2
    if a:
        R.paste(im, a, x, int(fh * y), anchor="lm")
        x += a.width
    if b:
        R.paste(im, b, x, int(fh * y), anchor="lm")
    return im


# --------------------------------------------------------------------------
def panel_rise(canvas, p, title, chips, y=0.60):
    """A card sliding up, then chips landing in sequence.

    The chips are the reason this exists: one lands every 12% of the
    window, which is what a sound effect gets pinned to.
    """
    im = _blank(canvas)
    fw, fh = im.size
    e = _ease_out(min(1.0, p / 0.35), 3.0)

    pad = int(fw * 0.055)
    size_px = int(fh * 0.030)
    head = R.text(title, size_px, B.WHITE, tracking=0.14)
    chip_h = int(fh * 0.040)
    chip_imgs = [R.text(c, int(size_px * 0.86), B.WHITE, tracking=0.10) for c in chips]

    box_w = max(head.width, sum(c.width + pad for c in chip_imgs)) + pad * 2
    box_w = min(box_w, int(fw * 0.90))
    box_h = head.height + chip_h + pad * 2 + int(fh * 0.012)

    card = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle(
        [0, 0, box_w - 1, box_h - 1], radius=int(fh * 0.008),
        fill=(0, 0, 0, 226))
    R.paste(card, R.accent_stripe(box_w, max(2, int(fh * 0.0035))), 0, box_h - 1,
            anchor="lb")
    R.paste(card, head, pad, pad, anchor="lt")

    cx = pad
    for i, ci in enumerate(chip_imgs):
        at = 0.35 + i * 0.12
        q = _ease_out(max(0.0, min(1.0, (p - at) / 0.14)), 2.6)
        if q <= 0:
            cx += ci.width + pad
            continue
        cw = ci.width + int(pad * 0.7)
        chip = Image.new("RGBA", (cw, chip_h), (0, 0, 0, 0))
        ImageDraw.Draw(chip).rounded_rectangle(
            [0, 0, cw - 1, chip_h - 1], radius=int(chip_h * 0.22),
            fill=B.rgb(B.RED) + (int(238 * q),))
        R.paste(chip, ci, cw // 2, chip_h // 2, anchor="cm")
        chip.putalpha(chip.getchannel("A").point(lambda v: int(v * q)))
        R.paste(card, chip, cx, int(pad + head.height + fh * 0.012 + (1 - q) * fh * 0.012),
                anchor="lt")
        cx += ci.width + pad

    card.putalpha(card.getchannel("A").point(lambda v: int(v * e)))
    R.paste(im, card, fw // 2, int(fh * y + (1 - e) * fh * 0.05), anchor="ct")
    return im


COMPONENTS = {
    "glow-burst": glow_burst,
    "type-on": type_on,
    "scramble": scramble,
    "panel-rise": panel_rise,
}
