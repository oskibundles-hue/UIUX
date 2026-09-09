#!/usr/bin/env python3
"""Cut usable sounds out of the harvested Formula Dynamics clip audio.

Segments were chosen from a rolling spectral profile, not by ear-guessing:
low-band share (30-250 Hz) identifies engine content, and high-band share
(>4 kHz) flags wind and handling noise. The GT3 clip peaks at 94% low-band
with 0.4% HF around t=37-39s — that is the cleanest engine in the library.

Denoising is deliberately gentle. Engine audio lives in exactly the band a
noise gate wants to remove, so this uses a soft per-bin spectral subtraction
with a floor rather than a gate, and errs toward leaving noise in.
"""
import pathlib

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = pathlib.Path(__file__).parent
RAW = HERE / "assets" / "harvest-raw"
OUT = HERE / "assets" / "sfx-fd"
SR = 48000

# name -> (source clip, start s, end s, note)
CUTS = [
    ("fd_engine_peak",   "gt3_rolling_in",     36.8, 39.6,
     "94% low-band, 0.4% HF — the cleanest engine in the set"),
    ("fd_engine_steady", "gt3_rolling_in",     28.0, 31.2,
     "steady 83% low-band, even level"),
    ("fd_engine_settle", "gt3_rolling_in",     43.6, 46.0,
     "engine settling, 92% low-band"),
    ("fd_engine_low",    "gt3_rolling_in",     15.4, 18.2,
     "86% low-band, mid level — good bed"),
    ("fd_shop_room",     "gt3_rolling_in",     46.6, 49.0,
     "engine off — room tone, useful as a bed and as a noise profile"),
    ("fd_lift_low",      "black_car_on_lift",  29.6, 32.4,
     "44% low-band section of the lift clip"),
    ("fd_wheels_work",   "wheels_off",         11.4, 13.8,
     "loudest 2 s of the wheels-off clip"),
]


def denoise(x, noise, amount=0.7, floor=0.16):
    """Soft spectral subtraction. `noise` is a quiet reference from the same
    recording, so the profile matches the actual room and camera."""
    n = 2048
    f, t, Z = signal.stft(x, SR, nperseg=n, noverlap=n * 3 // 4)
    _, _, N = signal.stft(noise, SR, nperseg=n, noverlap=n * 3 // 4)
    prof = np.median(np.abs(N), axis=1, keepdims=True)
    mag = np.abs(Z)
    cleaned = np.maximum(mag - amount * prof, floor * mag)
    _, y = signal.istft(cleaned * np.exp(1j * np.angle(Z)), SR,
                        nperseg=n, noverlap=n * 3 // 4)
    return y[:len(x)]


def cut(src, a, b):
    sr, x = wavfile.read(RAW / f"{src}.wav")
    x = x.astype(float) / 32768
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    return x[int(a * sr):int(b * sr)], x


def save(name, x, peak_db=-3.0, fade=0.03):
    x = x / (np.max(np.abs(x)) + 1e-12) * (10 ** (peak_db / 20))
    f = int(fade * SR)
    if len(x) > 2 * f:
        x[:f] *= np.linspace(0, 1, f)[:, None]
        x[-f:] *= np.linspace(1, 0, f)[:, None]
    wavfile.write(OUT / f"{name}.wav", SR, (x * 32767).astype(np.int16))
    return len(x) / SR


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, src, a, b, note in CUTS:
        seg, full = cut(src, a, b)
        # noise reference: the quietest 1.5 s in the source recording
        m = full.mean(1)
        w = int(1.5 * SR)
        step = int(0.5 * SR)
        levels = [(np.sqrt((m[i:i + w] ** 2).mean()), i)
                  for i in range(0, max(1, len(m) - w), step)]
        _, qi = min(levels)
        noise = full[qi:qi + w]

        out = np.stack([
            denoise(seg[:, 0], noise[:, 0]),
            denoise(seg[:, 1], noise[:, 1]),
        ], axis=1)
        # trim sub-25 Hz rumble the camera picked up; keep everything musical
        sos = signal.butter(2, 25 / (SR / 2), "high", output="sos")
        out = signal.sosfilt(sos, out, axis=0)

        dur = save(name, out)
        rows.append((name, dur, src, note))
        print(f"  ok  {name:18s} {dur:5.2f}s  from {src}  — {note}")

    lines = ["# Formula Dynamics' own recordings", "",
             "Cut from the shop's own footage — engine, exhaust and shop sounds",
             "belonging to Formula Dynamics, no third-party licence involved.",
             "",
             "Segments were chosen from a rolling spectral profile: low-band share",
             "(30-250 Hz) finds engine content, high-band share (>4 kHz) flags wind",
             "and handling noise. Gently denoised with a noise profile taken from",
             "the quietest passage of the same recording, so the profile matches the",
             "actual room and camera.",
             "", "| file | length | source clip | why |", "|---|---|---|---|"]
    for name, dur, src, note in rows:
        lines.append(f"| {name}.wav | {dur:.2f} s | {src} | {note} |")
    (OUT / "FD-RECORDINGS.md").write_text("\n".join(lines) + "\n")
    print(f"\n{len(rows)} cuts -> {OUT}")
