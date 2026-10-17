# shot_sheet.py "k:n,..." out.jpg -- rendered shots (.work/shots), n frames each, speedo boxes in orange (round 1 hands / speedo check)
import json,subprocess,sys
from PIL import Image,ImageDraw
FF='/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
R='/home/user/se/supercar-experience/10-vlog-locked-on/2026-09-26-one-way-ticket/part2'
e=json.load(open(R+'/data/edl.json')); c=json.load(open(R+'/config.json'))
SP={s['shot']:s['box'] for s in c['speedo']}
W,H=216,384; f=W/1080; tiles=[]
for spec in sys.argv[1].split(','):
    k,n=map(int,spec.split(':')); s=e['shots'][k]; fr=int(s['dur']*29.97)
    idx=[int(fr*(i+0.5)/n) for i in range(n)]
    sel='+'.join(f'eq(n\\,{i})' for i in idx)
    raw=subprocess.run([FF,'-v','error','-i',f'{R}/.work/shots/{k:02d}.mov','-vf',f"select='{sel}',scale={W}:{H}",'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    for j,i in enumerate(idx):
        b=raw[j*W*H*3:(j+1)*W*H*3]
        if len(b)<W*H*3: break
        im=Image.frombytes('RGB',(W,H),b); d=ImageDraw.Draw(im)
        if k in SP: x,y,w,h=SP[k]; d.rectangle([x*f,y*f,(x+w)*f,(y+h)*f],outline=(255,79,22),width=2)
        d.rectangle([0,0,W,13],fill=(0,0,0)); d.text((2,0),f"{k} {s['src']} {s['in']+i/29.97:.1f} t{s['t']+i/29.97:.1f}",fill=(255,200,0)); tiles.append(im)
cols=10; rows=(len(tiles)+cols-1)//cols
sh=Image.new('RGB',(cols*W,rows*H),(30,30,30))
for i,t in enumerate(tiles): sh.paste(t,((i%cols)*W,(i//cols)*H))
sh.save(sys.argv[2],quality=80); print(len(tiles),sh.size)
