#!/usr/bin/env python3
"""
speech_window - find the most talkative stretch of a long take.

A nine-minute take silence-cut end to end is a seven-minute file. That is not a
Reel, and it is not what you would ever upload. What you actually want out of a
long take is its best sixty seconds.

"Best" has to be computable or it is just a guess. In a build vlog the signal is
speech: the strongest stretch is where you are talking most continuously, not
where the room is quiet and the camera is drifting. So this slides a window over
the clip and returns the one containing the most speech, with its edges snapped
to phrase boundaries so the Reel does not open or close mid-word.

Reads only the audio, so it runs in seconds on a multi-gigabyte 4K file.

Prints:  START LENGTH   (seconds, both floats)

Usage:
    python3 speech_window.py source.mov --window 60 --noise -22
"""

import argparse
import re
import shutil
import subprocess
import sys


def duration(ff, path):
    out = subprocess.run([ff, "-hide_banner", "-i", path],
                         capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    if not m:
        raise SystemExit("could not read duration from %s" % path)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def speech_segments(ff, path, noise, min_silence, total):
    """Everything that is not detected silence, as (start, end) pairs."""
    out = subprocess.run(
        [ff, "-hide_banner", "-vn", "-i", path,
         "-af", "silencedetect=noise=%ddB:d=%.2f" % (noise, min_silence),
         "-f", "null", "-"],
        capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.-]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.-]+)", out)]
    segs, cursor = [], 0.0
    for i, s in enumerate(starts):
        s = max(0.0, s)
        if s > cursor:
            segs.append((cursor, s))
        cursor = ends[i] if i < len(ends) else total
    if cursor < total:
        segs.append((cursor, total))
    return [(a, b) for a, b in segs if b - a > 0.05]


def speech_in(segs, a, b):
    return sum(max(0.0, min(e, b) - max(s, a)) for s, e in segs)


def best_window(segs, total, window, step=1.0):
    """Slide a window of `window` seconds and keep the position holding the most
    speech. Ties go to the earlier position, which favours the setup over the
    tail - a viewer needs the context before the payoff."""
    if total <= window:
        return 0.0, total
    best_t, best_v = 0.0, -1.0
    t = 0.0
    while t + window <= total:
        v = speech_in(segs, t, t + window)
        if v > best_v + 1e-9:
            best_v, best_t = v, t
        t += step
    return best_t, window


def snap(segs, start, length):
    """Pull the edges onto phrase boundaries so the window neither starts nor
    ends mid-sentence. Only ever shrinks inward, never grows past the window."""
    end = start + length
    inside = [(s, e) for s, e in segs if e > start and s < end]
    if not inside:
        return start, length
    first, last = inside[0], inside[-1]
    new_start = first[0] if first[0] >= start else start
    new_end = last[1] if last[1] <= end else end
    if new_end - new_start < length * 0.5:
        return start, length
    return new_start, new_end - new_start


def main():
    ap = argparse.ArgumentParser(description="Find the most talkative window of a clip.")
    ap.add_argument("input")
    ap.add_argument("--window", type=float, default=60.0,
                    help="target window length in seconds (default 60)")
    ap.add_argument("--noise", type=int, default=-22, help="silence threshold in dB")
    ap.add_argument("--min-silence", type=float, default=0.25)
    ap.add_argument("--step", type=float, default=1.0, help="slide granularity")
    ap.add_argument("--report", action="store_true", help="explain the choice on stderr")
    args = ap.parse_args()

    ff = shutil.which("ffmpeg")
    if not ff:
        raise SystemExit("ffmpeg not found on PATH")

    total = duration(ff, args.input)
    segs = speech_segments(ff, args.input, args.noise, args.min_silence, total)
    if not segs:
        print("0.000 %.3f" % min(total, args.window))
        return

    start, length = best_window(segs, total, args.window, args.step)
    start, length = snap(segs, start, length)

    if args.report:
        talk = speech_in(segs, start, start + length)
        overall = sum(e - s for s, e in segs)
        sys.stderr.write(
            "    clip %.0fs, %.0fs of speech in %d phrases\n"
            "    window %.1f-%.1fs holds %.0fs of speech (%.0f%% of the window, "
            "%.0f%% of everything you said)\n"
            % (total, overall, len(segs), start, start + length, talk,
               100 * talk / length, 100 * talk / overall if overall else 0))

    print("%.3f %.3f" % (start, length))


if __name__ == "__main__":
    main()
