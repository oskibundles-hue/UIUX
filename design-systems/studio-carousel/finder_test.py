"""Measure how often finder.py misses a plate, on drawn plates only.

    python3 finder_test.py [how many, default 240] [--sheet misses.jpg]

It draws dummy plates of known position on drawn scenes (near and far, light and dark, tilted, soft,
dim, noisy), runs the finder, and counts a plate as found only when a cover box hides at least 90% of
its characters. A third as many scenes again carry no plate, to count false covers. Drawn plates are
easier than real ones, so the real miss rate is higher than this prints: it is a floor, not a promise.
"""
import os
import random
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finder  # noqa: E402
from engine import PAD  # noqa: E402

FONTS = ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
FONT = next(f for f in FONTS if os.path.exists(f))
SIZES = (('near (plate over 12% of the width)', 0.12, 0.28), ('middle (5 to 12%)', 0.05, 0.12),
         ('far (2 to 5%)', 0.02, 0.05))


def scene(rng, w=1600, h=1200):
    """A drawn shop scene: a floor, a wall, a car-like body and some clutter."""
    yy = np.mgrid[0:h, 0:w][0] / h
    base = rng.randint(70, 200)
    im = Image.fromarray(np.stack([base - 40 * yy + rng.randint(-8, 8)] * 3, -1).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for _ in range(rng.randint(4, 10)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        v = rng.randint(20, 235)
        d.rounded_rectangle([x, y, x + rng.randint(40, 500), y + rng.randint(30, 400)], rng.randint(0, 60),
                            fill=(v, v + rng.randint(-20, 20), v + rng.randint(-20, 20)))
    for _ in range(rng.randint(0, 6)):   # wheel-like and lamp-like shapes
        x, y, r = rng.randint(0, w), rng.randint(0, h), rng.randint(20, 160)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(rng.randint(0, 255),) * 3)
    return im


def add_plate(im, rng, lo, hi):
    """Paste one dummy plate; returns the box round its characters, in the photo's pixels."""
    pw = int(im.width * rng.uniform(lo, hi))
    ph = int(pw * rng.uniform(0.42, 0.55))
    light = rng.random() < 0.75
    ground = rng.randint(190, 250) if light else rng.randint(15, 60)
    ink = rng.randint(10, 70) if light else rng.randint(200, 250)
    big = Image.new('RGBA', (pw * 4, ph * 4), (ground, ground, ground - rng.randint(0, 25) * light, 255))
    d = ImageDraw.Draw(big)
    text = ''.join(rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ0123456789') for _ in range(rng.randint(5, 8)))
    font = ImageFont.truetype(FONT, int(ph * 4 * rng.uniform(0.5, 0.62)))
    tb = d.textbbox((pw * 2, ph * 2), text, font=font, anchor='mm')
    if tb[2] - tb[0] > pw * 4 * 0.9:
        font = ImageFont.truetype(FONT, int(font.size * pw * 4 * 0.9 / (tb[2] - tb[0])))
        tb = d.textbbox((pw * 2, ph * 2), text, font=font, anchor='mm')
    d.text((pw * 2, ph * 2), text, font=font, fill=(ink, ink, ink, 255), anchor='mm')
    marks = Image.new('L', big.size, 0)
    ImageDraw.Draw(marks).rectangle(tb, fill=255)
    angle = rng.uniform(-10, 10)
    big = big.resize((pw, ph), Image.LANCZOS).rotate(angle, expand=True, resample=Image.BICUBIC)
    marks = marks.resize((pw, ph), Image.LANCZOS).rotate(angle, expand=True)
    x, y = rng.randint(10, im.width - big.width - 10), rng.randint(10, im.height - big.height - 10)
    im.paste(big, (x, y), big)
    bb = marks.point(lambda v: 255 if v > 128 else 0).getbbox()
    return [x + bb[0], y + bb[1], x + bb[2], y + bb[3]]


def finish(im, rng):
    """What a phone does to it: a little blur, dimmer or brighter, noise, JPEG."""
    im = im.filter(ImageFilter.GaussianBlur(rng.uniform(0, 1.6)))
    a = np.array(im).astype(np.float32) * rng.uniform(0.55, 1.15) + np.random.RandomState(rng.randint(0, 9999)).normal(
        0, rng.uniform(0, 7), (im.height, im.width, 1))
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def hidden(truth, covers):
    """Share of the characters' box that the cover boxes hide."""
    x0, y0, x1, y1 = truth
    m = np.zeros((y1 - y0, x1 - x0), bool)
    for c in covers:
        m[max(0, c[1] - y0):max(0, c[3] - y0), max(0, c[0] - x0):max(0, c[2] - x0)] = True
    return float(m.mean())


def covers_of(found):
    out = []
    for p in found['plates']:
        x0, y0, x1, y1 = p['box']
        gx, gy = (x1 - x0) * PAD, (y1 - y0) * PAD
        out.append([int(x0 - gx), int(y0 - gy), int(x1 + gx), int(y1 + gy)])
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    sheet = args.pop(args.index('--sheet') + 1) if '--sheet' in args else None
    nums = [a for a in args if a.isdigit()]
    n = int(nums[0]) if nums else 240
    rng = random.Random(13)
    tmp = tempfile.mkdtemp(prefix='finder-test-')
    path = os.path.join(tmp, 'p.jpg')
    total, missed, missed_tiles = {}, {}, []
    for i in range(n):
        name, lo, hi = SIZES[i % len(SIZES)]
        im = scene(rng)
        truth = add_plate(im, rng, lo, hi)
        finish(im, rng).save(path, quality=rng.randint(70, 92))
        found = finder.find(path)
        total[name] = total.get(name, 0) + 1
        if hidden(truth, covers_of(found)) < 0.9:
            missed[name] = missed.get(name, 0) + 1
            if sheet and len(missed_tiles) < 20:
                missed_tiles.append(finder.draw(path, found, 400))
    false = sure = clean = 0
    for i in range(n // 3):
        finish(scene(rng), rng).save(path, quality=85)
        plates = finder.find_plates(np.array(finder.photo(path)))
        false += len(plates) > 0
        sure += any(p['sure'] for p in plates)
        clean += 1
    for name, _, _ in SIZES:
        print(f'{name}: missed {missed.get(name, 0)} of {total[name]}')
    m = sum(missed.values())
    print(f'drawn plates missed: {m} of {n} ({100 * m / n:.0f}%)')
    print(f'scenes with no plate where it covered something anyway: {false} of {clean} ({sure} without a flag)')
    if sheet and missed_tiles:
        out = Image.new('RGB', (5 * 410, ((len(missed_tiles) + 4) // 5) * 310), 'white')
        for i, t in enumerate(missed_tiles):
            out.paste(t, ((i % 5) * 410 + 5, (i // 5) * 310 + 5))
        out.save(sheet, quality=85)
        print(sheet)
