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


def phrases_in(segs, a, b):
    """How many separate phrases fall in the window. This matters as much as
    total speech: a window holding one unbroken 60-second monologue has nothing
    for the silence cutter to remove, so it exports as a single 60s shot with
    none of the ~4s rhythm the edit is supposed to reproduce. Scoring on speech
    alone actively seeks those windows out, because the densest talking is by
    definition the part with the fewest pauses."""
    return sum(1 for s, e in segs if e > a and s < b and min(e, b) - max(s, a) > 0.15)


def window_score(segs, a, b, want_phrases=8):
    """Speech, discounted when the window has too few phrases to cut between."""
    talk = speech_in(segs, a, b)
    n = phrases_in(segs, a, b)
    return talk * min(1.0, n / float(want_phrases))


def best_window(segs, total, window, step=1.0):
    """Slide a window of `window` seconds and keep the position holding the most
    speech. Ties go to the earlier position, which favours the setup over the
    tail - a viewer needs the context before the payoff."""
    if total <= window:
        return 0.0, total
    best_t, best_v = 0.0, -1.0
    t = 0.0
    while t + window <= total:
        v = window_score(segs, t, t + window)
        if v > best_v + 1e-9:
            best_v, best_t = v, t
        t += step
    return best_t, window


def candidates(segs, total, window, step=1.0, k=8):
    """The k best window positions by speech, spread out so they are genuinely
    different sections rather than eight views of the same moment."""
    if total <= window:
        return [(0.0, total)]
    scored = []
    t = 0.0
    while t + window <= total:
        scored.append((window_score(segs, t, t + window), t))
        t += step
    scored.sort(reverse=True)
    picked = []
    for v, t in scored:
        if all(abs(t - p) >= window * 0.5 for p in picked):
            picked.append(t)
        if len(picked) >= k:
            break
    return [(t, window) for t in picked]


def picture_score(ff, path, start, length, samples=9):
    """Is there anything to look at? Mean brightness and how much of the luma
    range is in use, sampled across the window.

    Two things this had to learn. Five samples over sixty seconds walked straight
    past a dark stretch that was only a few seconds long but sat at the end of
    the window, so the count is higher now. And the thresholds are set for LOG
    footage, not graded: D-Log M sits around mean 90-110 with a wide spread, so
    "dark" here means well under that, not under mid-grey. The worst frame is
    weighted as well as the average - one dead patch in an otherwise good window
    is still a dead patch on screen."""
    import os
    import tempfile
    scores = []
    with tempfile.TemporaryDirectory() as td:
        for i in range(samples):
            t = start + length * (i + 0.5) / samples
            g = os.path.join(td, "s%d.pgm" % i)
            subprocess.run([ff, "-v", "error", "-y", "-ss", "%.3f" % t, "-i", path,
                            "-frames:v", "1", "-vf", "scale=64:114", "-pix_fmt", "gray", g],
                           capture_output=True)
            if not os.path.exists(g):
                continue
            d = open(g, "rb").read()
            j, tok = 0, []
            try:
                while len(tok) < 4:
                    nl = d.index(b"\n", j); tok += d[j:nl].split(); j = nl + 1
            except ValueError:
                continue
            px = d[j:]
            if not px:
                continue
            mean = sum(px) / len(px)
            spread = max(px) - min(px)
            # Below ~18 mean the frame is essentially unusable on a phone in
            # daylight; a spread under ~60 is a flat wall or a covered lens.
            # Log mid-grey is ~90-110; below ~55 the frame has nothing in it.
            bright = min(1.0, max(0.0, (mean - 12.0) / 55.0))
            contrast = min(1.0, spread / 120.0)
            frame = bright * contrast
            scores.append(frame)
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    worst = min(scores)
    # Half the weight on the average, half on the worst frame: a window that is
    # good for fifty seconds and black for ten is not a good window.
    return 0.5 * avg + 0.5 * worst


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
    ap.add_argument("--check-picture", action="store_true",
                    help="also sample frames and reject windows with nothing to look at")
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

    if args.check_picture and total > args.window:
        cands = candidates(segs, total, args.window, args.step)
        best, best_score = None, -1.0
        for c_start, c_len in cands:
            talk = window_score(segs, c_start, c_start + c_len)
            npf = phrases_in(segs, c_start, c_start + c_len)
            pic = picture_score(ff, args.input, c_start, c_len)
            score = talk * (0.25 + 0.75 * pic)
            if args.report:
                sys.stderr.write("    candidate %6.1fs: %2d phrases, score %5.1f, picture %.2f -> %.1f\n"
                                 % (c_start, npf, talk, pic, score))
            if score > best_score:
                best_score, best = score, (c_start, c_len)
        start, length = best
    else:
        start, length = best_window(segs, total, args.window, args.step)
    start, length = snap(segs, start, length)

    if args.report:
        talk = speech_in(segs, start, start + length)
        overall = sum(e - s for s, e in segs)
        sys.stderr.write(
            "    clip %.0fs, %.0fs of speech in %d phrases\n"
            "    window %.1f-%.1fs holds %.0fs of speech in %d phrases "
            "(%.0f%% of the window)\n"
            % (total, overall, len(segs), start, start + length, talk,
               phrases_in(segs, start, start + length), 100 * talk / length))

    print("%.3f %.3f" % (start, length))


if __name__ == "__main__":
    main()
