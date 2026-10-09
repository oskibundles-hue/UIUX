"""music.py -- the TEMP BED for Chapter 5 "Nampa, Idaho · night": an original warm-synth / lo-fi pad written here in numpy (no sample, no
library track, nothing from the footage). Copy of ../ch4/music.py with its own key, tempo, chords and seed so chapters differ
(test-ch3: 78 BPM F/C; Ch1: 72 E-flat; Ch2: 75 D; Ch4: 82 A; Ch5: 80 G; Ch6: 66 C minor; Ch7: 84 E; Ch8: 86 B-flat):
80 BPM, G major, Gmaj9 - Em9 - Cmaj9 - Dsus2 (two bars each), seed 51: a detuned soft-saw pad through a gentle low-pass (1400 Hz),
a sine sub, a muted Rhodes-like pluck on beats 1 and 3, a soft kick and a quiet shaker.
Placeholder until Omarie's Epidemic Sound account is set up (HANDOFF-lifestyle.md); the README records it.
    python3 music.py OUT.wav SECONDS
"""music.py -- the TEMP BED: an original warm-synth / lo-fi pad written here in numpy (no sample, no library track, nothing
from the footage). Chapter 4 copy of ../test-ch3/music.py with its own key and tempo so chapters differ (test-ch3: 78 BPM F/C;
Ch1: 72 BPM E-flat; Ch2: 75 BPM D): 82 BPM, A major, Amaj9 - F#m9 - Dmaj9 - Esus2 (two bars each), seed 41: a detuned soft-saw pad through a gentle
low-pass, a sine sub, a muted Rhodes-like pluck on beats 1 and 3, a soft kick and a quiet shaker. Placeholder until
Omarie's Epidemic Sound account is set up (HANDOFF-lifestyle.md); the README records it.
    python3 music.py OUT.wav SECONDS
"""
import sys, wave
import numpy as np

SR = 48000
BPM = 80
BEAT = 60 / BPM
CHORDS = [[55, 59, 62, 66, 69], [52, 55, 59, 62, 66], [48, 52, 55, 59, 62], [50, 57, 62, 64, 69]]  # Gmaj9 - Em9 - Cmaj9 - Dsus2
BASS = [31, 28, 36, 38]
SPARSE = False
LP = 1400
rng = np.random.default_rng(51)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp_fft(x, fc, slope=2):
    n = len(x)
    N = 1 << int(np.ceil(np.log2(n)))
    f = np.fft.rfftfreq(N, 1 / SR)
    H = 1 / np.sqrt(1 + (f / fc) ** (2 * slope))
    return np.fft.irfft(np.fft.rfft(x, N) * H, N)[:n]


def saw(f, t, ph=0.0):
    # band-limited-ish soft saw: 8 harmonics
    return sum(np.sin(2 * np.pi * k * f * t + ph * k) / k for k in range(1, 9))


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def make(seconds):
    n = int(seconds * SR)
    L = np.zeros(n); R = np.zeros(n)
    bar = 4 * BEAT
    seg = 2 * bar
    t_all = np.arange(n) / SR
    k = 0
    while k * seg < seconds:
        c = CHORDS[k % 4]
        s0 = int(k * seg * SR); s1 = min(n, int(((k + 1) * seg + 0.6) * SR))
        t = t_all[s0:s1] - k * seg
        e = env_adsr(s1 - s0, 1.2, 1.4)
        for i, m in enumerate(c):
            for det, side in ((-0.07, 0), (0.07, 1)):
                v = saw(hz(m) * 2 ** (det / 12), t, ph=i) * e * 0.05
                (L if side == 0 else R)[s0:s1] += v
        sub = np.sin(2 * np.pi * hz(BASS[k % 4]) * t) * e * 0.16
        L[s0:s1] += sub; R[s0:s1] += sub
        # Rhodes-like pluck on beats 1 and 3 of each bar
        for b in ((0,) if SPARSE else range(0, 8, 2)):
            p0 = s0 + int(b * BEAT * SR)
            if p0 >= n:
                break
            pn = min(n - p0, int(1.6 * SR))
            tp = np.arange(pn) / SR
            pe = np.exp(-tp * 3.2)
            for m in c[1:4]:
                v = (np.sin(2 * np.pi * hz(m + 12) * tp) + 0.25 * np.sin(2 * np.pi * hz(m + 24) * tp) * np.exp(-tp * 8)) * pe * 0.045
                L[p0:p0 + pn] += v * 0.8; R[p0:p0 + pn] += v
        k += 1
    pad = np.stack([lp_fft(L, LP), lp_fft(R, LP)], 1)
    # drums: soft kick on 1 and 3, shaker on the 8ths (quiet)
    drums = np.zeros((n, 2))
    b = 0
    while b * BEAT < seconds:
        p0 = int(b * BEAT * SR)
        if (b % 4 == 0) if SPARSE else (b % 2 == 0):
            kn = min(n - p0, int(0.35 * SR)); tk = np.arange(kn) / SR
            kick = np.sin(2 * np.pi * (48 + 60 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 9) * 0.2
            drums[p0:p0 + kn] += kick[:, None]
        for h in (() if SPARSE else (0, 0.5)):
            q0 = p0 + int(h * BEAT * SR)
            hn = min(n - q0, int(0.06 * SR))
            if hn > 0:
                sh = rng.standard_normal(hn) * np.exp(-np.arange(hn) / SR * 60) * (0.03 if h else 0.018)
                drums[q0:q0 + hn, 0] += sh * 0.8; drums[q0:q0 + hn, 1] += sh
        b += 1
    out = pad + drums
    out *= 0.5 / max(1e-9, np.abs(out).max())
    return out


def write_wav24(path, x):
    x = np.clip(x, -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR)
        w.writeframes(i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())


if __name__ == '__main__':
    write_wav24(sys.argv[1], make(float(sys.argv[2])))
    print('bed written', sys.argv[1])
