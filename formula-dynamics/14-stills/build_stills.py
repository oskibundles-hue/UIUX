#!/usr/bin/env python3
"""Static service posters, built from frames of the approved ads.

The layout is the detail grid that was rejected as a video: hero picture over a
strip of three detail panes, a vertical section tab, a header bar, and a caption
on its own plate.

It failed as film because the strip cut the hero in half for the whole runtime
and the eye had nowhere to rest. As a **still** that is exactly what you want —
a poster is read in one look, so showing the hero and three details at once is a
feature rather than a fight. Same components, right medium.

Frames come from the approved cuts, so a poster and its ad are unmistakably the
same campaign.

    python3 build_stills.py                 # all four
    python3 build_stills.py annual          # one
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "99-toolkit"))

from PIL import Image, ImageDraw            # noqa: E402
import fd_brand as B                        # noqa: E402
import fd_render as R                       # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "posters"
TMP = HERE / ".tmp"
W, H = B.CANVASES["9x16"]
SAFE = B.SAFE_ZONES_9X16


def ff():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def grab(src, t, out):
    """One frame, cropped to 9:16 at full canvas size."""
    subprocess.run(
        [ff(), "-nostdin", "-y", "-ss", str(t), "-i", str(src), "-frames:v", "1",
         "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
         str(out), "-loglevel", "error"], check=True)
    return Image.open(out).convert("RGB")


# ----------------------------------------------------------------- components

def vertical_tab(label):
    word = R.text(label, 58, B.WHITE, tracking=0.24)
    pad = 40
    bar = Image.new("RGBA", (word.width + pad * 2, word.height + pad * 2),
                    B.rgb(B.RED) + (255,))
    R.paste(bar, word, bar.width // 2, bar.height // 2, anchor="cm")
    return bar.rotate(90, expand=True)


def header_bar(label="FORMULA DYNAMICS", width=520, height=60):
    im = Image.new("RGBA", (width, height), B.rgb(B.RED) + (255,))
    R.paste(im, R.text(label, 29, B.WHITE, tracking=0.22),
            width // 2, height // 2, anchor="cm")
    return im


def caption_plate(service, offer, fine, height):
    """Service, the offer, and the conditions — on ground, never over picture."""
    im = Image.new("RGBA", (W, height), (10, 10, 12, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 5], fill=B.rgb(B.RED) + (255,))

    x = int(W * SAFE["left"])
    y = 42
    R.paste(im, R.text(service, 62, B.WHITE, tracking=0.05), x, y)
    y += 74
    R.paste(im, R.text(offer, 30, B.RED, tracking=0.20), x, y)
    y += 56
    R.paste(im, R.text(fine, 21, "#B4B3AE", tracking=0.12), x, y)

    # the five-segment accent stripe, bottom-right, as the sign-off
    st = R.accent_stripe(300, 9)
    im.alpha_composite(st.convert("RGBA"),
                       (W - int(W * SAFE["right"]) - 300, height - 40))
    return im


def poster(name, src, hero_t, detail_ts, tab, service, offer, fine):
    TMP.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)

    plate_h = 300
    strip_h = int(H * 0.20)
    strip_y = H - plate_h - strip_h
    pane_w = (W - 2 * 8) // 3

    canvas = Image.new("RGB", (W, H), (8, 8, 10))
    canvas.paste(grab(src, hero_t, TMP / f"{name}-hero.png"), (0, 0))

    for i, t in enumerate(detail_ts[:3]):
        f = grab(src, t, TMP / f"{name}-d{i}.png")
        # centre-crop each detail to the pane's aspect, then fit
        ar = pane_w / strip_h
        cw = min(f.width, int(f.height * ar))
        ch = int(cw / ar)
        f = f.crop(((f.width - cw) // 2, (f.height - ch) // 2,
                    (f.width + cw) // 2, (f.height + ch) // 2))
        canvas.paste(f.resize((pane_w, strip_h), Image.LANCZOS),
                     (i * (pane_w + 8), strip_y))

    im = canvas.convert("RGBA")
    im.alpha_composite(caption_plate(service, offer, fine, plate_h),
                       (0, H - plate_h))
    im.alpha_composite(header_bar(),
                       (W - 520 - int(W * SAFE["left"]), int(H * 0.09)))
    t = vertical_tab(tab)
    im.alpha_composite(t, (int(W * SAFE["left"]), int(H * 0.30)))

    path = OUT / f"{name}.png"
    im.convert("RGB").save(path, quality=95)
    print(f"ok  {path.name}  ({path.stat().st_size / 1024:.0f} KB)")


POSTERS = {}


def register(cars):
    POSTERS.update(cars)


if __name__ == "__main__":
    cars = {k: v for k, v in (
        ("annual", dict(
            src="sf90.mp4", hero_t=14.0, detail_ts=(12.0, 16.0, 19.4),
            tab="ANNUAL SERVICE", service="ANNUAL SERVICE PACKAGE",
            offer="$3,999 PER YEAR",
            fine="2 OIL  ·  1 BRAKE  ·  2 DIAGNOSTICS  ·  ANY SUSPENSION  ·  10% OFF UPGRADES")),
        ("fullppf", dict(
            src="roma.mov", hero_t=21.5, detail_ts=(7.0, 9.2, 10.6),
            tab="FULL CAR PPF", service="FULL CAR PPF",
            offer="CERAMIC COATING INCLUDED",
            fine="EXTERIOR AND INTERIOR CERAMIC  ·  FITTED IN HOUSE")),
        ("windshield", dict(
            src="gt3.mov", hero_t=22.4, detail_ts=(3.2, 2.1, 16.1),
            tab="WINDSHIELD PPF", service="WINDSHIELD PPF",
            offer="$899  ·  HEADLIGHTS FREE",
            fine="HEADLIGHT PPF INCLUDED FREE  ·  FITTED IN HOUSE")),
        ("freetune", dict(
            src="roma.mov", hero_t=17.0, detail_ts=(10.9, 19.0, 9.0),
            tab="FREE ECU TUNE", service="FREE ECU TUNE",
            offer="WITH A RYFT OR OPUS EXHAUST",
            fine="RYFT TITANIUM FITTED HERE  ·  CALIBRATION INCLUDED")),
    )}
    base = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
        "/tmp/claude-0/-home-user-UIUX/5bb5d167-c2f1-59e3-92c2-13e844847166/scratchpad/cars")
    want = sys.argv[1] if len(sys.argv) > 1 else "all"
    for key, cfg in cars.items():
        if want in ("all", key):
            cfg = dict(cfg)
            cfg["src"] = base / cfg["src"]
            poster(key, **cfg)
