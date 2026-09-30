#!/usr/bin/env python3
"""srcsheet.py -- planning sheets: first / middle / last SOURCE frame of each EDL shot (full mezzanine
frame, ungraded) with the configured 1080x1920 window drawn on it (gold = first frame's window,
white = last). python3 lib/srcsheet.py 0,1,2 out.jpg"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate as PL

ks = [int(x) for x in sys.argv[1].split(',')]
out = sys.argv[2]
th = 300
tiles = []
for k in ks:
    try:
        pl = PL.plan_shot(k)
    except SystemExit as e:
        print('skip', k, e); continue
    m = pl['m']; n = PL.FR[k][2] - PL.FR[k][1]
    for q, nm in ((0, 'in'), (n // 2, 'mid'), (n - 1, 'out')):
        jf, _ = pl['picks'][q]
        j = int(round(jf))
        r = PL.Reader(m, j, 1, (0, 0, m['w'] // 2 * 2, m['h'] // 2 * 2))
        img = Image.fromarray(r.get(j).copy()); r.close()
        sc = th / m['h']
        img = img.resize((int(m['w'] * sc), th), Image.BILINEAR)
        d = ImageDraw.Draw(img)
        cx, cy, s = pl['wins'][q]
        ww, hh = PL.W / s * (m['h'] / PL.H), PL.H / s * (m['h'] / PL.H)
        d.rectangle([(cx - ww / 2) * sc, (cy - hh / 2) * sc, (cx + ww / 2) * sc - 1, (cy + hh / 2) * sc - 1], outline=(251, 209, 1), width=2)
        for gx in range(0, m['w'], 240):
            d.line([(gx * sc, th - 8), (gx * sc, th)], fill=(255, 0, 0), width=1)
        d.text((3, 3), f'{k} {PL.SHOTS[k]["src"]} {nm} t{pl["ts"][q][0]:.2f}', fill=(255, 255, 0))
        tiles.append(img)
cols = 6
W = max(t.width for t in tiles)
rows = math.ceil(len(tiles) / cols)
sh = Image.new('RGB', (cols * W, rows * th), (30, 30, 30))
for i, t in enumerate(tiles):
    sh.paste(t, ((i % cols) * W, (i // cols) * th))
sh.save(out, quality=85)
print(out)
