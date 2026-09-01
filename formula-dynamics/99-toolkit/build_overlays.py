#!/usr/bin/env python3
"""
Formula Dynamics Performance - overlay and template generation.

Builds the drag-and-drop layer for video editing: colour swatches, accent
bars, pre-positioned logo bugs, lower thirds, service badges, title cards,
end cards and safe-zone guides.

Every full-frame asset is rendered at the exact pixel size of its canvas, so
in CapCut it drops onto the timeline already in position - no scaling, no
nudging, no drift between clips.

Run:  python3 99-toolkit/build_overlays.py
"""

from PIL import Image, ImageDraw

import fd_brand as B
import fd_render as R

TAGLINE = "PRECISION. PERFORMANCE. PASSION."


# ==========================================================================
# 1. Colour swatches
# ==========================================================================
def build_swatches():
    out = B.BRAND_CORE / "color-swatches"
    for name, hex_code, _ in B.PALETTE:
        im = Image.new("RGB", (1080, 1080), B.rgb(hex_code))
        R.save(im, out / f"fd-{name}-{hex_code.lstrip('#')}.png")

    # A single reference sheet for quick visual pickup.
    sheet = Image.new("RGBA", (1500, 620), B.rgb("#101012") + (255,))
    d = ImageDraw.Draw(sheet)
    w, gap, x = 250, 40, 60
    for name, hex_code, _ in B.PALETTE:
        d.rectangle([x, 120, x + w, 380], fill=B.rgb(hex_code),
                    outline=B.rgb("#333338"), width=2)
        R.paste(sheet, R.text(name, 46, B.WHITE, tracking=0.06), x, 420)
        R.paste(sheet, R.text(hex_code, 34, "#8A8A92", tracking=0.04), x, 480)
        x += w + gap
    R.paste(sheet, R.text("BRAND PALETTE", 52, B.RED, tracking=0.10), 60, 50)
    R.save(sheet.convert("RGB"), out / "_palette-reference.png")
    return len(B.PALETTE) + 1


# ==========================================================================
# 2. Accent bars
# ==========================================================================
def build_accent_bars():
    out = B.OVERLAYS / "accent-bars"
    n = 0
    for width in (1080, 1920, 2160):
        for label, height in (("thin", round(width * 0.011)),
                              ("bold", round(width * 0.022))):
            R.save(R.accent_stripe(width, height),
                   out / f"fd-accent-stripe_{width}w-{label}.png")
            solid = Image.new("RGBA", (width, height), B.rgb(B.RED) + (255,))
            R.save(solid, out / f"fd-red-bar_{width}w-{label}.png")
            n += 2
    return n


# ==========================================================================
# 3. Corner logo bugs - pre-positioned on full frames
# ==========================================================================
# Clear space is one FD-icon height on every side (brand guide section 6).
# Placements are expressed as fractions of frame width/height and already
# respect the 9:16 platform keep-out zones.
BUG_POSITIONS = {
    "top-left":     ("l", "t"),
    "top-center":   ("c", "t"),
    "top-right":    ("r", "t"),
    "bottom-left":  ("l", "b"),
}


def build_logo_bugs():
    out = B.OVERLAYS / "corner-logo-bugs"
    n = 0
    for canvas, (fw, fh) in B.CANVASES.items():
        sz = B.SAFE_ZONES_9X16 if canvas == "9x16" else {
            "top": 0.05, "bottom": 0.07, "left": 0.05, "right": 0.05}
        margin_x = round(fw * 0.06)

        for lockup, share in (("primary-horizontal", 0.30), ("icon-mark-only", 0.09)):
            for tone in ("white", "black"):
                mark = R.logo(f"fd-{lockup}--{tone}", width=round(fw * share))
                for pos, (ax, ay) in BUG_POSITIONS.items():
                    im = R.frame(canvas)
                    x = {"l": margin_x, "c": fw // 2, "r": fw - margin_x}[ax]
                    if ay == "t":
                        y = round(fh * sz["top"]) + round(fh * 0.015)
                    else:
                        y = fh - round(fh * sz["bottom"]) - round(fh * 0.015)
                    R.paste(im, mark, x, y, anchor=ax + ("t" if ay == "t" else "b"))
                    name = "monogram" if lockup == "icon-mark-only" else "logo"
                    R.save(im, out / f"bug_{canvas}_{pos}_{name}-{tone}.png")
                    n += 1
    return n


# ==========================================================================
# 4. Lower thirds
# ==========================================================================
def lower_third(canvas, title, subtitle=None, kicker=None):
    """A legible name plate that clears the platform UI on every format."""
    fw, fh = B.CANVASES[canvas]
    im = R.frame(canvas)

    scale = fw / 1080.0
    pad_x = round(fw * 0.06)
    bar_w = round(22 * scale)
    title_size = round(84 * scale)
    sub_size = round(34 * scale)
    kick_size = round(30 * scale)

    title_im = R.text(title, title_size, B.WHITE, tracking=0.035)
    sub_im = R.text(subtitle, sub_size, "#C9C9D0", tracking=0.10) if subtitle else None
    kick_im = R.text(kicker, kick_size, B.RED, tracking=0.16) if kicker else None

    inner_pad = round(34 * scale)
    text_w = max(title_im.width,
                 sub_im.width if sub_im else 0,
                 kick_im.width if kick_im else 0)
    panel_w = bar_w + inner_pad + text_w + inner_pad
    panel_h = inner_pad
    if kick_im:
        panel_h += kick_im.height + round(14 * scale)
    panel_h += title_im.height
    if sub_im:
        panel_h += round(14 * scale) + sub_im.height
    panel_h += inner_pad

    # Sit above the bottom keep-out zone rather than inside it.
    bottom_zone = B.SAFE_ZONES_9X16["bottom"] if canvas == "9x16" else 0.09
    panel_y = fh - round(fh * bottom_zone) - panel_h - round(fh * 0.03)

    panel = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 224))
    ImageDraw.Draw(panel).rectangle([0, 0, bar_w, panel_h], fill=B.rgb(B.RED) + (255,))

    y = inner_pad
    tx = bar_w + inner_pad
    if kick_im:
        R.paste(panel, kick_im, tx, y)
        y += kick_im.height + round(14 * scale)
    R.paste(panel, title_im, tx, y)
    y += title_im.height
    if sub_im:
        y += round(14 * scale)
        R.paste(panel, sub_im, tx, y)

    R.paste(im, panel, pad_x, panel_y)
    R.paste(im, R.accent_stripe(panel_w, round(9 * scale)), pad_x, panel_y + panel_h)
    return im


def build_lower_thirds():
    out = B.OVERLAYS / "lower-thirds"
    n = 0
    for canvas in ("9x16", "16x9"):
        for slug, label, _ in B.SERVICES:
            R.save(lower_third(canvas, label, B.SERVICE_SUBLINE[slug],
                               "FORMULA DYNAMICS"),
                   out / f"lt_{canvas}_service_{slug}.png")
            n += 1
        for slug, label, _prose, category in B.PARTNERS:
            R.save(lower_third(canvas, label, category, "OFFICIAL PARTNER"),
                   out / f"lt_{canvas}_partner_{slug}.png")
            n += 1
        R.save(lower_third(canvas, "BOOK YOUR BUILD", B.WEBSITE, "GET A QUOTE"),
               out / f"lt_{canvas}_cta_book-your-build.png")
        R.save(lower_third(canvas, B.INSTAGRAM.upper(), B.WEBSITE, "FOLLOW"),
               out / f"lt_{canvas}_cta_follow.png")
        n += 2
    return n


# ==========================================================================
# 5. Service badges
# ==========================================================================
def badge(label, tone="dark"):
    """A standalone chip in the style of the campaign posters."""
    size = 62
    pad_x, pad_y = 46, 28
    radius = 18
    ink = B.WHITE if tone == "dark" else B.BLACK

    label_im = R.text(label, size, ink, tracking=0.09)
    w = label_im.width + pad_x * 2
    h = label_im.height + pad_y * 2

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = (0, 0, 0, 190) if tone == "dark" else (255, 255, 255, 210)
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=radius, fill=fill,
                        outline=B.rgb(B.RED) + (255,), width=4)
    R.paste(im, label_im, w // 2, h // 2, anchor="cm")
    return im


def build_badges():
    out = B.OVERLAYS / "service-badges"
    n = 0
    for slug, label, _ in B.SERVICES:
        for tone in ("dark", "light"):
            R.save(badge(label, tone), out / f"badge_{slug}_{tone}.png")
            n += 1

    # A single strip of the four lead services, ready to drop in one piece.
    for tone in ("dark", "light"):
        chips = [badge(dict((s, l) for s, l, _ in B.SERVICES)[s], tone)
                 for s in B.PRIORITY_SERVICES]
        gap = 26
        w = sum(c.width for c in chips) + gap * (len(chips) - 1)
        h = max(c.height for c in chips)
        strip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = 0
        for c in chips:
            R.paste(strip, c, x, 0)
            x += c.width + gap
        R.save(strip, out / f"badge-strip_lead-services_{tone}.png")
        n += 1
    return n


# ==========================================================================
# 5b. Call-to-action captions
# ==========================================================================
def cta_caption(canvas, lead, accent, style="bar"):
    """A bottom-anchored call to action, clear of the platform UI.

    Two styles, because one is not enough in practice:

    "bar"   - solid brand red, white type. Maximum punch, reads in a glance.
    "panel" - black panel, white type with the accent half in red. Use it when
              the footage is red: a red bar over red paint disappears, and a
              lot of this shop's content is red cars.
    """
    fw, fh = B.CANVASES[canvas]
    im = R.frame(canvas)
    scale = fw / 1080.0

    size = round(74 * scale)
    pad_x = round(56 * scale)
    pad_y = round(30 * scale)
    max_text = fw * 0.78

    gap = 0
    if style == "bar":
        label = R.text(f"{lead} {accent}", size, B.WHITE, tracking=0.05)
        if label.width > max_text:
            label = R.fit_text(f"{lead} {accent}", round(max_text),
                               color=B.WHITE, tracking=0.05)
        parts = [label]
    else:
        gap = round(size * 0.30)
        a = R.text(lead, size, B.WHITE, tracking=0.05)
        b = R.text(accent, size, B.RED, tracking=0.05)
        if a.width + gap + b.width > max_text:
            shrink = max_text / (a.width + gap + b.width)
            small = max(10, round(size * shrink))
            a = R.text(lead, small, B.WHITE, tracking=0.05)
            b = R.text(accent, small, B.RED, tracking=0.05)
            gap = round(small * 0.30)
        parts = [a, b]

    text_w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    text_h = max(p.height for p in parts)
    box_w = text_w + pad_x * 2
    box_h = text_h + pad_y * 2

    # Sit above the bottom keep-out band, never inside it.
    bottom_zone = B.SAFE_ZONES_9X16["bottom"] if canvas == "9x16" else 0.09
    box_y = fh - round(fh * bottom_zone) - box_h - round(fh * 0.03)

    box = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    if style == "bar":
        d.rounded_rectangle([0, 0, box_w - 1, box_h - 1], radius=box_h // 2,
                            fill=B.rgb(B.RED) + (255,))
    else:
        d.rounded_rectangle([0, 0, box_w - 1, box_h - 1],
                            radius=round(14 * scale), fill=(0, 0, 0, 232))

    x = pad_x
    for part in parts:
        R.paste(box, part, x, box_h // 2, anchor="lm")
        x += part.width + gap

    R.paste(im, box, fw // 2, box_y, anchor="ct")

    if style == "panel":
        R.paste(im, R.accent_stripe(box_w, round(9 * scale)),
                fw // 2, box_y + box_h, anchor="ct")
    return im


def build_cta_captions():
    out = B.OVERLAYS / "cta-captions"
    n = 0
    for canvas in ("9x16", "16x9"):
        for slug, lead, accent, group in B.CTA_CAPTIONS:
            for style in ("bar", "panel"):
                R.save(cta_caption(canvas, lead, accent, style),
                       out / f"cta_{canvas}_{group}_{slug}_{style}.png")
                n += 1
    return n


# ==========================================================================
# 6. Title cards
# ==========================================================================
TITLES = [
    ("body-kits", "BODY", "KITS"),
    ("exhaust", "EXHAUST", "UPGRADES"),
    ("wheels", "WHEEL", "FITMENT"),
    ("tuning", "CUSTOM", "TUNING"),
    ("before-after", "BEFORE", "AFTER"),
    ("install-day", "INSTALL", "DAY"),
    ("sound-check", "SOUND", "CHECK"),
    ("dyno-results", "DYNO", "RESULTS"),
    ("the-build", "THE", "BUILD"),
    ("full-send", "FULL", "SEND"),
]


def title_card(canvas, line1, line2, tone="dark"):
    """Poster-style stacked title: white top line, red emphasis line."""
    fw, fh = B.CANVASES[canvas]
    im = R.frame(canvas)
    scale = fw / 1080.0

    top_ink = B.WHITE if tone == "dark" else B.BLACK
    target_w = round(fw * 0.84)

    # Both lines are set to the same measure, as on the campaign posters, but
    # capped in height so a short word does not swallow the frame.
    max_h = min(round(fw * 0.15), round(fh * 0.20))
    a = R.fit_text(line1, target_w, max_h, color=top_ink, tracking=0.01)
    b = R.fit_text(line2, target_w, max_h, color=B.RED, tracking=0.01, italic=0.16)

    # A soft shadow behind the type keeps it readable over bright or busy
    # footage without stamping a visible box onto the frame.
    shadow_opacity = 175 if tone == "dark" else 90
    a = R.with_shadow(a, opacity=shadow_opacity)
    b = R.with_shadow(b, opacity=shadow_opacity)

    y = round(fh * 0.32)
    R.paste(im, a, fw // 2, y, anchor="ct")
    y += a.height - round(14 * scale)
    R.paste(im, R.accent_stripe(round(fw * 0.42), round(10 * scale)),
            fw // 2, y, anchor="ct")
    y += round(30 * scale)
    R.paste(im, b, fw // 2, y, anchor="ct")
    return im


def build_title_cards():
    out = B.OVERLAYS / "title-cards"
    n = 0
    for canvas in ("9x16", "16x9"):
        for slug, l1, l2 in TITLES:
            for tone in ("dark", "light"):
                R.save(title_card(canvas, l1, l2, tone),
                       out / f"title_{canvas}_{slug}_{tone}.png")
                n += 1
    return n


# ==========================================================================
# 7. End cards
# ==========================================================================
# Reference width the end-card content block is composed at, before being
# scaled to fit whichever canvas it is going onto.
ENDCARD_REF_W = 1400


def end_card_block(canvas, tone):
    """Compose the end-card content once, at a fixed reference size.

    Laying out against the frame directly means a landscape canvas runs out of
    height and drops the last line, so the block is built independently and
    scaled to fit afterwards.
    """
    ink = B.WHITE if tone == "dark" else B.BLACK
    muted = "#9A9AA2" if tone == "dark" else "#5A5A62"
    w = ENDCARD_REF_W

    lockup = "fd-stacked" if canvas in ("9x16", "4x5", "1x1") else "fd-primary-horizontal"
    mark = R.logo(f"{lockup}--{'white' if tone == 'dark' else 'black'}",
                  width=round(w * (0.62 if lockup == "fd-stacked" else 0.84)))

    stripe = R.accent_stripe(round(w * 0.40), 13)
    tag = R.text(TAGLINE, 52, ink, tracking=0.14)
    lines = [R.text(t, 48, muted, tracking=0.08) for t in (B.WEBSITE, B.INSTAGRAM)]

    gap_mark, gap_tag, gap_line = 74, 62, 30
    height = (mark.height + gap_mark + stripe.height + gap_tag + tag.height
              + gap_tag + sum(l.height for l in lines) + gap_line * (len(lines) - 1))

    block = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    y = 0
    R.paste(block, mark, w // 2, y, anchor="ct")
    y += mark.height + gap_mark
    R.paste(block, stripe, w // 2, y, anchor="ct")
    y += stripe.height + gap_tag
    R.paste(block, tag, w // 2, y, anchor="ct")
    y += tag.height + gap_tag
    for i, line in enumerate(lines):
        R.paste(block, line, w // 2, y, anchor="ct")
        y += line.height + (gap_line if i < len(lines) - 1 else 0)

    return block.crop(block.getbbox())


def end_card(canvas, tone="dark"):
    fw, fh = B.CANVASES[canvas]
    im = R.frame(canvas, fill=B.BLACK if tone == "dark" else B.WHITE)

    block = end_card_block(canvas, tone)
    fit = min(fw * 0.82 / block.width, fh * 0.74 / block.height)
    block = block.resize((max(1, round(block.width * fit)),
                          max(1, round(block.height * fit))), Image.LANCZOS)

    R.paste(im, block, fw // 2, fh // 2, anchor="cm")
    return im


def build_end_cards():
    out = B.OVERLAYS / "end-cards"
    n = 0
    for canvas in B.CANVASES:
        for tone in ("dark", "light"):
            R.save(end_card(canvas, tone).convert("RGB"),
                   out / f"endcard_{canvas}_{tone}.png")
            n += 1
    return n


# ==========================================================================
# 8. Safe-zone guides
# ==========================================================================
def safe_zone(canvas):
    """A translucent guide layer. Sit it on top while editing, hide before export."""
    fw, fh = B.CANVASES[canvas]
    im = R.frame(canvas)
    d = ImageDraw.Draw(im)
    sz = B.SAFE_ZONES_9X16 if canvas == "9x16" else {
        "top": 0.05, "bottom": 0.07, "left": 0.05, "right": 0.05}

    red = B.rgb(B.RED) + (70,)
    bands = [
        (0, 0, fw, fh * sz["top"]),
        (0, fh * (1 - sz["bottom"]), fw, fh),
        (0, 0, fw * sz["left"], fh),
        (fw * (1 - sz["right"]), 0, fw, fh),
    ]
    for b in bands:
        d.rectangle(list(b), fill=red)

    grid = B.rgb(B.WHITE) + (60,)
    for i in (1, 2):
        d.line([fw * i / 3, 0, fw * i / 3, fh], fill=grid, width=2)
        d.line([0, fh * i / 3, fw, fh * i / 3], fill=grid, width=2)
    d.line([fw / 2, 0, fw / 2, fh], fill=B.rgb(B.GREEN) + (90,), width=2)
    d.line([0, fh / 2, fw, fh / 2], fill=B.rgb(B.GREEN) + (90,), width=2)

    label = f"{canvas}  {fw}x{fh}  -  RED = KEEP TEXT OUT"
    R.paste(im, R.text(label, round(fw / 1080 * 30), B.WHITE, tracking=0.06),
            fw // 2, round(fh * (sz["top"] + 0.02)), anchor="ct")
    return im


def build_safe_zones():
    out = B.TEMPLATES / "safe-zone-guides"
    for canvas in B.CANVASES:
        R.save(safe_zone(canvas), out / f"safe-zones_{canvas}.png")
    return len(B.CANVASES)


# ==========================================================================
if __name__ == "__main__":
    steps = [
        ("colour swatches", build_swatches),
        ("accent bars", build_accent_bars),
        ("logo bugs", build_logo_bugs),
        ("lower thirds", build_lower_thirds),
        ("service badges", build_badges),
        ("CTA captions", build_cta_captions),
        ("title cards", build_title_cards),
        ("end cards", build_end_cards),
        ("safe-zone guides", build_safe_zones),
    ]
    total = 0
    for label, fn in steps:
        count = fn()
        total += count
        print(f"  {label:<20} {count:>4} files")
    print(f"\nDone. {total} overlay/template files written.")
