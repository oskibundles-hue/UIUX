#!/usr/bin/env python3
"""
type_frames.py - the whole overlay layer as a transparent PNG sequence: the
letterbox bars, the handle bug and the staircase kinetic type.

The bars live here rather than in an ffmpeg drawbox because drawbox has no
timestamp variable -- its `t` is the box thickness, so an animated band written
as a drawbox expression silently fills the frame. Drawing the bars per frame in
Pillow is exact and costs nothing, since the type sequence is being written
frame by frame anyway.

The look: ALL CAPS Archivo heavy, left-aligned, each line indented further than
the last so the block walks down and to the right. Words arrive one at a time on
the beat of the speech. One word per block may carry an accent colour and a small
RGB split, which is the only colour in an otherwise monochrome frame.

Lines come from a JSON script:

  [{"at": 1.0, "until": 7.6, "lines": ["WHAT DO YOU", "PLAN TO DO"], "accent": "DO"}]

`at` is when the first word lands, `until` when the block leaves. Words inside a
block are spread evenly between the two. Frames are written as NNNNN.png at the
sequence fps, and every frame is emitted, including empty ones, so ffmpeg can
read the directory as a plain image sequence.
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont

def load_font(path, size, weight):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes([weight, 100])
    except Exception:
        pass
    return f

def band_at(keys, t, H, frame=None):
    """
    Band edges in pixels. `steps` snaps between fixed values at given frames,
    which is what a reference edit usually does; `top` eases between keyframes.
    """
    if "steps" in keys:
        top = keys["steps"][0][1]
        for f0, v in keys["steps"]:
            if frame is not None and frame >= f0:
                top = v
        return int(H * top), int(H * keys["bottom"])
    ks = keys["top"]
    top = ks[-1][1]
    if t <= ks[0][0]:
        top = ks[0][1]
    else:
        for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
            if t0 <= t <= t1:
                top = v0 + (v1 - v0) * (t - t0) / (t1 - t0)
                break
    return int(H * top), int(H * keys["bottom"])


def indents(n, step):
    """Staircase: each line steps right, and the last drops back to the margin."""
    return [i * step for i in range(n - 1)] + [0] if n > 1 else [0]

def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def draw_block(img, blk, shown, font, W, band, margin, step, accent_rgb):
    d = ImageDraw.Draw(img)
    lines = blk["lines"]
    accent = blk.get("accent", "").upper()
    if blk.get("accent_color"):
        accent_rgb = hex_rgb(blk["accent_color"])
    ind = indents(len(lines), step)
    lh = int(font.size * 1.12)
    top = band[0] + (band[1] - band[0] - lh * len(lines)) // 2
    seen = 0
    for li, line in enumerate(lines):
        x = margin + ind[li]
        y = top + li * lh
        for word in line.split():
            if seen >= shown:
                return
            seen += 1
            w = d.textlength(word + " ", font=font)
            if word.strip(",.?!").upper() == accent:
                # the one coloured word carries a 3px RGB split, like the reference
                for dx, col in ((-3, (0, 255, 255, 140)), (3, (255, 0, 80, 140))):
                    d.text((x + dx, y), word, font=font, fill=col)
                d.text((x, y), word, font=font, fill=accent_rgb + (255,))
            else:
                d.text((x, y), word, font=font, fill=(255, 255, 255, 255))
            x += w

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--font", default="../../remotion/public/fonts/Archivo.ttf")
    ap.add_argument("--size", type=float, default=0.038, help="cap height as a fraction of frame height")
    ap.add_argument("--weight", type=float, default=800)
    ap.add_argument("--margin", type=float, default=0.09, help="left margin as a fraction of width")
    ap.add_argument("--step", type=float, default=0.055, help="staircase indent per line, fraction of width")
    ap.add_argument("--band-keys", required=True, help="JSON with the band keyframes")
    ap.add_argument("--bug", default=None, help="handle bug PNG, centred in the top bar")
    ap.add_argument("--bug-y", type=float, default=0.155, help="bug top as a fraction of height")
    ap.add_argument("--bug-centre-from", type=int, default=None,
                    help="from this frame the bug sits centred in the band instead of in the top bar")
    ap.add_argument("--accent", default="#FE0F13")
    a = ap.parse_args()

    blocks = json.load(open(a.script))
    font = load_font(a.font, int(a.height * a.size), a.weight)
    keys = json.load(open(a.band_keys))
    bug = Image.open(a.bug).convert("RGBA") if a.bug else None
    if bug:
        bw = int(a.width * 0.30)
        bug = bug.resize((bw, int(bug.height * bw / bug.width)), Image.LANCZOS)
    margin = int(a.width * a.margin)
    step = int(a.width * a.step)
    accent = hex_rgb(a.accent)
    os.makedirs(a.out, exist_ok=True)

    n = int(round(a.seconds * a.fps))
    for i in range(n):
        t = i / a.fps
        img = Image.new("RGBA", (a.width, a.height), (0, 0, 0, 0))
        top, bot = band_at(keys, t, a.height, frame=i)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, a.width, top], fill=(0, 0, 0, 255))
        d.rectangle([0, bot, a.width, a.height], fill=(0, 0, 0, 255))
        if bug:
            centred = a.bug_centre_from is not None and i >= a.bug_centre_from
            by = (top + bot - bug.height) // 2 if centred else int(a.height * a.bug_y)
            img.alpha_composite(bug, ((a.width - bug.width) // 2, by))
        band = (top, bot)
        for blk in blocks:
            words = sum(len(l.split()) for l in blk["lines"])
            if "words_at" in blk:
                # every word has its own frame, measured off a reference edit
                if not (blk["words_at"][0] <= i < blk["until_f"]):
                    continue
                shown = sum(1 for wf in blk["words_at"] if wf <= i)
            else:
                if not (blk["at"] <= t < blk["until"]):
                    continue
                # words land over the first 70% of the block, then the line holds
                build = (blk["until"] - blk["at"]) * 0.7
                shown = words if t >= blk["at"] + build else int(words * (t - blk["at"]) / build) + 1
            draw_block(img, blk, shown, font, a.width, band, margin, step, accent)
        img.save(os.path.join(a.out, f"{i:05d}.png"))
    print(f"{n} frames -> {a.out}")

if __name__ == "__main__":
    main()
