"""Locked-On ABC v2 plate job: the hook's footage (reviewer, 4 Oct: both approved FD Locked-On ads put the frame-0 panel over
footage). #36 = the installer at the front fender, wide, the whole front of the car in the light tunnel; not used anywhere
else in this cut and not the trident. 56 frames (beats 0-4) from src 0.30 s at 1.0x."""
from full30 import OFPS, fb
ADS = {"M_h36": {"name": "h36", "src": "src/mc20", "shots": [dict(id="h36", clip="Clip #36.mp4", a=0.30, n=fb(4), speed=1.0)]}}
def timeline(ad):
    return [dict(x, f0=0, f1=x["n"], t0=0, t1=x["n"] / OFPS) for x in ad["shots"]], ad["shots"][0]["n"]
