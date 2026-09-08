#!/usr/bin/env python3
"""Fold the best of Kenney's CC0 recordings into the FD pack.

Kenney's libraries are game assets — most of the 753 files (lasers, footsteps,
space engines, casino chips, jingles) are wrong for a luxury automotive ad.
But the mechanical recordings are real, and real beats synthesised for
switches, metal impacts and clicks: the irregularity of an actual object
being struck is exactly what synthesis approximates badly.

The reverse holds for the cinematic layer. Kenney has no sub drops, no long
risers, no drones — so those stay designed.

Selections below were picked by measuring duration, peak and spectral
centroid across 71 candidates, not by name.
"""
import os
import pathlib
import subprocess

import numpy as np
import imageio_ffmpeg
from scipy.io import wavfile

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = pathlib.Path(__file__).parent
KEN = HERE / "assets" / "kenney"
OUT = HERE / "assets" / "sfx-fd"
SR = 48000

# target name -> (source file, why)
PICKS = {
    "k_impact_plate":  ("impact-sounds/Audio/impactPlate_heavy_001.ogg",
                        "steel plate, centroid 82 Hz — real low-end body"),
    "k_impact_plate2": ("impact-sounds/Audio/impactPlate_heavy_003.ogg",
                        "alternate plate strike, 97 Hz"),
    "k_impact_metal":  ("impact-sounds/Audio/impactMetal_heavy_002.ogg",
                        "tight metal hit, 800 Hz"),
    "k_impact_sub":    ("sci-fi-sounds/Audio/impactMetal_001.ogg",
                        "41 Hz — the deepest usable recording in the set"),
    "k_switch_heavy":  ("interface-sounds/Audio/switch_003.ogg",
                        "chunky mechanical throw, 242 Hz"),
    "k_switch_mid":    ("interface-sounds/Audio/switch_004.ogg",
                        "lighter switch, 996 Hz"),
    "k_click_tight":   ("interface-sounds/Audio/click_003.ogg",
                        "10 ms transient, 2 kHz"),
    "k_click_low":     ("interface-sounds/Audio/click_005.ogg",
                        "low click, 361 Hz"),
    "k_select":        ("interface-sounds/Audio/select_002.ogg",
                        "40 ms select, 1.2 kHz"),
    "k_tick_metal":    ("impact-sounds/Audio/impactTin_medium_002.ogg",
                        "tin tick, 617 Hz"),
    "k_glass":         ("interface-sounds/Audio/glass_005.ogg",
                        "glass accent, 2.7 kHz"),
}


def convert(src, dst, peak_db=-3.0):
    tmp = "/tmp/_conv.wav"
    r = subprocess.run([FF, "-v", "error", "-y", "-i", str(src),
                        "-ar", str(SR), "-ac", "2", tmp], capture_output=True)
    if r.returncode != 0 or not os.path.exists(tmp):
        return None
    sr, x = wavfile.read(tmp)
    x = x.astype(float) / 32768
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    x = x / (np.max(np.abs(x)) + 1e-12) * (10 ** (peak_db / 20))
    f = min(int(0.003 * SR), len(x) // 4)
    if f > 0:
        x[:f] *= np.linspace(0, 1, f)[:, None]
        x[-f:] *= np.linspace(1, 0, f)[:, None]
    wavfile.write(dst, SR, (x * 32767).astype(np.int16))
    return len(x) / SR


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    for name, (rel, why) in PICKS.items():
        src = KEN / rel
        if not src.exists():
            print(f"  MISSING {rel}")
            continue
        dur = convert(src, OUT / f"{name}.wav")
        if dur is None:
            print(f"  FAIL    {rel}")
            continue
        print(f"  ok  {name:18s} {dur:5.2f}s  {why}")
        lines.append(f"| {name}.wav | {dur:.2f} s | Kenney (CC0) | {why} |")
    (HERE / "assets" / "sfx-fd" / "KENNEY-SOURCES.md").write_text(
        "# Kenney-sourced sounds in this pack\n\n"
        "Kenney (kenney.nl) releases under Creative Commons Zero (CC0) —\n"
        "public domain, no attribution required, commercial use permitted.\n"
        "Credited here anyway because it is good practice.\n\n"
        "All files converted to 48 kHz 16-bit stereo and peak-normalised to\n"
        "-3 dBFS to match the rest of the pack.\n\n"
        "| file | length | source | why this one |\n|---|---|---|---|\n"
        + "\n".join(lines) + "\n"
    )
    print(f"\n{len(lines)} Kenney sounds folded in -> {OUT}")
