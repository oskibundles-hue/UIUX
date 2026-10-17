#!/usr/bin/env python3
"""make_edl.py -- the Part 2 cut as data -> data/edl.json (the Sep 15 rally v2 EDL schema).

Each beat lists its picture (src, in, dur[, speed]) back to back and its dialog pieces (src, in, out) placed at an offset
from the beat start ('at'), or in sync with a shot ('sync': shot index inside the beat, the piece's own source time
decides where it lands). Source times are seconds into the camera file (DJI_2026092[67]HHMMSS_NNNN_D.MP4); dialog edges
sit in the pauses of the day's word timings (/tmp/claude-0/p2day/tr, faster-whisper small.en) and are re-checked with
medium.en before the captions are built (tools/make_captions.py).
Re-run after editing: python3 tools/make_edl.py

Kept out on purpose (Part 1's held lines and the eight blockers): every speed, distance, hours-to-go, price and gas-dollar
line (0116 43-56 / 76-96 / 107-120 / 137-140, 0117 20-44 / 57-72, 0118 12-40, 0119 15-17 / 120-175, 0122 43-47, 0123
46-50), "go faster / go fast / obliterated" (0117), "they stole our car" (0106 90 s), the oil and coolant hunt (0106,
0107: maintenance trouble on a client car), "no hotel, no nothing" (0118 83-86: reads as a drowsy-driving boast, like
Part 1's held fuel-stop line), the TikTok audio and the third-party talk in 0107 / 0109 / 0111, people's names (0123).
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30000 / 1001

B = []


def beat(ch, note, shots, dialog=(), tail=0.0):
    B.append(dict(ch=ch, note=note, shots=shots, dialog=list(dialog), tail=tail))


# Fix A (Omarie, 6 Oct): every dialog piece's audio out-point is set by tail() from the word timestamps, not by hand:
# >= 350 ms (TAIL) after the last word ends (small.en, the captions' timing source), never into the next word (whose start
# is the later of the two models': whisper stretches a word over the pause before it), and a piece whose sentence runs on
# is extended to the sentence's end (EXTEND below, with the words the extension adds). When the picture cuts before
# the voice ends, the voice runs on under the next shot (an L-cut); the build asserts that no two voices overlap.
# Pieces dropped on 6 Oct because a clean tail was impossible (the next word starts < 350 ms after the line and the
# run-on is profanity, a figure, a third party or a line the two models hear differently):
#   0106 285.0 "I am in Nampa, Idaho" (runs on: "currently at Treasure Valley marketplace just west of Boise, looking at")
#   0106 63.5 "I'm driving to Vegas right now." (the other man's "Oh yeah?" starts on its last syllable)
#   0112 38.95 "But I'm cool, I'm chilling right now. I ate, like I'm energized." (no pause before "We finna charge up...")
#   0116 96.8 "Thank God there was no rain, ice, snow," (runs on: "like none of that shit")
#   0116 142.5 / 149.57 "side missions ..." / "it is what it is ..." (run on into "but shout out to God" / "but you got
#       what you got" (the models differ) and "But yeah, so appreciate y'all ...")
#   0119 134.75 "Let's see how much gas that gets us ..." (runs on into the hours-to-go line)
#   0119 247.15 "so you guys can get some cool little POVs" (runs on; the models differ: "I want to do it" / "if you want to")
#   0118 75.55 "It was lots of beautiful trees and scenery" (runs on: "and all kinds of shit out in Seattle")
#   0122 7.0 "we're back in Vegas, baby" (lead, 6 Oct: speaker scored OTHER, unconfirmed; STRIP-2 carries the beat)
TAIL = 0.40
EXTEND = {('0105', 4.80): 9.70,    # + "Appreciate you, thank you." (both models), next word 10.60
          ('0112', 54.80): 59.32,  # + small.en's "and" (medium.en hears a breath; not captioned), next word 60.98
          ('0114', 34.92): 37.00,  # + "I'm parched." (both models), next word 39.79
          ('0117', 100.80): 102.74,  # + "not an SOS." (both models), next word 103.46
          ('0107', 14.62): 19.95,  # v2: + "No cap." (both models), next word 20.56
          ('0116', 153.42): 161.30}  # v2: + "And yeah, out ..." to the end of his sign-off (data/words_small_fix.json): the next
                                     # word after "content." sits 20-760 ms later depending on the model (no clean tail there);
                                     # "And yeah," is captioned (both models), the last word is not (models differ: "you" / "to")
# part2 v2 (7 Oct, ported from part1 v2): where whisper stretches the next word back over a real pause, the next onset
# measured on the voice-band envelope of the clip audio (tools/onsets.py) bounds the tail instead; and the measured end of
# voice (voice_end) moves the last word's end later by at most VEND_MAX, so the tail is counted from the real end of voice.
NEXT_ONSET = {}
MED = json.load(open(os.path.join(ROOT, 'data', 'words_medium.json')))
TRD = '/tmp/claude-0/p2day/tr'
VEND_MAX = 0.40     # the measured end of voice moves the last word's end later by at most this much


# small.en words for windows the day index missed (re-run on the window, small.en beam 5, agrees with medium.en)
FIXW = json.load(open(os.path.join(ROOT, 'data', 'words_small_fix.json')))


def small_words(src):
    t = json.load(open(os.path.join(TRD, f'{src}.json')))
    sm = [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]
    fx = FIXW.get(src, [])
    if fx:
        a, b = fx[0][0], fx[-1][1]
        sm = sorted([w for w in sm if not (a - 0.01 <= w[0] <= b)] + [[w[0], w[1], w[2]] for w in fx], key=lambda w: w[0])
    return sm


def _inside(w, a, b):
    return min(w[1], b) - max(w[0], a) >= 0.15 or (a - 1e-6 <= w[0] < b - 0.1)


def voice_end(src, le):
    """the end of voice after a last word that ends at le: the voice-band envelope falls 12 dB under the word's peak and
    stays down 120 ms (tools/onsets.py)."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import onsets
    e, _ = onsets.measure(src, le, None)
    return e


def tail(src, a, b):
    """the out-point for a piece whose words lie in [a, b): last word end + TAIL, before the next word."""
    sm = small_words(src)
    md = [[w[0], w[1], w[2].strip()] for w in MED.get(f'{src}:{a:.2f}', [])]
    b = EXTEND.get((src, round(a, 2)), b)
    p = [w for w in sm if _inside(w, a, b)]
    le = p[-1][1]
    ve = voice_end(src, le)
    le_eff = max(le, ve) if ve is not None and ve - le <= VEND_MAX else le
    nxt = []
    for m in (sm, md):
        n = [w for w in m if w[0] > p[-1][0] + 0.01 and not _inside(w, a, b)]
        if n:
            nxt.append(n[0][0])
    no = max(nxt) if nxt else 1e9
    no_m = NEXT_ONSET.get((src, round(a, 2)))
    if no_m:
        no = max(no, no_m)
    out = round(min(le_eff + TAIL, no - 0.03), 3)
    assert out - le >= 0.35 - 1e-6 and out - le_eff >= 0.30 - 1e-6, (src, a, le, le_eff, no)
    return dict(out=out, last_word_end=round(le, 3), voice_end=round(ve, 3) if ve is not None else None,
                next_onset_measured=no_m, extended=(src, round(a, 2)) in EXTEND, out_asr=b)


# ---------------------------------------------------------------- OPEN: the hook, his own line over first light
beat('OPEN', 'hook panel on frame 0 (sunrise); VO 0116 (06:25): "So we are currently in somewhere in Nevada. I don\'t know where."', [
    ('0121', 128.0, 2.4, 1.0, 'hook frame: the desert road, morning (round 1: 0116 4.0-6.4 had his right hand off the wheel with a phone / can)'),
    ('0121', 100.0, 1.8, 1.0, 'rear-deck cam, the road behind'),
    ('0122', 300.0, 1.8, 1.0, 'the freeway'),
    ('0119', 67.0, 1.8, 1.0, 'the McLaren at the pump, door up behind him (hands / phone check 6 Oct)'),
], [('0116', 35.30, 39.40, ('at', 2.0))])

# ---------------------------------------------------------------- CH1 NIGHT SHIFT (19:32)
beat('CH1', 'CH1 slam; PLACE PIT STOP · IN-N-OUT; "We finally made it to In-N-Out. Appreciate you, thank you."', [
    ('0105', 19.8, 2.0, 1.0, 'In-N-Out, lit, under the CH1 slam (v2: 2.0 s, then the cut-in; config clockAs 0105 4.0 so the strip clock reads his line, never 19.8 then back to 6.0)'),
    ('0105', 6.0, 4.2, 1.0, 'v2 food break, SYNC cut-in: his face under the red neon, "...to In-N-Out. Appreciate you, thank you." (12-14 s is near-black, not used)'),
], [('0105', 4.80, 8.42, ('sync', 1))])
beat('CH1', 'VO 19:40: "Yeah, I just came from Seattle." (the conversation around it is out: third party)', [
    ('0106', 288.2, 3.2, 1.0, 'parked at the marketplace (0106 48-150 s is dark)'),
], [('0106', 65.85, 67.75, ('at', 0.2))])
# v2 food break (Omarie, 6 Oct: "i got no clips of me taking a break eating"); 19:52, after the 0106 beat (19:40-19:44) in day
# order. 0105 10.6-13.8 "We finally gonna eat. God damn. I've been trying to eat all day" is out: "I've" starts 280 ms after
# the profanity (no clean cut), and the two models differ on its first words ("We" / "And we're").
beat('CH1', 'FOOD BREAK 19:52: "I ain\'t gonna lie, nothing like doom-scrolling while eating. No cap."', [
    ('0107', 14.5, 5.8, 1.0, 'SYNC: eating at the car, mounted cam, parked (the burger in both hands, then the phone: the car is parked)'),
], [('0107', 14.62, 19.04, ('sync', 0))])
beat('CH1', 'gas station (in-car nat)', [
    ('0111', 23.0, 2.6, 1.0, 'at the pump'),
])
beat('CH1', '"It\'s a McLaren." / "I was like, that\'s not a Corvette."', [
    ('0111', 47.0, 1.8, 1.0, 'SYNC (v2: +0.1 s, the tail is counted from the measured end of voice)'),
    ('0111', 54.5, 2.55, 1.0, 'SYNC (v2: +0.15 s, measured end of voice)'),
], [('0111', 47.25, 48.45, ('sync', 0)), ('0111', 54.70, 56.50, ('sync', 1))])
beat('CH1', '"We are gassed up, we are ready to leave." / "Let\'s play some tunes and get up out of here."', [
    ('0112', 17.1, 3.0, 1.0, 'SYNC'),
    ('0112', 54.7, 3.8, 1.0, 'SYNC'),
], [('0112', 17.25, 19.55, ('sync', 0)), ('0112', 54.80, 58.35, ('sync', 1))])
beat('CH1', 'night road (the in-car stereo: bed music)', [
    ('0113', 108.5, 2.0, 1.0, 'night drive, hands on the wheel (104 had a hand off the wheel; v2: first, so the strip clock runs forward)'),
    ('0113', 112.5, 2.2, 1.0, 'night drive, headlights'),
    ('0113', 115.0, 2.0, 1.0, 'night drive, hands on the wheel (128.5 was black)'),
    ('0113', 118.0, 2.0, 1.0, 'night drive, hand on the wheel (round 1: 120.6-122 had the hand off the wheel, seen once the 16:9 fill was fixed)'),
])
beat('CH1', 'CLOCK STAMP 01:29 AFTER THE NAP: "I definitely did take a nice McLaren nap." / "Pretty nice parking lot. Reminds me of Vegas." / "I feel refreshed. I\'m parched." / "We back in business, baby!"', [
    ('0114', 7.3, 4.2, 1.0, 'SYNC: parked after the nap (16:9 source)'),
    ('0114', 19.6, 3.6, 1.0, 'SYNC (v2: +0.1 s, measured end of voice)'),
    ('0114', 34.8, 2.8, 1.0, 'SYNC (v2: +0.1 s, measured end of voice)'),
    ('0114', 42.6, 2.75, 1.0, 'SYNC (v2: +0.25 s, measured end of voice)'),
], [('0114', 7.45, 11.10, ('sync', 0)), ('0114', 19.75, 22.65, ('sync', 1)), ('0114', 34.92, 35.95, ('sync', 2)), ('0114', 42.70, 44.70, ('sync', 3))])
beat('CH1', '02:46 gas: "gassing up, dude, it is freezing"', [
    ('0115', 10.2, 2.0, 1.0, 'SYNC: at the pump, night (round 1: ends before the selfie turns sideways)'),
    ('0115', 20.8, 2.7, 1.0, 'CUTAWAY: the McLaren at the pump, doors up (phone on its side: config rot 90); his audio runs on'),
], [('0115', 10.35, 14.75, ('sync', 0))])

# ---------------------------------------------------------------- CH2 FIRST LIGHT (06:26)
beat('CH2', 'CH2 slam; "It was actually perfect weather this time."', [
    ('0116', 103.6, 3.3, 1.0, 'sunrise at the wheel, in sync with his line (round 2: 126.5 showed him talking under another line); right hand on the wheel, no phone; clock 06:26'),
], [('0116', 104.50, 106.62, ('at', 0.9))])
beat('CH2', '"We got the beautiful view to us right here." / first light', [
    ('0121', 155.0, 3.0, 1.0, 'CUTAWAY the road (round 1: 0116 121.1-124.1 had a hand off the wheel); his audio runs on'),
    ('0121', 110.0, 2.5, 1.0, 'the road (music; 0116 25.0 had the phone in his hand while driving)'),
], [('0116', 121.25, 123.90, ('at', 0.15))])
# v2 talk-to-camera (Omarie, 6 Oct: "just some 1 on 1 time with you guys"), 06:27, driving at dusk, one hand on the wheel
# (cleared by nq-check). Two pieces with a jump cut: 147.0-149.6 is out because the two models hear it differently ("but
# shout out to God" / "but you got what you got"), and 149.6-153.4 runs on from it with no pause. Piece A's tail is
# bounded by medium.en's "but" (147.14).
beat('CH2', 'TALK TO CAMERA 06:27: "I wish it was like more like, you feel me, side missions we could have done," / "But yeah, so appreciate y\'all being in the mirror, hanging out, hope you guys enjoy the content."', [
    ('0116', 142.35, 4.9, 1.0, 'SYNC: at the wheel, dusk light, talking to the camera (one hand on the wheel); speedo box'),
    ('0116', 153.3, 8.45, 1.0, 'SYNC (jump cut past 147.25-153.3), to the end of his sign-off; speedo box'),
], [('0116', 142.50, 146.70, ('sync', 0)), ('0116', 153.42, 159.45, ('sync', 1))])
beat('CH2', 'the desert, low on gas (road cutaways, his audio runs on): "There\'s nothing out here." / "As you can see, it\'s just all field." / "No cell service, not an SOS."', [
    ('0121', 104.0, 3.6, 1.0, 'CUTAWAY (the road; 0117 48.6-52.2 has the phone in his hand while driving)'),
    ('0121', 132.0, 2.4, 1.0, 'CUTAWAY (the road; 0117 74.7-77.1: phone in hand while driving)'),
    ('0121', 140.0, 2.6, 1.0, 'CUTAWAY (the road; 0117 100.7-103.3: phone in hand while driving)'),
], [('0117', 50.65, 51.70, ('at', 2.05)), ('0117', 74.85, 76.60, ('at', 3.75)), ('0117', 100.80, 101.90, ('at', 6.1))])
beat('CH2', '"I\'m looking at the gas station. Oh, thank the Lord." / LOCK-ON MCLAREN 600LT, doors up at the pump (nat)', [
    ('0119', 3.2, 4.5, 1.0, 'SYNC'),
    ('0119', 74.6, 3.6, 1.0, 'LOCK: the McLaren at the pump behind him, doors up (76.2-78.2)'),
], [('0119', 3.30, 7.60, ('sync', 0))])
beat('CH2', '"Man, so I think for the last bit of the drive, I\'m gonna have you guys like in the back"', [
    ('0119', 227.6, 6.6, 1.0, 'SYNC: at the pump'),
], [('0119', 227.70, 233.85, ('sync', 0))])

# ---------------------------------------------------------------- CH3 HOME STRETCH (07:32)
beat('CH3', 'CH3 slam; "Hopefully this don\'t fly off, good lord."', [
    ('0121', 20.9, 3.6, 1.0, 'SYNC: the camera goes on the rear deck (v2: +0.2 s, measured end of voice)'),
], [('0121', 21.00, 24.15, ('sync', 0))])
# v2: "you guys can hear the car" (0121 28.66-32.3; the day index heard "let's hear the car", a beam-1 miss: both models on the
# window agree, data/words_small_fix.json) (he is off camera, in sync with the hood view), then the engine fires (~34.8,
# measured on the clip audio) and idles: bed kind exhaust, in sync. The car is parked at the gas station here (07:32).
beat('CH3', '"You guys can hear me, you guys can hear the car, you guys can hear everything." then the engine fires (bed exhaust, in sync)', [
    ('0121', 28.5, 8.0, 1.0, 'SYNC: the deck cam over the car, parked at the gas station; the engine fires at ~34.8 and idles'),
], [('0121', 28.66, 32.60, ('sync', 0))])
beat('CH3', 'HUD STRIP-1: rear-deck POV, the engine (bed exhaust), SOMEWHERE IN NEVADA', [
    ('0121', 120.0, 8.0, 1.0, 'STRIP-1: rear-deck cam on the road'),
])
beat('CH3', 'VO 0118 (07:13): "Trip has been cool" / "it\'s been pretty fire, really nice scenery." / "I can\'t believe I just did the whole thing."', [
    ('0121', 88.0, 3.0, 1.0, 'rear-deck cam, on the road (config clockAs 0121 128.0: continues the STRIP-1 clock, never back to 07:33)'),
    ('0121', 150.0, 2.5, 1.0, 'rear-deck cam'),
    ('0121', 180.0, 2.5, 1.0, 'rear-deck cam'),
    ('0121', 192.0, 2.5, 1.0, 'rear-deck cam, on the road'),
], [('0118', 61.85, 63.30, ('at', 0.2)), ('0118', 69.45, 73.50, ('at', 2.4)), ('0118', 80.70, 82.75, ('at', 7.3))])
beat('CH3', 'the freeway toward Las Vegas (bed music: the in-car stereo, into STRIP-2)', [
    ('0122', 306.0, 2.0, 1.0, 'the freeway'),
    ('0122', 314.0, 2.0, 1.0, 'the freeway (v2: 322.0 out; the music is no longer timed to bars)'),
])
beat('CH3', 'HUD STRIP-2: INTO LAS VEGAS (09:04)', [
    ('0122', 451.0, 8.0, 1.0, 'STRIP-2: the freeway into Las Vegas'),
])
beat('CH3', 'PLACE 09:10 ARRIVED · SUPERCAR EXPERIENCE: "we just got back to the shop." / "Yeah, let me take my stuff out of here." / '
     '"So that concludes today\'s episode. We dropped it off here at Supercar Experience at headquarters." / "So I hope you guys enjoyed that. And until next time, peace."', [
    ('0123', 4.7, 2.1, 1.0, 'SYNC: at the SE Las Vegas shop (ends before the names at 7.0)'),
    ('0123', 13.7, 3.2, 1.0, 'SYNC'),
    ('0123', 39.7, 5.85, 1.0, 'SYNC (ends before the hours line at 46.0; v2: +0.15 s, measured end of voice)'),
    ('0123', 55.0, 4.6, 1.0, 'SYNC'),
], [('0123', 4.85, 6.35, ('sync', 0)), ('0123', 13.80, 16.60, ('sync', 1)), ('0123', 39.85, 45.20, ('sync', 2)),
    ('0123', 55.25, 59.50, ('sync', 3))])
END_CARD = 5.4

shots, dialog, beats, chapters = [], [], [], []
TITLES = {'CH1': ('NIGHT SHIFT',), 'CH2': ('FIRST LIGHT',), 'CH3': ('HOME STRETCH',)}
t = 0.0
for i, b in enumerate(B):
    t0 = t
    starts = []
    for (src, a, dur, sp, note) in b['shots']:
        starts.append((t, a))
        spd = 1.0 if sp == 'ramp' else sp
        shots.append(dict(beat=i, src=src, **{'in': a}, out=round(a + (12.0 if sp == 'ramp' else dur * spd), 3), speed=spd, t=round(t, 3), dur=round(dur, 3), note=note))
        t += dur
    for (src, a, b_, pl) in b['dialog']:
        if pl[0] == 'at':
            at = t0 + pl[1]
        else:
            st, sa = starts[pl[1]]
            at = st + (a - sa)
        tl = tail(src, a, b_)
        dialog.append(dict(beat=i, src=src, **{'in': a}, out=tl.pop('out'), t=round(at, 3), trim_pauses=None, **tl))
    if b['ch'] in TITLES and not any(c['title'] == TITLES[b['ch']][0] for c in chapters):
        chapters.append(dict(t=round(t0, 3), title=TITLES[b['ch']][0], clock=''))
    beats.append(dict(i=i, ch=b['ch'], t0=round(t0, 3), t1=round(t, 3), note=b['note']))
shots.append(dict(beat=len(B), src='card', **{'in': 0}, out=END_CARD, speed=1.0, t=round(t, 3), dur=END_CARD, note='END CARD'))
beats.append(dict(i=len(B), ch='END', t0=round(t, 3), t1=round(t + END_CARD, 3), note='end card'))
dur = round(t + END_CARD, 3)
for d in dialog:
    assert d['t'] >= -1e-6, d
# blocker 5: no source span in two shots
_sp = sorted((x['src'], x['in'], x['out']) for x in shots if x['src'] != 'card')
for p_, q_ in zip(_sp, _sp[1:]):
    assert not (p_[0] == q_[0] and q_[1] < p_[2] - 1e-6), f'source span used twice: {p_} {q_}'
# fix A: a voice may run on under the next shot (L-cut), but never into the next voice
bad = []
for p, q in zip(dialog, dialog[1:]):
    pe = p['t'] + p['out'] - p['in']
    if q['t'] - pe < 0.08:
        bad.append(f"voices overlap by {pe + 0.08 - q['t']:.2f}: {p['src']} {p['in']} (beat {p['beat']}) ends {pe:.2f}, {q['src']} {q['in']} (beat {q['beat']}) starts {q['t']:.2f}")
for m in bad:
    print('PROBLEM', m)
assert not bad
# fetch slack (not played; mix.py does not read audio_extra): spare source around the shots whose hands / phone / speedometer
# can only be checked on the mezzanines, plus a pool of road-only cutaways (rear-deck cam 0121, freeway 0122), so any shot
# can be slipped or covered without a second Dropbox round trip
SLACK = [('0116', 0.0, 163.0), ('0117', 44.0, 118.0), ('0119', 0.0, 96.0), ('0119', 133.0, 139.0), ('0119', 222.0, 253.0), ('0121', 18.0, 200.0),
         ('0122', 0.0, 16.0), ('0122', 290.0, 330.0), ('0122', 430.0, 480.0), ('0123', 0.0, 61.0), ('0115', 6.0, 30.0),
         ('0114', 0.0, 48.0), ('0111', 0.0, 60.0), ('0112', 10.0, 60.0), ('0105', 14.0, 29.0), ('0107', 10.0, 22.0), ('0106', 0.0, 8.0),
         ('0106', 280.0, 293.0), ('0106', 62.0, 69.0), ('0113', 100.0, 135.0), ('0118', 60.0, 84.0)]
extra = [dict(beat=-1, src=s_, **{'in': a}, out=b_, t=0.0, kind='slack') for s_, a, b_ in SLACK]
edl = dict(fps='30000/1001', size=[1080, 1920], duration=dur, chapters=chapters, shots=shots, dialog=dialog,
           audio_extra=extra, beats=beats, warnings=[])
json.dump(edl, open(os.path.join(ROOT, 'data', 'edl.json'), 'w'), indent=1)
print(f'{len(shots)} shots, {len(dialog)} dialog pieces, {dur:.2f} s ({int(dur // 60)}:{dur % 60:05.2f})')
for c in chapters:
    print(' chapter', c)
