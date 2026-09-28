#!/usr/bin/env python3
"""audiocheck.py -- the v2.4 sound checks on the finished mix (run by build.py --stage qa; or on its own after the audio
stage). Writes exports/qa/audio_v24.json.

  1. voice level: the voice-only loudness (DeepFilterNet3 voice of the dialog stem, BS.1770) of every piece of the clip
     that had the alarm, against the same clip's clean pieces. Pass: each cleaned piece within `tol` dB of the mean of
     the clean ones (the lineup was 1-6 dB low in v2 because it was levelled with the alarm counted as voice).
  2. accents: every Locked-On accent inside the cleaned stretch (the lock ticks, the sweep whoosh) keeps its full
     energy in the alarm bands. The accent's own sound (pack file x its mix gain) is projected out of the master in the
     alarm bands and in a reference band (1-2 kHz); pass when the two gains agree within 1 dB (a notch on the accents
     would pull the alarm-band gain down; v2.2 lost 10+ dB there).
  3. alarm residue: in the dialog stem, the alarm bands' level against their neighbouring bands over each cleaned
     piece, next to the same measure on the clean pieces.
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from cfg import load_config  # noqa: E402

C = load_config()
P = C['paths']
FF = os.environ.get('FFMPEG', P['ffmpeg'])
WORK = os.path.join(ROOT, '.work')
QA = os.path.join(ROOT, 'exports', 'qa')
SR = 48000
REF_BAND = (1000, 2000)


def read(p):
    raw = subprocess.run([FF, '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, '<f4').reshape(-1, 2).astype(np.float64)


def bandpass(x, lo, hi):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x), axis=0)


def band_level(x, lo, hi):
    X = np.fft.rfft(x.mean(1)); f = np.fft.rfftfreq(len(x), 1 / SR)
    return 10 * np.log10((np.abs(X[(f >= lo) & (f <= hi)]) ** 2).mean() + 1e-20)


def main(tol=1.0):
    cfg = C['audio'].get('dealarm') or {}
    mix = json.load(open(os.path.join(WORK, 'mix.json')))
    edl = json.load(open(P['edl']))
    out = {'tol_db': tol}
    # ---------------------------------------------------------------- 1. voice level
    pieces, cleaned = [], []
    for sp in cfg.get('spans', []):
        for d in mix['dialog']:
            if d['src'] != sp['src'] or d['i'] >= len(edl['dialog']):
                continue
            inside = d['a'] >= sp['a'] - 0.03 and d['b'] <= sp['b'] + 0.03
            is_ref = any(abs(d['a'] - r0) < 0.3 and abs(d['b'] - r1) < 0.3 for r0, r1 in sp.get('refs', []))
            if inside or is_ref:
                pieces.append(dict(i=d['i'], t0=d['t'], t1=round(d['t'] + d.get('dur', d['b'] - d['a']), 3), cleaned=inside))
                if inside:
                    cleaned.append(d['i'])
    if pieces and P.get('dfnPython') and os.path.exists(P['dfnPython']):
        job = os.path.join(WORK, 'audiocheck_voice.json')
        res = os.path.join(WORK, 'audiocheck_voice_out.json')
        json.dump(dict(stem=os.path.join(WORK, 'stem_dialog.wav'), gain=2.0, pieces=pieces, out=res), open(job, 'w'))
        subprocess.run([P['dfnPython'], os.path.join(HERE, 'dealarm_dfn.py'), 'voice', job], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        r = json.load(open(res))
        refs = [p['voice_lufs'] for p in r if not p['cleaned']]
        m = float(np.mean(refs))
        for p in r:
            p['vs_clean_mean_db'] = round(p['voice_lufs'] - m, 2)
        ok = all(abs(p['vs_clean_mean_db']) <= tol for p in r if p['cleaned'])
        out['voice_level'] = dict(pieces=r, clean_mean_lufs=round(m, 2), pass_=ok)
    else:
        out['voice_level'] = dict(skipped='no dealarm spans or no DeepFilterNet venv (paths.dfnPython)')
    # ---------------------------------------------------------------- 2. accents in the alarm bands
    master = read(os.path.join(WORK, 'mix.wav'))
    t_lo = min((p['t0'] for p in pieces if p['cleaned']), default=None)
    t_hi = max((p['t1'] for p in pieces if p['cleaned']), default=None)
    acc = []
    if t_lo is not None:
        cues = json.load(open(os.path.join(WORK, 'sfx_cues.json')))
        gains = {(s['file'], round(s['t'], 3)): s['gain_db'] for s in mix['sfx']}
        for c in cues:
            if not (t_lo - 0.5 <= c['t'] <= t_hi + 0.5):
                continue
            y = read(os.path.join(ROOT, P['sfx'], c['file']))
            if c.get('dur'):
                y = y[:int(c['dur'] * SR)]
            t = c['t'] - c.get('align', 0.0) * len(y) / SR
            i0 = int(round(t * SR)); n = min(len(y), len(master) - i0)
            g = 10 ** (gains.get((c['file'], round(c['t'], 3)), 0.0) / 20)
            y = y[:n] * g; mseg = master[i0:i0 + n]
            row = dict(file=c['file'], t=c['t'], why=c.get('why', ''))
            for nm, (lo, hi) in [('ref', REF_BAND)] + [(f'{lo}-{hi}', (lo, hi)) for lo, hi in cfg.get('bands', [])]:
                yb, mb = bandpass(y, lo, hi), bandpass(mseg, lo, hi)
                k = float((yb * mb).sum() / max((yb * yb).sum(), 1e-20))
                row[f'gain_{nm}'] = round(k, 3)
            row['alarm_band_vs_ref_db'] = [round(20 * np.log10(max(row[f'gain_{lo}-{hi}'], 1e-6) / max(row['gain_ref'], 1e-6)), 2)
                                           for lo, hi in cfg.get('bands', [])]
            row['pass_'] = all(abs(v) <= 1.0 for v in row['alarm_band_vs_ref_db'])
            acc.append(row)
    out['accents'] = dict(cues=acc, pass_=all(r['pass_'] for r in acc) if acc else None)
    # ---------------------------------------------------------------- 3. alarm residue in the dialog stem
    stem = read(os.path.join(WORK, 'stem_dialog.wav'))
    res = []
    for p in pieces:
        x = stem[int(p['t0'] * SR):int(p['t1'] * SR)]
        row = dict(i=p['i'], cleaned=p['cleaned'])
        for (lo, hi), (l0, l1), (r0, r1) in cfg.get('clamps', []):
            nb = 10 * np.log10(0.5 * (10 ** (band_level(x, l0, l1) / 10) + 10 ** (band_level(x, r0, r1) / 10)))
            row[f'{lo}-{hi}_over_neighbours_db'] = round(float(band_level(x, lo, hi) - nb), 2)
        res.append(row)
    out['alarm_residue'] = res
    os.makedirs(QA, exist_ok=True)
    json.dump(out, open(os.path.join(QA, 'audio_v24.json'), 'w'), indent=1)
    vl = out['voice_level']
    if 'pieces' in vl:
        print('voice level: ' + ', '.join(f"piece {p['i']} {p['voice_lufs']:.2f}{' (cleaned)' if p['cleaned'] else ''} {p['vs_clean_mean_db']:+.2f}"
                                          for p in vl['pieces']) + f" | pass {vl['pass_']}")
    print('accents: ' + ', '.join(f"{r['why']} {r['t']} {r['alarm_band_vs_ref_db']}" for r in acc) + f" | pass {out['accents']['pass_']}")
    print('alarm residue: ' + ', '.join(f"piece {r['i']} " + '/'.join(str(v) for k, v in r.items() if k.endswith('_db')) for r in res))
    return out


if __name__ == '__main__':
    main()
