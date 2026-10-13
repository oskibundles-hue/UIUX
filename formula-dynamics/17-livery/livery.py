#!/usr/bin/env python3
"""LIVERY - graphics for the FD "Livery" look (proposed, 2026-10-13).

The reel wears a race livery: FD's five-segment accent stripe raked at 12 deg
becomes the transition (the "stripe pass"), beat labels sit on white race-number
boards, and every word is Bebas Neue sheared to the same 12 deg rake.

All values come from 99-toolkit/fd_brand.py. Everything renders as full-frame
1080x1920 RGBA PNGs so ffmpeg only has to overlay them (FD pipeline rule).

    python3 livery.py stills <outdir>            # end card + sample plates + test sheet
    python3 livery.py pass <outdir>              # stripe-pass frame sequence (RGBA PNGs)
    python3 livery.py plate <out.png> 01 "WORD"  # one beat plate
    python3 livery.py endcard <out.png>
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "99-toolkit"))
import fd_brand as B  # noqa: E402

W, H = B.CANVASES["9x16"]
FPS = 30
RAKE_DEG = 12.0
SHEAR = math.tan(math.radians(RAKE_DEG))          # 0.2126
SZ = B.SAFE_ZONES_9X16
SAFE = dict(top=int(H * SZ["top"]), bottom=int(H * (1 - SZ["bottom"])),
            left=int(W * SZ["left"]), right=int(W * (1 - SZ["right"])))
RED, WHITE, BLACK = B.rgb(B.RED), B.rgb(B.WHITE), B.rgb(B.BLACK)
LOGO_H = HERE.parent / "02-logos/png-transparent/fd-primary-horizontal--white_2000w.png"

PASS_FRAMES = 10            # stripe pass length (0.333 s at 30 fps)
PASS_CUT = 5                # frame index at which the frame is fully covered
PASS_SPAN = W + int(H * SHEAR) + 120   # band group width: wider than frame + rake


def font(px):
    return ImageFont.truetype(str(B.FONT_BEBAS), px)


def raked_text(text, px, fill, tracking=0.04):
    """Bebas Neue set with tracking, then sheared forward to the 12 deg rake."""
    f = font(px)
    track = int(px * tracking)
    widths = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else int(px * 0.22) for c in text]
    asc, desc = f.getmetrics()
    tw = sum(widths) + track * (len(text) - 1)
    pad = int((asc + desc) * SHEAR) + 8
    im = Image.new("RGBA", (tw + pad + 8, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 4
    for c, w in zip(text, widths):
        if c != " ":
            d.text((x - f.getbbox(c)[0], 4), c, font=f, fill=fill)
        x += w + track
    # forward shear: top moves right. x_src = x_dst + SHEAR*(y - h) ... use affine
    h = im.height
    return im.transform(im.size, Image.AFFINE, (1, SHEAR, -SHEAR * h, 0, 1, 0),
                        resample=Image.BICUBIC)


def trim(im):
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def number_board(num, size=150):
    """White race-number board, black raked numeral. Rounded like a door roundel."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * 0.14), fill=WHITE + (255,))
    t = trim(raked_text(num, int(size * 0.82), BLACK + (255,), tracking=0.02))
    im.alpha_composite(t, ((size - t.width) // 2, (size - t.height) // 2 + 2))
    return im


def stripe_band(width, height, raked=True):
    """The five-segment accent stripe as one horizontal band (shares from fd_brand)."""
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 0.0
    for hexc, share in B.ACCENT_STRIPE:
        w = width * share
        d.rectangle((int(x), 0, int(x + w) + 1, height), fill=B.rgb(hexc) + (255,))
        x += w
    if raked:
        pad = int(height * SHEAR)
        out = Image.new("RGBA", (width + pad, height), (0, 0, 0, 0))
        out.paste(im, (0, 0))
        return out.transform(out.size, Image.AFFINE, (1, SHEAR, -SHEAR * height, 0, 1, 0),
                             resample=Image.BICUBIC)
    return im


def beat_plate(num, word, sub=None):
    """Full-frame plate: number board top-left of the safe area, raked word beside it,
    a short raked red tape under the word. Lives inside the 9:16 keep-out zones."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bx, by = SAFE["left"] + 14, SAFE["top"] + 40
    board = number_board(num)
    im.alpha_composite(board, (bx, by))
    wd = trim(raked_text(word, 112, WHITE + (255,)))
    maxw = SAFE["right"] - (bx + board.width + 28)
    if wd.width > maxw:
        wd = wd.resize((maxw, int(wd.height * maxw / wd.width)), Image.LANCZOS)
    wx = bx + board.width + 28
    wy = by + (board.height - wd.height) // 2 - 10
    # soft legibility shadow under the word only (not on the logo; brand rule is logo-only)
    sh = Image.new("RGBA", wd.size, (0, 0, 0, 0))
    sh.putalpha(wd.getchannel("A").point(lambda a: int(a * 0.55)))
    im.alpha_composite(sh, (wx + 4, wy + 5))
    im.alpha_composite(wd, (wx, wy))
    tape_w = min(wd.width, 260)
    tape = Image.new("RGBA", (tape_w, 12), RED + (255,))
    pad = int(12 * SHEAR)
    t2 = Image.new("RGBA", (tape_w + pad, 12), (0, 0, 0, 0)); t2.paste(tape, (0, 0))
    t2 = t2.transform(t2.size, Image.AFFINE, (1, SHEAR, -SHEAR * 12, 0, 1, 0), resample=Image.BICUBIC)
    im.alpha_composite(t2, (wx, wy + wd.height + 14))
    if sub:
        s = trim(raked_text(sub, 46, WHITE + (230,), tracking=0.08))
        im.alpha_composite(s, (wx, wy + wd.height + 40))
    return im


def stripe_pass_frame(i):
    """Frame i of the stripe pass: five raked full-height bands sweep left to right.
    Fully covered at PASS_CUT - the hard cut hides under it."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    off = int(H * SHEAR)
    # Left edge L of the band group. Full cover needs L <= -off and L + SPAN >= W,
    # i.e. L in [W - SPAN, -off] = [-off-120, -off]; the cut frame sits at -off-60.
    l_start, l_cut, l_end = -(PASS_SPAN + off), -off - 60, W
    if i <= PASS_CUT:
        p = i / PASS_CUT
        x0 = l_start + (1 - (1 - p) ** 3) * (l_cut - l_start)      # ease out into cover
    else:
        p = (i - PASS_CUT) / (PASS_FRAMES - PASS_CUT)
        x0 = l_cut + (p ** 3) * (l_end - l_cut)                     # ease in out of frame
    d = ImageDraw.Draw(im)
    x = x0
    # bands ordered so red leads (arrives first) - reverse of stripe order across travel
    for hexc, share in B.ACCENT_STRIPE[::-1]:
        w = PASS_SPAN * share
        # parallelogram raked forward
        poly = [(x, H), (x + w, H), (x + w + off, 0), (x + off, 0)]
        d.polygon(poly, fill=B.rgb(hexc) + (255,))
        x += w
    return im


def endcard():
    """Black ground, white primary logo, raked livery stripe, BOOK YOUR BUILD raked,
    site and handle. Everything inside the keep-out zones."""
    im = Image.new("RGBA", (W, H), BLACK + (255,))
    logo = Image.open(LOGO_H).convert("RGBA")
    lw = 600
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    ly = SAFE["top"] + 230
    im.alpha_composite(logo, ((W - lw) // 2, ly))
    # full-bleed raked stripe band across the card
    band = stripe_band(W + 200, 30)
    by = ly + logo.height + 120
    im.alpha_composite(band, (-100, by))
    l1 = trim(raked_text("BOOK YOUR", 150, WHITE + (255,)))
    l2 = trim(raked_text("BUILD", 230, RED + (255,)))
    y = by + 110
    im.alpha_composite(l1, ((W - l1.width) // 2, y))
    y += l1.height + 22
    im.alpha_composite(l2, ((W - l2.width) // 2, y))
    y += l2.height + 70
    site = trim(raked_text("FORMULADYNAMICSPERFORMANCE.COM", 58, WHITE + (255,), tracking=0.06))
    hand = trim(raked_text("@FORMULADYNAMICSPERFORMANCE", 58, RED + (255,), tracking=0.06))
    for t in (site, hand):
        if t.width > W - 2 * SAFE["left"] - 40:
            s = (W - 2 * SAFE["left"] - 40) / t.width
            t = t.resize((int(t.width * s), int(t.height * s)), Image.LANCZOS)
        im.alpha_composite(t, ((W - t.width) // 2, y))
        y += t.height + 30
    assert y < SAFE["bottom"], f"end card runs into bottom keep-out ({y} >= {SAFE['bottom']})"
    return im


def endcard_store():
    """Store variant (fd-f8): same card, site formuladynamics.com, store CTA."""
    im = Image.new("RGBA", (W, H), BLACK + (255,))
    logo = Image.open(LOGO_H).convert("RGBA")
    lw = 600
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    ly = SAFE["top"] + 230
    im.alpha_composite(logo, ((W - lw) // 2, ly))
    band = stripe_band(W + 200, 30)
    by = ly + logo.height + 120
    im.alpha_composite(band, (-100, by))
    y = by + 110
    for txt, px, col in (("SHOP F8 PARTS", 150, WHITE), ("ONLINE", 200, RED)):
        t = trim(raked_text(txt, px, col + (255,)))
        im.alpha_composite(t, ((W - t.width) // 2, y)); y += t.height + 22
    y += 48
    for txt, col in (("FORMULADYNAMICS.COM", WHITE), ("@FORMULADYNAMICSPERFORMANCE", RED)):
        t = trim(raked_text(txt, 58, col + (255,), tracking=0.06))
        im.alpha_composite(t, ((W - t.width) // 2, y)); y += t.height + 30
    assert y < SAFE["bottom"]
    return im


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "stills"
    if cmd == "pass":
        out = Path(argv[2]); out.mkdir(parents=True, exist_ok=True)
        for i in range(PASS_FRAMES + 1):
            stripe_pass_frame(i).save(out / f"pass_{i:02d}.png")
    elif cmd == "plate":
        beat_plate(argv[3], argv[4], argv[5] if len(argv) > 5 else None).save(argv[2])
    elif cmd == "endcard":
        endcard().save(argv[2])
    elif cmd == "endcard-store":
        endcard_store().save(argv[2])
    elif cmd == "stills":
        out = Path(argv[2]); out.mkdir(parents=True, exist_ok=True)
        endcard().convert("RGB").save(out / "endcard_build.png")
        endcard_store().convert("RGB").save(out / "endcard_store.png")
        beat_plate("01", "ON THE LIFT").save(out / "plate_sample.png")
        # look-test sheet: plate over mid grey + 3 pass frames + both end cards, 1/3 scale
        tiles = []
        g = Image.new("RGBA", (W, H), (96, 96, 100, 255)); g.alpha_composite(beat_plate("01", "ON THE LIFT"))
        tiles.append(g)
        for i in (2, PASS_CUT, 8):
            t = Image.new("RGBA", (W, H), (60, 60, 64, 255)); t.alpha_composite(stripe_pass_frame(i)); tiles.append(t)
        tiles += [endcard(), endcard_store()]
        s = 3
        sheet = Image.new("RGB", (W // s * len(tiles) + 10 * (len(tiles) + 1), H // s + 20), (30, 30, 30))
        for k, t in enumerate(tiles):
            sheet.paste(t.convert("RGB").resize((W // s, H // s), Image.LANCZOS), (10 + k * (W // s + 10), 10))
        sheet.save(out / "look_test_sheet.jpg", quality=88)
    else:
        print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv) or 0)
