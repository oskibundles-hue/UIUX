"""Studio carousel generator: a 5-slide 4:5 Instagram carousel (1080x1350) in the studio look.

    python3 generate.py <spec.json> <out_dir>                # the spec's variation (studio by default)
    python3 generate.py <spec.json> <out_dir> --variations   # every variation side by side, to pick from

Writes 01.png to 05.png, spread45.png (slides 4 and 5 as one 2160-wide spread; the cutout build only)
and layout.json (every text, part, subject and photo box, for qa.py). Everything brand-specific comes
from the spec; see README.md for its fields and LAYOUT.md for the rules. Needs numpy, Pillow and scipy.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photos import clean_cut, panel, photo, redact  # noqa: E402

W, H = 1080, 1350
MARGIN = 40   # every word and every photo frame stays this far inside the slide (LAYOUT.md)
BACKGROUND = {'soft_fill', 'ghost', 'vertical'}   # type behind everything; may bleed off the frame

# ---- variations: a theme (the colours of the studio and the type behind) and a layout. The light grey
# studio with the default layout is the house default (Omarie, 13 Oct 2026: "one of my new favorites").
THEMES = {
    'studio': {'base': 214, 'falloff': 1.0, 'tint': (1, 1, 1.01), 'soft': (226, 226, 230), 'ghost': (190, 190, 196),
               'fill': (250, 250, 252), 'stroke': (205, 205, 210), 'ink': None, 'shadow': (80, 80, 86)},
    'night': {'base': 64, 'falloff': 0.8, 'tint': (1, 1, 1.04), 'soft': (78, 78, 86), 'ghost': (98, 98, 108),
              'fill': (34, 34, 38), 'stroke': (92, 92, 100), 'ink': (232, 232, 236), 'shadow': (0, 0, 0)},
    'sand': {'base': 214, 'falloff': 1.0, 'tint': (1.03, 0.99, 0.92), 'soft': (232, 224, 210), 'ghost': (196, 184, 166),
             'fill': (250, 246, 238), 'stroke': (210, 198, 180), 'ink': (58, 46, 36), 'shadow': (96, 80, 62)},
}
LAYOUTS = ('default', 'mirror')
VARIATIONS = {  # what --variations renders; the first is the default
    'studio': ('studio', 'default'),
    'studio-mirror': ('studio', 'mirror'),
    'night': ('night', 'default'),
    'sand': ('sand', 'default'),
}


def mirror(layout, width):
    """The same layout flipped left to right, for slides 1 to 3. Photos and renders are placed, never flipped."""
    flip = {'l': 'r', 'r': 'l', 'm': 'm'}
    out = []
    for e in layout:
        e = dict(e)
        if e['type'] == 'steps':  # the grid is centred already
            out.append(e)
            continue
        for k in ('x', 'cx'):
            if k in e:
                e[k] = width - e[k]
        if e['type'] in ('panel', 'rule'):  # placed by their left edge, with no anchor
            e['x'] -= e['w']
            out.append(e)
            continue
        default = 'lb' if e['type'] == 'vertical' else 'lt'
        a = e.get('anchor', default)
        e['anchor'] = flip[a[0]] + a[1]
        if e['type'] == 'part' and e.get('rot'):
            e['rot'] = -e['rot']
        out.append(e)
    return out


# ---- the default layout. Words are {role} keys from spec["words"]; parts and subjects are slot
# names from spec["parts"] and spec["subjects"]. A spec replaces any slide with its own list.
DEFAULT_LAYOUT = {
    '1': [  # cover: giant vertical word, hero part huge, model stacked bottom right
        {'type': 'soft_fill', 'text': '{product}', 'px': 330, 'x': 660, 'y': 330, 'anchor': 'mm', 'alpha': 70},
        {'type': 'ghost', 'text': '{brand}', 'px': 70, 'x': 1030, 'y': 60, 'anchor': 'rt', 'width': 2, 'spacing': 14},
        {'type': 'vertical', 'text': '{cover_word}', 'px': 470, 'x': -62, 'y': 1390},
        {'type': 'part', 'ref': 'hero', 'w': 1000, 'cx': 640, 'cy': 520, 'rot': -4},
        {'type': 'echo', 'text': '{model}', 'px': 170, 'x': 1028, 'y': 1000, 'anchor': 'rt'},
        {'type': 'label', 'text': '{product}', 'px': 46, 'x': 1020, 'y': 1250, 'anchor': 'rt', 'spacing': 9},
    ],
    '2': [  # stacked headline top left, two parts floating, feature list mid left
        {'type': 'soft_fill', 'text': '{brand}', 'px': 520, 'x': 660, 'y': 330, 'anchor': 'mm', 'alpha': 70},
        {'type': 'echo', 'text': '{product}', 'px': 120, 'x': 40, 'y': 150},
        {'type': 'label', 'text': '{subject_name}', 'px': 52, 'x': 44, 'y': 300, 'spacing': 8},
        {'type': 'part', 'ref': 'a', 'w': 560, 'cx': 790, 'cy': 560, 'rot': -6},
        {'type': 'part', 'ref': 'b', 'w': 620, 'cx': 760, 'cy': 1150, 'rot': 8},
        {'type': 'echo', 'text': '{feature_1}', 'px': 96, 'x': 50, 'y': 760},
        {'type': 'label', 'text': '{feature_2}', 'px': 44, 'x': 54, 'y': 880, 'spacing': 8},
        {'type': 'echo', 'text': '{feature_3}', 'px': 64, 'x': 50, 'y': 940},
    ],
    '3': [  # three views of the subject in a row, parts set out above and below
        {'type': 'ghost', 'text': '{brand}', 'px': 64, 'x': 30, 'y': 30, 'width': 2, 'spacing': 14},
        {'type': 'ghost', 'text': '{cover_word}', 'px': 560, 'x': 540, 'y': 675, 'rot': 90, 'anchor': 'mm', 'width': 2},
        {'type': 'part', 'ref': 'flat1', 'box': [900, 260], 'cx': 540, 'cy': 330},
        {'type': 'part', 'ref': 'flat2', 'box': [400, 240], 'cx': 290, 'cy': 1110},
        {'type': 'part', 'ref': 'flat3', 'box': [400, 240], 'cx': 790, 'cy': 1110},
        {'type': 'subject', 'ref': 'side', 'w': 330, 'cx': 190, 'cy': 690},
        {'type': 'subject', 'ref': 'rear', 'w': 260, 'cx': 540, 'cy': 690},
        {'type': 'subject', 'ref': 'three_quarter', 'w': 310, 'cx': 885, 'cy': 690},
        {'type': 'label', 'text': '{subject_name}', 'px': 40, 'x': 540, 'y': 840, 'anchor': 'mt', 'spacing': 10},
    ],
    'spread': [  # slides 4 and 5 as one 2160-wide canvas, the hero view straddling the seam
        {'type': 'soft_fill', 'text': '{brand}', 'px': 900, 'x': 1080, 'y': 640, 'anchor': 'mm', 'alpha': 60},
        {'type': 'part', 'ref': 'flat1', 'w': 560, 'cx': 300, 'cy': 230, 'rot': -15},
        {'type': 'part', 'ref': 'b', 'w': 480, 'cx': 1880, 'cy': 230, 'rot': -25},
        {'type': 'part', 'ref': 'c', 'w': 360, 'cx': 1240, 'cy': 1210},
        {'type': 'label', 'text': '{brand}', 'px': 46, 'x': 1040, 'y': 420, 'anchor': 'rt', 'spacing': 16},
        {'type': 'label', 'text': '{product_word}', 'px': 46, 'x': 1120, 'y': 420, 'anchor': 'lt', 'spacing': 16},
        {'type': 'subject', 'ref': 'front', 'w': 600, 'cx': 380, 'cy': 680},
        {'type': 'subject', 'ref': 'three_quarter', 'w': 600, 'cx': 1800, 'cy': 680},
        {'type': 'subject', 'ref': 'rear', 'w': 600, 'cx': 1080, 'cy': 740},
        {'type': 'echo', 'text': '{subject_name}', 'px': 74, 'x': 50, 'y': 960},
        {'type': 'label', 'text': '{product}', 'px': 40, 'x': 52, 'y': 1060, 'spacing': 7},
        {'type': 'echo', 'text': '{closing_1}', 'px': 58, 'x': 2110, 'y': 960, 'anchor': 'rt'},
        {'type': 'echo', 'text': '{closing_2}', 'px': 58, 'x': 2110, 'y': 1035, 'anchor': 'rt'},
        {'type': 'ghost', 'text': '{brand}', 'px': 110, 'x': 2130, 'y': 1330, 'anchor': 'rb', 'width': 2,
         'spacing': 10},
    ],
}


# ---- the photo build: the same look made from real photos. Framed photo panels stand in for the
# renders, and slide 3 is a 2x2 grid of numbered steps. Five single slides, no spread.
PHOTO_LAYOUT = {
    '1': [  # hook: the vertical word up the side, the subject framed beside it, a part floating over the corner
        {'type': 'vertical', 'text': '{cover_word}', 'px': 300, 'x': 20, 'y': 675, 'anchor': 'lm', 'fit': True},
        {'type': 'panel', 'ref': 'hero', 'x': 300, 'y': 110, 'w': 740, 'h': 600, 'focus': [0.5, 0.55]},
        {'type': 'part', 'ref': 'hero_part', 'w': 400, 'cx': 870, 'cy': 1030, 'rot': -8},
        {'type': 'echo', 'text': '{model}', 'px': 260, 'x': 290, 'y': 839},
        {'type': 'label', 'text': '{job}', 'px': 50, 'x': 300, 'y': 1175, 'spacing': 9},
        {'type': 'label', 'text': '{brand}', 'px': 30, 'x': 302, 'y': 1245, 'colour': 'brand', 'spacing': 8},
    ],
    '2': [  # the part: one large clean cutout and a one-line headline
        {'type': 'soft_fill', 'text': '{model}', 'px': 760, 'x': 680, 'y': 620, 'anchor': 'mm', 'alpha': 70},
        {'type': 'echo', 'text': '{category}', 'px': 120, 'x': 40, 'y': 200},
        {'type': 'label', 'text': '{subject_name}', 'px': 48, 'x': 46, 'y': 330, 'spacing': 8},
        {'type': 'part', 'ref': 'main', 'box': [600, 900], 'cx': 720, 'cy': 790},
        {'type': 'echo', 'text': '{part_line}', 'px': 70, 'x': 40, 'y': 1150},
        {'type': 'label', 'text': '{job}', 'px': 40, 'x': 44, 'y': 1240, 'spacing': 7},
    ],
    '3': [  # the steps: four photos in tidy boxes on a clear 2x2 grid, numbered
        {'type': 'ghost', 'text': '{subject_name}', 'px': 60, 'x': 1020, 'y': 80, 'anchor': 'rt', 'width': 2,
         'spacing': 10},
        {'type': 'echo', 'text': '{steps_title}', 'px': 96, 'x': 60, 'y': 140},
        {'type': 'steps', 'items': [{'ref': 'step1', 'text': '{step_1}'}, {'ref': 'step2', 'text': '{step_2}'},
                                    {'ref': 'step3', 'text': '{step_3}'}, {'ref': 'step4', 'text': '{step_4}'}]},
    ],
    '4': [  # the subject, one large framed photo
        {'type': 'soft_fill', 'text': '{model}', 'px': 760, 'x': 480, 'y': 640, 'anchor': 'mm', 'alpha': 70},
        {'type': 'ghost', 'text': '{category}', 'px': 60, 'x': 50, 'y': 50, 'width': 2, 'spacing': 10},
        {'type': 'panel', 'ref': 'view', 'x': 160, 'y': 140, 'w': 760, 'h': 860},
        {'type': 'label', 'text': '{view_line}', 'px': 46, 'x': 66, 'y': 1060, 'spacing': 12},
        {'type': 'echo', 'text': '{subject_name}', 'px': 110, 'x': 60, 'y': 1170},
    ],
    '5': [  # call to action: the cutout stays clear of the ghost words
        {'type': 'ghost', 'text': '{brand_1}', 'px': 200, 'x': 30, 'y': 90, 'width': 2},
        {'type': 'ghost', 'text': '{brand_2}', 'px': 200, 'x': 30, 'y': 300, 'width': 2},
        {'type': 'part', 'ref': 'closing_part', 'box': [330, 800], 'cx': 875, 'cy': 520},
        {'type': 'echo', 'text': '{cta_1}', 'px': 84, 'x': 50, 'y': 990},
        {'type': 'label', 'text': '{cta_2}', 'px': 40, 'x': 54, 'y': 1095, 'spacing': 5},
        {'type': 'rule', 'x': 54, 'y': 1170, 'w': 120, 'h': 6},
        {'type': 'label', 'text': '{brand}', 'px': 52, 'x': 50, 'y': 1195, 'spacing': 9},
        {'type': 'label', 'text': '{handle}', 'px': 32, 'x': 54, 'y': 1255, 'colour': 'brand', 'spacing': 4},
    ],
}
BUILDS = {'cutout': DEFAULT_LAYOUT, 'photo': PHOTO_LAYOUT}   # spec["build"]; cutout is the default


def rgb(c):
    if isinstance(c, str):
        c = c.lstrip('#')
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(c)


class Carousel:
    def __init__(self, spec_path, variation=None):
        self.root = os.path.dirname(os.path.abspath(spec_path))
        with open(spec_path) as fh:
            self.spec = json.load(fh)
        theme, self.layout = VARIATIONS[variation] if variation else (
            self.spec.get('theme', 'studio'), self.spec.get('layout', 'default'))
        if theme not in THEMES or self.layout not in LAYOUTS:
            raise ValueError(f'unknown theme {theme!r} or layout {self.layout!r}')
        self.build = self.spec.get('build', 'cutout')
        if self.build not in BUILDS:
            raise ValueError(f'unknown build {self.build!r}')
        self.theme = THEMES[theme]
        b = self.spec['brand']
        self.font_path = self.path(b['font'])
        self.colour = rgb(b['colour'])
        # brand ink and ghost are for the plain studio; the other themes bring their own
        self.ink = self.theme['ink'] or rgb(b.get('ink', '#28282C'))
        self.ghost_col = rgb(b['ghost']) if b.get('ghost') and theme == 'studio' else self.theme['ghost']
        self.words = self.spec.get('words', {})
        self._fonts, self._cache = {}, {}

    def path(self, p):
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(self.root, p))

    def font(self, px):
        if px not in self._fonts:
            self._fonts[px] = ImageFont.truetype(self.font_path, px)
        return self._fonts[px]

    def text(self, t):
        return t.format_map(self.words)

    def col(self, c, default):
        """A colour from an element: a hex, an [r, g, b], or the names "brand" and "ink"."""
        named = {'brand': self.colour, 'ink': self.ink}
        return rgb(default) if c is None else named[c] if c in ('brand', 'ink') else rgb(c)

    # ---- backdrop
    def studio(self, w, h):
        """Seamless backdrop: bright centre, darker top and edges, in the theme's tone."""
        t = self.theme
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = ((xx - w / 2) / (w * 0.75)) ** 2 + ((yy - h * 0.5) / (h * 0.8)) ** 2
        v = t['base'] - t['falloff'] * (26 * (yy / h - 0.55) ** 2 * 4 + 30 * np.clip(r, 0, 1.4))
        return Image.fromarray(np.stack([v * c for c in t['tint']], -1).clip(0, 255).astype(np.uint8))

    # ---- type
    def text_layer(self, text, px, fill=None, stroke=0, stroke_col=None, spacing=0):
        f = self.font(px)
        widths = [f.getlength(c) for c in text]
        tw = int(sum(widths) + spacing * (len(text) - 1))
        _, t, _, b = f.getbbox(text)
        lay = Image.new('RGBA', (tw + 40 + stroke * 2, b - t + 40 + stroke * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        x = 20 + stroke
        for c, cw in zip(text, widths):
            d.text((x, 20 + stroke - t), c, font=f, fill=fill if fill else (0, 0, 0, 0),
                   stroke_width=stroke, stroke_fill=stroke_col)
            x += cw + spacing
        return lay

    @staticmethod
    def put(img, lay, x, y, anchor='lt'):
        if anchor[0] == 'm':
            x -= lay.width // 2
        elif anchor[0] == 'r':
            x -= lay.width
        if anchor[1] == 'm':
            y -= lay.height // 2
        elif anchor[1] == 'b':
            y -= lay.height
        x, y = int(x), int(y)
        img.paste(lay, (x, y), lay)
        return x, y

    @staticmethod
    def ink_box(lay, x, y, thresh=100):
        bb = lay.getchannel('A').point(lambda v: 255 if v > thresh else 0).getbbox()
        return [x + bb[0], y + bb[1], x + bb[2], y + bb[3]] if bb else None

    def draw_text(self, img, e):
        kind, text, px = e['type'], self.text(e['text']), e['px']
        anchor, sp = e.get('anchor', 'lt'), e.get('spacing', 0)
        if kind == 'soft_fill':  # big faint filled word behind everything
            col = rgb(e.get('colour', self.theme['soft']))
            lay = self.text_layer(text, px, fill=col + (e.get('alpha', 150),), spacing=sp)
            lay = lay.filter(ImageFilter.GaussianBlur(1.5))
            x, y = self.put(img, lay, e['x'], e['y'], anchor)
            box = self.ink_box(lay, x, y, 20)
        elif kind == 'ghost':  # outline only
            col = rgb(e.get('colour', self.ghost_col))
            lay = self.text_layer(text, px, stroke=e.get('width', 3), stroke_col=col + (255,), spacing=sp)
            if e.get('rot'):
                lay = lay.rotate(e['rot'], expand=True)
            x, y = self.put(img, lay, e['x'], e['y'], anchor)
            box = self.ink_box(lay, x, y)
        elif kind == 'vertical':  # the cover's huge vertical word; x, y is its bottom-left corner
            lay = self.text_layer(text, px, fill=rgb(e.get('fill', self.theme['fill'])) + (255,), stroke=3,
                                  stroke_col=rgb(e.get('stroke', self.theme['stroke'])) + (255,), spacing=sp)
            lay = lay.rotate(90, expand=True)
            if e.get('fit') and lay.height > H - 2 * MARGIN + 40:  # the layer has 20 px of padding each end
                s = (H - 2 * MARGIN + 40) / lay.height
                lay = lay.resize((int(lay.width * s), int(lay.height * s)), Image.LANCZOS)
            x, y = self.put(img, lay, e['x'], e['y'], e.get('anchor', 'lb'))
            box = self.ink_box(lay, x, y)
        elif kind == 'echo':  # solid line in the brand colour with a blurred echo above and right
            col = self.col(e.get('colour'), self.colour)
            sp = e.get('spacing', 2)
            base = self.text_layer(text, px, fill=col + (255,), spacing=sp)
            off = int(px * 0.42)
            pad = Image.new('RGBA', (base.width + 60, base.height + int(px * 0.9)), (0, 0, 0, 0))
            for dx, dy, a, bl in [(int(px * .45), 0, 38, 7), (int(px * .22), int(px * .2), 75, 3)]:
                ech = self.text_layer(text, px, fill=col + (a,), spacing=sp).filter(ImageFilter.GaussianBlur(bl))
                pad.alpha_composite(ech, (dx, dy))
            pad.alpha_composite(base, (0, off))
            y0 = e['y'] - off if anchor[1] == 't' else e['y']
            x, y = self.put(img, pad, e['x'], y0, anchor)
            box = self.ink_box(base, x, y + off)
            echo_box = self.ink_box(pad, x, y, 10)   # the headline with its blurred echo
        elif kind == 'label':
            col = self.col(e.get('colour'), self.ink)
            lay = self.text_layer(text, px, fill=col + (255,), spacing=e.get('spacing', 5))
            x, y = self.put(img, lay, e['x'], e['y'], anchor)
            box = self.ink_box(lay, x, y)
        else:
            raise ValueError(f'unknown element type {kind!r}')
        rec = {'kind': 'text', 'type': kind, 'text': text, 'box': box,
               'layer': 'background' if kind in BACKGROUND else 'foreground',
               'bleed': e.get('bleed', kind in BACKGROUND)}
        if kind == 'echo':
            rec['echo_box'] = echo_box
        return rec

    # ---- parts: product photos cut out with rembg beforehand, never recoloured
    def part(self, ref):
        if ref in self._cache:
            return self._cache[ref]
        src = self.spec['parts'][ref]
        src = {'file': src} if isinstance(src, str) else src
        im = Image.open(self.path(src['file'])).convert('RGBA')
        if src.get('clean') is not None:  # a rough rembg cutout: keep the largest piece, trim and fade it
            im = clean_cut(im, **src['clean'])
        elif src.get('split'):  # one photo of several pieces: take one piece, largest first
            pieces = self.pieces(im, src.get('open', 0))
            im = pieces[src.get('piece', 0)]
        else:
            a = im.getchannel('A').point(lambda v: 0 if v < 40 else v)
            im.putalpha(a)
            im = im.crop(a.getbbox())
        self._cache[ref] = im
        return im

    @staticmethod
    def pieces(im, open_it=0):
        a = np.array(im.getchannel('A'))
        mask = a > 60
        if open_it:
            mask = ndimage.binary_opening(mask, iterations=open_it)
        lab, k = ndimage.label(mask)
        out = []
        for i in range(1, k + 1):
            m = lab == i
            if m.sum() < 2000:
                continue
            ys, xs = np.where(m)
            box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
            piece = im.crop(box)
            keep = (m[box[1]:box[3], box[0]:box[2]] * 255).astype(np.uint8)
            piece.putalpha(Image.fromarray(np.minimum(np.array(piece.getchannel('A')), keep)))
            out.append((m.sum(), piece))
        return [p for _, p in sorted(out, key=lambda t: -t[0])]

    def draw_part(self, img, e):
        p = self.part(e['ref'])
        if e.get('rot'):
            p = p.rotate(e['rot'], expand=True, resample=Image.BICUBIC)
            p = p.crop(p.getchannel('A').getbbox())
        if 'box' in e:  # fit inside a box instead of a set width
            bw, bh = e['box']
            w = p.width * min(bw / p.width, bh / p.height)
        else:
            w = e['w']
        s = w / p.width
        p = p.resize((max(1, int(p.width * s)), max(1, int(p.height * s))), Image.LANCZOS)
        x, y = int(e['cx'] - p.width / 2), int(e['cy'] - p.height / 2)
        if e.get('shadow', True):  # soft floor shadow
            sh = Image.new('L', img.size, 0)
            sh.paste(p.getchannel('A').point(lambda v: 70 if v > 120 else 0), (x + 14, y + 40))
            sh = sh.filter(ImageFilter.GaussianBlur(30))
            img.paste(Image.new('RGB', img.size, self.theme['shadow']), (0, 0), sh)
        img.paste(p, (x, y), p)
        mask = np.zeros((img.height, img.width), bool)
        a = np.array(p.getchannel('A')) > 128
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(img.width, x + p.width), min(img.height, y + p.height)
        mask[y0:y1, x0:x1] = a[y0 - y:y1 - y, x0 - x:x1 - x]
        return {'kind': 'part', 'ref': e['ref'], 'box': self.mask_box(mask), 'mask': mask}

    # ---- subjects: studio renders blended in by a soft mask, never a hard cutout
    def subject_layer(self, ref):
        if ref in self._cache:
            return self._cache[ref]
        a = np.array(Image.open(self.path(self.spec['subjects'][ref])).convert('RGB')).astype(np.float32)
        h, w, _ = a.shape
        bgrow = np.median(np.concatenate([a[:, :12], a[:, -12:]], 1), 1)  # studio tone per row
        dist = np.abs(a - bgrow[:, None, :]).max(-1)
        m = ndimage.gaussian_filter(np.clip((dist - 7) / 28, 0, 1), 1.2)
        ys, xs = np.where(m > 0.5)
        pad = 30
        box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(w, xs.max() + pad), min(h, ys.max() + pad))
        lay = Image.fromarray(np.dstack([a, m * 255]).clip(0, 255).astype(np.uint8), 'RGBA').crop(box)
        self._cache[ref] = lay
        return lay

    def draw_subject(self, img, e):
        lay = self.subject_layer(e['ref'])
        if e.get('crop'):
            lay = lay.crop(tuple(e['crop']))
        s = e['w'] / lay.width
        lay = lay.resize((int(lay.width * s), int(lay.height * s)), Image.LANCZOS)
        x, y = int(e['cx'] - lay.width / 2), int(e['cy'] - lay.height / 2)
        sh = Image.new('L', img.size, 0)  # soft floor shadow under the subject
        ImageDraw.Draw(sh).ellipse([x + lay.width * .08, y + lay.height * .80,
                                    x + lay.width * .92, y + lay.height * 1.02], fill=110)
        sh = sh.filter(ImageFilter.GaussianBlur(max(8, lay.width // 25)))
        img.paste(Image.new('RGB', img.size, self.theme['shadow']), (0, 0), sh)
        img.paste(lay.convert('RGB'), (x, y), lay.getchannel('A'))
        bb = lay.getchannel('A').point(lambda v: 255 if v > 128 else 0).getbbox()
        return {'kind': 'subject', 'ref': e['ref'], 'box': [x + bb[0], y + bb[1], x + bb[2], y + bb[3]]}

    # ---- photos: real photos, framed. Plates are covered before anything is cropped
    def photo_pic(self, ref):
        key = ('photo', ref)
        if key not in self._cache:
            src = self.spec['photos'][ref]
            src = {'file': src} if isinstance(src, str) else src
            im = photo(self.path(src['file']))
            for box in src.get('redact') or []:
                im = redact(im, box)
            if src.get('crop'):  # crop every face out here
                im = im.crop(tuple(src['crop']))
            self._cache[key] = im
        return self._cache[key]

    def draw_panel(self, img, e):
        x, y, w, h = e['x'], e['y'], e['w'], e['h']
        frame = panel(img, self.photo_pic(e['ref']), x, y, w, h, tuple(e.get('focus', (0.5, 0.5))),
                      e.get('shadow', True), self.theme['shadow'])
        return {'kind': 'panel', 'ref': e['ref'], 'box': [x, y, x + w, y + h], 'frame': frame}

    def draw_steps(self, img, e):
        """A 2x2 grid of framed photos, each with its number in the brand colour and a short label."""
        bw, bh = e.get('box', (450, 420))
        inset, px = e.get('inset', 60), e.get('px', 38)
        cols, rows = [inset, img.width - inset - bw], e.get('rows', (290, 800))
        recs = []
        for i, item in enumerate(e['items'][:4]):
            x, y = cols[i % 2], rows[i // 2]
            recs.append(self.draw_panel(img, {'ref': item['ref'], 'x': x, 'y': y, 'w': bw, 'h': bh,
                                              'focus': item.get('focus', (0.5, 0.5))}))
            num = self.draw_text(img, {'type': 'label', 'text': item.get('num', f'{i + 1:02d}'), 'px': px,
                                       'x': x - 2, 'y': y + bh + 22, 'colour': 'brand', 'spacing': 4})
            words = self.draw_text(img, {'type': 'label', 'text': item['text'], 'px': px,
                                         'x': num['box'][2] - 4, 'y': y + bh + 22, 'spacing': 6})
            recs += [num, words]
        return recs

    def draw_rule(self, img, e):
        box = [e['x'], e['y'], e['x'] + e['w'], e['y'] + e['h']]
        ImageDraw.Draw(img).rectangle([box[0], box[1], box[2] - 1, box[3] - 1],
                                      fill=self.col(e.get('colour'), self.colour))
        return {'kind': 'rule', 'box': box}

    @staticmethod
    def mask_box(mask):
        ys, xs = np.where(mask)
        return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None

    # ---- slides
    def canvas(self, key, width):
        img = self.studio(width, H)
        layout = self.spec.get('slides', {}).get(key) or BUILDS[self.build][key]
        if self.layout == 'mirror' and key != 'spread':  # the spread keeps its order, so it reads across the swipe
            layout = mirror(layout, width)
        recs = []
        for e in layout:
            if e['type'] == 'part':
                recs.append(self.draw_part(img, e))
            elif e['type'] == 'subject':
                recs.append(self.draw_subject(img, e))
            elif e['type'] == 'panel':
                recs.append(self.draw_panel(img, e))
            elif e['type'] == 'steps':
                recs += self.draw_steps(img, e)
            elif e['type'] == 'rule':
                recs.append(self.draw_rule(img, e))
            else:
                recs.append(self.draw_text(img, e))
        return img, recs

    def render(self, out):
        os.makedirs(out, exist_ok=True)
        canvases = {}
        for k in (k for k in '12345' if k in BUILDS[self.build]):
            img, recs = self.canvas(k, W)
            img.save(f'{out}/0{k}.png')
            canvases[k] = {'size': [W, H], 'files': [f'0{k}.png'], 'records': recs}
        if 'spread' in BUILDS[self.build]:
            img, recs = self.canvas('spread', 2 * W)
            img.crop((0, 0, W, H)).save(f'{out}/04.png')
            img.crop((W, 0, 2 * W, H)).save(f'{out}/05.png')
            img.save(f'{out}/spread45.png')
            canvases['spread'] = {'size': [2 * W, H], 'files': ['04.png', '05.png'], 'records': recs}
        with open(f'{out}/layout.json', 'w') as fh:
            json.dump({k: {**c, 'records': [{a: b for a, b in r.items() if a != 'mask'} for r in c['records']]}
                       for k, c in canvases.items()}, fh, indent=1)
        return canvases


def render_variations(spec_path, out):
    """Every variation in its own folder, plus variations.jpg: one row per variation, to pick from."""
    rows = []
    for name in VARIATIONS:
        Carousel(spec_path, name).render(f'{out}/{name}')
        rows.append(name)
    tw, th, lab = 300, 375, 34
    sheet = Image.new('RGB', (5 * tw, len(rows) * (th + lab)), 'white')
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(rows):
        d.text((8, i * (th + lab) + 10), name + ('  (default)' if i == 0 else ''), fill='black')
        for j in range(5):
            im = Image.open(f'{out}/{name}/0{j + 1}.png').convert('RGB').resize((tw, th), Image.LANCZOS)
            sheet.paste(im, (j * tw, i * (th + lab) + lab))
    sheet.save(f'{out}/variations.jpg', quality=88)
    return rows


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--variations']
    if len(args) != 2:
        sys.exit(__doc__)
    if '--variations' in sys.argv:
        print('ok', render_variations(*args), f'{args[1]}/variations.jpg')
    else:
        Carousel(args[0]).render(args[1])
        print('ok', sorted(f for f in os.listdir(args[1]) if f.endswith('.png')))
