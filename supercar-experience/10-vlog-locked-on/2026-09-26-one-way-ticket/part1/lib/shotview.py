#!/usr/bin/env python3
"""shotview.py -- first / middle / last frame of rendered shots (.work/shots/NN.mov) side by side, with the
safe-zone guides. python3 lib/shotview.py 5,6,11 out.jpg"""
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate as PL
ks = [int(x) for x in sys.argv[1].split(',')]
tw, th = 180, 320
tiles = []
for k in ks:
    p = os.path.join(PL.WORK, 'shots', f'{k:02d}.mov')
    if not os.path.exists(p):
        continue
    n = PL.FR[k][2] - PL.FR[k][1]
    idx = [0, n // 2, n - 1]
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    raw = subprocess.run([PL.FF, '-v', 'error', '-i', p, '-vf', f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc,scale={tw}:{th}",
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, th, tw, 3)
    for q, a in zip(idx, arr):
        im = Image.fromarray(a); d = ImageDraw.Draw(im)
        d.rectangle([54 * tw / 1080, 269 * th / 1920, 907 * tw / 1080, 1536 * th / 1920], outline=(90, 90, 90))
        d.text((3, 3), f'{k} {PL.SHOTS[k]["src"]} f{q}', fill=(255, 79, 22))
        l = float(np.mean(a) / 255)
        d.text((3, th - 12), f'mean {l:.2f}', fill=(255, 255, 255))
        tiles.append(im)
cols = 9
rows = (len(tiles) + cols - 1) // cols
sh = Image.new('RGB', (cols * tw, rows * th), (20, 20, 20))
for i, t in enumerate(tiles):
    sh.paste(t, ((i % cols) * tw, (i // cols) * th))
sh.save(sys.argv[2], quality=88)
print(sys.argv[2])
