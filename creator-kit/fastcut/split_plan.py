#!/usr/bin/env python3
"""Fast-cut a plan: first shot <= 3 s, every other shot <= 4.5 s (jump cuts inside the take)."""
import json, sys
p = json.load(open(sys.argv[1])); out = []
for i, s in enumerate(p['segments']):
    a, b = s['in'], s['out']; first = (i == 0)
    while b - a > 0.2:
        step = 3.0 if (first and not out) else 4.5
        c = min(b, a + step)
        if b - c < 1.2: c = b
        out.append(dict(s, **{'in': round(a, 3), 'out': round(c, 3)})); a = c
p['segments'] = out; json.dump(p, open(sys.argv[1], 'w'), indent=1)
print(len(out), 'shots', round(sum(s['out'] - s['in'] for s in out), 1), 's')
