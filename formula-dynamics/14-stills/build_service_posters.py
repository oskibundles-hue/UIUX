#!/usr/bin/env python3
"""One poster per service, three layouts, photo supplied by the shop.

The brief was a competitor's brake ad. What is worth taking from it is the
STRUCTURE - a stacked headline, an icon list of what the service actually
includes, a CTA and a contact foot - not its identity. Everything here is set
in Formula Dynamics' own system: brand red as the only accent, Bebas Neue,
dark ground, and translucent panels that are never bordered.

Layouts
  A  spec      full-bleed photo, headline top, inclusions down the left rail
  B  band      photo across the top, solid lower half, inclusions in a row
  C  rail      vertical service rail, photo right, frosted panel carrying copy

    python3 build_service_posters.py brakes --photo gt3.jpg
    python3 build_service_posters.py brakes            # placeholder photo
    python3 build_service_posters.py all --layout A
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "99-toolkit"))

from PIL import Image, ImageDraw, ImageFilter, ImageStat  # noqa: E402
import fd_brand as B                            # noqa: E402
import fd_render as R                           # noqa: E402

OUT = HERE / "service-posters"
W, H = B.CANVASES["9x16"]

# Instagram's action rail starts at x = 907 on a 1080 canvas. Nothing that has
# to be read may cross it - the same number fd_hud.py uses for video.
SAFE_RIGHT = int(W * 0.824)
MARGIN = 64


# --------------------------------------------------------------------------
# Icons - drawn, not sourced, so they carry the brand's weight and colour
# --------------------------------------------------------------------------
def _icon(size, draw_fn, color):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im), size, R.__dict__.get("_", None) or color)
    return im


def icon_rotor(d, s, c):
    """A vented rotor read end-on: outer ring, drill holes, hub."""
    pad, w = s * 0.08, max(2, int(s * 0.055))
    d.ellipse([pad, pad, s - pad, s - pad], outline=c, width=w)
    d.ellipse([s * 0.33, s * 0.33, s * 0.67, s * 0.67], outline=c, width=w)
    import math
    for i in range(6):
        a = math.radians(i * 60 + 15)
        cx, cy = s / 2 + math.cos(a) * s * 0.25, s / 2 + math.sin(a) * s * 0.25
        r = s * 0.045
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)


def icon_fluid(d, s, c):
    """A drop: the triangle and the bowl share a tangent so it reads as one."""
    w = max(2, int(s * 0.055))
    d.ellipse([s * 0.22, s * 0.40, s * 0.78, s * 0.92], outline=c, width=w)
    d.polygon([(s * 0.5, s * 0.08), (s * 0.30, s * 0.52), (s * 0.70, s * 0.52)],
              outline=c, width=w)
    d.polygon([(s * 0.5, s * 0.10), (s * 0.34, s * 0.50), (s * 0.66, s * 0.50)],
              fill=c)


def icon_caliper(d, s, c):
    """A caliper body gripping a disc edge - the bracket plus the disc line."""
    w = max(2, int(s * 0.055))
    d.rounded_rectangle([s * 0.10, s * 0.26, s * 0.62, s * 0.74],
                        radius=s * 0.12, outline=c, width=w)
    d.rounded_rectangle([s * 0.26, s * 0.40, s * 0.46, s * 0.60],
                        radius=s * 0.05, fill=c)
    d.line([(s * 0.74, s * 0.10), (s * 0.74, s * 0.90)], fill=c, width=w)
    d.line([(s * 0.88, s * 0.10), (s * 0.88, s * 0.90)], fill=c, width=w)


def icon_pad(d, s, c):
    """Friction block over its backing plate."""
    w = max(2, int(s * 0.055))
    d.rounded_rectangle([s * 0.14, s * 0.30, s * 0.86, s * 0.58],
                        radius=s * 0.07, fill=c)
    d.rounded_rectangle([s * 0.14, s * 0.64, s * 0.86, s * 0.80],
                        radius=s * 0.05, outline=c, width=w)


def icon_check(d, s, c):
    w = max(3, int(s * 0.075))
    d.ellipse([s * 0.06, s * 0.06, s * 0.94, s * 0.94], outline=c,
              width=max(2, int(s * 0.055)))
    d.line([(s * 0.28, s * 0.52), (s * 0.44, s * 0.68), (s * 0.73, s * 0.33)],
           fill=c, width=w, joint="curve")


def icon_gauge(d, s, c):
    import math
    w = max(2, int(s * 0.055))
    d.arc([s * 0.08, s * 0.08, s * 0.92, s * 0.92], 150, 390, fill=c, width=w)
    a = math.radians(300)
    d.line([(s / 2, s / 2),
            (s / 2 + math.cos(a) * s * 0.30, s / 2 + math.sin(a) * s * 0.30)],
           fill=c, width=w)
    d.ellipse([s * 0.44, s * 0.44, s * 0.56, s * 0.56], fill=c)


ICONS = {"rotor": icon_rotor, "fluid": icon_fluid, "caliper": icon_caliper,
         "pad": icon_pad, "check": icon_check, "gauge": icon_gauge}


def badge(kind, size=86, color=B.RED):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ICONS[kind](ImageDraw.Draw(im), size, color)
    return im


# --------------------------------------------------------------------------
# Photo handling
# --------------------------------------------------------------------------
def placeholder(w, h, note="ADD PHOTO"):
    """A marked slot, so a layout can be judged before the picture exists."""
    im = Image.new("RGBA", (w, h), (17, 17, 20, 255))
    d = ImageDraw.Draw(im)
    for i in range(-h, w, 54):                      # diagonal hatch
        d.line([(i, h), (i + h, 0)], fill=(26, 26, 31), width=2)
    tag = R.text(note, 34, "#4A4A52", tracking=0.30)
    im.paste(tag, ((w - tag.width) // 2, (h - tag.height) // 2), tag)
    size = R.text(f"{w} x {h}", 22, "#37373E", tracking=0.18)
    im.paste(size, ((w - size.width) // 2, (h + tag.height) // 2 + 14), size)
    return im


def cover(src, w, h, focus=0.5, fx=0.5):
    """Scale to cover the box and crop, keeping `focus` of the height."""
    im = src.convert("RGB")
    f = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * f)), max(h, round(im.height * f))),
                   Image.LANCZOS)
    x = int((im.width - w) * fx)
    y = int((im.height - h) * focus)
    return im.crop((x, y, x + w, y + h)).convert("RGBA")


# White type needs the ground under it below roughly this luminance. A fixed
# scrim is set for one car and fails on the next: the white GT3 RS measured 124
# under the headline where a dark Cullinan measures single figures. So the
# scrim SOLVES for the target instead of being dialled in by eye.
TARGET_LUMA = 40
DEBUG = bool(os.environ.get("FD_POSTER_DEBUG"))


def solve_alpha(base, box, target=TARGET_LUMA, floor=8):
    """How much to blend toward black so this box reads at `target`."""
    box = (max(0, box[0]), max(0, box[1]), min(base.width, box[2]),
           min(base.height, box[3]))
    if box[2] <= box[0] or box[3] <= box[1]:
        return 0.0
    mean = ImageStat.Stat(base.crop(box).convert("L")).mean[0]
    if mean <= target:
        if DEBUG:
            print(f"      ground {box[1]:>4}-{box[3]:<4} {mean:6.1f} -> already clear")
        return 0.0
    a = min(0.92, (mean - target) / max(1.0, mean - floor))
    if DEBUG:
        print(f"      ground {box[1]:>4}-{box[3]:<4} {mean:6.1f} -> "
              f"{mean * (1 - a) + floor * a:5.1f}  (alpha {a:.2f})")
    return a


def scrim(base, box, top=0, bottom=210, feather=True, adapt=True):
    """Darken a band so type can sit on a photograph and still be read."""
    if adapt:
        need = solve_alpha(base, box)
        bottom = max(bottom, int(255 * need))
    x0, y0, x1, y1 = box
    band = Image.new("L", (1, max(1, y1 - y0)))
    for i in range(band.height):
        t = i / max(1, band.height - 1)
        band.putpixel((0, i), int(top + (bottom - top) * t))
    mask = band.resize((x1 - x0, y1 - y0))
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(8))
    base.paste(Image.new("RGB", (x1 - x0, y1 - y0), (6, 6, 8)), (x0, y0), mask)


def top_scrim(base, y_full, y_end, target=TARGET_LUMA):
    """Hold strong from the top edge to y_full, then fade out by y_end.

    The mirror of base_scrim. A top gradient that is strongest at y=0 leaves the
    headline - which starts 200px down - in the weak tail, which is how the
    white GT3 RS measured 124 under it.
    """
    need = solve_alpha(base, (0, 0, base.width, y_full), target)
    if need <= 0:
        return
    scrim(base, (0, 0, base.width, y_full), top=int(255 * need),
          bottom=int(255 * need), feather=False, adapt=False)
    scrim(base, (0, y_full, base.width, y_end), top=int(255 * need),
          bottom=0, adapt=False)


def base_scrim(base, y_start, y_full, target=TARGET_LUMA):
    """Ramp in from y_start, then hold flat to the foot.

    A single gradient to the bottom edge leaves the middle of the band - which
    is exactly where the inclusion list sits - at a third of full strength. The
    ramp buys the soft edge; the flat section below it does the actual work, and
    its strength is solved from what is under it.
    """
    need = solve_alpha(base, (0, y_full, base.width, base.height), target)
    if need <= 0:
        return
    scrim(base, (0, y_start, base.width, y_full), top=0,
          bottom=int(255 * need), adapt=False)
    scrim(base, (0, y_full, base.width, base.height), top=int(255 * need),
          bottom=int(255 * need), feather=False, adapt=False)


def glass(base, box, darken=0.46, blur=16):
    """Frost cut from the picture itself. Translucent, never bordered."""
    darken = max(darken, solve_alpha(base, box))
    x0, y0, x1, y1 = box
    patch = base.crop(box).convert("RGB").filter(ImageFilter.GaussianBlur(blur))
    patch = Image.blend(patch, Image.new("RGB", patch.size, (8, 8, 10)), darken)
    patch = patch.convert("RGBA")
    base.paste(patch, (x0, y0))


# --------------------------------------------------------------------------
# Shared furniture
# --------------------------------------------------------------------------
def put(base, layer, x, y, shadow=True):
    """Paste so the INK lands at (x, y), and report the ink height.

    fd_render.with_shadow grows the canvas by blur*3 on every side, so pasting
    the shadowed layer at (x, y) actually places the glyphs at (x+grow, y+grow).
    Advancing by the unshadowed height then stacks the next line on top of the
    last - which is what put the fine print through the price. Offsetting by
    `grow` here keeps every caller's arithmetic honest.
    """
    if not shadow:
        R.paste(base, layer, x, y)
        return layer.height
    grow = int(max(3, layer.height * 0.06) * 3)
    R.paste(base, R.with_shadow(layer), x - grow, y - grow)
    return layer.height


def brandmark(base, x, y, h=52):
    lg = R.logo("fd-icon--mono-white", height=h)
    R.paste(base, lg, x, y)
    return lg.width


def qualifier(base, y, lines=("EXOTICS  ·  LUXURY  ·  PERFORMANCE",
                             "ALL MAKES  ·  ALL MODELS")):
    """Top-right eligibility strip - kept inside the action rail."""
    for i, ln in enumerate(lines):
        t = R.text(ln, 23 if i == 0 else 21,
                   B.WHITE if i == 0 else "#9A99A0", tracking=0.16)
        put(base, t, SAFE_RIGHT - t.width, y + i * 30)


def footer(base, words, y):
    t = R.text("   |   ".join(words), 21, "#8B8A91", tracking=0.22)
    R.paste(base, t, (W - t.width) // 2, y)


def contact_line(base, y, centre=True):
    bits = [B.INSTAGRAM, B.WEBSITE]
    t = R.text("      ".join(bits), 26, B.WHITE, tracking=0.12)
    x = (W - t.width) // 2 if centre else MARGIN
    put(base, t, x, y)
    return t.height


def contact_block(im, x, y, size=28):
    """Phone and handle on top, address and site beneath. One place, so the
    five layouts cannot drift apart as details change."""
    a = R.text(f"{PHONE}     {HANDLE}", size, B.WHITE, tracking=0.08)
    put(im, a, x, y)
    b = R.text(f"{ADDRESS}     {SITE}", int(size * 0.79), "#A9A8AF",
               tracking=0.12)
    put(im, b, x, y + a.height + 14)
    return a.height + 14 + b.height


def headline(base, x, y, l1, l2, size=132, gap=6):
    a = R.fit_text(l1, SAFE_RIGHT - x, max_height=size, color=B.WHITE,
                   tracking=0.01)
    put(base, a, x, y)
    b = R.fit_text(l2, SAFE_RIGHT - x, max_height=size, color=B.RED,
                   tracking=0.01)
    put(base, b, x, y + a.height + gap)
    return y + a.height + gap + b.height


# --------------------------------------------------------------------------
# Shop facts - read off formuladynamics.com, not remembered
# --------------------------------------------------------------------------
PHONE = "(702) 430-1040"
ADDRESS = "4790 POLARIS AVE  ·  LAS VEGAS, NV"
SITE = "formuladynamics.com"
# Confirmed by the shop 14 Sept: @formuladynamicsperformance is current and
# @formuladynamicsusa is the old one, being taken off the website.
HANDLE = "@formuladynamicsperformance"
QUALIFIER = ("EXOTICS  ·  LUXURY  ·  PERFORMANCE", "ALL MAKES  ·  ALL MODELS")
FOOT = ("PERFORMANCE", "PROTECTION", "MAINTENANCE", "AND BEYOND")


# --------------------------------------------------------------------------
# One entry per service. Everything on screen comes from here.
# --------------------------------------------------------------------------
SERVICE_POSTERS = {
    "brakes": dict(
        eyebrow="BRAKE SERVICE",
        # Benefit first, price late - the shop's own copy rule. The service
        # name is the eyebrow; the headline is what it does for the car.
        h1="STOPS WHEN", h2="YOU NEED IT TO",
        tagline=("ROTORS, FLUID AND CALIPERS", "CHECKED, SERVICED, SIGNED OFF"),
        includes=[
            ("rotor",   "ROTORS",     "INSPECTED"),
            ("fluid",   "BRAKE FLUID", "FLUSHED & BLED"),
            ("caliper", "CALIPERS",   "CLEANED & CHECKED"),
            ("pad",     "BRAKE",      "UPGRADES AVAILABLE"),
        ],
        price="$499",
        fine="PADS SOLD SEPARATELY",
        cta=("BOOK YOUR", "BRAKE SERVICE"),
    ),
}


# --------------------------------------------------------------------------
# Layout A - SPEC. Full-bleed photo, headline high, inclusions down the rail.
# --------------------------------------------------------------------------
def layout_spec(photo, s):
    im = cover(photo, W, H, focus=0.55)
    top_scrim(im, 600, 760)
    base_scrim(im, 840, 1000)

    brandmark(im, MARGIN, 72)
    qualifier(im, 78, QUALIFIER)

    y = 210
    eb = R.text(s["eyebrow"], 30, B.RED, tracking=0.34)
    put(im, eb, MARGIN, y)
    y = headline(im, MARGIN, y + eb.height + 20, s["h1"], s["h2"], size=124)

    R.paste(im, R.accent_stripe(round(W * 0.26), 9), MARGIN, y + 40)

    y = 1010
    for i, (kind, a, b) in enumerate(s["includes"]):
        ic = badge(kind, 76)
        R.paste(im, ic, MARGIN, y + 4)
        ta = R.text(a, 40, B.WHITE, tracking=0.05)
        tb = R.text(b, 32, "#B9B8BF", tracking=0.08)
        put(im, ta, MARGIN + 104, y)
        put(im, tb, MARGIN + 104, y + ta.height + 6)
        y += 116

    # Price and CTA share the foot so the ask and the number read together.
    pr = R.text(s["price"], 116, B.WHITE, tracking=0.01)
    put(im, pr, MARGIN, H - 330)
    fn = R.text(s["fine"], 24, "#9A99A0", tracking=0.16)
    put(im, fn, MARGIN + 6, H - 330 + pr.height + 18)

    c1 = R.text(s["cta"][0], 44, B.WHITE, tracking=0.06)
    c2 = R.text(s["cta"][1], 44, B.RED, tracking=0.06)
    put(im, c1, SAFE_RIGHT - c1.width, H - 326)
    put(im, c2, SAFE_RIGHT - c2.width, H - 326 + c1.height + 4)

    contact_block(im, MARGIN, H - 172, 29)
    footer(im, FOOT, H - 62)
    return im


# --------------------------------------------------------------------------
# Layout B - BAND. Photo across the top, copy on solid ground beneath it.
# --------------------------------------------------------------------------
def layout_band(photo, s):
    # The split is set by what has to fit BELOW it, not by taste: tagline,
    # a two-by-two grid, the price, the CTA bar and two contact lines.
    split = 1040
    im = Image.new("RGBA", (W, H), (10, 10, 12, 255))
    im.paste(cover(photo, W, split, focus=0.5), (0, 0))
    scrim(im, (0, 0, W, 300), top=190, bottom=0)
    scrim(im, (0, split - 420, W, split), top=0, bottom=255)

    brandmark(im, MARGIN, 72)
    qualifier(im, 78, QUALIFIER)

    eb = R.text(s["eyebrow"], 30, B.RED, tracking=0.34)
    put(im, eb, MARGIN, split - 320)
    headline(im, MARGIN, split - 320 + eb.height + 16, s["h1"], s["h2"], size=112)

    # A red seam marks where the picture stops and the offer starts.
    ImageDraw.Draw(im).rectangle([0, split, W, split + 8], fill=B.RED)

    y = split + 74
    t1 = R.text(s["tagline"][0], 34, B.WHITE, tracking=0.07)
    t2 = R.text(s["tagline"][1], 34, "#B9B8BF", tracking=0.07)
    R.paste(im, t1, MARGIN, y)
    R.paste(im, t2, MARGIN, y + t1.height + 8)

    y += t1.height + t2.height + 52
    col = (SAFE_RIGHT - MARGIN) // 2
    pitch = 140            # icon 64 + label 32 + sub 26 + breathing room
    for i, (kind, a, b) in enumerate(s["includes"]):
        cx = MARGIN + (i % 2) * col
        cy = y + (i // 2) * pitch
        R.paste(im, badge(kind, 64), cx, cy)
        ta = R.text(a, 32, B.WHITE, tracking=0.05)
        tb = R.text(b, 26, "#9A99A0", tracking=0.08)
        R.paste(im, ta, cx, cy + 78)
        R.paste(im, tb, cx, cy + 78 + ta.height + 5)

    pr = R.text(s["price"], 132, B.WHITE, tracking=0.01)
    R.paste(im, pr, MARGIN, H - 350)
    fn = R.text(s["fine"], 24, "#9A99A0", tracking=0.16)
    put(im, fn, MARGIN + 6, H - 350 + pr.height + 18)

    bar_y = H - 186
    ImageDraw.Draw(im).rectangle([MARGIN, bar_y, SAFE_RIGHT, bar_y + 76], fill=B.RED)
    cta = R.text(f"{s['cta'][0]} {s['cta'][1]}", 40, B.WHITE, tracking=0.08)
    R.paste(im, cta, MARGIN + (SAFE_RIGHT - MARGIN - cta.width) // 2,
            bar_y + (76 - cta.height) // 2)

    cb = R.text(f"{PHONE}   {HANDLE}   {SITE}", 25, B.WHITE, tracking=0.08)
    put(im, cb, (W - cb.width) // 2, H - 96)
    footer(im, FOOT, H - 52)
    return im


# --------------------------------------------------------------------------
# Layout C - RAIL. Vertical service rail, photo right, frosted copy panel.
# --------------------------------------------------------------------------
def layout_rail(photo, s):
    rail = 104
    im = Image.new("RGBA", (W, H), (10, 10, 12, 255))
    im.paste(cover(photo, W - rail, H, focus=0.5), (rail, 0))
    scrim(im, (rail, 0, W, 360), top=185, bottom=0)

    ImageDraw.Draw(im).rectangle([0, 0, rail, H], fill=B.RED)
    tab = R.text(s["eyebrow"], 46, B.WHITE, tracking=0.26).rotate(90, expand=True)
    im.paste(tab, ((rail - tab.width) // 2, (H - tab.height) // 2), tab)

    brandmark(im, rail + 44, 72)
    qualifier(im, 78, QUALIFIER)

    # The copy sits on glass cut from the photo - translucent, never bordered.
    panel = (rail, 990, W, H)
    glass(im, panel, darken=0.55, blur=18)

    x = rail + 44
    y = 1040
    y = headline(im, x, y, s["h1"], s["h2"], size=88)

    R.paste(im, R.accent_stripe(round(W * 0.22), 8), x, y + 34)

    # The list is hung off the price block, not off the headline, so a longer
    # headline can never push a row through the number.
    row = 72
    y = min(y + 44, H - 292 - 36 - row * len(s["includes"]))
    for i, (kind, a, b) in enumerate(s["includes"]):
        R.paste(im, badge(kind, 54), x, y + 2)
        ta = R.text(f"{a}  {b}", 30, B.WHITE, tracking=0.06)
        R.paste(im, ta, x + 74, y + 12)
        y += row

    pr = R.text(s["price"], 104, B.WHITE, tracking=0.01)
    R.paste(im, pr, x, H - 292)
    fn = R.text(s["fine"], 23, "#A9A8AF", tracking=0.16)
    R.paste(im, fn, x + 4, H - 292 + pr.height + 16)

    c1 = R.text(s["cta"][0], 38, B.WHITE, tracking=0.06)
    c2 = R.text(s["cta"][1], 38, B.RED, tracking=0.06)
    R.paste(im, c1, SAFE_RIGHT - c1.width, H - 288)
    R.paste(im, c2, SAFE_RIGHT - c2.width, H - 288 + c1.height + 4)

    contact_block(im, x, H - 140, 26)
    return im




# --------------------------------------------------------------------------
# Layout D - JOB SHEET. The work order the car actually leaves with.
# Lifted from the Precision Workshop direction in the overlay pick, where the
# job-sheet title card was called the best single piece of all three looks.
# The photo is a LANDSCAPE band so a 3:2 shop frame is not cropped to ribbons.
# --------------------------------------------------------------------------
def layout_job(photo, s):
    band_h = 760
    im = Image.new("RGBA", (W, H), (10, 10, 12, 255))
    im.paste(cover(photo, W, band_h, focus=0.52), (0, 0))
    scrim(im, (0, 0, W, 240), top=190, bottom=0)

    brandmark(im, MARGIN, 64)
    qualifier(im, 70, QUALIFIER)

    ImageDraw.Draw(im).rectangle([0, band_h, W, band_h + 6], fill=B.RED)

    y = band_h + 58
    eb = R.text("WORK ORDER", 26, B.RED, tracking=0.34)
    put(im, eb, MARGIN, y)
    job = R.text("FD-BRK-01", 26, "#8B8A91", tracking=0.20)
    put(im, job, SAFE_RIGHT - job.width, y)

    y = headline(im, MARGIN, y + eb.height + 26, s["h1"], s["h2"], size=98)

    # Ruled docket rows - a hairline per line item, ticked, priced at the foot.
    y += 54
    d = ImageDraw.Draw(im)
    for kind, a, b in s["includes"]:
        d.line([(MARGIN, y), (SAFE_RIGHT, y)], fill=(42, 40, 46), width=2)
        R.paste(im, badge(kind, 44), MARGIN + 4, y + 22)
        ta = R.text(f"{a}  {b}", 30, B.WHITE, tracking=0.06)
        R.paste(im, ta, MARGIN + 66, y + 30)
        tick = R.text("DONE", 22, B.RED, tracking=0.22)
        R.paste(im, tick, SAFE_RIGHT - tick.width, y + 34)
        y += 92
    d.line([(MARGIN, y), (SAFE_RIGHT, y)], fill=(42, 40, 46), width=2)

    y += 44
    lbl = R.text("TOTAL", 26, "#8B8A91", tracking=0.26)
    R.paste(im, lbl, MARGIN, y + 34)
    pr = R.text(s["price"], 92, B.WHITE, tracking=0.01)
    put(im, pr, MARGIN + 150, y)
    fn = R.text(s["fine"], 22, "#8B8A91", tracking=0.16)
    R.paste(im, fn, MARGIN + 152, y + pr.height + 14)

    c1 = R.text(s["cta"][0], 34, B.WHITE, tracking=0.06)
    c2 = R.text(s["cta"][1], 34, B.RED, tracking=0.06)
    put(im, c1, SAFE_RIGHT - c1.width, y + 6)
    put(im, c2, SAFE_RIGHT - c2.width, y + 6 + c1.height + 6)

    contact_block(im, MARGIN, H - 154, 26)
    footer(im, FOOT, H - 58)
    return im


# --------------------------------------------------------------------------
# Layout E - TELEMETRY. The overlay pick's own favourite, as a still: a ruler
# down the edge, one red needle on the number that matters, frosted haze
# rather than boxes, and red used only as the live signal.
# --------------------------------------------------------------------------
def layout_telemetry(photo, s):
    im = cover(photo, W, H, focus=0.5, fx=0.5)
    top_scrim(im, 580, 740)
    base_scrim(im, 1020, 1140)

    brandmark(im, MARGIN, 72)
    qualifier(im, 78, QUALIFIER)

    # A measurement ruler down the right edge - the shop measures things.
    d = ImageDraw.Draw(im)
    rx = SAFE_RIGHT + 26
    for i in range(34):
        ty = 430 + i * 30
        long_tick = (i % 5 == 0)
        d.line([(rx, ty), (rx + (26 if long_tick else 13), ty)],
               fill=(255, 255, 255, 150 if long_tick else 70),
               width=3 if long_tick else 2)

    y = 210
    eb = R.text(s["eyebrow"], 28, B.RED, tracking=0.34)
    put(im, eb, MARGIN, y)
    y = headline(im, MARGIN, y + eb.height + 20, s["h1"], s["h2"], size=116)

    # The inclusions read as a readout, not a bulleted list.
    y = 1160
    for kind, a, b in s["includes"]:
        R.paste(im, badge(kind, 46), MARGIN, y)
        ta = R.text(a, 28, B.WHITE, tracking=0.10)
        tb = R.text(b, 28, "#A9A8AF", tracking=0.06)
        put(im, ta, MARGIN + 66, y + 8)
        put(im, tb, MARGIN + 66 + 250, y + 8)
        y += 64

    # The needle: red only where the live value is.
    py = H - 336
    d.rectangle([MARGIN, py - 14, MARGIN + 7, py + 128], fill=B.RED)
    pr = R.text(s["price"], 108, B.WHITE, tracking=0.01)
    put(im, pr, MARGIN + 30, py)
    fn = R.text(s["fine"], 22, "#A9A8AF", tracking=0.16)
    put(im, fn, MARGIN + 32, py + pr.height + 16)

    c1 = R.text(s["cta"][0], 36, B.WHITE, tracking=0.06)
    c2 = R.text(s["cta"][1], 36, B.RED, tracking=0.06)
    put(im, c1, SAFE_RIGHT - c1.width, py + 10)
    put(im, c2, SAFE_RIGHT - c2.width, py + 10 + c1.height + 6)

    contact_block(im, MARGIN, H - 160, 27)
    footer(im, FOOT, H - 60)
    return im


LAYOUTS = {"A": ("spec", layout_spec), "B": ("band", layout_band),
           "C": ("rail", layout_rail), "D": ("job", layout_job),
           "E": ("telemetry", layout_telemetry)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("service", help="key in SERVICE_POSTERS, or 'all'")
    ap.add_argument("--photo", help="hero photograph; omit for a marked slot")
    ap.add_argument("--layout", default="all", help="A-E or all")
    ap.add_argument("--fx", type=float, default=0.5,
                    help="horizontal crop aim, 0 left .. 1 right")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    photo = Image.open(a.photo) if a.photo else placeholder(W, H)
    keys = list(SERVICE_POSTERS) if a.service == "all" else [a.service]
    want = list(LAYOUTS) if a.layout == "all" else [a.layout.upper()]

    for key in keys:
        for L in want:
            tag, fn = LAYOUTS[L]
            im = fn(photo, SERVICE_POSTERS[key])
            path = OUT / f"{key}-{L}-{tag}.png"
            im.convert("RGB").save(path)
            print(f"  {path.name}  {im.width}x{im.height}  "
                  f"{path.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
