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
TR = '/tmp/claude-0/-home-user-UIUX/367d87e8-d068-53b7-8f18-ebc5dc9cdf69/scratchpad/days/trip-0926/tr'

# (clip, words as whisper small.en wrote them) -> words to show; times are re-spread over the matched span
FIX = {
    '0076': [(['a', 'super', 'car', 'experience', 'vlog.'], ['our', 'Supercar', 'Experience', 'vlog.'],
              'medium.en: "this is our supercar experience vlog"; the brand is one word'),
             (['this.'], ['us.'], 'medium.en: "look at us."')],
    '0077': [(['treated'], ['treating', 'you'], 'medium.en: "Seattle\'s treating you well today"')],
    '0079': [],
    '0087': [(['you', 'doing?'], ['How', 'you', 'doing?'], 'medium.en: "How you doing?" (small.en ran "How you" into one word)'),
             (['got', 'to'], ['gotta'], 'medium.en: "I gotta drive it"')],
    '0090': [(['600lt'], ['600LT'], 'spelling')],
    '0094': [(['y', "'all"], ["y'all"], 'one word')],
    '0102': [(['OT'], ['LT'], 'the car is the 600LT (Omarie, 6 Oct); medium.en also heard LT'),
             (['red', 'bull'], ['Red', 'Bull'], 'spelling'),
             (['In', 'and', 'out'], ['In-N-Out'], 'the restaurant (Part 2 stops there); medium.en: "In-N-Out"')],
}
# pieces whose first word starts a hair before the cut's in-point (the word is in the audio of the piece)
LEAD = {}


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
        ws = apply_fix(d['src'], words_of(d['src'], a, d['out']), used)
        caps.append(dict(src=d['src'], **{'in': d['in']}, out=d['out'], t=d['t'],
                         words=[[round(d['t'] + w[0] - d['in'], 3), round(d['t'] + w[1] - d['in'], 3), w[2]] for w in ws]))
    json.dump(caps, open(os.path.join(ROOT, 'data', 'captions.json'), 'w'), indent=1)
    json.dump(used, open(os.path.join(ROOT, 'data', 'caption_fixes.json'), 'w'), indent=1)
    for c in caps:
        print(f"{c['t']:7.2f} {c['src']} " + ' '.join(w[2] for w in c['words']))
    print(len(used), 'fixes applied')


if __name__ == '__main__':
    main()
