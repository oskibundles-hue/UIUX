#!/usr/bin/env python3
"""make_edl.py -- Chapter 8 "Las Vegas" of the One-way ticket long-form (Lifestyle, @nq.young), as data -> edl.json in
ch4's schema (plus `title` and `frames`). Chapter 7 ends on 0119 "Donezo." at the pump; the spoken outro ends the video.

Spans from ../PLAN.md, chapter 8, in camera-clock order (0119 Pahranagat -> 0121 desert road -> 0122 Las Vegas -> 0123
the shop). The route map is out of v1 (brief).

Changes from the PLAN spans, each for a reason:
  * 0119 227.8-245 becomes 227.80-233.75 "...I'm gonna have you guys like in the back": the rest (238.5-245) says the
    same thing twice more; the line hands straight to the rear-deck camera montage.
  * 0121 80-120: a montage of six 2.4-2.6 s pieces (leaving the station, the truck stop, trees, the green road, the
    desert hills, the valley), no talk; the bed comes up here (music comes up only in montages).
  * 0122 skyline 552-570 and 582-600: five 3 s pieces, no talk, bed up; the camera sound is MUTED under them because
    flags.json has car-stereo blocks at 510-552 and 570-582 on either side (the stereo could bleed into the edges).
  * 0123 4.1-12.4 becomes 4.90-12.02: "Apparently not," answers someone off camera before the clip starts, so the
    piece starts on "we just got back to the shop"; it ends on "honestly," (the "but" at 12.05 leads nowhere).
  * 0123 17.1-27.2 becomes 17.05-24.20: "Pretty, pretty gnarly." (25.8-27.2) repeats the line before it.
  * Outro 0123 39.9-59.4 as filmed (PLAN: "use what was filmed"); it names the shop out loud ("We dropped it off here
    at Supercar Experience at headquarters"): flagged to the lead (Ch3 cut a spoken SE line, PLAN 3.2).
Blur (Omarie, 2026-10-09, overrides the brief: "only blur should be the dash"): the only blur in Ch5-8 is the dashboard
(cluster, speedometer, centre screen) while the car is moving. Chapter 8 shows no dashboard while moving (the 0121/0122
montage camera sits on the rear deck looking back; the 0119 and 0123 selfies are parked), so it has no blur: no plate,
billboard, sign or phone-number blur.
Music flags (flags.json): the only block flags on these clips are 0119 104.2-129.6 (cashier, stranger) and the 0122
car-stereo windows (96-132, 180-192, 420-492, 510-552, 570-582): none touches a used range; the assert below checks.
Re-run: python3 make_edl.py
"""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TRD = '/home/user/day-owt/tr'
AUD = '/home/user/day-owt/aud'
FPS = 30000 / 1001
TAIL = 0.40
CH, CH_NAME, TITLE = 'CH8', 'Las Vegas', 'LAS VEGAS'
CLOCK = '0119 Pahranagat Valley (selfie at the Shell) to 0123 the shop, DJI camera clock'
BEAT = 'CH8 Las Vegas: an hour and some change out -> the last bit from the back -> desert road montage -> seven minutes out -> the skyline -> back at the shop -> the outro, peace'

SHOTS = [
    ('0119', 84.70, None, 1.0, 'SHELL STATION SELFIE (parked), under the "LAS VEGAS" title: "Pahranagat Valley, we are about an hour and some change from Vegas. We\'re in the final countdown."', (84.70, 91.47)),
    ('0119', 227.80, None, 1.0, 'AT THE PUMP: "Man, so I think for the last bit of the drive, I\'m gonna have you guys like in the back"', (227.80, 233.75)),
    ('0121', 80.0, 2.4, 1.0, 'MONTAGE rear deck: leaving the station', None),
    ('0121', 87.0, 2.4, 1.0, 'MONTAGE rear deck: the truck stop', None),
    ('0121', 93.5, 2.4, 1.0, 'MONTAGE rear deck: trees', None),
    ('0121', 99.0, 2.4, 1.0, 'MONTAGE rear deck: the green road', None),
    ('0121', 107.0, 2.4, 1.0, 'MONTAGE rear deck: the desert hills', None),
    ('0121', 115.0, 2.6, 1.0, 'MONTAGE rear deck: the valley', None),
    ('0122', 43.25, None, 1.0, 'REAR CAMERA (sound in sync): "...to the shop. Seven minutes out."', (43.25, 47.37)),
    ('0122', 552.6, 3.0, 1.0, 'MONTAGE skyline: Las Vegas behind, the dump truck closing in', None),
    ('0122', 558.5, 3.0, 1.0, 'MONTAGE skyline: cars passing', None),
    ('0122', 565.0, 3.0, 1.0, 'MONTAGE skyline', None),
    ('0122', 584.0, 3.0, 1.0, 'MONTAGE skyline', None),
    ('0122', 594.5, 3.0, 1.0, 'MONTAGE skyline: the van passing', None),
    ('0123', 4.90, None, 1.0, 'BACK AT THE SHOP: "we just got back to the shop. Joey and John here. I swear we got that last part. I don\'t know what we got, honestly,"', (4.90, 11.97)),
    ('0123', 17.05, None, 1.0, 'JUMP: "Hopefully I got the driving part. Damn. The last little driving piece is pretty gnarly. I\'m not gonna lie."', (17.05, 23.97)),
    ('0123', 39.90, None, 1.0, 'THE OUTRO (as filmed): "So that concludes today\'s episode... And until next time, peace."', (39.90, 59.38)),
]
TITLE_AT = 0
OUT = {('0123', 4.90): 12.02, ('0123', 17.05): 24.20, ('0123', 39.90): 59.80}
MUTE = [('0122', 552.0, 600.0, 'skyline: car-stereo blocks either side (flags.json 510-552, 570-582)')]
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
