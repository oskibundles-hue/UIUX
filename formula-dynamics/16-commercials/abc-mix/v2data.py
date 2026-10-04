"""v2 (A-B-C mix) scene: flat full-frame shots on v1's exact order and timing (full30.SEGS focus windows), #22 running on
through the riser to the drop, #29 from the drop to beat 55, then the approved end card.  -> .work/G/scene.js"""
import json, os
from full30 import SEGS, fb, OFPS, BEAT, NF
T = os.path.dirname(os.path.abspath(__file__))
shots = []
for s in SEGS:
    if s["key"] == "s22":
        shots.append(dict(key="s22", clip=s["clip"], rel="G_s22/s22", g0=fb(41), g1=fb(48), off=0, src0=0.30))
    elif s["key"] == "r29":
        shots.append(dict(key="r29", clip=s["clip"], rel="F_r29/r29", g0=fb(48), g1=fb(55), off=s["focus0"] - s["f0"], src0=s["a_focus"]))
    else:
        shots.append(dict(key=s["key"], clip=s["clip"], rel=f"F_{s['key']}/{s['key']}", g0=s["focus0"], g1=s["focus1"], off=s["focus0"] - s["f0"], src0=s["a_focus"]))
for s in shots:
    s["n_avail"] = len([f for f in os.listdir(f"{T}/plates/{s['rel']}") if f.endswith(".jpg")])
    assert s["off"] + (s["g1"] - s["g0"]) <= s["n_avail"], (s["key"], "plate too short: would freeze")
scene = {"nf": NF, "beat": BEAT, "fps": OFPS, "shots": shots,
         "T35": json.load(open(f"{T}/tracks/s35.json")), "T22": json.load(open(f"{T}/tracks/s22.json")),
         "s35_f0": next(s["f0"] for s in SEGS if s["key"] == "s35")}
os.makedirs(f"{T}/.work/G", exist_ok=True)
open(f"{T}/.work/G/scene.js", "w").write("window.SCENE = " + json.dumps(scene) + ";\n")
print("%-5s %-14s %-17s %-15s" % ("key", "clip", "on screen (s)", "src (s)"))
print("%-5s %-14s %6.3f-%6.3f s" % ("hook", "black ground", 0, fb(4) / OFPS))
for s in shots:
    d = (s["g1"] - s["g0"]) / OFPS
    print("%-5s %-14s %6.3f-%6.3f s   %6.3f-%6.3f" % (s["key"], s["clip"], s["g0"] / OFPS, s["g1"] / OFPS, s["src0"], s["src0"] + d))
print("end   approved v4 file  %6.3f-%6.3f s" % (fb(55) / OFPS, NF / OFPS))
