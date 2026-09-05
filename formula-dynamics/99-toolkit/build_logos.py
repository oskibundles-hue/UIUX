#!/usr/bin/env python3
"""
Formula Dynamics Performance - logo vectorisation.

SOURCE OF TRUTH: 01-brand-core/logo-source/fd-primary-horizontal_master.png

That file is the supplied master artwork - transparent background, exact brand
hexes, no compression drift. Every lockup, PNG and overlay in the kit is built
from it, so the artwork stays sharp at any size.

    Do not trace logo artwork out of brand-guide-master.png. That raster
    carries the lockup at 596x250 px and the mark at just 149x114 px; tracing
    it and scaling up is what produced the soft, round-cornered mark that
    shipped in the first version of this kit - measured at 8.7% mean error
    against the master, against 0.84% (the anti-aliasing floor) for a trace of
    the master itself.

The master holds the primary horizontal lockup. Its four components - mark,
wordmark, accent stripe and PERFORMANCE - are detected here by occupancy, then
recomposed into the stacked and icon lockups at the arrangement those lockups
already use. Nothing is redrawn; the components are the supplied artwork.

Run:  python3 99-toolkit/build_logos.py
"""

import numpy as np
import potrace
import cairosvg
from PIL import Image

import fd_brand as B

# --- Tracing quality -------------------------------------------------------
# No source blur: the master has clean edges, and blurring them is what
# rounded the corners last time. alphamax below potrace's 1.0 default keeps
# the mark's hard corners hard.
TRACE_SCALE = 8       # supersample factor before tracing
ALPHA_MAX = 0.7       # potrace corner threshold; lower = corners stay corners
OPT_TOLERANCE = 0.2   # potrace curve-fitting tolerance; lower = closer fit
MIN_ALPHA = 0.5       # supersampled coverage threshold

PNG_WIDTHS = [1000, 2000, 4000]

VARIANTS = ["white", "black", "mono-white", "mono-black"]

# Components that carry the flipping ink (black on light, white on dark).
# The accent stripe and PERFORMANCE are fixed artwork in every variant.
FLIPPING = {"mark", "wordmark"}


# --------------------------------------------------------------------------
# Reading the master
# --------------------------------------------------------------------------
def load_master():
    path = B.BRAND_CORE / "logo-source" / "fd-primary-horizontal_master.png"
    im = Image.open(path).convert("RGBA")
    return np.asarray(im).astype(np.float32)


def bands(occupied):
    """Contiguous True runs in a 1-D boolean array, as (start, end) pairs."""
    out, start = [], None
    for i, v in enumerate(occupied):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(occupied) - 1))
    return out


def split_components(src):
    """Locate mark, wordmark, stripe and performance inside the master.

    Found by occupancy rather than hardcoded pixel boxes, so replacing the
    master with a new export does not require editing this file.
    """
    op = src[:, :, 3] > 30
    rows = bands(op.any(axis=1))
    if len(rows) != 3:
        raise SystemExit(f"expected 3 horizontal bands in the master, got {len(rows)}")
    (top0, top1), (st0, st1), (pf0, pf1) = rows

    # The top band splits into mark | wordmark at its widest interior gap.
    strip = op[top0:top1 + 1]
    cols = strip.any(axis=0)
    filled = bands(cols)
    gaps = [(filled[i][1] + 1, filled[i + 1][0] - 1) for i in range(len(filled) - 1)]
    gx0, gx1 = max(gaps, key=lambda g: g[1] - g[0])

    def box(y0, y1, x0=None, x1=None):
        sub = op[y0:y1 + 1]
        c = np.where(sub.any(axis=0))[0]
        lo = c.min() if x0 is None else max(c.min(), x0)
        hi = c.max() if x1 is None else min(c.max(), x1)
        return (int(lo), int(y0), int(hi) + 1, int(y1) + 1)

    return {
        "mark": box(top0, top1, None, gx0 - 1),
        "wordmark": box(top0, top1, gx1 + 1, None),
        "stripe": box(st0, st1),
        "performance": box(pf0, pf1),
    }


def ink_masks(src, box):
    """Per-brand-ink coverage masks for one component.

    Every pixel is assigned to the nearest brand ink and weighted by its own
    alpha, so anti-aliased edges and the joins between adjacent stripe
    segments both come out clean.
    """
    x0, y0, x1, y1 = box
    patch = src[y0:y1, x0:x1]
    rgb, alpha = patch[:, :, :3], patch[:, :, 3] / 255.0

    inks = [B.RED, B.WHITE, B.BLACK, B.GREEN, B.YELLOW]
    dist = np.stack([
        np.linalg.norm(rgb - np.array(B.rgb(h), dtype=np.float32), axis=-1)
        for h in inks
    ])
    winner = np.argmin(dist, axis=0)
    return {h: np.where(winner == i, alpha, 0.0) for i, h in enumerate(inks)
            if (winner == i).any()}


# --------------------------------------------------------------------------
# Composition
# --------------------------------------------------------------------------
class Lockup:
    """A canvas of per-ink coverage masks, assembled from master components."""

    def __init__(self, width, height):
        self.w, self.h = int(width), int(height)
        self.layers = []          # (ink_hex, mask, flips)

    def place(self, src, box, name, x, y, w, h):
        """Scale one component's ink masks and stamp them onto the canvas."""
        flips = name in FLIPPING
        for ink, mask in ink_masks(src, box).items():
            im = Image.fromarray((mask * 255).astype(np.uint8), "L")
            im = im.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
            canvas = np.zeros((self.h, self.w), np.float32)
            arr = np.asarray(im, dtype=np.float32) / 255.0
            px, py = int(round(x)), int(round(y))
            ah, aw = arr.shape
            canvas[py:py + ah, px:px + aw] = arr[:self.h - py, :self.w - px]
            self.layers.append((ink, canvas, flips))
        return self

    def merged(self):
        """Merge same-ink, same-flip layers so each traces as one path."""
        out = {}
        for ink, mask, flips in self.layers:
            key = (ink, flips)
            out[key] = np.maximum(out[key], mask) if key in out else mask
        return [(ink, mask, flips) for (ink, flips), mask in out.items()]


def aspect(box):
    x0, y0, x1, y1 = box
    return (x1 - x0) / (y1 - y0)


# --------------------------------------------------------------------------
# Vector tracing
# --------------------------------------------------------------------------
def trace_mask(mask, scale=TRACE_SCALE):
    """Trace a coverage mask to an SVG path, in canvas pixel units."""
    if mask.sum() < 4:
        return ""
    h, w = mask.shape
    img = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
    img = img.resize((w * scale, h * scale), Image.BICUBIC)
    big = np.asarray(img, dtype=np.float32) / 255.0 > MIN_ALPHA
    if big.sum() < scale * scale * 4:
        return ""

    # potrace treats zeros as foreground, so the mask is inverted on the way in.
    path = potrace.Bitmap(~big).trace(
        turdsize=max(2, scale * scale // 2),
        alphamax=ALPHA_MAX,
        opticurve=True,
        opttolerance=OPT_TOLERANCE,
    )

    s = 1.0 / scale

    def f(v):
        return f"{v * s:.2f}".rstrip("0").rstrip(".")

    parts = []
    for curve in path:
        p = curve.start_point
        parts.append(f"M{f(p.x)} {f(p.y)}")
        for seg in curve:
            if seg.is_corner:
                parts.append(f"L{f(seg.c.x)} {f(seg.c.y)}")
                parts.append(f"L{f(seg.end_point.x)} {f(seg.end_point.y)}")
            else:
                parts.append(
                    f"C{f(seg.c1.x)} {f(seg.c1.y)} "
                    f"{f(seg.c2.x)} {f(seg.c2.y)} "
                    f"{f(seg.end_point.x)} {f(seg.end_point.y)}"
                )
        parts.append("Z")
    return "".join(parts)


def vectorise(lockup):
    """Trace every ink layer. Returns [(hex, path_d, flips), ...]."""
    out = []
    for ink, mask, flips in lockup.merged():
        d = trace_mask(mask)
        if d:
            out.append((ink, d, flips))
    return out


# --------------------------------------------------------------------------
# SVG assembly and export
# --------------------------------------------------------------------------
def recolour(layers, mode):
    """Apply a variant.

    The mark and wordmark flip with the background. The accent stripe and
    PERFORMANCE do not - the stripe genuinely carries both a black and a white
    segment, and whichever matches the background reads as a gap. That is how
    the master is drawn.
    """
    out = []
    for ink, d, flips in layers:
        if mode == "white":
            c = B.WHITE if flips else ink
        elif mode == "black":
            c = B.BLACK if flips else ink
        elif mode == "mono-white":
            c = B.WHITE
        elif mode == "mono-black":
            c = B.BLACK
        else:
            raise ValueError(mode)
        out.append((c, d))
    return out


def write_svg(path, layers, w, h, title):
    body = "\n".join(
        f'  <path fill="{c}" fill-rule="evenodd" d="{d}"/>' for c, d in layers
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}">\n  <title>{title}</title>\n{body}\n</svg>\n'
    )


def render_pngs(svg_path, stem, w, h):
    """Rasterise an SVG to transparent PNGs plus flat-background versions."""
    for width in PNG_WIDTHS:
        out = B.LOGOS / "png-transparent" / f"{stem}_{width}w.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(url=str(svg_path), write_to=str(out),
                         output_width=width, output_height=max(1, round(width * h / w)))

    fg = Image.open(B.LOGOS / "png-transparent" / f"{stem}_2000w.png").convert("RGBA")
    for label, bg_hex, folder in (
        ("on-black", B.BLACK, "png-on-black"),
        ("on-white", B.WHITE, "png-on-white"),
    ):
        pad = round(fg.height * 0.35)
        card = Image.new("RGBA", (fg.width + pad * 2, fg.height + pad * 2),
                         B.rgb(bg_hex) + (255,))
        card.alpha_composite(fg, (pad, pad))
        out = B.LOGOS / folder / f"{stem}_{label}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        card.convert("RGB").save(out, optimize=True)


# --------------------------------------------------------------------------
# The four lockups
# --------------------------------------------------------------------------
def build_lockups(src, C):
    """Assemble each lockup as a Lockup canvas.

    `primary-horizontal` is the master itself, untouched. The other three are
    the master's own components restacked, keeping the arrangement and relative
    gaps the existing lockups use.
    """
    mx0, my0, mx1, my1 = C["mark"]
    mark_w, mark_h = mx1 - mx0, my1 - my0
    lock = {}

    # --- primary horizontal: the master, as supplied -----------------------
    x0 = min(C[k][0] for k in C)
    y0 = min(C[k][1] for k in C)
    x1 = max(C[k][2] for k in C)
    y1 = max(C[k][3] for k in C)
    L = Lockup(x1 - x0, y1 - y0)
    for name in ("mark", "wordmark", "stripe", "performance"):
        bx0, by0, bx1, by1 = C[name]
        L.place(src, C[name], name, bx0 - x0, by0 - y0, bx1 - bx0, by1 - by0)
    lock["primary-horizontal"] = L

    # --- mark only ---------------------------------------------------------
    L = Lockup(mark_w, mark_h)
    L.place(src, C["mark"], "mark", 0, 0, mark_w, mark_h)
    lock["icon-mark-only"] = L

    # --- icon: mark over a full-width stripe --------------------------------
    # Gaps measured off the shipped icon lockup: stripe sits 10.4% of the mark
    # height below it, and the stripe runs the full lockup width.
    gap = round(mark_h * 0.104)
    sw = round(mark_w * 1.031)
    sh = max(2, round(sw / aspect(C["stripe"])))
    pad = round((sw - mark_w) / 2)
    L = Lockup(sw, mark_h + gap + sh)
    L.place(src, C["mark"], "mark", pad, 0, mark_w, mark_h)
    L.place(src, C["stripe"], "stripe", 0, mark_h + gap, sw, sh)
    lock["icon"] = L

    # --- stacked: mark over wordmark, stripe, PERFORMANCE -------------------
    # Proportions measured off the shipped stacked lockup (normalised to a
    # 1000-unit width): mark 77.5% wide, wordmark 87.5%, stripe ~99%.
    total_w = round(mark_w / 0.775)
    word_w = round(total_w * 0.875)
    word_h = round(word_w / aspect(C["wordmark"]))
    stripe_w = round(total_w * 0.988)
    stripe_h = max(2, round(stripe_w / aspect(C["stripe"])))
    perf_w = round(total_w * 0.987)
    perf_h = round(perf_w / aspect(C["performance"]))

    g1 = round(total_w * 0.045)      # mark -> wordmark
    g2 = round(total_w * 0.056)      # wordmark -> stripe
    g3 = round(total_w * 0.046)      # stripe -> performance

    y = 0
    L = Lockup(total_w, mark_h + g1 + word_h + g2 + stripe_h + g3 + perf_h)
    L.place(src, C["mark"], "mark", (total_w - mark_w) / 2, y, mark_w, mark_h)
    y += mark_h + g1
    L.place(src, C["wordmark"], "wordmark", (total_w - word_w) / 2, y, word_w, word_h)
    y += word_h + g2
    L.place(src, C["stripe"], "stripe", (total_w - stripe_w) / 2, y, stripe_w, stripe_h)
    y += stripe_h + g3
    L.place(src, C["performance"], "performance", (total_w - perf_w) / 2, y, perf_w, perf_h)
    lock["stacked"] = L

    return lock


def main():
    src = load_master()
    C = split_components(src)
    print("master components (x0, y0, x1, y1):")
    for k, v in C.items():
        print(f"  {k:12s} {v}  {v[2]-v[0]}x{v[3]-v[1]}")

    for name, lockup in build_lockups(src, C).items():
        layers = vectorise(lockup)
        w, h = lockup.w, lockup.h
        print(f"{name}: {w}x{h}, {len(layers)} ink layers")
        for variant in VARIANTS:
            stem = f"fd-{name}--{variant}"
            svg = B.LOGOS / "svg-vector" / f"{stem}.svg"
            write_svg(svg, recolour(layers, variant), w, h,
                      f"Formula Dynamics Performance - {name} ({variant})")
            render_pngs(svg, stem, w, h)
        print(f"  wrote {len(VARIANTS)} variants + PNGs")


if __name__ == "__main__":
    main()
