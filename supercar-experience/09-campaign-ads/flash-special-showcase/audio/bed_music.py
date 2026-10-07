#!/usr/bin/env python3
"""
bed_music.py -- fix r2 sound bed: the CLIP'S OWN MUSIC as the main bed, designed accents under it.

Omarie, 26 Sept 2026: "Keep music as well if the videos ever have any." GT3RS_livery.mov carries a
music track (13.97 s, ~130 BPM, mastered hot: RMS -9.6 dB, peaks at 0 dBFS). The picture runs
18.018 s, so the music has to be extended. The options were tried in this order:

  (a) GT3RS_white.mov (same listing, daytime) -- NOT the same track. Waveform cross-correlation of
      2 s windows of the livery audio against the whole white audio peaks at |NCC| 0.10-0.11 (the same
      recording would be > 0.8), its tempo estimate differs (no stable ~130 BPM pulse), and its
      spectrum is different (34 % of the energy under 120 Hz vs 68 %). Nothing to continue from.
  (b) USED: a beat-matched loop extension. Self-similarity of the livery music shows its phrase
      repeating with a period of 5.4914 s (12 beats at ~131 BPM): orig 0.7-2.2 s matches orig
      6.2-7.7 s at NCC 0.79-0.82 (sample-exact lag refined at 48 kHz: 263 587 samples). The music
      plays straight through that repeat once: after orig B = 6.4764 s it continues from
      orig A = 0.9850 s (a quiet point just before the phrase's downbeat, -26 dB envelope dip on both
      sides), with a 12 ms equal-power crossfade. That adds exactly one phrase (5.491 s); the head
      is trimmed by 0.976 s (the quietest, least-defined part of the clip's intro) so that
        * the clip's strongest drop transient (orig 4.056 s) lands on the picture's DROP (8.571 s),
        * a kick (orig 10.041 s) lands on the END CARD hit (14.571 s, 15 ms early),
        * the splice sits at output 5.500 s, 71 ms before the whip into beat 11.
      No time-stretch at all (0 %).
  (c) not needed.

The music is never cut at a picture cut. The only level moves on it: a 12 ms fade-in at 0, a -4 dB
dip across the tape-stop moment (13.714 -> 14.52, back to 0 dB by the end-card hit at 14.571) so the
tape stop reads, and the final fade (17.35 -> 17.95 s) to digital silence (the last ~68 ms are 0).

ACCENTS (synth.py, the same generators as bed_hero.py). Each one is set to 45 % (-7 dB) of the
music's RMS over the accent's own energetic span (90 % of its energy, 20-300 ms; the end-card
impact 50 %). Everything pitched in F minor that
would clash with the track (pad, 808, kick/clap/hat pattern, pluck arp, braams, bells, the riser's
saw stack, the swell's chord, the synthetic engines) is removed.
  impact_open 0.000 | whooshes 1.714 3.429 5.571 10.714 12.857 (peaks) | lock-on ticks: door
  bracket acquire 3.84 / lock 4.02, crest lock 6.69, reel lands 9.000 9.107 9.214 9.429 |
  noise riser 6.857 -> 8.357 (into the black gap) | DROP impact 8.571 | impact_2 12.000 |
  tape stop 13.714 -> 14.143 (the music itself, varispeed-stopped, under the running track) |
  reversed cymbal swell 14.143 -> 14.571 | END CARD impact_3 14.571.

MASTER: sum -> look-ahead true-peak limiter whose detector is max(|L|, |R|, 0.707 |L+R|) (so the
-3 dB mono fold-down is held under the same ceiling as each channel) at -2.0 dBTP, gain iterated
to -14.0 LUFS (ffmpeg loudnorm print), plain numpy gain (no loudnorm resampling), 24-bit WAV,
864 865 samples = the picture's 432 frames at 23.976 fps.

    python3 audio/bed_music.py            # -> audio/bed_music.wav + audio/bed_music_sync.json
    python3 audio/bed_music.py --footage /path/to/footage --ffmpeg /path/to/ffmpeg
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
import synth as S  # noqa: E402
from synth import SR, n_of, db  # noqa: E402

SCRATCH = '/tmp/claude-0/-home-user-UIUX/2e2fc1bb-c45d-5ce1-ba97-afbf7647f193/scratchpad'
FPS = 24000 / 1001
N_OUT = int(round(432 / FPS * SR))        # 864 865 samples = 18.018 s

# ---- music edit (seconds of the ORIGINAL clip audio)
LAG = 263587 / SR                          # 5.491396 s phrase period (NCC-refined at 48 kHz)
SPLICE_A = 0.9850                          # continue from here ...
SPLICE_B = SPLICE_A + LAG                  # ... after playing up to here (6.4764 s)
HEAD = 0.9760                              # output 0 = orig 0.976 (drop transient 4.056 -> 8.571)
XF = 0.012                                 # equal-power crossfade at the splice
FADE0, FADE1 = 17.35, 17.95                # final fade to digital silence

# ---- picture cue times (edl.py / bed_hero_sync.json)
T_DROP, T_I2, T_STOP0, T_STOP1, T_END = 8.5714, 12.0, 13.7143, 14.1429, 14.5714
WHOOSH = [1.7143, 3.4286, 5.5714, 10.7143, 12.8571]
TICKS = [(3.84, 0.8), (4.02, 1.0), (6.69, 1.0), (9.000, 0.8), (9.107, 0.8), (9.214, 0.8), (9.429, 1.0)]
RISER = (6.8571, 8.3571)
ACC_RATIO = 0.45


def read_audio(ff, path):
    r = subprocess.run([ff, '-v', 'error', '-i', path, '-map', '0:a:0', '-f', 'f32le', '-ac', '2',
                        '-ar', str(SR), '-'], capture_output=True, check=True)
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
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', path, '-af',
                        'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True)
    return json.loads(re.findall(r'\{[^{}]+\}', r.stderr)[-1])


# ----------------------------------------------------------------------------- music
def music_edit(orig):
    """Output-length music: orig[HEAD : B] then orig[A : ...], equal-power crossfade at the splice."""
    s_out = n_of(SPLICE_B - HEAD)                 # output sample of the splice (5.500 s)
    lag = n_of(LAG)
    h = n_of(HEAD)
    n = N_OUT
    idx_pre = np.arange(n) + h                    # orig sample if no splice
    idx_post = idx_pre - lag
    pre = orig[np.clip(idx_pre, 0, len(orig) - 1)] * (idx_pre < len(orig))[:, None]
    post = orig[np.clip(idx_post, 0, len(orig) - 1)] * ((idx_post >= 0) & (idx_post < len(orig)))[:, None]
    xf = n_of(XF)
    u = np.clip((np.arange(n) - (s_out - xf // 2)) / xf, 0, 1)
    out = pre * np.cos(u * np.pi / 2)[:, None] + post * np.sin(u * np.pi / 2)[:, None]
    fi = n_of(0.012)
    out[:fi] *= (np.sin(np.linspace(0, np.pi / 2, fi)) ** 2)[:, None]
    info = dict(splice_out_sec=s_out / SR, orig_end_used_sec=(n + h - lag) / SR)
    return out, info


def music_gain_curve(n):
    t = np.arange(n) / SR
    g_db = np.zeros(n)
    # review r2 (craft): the tape stop doubled the running track. The music now hands over to its own
    # varispeed stop (running track out over 60 ms at T_STOP0) and comes back on the end-card hit, so the
    # stop IS the music, not a copy on top of it.
    dip = -80.0
    a = np.clip((t - T_STOP0) / 0.06, 0, 1)
    b = np.clip((t - (T_END - 0.05)) / 0.05, 0, 1)
    g_db += dip * a * (1 - b)
    g = db(g_db)
    g *= np.clip(t / 0.008, 0, 1)                    # 8 ms fade-in: no step on sample 0 (review r2 nit)
    f = np.clip((t - FADE0) / (FADE1 - FADE0), 0, 1)
    g *= np.cos(f * np.pi / 2) ** 2
    g[t >= FADE1] = 0.0
    return g


# ----------------------------------------------------------------------------- accents
def tick(rng, level=1.0):
    """Lock-on tick: 1.5 ms noise click + a 9 ms inharmonic metallic ping (no stable pitch)."""
    n = n_of(0.05)
    t = S.tax(n)
    click = S.fft_filter(rng.standard_normal(n), lo=2500, hi=12000) * np.exp(-t / 0.0015)
    ping = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((3170, 1.0), (4610, 0.6), (6930, 0.35)))
    ping = ping * np.exp(-t / 0.009) * np.minimum(1, t / 0.0004)
    x = click / np.abs(click).max() + 0.5 * ping
    return np.stack([x, x], 1) * level


def noise_riser(rng, dur, top=9000):
    """synth.riser without its saw stack (F2->F4) and snare roll: the noise band sweep only."""
    n = n_of(dur)
    t = S.tax(n)
    fcf = lambda tt: 350 * (top / 350) ** (np.clip(tt / dur, 0, 1) ** 1.3)
    mask = lambda tt, ff: 1 / np.sqrt(1 + 3.0 * (ff[None, :] / fcf(tt)[:, None] - fcf(tt)[:, None] / np.maximum(ff[None, :], 1)) ** 2)
    nz = np.stack([S.stft_mask(rng.standard_normal(n), mask) for _ in range(2)], 1)
    nz /= np.abs(nz).max()
    return nz * ((t / dur) ** 2.2)[:, None]


def cymbal_swell(rng, ir, dur):
    """synth.reverse_swell without the minor chord: a reversed open-cymbal bloom."""
    x = S.hat(rng, open_=True)
    wet = S.conv(np.concatenate([x, np.zeros(n_of(0.1))]), ir)
    n = n_of(dur)
    wet = wet[:n][::-1]
    wet /= np.abs(wet).max()
    tt = S.tax(len(wet))
    return wet * (tt / tt[-1])[:, None] ** 1.5


def tape_stop(music, t0, t1):
    """The running music, varispeed-stopped over [t0, t1) -- the tape-stop moment as an accent."""
    a, b = n_of(t0), n_of(t1)
    L = b - a
    u = np.arange(L) / L
    x = S.varispeed(music[a:a + L].copy(), (1 - u) ** 1.3)
    x = S.fft_filter(x, hi=9000)
    x *= np.minimum(1, (L - np.arange(L)) / n_of(0.02))[:, None]
    return x


def rms(x):
    return float(np.sqrt((x ** 2).mean()) + 1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--footage', default=os.path.join(SCRATCH, 'footage'))
    ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', os.path.join(SCRATCH, 'ffmpeg')))
    ap.add_argument('--out', default=os.path.join(HERE, 'bed_music'))
    ap.add_argument('--seed', type=int, default=11)
    A = ap.parse_args()
    ff = A.ffmpeg
    rng = np.random.default_rng(A.seed)

    orig = read_audio(ff, os.path.join(A.footage, 'GT3RS_livery.mov'))
    music, info = music_edit(orig)
    music_g = music * music_gain_curve(len(music))[:, None]

    ir_hall = S.reverb_ir(rng, t60=2.6, damp=0.3)
    ev = []                                          # (name, signal, place_t, measure_t)
    ev.append(('impact_open', S.impact(rng, ir_hall, size=0.8), 0.0, 0.0))
    for k, tw in enumerate(WHOOSH):
        w = S.whoosh(rng, dur=0.7, peak=0.62, direction=1 if k % 2 == 0 else -1)
        ev.append((f'whoosh_{tw:.3f}', w, tw - 0.7 * 0.62, tw - 0.15))
    for tt, lv in TICKS:
        ev.append((f'tick_{tt:.3f}', tick(rng, lv), tt, tt))
    rz = noise_riser(rng, RISER[1] - RISER[0])
    ev.append(('riser', rz, RISER[0], RISER[1] - 0.3))
    ev.append(('impact_drop', S.impact(rng, ir_hall, size=1.0), T_DROP, T_DROP))
    ev.append(('impact_2', S.impact(rng, ir_hall, size=1.0), T_I2, T_I2))
    ev.append(('tapestop', tape_stop(music, T_STOP0, T_STOP1), T_STOP0, T_STOP0))
    sw = cymbal_swell(rng, ir_hall, T_END - T_STOP1)
    ev.append(('swell', sw, T_END - len(sw) / SR, T_END - 0.3))
    ev.append(('impact_3', S.impact(rng, ir_hall, size=1.3, dur=3.3), T_END, T_END))

    acc = np.zeros_like(music)
    gains = {}
    win = n_of(0.3)
    for name, sig, tp, tm in ev:
        one = np.zeros_like(music)
        S.place(one, sig, tp, 1.0)
        m0 = n_of(tm)
        # window = the accent's own energetic span (90 % of its energy from m0), 20-300 ms, so a
        # 10 ms tick is compared with the music over 20 ms, not diluted over 300 ms
        e = np.cumsum((one[m0:m0 + win] ** 2).sum(1))
        wlen = int(np.clip(np.searchsorted(e, 0.9 * e[-1]) + 1, n_of(0.02), win))
        r_acc = rms(one[m0:m0 + wlen])
        r_mus = rms(music_g[m0:m0 + wlen]) if name != 'tapestop' else rms(music[m0:m0 + wlen])
        # the tape stop is the music itself (the running track is out while it plays), so it plays at
        # the music's own level; every other accent sits at ACC_RATIO under the music
        target = (0.50 if name == 'impact_3' else 1.0 if name == 'tapestop' else ACC_RATIO) * r_mus
        g = target / r_acc
        gains[name] = round(20 * np.log10(g), 2)
        acc += one * g
    # accents obey the same final fade as the music
    t = np.arange(len(acc)) / SR
    f = np.clip((t - FADE0) / (FADE1 - FADE0), 0, 1)
    acc *= (np.cos(f * np.pi / 2) ** 2)[:, None]
    acc[t >= FADE1] = 0

    mix = music_g + acc
    mix[t >= FADE1] = 0

    # ---- master: linked true-peak limiter (L, R, and the -3 dB mono sum) + gain to -14 LUFS
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
        g = np.convolve(np.concatenate([np.ones(L - 1), mm]), np.ones(L) / L, mode='valid')
        return x * np.minimum(g, 1)[:, None]

    tmp = A.out + '_tmp.wav'
    gain_db = -4.0
    for it in range(6):
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
    tail = fin[-n_of(0.05):]
    meta = dict(
        source='GT3RS_livery.mov audio (the clip\'s own music), extended by one phrase',
        option='b: beat-matched loop extension (white.mov is a different track; no time-stretch)',
        white_xcorr='max |NCC| 0.10-0.11 of 2 s livery windows against GT3RS_white.mov',
        edit=dict(head_orig_sec=HEAD, splice_orig_B=round(SPLICE_B, 6), splice_orig_A=SPLICE_A,
                  lag_sec=round(LAG, 6), lag_samples=n_of(LAG), crossfade_ms=XF * 1000, **info,
                  stretch_pct=0.0),
        alignment={'drop 8.571': 'orig 4.056 transient', 'endcard 14.571': 'orig 10.041 kick (15 ms early)',
                   'splice 5.500': 'whip 5.571'},
        accents_gain_db=gains, accent_ratio=ACC_RATIO,
        removed=['pad', '808', 'kick/clap/hat pattern', 'pluck arp', 'braams', 'bells', 'riser saw stack',
                 'swell chord', 'synthetic flat-six engines'],
        master=dict(gain_db=round(gain_db, 2), I=m['input_i'], TP=m['input_tp'], LRA=m['input_lra'],
                    mono_fold_minus3dB_tp_dbfs=round(float(mono_tp), 2),
                    last_50ms_peak=float(np.abs(tail).max())),
        samples=len(fin), seconds=len(fin) / SR,
    )
    json.dump(meta, open(A.out + '_sync.json', 'w'), indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == '__main__':
    main()
