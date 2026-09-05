#!/usr/bin/env python3
"""
assemble_reel.py - join ordered segments from finished exports into one Reel
master, and carry the word-level captions across onto the new timeline.

Plan file (JSON):
{
  "fps": 29.97,
  "segments": [
    {"clip": "exports/09 gt3 rolling in.mp4", "words": "trial/a09.json",
     "in": 38.9, "out": 42.7, "captions": true}
  ],
  "fix": {"Astin": "Aston", "Thanks": "That's"}
}

`words` is the faster-whisper JSON written by transcribe.py (segments with
word timings, in the clip's own timeline). Every word whose midpoint falls
inside [in, out] is shifted onto the assembled timeline. Punctuation is
stripped because the reference captions carry none.

Usage:
  assemble_reel.py plan.json out.mp4 props.json [--crf 14]

Segments are re-encoded (frame-accurate cuts; stream copy would snap to
keyframes) in one ffmpeg pass with the concat filter, so the master is a
single generation away from the exports.
"""
import argparse, json, os, re, subprocess, sys

def load_words(path):
    out = []
    for seg in json.load(open(path)):
        out.extend(seg.get("words", []))
    return out

def clean(word, fix):
    w = word.strip()
    core = re.sub(r"^[^\w']+|[^\w']+$", "", w)
    return fix.get(core, core)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("out"); ap.add_argument("props")
    ap.add_argument("--crf", type=float, default=14)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    plan = json.load(open(a.plan))
    fix = plan.get("fix", {})
    fps = plan.get("fps", 29.97)
    segs = plan["segments"]

    inputs, vparts, aparts, words, cuts = [], [], [], [], []
    t = 0.0
    clip_index = {}
    for i, s in enumerate(segs):
        clip = s["clip"]
        if clip not in clip_index:
            clip_index[clip] = len(inputs); inputs.append(clip)
        k = clip_index[clip]
        d = s["out"] - s["in"]
        if d <= 0: sys.exit(f"segment {i}: out <= in")
        vparts.append(f"[{k}:v]trim=start={s['in']}:end={s['out']},setpts=PTS-STARTPTS[v{i}]")
        aparts.append(f"[{k}:a]atrim=start={s['in']}:end={s['out']},asetpts=PTS-STARTPTS[a{i}]")
        if s.get("captions", True) and s.get("words"):
            for w in load_words(s["words"]):
                mid = (w["s"] + w["e"]) / 2
                if s["in"] <= mid <= s["out"]:
                    txt = clean(w["w"], fix)
                    if not txt: continue
                    words.append({
                        "text": txt,
                        "start": round(max(0, w["s"] - s["in"]) + t, 3),
                        "end": round(min(d, w["e"] - s["in"]) + t, 3),
                    })
        cuts.append({"at": round(t, 3), "clip": os.path.basename(clip),
                     "in": s["in"], "out": s["out"]})
        t += d

    # Words from whisper can overlap by a frame or two; make them monotonic.
    for p, q in zip(words, words[1:]):
        if q["start"] < p["end"]:
            p["end"] = q["start"]
    for w in words:
        if w["end"] - w["start"] < 0.08: w["end"] = w["start"] + 0.08

    chain = "".join(f"[v{i}][a{i}]" for i in range(len(segs)))
    fc = ";".join(vparts + aparts) + f";{chain}concat=n={len(segs)}:v=1:a=1[v][a]"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-y"]
    for p in inputs: cmd += ["-i", p]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out]

    props = {"src": os.path.basename(a.out), "words": words, "phrases": [],
             "durationSeconds": round(t, 3), "cuts": cuts}
    json.dump(props, open(a.props, "w"), indent=1)
    print(f"{len(segs)} segments, {t:.2f}s, {len(words)} caption words, {len(inputs)} sources")
    if a.dry:
        print(" ".join(cmd)); return
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
