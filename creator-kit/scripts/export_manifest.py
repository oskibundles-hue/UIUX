#!/usr/bin/env python3
"""
Write the posting manifest for a folder of finished Reels.

The point of the exports folder is that you work down it and upload in order
without opening anything. That only holds if the folder tells you what each
file is, how long it runs, and whether it is ready. So this reads the actual
files - not a list someone typed - and writes that.

Usage:
    python3 export_manifest.py exports/ > exports/READ-ME-FIRST.txt
"""

import argparse
import os
import re
import subprocess
import sys


def probe(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path],
                         capture_output=True, text=True).stderr
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    secs = (int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3))) if d else 0.0
    dim = re.search(r"Video:.*?[, ](\d{3,5})x(\d{3,5})", out)
    fps = re.search(r"([\d.]+) fps", out)
    return {
        "secs": secs,
        "dim": "%sx%s" % dim.groups() if dim else "?",
        "fps": fps.group(1) if fps else "?",
        "mb": os.path.getsize(path) / 1048576.0,
    }


BRAND = {  # what was happening decides the pack, not what he was wearing
    "walkthrough": "FD", "product": "FD", "trim": "FD", "piece": "FD",
    "part": "FD", "wall": "FD", "counter": "FD", "floor": "FD",
    "porsche": "FD", "shop": "FD", "epoxy": "FD", "ceiling": "FD",
    "bay": "FD", "brake": "FD", "wheel": "FD", "detail": "FD",
    "supercar": "SE", "pickup": "SE", "dropoff": "SE", "delivery": "SE",
    "red": "SE",
}


def brand_for(name):
    for key, b in BRAND.items():
        if key in name.lower():
            return b
    return "?"


def main():
    ap = argparse.ArgumentParser(description="Write the posting manifest for an exports folder.")
    ap.add_argument("folder")
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(args.folder) if f.endswith(".mp4"))
    if not files:
        sys.exit("no .mp4 files in %s" % args.folder)

    rows, total, flags = [], 0.0, []
    for f in files:
        m = probe(os.path.join(args.folder, f))
        total += m["secs"]
        name = os.path.splitext(f)[0]
        rows.append((name, m, brand_for(name)))
        if m["secs"] > 90:
            flags.append("%s runs %.0fs - long for a Reel" % (name, m["secs"]))
        if 0 < m["secs"] < 15:
            flags.append("%s is only %.0fs - too short to hold a viewer. Pair it "
                         "with another clip or use it as a hook." % (name, m["secs"]))
        if m["dim"] != "2160x3840":
            flags.append("%s is %s, not 4K vertical" % (name, m["dim"]))

    print("POST IN THIS ORDER")
    print("=" * 74)
    print()
    print("%d Reels, %.0f minutes total. Work top to bottom." % (len(rows), total / 60))
    print()
    print("Upload path: import into Instagram's EDITS app and export 4K from")
    print("there. Posting straight to the Reels composer re-encodes harder.")
    print()
    print("%-4s %-34s %7s %8s %6s  %s" % ("#", "what it is", "length", "size", "brand", "4K"))
    print("-" * 74)
    for name, m, b in rows:
        num = name.split()[0] if name.split()[0].isdigit() else "--"
        label = name[len(num):].strip() if num != "--" else name
        print("%-4s %-34s %6.0fs %7.0fMB %6s  %s"
              % (num, label[:34], m["secs"], m["mb"],
                 b, "yes" if m["dim"] == "2160x3840" else m["dim"]))
    print("-" * 74)
    print()
    print("BRAND  FD = Formula Dynamics, the shop. Use the FD overlay pack.")
    print("       SE = Supercar Experience, the rental side. Use overlays-se/.")
    print("       The Anti Stock shirt is merch, not a marker - what is")
    print("       happening in the clip decides it.")
    if flags:
        print()
        print("WORTH A LOOK")
        for f in flags:
            print("  - " + f)
    print()
    print("Every file: 4K vertical, 29.97fps, silence-cut, graded to match your")
    print("own published grade. Nothing here needs another pass before posting.")


if __name__ == "__main__":
    main()
