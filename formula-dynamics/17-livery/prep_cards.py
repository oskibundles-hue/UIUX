#!/usr/bin/env python3
"""Product cards for LIVERY store reels, lifted from the clean opening of an approved store ad.

    python3 prep_cards.py <ad.mp4> <t> <out.png>

The v2.1 store ads open on the product photo alone (white panel, black below) for about
0.5 s before the FD logo, title and price animate in. This grabs a frame from that clean
stretch (t <= 0.3 s), cuts the product out of the white panel and scales it to fill a white
field that bleeds to the frame edges under the beat-plate zone, with a raked FD stripe band on top. Nothing from the ad's graphics
survives: the grab is before they appear, and only the white panel is kept.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import livery as L  # noqa: E402

PANEL_Y = 520          # panel top: clear of the beat plate (board ends ~y 440)
FILL_MARGIN = 40       # white kept round the product inside the field
MASK_LO, MASK_HI = 196, 236   # luma ramp for blending the product into the field


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
    mask = g.crop((0, top, w, bot)).point(lambda v: 255 if v < MASK_LO else 0)
    bb = mask.getbbox()
    # Fill the frame: the studio backdrop bleeds edge to edge below the beat board, and the
    # product is scaled up to fill that white field (Omarie, 13 Oct: "make the F8 product
    # cards fill the frame"). The board sits on black above a raked stripe band.
    prod = fr.crop((bb[0], top + bb[1], bb[2], top + bb[3]))
    bg = fr.getpixel((5, top + 5))
    field_y = PANEL_Y - 20
    card = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 255))
    card.paste(Image.new("RGBA", (L.W, L.H - field_y), bg + (255,)), (0, field_y))
    room_w, room_h = L.W - 2 * FILL_MARGIN, L.H - field_y - 2 * FILL_MARGIN - 60
    scale = min(room_w / prod.width, room_h / prod.height)
    prod = prod.resize((round(prod.width * scale), round(prod.height * scale)), Image.LANCZOS)
    py = field_y + FILL_MARGIN + (room_h - prod.height) // 2
    # Near-white pixels fade out so the photo's own panel edge and faint print behind the
    # product don't show at this size; the field is white, so highlights lose nothing.
    a = prod.convert("L").point(lambda v: 0 if v >= MASK_HI else 255 if v <= MASK_LO
                                else round(255 * (MASK_HI - v) / (MASK_HI - MASK_LO)))
    a = a.filter(ImageFilter.GaussianBlur(1.2))
    card.paste(prod, ((L.W - prod.width) // 2, py), a)
    band = L.stripe_band(L.W, 30)
    card.alpha_composite(band, (0, field_y - 30))
    card.convert("RGB").save(out)
    print(out, "product", prod.size, "scale", round(scale, 2), "at y", py)


if __name__ == "__main__":
    main(*sys.argv[1:4])
