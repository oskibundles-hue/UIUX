#!/usr/bin/env python3
"""words_agree.py -- the caption words for Chapter 8 (copy of ../ch4/words_agree.py): only words both ASR models hear (small.en, the day index in
/home/user/day-owt/tr, and medium.en, words_medium.json), per edl.json dialog piece, with chapter-relative times
-> words_agree.json. Words are matched in order (difflib on normalised text) and must start within 0.6 s of each other;
the time is the mean of the two models, clipped to the piece. Spoken figures are kept as spoken (captions only).
    python3 words_agree.py
"""
import difflib, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
edl = json.load(open(os.path.join(HERE, 'edl.json')))
med = json.load(open(os.path.join(HERE, 'words_medium.json')))


def norm(w):
    return re.sub(r"[^a-z0-9']", '', w.lower())


def small(src):
    t = json.load(open(f'/home/user/day-owt/tr/{src}.json'))
    return [(w[0], w[1], w[2].strip()) for s in t['segments'] for w in s['words']]


out, stats, gaps = [], [], []
for d in edl['dialog']:
    a, b = d['in'], d['out']
    S = [w for w in small(d['src']) if a - 0.05 <= w[0] < b]
    M = [tuple(w) for w in med.get(f"{d['src']}:{d['in']:.2f}", []) if a - 0.05 <= w[0] < b]
    sm = difflib.SequenceMatcher(a=[norm(w[2]) for w in S], b=[norm(w[2]) for w in M], autojunk=False)
    n = 0
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            ws, wm = S[blk.a + k], M[blk.b + k]
            if not norm(ws[2]) or abs(ws[0] - wm[0]) > 0.6:
                continue
            t0 = max(a, (ws[0] + wm[0]) / 2); t1 = min(b, max(t0 + 0.05, (ws[1] + wm[1]) / 2))
            out.append(dict(t0=round(d['t'] + t0 - a, 3), t1=round(d['t'] + t1 - a, 3), word=wm[2], src=d['src'], src_t=round(t0, 2)))
            n += 1
    got = {round(w['src_t'], 2) for w in out if w['src'] == d['src']}
    miss = [w for w in S if not any(abs(max(a, w[0]) - g) < 0.65 for g in got)]
    gaps.extend(dict(t=round(d['t'] + max(a, w[0]) - a, 2), src=d['src'], src_t=w[0], small=w[2]) for w in miss)
    stats.append(f"{d['src']} {a}: small {len(S)} medium {len(M)} agree {n}")
out.sort(key=lambda w: w['t0'])
json.dump(dict(note='Chapter 8 caption words both small.en and medium.en hear; t0/t1 are chapter seconds',
               duration=edl['duration'], words=out, gaps=gaps), open(os.path.join(HERE, 'words_agree.json'), 'w'), indent=0)
print('\n'.join(stats)); print('agreed words', len(out))
for g in gaps:
    print(f"GAP {g['t']:7.2f}  {g['src']} {g['src_t']:.2f}  small.en '{g['small']}' (medium.en differs)")
