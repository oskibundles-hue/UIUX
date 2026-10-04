"""FD PPF 30 s -- STYLE FRAMES for a new 3D / motion look (3 Oct 2026). Three directions, each a ~3 s motion test + a hero.
Every shot plays at 1.0x (no slow-mo below 1x: it smeared edges in earlier reviews). Source clips have no internal cuts
(ffmpeg scene > 0.25: none in #20 #22 #27 #32 #33 #37 #38), so no stray frames can get in.

On camera, per plate:
  A  a33  #33  orange squeegee pushing the water out from under the film (close, wet film)      -> SQUEEGEE
  B  b38  #38  blade drawn along the panel seam (close)                                          -> TRIM          (hero card)
     b33  #33  orange squeegee on the wet film                                                   -> SQUEEGEE      (card passing the lens)
     b22  #22  fingers working the film edge into the panel gap                                  -> WRAP THE EDGES (next card)
     b32  #32  hand flat on the wet film on the hood, spray bottle                               -> LAY THE FILM  (behind)
  C  c20  #20  hands at the hood's front-left corner, working the film round the edge            -> WRAP THE EDGES
"""
OFPS = 30000 / 1001
BPM = 128
BEAT = 60 / BPM
NF = 90                                   # 3.003 s motion tests

SHOTS = {
    "a33": dict(clip="Clip #33.mp4", a=0.90),
    "b38": dict(clip="Clip #38.mp4", a=0.40),
    "b33": dict(clip="Clip #33.mp4", a=0.60),
    "b22": dict(clip="Clip #22.mp4", a=0.30),
    "b32": dict(clip="Clip #32.mp4", a=3.20),
    "c20": dict(clip="Clip #20.mp4", a=0.50),
}
ADS = {k: {"name": k, "src": "src/mc20", "shots": [dict(v, id=k, n=NF, speed=1.0)]} for k, v in SHOTS.items()}


def timeline(ad):
    s = ad["shots"]
    return [dict(x, f0=0, f1=NF, t0=0, t1=NF / OFPS, dur=NF / OFPS) for x in s], NF
