#!/usr/bin/env python3
"""make_edl.py -- the opening A/B look test for "One-way ticket" (Lifestyle, @nq.young): two openings Omarie watches
back to back before the full 16-min cut.

  A (HiddenQuan, cold talk):  HOOK -> CH1 start
  B (Brez Scales, montage):   HOOK -> MONTAGE (about 20 s, no talk, bed up, cut on the beat, trip order) -> CH1 start

-> edl_A.json / edl_B.json in the test-ch3 schema (shots / dialog / audio_extra / mute), plus per-shot `kind`
(talk | cutaway | montage), the montage start (`montage_t`, where the bed is aligned to a chord change) and per-shot
`nat` (natural sound level, None = muted).

Word edges: faster-whisper small.en (the day index, /home/user/day-owt/tr) and medium.en (run here on 7 Oct over the
hook and CH1 spans), checked against the 300-3400 Hz voice envelope of /home/user/day-owt/aud/<clip>.m4a in 50 ms frames.
Each out-point leaves >= 350 ms after the last word (both models), before the next onset.

  0117 100.85-103.12  "(I have) no cell service, not an SOS."  medium.en hears "I have" at 100.96 after "You feel
                      me?" (ends 100.80), so the in-point is 100.85; "Crazy as fuck" starts 103.42 (medium), so out 103.12.
  0117 111.40-113.62  "We're gonna have to make it, we don't have a choice."  small.en heard "I have to make it" at
                      111.86; medium.en hears "we're going to have" from 111.44 (after "...we'll make it," ends 111.36),
                      so starting at the brief's 111.9 would clip "gonna". In-point 111.40; next word 117.6.
  0075  56.45-60.95   "It's 4:30 in the morning. I got my Uber coming right now."  voice onset 56.55, "now" ends
                      60.48-60.60, next "It's" onset 61.05.
  0075  69.32-77.02   "So we are heading to Seattle, Washington to go pick up a McLaren 600 LT."  "here." ends 69.2;
                      "LT" ends 76.64-76.68 (both models); the next word ("or", into "Supercar Experience") is loud at
                      77.20, so out 77.02 with a 100 ms fade.
  0075  80.50-86.38   "So let's head up out of here. Alright famo." + a short tail: "famo" ends 85.55 (envelope), next
                      voice 87.15. Ends 86.38: the fetched mezzanine stops at 86.4.

Hands rule (Omarie, 2026-10-06): 0117 100-114 has the PHONE IN HIS RIGHT HAND WHILE MOVING (motion-blurred desert
through the window, 7 Oct check), so both 0117 lines play over drive CUTAWAYS (picture only; his 0117 voice and road
sound run on): 0121 rear camera (desert highway) and 0099 eastern Oregon plains (both hands on the wheel).

Montage (B): 78 BPM bed (music.py), cuts on the beat: 4+3+3+3+3+4+6 beats (3.08 / 2.31 s a shot, the last 4.6 s) = 26 beats
= 20.0 s, 7 shots. 0116:18-24 (sunrise) is DROPPED: the frame gate shows a lit phone in his hand while driving. 0122:553-559
is DROPPED: it is the same rear-camera frame (billboard + skyline) as 0122:584-590, so the two back to back read as
one shot. Stereo check (qa/shz.py, Shazam, 7 Oct, 8 s windows every 4 s over every used range): no match anywhere
except 0099 175-183 (Mrs. Trendsetter, Lil Baby), 0122 552-560 (spend the money, Fousheé) and 0122 583-591 (COMË N GO,
Yeat), so 0099 and 0122 carry NO source sound (bed only), in the montage and in the hook cutaway alike (the cutaway
plays over 0117's own sound anyway).
Re-run: python3 make_edl.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BEAT = 60 / 78
NAT_TALK, NAT_MONT = -24.0, -30.0

# (src, in, dur, kind, note, dialog (src, in, out) or None, nat level or None)
H1 = ('0117', 100.85, 103.12, 'HOOK 1: "(I have) no cell service, not an SOS."')
H2 = ('0117', 111.40, 113.62, 'HOOK 2: "We\'re gonna have to make it, we don\'t have a choice."')
HOOK = [
    ('0121', 152.00, H1[2] - H1[1], 'cutaway', 'CUTAWAY over HOOK 1 (0117 phone in hand while moving): rear camera, desert highway', H1, None),
    ('0099', 176.30, H2[2] - H2[1], 'cutaway', 'CUTAWAY over HOOK 2 (0117 phone in hand while moving): eastern Oregon plains, hands on the wheel', H2, None),
    ('0075', 56.45, 60.95 - 56.45, 'talk', 'HOOK 3 (rotate): "It\'s 4:30 in the morning. I got my Uber coming right now."', ('0075', 56.45, 60.95, ''), NAT_TALK),
    ('0075', 69.32, 77.02 - 69.32, 'talk', 'HOOK 4 (rotate), jump cut: "So we are heading to Seattle, Washington to go pick up a McLaren 600 LT."', ('0075', 69.32, 77.02, ''), NAT_TALK),
]
CH1 = [('0075', 80.50, 86.38 - 80.50, 'talk', 'CH1 START (rotate), jump cut: "So let\'s head up out of here. Alright famo." + tail', ('0075', 80.50, 86.38, ''), NAT_TALK)]
B2, B3, B4, B6 = 2 * BEAT, 3 * BEAT, 4 * BEAT, 6 * BEAT
MONTAGE = [
    ('0092', 19.00, B4, 'montage', 'Seattle, top down, cabin side (parked)', None, NAT_MONT),
    ('0094', 27.50, B3, 'montage', 'forest road POV (1.4x top-anchored window: mirror, his arm and the dash are below the frame; see README)', None, NAT_MONT),
    ('0095', 8.80, B2, 'montage', 'green forest road (2 beats: 8.8-10.34 is clear of the flares at 8.2 and 10.5+)', None, NAT_MONT),
    ('0098', 97.35, B4, 'montage', 'trees and highway (1.4x top-anchored window: rear-view mirror out of frame; the beat from 0095)', None, NAT_MONT),
    ('0099', 179.00, B3, 'montage', 'eastern Oregon plains (source muted: stereo, Shazam)', None, None),
    # 0116 18-24 (sunrise) DROPPED at the frame gate: a lit phone in his hand while driving in every frame of the window
    ('0121', 148.40, B4, 'montage', 'desert highway, rear camera', None, NAT_MONT),
    ('0122', 583.40, B6, 'montage', 'Las Vegas, Rio billboard and skyline, rear camera (last; source muted: stereo, Shazam)', None, None),
]


def build(rows, name):
    shots, dialog = [], []
    t = 0.0
    mt = None
    for i, (src, a, dur, kind, note, dl, nat) in enumerate(rows):
        if kind == 'montage' and mt is None:
            mt = round(t, 4)
        if dl:
            dialog.append(dict(beat=i, src=dl[0], **{'in': dl[1]}, out=dl[2], t=round(t, 4), text=dl[3] if len(dl) > 3 else ''))
        shots.append(dict(beat=i, src=src, **{'in': round(a, 4)}, out=round(a + dur, 4), speed=1.0, t=round(t, 4),
                          dur=round(dur, 4), kind=kind, nat=nat, note=note))
        t += dur
    # seam tail: where one 0117 line runs straight into the next (HOOK1 -> HOOK2) the first line's audio runs 40 ms past its
    # picture cut, under the next line's 12 ms fade-in, so the road sound never drops to a hole at the join (the mix had a
    # 17 dB, 40 ms dip). The extra 40 ms stays inside the 0.38 s tail after "SOS." and ends 0.3 s before "Crazy".
    for a, b in zip(dialog, dialog[1:]):
        if a['src'] == b['src'] == '0117' and abs(a['t'] + a['out'] - a['in'] - b['t']) < 1e-3:
            a['tail'] = 0.04
    # nat under talk/cutaways comes from the dialog take (0117 / 0075) at NAT_TALK
    extra = [dict(beat=d['beat'], src=d['src'], **{'in': d['in']}, out=d['out'], t=d['t'], kind='nat', lufs=NAT_TALK, tail=d.get('tail', 0.0))
             for d in dialog if d['src'] == '0117']
    flags = [f for f in json.load(open('/home/user/day-owt/flags.json')) if f.get('severity') == 'block']
    for s in shots:
        for f in flags:
            if f['clip'] == s['src'] and s['in'] < f['t1'] and f['t0'] < s['out']:
                if s['kind'] == 'montage' and s['nat'] is None and f['category'] == 'music':
                    continue   # picture only; the stereo is muted
                if s['src'] == '0099' and f['category'] == 'music':
                    continue   # 0099 hook cutaway: picture only, 0117 sound under it
                raise SystemExit(f'BLOCK FLAG {f["clip"]} {f["t0"]}-{f["t1"]} {f["category"]} under {s["src"]} {s["in"]}-{s["out"]}')
    edl = dict(name=name, fps='30000/1001', size=[1280, 720], duration=round(t, 4), montage_t=mt, beat=BEAT,
               shots=shots, dialog=dialog, audio_extra=extra, mute=[], bleeps=[],
               rotate={'0075': 'check at the gate'})
    json.dump(edl, open(os.path.join(HERE, f'edl_{name}.json'), 'w'), indent=1)
    print(f'{name}: shots {len(shots)}  dialog {len(dialog)}  runtime {t:.2f} s  montage_t {mt}')


build(HOOK + CH1, 'A')
build(HOOK + MONTAGE + CH1, 'B')
