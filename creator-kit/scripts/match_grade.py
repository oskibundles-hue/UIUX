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


def grey_point(pixels, curves=None):
    """Average colour of the near-neutral pixels.

    Whole-frame averages measure content, not cast. A shot with a red microfiber
    on the floor has a high red mean and nothing is wrong with it. What tells you
    the GRADE has gone warm is where the greys sit - the concrete, the shop
    walls, the black panelling. So only low-saturation mid-brightness pixels are
    counted, and those approximate the grey point.

    Chasing the whole-frame mean instead sent an earlier attempt at this in the
    wrong direction: it "corrected" clip 14 from +6.8 to +10.8."""
    tot = [0.0, 0.0, 0.0]
    cnt = 0
    for px in pixels:
        n = len(px) // 3
        for k in range(n):
            r, g, b = px[3 * k], px[3 * k + 1], px[3 * k + 2]
            if curves:
                r = curves[0][r]; g = curves[1][g]; b = curves[2][b]
            mx, mn = max(r, g, b), min(r, g, b)
            if mx - mn <= 26 and 35 <= (r + g + b) / 3.0 <= 210:
                tot[0] += r; tot[1] += g; tot[2] += b; cnt += 1
    if cnt < 200:
        return None
    return [x / cnt for x in tot]


def neutralise(curves, src_paths, ref_paths, grey_target=None):
    """Put this clip's greys where the reference's greys are.

    A white-balance nudge and nothing else: three numbers, clamped, applied on
    top of the tone curves. It cannot encode scene content, so a red object in
    shot stays red while the concrete goes back to grey."""
    src_px = [read_ppm(p) for p in src_paths]
    ref_px = [read_ppm(p) for p in ref_paths]
    want = grey_point(ref_px)
    if not want:
        print("  neutralise: reference has too few neutral pixels, skipped")
        return curves
    if grey_target is not None:
        # Aim the greys at a chosen R-B instead of the reference's own. The
        # reference sits at about +5.7 (a warm, shop-light look); a vlog grade
        # wants the concrete closer to grey, so the target is set lower while
        # the average level of the greys is left where the reference put it.
        mid = (want[0] + want[2]) / 2.0
        want = [mid + grey_target / 2.0, want[1], mid - grey_target / 2.0]

    # Iterate. Each pass is clamped so one odd clip cannot be re-tinted wholesale,
    # and applying a gain moves which pixels still count as near-neutral - so a
    # single pass lands short. Three passes took the worst clip of the session
    # from +6.8 to inside a point of neutral; one pass only reached +3.0.
    before = None
    for _ in range(3):
        have = grey_point(src_px, [[int(round(v)) for v in c] for c in curves])
        if not have:
            print("  neutralise: not enough neutral pixels, skipped")
            return curves
        if before is None:
            before = have
        gains = []
        for c in range(3):
            ratio = (want[c] / want[1]) / max(1e-6, have[c] / have[1])
            gains.append(min(1.15, max(0.87, ratio)))
        if max(abs(g - 1.0) for g in gains) < 0.005:
            break
        curves = [enforce_monotonic([min(255.0, max(0.0, v * gains[c])) for v in curves[c]])
                  for c in range(3)]
    after = grey_point(src_px, [[int(round(v)) for v in c] for c in curves]) or before
    print("  grey point R-B: %+.1f -> %+.1f  (reference %+.1f)"
          % (before[0] - before[2], after[0] - after[2], want[0] - want[2]))
    return curves


def main():
    ap = argparse.ArgumentParser(description="Copy a grade by histogram matching.")
    ap.add_argument("--ref", required=True, help="glob of reference PPM frames")
    ap.add_argument("--src", required=True, help="glob of source PPM frames")
    ap.add_argument("--out", required=True, help="output .cube path")
    ap.add_argument("--name", default=None)
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--strength", type=float, default=1.0,
                    help="0 = no change, 1 = full match, >1 exaggerates")
    ap.add_argument("--no-neutralise", action="store_true",
                    help="skip the grey-point white balance pass")
    ap.add_argument("--grey-target", type=float, default=None,
                    help="R-B of the neutral greys to aim for (default: the reference's own)")
    ap.add_argument("--lift", type=float, default=0.0,
                    help="raise the blacks: 0.03 lifts pure black to ~8/255, fading out by the mids")
    ap.add_argument("--knee", type=float, default=0.0,
                    help="soften the highlights: 0.1 rolls the top of the curve off gently")
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

    if not args.no_neutralise:
        curves = neutralise(curves, src_paths, ref_paths, args.grey_target)

    if args.lift > 0 or args.knee > 0:
        # Applied after the match so the tone shape is still the reference's;
        # these only bend the ends. Lift: milky blacks, weighted to the shadows
        # by (1-x)^2. Knee: pull the top down and ease into it, so bright
        # panels and reflections stop clipping to flat white.
        def bend(v):
            x = v / 255.0
            x = x + args.lift * (1.0 - x) ** 2
            if args.knee > 0:
                k = 1.0 - args.knee
                if x > k:
                    x = k + (x - k) / (1.0 + (x - k) / args.knee * 1.5)
            return min(255.0, max(0.0, x * 255.0))
        curves = [enforce_monotonic([bend(v) for v in c]) for c in curves]

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
