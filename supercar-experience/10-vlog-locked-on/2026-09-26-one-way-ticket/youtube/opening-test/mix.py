#!/usr/bin/env python3
"""mix.py -- the opening test's sound, for edl_A.json or edl_B.json -> WORK/mix_<A|B>.wav (-14 LUFS, -1.5 dBTP) + mix_<A|B>.json.

Same chain as ../test-ch3/mix.py (its BS.1770 meter, true-peak limiter, voice chain and IO are imported from there):
  dialog  each dialog piece through the test chapter's voice chain, -16 LUFS, 12 ms fade in, 100 ms fade out.
  nat     talk shots: their own camera sound; the 0117 lines (played over cutaways): 0117's own sound. Every transcribed
          word in it is replaced by its < 250 Hz content (no second voice, the road stays). -24 LUFS, ducked 10 dB under talk.
          Montage shots: their own sound at -30 LUFS (engine / road / wind only), except 0099 and 0122 (car stereo,
          Shazam): muted.
  bed     ../test-ch3/music.py (original synth, 78 BPM), regenerated at the length needed (rounded up to a whole chord + 3 s: music.py's envelope breaks on a
          final chord shorter than its 1.2 s attack). Under talk -39.5 LUFS (as the
          approved chapter), in gaps -21. In B's montage it is up: level set so the FINAL mix sits at MONT_ST LUFS
          short-term, aligned so the montage starts on a chord change (bar 1 of the 2-bar progression) and cuts land on
          beats; the duck is off inside the montage and snaps back (60 ms attack) for CH1.
Master: 30 Hz high-pass, true-peak limiter at -1.8 dBTP (as the chapters: the AAC 320k master lands at or under -1.5),
gain iterated to -14.0 LUFS. `preview` keeps the v1/v2 previews' -2.3 (AAC 192k adds up to 0.5 dB).
Also writes the NO MUSIC mix (dialog + natural sound, same dialog gains, its own -14 LUFS master) -> WORK/nomusic_<name>.wav,
and the voice-over-music margin per word (small.en word windows from /home/user/day-owt/tr), as ../ch3/mix.py.
    python3 mix.py A|B|A2|B2 [preview]
"""
import importlib.util, json, math, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CH3 = os.path.join(HERE, '..', 'test-ch3')
_IIO = '/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
if not os.path.exists(_IIO):
    os.environ.setdefault('FFMPEG', 'ffmpeg')   # test-ch3/mix.py defaults to the imageio build; fall back to the system ffmpeg
spec = importlib.util.spec_from_file_location('ch3mix', os.path.join(CH3, 'mix.py'))
M = importlib.util.module_from_spec(spec)
_cwd = os.getcwd(); os.chdir(CH3); spec.loader.exec_module(M); os.chdir(_cwd)
SR = M.SR
PREVIEW = len(sys.argv) > 2 and sys.argv[2] == 'preview'
# limiter ceiling: the 4K master's AAC 320k adds up to ~0.2 dB (CEIL -1.8, as Ch1-Ch4); the 192k previews added up to 0.5 dB
# (B: -1.2 dBTP at -1.5, -1.49 at -2.0), so `preview` keeps -2.3
M.CEIL = -2.3 if PREVIEW else -1.8
WORK = '/home/user/day-owt/openwork'
NAME = sys.argv[1]
EDL = json.load(open(os.path.join(HERE, f'edl_{NAME}.json')))
FPS = 30000 / 1001
NF = int(round(EDL['duration'] * FPS))
NS = int(round(NF / FPS * SR))
DIALOG_LUFS = -16.0
BED_TALK, BED_GAP = -39.5, -21.0
MONT_ST = -17.0
MONT_BED_V2, MONT_DUCK = -19.0, -23.0   # v2 sound-bite montage: bed level between lines, and its duck under his lines (dB)


def words_of(src, a, b):
    """small.en word windows of `src` (the day index, /home/user/day-owt/tr), as ../ch3/mix.py's per-word margin."""
    t = json.load(open(f'/home/user/day-owt/tr/{src}.json'))
    return [(w[0], w[1], w[2].strip()) for s in t['segments'] for w in s['words']]


def activity(spans, attack=0.06, release=0.4, bridge=0.6):
    a = np.zeros(NS); merged = []
    for s, e in sorted(spans):
        if merged and s - merged[-1][1] < bridge:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    for s, e in merged:
        a[max(0, int((s - attack) * SR)):min(NS, int((e + 0.05) * SR))] = 1
    k = int(release * SR)
    c = np.concatenate([np.zeros(k), np.cumsum(a)])
    return np.maximum(a, (c[k:k + NS] - c[:NS]) / k)


def short_term(x, win=3.0, hop=0.5):
    out = []
    n = int(win * SR)
    for i in range(0, len(x) - n + 1, int(hop * SR)):
        out.append(M.lufs(x[i:i + n]))
    return out


def build_bed(mt):
    os.makedirs(WORK, exist_ok=True)
    seg = 8 * EDL['beat']                  # one chord = 2 bars
    off = (math.ceil(mt / seg) * seg - mt) if mt is not None else 0.0
    path = f'{WORK}/bed_{NAME}.wav'
    subprocess.run([sys.executable, os.path.join(CH3, 'music.py'), path, f'{math.ceil((EDL["duration"] + off + 2) / seg) * seg + 3.0:.2f}'], check=True,
                   capture_output=True)
    x = M.read_wav(path)[int(round(off * SR)):][:NS]
    return np.concatenate([x, np.zeros((NS - len(x), 2))]) if len(x) < NS else x, off


def main():
    rep = {'dialog': [], 'nat': []}
    dia = np.zeros((NS, 2)); spans = []
    for d in EDL['dialog']:
        x = M.aud(d['src'], d['in'], d['out'] + d.get('tail', 0.0), M.CHAIN)
        m = x.mean(1)
        for bl in EDL.get('bleeps', []):      # v2: a 1 kHz tone over the word, as ../test-ch3/mix.py
            if bl['src'] == d['src'] and d['in'] < bl['out'] and bl['in'] < d['out']:
                i0 = int((max(bl['in'], d['in']) - d['in']) * SR); i1 = int((min(bl['out'], d['out']) - d['in']) * SR)
                rms = np.sqrt((m[max(0, i0 - SR // 2):i1 + SR // 2] ** 2).mean())
                tone = np.sin(2 * np.pi * 1000 * np.arange(i1 - i0) / SR) * rms * 1.2
                r = int(0.005 * SR)
                tone[:r] *= M.ramp(r); tone[-r:] *= M.ramp(r, False)
                m[i0:i1] = tone
                rep.setdefault('bleeps', []).append(dict(src=d['src'], word=bl.get('word'), t=round(d['t'] + i0 / SR, 2)))
        x = np.stack([m, m], 1)
        g = 10 ** ((DIALOG_LUFS - M.lufs(x)) / 20)
        M.place(dia, M.fades(x * g, 0.012, 0.1), d['t'])
        spans.append((d['t'], d['t'] + d['out'] - d['in']))
        rep['dialog'].append(dict(src=d['src'], **{'in': d['in']}, out=d['out'], t=d['t'], gain_db=round(20 * math.log10(g), 1)))
    mt = EDL.get('montage_t')
    mont = [s for s in EDL['shots'] if s['kind'] == 'montage']
    m0, m1 = (mt, mont[-1]['t'] + mont[-1]['dur']) if mont else (None, None)
    act = activity(spans, attack=0.15) if EDL.get('montage_duck') else activity(spans)   # v2: duck lands before each bite
    V2 = EDL.get('montage_duck', False)
    if mont and not V2:
        act[int(m0 * SR):int(m1 * SR) - int(0.06 * SR)] = 0      # no duck inside the montage (v1); v2 ducks under his lines
    nat = np.zeros((NS, 2)); natm = np.zeros((NS, 2))
    segs = [(s['src'], s['in'], s['out'], s['t'], s['nat'], s['kind']) for s in EDL['shots'] if s['nat'] is not None]
    segs += [(e['src'], e['in'], e['out'] + e.get('tail', 0.0), e['t'], e['lufs'], 'talk') for e in EDL['audio_extra'] if e['kind'] == 'nat']
    for src, a, b, t, lv, kind in segs:
        M.place(natm if kind == 'montage' else nat, M.nat_seg(src, a, b, lv), t)
        rep['nat'].append(dict(src=src, **{'in': a}, out=b, t=t, lufs=lv))
    nat *= (1 - act * (1 - 10 ** (-10 / 20)))[:, None]
    nat += natm
    bed, off = build_bed(mt)
    bed *= 10 ** ((BED_GAP - M.lufs(bed)) / 20)
    g = 1 - act * (1 - 10 ** ((BED_TALK - BED_GAP) / 20))
    if mont and V2:     # v2 montage: the bed is up between lines and ducks only MONT_DUCK under them (a trailer keeps the music)
        menv = np.zeros(NS); menv[int(m0 * SR):int(m1 * SR)] = 1
        gm = 1 - act * (1 - 10 ** (MONT_DUCK / 20))
        g = g * (1 - menv) + gm * menv
    e = int(1.2 * SR); g[NS - e:] *= M.ramp(e, False)
    bed_d = bed * g[:, None]

    def assemble(mont_gain_db):
        b = bed_d.copy()
        if mont:
            env = np.zeros(NS); i0, i1, r = int(m0 * SR), int(m1 * SR), int(0.08 * SR)
            env[i0:i1] = 1; env[i0:i0 + r] = M.ramp(r); env[i1 - r:i1] = M.ramp(r, False)
            b *= (1 + env * (10 ** (mont_gain_db / 20) - 1))[:, None]
        return dia + nat + b, b

    mg = 0.0
    if V2:
        mg = MONT_BED_V2 - BED_GAP     # fixed: the montage bed sits at MONT_BED_V2 (pre-master) between lines
    for _ in range(0 if V2 else 4):
        mix, b = assemble(mg)
        y, L, tp = M.master(mix)
        if not mont:
            break
        st = short_term(y[int(m0 * SR):int(m1 * SR)])
        cur = float(np.median(st))
        if abs(cur - MONT_ST) < 0.3:
            break
        mg += MONT_ST - cur
    if V2:
        mix, b = assemble(mg)
        y, L, tp = M.master(mix)
    rep['bed'] = dict(source='../test-ch3/music.py (original, synthesized here), 78 BPM', talk_lufs=BED_TALK, gap_lufs=BED_GAP,
                      offset_s=round(off, 3), montage=[m0, m1], montage_boost_db=round(mg, 2))
    if mont:
        st = short_term(y[int(m0 * SR):int(m1 * SR)])
        rep['montage_short_term_lufs'] = dict(median=round(float(np.median(st)), 1), min=round(min(st), 1), max=round(max(st), 1))
    # voice over music on every voiced 50 ms frame (as test-ch3)
    margins = []; h = int(0.05 * SR)
    for d in EDL['dialog']:
        i0, i1 = int(d['t'] * SR), int((d['t'] + d['out'] - d['in']) * SR)
        fr = [(k, 10 * np.log10((dia[k:k + h] ** 2).mean() + 1e-12), 10 * np.log10((b[k:k + h] ** 2).mean() + 1e-12))
              for k in range(i0, i1 - h, h)]
        top = max(v for _, v, _ in fr)
        margins += [(round(v - m, 1), d['src'], round(d['in'] + (k - i0) / SR, 2)) for k, v, m in fr if v > top - 15 and v > -40]
    # per word (as ../ch3/mix.py): small.en word windows; mean power of the voiced frames inside the word vs the bed
    wm = []
    for d in EDL['dialog']:
        fr = [m for m in margins if m[1] == d['src'] and d['in'] - 0.01 <= m[2] <= d['out']]
        for w0, w1, txt in words_of(d['src'], d['in'], d['out']):
            if w0 >= d['out'] or w1 <= d['in']:
                continue
            ks = [int((d['t'] + m[2] - d['in']) * SR) for m in fr if w0 - 0.05 <= m[2] < w1]
            if not ks:
                continue
            v = np.mean([(dia[k:k + h] ** 2).mean() for k in ks]); bb = np.mean([(b[k:k + h] ** 2).mean() for k in ks])
            wm.append((round(10 * np.log10((v + 1e-12) / (bb + 1e-12)), 1), d['src'], round(w0, 2), txt))
    wm.sort()
    rep['voice_over_music_words_db'] = dict(min=wm[0][0] if wm else None, words=len(wm), under_12=[w for w in wm if w[0] < 12],
                                            lowest5=wm[:5])
    margins.sort()
    rep['voice_over_music_db'] = dict(min=margins[0][0], frames=len(margins), under_10=[m for m in margins if m[0] < 10][:20])
    M.write_wav24(f'{WORK}/mix_{NAME}.wav', y)
    rep['master'] = dict(lufs=round(L, 2), true_peak=round(tp, 2), ceil=M.CEIL)
    yn, Ln, tpn = M.master(dia + nat)      # NO MUSIC: the same dialog and natural-sound buses, no bed, its own -14 LUFS master
    M.write_wav24(f'{WORK}/nomusic_{NAME}.wav', yn)
    rep['nomusic'] = dict(lufs=round(Ln, 2), true_peak=round(tpn, 2), ceil=M.CEIL)
    json.dump(rep, open(f'{WORK}/mix_{NAME}.json', 'w'), indent=1)
    print(json.dumps({'name': NAME, 'master': rep['master'], 'nomusic': rep['nomusic'],
                      'word_min_db': rep['voice_over_music_words_db']['min'], 'words': rep['voice_over_music_words_db']['words'], 'montage_st': rep.get('montage_short_term_lufs'),
                      'boost_db': rep['bed']['montage_boost_db'], 'voice_over_music_min_db': rep['voice_over_music_db']['min'],
                      'under_10': len(rep['voice_over_music_db']['under_10'])}))


if __name__ == '__main__':
    main()
