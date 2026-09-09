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

from PIL import Image, ImageDraw, ImageFilter, ImageStat  # noqa: E402
import fd_brand as B                        # noqa: E402
import fd_render as R                       # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "posters"
TMP = HERE / ".tmp"
W, H = B.CANVASES["9x16"]
SAFE = B.SAFE_ZONES_9X16

# What the frosted plate is pulled down to, in 0-255 luma. Low enough that
# white type and the red offer line both hold on any frame behind it.
TARGET_GLASS = 34


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


def frost(base, box, darken=0.42, feather=52):
    """Frosted glass cut out of the picture itself.

    The same device as the video panels: crop that rectangle of the poster,
    blur it, pull the brightness down, and put it back. The words then sit on
    the photograph rather than on a plate laid over it — which is the whole
    difference between translucent and a black box with a red border.

    The top edge fades in over `feather` pixels so there is no hard line where
    the glass starts.
    """
    x, y, w, h = box
    tile = base.crop((x, y, x + w, y + h)).convert("RGB")
    tile = tile.filter(ImageFilter.GaussianBlur(26))

    # How far to pull it down depends on what is behind it. A plate over dark
    # tarmac needs almost nothing; the same plate over sunlit concrete needs a
    # lot, and a fixed number is what left red type unreadable on the
    # windshield poster. Aim the glass at a set brightness instead.
    mean = ImageStat.Stat(tile.convert("L")).mean[0]
    if mean > TARGET_GLASS:
        darken = min(0.78, max(darken, 1 - TARGET_GLASS / mean))
    tile = Image.blend(tile, Image.new("RGB", tile.size, (9, 9, 11)), darken)

    tile = tile.convert("RGBA")
    a = Image.new("L", tile.size, 255)
    d = ImageDraw.Draw(a)
    for i in range(feather):                      # ease the top edge in
        d.line([(0, i), (w, i)], fill=int(255 * (i / feather) ** 0.8))
    tile.putalpha(a)
    return tile


def caption_plate(base, service, offer, fine, height):
    """Service, the offer, and the conditions, on glass cut from the poster.

    No fill and no border: the only furniture is a short red rule under the
    service name, the same 30%-width rule the video panels carry.
    """
    y0 = H - height
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(frost(base, (0, y0, W, height)), (0, y0))

    d = ImageDraw.Draw(im)
    x = int(W * SAFE["left"])
    y = y0 + 40

    name = R.text(service, 62, B.WHITE, tracking=0.05)
    R.paste(im, R.with_shadow(name), x, y)
    y += name.height + 16
    d.rectangle([x, y, x + int(name.width * 0.30), y + 7],
                fill=B.rgb(B.RED) + (255,))          # short rule, never a border
    y += 26
    R.paste(im, R.with_shadow(R.text(offer, 30, B.RED, tracking=0.20)), x, y)
    y += 52
    R.paste(im, R.with_shadow(R.text(fine, 21, "#C8C7C2", tracking=0.12)), x, y)

    # the five-segment accent stripe, bottom-right, as the sign-off
    st = R.accent_stripe(300, 9)
    im.alpha_composite(st.convert("RGBA"),
                       (W - int(W * SAFE["right"]) - 300, H - 40))
    return im


def poster(name, src, hero_t, hero_y, detail_ts, tab, service, offer, fine):
    TMP.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)

    plate_h = 330
    strip_h = int(H * 0.20)
    strip_y = H - plate_h - strip_h
    pane_w = (W - 2 * 8) // 3

    canvas = Image.new("RGB", (W, H), (8, 8, 10))

    # The hero is PUSHED UP into the window it actually gets, instead of being
    # pasted whole and then buried under the strip. That is what was cutting
    # cars in half: the frame filled the canvas but only the top two thirds of
    # it was ever visible, so the car sat behind the detail panes.
    #
    # `hero_y` is how far up the car needs to move. The frame is scaled by just
    # enough that lifting it by that much still reaches the bottom edge - so the
    # picture is full bleed, the car lands in the visible window, and the plate
    # at the foot has real photograph behind it to frost.
    hero = grab(src, hero_t, TMP / f"{name}-hero.png")
    lift = max(0, hero_y)
    f = 1 + lift / H
    big = hero.resize((round(W * f), round(H * f)), Image.LANCZOS)
    x0 = (big.width - W) // 2
    canvas.paste(big.crop((x0, lift, x0 + W, lift + H)), (0, 0))

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
    im.alpha_composite(caption_plate(canvas, service, offer, fine, plate_h))
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
        # hero_t / hero_y were picked by scanning every source at 2 fps for
        # edge energy and then reading the frames: the timestamp is the
        # sharpest one where the WHOLE car is in shot, and hero_y slides the
        # crop window onto it.
        ("annual", dict(
            src="sf90.mp4", hero_t=8.5, hero_y=430, detail_ts=(18.0, 12.0, 19.4),
            tab="ANNUAL SERVICE", service="ANNUAL SERVICE PACKAGE",
            offer="$3,999 PER YEAR",
            fine="2 OIL  ·  1 BRAKE  ·  2 DIAGNOSTICS  ·  ANY SUSPENSION  ·  10% OFF UPGRADES")),
        ("fullppf", dict(
            src="roma.mov", hero_t=6.5, hero_y=400, detail_ts=(19.5, 9.2, 10.6),
            tab="FULL CAR PPF", service="FULL CAR PPF",
            offer="CERAMIC COATING INCLUDED",
            fine="EXTERIOR AND INTERIOR CERAMIC  ·  FITTED IN HOUSE")),
        ("windshield", dict(
            src="gt3.mov", hero_t=6.5, hero_y=460, detail_ts=(3.2, 5.5, 16.1),
            tab="WINDSHIELD PPF", service="WINDSHIELD PPF",
            offer="$899  ·  HEADLIGHTS FREE",
            fine="HEADLIGHT PPF INCLUDED FREE  ·  FITTED IN HOUSE")),
        ("freetune", dict(
            src="roma.mov", hero_t=2.5, hero_y=380, detail_ts=(10.9, 19.5, 9.0),
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
