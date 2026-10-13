#!/usr/bin/env python3
"""Product cards for LIVERY store reels, lifted from the clean opening of an approved store ad.

    python3 prep_cards.py <ad.mp4> <t> <out.png>

The v2.1 store ads open on the product photo alone (white panel, black below) for about
0.5 s before the FD logo, title and price animate in. This grabs a frame from that clean
stretch (t <= 0.3 s), keeps only the white product panel, and sets it on black under the
beat-plate zone with a raked FD stripe band below it. Nothing from the ad's graphics
survives: the grab is before they appear, and only the white panel is kept.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import livery as L  # noqa: E402

PANEL_Y = 520          # panel top: clear of the beat plate (board ends ~y 440)


def main(src, t, out):
    if float(t) > 0.3:
        raise SystemExit("grab must come from the clean opening (t <= 0.3 s)")
    tmp = Path(tempfile.mkdtemp()) / "f.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", str(tmp)], check=True)
    fr = Image.open(tmp).convert("RGB")
    g = fr.convert("L")
    w, h = g.size
    col = g.resize((1, h), Image.BOX)
    rows = [col.getpixel((0, y)) for y in range(h)]
    white = [y for y, v in enumerate(rows) if v > 200]
    top, bot = white[0], white[-1]
    # product bbox inside the panel (pixels darker than the backdrop)
    mask = g.crop((0, top, w, bot)).point(lambda v: 255 if v < 225 else 0)
    bb = mask.getbbox()
    y0 = max(top, top + bb[1] - 90)
    y1 = min(bot, top + bb[3] + 90)
    panel = fr.crop((0, y0, w, y1))
    card = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 255))
    scale = L.W / panel.width
    panel = panel.resize((L.W, round(panel.height * scale)), Image.LANCZOS)
    card.paste(panel, (0, PANEL_Y))
    band = L.stripe_band(L.W, 30)
    card.alpha_composite(band, (0, PANEL_Y + panel.height + 24))
    card.convert("RGB").save(out)
    print(out, "panel", panel.size, "src rows", y0, y1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
