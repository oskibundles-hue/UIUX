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


# ======================================================================================================== v2 (8 Oct)
# Omarie on B: "the montage could be more dramatic but its good its just full of shots of me driving no critical moments
# interactions breaks, gas runs, etc". B2's montage is a SOUND-BITE TRAILER of the trip, in trip order, cut on the bed's
# beat, the music up between his lines and ducked under them. Two fixes he chose apply to A2 and B2:
#   1. HOOK 2's cutaway is a desert road (0121 rear camera, 199.6) instead of the sky-heavy 0099 176.3.
#   2. CH1's dark tail lifts only him (subject_lift.py, look_v2.json), not the room; v1's whole-frame gamma ramp is gone.
# B2 also J-cuts CH1's "So let's head up out of here" under the last two montage beats (into the dark hallway).
# Word edges: words_medium_B2.json (medium.en) and /home/user/day-owt/tr (small.en); speakers.json for HOST/OTHER.
# The empty-tank hook is not resolved in the montage (no 0119 "Yes Lord", no gas-light payoff).
HOOK_V2 = [HOOK[0],
           ('0121', 199.60, H2[2] - H2[1], 'cutaway', 'CUTAWAY over HOOK 2 (0117 phone in hand while moving): desert road, rear camera (v2: replaces the sky-heavy 0099 176.3)', H2, None),
           HOOK[2], HOOK[3]]

# montage v2 rows: (src, in, beats, note, [(dialog src, in, out, offset of the dialog from the shot start)], nat)
#   offset None = lip sync (dialog in - picture in). nat None = source sound muted (stereo, strangers, or a borrowed picture).
MONT2 = [
    # v2.2 (8 Oct, Omarie picked B2): the 0118 night drive trimmed 5.0 -> 3.85 s (3.25 + 1.75 beats), both bites whole.
    # v2.1 (nq-check, 8 Oct): varied cut lengths (beats may be halves): quick cuts through the gas and food run, longer
    # holds on the oil scare, the counter, the nap and the night trouble; montage <= 32 s. Bites trimmed to whole words.
    # 0090 21.8 "Oh yeah!" DROPPED at the frame gate: a whip pan, and the car's rear plate (and a red car's) in frame.
    # 0105 4.85 "We finally made it" DROPPED (nq-check): its picture is near-black; straight to the In-N-Out sign.
    ('0091', 7.30, 3, 'Seattle, in the parked car at the shop - "Spider top goes down" (hoodie chest print blurred)',
     [('0091', 7.30, 9.66, None)], NAT_MONT),
    ('0093', 6.20, 3, 'top down through the trees (moving; one hand on the wheel while he talks) - "out here, like gorgeous"',
     [('0093', 6.25, 8.38, None)], NAT_MONT),
    ('0102', 19.45, 2, 'first gas run, Oregon (parked at the pump) - "Red Bull and my snacks"', [('0102', 19.48, 21.04, None)], NAT_MONT),
    ('0105', 7.30, 2, 'In-N-Out at night, the sign behind him (on foot) - "To In-N-Out."', [('0105', 7.32, 8.40, None)], NAT_MONT),
    ('0107', 254.75, 4, 'the oil scare: parked at In-N-Out, him gesturing then down at his phone looking up the oil cap. VOICE from '
     '0106 (its picture is near-black): "Where the [bleep] is the oil in this [bleep]?", held a beat after the line',
     [('0106', 182.05, 184.35, 0.10)], None),
    ('0111', 47.40, 5, 'gas-station counter, him laughing (strangers out of frame; their voices muted) - "It\'s a McLaren." / '
     '"Everyone can say I\'m a Corvette too"', [('0111', 47.45, 48.45, None), ('0111', 49.62, 51.40, None)], None),
    ('0112', 13.90, 2.5, 'second gas run, in the parked car at the pump - "gassed up, shawty!"', [('0112', 13.95, 15.86, None)], NAT_MONT),
    ('0114', 8.70, 3.5, 'the night nap, parked - "take a nice McLaren nap" (hoodie print and the lit TFT blurred)',
     [('0114', 8.85, 11.18, None)], NAT_MONT),
    ('0114', 42.65, 4, 'awake, parked - "We back in business, baby!" (hoodie print and the lit TFT blurred)',
     [('0114', 42.70, 44.75, None)], NAT_MONT),
    ('0115', 12.75, 3, 'night gas run, standing at the pump - "It is freezing." (SE logo on the hoodie blurred from +1.25)',
     [('0115', 13.20, 15.05, None)], NAT_MONT),
    ('0118', 83.60, 3.25, 'morning drive, cabin camera (moving; left hand on the wheel) - "No hotel, no nothing."',
     [('0118', 83.65, 86.10, None)], NAT_MONT),
    ('0118', 90.05, 1.75, 'jump cut - "But you know, we dug it out."', [('0118', 90.08, 91.35, None)], NAT_MONT),
    ('0122', 583.40, 2.5, 'Las Vegas skyline, rear camera (last; bed only: stereo, Shazam; plate and LED billboard blurred)', [], None),
]
BLEEPS2 = [dict(src='0106', **{'in': 182.60}, out=182.92, word='fuck'), dict(src='0106', **{'in': 183.66}, out=184.32, word='bitch')]
J_CH1 = 2 * BEAT     # B2: CH1's first line starts under the last two montage beats
# picture-only allowances against flags.json blocks, each checked at the frame gate
ALLOW2 = {('0111', 'stranger'): 'picture 47.40-51.25 shows only him (clerks out of frame, gate-checked); nat muted, dialog is his words only'}


def build_v2(name, montage):
    shots, dialog = [], []
    t = 0.0
    mt = None
    rows = [(s, a, d, k, n, dl, nat) for (s, a, d, k, n, dl, nat) in HOOK_V2]
    for i, (src, a, dur, kind, note, dl, nat) in enumerate(rows):
        dialog.append(dict(beat=i, src=dl[0], **{'in': dl[1]}, out=dl[2], t=round(t, 4), text=dl[3] if len(dl) > 3 else ''))
        shots.append(dict(beat=i, src=src, **{'in': round(a, 4)}, out=round(a + dur, 4), speed=1.0, t=round(t, 4),
                          dur=round(dur, 4), kind=kind, nat=nat, note=note))
        t += dur
    if montage:
        mt = round(t, 4)
        for src, a, beats, note, dls, nat in MONT2:
            dur = beats * BEAT
            for ds, di, do, off in dls:
                off = (di - a) if off is None else off
                dialog.append(dict(beat=len(shots), src=ds, **{'in': di}, out=do, t=round(t + off, 4), text=''))
            shots.append(dict(beat=len(shots), src=src, **{'in': round(a, 4)}, out=round(a + dur, 4), speed=1.0, t=round(t, 4),
                              dur=round(dur, 4), kind='montage', nat=nat, note=note))
            t += dur
    j = J_CH1 if montage else 0.0
    pin = 80.50 + j
    dialog.append(dict(beat=len(shots), src='0075', **{'in': 80.50}, out=86.38, t=round(t - j, 4),
                       text='CH1: "So let\'s head up out of here. Alright famo."' + (' (J-cut %.2f s)' % j if j else '')))
    shots.append(dict(beat=len(shots), src='0075', **{'in': round(pin, 4)}, out=86.38, speed=1.0, t=round(t, 4),
                      dur=round(86.38 - pin, 4), kind='talk', nat=NAT_TALK,
                      note='CH1 START (rotate), subject lift' + (', picture from %.2f under the J-cut voice' % pin if j else '')))
    t += 86.38 - pin
    for a, b in zip(dialog, dialog[1:]):
        if a['src'] == b['src'] == '0117' and abs(a['t'] + a['out'] - a['in'] - b['t']) < 1e-3:
            a['tail'] = 0.04
    extra = [dict(beat=d['beat'], src=d['src'], **{'in': d['in']}, out=d['out'], t=d['t'], kind='nat', lufs=NAT_TALK, tail=d.get('tail', 0.0))
             for d in dialog if d['src'] == '0117']
    flags = [f for f in json.load(open('/home/user/day-owt/flags.json')) if f.get('severity') == 'block']
    for s in shots:
        for f in flags:
            if f['clip'] == s['src'] and s['in'] < f['t1'] and f['t0'] < s['out']:
                if f['category'] == 'music' and s['nat'] is None:
                    continue
                if (f['clip'], f['category']) in ALLOW2:
                    continue
                raise SystemExit(f'BLOCK FLAG {f["clip"]} {f["t0"]}-{f["t1"]} {f["category"]} under {s["src"]} {s["in"]}-{s["out"]}')
    for d in dialog:
        for f in flags:
            if f['clip'] == d['src'] and d['in'] < f['t1'] and f['t0'] < d['out'] and f['category'] == 'music':
                raise SystemExit(f'MUSIC FLAG under dialog {d}')
    edl = dict(name=name, fps='30000/1001', size=[1280, 720], duration=round(t, 4), montage_t=mt, beat=BEAT, v2=True,
               montage_duck=True, shots=shots, dialog=sorted(dialog, key=lambda d: d['t']), audio_extra=extra, mute=[],
               bleeps=BLEEPS2 if montage else [], rotate={'0075': 'cw', '0090': 'cw', '0115': 'cw'})
    json.dump(edl, open(os.path.join(HERE, f'edl_{name}.json'), 'w'), indent=1)
    print(f'{name}: shots {len(shots)}  dialog {len(dialog)}  runtime {t:.2f} s  montage_t {mt}' +
          (f'  montage {sum(s["dur"] for s in shots if s["kind"] == "montage"):.2f} s' if montage else ''))


build_v2('A2', False)
build_v2('B2', True)
