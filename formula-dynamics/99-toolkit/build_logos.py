#!/usr/bin/env python3
"""
Formula Dynamics Performance - logo extraction and vectorisation.

Reads the official brand guide raster, isolates each logo lockup, snaps every
pixel to an exact brand colour, then traces the result to true vector SVG.
Everything downstream (PNGs, overlays, end cards) is rendered from those
vectors, so the artwork stays sharp at any size.

The source raster has soft, slightly noisy edges, so the alpha channel is
smoothed before thresholding - otherwise the noise in the edge ramp traces
through as visible wobble on straight strokes.

Run:  python3 99-toolkit/build_logos.py
"""

import numpy as np
import potrace
import cairosvg
from PIL import Image, ImageFilter

import fd_brand as B

# --- Tracing quality -------------------------------------------------------
TRACE_SCALE = 6       # supersample factor before tracing
EDGE_BLUR = 0.7       # source-pixel blur radius; smooths edge-ramp noise
ALPHA_FLOOR = 0.06    # below this, treat as background
ALPHA_MAX = 1.1       # potrace corner threshold
OPT_TOLERANCE = 0.4   # potrace curve-fitting tolerance

PNG_WIDTHS = [1000, 2000, 4000]

# Source regions inside the brand guide (left, top, right, bottom)
LOCKUPS = {
    "primary-horizontal": (67, 190, 663, 440),
    "stacked": (1037, 240, 1194, 401),
    "icon": (1291, 273, 1440, 387),
}

VARIANTS = ["white", "black", "mono-white", "mono-black"]


# --------------------------------------------------------------------------
# Palette-locked alpha keying
# --------------------------------------------------------------------------
def key_on_black(arr):
    """Separate artwork from a black background.

    Each pixel is modelled as ``alpha * ink`` for one of the brand inks. The
    best-fitting ink wins, which both extracts a clean alpha channel and snaps
    the colour to an exact brand hex - removing any compression drift in the
    source raster.

    Returns (alpha, ink_index) where ink_index maps into B.INK_COLORS.
    """
    px = arr.astype(np.float64)
    best_res = best_a = best_i = None

    for i, ink in enumerate(B.INK_COLORS):
        c = np.array(B.rgb(ink), dtype=np.float64)
        a = np.clip((px @ c) / float(c @ c), 0.0, 1.0)
        residual = np.linalg.norm(px - a[..., None] * c, axis=-1)
        if best_res is None:
            best_res, best_a = residual, a
            best_i = np.full(a.shape, i, np.int8)
        else:
            win = residual < best_res
            best_res = np.where(win, residual, best_res)
            best_a = np.where(win, a, best_a)
            best_i = np.where(win, i, best_i)

    best_a = np.where(best_a < ALPHA_FLOOR, 0.0, best_a)
    return best_a, best_i


def content_box(alpha):
    """Tight bounding box of everything with meaningful opacity."""
    rows = np.where(alpha.max(axis=1) > 0.15)[0]
    cols = np.where(alpha.max(axis=0) > 0.15)[0]
    return cols.min(), rows.min(), cols.max() + 1, rows.max() + 1


def crop(alpha, idx):
    x0, y0, x1, y1 = content_box(alpha)
    return alpha[y0:y1, x0:x1], idx[y0:y1, x0:x1]


def runs(occupied):
    """Contiguous True runs in a 1-D boolean array, as (start, end) pairs."""
    out, start = [], None
    for i, v in enumerate(occupied):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(occupied)))
    return out


# --------------------------------------------------------------------------
# Vector tracing
# --------------------------------------------------------------------------
def smooth_layers(alpha, idx, scale=TRACE_SCALE, blur=EDGE_BLUR):
    """Build one supersampled, denoised boolean mask per brand ink.

    Each ink's alpha is blurred and upsampled independently, then every pixel
    is awarded to the ink with the strongest response. That keeps the outer
    silhouette smooth *and* keeps the joins between adjacent inks (the accent
    stripe segments) clean.
    """
    h, w = alpha.shape
    fields = []
    for i in range(len(B.INK_COLORS)):
        layer = (alpha * (idx == i) * 255).astype(np.uint8)
        img = Image.fromarray(layer, "L")
        if blur:
            img = img.filter(ImageFilter.GaussianBlur(blur))
        img = img.resize((w * scale, h * scale), Image.BICUBIC)
        fields.append(np.asarray(img, dtype=np.float32) / 255.0)

    total = np.sum(fields, axis=0)
    winner = np.argmax(fields, axis=0)
    solid = total > 0.5
    return [solid & (winner == i) for i in range(len(fields))]


def trace_mask(mask, scale=TRACE_SCALE):
    """Trace a supersampled boolean mask to an SVG path in source pixel units."""
    if mask.sum() < scale * scale * 4:
        return ""

    # potrace treats zeros as foreground, so the mask is inverted on the way in.
    path = potrace.Bitmap(~mask).trace(
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


def vectorise(alpha, idx):
    """Trace one layer per brand ink. Returns [(hex, path_d), ...]."""
    out = []
    for i, mask in enumerate(smooth_layers(alpha, idx)):
        d = trace_mask(mask)
        if d:
            out.append((B.INK_COLORS[i], d))
    return out


# --------------------------------------------------------------------------
# SVG assembly and export
# --------------------------------------------------------------------------
def recolour(layers, mode):
    out = []
    for ink, d in layers:
        if mode == "white":
            c = ink                                   # artwork as designed
        elif mode == "black":
            c = B.BLACK if ink == B.WHITE else ink    # wordmark flips to black
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
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}">\n  <title>{title}</title>\n{body}\n</svg>\n'
    )


def render_pngs(svg_path, stem, w, h):
    """Rasterise an SVG to transparent PNGs plus flat-background versions."""
    for width in PNG_WIDTHS:
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(B.LOGOS / "png-transparent" / f"{stem}_{width}w.png"),
            output_width=width,
            output_height=max(1, round(width * h / w)),
        )

    fg = Image.open(B.LOGOS / "png-transparent" / f"{stem}_2000w.png").convert("RGBA")
    for label, bg_hex, folder in (
        ("on-black", B.BLACK, "png-on-black"),
        ("on-white", B.WHITE, "png-on-white"),
    ):
        pad = round(fg.height * 0.35)
        canvas = Image.new("RGBA", (fg.width + pad * 2, fg.height + pad * 2),
                           B.rgb(bg_hex) + (255,))
        canvas.alpha_composite(fg, (pad, pad))
        canvas.convert("RGB").save(B.LOGOS / folder / f"{stem}_{label}.png")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def collect_sources(guide):
    """Return [(name, alpha, ink_idx), ...] at the best available resolution."""
    jobs = []
    prim = None

    for name, box in LOCKUPS.items():
        alpha, idx = crop(*key_on_black(np.array(guide.crop(box))))
        jobs.append((name, alpha, idx))
        if name == "primary-horizontal":
            prim = (alpha, idx)

    # The bare FD monogram is taken from the primary lockup, where it is
    # rendered ~25% larger than in the standalone icon swatch.
    alpha, idx = prim
    white = (alpha > 0.5) & (idx == B.INK_COLORS.index(B.WHITE))
    column_runs = runs(white.max(axis=0))
    if column_runs:
        x0, x1 = column_runs[0]          # leftmost white shape = the FD mark
        rows = np.where(white[:, x0:x1].max(axis=1))[0]
        y0, y1 = rows.min(), rows.max() + 1
        jobs.append(("icon-mark-only", alpha[y0:y1, x0:x1], idx[y0:y1, x0:x1]))

    return jobs


def build():
    guide = Image.open(B.BRAND_GUIDE).convert("RGB")
    count = 0

    for name, alpha, idx in collect_sources(guide):
        h, w = alpha.shape
        layers = vectorise(alpha, idx)
        inks = sorted({c for c, _ in layers})
        print(f"  {name:<20} {w}x{h}px  ->  {len(layers)} vector layer(s) {inks}")

        for variant in VARIANTS:
            stem = f"fd-{name}--{variant}"
            svg_path = B.LOGOS / "svg-vector" / f"{stem}.svg"
            write_svg(svg_path, recolour(layers, variant), w, h,
                      f"Formula Dynamics Performance - {name} ({variant})")
            render_pngs(svg_path, stem, w, h)
            count += 1

    return count


if __name__ == "__main__":
    print("Extracting and vectorising logo lockups...")
    n = build()
    print(f"\nDone. {n} logo variants written to 02-logos/.")
