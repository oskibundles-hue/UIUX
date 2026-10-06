"""The 30 s ad cut's timing files, from src/cut30.json (which shots, how many frames each).

Writes shots30.json (the same shots with their 30 s start and end, the same clip, in-point and speed, so
tools/car_audio.py --cut 30 lines each clip's sound up with its plate) and sfx/events30.json (the SFX engine's
spotting list for the 30 s cut: the 76 s events for those shots, cut to each shot's new length, with the
30 s cut's tighter timings and its own cut sounds).

  python3 tools/cut30.py
"""
import json, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FPS = 30

# the 30 s cut's tighter timings (src/Ad.tsx, `short`): shot -> {what: new local frame}, None = not in the 30 s cut
SHORT = {
    6: {'caption "What"': 6, 'caption "is it"': 11, 'caption "this time?"': 16},
    10: {'"No"': 10, '"Let me book it"': 16, 'prompt bar slides up': None, 'prompt types "I need a car for F1 weekend…"': None,
         'send pressed': None},
}
CUTS = {'4': ['section'], '12': ['punch'], '17': ['whip'], '21': ['punch'], '30': ['punch'], '32': ['speed']}
# no shot 31 riser here: the music's own tension (16.6 - 17.7 s) runs into the drop on shot 30's engine start (its frame 36)
TENSION = {'shot': 30, 'at': 0, 'kind': 'tension', 'until_cut': 30, 'until_at': 36,
           'what': 'tension into the drop: the GT3 RS engine fires and the beat comes back on the same frame'}


def main():
    cut = json.load(open(os.path.join(P, 'src', 'cut30.json')))
    shots = {s['id']: s for s in json.load(open(os.path.join(P, 'shots.json')))}
    out, f, length = [], 0, {}
    for sid, n in cut['shots']:
        s = dict(shots[sid])
        s['t0'], s['t1'] = round(f / FPS, 4), round((f + n) / FPS, 4)
        out.append(s)
        length[sid] = n
        f += n
    json.dump(out, open(os.path.join(P, 'shots30.json'), 'w'), indent=1, ensure_ascii=False)

    ev76 = json.load(open(os.path.join(P, 'sfx', 'events.json')))
    events, dropped = [], []
    for e in ev76['events']:
        if e['shot'] not in length or e['kind'] == 'tension':
            continue
        e = dict(e)
        new = SHORT.get(e['shot'], {}).get(e['what'], e['at'])
        if new is None:
            dropped.append(f"{e['shot']}: {e['what']} (not in the 30 s cut)")
            continue
        e['at'] = new
        L = length[e['shot']]
        if e.get('repeat'):
            keep = sum(1 for i in range(e['repeat']) if e['at'] + i * e.get('step', 0) < L)
            if keep < e['repeat']:
                dropped.append(f"{e['shot']}: {e['what']} x{e['repeat'] - keep} (past the shot's end)")
            e['repeat'] = keep
        if e['at'] >= L or not e.get('repeat', 1):
            dropped.append(f"{e['shot']}: {e['what']} (past the shot's end)")
            continue
        events.append(e)
    events.append(TENSION)
    events.sort(key=lambda e: (list(length).index(e['shot']), e['at']))
    spec = {k: v for k, v in ev76.items() if k not in ('events', 'cuts')}
    spec.update(about='Spotting list for the 30 s cut, made by tools/cut30.py from sfx/events.json and src/cut30.json. ' + ev76['about'],
                total=f, shots_from='shots30.json', motion=None, spotting_video=None, cuts=CUTS, events=events,
                music={'file': 'public/audio/bed30.wav', 'gain': 1.0,
                       'note': 'music_roar30.wav x 0.55 with ducks + the natural car sound stem, made by tools/car_audio.py --cut 30'})
    json.dump(spec, open(os.path.join(P, 'sfx', 'events30.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'shots30.json: {len(out)} shots, {f} frames; sfx/events30.json: {len(events)} events; dropped {len(dropped)}:')
    for d in dropped:
        print('  ' + d)


if __name__ == '__main__':
    main()
