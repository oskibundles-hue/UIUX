"""Check a studio carousel before it goes to nq-check.

    python3 qa.py                    # renders sample/spec.json into the scratch dir below
    python3 qa.py <spec.json> [out]  # renders that spec
    add --variations to render and check every variation (generate.py --variations)

Prints one line per failure and exits 1 on any, or prints `all clear`. It fails on:
  - a slide that isn't 1080x1350 (or a spread that isn't 2160x1350);
  - foreground text crossing a frame edge (the spread's seam counts), unless the element has "bleed": true;
  - foreground text whose box covers a part's opaque pixels by more than OVERLAP of the box;
  - a part's alpha box within GAP px of a subject's alpha box;
  - any word on a slide that isn't on the spec's allowed_words.
"""
import json
import os
import re
import sys
import tempfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import H, VARIATIONS, W, Carousel  # noqa: E402

OVERLAP = 0.02   # share of a text box that may sit on a part's opaque pixels
GAP = 30         # px between a part's alpha box and a subject's


def words_of(text):
    return re.findall(r"[A-Z0-9][A-Z0-9'&-]*", text.upper())


def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return max(dx, dy) if (dx == 0 or dy == 0) else (dx * dx + dy * dy) ** 0.5


def check(spec_path, out, variation=None):
    car = Carousel(spec_path, variation)
    canvases = car.render(out)
    allowed = {w.upper() for w in car.spec.get('allowed_words', [])}
    fails = []
    for f in ('01.png', '02.png', '03.png', '04.png', '05.png'):
        size = Image.open(os.path.join(out, f)).size
        if size != (W, H):
            fails.append(f'{f}: is {size[0]}x{size[1]}, not {W}x{H}')
    size = Image.open(os.path.join(out, 'spread45.png')).size
    if size != (2 * W, H):
        fails.append(f'spread45.png: is {size[0]}x{size[1]}, not {2 * W}x{H}')

    for key, c in canvases.items():
        name = f'slide {key}' if key != 'spread' else 'spread 4-5'
        recs = c['records']
        texts = [r for r in recs if r['kind'] == 'text' and r['box']]
        parts = [r for r in recs if r['kind'] == 'part' and r['box']]
        subjects = [r for r in recs if r['kind'] == 'subject']
        for t in texts:
            x0, y0, x1, y1 = t['box']
            for w in words_of(t['text']):
                if w not in allowed:
                    fails.append(f'{name}: "{w}" in "{t["text"]}" is not on allowed_words')
            if t['layer'] != 'foreground':
                continue
            if not t['bleed']:
                seam = key == 'spread' and x0 < W < x1
                if seam or x0 < 0 or y0 < 0 or x1 > c['size'][0] or y1 > H:
                    where = 'the seam between slides 4 and 5' if seam else 'the frame edge'
                    fails.append(f'{name}: "{t["text"]}" crosses {where} at {t["box"]}')
            area = max(1, (x1 - x0) * (y1 - y0))
            cx0, cy0 = max(0, x0), max(0, y0)
            for p in parts:
                hit = int(p['mask'][cy0:max(cy0, y1), cx0:max(cx0, x1)].sum())
                if hit / area > OVERLAP:
                    fails.append(f'{name}: "{t["text"]}" sits on part {p["ref"]} ({hit / area:.1%} of its box)')
        for p in parts:
            for s in subjects:
                g = gap(p['box'], s['box'])
                if g < GAP:
                    fails.append(f'{name}: part {p["ref"]} is {g:.0f}px from subject {s["ref"]} (needs {GAP})')
    return fails


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    args = [a for a in sys.argv[1:] if a != '--variations']
    spec = args[0] if args else os.path.join(here, 'sample', 'spec.json')
    out = args[1] if len(args) > 1 else os.path.join(tempfile.gettempdir(), 'studio-carousel-qa')
    if '--variations' in sys.argv:
        fails = [f'{v}: {f}' for v in VARIATIONS for f in check(spec, os.path.join(out, v), v)]
    else:
        fails = check(spec, out)
    for f in fails:
        print('FAIL', f)
    print(f'{len(fails)} failure(s); slides in {out}' if fails else f'all clear; slides in {out}')
    sys.exit(1 if fails else 0)
