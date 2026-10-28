# one frame per shot from the final file (a frame where the shot's graphics have landed) -> labelled sheet
import json, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
E=json.load(open('build_v5/edl.json')); B=E['beat']; F=24000/1001
mp4=sys.argv[1]; out=sys.argv[2]
# sample point per shot (beats): late enough that its words have landed
PICK=[1.0,3.0,4.6,5.7,6.3,6.8,7.8,8.5,10.3,11.8,12.7,13.7,14.5,15.5,16.5,23.5]
font=ImageFont.truetype('fonts/JetBrainsMono-700.ttf',20)
tiles=[]
for s,pb in zip(E['shots'],PICK):
    t=pb*B
    raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',mp4,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    im=Image.fromarray(np.frombuffer(raw,np.uint8).reshape(1920,1080,3)).resize((270,480))
    c=Image.new('RGB',(270,530),(12,12,12)); c.paste(im,(0,0)); d=ImageDraw.Draw(c)
    d.text((6,486),f"{s['b'][0]*B:5.2f}-{s['b'][1]*B:5.2f}s",fill=(255,79,22),font=font)
    d.text((6,508),f"src {s['src']:.2f} {s['car']}",fill=(200,200,200),font=font)
    tiles.append(c)
cols=5; rows=(len(tiles)+cols-1)//cols
sheet=Image.new('RGB',(270*cols,530*rows),(0,0,0))
for k,tl in enumerate(tiles): sheet.paste(tl,((k%cols)*270,(k//cols)*530))
sheet.save(out,quality=90); print(out)
