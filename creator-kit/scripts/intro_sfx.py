#!/usr/bin/env python3
"""Synthesise the intro's sound design at the animation's own timings. Pure Python, 48 kHz stereo WAV.
usage: gen_sfx.py out.wav duration small_text big_text montageEnd"""
import sys, math, random, wave, struct
out, dur, small, big, mend = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4], float(sys.argv[5])
SR = 48000; N = int(dur * SR); L = [0.0] * N; R = [0.0] * N
random.seed(7)
def add(t, samples, gain=1.0, pan=0.0):
    i0 = int(t * SR)
    gl, gr = gain * (1 - max(0, pan)), gain * (1 + min(0, pan))
    for k, v in enumerate(samples):
        j = i0 + k
        if 0 <= j < N: L[j] += v * gl; R[j] += v * gr
def noise(n): return [random.uniform(-1, 1) for _ in range(n)]
def onepole_lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = 0.0; o = []
    for v in x: y = a * y + (1 - a) * v; o.append(y)
    return o
def hp(x, fc): lp = onepole_lp(x, fc); return [a - b for a, b in zip(x, lp)]
def env_exp(n, tau): return [math.exp(-k / (tau * SR)) for k in range(n)]
def click(bright=3000, length=0.018, tau=0.004):
    n = int(length * SR); x = hp(noise(n), bright); e = env_exp(n, tau); return [a * b for a, b in zip(x, e)]
def thock(f=170, length=0.06):
    n = int(length * SR); e = env_exp(n, 0.012); return [math.sin(2 * math.pi * f * k / SR) * e[k] for k in range(n)]
def whoosh(length=0.8):
    n = int(length * SR); x = noise(n); x = onepole_lp(x, 1800); x = hp(x, 250); o = []
    for k in range(n):
        p = k / n; e = math.sin(math.pi * min(1, p) ) ** 1.4 * (1 - 0.3 * p); o.append(x[k] * e)
    return o
def impact(f0=58, length=0.7):
    n = int(length * SR); e = env_exp(n, 0.16); ph = 0.0; o = []
    for k in range(n):
        f = f0 * (1 + 1.8 * math.exp(-k / (0.02 * SR))); ph += 2 * math.pi * f / SR; o.append(math.sin(ph) * e[k])
    t = onepole_lp(noise(int(0.05 * SR)), 400); et = env_exp(len(t), 0.01)
    for k in range(len(t)): o[k] += t[k] * et[k] * 0.8
    return o
def riser(length=1.1):
    n = int(length * SR); x = hp(noise(n), 1500); x = onepole_lp(x, 6000); o = []
    for k in range(n):
        p = k / n; e = (p ** 1.6) * (1 if p < 0.85 else (1 - p) / 0.15); o.append(x[k] * e)
    return o
# 1. montage cut ticks (quiet)
for i in range(1, 10): add(0.22 * i, click(4200, 0.012, 0.003), 0.18, pan=random.uniform(-0.4, 0.4))
# 2. typewriter: small line 0.15-0.95, big line 1.05-2.55 (same schedule as IntroCut.tsx)
def typed_times(text, a, b):
    n = len(text); return [(a + (b - a) * (k + 1) / n, ch) for k, ch in enumerate(text)]
for t, ch in typed_times(small, 0.15, 0.95):
    if ch != ' ': add(t, click(random.choice([2600, 3200, 3800]), 0.016, 0.0035), 0.45, pan=random.uniform(-0.25, 0.25))
for t, ch in typed_times(big, 1.05, 2.55):
    if ch != ' ': add(t, click(random.choice([2200, 2800]), 0.02, 0.005), 0.6, pan=random.uniform(-0.2, 0.2)); add(t, thock(random.choice([150, 175, 200])), 0.35)
    else: add(t, thock(120, 0.08), 0.5)   # space bar
# 3. frame opens: impact + whoosh
add(mend, impact(), 0.9); add(mend - 0.05, whoosh(0.85), 0.55, pan=0.0)
# 4. light leak riser 3.2-4.3, soft tail hit at 4.3
add(3.2, riser(1.1), 0.5); add(4.28, impact(72, 0.5), 0.35)
# normalise to -3 dBFS peak
pk = max(max(abs(v) for v in L), max(abs(v) for v in R), 1e-6); g = 0.708 / pk
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<hh', int(max(-1, min(1, L[i] * g)) * 32767), int(max(-1, min(1, R[i] * g)) * 32767)) for i in range(N)))
print('wrote', out, f'{dur}s peak gain {g:.2f}')
