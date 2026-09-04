#!/usr/bin/env python3
"""
Formula Dynamics Performance - printable brand & video guide (PDF).

Builds FORMULA-DYNAMICS-BRAND-GUIDE.pdf from the same source of truth as every
other asset (fd_brand.py), so the printed guide can never drift from the files
it describes.

Run:  python3 99-toolkit/build_pdf.py
"""

import tempfile
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

import fd_brand as B
import fd_render as R

PAGE_W, PAGE_H = A4
MARGIN = 46
CONTENT_W = PAGE_W - MARGIN * 2

DISPLAY = "Bebas"
BODY = "Helvetica"
BODY_B = "Helvetica-Bold"

INK = "#16161A"
MUTED = "#6A6A74"
RULE = "#DDDDE3"
PANEL = "#F4F4F7"

OUT = B.KIT / "FORMULA-DYNAMICS-BRAND-GUIDE.pdf"

_tmp = Path(tempfile.mkdtemp(prefix="fd-pdf-"))


# --------------------------------------------------------------------------
# Image prep
# --------------------------------------------------------------------------
def flat(stem, width, bg=(58, 60, 66)):
    """Composite a transparent kit asset onto a solid card so it prints."""
    src = B.KIT / stem
    im = Image.open(src).convert("RGBA")
    im = im.resize((width, max(1, round(im.height * width / im.width))),
                   Image.LANCZOS)
    card = Image.new("RGB", im.size, bg)
    card.paste(im, (0, 0), im)
    out = _tmp / (stem.replace("/", "_"))
    card.save(out)
    return str(out)


def logo_png(stem, width):
    im = R.logo(stem, width=width)
    card = Image.new("RGBA", im.size, (0, 0, 0, 0))
    card.alpha_composite(im)
    out = _tmp / f"{stem}_{width}.png"
    card.save(out)
    return str(out)


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------
class Doc:
    def __init__(self, canvas):
        self.c = canvas
        self.page = 0
        self._open = False      # a page is started but not yet flushed
        self._footer = True     # ...and whether it should get a footer

    # -- primitives --------------------------------------------------------
    def rect(self, x, y, w, h, fill):
        self.c.setFillColor(fill)
        self.c.rect(x, y, w, h, stroke=0, fill=1)

    def line(self, x1, y1, x2, y2, color=RULE, width=1):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(width)
        self.c.line(x1, y1, x2, y2)

    def stripe(self, x, y, w, h=4.5):
        """The four-colour racing stripe."""
        cx = x
        for hex_code, share in B.ACCENT_STRIPE:
            seg = w * share
            self.rect(cx, y, seg, h, hex_code)
            cx += seg

    def _tracked(self, text, x, y, font, size, color, tracking):
        """Draw letter-spaced text.

        PDF char spacing (Tc) is graphics state and survives ET, so it would
        leak into every later paragraph and push wrapped text past the measured
        width. Resetting it after the glyphs, inside the same block, keeps the
        spacing on this run only.
        """
        t = self.c.beginText(x, y)
        t.setFont(font, size)
        t.setFillColor(color)
        t.setCharSpace(size * tracking)
        t.textOut(text)
        t.setCharSpace(0)
        self.c.drawText(t)

    def text_width(self, text, font, size, tracking):
        return (pdfmetrics.stringWidth(text, font, size)
                + size * tracking * max(0, len(text) - 1))

    def display(self, text, x, y, size, color=INK, tracking=0.06):
        self._tracked(text.upper(), x, y, DISPLAY, size, color, tracking)

    def display_fit(self, text, x, y, size, max_w, color=INK, tracking=0.06):
        """Draw display type, shrinking it to fit `max_w` rather than
        letting a long name run into the next column."""
        while size > 8 and self.text_width(text.upper(), DISPLAY, size,
                                           tracking) > max_w:
            size -= 0.5
        self._tracked(text.upper(), x, y, DISPLAY, size, color, tracking)

    def display_centred(self, text, cx, y, size, color=INK, tracking=0.06):
        w = self.text_width(text.upper(), DISPLAY, size, tracking)
        self._tracked(text.upper(), cx - w / 2, y, DISPLAY, size, color, tracking)

    def label(self, text, x, y, size=7.5, color=MUTED, tracking=0.16):
        self._tracked(text.upper(), x, y, BODY_B, size, color, tracking)

    def body(self, html, x, y, w, size=9.4, leading=14.2, color=INK):
        """Draw wrapped body copy. Returns the y of the bottom of the block."""
        style = ParagraphStyle("b", fontName=BODY, fontSize=size,
                               leading=leading, textColor=color)
        p = Paragraph(html, style)
        _, h = p.wrapOn(self.c, w, PAGE_H)
        p.drawOn(self.c, x, y - h)
        return y - h

    def bullets(self, items, x, y, w, size=9.4, leading=14.2, gap=6):
        for it in items:
            self.rect(x + 1, y - 6.5, 3.5, 3.5, B.RED)
            y = self.body(it, x + 14, y, w - 14, size, leading) - gap
        return y

    def table(self, rows, x, y, widths, head=True, size=8.8, row_h=None):
        """A light, ruled table. rows[0] is the header when head is True."""
        pad = 7
        for i, row in enumerate(rows):
            cells = []
            max_h = 0
            for text, cw in zip(row, widths):
                bold = head and i == 0
                style = ParagraphStyle(
                    "t", fontName=BODY_B if bold else BODY, fontSize=size,
                    leading=size * 1.42,
                    textColor=INK if bold else "#3A3A44")
                p = Paragraph(text, style)
                _, h = p.wrapOn(self.c, cw - pad * 2, PAGE_H)
                cells.append((p, h, cw))
                max_h = max(max_h, h)
            h = (row_h or max_h + pad * 1.6)

            if head and i == 0:
                self.rect(x, y - h, sum(widths), h, PANEL)
            cx = x
            for p, ph, cw in cells:
                p.drawOn(self.c, cx + pad, y - pad * 0.8 - ph)
                cx += cw
            y -= h
            self.line(x, y, x + sum(widths), y)
        return y

    # -- page furniture ----------------------------------------------------
    def new_page(self, kicker, title):
        if self._open:
            if self._footer:
                self.footer()
            self.c.showPage()
        self.page += 1
        self._open = True
        self._footer = True

        self.c.setFillColor("#FFFFFF")
        self.c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

        top = PAGE_H - MARGIN
        self.stripe(MARGIN, top - 6, 132, 4)
        self.label(kicker, MARGIN, top - 24, 7.5, B.RED, 0.20)
        self.display(title, MARGIN, top - 58, 27)
        self.line(MARGIN, top - 74, PAGE_W - MARGIN, top - 74)
        return top - 100

    def footer(self):
        y = MARGIN - 14
        self.line(MARGIN, y + 16, PAGE_W - MARGIN, y + 16, RULE)
        self.c.setFillColor(MUTED)
        self.c.setFont(BODY, 7.4)
        self.c.drawString(MARGIN, y, "Formula Dynamics Performance  ·  Brand & Video Asset Guide")
        self.c.drawRightString(PAGE_W - MARGIN, y, str(self.page))

    def finish(self):
        self.footer()
        self.c.showPage()
        self.c.save()


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def page_cover(d):
    c = d.c
    d.page = 1
    d._open = True
    d._footer = False          # the cover carries no running footer
    d.rect(0, 0, PAGE_W, PAGE_H, "#0A0A0C")

    c.drawImage(logo_png("fd-primary-horizontal--white", 1600),
                MARGIN, PAGE_H - 300, width=330, height=330 / 2.384,
                mask="auto")

    d.stripe(MARGIN, PAGE_H - 340, 240, 6)

    d.display("BRAND &", MARGIN, PAGE_H - 430, 54, "#FFFFFF", 0.02)
    d.display("VIDEO ASSET", MARGIN, PAGE_H - 486, 54, "#FFFFFF", 0.02)
    d.display("GUIDE", MARGIN, PAGE_H - 542, 54, B.RED, 0.02)

    d.body(
        "Everything needed to edit on-brand video &mdash; colours, type, logo "
        "rules, the overlay library, CapCut workflow, shot formulas and copy.",
        MARGIN, PAGE_H - 580, 330, 10.4, 15.5, "#B8B8C2")

    y = 150
    d.line(MARGIN, y + 34, PAGE_W - MARGIN, y + 34, "#2A2A32")
    d.label("CONTACT", MARGIN, y + 12, 7.5, B.RED, 0.20)
    c.setFillColor("#D6D6DE")
    c.setFont(BODY, 9.6)
    for i, line in enumerate((B.WEBSITE, B.INSTAGRAM, B.EMAIL)):
        c.drawString(MARGIN, y - 12 - i * 15, line)

    c.setFillColor("#55555F")
    c.setFont(BODY, 7.6)
    c.drawRightString(PAGE_W - MARGIN, y - 42,
                      "Generated from the kit source of truth · 99-toolkit/build_pdf.py")


def page_contents(d):
    y = d.new_page("Start here", "Contents")

    rows = [["Page", "Section", "What it answers"]]
    for n, sec, ans in CONTENTS:
        rows.append([str(n), f"<b>{sec}</b>", ans])
    y = d.table(rows, MARGIN, y, [42, 150, CONTENT_W - 192])

    y -= 30
    d.rect(MARGIN, y - 108, CONTENT_W, 108, PANEL)
    d.rect(MARGIN, y - 108, 4, 108, B.RED)
    d.label("THE ONE RULE THAT SAVES THE MOST TIME", MARGIN + 20, y - 26, 8, B.RED)
    d.body(
        "<b>Every full-frame overlay is rendered at the exact pixel size of its "
        "canvas.</b> A file ending <b>_9x16</b> is exactly 1080 &times; 1920. Set your "
        "CapCut project to 9:16 and that overlay drops onto the timeline already "
        "in position at 100% scale &mdash; no resizing, no nudging. That is what keeps "
        "the logo in identical placement across every video you post.",
        MARGIN + 20, y - 38, CONTENT_W - 40, 9.4, 14)


def page_palette(d):
    y = d.new_page("01 · Brand core", "Colour palette")

    sw, gap = 88, 14
    x = MARGIN
    for name, hex_code, _ in B.PALETTE:
        d.rect(x, y - 88, sw, 88, hex_code)
        if hex_code == "#FFFFFF":
            d.c.setStrokeColor(RULE)
            d.c.setLineWidth(1)
            d.c.rect(x, y - 88, sw, 88, stroke=1, fill=0)
        d.display(name, x, y - 108, 15)
        d.c.setFillColor(MUTED)
        d.c.setFont(BODY, 8.4)
        d.c.drawString(x, y - 122, hex_code)
        d.c.drawString(x, y - 133, "rgb(%d, %d, %d)" % B.rgb(hex_code))
        x += sw + gap

    y -= 168
    rows = [["Colour", "Role"]] + [[f"<b>{n.title()}</b>", r] for n, _, r in B.PALETTE]
    y = d.table(rows, MARGIN, y, [110, CONTENT_W - 110])

    y -= 26
    d.rect(MARGIN, y - 62, CONTENT_W, 62, "#FFF3F3")
    d.rect(MARGIN, y - 62, 4, 62, B.RED)
    d.label("IMPORTANT", MARGIN + 20, y - 22, 8, B.RED)
    d.body("<b>Green and yellow are stripe colours, not brand colours.</b> They appear "
           "only inside the four-colour accent stripe. Never set a headline in green "
           "or fill a background with yellow.",
           MARGIN + 20, y - 32, CONTENT_W - 40, 9.4, 13.5)

    y -= 92
    d.label("THE ACCENT STRIPE", MARGIN, y, 8, INK)
    d.stripe(MARGIN, y - 22, CONTENT_W, 10)
    d.body("Red &rarr; White &rarr; Green &rarr; Yellow, left to right, in roughly "
           "42 / 24 / 20 / 14 proportion. Ready-made bars live in "
           "<b>03-overlays/accent-bars/</b>.",
           MARGIN, y - 34, CONTENT_W, 9.2, 13)


def page_type(d):
    y = d.new_page("01 · Brand core", "Typography")

    d.label("PRIMARY TYPEFACE · HEADLINES", MARGIN, y, 8, B.RED)
    d.display("BEBAS NEUE", MARGIN, y - 46, 40)
    d.c.setFillColor(MUTED)
    d.c.setFont(BODY, 8.6)
    d.c.drawString(MARGIN, y - 62, "Bold Condensed  ·  bundled in 07-fonts/  ·  SIL Open Font License 1.1")
    d.display("ABCDEFGHIJKLMNOPQRSTUVWXYZ", MARGIN, y - 92, 19, "#3A3A44", 0.04)
    d.display("0123456789", MARGIN, y - 116, 19, "#3A3A44", 0.04)

    y -= 156
    d.line(MARGIN, y + 14, PAGE_W - MARGIN, y + 14)
    d.label("ACCENT TYPEFACE · PERFORMANCE", MARGIN, y - 8, 8, B.RED)
    d.display("NEUROPOL X", MARGIN, y - 50, 34, MUTED)
    d.body("<b>Commercial licence &mdash; not bundled.</b> You mostly don't need it: the "
           "word &ldquo;PERFORMANCE&rdquo; is already part of the vector logo artwork and "
           "scales to any size. Neuropol X is only required to set <i>new</i> words in "
           "that style. Where this kit needs the look, it uses italicised Bebas Neue.",
           MARGIN, y - 66, CONTENT_W, 9.4, 13.8)

    y -= 156
    d.label("SUBSTITUTES, IN ORDER OF PREFERENCE", MARGIN, y, 8, INK)
    y = d.table([["Substitute", "Where", "Notes"],
                 ["<b>Oswald</b>", "Google Fonts, free", "Closest free match"],
                 ["<b>Anton</b>", "Google Fonts, free", "Heavier; good for big titles"],
                 ["<b>Archivo Narrow</b>", "Google Fonts, free", "More neutral"],
                 ["Arial Narrow Bold", "System", "Last resort"]],
                MARGIN, y - 14, [140, 150, CONTENT_W - 290])

    y -= 26
    d.label("TYPE RULES", MARGIN, y, 8, INK)
    d.bullets([
        "Headlines in <b>caps</b>, Bebas Neue, 2&ndash;4% letter-spacing.",
        "Emphasis: <b>one word</b> in red <b>#FE0F13</b> &mdash; never a whole line.",
        "Never stretch or condense type to fit. Change the size instead.",
        "Never outline headline type in red. White with a black outline or shadow.",
        "Two weights maximum on screen at once. Usually one is enough.",
    ], MARGIN, y - 16, CONTENT_W)


def page_logos(d):
    y = d.new_page("02 · Logos", "Logo lockups")

    d.body("Four lockups, each supplied in four colour variants, as true vector SVG "
           "plus PNG at 1000 / 2000 / 4000&nbsp;px wide.",
           MARGIN, y, CONTENT_W, 9.6, 14)
    y -= 34

    specs = [("fd-primary-horizontal--black", 210, "Primary horizontal",
              "The default. Corner bugs, end cards, wide layouts."),
             ("fd-stacked--black", 108, "Compact stacked",
              "Tight or vertical space, centred end cards, profile art."),
             ("fd-icon--black", 100, "Icon / monogram",
              "Compact mark where the name is already known."),
             ("fd-icon-mark-only--black", 78, "Bare monogram",
              "Tiny watermarks, favicons, profile pictures, app icons.")]

    for stem, w_pt, name, use in specs:
        im = R.logo(stem, width=1200)
        h_pt = w_pt * im.height / im.width
        block_h = max(h_pt, 46) + 26
        d.rect(MARGIN, y - block_h, CONTENT_W, block_h, PANEL)
        d.c.drawImage(logo_png(stem, 1400), MARGIN + 22,
                      y - block_h + (block_h - h_pt) / 2,
                      width=w_pt, height=h_pt, mask="auto")
        tx = MARGIN + 268
        d.display(name, tx, y - block_h + block_h / 2 + 6, 15)
        d.body(use, tx, y - block_h + block_h / 2 - 2, CONTENT_W - 290, 8.6, 12, MUTED)
        y -= block_h + 10

    y -= 2
    d.label("PICK THE VARIANT BY BACKGROUND", MARGIN, y, 8, INK)
    d.table([["Background", "Variant", "Why"],
             ["Dark footage / black", "<b>--white</b>", "White wordmark, red PERFORMANCE"],
             ["Light footage / white", "<b>--black</b>", "Black wordmark, red PERFORMANCE"],
             ["Busy, mixed or moving", "<b>--mono-white</b> / <b>--mono-black</b>",
              "Single colour, no red &mdash; maximum legibility"]],
            MARGIN, y - 14, [148, 158, CONTENT_W - 306])


def page_logo_rules(d):
    y = d.new_page("02 · Logos", "Logo rules")

    d.label("CLEAR SPACE", MARGIN, y, 8, B.RED)
    # Track the real bottom of the paragraph so the diagram can never land on it.
    y = d.body("Keep clear space equal to <b>the height of the FD icon</b> on all four "
               "sides. Nothing &mdash; text, frame edges, other graphics &mdash; inside that margin.",
               MARGIN, y - 14, CONTENT_W, 9.4, 13.8) - 18

    im = R.logo("fd-primary-horizontal--black", width=1200)
    lw = 196
    lh = lw * im.height / im.width
    pad = lh * 0.62 * 0.55
    box_h = lh + pad * 2
    box_y = y - box_h

    d.rect(MARGIN, box_y, lw + pad * 2, box_h, PANEL)
    d.c.setStrokeColor("#B9B9C4")
    d.c.setLineWidth(0.8)
    d.c.setDash(3, 3)
    d.c.rect(MARGIN + pad, box_y + pad, lw, lh, stroke=1, fill=0)
    d.c.setDash()
    d.c.drawImage(logo_png("fd-primary-horizontal--black", 1400),
                  MARGIN + pad, box_y + pad, width=lw, height=lh, mask="auto")
    d.label("MINIMUM CLEAR SPACE = FD ICON HEIGHT",
            MARGIN + lw + pad * 2 + 20, box_y + box_h / 2 - 3, 7.6, MUTED)

    y = box_y - 30
    d.label("MINIMUM SIZE", MARGIN, y, 8, B.RED)
    y = d.table([["Medium", "Minimum width", "In context"],
                 ["Print", "<b>25 mm</b>", "&mdash;"],
                 ["Digital / screen", "<b>120 px</b>",
                  "11% of a 1080-wide frame. The supplied bugs sit at 30%."]],
                MARGIN, y - 14, [130, 120, CONTENT_W - 250])

    y -= 26
    d.label("SIZING THE LOGO YOURSELF", MARGIN, y, 8, B.RED)
    y = d.bullets([
        "Practical range for a corner bug is <b>22&ndash;32% of frame width</b>.",
        "Always scale with the aspect ratio locked. In CapCut drag a <b>corner</b> "
        "handle &mdash; an edge handle stretches the logo, which the brand guide prohibits.",
        "Better still, use the pre-positioned bugs in <b>03-overlays/corner-logo-bugs/</b> "
        "and don't scale at all.",
    ], MARGIN, y - 14, CONTENT_W)

    y -= 16
    col = (CONTENT_W - 18) / 2
    d.rect(MARGIN, y - 126, col, 126, "#F0FAF3")
    d.rect(MARGIN, y - 126, 4, 126, B.GREEN)
    d.label("DO", MARGIN + 18, y - 22, 9, B.GREEN)
    d.bullets(["Use approved logo files from <b>02-logos/</b>.",
               "Maintain clear space.",
               "Use approved brand colours.",
               "Ensure legibility at every size."],
              MARGIN + 18, y - 34, col - 36, 8.6, 12, 3)

    x2 = MARGIN + col + 18
    d.rect(x2, y - 126, col, 126, "#FFF3F3")
    d.rect(x2, y - 126, 4, 126, B.RED)
    d.label("DON'T", x2 + 18, y - 22, 9, B.RED)
    d.bullets(["Stretch or distort the logo.",
               "Change colours or add effects.",
               "Recreate or redraw the logo.",
               "Place it on a busy background."],
              x2 + 18, y - 34, col - 36, 8.6, 12, 3)


def page_canvases(d):
    y = d.new_page("03 · Formats", "Canvases & safe zones")

    y = d.table([["Suffix", "Pixels", "Use for"],
                 ["<b>9x16</b>", "1080 &times; 1920", "TikTok, Reels, Shorts &mdash; <b>your main format</b>"],
                 ["<b>4x5</b>", "1080 &times; 1350", "Instagram feed video"],
                 ["<b>1x1</b>", "1080 &times; 1080", "Square feed posts"],
                 ["<b>16x9</b>", "1920 &times; 1080", "YouTube, website, landing hero"]],
                MARGIN, y, [80, 110, CONTENT_W - 190])

    y -= 28
    img_w = 150
    img_h = img_w * 1920 / 1080
    d.c.drawImage(flat("04-templates/safe-zone-guides/safe-zones_9x16.png", 600,
                       bg=(120, 122, 128)),
                  MARGIN, y - img_h, width=img_w, height=img_h)

    tx = MARGIN + img_w + 24
    tw = CONTENT_W - img_w - 24
    d.label("READING THE SAFE-ZONE GUIDE", tx, y - 12, 8, B.RED)
    d.bullets([
        "<b>Red bands</b> &mdash; platform UI sits here. No logos, no text, no faces.",
        "<b>White lines</b> &mdash; thirds grid, for composing shots.",
        "<b>Green cross</b> &mdash; exact frame centre.",
    ], tx, y - 26, tw, 9, 13, 6)

    yy = y - 100
    d.body("Drop the guide matching your canvas onto the <b>top</b> track while "
           "editing, then <b>hide or delete that layer before exporting.</b> The 9:16 "
           "zones are sized for the TikTok/Reels/Shorts chrome: status bar on top, "
           "caption and CTA at the bottom, like/comment/share rail on the right.",
           tx, yy, tw, 9.2, 13.6)

    y -= img_h + 26
    d.rect(MARGIN, y - 58, CONTENT_W, 58, PANEL)
    d.rect(MARGIN, y - 58, 4, 58, B.RED)
    d.body("<b>Set the canvas ratio before you add overlays.</b> If an overlay looks "
           "the wrong size, the project ratio doesn't match the filename &mdash; fix the "
           "ratio, don't scale the overlay.",
           MARGIN + 20, y - 18, CONTENT_W - 40, 9.4, 13.5)


def page_overlays(d):
    y = d.new_page("03 · Overlays", "The overlay library")

    d.body("Transparent PNGs built to sit on top of footage. Full-frame assets are "
           "rendered at exact canvas size, so they need no scaling.",
           MARGIN, y, CONTENT_W, 9.6, 14)
    y -= 30

    shots = [("03-overlays/title-cards/title_9x16_body-kits_dark.png", "Title cards"),
             ("03-overlays/corner-logo-bugs/bug_9x16_top-left_logo-white.png", "Logo bugs"),
             ("03-overlays/lower-thirds/lt_9x16_service_exhaust.png", "Lower thirds"),
             ("03-overlays/end-cards/endcard_9x16_dark.png", "End cards")]

    tw = (CONTENT_W - 3 * 14) / 4
    th = tw * 1920 / 1080
    x = MARGIN
    for stem, name in shots:
        d.c.drawImage(flat(stem, 420), x, y - th, width=tw, height=th)
        d.label(name, x, y - th - 14, 7.6, INK)
        x += tw + 14

    y -= th + 40
    y = d.table([
        ["Folder", "What it is", "Naming"],
        ["<b>corner-logo-bugs/</b>", "Logo pre-positioned on a full frame. Clears the platform UI.",
         "bug_<i>canvas</i>_<i>position</i>_<i>type-tone</i>"],
        ["<b>lower-thirds/</b>", "Service, partner and CTA name plates.",
         "lt_<i>canvas</i>_<i>kind</i>_<i>name</i>"],
        ["<b>title-cards/</b>", "Two-line openers: white top line, red italic beneath.",
         "title_<i>canvas</i>_<i>name</i>_<i>tone</i>"],
        ["<b>end-cards/</b>", "Full-frame closing card with contact details. Not transparent.",
         "endcard_<i>canvas</i>_<i>tone</i>"],
        ["<b>service-badges/</b>", "Red-outlined chips for feature callouts.",
         "badge_<i>service</i>_<i>tone</i>"],
        ["<b>accent-bars/</b>", "Racing stripe and solid red bars. Also the house transition.",
         "fd-accent-stripe_<i>width</i>w-<i>weight</i>"],
    ], MARGIN, y, [116, CONTENT_W - 296, 180])

    y -= 24
    d.rect(MARGIN, y - 62, CONTENT_W, 62, PANEL)
    d.rect(MARGIN, y - 62, 4, 62, B.RED)
    d.label("HOUSE TRANSITION", MARGIN + 20, y - 22, 8, B.RED)
    d.body("Drop <b>fd-accent-stripe_1080w-bold.png</b> on a cut and keyframe its X "
           "position across the frame over 6&ndash;10 frames. Cheapest on-brand transition "
           "you can make.", MARGIN + 20, y - 32, CONTENT_W - 40, 9.2, 13)


def page_workflow(d):
    y = d.new_page("04 · Video system", "CapCut workflow")

    d.label("BUILD ORDER &mdash; WORK TOP-DOWN, EACH STEP A NEW TRACK", MARGIN, y, 8, B.RED)
    y = d.table([["#", "Track", "What goes on it"],
                 ["1", "<b>Footage</b>", "Rough cut. Get timing right before any graphics."],
                 ["2", "<b>Title card</b>", "First 1&ndash;2 s."],
                 ["3", "<b>Logo bug</b>", "Full duration."],
                 ["4", "<b>Lower third</b>", "1&ndash;2 s in, hold 3&ndash;4 s."],
                 ["5", "<b>Badges / stats</b>", "On the feature shots."],
                 ["6", "<b>End card</b>", "Last 1.5&ndash;2.5 s."],
                 ["7", "<b>Audio</b>", "Music, engine audio, VO."],
                 ["8", "<b>Captions</b>", "Auto-captions, restyled."]],
                MARGIN, y - 14, [34, 110, CONTENT_W - 144])

    y -= 20
    d.body("<b>Cut the picture first.</b> Adding graphics before the edit is locked "
           "means redoing them. And <b>never resize a full-frame overlay</b> &mdash; it is "
           "already frame-size and positioned.",
           MARGIN, y, CONTENT_W, 9.2, 13.4)

    y -= 46
    d.label("ANIMATION &mdash; FAST AND MECHANICAL. MOTORSPORT, NOT WEDDING VIDEO.",
            MARGIN, y, 8, B.RED)
    y = d.table([["Element", "In", "Out"],
                 ["Title card", "Scale 105%&nbsp;&rarr;&nbsp;100% over 8 frames + fade", "Fade 4 frames"],
                 ["Logo bug", "Fade in over 6 frames", "Hold to end"],
                 ["Lower third", "Slide from left over 8 frames", "Slide out or fade"],
                 ["Badge", "Pop: scale 90%&nbsp;&rarr;&nbsp;100% over 5 frames", "Fade"],
                 ["End card", "Cut straight in, no fade", "&mdash;"]],
                MARGIN, y - 14, [96, 240, CONTENT_W - 336])

    y -= 26
    d.label("CAPTIONS", MARGIN, y, 8, B.RED)
    d.bullets([
        "Font <b>Bebas Neue</b>; white with a black outline or subtle shadow.",
        "Key word in red <b>#FE0F13</b> &mdash; the part number, horsepower figure, price, "
        "the payoff word. Never body text, never the outline.",
        "Keep captions above the bottom keep-out zone.",
    ], MARGIN, y - 14, CONTENT_W)


def page_troubleshoot(d):
    y = d.new_page("04 · Video system", "Troubleshooting")

    d.label("COMMON MISTAKES", MARGIN, y, 8, B.RED)
    y = d.table([["Symptom", "Cause", "Fix"],
                 ["Logo in a different spot each video", "Overlay manually scaled or moved",
                  "Re-add the bug and don't touch it"],
                 ["Logo looks stretched", "Dragged an edge handle",
                  "Undo; drag a <b>corner</b> handle"],
                 ["Text cut off on TikTok", "Sat inside the keep-out zone",
                  "Check the safe-zone guide"],
                 ["Overlay too small or letterboxed", "Canvas ratio &ne; file canvas",
                  "Set ratio first, then re-add"],
                 ["Logo invisible on light footage", "Used <b>-white</b> on white",
                  "Use the <b>-black</b> bug"],
                 ["Logo lost on busy paint", "Full colour on a detailed panel",
                  "Use <b>mono-white</b> / <b>mono-black</b>"]],
                MARGIN, y - 14, [168, 152, CONTENT_W - 320])

    y -= 32
    d.label("BEFORE YOU POST", MARGIN, y, 8, B.RED)
    y -= 18
    for ch in ["Safe-zone guide layer hidden or deleted",
               "Logo bug present, full duration, correct tone for the footage",
               "Nothing important inside the keep-out bands",
               "End card holds 1.5 s or more",
               "Audio peaks below 0 dB &mdash; no clipping on exhaust notes",
               "Caption spelling: model names, part numbers, partner names",
               "Exported at 1080p, 20 Mbps or higher",
               "Watched once on a phone before posting"]:
        d.c.setStrokeColor("#9A9AA4")
        d.c.setLineWidth(0.9)
        d.c.rect(MARGIN + 1, y - 8.5, 8, 8, stroke=1, fill=0)
        d.body(ch, MARGIN + 18, y, CONTENT_W - 18, 9.2, 12.5)
        y -= 18

    y -= 18
    d.rect(MARGIN, y - 72, CONTENT_W, 72, PANEL)
    d.rect(MARGIN, y - 72, 4, 72, B.RED)
    d.label("IF AN OVERLAY LOOKS WRONG-SIZED", MARGIN + 20, y - 22, 8, B.RED)
    d.body("The project ratio doesn't match the filename. <b>Fix the ratio, don't "
           "scale the overlay.</b> Scaling is what breaks placement consistency "
           "between videos &mdash; the single thing that makes a feed look amateur.",
           MARGIN + 20, y - 32, CONTENT_W - 40, 9.2, 13.2)


def page_export(d):
    y = d.new_page("04 · Video system", "Export specs")

    y = d.table([["Platform", "Ratio", "Resolution", "FPS", "Length"],
                 ["TikTok", "9:16", "1080 &times; 1920", "30 / 60", "15&ndash;60 s"],
                 ["Instagram Reels", "9:16", "1080 &times; 1920", "30 / 60", "15&ndash;90 s"],
                 ["YouTube Shorts", "9:16", "1080 &times; 1920", "30 / 60", "&le; 60 s"],
                 ["Instagram feed", "4:5", "1080 &times; 1350", "30", "15&ndash;60 s"],
                 ["YouTube", "16:9", "1920 &times; 1080", "30 / 60", "any"]],
                MARGIN, y, [130, 62, 118, 78, CONTENT_W - 388])

    y -= 24
    d.body("<b>Shoot 60&nbsp;fps</b> even when delivering 30 &mdash; it gives you clean slow "
           "motion for reveals and rolling shots. Match the project frame rate to the "
           "footage and don't convert on export.",
           MARGIN, y, CONTENT_W, 9.4, 13.8)

    y -= 40
    d.label("EXPORT SETTINGS", MARGIN, y, 8, B.RED)
    y = d.table([["Setting", "Value"],
                 ["Codec", "H.264"],
                 ["Resolution", "1080p"],
                 ["Frame rate", "Match the project"],
                 ["Bitrate", "<b>Higher / 20 Mbps+</b> &mdash; CapCut's &ldquo;Recommended&rdquo; is too low for car paint"],
                 ["Format", "MP4"],
                 ["Audio", "AAC, 320 kbps"]],
                MARGIN, y - 14, [130, CONTENT_W - 130])

    y -= 22
    d.body("Low bitrate shows up as blocking in dark paint, smearing on carbon fibre "
           "and banding in sky gradients &mdash; exactly the shots you care about.",
           MARGIN, y, CONTENT_W, 9.2, 13.4)

    y -= 40
    d.label("COLOUR", MARGIN, y, 8, B.RED)
    y = d.bullets([
        "Don't crush blacks &mdash; keep shadow detail; compression eats it.",
        "Don't over-sharpen. It amplifies compression artefacts.",
        "Keep red near <b>#FE0F13</b>. Oversaturated red clips and goes orange.",
    ], MARGIN, y - 14, CONTENT_W)

    y -= 12

    y -= 20
    d.rect(MARGIN, y - 72, CONTENT_W, 72, PANEL)
    d.rect(MARGIN, y - 72, 4, 72, B.RED)
    d.label("WHY BITRATE MATTERS MORE THAN RESOLUTION HERE", MARGIN + 20, y - 22, 8, B.RED)
    d.body("Car paint, carbon fibre and sky gradients are the hardest things you can "
           "hand a video codec. CapCut's &ldquo;Recommended&rdquo; bitrate is tuned for talking "
           "heads. Always export <b>Higher</b>.",
           MARGIN + 20, y - 32, CONTENT_W - 40, 9.2, 13.2)


def page_services(d):
    y = d.new_page("05 · The business", "Services")

    d.body("Formula Dynamics offers <b>upgrades and service</b>. Both belong in the "
           "content mix &mdash; service is what turns a one-time customer into a long-term "
           "one, and it differentiates you from shops that only bolt on parts.",
           MARGIN, y, CONTENT_W, 9.6, 14)
    y -= 40

    d.label("CURRENT VIDEO FOCUS", MARGIN, y, 8, B.RED)
    y -= 12
    labels = {s: l for s, l, _ in B.SERVICES}
    x = MARGIN
    for slug in B.PRIORITY_SERVICES:
        txt = labels[slug]
        w = d.text_width(txt.upper(), DISPLAY, 15, 0.06) + 26
        d.c.setStrokeColor(B.RED)
        d.c.setLineWidth(1.4)
        d.c.roundRect(x, y - 26, w, 26, 5, stroke=1, fill=0)
        d.display(txt, x + 13, y - 18, 15)
        x += w + 10
    y -= 46

    rows = [["Service", "On screen", "Descriptor"]]
    for slug, label, desc in B.SERVICES:
        rows.append([f"<b>{label.title()}</b>", label, desc])
    d.table(rows, MARGIN, y, [120, 118, CONTENT_W - 238])


def page_partners(d):
    y = d.new_page("05 · The business", "Select partners")

    rows = [["Partner", "Category", "Lower third"]]
    for slug, label, prose, category in B.PARTNERS:
        rows.append([f"<b>{prose}</b>", category, f"lt_9x16_partner_{slug}.png"])
    y = d.table(rows, MARGIN, y, [120, 200, CONTENT_W - 320])

    y -= 28
    d.label("CASING: PROSE VS. ON-SCREEN", MARGIN, y, 8, B.RED)
    y = d.table([["Write in captions", "Renders on screen as"]] +
                [[f"<b>{p}</b>", l] for _, l, p, _ in B.PARTNERS],
                MARGIN, y - 14, [180, CONTENT_W - 180])

    y -= 20
    d.body("Two of these use deliberate lowercase styling &mdash; respect it <b>in writing</b>. "
           "The on-screen versions are uppercase because every graphic is set in Bebas "
           "Neue, which has no lowercase. That's a property of the typeface, not a "
           "misspelling.", MARGIN, y, CONTENT_W, 9.4, 13.8)

    y -= 56
    d.rect(MARGIN, y - 74, CONTENT_W, 74, PANEL)
    d.rect(MARGIN, y - 74, 4, 74, B.RED)
    d.label("PARTNER LOGOS ARE NOT IN THIS KIT", MARGIN + 20, y - 22, 8, B.RED)
    d.body("Partner logos are their intellectual property, so none are generated here. "
           "Request official vector or 2000&nbsp;px+ transparent files from each partner's "
           "media kit and drop them into <b>03-overlays/partner-logos/</b>. Never "
           "screenshot a logo off a website.",
           MARGIN + 20, y - 32, CONTENT_W - 40, 9.2, 13)

    y -= 100
    d.label("BEFORE CO-LOCKING A PARTNER MARK WITH YOURS", MARGIN, y, 8, INK)
    d.bullets(["Read their brand guidelines &mdash; clear space, minimum size, approved "
               "colour variants.",
               "Some brands prohibit adjacent co-locking entirely. When in doubt, give "
               "the partner logo its own frame.",
               "Tag partner accounts in the post and in the video &mdash; that's what earns "
               "the reshare. Confirm each handle before publishing.",
               "Never imply an endorsement or partnership tier that isn't real."],
              MARGIN, y - 16, CONTENT_W)


SHOTS_A = [
    ("01", "The Reveal", "body kits",
     "The finished car, moving, low angle. Never open on a &ldquo;before&rdquo;.",
     ["Low front 3/4, car rolling in &mdash; camera at bumper height",
      "Slow pan along the new aero",
      "Detail: splitter, diffuser, canards &mdash; macro, shallow depth",
      "Carbon weave close-up, rake light across the weave",
      "Wide static hero frame, hold 3 s",
      "Before shot <b>last</b>, as contrast"]),
    ("02", "Sound Check", "exhaust",
     "The sound, in the first half second. Cut to the loudest frame first.",
     ["Tailpipe, engine off, tight",
      "Cold start with tips in frame &mdash; <b>record clean audio</b>",
      "Rev, exterior &mdash; mic away from the car; phone mics clip",
      "Rev, interior driver POV",
      "Valve open/close comparison",
      "Drive-by, static camera &mdash; the money shot"]),
    ("03", "Fitment", "wheels",
     "The wheel gap closing, or the first wheel going on.",
     ["Old wheel static, brief",
      "Wheel off, hub bare",
      "New wheel lifted into frame &mdash; slow motion, 60 fps",
      "Bolting up, torque wrench &mdash; signals competence",
      "Car dropping off the lift, slow motion",
      "Rolling shot, then static 3/4 hero"]),
    ("04", "Dyno / Tune", "tuning",
     "The number. Put the peak figure on screen in the first 2 s.",
     ["Car strapped to the dyno",
      "Laptop with live graph, over-shoulder",
      "Wheels spinning under load, slow motion",
      "Operator watching &mdash; the human element",
      "Screen with the final figure &mdash; hold, this is the payoff",
      "Owner's reaction if you can get it"]),
]

SHOTS_B = [
    ("05", "Before & After", "any service",
     "The after. Always lead with the after.",
     ["After (2 s) &rarr; hard cut to before (2 s) &rarr; build montage (10 s) "
      "&rarr; after again, held longer (5 s)",
      "<b>Lock the camera to the same position for both states.</b> A tripod mark "
      "on the floor makes the cut land",
      "Same angle, same light, same lens"]),
    ("06", "Install Day", "timelapse",
     "The last 2 s of the timelapse, played first.",
     ["Lock a phone on a tripod for the whole job",
      "Shoot 1 frame/sec, or record long takes and speed to 10&ndash;20&times;",
      "Cut in real-time close-ups so it isn't only timelapse"]),
    ("07", "Service & Maintenance", "the trust builder",
     "Less glamorous, converts well. Shows you're a real shop.",
     ["Car on the lift in a clean bay &mdash; a tidy shop is the message",
      "Fluid change, close and clean",
      "Torque wrench, gloves on",
      "Diagnostic screen; finished car wiped down",
      "Post these between the loud upgrade videos"]),
]


# Left column width before the hook copy starts.
HOOK_COL_X = 178


def _shot_blocks(d, y, blocks):
    for num, name, tag, hook, shots in blocks:
        d.line(MARGIN, y + 8, PAGE_W - MARGIN, y + 8)
        d.display(num, MARGIN, y - 14, 22, B.RED, 0.02)
        d.display_fit(name, MARGIN + 40, y - 14, 19, HOOK_COL_X - 40 - 12)
        d.label(tag, MARGIN + 40, y - 27, 7.2, MUTED)
        d.body(f"<b>Hook:</b> {hook}", MARGIN + HOOK_COL_X, y - 12,
               CONTENT_W - HOOK_COL_X, 8.8, 12.4)
        y = d.bullets(shots, MARGIN + HOOK_COL_X, y - 30,
                      CONTENT_W - HOOK_COL_X, 8.6, 11.6, 2)
        y -= 22
    return y


def page_shots_a(d):
    y = d.new_page("04 · Video system", "Shot formulas")
    d.body("Every formula uses the same skeleton: <b>0&ndash;3 s hook</b> (best frame you "
           "own) &middot; <b>3&ndash;8 s context</b> &middot; <b>8&ndash;20 s payoff</b> &middot; "
           "<b>20&ndash;27 s proof</b> &middot; <b>27&ndash;30 s CTA</b>.",
           MARGIN, y, CONTENT_W, 9.4, 13.8)
    _shot_blocks(d, y - 32, SHOTS_A)


def page_shots_b(d):
    y = d.new_page("04 · Video system", "Shot formulas / 2")
    y = _shot_blocks(d, y, SHOTS_B)

    y -= 10
    d.label("CONTENT MIX, PER 10 POSTS", MARGIN, y, 8, B.RED)
    y = d.table([["Type", "Count"],
                 ["Upgrade reveals (kits, wheels, exhaust)", "4"],
                 ["Sound / dyno / performance payoff", "2"],
                 ["Before &amp; after", "1"],
                 ["Service / maintenance / trust", "2"],
                 ["Shop culture, team, partners", "1"]],
                MARGIN, y - 14, [CONTENT_W - 80, 80])

    y -= 20
    d.label("SHOOTING BASICS", MARGIN, y, 8, B.RED)
    d.bullets(["<b>Film 60 fps.</b> Slow motion later without stuttering.",
               "<b>Golden hour or full shade.</b> Midday sun blows out paint.",
               "<b>Move the camera or move the car.</b> Never both static.",
               "<b>Clean the car first.</b> Every time &mdash; dust reads as neglect at 4K.",
               "Kill reflections: you, your phone, the bay lights.",
               "Wipe the lens between setups. Record audio separately for exhaust."],
              MARGIN, y - 14, CONTENT_W, 8.8, 12.2, 3)


def page_copy(d):
    y = d.new_page("05 · Copy", "Hooks, captions & voice")

    d.label("HOW WE SOUND", MARGIN, y, 8, B.RED)
    y = d.table([["Do", "Don't"],
                 ["&ldquo;Titanium valvetronic. 12 lb lighter.&rdquo;", "&ldquo;INSANE SOUND!!!&rdquo;"],
                 ["&ldquo;Fitted, aligned, torqued to spec.&rdquo;", "&ldquo;Best work in the game&rdquo;"],
                 ["&ldquo;Before: 612. After: 703.&rdquo;", "&ldquo;Massive gains!!&rdquo;"],
                 ["Name the part, the car, the spec", "Vague hype with no substance"]],
                MARGIN, y - 14, [CONTENT_W / 2, CONTENT_W / 2])

    y -= 18
    d.body("<b>Specific beats loud.</b> A part number, a weight saving, a torque figure "
           "&mdash; real numbers are what the owner of a six-figure car responds to. Anyone "
           "can shout. Short sentences, hard stops, matching the edit.",
           MARGIN, y, CONTENT_W, 9.4, 13.8)

    y -= 42
    d.label("HOOK RULES", MARGIN, y, 8, B.RED)
    y = d.bullets([
        "<b>No throat-clearing.</b> Never &ldquo;So today we&hellip;&rdquo; or &ldquo;What's up guys&rdquo;.",
        "<b>Lead with the best frame you own</b> &mdash; not the setup, the payoff.",
        "<b>Numbers stop scrolls.</b> Horsepower, weight saved, price, hours.",
        "<b>Ask something they'd answer.</b> &ldquo;Wheels or aero first?&rdquo; drives comments.",
        "<b>Never bury the sound.</b> On an exhaust video the note <i>is</i> the hook.",
    ], MARGIN, y - 14, CONTENT_W)

    y -= 12
    d.label("SAMPLE HOOKS", MARGIN, y, 8, B.RED)
    y = d.table([["Service", "Hooks"],
                 ["<b>Body kits</b>", "Carbon, from every angle. &middot; This is what [CAR] should have looked like from the factory. &middot; Full aero. Nothing left stock."],
                 ["<b>Exhaust</b>", "Turn the sound on. &middot; Cold start, headphones on. &middot; Valves closed. Valves open. Hear it."],
                 ["<b>Wheels</b>", "Fitment is everything. &middot; Wheel gap: gone. &middot; Forged. Lighter than stock. Stronger too."],
                 ["<b>Tuning</b>", "[FIGURE] whp. Here's the pull. &middot; Before: [FIGURE]. After: [FIGURE]. &middot; Watch the graph."],
                 ["<b>Service</b>", "Not every day is a build day. &middot; The unglamorous part that keeps it running."]],
                MARGIN, y - 14, [92, CONTENT_W - 92])

    y -= 22
    d.label("CTA LINES &mdash; PICK ONE, NEVER STACK TWO", MARGIN, y, 8, B.RED)
    d.body("Book your build &mdash; link in bio. &nbsp;&middot;&nbsp; DM us for a quote on your "
           "[CAR]. &nbsp;&middot;&nbsp; Tell us what you'd fit next. &nbsp;&middot;&nbsp; Now "
           "booking for [MONTH]. &nbsp;&middot;&nbsp; Full spec in the comments.",
           MARGIN, y - 16, CONTENT_W, 9.4, 13.8)

    y -= 62
    d.rect(MARGIN, y - 56, CONTENT_W, 56, "#FFF3F3")
    d.rect(MARGIN, y - 56, 4, 56, B.RED)
    d.body("<b>On claims:</b> only publish figures you actually measured. &ldquo;Up to&rdquo; and "
           "&ldquo;gains vary by fuel and conditions&rdquo; are honest and cost nothing. Getting "
           "caught inflating a dyno number destroys trust with exactly the customer "
           "you want.", MARGIN + 20, y - 16, CONTENT_W - 40, 9.2, 13)


def page_ctas(d):
    y = d.new_page("05 · Copy", "Calls to action")

    d.body("Sixteen on-screen calls to action, each in two styles. Ready-made "
           "graphics are in <b>03-overlays/cta-captions/</b>.",
           MARGIN, y, CONTENT_W, 9.6, 14)
    y -= 34

    d.label("THE TWO STYLES", MARGIN, y, 8, B.RED)
    y = d.table([["Style", "Looks like", "Use when"],
                 ["<b>bar</b>", "Solid red pill, white type",
                  "Default. Dark, neutral or light footage."],
                 ["<b>panel</b>", "Black panel, key word in red, accent stripe under",
                  "<b>The footage is red.</b> Also busy or bright backgrounds."]],
                MARGIN, y - 14, [70, 200, CONTENT_W - 270])

    y -= 16
    d.body("A red bar over a red Ferrari disappears, and a lot of this shop's "
           "content is red cars. When in doubt, use <b>panel</b>.",
           MARGIN, y, CONTENT_W, 9.2, 13.4)

    y -= 30
    rows = [["Group", "Captions"]]
    for key, blurb in B.CTA_GROUPS.items():
        lines = [f"{lead} {accent}" for _, lead, accent, g in B.CTA_CAPTIONS
                 if g == key]
        short = blurb.split(".")[0] + "."
        rows.append([f"<b>{key.title()}</b><br/><font size=7 color='#7A7A84'>"
                     f"{short}</font>",
                     "<br/>".join(f"<b>{l}</b>" for l in lines)])
    y = d.table(rows, MARGIN, y, [268, CONTENT_W - 268])

    y -= 24
    d.label("RULES THAT ACTUALLY MOVE THE NUMBER", MARGIN, y, 8, B.RED)
    d.bullets([
        "<b>One CTA per video. Never two.</b> Two asks is zero asks. If the end "
        "card is on screen, that <i>is</i> the CTA.",
        "<b>Put it on the payoff, not the last frame.</b> Most viewers leave "
        "before the end. Bring it up as the best shot lands and hold 2&ndash;3 s.",
        "<b>Match the ask to the content.</b> A reveal earns BOOK NOW. A "
        "shop-culture clip earns FOLLOW FOR MORE BUILDS.",
        "<b>Alternate reach and conversion.</b> Every third or fourth post, use "
        "an engagement CTA &mdash; comments widen the audience the next sales CTA "
        "lands on.",
        "<b>Make the destination match the words.</b> LINK IN BIO has to reach a "
        "page where booking is the first thing visible.",
    ], MARGIN, y - 14, CONTENT_W, 9.0, 13.0, 4)


def page_folders(d):
    y = d.new_page("Reference", "Where the files live")

    y = d.table([["Folder", "What's in it"],
                 ["<b>01-brand-core/</b>", "The rules: brand spec, tokens, master guide, colour swatches"],
                 ["<b>02-logos/</b>", "Every lockup &mdash; vector SVG plus PNG at three sizes"],
                 ["<b>03-overlays/</b>", "Drop-on-timeline video graphics &mdash; <b>the daily driver</b>"],
                 ["<b>04-templates/</b>", "Safe-zone guides and the campaign posters for reference"],
                 ["<b>05-copy-library/</b>", "Hooks, captions, hashtags, CTAs, voice"],
                 ["<b>06-video-system/</b>", "How to shoot, edit and export; CapCut workflow"],
                 ["<b>07-fonts/</b>", "Bebas Neue plus notes on the accent face"],
                 ["<b>99-toolkit/</b>", "The scripts that generated everything here"]],
                MARGIN, y, [136, CONTENT_W - 136])

    y -= 28
    d.label("FIND IT FAST", MARGIN, y, 8, B.RED)
    y = d.table([["I need to&hellip;", "Go to"],
                 ["Put the logo on a video", "03-overlays/corner-logo-bugs/"],
                 ["Name a service on screen", "03-overlays/lower-thirds/"],
                 ["Open with a title", "03-overlays/title-cards/"],
                 ["Close with contact info", "03-overlays/end-cards/"],
                 ["Use the logo somewhere else", "02-logos/"],
                 ["Check a colour or font", "01-brand-core/BRAND-SPEC.md"],
                 ["Write a caption", "05-copy-library/"],
                 ["Know how to shoot / edit / export", "06-video-system/"]],
                MARGIN, y - 14, [CONTENT_W / 2, CONTENT_W / 2])

    y -= 30
    d.rect(MARGIN, y - 92, CONTENT_W, 92, PANEL)
    d.rect(MARGIN, y - 92, 4, 92, B.RED)
    d.label("KEEPING THE KIT CONSISTENT", MARGIN + 20, y - 22, 8, B.RED)
    d.body("Every asset is generated from code. Change a colour, service, partner or "
           "contact detail in <b>99-toolkit/fd_brand.py</b>, then run "
           "<b>python3 build_all.py</b> &mdash; all 300+ files regenerate together, this "
           "guide included. Nothing gets forgotten and nothing drifts out of spec.",
           MARGIN + 20, y - 32, CONTENT_W - 40, 9.2, 13.2)


def page_back(d):
    if d._open:
        if d._footer:
            d.footer()
        d.c.showPage()
    d.page += 1
    d._open = True
    d._footer = False
    d.rect(0, 0, PAGE_W, PAGE_H, "#0A0A0C")

    d.c.drawImage(logo_png("fd-stacked--white", 1200),
                  PAGE_W / 2 - 80, PAGE_H / 2 - 20, width=160,
                  height=160 * R.logo("fd-stacked--white", width=400).height /
                  R.logo("fd-stacked--white", width=400).width, mask="auto")

    d.stripe(PAGE_W / 2 - 70, PAGE_H / 2 - 56, 140, 5)
    d.display_centred("PRECISION. PERFORMANCE. PASSION.",
                      PAGE_W / 2, PAGE_H / 2 - 88, 14, "#FFFFFF", 0.12)

    d.c.setFillColor("#8A8A94")
    d.c.setFont(BODY, 9.4)
    for i, line in enumerate((B.WEBSITE, B.INSTAGRAM, B.EMAIL)):
        d.c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 130 - i * 15, line)


CONTENTS = [
    (3, "Colour palette", "Every hex, and what each colour is allowed to do"),
    (4, "Typography", "Bebas Neue, the accent face, and substitutes"),
    (5, "Logo lockups", "Four lockups, four variants, which to use when"),
    (6, "Logo rules", "Clear space, minimum size, do and don't"),
    (7, "Canvases &amp; safe zones", "Frame sizes and where the platform UI sits"),
    (8, "The overlay library", "What exists, how it's named, how to use it"),
    (9, "CapCut workflow", "Build order and animation timings"),
    (10, "Troubleshooting", "Common mistakes and the pre-flight checklist"),
    (11, "Export specs", "Settings and colour notes for each platform"),
    (12, "Services", "Exact wording for everything you offer"),
    (13, "Select partners", "Names, casing, and the rules for partner marks"),
    (14, "Shot formulas", "Seven repeatable video formats"),
    (16, "Hooks &amp; voice", "How the brand sounds, and what to write"),
    (17, "Calls to action", "The 16 CTAs, and which one to use when"),
    (18, "Where the files live", "The folder map and a find-it-fast table"),
]

PAGES = [page_contents, page_palette, page_type, page_logos, page_logo_rules,
         page_canvases, page_overlays, page_workflow, page_troubleshoot,
         page_export, page_services, page_partners, page_shots_a, page_shots_b,
         page_copy, page_ctas, page_folders]


def build():
    from reportlab.pdfgen import canvas as rl_canvas

    pdfmetrics.registerFont(TTFont(DISPLAY, str(B.FONT_BEBAS)))

    c = rl_canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("Formula Dynamics Performance - Brand & Video Asset Guide")
    c.setAuthor("Formula Dynamics Performance")
    c.setSubject("Brand specification and video production guide")

    d = Doc(c)
    page_cover(d)
    for fn in PAGES:
        fn(d)
    page_back(d)
    c.save()
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path.relative_to(B.KIT)} "
          f"({path.stat().st_size / 1024:.0f} KB)")
