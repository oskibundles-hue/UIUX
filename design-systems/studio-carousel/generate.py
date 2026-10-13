"""Studio carousel generator: a 5-slide 4:5 Instagram carousel (1080x1350) in the studio look.

    python3 generate.py <spec.json> <out_dir>

Writes 01.png to 05.png, spread45.png (slides 4 and 5 as one 2160-wide spread) and layout.json
(every text, part and subject box, for qa.py). Everything brand-specific comes from the spec;
see README.md for its fields. Needs numpy, Pillow and scipy.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

W, H = 1080, 1350
BACKGROUND = {'soft_fill', 'ghost', 'vertical'}   # type behind everything; may bleed off the frame

# ---- the default layout. Words are {role} keys from spec["words"]; parts and subjects are slot
# names from spec["parts"] and spec["subjects"]. A spec replaces any slide with its own list.
DEFAULT_LAYOUT = {
    '1': [  # cover: giant vertical word, hero part huge, model stacked bottom right
        {'type': 'soft_fill', 'text': '{product}', 'px': 330, 'x': 660, 'y': 330, 'anchor': 'mm', 'alpha': 70},
        {'type': 'ghost', 'text': '{brand}', 'px': 70, 'x': 1030, 'y': 60, 'anchor': 'rt', 'width': 2, 'spacing': 14,
         'colour': [196, 196, 200]},
        {'type': 'vertical', 'text': '{cover_word}', 'px': 470, 'x': -62, 'y': 1390},
        {'type': 'part', 'ref': 'hero', 'w': 1000, 'cx': 640, 'cy': 520, 'rot': -4},
        {'type': 'echo', 'text': '{model}', 'px': 170, 'x': 1040, 'y': 1000, 'anchor': 'rt'},
        {'type': 'label', 'text': '{product}', 'px': 46, 'x': 1034, 'y': 1250, 'anchor': 'rt', 'spacing': 9},
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
        {'type': 'ghost', 'text': '{brand}', 'px': 64, 'x': 30, 'y': 30, 'width': 2, 'spacing': 14,
         'colour': [190, 190, 196]},
        {'type': 'ghost', 'text': '{cover_word}', 'px': 560, 'x': 540, 'y': 675, 'rot': 90, 'anchor': 'mm', 'width': 2,
         'colour': [204, 204, 210]},
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
         'spacing': 10, 'colour': [200, 200, 206]},
    ],
}


def rgb(c):
    if isinstance(c, str):
        c = c.lstrip('#')
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(c)


class Carousel:
    def __init__(self, spec_path):
        self.root = os.path.dirname(os.path.abspath(spec_path))
        with open(spec_path) as fh:
            self.spec = json.load(fh)
        b = self.spec['brand']
        self.font_path = self.path(b['font'])
        self.colour = rgb(b['colour'])
        self.ink = rgb(b.get('ink', '#28282C'))
        self.ghost_col = rgb(b.get('ghost', '#B0B0B6'))
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

    # ---- backdrop
    @staticmethod
    def studio(w, h):
        """Light grey seamless, bright centre, darker top and edges."""
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        base = 214 - 26 * (yy / h - 0.55) ** 2 * 4
        r = ((xx - w / 2) / (w * 0.75)) ** 2 + ((yy - h * 0.5) / (h * 0.8)) ** 2
        v = base - 30 * np.clip(r, 0, 1.4)
        return Image.fromarray(np.stack([v, v, v + 2], -1).clip(0, 255).astype(np.uint8))

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
            col = rgb(e.get('colour', [226, 226, 230]))
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
            lay = self.text_layer(text, px, fill=rgb(e.get('fill', [250, 250, 252])) + (255,), stroke=3,
                                  stroke_col=rgb(e.get('stroke', [205, 205, 210])) + (255,), spacing=sp)
            lay = lay.rotate(90, expand=True)
            x, y = self.put(img, lay, e['x'], e['y'], 'lb')
            box = self.ink_box(lay, x, y)
        elif kind == 'echo':  # solid line in the brand colour with a blurred echo above and right
            col = rgb(e.get('colour', self.colour))
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
        elif kind == 'label':
            col = rgb(e.get('colour', self.ink))
            lay = self.text_layer(text, px, fill=col + (255,), spacing=e.get('spacing', 5))
            x, y = self.put(img, lay, e['x'], e['y'], anchor)
            box = self.ink_box(lay, x, y)
        else:
            raise ValueError(f'unknown element type {kind!r}')
        return {'kind': 'text', 'type': kind, 'text': text, 'box': box,
                'layer': 'background' if kind in BACKGROUND else 'foreground',
                'bleed': e.get('bleed', kind in BACKGROUND)}

    # ---- parts: product photos cut out with rembg beforehand, never recoloured
    def part(self, ref):
        if ref in self._cache:
            return self._cache[ref]
        src = self.spec['parts'][ref]
        src = {'file': src} if isinstance(src, str) else src
        im = Image.open(self.path(src['file'])).convert('RGBA')
        if src.get('split'):  # one photo of several pieces: take one piece, largest first
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
            img.paste(Image.new('RGB', img.size, (80, 80, 86)), (0, 0), sh)
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
        img.paste(Image.new('RGB', img.size, (90, 90, 96)), (0, 0), sh)
        img.paste(lay.convert('RGB'), (x, y), lay.getchannel('A'))
        bb = lay.getchannel('A').point(lambda v: 255 if v > 128 else 0).getbbox()
        return {'kind': 'subject', 'ref': e['ref'], 'box': [x + bb[0], y + bb[1], x + bb[2], y + bb[3]]}

    @staticmethod
    def mask_box(mask):
        ys, xs = np.where(mask)
        return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None

    # ---- slides
    def canvas(self, key, width):
        img = self.studio(width, H)
        layout = self.spec.get('slides', {}).get(key) or DEFAULT_LAYOUT[key]
        recs = []
        for e in layout:
            if e['type'] == 'part':
                recs.append(self.draw_part(img, e))
            elif e['type'] == 'subject':
                recs.append(self.draw_subject(img, e))
            else:
                recs.append(self.draw_text(img, e))
        return img, recs

    def render(self, out):
        os.makedirs(out, exist_ok=True)
        canvases = {}
        for k in ('1', '2', '3'):
            img, recs = self.canvas(k, W)
            img.save(f'{out}/0{k}.png')
            canvases[k] = {'size': [W, H], 'files': [f'0{k}.png'], 'records': recs}
        img, recs = self.canvas('spread', 2 * W)
        img.crop((0, 0, W, H)).save(f'{out}/04.png')
        img.crop((W, 0, 2 * W, H)).save(f'{out}/05.png')
        img.save(f'{out}/spread45.png')
        canvases['spread'] = {'size': [2 * W, H], 'files': ['04.png', '05.png'], 'records': recs}
        with open(f'{out}/layout.json', 'w') as fh:
            json.dump({k: {**c, 'records': [{a: b for a, b in r.items() if a != 'mask'} for r in c['records']]}
                       for k, c in canvases.items()}, fh, indent=1)
        return canvases


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    Carousel(sys.argv[1]).render(sys.argv[2])
    print('ok', sorted(f for f in os.listdir(sys.argv[2]) if f.endswith('.png')))
