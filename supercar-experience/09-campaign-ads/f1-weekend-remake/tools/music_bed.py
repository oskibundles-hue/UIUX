"""Fit 'ROAR' (type beat, raw/music/roar.mp3) to the ad's cut as the music bed.

The track is 141.0 BPM (beat 0.42554 s, first beat 0.0679 s, sections of 64 beats with a short dropout
before each; it hard-stops on beat 352). The kicks start 42 ms before that grid, so edits use the kick. The ad keeps its own clock; the track is placed so its bars
land on the ad's big moments, with two edits, both on bar lines so the groove never skips:

  ad  0.0 - 63.5  track from 25.00 s, so the beat-64 section drop lands on the title -> open cut (2.3 s),
                  right after the track's own dropout
  ad 64.5 - end   track from beat 324 (137.94 s): the full beat slams back on the relief cut and runs
                  to the track's own hard stop just before the end card ends

Automation (ad seconds):
  0.0 - 2.3   low-pass opening, 300 Hz -> 1 kHz, then the full beat on the cut
  8.0 - 12.7  pull back: gentle 1.2 kHz low-pass, -2 dB
  60.0 - 64.4 tension: low-pass sweep 900 -> 250 Hz, -4 -> -10 dB; the SFX engine adds the riser
              (it peaks on the 63.5 s speed cut), then 0.1 s of air before the drop at 64.5

Writes public/audio/music_roar.wav (48 kHz float, matched to the synth bed's loudness, -9.7 LUFS) for
sfx/events.json. The original synth bed (npm run audio -> public/audio/music.wav) is untouched.

--cut 30 fits the same track to the 30 s cut (src/cut30.json) and writes music_roar30.wav:
  ad  0.0 - 17.7  same first part (beat 64 on the title -> open cut at 2.3 s)
  ad 17.8 - end   beat 324, so the drop lands on the GT3 RS's engine start in shot 30 (its frame 36)
  automation: low-pass opening, a gentle pull back under the text bubble (shot 4, 3.17 - 5.70),
  tension 16.6 - 17.7 (900 -> 250 Hz, -4 -> -10 dB), 0.1 s of air, drop at 17.8; the track's own stop at 29.72.

  uv run --no-project --with numpy --with scipy --with soundfile python tools/music_bed.py [--cut 30]
"""
import argparse, os, re, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt

SR = 48000
DUR = 2295 / 30                  # ad length, s (76 s cut; --cut 30 changes these in main)
T0, BEAT = 0.0679, 0.42554       # track beat grid (measured, median residual 6 ms)
LEAD = 0.042                     # kicks start this much before the grid (41.5-43.7 ms on four section drops)
OFF_A = T0 - LEAD + 64 * BEAT - 2.3     # track = ad + OFF_A for the first part
OFF_B = T0 - LEAD + 324 * BEAT - 64.5   # track = ad + OFF_B after the relief cut
CUT_A, GAP_END = 64.4, 64.5      # first part ends, relief drop
TARGET_LUFS = -9.7               # same as the synth bed, so the engine's balance carries over
CUTOFFS = [250, 400, 650, 900, 1200, 2000, 3500, 6000]

here = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(here, '..')
SRC = os.path.join(P, 'raw', 'music', 'roar.mp3')
DST = os.path.join(P, 'public', 'audio', 'music_roar.wav')


def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def ramp(t, pts):
    """Piecewise curve through (time, value) points; flat outside."""
    ts, vs = zip(*pts)
    return np.interp(t, ts, vs)


def lowpass_blend(x, fc):
    """Time-varying low-pass: crossfade zero-phase filtered copies (they stay in phase), log-spaced cutoffs.
    fc >= 20000 means dry."""
    bank = [sosfiltfilt(butter(2, c, fs=SR, output='sos'), x, axis=0) for c in CUTOFFS] + [x]
    freqs = np.log(np.array(CUTOFFS + [20000.0]))
    pos = np.interp(np.log(np.clip(fc, CUTOFFS[0], 20000)), freqs, np.arange(len(freqs)))
    lo = np.floor(pos).astype(int); hi = np.minimum(lo + 1, len(freqs) - 1); w = (pos - lo)[:, None]
    out = np.zeros_like(x)
    for k in range(len(bank)):
        out += bank[k] * (((lo == k)[:, None] * (1 - w)) + ((hi == k)[:, None] * w))
    return out


def loudness(path):
    s = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', s)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', s)[-1])


# per cut: length, end of the first part, the drop, and the automation points (ad seconds)
DRY = 20000
CUTS = {
    '76': dict(dur=2295 / 30, cut_a=CUT_A, gap_end=GAP_END, dst=DST,
               fc=[(0.0, 300), (2.2, 1000), (2.3, DRY), (7.85, DRY), (8.0, 1200), (12.55, 1200), (12.7, DRY),
                   (59.9, DRY), (60.0, 900), (CUT_A, 250), (GAP_END, DRY)],
               gain=[(7.85, 0), (8.0, -2), (12.55, -2), (12.7, 0), (59.9, 0), (60.0, -4), (CUT_A, -10), (GAP_END, 0)]),
    '30': dict(dur=30.0, cut_a=17.7, gap_end=17.8, dst=os.path.join(P, 'public', 'audio', 'music_roar30.wav'),
               fc=[(0.0, 300), (2.2, 1000), (2.3, DRY), (3.1, DRY), (3.2, 1500), (5.6, 1500), (5.7, DRY),
                   (16.5, DRY), (16.6, 900), (17.7, 250), (17.8, DRY)],
               gain=[(3.1, 0), (3.2, -1.5), (5.6, -1.5), (5.7, 0), (16.5, 0), (16.6, -4), (17.7, -10), (17.8, 0)]),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cut', default='76', choices=sorted(CUTS))
    c = CUTS[ap.parse_args().cut]
    DUR, CUT_A, GAP_END, DST = c['dur'], c['cut_a'], c['gap_end'], c['dst']
    OFF_B = T0 - LEAD + 324 * BEAT - GAP_END
    trk = decode(SRC)
    n = int(round(DUR * SR))
    t = np.arange(n) / SR

    def take(ad0, ad1, off):
        i0, i1 = int(round(ad0 * SR)), int(round(ad1 * SR))
        s0 = int(round((ad0 + off) * SR))
        seg = trk[s0:s0 + (i1 - i0)]
        return i0, np.pad(seg, ((0, (i1 - i0) - len(seg)), (0, 0)))

    out = np.zeros((n, 2))
    i0, a = take(0.0, CUT_A, OFF_A)
    out[i0:i0 + len(a)] = a
    i0, b = take(GAP_END, DUR, OFF_B)
    out[i0:i0 + len(b)] = b

    fc = ramp(t, c['fc'])
    gain_db = ramp(t, c['gain'])
    out = lowpass_blend(out, fc) * (10 ** (gain_db / 20))[:, None]

    # de-click every edge: in at 0, out at the first part's end, the track's own stop at the very end
    def fade(at, ms, up):
        k = int(ms / 1000 * SR); i = int(round(at * SR))
        env = np.linspace(0, 1, k) if up else np.linspace(1, 0, k)
        if up:
            out[i:i + k] *= env[:, None]
        else:
            out[max(0, i - k):i] *= env[-min(k, i):, None]
    fade(0.0, 30, True)
    fade(CUT_A, 25, False)
    out[int(round(CUT_A * SR)):int(round(GAP_END * SR))] = 0
    fade(GAP_END, 3, True)
    fade(DUR, 40, False)

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    sf.write(DST, out.astype(np.float32), SR, subtype='FLOAT')
    lufs, _ = loudness(DST)
    out *= 10 ** ((TARGET_LUFS - lufs) / 20)
    sf.write(DST, out.astype(np.float32), SR, subtype='FLOAT')
    lufs, tp = loudness(DST)
    hit = lambda k, off: T0 - LEAD + k * BEAT - off
    print(f'wrote {os.path.relpath(DST, P)}: {DUR:.2f} s, {lufs:.1f} LUFS, peak {tp:.1f} dBFS; '
          f'kick of beat 64 on ad {hit(64, OFF_A):.3f} s, beat 324 on ad {hit(324, OFF_B):.3f} s, '
          f'track stops at ad {hit(352, OFF_B):.2f} s')


if __name__ == '__main__':
    main()
