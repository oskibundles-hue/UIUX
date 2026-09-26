#!/usr/bin/env python3
"""mix.py -- the sound of the Locked-On layer: the approved vlog audio untouched, plus quiet accents.

    python3 lib/mix.py --video V.mp4 --ffmpeg FF --times .work/page.json --captions lib/data/captions.json \
                       --out .work/mix.wav [--report .work/mix.json]

Main track: the T7 cut's own audio (his voice + the music), sample for sample, no EQ, no ducking, no edits.
The only things done to it: one static gain to land the whole mix on -14.0 LUFS (it is -14.5 LUFS as
delivered), a transparent true-peak limiter that only touches the few peaks above the ceiling, and a 40 ms
fade on its very last samples (it ended on a non-zero sample, which would click) where the tail takes over.

Accents (all synthesised here with lib/synth.py, so they are original and cleared):
  * a soft whoosh on each chapter card, peaking as the panel finishes unrolling
  * lock-on ticks: two per car lock (acquire, lock) and one on each route waypoint (on the spoken word)
  * an impact on the end card
Level rule: each accent's loudest 50 ms sits 20 dB under the programme around it (the 90th percentile of
the programme's 50 ms RMS over +-0.6 s, i.e. the dialogue peaks), and the whole accent bus is ducked a
further 6 dB while a word is being spoken (lib/data/captions.json word highlight, +-0.12/0.25 s, 40 ms
ramps). The accents never mask speech.

Tail: the picture runs 1.6 s past the source audio (the Locked-On end card). The audio carries on with the
music's own natural decay (a wet-only reverb of its last 0.8 s, synthetic hall, no dry repeat) plus the end
card impact's tail, fades to silence, and the last 50 ms (and more) are exact zeros.
Loudness is measured with ffmpeg loudnorm (print) on the final buffer: -14.0 LUFS integrated, true peak
<= -2.2 dBTP pre-AAC (so the AAC decode stays under -1.5 dBTP).
"""
import argparse, json, os, re, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S  # noqa: E402

SR = 48000
FPS = 30000 / 1001
FF = None


def limiter_gain(det, ceiling_db, look=0.0015, release=0.012, os_=4):
    """Gain curve of synth.limiter (4x-oversampled true-peak brickwall) for a multi-column detector,
    so the same gain can be applied to L/R while the detector also sees the mono fold-down."""
    c = S.db(ceiling_db)
    n = det.shape[0]
    X = np.fft.rfft(det, axis=0)
    up = np.fft.irfft(X, n * os_, axis=0) * os_
    peak = np.abs(up).max(1).reshape(n, os_).max(1)
    need = np.minimum(1, c / np.maximum(peak, 1e-9))
    L = S.n_of(look + release)
    mm = np.lib.stride_tricks.sliding_window_view(np.concatenate([need, np.ones(L)]), L).min(1)[:n]
    g = np.convolve(np.concatenate([np.ones(L - 1), mm]), np.ones(L) / L, mode='valid')
    return np.minimum(g, 1)


def tick(rng, level=1.0):
    """Lock-on tick (from the showcase's audio/bed_music.py): 1.5 ms noise click + a 9 ms inharmonic ping."""
    n = S.n_of(0.05)
    t = S.tax(n)
    click = S.fft_filter(rng.standard_normal(n), lo=2500, hi=12000) * np.exp(-t / 0.0015)
    ping = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((3170, 1.0), (4610, 0.6), (6930, 0.35)))
    ping = ping * np.exp(-t / 0.009) * np.minimum(1, t / 0.0004)
    x = click / np.abs(click).max() + 0.5 * ping
    return np.stack([x, x], 1) * level


def rms50(x):
    """50 ms RMS (dBFS) of a stereo buffer, hop 10 ms."""
    m = (x ** 2).mean(1)
    L, hop = S.n_of(0.05), S.n_of(0.01)
    if len(m) < L:
        return np.array([10 * np.log10(m.mean() + 1e-12)])
    c = np.concatenate([[0], np.cumsum(m)])
    idx = np.arange(0, len(m) - L + 1, hop)
    return 10 * np.log10((c[idx + L] - c[idx]) / L + 1e-12)


def loudness(ff, x, tmp):
    write_wav(tmp, x, bits=32)
    err = subprocess.run([ff, '-hide_banner', '-nostats', '-i', tmp, '-af',
                          'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    j = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', err, re.S).group(0))
    return float(j['input_i']), float(j['input_tp'])


def write_wav(path, x, bits=24):
    import wave
    x = np.clip(x, -1, 1)
    if bits == 32:   # float WAV via ffmpeg (wave module cannot write float)
        raw = x.astype('<f4').tobytes()
        subprocess.run([FF, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_f32le', path],
                       input=raw, check=True)
        return
    q = np.round(x * (2 ** 23 - 1)).astype('<i4')
    b = np.stack([(q >> s) & 0xFF for s in (0, 8, 16)], -1).astype(np.uint8).reshape(-1).tobytes()
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR); w.writeframes(b)


def main():
    global FF
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True); ap.add_argument('--ffmpeg', required=True)
    ap.add_argument('--times', required=True); ap.add_argument('--captions', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--report')
    A = ap.parse_args()
    FF = A.ffmpeg
    T = json.load(open(A.times))['TIMES']
    raw = subprocess.run([FF, '-v', 'error', '-i', A.video, '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    src = np.frombuffer(raw, '<f4').reshape(-1, 2).astype(np.float64)
    N = int(round(T['total'] * SR))
    n_src = len(src)
    rng = np.random.default_rng(915)
    ir = S.reverb_ir(rng, t60=1.6, predelay=0.010, damp=0.45)

    # ---------------------------------------------------------------- speech envelope (captions)
    cap = json.load(open(A.captions))
    word = np.array(cap['word'], bool)
    sp = np.zeros(N)
    for i in np.where(word)[0]:
        a, b = S.n_of(i / FPS - 0.12), S.n_of((i + 1) / FPS + 0.25)
        sp[max(0, a):min(N, b)] = 1
    ramp = S.n_of(0.04)
    k = np.ones(ramp) / ramp
    duck_db = -6.0
    duck = 10 ** (duck_db * np.convolve(sp, k, mode='same') / 20)

    # ---------------------------------------------------------------- accents
    events = []                                  # (name, buffer, start time, main time)
    for i, c in enumerate(T['ch']):
        dur, pk = 0.62, 0.45
        wz = S.whoosh(rng, dur=dur, peak=pk, direction=1 if i % 2 == 0 else -1, f0=300, f1=4200)
        wz = S.fft_filter(wz, lo=180, hi=7000)
        t_peak = c['ts'] + 0.20
        events.append((f'whoosh_ch{i + 1}', wz, t_peak - dur * pk, t_peak))
    for k_, tk in enumerate(T['ticks']):
        events.append((f'tick_route{k_ + 1}', tick(rng), tk, tk))
    for key in ('soe', 'urus'):
        a = T[key]['a']
        events.append((f'tick_{key}_acquire', tick(rng, 0.8), a, a))
        events.append((f'tick_{key}_lock', tick(rng), a + 0.23, a + 0.23))
    imp = S.impact(rng, ir, size=0.75, dur=3.4)
    events.append(('impact_end', imp, T['end'], T['end']))

    prog = np.zeros((N, 2)); prog[:n_src] = src[:N]
    bus = np.zeros((N, 2))
    rep = []
    for name, x, t0, tm in events:
        # reference: the programme's 50 ms RMS over +-0.6 s around the accent (90th percentile = dialogue peaks)
        a, b = max(0, S.n_of(tm - 0.6)), min(n_src, S.n_of(tm + 0.6))
        ref = float(np.percentile(rms50(src[a:b]), 90)) if b - a > S.n_of(0.1) else -30.0
        own = float(rms50(x).max())
        g = 10 ** ((ref - 20.0 - own) / 20)
        S.place(bus, x * g, t0)
        s0 = S.n_of(tm)
        rep.append(dict(name=name, t=round(tm, 3), ref_db=round(ref, 1), accent_db=round(ref - 20.0, 1),
                        ducked=bool(sp[min(N - 1, s0)] > 0.5)))
    bus *= duck[:, None]

    # ---------------------------------------------------------------- tail (natural decay of the music)
    fade = S.n_of(0.04)
    prog[n_src - fade:n_src] *= np.cos(np.linspace(0, np.pi / 2, fade))[:, None] ** 2
    seg = src[n_src - S.n_of(0.8):n_src]
    wet = np.stack([S.conv(seg[:, c], ir[:, c]) for c in range(2)], 1)
    tail = wet[len(seg) - fade:]                 # the part of the reverb that rings on after the last sample
    # match the tail's first 100 ms to 70 % of the music's last 100 ms
    lvl_src = np.sqrt((src[n_src - S.n_of(0.1):n_src] ** 2).mean())
    lvl_tail = np.sqrt((tail[fade:fade + S.n_of(0.1)] ** 2).mean()) + 1e-9
    tail *= 0.7 * lvl_src / lvl_tail
    tail[:fade] *= np.sin(np.linspace(0, np.pi / 2, fade))[:, None] ** 2
    t0 = n_src - fade
    m = min(len(tail), N - t0)
    prog[t0:t0 + m] += tail[:m]

    mix = prog + bus
    # fade everything to silence by the end, then >= 60 ms of exact zeros
    t_end0, t_end1 = T['total'] - 1.10, T['total'] - 0.065
    tt = np.arange(N) / SR
    f = np.clip((tt - t_end0) / (t_end1 - t_end0), 0, 1)
    mix *= (np.cos(f * np.pi / 2) ** 2)[:, None]
    mix[tt >= t_end1] = 0

    # ---------------------------------------------------------------- loudness: static gain + transparent TP limiter
    tmp = os.path.join(os.path.dirname(os.path.abspath(A.out)), '_mix_meas.wav')
    i0, tp0 = loudness(FF, mix, tmp)
    out = mix
    for _ in range(3):
        i1, _tp = loudness(FF, out, tmp)
        out = out * 10 ** ((-14.0 - i1) / 20)
        # detector includes the -3 dB mono fold-down, ceiling -2.2 dBTP (AAC adds a few tenths)
        ms = 0.7071 * (out[:, 0] + out[:, 1])
        det = np.stack([out[:, 0], out[:, 1], ms], 1)
        g = limiter_gain(det, -2.3)
        out = out * g[:, None]
        out[tt >= t_end1] = 0
    i2, tp2 = loudness(FF, out, tmp)
    # the limiter pass leaves the mix a few hundredths under target: one last static trim if the peaks allow it
    trim = -14.0 - i2
    if abs(trim) > 0.01 and tp2 + trim <= -2.2:
        out = out * 10 ** (trim / 20)
        i2, tp2 = loudness(FF, out, tmp)
    os.remove(tmp)
    write_wav(A.out, out)
    zeros_ms = 1000 * (N - 1 - np.max(np.where(np.abs(out).max(1) > 0)[0])) / SR
    info = dict(samples=N, seconds=round(N / SR, 4), source_seconds=round(n_src / SR, 4),
                before=dict(I=i0, TP=tp0), after=dict(I=i2, TP=tp2), trailing_zeros_ms=round(zeros_ms, 1),
                accents=rep, duck_db=duck_db)
    if A.report:
        json.dump(info, open(A.report, 'w'), indent=1)
    print(f'mix: {N / SR:.3f} s, {i0:.2f} -> {i2:.2f} LUFS, TP {tp2:.2f} dBTP, trailing zeros {zeros_ms:.0f} ms, '
          f'{len(events)} accents')


if __name__ == '__main__':
    main()
