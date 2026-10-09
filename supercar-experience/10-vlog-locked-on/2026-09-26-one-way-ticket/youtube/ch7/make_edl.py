#!/usr/bin/env python3
"""make_edl.py -- Chapter 7 "Sunrise · Nevada" of the One-way ticket long-form (Lifestyle, @nq.young), as data ->
edl.json in ch4's schema (plus `title` and `frames`). Chapter 6 ends on 0115 "she's still doing great."

Spans from ../PLAN.md, chapter 7, in camera-clock order (0116 06:24 -> 0119 07:25).
0116, 0117 and 0118 are driving clips: road and wind fill the voice band, so their out-points come from the word times
(ASR_ONLY: last small.en word + TAIL, 50 ms before the next word); 0119's come from the envelope.

Hands rule (Omarie, 2026-10-06; brief): one hand on the wheel while he talks is fine; a phone in hand, or both hands off
the wheel, while moving needs a cutaway. 0116 and 0117 (side camera) show the phone in his hand for most of every used
line, so those lines keep their sound and the picture cuts away to the same moment through the windscreen: a 'zoom' window
(look.json: [width fraction, centre x, centre y] of the square) on the upper right of the same camera, which holds the
windscreen and the desert and leaves his hands, the phone and the centre screen below the frame. The shots that show him
are only the ones where one hand is on the wheel and no phone is up (set from the hands check on the frame gate).

Changes from the PLAN spans, each for a reason:
  * 0116 4.6-13.0: him for the opening line, then the windscreen zoom from where the phone comes up ("let me take a
    video of that").
  * 0116 52.1-54.7: sound only, over the windscreen zoom (both hands are off the wheel: one at his chin, one gesturing).
  * 0117 74.9-81.4 and the hook 0117 100.9-113.2: sound only, over the windscreen zoom (phone in hand). The hook is
    100.85-104.15 and 111.85-113.55 (the 7 s of silence between is cut); "fuck" (103.8-104.0) is bleeped, as the
    opening's hook plan says (PLAN.md, hook 1).
  * 0118 61.9-91.2 becomes 61.85-63.55 "trip has been cool" + 69.40-73.75 + 75.50-88.35 + 89.95-91.60: "is this
    focusing on you?" (67.0-68.7, to the camera) and two 2 s pauses are cut; "shit" (79.0-79.1) is bleeped.
Music flags (flags.json): the block flags on these clips are 0116 78-96, 110-118, 146-156 (hands off) and 0117 20-34,
43-53, 0118 20-46 (phone while driving): none touches a used range; the assert below checks every block flag.
Re-run: python3 make_edl.py
"""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TRD = '/home/user/day-owt/tr'
AUD = '/home/user/day-owt/aud'
FPS = 30000 / 1001
TAIL = 0.40
CH, CH_NAME, TITLE = 'CH7', 'Sunrise · Nevada', 'SUNRISE · NEVADA'
CLOCK = '06:24:42 (0116) to 07:25:54 (0119), DJI camera clock'
BEAT = 'CH7 Sunrise, Nevada: the desert at sunrise -> 186 miles to home -> fields -> no cell service, have to make it -> the trip in his words -> the gas station, we thought we were donezo'

SHOTS = [
    ('0116', 4.55, 3.0, 1.0, 'SUNRISE, side camera, driving, under the "SUNRISE · NEVADA" title: "As of right now you see the beautiful desert..."', (4.55, 13.00)),
    ('0116', 7.55, 'REST', 1.0, 'CUTAWAY (windscreen zoom, same moment): "...You see that? Actually, let me take a video of that because it actually looks amazing" (the phone comes up)', None),
    ('0116', 51.95, None, 1.0, 'CUTAWAY (windscreen zoom; sound in sync): "186 miles till we\'re back home."', (51.95, 54.69)),
    ('0116', 121.30, None, 1.0, 'SIDE CAMERA, one hand on the wheel: "We got the beautiful view to us right here. Life\'s been good, you feel me?"', (121.30, 127.70)),
    ('0117', 74.80, None, 1.0, 'CUTAWAY (windscreen zoom, fields; sound in sync): "As you can see, it\'s just all field. And there\'s a flock of crows right in front of me that are about to get obliterated."', (74.80, 81.40)),
    ('0117', 100.85, None, 1.0, 'THE HOOK IN CONTEXT (windscreen zoom; sound in sync): "No cell service, not an SOS. Crazy as [bleep]."', (100.85, 104.00)),
    ('0117', 111.85, None, 1.0, 'JUMP: "I have to make it, we don\'t have a choice."', (111.85, 113.20)),
    ('0118', 61.85, None, 1.0, 'CABIN, rear camera, driving: "Trip has been cool..."', (61.85, 63.18)),
    ('0118', 69.40, None, 1.0, 'JUMP: "It\'s been pretty fire. Wow, really nice scenery."', (69.40, 73.42)),
    ('0118', 75.50, None, 1.0, 'JUMP: "It was lots of beautiful trees and scenery and all kinds of [bleep] out in Seattle. I can\'t believe I just did the whole thing. No, no hotel, no nothing. That was the crazy part,"', (75.50, 88.12)),
    ('0118', 89.95, None, 1.0, 'JUMP: "but you know, we thug it out."', (89.95, 91.23)),
    ('0119', 0.90, None, 1.0, 'PULLING IN (rear camera, both hands on the wheel): "Why ya chat, we Gucci. I\'m looking at the gas station. Oh, thank the Lord. Thank the Lord, that we were toast."', (0.90, 11.70)),
    ('0119', 51.90, None, 1.0, 'AT THE PUMP: "I ain\'t gonna lie, I thought we were donezo. Over with, no return, call somebody to come get us. Donezo."', (51.90, 59.14)),
]
TITLE_AT = 0
OUT = {('0117', 100.85): 104.15, ('0119', 0.90): 12.10}   # past the bleeped word; 0119 'toast.' ends 11.70, next word 12.52
MUTE = []
BLEEP = [('0117', 103.78, 104.05, 'fuck'), ('0118', 78.98, 79.14, 'shit')]
ASR_ONLY = {'0116', '0117', '0118'}
ROT = {}


def words(src):
    t = json.load(open(os.path.join(TRD, f'{src}.json')))
    return [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]


def inside(w, a, b):
    return min(w[1], b) - max(w[0], a) >= 0.15 or (a - 1e-6 <= w[0] < b - 0.1)


_ENV = {}


def envelope(src):
    """Voice-band (300-3400 Hz) level of the camera audio in 50 ms frames (dB), whole clip, cached."""
    if src not in _ENV:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{AUD}/{src}.m4a', '-af', 'highpass=f=300,lowpass=f=3400',
                              '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, '<f4'); h = 800
        n = len(x) // h
        _ENV[src] = 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    return _ENV[src]


def voiced(src, a, b):
    """Frames of [a-3, b+3] above the local floor (10th percentile) + 12 dB, as a boolean array and its start time."""
    e = envelope(src)
    i0, i1 = max(0, int((a - 3) / 0.05)), min(len(e), int((b + 3) / 0.05))
    seg = e[i0:i1]
    return seg > np.percentile(seg, 10) + 12, i0 * 0.05


def measure(src, a, b):
    """The voice end near the ASR out-point b (last voiced frame starting before b + 0.3) and the next voice onset
    after it (a gap of >= 0.15 s), and the onset at the in-point a, from the envelope: (onset, voice_end, next_onset)."""
    v, t0 = voiced(src, a, b)
    ts = t0 + np.arange(len(v)) * 0.05
    on = [t for t, q in zip(ts, v) if q and t >= a - 0.3]
    onset = on[0] if on else a
    ve = max([t + 0.05 for t, q in zip(ts, v) if q and a - 0.1 <= t < b + 0.3] or [b])
    nx = [t for t, q in zip(ts, v) if q and t >= ve + 0.15]
    return round(onset, 2), round(ve, 2), round(nx[0], 2) if nx else 1e9


WARN = []


def tail(src, a, b):
    W = words(src)
    p = [w for w in W if inside(w, a, b)]
    le = p[-1][1]
    onset, ve, no = measure(src, a, b)
    if (src, a) in OUT:
        out = OUT[(src, a)]
    elif src in ASR_ONLY:
        # driving clips: road and wind noise fill the voice band, so the envelope cannot find the voice; the out-point
        # is the last word's end (small.en) + TAIL, stopped 50 ms before the next word
        nw = [w for w in W if w[0] > p[-1][0] + 0.01 and not inside(w, a, b)]
        out = round(min(le + TAIL, (nw[0][0] if nw else 1e9) - 0.05), 2)
        ve, no = le, (nw[0][0] if nw else 1e9)
    else:
        out = round(min(max(ve, le if le - ve < 0.4 else ve) + TAIL, no - 0.05), 2)
    if out - ve < 0.25 - 1e-6:
        WARN.append(f'{src} {a}: voice ends {ve:.2f}, next onset {no:.2f}: tail {out - ve:.2f} s')
    pre = [t for t in [onset] if t < a - 0.02 and src not in ASR_ONLY]
    if pre:
        WARN.append(f'{src} {a}: voice onset {onset:.2f} is before the in-point')
    return out, round(le, 3), p, (onset, ve, no)


shots, dialog, extra = [], [], []
t = 0.0
dl_end = None
for i, (src, a, dur, sp, note, dl) in enumerate(SHOTS):
    if dl:
        out, le, p, m = tail(src, dl[0], dl[1])
        din = dl[0]
        dialog.append(dict(beat=i, src=src, **{'in': din}, out=out, t=round(t + (din - a), 3), trim_pauses=None,
                           last_word_end=le, onset_measured=m[0], voice_end=m[1], next_onset_measured=m[2], extended=False,
                           out_asr=dl[1], text=' '.join(w[2] for w in p)))
        dl_end = dialog[-1]['t'] + out - din
        if dur is None:
            dur = round(out - a, 3)
    elif dur == 'REST':
        dur = round(dl_end - t, 3)
    shots.append(dict(beat=i, src=src, **{'in': a}, out=round(a + dur * sp, 3), speed=sp, t=round(t, 3), dur=round(dur, 3),
                      note=note))
    t += dur
dur_total = round(t, 3)

# frame-exact: the chapter is a whole number of frames, so the four proxies and wavs join without drift
NF = int(round(dur_total * FPS))

# assert: no shot or audio range sits on a block flag
flags = [f for f in json.load(open('/home/user/day-owt/flags.json')) if f.get('severity') == 'block']
for s in shots + extra + dialog:
    lo, hi = s['in'], s['out']
    for f in flags:
        if f['clip'] == s['src'] and lo < f['t1'] and f['t0'] < hi:
            raise SystemExit(f'BLOCK FLAG {f["clip"]} {f["t0"]}-{f["t1"]} {f["category"]} under {s["src"]} {lo}-{hi}')
# warn: another speaker (speakers.json OTHER) inside a dialog piece
spk = json.load(open('/home/user/day-owt/speakers.json'))['clips']
for d in dialog:
    for q in spk.get(d['src'], []):
        if q['speaker'] != 'HOST' and q['start'] < d['out'] and d['in'] < q['end']:
            WARN.append(f"{d['src']} {d['in']}-{d['out']}: speaker model says {q['speaker']} ({q['score']:.2f}) at {q['start']}-{q['end']} \"{q['text']}\"")

ti = TITLE_AT
edl = dict(fps='30000/1001', size=[3840, 2160], duration=dur_total, frames=NF,
           chapters=[dict(t=0.0, title=CH_NAME, clock=CLOCK)],
           title=dict(text=TITLE, t0=round(shots[ti]['t'] + 0.6, 3), t1=round(shots[ti]['t'] + 3.9, 3)),
           shots=shots, dialog=dialog, audio_extra=extra,
           beats=[dict(i=0, ch=CH, t0=0.0, t1=dur_total, note=BEAT)],
           mute=[dict(src=s, **{'in': a}, out=b, note=n) for s, a, b, n in MUTE],
           bleeps=[dict(src=s, **{'in': a}, out=b, word=n) for s, a, b, n in BLEEP],
           rotate=ROT, warnings=WARN)
json.dump(edl, open(os.path.join(HERE, 'edl.json'), 'w'), indent=1)
print(f'shots {len(shots)}  dialog {len(dialog)}  runtime {dur_total:.2f} s ({int(dur_total // 60)}:{dur_total % 60:04.1f}), {NF} frames  '
      f'picture changes/min {60 * (len(shots) - 1) / dur_total:.1f}')
for d in dialog:
    print(f"  {d['src']} {d['in']:.2f}-{d['out']:.2f}  onset {d['onset_measured']}  voice_end {d['voice_end']}  next {d['next_onset_measured']}  | {d['text'][:70]}")
for w in WARN:
    print('WARN', w)
