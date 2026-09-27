#!/usr/bin/env python3
"""
mix.py -- the sound of the rally vlog v2: dialog + nat + music + Locked-On SFX -> -14 LUFS masters.

Buses (48 kHz stereo float):
  dialog  every EDL dialog piece from the mezzanine audio: ffmpeg highpass 80 Hz -> afftdn (gentle, noise
          tracking) -> acompressor (2:1, slow) on the piece with 0.6 s of padding, then cut to the piece, summed
          to mono (centred), levelled per piece to config `audio.dialogLufs` (BS.1770 integrated, measured
          here), 12 ms edge fades. Per-piece trims: config `audio.trims`.
  nat     the EDL's nat/extra audio and the B-roll shots' own sound (config `audio.nat`), each levelled to its
          own target, 150 ms fades, ducked `audio.natDuckDb` under dialog.
  music   `audio/music.wav` when it exists (the swappable slot, config `music`), else the original synth bed
          (lib/music.py). Levelled so the unducked bed is `music.lufs`, ducked `music.duckDb` under dialog
          (attack 120 ms before a piece, release 350 ms after, gaps < 0.6 s bridged).
  sfx     the Locked-On pack (10-motion-sfx/locked-on-sfx), cue list from build.py (.work/sfx_cues.json). Each
          accent is set to `sfx.ratio` (45 %) of the UNDUCKED music RMS over the accent's own energetic span,
          then ducked a further `sfx.duckDb` under dialog, so ticks stay audible without stepping on words.
Master: sum -> 30 Hz high-pass -> 4x true-peak limiter at `master.ceiling` -> gain iterated (numpy BS.1770) to
`master.lufs`, re-limited; the last 60 ms are exact zeros. The no-music master is the same without the music bus.
Every level is reported in .work/mix.json.
"""
import argparse, json, math, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import synth as S  # noqa: E402

SR = 48000
FPS = 30000 / 1001
CFG = json.load(open(os.path.join(ROOT, 'config.json')))
P = CFG['paths']
FF = os.environ.get('FFMPEG', P['ffmpeg'])
EDL = json.load(open(P['edl']))
NF = int(round(EDL['duration'] * FPS))
DUR = NF / FPS
NS = int(round(DUR * SR))
WORK = os.path.join(ROOT, '.work')
A = CFG['audio']


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------------------ bus cache (rally-v2 render loop)
# The dialog and nat buses only change when their own inputs change, so a layer or SFX fix re-mixes without
# re-decoding and re-filtering 46 pieces of camera audio. Arrays are stored as float64 .npy: bit-identical.
import hashlib, time  # noqa: E402
CACHE = os.path.join(WORK, 'cache')


def _mezz_listing():
    out = []
    for d in (P['mezz'], os.path.join(WORK, 'mezz_extra')):
        if os.path.isdir(d):
            out += sorted(f'{fn}:{os.path.getsize(os.path.join(d, fn))}' for fn in os.listdir(d))
    return out


def cached_bus(name, parts, build):
    key = hashlib.sha1((json.dumps(parts, sort_keys=True, default=str) + '|'.join(_mezz_listing())).encode()
                       + open(__file__, 'rb').read()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    npy, js = os.path.join(CACHE, f'{name}.npy'), os.path.join(CACHE, f'{name}.json')
    if os.path.exists(npy) and os.path.exists(js):
        meta = json.load(open(js))
        if meta.get('key') == key:
            return np.load(npy), meta['extra'], True
    arr, extra = build()
    np.save(npy + '.tmp.npy', arr); os.replace(npy + '.tmp.npy', npy)
    json.dump(dict(key=key, extra=extra), open(js, 'w'))
    return arr, extra, False


# ------------------------------------------------------------------------------ loudness (BS.1770-4)
def _kweight_gain(n):
    """|H(f)|^2 of the BS.1770 K-weighting (pre-filter shelf + RLB high-pass) at the rfft bins of length n."""
    f = np.fft.rfftfreq(n, 1 / SR)
    w = 2 * np.pi * f / SR
    z = np.exp(1j * w)

    def biq(b, a):
        return (b[0] + b[1] / z + b[2] / z ** 2) / (a[0] + a[1] / z + a[2] / z ** 2)
    h1 = biq([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
    h2 = biq([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])
    return np.abs(h1 * h2) ** 2


def lufs(x, gate=True):
    """integrated loudness of a stereo (n,2) or mono (n,) float buffer."""
    if x.ndim == 1:
        x = np.stack([x, x], 1) * (1 / math.sqrt(2))
    n = x.shape[0]
    if n < SR * 0.4:
        x = np.concatenate([x, np.zeros((int(SR * 0.4) - n, 2))])
        n = x.shape[0]
    N = 1 << int(math.ceil(math.log2(n)))
    X = np.fft.rfft(x, N, axis=0)
    y = np.fft.irfft(X * np.sqrt(_kweight_gain(N))[:, None], N, axis=0)[:n]
    p = (y ** 2).sum(1)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    c = np.concatenate([[0], np.cumsum(p)])
    starts = np.arange(0, n - blk + 1, hop)
    z = (c[starts + blk] - c[starts]) / blk
    L = -0.691 + 10 * np.log10(np.maximum(z, 1e-12))
    if not gate:
        return float(-0.691 + 10 * np.log10(max(z.mean(), 1e-12)))
    z1 = z[L > -70]
    if not len(z1):
        return -70.0
    rel = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > rel]
    return float(-0.691 + 10 * np.log10(z2.mean())) if len(z2) else -70.0


def true_peak_db(x):
    X = np.fft.rfft(x, axis=0)
    up = np.fft.irfft(X, x.shape[0] * 4, axis=0) * 4
    return float(20 * np.log10(np.abs(up).max() + 1e-12))


# ------------------------------------------------------------------------------ io
def mezz_audio(src, a, b, af=None):
    """source seconds [a, b] of clip src from the mezzanine (or .work/mezz_extra), float64 stereo."""
    cands = []
    for d in (P['mezz'], os.path.join(WORK, 'mezz_extra')):
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            m = re.match(r'^(\w+?)_(?:audio_)?([\d.]+)-([\d.]+)\.(mov|wav)$', fn)
            if m and m.group(1) == src and float(m.group(2)) - 0.03 <= a and b <= float(m.group(3)) + 0.03:
                cands.append((os.path.join(d, fn), float(m.group(2))))
    if not cands:
        raise SystemExit(f'no audio for {src} {a}-{b}')
    path, t0 = cands[0]
    ss = a - t0
    pad0 = min(0.6, max(0.0, ss))
    cmd = [FF, '-v', 'error', '-ss', f'{ss - pad0:.6f}', '-i', path, '-t', f'{b - a + pad0 + 0.6:.6f}', '-map', '0:a:0']
    if af:
        cmd += ['-af', af]
    cmd += ['-f', 'f32le', '-ac', '2', '-ar', str(SR), '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, '<f4').reshape(-1, 2).astype(np.float64)
    i0 = int(round(pad0 * SR))
    n = int(round((b - a) * SR))
    out = x[i0:i0 + n]
    if len(out) < n:
        out = np.concatenate([out, np.zeros((n - len(out), 2))])
    return out


def read_wav(path):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, '<f4').reshape(-1, 2).astype(np.float64)


def write_wav24(path, x):
    x = np.clip(x, -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    b = i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR); w.writeframes(b)


def fades(x, fin, fout):
    n = len(x)
    a, b = min(n, int(fin * SR)), min(n, int(fout * SR))
    if a:
        x[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2 if x.ndim == 1 else (np.sin(np.linspace(0, np.pi / 2, a)) ** 2)[:, None]
    if b:
        g = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
        x[n - b:] *= g if x.ndim == 1 else g[:, None]
    return x


def place(bus, x, t):
    s = int(round(t * SR))
    if s < 0:
        x = x[-s:]; s = 0
    e = min(len(bus), s + len(x))
    if e > s:
        bus[s:e] += x[:e - s]


# ------------------------------------------------------------------------------ buses
DIALOG_AF = A['dialogFilter']


def build_dialog(report):
    bus = np.zeros((NS, 2))
    spans = []
    for i, d in enumerate(EDL['dialog'] + A.get('extraDialog', [])):
        tr = A['trims'].get(str(i), {}) if i < len(EDL['dialog']) else {}
        a = d['in'] + tr.get('in', 0.0)
        b = d['out'] + tr.get('out', 0.0)
        t = d['t'] + tr.get('in', 0.0) + d.get('shift', 0.0)
        x = mezz_audio(d['src'], a, b, DIALOG_AF)
        m = x.mean(1)
        L = lufs(np.stack([m, m], 1))                  # loudness of the piece as placed (centred mono, L = R = m)
        tgt = A['dialogLufs'] + tr.get('gainDb', 0.0) + d.get('gainDb', 0.0)
        g = float(np.clip(tgt - L, -12, 18))
        m = fades(m * 10 ** (g / 20), tr.get('fin', A['edgeFade']), tr.get('fout', A['edgeFade']))
        st = np.stack([m, m], 1)
        place(bus, st, t)
        spans.append([t, t + (b - a)])
        report['dialog'].append(dict(i=i, src=d['src'], a=round(a, 3), b=round(b, 3), t=round(t, 3), lufs_in=round(L, 2), gain_db=round(g, 2)))
    return bus, spans


def activity(spans, pre=0.12, post=0.35, bridge=0.6):
    """0..1 dialog activity envelope (smoothed), for ducking."""
    sp = sorted(spans)
    merged = []
    for a, b in sp:
        if merged and a - merged[-1][1] < bridge:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    env = np.zeros(NS)
    for a, b in merged:
        i0, i1 = max(0, int((a - pre) * SR)), min(NS, int((b + post) * SR))
        env[i0:i1] = 1
    # raised-cosine ramps: attack over `pre`, release over `post`
    k_a, k_r = int(pre * SR), int(post * SR)
    out = env.copy()
    for a, b in merged:
        i0 = max(0, int((a - pre) * SR)); i1 = min(NS, i0 + k_a)
        out[i0:i1] = 0.5 - 0.5 * np.cos(np.pi * np.arange(i1 - i0) / max(1, k_a))
        j1 = min(NS, int((b + post) * SR)); j0 = max(0, j1 - k_r)
        out[j0:j1] = np.minimum(out[j0:j1], 0.5 + 0.5 * np.cos(np.pi * np.arange(j1 - j0) / max(1, k_r)))
    return out, merged


def nat_speech_spans():
    """timeline spans of transcribed words inside each nat clip (someone talking in the nat -> the music ducks too)."""
    out = []
    for e in A['nat']:
        p = os.path.join(P['transcripts'], f"{e['src']}.json")
        if not os.path.exists(p):
            continue
        tr = json.load(open(p))
        for sg in tr['segments']:
            for w in sg['words']:
                if w[0] < e['b'] and w[1] > e['a']:
                    out.append([e['t'] + max(w[0], e['a']) - e['a'], e['t'] + min(w[1], e['b']) - e['a']])
    return out


def build_nat(act, report):
    return build_nat_raw(report) * (10 ** (A['natDuckDb'] * act / 20))[:, None]


def build_nat_raw(report):
    bus = np.zeros((NS, 2))
    for e in A['nat']:
        x = mezz_audio(e['src'], e['a'], e['b'], 'highpass=f=40')
        L = lufs(x)
        g = float(np.clip(e.get('lufs', A['natLufs']) - L, -20, 20))
        x = fades(x * 10 ** (g / 20), e.get('fin', 0.15), e.get('fout', 0.15))
        place(bus, x, e['t'])
        report['nat'].append(dict(src=e['src'], a=e['a'], b=e['b'], t=e['t'], lufs_in=round(L, 2), gain_db=round(g, 2)))
    return bus


def load_music(report):
    mc = CFG['music']
    slot = os.path.join(ROOT, mc['file'])
    if os.path.exists(slot):
        x = read_wav(slot)
        report['music'] = dict(source=mc['file'], bpm=mc.get('bpm'), downbeat0=mc.get('downbeat0'))
        x = x[int(mc.get('offset', 0.0) * SR):]
    else:
        path = os.path.join(WORK, 'music_synth.wav')
        x = read_wav(path)
        sync = json.load(open(os.path.join(WORK, 'music_synth.json')))
        report['music'] = dict(source='original synth bed (lib/music.py), no music.wav supplied', bpm=sync['bpm'], downbeat0=sync['downbeat0'])
    if len(x) < NS:
        x = np.concatenate([x, np.zeros((NS - len(x), 2))])
    x = x[:NS].copy()
    if os.path.exists(slot) and mc.get('tapeStop'):
        # a supplied track is stopped here on its own (varispeed), then silent until the end card hit
        t0, t1 = [int(v * SR) for v in mc['tapeStop']]
        u = np.arange(t1 - t0) / (t1 - t0)
        x[t0:t1] = S.varispeed(x[t0:t1], (1 - u) ** 1.3) * np.minimum(1, (t1 - t0 - np.arange(t1 - t0)) / (0.02 * SR))[:, None]
        x[t1:] = 0
    return x


def span_rms(x, i0, i1):
    seg = x[max(0, i0):min(len(x), i1)]
    return float(np.sqrt((seg ** 2).mean() + 1e-12)) if len(seg) else 1e-6


def energetic_span(y):
    """the part of a sound holding 90 % of its energy (clamped to 20-300 ms)."""
    e = (y ** 2).sum(1) if y.ndim == 2 else y ** 2
    c = np.cumsum(e) / max(e.sum(), 1e-12)
    a = int(np.searchsorted(c, 0.05)); b = int(np.searchsorted(c, 0.95))
    mid = (a + b) // 2
    half = int(np.clip((b - a) / 2, 0.01 * SR, 0.15 * SR))
    return max(0, mid - half), min(len(e), mid + half)


def build_sfx(music_raw, act, report):
    bus = np.zeros((NS, 2))
    cues = json.load(open(os.path.join(WORK, 'sfx_cues.json')))
    lib = {}
    ref = float(np.median([span_rms(music_raw, i, i + SR) for i in range(0, NS - SR, SR)]))
    for c in cues:
        f = c['file']
        if f not in lib:
            lib[f] = read_wav(os.path.join(ROOT, P['sfx'], f))
        y = lib[f].copy()
        if c.get('dur'):
            y = y[:int(c['dur'] * SR)]
            y = fades(y, 0.0, min(0.08, c['dur'] / 3))
        t = c['t'] - c.get('align', 0.0) * len(y) / SR
        a, b = energetic_span(y)
        i0 = int(t * SR) + a
        mus = max(span_rms(music_raw, i0, int(t * SR) + b), 0.35 * ref)
        own = span_rms(y, a, b)
        g = A['sfx']['ratio'] * mus / own * 10 ** (c.get('db', 0.0) / 20)
        d = 10 ** (A['sfx']['duckDb'] * float(act[min(NS - 1, max(0, i0))]) / 20)
        place(bus, y * g * d, t)
        report['sfx'].append(dict(file=f, t=round(c['t'], 3), why=c.get('why', ''), gain_db=round(20 * math.log10(g * d), 2), duck=round(20 * math.log10(d), 2)))
    return bus


def master(x, target, ceiling):
    x = S.fft_filter(x, lo=30, slope=2)
    gain = 1.0
    for it in range(4):
        y = S.limiter(x * gain, ceiling_db=ceiling)
        L = lufs(y)
        if abs(L - target) < 0.05:
            break
        gain *= 10 ** ((target - L) / 20)
    master.gain = gain
    y = S.limiter(x * gain, ceiling_db=ceiling)
    tail = int(0.06 * SR)
    y[-tail:] = 0
    fl = int(0.25 * SR)
    y[-tail - fl:-tail] *= (np.cos(np.linspace(0, np.pi / 2, fl)) ** 2)[:, None]
    return y, lufs(y), true_peak_db(y)


def meter_table(dialog, t0, t1, bands=14):
    """14-band level envelope of the dialog bus (Omarie speaking) for the quote card's meter."""
    x = dialog[int(t0 * SR):int(t1 * SR)].mean(1)
    hop = SR / FPS; n = int(len(x) / hop) - 1
    edges = np.geomspace(120, 7000, bands + 1)
    fr = np.fft.rfftfreq(2048, 1 / SR)
    rows = []
    for i in range(n):
        a = int(i * hop); seg = x[a:a + 2048]
        if len(seg) < 2048:
            seg = np.pad(seg, (0, 2048 - len(seg)))
        sp = np.abs(np.fft.rfft(seg * np.hanning(2048)))
        rows.append([20 * np.log10(sp[(fr >= edges[k]) & (fr < edges[k + 1])].mean() + 1e-9) for k in range(bands)])
    Aa = np.array(rows)
    lo, hi = np.percentile(Aa, 8), np.percentile(Aa, 99.5)
    Aa = np.clip((Aa - lo) / (hi - lo), 0, 1) ** 1.3
    Aa = Aa[:, [0, 7, 2, 9, 4, 11, 6, 13, 1, 8, 3, 10, 5, 12]]
    return {'fps': FPS, 'src': f'dialog bus {t0:.2f}-{t1:.2f} s (the guest)', 'bands': [[round(float(v), 3) for v in r] for r in Aa]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(WORK, 'mix.wav'))
    ap.add_argument('--out-nomusic', default=os.path.join(WORK, 'mix_nomusic.wav'))
    ap.add_argument('--dialog-only', action='store_true')
    a = ap.parse_args()
    rep = {'dialog': [], 'nat': [], 'sfx': []}
    T = {}; t0 = time.time()
    def _dialog():
        r = {'dialog': []}; d, sp = build_dialog(r)
        return d, dict(spans=sp, dialog=r['dialog'])
    dialog, ex, hit = cached_bus('dialog', [EDL['dialog'], A.get('extraDialog', []), A['trims'], A['dialogFilter'], A['dialogLufs'], A['edgeFade']], _dialog)
    spans = [tuple(x) for x in ex['spans']]; spans = [list(x) for x in spans]; rep['dialog'] = ex['dialog']
    T['dialog'] = f'{time.time() - t0:.1f}s' + (' (cached)' if hit else ''); t0 = time.time()
    dk = A['duck']
    nsp = nat_speech_spans()
    act, merged = activity(spans + nsp, pre=dk['attack'], post=dk['release'], bridge=dk['bridge'])
    rep['nat_speech_spans'] = [[round(a, 3), round(b, 3)] for a, b in nsp]
    write_wav24(os.path.join(WORK, 'stem_dialog.wav'), dialog * 0.5)
    if a.dialog_only:
        json.dump(rep, open(os.path.join(WORK, 'mix.json'), 'w'), indent=1)
        return
    def _nat():
        r = {'nat': []}; bus = build_nat_raw(r)
        return bus, dict(nat=r['nat'])
    nat_raw, ex, hit = cached_bus('nat', [A['nat'], A['natLufs']], _nat)
    rep['nat'] = ex['nat']
    nat = nat_raw * (10 ** (A['natDuckDb'] * act / 20))[:, None]
    T['nat'] = f'{time.time() - t0:.1f}s' + (' (cached)' if hit else ''); t0 = time.time()
    music_raw = load_music(rep)
    Lm = lufs(music_raw)
    music_raw *= 10 ** ((CFG['music']['lufs'] - Lm) / 20)
    music = music_raw * (10 ** (CFG['music']['duckDb'] * act / 20))[:, None]
    sfx = build_sfx(music_raw, act, rep)
    mc = CFG['master']
    on = CFG['music'].get('enabled', True) and os.environ.get('MUSIC', '1') not in ('0', 'false', 'off')
    T['music+sfx'] = f'{time.time() - t0:.1f}s'; t0 = time.time()
    full, L1, tp1 = master(dialog + nat + (music if on else 0) + sfx, mc['lufs'], mc['ceiling'])
    g_full = master.gain
    nomus, L2, tp2 = master(dialog + nat + sfx, mc['lufs'], mc['ceiling'])
    T['masters'] = f'{time.time() - t0:.1f}s'; t0 = time.time()
    write_wav24(a.out, full)
    write_wav24(a.out_nomusic, nomus)
    # the music stem exactly as it sits in the master (ducked, at the master's gain, before the limiter)
    stem = S.fft_filter(music, lo=30, slope=2) * g_full
    fl = int(0.25 * SR); stem[-int(0.06 * SR):] = 0
    write_wav24(os.path.join(WORK, 'music_stem.wav'), stem)
    rep['music_enabled'] = bool(on)
    # verification: music level under every dialog piece vs the piece itself (RMS over the piece, dB)
    chk = []
    for d in rep['dialog']:
        i0, i1 = int(d['t'] * SR), int((d['t'] + d['b'] - d['a']) * SR)
        dm = 20 * math.log10(span_rms(dialog, i0, i1) + 1e-9)
        mu = 20 * math.log10(span_rms(music, i0, i1) + 1e-9)
        un = 20 * math.log10(span_rms(music_raw, i0, i1) + 1e-9)
        chk.append(dict(i=d['i'], t=d['t'], dialog_db=round(dm, 1), music_db=round(mu, 1), music_unducked_db=round(un, 1),
                        duck_db=round(mu - un, 1), dialog_over_music_db=round(dm - mu, 1)))
    rep['duck_check'] = chk
    for nm, x in (('stem_nat', nat), ('stem_music', music), ('stem_sfx', sfx)):
        write_wav24(os.path.join(WORK, nm + '.wav'), x * 0.5)
    # meter data for the quote card (Omarie's pick)
    tc = CFG['layer']['testimonial']
    json.dump(meter_table(dialog, tc['t0'], tc['t1']), open(os.path.join(WORK, 'meter.json'), 'w'))
    rep['master'] = dict(lufs=round(L1, 2), true_peak_db=round(tp1, 2), nomusic_lufs=round(L2, 2), nomusic_true_peak_db=round(tp2, 2),
                         music_unducked_lufs=CFG['music']['lufs'], dialog_spans=len(merged), samples=NS, seconds=round(NS / SR, 4))
    json.dump(rep, open(os.path.join(WORK, 'mix.json'), 'w'), indent=1)
    T['stems+report'] = f'{time.time() - t0:.1f}s'
    log(f'mix: {L1:.2f} LUFS TP {tp1:.2f} | no-music {L2:.2f} LUFS TP {tp2:.2f} | music: {rep["music"]["source"]} | ' + ', '.join(f'{k} {v}' for k, v in T.items()))


if __name__ == '__main__':
    main()
