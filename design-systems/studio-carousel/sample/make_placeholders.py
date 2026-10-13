"""Draws the labelled placeholder images the sample spec uses (python3 make_placeholders.py).

Parts are grey shapes on a transparent ground, as a rembg cutout would come out. The flat lay is
three pieces in one image, so the generator's split is exercised. Subjects are dark shapes on a
studio-grey ground, as a studio render would come, so the soft mask is exercised.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'assets')
LABEL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40) \
    if os.path.exists('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') else ImageFont.load_default()


def metal(d, box):
    x0, y0, x1, y1 = box
    for i in range(int(y1 - y0)):  # vertical sheen so it reads as a part, not a flat block
        v = int(120 + 90 * abs(np.sin(i / (y1 - y0) * np.pi)))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=(v, v, v + 4, 255))


def part(name, w, h, text, shapes):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for box, r in shapes:
        tile = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        metal(ImageDraw.Draw(tile), box)
        mask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle(box, r, fill=255)
        im.paste(tile, (0, 0), mask)
        ImageDraw.Draw(im).text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text, font=LABEL,
                                fill=(40, 40, 44, 255), anchor='mm')
    im.save(os.path.join(OUT, name))


def subject(name, text):
    w, h = 1600, 1000
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    v = 205 - 18 * (yy / h)  # studio tone that changes down the frame, as a render's does
    im = Image.fromarray(np.stack([v, v, v + 2], -1).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([260, 380, 1340, 700], 120, fill=(52, 52, 58))
    d.rounded_rectangle([480, 260, 1100, 460], 90, fill=(64, 64, 70))
    for cx in (480, 1120):
        d.ellipse([cx - 110, 600, cx + 110, 820], fill=(24, 24, 26))
    d.text((800, 520), text, font=LABEL, fill=(230, 230, 234), anchor='mm')
    im.save(os.path.join(OUT, name))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    part('part_hero.png', 1400, 700, 'PLACEHOLDER HERO PART', [([60, 160, 1340, 540], 180)])
    part('part_a.png', 900, 500, 'PLACEHOLDER PART A', [([40, 60, 860, 440], 60)])
    part('part_b.png', 900, 420, 'PLACEHOLDER PART B', [([40, 80, 860, 340], 130)])
    part('part_c.png', 600, 600, 'PART C', [([60, 60, 540, 540], 240)])
    part('flatlay.png', 1600, 1100, 'FLAT PIECE', [([60, 60, 1540, 400], 120), ([60, 520, 760, 1040], 80),
                                                    ([880, 560, 1540, 1000], 200)])
    for n in ('side', 'rear', 'front', 'three_quarter'):
        subject(f'subject_{n}.png', f'PLACEHOLDER SUBJECT {n.upper().replace("_", " ")}')
    print('ok', sorted(os.listdir(OUT)))
