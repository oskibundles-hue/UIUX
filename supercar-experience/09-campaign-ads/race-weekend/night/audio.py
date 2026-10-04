"""audio.py - original score + designed accents for the F1 weekend ad, mastered for Instagram.

Everything here is synthesised from scratch in numpy (no samples, no third-party music), so the
track is owned outright and cleared for paid ads. 128 BPM in A minor, on the same beat grid as
edl.json / front.html (B = 0.46875 s). Accents sit ~7 dB (~45%) under the music; the music drops
into its own tape stop on b21-b22 before the end-card hit.

  python audio.py out.wav            -> 48 kHz stereo 24-bit, -14 LUFS integrated, TP <= -1.5 dBTP,
                                        last 50 ms silent (measured with ffmpeg ebur128 and printed)
"""
import sys, subprocess, re, os
import numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt, resample_poly

SR = 48000
B = 0.46875
FPS = 24000 / 1001
DUR = 360 / FPS                     # 15.015 s, same as the picture
N = int(round(DUR * SR))
rng = np.random.default_rng(1103)


def bt(n): return n * B
def at(t): return int(round(t * SR))
def env_exp(n, tau): return np.exp(-np.arange(n) / (tau * SR))
def hz(midi): return 440.0 * 2 ** ((midi - 69) / 12)


def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


def add(bus, sig, t, gain=1.0, pan=0.0):
    i = at(t)
    if i >= N: return
    s = sig[: N - i] * gain
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    if s.ndim == 1:
        bus[i:i + len(s), 0] += s * l * 1.414; bus[i:i + len(s), 1] += s * r * 1.414
    else:
        bus[i:i + len(s)] += s


# ---------------------------------------------------------------- instruments
def kick(dec=0.32):
    n = at(0.45); tt = np.arange(n) / SR
    f = 46 + 110 * np.exp(-tt / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    k = np.sin(ph) * env_exp(n, dec * 0.45)
    click = hp(rng.standard_normal(n), 2500) * env_exp(n, 0.003) * 0.35
    return np.tanh((k + click) * 1.6) * 0.9


def clap():
    n = at(0.35); x = bp(rng.standard_normal(n), 900, 5000)
    e = np.zeros(n)
    for d in (0, 0.011, 0.022):
        e[at(d):] += env_exp(n - at(d), 0.006 if d < 0.02 else 0.09)
    return x * e * 0.55


def hat(open_=False):
    n = at(0.25 if open_ else 0.06)
    x = hp(rng.standard_normal(n), 7000, 4)
    return x * env_exp(n, 0.07 if open_ else 0.012) * (0.3 if open_ else 0.22)


def saw(f, n, det=0.0):
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-det, 0, det):
        ph = (tt * f * (1 + d)) % 1.0
        out += 2 * ph - 1
    return out / 3


def bass_note(midi, n):
    x = saw(hz(midi), n, 0.004) * 0.7 + np.sin(2 * np.pi * hz(midi - 12) * np.arange(n) / SR) * 0.6
    e = np.minimum(1, np.arange(n) / at(0.004)) * env_exp(n, 0.09)
    return lp(x, 900) * e * 0.55


def pluck(midi, n):
    x = saw(hz(midi), n, 0.006)
    return lp(x, 2600) * env_exp(n, 0.07) * 0.18


def pad(chord, n):
    x = sum(saw(hz(m), n, 0.008) for m in chord) / len(chord)
    a = np.minimum(1, np.arange(n) / at(0.25))
    return lp(x, 1500) * a * 0.22


def beep(f, dur=0.09):
    n = at(dur); tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * f * tt)) * 0.5 + np.sin(2 * np.pi * f * tt) * 0.5
    e = np.minimum(1, np.arange(n) / at(0.002)) * np.minimum(1, (n - np.arange(n)) / at(0.01))
    return lp(x, 5000) * e * 0.32


def whoosh(dur=0.32, up=True, lo=300, hi=7000):
    n = at(dur); x = rng.standard_normal(n)
    out = np.zeros(n); steps = 24
    for k in range(steps):
        a, b = k * n // steps, (k + 1) * n // steps
        p = k / (steps - 1); p = p if up else 1 - p
        fc = lo * (hi / lo) ** p
        out[a:b] = bp(x[a:b], fc * 0.7, min(fc * 1.4, 20000))
    e = np.sin(np.pi * np.arange(n) / n) ** 1.5
    return out * e * 0.5


def impact(size=1.0):
    n = at(1.6); tt = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(30 + 50 * np.exp(-tt / 0.12)) / SR) * env_exp(n, 0.45)
    nz = lp(rng.standard_normal(n), 2500) * env_exp(n, 0.18) * 0.5
    return np.tanh((sub + nz) * 1.4) * 0.8 * size


def tick():
    n = at(0.02)
    atk = np.minimum(1, np.arange(n) / at(0.0015))          # 1.5 ms attack: no one-sample jump
    return hp(rng.standard_normal(n), 3000) * env_exp(n, 0.002) * atk * 0.5


def ding(f=1760):
    n = at(0.6); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.01 * tt)) * env_exp(n, 0.18) * 0.22


def snap():
    n = at(0.12)
    atk = np.minimum(1, np.arange(n) / at(0.0015))
    return (hp(rng.standard_normal(n), 1800) * env_exp(n, 0.006) * 0.7 +
            np.sin(2 * np.pi * 70 * np.arange(n) / SR) * env_exp(n, 0.04) * 0.6) * atk


def reverb(x, secs=1.1, mix=0.18):
    n = at(secs)
    ir = rng.standard_normal((n, 2)) * env_exp(n, secs / 5)[:, None]
    ir[:, 0] = lp(ir[:, 0], 6000); ir[:, 1] = lp(ir[:, 1], 6000)
    wet = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    wet *= np.sqrt(np.mean(x ** 2) / max(np.mean(wet ** 2), 1e-12))
    return x * (1 - mix) + wet * mix


# ---------------------------------------------------------------- music
def music():
    m = np.zeros((N + at(2), 2))
    roots = [45, 41, 43, 40, 45, 41]                    # A F G E A F (one per bar, bars 0-5)
    chords = {45: [57, 60, 64], 41: [53, 57, 60], 43: [55, 59, 62], 40: [52, 56, 59]}
    arp = [0, 7, 12, 15, 12, 7, 3, 7]
    for b in range(0, 21):                              # groove b0-b21
        add(m, kick(), bt(b), 0.95)
        if b % 2 == 1: add(m, clap(), bt(b), 0.7, 0.05)
        add(m, hat(True), bt(b + 0.5), 0.6, 0.3)
        root = roots[b // 4]
        for s in range(4):                              # 16th bass pulse
            add(m, bass_note(root - 12 + (12 if s == 3 else 0), at(B / 4 * 0.9)), bt(b + s / 4), 0.8)
        if b >= 4:
            for s in range(4): add(m, hat(), bt(b + s / 4), 0.5 if s % 2 else 0.8, -0.3)
        if b >= 7:
            for s in range(4):
                add(m, pluck(root + 24 + arp[(b * 4 + s) % 8], at(0.2)), bt(b + s / 4), 0.9, 0.35 * (-1) ** s)
    for bar in range(0, 6):
        r = roots[bar]; ch = chords[r]
        add(m, pad(ch, at(bt(4))), bt(bar * 4), 0.8)
    # riser into the tape stop
    n = at(bt(2)); x = rng.standard_normal(n)
    rise = np.zeros(n); k = 16
    for i in range(k):
        a, b = i * n // k, (i + 1) * n // k
        rise[a:b] = bp(x[a:b], 400 * (8000 / 400) ** (i / k), min(800 * (8000 / 400) ** (i / k), 20000))
    add(m, rise * np.linspace(0, 1, n) ** 2 * 0.35, bt(19))
    m = reverb(m, 0.9, 0.12)
    # tape stop on b21-b22: playback rate ramps 1 -> 0
    a, b = at(bt(21)), at(bt(22))
    seg = m[a:b].copy(); L = b - a
    rate = np.linspace(1, 0, L) ** 1.3
    pos = np.cumsum(rate); pos = pos / pos[-1] * (L * 0.55)
    idx = np.clip(pos, 0, L - 1)
    for c in range(2): m[a:b, c] = np.interp(idx, np.arange(L), seg[:, c]) * np.linspace(1, 0.2, L)
    m[b:] = 0
    # end card b22-b32: half-time, pad + soft kick, final hit on b30
    add(m, impact(1.0), bt(22), 0.9)
    add(m, pad([57, 60, 64, 69], at(bt(8.5))), bt(22), 2.4)
    for b in range(22, 30):                             # half-time groove under the end card
        if b % 2 == 0: add(m, kick(0.5), bt(b), 1.0)
        else: add(m, clap(), bt(b), 0.6, 0.05)
        add(m, hat(True), bt(b + 0.5), 0.45, 0.3)
        for s in range(2):
            add(m, bass_note(33 + (12 if s else 0), at(B / 2 * 0.9)), bt(b + s / 2), 0.9)
            add(m, hat(), bt(b + s / 2), 0.45, -0.3)
        for s in range(2):
            add(m, pluck([69, 72, 76, 81][(b * 2 + s) % 4], at(0.3)), bt(b + s / 2), 0.8, 0.35 * (-1) ** s)
    add(m, impact(0.8), bt(30), 0.7)
    add(m, pad([45, 57, 60, 64], at(bt(2))), bt(30), 2.0)
    m[at(bt(22)):] = reverb(m[at(bt(22)):], 1.6, 0.22)
    return m[:N]


# ---------------------------------------------------------------- accents (sync to the picture)
def accents():
    a = np.zeros((N + at(2), 2))
    for b, f in ((1, 880), (1.5, 880), (2, 1320), (5, 880), (6, 880), (7, 1320)):
        add(a, beep(f, 0.11 if f > 1000 else 0.08), bt(b), 1.0)
    for b, up in ((3, True), (9, False), (19, True)):                      # chequered wipes
        add(a, whoosh(0.3, up), bt(b) - 0.15, 1.0)
    for b in (5, 6, 7, 15, 16, 17, 20, 21):                               # whip cuts
        add(a, whoosh(0.16, True, 600, 9000), bt(b) - 0.09, 0.7, 0.4 * (-1) ** int(b))
    add(a, impact(0.6), bt(3), 0.6); add(a, impact(0.7), bt(8), 0.7)       # IN VEGAS / RACE NIGHT
    add(a, snap(), bt(12), 1.0); add(a, snap(), bt(12) + 0.03, 0.6)         # timing gates
    add(a, tick(), bt(13), 1.0); add(a, tick(), bt(13) + 0.05, 1.0)         # bracket lock
    add(a, impact(0.5), bt(15), 0.5)                                        # F1 WEEKEND slam
    for k in range(14):                                                     # countdown reel ticks (decelerating)
        add(a, tick(), bt(17) + 0.02 + 0.42 * (1 - (1 - k / 14) ** 0.5), 0.7)
    add(a, ding(1760), bt(17) + 0.46, 1.0)
    for k in range(16):
        add(a, tick(), bt(22.5) + bt(2) * (1 - (1 - k / 16) ** 0.5), 0.55)
    add(a, ding(1760), bt(24.5), 0.8)
    add(a, impact(0.5), bt(24), 0.55)                                       # BOOK NOW
    return reverb(a, 0.6, 0.1)[:N]


# ---------------------------------------------------------------- master
def measure(path):
    o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    s = o[o.rfind('Summary:'):]
    I = float(re.search(r'I:\s+(-?[\d.]+) LUFS', s).group(1))
    tp = float(re.search(r'Peak:\s+(-?[\d.]+) dBFS', s[s.find('True peak'):]).group(1))
    return I, tp


def limit(x, ceil_db=-3.2):
    c = 10 ** (ceil_db / 20)
    up = resample_poly(x, 4, 1, axis=0)                     # 4x oversampled true-peak estimate
    pk = np.abs(up).max(1).reshape(-1, 4).max(1)[: len(x)]
    g = np.minimum(1, c / np.maximum(pk, 1e-9))
    la = at(0.0015)
    gm = np.array([g[max(0, i - la):i + la + 1].min() for i in range(0, len(g), 16)])
    gm = np.repeat(gm, 16)[: len(g)]
    rel = 1 - np.exp(-1 / (0.06 * SR))
    out = np.empty_like(gm); cur = 1.0
    for i in range(len(gm)):
        cur = gm[i] if gm[i] < cur else cur + (gm[i] - cur) * rel
        out[i] = cur
    return x * out[:, None]


def main():
    dst = sys.argv[1]
    mus = music(); acc = accents()
    mix = mus + acc * 10 ** (-7 / 20) * 1.6               # accents ~45% under the music bed
    mix = np.stack([hp(mix[:, c], 25) for c in range(2)], 1)
    tmp = dst + '.pre.wav'
    gain = 1.0
    for it in range(4):
        y = limit(mix * gain)
        y[-at(0.05):] = 0                                   # last 50 ms silent
        fade = at(0.25); y[-at(0.05) - fade:-at(0.05)] *= np.linspace(1, 0, fade)[:, None]
        sf.write(tmp, y, SR, subtype='PCM_24')
        I, tp = measure(tmp)
        print(f'pass {it}: gain {20*np.log10(gain):+.2f} dB -> I {I:.2f} LUFS, TP {tp:.2f} dBTP', flush=True)
        if abs(I + 14) <= 0.3 and tp <= -3.0: break
        gain *= 10 ** ((-14 - I) / 20)
    os.replace(tmp, dst)
    I, tp = measure(dst)
    print(f'MASTER {dst}: {I:.2f} LUFS integrated, true peak {tp:.2f} dBTP, {len(y)/SR:.3f} s')


if __name__ == '__main__':
    main()
