#!/usr/bin/env python3
"""Harvest engine and exhaust audio from the Formula Dynamics car clips.

The masters are 2160x3840 at ~49 Mbps, so each file is 130-560 MB and the
audio is interleaved — the whole thing has to come down to get the audio out.
Handled one at a time: download, extract, delete the video, move on.

ffmpeg cannot open these URLs through the agent proxy (it returns no streams,
which reads as "no audio" when the audio is fine), so curl fetches to disk
first.
"""
import os
import pathlib
import subprocess
import sys

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = pathlib.Path(__file__).parent
RAW = HERE / "assets" / "harvest-raw"
CDN = "https://d2ol7oe51mr4n9.cloudfront.net/user_3EmIbqAsNEPTa3GqLOpFdlVHf2Z"

# The clips with engine/exhaust content, from the "Anti Stock Downloads"
# artifact. Ordered smallest first so something useful lands early.
CLIPS = [
    ("wheels_off",          "0ddafd89-32e9-472e-b939-e6106c1c3c3a", 126),
    ("black_car_on_lift",   "fa9e0f32-51f3-4e52-bb1a-e912aecbef40", 256),
    ("gt3_rolling_in",      "38d449d8-0edc-45f6-ae15-218dc4e1fc80", 297),
    ("teal_brakes_ryft",    "3e3814d3-ece1-4432-b5b3-66da0c1d660f", 299),
    ("matte_black_wheels",  "688d2593-b4b0-4afb-8528-34e80625375d", 319),
    ("sf90_pulls_up",       "aed877d4-f282-4c2d-a47d-7246894bf42e", 431),
    ("red_supercar",        "f88c7a50-5672-4ac3-a63f-fbcbb9b64f87", 564),
]


def harvest(name, uid, mb):
    vid = RAW / f"_{name}.mp4"
    wav = RAW / f"{name}.wav"
    if wav.exists():
        return f"have {name}"

    url = f"{CDN}/{uid}.mp4"
    r = subprocess.run(["curl", "-sS", "-L", "--max-time", "900",
                        "-o", str(vid), url], capture_output=True)
    if r.returncode != 0 or not vid.exists() or vid.stat().st_size < 1_000_000:
        vid.unlink(missing_ok=True)
        return f"FAIL {name}: download ({r.stderr.decode()[:80]})"

    # full-quality audio, no resampling artefacts
    r = subprocess.run([FF, "-v", "error", "-y", "-i", str(vid),
                        "-vn", "-ac", "2", "-ar", "48000",
                        "-c:a", "pcm_s16le", str(wav)], capture_output=True)
    got = vid.stat().st_size / 1048576
    vid.unlink(missing_ok=True)            # reclaim immediately

    if r.returncode != 0 or not wav.exists():
        return f"FAIL {name}: extract ({r.stderr.decode()[:80]})"
    return f"ok   {name:22s} {got:6.1f} MB video -> {wav.stat().st_size/1048576:5.1f} MB wav"


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:]
    for name, uid, mb in CLIPS:
        if only and name not in only:
            continue
        print(harvest(name, uid, mb), flush=True)
    print("HARVEST COMPLETE", flush=True)
