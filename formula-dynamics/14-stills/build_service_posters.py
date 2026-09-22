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
PHOTOS = HERE / "photos"
APPROVED_LAYOUT = "J"   # signed off 14 Sept; every service is built on it
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
        photo="DSC00075.JPEG",
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
        # "Parts", not "pads": the list names rotors and pads both, so the
        # narrower word under-declared what the customer may still owe for.
        # Shop's own wording, 14 Sept.
        fine="PARTS SOLD SEPARATELY",
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
    ap.add_argument("--layout", default=APPROVED_LAYOUT,
                    help="letter, or all. Default is the approved layout.")
    ap.add_argument("--fx", type=float, default=0.5,
                    help="horizontal crop aim, 0 left .. 1 right")
    ap.add_argument("--cars", action="store_true",
                    help="render the service against every car in photos/")
    a = ap.parse_args()

    if a.cars:
        return cars(a.service, a.layout.upper())

    OUT.mkdir(parents=True, exist_ok=True)
    keys = list(SERVICE_POSTERS) if a.service == "all" else [a.service]
    want = list(LAYOUTS) if a.layout == "all" else [a.layout.upper()]

    for key in keys:
        cfg = SERVICE_POSTERS[key]
        # Each service names its own frame; --photo overrides for a one-off.
        src = a.photo or (PHOTOS / cfg["photo"] if cfg.get("photo") else None)
        photo = Image.open(src) if src else placeholder(W, H)
        for L in want:
            tag, fn = LAYOUTS[L]
            im = fn(photo, cfg)
            path = OUT / f"{key}-{L}-{tag}.png"
            im.convert("RGB").save(path)
            print(f"  {path.name}  {im.width}x{im.height}  "
                  f"{path.stat().st_size / 1e6:.1f} MB")




# ==========================================================================
# v2 - the sale-driven set
#
# The boss picked A and B, asked for bigger type, a sale-driven read and a
# composition closer to the reference ad. All three are measured decisions:
#
# TYPE. A 1080px poster renders about 390pt wide in an iPhone feed - a scale of
# 0.361. The v1 posters ran type down to 21px, which lands at 7.6pt on a phone
# against an ~11pt readable floor. Nothing here goes below MIN_TYPE.
#
# SALE. "From $499" rather than "$499": pads are sold separately, so $499 is
# genuinely the floor rather than the price, and the honest wording is also the
# one that reads as an offer.
#
# REFERENCE. Five inclusions rather than four, a supporting tagline under the
# headline, glyphs on the phone and address, and a CTA that ends in TODAY - the
# structural moves from the ad the shop brought in, in our own type and colour.
# ==========================================================================
MIN_TYPE = 34          # 12.3pt on a phone; below this is decoration, not copy
PHONE_SCALE = 390.0 / 1080.0


def t(msg, size, color=B.WHITE, tracking=0.0, floor=True):
    """Text with the mobile floor enforced, so it cannot regress by accident."""
    if floor and size < MIN_TYPE:
        raise ValueError(f"{size}px = {size * PHONE_SCALE:.1f}pt on a phone; "
                         f"floor is {MIN_TYPE}px")
    return R.text(msg, size, color, tracking=tracking)


def glyph_phone(size=40, color=B.RED):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = max(3, int(size * 0.13))
    d.rounded_rectangle([size * .16, size * .06, size * .42, size * .40],
                        radius=size * .10, fill=color)
    d.rounded_rectangle([size * .58, size * .58, size * .84, size * .92],
                        radius=size * .10, fill=color)
    d.arc([size * .10, size * .10, size * .90, size * .90], 20, 70,
          fill=color, width=w)
    return im


def glyph_pin(size=40, color=B.RED):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([size * .18, size * .08, size * .82, size * .72], fill=color)
    d.polygon([(size * .5, size * .95), (size * .30, size * .58),
               (size * .70, size * .58)], fill=color)
    d.ellipse([size * .38, size * .28, size * .62, size * .52], fill=(10, 10, 12))
    return im


def offer_block(im, x, y, s, price_size=150):
    """The sale, read as an offer rather than a bare number."""
    lab = t(s["offer_label"], 38, "#C9C8CF", tracking=0.20)
    put(im, lab, x, y)
    pr = R.text(s["price"], price_size, B.WHITE, tracking=0.01)
    put(im, pr, x, y + lab.height + 14)
    note = t(s["fine"], 34, B.RED, tracking=0.16)
    put(im, note, x, y + lab.height + 14 + pr.height + 20)
    return lab.height + 14 + pr.height + 20 + note.height


def cta_block(im, x, y, s, size=54, right=False, avoid_x=None):
    if right and avoid_x is not None:
        while size > MIN_TYPE:
            w = max(R.text(l, size, B.WHITE, tracking=0.05).width
                    for l in s["cta"])
            if SAFE_RIGHT - w >= avoid_x + 24:
                break
            size -= 2
        else:
            w = max(R.text(l, MIN_TYPE, B.WHITE, tracking=0.05).width
                    for l in s["cta"])
            if SAFE_RIGHT - w < avoid_x + 24:
                raise ValueError(
                    f'CTA "{s["cta"][0]} {s["cta"][1]}" cannot clear the offer '
                    f"at {MIN_TYPE}px - shorten it")
    a = t(s["cta"][0], size, B.WHITE, tracking=0.05)
    b = t(s["cta"][1], size, B.RED, tracking=0.05)
    ax = SAFE_RIGHT - a.width if right else x
    bx = SAFE_RIGHT - b.width if right else x
    put(im, a, ax, y)
    put(im, b, bx, y + a.height + 8)
    return a.height + 8 + b.height


def contact_big(im, x, y):
    """Phone and address with glyphs, at a size that survives a phone screen."""
    g = glyph_phone(44)
    R.paste(im, g, x, y + 2)
    ph = t(PHONE, 46, B.WHITE, tracking=0.06)
    put(im, ph, x + 60, y)
    hd = t(HANDLE, 34, "#C9C8CF", tracking=0.08)
    put(im, hd, x + 60, y + ph.height + 12)
    y2 = y + ph.height + 12 + hd.height + 20
    g2 = glyph_pin(40)
    R.paste(im, g2, x + 2, y2 + 2)
    ad = t(ADDRESS.replace("  ·  ", ", ").title().upper(), 34, B.WHITE,
           tracking=0.08)
    put(im, ad, x + 60, y2)
    st = t(SITE, 34, "#C9C8CF", tracking=0.08)
    put(im, st, x + 60, y2 + ad.height + 12)
    return y2 + ad.height + 12 + st.height - y


def footer_big(im, words, y):
    ft = t("   |   ".join(words), 26, "#8B8A91", tracking=0.20, floor=False)
    R.paste(im, ft, (W - ft.width) // 2, y)


def icon_rows(im, x, y, s, icon=92, lead=52, sub=40, pitch=136):
    """The reference's five-row inclusion list, at phone-legible sizes."""
    for kind, a, b in s["includes5"]:
        R.paste(im, badge(kind, icon), x, y + 6)
        ta = t(a, lead, B.WHITE, tracking=0.04)
        tb = t(b, sub, "#C9C8CF", tracking=0.06)
        put(im, ta, x + icon + 30, y)
        put(im, tb, x + icon + 30, y + ta.height + 10)
        y += pitch
    return y


SERVICE_POSTERS["brakes"].update(
    offer_label="BRAKE SERVICE FROM",
    # "From" is both the sale framing and the accurate one: pads are extra, so
    # 499 is the floor rather than the price.
    includes5=[
        ("rotor",   "ROTORS",      "INSPECTED & MEASURED"),
        ("fluid",   "BRAKE FLUID", "FLUSHED & BLED"),
        ("caliper", "CALIPERS",    "CLEANED & CHECKED"),
        ("pad",     "PADS",        "FACTORY & PERFORMANCE"),
        ("check",   "FULL SAFETY", "INSPECTION"),
    ],
    cta=("BOOK YOUR BRAKE", "SERVICE TODAY"),
)


class Cursor:
    """Vertical layout with a floor, so an overrun is an error not a surprise.

    Three collisions were found by eye in the v1 layouts because blocks were
    placed at H-minus-a-constant and the content above was free to grow into
    them. Here every block reports its height and the cursor refuses to pass
    the floor.
    """

    def __init__(self, y, floor, name):
        self.y, self.floor, self.name = y, floor, name

    def advance(self, h, gap=0):
        self.y += h + gap
        if self.y > self.floor:
            raise ValueError(f"{self.name}: content reached y={self.y:.0f}, "
                             f"floor is {self.floor}")
        return self.y


def qualifier_big(im, y):
    for i, ln in enumerate(QUALIFIER):
        tx = t(ln, 34 if i == 0 else 30, B.WHITE if i == 0 else "#C9C8CF",
               tracking=0.12, floor=False)
        put(im, tx, SAFE_RIGHT - tx.width, y + i * 42)


def contact_compact(im, x, y):
    a = t(f"{PHONE}    {HANDLE}", 40, B.WHITE, tracking=0.06)
    put(im, a, x, y)
    b = t(f"{ADDRESS}    {SITE}", 34, "#C9C8CF", tracking=0.08)
    put(im, b, x, y + a.height + 14)
    return a.height + 14 + b.height


# --------------------------------------------------------------------------
# F - OFFER SPEC.  A, grown to phone sizes and given the reference's five-row
# inclusion list, tagline and TODAY call to action.
# --------------------------------------------------------------------------
def layout_offer_spec(photo, s):
    im = cover(photo, W, H, focus=0.55)
    top_scrim(im, 640, 800)
    base_scrim(im, 620, 700)

    brandmark(im, MARGIN, 66, 58)
    qualifier_big(im, 72)

    c = Cursor(196, H - 120, "F")
    eb = t(s["eyebrow"], 38, B.RED, tracking=0.30)
    put(im, eb, MARGIN, c.y); c.advance(eb.height, 22)
    c.y = headline(im, MARGIN, c.y, s["h1"], s["h2"], size=112); c.advance(0, 26)
    for ln in s["tagline"]:
        tl = t(ln, 42, B.WHITE, tracking=0.05)
        put(im, tl, MARGIN, c.y); c.advance(tl.height, 10)
    c.advance(0, 20)
    R.paste(im, R.accent_stripe(round(W * 0.28), 10), MARGIN, c.y); c.advance(10, 40)

    c.y = icon_rows(im, MARGIN, c.y, s, icon=88, lead=50, sub=38, pitch=126)
    c.advance(0, 26)

    offer_block(im, MARGIN, c.y, s, price_size=132)
    cta_block(im, MARGIN, c.y + 16, s, size=50, right=True)
    c.advance(238, 40)

    contact_big(im, MARGIN, c.y); c.advance(192, 0)
    footer_big(im, FOOT, H - 62)
    return im


# --------------------------------------------------------------------------
# G - OFFER BAND.  B, with the sale carried on a banner across the foot of the
# picture so the offer lands before the copy does.
# --------------------------------------------------------------------------
def layout_offer_band(photo, s):
    # 730 not 780: the five rows plus the CTA and contact need the height more
    # than the picture does, and the Cursor floor proved it by 53px.
    band = 690
    im = Image.new("RGBA", (W, H), (10, 10, 12, 255))
    im.paste(cover(photo, W, band, focus=0.5), (0, 0))
    top_scrim(im, 300, 430)

    brandmark(im, MARGIN, 66, 58)
    qualifier_big(im, 72)

    # The offer banner sits ON the picture - the sale reads first.
    by = band - 132
    ImageDraw.Draw(im).rectangle([0, by, W, band], fill=B.RED)
    ol = t(s["offer_label"], 40, "#FFD9DA", tracking=0.18)
    put(im, ol, MARGIN, by + 24)
    op = R.text(s["price"], 78, B.WHITE, tracking=0.01)
    put(im, op, MARGIN + ol.width + 34, by + 18)
    c = Cursor(band + 26, H - 100, "G")
    on = t(s["fine"], 34, B.RED, tracking=0.14)
    put(im, on, MARGIN, c.y); c.advance(on.height, 22)
    eb = t(s["eyebrow"], 38, B.RED, tracking=0.30)
    put(im, eb, MARGIN, c.y); c.advance(eb.height, 18)
    c.y = headline(im, MARGIN, c.y, s["h1"], s["h2"], size=92); c.advance(0, 26)

    c.y = icon_rows(im, MARGIN, c.y, s, icon=76, lead=44, sub=34, pitch=100)
    c.advance(0, 30)

    cta_block(im, MARGIN, c.y, s, size=52); c.advance(120, 30)
    contact_compact(im, MARGIN, c.y); c.advance(90, 0)
    footer_big(im, FOOT, H - 58)
    return im


# --------------------------------------------------------------------------
# H - OFFER LED.  The most sale-driven of the three: the number is the hero and
# the service name sits under it.
# --------------------------------------------------------------------------
def layout_offer_led(photo, s):
    im = cover(photo, W, H, focus=0.58)
    top_scrim(im, 900, 1040)
    base_scrim(im, 880, 1000)

    brandmark(im, MARGIN, 66, 58)
    qualifier_big(im, 72)

    c = Cursor(214, H - 120, "H")
    lab = t(s["offer_label"], 44, "#C9C8CF", tracking=0.18)
    put(im, lab, MARGIN, c.y); c.advance(lab.height, 6)
    pr = R.fit_text(s["price"], SAFE_RIGHT - MARGIN, max_height=250,
                    color=B.WHITE, tracking=0.0)
    put(im, pr, MARGIN, c.y); c.advance(pr.height, 8)
    note = t(s["fine"], 36, B.RED, tracking=0.16)
    put(im, note, MARGIN, c.y); c.advance(note.height, 34)

    R.paste(im, R.accent_stripe(round(W * 0.34), 10), MARGIN, c.y)
    c.advance(10, 34)
    c.y = headline(im, MARGIN, c.y, s["h1"], s["h2"], size=84); c.advance(0, 30)

    c.y = icon_rows(im, MARGIN, c.y, s, icon=74, lead=44, sub=34, pitch=104)
    c.advance(0, 30)

    cta_block(im, MARGIN, c.y, s, size=52); c.advance(120, 26)
    contact_compact(im, MARGIN, c.y); c.advance(90, 0)
    footer_big(im, FOOT, H - 58)
    return im


LAYOUTS.update({"F": ("offer-spec", layout_offer_spec),
                "G": ("offer-band", layout_offer_band),
                "H": ("offer-led", layout_offer_led)})



# ==========================================================================
# v3 - service first, exotic second, price third.
#
# The hierarchy was upside down: the benefit line was the biggest thing on the
# poster and the service name was a 38px red eyebrow. Now the three things the
# shop wants seen - WHAT it is, WHO it is for, WHAT it costs - are the three
# largest elements, and the benefit line supports them instead of leading.
# ==========================================================================
SERVICE_POSTERS["brakes"].update(
    big=("BRAKE", "SERVICE"),
    for_line="FOR EXOTICS  ·  LUXURY  ·  PERFORMANCE",
    support="STOPS WHEN YOU NEED IT TO.",
)


def service_head(im, x, y, s, width=None, bar=True, cap=210):
    """The service name at full width, then who it is for on a red bar."""
    width = width or (SAFE_RIGHT - x)
    a = R.fit_text(s["big"][0], width, max_height=cap, color=B.WHITE,
                   tracking=0.0)
    put(im, a, x, y)
    b = R.fit_text(s["big"][1], width, max_height=cap, color=B.RED,
                   tracking=0.0)
    put(im, b, x, y + a.height + 4)
    y2 = y + a.height + 4 + b.height
    if not bar:
        return y2 - y
    # A solid red bar is the one place the brand shouts, and it is carrying the
    # qualifier rather than decoration - it says the shop is for this car.
    # Edge to edge, not inset to the text column: the bar reads as a band the
    # poster is wearing rather than another block in the stack. 44px is the
    # largest step up that still lands clear of Instagram's action rail - it
    # ends at x=827 against the rail at 890, where 48px would cross it.
    bh = 82
    ImageDraw.Draw(im).rectangle([0, y2 + 26, W, y2 + 26 + bh], fill=B.RED)
    fl = t(s["for_line"], 44, B.WHITE, tracking=0.14)
    R.paste(im, fl, x + 26, y2 + 26 + (bh - fl.height) // 2)
    return y2 + 26 + bh - y


def price_hero(im, x, y, s, cap=190, right=False):
    """The number, sized to be unmissable rather than tucked in a corner."""
    lab = t(s["offer_label"], 40, "#C9C8CF", tracking=0.18)
    lx = SAFE_RIGHT - lab.width if right else x
    put(im, lab, lx, y)
    # No published price means no invented one. The offer takes the slot, set
    # in words rather than digits, so it still reads as the big promise.
    if s.get("price"):
        pr = R.fit_text(s["price"], SAFE_RIGHT - x, max_height=cap,
                        color=B.WHITE, tracking=0.0)
    else:
        pr = R.fit_text(s.get("big_offer", DM), int((SAFE_RIGHT - x) * 0.56),
                        max_height=int(cap * 0.52), color=B.WHITE,
                        tracking=0.02)
    px = SAFE_RIGHT - pr.width if right else x
    put(im, pr, px, y + lab.height + 10)
    note = t(s["fine"], 34, B.RED, tracking=0.16)
    nx = SAFE_RIGHT - note.width if right else x
    put(im, note, nx, y + lab.height + 10 + pr.height + 16)
    price_hero.right = px + pr.width
    return lab.height + 10 + pr.height + 16 + note.height


# --------------------------------------------------------------------------
# J - SERVICE FIRST.  Full-bleed photo. Name, qualifier, price, in that order.
# --------------------------------------------------------------------------
def layout_service_first(photo, s):
    im = cover(photo, W, H, focus=0.58,
               fx=auto_fx(photo, prefer=s.get("crop", "detail")))
    top_scrim(im, 780, 920)
    base_scrim(im, 620, 760)

    brandmark(im, MARGIN, 62, 54)

    c = Cursor(170, H - 96, "J")
    c.advance(service_head(im, MARGIN, c.y, s), 30)
    sup = t(s["support"], 44, B.WHITE, tracking=0.05)
    put(im, sup, MARGIN, c.y); c.advance(sup.height, 36)

    c.y = icon_rows(im, MARGIN, c.y, s, icon=68, lead=42, sub=34, pitch=100)
    c.advance(0, 26)

    py = c.y
    c.advance(price_hero(im, MARGIN, py, s, cap=170), 8)
    cta_block(im, MARGIN, py + 30, s, size=48, right=True,
               avoid_x=price_hero.right)
    c.advance(0, 30)

    contact_compact(im, MARGIN, c.y); c.advance(90, 0)
    footer_big(im, FOOT, H - 56)
    return im


# --------------------------------------------------------------------------
# K - SERVICE BAND.  Photo band, then name and price on solid ground, so both
# run at full size with nothing competing behind them.
# --------------------------------------------------------------------------
def layout_service_band(photo, s):
    band = 415
    im = Image.new("RGBA", (W, H), (10, 10, 12, 255))
    im.paste(cover(photo, W, band, focus=0.5), (0, 0))
    top_scrim(im, 210, 330)
    brandmark(im, MARGIN, 58, 52)

    c = Cursor(band + 48, H - 96, "K")
    c.advance(service_head(im, MARGIN, c.y, s, cap=175), 26)
    sup = t(s["support"], 42, "#C9C8CF", tracking=0.05)
    put(im, sup, MARGIN, c.y); c.advance(sup.height, 34)

    c.y = icon_rows(im, MARGIN, c.y, s, icon=64, lead=40, sub=34, pitch=88)
    c.advance(0, 24)

    py = c.y
    c.advance(price_hero(im, MARGIN, py, s, cap=135), 6)
    cta_block(im, MARGIN, py + 24, s, size=46, right=True,
               avoid_x=price_hero.right)
    c.advance(0, 26)

    contact_compact(im, MARGIN, c.y); c.advance(90, 0)
    footer_big(im, FOOT, H - 54)
    return im


# --------------------------------------------------------------------------
# L - SERVICE SPLIT.  Name over the picture at the top, price on its own dark
# plate at the foot - the two biggest things at opposite ends of the frame.
# --------------------------------------------------------------------------
def layout_service_split(photo, s):
    im = cover(photo, W, H, focus=0.52)
    top_scrim(im, 720, 880)

    plate_top = 1045
    glass(im, (0, plate_top, W, H), darken=0.62, blur=22)

    brandmark(im, MARGIN, 62, 54)

    c = Cursor(180, plate_top - 40, "L")
    c.advance(service_head(im, MARGIN, c.y, s), 28)
    sup = t(s["support"], 44, B.WHITE, tracking=0.05)
    put(im, sup, MARGIN, c.y); c.advance(sup.height, 0)

    c2 = Cursor(plate_top + 46, H - 92, "L-plate")
    c2.y = icon_rows(im, MARGIN, c2.y, s, icon=56, lead=38, sub=34, pitch=76)
    c2.advance(0, 14)
    py = c2.y
    c2.advance(price_hero(im, MARGIN, py, s, cap=128), 4)
    cta_block(im, MARGIN, py + 22, s, size=46, right=True,
                avoid_x=price_hero.right)
    c2.advance(0, 22)
    contact_compact(im, MARGIN, c2.y); c2.advance(90, 0)
    footer_big(im, FOOT, H - 52)
    return im


LAYOUTS.update({"J": ("service-first", layout_service_first),
                "K": ("service-band", layout_service_band),
                "L": ("service-split", layout_service_split)})



# ==========================================================================
# The rest of the menu, on the approved layout.
#
# Every line item below is lifted from SERVICE-LINE-ITEMS.md rather than
# written fresh, so the ticks and the open boxes in that file still describe
# exactly what is on screen. Where a service has three lines, it gets three -
# the layout takes a short list without complaint, and padding one out would
# mean inventing claims the shop has not seen.
#
# Services with no published price do not get a made-up one. They carry
# DM FOR PRICING, which is the shop's own stated preference for high-ticket
# work: it lets them sell rather than letting the number decide.
# ==========================================================================
def icon_shield(d, s, c):
    w = max(2, int(s * 0.055))
    d.polygon([(s*.5, s*.08), (s*.88, s*.24), (s*.88, s*.56),
               (s*.5, s*.92), (s*.12, s*.56), (s*.12, s*.24)],
              outline=c, width=w)
    d.line([(s*.32, s*.48), (s*.45, s*.62), (s*.70, s*.34)], fill=c,
           width=max(3, int(s*.075)), joint="curve")


def icon_chip(d, s, c):
    w = max(2, int(s * 0.055))
    d.rounded_rectangle([s*.24, s*.24, s*.76, s*.76], radius=s*.08,
                        outline=c, width=w)
    d.rectangle([s*.40, s*.40, s*.60, s*.60], fill=c)
    for i in range(3):
        o = s * (0.34 + i * 0.16)
        for a, b, cc, dd in ((o, s*.08, o, s*.24), (o, s*.76, o, s*.92),
                             (s*.08, o, s*.24, o), (s*.76, o, s*.92, o)):
            d.line([(a, b), (cc, dd)], fill=c, width=w)


def icon_spring(d, s, c):
    w = max(3, int(s * 0.07))
    d.line([(s*.5, s*.06), (s*.5, s*.18)], fill=c, width=w)
    d.line([(s*.5, s*.82), (s*.5, s*.94)], fill=c, width=w)
    for i in range(4):
        y = s * (0.20 + i * 0.155)
        d.line([(s*.24, y), (s*.76, y + s*.075)], fill=c, width=w)
        d.line([(s*.76, y + s*.075), (s*.24, y + s*.155)], fill=c, width=w)


def icon_wrench(d, s, c):
    w = max(3, int(s * 0.10))
    d.line([(s*.30, s*.70), (s*.72, s*.28)], fill=c, width=w)
    d.ellipse([s*.14, s*.54, s*.44, s*.86], outline=c, width=max(2, int(s*.06)))
    d.ellipse([s*.60, s*.14, s*.88, s*.42], outline=c, width=max(2, int(s*.06)))


def icon_calendar(d, s, c):
    w = max(2, int(s * 0.055))
    d.rounded_rectangle([s*.12, s*.20, s*.88, s*.88], radius=s*.07,
                        outline=c, width=w)
    d.line([(s*.12, s*.40), (s*.88, s*.40)], fill=c, width=w)
    d.line([(s*.32, s*.08), (s*.32, s*.26)], fill=c, width=w)
    d.line([(s*.68, s*.08), (s*.68, s*.26)], fill=c, width=w)
    d.rectangle([s*.30, s*.54, s*.46, s*.70], fill=c)


ICONS.update(shield=icon_shield, chip=icon_chip, spring=icon_spring,
             wrench=icon_wrench, calendar=icon_calendar)

DM = "DM FOR PRICING"

MENU = {
 "oil": dict(
   photo="DSC08985-Edit.JPEG", big=("OIL", "SERVICE"),
   support="THE OIL ITSELF, NOT JUST THE LABOR.", crop="body",
   includes5=[("fluid", "OIL & FILTER", "REPLACED"),
              ("check", "MULTI-POINT", "INSPECTION"),
              ("gauge", "FLUIDS", "TOPPED OFF")],
   offer_label="OIL SERVICE FROM", price="$1,199",
   fine="THE OIL IS INCLUDED", cta=("BOOK YOUR OIL", "SERVICE TODAY")),

 "suspension": dict(
   photo="DSC07635-Edit.JPEG", big=("SUSPENSION", "SERVICE"),
   support="RIDES THE WAY IT LEFT THE FACTORY.",
   includes5=[("spring", "RIDE HEIGHT", "SET"),
              ("wrench", "BUSHINGS", "CHECKED"),
              ("gauge", "FOUR-WHEEL", "ALIGNMENT")],
   offer_label="SUSPENSION SERVICE", price=None, big_offer=DM,
   fine="IN THE ANNUAL PACKAGE", cta=("BOOK YOUR", "SERVICE TODAY")),

 "diagnostics": dict(
   photo="DSC06522.JPEG", big=("FULL", "DIAGNOSTICS"),
   support="KNOW WHAT IT NEEDS BEFORE IT BREAKS.",
   includes5=[("chip", "FULL ECU", "SCAN"),
              ("check", "WRITTEN", "REPORT")],
   offer_label="DIAGNOSTICS FROM", price="$499",
   fine="TWO IN THE ANNUAL PACKAGE", cta=("BOOK YOUR", "DIAGNOSTICS TODAY")),

 "fullppf": dict(
   photo="DSC05931.JPEG", big=("FULL CAR", "PPF"),
   support="THE PAINT IS THE EXPENSIVE PART.",
   includes5=[("shield", "EVERY PAINTED", "PANEL"),
              ("shield", "EDGES & JAMBS", "WRAPPED"),
              ("fluid", "EXTERIOR CERAMIC", "COATING"),
              ("fluid", "INTERIOR CERAMIC", "COATING")],
   offer_label="FULL CAR PPF", price=None, big_offer=DM,
   fine="SELF-HEALING FILM", cta=("BOOK YOUR", "PPF TODAY")),

 "windshieldppf": dict(
   photo="DSC08987.JPEG", big=("WINDSHIELD", "PPF"),
   support="EDGE TO EDGE, OPTICALLY CLEAR.",
   includes5=[("shield", "ROCK CHIP", "PROTECTION"),
              ("shield", "EDGE-TO-EDGE", "COVERAGE"),
              ("check", "HEADLIGHT PPF", "FREE")],
   offer_label="WINDSHIELD PPF", price="$899",
   fine="HEADLIGHTS INCLUDED FREE", cta=("BOOK YOUR", "WINDSHIELD TODAY")),

 "tune": dict(
   photo="DSC02047.JPEG", big=("ECU", "TUNE"),
   support="STOCK IS A STARTING POINT.",
   includes5=[("chip", "CUSTOM", "CALIBRATION"),
              ("gauge", "ROAD", "TESTED"),
              ("wrench", "RYFT TITANIUM", "FITTED HERE")],
   offer_label="ECU TUNE", price="FREE",
   fine="WITH A RYFT OR OPUS EXHAUST", cta=("BOOK YOUR", "TUNE TODAY")),

 "gradientppf": dict(
   photo="DSC05812.JPEG", big=("CUSTOM", "GRADIENT PPF"),
   support="A COLOUR NOBODY ELSE IS RUNNING.",
   includes5=[("shield", "COLOR MATCHED", "TO YOU"),
              ("shield", "EVERY PANEL", "WRAPPED"),
              ("fluid", "CERAMIC", "COATING")],
   offer_label="CUSTOM GRADIENT PPF", price=None, big_offer=DM,
   fine="FITTED IN HOUSE", cta=("BOOK YOUR", "WRAP TODAY")),

 "annual": dict(
   photo="DSC05802.JPEG", big=("ANNUAL", "SERVICE PACKAGE"),
   support="A YEAR OF SERVICE, BOUGHT ONCE.",
   includes5=[("fluid", "TWO OIL", "SERVICES"),
              ("rotor", "ONE BRAKE", "SERVICE"),
              ("chip", "TWO", "DIAGNOSTICS"),
              ("spring", "ANY SUSPENSION", "SERVICE"),
              ("calendar", "10% OFF", "UPGRADES")],
   offer_label="ANNUAL PACKAGE", price="$3,999",
   fine="PER YEAR  ·  PARTS SOLD SEPARATELY",
   cta=("ASK ABOUT THE", "ANNUAL PACKAGE")),
}

for _k, _v in MENU.items():
    _v.setdefault("for_line", SERVICE_POSTERS["brakes"]["for_line"])
    _v.setdefault("eyebrow", _v["big"][0] + " " + _v["big"][1])
    _v.setdefault("tagline", (_v["support"], ""))
    _v.setdefault("includes", _v["includes5"][:4])
    SERVICE_POSTERS[_k] = _v



def auto_fx(img, tw=W, th=H, steps=41, prefer="detail"):
    """Aim the crop at the wheel by finding the busiest column window.

    Every shop frame is 3:2 landscape, so a 9:16 crop keeps roughly 30% of the
    width. Centring it is a coin flip - on half these photographs the wheel
    sits right of centre and a centred crop cuts it. Spokes, tyre lettering and
    caliper edges are the highest-frequency detail in the frame, so the window
    with the most edge energy is the wheel. Same technique the poster heroes
    used to pick their frames off the footage.
    """
    from PIL import ImageFilter
    im = img.convert("L").filter(ImageFilter.FIND_EDGES)
    scale = 420 / im.width
    im = im.resize((420, max(1, round(im.height * scale))))
    win = max(1, round(im.height * tw / th))
    if win >= im.width:
        return 0.5
    col = [sum(im.crop((x, 0, x + 1, im.height)).getdata()) for x in range(im.width)]
    # prefer="detail" takes the busiest window - the wheel, which is the
    # subject of a brake ad. prefer="body" takes the calmest, which lands on
    # panel and paint instead. An oil ad that crops to a brake caliper is
    # telling the customer the wrong story, and the same photograph can serve
    # either service depending only on where the window sits.
    run = sum(col[:win])
    best, best_x = run, 0
    for x in range(1, im.width - win):
        run += col[x + win - 1] - col[x - 1]
        if (run > best) if prefer == "detail" else (run < best):
            best, best_x = run, x
    return best_x / (im.width - win)


# ==========================================================================
# The car sets - one approved poster per photograph in the library.
#
# The design is settled, so the variable is the car. Every frame in photos/
# gets the same layout J, which is what turns one approved ad into a set the
# shop can post through.
#
# CROP. auto_fx has two aims. "detail" takes the busiest window - spokes,
# tyre lettering, caliper edges - which is the subject of a brake ad. "body"
# takes the calmest, which lands on paint and panel instead, because an oil
# ad that crops to a brake caliper tells the customer the wrong story.
#
# Neither rule is right on all fifteen. Read off a side-by-side of both modes,
# body-aim wins on the frames where the calm part of the picture is the car -
# a Ferrari shield on a black panel, a clean flank - and loses on the frames
# where the calm part is empty asphalt or a studio wall. Those go back to
# detail aim. The set below is that judgement, per photograph, not a rule.
# ==========================================================================
CROP_DETAIL = {"DSC00075", "DSC05799", "DSC05802", "DSC05812",
               "DSC06522", "DSC06603", "DSC07649-Edit"}


def cars(key, layout=APPROVED_LAYOUT):
    """Render one service against every photograph in the library."""
    cfg = dict(SERVICE_POSTERS[key])
    tag, fn = LAYOUTS[layout]
    title = " ".join(w.title() for w in cfg["big"])
    out = OUT / f"{key}-cars"
    out.mkdir(parents=True, exist_ok=True)

    for src in sorted(PHOTOS.glob("*.JPEG")):
        shot_im = Image.open(src)
        # A poster is 1920 tall. Three frames in the library are 1000x667 web
        # exports, which would be blown up 2.9x to fill it - that is mush on a
        # phone, not a photograph. Skip anything that cannot fill the canvas
        # without upscaling.
        if shot_im.height < H:
            print(f"  skip {src.stem}  {shot_im.width}x{shot_im.height} "
                  f"- under the {W}x{H} canvas")
            continue
        aim = "detail" if src.stem in CROP_DETAIL else cfg.get("crop", "detail")
        shot = dict(cfg, crop=aim)
        im = fn(shot_im, shot)
        path = out / f"{title} - {src.stem}.png"
        im.convert("RGB").save(path)
        print(f"  {path.name}  {aim:6s}  "
              f"{path.stat().st_size / 1e6:.1f} MB")

if __name__ == "__main__":
    main()
