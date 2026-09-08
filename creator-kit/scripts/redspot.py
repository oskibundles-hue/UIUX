#!/usr/bin/env python3
"""Find where the red car sits in a frame: centroid of strongly red pixels as fractions of width/height.
usage: redspot.py <video> <t1> [t2 ...]  -> prints t x y fraction"""
import subprocess, sys, struct
def frame(video, t, w=108, h=192):
    out = subprocess.run(["/root/bin/ffmpeg","-v","error","-ss",str(t),"-i",video,"-frames:v","1","-vf",f"scale={w}:{h}","-pix_fmt","rgb24","-f","rawvideo","-"],capture_output=True).stdout
    return out, w, h
for t in sys.argv[2:]:
    px, w, h = frame(sys.argv[1], float(t))
    sx=sy=n=0
    for i in range(w*h):
        r,g,b = px[3*i], px[3*i+1], px[3*i+2]
        if r>110 and r-g>55 and r-b>45: sx+=i%w; sy+=i//w; n+=1
    if n<40: print(f"{t} none 0")
    else: print(f"{t} {sx/n/w:.3f} {sy/n/h:.3f} {n/(w*h):.3f}")
