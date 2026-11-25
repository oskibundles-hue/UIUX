#!/usr/bin/env python3
"""Formula Dynamics referral kit: QR cards (phone + print) and the animated phone card.

    uv run --no-project --with pillow --with "qrcode[pil]" python build_referral_kit.py
    ... build_referral_kit.py --no-video      # stills only

Everything Nate still has to decide lives in the CONFIG block. Change it and re-run; every
card regenerates. Until he signs off, OFFER is None and the cards carry no offer line, so
they are honest to hand out today: the code alone is what credits a referral.

Outputs (renders/):
    referral-card_9x16.png             2160x3840  phone card, ready now (no offer line)
    referral-card_9x16_offer-draft.png 2160x3840  same card showing where the offer would sit
    referral-card_print_3.5x2.png      2250x1350  600 dpi business card, 1/8 in bleed each side
    referral-card_9x16_animated.mp4    1080x1920  7 s, 30 fps, ends on the still
"""
import argparse
import math
import random
import subprocess
import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FD = HERE.parent
OUT = HERE / "renders"

# ---------------------------------------------------------------- CONFIG (Nate decides) ---
CODE = "OMARIE"            # PLACEHOLDER until Nate confirms the code name
OFFER = None               # PLACEHOLDER e.g. "FIRST VISIT: [NATE TO SET]". None = no offer line.
OFFER_DRAFT_TEXT = "OFFER LINE  ·  NATE TO SET"
# The site's booking form (Contact page) has a free-text message box; the code goes there.
QR_URL = f"https://www.formuladynamicsperformance.com/contact?ref={CODE.lower()}"
FD_SITE = "FORMULADYNAMICSPERFORMANCE.COM"        # = brand_tokens.FD_SITE
FD_HANDLE = "@FORMULADYNAMICSPERFORMANCE"         # = brand_tokens.FD_HANDLE
# -------------------------------------------------------------------------------------------

# FD pack (brand/packs.json, fd-telemetry). Red is the live signal only.
RED = (254, 15, 19)
WHITE = (255, 255, 255)
INK = (8, 8, 10)
SUB = (201, 201, 208)
GREY = (154, 154, 162)
STRIPE = [((254, 15, 19), .367), ((0, 0, 0), .214), ((255, 255, 255), .194),
          ((29, 177, 75), .170), ((255, 222, 0), .055)]

BEBAS = FD / "07-fonts/BebasNeue-Regular.ttf"
BARLOW_M = FD / "11-service-reels/fonts/BarlowCondensed-Medium.ttf"
BARLOW_B = FD / "11-service-reels/fonts/BarlowCondensed-Bold.ttf"
LOGO = FD / "02-logos/png-transparent/fd-primary-horizontal--white_2000w.png"

_fonts = {}


def font(path, px):
    key = (str(path), int(px))
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(path), int(px))
    return _fonts[key]


# ---------------------------------------------------------------- easing -------------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur) if dur > 0 else float(t >= start)


def out_cubic(p):
    return 1 - (1 - p) ** 3


def out_expo(p):
    return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)


def out_back(p, k=1.70158):
    p -= 1
    return 1 + (k + 1) * p ** 3 + k * p ** 2


# ---------------------------------------------------------------- drawing helpers ----------
def text_w(txt, f, track=0):
    if not txt:
        return 0
    return sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)


def draw_tracked(d, xy, txt, f, fill, track=0):
    x, y = xy
    for c in txt:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track


def text_layer(txt, f, fill, track=0):
    """Text on its own RGBA tile, cropped to the ink box (for masked reveals)."""
    w = int(text_w(txt, f, track)) + 8
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (w, asc + desc + 8), (0, 0, 0, 0))
    draw_tracked(ImageDraw.Draw(im), (4, 4), txt, f, fill, track)
    return im.crop(im.getbbox())


def paste_reveal(canvas, layer, x, y, p, rise=1.0):
    """Mask-up reveal: the layer slides up out of a slot at its final position."""
    if p <= 0:
        return
    h = layer.height
    off = int(round((1 - out_expo(p)) * h * rise))
    vis = layer.crop((0, 0, layer.width, h - off)) if off < h else None
    if vis is not None and vis.height > 0:
        canvas.alpha_composite(vis, (int(x), int(y + off)))


def with_alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(l2.getchannel("A").point(lambda v: int(v * a)))
    return l2


def stripe_band(length, thick):
    """The FD racing stripe, colours in brand proportion, as a horizontal RGBA strip."""
    im = Image.new("RGBA", (length, thick), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 0.0
    for col, frac in STRIPE:
        h = thick * frac
        d.rectangle([0, int(round(y)), length, int(round(y + h))], fill=col + (255,))
        y += h
    return im


_logo_cache = {}


def logo(width):
    if width not in _logo_cache:
        lg = Image.open(LOGO).convert("RGBA")
        lg = lg.crop(lg.getbbox())
        _logo_cache[width] = lg.resize((width, round(lg.height * width / lg.width)), Image.LANCZOS)
    return _logo_cache[width]


def qr_matrix():
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, border=0)
    q.add_data(QR_URL)
    q.make(fit=True)
    return q.get_matrix()


QR = qr_matrix()


def qr_tile(size, reveal=1.0, quiet=4):
    """White tile with the QR drawn as square modules. reveal sweeps in diagonally."""
    n = len(QR)
    mod = size / (n + 2 * quiet)
    im = Image.new("RGBA", (size, size), WHITE + (255,))
    d = ImageDraw.Draw(im)
    for r in range(n):
        for c in range(n):
            if not QR[r][c]:
                continue
            # diagonal sweep, top-left to bottom-right
            k = (r + c) / (2 * (n - 1))
            if reveal < 1 and reveal < k * 0.85 + 0.15 * random.Random(r * 997 + c).random():
                continue
            x0 = (quiet + c) * mod
            y0 = (quiet + r) * mod
            d.rectangle([round(x0), round(y0), round(x0 + mod) - 1, round(y0 + mod) - 1],
                        fill=INK + (255,))
    return im


def corner_ticks(d, box, arm, thick, spread=0.0, col=RED):
    """Lock-on brackets at the four corners of box, pushed outward by `spread` px."""
    x0, y0, x1, y1 = box
    for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        px, py = cx - sx * spread, cy - sy * spread
        d.rectangle(sorted_box(px, py, px + sx * arm, py + sy * thick), fill=col)
        d.rectangle(sorted_box(px, py, px + sx * thick, py + sy * arm), fill=col)


def sorted_box(a, b, c, e):
    return [min(a, c), min(b, e), max(a, c), max(b, e)]


def dashed_rect(d, box, dash, gap, width, fill):
    x0, y0, x1, y1 = box
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x0, y1, x1, y1), (x0, y0, x0, y1), (x1, y0, x1, y1)):
        length = math.hypot(bx - ax, by - ay)
        pos = 0
        while pos < length:
            e = min(pos + dash, length)
            fx, fy = ax + (bx - ax) * pos / length, ay + (by - ay) * pos / length
            tx, ty = ax + (bx - ax) * e / length, ay + (by - ay) * e / length
            d.line([(fx, fy), (tx, ty)], fill=fill, width=width)
            pos += dash + gap


# ---------------------------------------------------------------- the phone card -----------
DUR = 7.0


def speed_lines(W, H, s, t):
    """Faint diagonal motion lines drifting along the stripe angle (static on the still)."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = random.Random(7)
    ang = math.radians(-22)
    dx, dy = math.cos(ang), math.sin(ang)
    for i in range(26):
        y = rng.uniform(-0.2, 1.1) * H
        L = rng.uniform(140, 520) * s
        speed = rng.uniform(40, 120) * s
        x = (rng.uniform(-0.3, 1.0) * W + speed * t) % (W * 1.4) - 0.2 * W
        a = rng.randint(10, 26)
        d.line([(x, y), (x + dx * L, y + dy * L)], fill=GREY + (a,), width=max(1, int(2 * s)))
    return lay


def phone_card(t=DUR, W=1080, offer_mode="none"):
    """offer_mode: 'none' (ready now), 'draft' (placeholder slot), 'set' (uses OFFER)."""
    s = W / 1080
    H = int(1920 * s)
    cv = Image.new("RGBA", (W, H), INK + (255,))

    # motion lines, then the diagonal racing stripe across the top right
    cv.alpha_composite(speed_lines(W, H, s, t))
    band_len = int(1100 * s)
    band = stripe_band(band_len, int(56 * s))
    p = out_expo(prog(t, 0.0, 0.7))
    if p > 0:
        vis = band.crop((0, 0, max(1, int(band_len * p)), band.height))
        rot = vis.rotate(22, expand=True, resample=Image.BICUBIC)
        # anchored at its lower-left end, so it grows up and out past the top-right corner
        cv.alpha_composite(rot, (int(730 * s), int(262 * s) - rot.height))

    d = ImageDraw.Draw(cv)
    cx = W // 2

    # logo
    lg = logo(int(560 * s))
    p = out_cubic(prog(t, 0.2, 0.5))
    if p > 0:
        cv.alpha_composite(with_alpha(lg, p), (int(84 * s), int((120 - 30 * (1 - p)) * s)))

    # kicker
    kick = text_layer(f"REFERRED BY {CODE}", font(BARLOW_B, 36 * s), SUB, track=7 * s)
    kx, ky = int(88 * s), int(345 * s)
    p = prog(t, 0.5, 0.4)
    if p > 0:
        d.rectangle([kx, ky + 6 * s, kx + 10 * s, ky + kick.height - 2 * s], fill=RED)
        paste_reveal(cv, kick, kx + 28 * s, ky, p)

    # headline, three hard stops
    hf = font(BEBAS, 168 * s)
    y = 400 * s
    for i, word in enumerate(("SERVICE.", "UPGRADES.", "TUNING.")):
        lay = text_layer(word, hf, WHITE, track=2 * s)
        paste_reveal(cv, lay, 84 * s, y, prog(t, 0.7 + i * 0.16, 0.55))
        y += 150 * s
    # red rule grows under the headline
    p = out_expo(prog(t, 1.35, 0.5))
    if p > 0:
        d.rectangle([84 * s, 868 * s, 84 * s + 260 * s * p, 878 * s], fill=RED)
    sub = text_layer("Exotic and performance cars  ·  Las Vegas", font(BARLOW_M, 36 * s), SUB)
    paste_reveal(cv, sub, 88 * s, 898 * s, prog(t, 1.45, 0.5))

    # QR tile with lock-on brackets
    qs = int(440 * s)
    qx, qy = int(84 * s), int(1000 * s)
    p = prog(t, 1.8, 0.9)
    if p > 0:
        tile = qr_tile(qs, reveal=out_cubic(p))
        sc = 0.92 + 0.08 * out_back(clamp(p * 1.6))
        tw = int(qs * sc)
        tile = tile.resize((tw, tw), Image.LANCZOS) if tw != qs else tile
        off = (qs - tw) // 2
        cv.alpha_composite(with_alpha(tile, clamp(p * 3)), (qx + off, qy + off))
    p = prog(t, 1.65, 0.6)
    if p > 0:
        spread = (1 - out_back(p, 2.2)) * 160 * s + 22 * s
        corner_ticks(d, (qx, qy, qx + qs, qy + qs), 64 * s, 10 * s, spread=spread)
    # one red scan pass after the code lands (finishes well before the hold)
    p = prog(t, 3.9, 0.7)
    if 0 < p < 1:
        sy = qy + qs * out_cubic(p)
        glow = Image.new("RGBA", (qs, int(40 * s)), RED + (0,))
        gd = ImageDraw.Draw(glow)
        for i in range(glow.height):
            gd.line([(0, i), (qs, i)], fill=RED + (int(150 * (i / glow.height) ** 2),))
        cv.alpha_composite(glow, (qx, int(sy - glow.height)))
        d.rectangle([qx, sy - 3 * s, qx + qs, sy + 3 * s], fill=RED)

    # right column beside the QR: the instruction, then the code
    rx = qx + qs + 70 * s
    scan = text_layer("SCAN TO", font(BEBAS, 74 * s), GREY, track=2 * s)
    book = text_layer("BOOK YOUR", font(BEBAS, 74 * s), WHITE, track=2 * s)
    serv = text_layer("SERVICE", font(BEBAS, 74 * s), WHITE, track=2 * s)
    for i, lay in enumerate((scan, book, serv)):
        paste_reveal(cv, lay, rx, qy + 6 * s + i * 78 * s, prog(t, 2.3 + i * 0.1, 0.5))
    arrow_p = out_expo(prog(t, 2.6, 0.5))
    if arrow_p > 0:
        ax0, ay = rx, qy + 290 * s
        d.rectangle([ax0, ay, ax0 + 150 * s * arrow_p, ay + 8 * s], fill=RED)
        if arrow_p > 0.9:
            # arrow head points back at the QR
            d.polygon([(ax0 - 18 * s, ay + 4 * s), (ax0 + 14 * s, ay - 16 * s), (ax0 + 14 * s, ay + 24 * s)], fill=RED)

    # the code
    lab = text_layer("USE CODE", font(BARLOW_B, 38 * s), SUB, track=8 * s)
    paste_reveal(cv, lab, 88 * s, 1500 * s, prog(t, 2.75, 0.4))
    cf = font(BEBAS, 250 * s)
    x = 80 * s
    for i, ch in enumerate(CODE):
        p = prog(t, 2.9 + i * 0.07, 0.45)
        w = cf.getlength(ch)
        if p > 0:
            lay = text_layer(ch, cf, RED)
            sc = 1.35 - 0.35 * out_back(p, 2.0)
            lw, lh = max(1, int(lay.width * sc)), max(1, int(lay.height * sc))
            lay = with_alpha(lay.resize((lw, lh), Image.LANCZOS), clamp(p * 2.5))
            ox = x + (cf.getlength(ch) - lw) / 2
            cv.alpha_composite(lay, (int(ox), int(1548 * s + (lay.height / sc - lh) / 2)))
        x += w + 10 * s
    help_t = text_layer("Put the code in the booking message, or say it when you call.",
                        font(BARLOW_M, 34 * s), SUB)
    paste_reveal(cv, help_t, 88 * s, 1762 * s, prog(t, 3.35, 0.5))

    # offer slot
    if offer_mode == "draft":
        p = clamp(prog(t, 3.5, 0.4))
        if p > 0:
            box = [rx, qy + 330 * s, W - 64 * s, qy + qs]
            dashed_rect(d, box, 18 * s, 12 * s, int(3 * s), GREY + (int(255 * p),))
            of = font(BARLOW_B, 30 * s)
            for j, line in enumerate(("OFFER LINE GOES HERE", "NATE TO SET  ·  PLACEHOLDER")):
                lw = text_w(line, of, 2 * s)
                draw_tracked(d, (box[0] + (box[2] - box[0] - lw) / 2, box[1] + 22 * s + j * 46 * s),
                             line, of, GREY + (int(255 * p),), 2 * s)
    elif offer_mode == "set" and OFFER:
        lay = text_layer(OFFER, font(BEBAS, 64 * s), WHITE, track=2 * s)
        paste_reveal(cv, lay, rx, qy + 340 * s, prog(t, 3.5, 0.5))

    # footer
    fpx = 40
    while True:  # fit the contact line inside the side margins
        foot = text_layer(f"{FD_SITE}  ·  {FD_HANDLE}", font(BEBAS, fpx * s), GREY, track=1.5 * s)
        if foot.width <= W - 176 * s or fpx <= 26:
            break
        fpx -= 1
    p = prog(t, 3.5, 0.6)
    if p > 0:
        cv.alpha_composite(with_alpha(foot, p), (int(cx - foot.width / 2), int(1850 * s)))
    p = out_expo(prog(t, 0.1, 0.9))
    if p > 0:
        bar = stripe_band(int(W * p) or 1, int(14 * s))
        cv.alpha_composite(bar, (0, H - bar.height))
    return cv.convert("RGB")


# ---------------------------------------------------------------- the print card -----------
def print_card():
    """3.5 x 2 in at 600 dpi, 0.125 in bleed: 2250 x 1350, safe area inset 150 px."""
    W, H = 2250, 1350
    bleed, safe = 75, 150
    cv = Image.new("RGBA", (W, H), INK + (255,))
    s = 1.55  # relative to the phone card's 1080 scale, tuned for a card read at arm's length
    band = stripe_band(1500, 46).rotate(22, expand=True, resample=Image.BICUBIC)
    cv.alpha_composite(band, (W - 700, -260))
    d = ImageDraw.Draw(cv)
    lg = logo(760)
    cv.alpha_composite(lg, (safe, safe))
    y = safe + lg.height + 70
    kick = text_layer(f"REFERRED BY {CODE}", font(BARLOW_B, 60), SUB, track=10)
    d.rectangle([safe, y + 8, safe + 13, y + kick.height - 2], fill=RED)
    cv.alpha_composite(kick, (safe + 36, y))
    y += kick.height + 60
    lab = text_layer("USE CODE", font(BARLOW_B, 60), SUB, track=10)
    cv.alpha_composite(lab, (safe, y))
    y += lab.height + 10
    code = text_layer(CODE, font(BEBAS, 300), RED, track=14)
    cv.alpha_composite(code, (safe, y))
    y += code.height + 34
    h1 = text_layer("Put it in the booking message, or say it when you call.", font(BARLOW_M, 60), SUB)
    cv.alpha_composite(h1, (safe, y))
    # QR, right side, inside the safe area, with brackets
    qs = 660
    qx, qy = W - safe - qs - 40, H - safe - qs - 120
    cv.alpha_composite(qr_tile(qs), (qx, qy))
    corner_ticks(d, (qx, qy, qx + qs, qy + qs), 80, 13, spread=26)
    st = text_layer("SCAN TO BOOK YOUR SERVICE", font(BEBAS, 62), WHITE, track=3)
    cv.alpha_composite(st, (qx + (qs - st.width) // 2, qy + qs + 46))
    foot = text_layer(FD_SITE, font(BEBAS, 50), GREY, track=3)
    cv.alpha_composite(foot, (safe, H - safe - foot.height - 10))
    # runs off the bottom edge so the trim can wander without breaking the stripe
    bar = stripe_band(W, bleed + 30)
    cv.alpha_composite(bar, (0, H - bar.height))
    return cv.convert("RGB")


# ---------------------------------------------------------------- video -------------------
def render_video(path, fps=30):
    W, H = 1080, 1920
    n = int(DUR * fps)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(phone_card(t=i / fps, W=W).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("ffmpeg failed")


def contact_sheet(path, times=(0.3, 0.8, 1.3, 1.9, 2.4, 3.0, 3.6, 4.2, 7.0)):
    th = [phone_card(t=t, W=360) for t in times]
    sheet = Image.new("RGB", (360 * len(th) + 10 * (len(th) - 1), 640 + 50), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(zip(times, th)):
        sheet.paste(im, (i * 370, 50))
        d.text((i * 370 + 8, 10), f"{t:.1f}s", font=font(BARLOW_B, 30), fill=(255, 255, 255))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    phone_card(W=2160, offer_mode="set" if OFFER else "none").save(OUT / "referral-card_9x16.png")
    phone_card(W=2160, offer_mode="draft").save(OUT / "referral-card_9x16_offer-draft.png")
    print_card().save(OUT / "referral-card_print_3.5x2.png", dpi=(600, 600))
    contact_sheet(OUT / "animation-contact-sheet.png")
    if not a.no_video:
        render_video(OUT / "referral-card_9x16_animated.mp4")
    print("QR ->", QR_URL, f"({len(QR)}x{len(QR)} modules)")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name}  {p.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
