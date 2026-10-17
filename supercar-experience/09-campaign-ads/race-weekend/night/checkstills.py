# composite front stills (capture.py 'at') over the plate frame at the same time -> one strip
import sys, os, numpy as np, subprocess
from PIL import Image
F=24000/1001; W,H=1080,1920
ts=[float(x) for x in sys.argv[1].split(',')]
d='.work_v5/check'; os.makedirs(d,exist_ok=True)
subprocess.run(['.venv/bin/python','build_v5/capture.py','at',d,sys.argv[1]],check=True)
pf=open('.work_v5/plate.rgb','rb'); tiles=[]
for t in ts:
    i=round(t*F); pf.seek(i*W*H*3); p=Image.fromarray(np.frombuffer(pf.read(W*H*3),np.uint8).reshape(H,W,3)).convert('RGBA')
    fg=Image.open(f'{d}/t{t:07.3f}.png').convert('RGBA'); p.alpha_composite(fg); p=p.convert('RGB')
    p.save(f'{d}/c{t:07.3f}.jpg',quality=90); tiles.append(p.resize((360,640)))
s=Image.new('RGB',(360*len(tiles),640))
for k,tl in enumerate(tiles): s.paste(tl,(k*360,0))
s.save(sys.argv[2],quality=88)
