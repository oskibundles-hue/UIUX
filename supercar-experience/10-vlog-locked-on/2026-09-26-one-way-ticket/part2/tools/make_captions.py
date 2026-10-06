#!/usr/bin/env python3
"""make_captions.py -- data/captions.json (H1 boxed captions) from the day's word timings and data/edl.json.

Words and their timings are faster-whisper small.en's (days/trip-0926/tr/<clip>.json, the day index). Every piece in
the cut was transcribed a second time with medium.en (beam 5); where the two disagree, FIX below carries the reading
used, with the reason. Fixes only re-spell or re-split words that are in the audio; nothing is added that he does not
say. A word is kept when 0.15 s of it lies inside the piece [in, out) (see words_of). Timeline time = piece t + (word time - in).
    python3 tools/make_captions.py [--tr DIR]
"""
import argparse, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TR = '/tmp/claude-0/p2day/tr'

# (clip, words as whisper small.en wrote them) -> words to show; times are re-spread over the matched span
FIX = {
    '0105': [(['it.', 'To', 'In', '-N', '-Out.'], ['it', 'to', 'In-N-Out.'], 'medium.en: "We finally made it to In-N-Out." (one sentence; the restaurant\'s spelling)')],
    '0118': [(['Wow,'], [], 'medium.en does not hear "Wow" ("It\'s been pretty fire, really nice scenery"): not captioned'),
             (['trip'], ['Trip'], 'sentence start')],
    '0112': [(['We', 'are', 'gassed', 'up,'], ['We', 'are', 'gassed', 'up,'], 'both models'),
             (['here,', 'and'], ['here.'], 'fix A tail: medium.en does not hear the trailing "and" (a breath): not captioned')],
    '0111': [(['It\'s', 'a', 'McLaren'], ['It\'s', 'a', 'McLaren.'], 'punctuation'),
             (['like', 'that\'s'], ['like,', 'that\'s'], 'punctuation')],
}   # PART2_FIX: every piece in the cut was re-run with medium.en (beam 5); only pieces whose words both models share are in the cut
OVERRIDE = {}
LEAD = {}
PIN = {}
# round 1 (6 Oct): four pages sat +220 to +300 ms off the speech (build.py caption_sync, the gate's own measure: the
# speech-band energy of the dialog stem lands that much after small.en's word times). Every word of the piece moves by
# the shift that brings the gate's lag to within +/-30 ms (searched in 50 ms steps on the round-1 stem).
SHIFT = {('0111', 54.70): +0.22, ('0115', 10.35): +0.40, ('0116', 121.25): +0.40, ('0117', 100.80): +0.25}


def words_of(clip, a, b):
    t = json.load(open(os.path.join(TR, f'{clip}.json')))
    out = []
    for s in t['segments']:
        for w in s['words']:
            # a word is shown when at least 0.15 s of it is inside the piece (whisper stretches a word over the pause
            # before it, so a start slightly before `in` is normal), or it starts inside and not in the last 0.1 s
            ov = min(w[1], b) - max(w[0], a)
            if ov >= 0.15 or (a - 1e-6 <= w[0] < b - 0.1):
                out.append([max(w[0], a), min(w[1], b), w[2].strip()])
    return out


def apply_fix(clip, ws, used):
    for src, dst, why in FIX.get(clip, []):
        n = len(src)
        i = 0
        while i + n <= len(ws):
            if [w[2] for w in ws[i:i + n]] == src:
                a, b = ws[i][0], ws[i + n - 1][1]
                if not dst:   # a word that is dropped, not captioned
                    del ws[i:i + n]
                    used.append(dict(clip=clip, at=round(a, 2), whisper=' '.join(src), shown='(dropped)', why=why))
                    continue
                step = (b - a) / len(dst)
                new = [[round(a + k * step, 3), round(a + (k + 1) * step, 3), d] for k, d in enumerate(dst)]
                ws[i:i + n] = new
                used.append(dict(clip=clip, at=round(a, 2), whisper=' '.join(src), shown=' '.join(dst), why=why))
                i += len(dst)
            else:
                i += 1
    return ws


def main():
    global TR
    ap = argparse.ArgumentParser()
    ap.add_argument('--tr', default=TR)
    A = ap.parse_args()
    TR = A.tr
    edl = json.load(open(os.path.join(ROOT, 'data', 'edl.json')))
    caps, used = [], []
    for d in edl['dialog']:
        a = LEAD.get((d['src'], d['in']), d['in'])
        ov = OVERRIDE.get((d['src'], d['in']))
        if ov:
            ws = [list(w) for w in ov]
            used.append(dict(clip=d['src'], at=ov[0][0], whisper='(piece rewritten)', shown=' '.join(w[2] for w in ov),
                             why='wording settled by the lead (6 Oct); timings from medium.en / small.en, see OVERRIDE'))
        else:
            # fix A: the out-point sits >= 350 ms after the last word; captions stop at that word (make_edl.py tail)
            ws = apply_fix(d['src'], words_of(d['src'], a, d.get('last_word_end', d['out']) + 0.01), used)
            pin = PIN.get((d['src'], d['in']))
            if pin:
                ws[0][0], ws[0][1] = pin
                ws[1][0] = max(ws[1][0], pin[1])
        sh = SHIFT.get((d['src'], round(d['in'], 2)), 0.0)
        ws = [[w[0] + sh, w[1] + sh, w[2]] for w in ws]
        caps.append(dict(src=d['src'], **{'in': d['in']}, out=d['out'], t=d['t'],
                         words=[[round(d['t'] + w[0] - d['in'], 3), round(d['t'] + w[1] - d['in'], 3), w[2]] for w in ws]))
    json.dump(caps, open(os.path.join(ROOT, 'data', 'captions.json'), 'w'), indent=1)
    json.dump(used, open(os.path.join(ROOT, 'data', 'caption_fixes.json'), 'w'), indent=1)
    for c in caps:
        print(f"{c['t']:7.2f} {c['src']} " + ' '.join(w[2] for w in c['words']))
    print(len(used), 'fixes applied')


if __name__ == '__main__':
    main()
