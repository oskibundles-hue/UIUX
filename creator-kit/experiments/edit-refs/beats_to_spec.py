#!/usr/bin/env python3
"""
Cut-on-hits for the car-only teaser (the @olafmotion / @jonasblk_ reference):
turn a list of drum-hit times into a Kinetic Cut spec, so the existing
builder (../kinetic/build_kinetic.py) does the mono grade, letterbox, white
flashes and smears. Nothing here re-implements those.

Every shot starts on a hit and runs to the next one. --flash puts a one-frame
white flash on each hit (taken out of the shot, so timing does not drift).
No type: the spec points at an empty type script, so the piece is car-only.

    python3 beats_to_spec.py --beats hits.txt --clips "MC20 a.mp4@4.0" "MC20 b.mp4@12.5" ... \\
        --audio-track bed.wav --flash --out spec_mc20.json

hits.txt: one time in seconds per line (a "# comment" or a second column is
ignored), measured on the music bed from its start. build_kinetic.py plays the
bed from 0, so hit times are kept as they are; if the first hit is after 0, a
lead-in shot (the first clip) fills the gap.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIN = os.path.normpath(os.path.join(HERE, "..", "kinetic"))


def read_beats(path):
    out = []
    for line in open(path):
        line = line.split("#")[0].strip().replace(",", " ")
        if line:
            out.append(float(line.split()[0]))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--beats", required=True)
    ap.add_argument("--clips", nargs="+", required=True, help="clip file names in --footage, each @in-point; cycled with in-points advanced")
    ap.add_argument("--audio-track", required=True, help="the music bed the hits were measured on")
    ap.add_argument("--max-seconds", type=float, default=20.0)
    ap.add_argument("--tail", type=float, default=1.0, help="seconds held after the last hit")
    ap.add_argument("--flash", action="store_true", help="1-frame white flash on every hit")
    ap.add_argument("--fps", type=int, default=30, help="build_kinetic.py takes an integer rate")
    ap.add_argument("--band-top", type=float, default=0.34, help="constant letterbox top edge (fraction of height); bottom stays 0.658")
    ap.add_argument("--saturation", type=float, default=0.0, help="0 = full B&W")
    ap.add_argument("--contrast", type=float, default=1.35)
    ap.add_argument("--brightness", type=float, default=-0.02)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    beats = read_beats(a.beats)
    if len(beats) < 2:
        raise SystemExit("need at least two hits")
    beats = [b for b in beats if b <= a.max_seconds + 1e-6]
    if a.tail > 0:
        beats.append(beats[-1] + a.tail)
    lead_in = beats[0] > 1e-3
    if lead_in:
        beats = [0.0] + beats          # lead-in shot up to the first hit (not itself a hit)
    clips = []
    for c in a.clips:
        p, t = c.rsplit("@", 1) if "@" in c else (c, "0")
        clips.append((p, float(t)))

    shots = []
    fr = 1.0 / a.fps
    for i in range(len(beats) - 1):
        dur = beats[i + 1] - beats[i]
        p, t = clips[i % len(clips)]
        t_in = t + (i // len(clips)) * 1.0   # cycling: move the in-point on 1 s per pass
        on_hit = not (lead_in and i == 0)
        if a.flash and on_hit and dur > 3 * fr:
            shots.append({"fx": "flash", "frames": 1})
            dur -= fr
        shots.append({"clip": p, "in": round(t_in, 3), "dur": round(dur, 4)})
    total = beats[-1]

    empty = os.path.splitext(os.path.abspath(a.out))[0] + "_type.json"
    json.dump([], open(empty, "w"))
    spec = {
        "name": "car-only teaser (cut on hits)",
        "font": os.path.join(HERE, "..", "..", "remotion", "public", "fonts", "Archivo.ttf"),
        "bug": os.path.join(KIN, "bug_nq.png"),
        "accent": "#FFFFFF",
        "type_script": empty,
        "grade": {"saturation": a.saturation, "contrast": a.contrast,
                  "brightness": a.brightness, "gamma": a.gamma},
        "band": {"bottom": 0.658, "top": [[0.0, a.band_top], [total, a.band_top]]},
        "audio_track": os.path.abspath(a.audio_track),
        "shots": shots,
    }
    json.dump(spec, open(a.out, "w"), indent=1)
    print(f"{a.out}: {len([s for s in shots if 'clip' in s])} shots over {total:.2f}s")


if __name__ == "__main__":
    main()
