#!/usr/bin/env python3
"""
FORMULA DYNAMICS — 9:16 social ad renderer.

Renders animated typography / HUD overlay frames with Pillow, then composites
them onto the footage plate with ffmpeg.

    python3 build_ad.py                 # full render -> out/formula-dynamics-15s-9x16.mp4
    python3 build_ad.py --frames-only   # just write out the PNG overlay sequence
    python3 build_ad.py --stills 2.0 6.5 10.0   # preview single composited frames

All copy, timing and spec numbers live in the CONFIG block below — edit there,
never in the drawing code.
"""

import argparse
import math
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, "fonts")
PLATE = os.path.join(ROOT, "source", "plate-1080x1920.mp4")
OUT_DIR = os.path.join(ROOT, "exports")
FRAME_DIR = os.path.join(ROOT, ".frames")

W, H = 1080, 1920
FPS = 30
DURATION = 15.70

# ---------------------------------------------------------------------------
# CONFIG — copy, timing, palette
# ---------------------------------------------------------------------------

BRAND = "FORMULA DYNAMICS"
DESCRIPTOR = "PERFORMANCE ENGINEERING"
DOMAIN = "FORMULADYNAMICS.COM"
CTA = "BOOK A DYNO SESSION"

# Placeholder figures — swap for the real build sheet before this ever runs as paid media.
BUILD_LABEL = "STAGE 2 · MCLAREN 765LT"
SPECS = [
    # label,      from,   to,      unit,      decimals
    ("POWER", 755, 902, "HP", 0),
    ("TORQUE", 590, 701, "LB-FT", 0),
    ("0–60", 2.7, 2.4, "SEC", 1),
]

HEADLINE_A = ["STOCK IS A", "STARTING POINT."]
HEADLINE_B = ["BUILT ON DATA.", "TUNED BY HAND."]

INK = (237, 234, 228)
DIM = (150, 146, 138)
ACCENT = (255, 59, 33)
HAIRLINE = (237, 234, 228, 44)

# Beat timing (seconds): (in, hold_out)
T_HUD = (0.35, 12.30)
T_HEAD_A = (1.05, 4.30)
T_SPECS = (4.80, 8.60)
T_HEAD_B = (9.10, 12.10)
T_END = 12.40

SHOW_SAFE = False
MARGIN = 96
# Platform UI safe area (Reels / TikTok / Shorts): keep type out of these bands.
SAFE_TOP = 150
SAFE_BOTTOM = 330
SPECS_TOP = 430
HEADLINE_TOP = 1236

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def display(size):
    return font("BigShoulders-Bold.ttf", size)


def mono(size, bold=False):
    return font("GeistMono-Bold.ttf" if bold else "GeistMono-Regular.ttf", size)


def fit_display(draw, lines, max_size, tracking=-2, max_w=None):
    """Largest display size at which every line fits the type column."""
    max_w = max_w or (W - 2 * MARGIN)
    size = max_size
    while size > 40:
        f = display(size)
        if all(text_width(draw, ln, f, tracking) <= max_w for ln in lines):
            return f, size
        size -= 2
    return display(size), size


def vgradient(height, color, top_alpha, bottom_alpha):
    """1px-wide vertical gradient scrim, stretched to frame width."""
    strip = Image.new("RGBA", (1, height))
    px = strip.load()
    for y in range(height):
        k = y / max(1, height - 1)
        px[0, y] = rgba(color, top_alpha + (bottom_alpha - top_alpha) * k)
    return strip.resize((W, height), Image.BILINEAR)


def ease_out(x):
    """Cubic ease-out, clamped."""
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return 3 * x * x - 2 * x * x * x


def beat(t, start, end, fade_in=0.45, fade_out=0.40):
    """Envelope for a timed element -> (opacity 0..1, entrance progress 0..1)."""
    if t < start or t > end:
        return 0.0, 0.0
    p = ease_out((t - start) / fade_in) if fade_in else 1.0
    o = p
    if t > end - fade_out and fade_out:
        o *= 1 - ease_in_out((t - (end - fade_out)) / fade_out)
    return o, p


def rgba(color, alpha):
    return (color[0], color[1], color[2], max(0, min(255, int(round(alpha * 255)))))


def tracked_text(draw, xy, text, fnt, fill, tracking=0, anchor_x="left"):
    """Draw text with manual letter-spacing. Returns total advance width."""
    total = 0
    for ch in text:
        total += draw.textlength(ch, font=fnt) + tracking
    if text:
        total -= tracking
    x, y = xy
    if anchor_x == "center":
        x -= total / 2
    elif anchor_x == "right":
        x -= total
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return total


def text_width(draw, text, fnt, tracking=0):
    total = sum(draw.textlength(c, font=fnt) + tracking for c in text)
    return total - tracking if text else 0


def wipe_mask(size, progress, feather=140, direction="right"):
    """Soft-edged reveal mask, used to wipe headlines in from the left."""
    w, h = size
    mask = Image.new("L", (w, h), 0)
    if progress <= 0:
        return mask
    if progress >= 1:
        mask.paste(255, (0, 0, w, h))
        return mask
    edge = progress * (w + feather)
    d = ImageDraw.Draw(mask)
    solid = int(edge - feather)
    if solid > 0:
        d.rectangle([0, 0, min(solid, w), h], fill=255)
    steps = 24
    for i in range(steps):
        x0 = solid + (feather / steps) * i
        x1 = solid + (feather / steps) * (i + 1)
        if x1 < 0 or x0 > w:
            continue
        v = int(255 * (1 - i / steps))
        d.rectangle([max(0, x0), 0, min(w, x1), h], fill=v)
    return mask


# ---------------------------------------------------------------------------
# emblem — tach sweep + FD monogram
# ---------------------------------------------------------------------------


def emblem(size, alpha, sweep=1.0):
    """Concentric tachometer arc with tick marks and an FD monogram."""
    ss = 4  # supersample
    s = size * ss
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(s * 0.06)
    box = [pad, pad, s - pad, s - pad]

    d.arc(box, 135, 45, fill=rgba(INK, alpha * 0.30), width=max(2, int(s * 0.008)))

    if sweep > 0:
        span = 270 * max(0.0, min(1.0, sweep))
        d.arc(box, 135, 135 + span, fill=rgba(ACCENT, alpha), width=max(3, int(s * 0.016)))

    # tick marks around the sweep
    cx = cy = s / 2
    r_out = (s - 2 * pad) / 2 - s * 0.045
    for i in range(10):
        ang = math.radians(135 + i * 30)
        long_tick = i % 3 == 0
        r_in = r_out - (s * 0.055 if long_tick else s * 0.030)
        lit = (i / 9) <= sweep
        col = rgba(INK, alpha * (0.85 if lit else 0.22))
        d.line(
            [cx + r_in * math.cos(ang), cy + r_in * math.sin(ang),
             cx + r_out * math.cos(ang), cy + r_out * math.sin(ang)],
            fill=col, width=max(2, int(s * 0.010)),
        )

    f = display(int(s * 0.44))
    tracked_text(d, (cx, cy - s * 0.30), "FD", f, rgba(INK, alpha), tracking=int(s * 0.012), anchor_x="center")

    return img.resize((size, size), Image.LANCZOS)


# ---------------------------------------------------------------------------
# beats
# ---------------------------------------------------------------------------


def draw_scrims(base, t):
    """Legibility gradients under the HUD and the lower type block."""
    top_o, _ = beat(t, T_HUD[0] - 0.2, T_HUD[1] + 0.4, fade_in=0.7, fade_out=0.7)
    if top_o > 0:
        g = vgradient(430, (5, 5, 6), 0.50 * top_o, 0.0)
        base.alpha_composite(g, (0, 0))

    lower = max(
        beat(t, *T_HEAD_A, fade_in=0.5, fade_out=0.45)[0],
        beat(t, *T_HEAD_B, fade_in=0.5, fade_out=0.45)[0],
    )
    if lower > 0:
        h = H - HEADLINE_TOP + 150
        g = vgradient(h, (5, 5, 6), 0.0, 0.72 * lower)
        base.alpha_composite(g, (0, H - h))

    spec_o, _ = beat(t, *T_SPECS, fade_in=0.5, fade_out=0.45)
    if spec_o > 0:
        g = vgradient(700, (5, 5, 6), 0.0, 0.36 * spec_o)
        base.alpha_composite(g, (0, SPECS_TOP - 260))
        base.alpha_composite(vgradient(260, (5, 5, 6), 0.36 * spec_o, 0.0), (0, SPECS_TOP + 440))


def draw_hud(base, d, t):
    o, p = beat(t, *T_HUD, fade_in=0.55, fade_out=0.55)
    if o <= 0:
        return
    y = 96
    f = mono(27, bold=True)
    tracked_text(d, (MARGIN, y), BRAND, f, rgba(INK, o * 0.92), tracking=5)

    # accent tick + descriptor, right aligned
    fr = mono(23)
    tracked_text(d, (W - MARGIN, y + 4), DESCRIPTOR, fr, rgba(DIM, o * 0.85), tracking=4, anchor_x="right")

    # hairline that draws in under the lockup
    rule_p = ease_out((t - T_HUD[0]) / 0.9)
    x1 = MARGIN + (W - 2 * MARGIN) * rule_p
    d.line([MARGIN, y + 48, x1, y + 48], fill=rgba(INK, o * 0.22), width=2)
    d.line([MARGIN, y + 48, MARGIN + 74 * rule_p, y + 48], fill=rgba(ACCENT, o), width=2)


def draw_headline(base, d, t, window, lines, anchor_y):
    o, _ = beat(t, *window, fade_in=0.5, fade_out=0.45)
    if o <= 0:
        return
    f, size = fit_display(d, lines, 156)
    line_h = int(size * 0.92)

    for i, line in enumerate(lines):
        lp = ease_out((t - window[0] - i * 0.16) / 0.75)
        if lp <= 0:
            continue
        dy = (1 - lp) * 46
        y = anchor_y + i * line_h + dy

        layer = Image.new("RGBA", (W, line_h + 90), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        tracked_text(ld, (MARGIN, 0), line, f, rgba(INK, o * lp), tracking=-2)
        layer.putalpha(
            Image.composite(
                layer.getchannel("A"),
                Image.new("L", layer.size, 0),
                wipe_mask(layer.size, min(1.0, lp * 1.25)),
            )
        )
        base.alpha_composite(layer, (0, int(y)))

    # accent rule under the block
    rp = ease_out((t - window[0] - 0.30) / 0.85)
    if rp > 0:
        ry = anchor_y + len(lines) * line_h + 34
        d.line([MARGIN, ry, MARGIN + 210 * rp, ry], fill=rgba(ACCENT, o), width=5)


def draw_specs(base, d, t):
    o, _ = beat(t, *T_SPECS, fade_in=0.5, fade_out=0.45)
    if o <= 0:
        return

    top = SPECS_TOP
    lf = mono(26, bold=True)
    tracked_text(d, (MARGIN, top), BUILD_LABEL, lf, rgba(ACCENT, o), tracking=6)
    d.line([MARGIN, top + 52, W - MARGIN, top + 52], fill=rgba(INK, o * 0.20), width=2)

    row_h = 132
    for i, (label, a, b, unit, dec) in enumerate(SPECS):
        rp = ease_out((t - T_SPECS[0] - 0.18 - i * 0.18) / 0.7)
        if rp <= 0:
            continue
        y = top + 92 + i * row_h + (1 - rp) * 24
        ro = o * rp

        tracked_text(d, (MARGIN, y + 26), label, mono(26), rgba(DIM, ro), tracking=5)

        # counter ramps from the stock figure to the tuned figure
        cp = ease_in_out((t - T_SPECS[0] - 0.35 - i * 0.18) / 1.15)
        val = a + (b - a) * cp
        txt = f"{val:.{dec}f}"

        vf = display(96)
        uf = mono(28, bold=True)
        x = W - MARGIN
        x -= tracked_text(d, (x, y + 34), unit, uf, rgba(DIM, ro), tracking=4, anchor_x="right") + 18
        x -= tracked_text(d, (x, y - 16), txt, vf, rgba(INK, ro), tracking=1, anchor_x="right") + 26

        # stock -> tuned delta, small, in front of the big number
        stock = f"{a:.{dec}f}"
        sf = mono(28)
        aw = text_width(d, "→", mono(28, bold=True), 0)
        tracked_text(d, (x, y + 34), "→", mono(28, bold=True), rgba(ACCENT, ro), tracking=0, anchor_x="right")
        tracked_text(d, (x - aw - 14, y + 34), stock, sf, rgba(DIM, ro * 0.85), tracking=2, anchor_x="right")

        d.line([MARGIN, y + 108, W - MARGIN, y + 108], fill=rgba(INK, ro * 0.13), width=2)


def draw_end_card(base, d, t):
    if t < T_END:
        return
    p = ease_out((t - T_END) / 0.85)

    # scrim
    scrim = Image.new("RGBA", (W, H), rgba((6, 6, 7), 0.72 * ease_in_out((t - T_END) / 0.7)))
    base.alpha_composite(scrim)

    cx = W / 2
    o = p

    em_size = 190
    em = emblem(em_size, o, sweep=ease_out((t - T_END - 0.15) / 1.0))
    base.alpha_composite(em, (int(cx - em_size / 2), 636))

    f = display(140)
    dy = (1 - p) * 22
    tracked_text(d, (cx, 880 + dy), "FORMULA", f, rgba(INK, o), tracking=6, anchor_x="center")
    tracked_text(d, (cx, 1010 + dy), "DYNAMICS", f, rgba(INK, o), tracking=6, anchor_x="center")

    rp = ease_out((t - T_END - 0.35) / 0.7)
    if rp > 0:
        d.line([cx - 130 * rp, 1186, cx + 130 * rp, 1186], fill=rgba(ACCENT, o), width=4)

    tracked_text(d, (cx, 1226), DESCRIPTOR, mono(28), rgba(DIM, o), tracking=8, anchor_x="center")

    cp = ease_out((t - T_END - 0.55) / 0.7)
    if cp > 0:
        bw, bh = 620, 108
        bx, by = cx - bw / 2, 1374 + (1 - cp) * 18
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=6,
                            outline=rgba(INK, o * cp * 0.55), width=2)
        d.rectangle([bx, by, bx + 6, by + bh], fill=rgba(ACCENT, o * cp))
        tracked_text(d, (cx + 3, by + 30), CTA, mono(30, bold=True), rgba(INK, o * cp), tracking=6, anchor_x="center")
        tracked_text(d, (cx, by + bh + 44), DOMAIN, mono(26), rgba(DIM, o * cp), tracking=7, anchor_x="center")


def draw_safe_guides(d):
    g = (0, 200, 255, 110)
    d.rectangle([MARGIN, SAFE_TOP, W - MARGIN, H - SAFE_BOTTOM], outline=g, width=3)
    d.line([W - 150, 0, W - 150, H], fill=(255, 200, 0, 90), width=2)


# ---------------------------------------------------------------------------
# frame assembly
# ---------------------------------------------------------------------------


def render_frame(t):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_scrims(img, t)
    d = ImageDraw.Draw(img)
    draw_hud(img, d, t)
    draw_headline(img, d, t, T_HEAD_A, HEADLINE_A, HEADLINE_TOP)
    draw_specs(img, d, t)
    draw_headline(img, d, t, T_HEAD_B, HEADLINE_B, HEADLINE_TOP)
    draw_end_card(img, d, t)
    if SHOW_SAFE:
        draw_safe_guides(d)
    return img


def render_sequence():
    if os.path.isdir(FRAME_DIR):
        shutil.rmtree(FRAME_DIR)
    os.makedirs(FRAME_DIR)
    n = int(round(DURATION * FPS))
    for i in range(n):
        render_frame(i / FPS).save(os.path.join(FRAME_DIR, f"{i:05d}.png"))
        if i % 60 == 0:
            print(f"  frame {i}/{n}", flush=True)
    return n


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def composite(out_path, crf=20):
    ff = ffmpeg_bin()
    cmd = [
        ff, "-y", "-hide_banner", "-loglevel", "error",
        "-i", PLATE,
        "-framerate", str(FPS), "-i", os.path.join(FRAME_DIR, "%05d.png"),
        "-filter_complex",
        "[0:v]fps=30,eq=contrast=1.05:saturation=0.95:gamma=1.0,"
        "vignette=angle=PI/4.6[bg];"
        "[bg][1:v]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]",
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
        "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out_path,
    ]
    subprocess.run(cmd, check=True)


def still(t, out_path):
    ff = ffmpeg_bin()
    tmp = os.path.join(OUT_DIR, ".still_bg.png")
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-ss", str(t),
                    "-i", PLATE, "-frames:v", "1",
                    "-vf", "eq=contrast=1.05:saturation=0.95:gamma=1.0,vignette=angle=PI/4.6",
                    tmp], check=True)
    bg = Image.open(tmp).convert("RGBA")
    bg.alpha_composite(render_frame(t))
    bg.convert("RGB").save(out_path, quality=90)
    os.remove(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-only", action="store_true")
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--safe", action="store_true", help="overlay safe-area guides")
    args = ap.parse_args()

    global SHOW_SAFE
    SHOW_SAFE = args.safe

    os.makedirs(OUT_DIR, exist_ok=True)

    if args.stills:
        for t in args.stills:
            p = os.path.join(OUT_DIR, f"still-{t:05.2f}s.jpg".replace(".", "_", 1))
            still(t, p)
            print(p)
        return

    if not os.path.exists(PLATE):
        sys.exit(f"missing footage plate: {PLATE}")

    print("rendering overlay frames...")
    n = render_sequence()
    print(f"{n} frames")
    out = os.path.join(OUT_DIR, "formula-dynamics-15s-9x16.mp4")
    print("compositing...")
    composite(out, crf=args.crf)
    still(13.9, os.path.join(OUT_DIR, "poster.jpg"))
    print(out)


if __name__ == "__main__":
    main()
