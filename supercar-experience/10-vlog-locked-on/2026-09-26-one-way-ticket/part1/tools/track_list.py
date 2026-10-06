#!/usr/bin/env python3
"""track_list.py -- every in-car song that can be heard in the Part 1 v2 mix, in EPISODE time (Omarie, 6 Oct: "Use it,
flag the tracks").

Source: the Shazam pass over the full clip audio (paths.music_tracks, copy at ../in_car_tracks.json): one entry per song
per clip, with clip_from / clip_to = the span of 10 s windows that matched (n windows). Each entry is mapped through
  - the bed segments (config bed.segs, kind music/nat/exhaust: clip span a-b placed at episode t), and
  - the dialog pieces (data/edl.json dialog: clip span in-out placed at t), where the stereo plays UNDER the voice.
A song counts as audible where its matched clip span overlaps a placed span. Single-window matches (n == 1) and matches
under the voice are marked "check". Writes exports/qa/in_car_tracks_part1.md and .json.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from cfg import load_config  # noqa: E402

C = load_config()
EDL = json.load(open(os.path.join(ROOT, C['paths']['edl'])))
tp = C['paths'].get('music_tracks')
if not tp or not os.path.exists(tp):
    tp = os.path.join(ROOT, '..', 'in_car_tracks.json')
TR = json.load(open(tp))
QA = os.path.join(ROOT, 'exports', 'qa')


def tc(s):
    return f'{int(s // 60)}:{s % 60:05.2f}'


placed = []
for s in C['bed']['segs']:
    placed.append(dict(where=f"bed ({s['kind']})", src=s['src'], a=s['a'], b=s['b'], t=s['t'], under_voice=False))
for d in EDL['dialog']:
    placed.append(dict(where='under the voice', src=d['src'], a=d['in'], b=d['out'], t=d['t'], under_voice=True))

DIRECT = json.load(open(os.path.join(ROOT, 'data', 'shazam_spans.json')))
rows, quiet = [], []
for p in placed:
    key = f"{p['src']}:{p['a']}:{p['b']}"
    if key in DIRECT:                                  # Shazam on the exact placed span (data/shazam_spans.json)
        hit = DIRECT[key]
        if hit:
            scan = [x for x in TR if x['clip'] == p['src'] and x['title'] == hit[0] and x['clip_from'] < p['b'] + 15 and x['clip_to'] > p['a'] - 15]
            n = max([x['n'] for x in scan] or [0])
            check = []
            if n <= 1:
                check.append(f'clip scan: {n} window(s)')
            if p['under_voice']:
                check.append('under the voice')
            rows.append(dict(title=hit[0], artist=hit[1], clip=p['src'], clip_in=p['a'], clip_out=p['b'], ep_in=round(p['t'], 2),
                             ep_out=round(p['t'] + p['b'] - p['a'], 2), where=p['where'], shazam_windows=n,
                             confidence='direct match on the exact span' + (f' + {n} nearby clip-scan window(s)' if n else ''),
                             check='check: ' + '; '.join(check) if check else ''))
        elif p['under_voice']:
            quiet.append(p)
        continue
    for x in TR:                                       # no direct check: overlap with the clip scan (30 s grid)
        if x['clip'] != p['src']:
            continue
        lo, hi = max(p['a'], x['clip_from']), min(p['b'], x['clip_to'])
        if hi - lo < 0.5:
            continue
        rows.append(dict(title=x['title'], artist=x['artist'], clip=x['clip'], clip_in=round(lo, 2), clip_out=round(hi, 2),
                         ep_in=round(p['t'] + lo - p['a'], 2), ep_out=round(p['t'] + hi - p['a'], 2), where=p['where'],
                         shazam_windows=x['n'], confidence=x['confidence'], check='check: clip scan only' + ('; single window' if x['n'] == 1 else '')))
rows.sort(key=lambda r: r['ep_in'])

nomusic_bed = [s for s in C['bed']['segs'] if s['kind'] == 'music']
os.makedirs(QA, exist_ok=True)
json.dump(dict(source=[os.path.basename(tp), 'data/shazam_spans.json'], episode=C['name'], tracks=rows, no_song_recognised_under_voice=[dict(src=p['src'], a=p['a'], b=p['b'], ep=p['t']) for p in quiet]), open(os.path.join(QA, 'in_car_tracks_part1.json'), 'w'), indent=1)
L = [f"# In-car tracks heard in {C['name']}\n",
     'For Omarie to check before posting (commercial tracks can get a business-page post muted). Episode timecodes are',
     'm:ss.ss in the v2 cut. Source: Shazam on the exact clip span of every music bed segment and cabin dialog piece',
     '(data/shazam_spans.json), cross-checked with the full-clip scan (one 10 s window every 30 s, ../in_car_tracks.json).',
     '"check" = at most one nearby clip-scan window (within 15 s) agrees with the direct match.\n',
     '| # | Title | Artist | Episode in -> out | Clip (s) | Where | Confidence |', '|---|---|---|---|---|---|---|']
for i, r in enumerate(rows, 1):
    L.append(f"| {i} | {r['title']} | {r['artist']} | {tc(r['ep_in'])} -> {tc(r['ep_out'])} | {r['clip']} {r['clip_in']}-{r['clip_out']} | "
             f"{r['where']} | {r['confidence']}{'; **' + r['check'] + '**' if r['check'] else ''} |")
L += ['', f'Dialog pieces from the cabin clips with no song recognised on their exact span ({len(quiet)}): ' +
      ', '.join(f"{p['src']} at {tc(p['t'])}" for p in quiet) + '. A stereo may still be faintly audible under the voice there.']
L += ['', '**NO MUSIC version:** the music bed segments (' + ', '.join(f"{tc(s['t'])}" for s in nomusic_bed) +
      ') are swapped for road/exhaust nat from clip 0095. The dialog pieces keep their own cabin audio, so any faint stereo',
      'under his voice in the pieces listed above stays in the NO MUSIC version too.', '']
open(os.path.join(QA, 'in_car_tracks_part1.md'), 'w').write('\n'.join(L))
for r in rows:
    print(f"{tc(r['ep_in'])}-{tc(r['ep_out'])}  {r['title']} / {r['artist']}  [{r['where']}] {r['check']}")
