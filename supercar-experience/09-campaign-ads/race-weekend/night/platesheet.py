import json, sys, numpy as np
from PIL import Image
E=json.load(open('build_v5/edl.json')); B=E['beat']; F=24000/1001
fr=lambda b: round(b*B*F)
W,H=1080,1920; f=open('.work_v5/plate.rgb','rb')
def get(i): f.seek(i*W*H*3); return Image.fromarray(np.frombuffer(f.read(W*H*3),np.uint8).reshape(H,W,3)).resize((135,240))
tiles=[]
for s in E['shots']:
    a,b=fr(s['b'][0]),fr(s['b'][1])-1; tiles+= [get(a),get(b)]
sheet=Image.new('RGB',(135*10,240*3))
for k,t in enumerate(tiles): sheet.paste(t,((k%10)*135,(k//10)*240))
sheet.save('frames/plate_firstlast.jpg')
