#!/usr/bin/env python3
"""
Re-master a finished video's audio the Anti Stock way and copy the picture:
two-pass loudnorm I=-14 TP=-1.5 LRA=11, then alimiter limit=0.84 level=false
(the chain in creator-kit/scripts/compose_reel.sh). For outputs of tools whose
audio is not mastered, e.g. build_kinetic.py with an audio_track.

    python3 master_loudness.py IN.mp4 OUT.mp4 [--trim-audio SECONDS]

--trim-audio drops that much from the head of the audio first (use the
offset beats_to_spec.py prints when the first hit is not at 0 on the bed).
"""
import argparse, os, sys, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media as M  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--trim-audio", type=float, default=0.0)
    a = ap.parse_args()
    info = M.probe(a.src)
    x = M.read_audio(a.src)
    n = int(round(info["duration"] * M.SR))
    s = int(round(a.trim_audio * M.SR))
    x = np.pad(x[s:], ((0, max(0, n - len(x[s:]))), (0, 0)))[:n]
    with tempfile.TemporaryDirectory() as d:
        raw, mst = os.path.join(d, "raw.wav"), os.path.join(d, "master.wav")
        M.write_wav(raw, x)
        m = M.master_audio(raw, mst)
        M.mux(a.src, mst, a.out)
    j = M.loudness(a.out)
    print(f"{a.out}: in {m['input_i']} LUFS -> {j['input_i']} LUFS, true peak {j['input_tp']} dBTP")


if __name__ == "__main__":
    main()
