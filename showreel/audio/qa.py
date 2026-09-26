#!/usr/bin/env python3
"""Audio QA for the rendered soundtrack (numpy + Pillow). Run after `python3 audio/synth.py --stems`.

    python3 audio/qa.py [dist/soundtrack.wav] [--out .cache/audio-qa] [--zoom 11.2:13.3,...]
    python3 audio/qa.py --make-cues [.cache/storyboard-cues.json]     # provisional cues from storyboard.json

Prints: format/integrity (frames, NaN, DC, clean start/end, tail level), a per-bar level table, the kick grid
check (kick stem onsets vs the arrangement's kick hits, and the master cross-correlated against the kick stem),
a discontinuity (click) scan, spectral tilt, low-end balance (the 50 Hz third-octave over 1 kHz) and stereo
correlation, the picture-lock table (every storyboard moment the score has to hit, expected vs measured, from
the stems), and the level of each picture micro-sfx against the music bed at its moment. Writes overview.png
(waveform + beat grid, short-term loudness, log spectrogram), zoom-*.png (16th grid) around every section
change and lock.json (the lock table and micro-sfx levels).

--make-cues writes the storyboard's R.sfx / R.cue timeline in the exact shape tools/cues.mjs exports, so the
score can be rendered against the picture's declared sounds before the scenes exist:
    python3 audio/synth.py --cues .cache/storyboard-cues.json --stems && python3 audio/qa.py
"""
import argparse
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth  # noqa: E402

SR = synth.SR
BEAT = synth.BEAT
BAR = synth.BAR
STOPS = np.array([[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66], [245, 125, 21],
                  [250, 193, 39], [252, 255, 164]], float)


def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              os.path.join(synth.ROOT, 'fonts', 'JetBrainsMono-Regular.ttf')):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def colormap(v):
    x = np.clip(v, 0, 1) * (len(STOPS) - 1)
    i = np.minimum(x.astype(int), len(STOPS) - 2)
    f = (x - i)[..., None]
    return (STOPS[i] * (1 - f) + STOPS[i + 1] * f).astype(np.uint8)


def rms_db(x):
    return synth.todb(np.sqrt(np.mean(np.square(x)))) if x.size else -240.0


def spectrogram(mono, w, h, nfft, hop, rng_db=90.0):
    frames = np.lib.stride_tricks.sliding_window_view(np.pad(mono, (nfft // 2, nfft // 2)), nfft)[::hop]
    S = 20 * np.log10(np.abs(np.fft.rfft(frames * np.hanning(nfft), axis=1)) + 1e-9)
    S -= S.max()
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    fy = 30 * (20000 / 30) ** (1 - np.arange(h) / (h - 1))
    bins = np.clip(np.searchsorted(freqs, fy), 1, len(freqs) - 1)
    cols = np.linspace(0, S.shape[0] - 1, w).astype(int)
    return Image.fromarray(colormap((S[cols][:, bins].T + rng_db) / rng_db))


def overview(x, path, title):
    n = x.shape[1]
    dur = n / SR
    W, H = 2400, 1300
    img = Image.new('RGB', (W, H), (14, 16, 22))
    d = ImageDraw.Draw(img)
    f = font(18)
    x0, w = 60, W - 80

    def grid(y0, y1, label=False):
        for b in range(int(dur / BEAT) + 1):
            xx = x0 + int(b * BEAT / dur * w)
            bar = b % 4 == 0
            d.line([(xx, y0), (xx, y1)], fill=(90, 160, 255) if bar else (60, 70, 90), width=2 if bar else 1)
            if bar and label and b // 4 < synth.BARS:
                d.text((xx + 4, y0 + 2), 'bar %d' % (b // 4 + 1), fill=(150, 190, 255), font=f)
    wy0, wy1 = 40, 420
    mid = (wy0 + wy1) // 2
    for c, idx in enumerate(np.array_split(np.arange(n), w)):
        seg = x[:, idx[0]:idx[-1] + 1]
        r = np.sqrt(np.mean(seg ** 2))
        d.line([(x0 + c, mid - seg.max() * (wy1 - wy0) / 2), (x0 + c, mid - seg.min() * (wy1 - wy0) / 2)],
               fill=(70, 200, 170))
        d.line([(x0 + c, mid - r * (wy1 - wy0) / 2), (x0 + c, mid + r * (wy1 - wy0) / 2)], fill=(170, 255, 220))
    grid(wy0, wy1, True)
    d.text((x0, 10), 'waveform (min/max + rms), beat grid (bars blue)   ' + title, fill=(220, 220, 220), font=f)
    ly0, ly1 = 450, 650
    k = synth.iir(x, synth.K_WEIGHTING)
    c = np.concatenate([np.zeros((2, 1)), np.cumsum(k ** 2, axis=1)], axis=1)
    win, hop = int(0.4 * SR), int(0.05 * SR)
    pts = []
    for s in range(0, n - win + 1, hop):
        L = -0.691 + 10 * np.log10(((c[:, s + win] - c[:, s]) / win).sum() + 1e-12)
        pts.append((x0 + (s + win / 2) / n * w, ly1 - (np.clip(L, -40, 0) + 40) / 40 * (ly1 - ly0)))
    for v in (-30, -20, -14, -10):
        yy = ly1 - (v + 40) / 40 * (ly1 - ly0)
        d.line([(x0, yy), (x0 + w, yy)], fill=(60, 60, 60))
        d.text((5, yy - 9), '%d' % v, fill=(160, 160, 160), font=f)
    grid(ly0, ly1)
    d.line(pts, fill=(255, 200, 80), width=2)
    d.text((x0, ly0 - 22), 'short-term loudness (LUFS, 400 ms)', fill=(220, 220, 220), font=f)
    sy0, sy1 = 690, 1280
    img.paste(spectrogram(x.mean(axis=0), w, sy1 - sy0, 4096, 480), (x0, sy0))
    grid(sy0, sy1)
    for fr in (50, 100, 200, 500, 1000, 2000, 5000, 10000):
        yy = sy0 + (1 - np.log(fr / 30) / np.log(20000 / 30)) * (sy1 - sy0 - 1)
        d.line([(x0 - 8, yy), (x0, yy)], fill=(200, 200, 200))
        d.text((2, yy - 9), ('%dk' % (fr // 1000)) if fr >= 1000 else str(fr), fill=(200, 200, 200), font=f)
    d.text((x0, sy0 - 22), 'spectrogram (mid, log f 30 Hz - 20 kHz, 90 dB range)', fill=(220, 220, 220), font=f)
    img.save(path)


def zoom(x, t0, t1, path, name):
    W, H = 2400, 1000
    img = Image.new('RGB', (W, H), (14, 16, 22))
    d = ImageDraw.Draw(img)
    f = font(18)
    x0, w = 60, W - 80
    seg = x[:, int(t0 * SR):int(t1 * SR)]
    cols = np.array_split(np.arange(seg.shape[1]), w)
    for ch, (y0, y1, col) in enumerate(((40, 300, (70, 200, 170)), (320, 580, (200, 160, 90)))):
        mid = (y0 + y1) // 2
        for c, idx in enumerate(cols):
            v = seg[ch, idx[0]:idx[-1] + 1]
            d.line([(x0 + c, mid - v.max() * (y1 - y0) / 2), (x0 + c, mid - v.min() * (y1 - y0) / 2)], fill=col)
    s16 = BEAT / 4
    for k in range(int(np.ceil(t0 / s16 - 1e-9)), int(t1 / s16) + 1):
        xx = x0 + (k * s16 - t0) / (t1 - t0) * w
        c = (90, 160, 255) if k % 16 == 0 else (80, 90, 120) if k % 4 == 0 else (38, 42, 52)
        d.line([(xx, 40), (xx, H - 20)], fill=c, width=2 if k % 16 == 0 else 1)
        if k % 4 == 0:
            d.text((xx + 3, 22), '%d.%d' % (k // 16 + 1, (k % 16) // 4 + 1), fill=(160, 180, 220), font=f)
    img.paste(spectrogram(seg.mean(axis=0), w, H - 620, 2048, 96, 80.0), (x0, 600))
    d.text((x0, 2), '%s  %.3f-%.3f s  (L teal, R amber; 16th grid, labels bar.beat)' % (name, t0, t1),
           fill=(230, 230, 230), font=f)
    img.save(path)


def kick_check(stem_dir, master):
    """Kick stem onsets (first sound after >= 2 ms of digital silence: the stem is dry one-shots) against the
    arrangement's kick hits, then the master cross-correlated with the kick stem around every hit."""
    p = os.path.join(stem_dir, 'kick.wav')
    if not os.path.exists(p):
        print('kick grid   (no %s: run synth.py --stems)' % os.path.relpath(p))
        return
    k = synth.read_wav(p)[0]
    expected = np.array([h['t'] for h in synth.Song(synth.SONG).hits('kick')])
    a = np.abs(k).max(axis=0)
    loud = np.flatnonzero(a >= 1e-7)
    if not loud.size or not expected.size:
        print('kick grid   no kicks')
        return
    gaps = np.flatnonzero(np.diff(loud) > 96)
    ons = np.concatenate([[loud[0]], loud[gaps + 1]]) / SR
    dev = np.array([(t - expected[np.argmin(abs(expected - t))]) * 1000 for t in ons])
    grid_dev = np.array([(t - round(t / (BEAT / 4)) * BEAT / 4) * 1000 for t in ons])
    missing = [t for t in expected if not np.any(abs(ons - t) < 0.002)]
    print('kick grid   %d onsets / %d expected, max |onset - hit| %.3f ms, max |onset - 16th grid| %.3f ms%s' % (
        len(ons), len(expected), abs(dev).max(), abs(grid_dev).max(), ('  MISSING %s' % missing) if missing else ''))
    m, kk = master.mean(axis=0), k.mean(axis=0)
    lags = np.arange(-240, 241)
    worst = []
    for t in expected:
        c = int(round(t * SR))
        ref = kk[max(0, c - 480):c + 2400]
        lo = max(0, c - 480) - 240
        if lo < 0 or lo + 480 + ref.size > m.size:
            continue
        seg = m[lo:lo + 480 + ref.size]
        xc = np.array([np.dot(ref, seg[240 + L:240 + L + ref.size]) for L in lags])
        worst.append((abs(lags[int(np.argmax(xc))]) / SR * 1000, t))
    worst.sort(reverse=True)
    print('kick grid   master vs kick stem: max |lag| %.3f ms over %d hits%s' % (
        worst[0][0], len(worst), ''.join('  (%.3f s: %.2f ms)' % (t, v) for v, t in worst[:3] if v > 0.5)))


def click_scan(x):
    m = x.mean(axis=0)
    d2 = np.abs(np.diff(m, 2))
    w = 240
    c = np.concatenate([[0], np.cumsum(d2 ** 2)])
    loc = np.sqrt((c[w:] - c[:-w]) / w)
    loc = np.concatenate([np.full(w // 2, loc[0]), loc, np.full(len(d2) - len(loc) - w // 2, loc[-1])])
    idx = np.flatnonzero((d2 / (loc + 1e-7) > 9) & (d2 > 1e-3))
    groups = []
    for i in idx:
        if not groups or i - groups[-1] > 480:
            groups.append(i)
    print('clicks      %d discontinuity candidates%s' % (len(groups), (': ' + ' '.join('%.4f' % (g / SR) for g in groups[:20]))
                                                         if groups else ''))


def balance(x):
    def third_oct(seg):
        m = seg.mean(axis=0)
        S = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
        fr = np.fft.rfftfreq(len(m), 1 / SR)
        cs = 1000 * 2 ** (np.arange(-16, 14) / 3)
        return cs, np.array([10 * np.log10(S[(fr >= c / 2 ** (1 / 6)) & (fr < c * 2 ** (1 / 6))].sum() + 1e-20) for c in cs])
    hp = synth.filt(x, ('hp', 1000, 0.7))
    for b in range(synth.BARS):
        a0, a1 = int(b * BAR * SR), int((b + 1) * BAR * SR)
        seg = x[:, a0:a1]
        cs, L = third_oct(seg)
        sel = (cs >= 100) & (cs <= 10000)
        slope = np.polyfit(np.log2(cs[sel]), L[sel] - L[np.argmin(abs(cs - 1000))], 1)[0]
        mono = seg.mean(axis=0)
        i50, i1k = int(np.argmin(abs(cs - 50))), int(np.argmin(abs(cs - 1000)))
        print('bar %d       tilt %+.2f dB/oct (100 Hz-10 kHz)  50 Hz 1/3-oct %+5.1f dB over 1 kHz  L/R corr %.2f '
              '(>1 kHz %.2f)  mono downmix %+.2f LU' % (
                  b + 1, slope, L[i50] - L[i1k], np.corrcoef(seg[0], seg[1])[0, 1],
                  np.corrcoef(hp[0, a0:a1], hp[1, a0:a1])[0, 1], synth.lufs(np.stack([mono, mono])) - synth.lufs(seg)))


# ---- provisional cues from the storyboard ----------------------------------------------------------------
def make_cues(out, board=None):
    """storyboard.json -> {bpm, duration, fps, scenes, fx, sounds} as tools/cues.mjs would export it: scenes
    sorted by start (stable), every R.cue (parsed from its engine_call) sorted by t, every scene's R.sfx
    {t, type, ...opts} sorted by t."""
    board = board or os.path.join(synth.ROOT, 'storyboard.json')
    with open(board, 'r', encoding='utf-8') as fh:
        d = json.load(fh)

    def cue(call):
        m = re.search(r"R\.cue\(\s*([-0-9.e]+)\s*,\s*'(\w+)'\s*(?:,\s*(\{.*\}))?\s*\)", call)
        obj = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', m.group(3) or '{}')
        return dict({'t': float(m.group(1)), 'type': m.group(2)}, **json.loads(obj))
    g = d['grid']
    data = dict(bpm=g['bpm'], duration=g['duration'], fps=g['fps'],
                scenes=sorted((dict(id=sc['id'], start=sc['start'], end=sc['end']) for sc in d['scenes']),
                              key=lambda sc: sc['start']),
                fx=sorted((cue(c['engine_call']) for c in d['fx_cues']), key=lambda c: c['t']),
                sounds=sorted((dict({'t': e['t'], 'type': e['type']}, **(e.get('opts') or {}))
                               for sc in d['scenes'] for e in (sc.get('sfx') or [])), key=lambda e: e['t']))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(data, indent=2) + '\n')
    print('wrote %s: %d scenes, %d fx cues, %d sound events' % (
        os.path.relpath(out), len(data['scenes']), len(data['fx']), len(data['sounds'])))


# ---- picture-lock measurements (stems from synth.py --stems) ---------------------------------------------
def load_stems(d):
    st = {}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith('.wav'):
            st[f[:-4]] = synth.read_wav(os.path.join(d, f))[0]
    side = None
    if os.path.exists(os.path.join(d, 'render.json')):
        with open(os.path.join(d, 'render.json'), 'r', encoding='utf-8') as fh:
            side = json.load(fh)
    return st, side


def cut(x, t0, t1):
    return x[:, max(0, int(round(t0 * SR))):max(0, int(round(t1 * SR)))]


def lvl(x, t0, t1):
    """RMS in dBFS over [t0, t1)."""
    return rms_db(cut(x, t0, t1))


def pk(x, t0, t1):
    c = cut(x, t0, t1)
    return synth.todb(np.abs(c).max()) if c.size else -240.0


def short_max(x, t0, t1, win=0.01):
    """Loudest win-long RMS window inside [t0, t1) in dBFS."""
    p = np.mean(np.square(cut(x, t0, t1)), axis=0)
    w = int(win * SR)
    if p.size < w:
        return 10 * np.log10(p.mean() + 1e-24) if p.size else -240.0
    c = np.concatenate([[0.0], np.cumsum(p)])
    return float(10 * np.log10(((c[w:] - c[:-w]) / w).max() + 1e-24))


def onset(x, T, search=0.025, fwd=0.0015, bwd=0.02):
    """(time, rise dB) of the strongest energy rise near T: argmax of forward / backward window energy."""
    p = np.mean(np.square(x), axis=0)
    c = np.concatenate([[0.0], np.cumsum(p)])
    wf, wb = max(1, int(fwd * SR)), int(bwd * SR)
    lo, hi = max(wb, int((T - search) * SR)), min(p.size - wf, int((T + search) * SR))
    if hi <= lo:
        return float('nan'), 0.0
    i = np.arange(lo, hi)
    r = 10 * np.log10(((c[i + wf] - c[i]) / wf + 1e-14) / ((c[i] - c[i - wb]) / wb + 1e-14))
    k = int(np.argmax(r))
    return i[k] / SR, float(r[k])


def first_sound(x, thr=1e-4):
    a = np.flatnonzero(np.abs(x).max(axis=0) > thr)
    return a[0] / SR if a.size else float('nan')


def onsets_in(x, t0, t1, fwd=0.0015, bwd=0.010, min_rise=4.0, min_gap=0.045, floor_db=-70.0):
    """Onsets in [t0, t1): peaks (>= min_gap apart) of the forward / backward window energy ratio that rise
    by min_rise dB over a level above floor_db. 0.25 ms resolution; works on noisy decays (snare rolls)."""
    p = np.mean(np.square(x), axis=0)
    c = np.concatenate([[0.0], np.cumsum(p)])
    wf, wb, hop = int(fwd * SR), int(bwd * SR), max(1, int(0.00025 * SR))
    i = np.arange(max(0, int(round(t0 * SR))), min(p.size - wf, int(round(t1 * SR))), hop)
    if i.size == 0:
        return []
    ef = (c[i + wf] - c[i]) / wf
    eb = (c[i] - c[np.maximum(i - wb, 0)]) / wb
    r = 10 * np.log10((ef + 1e-14) / (eb + 1e-14))
    ok = (r > min_rise) & (10 * np.log10(ef + 1e-24) > floor_db)
    out = []
    for k in np.flatnonzero(ok):
        t = i[k] / SR
        if out and t - out[-1][0] < min_gap:
            if r[k] > out[-1][1]:
                out[-1] = (t, r[k])
            continue
        out.append((t, r[k]))
    return [round(float(t), 4) for t, _ in out]


def event_buf(ev, side, song=None):
    """One sound event from render.json rendered alone, exactly as the mixer places it (same renderer, seed,
    SFX_MIX gain and stems pregain). -> (stereo buffer, start time)."""
    kw = {k: v for k, v in ev.items() if k not in ('type', 'gain_db', 'ride_db', 'source', 'passes', 'anchor')}
    if ev['type'] == 'reverse':
        song = song or synth.Song(synth.SONG)
        kw['chord_notes'] = synth.voicing(song.chord_at(ev['t'] + ev['dur'] + 1e-6), 64.0)
    buf, off = synth.RENDERERS[ev['type']](**kw)
    buf = synth.stereo(buf) if buf.ndim == 1 else buf
    return buf * synth.undb(ev.get('gain_db', 0.0)) * side['pregain'], ev['t'] + off


def find_event(side, typ, t, source=None, tol=0.002):
    for ev in side['events']:
        if ev['type'] == typ and abs(ev['t'] - t) < tol and (source is None or ev['source'].startswith(source)):
            return ev
    return None


def peak_time(buf, t0, win=0.004):
    e = np.convolve(np.abs(buf).max(axis=0), np.ones(int(win * SR)) / int(win * SR), mode='same')
    return t0 + int(np.argmax(e)) / SR


NOTE_NAMES = ('C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B')


def chroma(x, t0, t1, fmin=90.0, fmax=2000.0):
    """Pitch-class energy profile of [t0, t1) -> the strongest pitch classes, strongest first."""
    m = cut(x, t0, t1).mean(axis=0)
    S = np.abs(np.fft.rfft(m * np.hanning(m.size), 1 << 17)) ** 2
    f = np.fft.rfftfreq(1 << 17, 1.0 / SR)
    sel = (f >= fmin) & (f <= fmax)
    pc = np.round(12 * np.log2(f[sel] / 440.0) + 69).astype(int) % 12
    prof = np.bincount(pc, weights=S[sel], minlength=12)
    return [NOTE_NAMES[k] for k in np.argsort(prof)[::-1] if prof[k] > 0.08 * prof.max()]


def logspec(m, t, win=0.02, fmin=150.0, fmax=5000.0, bpo=96):
    a = int(t * SR)
    n = int(win * SR)
    S = np.abs(np.fft.rfft(m[a:a + n] * np.hanning(n), 1 << 16))
    f = np.fft.rfftfreq(1 << 16, 1.0 / SR)
    grid = fmin * 2 ** (np.arange(int(np.log2(fmax / fmin) * bpo)) / bpo)
    v = np.log(np.interp(grid, f, S) + 1e-9)
    return v - v.mean()


def shift_st(m, t0, t1, rng_st=9):
    """Pitch shift in semitones between the spectra at t0 and t1 (log-frequency cross-correlation)."""
    a, b = logspec(m, t0), logspec(m, t1)
    lags = np.arange(-rng_st * 8, rng_st * 8 + 1)
    xc = [np.dot(a[max(0, -L):a.size - max(0, L)], b[max(0, L):b.size - max(0, -L)]) for L in lags]
    return lags[int(np.argmax(xc))] / 8.0


def new_note(x, t, win=0.04, fmin=150.0, fmax=5000.0):
    """Name of the note that starts at t: the strongest positive spectral change (after vs before t)."""
    a, b = cut(x, t, t + win).mean(axis=0), cut(x, t - win, t).mean(axis=0)
    if b.size < a.size:
        b = np.pad(b, (a.size - b.size, 0))
    w = np.hanning(a.size)
    S1, S0 = np.abs(np.fft.rfft(a * w, 1 << 16)), np.abs(np.fft.rfft(b * w, 1 << 16))
    f = np.fft.rfftfreq(1 << 16, 1.0 / SR)
    sel = (f >= fmin) & (f <= fmax)
    f0 = f[sel][int(np.argmax(np.maximum(S1 - S0, 0.0)[sel]))]
    m = int(round(12 * np.log2(f0 / 440.0) + 69))
    return '%s%d' % (NOTE_NAMES[m % 12], m // 12 - 1)


def centroid(x, t0, t1):
    m = cut(x, t0, t1).mean(axis=0)
    S = np.abs(np.fft.rfft(m * np.hanning(m.size)))
    f = np.fft.rfftfreq(m.size, 1.0 / SR)
    return float((S * f).sum() / (S.sum() + 1e-12))


def lufs_s(x, t0, t1):
    c = cut(x, t0, t1)
    return synth.lufs(c) if c.shape[1] >= int(0.4 * SR) else float('nan')


def lock_report(stems_dir, out_json=None):
    """The storyboard's picture-lock moments for the score: expected vs measured, from the stems."""
    st, side = load_stems(stems_dir)
    need = ('master', 'music', 'sfx', 'swell', 'drums', 'kick')
    if not all(k in st for k in need):
        print('lock        (stems missing: run synth.py --stems)')
        return None
    M, mus, sfx, sw, dr, kk = (st[k] for k in need)
    part = {k[5:]: v for k, v in st.items() if k.startswith('part-')}
    zero = np.zeros_like(M)
    P = lambda name: part.get(name, zero)  # noqa: E731
    rows = []

    def row(t, what, expected, measured, ok):
        rows.append(dict(t=t, what=what, expected=expected, measured=measured, ok=bool(ok)))

    # bar 1: one hit per word
    t = first_sound(M)
    row(0.0, 'LIGHT impact: first sound', 'onset 0.000 s', 'onset %.4f s, peak %.1f dBFS in 100 ms' % (t, pk(M, 0, 0.1)),
        abs(t) < 0.002)
    for T, what in ((0.46875, 'HEAVY slam'), (0.9375, 'NARROW squeeze stab'), (1.40625, 'WIDE supersaw stab')):
        to, r = onset(mus, T)
        tm, rm = onset(M, T)
        row(T, what + ': onset', 'music + master onset at %.5f' % T,
            'music %.4f (+%.1f dB rise), master %.4f (+%.1f dB)' % (to, r, tm, rm),
            abs(to - T) < 0.003 and abs(tm - T) < 0.003 and r > 6)
    pon = onsets_in(P('pluck'), 0.0, 0.47)
    names = [new_note(P('pluck'), t) for t in pon]
    pl = cut(P('pluck'), 0.0, 0.8).mean(axis=0)
    Sp = np.abs(np.fft.rfft(pl)) ** 2
    fp = np.fft.rfftfreq(pl.size, 1.0 / SR)
    lowp = 10 * np.log10(Sp[fp < 300].sum() / Sp.sum())
    row(0.0, 'LIGHT bed: glassy 16th plucks F5 Ab5 C6 F6, high-passed', 'onsets 0/.117/.234/.352; F5 Ab5 C6 F6',
        'onsets %s; %s; energy < 300 Hz %.0f dB' % (pon, ' '.join(names), lowp),
        len(pon) == 4 and names == ['F5', 'Ab5', 'C6', 'F6'] and lowp < -30)
    bm = cut(P('boom'), 0.47, 0.75).mean(axis=0)
    Sb = np.abs(np.fft.rfft(bm * np.hanning(bm.size), 1 << 17))
    fb = np.fft.rfftfreq(1 << 17, 1.0 / SR)
    h1 = Sb[(fb > 38) & (fb < 50)].max()
    h3 = Sb[(fb > 120) & (fb < 145)].max()
    row(0.46875, 'SLAM: distorted sub', 'F1 with strong odd harmonics', 'F1 + 3rd harmonic at %+.1f dB' % synth.todb(h3 / h1),
        synth.todb(h3 / h1) > -20)
    ms = P('stab').mean(axis=0)
    b = shift_st(ms, 0.9375, 1.0475)
    row(0.9375, 'NARROW: bend of the band-passed saw chord', '-5 st over 0.1 s (-4.0 between windows at +10 ms / +120 ms)',
        '%+.2f st' % b, -5.5 < b < -3.0)
    sw_saw = cut(P('saw'), 1.40625, 1.75)
    sm = rms_db(sw_saw[0] - sw_saw[1]) - rms_db(sw_saw[0] + sw_saw[1]) if sw_saw.size else -240
    row(1.40625, 'WIDE: stereo width of the supersaw', 'wide (side/mid > -10 dB)', 'side/mid %.1f dB' % sm, sm > -10)
    kon = onsets_in(kk, 0.0, 2.5)
    before = [round(v, 4) for v in kon if v < 1.87]
    row(1.875, 'GROOVE IN: kicks before 1.875 / first groove kick', '[0.0, 0.46875] then 1.875',
        '%s then %s' % (before, next((round(v, 4) for v in kon if v >= 1.87), None)),
        len(before) == 2 and abs(before[0]) < 0.002 and abs(before[1] - 0.46875) < 0.002
        and any(abs(v - 1.875) < 0.002 for v in kon))
    cl = [round(v, 4) for v in onsets_in(P('clap'), 1.8, 3.75)]
    row(2.34375, 'claps on the landing and on "notices the camera"', '[2.34375, 3.28125]', str(cl),
        len(cl) == 2 and abs(cl[0] - 2.34375) < 0.002 and abs(cl[1] - 3.28125) < 0.002)
    song = synth.Song(synth.SONG)
    ev = find_event(side, 'reverse', 3.515625) if side else None
    tp = peak_time(*event_buf(ev, side, song)) if ev else float('nan')
    row(3.75, 'dive: reverse swell 3.515625 -> 3.75', 'swell peaks at 3.75', '%s swell peaks at %.4f s' % (
        ev['source'] if ev else 'no', tp), abs(tp - 3.75) < 0.01)
    low = synth.filt(M, ('lp', 120, 0.7))
    to, r = onset(low, 3.75, fwd=0.004)
    row(3.75, 'sub boom (box unfolds)', 'low-band (<120 Hz) onset 3.75', '%.4f s (+%.1f dB)' % (to, r), abs(to - 3.75) < 0.005)
    c0, c1 = chroma(P('pad'), 4.25, 4.65), chroma(P('pad'), 4.75, 5.15)
    row(4.6875, 'pad Abmaj7 -> Eb at 4.6875', 'Ab C Eb G -> Eb G Bb', '%s -> %s' % (' '.join(c0[:4]), ' '.join(c1[:4])),
        set(c0[:4]) == {'Ab', 'C', 'Eb', 'G'} and set(c1[:3]) == {'Eb', 'G', 'Bb'})
    pa = chroma(P('arp'), 3.75, 5.625)
    row(3.75, 'arp: 16ths of F minor pentatonic', 'F Ab Bb C Eb only', ' '.join(pa[:6]),
        set(pa[:5]) == {'F', 'Ab', 'Bb', 'C', 'Eb'} and len(onsets_in(P('arp'), 3.74, 5.62, min_gap=0.08)) == 16)
    c0, c1 = centroid(P('arp'), 3.75, 4.2), centroid(P('arp'), 5.15, 5.6)
    row(3.75, 'arp opens its filter across bar 3', 'brighter at the end', 'centroid %.0f Hz -> %.0f Hz' % (c0, c1), c1 > 1.3 * c0)
    nk = dr - P('kick')
    d3, d4 = lvl(nk, 4.6875, 5.15625), lvl(nk, 5.15625, 5.625)
    o3 = sum(len(onsets_in(P(q), 4.6875, 5.15)) for q in ('clap', 'hat', 'shaker', 'tom', 'rim'))
    o4 = sum(len(onsets_in(P(q), 5.15625, 5.62)) for q in ('clap', 'hat', 'shaker', 'tom', 'rim'))
    row(5.15625, 'drums THIN (kick + rim + soft hat)', 'fewer, quieter hits in beat 4',
        'non-kick drums %.1f -> %.1f dBFS, %d -> %d hits' % (d3, d4, o3, o4), d4 < d3 - 3 and o4 < o3)
    sn = [round(v, 4) for v in onsets_in(P('snare'), 6.4, 7.1)]
    row(6.5625, 'snare roll: 8ths then 16ths from 6.796875', '[6.5625, 6.7969, 6.9141, 7.0312]', str(sn),
        len(sn) == 4 and abs(sn[0] - 6.5625) < 0.002 and abs(sn[1] - 6.796875) < 0.002)
    cA, cB = centroid(mus, 7.035, 7.09), centroid(mus, 7.13, 7.2)
    row(7.03125, 'TAPE-STOP of the music bus over 0.18 s', 'pitch dives (spectral centroid falls)',
        'centroid %.0f Hz -> %.0f Hz, music %.1f dBFS during the stop' % (cA, cB, lvl(mus, 7.03125, 7.21125)), cB < 0.7 * cA)
    q = short_max(mus, 7.215, 7.496)
    row(7.21, 'breath: music bus after the stop', '< -40 dBFS until 7.5', 'max 10 ms RMS %.1f dBFS (7.215-7.496)' % q, q < -40)
    nb = short_max(sfx - sw, 7.30, 7.496)
    row(7.3, 'breath: everything but the swells', 'near-silence', 'max 10 ms RMS %.1f dBFS' % nb, nb < -45)
    swp = [lvl(sw, a, a + 0.02) for a in (7.1, 7.3, 7.45, 7.475)]
    row(7.5, 'swells (reverse + reverse cymbal + sub inhale) land on 7.5', 'rising into 7.5',
        ' -> '.join('%.1f' % v for v in swp) + ' dBFS', swp[-1] > swp[0] + 10)
    inh = synth.filt(sw, ('lp', 90, 0.7))
    row(7.5, 'sub inhale 30 -> 55 Hz', 'low band rising into 7.5',
        '%.1f -> %.1f dBFS (<90 Hz, 7.10 / 7.46)' % (lvl(inh, 7.10, 7.14), lvl(inh, 7.44, 7.48)),
        lvl(inh, 7.44, 7.48) > lvl(inh, 7.10, 7.14) + 6)
    to, r = onset(M, 7.5)
    km = synth.iir(M, synth.K_WEIGHTING)
    a, bb = lvl(km, 7.2656, 7.5), lvl(km, 7.5, 7.96875)
    row(7.5, 'THE DROP', 'onset 7.5; drop >= 8 dB over the breath', 'onset %.4f (+%.1f dB); K-weighted RMS breath %.1f -> '
        'drop beat %.1f dBFS' % (to, r, a, bb), abs(to - 7.5) < 0.003 and bb - a >= 8)

    def layers(t0, t1):
        return sorted(q for q, v in part.items() if lvl(v, t0, t1) > -45)
    la, lb = layers(6.5625, 7.03125), layers(7.5, 7.96875)
    oa = sum(len(onsets_in(P(q), 6.5625, 7.03)) for q in synth.DRUM_PARTS)
    ob = sum(len(onsets_in(P(q), 7.5, 7.96)) for q in synth.DRUM_PARTS)
    row(7.5, 'drop density: layers sounding, last beat before the breath -> first beat of the drop',
        'many more layers', '%d (%s) -> %d (%s); drum hits %d -> %d' % (len(la), ' '.join(la), len(lb), ' '.join(lb), oa, ob),
        len(lb) >= len(la) + 3)
    ko, co = onsets_in(P('kick'), 7.45, 7.55), onsets_in(P('crash'), 7.45, 7.55)
    row(7.5, 'drop keeps its musical kick + crash under the picture impact', 'kick and crash at 7.5',
        'kick %s, crash %s' % (ko, co), bool(ko) and bool(co) and abs(ko[0] - 7.5) < 0.002 and abs(co[0] - 7.5) < 0.002)
    to, r = onset(M, 7.96875)
    row(7.96875, 'secondary impact', 'onset 7.96875', '%.4f (+%.1f dB)' % (to, r), abs(to - 7.96875) < 0.003)
    to = onsets_in(P('stab'), 8.3, 8.6)
    row(8.4375, 'reverse zip into the bright stab', 'stab at 8.4375', 'stab onset %s, stab centroid %.0f Hz' % (
        [round(v, 4) for v in to], centroid(P('stab'), 8.44, 8.55)), bool(to) and abs(to[0] - 8.4375) < 0.002)
    ev = find_event(side, 'whoosh', 9.140625) if side else None
    if ev:
        w, t0w = event_buf(ev, side)
        k = int((ev['anchor'] - t0w) * SR)
        a0, a1 = w[:, k // 3:2 * k // 3], w[:, 2 * k // 3:k]
        lr0, lr1 = rms_db(a0[0]) - rms_db(a0[1]), rms_db(a1[0]) - rms_db(a1[1])
        pt = peak_time(w, t0w)
    else:
        lr0 = lr1 = pt = float('nan')
    row(9.140625, 'whip whoosh R -> L into 9.375', 'right first, left at the end, peak 9.375',
        'L-R %+.1f dB -> %+.1f dB, peak %.4f s' % (lr0, lr1, pt), lr0 < -1 and lr1 > 1 and abs(pt - 9.375) < 0.03)
    sn = [round(v, 4) for v in onsets_in(P('snare'), 10.9, 11.25)]
    row(11.015625, 'snare fill in 16ths', '[11.0156, 11.1328]', str(sn), len(sn) == 2 and abs(sn[0] - 11.015625) < 0.002)
    mm = cut(mus - kk, 11.25, 11.484375).mean(axis=0)          # the edits work on the mix minus the kick
    L32 = int(round(synth.S16 / 2 * SR))
    rr = float(np.dot(mm[:-L32], mm[L32:]) / (np.sqrt(np.dot(mm[:-L32], mm[:-L32]) * np.dot(mm[L32:], mm[L32:])) + 1e-12))
    kd = onsets_in(kk, 11.2, 11.3)
    row(11.25, 'glitch stutter: previous 8th re-triggered in 32nds', 'repeats every 32nd; downbeat kick kept',
        'autocorr @32nd %.2f (mix minus kick); kick %s' % (rr, kd), rr > 0.5 and bool(kd) and abs(kd[0] - 11.25) < 0.002)
    s1 = [round(v, 4) for v in onsets_in(P('stab'), 11.4, 11.6)]
    s2 = [round(v, 4) for v in onsets_in(P('snare'), 11.4, 11.6)]
    row(11.484375, 'stab + snare', 'both at 11.484375', 'stab %s, snare %s' % (s1, s2),
        bool(s1) and bool(s2) and abs(s1[0] - 11.484375) < 0.002 and abs(s2[0] - 11.484375) < 0.002)
    ma = P('arp').mean(axis=0)
    i1, i2 = shift_st(ma, 11.72, 11.837), shift_st(ma, 11.72, 11.954)
    row(11.71875, 'row stutters rising F -> Ab -> C', '+3 st, +7 st', '%+.1f st, %+.1f st' % (i1, i2),
        abs(i1 - 3) < 0.6 and abs(i2 - 7) < 0.6)
    a, bb = cut(mus, 11.71875, 11.8359375).mean(axis=0), cut(mus, 12.0703125, 12.1875).mean(axis=0)
    fa, fb = np.abs(np.fft.rfft(a)), np.abs(np.fft.rfft(bb))
    sim = float(np.corrcoef(np.log(fa + 1e-6), np.log(fb + 1e-6))[0, 1])
    row(12.0703125, 'buffer repeat of 11.71875', 'same material', 'spectral correlation %.2f' % sim, sim > 0.6)
    s1 = [round(v, 4) for v in onsets_in(P('saw'), 12.1, 12.3)]
    s2 = [round(v, 4) for v in onsets_in(P('clap'), 12.1, 12.3)]
    row(12.1875, 'big Fm(add9) stab + clap', 'both at 12.1875', 'saw %s, clap %s' % (s1, s2),
        bool(s1) and bool(s2) and abs(s1[0] - 12.1875) < 0.002 and abs(s2[0] - 12.1875) < 0.002)
    kick_after = pk(P('kick'), 12.66, 13.12)
    hat_after = max(pk(P('hat'), 12.66, 13.12), pk(P('ohat'), 12.66, 13.12))
    sr = onsets_in(P('snare'), 12.6, 13.1)
    row(12.65625, 'drums OUT, 32nd snare roll', 'no kick / hats; roll of 32nds to 12.949',
        'kick %.0f dBFS, hats %.0f dBFS, %d snare hits %.4f..%.4f' % (
            kick_after, hat_after, len(sr), sr[0] if sr else 0, sr[-1] if sr else 0),
        kick_after < -80 and hat_after < -80 and len(sr) == 6 and abs(sr[-1] - 12.94921875) < 0.002)
    g0, g1 = 13.0078125, 13.125
    gm = pk(mus, g0, g1)
    gs = pk(sfx - sw, g0, g1)
    row(g0, 'THE GAP: music bus', '< -50 dBFS', 'peak %.1f dBFS' % gm, gm < -50)
    row(g0, 'THE GAP: sfx bus minus the swell', '< -50 dBFS', 'peak %.1f dBFS' % gs, gs < -50)
    mg, sg = cut(M, g0 + 0.001, g1 - 0.001), cut(sw, g0 + 0.001, g1 - 0.001)
    cc = float(np.corrcoef(mg.mean(axis=0), sg.mean(axis=0))[0, 1])
    row(g0, 'THE GAP: master = only the swell', 'master follows the swell stem',
        'master %.1f dBFS vs swell stem %.1f dBFS, correlation %.3f' % (rms_db(mg), rms_db(sg), cc), cc > 0.98)
    et = np.arange(12.9, 13.13, 0.002)
    swl = [lvl(sw, a, a + 0.004) for a in et]
    tp = et[int(np.argmax(swl))] + 0.002
    row(g1, 'final swell peaks into the hit', 'peak at 13.125', 'swell peak %.4f s' % tp, abs(tp - 13.125) < 0.01)
    to, r = onset(M, 13.125)
    row(13.125, 'FINAL HIT', 'onset 13.125', 'onset %.4f (+%.1f dB), peak %.1f dBFS' % (to, r, pk(M, 13.125, 13.3)),
        abs(to - 13.125) < 0.003)
    ko, co = onsets_in(P('kick'), 13.1, 13.15), onsets_in(P('crash'), 13.1, 13.15)
    sc = chroma(P('saw'), 13.13, 13.6)
    sw_s = cut(P('saw'), 13.13, 13.6)
    sm = rms_db(sw_s[0] - sw_s[1]) - rms_db(sw_s[0] + sw_s[1])
    row(13.125, 'final hit: kick + crash + wide Fm(add9) stab', 'kick, crash at 13.125; F Ab C G; wide',
        'kick %s, crash %s; stab %s; side/mid %.1f dB' % (ko, co, ' '.join(sc[:4]), sm),
        bool(ko) and bool(co) and set(sc[:4]) == {'F', 'Ab', 'C', 'G'} and sm > -10)
    low = synth.filt(M, ('lp', 70, 0.7), ('lp', 70, 0.7))
    l0, l15 = lvl(low, 13.175, 13.225), lvl(low, 14.625, 14.675)
    mm = cut(M, 13.3, 14.2).mean(axis=0)
    Sm = np.abs(np.fft.rfft(mm * np.hanning(mm.size), 1 << 18))
    fm = np.fft.rfftfreq(1 << 18, 1.0 / SR)
    sel = (fm > 20) & (fm < 100)
    row(13.125, 'final hit: ~40 Hz sub boom, ~1.5 s decay', 'boom near 40 Hz, gone (>30 dB down) by +1.5 s',
        '%.1f Hz; <70 Hz %.1f dBFS at +0.05 s -> %.1f dBFS at +1.5 s' % (fm[sel][np.argmax(Sm[sel])], l0, l15),
        35 < fm[sel][np.argmax(Sm[sel])] < 50 and l0 - l15 > 30)
    hl = [lvl(st['ret-hall'], a, a + 0.1) for a in (13.3, 14.0, 14.7)] if 'ret-hall' in st else [float('nan')] * 3
    row(13.125, 'final stab into a long hall', 'hall tail rings through bar 8', 'hall return %s dBFS at 13.3 / 14.0 / 14.7 s' % (
        ' / '.join('%.1f' % v for v in hl)), hl[1] > -45 and hl[0] > hl[1] > hl[2])
    after = sorted((round(v, 3), q) for q in synth.DRUM_PARTS for v in onsets_in(P(q), 13.15, 15.0))
    row(13.15, 'no drums after the final hit', 'no drum onsets after 13.125', str(after[:6]) if after else 'none', not after)
    hitpk = pk(M, 13.125, 13.4)
    tail = lvl(M, 14.96, 14.98)
    tail_pre = lvl(M, 14.84, 14.86)
    row(14.98, 'tail', '<= -40 dB by 14.98', 'RMS %.1f dBFS at 14.96-14.98 (%.1f dB under the hit; %.1f dBFS at 14.85 '
        'before the end fade)' % (tail, hitpk - tail, tail_pre), tail < -40 and hitpk - tail > 40)
    row(15.0, 'file ends in digital silence', 'last sample 0', 'last sample %s, last 10 ms peak %.1f dBFS' % (
        M[:, -1].tolist(), pk(M, 14.99, 15.0)), not M[:, -1].any())
    print('picture lock (expected vs measured, stems in %s)' % os.path.relpath(stems_dir))
    for rw in rows:
        print('  %s %9.5f  %-52s | %-40s | %s' % ('ok ' if rw['ok'] else 'NO ', rw['t'], rw['what'][:52],
                                                  rw['expected'][:40], rw['measured']))
    print('lock        %d / %d moments ok' % (sum(rw['ok'] for rw in rows), len(rows)))
    return dict(rows=rows, side=side)


def micro_levels(stems_dir, types=('click', 'tick', 'pop', 'blip', 'type', 'zap')):
    """Each picture micro-sfx rendered alone (same renderer, seed and gain as the mix) against the music bed
    over the same window (the event's own length, where it is within 30 dB of its peak). K-weighted RMS."""
    st, side = load_stems(stems_dir)
    if not side or 'music' not in st:
        print('micro sfx   (no render.json: run synth.py --stems)')
        return None
    mus = st['music']
    kw_m = synth.iir(mus, synth.K_WEIGHTING)
    out = []
    for ev in side['events']:
        if ev['type'] not in types:
            continue
        buf, t_ev = event_buf(ev, side)
        off = t_ev - ev['t']
        e = np.abs(buf).max(axis=0)
        k = int(0.005 * SR)
        env = np.convolve(e, np.ones(k) / k, mode='same')
        live = np.flatnonzero(env > env.max() * 10 ** (-30 / 20))
        L = int(np.clip((live[-1] + 1) if live.size else k, 0.02 * SR, 0.4 * SR))
        s0 = int(round((ev['t'] + off) * SR))
        kb = synth.iir(buf[:, :L], synth.K_WEIGHTING)
        ev_db = rms_db(kb)
        bed = rms_db(kw_m[:, s0:s0 + L])
        out.append(dict(t=ev['t'], type=ev['type'], pitch=ev.get('pitch'), source=ev['source'], dur=L / SR,
                        event_db=ev_db, bed_db=bed, diff=ev_db - bed, ride_db=ev.get('ride_db', 0.0)))
    if not out:
        print('micro sfx   none')
        return out
    print('micro sfx   level vs the music bed at its moment (K-weighted RMS over the event, target -6..-10 dB)')
    bedded = [o for o in out if o['bed_db'] > -40.0]
    for ty in types:
        ds = [o['diff'] for o in bedded if o['type'] == ty]
        if ds:
            print('  %-6s n=%2d  median %+5.1f dB  range %+5.1f .. %+5.1f dB' % (
                ty, len(ds), float(np.median(ds)), min(ds), max(ds)))
    ds = [o['diff'] for o in bedded]
    print('  all     n=%2d  median %+5.1f dB  within -10..-6: %d, within -12..-4: %d' % (
        len(ds), float(np.median(ds)), sum(1 for d in ds if -10.05 <= d <= -5.95), sum(1 for d in ds if -12 <= d <= -4)))
    for o in out:
        if o['bed_db'] <= -40.0:
            print('  solo    %.4f %s over a %.0f dBFS bed (the music has decayed): %.1f dBFS' % (
                o['t'], o['type'], o['bed_db'], o['event_db']))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('wav', nargs='?', default=os.path.join(synth.ROOT, 'dist', 'soundtrack.wav'))
    ap.add_argument('--out', default=os.path.join(synth.ROOT, '.cache', 'audio-qa'))
    ap.add_argument('--stems', default=os.path.join(synth.ROOT, '.cache', 'stems'))
    ap.add_argument('--zoom', default='', help='extra zoom windows, e.g. 6.4:8.4,11.2:13.3')
    ap.add_argument('--make-cues', nargs='?', const=os.path.join(synth.ROOT, '.cache', 'storyboard-cues.json'),
                    default=None, metavar='OUT', help='write provisional cues from storyboard.json and exit')
    a = ap.parse_args(argv)
    if a.make_cues:
        make_cues(a.make_cues)
        return
    os.makedirs(a.out, exist_ok=True)
    x, sr = synth.read_wav(a.wav)
    n = x.shape[1]
    print('file        %s: %d frames @ %d Hz x %d ch = %.6f s (expected %d)%s' % (
        os.path.relpath(a.wav), n, sr, x.shape[0], n / sr, synth.N_FRAMES, '' if n == synth.N_FRAMES else '  WRONG LENGTH'))
    print('integrity   finite %s  peak %.2f dBFS  true peak %.2f dBTP  DC %.1e / %.1e' % (
        np.isfinite(x).all(), synth.todb(np.abs(x).max()), synth.todb(synth.true_peak(x)), x[0].mean(), x[1].mean()))
    print('edges       first sample %s  last sample %s  last 10 ms peak %.1f dBFS  last 200 ms rms %.1f dBFS' % (
        x[:, 0].tolist(), x[:, -1].tolist(), synth.todb(np.abs(x[:, -480:]).max()), rms_db(x[:, -9600:])))
    print('loudness    %.2f LUFS integrated (BS.1770)' % synth.lufs(x))
    for b in range(synth.BARS):
        seg = x[:, int(b * BAR * SR):int((b + 1) * BAR * SR)]
        sec = synth.SONG[b].get('section', '') if b < len(synth.SONG) else ''
        print('bar %d %-8s rms %6.1f dBFS  peak %6.1f dBFS  loudness %6.1f LUFS  side/mid %6.1f dB' % (
            b + 1, sec, rms_db(seg), synth.todb(np.abs(seg).max()), synth.lufs(seg),
            rms_db(seg[0] - seg[1]) - rms_db(seg[0] + seg[1])))
    kick_check(a.stems, x)
    click_scan(x)
    balance(x)
    lock = lock_report(a.stems)
    micro = micro_levels(a.stems)
    with open(os.path.join(a.out, 'lock.json'), 'w', encoding='utf-8') as fh:
        json.dump(dict(lock=lock and lock['rows'], micro=micro), fh, indent=1)
    overview(x, os.path.join(a.out, 'overview.png'), os.path.basename(a.wav))
    wins = []
    prev = None
    for b, bd in enumerate(synth.SONG):
        if bd.get('section') != prev and b:
            wins.append((max(0.0, b * BAR - 1.0), min(n / SR, b * BAR + 1.0), 'bar%d-%s' % (b + 1, bd.get('section', ''))))
        prev = bd.get('section')
    wins.append((max(0.0, n / SR - 2.1), n / SR, 'ending'))
    for spec in filter(None, a.zoom.split(',')):
        t0, t1 = (float(v) for v in spec.split(':'))
        wins.append((t0, t1, '%.2f-%.2f' % (t0, t1)))
    for t0, t1, name in wins:
        zoom(x, t0, t1, os.path.join(a.out, 'zoom-%s.png' % name), name)
    print('images      %s (overview.png + %d zooms)' % (os.path.relpath(a.out), len(wins)))


if __name__ == '__main__':
    main()
