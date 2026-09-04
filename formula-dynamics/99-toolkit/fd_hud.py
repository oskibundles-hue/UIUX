"""
Formula Dynamics Performance - HUD component set.

A technical-annotation layer: elbow callouts that point at parts of the car,
a persistent title block, and a ticker strip. The layout language follows the
convention used across automotive spec videos - thin leader lines, indexed
labels, a bracketed name plate - rebuilt from scratch in the Formula Dynamics
palette and typeface rather than copied from any template's artwork.

Every component returns a full-frame RGBA image at canvas size, so it drops
onto a timeline in position like the rest of the kit.
"""

from PIL import Image, ImageDraw, ImageFilter

import fd_brand as B
import fd_render as R


# --------------------------------------------------------------------------
def _scrim(canvas, top, height, strength=150, blur=0.05):
    """Soft band used behind persistent furniture so it survives any shot."""
    fw, fh = B.CANVASES[canvas]
    band = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    y0, h = int(fh * top), int(fh * height)
    for i in range(h):
        a = int(strength * (1 - abs(i - h / 2) / (h / 2)) ** 0.8)
        d.line([(0, y0 + i), (fw, y0 + i)], fill=(0, 0, 0, a))
    return band.filter(ImageFilter.GaussianBlur(round(fw * blur)))


# --------------------------------------------------------------------------
def callout(canvas, index, label, anchor, side="left", drop=0.11, run=0.16):
    """An indexed leader line pointing at a feature.

    anchor - (x, y) as fractions of the frame; the point on the car.
    side   - which way the label runs from the anchor.
    drop   - vertical leg length, as a fraction of frame height.
    run    - horizontal leg length, as a fraction of frame width.

    Shape: a small open square on the feature, a vertical leg, then a
    horizontal leg to the label. The elbow keeps the line off the subject
    instead of crossing it.
    """
    fw, fh = B.CANVASES[canvas]
    im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = fw / 1080.0

    ax, ay = anchor[0] * fw, anchor[1] * fh
    dirn = -1 if side == "left" else 1
    ey = ay + drop * fh                      # elbow
    lx = ax + dirn * run * fw                # label end

    white = B.rgb(B.WHITE) + (235,)
    lw = max(2, round(2.2 * s))

    d.line([ax, ay, ax, ey], fill=white, width=lw)
    d.line([ax, ey, lx, ey], fill=white, width=lw)

    # Open square on the feature, filled marker at the label end.
    r = round(7 * s)
    d.rectangle([ax - r, ay - r, ax + r, ay + r], outline=white, width=lw)
    r2 = round(5 * s)
    d.rectangle([lx - r2, ey - r2, lx + r2, ey + r2],
                fill=B.rgb(B.RED) + (255,))

    idx = R.text(index, round(26 * s), B.RED, tracking=0.16)
    txt = R.text(label, round(34 * s), B.WHITE, tracking=0.10)
    gap = round(10 * s)
    pad = round(16 * s)

    block_w = idx.width + gap + txt.width
    tx = lx - block_w - pad if dirn < 0 else lx + pad
    ty = ey - round(24 * s)

    # A short tick under the label ties it to the leader line.
    d.line([tx, ty + txt.height + round(8 * s),
            tx + block_w, ty + txt.height + round(8 * s)],
           fill=B.rgb(B.RED) + (255,), width=max(2, round(2 * s)))

    R.paste(im, idx, tx, ty + round(6 * s))
    R.paste(im, txt, tx + idx.width + gap, ty)
    return im


# --------------------------------------------------------------------------
def title_block(canvas, name, subline=None, y=0.705):
    """Persistent lower name plate with a bracket device.

    Sits above the ticker and clears the platform keep-out band.
    """
    fw, fh = B.CANVASES[canvas]
    im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    s = fw / 1080.0
    x0 = round(fw * 0.075)
    top = round(fh * y)

    im.alpha_composite(_scrim(canvas, y - 0.035, 0.16, 130))
    d = ImageDraw.Draw(im)

    name_im = R.text(name, round(84 * s), B.WHITE, tracking=0.02)
    sub_im = R.text(subline, round(38 * s), B.WHITE, tracking=0.14) if subline else None

    # The bracket carries the actual FD monogram rather than an abstract
    # wedge. On footage that swings from near-black to blown-out sky, no
    # corner logo bug survives at the top of frame - putting the mark inside
    # the scrimmed title block keeps it legible on every shot.
    bw, bh = round(78 * s), round(78 * s)
    lw = max(2, round(3 * s))
    d.line([x0, top, x0, top + bh], fill=B.rgb(B.WHITE) + (255,), width=lw)
    d.line([x0, top, x0 + bw, top], fill=B.rgb(B.WHITE) + (255,), width=lw)
    mark = R.logo("fd-icon-mark-only--white", width=round(58 * s))
    R.paste(im, mark, x0 + round(14 * s), top + round(16 * s))

    tx = x0 + round(108 * s)
    R.paste(im, name_im, tx, top - round(6 * s))

    y2 = top - round(6 * s) + name_im.height + round(12 * s)
    if sub_im:
        R.paste(im, sub_im, tx, y2)
        # The brand stripe replaces the template's hatched rule.
        R.paste(im, R.accent_stripe(round(fw * 0.30), round(9 * s)),
                tx + sub_im.width + round(24 * s), y2 + round(10 * s))
    return im


# --------------------------------------------------------------------------
def ticker(canvas, segments, y=0.845):
    """Full-width strip of short segments separated by red slashes."""
    fw, fh = B.CANVASES[canvas]
    im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    s = fw / 1080.0
    im.alpha_composite(_scrim(canvas, y - 0.022, 0.075, 120, 0.03))

    size = round(30 * s)
    parts, total = [], 0
    sep = R.text("/////", size, B.RED, tracking=0.02)
    for i, seg in enumerate(segments):
        if i:
            parts.append(sep)
            total += sep.width + round(22 * s) * 2
        t = R.text(seg, size, B.WHITE, tracking=0.12)
        parts.append(t)
        total += t.width

    x = (fw - total) // 2
    cy = round(fh * y)
    for p in parts:
        R.paste(im, p, x, cy, anchor="lm")
        x += p.width + (round(22 * s) if p is not parts[-1] else 0)
    return im
