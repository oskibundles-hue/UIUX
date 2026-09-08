#!/usr/bin/env python3
"""Tell Omarie's voice from everyone else's, per transcript segment.

  build:  who_speaks.py build <audio> <transcript.json> [--not start-end ...] -o profile.json
          Everything in the transcript is him except the --not ranges (clip seconds).
  tag:    who_speaks.py tag <audio> <transcript.json> --profile profile.json [--threshold 0.72] [-o drop.json]
          Prints one line per segment with its similarity, writes drop.json with the ranges that are not him.

Segments are the transcript's own (faster-whisper) segments; each is embedded with
Resemblyzer's speaker encoder and compared to the profile by cosine similarity."""
import sys, json, subprocess, argparse, os
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav

def load_audio(path):
    raw = subprocess.run(["/root/bin/ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def segments(tx):
    d = json.load(open(tx)); out = []
    for s in d:
        if s["end"] - s["start"] >= 0.8: out.append((float(s["start"]), float(s["end"]), s.get("text", "").strip()))
    return out

def embed_all(enc, wav, segs):
    embs = []
    for a, b, _ in segs:
        piece = wav[int(a * 16000):int(b * 16000)]
        if len(piece) < 16000 * 0.6: embs.append(None); continue
        embs.append(enc.embed_utterance(preprocess_wav(piece, source_sr=16000)))
    return embs

def overlaps(a, b, ranges): return any(lo < b and a < hi for lo, hi in ranges)

ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["build", "tag"]); ap.add_argument("audio"); ap.add_argument("transcript")
ap.add_argument("--not", dest="not_ranges", nargs="*", default=[]); ap.add_argument("--profile"); ap.add_argument("--threshold", type=float, default=0.70); ap.add_argument("-o", "--out")
a = ap.parse_args()
enc = VoiceEncoder("cpu", verbose=False); wav = load_audio(a.audio); segs = segments(a.transcript); embs = embed_all(enc, wav, segs)
if a.mode == "build":
    nots = [tuple(map(float, r.split("-"))) for r in a.not_ranges]
    his = [e for (s, e_, _), e in zip(segs, embs) if e is not None and not overlaps(s, e_, nots)]
    others = [e for (s, e_, _), e in zip(segs, embs) if e is not None and overlaps(s, e_, nots)]
    prof = np.mean(his, axis=0); prof /= np.linalg.norm(prof)
    old = json.load(open(a.profile)) if a.profile and os.path.exists(a.profile) else None
    if old:  # blend with an existing profile so it keeps learning
        prof = (np.array(old["embedding"]) * old["n"] + prof * len(his)); prof /= np.linalg.norm(prof)
    json.dump({"embedding": prof.tolist(), "n": (old["n"] if old else 0) + len(his)}, open(a.out, "w"))
    sims_h = [float(np.dot(prof, e)) for e in his]; sims_o = [float(np.dot(prof, e)) for e in others]
    print(f"profile from {len(his)} of his segments; his similarity {min(sims_h):.2f}-{max(sims_h):.2f}; others {['%.2f' % x for x in sims_o]}")
else:
    prof = np.array(json.load(open(a.profile))["embedding"]); drop = []
    for (s, e_, text), e in zip(segs, embs):
        sim = float(np.dot(prof, e)) if e is not None else float("nan")
        him = (e is None) or sim >= a.threshold
        print(f"{s:6.1f}-{e_:6.1f}  {sim:5.2f}  {'HIM  ' if him else 'OTHER'}  {text[:70]}")
        if not him: drop.append([round(s - 0.05, 2), round(e_ + 0.05, 2)])
    if a.out: json.dump(drop, open(a.out, "w")); print("wrote", a.out, len(drop), "ranges")
