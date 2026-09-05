#!/usr/bin/env python3
"""Measure the look of a set of PPM frames: luma percentiles, saturation by
band, and colour balance (R-B, G-(R+B)/2) in shadows / mids / highlights."""
import glob, sys, colorsys

def load(p):
    d = open(p, "rb").read()
    parts = d.split(maxsplit=4)
    w, h = int(parts[1]), int(parts[2]); px = parts[4][:w*h*3]; px = px[:len(px)//3*3]
    return [(px[i], px[i+1], px[i+2]) for i in range(0, len(px), 3)]

def stats(paths):
    pix = []
    for p in paths: pix += load(p)[::3]
    ys = sorted(0.2126*r+0.7152*g+0.0722*b for r,g,b in pix)
    n = len(ys)
    pct = {k: ys[int(n*k/100)] for k in (1,5,25,50,75,95,99)}
    bands = {"shadow": [], "mid": [], "high": []}
    for r,g,b in pix:
        y = 0.2126*r+0.7152*g+0.0722*b
        k = "shadow" if y < 60 else "mid" if y < 160 else "high"
        mx, mn = max(r,g,b), min(r,g,b)
        sat = (mx-mn)/mx if mx else 0
        bands[k].append((r-b, g-(r+b)/2, sat, mx-mn))
    out = {"luma": pct}
    for k, v in bands.items():
        if not v: continue
        m = len(v)
        out[k] = {"R-B": sum(x[0] for x in v)/m, "G-mag": sum(x[1] for x in v)/m,
                  "sat": sum(x[2] for x in v)/m, "chroma": sum(x[3] for x in v)/m, "n": m}
    return out

if __name__ == "__main__":
    for g in sys.argv[1:]:
        s = stats(sorted(glob.glob(g)))
        print(g)
        print("  luma pct:", {k: round(v) for k,v in s["luma"].items()})
        for k in ("shadow","mid","high"):
            if k in s:
                b = s[k]; print(f"  {k:<7} R-B {b['R-B']:+5.1f}  G-mag {b['G-mag']:+5.1f}  sat {b['sat']:.3f}  chroma {b['chroma']:5.1f}  n={b['n']}")
