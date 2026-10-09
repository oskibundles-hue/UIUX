#!/usr/bin/env python3
"""make_edl.py -- Chapter 6 "1:29 a.m." (the SETBACK) of the One-way ticket long-form (Lifestyle, @nq.young), as data ->
edl.json in ch4's schema (plus `title` and `frames`). Chapter 5 ends on 0112 "It's light work."

Spans from ../PLAN.md, chapter 6. Out-points from the voice-band envelope (measure() below), as in Ch5.
Changes from the PLAN spans, each for a reason:
  * 0114 3.9-30.5 is five pieces (3.80-5.25, 7.40-11.05, 13.20-16.85, 19.70-22.70, 25.60-30.55): the 1.6-3.0 s silent
    pauses between his lines are cut (jump cuts on the static night cabin), so the half-awake talk keeps moving.
  * 0114 87.9-89 runs 87.80-89.0 "My wrist hurts." ("Oh shit" before it, 86.7-87.6, is not used; "I don't know if I was
    like..." after it trails off and is not used).
  * 0115: 2.3-14.7, then 30.7-36.8, and it ENDS on 14.7-22.45. PLAN's 14.7-30.7 is "I'm not gonna lie to you, car still
    holding up good, brand new engine in her, she's still doing great" (to 22.1; medium.en hears the words small.en
    stretched over 19.9-30.7), then "post it up at the uh, what is this, Sinclair... she's doing great so" (24-29.6),
    which repeats and names a gas brand: cut. Ending on "she's still doing great" closes the setback on the turn.
    Clock order inside 0115 is broken for that one line (it runs before 30.7-36.8 in the camera, after it here); PLAN
    asks both for clock order and for this ending, and the ending reads as the point of the chapter.
  * 0115 is sideways for the whole span used (the 0115 mezzanine is 1280x720 with the picture on its side, not only
    0:34-0:40 as day.md says), so every 0115 shot is turned clockwise (look.json rot 'cw') and the 16:9 window is cut
    from the upright 720x1280 frame around his face (cy per shot).
Music flags (flags.json): 0114's only block flag is 180-252 (stereo), outside 3.8-89.0; 0115 has none.
Re-run: python3 make_edl.py
"""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TRD = '/home/user/day-owt/tr'
AUD = '/home/user/day-owt/aud'
FPS = 30000 / 1001
TAIL = 0.40
CH, CH_NAME, TITLE = 'CH6', '1:29 a.m.', '1:29 A.M.'
CLOCK = '01:29:05 (0114) to 02:46:38 (0115), DJI camera clock (time zone to be checked by nq-facts)'
BEAT = 'CH6 1:29 a.m., the setback: woke up from a McLaren nap in a parking lot, wrist hurts -> 5-6 hours out, freezing -> car still holding up'

SHOTS = [
    ('0114', 3.70, None, 1.0, 'NIGHT CABIN (parked, Club 93 lot), under the "1:29 A.M." title: "I\'m not gonna lie, chat,"', (3.70, 5.20)),
    ('0114', 7.40, None, 1.0, 'JUMP: "I definitely did take a nice McLaren nap."', (7.40, 11.00)),
    ('0114', 13.20, None, 1.0, 'JUMP: "I\'m in the Club 93 parking lot."', (13.20, 16.80)),
    ('0114', 19.70, None, 1.0, 'JUMP: "Pretty nice parking lot. Reminds me of Vegas."', (19.70, 22.60)),
    ('0114', 25.60, None, 1.0, 'JUMP: "I took a nice, supposed to be hour nap, probably hour and 30 minute nap."', (25.60, 30.50)),
    ('0114', 87.80, None, 1.0, 'CABIN (parked, phone in hand): "My wrist hurts."', (87.80, 89.00)),
    ('0115', 1.78, None, 1.0, 'GAS STOP, 02:46 (selfie, camera on its side: turned upright): "Alright chat, so we\'re about six hours out, six-five hours out, gassing up. Dude, it is freezing."', (1.78, 14.70)),
    ('0115', 31.15, None, 1.0, 'JUMP: "Whoo, six more hours it is. When I say it\'s cold, it\'s cold outside, like it\'s really cold outside, so"', (31.15, 36.75)),
    ('0115', 15.00, None, 1.0, 'END (back in the take): "I\'m not gonna lie to you, car still holding up good, brand new engine in her, she\'s still doing great."', (15.00, 22.10)),
]
TITLE_AT = 0
# 0114 is a quiet half-awake voice in a silent cabin: the envelope's +12 dB rule misses it, so its outs are set by hand
# from the +6 dB frames (voiced 4.0-5.4, 7.5-10.9, 13.3-16.7, 20.0-22.6, 25.8-30.45, env.py). 0115 "freezing" and "I'm"
# run together: "freezing" is voiced to ~15.0 and medium.en puts "I'm" at 15.06, so the first piece ends and the last
# one starts at 15.0 (medium.en: "...she's still doing great" ends 22.1, then silence to 24.0).
OUT = {('0114', 3.70): 5.65, ('0114', 7.40): 11.15, ('0114', 13.20): 16.95, ('0114', 19.70): 22.85, ('0114', 25.60): 30.75,
       ('0115', 1.78): 15.02}
MUTE = []
BLEEP = []
ASR_ONLY = set()
ROT = {'0115': 'cw'}


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
