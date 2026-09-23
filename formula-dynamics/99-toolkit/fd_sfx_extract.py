#!/usr/bin/env python3
"""Pull one-shot sound effects out of reference video, using numpy and PIL only.

The kit has seventeen sounds and every ad is built from the same handful, so
the obvious way to widen it is to lift hits out of the reference clips the shop
already collects. This does that: it finds the discrete hits in a soundtrack,
cuts them clean, measures each one and sorts it into the families fd_sfx.py
speaks in - tick, impact, whoosh, sub.

    python3 fd_sfx_extract.py <dir-or-files>... -o out/
    python3 fd_sfx_extract.py ... --audition        # one file to judge by ear

RIGHTS COME FIRST. Anything cut out of a downloaded video is someone else's
audio. A generic UI tick is unlikely to trouble anyone; a distinctive sound
design, a music sting or a voice is a different matter, and an ad running for a
paying client is the wrong place to find out. Nothing this produces goes into
the shipping kit until the shop says where the source came from and that it may
be used commercially. The classifier rejects speech on purpose, which reduces
the risk and does not remove it.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import shutil
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".wav", ".m4a", ".mp3"}
MAX_HIT = 1.2          # seconds; anything still going at the cap is not a hit


def ffmpeg_bin() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if not found:
            sys.exit("no ffmpeg available")
        return found


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(
        [ffmpeg_bin(), "-nostdin", "-v", "quiet", "-i", str(path),
         "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True).stdout
    return np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0


def slice_hits(x: np.ndarray, stem: str):
    """Cut at a sharp rise, then follow the tail down to near silence.

    A fixed-length window would chop a long impact and pad a short tick. The
    tail is followed to 8% of the hit's own peak instead, and faded over the
    last 20 ms so a cut slice does not click when it is dropped into a bed.
    """
    hop = 256
    n = x.size // hop
    if n < 4:
        return []
    env = np.abs(x[:n * hop].reshape(n, hop)).max(1)
    sm = np.convolve(env, np.ones(3) / 3, mode="same")
    d = np.diff(sm, prepend=sm[0])
    thr = max(d.std() * 3.0, 0.02)

    picks, last = [], -999
    for i in np.where((d > thr) & (sm > 0.05))[0]:
        if (i - last) * hop / SR > 0.25:
            picks.append(int(i))
            last = i

    out = []
    for k, i in enumerate(picks):
        start = max(0, (i - 2) * hop)
        lim = min(n, i + int(MAX_HIT * SR / hop))
        peak = sm[i:lim].max() if lim > i else 0.0
        j = i
        while j < lim - 1 and sm[j] > peak * 0.08:
            j += 1
        seg = x[start:min(x.size, (j + 3) * hop)]
        if seg.size < int(0.03 * SR) or np.abs(seg).max() < 0.06:
            continue
        seg = seg.copy()
        f = min(seg.size // 4, int(0.02 * SR))
        if f > 0:
            seg[-f:] *= np.linspace(1, 0, f)
        out.append((f"{stem}-{k + 1:02d}", seg / np.abs(seg).max() * 0.95))
    return out


def features(seg: np.ndarray) -> dict:
    dur = seg.size / SR
    S = np.abs(np.fft.rfft(seg * np.hanning(seg.size)))
    f = np.fft.rfftfreq(seg.size, 1 / SR)
    P = S / (S.sum() + 1e-9)
    hop = 256
    n = seg.size // hop
    env = np.abs(seg[:n * hop].reshape(n, hop)).max(1) if n else np.array([0.0])
    pk = int(env.argmax())
    tail = env[pk:]
    half = (float(np.argmax(tail < tail[0] * 0.5)) * hop / SR
            if (tail < tail[0] * 0.5).any() else dur)
    return {
        "dur": round(dur, 3),
        "centroid": round(float((f * P).sum())),
        "halflife": round(half, 3),
        # Spectral flatness: noise sits near 1, a tone near 0. Separates a
        # whoosh from a musical stab.
        "flatness": round(float(np.exp(np.log(S + 1e-9).mean())
                                / (S.mean() + 1e-9)), 4),
        "voiceband": round(float(P[(f >= 300) & (f <= 3400)].sum()), 3),
    }


def classify(r: dict):
    """Family, or None with the reason it was rejected."""
    if r["dur"] >= MAX_HIT and r["halflife"] > 0.15:
        return None, "sustained - music or room, not a hit"
    if r["voiceband"] > 0.60 and r["halflife"] > 0.10:
        return None, "speech-like"
    if r["halflife"] > 0.35:
        return None, "never decays"
    if r["dur"] < 0.05:
        return None, "too short to use"
    c, d = r["centroid"], r["dur"]
    if c < 700:
        return "sub", None
    if c > 4200 and d < 0.30:
        return "tick", None
    if r["flatness"] > 0.09 and 0.15 < d < 0.90:
        return "whoosh", None
    if d < 0.45:
        return "impact", None
    return None, "unclassified"


def write_wav(path: Path, seg: np.ndarray):
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((seg * 32767).astype("<i2").tobytes())


def audition(kept: dict, src: Path, dest: Path, per_family=8):
    """One file: a marker tone, then that family's sounds, spaced to compare."""
    def beep(f, dur=0.10):
        t = np.arange(int(SR * dur)) / SR
        return (np.sin(2 * np.pi * f * t) * np.hanning(t.size) * 0.25
                ).astype(np.float32)

    out = np.zeros(0, dtype=np.float32)
    for fam, tone in (("tick", 1400), ("impact", 900),
                      ("whoosh", 1100), ("sub", 500)):
        names = kept.get(fam, [])[:per_family]
        if not names:
            continue
        out = np.concatenate([out, beep(tone),
                              np.zeros(int(SR * 0.25), dtype=np.float32)])
        for n in names:
            with wave.open(str(src / f"{n}.wav")) as w:
                x = np.frombuffer(w.readframes(w.getnframes()),
                                  "<i2").astype(np.float32) / 32768
            out = np.concatenate([out, x,
                                  np.zeros(int(SR * 0.35), dtype=np.float32)])
        out = np.concatenate([out, np.zeros(int(SR * 0.7), dtype=np.float32)])
    if out.size:
        write_wav(dest, out / np.abs(out).max() * 0.9)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("sfx-candidates"))
    ap.add_argument("--audition", action="store_true")
    a = ap.parse_args()

    hits_dir = a.out / "hits"
    hits_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for p in a.paths:
        if p.is_dir():
            files += [q for q in sorted(p.rglob("*"))
                      if q.suffix.lower() in VIDEO_EXT]
        elif p.suffix.lower() in VIDEO_EXT:
            files.append(p)

    rows, kept, dropped = [], {}, {}
    for p in files:
        x = load(p)
        if x.size == 0:
            print(f"  {p.name:28s} no audio")
            continue
        made = slice_hits(x, p.stem)
        for name, seg in made:
            r = features(seg)
            fam, why = classify(r)
            r.update(name=name, source=p.name, family=fam or "",
                     rejected=why or "")
            rows.append(r)
            if fam:
                write_wav(hits_dir / f"{name}.wav", seg)
                kept.setdefault(fam, []).append(name)
            else:
                dropped[why] = dropped.get(why, 0) + 1
        print(f"  {p.name:28s} {x.size/SR:6.1f}s -> {len(made):3d} cut")

    if rows:
        with (a.out / "CANDIDATES.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    json.dump(kept, (a.out / "kept.json").open("w"), indent=1)

    total = sum(len(v) for v in kept.values())
    print(f"\nkept {total} of {len(rows)}")
    for fam in sorted(kept):
        print(f"  {fam:8s} {len(kept[fam])}")
    for why, n in sorted(dropped.items(), key=lambda kv: -kv[1]):
        print(f"  rejected: {why}  x{n}")

    if a.audition and total:
        audition(kept, hits_dir, a.out / "_audition.wav")
        print(f"\n  {a.out / '_audition.wav'}")

    print("\nNothing here enters the kit until the shop confirms the source "
          "may be used commercially.")


if __name__ == "__main__":
    main()
