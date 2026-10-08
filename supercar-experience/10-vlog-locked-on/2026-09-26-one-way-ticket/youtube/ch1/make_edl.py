#!/usr/bin/env python3
"""make_edl.py -- Chapter 1 "4:30 a.m." of the One-way ticket long-form (Lifestyle, @nq.young), as data -> edl.json in the
same schema as ../test-ch3 (shots / dialog / audio_extra), which mix.py, words_medium.py and render.py read.

Spans come from ../PLAN.md, chapter 1. The opening (../opening-test, B2 v2.2) already ends on the 0075 80.7-85.6 line,
so this chapter starts at 0076. Word timings: /home/user/day-owt/tr (small.en); in/out points checked against the
voice-band envelope (300-3400 Hz, 50 ms frames) of /home/user/day-owt/aud/<clip>.m4a. Every out-point leaves >= 350 ms
after the last word or stops before the next voice onset (MEASURED below).

Changes from the PLAN spans, each for a reason:
  * Opens on 0076 21.15-23.05 (picture: the airport kerb at night, within the fetch padding) under the "4:30 a.m."
    title, so the chapter card sits on an establishing shot, not on a face mid-sentence. His "pretty tough" under it is
    reduced to its < 250 Hz content in the nat bus (no words).
  * 0076 24.9-34.4 runs to 34.84 so "...what we got" is not clipped (next word 36.14).
  * 0076 88.4-134.4, trimmed at word level:
      89.2-90.3 "So I" + 91.15-93.45 "have Muse make me like a route" (1.6 s pause shortened to ~0.8 s);
      93.45-113.1 cut: the "Jason ... recommended ... 12 hour run ... better view on the next front" aside (long
        pauses at 93.4-95.4, 95.9-97.7, 103.3-104.2; it repeats the 12 hours said again below) and the
        false start "So we're going to be doing, what do you say,";
      113.1-124.8 "we're going to be doing straight from Seattle Tacoma to Sandy Utah, which is like 830 miles,
        12 hours, and then we're gonna be doing Sandy to,";
      cut 124.8-125.65: the OTHER-scored "oh," (speaker model 0.51) and its pause;
      125.65-127.85 "420 miles, six hours."; cut 127.85-132.4: "So it's about a 18." (said again next);
      132.4-135.95 "It's looking like a 18 hour drive, Chad. I ain't gonna lie." (runs 1.5 s past the PLAN end;
        "I ain't gonna lie" is scored OTHER 0.63 but runs on without a gap in the envelope: flagged for nq-check).
    Spoken figures (830 miles, 12 hours, 420 miles, six hours, 18 hour) stay spoken only; no card repeats them.
  * 0077 78.4-98 (the tram) ends at 93.72 on "...close on her.": 96.47-98.03 "I don't know, I don't know" is scored
    OTHER 0.94 (a stranger) and 98.11 is the airport PA "Please stand clear of the tram doors". Jump cuts past the
    pauses (see SHOTS).
  * 0080 51.7-54.1 starts at 49.1 ("It's a little lopsided but I got it with the cream cheese, never tried that"),
    inside the fetch padding, so the line starts on its own beginning.
  * 0081 2.9-7.6 ends at 7.99 (last word 7.59 + 0.4; next voice is OTHER at 9.03).
Music flags (flags.json): none of 0076, 0077 or 0080 carries a music flag; 0081's PA/music block (53.0-97.5) and the
0080 cut_request (89.58-111.9) are far outside the used ranges; the assert below checks every block flag.
Re-run: python3 make_edl.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
TRD = '/home/user/day-owt/tr'
FPS = 30000 / 1001
TAIL = 0.40

# (src, in, dur, speed, note, sync-dialog (in, asr_out) or None)
SHOTS = [
    ('0076', 21.15, 1.9, 1.0, 'ESTABLISH (picture + nat only): the airport kerb at night; the "4:30 a.m." chapter title', None),
    ('0076', 24.9, None, 1.0, '"That\'s a little tired, but we up now. Wish this thing did better no light, but we\'re gonna work on what we got."', (24.9, 34.44)),
    ('0076', 89.2, None, 1.0, 'terminal: "So I"', (89.2, 89.6)),
    ('0076', 91.15, None, 1.0, 'JUMP: "have Muse make me like a route"', (91.15, 93.33)),
    ('0076', 113.1, None, 1.0, 'JUMP: "we\'re going to be doing straight from Seattle Tacoma to Sandy Utah, which is like 830 miles, 12 hours, and then we\'re gonna be doing Sandy to," (figures spoken only)', (113.1, 123.9)),
    ('0076', 125.65, None, 1.0, 'JUMP (past the OTHER "oh,"): "420 miles, six hours."', (125.65, 127.53)),
    ('0076', 132.4, None, 1.0, 'JUMP: "It\'s looking like a 18 hour drive, Chad. I ain\'t gonna lie."', (132.4, 135.27)),
    ('0077', 78.3, None, 1.0, 'THE TRAM: "I\'m gonna miss this little tram. Oh my God."', (78.3, 80.6)),
    ('0077', 82.35, None, 1.0, 'JUMP: "Should I run? Nope, not doing it. It\'s already closing."', (82.35, 87.8)),
    ('0077', 91.4, None, 1.0, 'JUMP (past the OTHER "Yep."): "I think it\'s gonna close on her."', (91.4, 93.32)),
    ('0080', 49.1, None, 1.0, 'THE BAGEL: "It\'s a little lopsided but I got it with the cream cheese, never tried that"', (49.1, 54.06)),
    ('0081', 2.85, None, 1.0, 'END: "I\'m finally getting on the plane. Damn, my thing dying already is crazy."', (2.85, 7.59)),
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
MEASURED = {('0076', 89.2): (89.60, 91.30, 90.30),      # "So I" ends 89.6; "have" starts 91.3 (pause kept short)
            ('0076', 91.15): (93.35, 94.45, 93.45),     # "...like a route" ends 93.35; "and" is cut
            ('0076', 113.1): (124.75, 125.15, 124.80),  # "...Sandy to," ends 124.75; OTHER "oh," at 125.15
            ('0076', 125.65): (127.60, 128.00, 127.85), # "six hours." ends 127.6; "So" at 128.0
            ('0076', 132.4): (135.60, 136.55, 135.95),  # "...I ain't gonna lie." ends 135.6; OTHER "That's not good" 136.55
            ('0077', 78.3): (80.60, 82.70, 81.00),      # "Oh my God." ends 80.6
            ('0077', 82.35): (87.75, 89.50, 88.15),     # "It's already closing." ends 87.75; OTHER "Yep." 89.5
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
for i, (src, a, dur, sp, note, dl) in enumerate(SHOTS):
    if dl:
        out, le, p, m = tail(src, dl[0], dl[1])
        din = dl[0]
        if dur is None:
            dur = round(out - a, 3)
        dialog.append(dict(beat=i, src=src, **{'in': din}, out=out, t=round(t + (din - a), 3), trim_pauses=None,
                           last_word_end=le, voice_end=m[0] if m else None, next_onset_measured=m[1] if m else None, extended=False, out_asr=dl[1],
                           text=' '.join(w[2] for w in p)))
    shots.append(dict(beat=i, src=src, **{'in': a}, out=round(a + dur * sp, 3), speed=sp, t=round(t, 3), dur=round(dur, 3),
                      note=note))
    t += dur
dur_total = round(t, 3)

# room tone for the NO MUSIC mix / gaps: none needed (every shot carries its own camera sound)

# assert: no shot or audio range sits on a block flag (with the 0.8 s fetch handle the render must not use)
flags = [f for f in json.load(open('/home/user/day-owt/flags.json')) if f.get('severity') == 'block']
for s in shots + extra:
    lo, hi = s['in'], s['out']
    for f in flags:
        if f['clip'] == s['src'] and lo < f['t1'] and f['t0'] < hi:
            raise SystemExit(f'BLOCK FLAG {f["clip"]} {f["t0"]}-{f["t1"]} {f["category"]} under {s["src"]} {lo}-{hi}')

edl = dict(fps='30000/1001', size=[3840, 2160], duration=dur_total,
           chapters=[dict(t=0.0, title='4:30 a.m.', clock='')],
           shots=shots, dialog=dialog, audio_extra=extra,
           beats=[dict(i=0, ch='CH1', t0=0.0, t1=dur_total, note='CH1 4:30 a.m.: Las Vegas airport before dawn -> the route -> the tram -> the bagel -> boarding')],
           mute=[dict(src=s, **{'in': a}, out=b, note=n) for s, a, b, n in MUTE],
           bleeps=[dict(src=s, **{'in': a}, out=b, word=n) for s, a, b, n in BLEEP],
           rotate=ROT, warnings=WARN)
json.dump(edl, open(os.path.join(HERE, 'edl.json'), 'w'), indent=1)
print(f'shots {len(shots)}  dialog {len(dialog)}  runtime {dur_total:.2f} s ({int(dur_total // 60)}:{dur_total % 60:04.1f})  '
      f'picture changes/min {60 * (len(shots) - 1) / dur_total:.1f}')
for w in WARN:
    print('WARN', w)
