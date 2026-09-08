#!/usr/bin/env python3
"""Build the Formula Dynamics logo assets as clean vector SVG.

The monogram path is traced from the official profile mark; the tachometer
arc (green -> yellow -> red) is redrawn as true geometry so it stays crisp
at 4K.  Outputs:
    fd_mark.svg        disc + arc + monogram (the full lockup)
    fd_mark_flat.svg   monogram only, no disc (for dark backgrounds)
    fd_bug.svg         small corner bug used by the reel overlay
"""
import math
import pathlib

HERE = pathlib.Path(__file__).parent
LOGO = HERE / "logo"

# ---- brand constants -------------------------------------------------------
INK = "#11121F"        # monogram / dark ground
WHITE = "#FFFFFF"
ARC_GREEN = "#57B752"
ARC_YELLOW = "#F9FC68"
ARC_RED = "#E4362B"

D = (LOGO / "monogram_path.txt").read_text().strip()
# traced monogram bounding box, in its own 1000-wide user space
MONO_W, MONO_H = 1000.0, 707.0


def arc(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    laf = 1 if abs(a1 - a0) > 180 else 0
    return f"M{x0:.2f},{y0:.2f} A{r},{r} 0 {laf} 1 {x1:.2f},{y1:.2f}"


def monogram(scale, cx, cy, fill):
    """Monogram centred on (cx, cy) at the given scale."""
    w, h = MONO_W * scale, MONO_H * scale
    tx, ty = cx - w / 2, cy - h / 2
    return (
        f'<g transform="translate({tx:.2f},{ty:.2f}) scale({scale:.5f})">'
        f'<path d="{D}" fill="{fill}" fill-rule="evenodd"/></g>'
    )


def full_mark(size=1000, disc=True, ring=True, ink=INK, ground=WHITE):
    c = size / 2
    r_disc = size * 0.47
    r_arc = size * 0.447
    sw = size * 0.034
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}">'
    ]
    if disc:
        out.append(f'<circle cx="{c}" cy="{c}" r="{r_disc:.2f}" fill="{ground}"/>')
    if ring:
        out.append(
            f'<g fill="none" stroke-width="{sw:.2f}" stroke-linecap="butt">'
            f'<path d="{arc(c, c, r_arc, 199, 268)}" stroke="{ARC_GREEN}"/>'
            f'<path d="{arc(c, c, r_arc, 269, 330)}" stroke="{ARC_YELLOW}"/>'
            f'<path d="{arc(c, c, r_arc, 331, 379)}" stroke="{ARC_RED}"/>'
            f"</g>"
        )
    # monogram sized so its width is 62% of the disc diameter
    scale = (size * 0.62) / MONO_W
    out.append(monogram(scale, c, c, ink))
    out.append("</svg>")
    return "".join(out)


def flat_mark(width=1000, fill=WHITE):
    h = width * MONO_H / MONO_W
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {h:.1f}" '
        f'width="{width}" height="{h:.1f}">'
        f'<g transform="scale({width/MONO_W:.5f})">'
        f'<path d="{D}" fill="{fill}" fill-rule="evenodd"/></g></svg>'
    )


if __name__ == "__main__":
    (LOGO / "fd_mark.svg").write_text(full_mark())
    (LOGO / "fd_mark_dark.svg").write_text(full_mark(ink=WHITE, ground=INK))
    (LOGO / "fd_mark_flat_white.svg").write_text(flat_mark(fill=WHITE))
    (LOGO / "fd_mark_flat_ink.svg").write_text(flat_mark(fill=INK))
    print("wrote fd_mark.svg, fd_mark_dark.svg, fd_mark_flat_white.svg, fd_mark_flat_ink.svg")
