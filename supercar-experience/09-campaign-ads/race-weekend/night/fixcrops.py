# before (v1) / after (v2) crops for review fixes 1-4, and the orange sample (decoded as BT.709, as players do)
import subprocess, numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
V1='exports/SE_F1_Weekend_Countdown_v1_post-2026-10-04_9x16.mp4'; V2=sys.argv[1]; F=24000/1001
font=ImageFont.truetype('fonts/JetBrainsMono-700.ttf',22)
def frame(f,t):
    raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.4f}','-i',f,'-frames:v','1','-vf','scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24','-f','rawvideo','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(1920,1080,3)
def pair(name,f1,t1,box1,t2,box2,label2):
    a=Image.fromarray(frame(V1,t1)).crop(box1); b=Image.fromarray(frame(V2,t2)).crop(box2)
    h=480; a=a.resize((int(a.width*h/a.height),h)); b=b.resize((int(b.width*h/b.height),h))
    c=Image.new('RGB',(a.width+b.width+20,h+40),(10,10,10)); c.paste(a,(0,40)); c.paste(b,(a.width+20,40))
    d=ImageDraw.Draw(c); d.text((6,8),f'BEFORE v1 t={t1:.2f}s',fill=(255,79,22),font=font); d.text((a.width+26,8),f'AFTER v2 t={t2:.2f}s {label2}',fill=(255,79,22),font=font)
    c.save(f'exports/review_v2/fix_{name}.jpg',quality=90)
B=0.6742
pair('1_sf90_dash',V1,106/F,(0,0,1080,800),8*B+0.3,(0,700,1080,1500),'(cockpit shot removed; SF90 profile, HUD only)')
pair('2a_reel_countdown',V1,195/F,(40,330,900,760),12*B+0.25,(40,330,900,760),'(feathered, unreadable spin)')
pair('2b_reel_endcard',V1,260/F,(500,300,880,470),17.4*B+0.4,(500,300,880,470),'')
FZ=14.0114
pair('3_sweep',V1,315/F,(0,800,1080,1400),FZ+0.35,(0,800,1080,1400),'(feathered sweep)')
for nm,f in (('v1',V1),('v2',V2)):
    px=frame(f,0.0)[766:778,700:780].reshape(-1,3).mean(0)
    print(nm,'S3 bar orange (BT.709 decode): #%02X%02X%02X'%tuple(int(round(v)) for v in px))
