"""v2 (A-B-C mix) plate jobs not covered by full30's v1 plates. #22 runs on from its v1 in-point (0.30 s at beat 41)
through the riser to the drop at beat 48 (src 0.30-3.58 s of the 3.69 s clip, 1.0x)."""
from full30 import OFPS, BEAT, fb, timeline as _t
N22 = fb(48) - fb(41)
ADS = {"G_s22": {"name": "s22", "src": "src/mc20", "shots": [dict(id="s22", clip="Clip #22.mp4", a=0.30, n=N22, speed=1.0)]}}
def timeline(ad):
    return [dict(x, f0=0, f1=x["n"], t0=0, t1=x["n"] / OFPS) for x in ad["shots"]], ad["shots"][0]["n"]
