#!/usr/bin/env python3
"""
Synthesise SFX kit v2 into creator-kit/sfx/kit-v2/ with numpy only.

Built for the edit references Muse relayed (the @jerrzyo SFX palette and the
@cinamiti rapid zoom). Every sound is generated here from noise and oscillators
with a fixed seed, so a re-run writes byte-identical files. No downloads, no
samples: original work, free to use (see kit-v2/LICENCE.md).

48 kHz, 24-bit PCM, stereo, each peak-normalised to -1 dBFS.
Also writes audition.wav (every sound in order, 0.4 s gaps) and kit.json
(length and the hit time inside each file, for placing a sound so its
transient lands on a frame).

    python3 gen_sfx_kit.py [--out DIR]
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from media import write_wav, KIT, FPS  # noqa: E402

SR = 48000
PEAK = 10 ** (-1 / 20)            # -1 dBFS
GAP = 0.4


def t_axis(dur):
    return np.arange(int(round(dur * SR))) / SR


def svf(x, fc, q=0.7, mode="bp"):
    """Chamberlin state-variable filter; fc may be an array (time-varying)."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    f = 2 * np.sin(np.pi * np.clip(fc, 20, SR / 6) / SR)
    damp = 1.0 / q
    lo = bp = 0.0
    y = np.empty_like(x)
    for i in range(len(x)):
        hi = x[i] - lo - damp * bp
        bp += f[i] * hi
        lo += f[i] * bp
        y[i] = bp if mode == "bp" else (lo if mode == "lp" else hi)
    return y


def onepole_hp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); prev_x = prev_y = 0.0
    for i in range(len(x)):
        prev_y = a * (prev_y + x[i] - prev_x); prev_x = x[i]; y[i] = prev_y
    return y


def fftconv(a, b):
    n = len(a) + len(b) - 1
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, m) * np.fft.rfft(b, m), m)[:n]


def tail(rng, dur, decay, hp=800):
    """A short synthetic room: decaying filtered noise used as an impulse response."""
    t = t_axis(dur)
    ir = rng.standard_normal(len(t)) * np.exp(-t / decay)
    ir = onepole_hp(ir, hp)
    ir[0] = 1.0
    return ir / np.abs(ir).sum() * 6


def env_exp(dur, tau, attack=0.0005):
    t = t_axis(dur)
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    return a * np.exp(-t / tau)


def stereo(m, width=0.0, rng=None, pan=None):
    """Mono to stereo. width adds a decorrelated side; pan is an array/const in [-1, 1]."""
    m = np.asarray(m, float)
    if pan is None:
        pan = 0.0
    pan = np.broadcast_to(np.asarray(pan, float), m.shape)
    l = m * np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
    r = m * np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
    if width and rng is not None:
        d = int(0.0007 * SR)
        side = np.concatenate([np.zeros(d), m[:-d]]) * width
        l, r = l + side * 0.5, r - side * 0.5
    return np.stack([l, r], axis=1)


def norm(x):
    p = np.abs(x).max()
    return x / p * PEAK if p > 0 else x


# ---------------------------------------------------------------- the sounds

def click(rng, dur=0.012, f=3800, tau=0.0018, body=None):
    t = t_axis(dur)
    n = rng.standard_normal(len(t)) * np.exp(-t / (tau * 0.6))
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
    x = 0.6 * onepole_hp(n, 1500) + 0.7 * s
    if body:
        bf, btau = body
        x = x + 0.5 * np.sin(2 * np.pi * bf * t) * np.exp(-t / btau)
    return x


def rapid_click(seed, period, dur=1.0, ramp=False):
    """A click train. period in seconds; ramp accelerates from 1/6 s to period."""
    rng = np.random.default_rng(seed)
    out = np.zeros(int(dur * SR) + SR // 10)
    t, k = 0.0, 0
    while t < dur - 1e-9:
        c = click(rng, f=3600 + rng.uniform(-300, 300), tau=0.0015)
        c *= 0.85 + 0.15 * rng.random()
        s = int(round(t * SR))
        out[s:s + len(c)] += c
        k += 1
        if ramp:
            frac = min(1.0, t / dur)
            t += (1 / 6) * (1 - frac) + period * frac
        else:
            t += period
    out = out[:int(dur * SR) + int(0.02 * SR)]
    return stereo(out, 0.25, rng), 0.0


def mech_click(seed, variant):
    """Keyboard switch: down-stroke and up-stroke. a = thock (linear), b = clicky."""
    rng = np.random.default_rng(seed)
    dur = 0.16
    out = np.zeros(int(dur * SR))
    if variant == "a":
        down = click(rng, dur=0.05, f=2200, tau=0.003, body=(190, 0.018))
        up = click(rng, dur=0.03, f=2900, tau=0.0018, body=(260, 0.008)) * 0.45
        up_t = 0.085
    else:
        down = click(rng, dur=0.02, f=5200, tau=0.0011)
        down2 = click(rng, dur=0.04, f=3100, tau=0.0025, body=(320, 0.01)) * 0.8
        down = np.concatenate([down, np.zeros(int(0.006 * SR))])
        down = np.pad(down, (0, max(0, len(down2) + int(0.006 * SR) - len(down))))
        down[int(0.006 * SR):int(0.006 * SR) + len(down2)] += down2
        up = click(rng, dur=0.02, f=4600, tau=0.0012) * 0.55
        up_t = 0.07
    out[:len(down)] += down
    s = int(up_t * SR); out[s:s + len(up)] += up
    out = fftconv(out, tail(rng, 0.08, 0.012, 600))[:len(out)]
    return stereo(out, 0.2, rng), 0.0


def button(seed):
    """A UI press: soft click plus a short pitched blip, then a quieter release."""
    rng = np.random.default_rng(seed)
    t = t_axis(0.14)
    blip = np.sin(2 * np.pi * (1250 + 300 * np.exp(-t / 0.01)) * t) * env_exp(0.14, 0.022, 0.001)
    out = 0.55 * blip
    c = click(rng, dur=0.01, f=4200, tau=0.0012)
    out[:len(c)] += 0.6 * c
    r = click(rng, dur=0.01, f=3000, tau=0.0012) * 0.3
    s = int(0.09 * SR); out[s:s + len(r)] += r
    return stereo(out), 0.0


def whoosh(seed, dur=0.75, peak_at=0.62):
    """Band-passed noise sweeping up, swelling to peak_at and cutting off fast, panning L to R."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    n = rng.standard_normal(len(t))
    x = t / peak_at
    fc = np.where(x < 1, 350 + 3200 * x ** 2.2, 3550 - 2000 * (x - 1) / (dur / peak_at - 1))
    b = svf(n, fc, q=1.6)
    b += 0.35 * svf(rng.standard_normal(len(t)), fc * 2.2, q=2.5)
    env = np.where(x < 1, x ** 2.6, np.exp(-(t - peak_at) / 0.03))
    pan = np.clip(-0.8 + 1.6 * t / peak_at, -0.8, 0.8)
    return stereo(b * env, 0.3, rng, pan), peak_at


def big_flash(seed, dur=0.9):
    """A bright transient: a cracking noise burst, a falling zap and an airy tail."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    crack = onepole_hp(rng.standard_normal(len(t)), 2500) * env_exp(dur, 0.012, 0.0003)
    burst = svf(rng.standard_normal(len(t)), 6000, q=0.6) * env_exp(dur, 0.09, 0.001)
    f = 200 + 5200 * np.exp(-t / 0.035)
    zap = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(dur, 0.06, 0.0005)
    sub = np.sin(2 * np.pi * 52 * t) * env_exp(dur, 0.18, 0.002)
    x = 1.0 * crack + 0.7 * burst + 0.45 * zap + 0.55 * sub
    x = x + 0.5 * fftconv(x, tail(rng, 0.6, 0.12, 1200))[:len(x)]
    return stereo(x, 0.5, rng), 0.0


def whoosh_flash(seed):
    w, hit = whoosh(seed, dur=0.75, peak_at=0.62)
    f, _ = big_flash(seed + 1)
    n = int(hit * SR) + len(f)
    out = np.zeros((n, 2))
    out[:len(w)] += norm(w) * 0.75
    s = int(hit * SR); out[s:s + len(f)] += norm(f)
    return out, hit


def source_tone(rng, dur):
    t = t_axis(dur)
    return (0.6 * np.sign(np.sin(2 * np.pi * 110 * t)) * 0.4
            + 0.5 * np.sin(2 * np.pi * 440 * t + 3 * np.sin(2 * np.pi * 7 * t))
            + 0.3 * svf(rng.standard_normal(len(t)), 1800, q=1.0))


def glitch(seed, kind):
    rng = np.random.default_rng(seed)
    dur = 0.55
    src = source_tone(rng, dur)
    if kind == 1:      # bit-crush plus sample-rate reduction, steps in and out
        out = np.empty_like(src)
        seg = np.linspace(0, len(src), 6).astype(int)
        for i in range(5):
            bits = [3, 5, 2, 4, 3][i]; hold = [18, 6, 40, 10, 24][i]
            s = src[seg[i]:seg[i + 1]]
            s = np.repeat(s[::hold], hold)[:len(s)]
            q = 2 ** bits
            out[seg[i]:seg[i + 1]] = np.round(s * q) / q
        out *= env_exp(dur, 0.25, 0.001)
    elif kind == 2:    # stutter: a 22 ms slice gated on and off, speeding up
        sl = src[:int(0.022 * SR)] * np.hanning(int(0.022 * SR)) ** 0.2
        out = np.zeros(int(dur * SR)); t = 0.0; gap = 0.055
        while t < dur - 0.03:
            s = int(t * SR); out[s:s + len(sl)] += sl[:max(0, len(out) - s)]
            t += gap; gap = max(0.024, gap * 0.86)
    else:              # buffer repeat: a grain repeated, halving in length (pitch steps up)
        out = np.zeros(int(dur * SR)); pos = 0; g = int(0.08 * SR)
        grain = src[int(0.1 * SR):int(0.1 * SR) + g]
        while pos < len(out) and g > 40:
            for _ in range(2):
                e = min(len(out), pos + g)
                out[pos:e] += grain[:e - pos] * np.hanning(g)[:e - pos] ** 0.1
                pos += g
            g = int(g * 0.62); grain = grain[::2][:g] if len(grain[::2]) >= g else grain[:g]
    return stereo(out, 0.35, rng), 0.0


def zoom_riser(seed, dur=1.0):
    """Rising sine sweep plus noise riser, tremolo speeding up, peak at the end (the land)."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    x = t / dur
    f = 120 * (16 ** x)                      # 120 Hz to 1.9 kHz, exponential
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    noise = svf(rng.standard_normal(len(t)), 500 + 7000 * x ** 2, q=1.2)
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * np.cumsum(4 + 26 * x) / SR)
    env = x ** 2.2
    env[-int(0.006 * SR):] *= np.linspace(1, 0, int(0.006 * SR))
    return stereo((0.6 * tone + 0.8 * noise) * trem * env, 0.4, rng), dur


def build_all():
    p3 = 3 / FPS     # one click every 3 frames at 29.97 = the rapid-zoom run
    return [
        ("rapid_click_3f", rapid_click(101, p3), "click train, one every 3 frames (9.99/s) at 29.97 fps; 1 s"),
        ("rapid_click_2f", rapid_click(102, 2 / FPS), "click train, one every 2 frames (15/s); 1 s"),
        ("rapid_click_1f", rapid_click(103, 1 / FPS), "click train, one per frame (30/s); 1 s"),
        ("rapid_click_ramp", rapid_click(104, 1 / FPS, ramp=True), "click train accelerating from 6/s to 30/s; 1 s"),
        ("mech_click_a", mech_click(201, "a"), "mechanical key, linear thock: down and up stroke"),
        ("mech_click_b", mech_click(202, "b"), "mechanical key, clicky switch: double click down, up stroke"),
        ("button", button(301), "UI press: click plus a short blip, then release"),
        ("whoosh", whoosh(401), "band-passed noise sweep, L to R; peak at 0.62 s"),
        ("big_flash", big_flash(501), "bright transient: crack, burst, falling zap, sub, airy tail; hit at 0"),
        ("whoosh_flash", whoosh_flash(601), "whoosh into big_flash; flash hit at 0.62 s"),
        ("glitch_1", glitch(701, 1), "bit-crush and sample-rate reduction, stepped"),
        ("glitch_2", glitch(702, 2), "stutter: one slice gated, speeding up"),
        ("glitch_3", glitch(703, 3), "buffer repeat: a grain repeated, halving each time"),
        ("zoom_riser", zoom_riser(801), "riser for the rapid zoom; peak at the end (1.0 s), place its end on the land"),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=KIT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    meta, aud = {}, []
    gap = np.zeros((int(GAP * SR), 2))
    for name, (x, hit), desc in build_all():
        x = norm(np.asarray(x, float))
        write_wav(os.path.join(a.out, name + ".wav"), x)
        meta[name] = {"seconds": round(len(x) / SR, 4), "hit": round(hit, 4), "what": desc}
        aud += [x, gap]
        print(f"{name:18s} {len(x) / SR:5.2f} s  peak {20 * np.log10(np.abs(x).max()):.2f} dBFS")
    write_wav(os.path.join(a.out, "audition.wav"), np.concatenate(aud[:-1]))
    json.dump({"sample_rate": SR, "bits": 24, "channels": 2, "peak_dbfs": -1.0,
               "generator": "creator-kit/experiments/edit-refs/gen_sfx_kit.py",
               "sounds": meta}, open(os.path.join(a.out, "kit.json"), "w"), indent=1)
    print(f"audition.wav: {len(meta)} sounds, {GAP} s gaps")


if __name__ == "__main__":
    main()
