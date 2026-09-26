#!/usr/bin/env python3
"""Audio QA for the rendered soundtrack (numpy + Pillow). Run after `python3 audio/synth.py --stems`.

    python3 audio/qa.py [dist/soundtrack.wav] [--out .cache/audio-qa] [--zoom 11.2:13.3,...]

Prints: format/integrity (frames, NaN, DC, clean start/end, tail level), a per-bar level table, the kick grid
check (kick stem onsets vs the arrangement's kick hits, and the master cross-correlated against the kick stem),
a discontinuity (click) scan, spectral tilt and stereo correlation. Writes overview.png (waveform + beat grid,
short-term loudness, log spectrogram) and zoom-*.png (16th grid) around every section change.
"""
import argparse
import os
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
        print('bar %d       tilt %+.2f dB/oct (100 Hz-10 kHz)  L/R corr %.2f (>1 kHz %.2f)  mono downmix %+.2f LU' % (
            b + 1, slope, np.corrcoef(seg[0], seg[1])[0, 1], np.corrcoef(hp[0, a0:a1], hp[1, a0:a1])[0, 1],
            synth.lufs(np.stack([mono, mono])) - synth.lufs(seg)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('wav', nargs='?', default=os.path.join(synth.ROOT, 'dist', 'soundtrack.wav'))
    ap.add_argument('--out', default=os.path.join(synth.ROOT, '.cache', 'audio-qa'))
    ap.add_argument('--stems', default=os.path.join(synth.ROOT, '.cache', 'stems'))
    ap.add_argument('--zoom', default='', help='extra zoom windows, e.g. 6.4:8.4,11.2:13.3')
    a = ap.parse_args(argv)
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
