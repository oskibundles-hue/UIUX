#!/usr/bin/env python3
"""
Formula Dynamics - UI/motion sound-effect pack.

Every sound here is SYNTHESISED from scratch. Nothing is sampled or lifted
from the reference clip: what was taken from it is the *design* - how many
hits, how bright, how fast they decay - measured off the audio with an onset
detector, then rebuilt with oscillators and filtered noise.

Measured off the reference (21.7 s screen recording, 100 onsets):

(measured on the mix, so the "decay" column includes bleed from the next hit -
one-shot files on their own decay faster, which is correct)

    family      centroid      decay ratio   spacing
    key click   6-9 kHz       0.00-0.20     0.08 s in runs
    ui tick     3-5 kHz       0.30-0.80     0.10-0.22 s
    riser/tail  6-9 kHz       2.4-7.6       one per reveal
    impact      3-5 kHz       0.35-0.55     every 1.5-2.5 s
    sub thump   60-190 Hz     0.5-1.4       under the big reveals

Run:  python3 99-toolkit/build_sfx.py
"""

import math
import struct
import wave

import numpy as np

import fd_brand as B

SR = 48000
OUT = B.KIT / "10-motion-sfx" / "sfx"

rng = np.random.default_rng(7)          # fixed seed - rebuilds are identical


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)


def noise(n):
    return rng.uniform(-1, 1, n)


def biquad(x, f0, q, kind="lp"):
    """One-pole-pair filter, direct form 1. Enough for sound design."""
    w0 = 2 * math.pi * f0 / SR
    alpha = math.sin(w0) / (2 * q)
    cw = math.cos(w0)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
    else:                                             # band
        b = [alpha, 0, -alpha]
    a = [1 + alpha, -2 * cw, 1 - alpha]
    b = [c / a[0] for c in b]
    a = [c / a[0] for c in a]
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, xi in enumerate(x):
        yi = b[0] * xi + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        y[i] = yi
        x2, x1 = x1, xi
        y2, y1 = y1, yi
    return y


def norm(x, peak=0.89):
    m = np.abs(x).max()
    return x * (peak / m) if m else x


def save(name, x, note):
    x = norm(x)
    # 4 ms fade in/out so nothing clicks at the file boundary
    f = int(SR * 0.004)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    p = OUT / f"{name}.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    MANIFEST.append((name, len(x) / SR, note))
    return p


MANIFEST = []


# --------------------------------------------------------------------------
# the four families
# --------------------------------------------------------------------------
def key_click(seed_f=7200, dur=0.075):
    """Keyboard key. Bright, no tail - centroid 6-9 kHz, decay ~0.0.

    Band-limited, not just high-passed: a bare high-pass leaves everything
    above the corner, which measured out at 14 kHz - thin and hissy rather
    than like a key.
    """
    n = int(SR * dur)
    x = biquad(noise(n), seed_f, 1.4, "band")
    x = biquad(x, 10500, 0.7, "lp")
    # A 55 ms click with an exp(-42) tail puts nearly all its energy in the
    # first 10 ms, which peak-normalises to almost no RMS: in the demo the
    # typing run measured 4% of an impact's RMS where the reference's own
    # typing measured 158%. Slower decay plus a little keyboard body.
    x *= np.exp(-np.linspace(0, 1, n) * 16)
    tick = np.sin(2 * math.pi * 2400 * t(dur)) * np.exp(-np.linspace(0, 1, n) * 30)
    body = (np.sin(2 * math.pi * 320 * t(dur))
            * np.exp(-np.linspace(0, 1, n) * 22))
    return x * 0.8 + tick * 0.35 + body * 0.22


def ui_tick(f=3600, dur=0.13):
    """Element appears. Pitched blip with a short tail - centroid 3-5 kHz.

    No octave partial and only a little air: both pushed the centroid up
    near 8 kHz on the first pass. The tail is deliberately slow enough to
    measure - a tick that has decayed to nothing by 150 ms reads as a
    click, not as something landing.
    """
    n = int(SR * dur)
    tt = t(dur)
    body = np.sin(2 * math.pi * f * tt) * np.exp(-np.linspace(0, 1, n) * 5.0)
    air = (biquad(noise(n), 3400, 1.0, "band")
           * np.exp(-np.linspace(0, 1, n) * 16))
    return body * 0.85 + air * 0.15


def riser(dur=0.60, f0=900, f1=7000):
    """Swell into a reveal. Rising centroid, decay ratio well above 1."""
    n = int(SR * dur)
    tt = t(dur)
    sweep = f0 * (f1 / f0) ** (tt / dur)
    ph = 2 * math.pi * np.cumsum(sweep) / SR
    tone = np.sin(ph) * 0.5
    # Lowpass the air: unfiltered it dragged the centroid to 12.5 kHz, well
    # above the 6-9 kHz the reference risers sit in.
    air = biquad(biquad(noise(n), 4000, 0.7, "hp"), 9500, 0.7, "lp")
    # A floor rather than true silence at the head: a riser that starts at
    # zero has no onset to measure against, and reads as a fade, not a lift.
    shape = 0.10 + 0.90 * np.linspace(0, 1, n) ** 2.2
    return (tone + air * 0.8) * shape


def whoosh(dur=0.42):
    """Movement. Band-passed noise swept across the spectrum, both directions."""
    n = int(SR * dur)
    x = noise(n)
    x = biquad(x, 1800, 0.6, "band")
    shape = np.sin(np.linspace(0, math.pi, n)) ** 1.6
    return x * shape


def impact(dur=0.5):
    """Section change. Body in the low mids, transient on top."""
    n = int(SR * dur)
    tt = t(dur)
    thump = (np.sin(2 * math.pi * 92 * np.exp(-tt * 7) * tt * 4)
             * np.exp(-np.linspace(0, 1, n) * 4.2))
    crack = biquad(noise(n), 3400, 0.8, "band") * np.exp(-np.linspace(0, 1, n) * 18)
    return thump * 0.75 + crack * 0.5


def sub_thump(dur=0.55, f=58):
    """Weight under a reveal. 60-190 Hz, nothing above."""
    n = int(SR * dur)
    tt = t(dur)
    pitch = f * (1 + 1.4 * np.exp(-tt * 26))
    ph = 2 * math.pi * np.cumsum(pitch) / SR
    return np.sin(ph) * np.exp(-np.linspace(0, 1, n) * 6.5)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.wav"):
        p.unlink()

    # Key clicks - three so a typing run does not machine-gun one sample.
    for i, f in enumerate((6600, 7400, 8300), 1):
        save(f"key-click-{i}", key_click(f),
             "Typewriter / caption keystroke. Lay at 0.08 s spacing for a run.")

    # UI ticks - one per element that appears.
    for i, f in enumerate((3200, 3900, 4700), 1):
        save(f"ui-tick-{i}", ui_tick(f),
             "A chip, callout or lower third landing. One per element.")

    save("ui-tick-soft", ui_tick(2600, 0.17) * 0.7,
         "Quieter tick for secondary elements, so a dense run still has shape.")

    # Risers.
    save("riser-short", riser(0.38), "Half-second lead-in to a callout.")
    save("riser-long", riser(0.95, 700, 8000), "Lead-in to a title or end card.")

    # Whooshes.
    save("whoosh-in", whoosh(0.40), "Element sliding in from off frame.")
    save("whoosh-out", whoosh(0.30)[::-1].copy(), "Element leaving frame.")

    # Impacts.
    save("impact-hard", impact(0.55), "Section change. The biggest hit in a cut.")
    save("impact-soft", impact(0.34) * 0.72, "Smaller punctuation between beats.")
    save("impact-tight", impact(0.22), "Fast cut on a beat.")

    # Sub.
    save("sub-thump", sub_thump(), "Weight under a title reveal.")
    save("sub-drop", sub_thump(0.85, 46), "Under the end card.")

    # Glitch, for the scramble text effect.
    n = int(SR * 0.26)
    g = noise(n)
    g = biquad(biquad(g, 2600, 1.6, "band"), 6000, 0.8, "lp")
    steps = (np.arange(n) // int(SR * 0.02)) % 2
    save("scramble", g * (0.35 + 0.65 * steps) * np.exp(-np.linspace(0, 1, n) * 4.5),
         "Under a scramble/resolve text effect. Loop or trim to the reveal.")

    # An audition file: every sound in order, 0.45 s apart.
    gap = int(SR * 0.45)
    total = np.zeros(gap * (len(MANIFEST) + 1))
    pos = 0
    for name, dur, _ in MANIFEST:
        with wave.open(str(OUT / f"{name}.wav")) as w:
            a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        a = a.astype(np.float32) / 32768
        total[pos:pos + len(a)] += a
        pos += gap
    pcm = (np.clip(norm(total[:pos + gap]), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(OUT / "_audition-all.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    lines = [
        "# SFX manifest",
        "",
        "Synthesised from scratch by `99-toolkit/build_sfx.py`. Nothing is",
        "sampled from any reference - only the timing and brightness were",
        "measured. 48 kHz mono WAV, peak-normalised to -1 dBFS.",
        "",
        "| File | Length | Use |",
        "|---|---|---|",
    ]
    for name, dur, note in MANIFEST:
        lines.append(f"| `{name}.wav` | {dur:.2f} s | {note} |")
    lines += ["", "`_audition-all.wav` plays every sound in order, 0.45 s apart.", ""]
    (OUT / "MANIFEST.md").write_text("\n".join(lines))
    return len(MANIFEST)


if __name__ == "__main__":
    print(f"Wrote {build()} sounds to 10-motion-sfx/sfx/.")
