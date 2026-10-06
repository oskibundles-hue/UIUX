#!/usr/bin/env python3
"""
mix.py -- the sound of the Part 1 vlog (v2, 6 Oct): dialog + the in-car bed + Locked-On SFX -> -14 LUFS masters.

Buses (48 kHz stereo float); all camera audio is read from paths.aud/<clip>.m4a (the camera's AAC, full length,
sample-aligned with the mezzanines), so a fix-A tail can run past a mezzanine's end:
  dialog  every EDL dialog piece: the fix-B chain (config `audio.dialogFilter`: HP 90 Hz, afftdn nr 10, -2 dB @300 Hz,
          +2.5 dB @3.5 kHz, de-esser, 3:1) on the piece with 0.6 s of padding, then cut to the piece, summed to mono
          (centred), levelled per piece to `audio.dialogLufs` (BS.1770 integrated, measured here), 12 ms fade in, 100 ms
          fade out (`audio.edgeFadeOut`, at the end of the >= 350 ms tail). Per-piece trims: `audio.trims`.
  bed     config `bed.segs`: the in-car stereo (kind music), exhaust and nat, each from its own clip, levelled to its own
          target, faded, with every transcribed word inside it muted (40 ms ramps: no third-party speech in the bed).
          Music ducks `bed.duckDb.music` (-14 dB) under dialog, exhaust and nat duck `audio.natDuckDb` (-12 dB)
          (attack before a piece, release after it, gaps < `duck.bridge` held down). No synth or library music.
  sfx     the Locked-On pack, cue list from build.py (.work/sfx_cues.json). Each accent is set to `sfx.ratio` of the
          UNDUCKED bed RMS over the accent's own energetic span (floor: 35 % of the median), then ducked `sfx.duckDb`
          under dialog.
Master: sum -> 30 Hz high-pass -> 4x true-peak limiter at `master.ceiling` -> gain iterated (numpy BS.1770) to
`master.lufs`, re-limited; the last 60 ms are exact zeros. The NO MUSIC master is the same with every music seg swapped
for its `sub` (road/exhaust nat of the same length). Every level is reported in .work/mix.json, with the voice over the
bed (music + exhaust + nat) for every dialog piece (fix B: >= audio.minVoiceOverBedDb).
"""
import argparse, json, math, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import synth as S  # noqa: E402

SR = 48000
FPS = 30000 / 1001
from cfg import load_config  # noqa: E402
CFG = load_config()
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
def aud_audio(src, a, b, af=None):
    """source seconds [a, b] of clip src from paths.aud/<src>.m4a (the camera AAC, full length), float64 stereo; the
    filter runs on 0.6 s of padding either side."""
    pad0 = min(0.6, max(0.0, a))
    cmd = [FF, '-v', 'error', '-ss', f'{a - pad0:.6f}', '-i', os.path.join(P['aud'], f'{src}.m4a'), '-t', f'{b - a + pad0 + 0.6:.6f}', '-map', '0:a:0']
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
        x = aud_audio(d['src'], a, b, DIALOG_AF)
        m = x.mean(1)
        L = lufs(np.stack([m, m], 1))                  # loudness of the piece as placed (centred mono, L = R = m)
        tgt = A['dialogLufs'] + tr.get('gainDb', 0.0) + d.get('gainDb', 0.0)
        g = float(np.clip(tgt - L, -12, 18))
        # fix A: the voice fades out over `edgeFadeOut` (100 ms) at the end of its >= 350 ms tail
        m = fades(m * 10 ** (g / 20), tr.get('fin', A['edgeFade']), tr.get('fout', A.get('edgeFadeOut', A['edgeFade'])))
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


BED = CFG['bed']


def clip_words(src):
    p = os.path.join(P['transcripts'], f'{src}.json')
    if not os.path.exists(p):
        return []
    return [w for sg in json.load(open(p))['segments'] for w in sg['words']]


def bed_seg(e, nomusic=False):
    """one bed seg (or, in the no-music bed, its `sub`), levelled, speech-muted and faded; returns (x, info)."""
    kind = e['kind']
    src, a, b = e['src'], e['a'], e['b']
    if nomusic and kind == 'music':
        sb = e['sub']
        src, a, b, kind = sb['src'], sb['a'], sb['a'] + (e['b'] - e['a']), 'exhaust'
    x = aud_audio(src, a, b, 'highpass=f=30')
    mutes = [list(m) for m in (e.get('mute', []) if src == e['src'] else [])]
    mutes += [[w[0] - 0.05, w[1] + 0.05] for w in clip_words(src) if w[0] < b and w[1] > a]
    muted = 0.0
    for ma, mb in mutes:
        i0, i1 = max(0, int(round((ma - a) * SR))), min(len(x), int(round((mb - a) * SR)))
        if i1 > i0:
            k = min(int(0.04 * SR), (i1 - i0) // 2)
            w = np.zeros(i1 - i0)
            if k:
                w[:k] = 0.5 + 0.5 * np.cos(np.pi * np.arange(k) / k)
                w[i1 - i0 - k:] = 0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k)
            x[i0:i1] *= w[:, None]
            muted += (i1 - i0) / SR
    L = lufs(x)
    tgt = e.get('lufs', BED['lufs'][kind]) if src == e['src'] else BED['lufs'][kind]
    g = float(np.clip(tgt - L, -24, 24))
    x = fades(x * 10 ** (g / 20), e.get('fin', 0.15), e.get('fout', 0.15))
    return x, kind, dict(why=e['why'], kind=kind, src=src, a=round(a, 3), b=round(b, 3), t=e['t'], lufs_in=round(L, 2),
                         gain_db=round(g, 2), muted_s=round(muted, 2))


def build_bed(act, nomusic, report):
    """the bed raw (unducked) and ducked, as summed stereo buses."""
    raw, ducked = np.zeros((NS, 2)), np.zeros((NS, 2))
    duck = {'music': BED['duckDb']['music'], 'exhaust': A['natDuckDb'], 'nat': A['natDuckDb']}
    for e in BED['segs']:
        x, kind, info = bed_seg(e, nomusic)
        s0 = int(round(e['t'] * SR))
        n = min(len(x), NS - s0)
        x = x[:n]
        place(raw, x, e['t'])
        g = 10 ** (duck[kind] * act[s0:s0 + n] / 20)
        place(ducked, x * g[:, None], e['t'])
        report.append(info)
    return raw, ducked


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


def build_sfx(bed_raw, act, report):
    bus = np.zeros((NS, 2))
    cues = json.load(open(os.path.join(WORK, 'sfx_cues.json')))
    lib = {}
    ref = float(np.median([span_rms(bed_raw, i, i + SR) for i in range(0, NS - SR, SR)]))
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
        mus = max(span_rms(bed_raw, i0, int(t * SR) + b), 0.35 * ref)
        own = span_rms(y, a, b)
        g = A['sfx']['ratio'] * mus / own * 10 ** (c.get('db', 0.0) / 20)
        d = 10 ** (A['sfx']['duckDb'] * float(act[min(NS - 1, max(0, i0))]) / 20)
        place(bus, y * g * d, t)
        report['sfx'].append(dict(file=f, t=round(c['t'], 3), why=c.get('why', ''), gain_db=round(20 * math.log10(g * d), 2), duck=round(20 * math.log10(d), 2)))
    return bus


def master(x, target, ceiling):
    x = S.fft_filter(x, lo=30, slope=2)
    gain = 1.0
    done = False
    for it in range(4):
        y = S.limiter(x * gain, ceiling_db=ceiling)
        L = lufs(y)
        if abs(L - target) < 0.05:
            done = True
            break
        gain *= 10 ** ((target - L) / 20)
    master.gain = gain
    if not done:            # (on a break, y is already the limiter output at this exact gain: same numbers, one pass fewer)
        y = S.limiter(x * gain, ceiling_db=ceiling)
    tail = int(0.06 * SR)
    y[-tail:] = 0
    fl = int(0.25 * SR)
    y[-tail - fl:-tail] *= (np.cos(np.linspace(0, np.pi / 2, fl)) ** 2)[:, None]
    return y, lufs(y), true_peak_db(y)


def _master_job(args):
    x, target, ceiling = args
    y, L, tp = master(x, target, ceiling)
    return y, L, tp, master.gain


def masters_parallel(xs, target, ceiling):
    import multiprocessing as mp
    try:
        with mp.get_context('fork').Pool(len(xs)) as pool:
            return pool.map(_master_job, [(x, target, ceiling) for x in xs])
    except (OSError, ValueError):
        return [_master_job((x, target, ceiling)) for x in xs]


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
    rep = {'dialog': [], 'bed': [], 'sfx': []}
    T = {}; t0 = time.time()
    def _dialog():
        r = {'dialog': []}; d, sp = build_dialog(r)
        return d, dict(spans=sp, dialog=r['dialog'])
    dialog, ex, hit = cached_bus('dialog', [EDL['dialog'], A.get('extraDialog', []), A['trims'], A['dialogFilter'], A['dialogLufs'],
                                            A['edgeFade'], A.get('edgeFadeOut'), P['aud']], _dialog)
    spans = [list(x) for x in ex['spans']]; rep['dialog'] = ex['dialog']
    T['dialog'] = f'{time.time() - t0:.1f}s' + (' (cached)' if hit else ''); t0 = time.time()
    dk = A['duck']
    act, merged = activity(spans, pre=dk['attack'], post=dk['release'], bridge=dk['bridge'])
    write_wav24(os.path.join(WORK, 'stem_dialog.wav'), dialog * 0.5)
    if a.dialog_only:
        json.dump(rep, open(os.path.join(WORK, 'mix.json'), 'w'), indent=1)
        return
    def _bed(nm):
        def f():
            r = []; raw, d = build_bed(act, nm, r)
            return np.stack([raw, d]), dict(bed=r)
        return f
    key = [BED, A['natDuckDb'], dk, spans, P['aud']]
    (bed_raw, bed), ex, hit1 = cached_bus('bed', key, _bed(False))
    rep['bed'] = ex['bed']
    (bed_raw_n, bed_n), ex_n, hit2 = cached_bus('bed_nomusic', key, _bed(True))
    for d, dn in zip(rep['bed'], ex_n['bed']):
        d['nomusic'] = 'same' if d['kind'] != 'music' else f"swapped for {dn['src']} {dn['a']}-{dn['b']} (road/exhaust nat)"
    rep['bed_source'] = ('the in-car stereo and exhaust/road nat from the clips themselves (config bed.segs, paths.aud); no synth or '
                         'library music; the NO MUSIC mix swaps each in-car song for road/exhaust nat of the same length')
    T['bed'] = f'{time.time() - t0:.1f}s' + (' (cached)' if hit1 and hit2 else ''); t0 = time.time()
    sfx = build_sfx(bed_raw, act, rep)
    sfx_n = build_sfx(bed_raw_n, act, {'sfx': []})
    mc = CFG['master']
    (full, L1, tp1, g_full), (nomus, L2, tp2, _) = masters_parallel([dialog + bed + sfx, dialog + bed_n + sfx_n], mc['lufs'], mc['ceiling'])
    T['masters'] = f'{time.time() - t0:.1f}s'; t0 = time.time()
    write_wav24(a.out, full)
    write_wav24(a.out_nomusic, nomus)
    # the bed stem exactly as it sits in the master (ducked, at the master's gain, before the limiter)
    stem = S.fft_filter(bed, lo=30, slope=2) * g_full
    stem[-int(0.06 * SR):] = 0
    write_wav24(os.path.join(WORK, 'bed_stem.wav'), stem)
    # fix B check: the voice over the bed (music + exhaust + nat, ducked) under every dialog piece (RMS over the piece, dB)
    chk = []
    for d in rep['dialog']:
        i0, i1 = int(d['t'] * SR), int((d['t'] + d['b'] - d['a']) * SR)
        dm = 20 * math.log10(span_rms(dialog, i0, i1) + 1e-9)
        bd = 20 * math.log10(span_rms(bed, i0, i1) + 1e-9)
        un = 20 * math.log10(span_rms(bed_raw, i0, i1) + 1e-9)
        bn = 20 * math.log10(span_rms(bed_n, i0, i1) + 1e-9)
        chk.append(dict(i=d['i'], t=d['t'], dialog_db=round(dm, 1), bed_db=round(bd, 1), bed_unducked_db=round(un, 1),
                        duck_db=round(bd - un, 1) if un > -150 else 0.0, dialog_over_bed_db=round(dm - bd, 1),
                        dialog_over_bed_nomusic_db=round(dm - bn, 1)))
    rep['duck_check'] = chk
    rep['voice_over_bed'] = dict(min_bed=min(c['dialog_over_bed_db'] for c in chk),
                                 median_bed=float(np.median([c['dialog_over_bed_db'] for c in chk])),
                                 min_bed_nomusic=min(c['dialog_over_bed_nomusic_db'] for c in chk), need=A.get('minVoiceOverBedDb', 10.0))
    for nm, x in (('stem_bed', bed), ('stem_bed_nomusic', bed_n), ('stem_sfx', sfx)):
        write_wav24(os.path.join(WORK, nm + '.wav'), x * 0.5)
    json.dump({}, open(os.path.join(WORK, 'meter.json'), 'w'))      # part1: no quote card in this vlog
    rep['master'] = dict(lufs=round(L1, 2), true_peak_db=round(tp1, 2), nomusic_lufs=round(L2, 2), nomusic_true_peak_db=round(tp2, 2),
                         dialog_spans=len(merged), samples=NS, seconds=round(NS / SR, 4))
    json.dump(rep, open(os.path.join(WORK, 'mix.json'), 'w'), indent=1)
    T['stems+report'] = f'{time.time() - t0:.1f}s'
    v = rep['voice_over_bed']
    log(f"mix: {L1:.2f} LUFS TP {tp1:.2f} | no-music {L2:.2f} LUFS TP {tp2:.2f} | voice over bed min {v['min_bed']} dB "
        f"(no-music {v['min_bed_nomusic']}) | " + ', '.join(f'{k} {v_}' for k, v_ in T.items()))


if __name__ == '__main__':
    main()
