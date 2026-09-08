#!/usr/bin/env python3
"""Formula Dynamics SFX pack — designed, not sampled.

Every sound here is synthesised from scratch, so the whole pack is original
work with no third-party licence attached. That matters: these run in paid
ads, and most "free" SFX libraries either require attribution, forbid
advertising use, or state no licence at all.

Design notes
------------
Cheap SFX are one layer. These are three: a transient that gives the ear a
point to lock onto, a body that carries the character, and a tail that sets
the size of the space. Impacts add a sub sweep underneath for weight on
phone speakers, which roll off below ~200 Hz — so the sub is felt through
the body's harmonics rather than heard directly.

48 kHz, 16-bit stereo, peak-normalised to -3 dBFS.
"""
import numpy as np
from scipy import signal
from scipy.io import wavfile
import pathlib

SR = 48000
OUT = pathlib.Path(__file__).parent / "assets" / "sfx-fd"
rng = np.random.default_rng(20260908)          # seeded: the pack is reproducible


# ---- helpers ---------------------------------------------------------------
def t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)


def env(n, a=0.002, d=0.10, s=0.0, r=0.20, curve=2.5):
    """ADSR over n samples, with a shaped decay."""
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    S = max(0, n - A - D - R)
    out = np.concatenate([
        np.linspace(0, 1, A) ** 0.5 if A else np.array([]),
        (1 - np.linspace(0, 1, D)) ** curve * (1 - s) + s if D else np.array([]),
        np.full(S, s),
        (np.linspace(1, 0, R) ** curve) * (s if s > 0 else 1) if R else np.array([]),
    ])
    return np.pad(out, (0, max(0, n - len(out))))[:n]


def noise(n, colour=0.0):
    """White noise, optionally tilted. colour<0 darker, >0 brighter."""
    x = rng.normal(0, 1, n)
    if colour:
        b, a = signal.butter(1, 0.25, "low" if colour < 0 else "high")
        x = 0.5 * x + abs(colour) * signal.lfilter(b, a, x)
    return x


def bp(x, f0, f1, order=2):
    """Band-pass with a time-varying centre, swept f0 -> f1."""
    n = len(x)
    cent = np.geomspace(max(f0, 20), max(f1, 20), n)
    out = np.zeros(n)
    step = 256
    zi = None
    for i in range(0, n, step):
        seg = x[i:i + step]
        fc = np.clip(cent[i] / (SR / 2), 1e-4, 0.98)
        lo = np.clip(fc * 0.55, 1e-4, 0.97)
        hi = np.clip(fc * 1.8, lo + 1e-3, 0.98)
        b, a = signal.butter(order, [lo, hi], btype="band")
        if zi is None:
            zi = signal.lfilter_zi(b, a) * (seg[0] if len(seg) else 0)
        seg_out, zi = signal.lfilter(b, a, seg, zi=zi)
        out[i:i + step] = seg_out
    return out


def lp(x, fc):
    b, a = signal.butter(4, np.clip(fc / (SR / 2), 1e-4, 0.98), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc):
    b, a = signal.butter(2, np.clip(fc / (SR / 2), 1e-4, 0.98), "high")
    return signal.lfilter(b, a, x)


def sat(x, drive=2.0):
    """Soft clip — adds harmonics so low material survives a phone speaker."""
    return np.tanh(x * drive) / np.tanh(drive)


def tail(x, amount=0.25, delay=0.035, fb=0.35, damp=6000):
    """Cheap feedback-delay reverb, enough to imply a room."""
    d = int(delay * SR)
    y = x.copy()
    buf = np.zeros(len(x) + d * 6)
    buf[:len(x)] = x
    for k in range(1, 6):
        seg = lp(buf[:len(x)], damp) * (fb ** k)
        y[k * d:] += seg[:len(y) - k * d]
    return x * (1 - amount) + y * amount


def stereo(x, width=0.35):
    """Decorrelate slightly so it sits wide without phase problems in mono."""
    d = int(0.006 * SR * width)
    r = np.pad(x, (d, 0))[:len(x)]
    r = lp(r, 12000)
    return np.stack([x, 0.82 * r + 0.18 * x], axis=1)


def sweep(dur, f0, f1, shape="exp"):
    tt = t(dur)
    if shape == "exp":
        f = np.geomspace(f0, f1, len(tt))
    else:
        f = np.linspace(f0, f1, len(tt))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def save(name, x, peak_db=-3.0):
    if x.ndim == 1:
        x = stereo(x)
    x = x / (np.max(np.abs(x)) + 1e-12) * (10 ** (peak_db / 20))
    # 4 ms fades kill any click at the file boundary
    f = int(0.004 * SR)
    x[:f] *= np.linspace(0, 1, f)[:, None]
    x[-f:] *= np.linspace(1, 0, f)[:, None]
    OUT.mkdir(parents=True, exist_ok=True)
    wavfile.write(OUT / f"{name}.wav", SR, (x * 32767).astype(np.int16))
    return name, round(len(x) / SR, 2)


# ---- impacts ---------------------------------------------------------------
def impact(dur=1.1, sub_f=(85, 34), body_f=(900, 120), drive=2.6, click=1.0):
    n = int(SR * dur)
    sub = sweep(dur, *sub_f) * env(n, 0.001, 0.30, 0, dur - 0.31, 2.0)
    body = bp(noise(n), *body_f) * env(n, 0.001, 0.16, 0, dur - 0.17, 3.0)
    tr = noise(int(0.012 * SR), 0.6) * env(int(0.012 * SR), 0.0002, 0.010, 0, 0.001)
    x = 1.0 * sub + 0.55 * body
    x[:len(tr)] += click * 0.7 * tr
    return tail(sat(x, drive), 0.22, 0.045, 0.30)


# ---- whooshes --------------------------------------------------------------
def whoosh(dur=0.9, f0=250, f1=5200, rev=False, res=2):
    n = int(SR * dur)
    x = bp(noise(n, 0.2), f0, f1, order=res)
    e = env(n, dur * 0.45, dur * 0.5, 0, dur * 0.05, 1.6)
    x = x * e
    if rev:
        x = x[::-1]
    return tail(x * 1.4, 0.20, 0.03, 0.25)


def pass_by(dur=1.1):
    """Doppler pass — pitch and pan sweep together."""
    n = int(SR * dur)
    x = bp(noise(n, 0.1), 400, 3000, order=3)
    e = np.exp(-((np.linspace(-1, 1, n)) ** 2) * 6)
    x = x * e
    pan = np.linspace(0, 1, n)
    left, right = x * np.cos(pan * np.pi / 2), x * np.sin(pan * np.pi / 2)
    return np.stack([left, right], axis=1)


# ---- risers ----------------------------------------------------------------
def riser(dur=1.8, kind="air"):
    n = int(SR * dur)
    if kind == "air":
        x = bp(noise(n, 0.3), 300, 8000, order=2)
        x *= np.linspace(0, 1, n) ** 1.7
    elif kind == "tone":
        base = sweep(dur, 180, 900)
        harm = sweep(dur, 360, 1800) * 0.4 + sweep(dur, 540, 2700) * 0.18
        x = (base + harm) * np.linspace(0, 1, n) ** 1.5
        x = sat(x, 1.6)
    else:  # stutter — gated riser, good under a count-up
        x = bp(noise(n, 0.2), 400, 6000, order=2) * np.linspace(0, 1, n) ** 1.4
        rate = np.linspace(6, 26, n)
        gate = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > -0.2).astype(float)
        x *= 0.35 + 0.65 * lp(gate, 900)
    return tail(x, 0.18, 0.05, 0.3)


# ---- UI / mechanical -------------------------------------------------------
def click(dur=0.05, f=(2600, 900), tone=0.35, drive=1.4):
    n = int(SR * dur)
    x = bp(noise(n, 0.5), *f, order=2) * env(n, 0.0004, dur * 0.35, 0, dur * 0.6, 3.0)
    x += tone * np.sin(2 * np.pi * f[0] * t(dur)) * env(n, 0.0004, dur * 0.25, 0, dur * 0.5, 4)
    return sat(x, drive)


def thock(dur=0.14):
    n = int(SR * dur)
    body = lp(noise(n), 1200) * env(n, 0.0008, 0.045, 0, 0.09, 3.0)
    low = sweep(dur, 220, 90) * env(n, 0.001, 0.05, 0, 0.08, 2.2)
    return sat(0.7 * body + 0.6 * low, 1.8)


def ratchet(dur=0.55, teeth=11):
    n = int(SR * dur)
    x = np.zeros(n)
    for i in range(teeth):
        pos = int((i / teeth) ** 0.85 * n * 0.9)
        c = click(0.028, (3200 - i * 90, 1100), tone=0.2)[:, 0] if False else None
        seg = bp(noise(int(0.026 * SR), 0.5), 3000 - i * 100, 1200, order=2)
        seg *= env(len(seg), 0.0003, 0.008, 0, 0.016, 3)
        x[pos:pos + len(seg)] += seg * (0.55 + 0.45 * i / teeth)
    return sat(x, 1.5)


# ---- accents ---------------------------------------------------------------
def pop(dur=0.13):
    n = int(SR * dur)
    x = sweep(dur, 900, 210) * env(n, 0.0006, 0.05, 0, 0.07, 3.0)
    x += 0.3 * bp(noise(n, 0.4), 2200, 700) * env(n, 0.0004, 0.02, 0, 0.03, 3)
    return sat(x, 2.0)


def bell(dur=1.5, f0=880, inharm=1.0):
    """FM-ish bell with inharmonic partials."""
    tt = t(dur)
    n = len(tt)
    parts = [(1.0, 1.0, 1.0), (2.76 * inharm, 0.5, 0.7), (5.40 * inharm, 0.28, 0.45),
             (8.93 * inharm, 0.15, 0.30)]
    x = np.zeros(n)
    for mult, amp, dec in parts:
        x += amp * np.sin(2 * np.pi * f0 * mult * tt) * np.exp(-tt * (3.0 / dec))
    return tail(x, 0.30, 0.06, 0.35)


def shimmer(dur=1.6):
    n = int(SR * dur)
    x = np.zeros(n)
    for f in (2400, 3200, 4100, 5300, 6900):
        e = np.exp(-t(dur) * rng.uniform(2.0, 4.0))
        x += np.sin(2 * np.pi * f * t(dur) + rng.uniform(0, 6)) * e * rng.uniform(0.4, 1.0)
    return tail(hp(x, 1800), 0.35, 0.05, 0.4)


def drone(dur=3.0, f=55):
    tt = t(dur)
    x = sum(np.sin(2 * np.pi * f * k * tt) / (k ** 1.4) for k in (1, 2, 3, 5, 7))
    x *= 1 + 0.06 * np.sin(2 * np.pi * 0.4 * tt)
    x = sat(x * 0.6, 1.4) * env(len(tt), 0.5, 0.4, 0.75, 0.9, 1.4)
    return lp(x, 2200)


# ---- the pack --------------------------------------------------------------
def build():
    made = []
    A = made.append
    # impacts
    A(save("impact_deep",   impact(1.30, (95, 30), (900, 110), 2.8)))
    A(save("impact_low",    impact(0.85, (80, 40), (1100, 160), 2.2)))
    A(save("impact_tight",  impact(0.42, (150, 60), (1800, 320), 2.0, click=1.3)))
    A(save("impact_metal",  impact(0.9, (200, 90), (3200, 900), 3.2, click=1.5)))
    A(save("sub_drop",      impact(1.6, (70, 26), (400, 70), 2.4, click=0.3)))
    # whooshes
    A(save("whoosh_short",  whoosh(0.65, 300, 5200)))
    A(save("whoosh_long",   whoosh(1.5, 180, 6400)))
    A(save("whoosh_reverse",whoosh(0.8, 300, 5200, rev=True)))
    A(save("whoosh_pass",   pass_by(1.15)))
    A(save("swish_fine",    whoosh(0.4, 1200, 7000, res=3)))
    # risers
    A(save("riser_air",     riser(1.5, "air")))
    A(save("riser_tone",    riser(2.2, "tone")))
    A(save("riser_stutter", riser(2.0, "stutter")))
    # UI / mechanical
    A(save("click_soft",    click(0.035, (1800, 700), 0.25, 1.2)))
    A(save("click_hard",    click(0.05, (3400, 1100), 0.45, 1.8)))
    A(save("tick",          click(0.018, (5200, 2000), 0.15, 1.3)))
    A(save("thock",         thock(0.16)))
    A(save("switch",        click(0.07, (2200, 500), 0.5, 2.2)))
    A(save("ratchet",       ratchet(0.5, 11)))
    # accents
    A(save("pop",           pop(0.13)))
    A(save("ding",          bell(1.4, 1180, 1.0)))
    A(save("chime_low",     bell(2.0, 640, 0.92)))
    A(save("shimmer",       shimmer(1.7)))
    A(save("reverse_tail",  whoosh(1.0, 900, 4200, rev=True, res=3)))
    # texture
    A(save("drone_low",     drone(3.2, 55)))
    A(save("air_bed",       lp(noise(int(SR * 3.0), -0.4), 900) * env(int(SR * 3.0), 0.6, 0.5, 0.7, 1.0, 1.2)))
    return made


if __name__ == "__main__":
    rows = build()
    lines = ["# Formula Dynamics SFX pack (designed)", "",
             "Synthesised from scratch — original work, no third-party licence.",
             "48 kHz, 16-bit stereo, peak -3 dBFS. Rebuild: `python3 build_sfx.py`.",
             "", "| file | length |", "|---|---|"]
    for name, dur in rows:
        lines.append(f"| {name}.wav | {dur:.2f} s |")
    (OUT / "MANIFEST.md").write_text("\n".join(lines) + "\n")
    print(f"{len(rows)} sounds -> {OUT}")
