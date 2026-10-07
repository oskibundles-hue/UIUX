#!/usr/bin/env python3
"""mix.py -- the test chapter's sound: dialog + natural sound + the temp bed -> two -14 LUFS mixes (with bed / NO MUSIC).

Buses (48 kHz stereo float), every camera sound read from /home/user/day-owt/aud/<clip>.m4a (the camera AAC, full length):
  dialog  each edl.json dialog piece through Part 2's voice chain (high-pass 90 Hz, afftdn nr 10, -2 dB @300 Hz, +2.5 dB
          @3.5 kHz, de-esser, 3:1 compressor), mono, levelled to -16 LUFS, 12 ms fade in, 100 ms fade out at the end of
          its >= 350 ms tail. Bleeps (edl `bleeps`) are a 1 kHz tone over the word.
  nat     each picture shot's own camera sound (cutaways carry on the take they cut away from; the 0.5x roll-up uses the
          real-time engine from audio_extra; the drive cutaways use the parked room tone 0092 37.6-43.6 because their own
          audio has the car stereo). Every transcribed word in it, his or anyone's, is replaced by its < 250 Hz content
          (no intelligible speech, the engine rumble stays), so the only voice is the dialog bus and strangers are muted.
          -24 LUFS per segment (the 0090 arrival -19: the engine is the moment), ducked 10 dB under dialog.
  bed     bed.wav (music.py, original). Off from the first 0090 shot to the start of the 0090 103.72 shot (the arrival:
          no bed, as PLAN says). -35 LUFS under talk, -21 in the gaps (attack 60 ms, release 400 ms, gaps < 0.6 s held).
Master: sum -> 30 Hz high-pass -> true-peak limiter (-1.5 dBTP) -> gain iterated to -14.0 LUFS (BS.1770, gated).
Report (mix.json): LUFS, true peak, and the voice-over-music margin on every voiced 50 ms frame of the dialog (dialog bus vs bed bus
after ducking; must be >= 10 dB).
    python3 mix.py WORKDIR
"""
import json, math, os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
FF = os.environ.get('FFMPEG', '/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2')
AUD = '/home/user/day-owt/aud'
TRD = '/home/user/day-owt/tr'
CHAIN = ('highpass=f=90:poles=2,afftdn=nr=10:nf=-42:tn=1,equalizer=f=300:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.0:g=2.5,'
         'deesser=i=0.4:m=0.5:f=0.5,acompressor=threshold=-24dB:ratio=3:attack=10:release=150:makeup=2')
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
FPS = 30000 / 1001
NF = int(round(EDL['duration'] * FPS))
DUR = NF / FPS
NS = int(round(DUR * SR))
DIALOG_LUFS, NAT_LUFS, NAT_ARRIVAL_LUFS = -16.0, -24.0, -19.0
BED_TALK, BED_GAP = -38.0, -21.0
TARGET, CEIL = -14.0, -1.5


# ---------------------------------------------------------------- BS.1770 / true peak (from part2/lib/mix.py)
def _kweight_gain(n):
    f = np.fft.rfftfreq(n, 1 / SR); z = np.exp(1j * 2 * np.pi * f / SR)

    def biq(b, a):
        return (b[0] + b[1] / z + b[2] / z ** 2) / (a[0] + a[1] / z + a[2] / z ** 2)
    h1 = biq([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
    h2 = biq([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])
    return np.abs(h1 * h2) ** 2


def lufs(x):
    if x.ndim == 1:
        x = np.stack([x, x], 1) * (1 / math.sqrt(2))
    n = x.shape[0]
    if n < SR * 0.4:
        x = np.concatenate([x, np.zeros((int(SR * 0.4) - n, 2))]); n = x.shape[0]
    N = 1 << int(math.ceil(math.log2(n)))
    y = np.fft.irfft(np.fft.rfft(x, N, axis=0) * np.sqrt(_kweight_gain(N))[:, None], N, axis=0)[:n]
    p = (y ** 2).sum(1)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    c = np.concatenate([[0], np.cumsum(p)])
    st = np.arange(0, n - blk + 1, hop)
    z = (c[st + blk] - c[st]) / blk
    L = -0.691 + 10 * np.log10(np.maximum(z, 1e-12))
    z1 = z[L > -70]
    if not len(z1):
        return -70.0
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean())) if len(z2) else -70.0


def os_peaks(x, os_=4, chunk=1 << 19, pad=8192):
    n = x.shape[0]; out = np.empty(n)
    for i0 in range(0, n, chunk):
        i1 = min(n, i0 + chunk); a, b = max(0, i0 - pad), min(n, i1 + pad)
        seg = x[a:b]
        up = np.fft.irfft(np.fft.rfft(seg, axis=0), seg.shape[0] * os_, axis=0) * os_
        out[i0:i1] = np.abs(up).max(1).reshape(seg.shape[0], os_).max(1)[i0 - a:i1 - a]
    return out


def true_peak_db(x):
    return float(20 * np.log10(os_peaks(x).max() + 1e-12))


def limiter(x, ceiling_db, look=0.0015, release=0.012):
    c = 10 ** (ceiling_db / 20); n = x.shape[0]
    need = np.minimum(1, c / np.maximum(os_peaks(x), 1e-9))
    L = int(round((look + release) * SR))
    mm = np.lib.stride_tricks.sliding_window_view(np.concatenate([need, np.ones(L)]), L).min(1)[:n]
    g = np.minimum(np.convolve(np.concatenate([np.ones(L - 1), mm]), np.ones(L) / L, mode='valid'), 1)
    return x * g[:, None]


def hp(x, fc):
    n = len(x); N = 1 << int(np.ceil(np.log2(n)))
    f = np.fft.rfftfreq(N, 1 / SR); H = 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(np.fft.rfft(x, N, axis=0) * H[:, None], N, axis=0)[:n]


def lp(x, fc):
    n = len(x); N = 1 << int(np.ceil(np.log2(max(n, 2))))
    f = np.fft.rfftfreq(N, 1 / SR); H = 1 / np.sqrt(1 + (f / fc) ** 8)
    return np.fft.irfft(np.fft.rfft(x, N, axis=0) * H[:, None], N, axis=0)[:n]


def master(x):
    x = hp(x, 30); gain = 1.0
    for _ in range(5):
        y = limiter(x * gain, CEIL); L = lufs(y)
        if abs(L - TARGET) < 0.05:
            break
        gain *= 10 ** ((TARGET - L) / 20)
    y[-int(0.06 * SR):] = 0
    return y, lufs(y), true_peak_db(y)


# ---------------------------------------------------------------- io
def aud(src, a, b, af=None):
    pad0 = min(0.6, max(0.0, a))
    cmd = [FF, '-v', 'error', '-ss', f'{a - pad0:.6f}', '-i', f'{AUD}/{src}.m4a', '-t', f'{b - a + pad0 + 0.6:.6f}', '-map', '0:a:0']
    if af:
        cmd += ['-af', af]
    raw = subprocess.run(cmd + ['-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, '<f4').reshape(-1, 2).astype(np.float64)
    i0, n = int(round(pad0 * SR)), int(round((b - a) * SR))
    out = x[i0:i0 + n]
    return np.concatenate([out, np.zeros((n - len(out), 2))]) if len(out) < n else out


def read_wav(path):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, '<f4').reshape(-1, 2).astype(np.float64)


def write_wav24(path, x):
    x = np.clip(x, -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR)
        w.writeframes(i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes())


def ramp(n, up=True):
    r = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
    return r if up else r[::-1]


def fades(x, fin, fout):
    a, b = min(len(x), int(fin * SR)), min(len(x), int(fout * SR))
    if a:
        x[:a] *= ramp(a)[:, None]
    if b:
        x[len(x) - b:] *= ramp(b, False)[:, None]
    return x


def place(bus, x, t):
    s = int(round(t * SR))
    if s < 0:
        x = x[-s:]; s = 0
    e = min(len(bus), s + len(x))
    if e > s:
        bus[s:e] += x[:e - s]


def words(src):
    t = json.load(open(f'{TRD}/{src}.json'))
    return [(w[0], w[1], w[2].strip()) for s in t['segments'] for w in s['words']]


# ---------------------------------------------------------------- buses
def build_dialog(rep):
    bus = np.zeros((NS, 2)); spans = []
    for d in EDL['dialog']:
        x = aud(d['src'], d['in'], d['out'], CHAIN)
        m = x.mean(1)
        for bl in EDL.get('bleeps', []):
            if bl['src'] == d['src'] and d['in'] < bl['out'] and bl['in'] < d['out']:
                i0 = int((max(bl['in'], d['in']) - d['in']) * SR); i1 = int((min(bl['out'], d['out']) - d['in']) * SR)
                rms = np.sqrt((m[max(0, i0 - SR // 2):i1 + SR // 2] ** 2).mean())
                tone = np.sin(2 * np.pi * 1000 * np.arange(i1 - i0) / SR) * rms * 1.2
                r = int(0.005 * SR)
                tone[:r] *= ramp(r); tone[-r:] *= ramp(r, False)
                m[i0:i1] = tone
        x = np.stack([m, m], 1)
        g = 10 ** ((DIALOG_LUFS - lufs(x)) / 20)
        x = fades(x * g, 0.012, 0.1)
        place(bus, x, d['t'])
        spans.append((d['t'], d['t'] + d['out'] - d['in']))
        rep['dialog'].append(dict(src=d['src'], **{'in': d['in']}, out=d['out'], t=d['t'], gain_db=round(20 * math.log10(g), 1)))
    return bus, spans


def activity(spans, attack=0.06, release=0.4, bridge=0.6):
    a = np.zeros(NS)
    sp = sorted(spans); merged = []
    for s, e in sp:
        if merged and s - merged[-1][1] < bridge:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    for s, e in merged:
        a[max(0, int((s - attack) * SR)):min(NS, int((e + 0.05) * SR))] = 1
    k = int(release * SR)
    c = np.concatenate([np.zeros(k), np.cumsum(a)])
    sm = (c[k:k + NS] - c[:NS]) / k      # trailing moving average = the release
    return np.maximum(a, sm)


def nat_segments():
    """(src, a, b, t, lufs) for the natural sound under the picture."""
    segs = []
    shots = EDL['shots']
    i = 0
    prev = None
    for s in shots:
        cut = s['note'].startswith('CUTAWAY')
        if cut and s['src'] == '0092':
            continue      # the drive cutaways: room tone below
        if cut and prev is not None:
            ps = prev
            a = ps['out'] + (s['t'] - (ps['t'] + ps['dur']))
            segs.append((ps['src'], a, a + s['dur'], s['t'], NAT_LUFS))
            continue
        if s['speed'] != 1.0:
            continue      # the 0.5x roll-up: audio_extra nat below
        a = s['in']
        t = s['t']
        if s['src'] == '0092' and abs(s['in'] - 88.5) < 1e-6:
            a, t = 88.8, s['t'] + 0.3      # the stereo song stops at 88.75
        lv = NAT_ARRIVAL_LUFS if s['src'] == '0090' and s['in'] < 30 else NAT_LUFS
        segs.append((s['src'], a, s['out'], t, lv))
        prev = s
    for e in EDL['audio_extra']:
        if e['kind'] == 'nat':
            segs.append((e['src'], e['in'], e['out'], e['t'], NAT_ARRIVAL_LUFS))
    cut0 = next(s for s in shots if s['note'].startswith('CUTAWAY DRIVE'))
    cut_d = sum(s['dur'] for s in shots if s['note'].startswith('CUTAWAY DRIVE'))
    segs.append(('0092', 37.6, 37.6 + cut_d, cut0['t'], NAT_LUFS))
    return segs


def nat_seg(src, a, b, lv):
    x = aud(src, a, b)
    W = words(src)
    lo = lp(x, 250)
    for w0, w1, _ in W:
        if w1 < a - 0.1 or w0 > b + 0.1:
            continue
        i0 = max(0, int((w0 - 0.08 - a) * SR)); i1 = min(len(x), int((w1 + 0.12 - a) * SR))
        if i1 <= i0:
            continue
        r = min(int(0.04 * SR), (i1 - i0) // 2)
        g = np.ones(i1 - i0)
        if r:
            g[:r] = ramp(r, False); g[-r:] = ramp(r)
        else:
            g[:] = 0
        x[i0:i1] = x[i0:i1] * g[:, None] + lo[i0:i1] * (1 - g)[:, None]
    L = lufs(x)
    x = x * 10 ** ((lv - L) / 20) if L > -69 else x
    return fades(x, 0.03, 0.03)


def main():
    work = sys.argv[1]
    rep = {'dialog': [], 'nat': []}
    dia, spans = build_dialog(rep)
    act = activity(spans)
    nat = np.zeros((NS, 2))
    for src, a, b, t, lv in nat_segments():
        place(nat, nat_seg(src, a, b, lv), t)
        rep['nat'].append(dict(src=src, **{'in': round(a, 3)}, out=round(b, 3), t=round(t, 3), lufs=lv))
    nat *= (1 - act * (1 - 10 ** (-10 / 20)))[:, None]
    # bed
    bed = read_wav(os.path.join(work, 'bed.wav'))[:NS]
    bed = np.concatenate([bed, np.zeros((NS - len(bed), 2))]) if len(bed) < NS else bed
    bed *= 10 ** ((BED_GAP - lufs(bed)) / 20)
    duck = 10 ** ((BED_TALK - BED_GAP) / 20)
    g = 1 - act * (1 - duck)
    on = np.ones(NS)
    s0 = [s for s in EDL['shots'] if s['src'] == '0090']
    off0 = s0[0]['t']; on1 = next(s['t'] for s in s0 if s['in'] > 100)
    i_off, i_on = int(off0 * SR), int(on1 * SR)
    fo, fi = int(1.5 * SR), int(2.0 * SR)
    on[i_off - fo:i_off] = ramp(fo, False); on[i_off:i_on] = 0; on[i_on:i_on + fi] = ramp(fi)
    e = int(1.2 * SR); on[NS - e:] *= ramp(e, False)
    bed *= (g * on)[:, None]
    rep['bed'] = dict(source='music.py (original, synthesized here)', talk_lufs=BED_TALK, gap_lufs=BED_GAP,
                      off=[round(off0, 3), round(on1, 3)])
    # voice over music wherever he speaks: every 50 ms frame inside a dialog piece where the voice is up (within 15 dB of
    # the piece's loudest frame and over -40 dBFS: syllables, not the pauses whisper stretches its word times over),
    # dialog bus RMS minus bed bus RMS (after ducking) on the same frame; must be >= 10 dB everywhere.
    margins = []
    h = int(0.05 * SR)
    for d in EDL['dialog']:
        i0, i1 = int(d['t'] * SR), int((d['t'] + d['out'] - d['in']) * SR)
        fr = [(k, 10 * np.log10((dia[k:k + h] ** 2).mean() + 1e-12), 10 * np.log10((bed[k:k + h] ** 2).mean() + 1e-12))
              for k in range(i0, i1 - h, h)]
        if not fr:
            continue
        top = max(v for _, v, _ in fr)
        for k, v, m in fr:
            if v > top - 15 and v > -40:
                margins.append((round(v - m, 1), d['src'], round(d['in'] + (k - i0) / SR, 2)))
    # per word (small.en word windows): mean power of the voiced frames inside the word vs the bed on those frames
    wm = []
    for d in EDL['dialog']:
        fr = [m for m in margins if m[1] == d['src'] and d['in'] - 0.01 <= m[2] <= d['out']]
        for w0, w1, txt in words(d['src']):
            if w0 >= d['out'] or w1 <= d['in']:
                continue
            ks = [int((d['t'] + m[2] - d['in']) * SR) for m in fr if w0 - 0.05 <= m[2] < w1]
            if not ks:
                continue
            v = np.mean([(dia[k:k + h] ** 2).mean() for k in ks]); b = np.mean([(bed[k:k + h] ** 2).mean() for k in ks])
            wm.append((round(10 * np.log10((v + 1e-12) / (b + 1e-12)), 1), d['src'], round(w0, 2), txt))
    wm.sort()
    rep['voice_over_music_words_db'] = dict(min=wm[0][0] if wm else None, words=len(wm), under_10=[w for w in wm if w[0] < 10], lowest5=wm[:5])
    margins.sort()
    rep['voice_over_music_db'] = dict(min=margins[0][0] if margins else None, frames=len(margins),
                                      p1=margins[len(margins) // 100][0] if margins else None,
                                      under_10=[m for m in margins if m[0] < 10], lowest5=margins[:5])
    out = {}
    for name, mix in (('mix', dia + nat + bed), ('nomusic', dia + nat)):
        y, L, tp = master(mix)
        write_wav24(os.path.join(work, f'{name}.wav'), y)
        out[name] = dict(lufs=round(L, 2), true_peak=round(tp, 2))
    rep['masters'] = out
    json.dump(rep, open(os.path.join(work, 'mix.json'), 'w'), indent=1)
    print(json.dumps({'masters': out, 'voice_over_music_word_min_db': rep['voice_over_music_words_db']['min'],
                      'words_under_10': len(rep['voice_over_music_words_db']['under_10']),
                      'voice_over_music_frame_min_db': rep['voice_over_music_db']['min'],
                      'frames': len(margins), 'under_10': len(rep['voice_over_music_db']['under_10'])}))


if __name__ == '__main__':
    main()
