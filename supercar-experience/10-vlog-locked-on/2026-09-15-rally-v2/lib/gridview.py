#!/usr/bin/env python3
"""gridview.py -- output frames of a rendered shot with a 100 px grid (to read boxes off). 
python3 lib/gridview.py SHOT f1,f2,... out.jpg   (f = OUTPUT frame numbers)"""
import sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate as PL
k = int(sys.argv[1]); fr = [int(x) for x in sys.argv[2].split(',')]
off = PL.FR[k][1]
idx = [f - off for f in fr]
sel = '+'.join(f'eq(n\\,{i})' for i in idx)
raw = subprocess.run([PL.FF, '-v', 'error', '-i', os.path.join(PL.WORK, 'shots', f'{k:02d}.mov'), '-vf', f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc",
                      '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
arr = np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080, 3)
tiles = []
for f, a in zip(sorted(fr), arr):
    im = Image.fromarray(a); d = ImageDraw.Draw(im)
    for x in range(0, 1080, 100): d.line([(x, 0), (x, 1920)], fill=(255, 0, 0) if x % 500 == 0 else (110, 0, 0), width=2)
    for y in range(0, 1920, 100): d.line([(0, y), (1080, y)], fill=(255, 0, 0) if y % 500 == 0 else (110, 0, 0), width=2)
    for y in (269, 1114, 1382, 1536): d.line([(0, y), (1080, y)], fill=(0, 255, 0), width=3)
    d.text((10, 10), f'shot {k} f{f}', fill=(255, 255, 0))
    tiles.append(im.resize((432, 768)))
sh = Image.new('RGB', (432 * len(tiles), 768))
for i, t in enumerate(tiles): sh.paste(t, (i * 432, 0))
sh.save(sys.argv[3], quality=85)
