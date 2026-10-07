#!/usr/bin/env python3
"""make_edl.py -- the Lifestyle TEST CHAPTER (Chapter 3, "Seattle, WA", the pickup -> first sit -> first drive) as data
-> edl.json in the Sep 15 rally v2 schema (shots / dialog / audio_extra), the one ../../../engine/vlog.py plan reads.

Spans come from ../PLAN.md, chapter 3 (Omarie picked them on 2026-10-07). Word timings: /home/user/day-owt/tr
(faster-whisper small.en, the day index). Every dialog out-point is the last word's end + TAIL, never into the next word
(any speaker), and it must leave >= 350 ms after the last word; pieces that cannot are listed in WARN. The second model
(medium.en) and the measured end of voice re-check these in step 2, before the captions and word pops (fetch handles of
0.8 s cover small moves).

Changes from the PLAN spans, each for a reason:
  * 0087 44.5-47.8 / 55.1-59.7: two pieces, the "From Supercar Experience" span (51.1-53.5) cut out, as PLAN says.
  * 0089 139.6-152.5: jump cut past the 145.6-147.8 pause with a 2.2 s CUTAWAY (0087 38.2-40.4, the white McLaren
    and the lot; FIRST span 38.4-40.2 plus 0.2 s each side, clear of the 33.9-37.6 stranger block), for picture changes.
  * 0090 1.5-28.5 -> 1.5-7.5 / 13.0-19.0 at 0.5x (the car rolls up: the slow part) / 19.0-27.9 at 1x. 7.5-13.0 is empty
    asphalt. Ends at 27.9, not 28.5: a staff member's legs are in frame at 28.0 and the stranger block starts at 28.7.
    No bed under it; the words the speaker model scores OTHER (1.49-2.77 "Hear the car", 10.47-12.21 "Fire / Oh") are
    muted (mute list), engine sound stays.
  * 0090 102.3-118.0 -> 104.0-109.25 / 110.2-118.0: starts on "we have the 600LT ..." (102.3 starts mid-sentence on
    "gonna fix that but"), jump cut past the pause at 109.3-110.2.
  * 0091 51.8-70.1: jump cut past the 3 s pause (56.3-59.0) before "impossible".
  * 0092 7.6-44.0 -> 7.52-24.0 / 26.5-37.35 (jump cut past the quiet 24-26.5), then his talk ends and 37.35-44.0 (both hands
    up on the camera, then the stereo song starts at 45.4) is replaced by two DRIVE cutaways from 0092 118-150 (top down,
    moving, one hand on the wheel and no phone in the 2 s keyframes): 126.5-129.5 and 140.0-143.0. PICTURE ONLY: 0092
    103-118 transcribes like lyrics ("somebody out there is waiting on me") and 150-162 is a flagged stereo song, so their
    audio is not used; the bed (or room tone in the NO MUSIC mix) carries them.
  * 0092 88.2-92.6: ends the chapter; "motherfucker" (90.81-91.69) bleeped.
In-points were moved onto the measured voice-band onsets (same envelope as MEASURED below), so no first word is clipped:
0087 44.5->44.25 ("How" starts ~44.35), 55.1->55.0 (onset 55.1), 0089 139.6->140.5 (starts on "right now"; "So" sits in
a 50 ms gap from "what you mean?"), 0090 104.0->103.72 ("But we have", no gap before "we"), 110.2->110.15, 0091
22.1->21.9 (onset 22.0), 0092 1.2->1.3 (digital silence to 1.4), 7.6->7.52 (dip before "Let's"; 6.75-7.45 holds
voice the ASR did not transcribe, left out).
Stereo check (Shazam, 4-8 s windows over every used range, 7 Oct): no match anywhere used, except Phantom up to ~88.7 at
the start of the last line (handled above); 0092 100-150 is SOMEBODY LOVES ME, so the drive cutaways stay picture only.
Re-run: python3 make_edl.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
TRD = '/home/user/day-owt/tr'
FPS = 30000 / 1001
TAIL = 0.40

# (src, in, dur, speed, note, sync-dialog (in, asr_out) or None)
SHOTS = [
    ('0087', 9.5, None, 1.0, 'FIRST: outside the shop, "I don\'t think they\'re open. Is this the McLaren?" (place title Seattle, WA)', (9.5, 18.0)),
    ('0087', 44.25, None, 1.0, '"How you doing? I\'m here to pick up the 600 LT."', (44.25, 47.8)),
    ('0087', 55.0, None, 1.0, 'JUMP (past "From Supercar Experience" 51.1-53.5): "...brand new engine in it. I got to drive it all the way back to Vegas."', (55.0, 59.7)),
    ('0088', 0.4, None, 1.0, 'inside the shop: "So they got one more hour until they\'re done with the car."', (0.4, 5.2)),
    ('0089', 140.5, 5.8, 1.0, 'SYNC: "right now he\'s finna go grab the 600 LT from the warehouse" (audio runs on under the cutaway)', (140.5, 152.5)),
    ('0087', 38.2, 2.2, 1.0, 'CUTAWAY (picture only): the white McLaren and the lot; his 0089 audio runs on', None),
    ('0089', 147.8, None, 1.0, 'SYNC back on him: "...and I\'ve been chillin out here waiting for it, but"', 'cont'),
    ('0089', 176.1, None, 1.0, '"I got a charge, I got a 12 hour drive." (spoken only; no card, no word pop)', (176.1, 178.1)),
    ('0089', 187.8, None, 1.0, 'JUMP (lead, 7 Oct: starts >= 0.1 s after the OTHER-scored "So I\'ll be right back"; "car" ends 187.70, "Brand" starts 187.93): "Brand new engine in it too ... let\'s see what he pulls up with it and how\'s it sounding."', (187.8, 194.2)),
    ('0090', 1.5, 6.0, 1.0, 'FIRST (rotate): hear the car; no bed; OTHER voice 1.49-2.77 muted', None),
    ('0090', 13.0, 12.0, 0.5, 'FIRST (rotate): the 600 LT rolls up, 0.5x (speed ramp in/out); nat engine in real time (audio_extra)', None),
    ('0090', 19.0, 8.9, 1.0, 'REACT (rotate): "Oh yeah ... Brand new engine" (ends 27.9: staff legs at 28.0)', (21.9, 27.9)),
    ('0090', 103.72, None, 1.0, 'PLAN (rotate): "But we have the 600LT that we will be driving from Seattle to Vegas."', (103.72, 109.3)),
    ('0090', 110.15, None, 1.0, 'FIRST (rotate; 116-118 interior: blur the cluster): "I\'m just gonna put my bag next to me. This is the interior chat. Little red gut."', (110.15, 118.0)),
    ('0091', 2.1, None, 1.0, 'FIRST, first sit: "We are in the 600 LT. Spider top goes down" (parked; phone in hand is fine here)', (2.1, 9.6)),
    ('0091', 21.9, None, 1.0, '"Good 12 hours out of us, so I\'m getting the car warmed up..." (parked)', (21.9, 30.0)),
    ('0091', 51.8, None, 1.0, 'SETBACK: "See the thing about this car is connecting to Bluetooth is like"', (51.8, 56.3)),
    ('0091', 59.0, None, 1.0, 'JUMP: "impossible ... I don\'t know why"', (59.0, 70.1)),
    ('0092', 1.3, None, 1.0, '"Finding out how to use Bluetooth was crazy" (x2)', (1.3, 5.1)),
    ('0092', 7.52, None, 1.0, 'FIRST, top down (parked): "Let\'s make sure this top work ... it\'s gonna be a long drive"', (7.52, 22.4)),
    ('0092', 26.5, None, 1.0, 'JUMP: "literally a long drive ... We don\'t have lift on this car. Oh we do have lift on this car. Alright cool." (medium.en; small.en stopped at "have")', (26.5, 36.95)),
    # nq-check gate, 2026-10-07: 126.5-129.5 failed (both hands off the wheel at 128.6). Only 139.95-143.75 has a hand on
    # the wheel in every frame among the fetched drive spans (the links had expired, so no new span), so the 6 s gap is
    # that one run at 0.633x (0092 is 59.94 fps: real slow motion), over the same room tone.
    ('0092', 139.95, 6.0, 0.6333, 'CUTAWAY DRIVE (picture only), 0.633x: top down, moving, a hand on the wheel in every frame', None),
    ('0092', 88.5, None, 1.0, 'PAYOFF (end; the stereo song Phantom (Shazam 84-88 s) stops at 88.75 on the <150 Hz band, his "We" starts 88.65: dialog from 88.62, nat from 88.8): "We out here in Seattle, Washington in a [bleep] 600 LT." (hands check at the gate)', (88.62, 92.6)),
]
MUTE = [('0090', 1.40, 2.85, 'OTHER: "Hear the car"'), ('0090', 10.40, 12.30, 'OTHER: "Fire", "Oh" (under the 0.5x)')]
BLEEP = [('0092', 90.81, 91.69, 'motherfucker')]
ROT = {'0090': 'sideways: sky on the left in the keyframes (0-114 s); rotate 90 deg clockwise, check per shot at the gate'}


def words(src):
    t = json.load(open(os.path.join(TRD, f'{src}.json')))
    return [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]


def inside(w, a, b):
    return min(w[1], b) - max(w[0], a) >= 0.15 or (a - 1e-6 <= w[0] < b - 0.1)


WARN = []
# where whisper stretches the next word back over a real pause, the out-point comes from the voice-band envelope of
# /home/user/day-owt/aud/<clip>.m4a (300-3400 Hz, 50 ms frames; measured 2026-10-07): (src, in) -> (voice_end, next_onset, out)
MEASURED = {('0089', 140.5): (151.40, 152.60, 152.00),   # "...waiting for it, but" ends 151.4; "yeah" starts 152.6
            ('0091', 21.9): (30.15, 30.95, 30.55),       # "...making sure everything" ends 30.15; "Oh" starts 30.95
            ('0092', 26.5): (36.95, None, 37.35)}        # medium.en: "...Alright cool." ends 36.95; steady handling noise after


def tail(src, a, b):
    W = words(src)
    p = [w for w in W if inside(w, a, b)]
    le = p[-1][1]
    n = [w for w in W if w[0] > p[-1][0] + 0.01 and not inside(w, a, b)]
    no = n[0][0] if n else 1e9
    out = round(min(le + TAIL, no - 0.03), 3)
    m = MEASURED.get((src, a))
    if m:
        return m[2], round(le, 3), p, m
    if out - le < 0.35 - 1e-6:
        WARN.append(f'{src} {a}: last word "{p[-1][2]}" ends {le:.2f}, next word "{n[0][2]}" at {no:.2f}: tail {out - le:.2f} s < 0.35')
    return out, round(le, 3), p, None


shots, dialog, extra = [], [], []
t = 0.0
pending = None
for i, (src, a, dur, sp, note, dl) in enumerate(SHOTS):
    if dl == 'cont':
        # back on the same take after a cutaway: picture runs to the end of the piece that started earlier
        d = dialog[-1]
        dur = round(d['t'] + (d['out'] - d['in']) - t, 3)
        a = round(d['in'] + (t - d['t']), 3)
        note += f' (in {a})'
    elif dl:
        out, le, p, m = tail(src, dl[0], dl[1])
        din = dl[0]
        if dur is None:
            dur = round(out - a, 3)
        dialog.append(dict(beat=i, src=src, **{'in': din}, out=out, t=round(t + (din - a), 3), trim_pauses=None,
                           last_word_end=le, voice_end=m[0] if m else None, next_onset_measured=m[1] if m else None, extended=False, out_asr=dl[1],
                           text=' '.join(w[2] for w in p)))
    shots.append(dict(beat=i, src=src, **{'in': a}, out=round(a + dur * sp, 3), speed=sp, t=round(t, 3), dur=round(dur, 3),
                      note=note))
    t += dur
dur_total = round(t, 3)

# nat sound in real time under the 0.5x roll-up (the engine), and room tone sources for the NO MUSIC mix
s10 = shots[10]
extra.append(dict(beat=10, src='0090', **{'in': 7.5}, out=19.5, t=round(s10['t'], 3), kind='nat',
                  note='engine approaching, real time, under the 0.5x picture (no bed in 0090)'))
extra.append(dict(beat=-1, src='0092', **{'in': 37.6}, out=43.6, t=0.0, kind='slack',
                  note='parked room tone after his talk (ends 0.8 s before the 45.4 stereo block); check it has no stereo intro'))
extra.append(dict(beat=-1, src='0089', **{'in': 194.2}, out=195.4, t=0.0, kind='slack', note='after "how\'s it sounding"'))

# assert: no shot or audio range sits on a block flag (with the 0.8 s fetch handle the render must not use)
flags = [f for f in json.load(open('/home/user/day-owt/flags.json')) if f.get('severity') == 'block']
for s in shots + extra:
    lo, hi = s['in'], s['out']
    for f in flags:
        if f['clip'] == s['src'] and lo < f['t1'] and f['t0'] < hi:
            raise SystemExit(f'BLOCK FLAG {f["clip"]} {f["t0"]}-{f["t1"]} {f["category"]} under {s["src"]} {lo}-{hi}')

edl = dict(fps='30000/1001', size=[3840, 2160], duration=dur_total,
           chapters=[dict(t=0.0, title='Seattle, WA', clock='')],
           shots=shots, dialog=dialog, audio_extra=extra,
           beats=[dict(i=0, ch='CH3', t0=0.0, t1=dur_total, note='TEST CHAPTER: Seattle, WA, the pickup -> first sit -> first drive')],
           mute=[dict(src=s, **{'in': a}, out=b, note=n) for s, a, b, n in MUTE],
           bleeps=[dict(src=s, **{'in': a}, out=b, word=n) for s, a, b, n in BLEEP],
           rotate=ROT, warnings=WARN)
json.dump(edl, open(os.path.join(HERE, 'edl.json'), 'w'), indent=1)
print(f'shots {len(shots)}  dialog {len(dialog)}  runtime {dur_total:.2f} s ({int(dur_total // 60)}:{dur_total % 60:04.1f})  '
      f'picture changes/min {60 * (len(shots) - 1) / dur_total:.1f}')
for w in WARN:
    print('WARN', w)
