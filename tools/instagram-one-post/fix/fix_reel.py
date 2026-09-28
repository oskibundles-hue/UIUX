#!/usr/bin/env python3
"""Render the corrected Instagram file for "The floor goes down" from the 4K master.

    python3 fix_reel.py MASTER.mp4 OUT.mp4

Decodes the 2160x3840 master, scales it to 1080x1920, applies the three fixes in
patches.py, and encodes H.264 in two passes at the approved export's bitrate, so the
file stays under Instagram's 300 MB Reels limit. The master's audio is copied untouched.

Needs ffmpeg with libx264 on PATH (or FFMPEG=/path) and numpy, pillow, opencv-python-headless.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

import patches

W, H = 1080, 1920
MAX_BYTES = 300 * 1000 * 1000  # Instagram Reels limit
VIDEO_KBPS = 13200  # about the approved export's 13.8 Mbps; lands near 285 MB
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def check_master(path):
    info = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    if "2160x3840" not in info or "29.97 fps" not in info:
        sys.exit(f"{path} is not the 2160x3840 29.97 fps master:\n{info}")


def render(master, out, pass_no, passlog):
    """Run decode -> patch -> encode once. Returns frames seen and frames each fix touched."""
    dec = subprocess.Popen([
        FFMPEG, "-loglevel", "error", "-i", master, "-map", "0:v:0",
        "-vf", f"scale={W}:{H}:flags=bicubic+accurate_rnd+full_chroma_int"
               ":in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc_args = [
        FFMPEG, "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30000/1001", "-i", "-",
        "-vf", "scale=in_range=pc:out_color_matrix=bt709:out_range=tv:flags=accurate_rnd,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-b:v", f"{VIDEO_KBPS}k",
        "-maxrate", "25000k", "-bufsize", "50000k",
        "-pass", str(pass_no), "-passlogfile", passlog,
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    if pass_no == 1:
        enc_args += ["-an", "-f", "null", os.devnull]
    else:
        enc_args[enc_args.index("-vf"):enc_args.index("-vf")] = ["-i", master, "-map", "0:v", "-map", "1:a", "-c:a", "copy"]
        enc_args += ["-movflags", "+faststart", "-shortest", out]
    enc = subprocess.Popen(enc_args, stdin=subprocess.PIPE)

    fixes = {"lower_third": patches.LowerThird(), "callout": patches.Callout(), "caption": patches.Caption()}
    touched = {k: 0 for k in fixes}
    size = W * H * 3
    idx = 0
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        for name, fix in fixes.items():
            new = fix.apply(frame, idx)
            if new is not frame:
                touched[name] += 1
                frame = new
        enc.stdin.write(frame.tobytes())
        idx += 1
    enc.stdin.close()
    if dec.wait() or enc.wait():
        sys.exit(f"ffmpeg failed in pass {pass_no}")
    return idx, touched


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    master, out = sys.argv[1], sys.argv[2]
    check_master(master)
    with tempfile.TemporaryDirectory() as tmp:
        passlog = os.path.join(tmp, "x264")
        frames1, touched1 = render(master, out, 1, passlog)
        frames, touched = render(master, out, 2, passlog)
    report = {"frames": frames, "patched_frames": touched, "bytes": os.path.getsize(out)}
    print(json.dumps(report, indent=2))
    if (frames1, touched1) != (frames, touched):
        sys.exit(f"passes disagree: {frames1} {touched1}")
    if min(touched.values()) == 0:
        sys.exit(f"a fix touched no frames: {touched}")
    if report["bytes"] > MAX_BYTES:
        sys.exit(f"{out} is {report['bytes']} bytes, over Instagram's {MAX_BYTES}")


if __name__ == "__main__":
    main()
