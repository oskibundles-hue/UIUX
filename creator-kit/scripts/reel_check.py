#!/usr/bin/env python3
"""
reel_check.py - pre-flight virality check for a finished Reel.

Scores the things Instagram's ranking actually rewards and that can be
measured from the file: watch-time structure (length, hook speed, shot
rhythm), caption coverage for muted viewers, loudness, exposure, and the
delivery spec. It cannot see whether the content is interesting; it tells
you whether the packaging is getting in the way of it.

Usage:
  reel_check.py reel.mp4 [--props props.json] [--json out.json]

--props is the Remotion props file written by assemble_reel.py; it carries the
cut list and word timings, which are exact. Without it, cuts come from scene
detection and speech from a silence scan, which are close enough.

Only ffmpeg is needed (no ffprobe).
"""
import argparse, json, re, subprocess, sys

FFMPEG = "ffmpeg"

def run(args):
    return subprocess.run([FFMPEG, "-hide_banner", *args], capture_output=True, text=True).stderr

def probe(path):
    err = run(["-i", path])
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+).*?bitrate: (\d+) kb/s", err)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    v = re.search(r"Video: (\w+).*?(\d{3,4})x(\d{3,4}).*?([\d.]+) fps", err)
    return {"duration": dur, "kbps": int(m[4]), "codec": v[1], "w": int(v[2]), "h": int(v[3]), "fps": float(v[4])}

def loudness(path):
    err = run(["-i", path, "-vn", "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    j = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    return float(j["input_i"]), float(j["input_tp"]), float(j["input_lra"])

def speech(path):
    err = run(["-i", path, "-vn", "-af", "silencedetect=n=-30dB:d=0.35", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return starts, ends

def scene_cuts(path, dur):
    # Sample at 1080 wide for speed; scene score is resolution-independent enough.
    err = run(["-i", path, "-an", "-vf", "scale=540:-2,select='gt(scene,0.35)',showinfo", "-f", "null", "-"])
    ts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", err)]
    return [0.0] + [t for t in ts if t > 0.5]

def exposure(path, dur, n=9):
    vals = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        err = run(["-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=96:-2,signalstats", "-f", "null", "-"])
        m = re.findall(r"YAVG:([\d.]+)", err)
        if m: vals.append(float(m[-1]))
    return vals

def clamp(x, lo=0, hi=1): return max(lo, min(hi, x))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--props"); ap.add_argument("--json")
    a = ap.parse_args()

    p = probe(a.video)
    dur = p["duration"]
    props = json.load(open(a.props)) if a.props else {}
    flags, scores = [], {}

    # 1. Length. Trial Reels reach non-followers; 30-60s is the sweet spot for
    # a shop vlog: long enough to earn a send, short enough to be finished.
    if dur < 15: s = 0.5; flags.append(f"{dur:.0f}s is short - little watch time to bank")
    elif dur <= 60: s = 1.0
    elif dur <= 90: s = 0.8
    elif dur <= 180: s = 0.55; flags.append(f"{dur:.0f}s - completion rate will sag past 90s")
    else: s = 0.2; flags.append(f"{dur:.0f}s - over 3 minutes is not recommended to new viewers")
    scores["length"] = s

    # 2. Hook: something has to happen in the first second.
    hook_text = bool(props.get("hook"))
    words = props.get("words") or []
    if words: first_speech = words[0]["start"]
    else:
        st, en = speech(a.video)
        first_speech = (en[0] if st and st[0] < 0.2 and en else 0.0)
    cuts = [c["at"] for c in props.get("cuts", [])] or scene_cuts(a.video, dur)
    first_cut = next((c for c in cuts if c > 0.3), dur)
    hook = 0.35 if hook_text else 0.0
    hook += 0.35 * clamp(1 - max(0, first_speech - 1.0) / 4)
    hook += 0.30 * clamp(1 - max(0, first_cut - 3.0) / 5)
    scores["hook"] = clamp(hook)
    if not hook_text and first_speech > 1.5: flags.append(f"nothing on screen or said until {first_speech:.1f}s - add a text hook at 0s")
    if first_cut > 5: flags.append(f"first cut at {first_cut:.1f}s - opening shot is long")

    # 3. Rhythm: the reference edit changes shot about every 4s.
    edges = sorted(set(cuts + [dur]))
    shots = [b - a_ for a_, b in zip(edges, edges[1:]) if b - a_ > 0.2]
    avg = sum(shots) / len(shots) if shots else dur
    longest = max(shots) if shots else dur
    r = clamp(1 - abs(avg - 4.5) / 6) * 0.6 + clamp(1 - max(0, longest - 8) / 10) * 0.4
    scores["rhythm"] = r
    if longest > 10: flags.append(f"longest shot {longest:.1f}s - cut it or put text on it")
    if avg > 7: flags.append(f"average shot {avg:.1f}s - slow for a vertical feed")

    # 4. Captions: most viewers are muted.
    if words:
        covered = sum(w["end"] - w["start"] for w in words)
        st, en = speech(a.video)
        silent = sum(max(0, (e - s)) for s, e in zip(st, en))
        spoken = max(0.1, dur - silent)
        cov = clamp(covered / spoken)
        gaps = [q["start"] - w["end"] for w, q in zip(words, words[1:])]
        scores["captions"] = 0.7 * cov + 0.3 * (1 if len(words) / dur > 1.2 else 0.6)
        if cov < 0.6: flags.append(f"captions cover {cov*100:.0f}% of speech")
    else:
        scores["captions"] = 0.0; flags.append("no caption data - muted viewers get nothing")

    # 5. Loudness: Instagram normalises, but a quiet or clipped master still
    # comes out worse. Target around -14 LUFS, true peak under -1 dBTP.
    lufs, tp, lra = loudness(a.video)
    ls = clamp(1 - abs(lufs + 14) / 8) * 0.7 + (0.3 if tp <= -0.5 else 0.05)
    scores["loudness"] = ls
    if lufs < -20: flags.append(f"quiet: {lufs:.1f} LUFS (target -14)")
    if tp > -0.5: flags.append(f"true peak {tp:.1f} dBTP - clipping risk")

    # 6. Exposure: dark frames read as 'nothing happening' in the feed.
    ys = exposure(a.video, dur)
    dark = sum(1 for y in ys if y < 40) / max(1, len(ys))
    scores["exposure"] = clamp(1 - dark * 1.5)
    if dark > 0.2: flags.append(f"{dark*100:.0f}% of sampled frames are dark (Y<40)")

    # 7. Delivery spec.
    spec = 1.0
    if (p["w"], p["h"]) not in [(1080, 1920), (2160, 3840)]: spec -= 0.4; flags.append(f"{p['w']}x{p['h']} is not 9:16 delivery size")
    if p["kbps"] < 9000: spec -= 0.3; flags.append(f"{p['kbps']/1000:.1f} Mbps is starving 4K (floor 10)")
    if abs(p["fps"] - 29.97) > 0.2 and abs(p["fps"] - 30) > 0.2: spec -= 0.3; flags.append(f"{p['fps']} fps")
    scores["spec"] = clamp(spec)

    weights = {"length": 15, "hook": 25, "rhythm": 15, "captions": 20, "loudness": 8, "exposure": 7, "spec": 10}
    total = sum(scores[k] * weights[k] for k in weights)
    verdict = "post it" if total >= 80 else "fix the flags first" if total >= 60 else "rework"

    print(f"\n{a.video}")
    print(f"  {dur:.1f}s  {p['w']}x{p['h']}  {p['fps']} fps  {p['kbps']/1000:.1f} Mbps  {lufs:.1f} LUFS  {tp:.1f} dBTP")
    print(f"  first speech {first_speech:.1f}s  first cut {first_cut:.1f}s  shots {len(shots)} avg {avg:.1f}s longest {longest:.1f}s  caption words {len(words)}")
    print()
    for k in weights:
        bar = "#" * int(scores[k] * 20)
        print(f"  {k:<9} {scores[k]*100:5.0f}  {bar}")
    print(f"\n  SCORE {total:.0f}/100  -  {verdict}")
    for f in flags: print(f"  ! {f}")
    if a.json:
        json.dump({"score": total, "verdict": verdict, "scores": scores, "flags": flags,
                   "probe": p, "lufs": lufs, "true_peak": tp, "first_speech": first_speech,
                   "first_cut": first_cut, "shots": shots}, open(a.json, "w"), indent=1)

if __name__ == "__main__":
    main()
