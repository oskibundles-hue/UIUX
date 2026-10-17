#!/usr/bin/env python3
"""remap_v2.py -- one-off (Part 1 v2, 6 Oct): move every timeline time and shot index in config.json from the v1 cut to the
v2 cut after fix A (tails) changed the EDL.

v1's EDL is read from git (the commit given, default HEAD) and v2's from data/edl.json. Shots are paired by index:
v1 0-4 -> v2 0-4, v2 5 is new (0097 4.6, the hook runs on under "... or Supercar Experience"), v1 5-25 -> v2 6-26,
v1 26 (0091 14.8, "Man, it's gonna be a long drive.") is out, v1 27-43 -> v2 27-43. A time inside a v1 shot keeps its
offset from the shot start; in a SYNC shot whose in-point moved, it keeps its source moment instead. Clamped to the v2
shot. Run once: python3 tools/remap_v2.py [commit]   (it refuses to run twice: config._remapped_v2 is set)
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30000 / 1001
REL = 'supercar-experience/10-vlog-locked-on/2026-09-26-one-way-ticket/part1/data/edl.json'


def pair(i):
    if i <= 4:
        return i
    if 5 <= i <= 25:
        return i + 1
    if i == 26:
        return None
    return i


def main():
    commit = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    v1 = json.loads(subprocess.run(['git', '-C', ROOT, 'show', f'{commit}:{REL}'], capture_output=True, check=True, text=True).stdout)
    v2 = json.load(open(os.path.join(ROOT, 'data', 'edl.json')))
    cp = os.path.join(ROOT, 'config.json')
    C = json.load(open(cp))
    assert not C.get('_remapped_v2'), 'already remapped'
    S1, S2 = v1['shots'], v2['shots']

    def m(x):
        for k, s in enumerate(S1):
            if s['t'] - 1e-6 <= x < s['t'] + s['dur'] - 1e-6 or (k == len(S1) - 1 and x <= s['t'] + s['dur'] + 1e-6):
                break
        j = pair(k)
        if j is None:                       # inside the dropped shot: the cut point that replaced it
            return round(S2[pair(k + 1)]['t'], 3)
        off = x - s['t']
        n = S2[j]
        if 'SYNC' in s.get('note', '') and abs(s['in'] - n['in']) > 1e-6:
            off += s['in'] - n['in']
        off = min(max(off, 0.0), n['dur'])
        return round(n['t'] + off, 3)

    mf = lambda f: int(round(m(f / FPS) * FPS))
    log = []

    def mt(d, k):
        if k in d and isinstance(d[k], (int, float)):
            o = d[k]; d[k] = m(o); log.append(f'{k} {o} -> {d[k]}')

    for tr in C['transitions']:
        tr['into'] = pair(tr['into'])
        mt(tr, 't0')
    for s in C['slams']:
        mt(s, 't')
    for c in C['layer']['comps']:
        mt(c, 't0'); mt(c, 't1')
        p = c.get('p', {})
        for k in ('exit', 'acquire', 'clockFrom'):
            mt(p, k)
        if 'progress' in p:
            p['progress'] = [m(x) for x in p['progress']]
        for e in p.get('expand', []):
            mt(e, 'a'); mt(e, 'b')
            e['places'] = [[m(t), name] for t, name in e['places']]
    lc = C['layer']['captions']
    mt(lc, 't0'); mt(lc, 't1')
    for k, tk in C['tracks'].items():
        if k.startswith('_'):
            continue
        tk['shot'] = pair(tk['shot'])
        for f in ('f0', 'f1', 'anchor'):
            o = tk[f]; tk[f] = mf(o); log.append(f'track {k} {f} {o} -> {tk[f]}')
    sp = []
    for s in C['speedo']:
        j = pair(s['shot'])
        if j is not None:
            s['shot'] = j; sp.append(s)
    sp.append(dict(shot=5, box=[330, 985, 210, 120], pad=16, radius=16,
                   why='0097 speedometer (v2 hook shot 5, 0097 4.6-7.8; box from shot 0, same camera mount)'))
    C['speedo'] = sorted(sp, key=lambda s: s['shot'])
    sh = {}
    for k, v in C['shots'].items():
        j = pair(int(k))
        if j is not None:
            sh[str(j)] = v
    sh['5'] = {'look': 'cabin'}
    C['shots'] = dict(sorted(sh.items(), key=lambda kv: int(kv[0])))
    C['_remapped_v2'] = f'config times and shot indices moved from the v1 cut ({commit}) to v2 by tools/remap_v2.py'
    json.dump(C, open(cp, 'w'), indent=1, ensure_ascii=False)
    print('\n'.join(log))


if __name__ == '__main__':
    main()
