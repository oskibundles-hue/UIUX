#!/usr/bin/env python3
"""words_agree_B2.py -- the caption words for the B2 opening (as ../ch3/words_agree.py): only words both ASR models hear
(small.en, the day index in /home/user/day-owt/tr, and medium.en, words_medium_B2.json from words_b2.py), per edl_B2.json
dialog piece, with timeline-relative times -> words_agree_B2.json. Words are matched in order (difflib on normalised
text) and must start within 0.6 s of each other; the time is the mean of the two models, clipped to the piece. A word
inside an edl_B2.json bleep (0106 182.6-182.92, 183.66-184.32) is left out, because the sound bleeps it. The words only
one model hears are listed per piece (`disagree`), for the lead.
    python3 words_agree_B2.py
"""
import difflib, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
edl = json.load(open(os.path.join(HERE, 'edl_B2.json')))
med = json.load(open(os.path.join(HERE, 'words_medium_B2.json')))


def norm(w):
    return re.sub(r"[^a-z0-9']", '', w.lower())


def small(src):
    t = json.load(open(f'/home/user/day-owt/tr/{src}.json'))
    return [(w[0], w[1], w[2].strip()) for s in t['segments'] for w in s['words']]


def medium(src, a, b):
    for k, ws in med.items():
        s, r = k.split(':'); r0, r1 = (float(v) for v in r.split('-'))
        if s == src and r0 <= a + 1e-3 and b <= r1 + 1e-3:
            return [tuple(w) for w in ws]
    return None     # not transcribed yet (words_b2.py): the piece is listed under `missing`, with no caption words


def bleeped(src, t):
    return any(bp['src'] == src and bp['in'] <= t < bp['out'] for bp in edl.get('bleeps', []))


out, stats, gaps, missing = [], [], [], []
for d in edl['dialog']:
    a, b = d['in'], d['out']
    S = [w for w in small(d['src']) if a - 0.05 <= w[0] < b]
    Mall = medium(d['src'], a, b)
    if Mall is None:
        missing.append(dict(src=d['src'], **{'in': a}, out=b, t=round(d['t'], 2), small=' '.join(w[2] for w in S)))
        stats.append(f"{d['src']} {a}: small {len(S)} medium MISSING"); continue
    M = [w for w in Mall if a - 0.05 <= w[0] < b]
    sm = difflib.SequenceMatcher(a=[norm(w[2]) for w in S], b=[norm(w[2]) for w in M], autojunk=False)
    n, used_s, used_m = 0, set(), set()
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            ws, wm = S[blk.a + k], M[blk.b + k]
            if not norm(ws[2]) or abs(ws[0] - wm[0]) > 0.6:
                continue
            used_s.add(blk.a + k); used_m.add(blk.b + k)
            if bleeped(d['src'], (ws[0] + wm[0]) / 2):
                continue
            t0 = max(a, (ws[0] + wm[0]) / 2); t1 = min(b, max(t0 + 0.05, (ws[1] + wm[1]) / 2))
            out.append(dict(t0=round(d['t'] + t0 - a, 3), t1=round(d['t'] + t1 - a, 3), word=wm[2], src=d['src'], src_t=round(t0, 2)))
            n += 1
    only_s = [w[2] for i, w in enumerate(S) if i not in used_s and not bleeped(d['src'], w[0])]
    only_m = [w[2] for i, w in enumerate(M) if i not in used_m and not bleeped(d['src'], w[0])]
    if only_s or only_m:
        gaps.append(dict(src=d['src'], **{'in': a}, out=b, t=round(d['t'], 2), small=' '.join(w[2] for w in S),
                         medium=' '.join(w[2] for w in M), only_small=only_s, only_medium=only_m))
    stats.append(f"{d['src']} {a}: small {len(S)} medium {len(M)} agree {n}")
out.sort(key=lambda w: w['t0'])
json.dump(dict(note='B2 opening caption words both small.en and medium.en hear; t0/t1 are opening-timeline seconds',
               duration=edl['duration'], words=out, disagree=gaps, missing=missing), open(os.path.join(HERE, 'words_agree_B2.json'), 'w'), indent=0)
print('\n'.join(stats)); print('agreed words', len(out))
for g in missing:
    print(f"MISSING medium.en {g['src']} {g['in']}-{g['out']} (t {g['t']}): small hears {g['small']!r}")
for g in gaps:
    print(f"DISAGREE {g['src']} {g['in']} (t {g['t']}): small-only {g['only_small']} medium-only {g['only_medium']}")
