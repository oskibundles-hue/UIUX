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

# part1 v2, fix A (Omarie, 6 Oct; ported from part2): every dialog piece's audio out-point is set by tail() from the word
# timestamps, not by hand: >= 350 ms (TAIL) after the last word ends (small.en, the captions' timing source), never into
# the next word (whose start is the later of the two models': whisper stretches a word over the pause before it; medium.en
# words from tools/words_medium.py). When the picture cuts before the voice ends, the voice runs on under the next shot
# (an L-cut); the build asserts that no two voices overlap. Where the next word follows too closely, NEXT_ONSET gives the
# next word's onset measured on the voice-band envelope of the clip audio (tools/onsets.py), which then bounds the tail.
TAIL = 0.40
# the piece runs on to its real end where the next words follow with no pause (the out-point would cut a word otherwise);
# value = the new bound for the piece's words (seconds in the clip). Each added word is heard the same by both models.
EXTEND = {
    ('0075', 69.40): 80.0,    # "... McLaren 600 LT or Supercar Experience" (no pause after "LT"; both models: "or Supercar experience")
    ('0077', 67.64): 71.8,    # "... pick up your McLaren, it's crazy." (no pause after "McLaren"; both models: "it's crazy")
    ('0079', 57.84): 63.85,   # "... make like a flying animation, like all that stuff." (no pause; both: "like all that stuff")
    ('0102', 81.74): 89.0,    # "... keep on going with our drive. See ya!" (both models on a re-run, 6 Oct; under the end card)
}
# where whisper stretches the next word back over a real pause, the next onset measured on the voice-band envelope of the
# clip audio (tools/onsets.py, checked by eye on the 10 ms envelope) bounds the tail instead
NEXT_ONSET = {
    ('0076', 14.38): 19.52,   # small.en's "pretty [18.12-19.06]" is a stretched word; the envelope is down 18.2-19.5
    ('0089', 140.55): 148.45, # both models' "and [147.5-148.7]" is stretched; the envelope is down 147.75-148.45
    ('0101', 2.74): 9.28,     # both models' "and [8.2-9.5]" is stretched; the envelope is down 8.4-9.25
}
MED = json.load(open(os.path.join(ROOT, 'data', 'words_medium.json')))
# small.en words for windows the day index missed (re-run on the window, small.en beam 5, agrees with medium.en)
FIXW = json.load(open(os.path.join(ROOT, 'data', 'words_small_fix.json')))
TRD = '/home/user/day/tr'
AUD = '/home/user/day/aud'
VEND_MAX = 0.40     # the measured end of voice moves the last word's end later by at most this much


def small_words(src):
    t = json.load(open(os.path.join(TRD, f'{src}.json')))
    sm = [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]
    fx = FIXW.get(src, [])
    if fx:
        a, b = fx[0][0], fx[-1][1]
        sm = sorted([w for w in sm if not (a - 0.01 <= w[0] <= b)] + [[w[0], w[1], w[2]] for w in fx])
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


def beat(ch, note, shots, dialog=(), tail=0.0):
    B.append(dict(ch=ch, note=note, shots=shots, dialog=list(dialog), tail=tail))


# ---------------------------------------------------------------- OPEN: the hook, his own line over the drive
beat('OPEN', 'hook panel on frame 0; VO 0075 (04:38, leaving home): "So we are heading to Seattle Washington to go pick up a McLaren 600 LT"', [
    ('0097', 10.4, 2.2, 1.0, 'hook frame: snow peaks ahead, cabin cam'),
    ('0095', 36.0, 1.8, 1.0, 'forest road'),
    ('0096', 39.4, 1.8, 1.0, 'mountains open up (hands on the wheel; v2: was 39.0, inside the CH3 HUD shot, which now starts at 31.4)'),
    ('0099', 175.0, 1.8, 1.0, 'open plains (v2: was 172.0, inside the CH3 HUD shot 166-174)'),
    ('0102', 15.6, 1.7, 1.0, 'the McLaren at the pump, on "McLaren 600 LT" (v2: ends 17.3, where the TEASE shot starts)'),
    ('0097', 4.6, 3.2, 1.0, 'v2: snow road, cabin cam, under "... or Supercar Experience" (the line now runs to its end)'),
], [('0075', 69.40, 76.72, ('at', 2.0))])

# ---------------------------------------------------------------- CH1 ONE-WAY TICKET (04:57; v1 read WHEELS UP)
beat('CH1', '"at the airport right now as you can see" / "a little tired, but we up now"', [
    ('0076', 58.0, 4.2, 1.0, 'terminal, walking in'),
    ('0077', 20.0, 4.36, 1.0, 'escalator down (v2 fix A: longer for the tail)'),
], [('0076', 14.38, 18.14, ('at', 0.5)), ('0076', 25.25, 28.56, ('at', 4.80))])
beat('CH1', '"This is a Supercar Experience vlog. We usually transport our vehicles, but I\'m driving this one, look at us." NAME LOCK', [
    ('0076', 40.0, 11.2, 1.0, 'SYNC: at the terminal doors'),
], [('0076', 40.10, 51.10, ('sync', 0))])
beat('CH1', 'MetaMuse weather: "it says no rain, good day to pick up your McLaren" (the line before it, "Seattle\'s ... well today", is out: its middle word is not confirmed by ear, small.en and medium.en both give "training"; the first shot stays as the phone-reading picture)', [
    ('0077', 57.8, 1.7, 1.0, 'SYNC: reading his phone'),
    ('0077', 67.7, 3.8, 1.0, 'SYNC (v2 fix A: longer for the tail): "it\'s crazy." runs on under the gate'),
], [('0077', 67.64, 70.44, ('sync', 1))])
beat('CH1', '"I\'m gonna try to put some animations in this ... make like a flying animation"', [
    ('0079', 50.75, 2.75, 1.0, 'SYNC: at the gate (v2: starts 0.65 s earlier, for the tail before it)'),
    ('0078', 30.0, 5.4, 1.0, 'the gate area (v2 fix A: longer for the tail)'),
], [('0079', 51.56, 53.34, ('sync', 0)), ('0079', 57.84, 62.96, ('at', 3.25))])
beat('CH1', '"I\'m finally getting on the plane."', [
    ('0081', 1.3, 3.7, 1.0, 'SYNC: the jet bridge (v2: starts 0.3 s earlier, for the tail before it)'),
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
    ('0087', 44.3, 3.95, 1.0, 'SYNC: at the door (v2 fix A: longer for the tail)'),
    ('0087', 52.0, 1.85, 1.0, 'SYNC (v2 fix A: longer for the tail)'),
    ('0087', 54.9, 5.2, 1.0, 'SYNC (v2 fix A: longer for the tail)'),
], [('0087', 44.42, 47.80, ('sync', 1)), ('0087', 52.10, 53.52, ('sync', 2)), ('0087', 55.04, 59.74, ('sync', 3))])
beat('CH2', '"So they got one more hour until they\'re done with the car."', [
    ('0088', 0.2, 5.45, 1.0, 'SYNC: inside the shop (v2 fix A: longer for the tail)'),
], [('0088', 0.40, 5.22, ('sync', 0))])
beat('CH2', '"right now he\'s gonna go grab the 600 LT from the warehouse"', [
    ('0089', 140.5, 7.0, 1.0, 'SYNC: outside the shop'),
], [('0089', 140.55, 147.48, ('sync', 0))])
beat('CH2', 'THE CAR ARRIVES (nat): LOCK-ON MCLAREN 600LT', [
    ('0090', 15.0, 5.6, 1.0, 'the McLaren rolls in (camera on its side: rotated)'),
])
beat('CH2', '"but we have the 600LT that we will be driving from Seattle to Vegas." / "This is the interior chat."', [
    ('0090', 103.8, 6.02, 1.0, 'SYNC (rotated) (v2 fix A: longer for the tail)'),
    ('0090', 114.6, 3.4, 1.0, 'SYNC: the red interior (rotated)'),
], [('0090', 103.90, 109.34, ('sync', 0)), ('0090', 114.66, 116.14, ('sync', 1))])
beat('CH2', '"We are in the 600 LT" (v2: "Man, it\'s gonna be a long drive." and its shot are out: the next words run straight on into "We got about ..." and a figure the two models hear differently, so no clean tail)', [
    ('0091', 1.9, 3.95, 1.0, 'SYNC: first sit, red seats (v2 fix A: longer for the tail)'),
], [('0091', 2.04, 5.10, ('sync', 0))])
beat('CH2', '"Let\'s make sure this top work" -> the roof goes down', [
    ('0092', 7.8, 5.0, 'ramp', 'SYNC then the roof opening at speed'),
], [('0092', 7.93, 9.30, ('sync', 0))])
beat('CH2', '"It is beautiful out here, like gorgeous. Like I\'m talking gorgeous." / "we\'re on our way ... to Las Vegas"', [
    ('0095', 24.4, 3.57, 1.0, 'CUTAWAY over 110.03-113.6 (nq-check, 7 Oct; lead: cut away): 0093 4.1-7.67 shows his open palm with the wheel out of frame, so the picture is the road (0095 24.4-27.97: both hands on the wheel, forest road; used nowhere else in the cut); his 0093 audio and captions run on'),
    ('0093', 7.67, 4.63, 1.0, 'SYNC: driving, passenger-side cam'),
], [('0093', 4.42, 11.72, ('sync', 1))])

# ---------------------------------------------------------------- CH3 HIT THE ROAD (12:10)
beat('CH3', 'CH3 slam; "I like it. I want y\'all to get the vibe. So you feel me? We gonna get the vibes right now."', [
    ('0095', 21.2, 3.2, 1.0, 'CUTAWAY over 112.8-116.0 (round 5): he gestures with both hands off the wheel, holding the camera, car stopped (0094 2.2-5.4 s); both hands on the wheel here, car rolling through forest; 0095 21.2-24.4 is used nowhere else in the cut; his 0094 audio and captions run on'),
    ('0095', 33.8, 2.2, 1.0, 'CUTAWAY over 116.0-118.2: he holds and taps a lit phone at a junction (0094 5.6-7.6 s), so the picture is the road (his audio and captions run on)'),
    ('0094', 7.6, 1.6, 1.0, 'SYNC: back to him, hand off the phone'),
], [('0094', 2.34, 9.06, ('at', 0.14))])
beat('CH3', 'the vibes: forest montage (music up, nat under)', [
    ('0095', 47.0, 1.5, 1.0, 'forest (nq-check, 7 Oct: starts at 47.0, after the red/magenta white-balance flash at 0095 46.70-46.97)'),
    ('0095', 51.8, 1.8, 1.0, 'forest, the road opens (7 Oct: 0.2 s earlier, to keep the montage length)'),
])
beat('CH3', '"Man, I miss trees and nature. Good lord. I just know they got some fire hiking trails out here."', [
    ('0095', 28.0, 5.8, 1.0, 'forest road (his line from 0094 over it: hands on the wheel here)'),
], [('0094', 156.98, 162.40, ('at', 0.2))])
beat('CH3', 'HUD-1 STRIP: into the mountains (13:28)', [
    ('0096', 31.4, 8.0, 1.0, 'HUD-1: mountains open up (both hands on the wheel; a phone is held from 42 s; v2: was 32.6, so the hook shot 39.4-41.2 is its own span)'),
])
beat('CH3', 'snow peaks', [
    ('0097', 16.0, 2.0, 1.0, 'snow peaks'),
])
beat('CH3', 'HUD-1 STRIP: open road (15:42)', [
    ('0099', 166.0, 8.0, 1.0, 'HUD-1: open plains'),
])
beat('CH3', '"I just wanted to let you guys know. We\'re in Oregon!" PLACE: JUST GOT INTO OREGON', [
    ('0099', 158.2, 4.4, 1.0, 'CUTAWAY over the whole 0100 shot (nq-check, 7 Oct; lead: cut away): 0100 33.0-37.4 has him turned round to the camera at speed, left hand not visible, so the picture is the road (0099 158.2-162.6: both hands on the wheel, open plains, a truck passes; used nowhere else in the cut); his 0100 audio and captions run on, at the same timeline place'),
], [('0100', 34.46, 36.96, ('at', 1.46))])
beat('CH3', '"I just pulled over so I can put the top down, I mean the top back up cuz my ears are ringing"', [
    ('0101', 2.6, 6.05, 1.0, 'SYNC: pulled over (v2 fix A: longer for the tail)'),
], [('0101', 2.74, 8.26, ('sync', 0))])
beat('TEASE', 'the fuel stop (16:47): "Gassing up the McLaren 600 LT right now" / Red Bull, snacks, In-N-Out / "All right chat, so we are about to keep on going" -> TO BE CONTINUED', [
    ('0102', 4.4, 4.11, 1.0, 'SYNC (v2 fix A: longer for the tail)'),
    ('0102', 17.3, 8.55, 1.0, 'SYNC: Red Bull and snacks (v2 fix A: longer for the tail)'),
    ('0102', 81.6, 5.6, 1.0, 'SYNC: keep on going (tease card)'),
], [('0102', 4.50, 8.12, ('sync', 0)), ('0102', 17.40, 25.46, ('sync', 1)),
    ('0102', 81.74, 86.64, ('sync', 2))])
END_CARD = 5.4

shots, dialog, beats, chapters = [], [], [], []
TITLES = {'CH1': ('ONE-WAY TICKET',), 'CH2': ('THE PICKUP',), 'CH3': ('HIT THE ROAD',)}
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
# shots in sync must not be shorter than their dialog piece
for d in dialog:
    assert d['t'] >= -1e-6, d
# never reuse a source span (picture)
_sp = sorted((x['src'], x['in'], x['out']) for x in shots if x['src'] != 'card')
for p_, q_ in zip(_sp, _sp[1:]):
    assert not (p_[0] == q_[0] and q_[1] < p_[2] - 1e-6), f'source span used twice: {p_} {q_}'
# fix A: a voice may run on under the next shot (L-cut), but never into the next voice
bad = []
for p, q in zip(dialog, dialog[1:]):
    pe = p['t'] + p['out'] - p['in']
    if q['t'] - pe < 0.08:
        bad.append(f"voices overlap by {pe + 0.08 - q['t']:.2f}: {p['src']} {p['in']} (beat {p['beat']}) ends {pe:.2f}, {q['src']} {q['in']} (beat {q['beat']}) starts {q['t']:.2f}")
# every shot inside a fetched mezzanine (paths.mezz/<src>_<in>-<out>.mov)
MZ = '/home/user/day/mezz1'
if os.path.isdir(MZ):
    cuts = [(f[:4], float(f[5:-4].split('-')[0]), float(f[5:-4].split('-')[1])) for f in os.listdir(MZ) if f.endswith('.mov')]
    for x in shots:
        if x['src'] != 'card' and not any(c[0] == x['src'] and c[1] - 1e-6 <= x['in'] and x['out'] <= c[2] + 1e-6 for c in cuts):
            bad.append(f"shot {shots.index(x)} {x['src']} {x['in']}-{x['out']} is outside every mezzanine")
for m in bad:
    print('PROBLEM', m)
assert not bad
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
