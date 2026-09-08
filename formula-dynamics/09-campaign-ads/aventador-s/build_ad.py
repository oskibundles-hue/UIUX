#!/usr/bin/env python3
"""
FORMULA DYNAMICS — Aventador S full build, 9:16 campaign ad (Pillow renderer).

Reads the edit from cue.json — the same file the Remotion project in remotion/
reads, so the two renderers produce the same cut and can be compared directly.

Brand constants, type and logo come from 99-toolkit; the HUD title block and
ticker come from fd_hud, as on the Roma and 765LT edits. No callouts: this clip
cuts roughly every second, and a leader line anchored to the car goes invalid
at the next cut.

    python3 build_ad.py                    # full render -> exports/
    python3 build_ad.py --dry-run          # cue sheet, render nothing
    python3 build_ad.py --stills 2.4 6.4   # preview composited frames
    python3 build_ad.py --safe             # add safe-zone guides to stills
"""

import argparse
import json
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
CUE = json.load(open(os.path.join(HERE, "cue.json")))
PLATE = os.path.join(HERE, "source", "plate-1080x1920.mp4")
OUT_DIR = os.path.join(HERE, "exports")
FRAME_DIR = os.path.join(HERE, ".frames")
OVERLAYS = os.path.join(KIT, "03-overlays")

CANVAS = CUE["canvas"]
W, H = CUE["width"], CUE["height"]
FPS = CUE["fps"]
DURATION = CUE["duration"]

L = CUE["layout"]
X0 = round(W * L["marginLeftFrac"])
X1 = round(W * (1 - L["marginRightFrac"]))
BAND_TOP = round(H * L["bandTopFrac"])

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


def beat(t, name, fade_in=0.45, fade_out=0.40):
    """(opacity, entrance progress) for a named beat from cue.json."""
    start, end = CUE["beats"][name]
    if t < start or t > end:
        return 0.0, 0.0
    p = ease_out((t - start) / fade_in) if fade_in else 1.0
    o = p
    if fade_out and t > end - fade_out:
        o *= 1 - ease_in_out((t - (end - fade_out)) / fade_out)
    return o, p


def faded(layer, o):
    if o >= 0.999:
        return layer
    out = layer.copy()
    out.putalpha(layer.getchannel("A").point(lambda v: int(v * o)))
    return out


def overlay_asset(rel):
    im = Image.open(os.path.join(OVERLAYS, rel)).convert("RGBA")
    return im if im.size == (W, H) else im.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------------------
# static layers — built once, faded per frame
# ---------------------------------------------------------------------------

_cache = {}


def layers():
    if _cache.get("_built"):
        return _cache
    _cache["title"] = HUD.title_block(CANVAS, CUE["car"], CUE["build"])
    _cache["ticker"] = HUD.ticker(CANVAS, CUE["ticker"])
    _cache["cta"] = overlay_asset(CUE["ctaOverlay"])
    _cache["end"] = overlay_asset(CUE["endCard"])
    _cache["hook"] = [
        R.with_shadow(R.fit_text(ln, X1 - X0, max_height=round(H * 0.10), tracking=0.02),
                      opacity=190)
        for ln in CUE["hook"]
    ]
    _cache["_built"] = True
    return _cache


# ---------------------------------------------------------------------------
# beats
# ---------------------------------------------------------------------------


def draw_mid_scrim(base, t):
    """Soft band behind the mid-band type.

    The clip cuts roughly every second and runs a tachometer close-up at ~6.2s;
    no ink colour survives blown sky, black bodywork and a lit gauge face, so
    the mid band gets a band under it. Same reasoning as --title-scrim on the
    GT3 RS in 06-video-system/AUTO-EDIT.md.
    """
    o = max(beat(t, "hook", 0.45, 0.40)[0], beat(t, "build", 0.45, 0.40)[0])
    if o <= 0:
        return
    if "midscrim" not in _cache:
        _cache["midscrim"] = HUD._scrim(CANVAS, 0.355, 0.31, 205, 0.05)
    base.alpha_composite(faded(_cache["midscrim"], o))


def draw_hud(base, t):
    Lc = layers()
    o, p = beat(t, "title", fade_in=0.55, fade_out=0.55)
    if o > 0:
        R.paste(base, faded(Lc["title"], o), int((1 - p) * -30), 0)
    o, _ = beat(t, "ticker", fade_in=0.55, fade_out=0.55)
    if o > 0:
        base.alpha_composite(faded(Lc["ticker"], o))


def draw_hook(base, t):
    o, _ = beat(t, "hook", fade_in=0.45, fade_out=0.40)
    if o <= 0:
        return
    start = CUE["beats"]["hook"][0]
    y = BAND_TOP
    for i, ln in enumerate(layers()["hook"]):
        lp = ease_out((t - start - i * 0.14) / 0.6)
        if lp <= 0:
            continue
        R.paste(base, faded(ln, o * lp), X0 - 40, int(y - (1 - lp) * 36))
        y += ln.height - round(H * 0.012)


def draw_build(base, t):
    """The build sheet — four numbered rows, one per confirmed item."""
    o, _ = beat(t, "build", fade_in=0.45, fade_out=0.40)
    if o <= 0:
        return
    start = CUE["beats"]["build"][0]
    top = BAND_TOP

    head = R.text(CUE["buildHeading"], 34, B.RED, tracking=0.16)
    R.paste(base, faded(R.with_shadow(head), o), X0 - 20, top - 20)

    stripe = R.accent_stripe(round((X1 - X0) * ease_out((t - start) / 0.7)), 8)
    if stripe.width > 2:
        R.paste(base, faded(stripe, o), X0, top + 54)

    row_h = round(H * 0.052)
    for i, (idx, label, sub) in enumerate(CUE["buildRows"]):
        rp = ease_out((t - start - 0.16 - i * 0.15) / 0.6)
        if rp <= 0:
            continue
        y = top + round(H * 0.048) + i * row_h + (1 - rp) * 20
        ro = o * rp

        num = R.text(idx, 28, B.RED, tracking=0.14)
        R.paste(base, faded(R.with_shadow(num), ro), X0 - 20, y + 16)

        name = R.text(label, 62, B.WHITE, tracking=0.03)
        R.paste(base, faded(R.with_shadow(name), ro), X0 + 66 - 22, y - 12)

        det = R.text(sub, 27, B.WHITE, tracking=0.12)
        R.paste(base, faded(R.with_shadow(det), ro * 0.72), X1 + 20, y + 18, "rt")

        rule = Image.new("RGBA", (X1 - X0, 2), B.rgb(B.WHITE) + (58,))
        R.paste(base, faded(rule, ro), X0, y + row_h - 14)


def draw_cta(base, t):
    o, _ = beat(t, "cta", fade_in=0.40, fade_out=0.35)
    if o > 0:
        base.alpha_composite(faded(layers()["cta"], o))


def draw_end(base, t):
    if t >= CUE["beats"]["end"][0]:
        base.alpha_composite(layers()["end"])      # hard cut


def draw_safe(base):
    from PIL import ImageDraw
    z = B.SAFE_ZONES_9X16
    d = ImageDraw.Draw(base)
    d.rectangle([W * z["left"], H * z["top"], W * (1 - z["right"]),
                 H * (1 - z["bottom"])], outline=(0, 200, 255, 120), width=3)
    d.rectangle([0, H * 0.40, W, H * 0.60], outline=(0, 255, 120, 110), width=3)


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------


def render_frame(t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mid_scrim(im, t)
    draw_hud(im, t)
    draw_hook(im, t)
    draw_build(im, t)
    draw_cta(im, t)
    draw_end(im, t)
    if SHOW_SAFE:
        draw_safe(im)
    return im


def cue_sheet():
    rows = [("Title block", "title", f'{CUE["car"]} / {CUE["build"]}'),
            ("Ticker", "ticker", " / ".join(CUE["ticker"])),
            ("Hook", "hook", " ".join(CUE["hook"])),
            ("Build sheet", "build", " · ".join(r[1] for r in CUE["buildRows"])),
            ("CTA", "cta", os.path.basename(CUE["ctaOverlay"])),
            ("End card", "end", os.path.basename(CUE["endCard"]))]
    print(f'\n{CUE["car"]} — {DURATION:.2f}s @ {FPS}fps, {W}x{H}\n')
    print(f"{'ELEMENT':<14}{'IN':>7}{'OUT':>8}{'HOLD':>7}   CONTENT")
    for name, key, content in rows:
        a, b = CUE["beats"][key]
        print(f"{name:<14}{a:>7.2f}{b:>8.2f}{b - a:>7.2f}   {content}")
    print()


def ffmpeg_bin():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def composite(out_path, crf=20):
    subprocess.run([
        ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", PLATE,
        "-framerate", str(FPS), "-i", os.path.join(FRAME_DIR, "%05d.png"),
        "-filter_complex",
        f'[0:v]fps={FPS},{CUE["grade"]}[bg];'
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
                    "-vf", CUE["grade"], tmp], check=True)
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

    out = os.path.join(OUT_DIR, "formula-dynamics-aventador-14s-9x16.mp4")
    print("compositing...")
    composite(out, crf=args.crf)
    still(12.6, os.path.join(OUT_DIR, "poster.jpg"))
    print(out)


if __name__ == "__main__":
    main()
