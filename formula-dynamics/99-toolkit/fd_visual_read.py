#!/usr/bin/env python3
"""Read the visual grammar of reference clips: numpy and PIL only.

Answers three questions about a clip, in order, because each one narrows the
next: how often does it cut, where in the frame does it move, and what shape is
that movement. Written after an impression that TikTok reference means fast
cutting turned out to be wrong by a wide margin - the twelve clips behind
VISUAL-GRAMMAR.md cut between 0.00 and 0.71 times a second and one of them is
85% frozen frames.

    python3 fd_visual_read.py <dir-or-files>...
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
W, H, FPS = 192, 342, 12


def ffmpeg_bin() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if not found:
            sys.exit("no ffmpeg available")
        return found


def frames(path: Path) -> np.ndarray:
    raw = subprocess.run(
        [ffmpeg_bin(), "-nostdin", "-v", "quiet", "-i", str(path), "-vf",
         f"fps={FPS},scale={W}:{H}", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    n = len(raw) // (W * H * 3)
    if n == 0:
        return np.zeros((0, H, W, 3), np.float32)
    return (np.frombuffer(raw[:n * W * H * 3], np.uint8)
            .reshape(n, H, W, 3).astype(np.float32) / 255)


def read(path: Path):
    f = frames(path)
    if f.shape[0] < 8:
        return None
    g = f.mean(3)
    diff = np.abs(np.diff(g, axis=0))
    d = diff.mean((1, 2))
    dur = f.shape[0] / FPS

    cuts = int((d > max(0.10, d.mean() + 2.2 * d.std())).sum())
    frozen = float((d < 0.004).mean())

    rows = diff.mean((0, 2))
    bands = np.add.reduceat(rows, [0, H // 5, 2 * H // 5, 3 * H // 5, 4 * H // 5])
    share = bands / max(1e-9, bands.sum())

    band = int(rows.argmax())
    lo, hi = max(0, band - H // 12), min(H, band + H // 12)
    sub = diff[:, lo:hi, :]
    active = sub.mean(1) > sub.mean() * 1.2
    left, right = [], []
    for t in range(active.shape[0]):
        idx = np.where(active[t])[0]
        if idx.size:
            left.append(idx.min())
            right.append(idx.max())

    move = "too still to read"
    if len(left) >= 6:
        left, right = np.array(left), np.array(right)
        ls, rs = float(np.std(left) / W), float(np.std(right) / W)
        width = (right - left) / W
        trend = float(np.corrcoef(np.arange(width.size), width)[0, 1])
        # A reveal anchors one edge; growth from the centre moves both apart;
        # content swapping moves both without the width going anywhere.
        if rs > ls * 1.6:
            move = "type-on (anchored left)"
        elif ls > rs * 1.6:
            move = "reveal from the right"
        elif trend > 0.25:
            move = "scale-pop (grows in place)"
        elif abs(trend) < 0.15:
            move = "swap-in-place (content replaces itself)"
        else:
            move = "mixed"
    return dict(dur=dur, cuts=cuts / dur, frozen=frozen, share=share,
                band=band / H, move=move)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", type=Path)
    a = ap.parse_args()

    files = []
    for p in a.paths:
        if p.is_dir():
            files += [q for q in sorted(p.rglob("*"))
                      if q.suffix.lower() in VIDEO_EXT]
        elif p.suffix.lower() in VIDEO_EXT:
            files.append(p)

    got = [(p, read(p)) for p in files]
    got = [(p, r) for p, r in got if r]

    print(f"\n{'clip':22s} {'len':>6s} {'cuts/s':>7s} {'frozen':>7s}")
    for p, r in got:
        print(f"{p.stem[:22]:22s} {r['dur']:6.1f} {r['cuts']:7.2f} "
              f"{r['frozen']*100:6.0f}%")

    print(f"\n{'clip':22s} {'top':>6s} {'upper':>6s} {'mid':>6s} "
          f"{'lower':>6s} {'bottom':>6s}")
    for p, r in got:
        print(f"{p.stem[:22]:22s} " +
              " ".join(f"{s*100:5.1f}%" for s in r["share"]))

    print(f"\n{'clip':22s} {'band':>6s}  move")
    for p, r in got:
        print(f"{p.stem[:22]:22s} {r['band']:6.2f}  {r['move']}")
    print("\nA graphic concentrated in one band with still edges is the "
          "reference's own discipline: the graphic moves, the frame does not.")


if __name__ == "__main__":
    main()
