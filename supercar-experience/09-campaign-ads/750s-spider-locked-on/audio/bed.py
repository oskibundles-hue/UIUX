#!/usr/bin/env python3
"""
bed.py -- the sound bed of "ROOF DOWN": the CLIP'S OWN MUSIC, continuous, with designed accents under it.

House rule 7 (LOCKED ON) and Omarie, 26 Sept 2026: "Keep music as well if the videos ever have any."
SCE_McLaren-750S_no-branding.mov carries a music track (24.36 s, 130.0 BPM, mastered hot, peaks at 0 dBFS).
The picture is 18.018 s, so no extension is needed: the music plays from orig 0.000 with NO edit, and the
picture was cut to it (lib/edl.py: every cut sits on a beat, G0 = 0.1154 s + k x 0.4615 s). Its low end
enters on beat 10 (4.731 s) = the DROP; its crash on beat 26 (12.115 s) = the giant-type hit. The track
changes section at orig ~18.2 s (a different phase: the clip's own edit), after the last picture frame.

The only moves on the music: an 8 ms fade-in at 0; the tape stop (the running track hands over to its own
varispeed stop at 13.500 s and comes back on the end-card hit, the bar downbeat at 13.962 s, playing on
from where it would be); the final fade 17.35 -> 17.95 s to digital silence.

ACCENTS (synth.py, the approved generators), each set to 45 % (-7 dB) of the music's RMS over the accent's
own energetic span (end-card impact 50 %, tape stop = the music itself at its own level):
  impact_open 0.000 | whooshes: hook exit 2.73, badge exit 4.47, whip 5.654, offer exit 7.84, whip 8.423,
  whip 10.731, SPIDER rise 11.19 | lock-on ticks: badge acquire 2.90 / lock 3.17, headlight 6.58 / 6.79,
  reel lands 5.192 5.308 5.423 5.654 | noise riser 3.23 -> 4.60 (into the black gap) | DROP impact 4.731 |
  crash impact 12.115 | tape stop 13.500 -> 13.962 | reversed cymbal swell into 13.962 | END CARD impact 13.962

MASTER: linked true-peak limiter (detector max(|L|, |R|, 0.707 |L+R|), so the -3 dB mono fold-down is held
too) at -2.0 dBTP, gain iterated to -14.0 LUFS (ffmpeg loudnorm print), 24-bit WAV of exactly the picture's
432 frames at 23.976 fps. Muxed as-is (no second loudnorm).

    python3 audio/bed.py --footage DIR --ffmpeg FFMPEG       # -> audio/bed.wav + audio/bed_sync.json
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
import synth as S  # noqa: E402
from synth import SR, n_of, db  # noqa: E402
import edl  # noqa: E402

CLIP = 'SCE_McLaren-750S_no-branding.mov'
N_OUT = int(round(edl.NF / edl.FPS * SR))
g = edl.g
T_DROP, T_CRASH, T_STOP0, T_END = edl.T_DROP, edl.T_CRASH, edl.T_STOP0, edl.T_END
FADE0, FADE1 = 17.35, 17.95
WHOOSH = [g(6) - 0.15, g(9) + 0.36, g(12), g(17) - 0.12, g(18), g(23), g(24) + 0.05]
TICKS = [(2.90, 0.8), (3.17, 1.0), (6.58, 0.8), (6.79, 1.0),
         (g(11), 0.8), (g(11) + edl.BEAT / 4, 0.8), (g(11) + edl.BEAT / 2, 0.8), (g(12), 1.0)]
RISER = (3.23, 4.60)
ACC_RATIO = 0.45


def read_audio(ff, path):
    r = subprocess.run([ff, '-v', 'error', '-i', path, '-map', '0:a:0', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, '<f4').reshape(-1, 2).astype(np.float64)


def write_wav24(path, x):
    import wave
    x = np.clip(x, -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    b = i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(b)


def loudness(ff, path):
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', path, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True)
    return json.loads(re.findall(r'\{[^{}]+\}', r.stderr)[-1])


def music_gain_curve(n):
    t = np.arange(n) / SR
    a = np.clip((t - T_STOP0) / 0.06, 0, 1)
    b = np.clip((t - (T_END - 0.05)) / 0.05, 0, 1)
    g_ = db(-80.0 * a * (1 - b))
    g_ *= np.clip(t / 0.008, 0, 1)
    f = np.clip((t - FADE0) / (FADE1 - FADE0), 0, 1)
    g_ *= np.cos(f * np.pi / 2) ** 2
    g_[t >= FADE1] = 0.0
    return g_


def tick(rng, level=1.0):
    n = n_of(0.05)
    t = S.tax(n)
    click = S.fft_filter(rng.standard_normal(n), lo=2500, hi=12000) * np.exp(-t / 0.0015)
    ping = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((3170, 1.0), (4610, 0.6), (6930, 0.35)))
    ping = ping * np.exp(-t / 0.009) * np.minimum(1, t / 0.0004)
    x = click / np.abs(click).max() + 0.5 * ping
    return np.stack([x, x], 1) * level


def noise_riser(rng, dur, top=9000):
    n = n_of(dur)
    t = S.tax(n)
    fcf = lambda tt: 350 * (top / 350) ** (np.clip(tt / dur, 0, 1) ** 1.3)
    mask = lambda tt, ff: 1 / np.sqrt(1 + 3.0 * (ff[None, :] / fcf(tt)[:, None] - fcf(tt)[:, None] / np.maximum(ff[None, :], 1)) ** 2)
    nz = np.stack([S.stft_mask(rng.standard_normal(n), mask) for _ in range(2)], 1)
    nz /= np.abs(nz).max()
    return nz * ((t / dur) ** 2.2)[:, None]


def cymbal_swell(rng, ir, dur):
    x = S.hat(rng, open_=True)
    wet = S.conv(np.concatenate([x, np.zeros(n_of(0.1))]), ir)
    wet = wet[:n_of(dur)][::-1]
    wet /= np.abs(wet).max()
    tt = S.tax(len(wet))
    return wet * (tt / tt[-1])[:, None] ** 1.5


def tape_stop(music, t0, t1):
    a, b = n_of(t0), n_of(t1)
    L = b - a
    u = np.arange(L) / L
    x = S.varispeed(music[a:a + L].copy(), (1 - u) ** 1.3)
    x = S.fft_filter(x, hi=9000)
    x *= np.minimum(1, (L - np.arange(L)) / n_of(0.02))[:, None]
    return x


def rms(x):
    return float(np.sqrt((x ** 2).mean()) + 1e-12)


def limit(x, ceiling_db):
    c = db(ceiling_db)
    n = len(x)
    os_ = 4
    up = np.fft.irfft(np.fft.rfft(x, axis=0), n * os_, axis=0) * os_
    det = np.maximum(np.abs(up).max(1), np.abs(up.sum(1)) * 0.7071)
    peak = det.reshape(n, os_).max(1)
    need = np.minimum(1, c / np.maximum(peak, 1e-9))
    L = n_of(0.0015 + 0.012)
    padded = np.concatenate([need, np.ones(L)])
    mm = np.lib.stride_tricks.sliding_window_view(padded, L).min(1)[:n]
    g_ = np.convolve(np.concatenate([np.ones(L - 1), mm]), np.ones(L) / L, mode='valid')
    return x * np.minimum(g_, 1)[:, None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--footage', required=True)
    ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', 'ffmpeg'))
    ap.add_argument('--out', default=os.path.join(HERE, 'bed'))
    ap.add_argument('--seed', type=int, default=11)
    A = ap.parse_args()
    ff = A.ffmpeg
    rng = np.random.default_rng(A.seed)

    orig = read_audio(ff, os.path.join(A.footage, CLIP))
    music = orig[:N_OUT].copy()
    assert len(music) == N_OUT, (len(music), N_OUT)
    music_g = music * music_gain_curve(len(music))[:, None]

    ir_hall = S.reverb_ir(rng, t60=2.6, damp=0.3)
    ev = [('impact_open', S.impact(rng, ir_hall, size=0.8), 0.0, 0.0)]
    for k, tw in enumerate(WHOOSH):
        w = S.whoosh(rng, dur=0.7, peak=0.62, direction=1 if k % 2 == 0 else -1)
        ev.append((f'whoosh_{tw:.3f}', w, tw - 0.7 * 0.62, tw - 0.15))
    for tt, lv in TICKS:
        ev.append((f'tick_{tt:.3f}', tick(rng, lv), tt, tt))
    ev.append(('riser', noise_riser(rng, RISER[1] - RISER[0]), RISER[0], RISER[1] - 0.3))
    ev.append(('impact_drop', S.impact(rng, ir_hall, size=1.0), T_DROP, T_DROP))
    ev.append(('impact_crash', S.impact(rng, ir_hall, size=0.9), T_CRASH, T_CRASH))
    ev.append(('tapestop', tape_stop(music, T_STOP0, T_END), T_STOP0, T_STOP0))
    sw = cymbal_swell(rng, ir_hall, 0.42)
    ev.append(('swell', sw, T_END - len(sw) / SR, T_END - 0.3))
    ev.append(('impact_end', S.impact(rng, ir_hall, size=1.3, dur=3.3), T_END, T_END))

    acc = np.zeros_like(music)
    gains = {}
    win = n_of(0.3)
    for name, sig, tp, tm in ev:
        one = np.zeros_like(music)
        S.place(one, sig, tp, 1.0)
        m0 = n_of(tm)
        e = np.cumsum((one[m0:m0 + win] ** 2).sum(1))
        wlen = int(np.clip(np.searchsorted(e, 0.9 * e[-1]) + 1, n_of(0.02), win))
        r_acc = rms(one[m0:m0 + wlen])
        # the tape stop and the swell play while the running track is out, so they are measured against the
        # un-dipped music (music_g is ~0 there)
        r_mus = rms((music if name in ('tapestop', 'swell') else music_g)[m0:m0 + wlen])
        target = (0.50 if name == 'impact_end' else 1.0 if name == 'tapestop' else ACC_RATIO) * r_mus
        gn = target / r_acc
        gains[name] = round(20 * np.log10(gn), 2)
        acc += one * gn
    t = np.arange(len(acc)) / SR
    f = np.clip((t - FADE0) / (FADE1 - FADE0), 0, 1)
    acc *= (np.cos(f * np.pi / 2) ** 2)[:, None]
    acc[t >= FADE1] = 0
    mix = music_g + acc
    mix[t >= FADE1] = 0

    tmp = A.out + '_tmp.wav'
    gain_db = -2.0
    for _ in range(8):
        y = limit(mix * db(gain_db), -2.0)
        y[t >= FADE1] = 0
        write_wav24(tmp, y)
        m = loudness(ff, tmp)
        err = -14.0 - float(m['input_i'])
        if abs(err) < 0.05:
            break
        gain_db += err
    os.replace(tmp, A.out + '.wav')
    fin = read_audio(ff, A.out + '.wav')
    mono_tp = 20 * np.log10(np.abs(np.fft.irfft(np.fft.rfft(fin.sum(1) * 0.7071), len(fin) * 4) * 4).max())
    meta = dict(
        source=CLIP + " audio (the clip's own music), orig 0.000 -> 18.018 s, no edit, no time-stretch",
        grid=dict(bpm=edl.BPM, g0=edl.G0, drop=round(T_DROP, 4), crash=round(T_CRASH, 4), tapestop=round(T_STOP0, 4),
                  endcard=round(T_END, 4)),
        accents_gain_db=gains, accent_ratio=ACC_RATIO,
        master=dict(gain_db=round(gain_db, 2), I=m['input_i'], TP=m['input_tp'], LRA=m['input_lra'],
                    mono_fold_minus3dB_tp_dbfs=round(float(mono_tp), 2),
                    last_50ms_peak=float(np.abs(fin[-n_of(0.05):]).max())),
        samples=len(fin), seconds=len(fin) / SR)
    json.dump(meta, open(A.out + '_sync.json', 'w'), indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == '__main__':
    main()
