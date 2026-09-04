#!/usr/bin/env python3
"""
Copy a grade from a reference video by matching histograms.

Given frames from a reference (an already-graded clip whose look you want) and
frames from a source (raw or log footage), this builds the per-channel tone
curves that push the source's colour distribution onto the reference's, and
writes them as a .cube LUT.

This is how you copy a look you cannot get the recipe for: instead of guessing
at contrast and saturation values, you measure where the reference actually
puts its shadows, midtones and highlights in each channel, and move the source
to match.

Both sets should come from similar content - same location, lighting and
subject. Matching histograms across genuinely different scenes transfers the
scene's colour distribution, not its grade.

Pure standard library. Frames are PPM (P6), which ffmpeg writes directly:
    ffmpeg -ss 5 -i clip.mp4 -frames:v 1 -vf scale=216:384 -pix_fmt rgb24 f.ppm

Usage:
    python3 match_grade.py --ref "hm/ref_*.ppm" --src "hm/src_*.ppm" \
                           --out matched.cube --name My_Look
"""

import argparse
import glob
import os


def read_ppm(path):
    data = open(path, "rb").read()
    if data[:2] != b"P6":
        raise SystemExit("%s is not a P6 PPM" % path)
    i, vals = 2, []
    while len(vals) < 3:
        while data[i] in b" \t\r\n":
            i += 1
        if data[i:i + 1] == b"#":
            while data[i] not in b"\n":
                i += 1
            continue
        s = i
        while data[i] not in b" \t\r\n":
            i += 1
        vals.append(int(data[s:i]))
    i += 1
    w, h, _ = vals
    return data[i:i + w * h * 3]


def histogram(paths):
    """Per-channel 256-bin histogram over every sampled frame."""
    hist = [[0] * 256 for _ in range(3)]
    for p in paths:
        px = read_ppm(p)
        for o in range(0, len(px), 3):
            hist[0][px[o]] += 1
            hist[1][px[o + 1]] += 1
            hist[2][px[o + 2]] += 1
    return hist


def cdf(h):
    total = sum(h) or 1
    out, run = [0.0] * 256, 0
    for i in range(256):
        run += h[i]
        out[i] = run / total
    return out


def build_map(src_cdf, ref_cdf):
    """For each source level, the reference level at the same percentile."""
    mapping, j = [0] * 256, 0
    for i in range(256):
        target = src_cdf[i]
        while j < 255 and ref_cdf[j] < target:
            j += 1
        mapping[i] = j
    return mapping


def smooth(mapping, passes=3):
    """Light smoothing so sparse histogram bins don't produce a jagged curve.

    Endpoints are pinned: without that, repeated smoothing walks black and
    white inward and the grade loses its range.
    """
    m = list(mapping)
    for _ in range(passes):
        out = list(m)
        for i in range(1, 255):
            out[i] = (m[i - 1] + 2 * m[i] + m[i + 1]) / 4.0
        out[0], out[255] = m[0], m[255]
        m = out
    return m


def enforce_monotonic(m):
    """A tone curve that dips produces posterised gradients. Clamp it."""
    out, prev = [], -1.0
    for v in m:
        v = max(v, prev)
        out.append(v)
        prev = v
    return out


def main():
    ap = argparse.ArgumentParser(description="Copy a grade by histogram matching.")
    ap.add_argument("--ref", required=True, help="glob of reference PPM frames")
    ap.add_argument("--src", required=True, help="glob of source PPM frames")
    ap.add_argument("--out", required=True, help="output .cube path")
    ap.add_argument("--name", default=None)
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--strength", type=float, default=1.0,
                    help="0 = no change, 1 = full match, >1 exaggerates")
    args = ap.parse_args()

    ref_paths = sorted(glob.glob(args.ref))
    src_paths = sorted(glob.glob(args.src))
    if not ref_paths or not src_paths:
        raise SystemExit("no frames matched (ref: %d, src: %d)" % (len(ref_paths), len(src_paths)))
    print("reference frames: %d   source frames: %d" % (len(ref_paths), len(src_paths)))

    ref_h, src_h = histogram(ref_paths), histogram(src_paths)
    curves = []
    for c in range(3):
        m = build_map(cdf(src_h[c]), cdf(ref_h[c]))
        m = enforce_monotonic(smooth(m))
        if args.strength != 1.0:
            m = [i + (v - i) * args.strength for i, v in enumerate(m)]
            m = enforce_monotonic([min(255.0, max(0.0, v)) for v in m])
        curves.append(m)

    for name, m in zip("RGB", curves):
        print("  %s curve: black %5.1f  mid %5.1f  white %5.1f" % (name, m[0], m[128], m[255]))

    size, n = args.size, args.size - 1
    title = args.name or os.path.splitext(os.path.basename(args.out))[0]

    def apply(curve, x):
        # x in 0..1 -> interpolate the 256-entry curve -> 0..1
        p = x * 255.0
        lo = int(p)
        hi = min(255, lo + 1)
        f = p - lo
        return (curve[lo] * (1 - f) + curve[hi] * f) / 255.0

    with open(args.out, "w") as f:
        f.write("# %s\n# Grade copied from a reference by per-channel histogram matching.\n" % title)
        f.write('TITLE "%s"\n' % title)
        f.write("LUT_3D_SIZE %d\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n\n" % size)
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    f.write("%.6f %.6f %.6f\n" % (apply(curves[0], r / n),
                                                  apply(curves[1], g / n),
                                                  apply(curves[2], b / n)))
    print("wrote %s (%d^3, %.0f KB)" % (args.out, size, os.path.getsize(args.out) / 1024.0))


if __name__ == "__main__":
    main()
