#!/usr/bin/env python3
"""contact_v3.py -- v2 | v3 pairs from 26.5 to 31.0 s every 0.25 s (480 px each, frame + time stamped; orange = new shot 10).
    python3 tools/contact_v3.py <v2.mp4> <v3.mp4> <out.jpg>"""
import subprocess, numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
v2, v3, out = sys.argv[1:4]
FPS = 30000/1001
ts = [round(26.5 + 0.25*i, 2) for i in range(19)]
idx = [int(round(t*FPS)) for t in ts]
def grab(p):
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    raw = subprocess.run(['ffmpeg','-v','error','-i',p,'-vf',f"select='{sel}',scale=480:854",'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,854,480,3)
A, B = grab(v2), grab(v3)
assert len(A)==len(B)==len(ts)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
cols = 3; pw = 480*2+12; ph = 854+36
rows = (len(ts)+cols-1)//cols
sh = Image.new('RGB', (cols*pw + (cols-1)*24, rows*ph), (18,18,18)); d = ImageDraw.Draw(sh)
for n,(t,i) in enumerate(zip(ts,idx)):
    x = (n%cols)*(pw+24); y=(n//cols)*ph
    win = 821 <= i <= 897
    d.text((x+4,y+6), f'{t:.2f}s  f{i}  {"NEW SHOT 10" if win else ""}', fill=(255,79,22) if win else (230,230,230), font=f)
    sh.paste(Image.fromarray(A[n]),(x,y+36)); sh.paste(Image.fromarray(B[n]),(x+492,y+36))
    d.text((x+6,y+40),'v2',fill=(255,255,255),font=f,stroke_width=2,stroke_fill=(0,0,0)); d.text((x+498,y+40),'v3',fill=(255,255,255),font=f,stroke_width=2,stroke_fill=(0,0,0))
sh.save(out, quality=88); print(sh.size)
