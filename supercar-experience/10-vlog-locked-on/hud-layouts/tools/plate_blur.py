#!/usr/bin/env python3
"""plate_blur.py -- feathered, tracked blur over a moving car's number plate (the client-plate rule).

  plate_blur.py <clip.mov> <tracks.json> <track> <out.mov> [--rel cx,cy,w,h]

The plate box is placed relative to the tracked car box (default 0.53,0.55,0.30,0.22 = centre x/y, width, height
as fractions of the car box, measured on the Sep 15 drive back). A mask per frame is drawn with Pillow and the
blurred clip is alpha-merged through it with ffmpeg. Check every 2nd-3rd frame at 3x before rendering.
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
clip, tracks, name, out = sys.argv[1:5]
rel = [float(v) for v in sys.argv[sys.argv.index('--rel') + 1].split(',')] if '--rel' in sys.argv else [0.53, 0.55, 0.30, 0.22]
fr = json.load(open(tracks))[name]['frames']
md = out + '.masks'; os.makedirs(md, exist_ok=True)
for f in fr:
    cx, cy = f['x'] + rel[0] * f['w'], f['y'] + rel[1] * f['h']; pw, ph = max(30, rel[2] * f['w']), max(20, rel[3] * f['h'])
    m = Image.new('L', (1080, 1920), 0)
    ImageDraw.Draw(m).rounded_rectangle([cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], 6, fill=255)
    m.filter(ImageFilter.GaussianBlur(4)).save(f"{md}/{f['f']:04d}.png")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', clip, '-framerate', '30000/1001', '-i', f'{md}/%04d.png', '-filter_complex',
                '[0:v]split=2[a][b];[b]gblur=sigma=10[bl];[1:v]format=gray[m];[bl][m]alphamerge[blm];[a][blm]overlay=shortest=1,format=yuv420p[v]',
                '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-c:a', 'pcm_s16le', out], check=True)
print('wrote', out)
