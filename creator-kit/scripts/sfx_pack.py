#!/usr/bin/env python3
"""Generate the kit's SFX pack: short, clean, synthesised effects at 48 kHz stereo, peak -3 dBFS.
usage: sfx_pack.py <outdir>   -> writes *.wav + MANIFEST.md + audition.wav"""
import sys, os, math, random, wave, struct
SR = 48000; out = sys.argv[1]; os.makedirs(out, exist_ok=True); random.seed(11)
def noise(n): return [random.uniform(-1, 1) for _ in range(n)]
def lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); y = 0.0; o = []
    for v in x: y = a * y + (1 - a) * v; o.append(y)
    return o
def hp(x, fc): l = lp(x, fc); return [a - b for a, b in zip(x, l)]
def env_exp(n, tau): return [math.exp(-k / (tau * SR)) for k in range(n)]
def sine_sweep(f0, f1, n, curve=1.0):
    ph = 0.0; o = []
    for k in range(n):
        p = (k / n) ** curve; f = f0 + (f1 - f0) * p; ph += 2 * math.pi * f / SR; o.append(math.sin(ph))
    return o
def mul(x, e): return [a * b for a, b in zip(x, e)]
def mix(*parts):
    n = max(len(p) for p in parts); o = [0.0] * n
    for p in parts:
        for i, v in enumerate(p): o[i] += v
    return o
def gain(x, g): return [v * g for v in x]
def bell(n, up=0.3, down=0.7):
    o = []
    for k in range(n):
        p = k / n; o.append((p / up) ** 1.5 if p < up else max(0.0, (1 - p) / (1 - up)) ** down)
    return o
def sfx():
    S = {}
    n = int(0.02 * SR); S["ui_click_soft"] = mul(hp(noise(n), 3200), env_exp(n, 0.004))
    n = int(0.03 * SR); S["ui_click_hard"] = mix(mul(hp(noise(n), 2200), env_exp(n, 0.006)), gain(mul(sine_sweep(180, 180, n), env_exp(n, 0.01)), 0.6))
    n = int(0.06 * SR); S["key_thock"] = mix(mul(hp(noise(n), 2600), env_exp(n, 0.004)), gain(mul(sine_sweep(170, 170, n), env_exp(n, 0.012)), 0.9))
    n = int(0.09 * SR); S["key_space"] = gain(mul(sine_sweep(120, 120, n), env_exp(n, 0.02)), 0.9)
    n = int(0.012 * SR); S["tick"] = mul(hp(noise(n), 4500), env_exp(n, 0.003))
    n = int(0.7 * SR); S["impact_low"] = mix(mul(sine_sweep(160, 52, n, 0.25), env_exp(n, 0.16)), gain(mul(lp(noise(int(0.05 * SR)), 400), env_exp(int(0.05 * SR), 0.01)), 0.8))
    n = int(1.0 * SR); S["impact_deep"] = mix(mul(sine_sweep(120, 38, n, 0.2), env_exp(n, 0.28)), gain(mul(lp(noise(int(0.08 * SR)), 300), env_exp(int(0.08 * SR), 0.015)), 0.9))
    n = int(0.35 * SR); S["hit_snap"] = mix(mul(hp(noise(n), 1200), env_exp(n, 0.02)), gain(mul(sine_sweep(400, 90, n, 0.3), env_exp(n, 0.05)), 0.8))
    n = int(0.8 * SR); S["whoosh_short"] = mul(hp(lp(noise(n), 1800), 250), bell(n, 0.45, 0.8))
    n = int(1.4 * SR); S["whoosh_long"] = mul(hp(lp(noise(n), 1400), 180), bell(n, 0.55, 0.8))
    n = int(0.5 * SR); S["swish"] = mul(hp(lp(noise(n), 6000), 1500), bell(n, 0.35, 0.6))
    n = int(1.2 * SR); x = hp(noise(n), 1500); S["riser_air"] = mul(x, [((k / n) ** 1.6) * (1 if k / n < 0.9 else (1 - k / n) / 0.1) for k in range(n)])
    n = int(2.0 * SR); S["riser_tone"] = mul(sine_sweep(90, 720, n, 1.4), [((k / n) ** 1.3) * (1 if k / n < 0.92 else (1 - k / n) / 0.08) for k in range(n)])
    n = int(0.12 * SR); S["pop"] = mul(sine_sweep(900, 220, n, 0.5), env_exp(n, 0.025))
    n = int(0.9 * SR); S["ding"] = mix(mul(sine_sweep(1760, 1760, n), env_exp(n, 0.25)), gain(mul(sine_sweep(2640, 2640, n), env_exp(n, 0.12)), 0.4))
    n = int(0.25 * SR); S["shutter"] = mix(mul(hp(noise(int(0.02 * SR)), 2500), env_exp(int(0.02 * SR), 0.004)), [0.0] * int(0.11 * SR) + mul(hp(noise(int(0.03 * SR)), 1800), env_exp(int(0.03 * SR), 0.006)))
    n = int(0.6 * SR); S["reverse_whoosh"] = mul(hp(lp(noise(n), 2200), 300), [((k / n) ** 2.2) for k in range(n)])
    return S
def write(path, mono):
    pk = max(max(abs(v) for v in mono), 1e-6); g = 0.708 / pk
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<hh', int(max(-1, min(1, v * g)) * 32767), int(max(-1, min(1, v * g)) * 32767)) for v in mono))
S = sfx(); rows = []; aud = []
for name, x in S.items():
    write(os.path.join(out, name + ".wav"), x); rows.append(f"| {name}.wav | {len(x)/SR:.2f} s |"); aud += x + [0.0] * int(0.45 * SR)
write(os.path.join(out, "audition.wav"), aud)
open(os.path.join(out, "MANIFEST.md"), "w").write("# SFX pack\n\nSynthesised, 48 kHz stereo, peak -3 dBFS. `audition.wav` plays every sound in this order with a short gap.\n\n| file | length |\n|---|---|\n" + "\n".join(rows) + "\n\nWhere they are used: `intro_sfx.py` (key clicks, thock, space, impact, whoosh, riser). Drop real recordings with the same names into this folder to replace any of them.\n")
print(len(S), "sounds;", f"audition {len(aud)/SR:.1f}s")
