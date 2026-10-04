"""Locked-On ABC v1 scene (4 Oct 2026). Omarie: "Can I get an ABC mix for Locked On as well? ... like a variation similar to the
ABC mix". Classic FD Locked-On base (frame-0 hook panel, tracked lock-ons, kinetic step cards, whips, impacts, FD end card v4)
with the A/B/C 3D moments folded in per step. Same shots, src windows, timing and music as abc-mix v3 (.work/H).

  python3 lo_data.py [L|M]   -> .work/<key>/scene.js  (L = v1; M = v2, adds the hook's footage: dimmed #36 under the panel) (shots, edit plan, lock tracks, wrap homographies) + .work/L/kitdata.js (end card bands)

Edit plan (cuts on the beat; whips between steps, impacts inside a step and on the drop):
  beat  4  hook -> #37   whip-left        beat  8  #37 -> #21  impact
  beat 11  #21 -> #26    whip-left        beat 14  #26 -> #27  impact
  beat 17  #27 -> #32    whip-up          beat 24  #32 -> #33  whip-left
  beat 28  #33 -> #25    impact           beat 31  #25 -> #38  whip-up
  beat 35  #38 -> #40    impact           beat 38  #40 -> #35  whip-left
  beat 41  #35 -> #22    impact           beat 48  #22 -> #29  impact on the drop (soft wash + FD red leak)
  beat 55  #29 -> end card  whip-up into the card's black ground; the card builds in the Locked-On way (fdc.js cardFD)
"""
import base64, io, json, os, shutil, sys
from PIL import Image
from full30 import fb, OFPS, BEAT, NF

T = os.path.dirname(os.path.abspath(__file__))
H = json.loads((lambda s: s[s.index('{'):s.rindex('}') + 1])(open(f"{T}/.work/H/scene.js").read()))
TRANS = [dict(b=4, kind="whip", dir="left"), dict(b=8, kind="impact"), dict(b=11, kind="whip", dir="left"), dict(b=14, kind="impact"),
         dict(b=17, kind="whip", dir="up"), dict(b=24, kind="whip", dir="left"), dict(b=28, kind="impact"), dict(b=31, kind="whip", dir="up"),
         dict(b=35, kind="impact"), dict(b=38, kind="whip", dir="left"), dict(b=41, kind="impact"), dict(b=48, kind="impact", drop=True),
         dict(b=55, kind="whip", dir="up")]
for x in TRANS:
    x["f"] = fb(x["b"])
LEAKS = [dict(key="s37", f0=fb(4), dur=0.9, side="right"), dict(key="r29", f0=fb(48), dur=1.4, side="left")]
BANDS = [("logo", 468, 814), ("tag", 859, 895), ("cta", 934, 1007), ("stripe", 1037, 1051), ("site", 1075, 1109), ("handle", 1118, 1147)]


def card_data():                                   # the approved hook ad's method (fd_ppf_hook_1003/scene.py), same card file
    im = Image.open(f"{T}/logos/fd_endcard__v4_nogrid_9x16.jpg").convert("RGB").resize((1080, 1920), Image.LANCZOS)
    out = []
    for name, y0, y1 in BANDS:
        b = io.BytesIO(); im.crop((0, y0, 1080, y1)).save(b, "PNG")
        out.append(dict(name=name, y0=y0, y1=y1, src="data:image/png;base64," + base64.b64encode(b.getvalue()).decode()))
    return {"bands": out}


KEY = sys.argv[1] if len(sys.argv) > 1 else "M"
scene = dict(H, trans=TRANS, leaks=LEAKS, locks=json.load(open(f"{T}/tracks/locks.json")))
if KEY != "L":                                     # v2: the frame-0 panel sits over dimmed footage (both approved FD Locked-On ads do)
    scene["hook"] = dict(rel="M_h36/h36", clip="Clip #36.mp4", src0=0.30, dim=0.42, push=[1.0, 1.04])
wd = f"{T}/.work/{KEY}"
os.makedirs(wd, exist_ok=True)
open(f"{wd}/scene.js", "w").write("window.SCENE = " + json.dumps(scene) + ";\n")
open(f"{wd}/kitdata.js", "w").write("window.KITDATA = " + json.dumps({"card": card_data()}) + ";\n")
if not os.path.exists(f"{wd}/mix.wav"):
    shutil.copy(f"{T}/.work/H/mix.wav", f"{wd}/mix.wav")
print("shots", len(scene["shots"]), "frames", NF, "transitions", len(TRANS), "locks", sorted(scene["locks"]))
