"""audio_day.py - soundtrack for the DAY ad: Car Scenes' ORIGINAL music from Day Time Duo 1, plus light accents.

LICENCE NOTE: Car Scenes music: organic posts OK; paid ads only after Car Scenes confirms the licence.
The music plays once, unbroken, from music time 4.010 s (a bar downbeat / strong hit) to the clip's own
outro at 22.6 s: no tape stop, no time-stretch, no copies layered on it. Level moves: 5 ms fade-in at a
zero-ish point, the clip's own outro, then a 0.4 s fade to digital silence (last 50 ms are 0).
Accents (each with >= 10 ms fade-in and fade-out, ~45 % under the music): soft whooshes under the sun-flare
wipes, a low snap on each lock-on. MASTER: true-peak limiter checked through the AAC encode, -14 LUFS.
"""
import sys, os, subprocess, json
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio as A
E = json.load(open(os.path.join(HERE, 'edl.json')))
SR = A.SR; FPS = A.FPS; P = E['beat']; S0 = E['music_start']
NFR = round(E['beats_total'] * P * FPS); N = int(round(NFR / FPS * SR)); A.N = N
SRC = os.path.join(os.path.dirname(HERE), 'audio', 'day_st.wav')
def bt(a): return a * P
def at(t): return int(round(t * SR))
def fades(x, ms=10):
    k = at(ms / 1000); x = x.copy()
    x[:k] *= np.linspace(0, 1, k)[:, None] if x.ndim == 2 else np.linspace(0, 1, k)
    x[-k:] *= np.linspace(1, 0, k)[:, None] if x.ndim == 2 else np.linspace(1, 0, k)
    return x

def main():
    dst = sys.argv[1]
    src, sr = sf.read(SRC); assert sr == SR and src.ndim == 2
    i0 = at(S0); mus = src[i0:i0 + N].copy()
    if len(mus) < N: mus = np.vstack([mus, np.zeros((N - len(mus), 2))])
    mus[:at(0.005)] *= np.linspace(0, 1, at(0.005))[:, None]
    acc = np.zeros((N + at(2), 2))
    for b in (4, 8, 16, 20, 28, 36):
        A.add(acc, fades(A.whoosh(0.4, True, 400, 6000)), bt(b) - 0.22, 0.8)
    for b in (16, 20):
        sn = A.snap(); sn[:at(0.010)] *= np.linspace(0, 1, at(0.010)); A.add(acc, fades(sn), bt(b) + 0.04, 0.9)
    acc = acc[:N]
    rm = np.sqrt(np.mean(mus ** 2)); ra = np.sqrt(np.mean(acc[np.abs(acc).sum(1) > 1e-4] ** 2))
    acc *= (rm * 10 ** (-7 / 20)) / max(ra, 1e-9) * 0.6
    mix = mus + acc
    tmp = dst + '.pre.wav'; gain = 1.0; ceil = -3.0
    for it in range(10):
        y = A.limit(mix * gain, ceil)
        fade = at(0.4); z = at(0.05)
        y[-z - fade:-z] *= np.linspace(1, 0, fade)[:, None]; y[-z:] = 0
        sf.write(tmp, y, SR, subtype='PCM_24')
        I, tp = A.measure(tmp)
        print(f'pass {it}: gain {20*np.log10(gain):+.2f} dB -> I {I:.2f} LUFS, TP {tp:.2f} dBTP', flush=True)
        if abs(I + 14) <= 0.2:
            m4a = dst + '.chk.m4a'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-c:a', 'aac', '-b:a', '256k', m4a], check=True)
            Ia, tpa = A.measure(m4a)
            print(f'   after AAC: I {Ia:.2f} LUFS, TP {tpa:.2f} dBTP (ceiling {ceil:.2f})', flush=True)
            if tpa <= -2.2: break
            ceil -= (tpa + 2.2) + 0.1; continue
        gain *= 10 ** ((-14 - I) / 20)
    os.replace(tmp, dst)
    I, tp = A.measure(dst)
    print(f'MASTER {dst}: {I:.2f} LUFS, TP {tp:.2f} dBTP, {len(y)/SR:.3f} s (music {S0:.3f}-{S0+len(y)/SR:.3f} s of the source)')

if __name__ == '__main__':
    main()
