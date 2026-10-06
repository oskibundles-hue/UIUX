#!/usr/bin/env python3
"""make_edl.py -- the Part 1 cut as data -> data/edl.json (the Sep 15 rally v2 EDL schema).

Each beat lists its picture (src, in, dur[, speed]) back to back and its dialog pieces (src, in, out) placed at an offset
from the beat start ('at'), or in sync with a shot ('sync': shot index inside the beat, the piece's own source time
decides where it lands). Source times are seconds into the camera file (DJI_20260926HHMMSS_NNNN_D.MP4); dialog edges
come from the day's word timings (days/trip-0926/tr, faster-whisper small.en) and were re-checked with medium.en.
Re-run after editing: python3 tools/make_edl.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30000 / 1001

# (chapter, note, shots [(src, in, dur, speed, note)], dialog [(src, in, out, place)], nat [(src, in, out, rel_t)])
# place: ('at', seconds from beat start) or ('sync', shot index in this beat)
B = []


def beat(ch, note, shots, dialog=(), tail=0.0):
    B.append(dict(ch=ch, note=note, shots=shots, dialog=list(dialog), tail=tail))


# ---------------------------------------------------------------- OPEN: the hook, his own line over the drive
beat('OPEN', 'hook panel on frame 0; VO 0075 (04:38, leaving home): "So we are heading to Seattle Washington to go pick up a McLaren 600 LT"', [
    ('0097', 10.4, 2.2, 1.0, 'hook frame: snow peaks ahead, cabin cam'),
    ('0095', 36.0, 1.8, 1.0, 'forest road'),
    ('0096', 39.0, 1.8, 1.0, 'mountains open up (hands on the wheel)'),
    ('0099', 172.0, 1.8, 1.0, 'open plains'),
    ('0102', 15.6, 2.0, 1.0, 'the McLaren at the pump, on "McLaren 600 LT"'),
], [('0075', 69.40, 76.72, ('at', 2.0))])

# ---------------------------------------------------------------- CH1 WHEELS UP (04:56)
beat('CH1', '"at the airport right now as you can see" / "a little tired, but we up now"', [
    ('0076', 58.0, 4.2, 1.0, 'terminal, walking in'),
    ('0077', 20.0, 3.6, 1.0, 'escalator down'),
], [('0076', 14.38, 18.14, ('at', 0.5)), ('0076', 25.25, 28.56, ('at', 4.45))])
beat('CH1', '"This is our Supercar Experience vlog. We usually transport our vehicles, but I\'m driving this one, look at us." NAME LOCK', [
    ('0076', 40.0, 11.2, 1.0, 'SYNC: at the terminal doors'),
], [('0076', 40.10, 51.10, ('sync', 0))])
beat('CH1', 'MetaMuse weather: "it says no rain, good day to pick up your McLaren" (the line before it, "Seattle\'s ... well today", is out: its middle word is not confirmed by ear, small.en and medium.en both give "training"; the first shot stays as the phone-reading picture)', [
    ('0077', 57.8, 1.7, 1.0, 'SYNC: reading his phone'),
    ('0077', 67.7, 3.0, 1.0, 'SYNC'),
], [('0077', 67.64, 70.44, ('sync', 1))])
beat('CH1', '"I\'m gonna try to put some animations in this ... make like a flying animation"', [
    ('0079', 51.4, 2.1, 1.0, 'SYNC: at the gate'),
    ('0078', 30.0, 4.6, 1.0, 'the gate area'),
], [('0079', 51.56, 53.34, ('sync', 0)), ('0079', 57.84, 62.96, ('at', 2.3))])
beat('CH1', '"I\'m finally getting on the plane."', [
    ('0081', 1.6, 3.4, 1.0, 'SYNC: the jet bridge'),
], [('0081', 2.90, 4.66, ('sync', 0))])
beat('CH1', 'CLOCK STAMP 09:00 IN THE AIR: window shots, engine nat', [
    ('0082', 2.0, 2.4, 1.0, 'window: wing and the city'),
    ('0082', 12.0, 2.6, 1.0, 'window: coming in low'),
])
beat('CH1', '"But we finna get in the Uber and I\'m finna pick up this car"', [
    ('0084', 88.8, 5.4, 1.0, 'SYNC: arrivals, walking'),
], [('0084', 89.04, 93.94, ('sync', 0))])

# ---------------------------------------------------------------- CH2 THE PICKUP (10:14)
beat('CH2', 'CH2 slam over the red shop building; "How you doing? I\'m here to pick up the 600 LT ... from Supercar Experience. I think you guys just put a brand new engine in it. I gotta drive it all the way back to Vegas."', [
    ('0087', 4.0, 2.6, 1.0, 'the red shop building, cars out front'),
    ('0087', 44.3, 3.6, 1.0, 'SYNC: at the door'),
    ('0087', 52.0, 1.7, 1.0, 'SYNC'),
    ('0087', 54.9, 5.0, 1.0, 'SYNC'),
], [('0087', 44.42, 47.80, ('sync', 1)), ('0087', 52.10, 53.52, ('sync', 2)), ('0087', 55.04, 59.74, ('sync', 3))])
beat('CH2', '"So they got one more hour until they\'re done with the car."', [
    ('0088', 0.2, 5.2, 1.0, 'SYNC: inside the shop'),
], [('0088', 0.40, 5.22, ('sync', 0))])
beat('CH2', '"right now he\'s gonna go grab the 600 LT from the warehouse"', [
    ('0089', 140.5, 7.0, 1.0, 'SYNC: outside the shop'),
], [('0089', 140.55, 147.48, ('sync', 0))])
beat('CH2', 'THE CAR ARRIVES (nat): LOCK-ON MCLAREN 600LT', [
    ('0090', 15.0, 5.6, 1.0, 'the McLaren rolls in (camera on its side: rotated)'),
])
beat('CH2', '"but we have the 600LT that we will be driving from Seattle to Vegas." / "This is the interior chat."', [
    ('0090', 103.8, 5.6, 1.0, 'SYNC (rotated)'),
    ('0090', 114.6, 3.4, 1.0, 'SYNC: the red interior (rotated)'),
], [('0090', 103.90, 109.34, ('sync', 0)), ('0090', 114.66, 116.14, ('sync', 1))])
beat('CH2', '"We are in the 600 LT" / "Man, it\'s gonna be a long drive."', [
    ('0091', 1.9, 3.3, 1.0, 'SYNC: first sit, red seats'),
    ('0091', 14.8, 2.8, 1.0, 'SYNC'),
], [('0091', 2.04, 5.10, ('sync', 0)), ('0091', 14.90, 17.46, ('sync', 1))])
beat('CH2', '"Let\'s make sure this top work" -> the roof goes down', [
    ('0092', 7.8, 5.0, 'ramp', 'SYNC then the roof opening at speed'),
], [('0092', 7.93, 9.30, ('sync', 0))])
beat('CH2', '"It is beautiful out here, like gorgeous. Like I\'m talking gorgeous." / "we\'re on our way ... to Las Vegas"', [
    ('0093', 4.1, 8.2, 1.0, 'SYNC: driving, passenger-side cam'),
], [('0093', 4.42, 11.72, ('sync', 0))])

# ---------------------------------------------------------------- CH3 HIT THE ROAD (12:10)
beat('CH3', 'CH3 slam; "I like it. I want y\'all to get the vibe. So you feel me? We gonna get the vibes right now."', [
    ('0094', 2.2, 3.2, 1.0, 'SYNC: him, then the camera turns to the road'),
    ('0095', 33.9, 2.2, 1.0, 'CUTAWAY over 116.0-118.2: he holds and taps a lit phone at a junction (0094 5.6-7.6 s), so the picture is the road (his audio and captions run on)'),
    ('0094', 7.6, 1.6, 1.0, 'SYNC: back to him, hand off the phone'),
], [('0094', 2.34, 9.06, ('sync', 0))])
beat('CH3', 'the vibes: forest montage (music up, nat under)', [
    ('0095', 46.0, 1.7, 1.0, 'forest'),
    ('0095', 52.0, 1.6, 1.0, 'forest, the road opens'),
])
beat('CH3', '"Man, I miss trees and nature. Good lord. I just know they got some fire hiking trails out here."', [
    ('0095', 28.0, 5.8, 1.0, 'forest road (his line from 0094 over it: hands on the wheel here)'),
], [('0094', 156.98, 162.40, ('at', 0.2))])
beat('CH3', 'HUD-1 STRIP: into the mountains (13:28)', [
    ('0096', 32.6, 8.0, 1.0, 'HUD-1: mountains open up (both hands on the wheel; a phone is held from 42 s)'),
])
beat('CH3', 'snow peaks', [
    ('0097', 16.0, 2.0, 1.0, 'snow peaks'),
])
beat('CH3', 'HUD-1 STRIP: open road (15:42)', [
    ('0099', 166.0, 8.0, 1.0, 'HUD-1: open plains'),
])
beat('CH3', '"I just wanted to let you guys know. We\'re in Oregon!" PLACE: JUST GOT INTO OREGON', [
    ('0100', 33.0, 4.4, 1.0, 'SYNC: cabin cam'),
], [('0100', 34.46, 36.96, ('sync', 0))])
beat('CH3', '"I just pulled over so I can put the top down, I mean the top back up cuz my ears are ringing"', [
    ('0101', 2.6, 5.8, 1.0, 'SYNC: pulled over'),
], [('0101', 2.74, 8.26, ('sync', 0))])
beat('TEASE', 'the fuel stop (16:47): "Gassing up the McLaren 600 LT right now" / Red Bull, snacks, In-N-Out / "All right chat, so we are about to keep on going" -> TO BE CONTINUED', [
    ('0102', 4.4, 3.8, 1.0, 'SYNC'),
    ('0102', 17.3, 8.3, 1.0, 'SYNC: Red Bull and snacks'),
    ('0102', 81.6, 5.6, 1.0, 'SYNC: keep on going (tease card)'),
], [('0102', 4.50, 8.12, ('sync', 0)), ('0102', 17.40, 25.46, ('sync', 1)),
    ('0102', 81.74, 86.64, ('sync', 2))])
END_CARD = 5.4

shots, dialog, beats, chapters = [], [], [], []
TITLES = {'CH1': ('WHEELS UP',), 'CH2': ('THE PICKUP',), 'CH3': ('HIT THE ROAD',)}
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
# fetch slack (not played; mix.py does not read audio_extra): extra source around the HUD shots, the car reveal and
# the hook frame, so a shot can be slipped a few seconds (phone in hand, a plate, a better frame) without a new fetch
SLACK = [('0096', 32.0, 52.0), ('0099', 158.0, 182.0), ('0090', 10.0, 30.0), ('0097', 4.0, 22.0), ('0102', 12.0, 28.0)]
extra = [dict(beat=-1, src=s_, **{'in': a}, out=b_, t=0.0, kind='slack') for s_, a, b_ in SLACK]
edl = dict(fps='30000/1001', size=[1080, 1920], duration=dur, chapters=chapters, shots=shots, dialog=dialog,
           audio_extra=extra, beats=beats, warnings=[])
json.dump(edl, open(os.path.join(ROOT, 'data', 'edl.json'), 'w'), indent=1)
print(f'{len(shots)} shots, {len(dialog)} dialog pieces, {dur:.2f} s ({int(dur // 60)}:{dur % 60:05.2f})')
for c in chapters:
    print(' chapter', c)
