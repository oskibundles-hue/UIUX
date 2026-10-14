"""Check a studio carousel before it goes to nq-check.

    python3 qa.py                    # renders and checks both samples (sample/spec.json, sample/photo_spec.json)
    python3 qa.py <spec.json> [out]  # renders and checks that spec
    python3 qa.py --selftest         # renders sample/broken_spec.json and confirms every check below fires
    add --variations to render and check every variation (generate.py --variations)

Prints one line per failure and exits 1 on any, or prints `all clear`. It fails on:
  - a slide that isn't 1080x1350 (or a spread that isn't 2160x1350);
  - foreground text crossing a frame edge (the spread's seam counts), unless the element has "bleed": true;
  - foreground text or a photo frame closer than MARGIN px to any edge of its slide;
  - foreground text on the cover (slide 1) closer than GRID_SAFE px to a side, because the profile grid
    crops the cover from 4:5 to 3:4;
  - a headline's blurred echo touching a photo frame or the canvas edge;
  - foreground text whose box covers a part's opaque pixels by more than OVERLAP of the box;
  - a part's alpha box within GAP px of a subject's alpha box;
  - a photo in the spec with no "redact" list (the plate boxes, [] when it has none);
  - any word on a slide that isn't on the spec's allowed_words.
The rules behind these are in LAYOUT.md.
"""
import os
import re
import sys
import tempfile

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import H, MARGIN, VARIATIONS, W, Carousel  # noqa: E402

OVERLAP = 0.02            # share of a text box that may sit on a part's opaque pixels
GAP = 30                  # px between a part's alpha box and a subject's
GRID_SAFE = MARGIN + 40   # px from each side for the cover's words: the grid's 3:4 crop takes about 34

# what --selftest must see from sample/broken_spec.json, one per check
EXPECTED = ('is 540x675, not', 'spread45.png: is', 'crosses the frame edge', 'crosses the seam',
            'from the edge of its slide', 'photo frame shot is', 'the profile grid crops the cover',
            'echo touches the frame of photo', 'echo runs off the canvas', 'sits on part', 'from subject',
            'has no "redact" list', 'is not on allowed_words')


def words_of(text):
    return re.findall(r"[A-Z0-9][A-Z0-9'&-]*", text.upper())


def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return max(dx, dy) if (dx == 0 or dy == 0) else (dx * dx + dy * dy) ** 0.5


def inset(box):
    """How far a box sits inside its own slide: (the smallest distance to a side, to any edge)."""
    x0, y0, x1, y1 = box
    off = W * int(((x0 + x1) / 2) // W)   # the spread is two slides side by side
    side = min(x0 - off, off + W - x1)
    return side, min(side, y0, H - y1)


def touches(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def inspect(car, canvases, out):
    allowed = {w.upper() for w in car.spec.get('allowed_words', [])}
    fails = []
    for f in sorted(f for c in canvases.values() for f in c['files']):
        size = Image.open(os.path.join(out, f)).size
        if size != (W, H):
            fails.append(f'{f}: is {size[0]}x{size[1]}, not {W}x{H}')
    if 'spread' in canvases:
        size = Image.open(os.path.join(out, 'spread45.png')).size
        if size != (2 * W, H):
            fails.append(f'spread45.png: is {size[0]}x{size[1]}, not {2 * W}x{H}')
    for ref, src in car.spec.get('photos', {}).items():
        if not isinstance(src, dict) or not isinstance(src.get('redact'), list):
            fails.append(f'photo {ref}: has no "redact" list. Look for plates and faces, then list the plate '
                         f'boxes ([] when there are none) and crop any face out')

    for key, c in canvases.items():
        name = f'slide {key}' if key != 'spread' else 'spread 4-5'
        recs = c['records']
        texts = [r for r in recs if r['kind'] == 'text' and r['box']]
        parts = [r for r in recs if r['kind'] == 'part' and r['box']]
        subjects = [r for r in recs if r['kind'] == 'subject']
        panels = [r for r in recs if r['kind'] == 'panel']
        for p in panels:
            if inset(p['box'])[1] < MARGIN:
                fails.append(f'{name}: photo frame {p["ref"]} is {inset(p["box"])[1]}px from the edge of its slide '
                             f'(needs {MARGIN})')
        for t in texts:
            x0, y0, x1, y1 = t['box']
            for w in words_of(t['text']):
                if w not in allowed:
                    fails.append(f'{name}: "{w}" in "{t["text"]}" is not on allowed_words')
            if t['layer'] != 'foreground':
                continue
            if not t['bleed']:
                seam = key == 'spread' and x0 < W < x1
                side, edge = inset(t['box'])
                if seam or x0 < 0 or y0 < 0 or x1 > c['size'][0] or y1 > H:
                    where = 'the seam between slides 4 and 5' if seam else 'the frame edge'
                    fails.append(f'{name}: "{t["text"]}" crosses {where} at {t["box"]}')
                elif edge < MARGIN:
                    fails.append(f'{name}: "{t["text"]}" is {edge}px from the edge of its slide (needs {MARGIN})')
                elif key == '1' and side < GRID_SAFE:
                    fails.append(f'{name}: "{t["text"]}" is {side}px from the side; the profile grid crops the cover '
                                 f'to 3:4, so its words need {GRID_SAFE}')
            if t.get('echo_box'):
                e = t['echo_box']
                for p in panels:
                    if touches(e, p['frame']):
                        fails.append(f'{name}: "{t["text"]}" echo touches the frame of photo {p["ref"]}')
                if not t['bleed'] and (e[0] <= 0 or e[1] <= 0 or e[2] >= c['size'][0] or e[3] >= H):
                    fails.append(f'{name}: "{t["text"]}" echo runs off the canvas at {e}')
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


def check(spec_path, out, variation=None):
    car = Carousel(spec_path, variation)
    return inspect(car, car.render(out), out)


def selftest(spec_path, out):
    """Render the broken spec, shrink two files on disk, and name any check that stays quiet."""
    car = Carousel(spec_path)
    canvases = car.render(out)
    for f in ('01.png', 'spread45.png'):   # a wrong size can't come from a spec, so make one
        im = Image.open(os.path.join(out, f))
        im.resize((im.width // 2, im.height // 2)).save(os.path.join(out, f))
    fails = inspect(car, canvases, out)
    for f in fails:
        print('fired', f)
    quiet = [e for e in EXPECTED if not any(e in f for f in fails)]
    for e in quiet:
        print('QUIET', e)
    print(f'{len(EXPECTED) - len(quiet)} of {len(EXPECTED)} checks fired on the broken spec')
    return 1 if quiet else 0


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    flags = {'--variations', '--selftest'}
    args = [a for a in sys.argv[1:] if a not in flags]
    tmp = os.path.join(tempfile.gettempdir(), 'studio-carousel-qa')
    if '--selftest' in sys.argv:
        sys.exit(selftest(os.path.join(here, 'sample', 'broken_spec.json'), tmp + '-broken'))
    jobs = [(args[0], args[1] if len(args) > 1 else tmp)] if args else [
        (os.path.join(here, 'sample', 'spec.json'), tmp), (os.path.join(here, 'sample', 'photo_spec.json'), tmp + '-photo')]
    fails = []
    for spec, out in jobs:
        tag = f'{os.path.basename(spec)}: ' if len(jobs) > 1 else ''
        if '--variations' in sys.argv:
            fails += [f'{tag}{v}: {f}' for v in VARIATIONS for f in check(spec, os.path.join(out, v), v)]
        else:
            fails += [tag + f for f in check(spec, out)]
    for f in fails:
        print('FAIL', f)
    where = ' and '.join(out for _, out in jobs)
    print(f'{len(fails)} failure(s); slides in {where}' if fails else f'all clear; slides in {where}')
    sys.exit(1 if fails else 0)
