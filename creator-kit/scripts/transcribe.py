#!/usr/bin/env python3
"""
transcribe.py - word-level transcripts for caption timing.

  transcribe.py <video|audio> [...] [-o outdir] [--model small.en]

Writes <outdir>/a<NN>.json for an input named "NN ....mp4" (else <stem>.json):
a list of segments, each with `text` and `words: [{w, s, e}]` in seconds.
Uses faster-whisper on CPU; the small.en model runs about 3x realtime on
four cores and is accurate enough on shop audio for word timing. Names and
brands still need a `fix` map in the assembler plan.
"""
import argparse, json, os, re, subprocess, tempfile

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+"); ap.add_argument("-o", "--outdir", default=".")
    ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    m = WhisperModel(a.model, device="cpu", compute_type="int8")
    os.makedirs(a.outdir, exist_ok=True)
    for src in a.inputs:
        stem = os.path.splitext(os.path.basename(src))[0]
        num = re.match(r"(\d{2})\b", stem)
        out = os.path.join(a.outdir, f"a{num[1]}.json" if num else f"{stem}.json")
        with tempfile.TemporaryDirectory() as td:
            wav = os.path.join(td, "a.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1",
                            "-ar", "16000", "-c:a", "pcm_s16le", wav], check=True)
            segs, _ = m.transcribe(wav, word_timestamps=True, vad_filter=True, beam_size=5)
            data = [{"start": s.start, "end": s.end, "text": s.text.strip(),
                     "words": [{"w": w.word.strip(), "s": w.start, "e": w.end} for w in (s.words or [])]}
                    for s in segs]
        json.dump(data, open(out, "w"), indent=1)
        print(f"{src} -> {out}  {len(data)} segments, {sum(len(s['words']) for s in data)} words")

if __name__ == "__main__":
    main()
