#!/usr/bin/env python3
"""remap_cut2.py -- one-off (Part 1 v2 cut 2, Omarie 7 Oct): move config.json from the v2 cut to v2 cut 2.

Cut 2 takes two spoken lines out of CH2: 0087 "I think you guys just put a brand new engine in it." (the 0087 SYNC shot
now opens at 57.758, was 54.9) and the whole 0088 beat ("So they got one more hour until they're done with the car.",
shot 21, 5.45 s). Together the cut is 243 frames (8.108 s) shorter. Nothing before the join (68.41 s) moves. Every
timeline time at or after the old 0089 shot (79.06 s) moves back by 243 frames; nothing in the config may sit inside
the changed span 68.41-79.06 (asserted). Shot indices: 0-20 stay, 21 (0088) is gone, 22.. -> 21..
Run once: python3 tools/remap_cut2.py   (it refuses to run twice: config._remapped_cut2 is set)
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30000 / 1001
N = 243
R = N / FPS
A, B = 68.41, 79.06          # the changed span on the old timeline
DROPPED = 21


def m(x):
    if x < A - 1e-6:
        return x
    assert x >= B - 1e-6, f'config time {x} sits inside the changed span {A}-{B}'
    return round(x - R, 3)


def mf(f):
    return f if f < A * FPS else f - N


def pair(i):
    if i < DROPPED:
        return i
    if i == DROPPED:
        return None
    return i - 1


def main():
    cp = os.path.join(ROOT, 'config.json')
    C = json.load(open(cp))
    assert not C.get('_remapped_cut2'), 'already remapped'
    log = []

    def mt(d, k):
        if k in d and isinstance(d[k], (int, float)):
            o = d[k]; d[k] = m(o)
            if o != d[k]:
                log.append(f'{k} {o} -> {d[k]}')

    tr = []
    for t in C['transitions']:
        j = pair(t['into'])
        assert j is not None
        if j != t['into']:
            log.append(f"transition into {t['into']} -> {j}")
        t['into'] = j
        mt(t, 't0')
        tr.append(t)
    C['transitions'] = tr
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
    for s in C['bed']['segs']:
        mt(s, 't')
    for k, tk in C['tracks'].items():
        if k.startswith('_'):
            continue
        j = pair(tk['shot'])
        assert j is not None
        tk['shot'] = j
        for f in ('f0', 'f1', 'anchor'):
            o = tk[f]; tk[f] = mf(o)
            if o != tk[f]:
                log.append(f'track {k} {f} {o} -> {tk[f]}')
    sp = []
    for s in C['speedo']:
        j = pair(s['shot'])
        assert j is not None, 'a speedo box on the dropped 0088 shot'
        s['shot'] = j; sp.append(s)
    C['speedo'] = sp
    sh = {}
    for k, v in C['shots'].items():
        j = pair(int(k))
        if j is None:
            log.append(f'shots[{k}] {v} dropped (0088)')
            continue
        sh[str(j)] = v
    C['shots'] = dict(sorted(sh.items(), key=lambda kv: int(kv[0])))
    C['_remapped_cut2'] = ('v2 cut 2 (7 Oct): config times after 79.06 s moved back 243 frames (8.108 s) and shot indices '
                           'after the dropped 0088 shot down by one, by tools/remap_cut2.py')
    json.dump(C, open(cp, 'w'), indent=1, ensure_ascii=False)
    print('\n'.join(log))


if __name__ == '__main__':
    main()
