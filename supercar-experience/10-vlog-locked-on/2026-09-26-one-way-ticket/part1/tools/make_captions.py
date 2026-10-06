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
    '0076': [(['That\'s'], [], 'piece 2 now opens in the pause before it (25.25 s): the word before "a little tired" is "I was" in medium.en '
                              'and "That\'s" in small.en / base.en, so it is not captioned (never a word the two models do not share)'),
             (['a', 'super', 'car', 'experience', 'vlog.'], ['a', 'Supercar', 'Experience', 'vlog.'],
              'two clean ASR passes on the source (0076 around 46 s) and one on the delivered audio all hear "this is a Supercar Experience vlog" (7 Oct, nq-second); the brand is one word'),
             (['this.'], ['us.'], 'medium.en: "look at us."')],
    # 0077 "Seattle's ... well today" is not in the cut (its middle word is unconfirmed: the day index says "treated",
    # medium.en and small.en say "training", the lead heard "treating you"), so it needs no fix here
    '0079': [],
    '0087': [(['you', 'doing?'], ['How', 'you', 'doing?'], 'medium.en: "How you doing?" (small.en ran "How you" into one word)'),
             (['got', 'to'], ['gotta'], 'medium.en: "I gotta drive it"')],
    '0089': [(['finna'], ['gonna'], 'medium.en (four runs) and small.en: "he\'s gonna go grab the 600 LT"; the day index said finna')],
    '0090': [(['600lt'], ['600LT'], 'spelling')],
    '0094': [(['y', "'all"], ["y'all"], 'one word')],
    '0102': [(['OT'], ['LT'], 'the car is the 600LT (Omarie, 6 Oct); medium.en also heard LT'),
             (['red', 'bull'], ['Red', 'Bull'], 'spelling'),
             (['In', 'and', 'out'], ['In-N-Out'], 'the restaurant (Part 2 stops there); medium.en: "In-N-Out"')],
}
# whole pieces whose captions are written word by word, [source start, source end, word] (source seconds, the piece's own
# clip). Used where the models disagree on the wording and the lead settled the text (6 Oct): 0094 2.34-9.06,
# "I want y'all to, you know what I'm saying, get the vibes, so you feel me. We gon' catch the vibes right now."
# Timings: medium.en's for the words it hears; small.en's for "you know what I'm saying" and "so you feel me", which
# medium.en does not transcribe (the day index and small.en agree on where they sit); the rest between the two.
OVERRIDE = {
    ('0094', 2.34): [
        [2.37, 2.71, 'I'], [2.71, 2.91, 'like'], [2.91, 3.23, 'it.'],
        [3.61, 3.66, 'I'], [3.66, 3.80, 'want'], [3.80, 4.01, "y'all"], [4.01, 4.08, 'to,'],
        [4.08, 4.28, 'you'], [4.28, 4.44, 'know'], [4.44, 4.60, 'what'], [4.60, 4.68, "I'm"], [4.68, 4.78, 'saying,'],
        [4.78, 4.96, 'get'], [4.96, 5.06, 'the'], [5.06, 5.40, 'vibes,'],
        [5.52, 5.74, 'so'], [5.74, 5.96, 'you'], [5.96, 6.18, 'feel'], [6.18, 6.64, 'me.'],
        [6.66, 7.20, 'We'], [7.20, 7.70, "gon'"], [7.74, 8.17, 'catch'], [8.17, 8.32, 'the'], [8.32, 8.60, 'vibes'],
        [8.60, 8.72, 'right'], [8.72, 9.03, 'now.'],
    ],
}
# pieces whose first word starts a hair before the cut's in-point (the word is in the audio of the piece)
LEAD = {('0093', 4.42): 3.86}
# first word pinned inside the pause-start of a piece: (src, in) -> (start, end, next word's start). 0093 now opens in the
# pause before "It is beautiful": the day index stretches "It" over the pause (3.89-4.41); medium.en and small.en both put
# it at 4.56-4.58, so the caption shows it from 4.56
PIN = {('0093', 4.42): (4.56, 4.70)}


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
            ws = apply_fix(d['src'], words_of(d['src'], a, d['out']), used)
            pin = PIN.get((d['src'], d['in']))
            if pin:
                ws[0][0], ws[0][1] = pin
                ws[1][0] = max(ws[1][0], pin[1])
        caps.append(dict(src=d['src'], **{'in': d['in']}, out=d['out'], t=d['t'],
                         words=[[round(d['t'] + w[0] - d['in'], 3), round(d['t'] + w[1] - d['in'], 3), w[2]] for w in ws]))
    json.dump(caps, open(os.path.join(ROOT, 'data', 'captions.json'), 'w'), indent=1)
    json.dump(used, open(os.path.join(ROOT, 'data', 'caption_fixes.json'), 'w'), indent=1)
    for c in caps:
        print(f"{c['t']:7.2f} {c['src']} " + ' '.join(w[2] for w in c['words']))
    print(len(used), 'fixes applied')


if __name__ == '__main__':
    main()
