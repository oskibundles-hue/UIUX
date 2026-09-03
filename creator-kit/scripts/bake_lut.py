#!/usr/bin/env python3
"""
Bake an ffmpeg filter chain into a .cube LUT.

Renders the cube's lattice points as an image, pushes that image through the
given ffmpeg filter chain, and reads the result back. Whatever the chain does
to colour becomes a LUT you can import into CapCut, DJI Mimo, Resolve or
Premiere - no ffmpeg needed at edit time.

Only per-pixel colour operations bake correctly. Spatial filters (denoise,
sharpen, blur) depend on neighbouring pixels and must stay in your edit as
separate steps; they are silently meaningless here.

Usage:
    python3 bake_lut.py --chain "curves=all='0/0 0.5/0.6 1/1',eq=saturation=1.5" \
                        --out mylook.cube --name My_Look [--size 33]
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def write_identity_ppm(path, size):
    """Lattice points in .cube order: red fastest, blue slowest.

    Laid out as `size` columns by size*size rows so the read-back is a
    straight sequential scan.
    """
    w, h = size, size * size
    n = size - 1
    rows = []
    for b in range(size):
        for g in range(size):
            row = bytearray()
            for r in range(size):
                row += bytes((round(r * 255 / n), round(g * 255 / n), round(b * 255 / n)))
            rows.append(bytes(row))
    with open(path, "wb") as f:
        f.write(b"P6\n%d %d\n255\n" % (w, h))
        f.write(b"".join(rows))


def read_ppm(path):
    data = open(path, "rb").read()
    if data[:2] != b"P6":
        raise SystemExit("expected a P6 PPM from ffmpeg, got %r" % data[:16])
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
    return w, h, data[i:i + w * h * 3]


def main():
    ap = argparse.ArgumentParser(description="Bake an ffmpeg filter chain into a .cube LUT.")
    ap.add_argument("--chain", required=True, help="ffmpeg -vf filter chain (colour ops only)")
    ap.add_argument("--out", required=True, help="output .cube path")
    ap.add_argument("--name", default=None, help="LUT title (defaults to the filename)")
    ap.add_argument("--size", type=int, default=33, help="cube size per axis (default 33)")
    ap.add_argument("--note", default=None, help="comment line written into the header")
    args = ap.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found on PATH")

    size = args.size
    title = args.name or os.path.splitext(os.path.basename(args.out))[0]
    tmp = tempfile.mkdtemp(prefix="bakelut-")
    src, dst = os.path.join(tmp, "id.ppm"), os.path.join(tmp, "out.ppm")

    try:
        write_identity_ppm(src, size)
        # -pix_fmt rgb24 keeps the round trip in RGB; going through YUV would
        # add a colour-space conversion that is not part of the chain.
        proc = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-i", src,
             "-vf", args.chain, "-pix_fmt", "rgb24", dst],
            capture_output=True, text=True)
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr)
            raise SystemExit("ffmpeg failed on the filter chain")

        w, h, px = read_ppm(dst)
        if (w, h) != (size, size * size):
            raise SystemExit("chain changed the image geometry (%dx%d); "
                             "remove any scale/crop/pad from it" % (w, h))

        with open(args.out, "w") as f:
            f.write("# %s\n" % title)
            if args.note:
                f.write("# %s\n" % args.note)
            f.write("# Baked from ffmpeg chain:\n# %s\n" % args.chain)
            f.write('TITLE "%s"\n' % title)
            f.write("LUT_3D_SIZE %d\n" % size)
            f.write("DOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n\n")
            for i in range(size * size * size):
                o = i * 3
                f.write("%.6f %.6f %.6f\n" % (px[o] / 255.0, px[o + 1] / 255.0, px[o + 2] / 255.0))

        print("wrote %s  (%d^3, %.0f KB)" % (args.out, size, os.path.getsize(args.out) / 1024.0))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
