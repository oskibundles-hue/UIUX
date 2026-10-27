#!/usr/bin/env python3
"""
thumbnail - pick the best cover frames from a Reel and render them as
Instagram covers, with and without a headline, plus a grid-crop check.

Never let Instagram pick the cover (docs/03-hooks-and-captions.md). This does
the picking for you:

  1. samples the video (default 80 frames) and scores each frame on
     sharpness, exposure (no crushed blacks or blown paint) and colour;
  2. keeps the best few, spread through the video so they aren't the same shot;
  3. renders each at 1080x1920 twice: clean, and with your headline in the
     brand's own type (the doc says test both);
  4. draws the 3:4 profile-grid crop over each so you can see what the grid
     cuts, and checks the headline sits inside it, out of the bottom third and
     out of the top-left corner where the UI goes;
  5. writes one contact sheet to pick from.

Style is Locked-On (the standard) in each brand's look:
  fd    Formula Dynamics: Bebas Neue, white, FD red #FE0F13 bar and accent line
  se    Supercar Experience: Space Grotesk, white, gold #BD9457 corner brackets,
        [ BRACKETED ] kicker in #FF4F16 (the site's own section device)
  vlog  personal (nq.young): Space Grotesk, white, caption gold #FBD101 rule

The headline is yours: the script never writes copy. Put the line you want
red/orange/gold after a | ("BUILT|NOT BOUGHT").

Usage:
    python3 thumbnail.py clip.mp4 --brand fd --text "FORGED|FITMENT DAY"
    python3 thumbnail.py clip.mp4 --brand se --text "KEYS|HANDED OVER" --kicker "THE PICKUP"
    python3 thumbnail.py clip.mp4 --brand vlog --at 12.5 --at 40   # your own frames
    python3 thumbnail.py clip.mp4 --brand fd --lut ../luts/fd.cube --picks 6

Needs ffmpeg, Pillow and numpy. Output goes to covers/<clip name>/.
"""

import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
FONTS = os.path.join(KIT, "fonts")
W, H = 1080, 1920
SW, SH = 216, 384                      # scoring size: small is fast and enough
GRID = (0, 240, 1080, 1680)            # Instagram's 3:4 profile-grid crop of a 9:16 cover
BOTTOM_THIRD = H * 2 // 3              # 1280: captions, buttons and the grid crop live here
TOP_LEFT = (0, 0, 540, 420)            # profile name and audio label

BRANDS = {
    "fd":   {"font": "BebasNeue-Regular.ttf", "accent": "#FE0F13", "case": "upper", "track": 2, "mark": "bar"},
    "se":   {"font": "SpaceGrotesk.ttf", "accent": "#FF4F16", "line": "#BD9457", "case": "upper", "track": 4,
             "mark": "brackets", "weight": 700},
    "vlog": {"font": "SpaceGrotesk.ttf", "accent": "#FBD101", "case": "keep", "track": 0, "mark": "rule", "weight": 700},
}


def probe_duration(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        sys.exit(f"could not read a duration from {video}")


def sample(video, dur, n):
    """n evenly spaced frames at scoring size as an (n, SH, SW, 3) uint8 array, with their times."""
    times = [dur * (i + 0.5) / n for i in range(n)]
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf",
                          f"fps={n / dur:.6f},scale={SW}:{SH}:force_original_aspect_ratio=increase,crop={SW}:{SH}",
                          "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True)
    if out.returncode:
        sys.exit("ffmpeg could not read frames: " + out.stderr.decode(errors="replace").strip()[-300:])
    frames = np.frombuffer(out.stdout, np.uint8)
    k = len(frames) // (SW * SH * 3)
    return frames[:k * SW * SH * 3].reshape(k, SH, SW, 3), times[:k]


def frame_stats(f):
    """Raw measures of one frame: sharpness, exposure, colourfulness."""
    g = f.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    r, gr, b = (f[..., i].astype(np.float32) for i in range(3))
    rg, yb = r - gr, 0.5 * (r + gr) - b
    return {
        "sharp": float(lap.var()),
        "mean": float(g.mean() / 255),
        "clipped": float((g > 250).mean()),
        "crushed": float((g < 6).mean()),
        "colour": float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean())),
    }


def score_frames(frames):
    """Score 0-1ish per frame. Sharpness counts most, relative to this video's own frames, so a dim
    clip isn't marked down for being dim; exposure and colour break ties; blown or black frames sink."""
    st = [frame_stats(f) for f in frames]
    sharp = np.array([s["sharp"] for s in st])
    colour = np.array([s["colour"] for s in st])
    rel = lambda a: (a - a.min()) / (np.ptp(a) or 1)
    out = []
    for i, s in enumerate(st):
        expo = 1 - min(1, abs(s["mean"] - 0.45) / 0.45)
        bad = min(1, 4 * s["clipped"] + 3 * s["crushed"])
        out.append(round(float(0.55 * rel(sharp)[i] + 0.25 * expo + 0.20 * rel(colour)[i] - 0.6 * bad), 4))
    return out, st


def pick(times, scores, frames, n, min_gap):
    """Best n frames, at least min_gap seconds apart and not near-identical to one already kept."""
    hist = [np.histogram(f, bins=24, range=(0, 255))[0] / f.size for f in frames]
    kept = []
    order = sorted(range(len(times)), key=lambda i: -scores[i])
    floor = scores[order[0]] * 0.6       # fewer options beats a soft or black one
    for i in order:
        if scores[i] < floor:
            break
        if all(abs(times[i] - times[j]) >= min_gap and np.abs(hist[i] - hist[j]).sum() > 0.08 for j in kept):
            kept.append(i)
        if len(kept) == n:
            break
    return sorted(kept, key=lambda i: times[i])


def grab(video, t, lut=None):
    """Full-quality frame at t, filled and centre-cropped to 1080x1920, graded through a .cube LUT if given."""
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    if lut:
        vf += f",lut3d='{lut}'"
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    if out.returncode or len(out.stdout) < W * H * 3:
        sys.exit(f"could not grab the frame at {t:.2f}s: " + out.stderr.decode(errors="replace").strip()[-300:])
    return Image.frombuffer("RGB", (W, H), out.stdout[:W * H * 3])


def font(brand, size):
    f = ImageFont.truetype(os.path.join(FONTS, brand["font"]), size)
    if brand.get("weight"):
        try:
            f.set_variation_by_axes([brand["weight"]])
        except Exception:
            pass  # static face: use as is
    return f


def text_w(draw, s, f, track):
    return draw.textlength(s, font=f) + track * max(0, len(s) - 1)


def draw_tracked(draw, xy, s, f, fill, track):
    x, y = xy
    if not track:
        draw.text((x, y), s, font=f, fill=fill)
        return
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + track


def fit_lines(draw, lines, brand, max_w, max_h):
    """Largest size (down from 220 px) at which every line fits max_w and the block fits max_h."""
    for size in range(220, 40, -4):
        f = font(brand, size)
        tr = brand["track"] * size // 100
        lh = int(size * (0.95 if brand["font"].startswith("Bebas") else 1.08))
        if max(text_w(draw, s, f, tr) for s in lines) <= max_w and lh * len(lines) <= max_h:
            return f, tr, lh
    return font(brand, 40), 0, 44


def render_text(img, brand_key, text, kicker=None, pos="upper"):
    """Headline in the brand's type, inside the grid crop, clear of the bottom third and top-left.
    Returns the image and the bounding box of everything drawn, for the safe-zone check."""
    brand = BRANDS[brand_key]
    parts = [p.strip() for p in text.split("|")]
    main = [l for l in parts[0].split("\\n") if l] if parts[0] else []
    accent = [l for l in parts[1].split("\\n") if l] if len(parts) > 1 else []
    if brand["case"] == "upper":
        main, accent = [l.upper() for l in main], [l.upper() for l in accent]
    lines = [(l, "#FFFFFF") for l in main] + [(l, brand["accent"]) for l in accent]
    margin = 110
    max_w = W - 2 * margin
    top = 470 if pos == "upper" else 760         # below the top-left UI band, well above the bottom third
    max_h = BOTTOM_THIRD - 80 - top

    img = img.convert("RGBA")
    probe = ImageDraw.Draw(img)
    f, tr, lh = fit_lines(probe, [l for l, _ in lines], brand, max_w, max_h - (90 if kicker else 0))
    kf = font(brand, max(34, lh // 4))
    block_h = lh * len(lines) + (int(kf.size * 1.9) if kicker else 0)

    # scrim: a soft dark band behind the block, so the type reads on any frame (legibility lens)
    band = Image.new("L", (W, H), 0)
    ImageDraw.Draw(band).rectangle((0, top - 110, W, top + block_h + 110), fill=215)
    img = Image.alpha_composite(img, Image.merge("RGBA", (*[Image.new("L", (W, H), 0)] * 3,
                                                           band.filter(ImageFilter.GaussianBlur(80)))))
    d = ImageDraw.Draw(img)

    y = top
    xs, boxes = [], []
    if kicker:
        k = f"[ {kicker.upper()} ]" if brand_key == "se" else kicker.upper()
        kw = text_w(d, k, kf, 3)
        draw_tracked(d, ((W - kw) / 2, y), k, kf, brand["accent"], 3)
        boxes.append(((W - kw) / 2, y, (W + kw) / 2, y + kf.size))
        y += int(kf.size * 1.9)
    low = []
    for s, col in lines:
        w = text_w(d, s, f, tr)
        x = (W - w) / 2
        under = np.asarray(img.crop((int(x), y, int(x + w), y + lh)).convert("RGB"))
        if contrast(col, under) < 3.0:
            low.append(s)
        # a soft shadow keeps the edge crisp over bright paint
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_tracked(ImageDraw.Draw(sh), (x, y + 6), s, f, (0, 0, 0, 170), tr)
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(img)
        draw_tracked(d, (x, y), s, f, col, tr)
        bb = d.textbbox((x, y), s, font=f)
        boxes.append((x, bb[1], x + w, bb[3]))
        xs.append((x, x + w))
        y += lh

    x0 = min(b[0] for b in boxes); x1 = max(b[2] for b in boxes)
    y0 = min(b[1] for b in boxes); y1 = max(b[3] for b in boxes)
    pad = 36
    if brand["mark"] == "bar":                       # FD: red bar under the block
        d.rectangle(((W - 160) / 2, y1 + 34, (W + 160) / 2, y1 + 46), fill=brand["accent"])
        y1 += 46
    elif brand["mark"] == "brackets":                # SE: Locked-On gold corner brackets
        L, t = 64, 6
        bx0, by0, bx1, by1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        for cx, cy, sx, sy in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
            d.rectangle((min(cx, cx + sx * L), min(cy, cy + sy * t), max(cx, cx + sx * L), max(cy, cy + sy * t)),
                        fill=brand["line"])
            d.rectangle((min(cx, cx + sx * t), min(cy, cy + sy * L), max(cx, cx + sx * t), max(cy, cy + sy * L)),
                        fill=brand["line"])
        x0, y0, x1, y1 = bx0, by0, bx1, by1
    elif brand["mark"] == "rule":                    # vlog: caption-gold rule above the block
        d.rectangle(((W - 120) / 2, y0 - 46, (W + 120) / 2, y0 - 38), fill=brand["accent"])
        y0 -= 46
    return img.convert("RGB"), (int(x0), int(y0), int(x1), int(y1)), low


def luminance(rgb):
    c = np.asarray(rgb, np.float64) / 255
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c @ np.array([0.2126, 0.7152, 0.0722])


def contrast(hex_col, under):
    """WCAG contrast of the text colour against the brightest tenth of what is behind it (the worst case)."""
    fg = luminance([int(hex_col[i:i + 2], 16) for i in (1, 3, 5)])
    bg = np.percentile(luminance(under.reshape(-1, 3)), 90)
    hi, lo = max(fg, bg), min(fg, bg)
    return (hi + 0.05) / (lo + 0.05)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def safe_check(box):
    """Problems with where the headline sits; empty list means it's safe."""
    issues = []
    if not (box[0] >= GRID[0] and box[1] >= GRID[1] and box[2] <= GRID[2] and box[3] <= GRID[3]):
        issues.append("outside the 3:4 grid crop")
    if box[3] > BOTTOM_THIRD:
        issues.append("in the bottom third")
    if overlaps(box, TOP_LEFT):
        issues.append("in the top-left UI corner")
    return issues


def grid_preview(img):
    """The cover with what the 3:4 profile grid cuts off dimmed, and the bottom third hatched."""
    p = img.convert("RGBA")
    shade = Image.new("RGBA", p.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shade)
    d.rectangle((0, 0, W, GRID[1]), fill=(0, 0, 0, 170))
    d.rectangle((0, GRID[3], W, H), fill=(0, 0, 0, 170))
    for x in range(-H, W, 48):
        d.line((x, H, x + (H - BOTTOM_THIRD), BOTTOM_THIRD), fill=(255, 255, 255, 40), width=3)
    d.rectangle(GRID, outline=(255, 255, 255, 230), width=6)
    return Image.alpha_composite(p, shade).convert("RGB")


def sheet(rows, path):
    """One row per pick: clean cover, headline cover, grid preview, with a label strip."""
    tw, th, lab = 270, 480, 46
    cols = 3 if rows and rows[0].get("text") is not None else 2
    s = Image.new("RGB", (cols * tw + (cols + 1) * 12, len(rows) * (th + lab + 12) + 12), (18, 18, 18))
    d = ImageDraw.Draw(s)
    lf = ImageFont.truetype(os.path.join(FONTS, "SpaceGrotesk.ttf"), 22)
    for r, row in enumerate(rows):
        y = 12 + r * (th + lab + 12)
        ims = [row["clean"]] + ([row["text"]] if cols == 3 else []) + [row["grid"]]
        for c, im in enumerate(ims):
            s.paste(im.resize((tw, th), Image.LANCZOS), (12 + c * (tw + 12), y))
        flag = "  SAFE" if not row["issues"] else "  CHECK: " + ", ".join(row["issues"])
        d.text((14, y + th + 10), f"#{row['n']}  {row['t']:.1f}s  score {row['score']:.2f}{flag}", font=lf,
               fill=(235, 235, 235) if not row["issues"] else (255, 120, 90))
    s.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--brand", choices=sorted(BRANDS), required=True)
    ap.add_argument("--text", help="headline; part after | takes the accent colour; \\n breaks a line")
    ap.add_argument("--kicker", help="small label above the headline (SE: shown as [ LABEL ])")
    ap.add_argument("--pos", choices=["upper", "middle"], default="upper")
    ap.add_argument("--picks", type=int, default=4, help="cover options to render (default 4)")
    ap.add_argument("--samples", type=int, default=80, help="frames to score (default 80)")
    ap.add_argument("--at", type=float, action="append", help="use this time (s) instead of auto-picking; repeatable")
    ap.add_argument("--lut", help=".cube LUT to grade the cover through, so it matches the Reel")
    ap.add_argument("--out", help="output folder (default creator-kit/covers/<clip name>)")
    args = ap.parse_args()

    if not os.path.isfile(args.video):
        sys.exit(f"not found: {args.video}")
    stem = os.path.splitext(os.path.basename(args.video))[0]
    out = args.out or os.path.join(KIT, "covers", stem)
    os.makedirs(out, exist_ok=True)
    dur = probe_duration(args.video)

    frames, times = sample(args.video, dur, max(args.samples, args.picks))
    scores, stats = score_frames(frames)
    if args.at:
        chosen = [(t, scores[int(np.argmin([abs(t - x) for x in times]))]) for t in args.at]
    else:
        chosen = [(times[i], scores[i]) for i in pick(times, scores, frames, args.picks, dur / (args.picks * 2.5))]

    rows, report = [], []
    for n, (t, sc) in enumerate(chosen, 1):
        clean = grab(args.video, t, args.lut)
        clean.save(os.path.join(out, f"cover-{n:02d}-clean.jpg"), quality=95)
        row = {"n": n, "t": t, "score": sc, "clean": clean, "text": None, "issues": []}
        base = clean
        if args.text:
            row["text"], box, low = render_text(clean, args.brand, args.text, args.kicker, args.pos)
            row["text"].save(os.path.join(out, f"cover-{n:02d}-text.jpg"), quality=95)
            row["issues"] = safe_check(box) + [f"low contrast: {l}" for l in low]
            base = row["text"]
        row["grid"] = grid_preview(base)
        row["grid"].save(os.path.join(out, f"grid-{n:02d}.jpg"), quality=90)
        rows.append(row)
        report.append({"n": n, "time": round(t, 2), "score": sc, "safe": not row["issues"], "issues": row["issues"]})

    sheet(rows, os.path.join(out, "sheet.png"))
    json.dump({"video": args.video, "brand": args.brand, "text": args.text, "covers": report},
              open(os.path.join(out, "covers.json"), "w"), indent=1)
    bad = [r for r in report if not r["safe"]]
    print(f"{len(report)} covers -> {out}/sheet.png" + (f" ({len(bad)} need a look)" if bad else ""))
    for r in report:
        print(f"  #{r['n']} {r['time']:6.1f}s score {r['score']:.2f}" + ("" if r["safe"] else "  " + ", ".join(r["issues"])))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
