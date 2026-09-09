#!/usr/bin/env python3
"""
FORMULA DYNAMICS — Aventador S full build, 9:16 campaign ad (Pillow renderer).

Reads the edit from cue.json — the same file the Remotion project in remotion/
reads, so the two renderers produce the same cut and can be compared directly.

Brand constants, type and logo come from 99-toolkit; the HUD title block and
ticker come from fd_hud, as on the Roma and 765LT edits. No callouts: this clip
cuts roughly every second, and a leader line anchored to the car goes invalid
at the next cut.

    python3 build_ad.py                       # base cut -> exports/
    python3 build_ad.py --cue variants/...    # a variant
    python3 build_ad.py --all                 # base + every variant
    python3 build_ad.py --dry-run             # cue sheet, render nothing
    python3 build_ad.py --stills 2.4 6.4      # preview composited frames
    python3 build_ad.py --safe                # add safe-zone guides to stills

Variants live in variants/. Each is a full cue file that changes only the hook
and the CTA, so a test isolates the message rather than the edit.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

from PIL import Image

KIT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # shared renderer sits one level below the kit
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "99-toolkit"))

import sce_brand as B          # noqa: E402
import fd_hud as HUD          # noqa: E402
import fd_render as R         # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layouts import LAYOUTS    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CUE_PATH = os.path.join(HERE, "cue.json")

# Shared renderer: the car folder comes from argv, and it must be known before
# anything below reads cue.json. main() re-parses the same flags properly.
_argv = sys.argv
if "--car" in _argv:
    HERE = os.path.abspath(_argv[_argv.index("--car") + 1])
    CUE_PATH = os.path.join(HERE, "cue.json")
elif "--cue" in _argv:
    CUE_PATH = os.path.abspath(_argv[_argv.index("--cue") + 1])
    _d = os.path.dirname(CUE_PATH)
    HERE = os.path.dirname(_d) if os.path.basename(_d) in ("variants", "cuts", "layouts") else _d
CUE = json.load(open(CUE_PATH))
PLATE = os.path.join(HERE, CUE.get("plate", "source/plate-1080x1920.mp4"))
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


def load_cue(path):
    """Swap in a different cue file and reset the layer cache."""
    global CUE, CUE_PATH, PLATE, W, H, FPS, DURATION, X0, X1, BAND_TOP
    CUE_PATH = path
    CUE = json.load(open(path))
    PLATE = os.path.join(HERE, CUE.get("plate", "source/plate-1080x1920.mp4"))
    W, H = CUE["width"], CUE["height"]
    FPS, DURATION = CUE["fps"], CUE["duration"]
    lay = CUE["layout"]
    X0 = round(W * lay["marginLeftFrac"])
    X1 = round(W * (1 - lay["marginRightFrac"]))
    BAND_TOP = round(H * lay["bandTopFrac"])
    _cache.clear()


class Ctx:
    """What a layout needs: the cue, the geometry, the timing helpers.

    Everything resolves against module globals at call time, so a layout keeps
    working after load_cue() swaps the cue and re-derives the geometry.
    """

    CANVAS = property(lambda self: CUE["canvas"])
    CUE = property(lambda self: CUE)
    W = property(lambda self: W)
    H = property(lambda self: H)
    X0 = property(lambda self: X0)
    X1 = property(lambda self: X1)
    BAND_TOP = property(lambda self: BAND_TOP)
    cache = property(lambda self: _cache)

    def beat(self, t, name, fade_in=0.45, fade_out=0.40):
        return beat(t, name, fade_in, fade_out)

    def faded(self, layer, o):
        return faded(layer, o)

    def ease_out(self, x):
        return ease_out(x)

    def ease_in_out(self, x):
        return ease_in_out(x)


CTX = Ctx()


def layout():
    name = CUE.get("layoutStyle", "hud")
    if name not in LAYOUTS:
        sys.exit(f'unknown layoutStyle "{name}" — have {", ".join(LAYOUTS)}')
    return LAYOUTS[name]


def out_name():
    """supercar-experience-<slug>-<T>s-9x16[-<variant>].mp4"""
    slug = CUE.get("slug") or os.path.basename(HERE)
    t = f"{DURATION:.0f}s"
    if CUE.get("layoutStyle", "hud") != "hud":
        return f'supercar-experience-{slug}-{t}-9x16-layout-{CUE["layoutStyle"]}.mp4'
    if CUE.get("cut"):
        return f'supercar-experience-{slug}-{CUE["cut"]}-9x16.mp4'
    v = CUE.get("variant", "")
    suffix = "" if not v or v.startswith("a-") else f"-{v}"
    return f"supercar-experience-{slug}-{t}-9x16{suffix}.mp4"


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
    if start > DURATION:            # parked beat — this cut does not use it
        return 0.0, 0.0
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
    lay = layout()
    lay["backdrop"](CTX, im, t)
    lay["identity"](CTX, im, t)
    lay["hook"](CTX, im, t)
    lay["build"](CTX, im, t)
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
    label = CUE.get("cut") or CUE.get("variant", "base")
    lname = CUE.get("layoutStyle", "hud")
    print(f'\n{CUE["car"]} — {DURATION:.2f}s @ {FPS}fps, {W}x{H}   '
          f'[{label} · layout: {lname}]')
    if CUE.get("shotOrder"):
        print(f'  shots {CUE["shotOrder"]} — re-cut plate {CUE["plate"]}')
    if CUE.get("variantAngle"):
        print(f'  {CUE["variantAngle"]}')
    print()
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
    ap.add_argument("--car", help="car folder holding cue.json, variants/ and source/plate-1080x1920.mp4")
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--safe", action="store_true")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--cue", help="cue file to render (default cue.json)")
    ap.add_argument("--all", action="store_true",
                    help="render the base cut and every file in variants/")
    args = ap.parse_args()
    if args.car:
        global HERE, CUE_PATH, PLATE
        HERE = os.path.abspath(args.car)
        CUE_PATH = os.path.join(HERE, "cue.json")
        load_cue(CUE_PATH)
    SHOW_SAFE = args.safe
    if args.cue:
        load_cue(os.path.abspath(args.cue))

    if args.all:
        import glob
        cues = ([os.path.join(HERE, "cue.json")]
                + sorted(glob.glob(os.path.join(HERE, "variants", "*.json")))
                + sorted(glob.glob(os.path.join(HERE, "cuts", "*.json")))
                + sorted(glob.glob(os.path.join(HERE, "layouts", "*.json"))))
        for c in cues:
            load_cue(c)
            if args.dry_run:
                cue_sheet()
            else:
                render_one(args.crf)
        return

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

    render_one(args.crf)


def render_one(crf):
    if not os.path.exists(PLATE):
        sys.exit(f"missing footage plate: {PLATE}")
    os.makedirs(OUT_DIR, exist_ok=True)

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

    out = os.path.join(OUT_DIR, out_name())
    print("compositing...")
    composite(out, crf=crf)
    if not CUE.get("variant", "").startswith(("b-", "c-", "d-")):
        still(12.6, os.path.join(OUT_DIR, "poster.jpg"))
    print(out)


if __name__ == "__main__":
    main()
