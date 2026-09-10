#!/usr/bin/env python3
"""Master a finished cut's audio to one loudness spec.

Every ad in a set gets posted next to every other one. If one is at -9.7 LUFS
and the next is at -20.7, the viewer reaches for the volume between them, and
the quiet one just sounds cheap. The first service set measured an **11 dB
spread**, three cuts peaking **above 0 dBFS** (that is clipping, not loudness),
and two with no audio track at all because the downscale dropped it.

So the level is not left to whatever the source happened to be:

    -14 LUFS integrated   what Instagram, TikTok and YouTube all normalise to.
                          Louder than this and the platform turns it down
                          anyway; quieter and it stays quiet next to everyone
                          else's.
    -1.0 dBTP ceiling     true peak, so the lossy encode the platform applies
                          on top has somewhere to go without distorting.
    stereo, 48 kHz        one format across the set. Mixed sample rates were
                          the other thing the first pass shipped.

Two passes, because one-pass loudnorm guesses: the first measures the file, the
second applies the correction it actually needs.

    python3 fd_master.py <folder>          # every mp4 in it, in place
    python3 fd_master.py <folder> -o <out> # write elsewhere
    python3 fd_master.py a.mp4 b.mp4       # named files
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

TARGET_I = -14.0
TARGET_TP = -1.0
TARGET_LRA = 11.0


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def has_audio(path):
    r = subprocess.run([ffmpeg(), "-i", str(path)], capture_output=True, text=True)
    return "Audio:" in r.stderr


def measure(path):
    """Pass one - what is actually in the file."""
    r = subprocess.run(
        [ffmpeg(), "-nostdin", "-i", str(path), "-af",
         f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return None
    return json.loads(m.group(0))


def master(path, out=None):
    path = Path(path)
    if not has_audio(path):
        print(f"skip  {path.name}  - no audio track to master")
        return False

    st = measure(path)
    if not st:
        print(f"skip  {path.name}  - could not measure")
        return False

    before_i, before_tp = st["input_i"], st["input_tp"]
    dest = Path(out) if out else path.with_suffix(".mastered.mp4")

    af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
          f":measured_I={st['input_i']}:measured_TP={st['input_tp']}"
          f":measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}"
          f":offset={st['target_offset']}:linear=true:print_format=summary")

    subprocess.run(
        [ffmpeg(), "-nostdin", "-y", "-i", str(path),
         "-af", af, "-ar", "48000", "-ac", "2",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(dest), "-loglevel", "error"], check=True)

    if not out:
        dest.replace(path)
        dest = path
    after = measure(dest)
    print(f"ok    {path.name}\n"
          f"        {float(before_i):+7.1f} LUFS -> {float(after['input_i']):+7.1f}   "
          f"peak {float(before_tp):+5.1f} -> {float(after['input_tp']):+5.1f} dBTP")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+", help="mp4 files, or a folder of them")
    ap.add_argument("-o", "--out-dir", help="write mastered copies here instead")
    a = ap.parse_args()

    files = []
    for t in a.targets:
        p = Path(t)
        files.extend(sorted(p.glob("*.mp4")) if p.is_dir() else [p])
    if not files:
        sys.exit("nothing to master")

    outdir = Path(a.out_dir) if a.out_dir else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    print(f"  Mastering {len(files)} file(s) to {TARGET_I} LUFS / {TARGET_TP} dBTP\n")
    done = sum(master(f, outdir / f.name if outdir else None) for f in files)
    print(f"\n  {done}/{len(files)} mastered.")
