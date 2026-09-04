#!/usr/bin/env python3
"""
Build the Supercar Experience overlay pack.

Renders 1080x1920 transparent PNGs via headless Chromium, matching the
geometry of the Formula Dynamics pack so the two are drop-in interchangeable
on a timeline.

Design tokens are lifted from supercarexp.vip's own CSS, not invented:

    --color-primary     #FF4F16   the accent
    --color-background  #0F1014   panel ground
    gold                #BD9457   used ONLY as a 25-30% opacity hairline on
                                  their site, never as a fill - that restraint
                                  is the luxury cue, so it is kept here
    --font-grotesk      a grotesk; Space Grotesk stands in for the licensed face

The bracketed label - [ THE PICKUP ] - is their own device, taken from the
site's section headers.

GEOMETRY IS MEASURED, NOT GUESSED. The first build of this pack looked right in
isolation and wrong next to the Formula Dynamics overlays: every element came
out 30-50% small, so intercutting the two brands read as sloppy. The alpha
bounding boxes of the FD pack are the reference:

    element        FD bounding box              first SE build      now
    bug            315 x 101  @ y 257           187 x  51           ~330 x ~100
    lower third    467 x 211  @ y 1276-1486     368 x 254 -> 1525   ~210, ends 1486
    cta bar        369 x 114  @ y 1364-1477     322 x 108           unchanged, matched
    cta panel      368 x 123  hugs its text     818 x 204 full-bleed hugs its text
    title          454 x 430  @ y 632-1061      725 x 215           two lines, ~420

Run with --verify to print the bounding boxes back and check them yourself.

Usage:
    python3 build_se_overlays.py --out ../overlays-se [--font /path/SpaceGrotesk.ttf]
"""

import argparse
import base64
import os
import subprocess
import tempfile

W, H = 1080, 1920

PRIMARY = "#FF4F16"
GROUND = "#0F1014"
GOLD_30 = "rgba(189,148,87,0.30)"
WHITE = "#FFFFFF"
INK = "#0F1014"

# Instagram covers these edges. Measured, not guessed.
SAFE = {"top": 260, "bottom": 470, "left": 72, "right": 190}

# Anchors taken from the Formula Dynamics pack so the two sets sit in the same
# places on the frame. LOWER_BASELINE is where FD's lower thirds and panels end;
# elements are anchored to that bottom edge rather than to a top offset, because
# the bottom is what has to clear Instagram's caption row.
GEO = {
    "bug_y": 256,
    "lower_baseline": 1486,
    "cta_bar_y": 1360,
    "title_y": 632,
}


def shell(font_b64, body, extra_css=""):
    return f"""<style>
@font-face{{font-family:'SG';src:url(data:font/ttf;base64,{font_b64}) format('truetype');font-weight:100 900;}}
html,body{{margin:0;padding:0;width:{W}px;height:{H}px;background:transparent;overflow:hidden}}
*{{box-sizing:border-box;font-family:'SG',sans-serif;-webkit-font-smoothing:antialiased}}
.wrap{{position:relative;width:{W}px;height:{H}px}}
.label{{color:{PRIMARY};letter-spacing:.22em;font-weight:600;text-transform:uppercase}}
.panel{{background:{GROUND};border:2px solid {GOLD_30}}}
{extra_css}
</style><div class="wrap">{body}</div>"""


def bug(font_b64, position, dark_footage):
    """Small permanent wordmark. Survives a repost or screen-record.

    Sized to the FD bug (315 x 101) so a video that cuts between the two brands
    does not appear to change zoom level.
    """
    fg = WHITE if dark_footage else INK
    sub = "rgba(255,255,255,.62)" if dark_footage else "rgba(15,16,20,.60)"
    y = GEO["bug_y"]
    pos = {
        "top-left": f"left:{SAFE['left']}px;top:{y}px;text-align:left",
        "top-right": f"right:{SAFE['right']}px;top:{y}px;text-align:right",
        "top-center": f"left:0;right:0;top:{y}px;text-align:center",
        "bottom-left": f"left:{SAFE['left']}px;bottom:{SAFE['bottom']}px;text-align:left",
    }[position]
    align = "flex-end" if position == "top-right" else (
        "center" if position == "top-center" else "flex-start")
    return f"""<div style="position:absolute;{pos};display:flex;flex-direction:column;align-items:{align}">
  <div style="display:flex;align-items:center;gap:22px">
    <div style="width:10px;height:88px;background:{PRIMARY};border-radius:5px"></div>
    <div>
      <div style="font-size:62px;font-weight:700;letter-spacing:-.015em;color:{fg};line-height:1.02">SUPERCAR</div>
      <div style="font-size:31px;font-weight:500;letter-spacing:.28em;color:{sub};line-height:1.25">EXPERIENCE</div>
    </div>
  </div>
</div>"""


def lower_third(font_b64, label, title, sub):
    """Anchored to the bottom edge, not the top, so every variant ends where the
    FD lower thirds end (y=1486) no matter how tall its text runs."""
    return f"""<div style="position:absolute;left:{SAFE['left']}px;bottom:{H - GEO['lower_baseline']}px">
  <div class="panel" style="display:inline-block;padding:18px 38px 20px;max-width:760px">
    <div class="label" style="font-size:21px">[ {label} ]</div>
    <div style="font-size:78px;font-weight:700;letter-spacing:-.025em;color:{WHITE};line-height:.94;margin-top:6px">{title}</div>
    <div style="font-size:25px;font-weight:500;letter-spacing:.06em;color:rgba(255,255,255,.72);margin-top:8px">{sub}</div>
    <div style="display:flex;gap:0;margin-top:16px;height:7px">
      <div style="flex:0 0 120px;background:{PRIMARY}"></div>
      <div style="flex:0 0 60px;background:rgba(189,148,87,.55)"></div>
      <div style="flex:1;background:rgba(255,255,255,.14)"></div>
    </div>
  </div>
</div>"""


def cta(font_b64, text, style):
    if style == "bar":
        # Already matched the FD bar (369 x 114). Left alone.
        y = GEO["cta_bar_y"]
        return f"""<div style="position:absolute;left:0;right:0;top:{y}px;display:flex;justify-content:center">
  <div style="background:{PRIMARY};padding:26px 46px;display:flex;align-items:center;gap:18px">
    <div style="font-size:44px;font-weight:700;letter-spacing:.01em;color:{WHITE};white-space:nowrap">{text}</div>
  </div>
</div>"""
    # The FD panel hugs its text rather than spanning the frame; a full-bleed
    # panel behind two short words reads as an empty box. Same bottom edge as
    # the lower thirds so a CTA can replace one mid-clip without shifting.
    return f"""<div style="position:absolute;left:0;right:0;bottom:{H - GEO['lower_baseline']}px;
     display:flex;justify-content:center">
  <div class="panel" style="display:inline-block;padding:18px 34px 20px;max-width:{W - SAFE['left'] - SAFE['right']}px">
    <div class="label" style="font-size:20px">[ SUPERCAR EXPERIENCE ]</div>
    <div style="font-size:58px;font-weight:700;letter-spacing:-.02em;color:{WHITE};line-height:1.02;margin-top:8px;white-space:nowrap">{text}</div>
    <div style="height:6px;background:{PRIMARY};width:140px;margin-top:14px"></div>
  </div>
</div>"""


def title_card(font_b64, label, line1, line2, dark_footage=True):
    """Stacked over two lines like the FD title cards, which is what gives them
    their weight. One long line at this size reads as a caption, not a title.

    Two variants, same as the FD pack: `dark` is white type for dark footage,
    `light` is ink type for a bright frame. A single white title card washes out
    over a sunlit driveway, which is exactly the shot a pickup video opens on.
    """
    y = GEO["title_y"]
    fg = WHITE if dark_footage else INK
    shadow = ("0 8px 40px rgba(0,0,0,.70)" if dark_footage
              else "0 8px 40px rgba(255,255,255,.65)")
    label_col = PRIMARY if dark_footage else "#C43A08"
    return f"""<div style="position:absolute;left:0;right:0;top:{y}px;text-align:center">
  <div class="label" style="font-size:26px;color:{label_col}">[ {label} ]</div>
  <div style="font-size:168px;font-weight:700;letter-spacing:-.035em;color:{fg};line-height:.94;margin-top:16px;
       text-shadow:{shadow}">{line1}<br>{line2}</div>
  <div style="display:flex;justify-content:center;gap:10px;margin-top:32px">
    <div style="width:150px;height:8px;background:{label_col}"></div>
    <div style="width:56px;height:8px;background:rgba(189,148,87,.6)"></div>
  </div>
</div>"""


def end_card(font_b64, dark_footage=True):
    """Full-frame scrim, not an opaque card - the footage stays faintly visible
    behind it, which keeps the last second of the Reel moving. A still card is
    where watch time goes to die, and watch time is the ranking signal."""
    if dark_footage:
        ground, fg = "rgba(15,16,20,.90)", WHITE
        sub, faint, tiny = ".80", ".50", ".38"
        label_col = PRIMARY
    else:
        ground, fg = "rgba(250,250,250,.92)", INK
        sub, faint, tiny = ".78", ".48", ".36"
        label_col = "#C43A08"
    rgb = "255,255,255" if dark_footage else "15,16,20"
    return f"""<div style="position:absolute;inset:0;background:{ground};display:flex;
     flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 90px">
  <div class="label" style="font-size:28px;color:{label_col}">[ SUPERCAR EXPERIENCE ]</div>
  <div style="font-size:118px;font-weight:700;letter-spacing:-.03em;color:{fg};line-height:1;margin-top:24px">BOOK YOUR<br>SUPERCAR</div>
  <div style="display:flex;gap:10px;margin-top:38px">
    <div style="width:170px;height:8px;background:{label_col}"></div>
    <div style="width:60px;height:8px;background:rgba(189,148,87,.6)"></div>
  </div>
  <div style="font-size:36px;font-weight:500;letter-spacing:.14em;color:rgba({rgb},{sub});margin-top:48px">
    LAS VEGAS &nbsp;&middot;&nbsp; SCOTTSDALE &nbsp;&middot;&nbsp; BOISE</div>
  <div style="font-size:28px;font-weight:500;letter-spacing:.10em;color:rgba({rgb},{faint});margin-top:28px">
    supercarexp.vip</div>
  <div style="font-size:22px;font-weight:500;letter-spacing:.10em;color:rgba({rgb},{tiny});margin-top:18px">
    RENTER MUST BE 21 AND OLDER</div>
</div>"""


def render(shell_bin, html, out_path):
    with tempfile.TemporaryDirectory() as td:
        page = os.path.join(td, "p.html")
        open(page, "w").write(html)
        r = subprocess.run([
            shell_bin, "--headless", "--disable-gpu", "--no-sandbox",
            "--hide-scrollbars", "--default-background-color=00000000",
            f"--screenshot={out_path}", f"--window-size={W},{H}",
            "file://" + page,
        ], capture_output=True, text=True)
        if not os.path.exists(out_path):
            raise SystemExit("render failed for %s\n%s" % (out_path, r.stderr[-800:]))


def alpha_bbox(path):
    """Bounding box of everything that is not transparent. Used by --verify so
    the pack's real geometry can be checked against the FD numbers rather than
    eyeballed."""
    with tempfile.TemporaryDirectory() as td:
        g = os.path.join(td, "a.pgm")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path,
                        "-vf", "alphaextract", "-pix_fmt", "gray", g], check=True)
        d = open(g, "rb").read()
        i, tok = 0, []
        while len(tok) < 4:
            j = d.index(b"\n", i); tok += d[i:j].split(); i = j + 1
        w, h = int(tok[1]), int(tok[2]); px = d[i:]
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        row = px[y * w:(y + 1) * w]
        if max(row) <= 8:
            continue
        if y < y0:
            y0 = y
        y1 = y
        for x in range(w):
            if row[x] > 8:
                x0 = min(x0, x); break
        for x in range(w - 1, -1, -1):
            if row[x] > 8:
                x1 = max(x1, x); break
    return x0, y0, x1, y1


LOWER_THIRDS = [
    ("THE PICKUP", "LAS VEGAS", "EXOTIC RENTALS · 4 HOURS OR FULL DAY"),
    ("THE PICKUP", "SCOTTSDALE", "EXOTIC RENTALS · 4 HOURS OR FULL DAY"),
    ("THE PICKUP", "BOISE", "EXOTIC RENTALS · 4 HOURS OR FULL DAY"),
    ("THE FLEET", "FERRARI", "AVAILABLE NOW"),
    ("THE FLEET", "LAMBORGHINI", "AVAILABLE NOW"),
    ("THE FLEET", "McLAREN", "AVAILABLE NOW"),
]

CTAS = [("BOOK NOW", "book-now"), ("BOOK YOUR SUPERCAR", "book-your-supercar"),
        ("DM TO BOOK", "dm-to-book"), ("LINK IN BIO", "link-in-bio"),
        ("MUST BE 21+", "must-be-21")]

TITLES = [("SUPERCAR EXPERIENCE", "THE", "PICKUP", "the-pickup"),
          ("SUPERCAR EXPERIENCE", "THE", "DROPOFF", "the-dropoff"),
          ("SUPERCAR EXPERIENCE", "DELIVERY", "DAY", "delivery-day"),
          ("SUPERCAR EXPERIENCE", "THE", "FLEET", "the-fleet")]


def main():
    ap = argparse.ArgumentParser(description="Build the Supercar Experience overlay pack.")
    ap.add_argument("--out", default="overlays-se")
    ap.add_argument("--font", default="/tmp/SpaceGrotesk.ttf")
    ap.add_argument("--verify", action="store_true",
                    help="print each overlay's alpha bounding box after building")
    ap.add_argument("--browser",
                    default="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")
    args = ap.parse_args()

    if not os.path.isfile(args.font):
        raise SystemExit("font not found: %s" % args.font)
    fb = base64.b64encode(open(args.font, "rb").read()).decode()

    written = []
    for sub in ("corner-logo-bugs", "lower-thirds", "cta-captions", "title-cards", "end-cards"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)

    for pos in ("top-left", "top-right", "top-center", "bottom-left"):
        for dark, tag in ((True, "white"), (False, "black")):
            p = os.path.join(args.out, "corner-logo-bugs", f"se-bug_9x16_{pos}_{tag}.png")
            render(args.browser, shell(fb, bug(fb, pos, dark)), p); written.append(p)

    for label, title, sub in LOWER_THIRDS:
        slug = f"{label.split()[-1].lower()}_{title.lower().replace(' ', '-')}"
        p = os.path.join(args.out, "lower-thirds", f"se-lt_9x16_{slug}.png")
        render(args.browser, shell(fb, lower_third(fb, label, title, sub)), p); written.append(p)

    for text, slug in CTAS:
        for style in ("bar", "panel"):
            p = os.path.join(args.out, "cta-captions", f"se-cta_9x16_{slug}_{style}.png")
            render(args.browser, shell(fb, cta(fb, text, style)), p); written.append(p)

    for label, l1, l2, slug in TITLES:
        for dark, tag in ((True, "dark"), (False, "light")):
            p = os.path.join(args.out, "title-cards", f"se-title_9x16_{slug}_{tag}.png")
            render(args.browser, shell(fb, title_card(fb, label, l1, l2, dark)), p)
            written.append(p)

    for dark, tag in ((True, "dark"), (False, "light")):
        p = os.path.join(args.out, "end-cards", f"se-endcard_9x16_{tag}.png")
        render(args.browser, shell(fb, end_card(fb, dark)), p); written.append(p)

    print("wrote %d overlays to %s" % (len(written), args.out))

    if args.verify:
        print("\n%-52s %-18s %s" % ("file", "size", "position"))
        for f in written:
            x0, y0, x1, y1 = alpha_bbox(f)
            print("%-52s %4d x %-4d      x %4d-%-4d  y %4d-%-4d"
                  % (os.path.relpath(f, args.out), x1 - x0 + 1, y1 - y0 + 1, x0, x1, y0, y1))


if __name__ == "__main__":
    main()
