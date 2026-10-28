#!/usr/bin/env python3
"""make_edl.py -- Chapter 4 "Into Oregon" of the One-way ticket long-form (Lifestyle, @nq.young), as data -> edl.json in
the same schema as ../test-ch3 and ../ch1 (shots / dialog / audio_extra), which mix.py, words_medium.py and render.py read.

Spans come from ../PLAN.md, chapter 2. Chapter 1 ends on 0081 "finally getting on the plane"; this one follows it.
Word timings: /home/user/day-owt/tr (small.en); in/out points set on the voice-band envelope (300-3400 Hz, 50 ms frames)
of /home/user/day-owt/aud/<clip>.m4a (MEASURED below): every out-point leaves >= 0.35 s after the last voiced frame and
stops before the next voice onset.

Changes from the PLAN spans, each for a reason:
  * 0082 0-12 (the landing, no speech) becomes two shots, 1.0-5.5 (wing and engine over the suburbs, under the
    "SEATTLE · MORNING" title) and 9.0-13.0 (low over the trees to the airport car park), because 12 s of one window
    shot holds too long for a no-talk opener (point 4: 6-9 picture changes a minute). 13.0 is inside the fetch
    padding (mezzanine 0-15.8). The 0.0-1.0 start is the window frame swinging in.
  * 0084 1-14.1 runs 1.25-14.40: the camera sound is digital silence 0.65-1.25 and "All right" starts at 1.35;
    "...where I'm at" ends 13.95 (envelope), next voice 15.65.
  * 0085 50-69 becomes 49.80-52.60 "You wanna see the fit check?" + 58.40-69.35 "Got the Hidden Hills jacket on, you
    see the back... the Rick Owens on, tough, huh": cut 52.6-58.4, which holds "I got a fit." (speaker model OTHER
    0.57) and "You're filming." (HOST 0.49, uncertain) while he sets the camera on the bench, so no possible stranger's
    voice is used and the dead time goes. The picture jumps from the selfie to the full-length fit check.
  * 0086 32-33.5 runs 31.90-34.45 so "Washington" (whisper gives it zero length at 33.54; voiced to ~34.05) is whole;
    the stranger (Uber driver) block flag starts at 35.0.
Music flags (flags.json): 0082, 0084, 0085 and 0086 carry no music flag; the only block flag on them is 0086 35.0-51.1
(stranger), outside the used range; the assert below checks every block flag.
Re-run: python3 make_edl.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
TRD = '/home/user/day-owt/tr'
FPS = 30000 / 1001
TAIL = 0.40

# (src, in, dur, speed, note, sync-dialog (in, asr_out) or None). dur None = to the dialog out; dur 'REST' = the
# picture-only cutaway that runs to the end of the previous dialog piece (J/L cover for a hands/phone failure).
SHOTS = [
    ('0093', 3.45, None, 1.0, 'OPEN (side cam, roof down, Washington suburbs) under the "INTO OREGON" title: "I ain\'t gonna lie, it is beautiful out here, like gorgeous."', (3.45, 8.19)),
    ('0093', 127.84, None, 1.0, '"But I just want to let you guys know, like I said, we\'re on our way... destination to Las Vegas. We\'re gonna do 12 hour non-stop all the way to Salt Lake I believe, and then we\'re gonna stay there overnight at the Hamptons"', (127.84, 140.54)),
    ('0094', 151.15, 3.85, 1.0, 'FOREST ROAD (rear cam): "This place is so nice. Like it\'s fresh air..." (picture until the phone comes up at ~155.4)', (151.15, 165.54)),
    ('0095', 18.6, 3.6, 1.0, 'CUTAWAY (picture + nat, 0094 line runs on): forest road, both hands on the wheel ("Man, I miss trees and nature")', None),
    ('0095', 22.3, 3.5, 1.0, 'CUTAWAY: forest road ("...some fire hiking trails out here")', None),
    ('0095', 31.0, 'REST', 1.0, 'CUTAWAY: forest road ("It\'s so nice out here.")', None),
    # MONTAGE (bed up, engine nat; no talk): forest -> highway and mountains
    ('0095', 14.4, 2.0, 1.0, 'MONTAGE: forest road, yellow lines', None),
    ('0095', 35.0, 2.1, 1.0, 'MONTAGE: forest road', None),
    ('0095', 49.0, 2.3, 1.0, 'MONTAGE: forest road, car passing', None),
    ('0095', 53.0, 2.3, 1.0, 'MONTAGE: forest road, stone wall', None),
    ('0098', 0.6, 2.4, 1.0, 'MONTAGE: highway, pines, pickup alongside', None),
    ('0098', 3.6, 2.3, 1.0, 'MONTAGE: highway', None),
    ('0098', 6.6, 2.3, 1.0, 'MONTAGE: highway', None),
    ('0098', 9.6, 2.3, 1.0, 'MONTAGE: highway', None),
    ('0098', 12.3, 2.0, 1.0, 'MONTAGE: highway, truck passing', None),
    ('0098', 47.0, 2.4, 1.0, 'MONTAGE (scenery crop, the cockpit below frame): highway, mountains', None),
    ('0098', 51.0, 2.3, 1.0, 'MONTAGE (scenery crop): highway, mountains', None),
    ('0098', 55.4, 2.4, 1.0, 'MONTAGE (scenery crop): valley, mountains', None),
    # END: Oregon
    ('0100', 18.2, None, 1.0, 'OREGON (desert, rear cam): "We are in Oregon, we passed the welcome to Oregon sign."', (18.2, 21.08)),
    ('0100', 28.15, None, 1.0, 'JUMP: "But we just got into Oregon. So that\'s a quick little update. Hopefully you guys can hear me. Oh yeah, I just wanted to let you guys know. We\'re in Oregon!" (ends on the shout; "Alright, I\'ll see you guys later" is cut: he reaches for the camera while driving)', (28.15, 36.92)),
]
MUTE = []
BLEEP = []
ROT = {}


def words(src):
    t = json.load(open(os.path.join(TRD, f'{src}.json')))
    return [[w[0], w[1], w[2].strip()] for s in t['segments'] for w in s['words']]


def inside(w, a, b):
    return min(w[1], b) - max(w[0], a) >= 0.15 or (a - 1e-6 <= w[0] < b - 0.1)


WARN = []
# out-points set from the voice-band envelope where whisper stretches a word over a pause (2026-10-08):
# (src, in) -> (voice_end, next_onset, out)
MEASURED = {('0093', 3.45): (8.05, 8.50, 8.40),      # "gorgeous" voiced to 8.05; "Like" (scored OTHER) at 8.50
            ('0093', 127.84): (140.50, 140.75, 140.70),  # "Hamptons" ends 140.50; "and once we're there" at 140.75 (cut: dangling)
            ('0094', 151.15): (165.54, 170.0, 165.90),  # "...out here." ends 165.54 (envelope 165.35 back to road noise)
            ('0100', 18.2): (21.00, 22.00, 21.45),     # "sign." ends ~21.0 (medium.en 21.08); "I better have a goddamn little map..." at 22.0 (cut)
            ('0100', 28.15): (37.45, 37.90, 37.80),   # "Oregon!" shouted to 37.45; "Alright, I'll see you guys later" from 37.90 (cut)
            }


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
dl_end = None
for i, (src, a, dur, sp, note, dl) in enumerate(SHOTS):
    if dl:
        out, le, p, m = tail(src, dl[0], dl[1])
        din = dl[0]
        dialog.append(dict(beat=i, src=src, **{'in': din}, out=out, t=round(t + (din - a), 3), trim_pauses=None,
                           last_word_end=le, voice_end=m[0] if m else None, next_onset_measured=m[1] if m else None, extended=False, out_asr=dl[1],
                           text=' '.join(w[2] for w in p)))
        dl_end = dialog[-1]['t'] + out - din
        if dur is None:
            dur = round(out - a, 3)
    elif dur == 'REST':
        dur = round(dl_end - t, 3)
    shots.append(dict(beat=i, src=src, **{'in': a}, out=round(a + dur * sp, 3), speed=sp, t=round(t, 3), dur=round(dur, 3),
                      note=note))
    t += dur
dur_total = round(t, 3)

NUDGE = {}
for d in dialog:
    pass

# room tone for the NO MUSIC mix / gaps: none needed (every shot carries its own camera sound)

# assert: no shot or audio range sits on a block flag (with the 0.8 s fetch handle the render must not use)
flags = [f for f in json.load(open('/home/user/day-owt/flags.json')) if f.get('severity') == 'block']
for s in shots + extra + dialog:
    lo, hi = s['in'], s['out']
    for f in flags:
        if f['clip'] == s['src'] and lo < f['t1'] and f['t0'] < hi:
            raise SystemExit(f'BLOCK FLAG {f["clip"]} {f["t0"]}-{f["t1"]} {f["category"]} under {s["src"]} {lo}-{hi}')

edl = dict(fps='30000/1001', size=[3840, 2160], duration=dur_total,
           chapters=[dict(t=0.0, title='Into Oregon', clock='12:00:58 (0093) to 16:06 (0100), DJI camera clock')],
           shots=shots, dialog=dialog, audio_extra=extra,
           beats=[dict(i=0, ch='CH4', t0=0.0, t1=dur_total, note='CH4 Into Oregon: leaving Seattle roof down -> the plan (Las Vegas via Salt Lake) -> the forest road -> montage -> "We\'re in Oregon!"')],
           mute=[dict(src=s, **{'in': a}, out=b, note=n) for s, a, b, n in MUTE],
           bleeps=[dict(src=s, **{'in': a}, out=b, word=n) for s, a, b, n in BLEEP],
           rotate=ROT, warnings=WARN)
json.dump(edl, open(os.path.join(HERE, 'edl.json'), 'w'), indent=1)
print(f'shots {len(shots)}  dialog {len(dialog)}  runtime {dur_total:.2f} s ({int(dur_total // 60)}:{dur_total % 60:04.1f})  '
      f'picture changes/min {60 * (len(shots) - 1) / dur_total:.1f}')
for w in WARN:
    print('WARN', w)
