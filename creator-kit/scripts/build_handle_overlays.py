#!/usr/bin/env python3
"""
Build the personal handle overlay pack - the Twitch-style social bug.

These are yours, not Formula Dynamics' and not Supercar Experience's. A handle
bug wearing a client's brand colours reads as an ad for the client. So the
accent here is #FBD101 - the gold from your own burned-in captions, which is
the one colour that is already unmistakably yours across every post.

    nq.young      Instagram
    youngomarie   YouTube
    youngomarie   TikTok

Position follows the streamer convention: bottom-left, out of the way of the
action, up far enough to clear Instagram's caption row. A top-left set is
included for shots where the interesting thing is in the lower half of the
frame - which, filming a car on a lift, is most of them.

Platform marks are drawn here as simplified glyphs rather than shipped brand
assets. That keeps the pack redistributable and keeps every icon on the same
optical weight, which shipped assets never are.

Usage:
    python3 build_handle_overlays.py --out ../overlays-handles [--verify]
"""

import argparse
import base64
import os
import subprocess
import tempfile

W, H = 1080, 1920

GOLD = "#FBD101"          # his caption accent - the one colour that is his
INK = "#0F1014"
WHITE = "#FDFDFD"         # his caption base, not pure white

SAFE = {"top": 260, "bottom": 470, "left": 72, "right": 190}

HANDLES = [
    ("instagram", "nq.young"),
    ("youtube", "youngomarie"),
    ("tiktok", "youngomarie"),
]


def icon(platform, colour, punch):
    """Simplified platform glyphs. `punch` is the colour showing through a
    solid mark - it has to match whatever sits behind, or the YouTube play
    triangle turns into a filled block."""
    if platform == "instagram":
        return (f'<svg viewBox="0 0 24 24" width="100%" height="100%">'
                f'<rect x="2.2" y="2.2" width="19.6" height="19.6" rx="5.6" fill="none" '
                f'stroke="{colour}" stroke-width="2.1"/>'
                f'<circle cx="12" cy="12" r="4.6" fill="none" stroke="{colour}" stroke-width="2.1"/>'
                f'<circle cx="17.6" cy="6.4" r="1.35" fill="{colour}"/></svg>')
    if platform == "youtube":
        return (f'<svg viewBox="0 0 24 24" width="100%" height="100%">'
                f'<rect x="1.4" y="5" width="21.2" height="14" rx="4.6" fill="{colour}"/>'
                f'<path d="M9.9 9.1 L16.2 12 L9.9 14.9 Z" fill="{punch}"/></svg>')
    return (f'<svg viewBox="0 0 24 24" width="100%" height="100%">'
            f'<path d="M16.4 2.4c.62 2.24 2.2 3.82 4.36 4.08v3.3c-1.66 0-3.16-.52-4.36-1.42v6.44 '
            f'c0 3.62-2.94 6.56-6.56 6.56S3.28 18.42 3.28 14.8s2.94-6.56 6.56-6.56c.38 0 .74.04 '
            f'1.1.1v3.42c-.34-.1-.72-.16-1.1-.16-1.8 0-3.26 1.46-3.26 3.26s1.46 3.26 3.26 3.26 '
            f'3.26-1.46 3.26-3.26V2.4h3.3z" fill="{colour}"/></svg>')


def shell(font_b64, body):
    return f"""<style>
@font-face{{font-family:'SG';src:url(data:font/ttf;base64,{font_b64}) format('truetype');font-weight:100 900;}}
html,body{{margin:0;padding:0;width:{W}px;height:{H}px;background:transparent;overflow:hidden}}
*{{box-sizing:border-box;font-family:'SG',sans-serif;-webkit-font-smoothing:antialiased}}
.wrap{{position:relative;width:{W}px;height:{H}px}}
</style><div class="wrap">{body}</div>"""


def single(platform, handle, position, dark_footage):
    """One platform, one handle. What you leave up for a whole video."""
    fg = WHITE if dark_footage else INK
    panel = "rgba(15,16,20,.62)" if dark_footage else "rgba(253,253,253,.72)"
    punch = "#16171C" if dark_footage else "#F2F2F0"
    y = (f"top:{SAFE['top']}px" if position == "top-left"
         else f"bottom:{SAFE['bottom']}px")
    return f"""<div style="position:absolute;left:{SAFE['left']}px;{y};
     display:flex;align-items:center;gap:20px;background:{panel};
     border-left:7px solid {GOLD};padding:18px 30px 18px 24px;border-radius:4px">
  <div style="width:52px;height:52px;color:{fg};display:flex">{icon(platform, fg, punch)}</div>
  <div style="font-size:46px;font-weight:700;letter-spacing:-.01em;color:{fg};line-height:1">{handle}</div>
</div>"""


def stacked(dark_footage):
    """All three at once. For an end card or the last few seconds, not for a
    whole video - three rows of text is a lot to leave sitting on the frame."""
    fg = WHITE if dark_footage else INK
    panel = "rgba(15,16,20,.68)" if dark_footage else "rgba(253,253,253,.76)"
    punch = "#16171C" if dark_footage else "#F2F2F0"
    rows = "".join(
        f'<div style="display:flex;align-items:center;gap:18px">'
        f'<div style="width:42px;height:42px;color:{fg};display:flex">{icon(p, fg, punch)}</div>'
        f'<div style="font-size:38px;font-weight:600;letter-spacing:-.01em;color:{fg};line-height:1">{h}</div>'
        f'</div>' for p, h in HANDLES)
    return f"""<div style="position:absolute;left:{SAFE['left']}px;bottom:{SAFE['bottom']}px;
     display:flex;flex-direction:column;gap:18px;background:{panel};
     border-left:7px solid {GOLD};padding:24px 34px 24px 26px;border-radius:4px">
  <div style="font-size:20px;font-weight:600;letter-spacing:.22em;color:{GOLD};
       text-transform:uppercase;margin-bottom:2px">Follow</div>
  {rows}
</div>"""


def inline_bar(dark_footage):
    """All three on one line, centred. Reads in about a second, which is what
    you want if it is only up for the last three."""
    fg = WHITE if dark_footage else INK
    panel = "rgba(15,16,20,.68)" if dark_footage else "rgba(253,253,253,.76)"
    punch = "#16171C" if dark_footage else "#F2F2F0"
    cells = ('<div style="width:5px;height:34px;background:%s;opacity:.35"></div>' % fg).join(
        f'<div style="display:flex;align-items:center;gap:14px">'
        f'<div style="width:36px;height:36px;color:{fg};display:flex">{icon(p, fg, punch)}</div>'
        f'<div style="font-size:32px;font-weight:600;color:{fg};line-height:1">{h}</div></div>'
        for p, h in HANDLES)
    return f"""<div style="position:absolute;left:0;right:0;bottom:{SAFE['bottom']}px;
     display:flex;justify-content:center">
  <div style="display:flex;align-items:center;gap:22px;background:{panel};
       border-bottom:6px solid {GOLD};padding:20px 30px;border-radius:4px">{cells}</div>
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


def main():
    ap = argparse.ArgumentParser(description="Build the personal handle overlay pack.")
    ap.add_argument("--out", default="overlays-handles")
    ap.add_argument("--font", default="/home/user/UIUX/creator-kit/fonts/SpaceGrotesk.ttf")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--browser",
                    default="/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")
    args = ap.parse_args()

    if not os.path.isfile(args.font):
        raise SystemExit("font not found: %s" % args.font)
    fb = base64.b64encode(open(args.font, "rb").read()).decode()
    os.makedirs(args.out, exist_ok=True)

    written = []
    for platform, handle in HANDLES:
        for position in ("bottom-left", "top-left"):
            for dark, tag in ((True, "white"), (False, "black")):
                p = os.path.join(args.out, f"handle_9x16_{platform}_{position}_{tag}.png")
                render(args.browser, shell(fb, single(platform, handle, position, dark)), p)
                written.append(p)

    for dark, tag in ((True, "white"), (False, "black")):
        p = os.path.join(args.out, f"handle_9x16_all-stacked_{tag}.png")
        render(args.browser, shell(fb, stacked(dark)), p); written.append(p)
        p = os.path.join(args.out, f"handle_9x16_all-bar_{tag}.png")
        render(args.browser, shell(fb, inline_bar(dark)), p); written.append(p)

    print("wrote %d overlays to %s" % (len(written), args.out))
    if args.verify:
        print("\n%-52s %-16s %s" % ("file", "size", "position"))
        for f in written:
            x0, y0, x1, y1 = alpha_bbox(f)
            print("%-52s %4d x %-4d    x %4d-%-4d  y %4d-%-4d"
                  % (os.path.basename(f), x1 - x0 + 1, y1 - y0 + 1, x0, x1, y0, y1))


if __name__ == "__main__":
    main()
