#!/usr/bin/env python3
"""Index a video library by what is visibly in it, using only numpy and PIL.

Written after a search for "the white/pink Porsche oil service" cost sixteen
clip downloads, about 11 GB, and a question to the shop. The clip was then
found in seconds by scoring frames for pink: the two oil clips came back at
21.2% and 19.8% of frame area against under 7% for everything else that day.

None of what follows needs a model. Every column is arithmetic over pixels,
which matters because the container this runs in has no torch, no cv2 and no
transformers, and anything installed into it dies with the session. What it
produces - a CSV and one contact sheet per clip - is small, lives in the repo
and answers most of the questions that sent us downloading.

    python3 fd_index.py index  <dir-or-files>...   -o indexdir
    python3 fd_index.py search indexdir --colour pink --min 10
    python3 fd_index.py search indexdir --sharp --bright --vertical

An "objects" column is deliberately left empty. Filling it needs CLIP or
similar on a machine that persists; the schema takes it without rework.
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"}
EVERY_SECONDS = 2.0        # one frame per this many seconds of clip
THUMB = (192, 341)         # contact-sheet cell, 9:16-ish
ANALYSE_W = 160            # frames are scored at this width; the eye is coarse

# Hue wedges in degrees. Pink and red overlap on purpose - "red" and "pink"
# are the words people actually use, and a magenta car answers to both.
HUES = {
    "red":    [(345, 360), (0, 10)],
    "pink":   [(290, 345)],
    "orange": [(10, 40)],
    "yellow": [(40, 70)],
    "green":  [(70, 165)],
    "teal":   [(165, 200)],
    "blue":   [(200, 260)],
    "purple": [(260, 290)],
}
COLUMNS = ["clip", "frame", "t", "w", "h", "orient", "sharp", "luma", "p97",
           "motion", "skin", "colours", "objects"]


# ---------------------------------------------------------------- ffmpeg ----
def ffmpeg_bin() -> str:
    """The toolkit's ffmpeg, or whatever is on PATH."""
    for mod, attr in (("imageio_ffmpeg", "get_ffmpeg_exe"),):
        try:
            return getattr(__import__(mod), attr)()
        except Exception:
            pass
    found = shutil.which("ffmpeg")
    if not found:
        sys.exit("no ffmpeg available")
    return found


def frames_of(video: Path, out: Path, every=EVERY_SECONDS) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg_bin(), "-nostdin", "-y", "-loglevel", "error", "-i", str(video),
         "-vf", f"fps=1/{every}", "-q:v", "3", str(out / "%04d.jpg")],
        check=False, stdin=subprocess.DEVNULL)
    return sorted(out.glob("*.jpg"))


# --------------------------------------------------------------- signals ----
def hsv(arr: np.ndarray):
    """Hue in degrees, saturation and value, from a float RGB array."""
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mx, mn = arr.max(2), arr.min(2)
    d = mx - mn
    sat = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0.0)
    safe = np.maximum(d, 1e-6)
    hue = np.where(mx == r, ((g - b) / safe) % 6,
                   np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4)) * 60.0
    return np.where(d < 1e-6, 0.0, hue), sat, mx


def colour_mix(hue, sat, val) -> dict[str, float]:
    """Fraction of the frame each named hue occupies.

    Grey, near-black and blown highlights are excluded. Without that a dark
    garage reads as "blue" and a white wall reads as whatever noise it carries,
    which is how a colour index turns into nonsense.
    """
    real = (sat > 0.12) & (val > 0.18) & (val < 0.97)
    total = float(real.size)
    mix = {}
    for name, wedges in HUES.items():
        m = np.zeros_like(real)
        for lo, hi in wedges:
            m |= (hue >= lo) & (hue < hi)
        frac = float((m & real).sum()) / total
        if frac >= 0.02:
            mix[name] = round(frac * 100, 1)
    return dict(sorted(mix.items(), key=lambda kv: -kv[1]))


def skin_fraction(hue, sat, val) -> float:
    """Roughly how much of the frame is skin, as a people-in-shot flag.

    Deliberately crude. It answers "does this clip need a permission
    conversation" and nothing finer; a gloved hand on a caliper should not
    trip it, a piece to camera should.
    """
    m = ((hue >= 5) & (hue <= 42) & (sat > 0.18) & (sat < 0.72)
         & (val > 0.25) & (val < 0.96))
    return round(float(m.mean()) * 100, 1)


def sharpness(grey: np.ndarray) -> float:
    """Edge energy. Low means motion blur or a soft focus pull.

    Scored on 0-255 rather than 0-1 so the number is legible: a sharp shop
    frame lands in the tens, a motion-blurred one near zero. On 0-1 every
    clip printed as 0.1 and the column told you nothing.
    """
    gy, gx = np.gradient(grey * 255.0)
    return round(float(np.hypot(gx, gy).std()), 1)


def measure(path: Path, prev: np.ndarray | None):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    small = im.resize((ANALYSE_W, max(1, round(ANALYSE_W * h / w))),
                      Image.BILINEAR)
    arr = np.asarray(small, dtype=np.float32) / 255.0
    hue, sat, val = hsv(arr)
    grey = arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)

    luma = grey * 255.0
    row = {
        "w": w, "h": h,
        "orient": "vertical" if h > w else ("square" if h == w else "landscape"),
        "sharp": sharpness(grey),
        "luma": round(float(luma.mean()), 1),
        "p97": round(float(np.percentile(luma, 97)), 1),
        "motion": 0.0 if prev is None
                  else round(float(np.abs(grey - prev).mean() * 100), 2),
        "skin": skin_fraction(hue, sat, val),
        "colours": " ".join(f"{k}:{v}" for k, v in colour_mix(hue, sat, val).items()),
        "objects": "",
    }
    return row, grey


# ------------------------------------------------------------ the writing ----
def contact_sheet(frames: list[Path], dest: Path, title: str, cols=10):
    from PIL import ImageDraw, ImageFont
    if not frames:
        return
    tw, th, gap, lab = THUMB[0], THUMB[1], 6, 16
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (gap + cols * (tw + gap),
                              gap + 26 + rows * (th + lab + gap)), (14, 14, 16))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        f = ImageFont.load_default()
    d.text((gap, gap), title, font=f, fill=(228, 26, 40))
    for i, p in enumerate(frames):
        r, c = divmod(i, cols)
        x = gap + c * (tw + gap)
        y = gap + 26 + r * (th + lab + gap)
        d.text((x, y), f"{(i + 1) * EVERY_SECONDS:.0f}s", font=f,
               fill=(190, 190, 196))
        im = Image.open(p)
        im.thumbnail((tw, th), Image.LANCZOS)
        sheet.paste(im, (x + (tw - im.width) // 2, y + lab))
    sheet.save(dest)


def index(paths: list[Path], out: Path, every: float):
    out.mkdir(parents=True, exist_ok=True)
    sheets = out / "sheets"
    sheets.mkdir(exist_ok=True)
    csv_path = out / "INDEX.csv"
    seen = set()
    if csv_path.exists():
        with csv_path.open() as fh:
            seen = {r["clip"] for r in csv.DictReader(fh)}
        fh_mode = "a"
    else:
        fh_mode = "w"

    videos = []
    for p in paths:
        if p.is_dir():
            videos += [q for q in sorted(p.rglob("*"))
                       if q.suffix.lower() in VIDEO_EXT]
        elif p.suffix.lower() in VIDEO_EXT:
            videos.append(p)

    with csv_path.open(fh_mode, newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        if fh_mode == "w":
            w.writeheader()
        for v in videos:
            if v.name in seen:
                print(f"  skip  {v.name}  (already indexed)")
                continue
            with tempfile.TemporaryDirectory() as tmp:
                frames = frames_of(v, Path(tmp), every)
                if not frames:
                    print(f"  FAIL  {v.name}  (no frames)")
                    continue
                prev = None
                for i, fr in enumerate(frames):
                    row, prev = measure(fr, prev)
                    row.update(clip=v.name, frame=i + 1,
                               t=round((i + 1) * every, 1))
                    w.writerow(row)
                contact_sheet(frames, sheets / f"{v.stem}.jpg",
                              f"{v.name}   {len(frames)} frames @ {every:g}s")
            print(f"  {v.name}  {len(frames)} frames")
    print(f"\n{csv_path}  and  {sheets}/")


# ------------------------------------------------------------- the asking ----
def search(out: Path, args):
    rows = list(csv.DictReader((out / "INDEX.csv").open()))
    hits = rows
    if args.colour:
        def frac(r):
            for part in r["colours"].split():
                k, _, v = part.partition(":")
                if k == args.colour:
                    return float(v)
            return 0.0
        hits = [r for r in hits if frac(r) >= args.min]
        hits.sort(key=frac, reverse=True)
    if args.sharp:
        cut = np.percentile([float(r["sharp"]) for r in rows], 60)
        hits = [r for r in hits if float(r["sharp"]) >= cut]
    if args.bright:
        hits = [r for r in hits if float(r["luma"]) >= 60]
    if args.dark:
        hits = [r for r in hits if float(r["luma"]) < 60]
    if args.vertical:
        hits = [r for r in hits if r["orient"] == "vertical"]
    if args.no_people:
        hits = [r for r in hits if float(r["skin"]) < 4.0]
    if args.clip:
        hits = [r for r in hits if args.clip.lower() in r["clip"].lower()]

    print(f"{'clip':44s} {'t':>6s} {'sharp':>6s} {'luma':>6s} "
          f"{'skin':>5s}  colours")
    for r in hits[:args.n]:
        print(f"{r['clip'][:44]:44s} {r['t']:>6s} {r['sharp']:>6s} "
              f"{r['luma']:>6s} {r['skin']:>5s}  {r['colours']}")
    print(f"\n{len(hits)} of {len(rows)} frames")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("index", help="score clips and write the index")
    i.add_argument("paths", nargs="+", type=Path)
    i.add_argument("-o", "--out", type=Path, default=Path("index"))
    i.add_argument("--every", type=float, default=EVERY_SECONDS,
                   help="seconds between sampled frames (default 2)")

    s = sub.add_parser("search", help="ask the index a question")
    s.add_argument("out", type=Path)
    s.add_argument("--colour", choices=sorted(HUES))
    s.add_argument("--min", type=float, default=8.0,
                   help="minimum %% of frame for --colour (default 8)")
    s.add_argument("--sharp", action="store_true", help="top 40%% by edge energy")
    s.add_argument("--bright", action="store_true")
    s.add_argument("--dark", action="store_true")
    s.add_argument("--vertical", action="store_true", help="poster-native 9:16")
    s.add_argument("--no-people", action="store_true",
                   help="skin under 4%% of frame")
    s.add_argument("--clip", help="substring of the clip filename")
    s.add_argument("-n", type=int, default=25)

    a = ap.parse_args()
    if a.cmd == "index":
        index(a.paths, a.out, a.every)
    else:
        search(a.out, a)


if __name__ == "__main__":
    main()
