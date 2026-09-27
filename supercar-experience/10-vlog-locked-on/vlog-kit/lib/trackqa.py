#!/usr/bin/env python3
"""trackqa.py -- draw tracked boxes from tracks.json on the source frames, as a contact sheet.
  python3 lib/trackqa.py --video V --ffmpeg FF --tracks lib/data/tracks.json --names a,b --every 4 --out sheet.jpg
"""
import argparse, json, subprocess
import numpy as np
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('--video', required=True); ap.add_argument('--ffmpeg', required=True)
ap.add_argument('--tracks', required=True); ap.add_argument('--names', required=True)
ap.add_argument('--every', type=int, default=4); ap.add_argument('--out', required=True)
ap.add_argument('--scale', type=float, default=0.25); ap.add_argument('--cols', type=int, default=8)
a = ap.parse_args()
db = json.load(open(a.tracks)); names = a.names.split(',')
f0 = min(db[n]['f0'] for n in names); f1 = max(db[n]['f1'] for n in names)
W, H = 1080, 1920
raw = subprocess.run([a.ffmpeg, '-v', 'error', '-i', a.video, '-vf', f"select='between(n\\,{f0}\\,{f1})'", '-vsync', '0',
                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
cols = ['#FBD101', '#00FFFF', '#FF40FF', '#40FF40', '#FF8040', '#FFFFFF']
tiles = []
for i in range(0, len(fr), a.every):
    f = f0 + i
    im = Image.fromarray(fr[i]); d = ImageDraw.Draw(im)
    for k, n in enumerate(names):
        tr = db[n]
        if tr['f0'] <= f <= tr['f1']:
            b = tr['frames'][f - tr['f0']]
            d.rectangle([b['x'], b['y'], b['x'] + b['w'], b['y'] + b['h']], outline=cols[k % 6], width=6)
            d.text((b['x'] + 6, b['y'] + 6), f"{n} {b['conf']:.2f}", fill=cols[k % 6])
    im = im.resize((int(W * a.scale), int(H * a.scale)))
    ImageDraw.Draw(im).text((4, 4), f'f{f}', fill='yellow')
    tiles.append(im)
tw, th = tiles[0].size; c = a.cols; r = (len(tiles) + c - 1) // c
sheet = Image.new('RGB', (tw * c, th * r))
for i, t in enumerate(tiles): sheet.paste(t, ((i % c) * tw, (i // c) * th))
sheet.save(a.out, quality=85); print(a.out, sheet.size)
