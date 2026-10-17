#!/usr/bin/env python3
"""onsets.py -- Part 1 v2, fix A helper: where does the voice really stop after each dialog piece, and where does the next
word really start? Whisper's word ends sit early and its next-word starts stretch back over the pause, so the tail is
checked on the clip audio itself: the voice-band (300-3400 Hz) envelope of paths.aud/<clip>.m4a at 10 ms, from the
piece's last word (small.en) to 3 s past it. Prints, per piece: the last word end of both models, both models' next word,
the measured end of voice (the envelope falls 12 dB under the last word's peak and stays down 120 ms) and the measured
next onset (the envelope rises 12 dB over the gap floor for 60 ms). make_edl.py NEXT_ONSET takes the measured onset
where the models crowd the tail.
    python3 tools/onsets.py
"""
import json, os, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from cfg import load_config  # noqa: E402
C = load_config()
SR = 16000


def env(src, a, b):
    raw = subprocess.run([C['paths']['ffmpeg'], '-v', 'error', '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i',
                          os.path.join(C['paths']['aud'], f'{src}.m4a'), '-af', 'highpass=f=300,lowpass=f=3400',
                          '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, '<f4').astype(np.float64)
    hop = SR // 100
    return np.array([20 * np.log10(np.sqrt((x[k:k + hop] ** 2).mean()) + 1e-9) for k in range(0, len(x) - hop, hop)])


def measure(src, le, nxt_hint):
    a = le - 0.6
    e = env(src, a, le + 3.0)
    i_le = int(0.6 * 100)
    pk = e[max(0, i_le - 40):i_le + 2].max()
    end = None
    for i in range(i_le - 10, len(e) - 12):
        if (e[i:i + 12] < pk - 12).all():
            end = a + i / 100; break
    on = None
    if end is not None:
        j0 = int((end - a) * 100)
        lim = min(len(e), j0 + 300)
        fl = np.percentile(e[j0:lim], 10)
        for i in range(j0 + 3, lim - 6):
            if (e[i:i + 6] > fl + 12).all():
                on = a + i / 100; break
    return end, on


def main():
    edl = json.load(open(C['paths']['edl']))
    med = json.load(open(os.path.join(ROOT, 'data', 'words_medium.json')))
    print(f"{'i':>2} {'src':4} {'in':>7} {'le_sm':>7} {'le_md':>7} {'nx_sm':>7} {'nx_md':>7} {'v_end':>7} {'v_on':>7}  next words")
    for i, d in enumerate(edl['dialog']):
        b = d.get('out_asr', d['out'])
        t = json.load(open(os.path.join(C['paths']['transcripts'], f"{d['src']}.json")))
        sm = [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]
        md = [[w[0], w[1], w[2].strip()] for w in med.get(f"{d['src']}:{d['in']:.2f}", [])]
        ins = lambda w: min(w[1], b) - max(w[0], d['in']) >= 0.15 or (d['in'] - 1e-6 <= w[0] < b - 0.1)
        ps, pm = [w for w in sm if ins(w)], [w for w in md if ins(w)]
        le = ps[-1][1]
        ns = [w for w in sm if w[0] > ps[-1][0] + 0.01 and not ins(w)]
        nm = [w for w in md if pm and w[0] > pm[-1][0] + 0.01 and not ins(w)]
        end, on = measure(d['src'], le, None)
        f = lambda v: f'{v:7.2f}' if v is not None else '      -'
        print(f"{i:2d} {d['src']} {d['in']:7.2f} {f(le)} {f(pm[-1][1] if pm else None)} {f(ns[0][0] if ns else None)} "
              f"{f(nm[0][0] if nm else None)} {f(end)} {f(on)}  {' '.join(w[2] for w in ns[:3])} | {' '.join(w[2] for w in nm[:3])}")


if __name__ == '__main__':
    main()
