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


# ---------------------------------------------------------------- OPEN: the hook, his own line over first light
beat('OPEN', 'hook panel on frame 0 (sunrise); VO 0116 (06:25): "So we are currently in somewhere in Nevada. I don\'t know where."', [
    ('0116', 4.0, 2.4, 1.0, 'hook frame: first light over the desert ("you see the beautiful desert")'),
    ('0121', 100.0, 1.8, 1.0, 'rear-deck cam, the road behind'),
    ('0122', 300.0, 1.8, 1.0, 'the freeway'),
    ('0119', 76.0, 1.8, 1.0, 'the McLaren at the pump, doors up'),
], [('0116', 35.30, 39.40, ('at', 2.0))])

# ---------------------------------------------------------------- CH1 NIGHT SHIFT (19:32)
# Every piece below is one whose words small.en (the day index) and medium.en (beam 5, re-run on the piece) agree on;
# pieces where they differ were cut, not guessed (list in README "Captions").
beat('CH1', 'CH1 slam; PLACE PIT STOP · IN-N-OUT; "We finally made it to In-N-Out." (0105 4.9-8.4 is dark: the line runs over the lit part)', [
    ('0105', 19.8, 4.6, 1.0, 'In-N-Out, lit (0105 0-18 s is dark / lens covered)'),
], [('0105', 4.80, 8.42, ('at', 0.3))])
beat('CH1', '"I am in Nampa, Idaho" / VO from 19:40: "I\'m driving to Vegas right now." "Yeah, I just came from Seattle." (the other man\'s "Oh yeah?" between is out)', [
    ('0106', 284.8, 3.2, 1.0, 'SYNC: parked at the marketplace'),
    ('0106', 288.2, 4.4, 1.0, 'parked (his 19:40 lines over it; 0106 48-150 s is dark)'),
], [('0106', 285.00, 287.86, ('sync', 0)), ('0106', 63.50, 64.72, ('at', 3.3)), ('0106', 65.85, 67.75, ('at', 4.85))])
beat('CH1', 'gas station (music)', [
    ('0111', 23.0, 2.6, 1.0, 'at the pump'),
])
beat('CH1', '"It\'s a McLaren." / "I was like, that\'s not a Corvette."', [
    ('0111', 47.0, 1.7, 1.0, 'SYNC'),
    ('0111', 54.5, 2.2, 1.0, 'SYNC'),
], [('0111', 47.25, 48.45, ('sync', 0)), ('0111', 54.70, 56.50, ('sync', 1))])
beat('CH1', '"We are gassed up, we are ready to leave." / "But I\'m cool, I\'m chilling right now. I ate, like I\'m energized." / "Let\'s play some tunes and get up out of here."', [
    ('0112', 17.1, 2.6, 1.0, 'SYNC'),
    ('0112', 38.8, 4.4, 1.0, 'SYNC'),
    ('0112', 54.7, 3.8, 1.0, 'SYNC'),
], [('0112', 17.25, 19.55, ('sync', 0)), ('0112', 38.95, 43.06, ('sync', 1)), ('0112', 54.80, 58.35, ('sync', 2))])
beat('CH1', 'night road (music only)', [
    ('0113', 112.5, 2.2, 1.0, 'night drive, headlights'),
    ('0113', 128.5, 2.0, 1.0, 'night drive'),
])
beat('CH1', 'CLOCK STAMP 01:29 AFTER THE NAP: "I definitely did take a nice McLaren nap." / "Pretty nice parking lot. Reminds me of Vegas." / "I feel refreshed." / "We back in business, baby!"', [
    ('0114', 7.3, 4.0, 1.0, 'SYNC: parked after the nap (16:9 source)'),
    ('0114', 19.6, 3.2, 1.0, 'SYNC'),
    ('0114', 34.8, 1.4, 1.0, 'SYNC'),
    ('0114', 42.6, 2.2, 1.0, 'SYNC'),
], [('0114', 7.45, 11.10, ('sync', 0)), ('0114', 19.75, 22.65, ('sync', 1)), ('0114', 34.92, 35.95, ('sync', 2)), ('0114', 42.70, 44.70, ('sync', 3))])
beat('CH1', '02:46 gas: "gassing up, dude, it is freezing"', [
    ('0115', 10.2, 4.7, 1.0, 'SYNC: at the pump, night'),
], [('0115', 10.35, 14.75, ('sync', 0))])

# ---------------------------------------------------------------- CH2 FIRST LIGHT (06:26)
beat('CH2', 'CH2 slam; "Thank God there was no rain, ice, snow," / "It was actually perfect weather this time."', [
    ('0116', 96.6, 10.2, 1.0, 'SYNC: sunrise at the wheel'),
], [('0116', 96.80, 102.95, ('sync', 0)), ('0116', 104.50, 106.62, ('sync', 0))])
beat('CH2', '"We got the beautiful view to us right here."', [
    ('0116', 121.1, 3.0, 1.0, 'SYNC'),
], [('0116', 121.25, 123.90, ('sync', 0))])
beat('CH2', '"I wish it was like more like, you feel me, side missions we could have done," / "it is what it is, you feel me, so we gonna make the best of what we can make out of this."', [
    ('0116', 142.4, 11.2, 1.0, 'SYNC'),
], [('0116', 142.50, 146.75, ('sync', 0)), ('0116', 149.57, 153.45, ('sync', 0))])
beat('CH2', 'the desert, low on gas: "There\'s nothing out here." / "As you can see, it\'s just all field." / "No cell service."', [
    ('0117', 48.6, 3.3, 1.0, 'SYNC'),
    ('0117', 74.7, 2.0, 1.0, 'SYNC'),
    ('0117', 100.7, 1.4, 1.0, 'SYNC'),
    ('0117', 88.0, 2.0, 1.0, 'the empty desert (music)'),
], [('0117', 50.65, 51.70, ('sync', 0)), ('0117', 74.85, 76.60, ('sync', 1)), ('0117', 100.80, 101.90, ('sync', 2))])
beat('CH2', '"I\'m looking at the gas station. Oh, thank the Lord." / LOCK-ON MCLAREN 600LT, doors up at the pump, VO "Let\'s see how much gas that gets us. That should be more than enough."', [
    ('0119', 3.2, 4.5, 1.0, 'SYNC'),
    ('0119', 64.5, 3.6, 1.0, 'LOCK: the McLaren at the pump, doors up'),
], [('0119', 3.30, 7.60, ('sync', 0)), ('0119', 134.75, 137.75, ('at', 4.85))])
beat('CH2', '"Man, so I think for the last bit of the drive, I\'m gonna have you guys like in the back" / "so you guys can get some cool little POVs"', [
    ('0119', 227.6, 6.4, 1.0, 'SYNC: at the pump'),
    ('0119', 246.9, 3.6, 1.0, 'SYNC'),
], [('0119', 227.70, 233.85, ('sync', 0)), ('0119', 247.15, 250.40, ('sync', 1))])

# ---------------------------------------------------------------- CH3 HOME STRETCH (07:32)
beat('CH3', 'CH3 slam; "Hopefully this don\'t fly off, good lord."', [
    ('0121', 20.9, 3.4, 1.0, 'SYNC: the camera goes on the rear deck'),
], [('0121', 21.00, 24.15, ('sync', 0))])
beat('CH3', 'HUD STRIP-1: rear-deck POV, the engine (nat), SOMEWHERE IN NEVADA', [
    ('0121', 120.0, 8.0, 1.0, 'STRIP-1: rear-deck cam on the road'),
])
beat('CH3', 'VO 0118 (07:13): "Trip has been cool" / "it\'s been pretty fire, really nice scenery." / "It was lots of beautiful trees and scenery" / "I can\'t believe I just did the whole thing."', [
    ('0121', 40.0, 3.0, 1.0, 'rear-deck cam'),
    ('0121', 150.0, 3.0, 1.0, 'rear-deck cam'),
    ('0121', 180.0, 3.0, 1.0, 'rear-deck cam'),
    ('0121', 60.0, 3.0, 1.0, 'rear-deck cam'),
], [('0118', 61.85, 63.30, ('at', 0.2)), ('0118', 69.45, 73.50, ('at', 1.9)), ('0118', 75.55, 78.10, ('at', 6.2)),
    ('0118', 80.70, 82.75, ('at', 9.0))])
beat('CH3', '"we\'re back in Vegas, baby" (index speaker label OTHER 0.61: lead to confirm by ear it is him) / the freeway', [
    ('0122', 4.7, 3.8, 1.0, 'SYNC'),
    ('0122', 310.0, 2.0, 1.0, 'the freeway (music)'),
], [('0122', 7.00, 8.24, ('sync', 0))])
beat('CH3', 'HUD STRIP-2: INTO LAS VEGAS (09:04)', [
    ('0122', 451.0, 8.0, 1.0, 'STRIP-2: the freeway into Las Vegas'),
])
beat('CH3', 'PLACE 09:10 ARRIVED · SUPERCAR EXPERIENCE: "we just got back to the shop." / "Yeah, let me take my stuff out of here." / '
     '"So that concludes today\'s episode. We dropped it off here at Supercar Experience at headquarters." / "So I hope you guys enjoyed that. And until next time, peace."', [
    ('0123', 4.7, 1.7, 1.0, 'SYNC: at the SE Las Vegas shop'),
    ('0123', 13.7, 3.0, 1.0, 'SYNC'),
    ('0123', 39.7, 5.6, 1.0, 'SYNC'),
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
        dialog.append(dict(beat=i, src=src, **{'in': a}, out=b_, t=round(at, 3), trim_pauses=None))
    if b['ch'] in TITLES and not any(c['title'] == TITLES[b['ch']][0] for c in chapters):
        chapters.append(dict(t=round(t0, 3), title=TITLES[b['ch']][0], clock=''))
    beats.append(dict(i=i, ch=b['ch'], t0=round(t0, 3), t1=round(t, 3), note=b['note']))
shots.append(dict(beat=len(B), src='card', **{'in': 0}, out=END_CARD, speed=1.0, t=round(t, 3), dur=END_CARD, note='END CARD'))
beats.append(dict(i=len(B), ch='END', t0=round(t, 3), t1=round(t + END_CARD, 3), note='end card'))
dur = round(t + END_CARD, 3)
# shots in sync must not be shorter than their dialog piece
for d in dialog:
    assert d['t'] >= -1e-6, d
# fetch slack (not played; mix.py does not read audio_extra): spare source around the shots whose hands / phone / speedometer
# can only be checked on the mezzanines, plus a pool of road-only cutaways (rear-deck cam 0121, freeway 0122), so any shot
# can be slipped or covered without a second Dropbox round trip
SLACK = [('0116', 0.0, 163.0), ('0117', 44.0, 118.0), ('0119', 0.0, 96.0), ('0119', 133.0, 139.0), ('0119', 222.0, 253.0), ('0121', 18.0, 200.0),
         ('0122', 0.0, 16.0), ('0122', 290.0, 330.0), ('0122', 430.0, 480.0), ('0123', 0.0, 61.0), ('0115', 6.0, 30.0),
         ('0114', 0.0, 48.0), ('0111', 0.0, 60.0), ('0112', 10.0, 60.0), ('0105', 14.0, 29.0), ('0106', 0.0, 8.0),
         ('0106', 280.0, 293.0), ('0106', 62.0, 69.0), ('0113', 100.0, 135.0), ('0118', 60.0, 84.0)]
extra = [dict(beat=-1, src=s_, **{'in': a}, out=b_, t=0.0, kind='slack') for s_, a, b_ in SLACK]
edl = dict(fps='30000/1001', size=[1080, 1920], duration=dur, chapters=chapters, shots=shots, dialog=dialog,
           audio_extra=extra, beats=beats, warnings=[])
json.dump(edl, open(os.path.join(ROOT, 'data', 'edl.json'), 'w'), indent=1)
print(f'{len(shots)} shots, {len(dialog)} dialog pieces, {dur:.2f} s ({int(dur // 60)}:{dur % 60:05.2f})')
for c in chapters:
    print(' chapter', c)
