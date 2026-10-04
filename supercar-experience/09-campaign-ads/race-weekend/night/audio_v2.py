"""audio_v2.py - soundtrack for v2: Car Scenes' ORIGINAL music from the source clip, plus light accents.

LICENCE NOTE: the music is the audio of Car Scenes' "Duo AMG x SF90 No Logo" edit. Omarie chose it
(3 Oct 2026). Organic posts OK; paid ads only after Car Scenes confirms the licence.

The music plays continuously from ONE start point (house style: never chopped at picture cuts):
music time = ad time + 2.9163 s, which puts its drop (5.6131 s) on ad beat 4 and keeps every picture
cut on its 89.0 BPM grid (beat 0.6742 s). No time-stretch.
Level moves on the music only: 12 ms fade-in, a -4 dB dip across the tape stop (a16 -> a17, back to
0 dB at the end-card hit), the final fade (last 0.6 s) to digital silence (last 50 ms are 0).
Tape stop: a varispeed copy of the music itself, a16 -> a17, laid over the dipped track.
Accents (generators from audio.py) sit ~7 dB (~45 %) under the music: chequered-wipe whooshes,
gate snap, bracket ticks, reel ticks + landing dings, end-card impact.
MASTER: true-peak limiter (4x oversampled) at -3.6 dBFS, gain iterated to -14 LUFS.
"""
import sys, os, subprocess
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio as A
import json

HERE = os.path.dirname(os.path.abspath(__file__))
E = json.load(open(os.path.join(HERE, 'edl.json')))
SR = A.SR; FPS = A.FPS
P = E['beat']; S0 = E['music_start']
NFR = round(E['beats_total'] * P * FPS)
N = int(round(NFR / FPS * SR))
SRC = os.path.join(os.path.dirname(HERE), 'audio', 'src_st.wav')
A.N = N   # audio.add() clips against its module N


def bt(a): return a * P
def at(t): return int(round(t * SR))


def main():
    dst = sys.argv[1]
    src, sr = sf.read(SRC)
    assert sr == SR and src.ndim == 2
    i0 = at(S0)
    mus = src[i0:i0 + N].copy()
    if len(mus) < N: mus = np.vstack([mus, np.zeros((N - len(mus), 2))])
    mus[:at(0.012)] *= np.linspace(0, 1, at(0.012))[:, None]
    # tape stop a16 -> a17
    a, b = at(bt(16)), at(bt(17)); L = b - a
    seg = mus[a:b].copy()
    rate = np.linspace(1, 0, L) ** 1.3
    pos = np.cumsum(rate); pos = pos / pos[-1] * (L * 0.55)
    ts = np.stack([np.interp(pos, np.arange(L), seg[:, c]) for c in range(2)], 1) * np.linspace(1, 0.15, L)[:, None]
    dip = np.ones(N); dip[a:b] = 10 ** (-4 / 20); dip[b - at(0.03):b] = np.linspace(10 ** (-4 / 20), 1, at(0.03))
    dip[a:a + at(0.03)] = np.linspace(1, 10 ** (-4 / 20), at(0.03))
    mus = mus * dip[:, None]
    fi = at(0.010); ts[:fi] *= np.linspace(0, 1, fi)[:, None]; ts[-fi:] *= np.linspace(1, 0, fi)[:, None]   # no click
    mus[a:b] += ts * 0.8

    # accents, ~45 % of the music
    acc = np.zeros((N + at(2), 2))
    for t, up in ((bt(4), True), (bt(8), False), (bt(14), True)):
        A.add(acc, A.whoosh(0.3, up), t - 0.15, 0.9)
    A.add(acc, A.snap(), bt(9), 1.0); A.add(acc, A.snap(), bt(9) + 0.03, 0.6)
    A.add(acc, A.tick(), bt(9.25), 1.0); A.add(acc, A.tick(), bt(9.25) + 0.05, 1.0)
    for b in (12, 12.5, 13): A.add(acc, A.tick(), bt(b), 1.0)     # THU / FRI / SAT
    A.add(acc, A.impact(0.4), bt(13.25), 0.6)                       # RACE NIGHT
    A.add(acc, A.impact(0.7), bt(17), 0.9)
    acc = acc[:N]
    rm = np.sqrt(np.mean(mus ** 2)); ra = np.sqrt(np.mean(acc[np.abs(acc).sum(1) > 1e-4] ** 2))
    acc *= (rm * 10 ** (-7 / 20)) / max(ra, 1e-9) * 0.6     # accents are sparse; their busy spans land ~45 % of the music
    mix = mus + acc

    tmp = dst + '.pre.wav'; gain = 1.0; ceil = -3.6
    for it in range(10):
        y = A.limit(mix * gain, ceil)
        fade = at(0.6); z = at(0.05)
        y[-z - fade:-z] *= np.linspace(1, 0, fade)[:, None]; y[-z:] = 0
        sf.write(tmp, y, SR, subtype='PCM_24')
        I, tp = A.measure(tmp)
        print(f'pass {it}: gain {20*np.log10(gain):+.2f} dB -> I {I:.2f} LUFS, TP {tp:.2f} dBTP', flush=True)
        if abs(I + 14) <= 0.2:
            # the AAC encode overshoots this dense master by ~2 dB: check the real delivery codec
            m4a = dst + '.chk.m4a'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-c:a', 'aac', '-b:a', '256k', m4a], check=True)
            Ia, tpa = A.measure(m4a)
            print(f'   after AAC: I {Ia:.2f} LUFS, TP {tpa:.2f} dBTP (ceiling {ceil:.2f})', flush=True)
            if tpa <= -2.2: break
            ceil -= (tpa + 2.2) + 0.1
            continue
        gain *= 10 ** ((-14 - I) / 20)
    os.replace(tmp, dst)
    I, tp = A.measure(dst)
    print(f'MASTER {dst}: {I:.2f} LUFS integrated, true peak {tp:.2f} dBTP, {len(y)/SR:.3f} s (music {S0:.4f}-{S0+len(y)/SR:.4f} s of the source)')


if __name__ == '__main__':
    main()
