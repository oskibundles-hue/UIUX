"""Draws the labelled placeholder images the sample specs use.

    python3 make_placeholders.py            # all of them
    python3 make_placeholders.py cutout     # only those for spec.json
    python3 make_placeholders.py photo      # only those for photo_spec.json

For spec.json: parts are grey shapes on a transparent ground, as a rembg cutout would come out. The
flat lay is three pieces in one image, so the generator's split is exercised. Subjects are dark shapes
on a studio-grey ground, as a studio render would come, so the soft mask is exercised.

For photo_spec.json: photos are drawn scenes saved as JPEGs. Two are stored on their side with the
rotation in EXIF, as a phone saves them, so photo() is exercised; one carries a dummy plate for
redact(). The rough cutouts have stray pieces, haze, a loose line at the top, a ragged arm and a flat
bottom edge, so each clean_cut() option has something to remove.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'assets')
FONTS = ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf')
LABEL = next((ImageFont.truetype(f, 40) for f in FONTS if os.path.exists(f)), ImageFont.load_default())


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


def scene(name, text, sideways=False, plate=None):
    """A stand-in for a shop photo: a wall, a floor, a dark subject and its label."""
    w, h = 1600, 1200
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    v = np.where(yy < 760, 150 - 40 * (yy / 760), 96 + 30 * ((yy - 760) / 440))
    im = Image.fromarray(np.stack([v + 6, v, v - 8], -1).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([300, 420, 1300, 860], 110, fill=(44, 46, 54))
    d.rounded_rectangle([520, 300, 1080, 520], 80, fill=(58, 60, 70))
    for cx in (520, 1080):
        d.ellipse([cx - 120, 740, cx + 120, 980], fill=(20, 20, 22))
    d.text((800, 640), text, font=LABEL, fill=(232, 232, 236), anchor='mm')
    if plate:  # a dummy plate, for redact() to cover
        d.rounded_rectangle(plate, 8, fill=(244, 244, 240), outline=(20, 20, 22), width=4)
        d.text(((plate[0] + plate[2]) / 2, (plate[1] + plate[3]) / 2), 'PLATE 000', font=LABEL,
               fill=(20, 20, 22), anchor='mm')
    exif = Image.Exif()
    if sideways:  # stored turned, with the rotation left to EXIF
        im = im.rotate(90, expand=True)
        exif[0x0112] = 6
    im.save(os.path.join(OUT, name), quality=80, exif=exif)


def rough_cut(name, text):
    """A stand-in for a raw rembg cutout of a tall part on a stand: one solid piece plus what rembg leaves behind."""
    w, h = 700, 1400
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    solid = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    metal(ImageDraw.Draw(solid), [0, 0, w, h])
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([230, 120, 470, 760], 60, fill=255)    # the body
    d.rectangle([315, 760, 385, 1400], fill=255)                # the pole, running off the crop: a flat bottom edge
    d.rectangle([330, 0, 344, 130], fill=255)                   # a loose line running off the top
    d.rectangle([470, 400, 690, 460], fill=255)                 # an arm with a ragged end
    for i in range(8):
        d.rectangle([640 + (i % 3) * 14, 396 + i * 9, 700, 402 + i * 9], fill=0)
    d.ellipse([40, 200, 150, 330], fill=255)                    # a stray piece: the ghost of a light
    d.ellipse([560, 980, 650, 1080], fill=255)                  # and another
    haze = Image.new('L', (w, h), 0)
    ImageDraw.Draw(haze).ellipse([150, 60, 550, 840], fill=50)  # translucent haze round the body
    im.paste(solid, (0, 0), Image.fromarray(np.maximum(np.array(mask), np.array(haze))))
    tag = Image.new('RGBA', (560, 60), (0, 0, 0, 0))
    ImageDraw.Draw(tag).text((280, 30), text, font=LABEL, fill=(40, 40, 44, 255), anchor='mm')
    tag = tag.rotate(90, expand=True)
    im.alpha_composite(tag, (320, 160))
    im.save(os.path.join(OUT, name))


def cutout_set():
    part('part_hero.png', 1400, 700, 'PLACEHOLDER HERO PART', [([60, 160, 1340, 540], 180)])
    part('part_a.png', 900, 500, 'PLACEHOLDER PART A', [([40, 60, 860, 440], 60)])
    part('part_b.png', 900, 420, 'PLACEHOLDER PART B', [([40, 80, 860, 340], 130)])
    part('part_c.png', 600, 600, 'PART C', [([60, 60, 540, 540], 240)])
    part('flatlay.png', 1600, 1100, 'FLAT PIECE', [([60, 60, 1540, 400], 120), ([60, 520, 760, 1040], 80),
                                                    ([880, 560, 1540, 1000], 200)])
    for n in ('side', 'rear', 'front', 'three_quarter'):
        subject(f'subject_{n}.png', f'PLACEHOLDER SUBJECT {n.upper().replace("_", " ")}')


def photo_set():
    scene('photo_hero.jpg', 'PLACEHOLDER PHOTO HERO', sideways=True)
    scene('photo_view.jpg', 'PLACEHOLDER PHOTO VIEW', sideways=True, plate=[640, 900, 960, 990])
    for i in range(1, 5):
        scene(f'photo_step{i}.jpg', f'PLACEHOLDER PHOTO STEP {i}')
    rough_cut('cut_rough.png', 'PLACEHOLDER ROUGH CUT')
    part('cut_top.png', 700, 600, 'PLACEHOLDER TOP CUT', [([60, 60, 640, 540], 120)])


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ['cutout', 'photo']
    if 'cutout' in which:
        cutout_set()
    if 'photo' in which:
        photo_set()
    print('ok', sorted(os.listdir(OUT)))
