#!/usr/bin/env python3
"""make_edl.py -- Chapter 5 "Nampa, Idaho · night" of the One-way ticket long-form (Lifestyle, @nq.young), as data ->
edl.json in ch4's schema (shots / dialog / audio_extra, plus `title` and `frames`), which mix.py, words_medium.py and
render.py read. Chapter 4 ends on 0100 "We're in Oregon!"; this one follows it.

Spans from ../PLAN.md, chapter 5 (cut to the content, no padding). Out-points are set from the voice-band envelope
(300-3400 Hz, 50 ms frames) of /home/user/day-owt/aud/<clip>.m4a by measure() below: each out leaves up to TAIL after the
last voiced frame and stops 50 ms before the next voice onset; edl.json records onset / voice_end / next onset per piece.
Changes from the PLAN spans, each for a reason:
  * 0105 4.9-13.8 becomes 4.92-6.45, 7.70-11.62 and 12.45-13.8: the 1.3 s silent pause before "To In-N-Out" goes, and
    "God damn" (11.9-12.3) is cut, as Ch4 cut its swear. Jump cuts in the selfie.
  * 0107 232.4-237.7 runs from 232.30 (voice onset 232.35).
  * 0112 13.8-32.6 becomes 13.8-19.85, 23.10-26.30 and 27.95-35.55: the 3.5 s pause (he taps the phone) and "Oh shit"
    (26.5-27.0) are cut, and the piece runs on to "It's light work." (34.3-35.2), which ends the chapter on a beat;
    "We're going to see..." (35.9) is not used.
  * The "NAMPA, IDAHO · NIGHT" title sits on the first night shot (0105), not on 0102: 0102 is the Oregon gas stop in
    daylight (16:47 camera clock), so the place would be wrong there.
Music flags (flags.json): no block flag on 0102, 0105, 0106 283-297 (the 0106 stranger block is 62.4-115.9), 0107
232-238 (the 0107 music blocks are 14.6-47.6, 107.8-133.7, 175.8-222.0) or 0112 13-36 (music block 90-102); the
assert below checks every block flag.
Re-run: python3 make_edl.py
"""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TRD = '/home/user/day-owt/tr'
AUD = '/home/user/day-owt/aud'
FPS = 30000 / 1001
TAIL = 0.40
CH, CH_NAME, TITLE = 'CH5', 'Nampa, Idaho · night', 'NAMPA, IDAHO · NIGHT'
CLOCK = '16:47 (0102, Oregon) to 20:16 (0112), DJI camera clock'
BEAT = 'CH5 Nampa, Idaho, night: snacks and the plan to run it straight -> In-N-Out at last -> where we are -> oil -> gassed up, 9 h 27 m to go, light work'

# (src, in, dur, speed, note, sync-dialog (in, asr_out) or None). dur None = to the dialog out; 'REST' = picture-only
# cutaway to the end of the previous dialog piece.
SHOTS = [
    ('0102', 17.40, None, 1.0, 'OREGON GAS STOP (selfie stick, parked): "As you can see I got my Red Bull and my snacks because we are going to starve ourselves until we can get to In-N-Out, that\'s the goal."', (17.40, 25.40)),
    ('0102', 58.40, None, 1.0, 'SELFIE at the pump: "I don\'t think I\'m going to go to sleep. I think I\'m just gonna run it the whole way there."', (58.40, 62.70)),
    ('0105', 4.92, None, 1.0, 'NIGHT, In-N-Out lot (selfie), under the "NAMPA, IDAHO · NIGHT" title: "We finally made it."', (4.92, 6.20)),
    ('0105', 7.70, None, 1.0, 'JUMP: "To In-N-Out. Appreciate you. Thank you. We finally gonna eat."', (7.70, 11.40)),
    ('0105', 12.45, None, 1.0, 'JUMP (past "God damn"): "I\'ve been trying to eat all day."', (12.45, 13.82)),
    ('0106', 283.30, None, 1.0, 'LOT (camera on the car, parked; he leans on it with his phone): "...to let you know where I\'m at, I am in Nampa, Idaho, currently at Treasure Valley Marketplace just west of Boise, looking at about 300 miles from Sandy, five hours away."', (283.30, 296.50)),
    ('0107', 232.30, None, 1.0, 'IN-N-OUT TABLE (static, eating): "I gotta have to put some actual oil inside the car because like it\'s been like over 500 miles."', (232.30, 237.70)),
    ('0112', 13.80, None, 1.0, 'CABIN (parked at the pump, door up): "We gots up, shawty! You feel me? We are gassed up, we are ready to leave."', (13.80, 19.50)),
    ('0112', 23.10, None, 1.0, 'JUMP: "So, right here as you can see." (shows the route on his phone)', (23.10, 26.10)),
    ('0112', 27.95, None, 1.0, 'JUMP (past "Oh shit"): "We got 9 hours, 27 minutes to go. It\'s light work."', (27.95, 35.20)),
]
TITLE_AT = 2          # the title card sits on this shot (+0.6 s)
OUT = {('0105', 7.70): 11.82,   # "eat." voiced to 11.75; "God damn" from 11.90 (cut)
       ('0112', 13.80): 19.85}  # "leave." voiced to 19.60; a non-voice sound (door/chime) runs 20.1-22.2
# 0102 58.40: "break." (the previous sentence) is voiced to 58.30; "I" starts 58.55
MUTE = []
BLEEP = []
ASR_ONLY = set()
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
