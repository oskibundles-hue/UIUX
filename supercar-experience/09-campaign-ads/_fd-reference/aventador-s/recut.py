#!/usr/bin/env python3
"""
Assemble a new footage plate by re-ordering the source shots.

`06-video-system/AUTO-EDIT.md` says the overlay tool does not cut footage — it
adds the graphics layer to a clip you already cut. This is the missing half: it
cuts. Given a list of shot ids from shots.json it trims each one and concatenates
them into a new plate, which a cue file in cuts/ then points at.

    python3 recut.py cuts/cue-detail-walk.json      # build that cut's plate
    python3 recut.py --all                          # every cut in cuts/
    python3 recut.py --list                         # print the shot list

AUDIO: the engine note in the source runs continuously, so splicing it with the
picture would jump at every cut. Instead the plate takes an unbroken audio bed
from the head of the source, trimmed to the new length. It stays smooth under a
re-ordered picture, and it is meant to sit under music anyway.
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = json.load(open(os.path.join(HERE, "shots.json")))
SOURCE = os.path.join(HERE, SHOTS["source"])


def ffmpeg_bin():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def shot(i):
    for s in SHOTS["shots"]:
        if s["id"] == i:
            return s
    sys.exit(f"no shot with id {i}")


def build_plate(cue_path):
    cue = json.load(open(cue_path))
    order = cue.get("shotOrder")
    if not order:
        sys.exit(f"{cue_path} has no shotOrder — nothing to re-cut")

    plate = os.path.join(HERE, cue["plate"])
    os.makedirs(os.path.dirname(plate), exist_ok=True)
    ff = ffmpeg_bin()
    work = os.path.join(HERE, ".recut")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)

    total = 0.0
    parts = []
    print(f'{cue.get("cut", os.path.basename(cue_path))}:')
    for n, sid in enumerate(order):
        s = shot(sid)
        dur = round(s["out"] - s["in"], 3)
        seg = os.path.join(work, f"{n:03d}.mp4")
        # re-encode each segment so the concat is frame-exact at the cut points
        subprocess.run([
            ff, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(s["in"]), "-t", str(dur), "-i", SOURCE,
            "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
            "-pix_fmt", "yuv420p", "-vsync", "cfr", "-r", str(cue["fps"]), seg,
        ], check=True)
        parts.append(seg)
        total += dur
        print(f"  {n + 1:2d}. shot {sid:2d}  {dur:5.2f}s  {s['label']}")

    listfile = os.path.join(work, "list.txt")
    with open(listfile, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")

    silent = os.path.join(work, "picture.mp4")
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", listfile,
                    "-c", "copy", silent], check=True)

    # continuous audio bed from the head of the source (see module docstring)
    subprocess.run([
        ff, "-y", "-hide_banner", "-loglevel", "error",
        "-i", silent, "-t", str(round(total, 3)), "-i", SOURCE,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", plate,
    ], check=True)
    shutil.rmtree(work, ignore_errors=True)

    print(f"  -> {os.path.relpath(plate, HERE)}  ({total:.2f}s)")
    if abs(total - cue["duration"]) > 0.05:
        print(f"  ! cue duration is {cue['duration']}s but the shots total "
              f"{total:.2f}s — update the cue file's duration and beats")
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cue", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        print(f"{SHOTS['source']}\n")
        for s in SHOTS["shots"]:
            print(f"  {s['id']:2d}  {s['in']:6.2f} - {s['out']:6.2f}  "
                  f"({s['out'] - s['in']:.2f}s)  {s['label']}")
        return

    cues = sorted(glob.glob(os.path.join(HERE, "cuts", "*.json"))) if args.all \
        else [os.path.abspath(args.cue)] if args.cue else []
    if not cues:
        ap.error("pass a cue file, or --all, or --list")
    for c in cues:
        build_plate(c)


if __name__ == "__main__":
    main()
