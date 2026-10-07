# Orange-car bbox per source frame (AMG GT Black Series is the only orange object in these shots).
import numpy as np, subprocess, sys, json
from PIL import Image
src, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
fps = 24000/1001
out = {}
p = subprocess.run(['ffmpeg','-v','error','-ss',str(a),'-t',str(b-a),'-i',src,'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
n = len(p)//(1080*1920*3)
for i in range(n):
    f = np.frombuffer(p[i*1080*1920*3:(i+1)*1080*1920*3],np.uint8).reshape(1920,1080,3).astype(int)
    r,g,bb = f[...,0],f[...,1],f[...,2]
    m = (r>140)&(g>40)&(g<r*0.75)&(bb<r*0.45)
    m[1350:] = False                      # drop road reflections
    ys,xs = np.nonzero(m)
    if len(xs) < 500: continue
    x0,x1 = np.percentile(xs,[1,99]); y0,y1 = np.percentile(ys,[1,99.5])
    out[round(a+i/fps,3)] = [int(x0),int(y0),int(x1),int(y1),int(len(xs))]
json.dump(out,open(sys.argv[4],'w'))
for k,v in list(out.items())[::4]: print(k,v)
