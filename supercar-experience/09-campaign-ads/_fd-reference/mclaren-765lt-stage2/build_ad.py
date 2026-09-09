#!/usr/bin/env python3
"""
FORMULA DYNAMICS — McLaren 765LT Stage 2, 9:16 campaign ad.

Built on the kit: brand constants from 99-toolkit/fd_brand.py, type and logo
rendering from fd_render.py, and the HUD component set from fd_hud.py — the
same title block / ticker / callout system used on the Ferrari Roma edit.
Ready-made full-frame overlays (CTA caption, end card) are composited straight
from 03-overlays/ rather than redrawn.

    python3 build_ad.py                    # full render -> exports/
    python3 build_ad.py --dry-run          # print the cue sheet, render nothing
    python3 build_ad.py --stills 2.4 6.4   # preview single composited frames
    python3 build_ad.py --safe             # add safe-zone guides to stills

Everything editable lives in the CONFIG block. Nothing brand-level is defined
here — colours, fonts, contact details and CTA copy all come from fd_brand.
"""

import argparse
import os
import shutil
import subprocess
import sys

from PIL import Image

KIT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(KIT, "99-toolkit"))

import fd_brand as B          # noqa: E402
import fd_hud as HUD          # noqa: E402
import fd_render as R         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLATE = os.path.join(HERE, "source", "plate-1080x1920.mp4")
OUT_DIR = os.path.join(HERE, "exports")
FRAME_DIR = os.path.join(HERE, ".frames")
OVERLAYS = os.path.join(KIT, "03-overlays")

CANVAS = "9x16"
W, H = B.CANVASES[CANVAS]
FPS = 30
DURATION = 15.70

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

CAR = "MCLAREN 765LT"
BUILD = "STAGE 2 BUILD"
TICKER = ["FORMULA DYNAMICS", "765LT", "PERFORMANCE"]

HOOK = ["STOCK IS A", "STARTING POINT."]

# ⚠ Placeholders. Stock column is factory 765LT; the tuned column is invented
# for layout. Replace with the real dyno sheet before this runs as paid media.
SPEC_HEADING = "STAGE 2 · BUILD SHEET"
SPECS = [
    # label,     from,  to,    unit,     decimals
    ("POWER", 755, 902, "HP", 0),
    ("TORQUE", 590, 701, "LB-FT", 0),
    ("0-60", 2.7, 2.4, "SEC", 1),
]

# idx, label, (x, y) anchor as frame fractions, side the label runs
# Anchors read off a full-size frame at 9.6s; label zones measured at mean
# brightness 10-26/255, so white type holds without a scrim.
CALLOUTS = [
    ("001", "REAR WING", (0.31, 0.549), "right"),
    ("002", "FORGED WHEELS", (0.79, 0.632), "left"),
]

CTA_OVERLAY = "cta-captions/cta_9x16_booking_book-your-build_bar.png"
END_CARD = "end-cards/endcard_9x16_dark.png"

# Beat timing (seconds). Order follows 06-video-system/AUTO-EDIT.md: the HUD
# clears the frame before the ask, and the end card is a hard cut.
T_TITLE = (0.40, 10.90)
T_TICKER = (0.90, 10.90)
T_HOOK = (1.20, 4.20)
T_SPECS = (4.60, 8.40)
T_CALLOUT = [(8.60, 10.40), (9.40, 10.90)]
T_CTA = (11.30, 12.75)
T_END = 12.90                     # hard cut, runs to the last frame

# Layout, in fractions of the frame. Left margin matches the kit's own
# title block (0.075); the upper band clears the right-hand action rail.
X0 = round(W * 0.075)
X1 = round(W * (1 - B.SAFE_ZONES_9X16["right"]))   # clears the action rail
BAND_TOP = round(H * 0.205)

SHOW_SAFE = False


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return 3 * x * x - 2 * x * x * x


def beat(t, window, fade_in=0.45, fade_out=0.40):
    """(opacity, entrance progress) for a timed element."""
    start, end = window
    if t < start or t > end:
        return 0.0, 0.0
    p = ease_out((t - start) / fade_in) if fade_in else 1.0
    o = p
    if fade_out and t > end - fade_out:
        o *= 1 - ease_in_out((t - (end - fade_out)) / fade_out)
    return o, p


def faded(layer, o):
    """Scale a layer's alpha channel."""
    if o >= 0.999:
        return layer
    out = layer.copy()
    out.putalpha(layer.getchannel("A").point(lambda v: int(v * o)))
    return out


def blank():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def overlay_asset(rel):
    im = Image.open(os.path.join(OVERLAYS, rel)).convert("RGBA")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return im


# ---------------------------------------------------------------------------
# static layers — built once, then faded per frame
# ---------------------------------------------------------------------------

_cache = {}


def layers():
    if _cache:
        return _cache
    # y positions come from the fd_hud defaults, which now clear the
    # 9:16 bottom keep-out band.
    _cache["title"] = HUD.title_block(CANVAS, CAR, BUILD)
    _cache["ticker"] = HUD.ticker(CANVAS, TICKER)
    _cache["callouts"] = [
        HUD.callout(CANVAS, idx, label, anchor, side=side, drop=-0.11, run=0.16)
        for idx, label, anchor, side in CALLOUTS
    ]
    _cache["cta"] = overlay_asset(CTA_OVERLAY)
    _cache["end"] = overlay_asset(END_CARD)
    _cache["hook"] = hook_block()
    return _cache


def hook_block():
    """Two-line Bebas hook, set to the type column width."""
    lines = [R.fit_text(ln, X1 - X0, max_height=round(H * 0.11), tracking=0.02)
             for ln in HOOK]
    return [R.with_shadow(ln, opacity=190) for ln in lines]


# ---------------------------------------------------------------------------
# beats
# ---------------------------------------------------------------------------


def draw_hook(base, t):
    o, _ = beat(t, T_HOOK, fade_in=0.5, fade_out=0.45)
    if o <= 0:
        return
    y = BAND_TOP
    for i, ln in enumerate(layers()["hook"]):
        lp = ease_out((t - T_HOOK[0] - i * 0.16) / 0.7)
        if lp <= 0:
            continue
        R.paste(base, faded(ln, o * lp), X0 - int(ln.width * 0.0) - 40,
                int(y - (1 - lp) * 40))
        y += ln.height - round(H * 0.012)


def draw_specs(base, t):
    o, _ = beat(t, T_SPECS, fade_in=0.5, fade_out=0.45)
    if o <= 0:
        return

    top = BAND_TOP
    head = R.text(SPEC_HEADING, 34, B.RED, tracking=0.16)
    R.paste(base, faded(R.with_shadow(head), o), X0 - 20, top - 20)

    stripe = R.accent_stripe(round((X1 - X0) * ease_out((t - T_SPECS[0]) / 0.8)), 8)
    if stripe.width > 2:
        R.paste(base, faded(stripe, o), X0, top + 56)

    row_h = round(H * 0.075)
    for i, (label, a, b, unit, dec) in enumerate(SPECS):
        rp = ease_out((t - T_SPECS[0] - 0.18 - i * 0.18) / 0.7)
        if rp <= 0:
            continue
        y = top + round(H * 0.055) + i * row_h + (1 - rp) * 24
        ro = o * rp

        lab = R.text(label, 36, B.WHITE, tracking=0.16)
        R.paste(base, faded(R.with_shadow(lab), ro), X0 - 20, y + 34)

        # the counter ramps from the stock figure to the tuned figure
        cp = ease_in_out((t - T_SPECS[0] - 0.35 - i * 0.18) / 1.15)
        val = R.text(f"{a + (b - a) * cp:.{dec}f}", 104, B.WHITE, tracking=0.02)
        unit_im = R.text(unit, 34, B.WHITE, tracking=0.14)
        arrow = R.text(">", 40, B.RED, tracking=0)
        stock = R.text(f"{a:.{dec}f}", 34, B.WHITE, tracking=0.10)

        x = X1
        R.paste(base, faded(R.with_shadow(unit_im), ro * 0.85), x + 20, y + 42, "rt")
        x -= unit_im.width + 18
        R.paste(base, faded(R.with_shadow(val), ro), x + 20, y - 14, "rt")
        x -= val.width + 26
        R.paste(base, faded(R.with_shadow(arrow), ro), x + 20, y + 38, "rt")
        x -= arrow.width + 14
        R.paste(base, faded(R.with_shadow(stock), ro * 0.7), x + 20, y + 42, "rt")

        rule = Image.new("RGBA", (X1 - X0, 2), B.rgb(B.WHITE) + (46,))
        R.paste(base, faded(rule, ro), X0, y + row_h - 22)


def draw_hud(base, t):
    L = layers()
    o, p = beat(t, T_TITLE, fade_in=0.55, fade_out=0.55)
    if o > 0:
        # short slide-in, as the kit's lower third does
        R.paste(base, faded(L["title"], o), int((1 - p) * -30), 0)
    o, _ = beat(t, T_TICKER, fade_in=0.55, fade_out=0.55)
    if o > 0:
        base.alpha_composite(faded(L["ticker"], o))


def draw_callouts(base, t):
    for layer, window in zip(layers()["callouts"], T_CALLOUT):
        o, p = beat(t, window, fade_in=0.35, fade_out=0.35)
        if o <= 0:
            continue
        # the leader line draws itself in with a quick horizontal wipe
        if p < 1:
            m = Image.new("L", (W, H), 0)
            m.paste(255, (0, 0, int(W * (0.25 + 0.75 * p)), H))
            clipped = layer.copy()
            clipped.putalpha(Image.composite(
                layer.getchannel("A"), Image.new("L", (W, H), 0), m))
            layer = clipped
        base.alpha_composite(faded(layer, o))


def draw_cta(base, t):
    o, _ = beat(t, T_CTA, fade_in=0.4, fade_out=0.35)
    if o > 0:
        base.alpha_composite(faded(layers()["cta"], o))


def draw_end(base, t):
    if t >= T_END:
        base.alpha_composite(layers()["end"])       # hard cut, no fade


def draw_safe(base):
    from PIL import ImageDraw
    z = B.SAFE_ZONES_9X16
    d = ImageDraw.Draw(base)
    d.rectangle([W * z["left"], H * z["top"], W * (1 - z["right"]),
                 H * (1 - z["bottom"])], outline=(0, 200, 255, 120), width=3)
    d.line([0, H * (1 - z["bottom"]), W, H * (1 - z["bottom"])],
           fill=(255, 200, 0, 140), width=3)


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------


def render_frame(t):
    im = blank()
    draw_hud(im, t)
    draw_hook(im, t)
    draw_specs(im, t)
    draw_callouts(im, t)
    draw_cta(im, t)
    draw_end(im, t)
    if SHOW_SAFE:
        draw_safe(im)
    return im


def cue_sheet():
    rows = [
        ("Title block", T_TITLE, f"{CAR} / {BUILD}"),
        ("Ticker", T_TICKER, " / ".join(TICKER)),
        ("Hook", T_HOOK, " ".join(HOOK)),
        ("Spec readout", T_SPECS, SPEC_HEADING),
    ]
    for (idx, label, _, _), w in zip(CALLOUTS, T_CALLOUT):
        rows.append((f"Callout {idx}", w, label))
    rows += [("CTA", T_CTA, os.path.basename(CTA_OVERLAY)),
             ("End card", (T_END, DURATION), os.path.basename(END_CARD))]
    print(f"\n{CAR} — {DURATION:.2f}s @ {FPS}fps, {W}x{H}\n")
    print(f"{'ELEMENT':<16}{'IN':>7}{'OUT':>8}{'HOLD':>7}   CONTENT")
    for name, (a, b), content in rows:
        print(f"{name:<16}{a:>7.2f}{b:>8.2f}{b - a:>7.2f}   {content}")
    print()


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


GRADE = "eq=contrast=1.05:saturation=0.95:gamma=1.0,vignette=angle=PI/4.6"


def composite(out_path, crf=20):
    subprocess.run([
        ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", PLATE,
        "-framerate", str(FPS), "-i", os.path.join(FRAME_DIR, "%05d.png"),
        "-filter_complex",
        f"[0:v]fps={FPS},{GRADE}[bg];"
        "[bg][1:v]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]",
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
        "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", out_path,
    ], check=True)


def still(t, out_path):
    tmp = os.path.join(OUT_DIR, ".still_bg.png")
    subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", str(t), "-i", PLATE, "-frames:v", "1",
                    "-vf", GRADE, tmp], check=True)
    bg = Image.open(tmp).convert("RGBA")
    bg.alpha_composite(render_frame(t))
    bg.convert("RGB").save(out_path, quality=90)
    os.remove(tmp)


def main():
    global SHOW_SAFE
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--safe", action="store_true")
    ap.add_argument("--crf", type=int, default=20)
    args = ap.parse_args()
    SHOW_SAFE = args.safe

    if args.dry_run:
        cue_sheet()
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    if args.stills:
        for t in args.stills:
            p = os.path.join(OUT_DIR, "still-{:05.2f}s.jpg".format(t).replace(".", "_", 1))
            still(t, p)
            print(p)
        return

    if not os.path.exists(PLATE):
        sys.exit(f"missing footage plate: {PLATE}")

    cue_sheet()
    if os.path.isdir(FRAME_DIR):
        shutil.rmtree(FRAME_DIR)
    os.makedirs(FRAME_DIR)

    n = int(round(DURATION * FPS))
    print("rendering overlay frames...")
    for i in range(n):
        render_frame(i / FPS).save(os.path.join(FRAME_DIR, f"{i:05d}.png"))
        if i % 60 == 0:
            print(f"  frame {i}/{n}", flush=True)

    out = os.path.join(OUT_DIR, "formula-dynamics-765lt-15s-9x16.mp4")
    print("compositing...")
    composite(out, crf=args.crf)
    still(13.6, os.path.join(OUT_DIR, "poster.jpg"))
    print(out)


if __name__ == "__main__":
    main()
