#!/usr/bin/env python3
"""
match_reference.py - reproduce a reference edit's timing with your own footage.

Takes the reference measured shot by shot (length, luminance, motion) and a
library of moments from your own clips measured the same way, and fills every
slot in the reference with the moment that best matches it.

Matching is on light and movement, not subject, because those are what carry an
edit's rhythm: when the reference flares bright for two frames, the rebuild
flares bright for two frames. Shots whose measured motion is extreme are not
footage at all in the reference -- they are whip transitions -- so those slots
become RGB smears, and near-white slots become flash frames.

No moment is used twice, and a moment within `--spacing` seconds of one already
used in the same clip is skipped, so the rebuild does not keep returning to the
same few seconds of footage.
"""
import argparse, json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="measured reference shots")
    ap.add_argument("--lib", required=True, help="measured moments from your own clips")
    ap.add_argument("--out", required=True)
    ap.add_argument("--smear-motion", type=float, default=90, help="above this the reference slot is a whip, not a shot")
    ap.add_argument("--flash-bright", type=float, default=0.55, help="above this fraction of near-white the slot is a flash")
    ap.add_argument("--spacing", type=float, default=3.0, help="seconds to keep clear around a used moment")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--flash-frames", default=None,
                    help="JSON list of reference frame numbers that are a single white frame")
    ap.add_argument("--card-from", type=int, default=None,
                    help="reference frame where the piece cuts to a flat end card")
    ap.add_argument("--card-colour", default="0x3E3E3E")
    a = ap.parse_args()

    ref = json.load(open(a.ref))
    lib = json.load(open(a.lib))
    flashes = set(json.load(open(a.flash_frames))) if a.flash_frames else set()
    used = []                      # (clip, t) already spent
    shots, angle = [], 0

    for r in ref:
        frames = int(round(r["dur"] * a.fps))
        if a.card_from is not None and r["f"] >= a.card_from:
            shots.append({"fx": "card", "frames": frames, "colour": a.card_colour})
            continue
        # a single white frame on the cut: the reference does this at most cuts in
        # the strobe, and it is most of why the strobe reads as an assault
        if r["f"] in flashes and frames > 1 and r["bright"] < a.flash_bright:
            shots.append({"fx": "flash", "frames": 1})
            frames -= 1
        if r["bright"] >= a.flash_bright:
            shots.append({"fx": "flash", "frames": frames})
            continue
        if r["mot"] >= a.smear_motion and shots:
            shots.append({"fx": "smear", "frames": frames, "angle": angle})
            angle ^= 1
            continue
        best, score = None, None
        for m in lib:
            if any(m["clip"] == c and abs(m["t"] - t) < a.spacing for c, t in used):
                continue
            # light first, movement second: an edit's pulse is mostly luminance
            s = abs(m["lum"] - r["lum"]) + 0.35 * abs(m["mot"] - min(r["mot"], 60))
            if shots and shots[-1].get("clip") == m["clip"]:
                s += 12                     # prefer cutting between clips
            if score is None or s < score:
                best, score = m, s
        if best is None:
            raise SystemExit("ran out of unused footage - lower --spacing or add clips")
        used.append((best["clip"], best["t"]))
        shots.append({"clip": best["clip"], "in": best["t"], "frames": frames})

    json.dump(shots, open(a.out, "w"), indent=1)
    kinds = {}
    for s in shots:
        kinds[s.get("fx", "shot")] = kinds.get(s.get("fx", "shot"), 0) + 1
    total = sum(s["frames"] for s in shots) / a.fps
    print(f"{len(shots)} slots, {total:.2f}s, {kinds}")


if __name__ == "__main__":
    main()
