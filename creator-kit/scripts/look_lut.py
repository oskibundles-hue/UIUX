#!/usr/bin/env python3
"""
look_lut.py - build a look LUT from measured parameters.

Histogram matching copies tone but cannot copy saturation or split-toning,
which are cross-channel. This writes a .cube from explicit, measurable
controls so a reference look can be matched by numbers (see look_stats.py):

  --gamma G        midtone lift (G<1 brightens mids), applied to luma only
  --black B        crush: input values below B/255 go to 0, rest re-stretched
  --sat S          chroma multiplier (1 = unchanged)
  --sat-high S     extra chroma multiplier for highlights (Y>160)
  --shadow  dR dG dB   RGB offsets (0-255 units) blended in where Y<60
  --mid     dR dG dB   ... where 60<=Y<160
  --high    dR dG dB   ... where Y>=160
  --shoulder K     soft highlight roll-off strength (0 = none)

Operations, in order: black crush -> luma gamma -> shoulder -> saturation
-> band offsets. Written as a 33^3 cube for ffmpeg lut3d.
"""
import argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--name", default="look")
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--black", type=float, default=0.0)
    ap.add_argument("--sat", type=float, default=1.0)
    ap.add_argument("--sat-high", type=float, default=1.0)
    ap.add_argument("--shadow", type=float, nargs=3, default=[0,0,0])
    ap.add_argument("--mid", type=float, nargs=3, default=[0,0,0])
    ap.add_argument("--high", type=float, nargs=3, default=[0,0,0])
    ap.add_argument("--shoulder", type=float, default=0.0)
    ap.add_argument("--size", type=int, default=33)
    a = ap.parse_args()

    def luma(r,g,b): return 0.2126*r+0.7152*g+0.0722*b
    def band_w(y):
        # smooth weights for shadow / mid / high around 60 and 160 (of 255)
        y255 = y*255
        s = 1/(1+math.exp((y255-60)/12)); h = 1/(1+math.exp((160-y255)/18))
        return s, max(0.0, 1-s-h), h

    def tx(r,g,b):
        # black crush + restretch
        if a.black > 0:
            k = a.black/255
            r,g,b = [max(0.0,(c-k)/(1-k)) for c in (r,g,b)]
        y = luma(r,g,b)
        if y > 0:
            y2 = y ** a.gamma
            if a.shoulder > 0:
                # roll highlights toward 1 softly
                y2 = y2 - a.shoulder * max(0.0, y2-0.6)**2
            f = y2 / y
            r,g,b = r*f, g*f, b*f
        y = luma(r,g,b)
        sw, mw, hw = band_w(y)
        sat = a.sat * (1 + (a.sat_high-1)*hw)
        r,g,b = [y + (c-y)*sat for c in (r,g,b)]
        off = [(a.shadow[i]*sw + a.mid[i]*mw + a.high[i]*hw)/255 for i in range(3)]
        r,g,b = r+off[0], g+off[1], b+off[2]
        return [min(1.0, max(0.0, c)) for c in (r,g,b)]

    n = a.size-1
    with open(a.out,"w") as f:
        f.write(f'# {a.name}\nTITLE "{a.name}"\nLUT_3D_SIZE {a.size}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n\n')
        for bi in range(a.size):
            for gi in range(a.size):
                for ri in range(a.size):
                    r,g,b = tx(ri/n, gi/n, bi/n)
                    f.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
    print("wrote", a.out)

if __name__ == "__main__":
    main()
