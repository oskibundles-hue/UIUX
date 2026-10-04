"""FD Maserati MC20 -- PPF full process, 30 s, 9:16 -- "3D rail" v1 (3 Oct 2026). Omarie picked B (Spatial Rail) + A's layers.

One timeline for everything: beats at 128 BPM from 0.000 s, 64 beats = 16 bars = 30.0 s (899 frames at 30000/1001).
  python3 full30.py            -> prints the shot sheet, writes .work/F/scene.json + scene.js, and registers plate jobs
  (plates.py F_<key> builds the graded 1.0x plates; music.py ppf30 builds the spliced bed)

Rail cards (index on the rail, focus beats, what is on camera):
  0  HOOK            0-4    black card: FD logo, EVERY INCH BY HAND, PAINT PROTECTION FILM -- complete on frame 0
  1  PREP & CLEAN    4-11   #37 yellow microfibre wiping the front fender; #21 spraying the front of the car with the hose
  2  PEEL THE FILM   11-17  #26 blue film pulled away from the sheet; #27 blue film peeled and rolled off the sheet
                            (no shot shows a blade cutting film, so the step is named for what is on camera)
  3  LAY THE FILM    17-24  #32 hand smoothing the wet film flat on the hood, spray bottle in the other hand
  4  SQUEEGEE        24-31  #33 orange squeegee pushing the water out; #25 blue applicator along the lower fender
  5  TRIM            31-38  #38 blade drawn along the panel seam; #40 blade along the film edge at the windshield base
  6  WRAP THE EDGES  38-44  #35 squeegee + fingers working the film round the panel edge; #22 fingers tucking the edge
  riser              44-48  camera leaves WRAP and pushes into the last card until it fills the frame on the drop
  7  REVEAL          48-54  #29 the finished hood and trident, full frame; A's FILM / CLEAR COAT / PAINT split and seal
  end                54-64  the card pulls back onto the rail, turns over: its back is the FD end card v4, which fills the frame
Every clip at 1.0x. A card's clip plays from a little before its focus to a little after (frozen beyond, while far away).
"""
import json, os, sys
T = os.path.dirname(os.path.abspath(__file__))
OFPS = 30000 / 1001
BPM = 128
BEAT = 60 / BPM
NBEATS = 64
NF = round(NBEATS * BEAT * OFPS)                 # 899
fb = lambda b: round(b * BEAT * OFPS)            # beat -> frame (nearest, grid never drifts)
DUR = {"#21": 2.90, "#22": 3.69, "#25": 6.9, "#26": 5.95, "#27": 10.43, "#29": 4.35, "#32": 10.20, "#33": 4.14,
       "#35": 2.60, "#37": 3.10, "#38": 4.99, "#40": 10.35}

# card: name, focus beats [b0, b1), segments: (key, clip, src at the segment's first focus beat, beats, extra)
CARDS = [
    dict(name="HOOK", b0=0, b1=4, segs=[]),
    dict(name="PREP & CLEAN", b0=4, b1=11, segs=[("s37", "#37", 1.10, 4, {}), ("s21", "#21", 0.45, 3, {})]),
    dict(name="PEEL THE FILM", b0=11, b1=17, segs=[("s26", "#26", 1.85, 3, {}), ("s27", "#27", 5.00, 3, {})]),
    dict(name="LAY THE FILM", b0=17, b1=24, segs=[("s32", "#32", 3.40, 7, {})]),
    dict(name="SQUEEGEE", b0=24, b1=31, segs=[("s33", "#33", 1.60, 4, {}), ("s25", "#25", 0.60, 3, {})]),
    dict(name="TRIM", b0=31, b1=38, segs=[("s38", "#38", 1.20, 4, {}), ("s40", "#40", 5.90, 3, {"zoom": (330, 1080, 440, 860, 1.35, 1.45)})]),
    dict(name="WRAP THE EDGES", b0=38, b1=44, segs=[("s35", "#35", 0.45, 3, {}), ("s22", "#22", 0.30, 3, {})]),
    dict(name="REVEAL", b0=48, b1=54, segs=[("r29", "#29", 1.00, 7, {"full": True})]),
]
LEAD, TAIL = 3.0, 1.5                            # beats of play wanted before / after a card's focus (clamped to the clip)


def plan():
    """Per segment: global play window (frames) and source in-point; freeze outside the window."""
    out = []
    for ci, c in enumerate(CARDS):
        b = c["b0"]
        for si, (key, clip, a, nb, ex) in enumerate(c["segs"]):
            first, last = si == 0, si == len(c["segs"]) - 1
            lead = min(LEAD, (a - 0.03) / BEAT) if first else 0.0
            tail_room = (DUR[clip] - 0.05 - (a + nb * BEAT)) / BEAT
            assert tail_room >= -1e-6, (key, "focus runs past the clip end")
            tail = min(TAIL, tail_room) if last else 0.0
            g0, g1 = b - lead, b + nb + tail             # play window in beats
            f0, f1 = fb(b) - int(lead * BEAT * OFPS), fb(g1)       # floor: never before src 0.03
            a0 = a - (fb(b) - f0) / OFPS                  # source time of the window's first frame (1.0x)
            out.append(dict(card=ci, key=key, clip=f"Clip {clip}.mp4", a_focus=a, a0=round(a0, 4), f0=f0, f1=f1, n=f1 - f0,
                            focus0=fb(b), focus1=fb(b + nb), beats=nb, **ex))
            b += nb
    return out


SEGS = plan()
# plate jobs for plates.py (graded R2, 1.0x, one folder per segment)
ADS = {f"F_{s['key']}": {"name": s["key"], "src": "src/mc20",
                         "shots": [dict(id=s["key"], clip=s["clip"], a=s["a0"], n=s["n"], speed=1.0, **({"zoom": s["zoom"]} if s.get("zoom") else {}))]}
       for s in SEGS}
# the music timeline (music.py): sections in beats, the reveal on bar 12, the end card from beat 54
ADS["ppf30"] = {"name": "ppf30", "shots": [
    dict(id="hook", clip=None, beats=4), dict(id="steps", clip=None, beats=40), dict(id="riser", clip=None, beats=4),
    dict(id="reveal", clip=None, beats=6, reveal=True), dict(id="end", clip=None, beats=10)]}


def timeline(ad):
    if ad["name"] != "ppf30":                      # plate jobs: one shot of n frames
        return [dict(x, f0=0, f1=x["n"], t0=0, t1=x["n"] / OFPS) for x in ad["shots"]], ad["shots"][0]["n"]
    out, b = [], 0
    for s in ad["shots"]:
        f0 = fb(b); b += s["beats"]; f1 = fb(b)
        out.append(dict(s, beat0=b - s["beats"], f0=f0, f1=f1, n=f1 - f0, t0=f0 / OFPS, t1=f1 / OFPS, dur=(f1 - f0) / OFPS))
    return out, out[-1]["f1"]


if __name__ == "__main__":
    print("frames", NF, "dur %.3f s" % (NF / OFPS))
    print("%-4s %-15s %-5s %-14s %-17s %-17s %s" % ("card", "step", "key", "clip", "on screen (focus)", "src focus in-out", "play window src"))
    for s in SEGS:
        c = CARDS[s["card"]]
        fi, fo = s["focus0"] / OFPS, s["focus1"] / OFPS
        print("%-4d %-15s %-5s %-14s %6.3f-%6.3f s   %6.3f-%6.3f s   %6.3f-%6.3f" % (s["card"], c["name"], s["key"], s["clip"], fi, fo,
              s["a_focus"], s["a_focus"] + (s["focus1"] - s["focus0"]) / OFPS, s["a0"], s["a0"] + (s["n"] - 1) / OFPS))
    wd = f"{T}/.work/F"; os.makedirs(wd, exist_ok=True)
    scene = {"nf": NF, "beat": BEAT, "fps": OFPS, "cards": [dict(name=c["name"], b0=c["b0"], b1=c["b1"]) for c in CARDS], "segs": SEGS}
    json.dump(scene, open(f"{wd}/scene.json", "w"), indent=1)
    open(f"{wd}/scene.js", "w").write("window.SCENE = " + json.dumps(scene) + ";\n")
