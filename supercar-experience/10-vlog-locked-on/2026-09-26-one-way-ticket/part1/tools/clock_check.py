#!/usr/bin/env python3
"""clock_check.py (Part 1 v2, 7 Oct) -- the strip clock never runs backwards (vlog rule: the day stays in camera-clock order).

Reads build.clock_table() (the same table the build writes to .work/clock.js, which the strip draws from) and checks the
displayed second (floor of the clock) for every output frame from the strip's `clockFrom` on (the hook is a flash-forward
with no clock). The end card (None) is skipped. Lists every backwards step and exits 1 if there is one.
    python3 tools/clock_check.py
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import build as B  # noqa: E402


def clock_from():
    for comp in B.C['layer'].get('comps', []):
        if isinstance(comp, dict) and 'clockFrom' in json.dumps(comp):
            def find(o):
                if isinstance(o, dict):
                    if 'clockFrom' in o:
                        return o['clockFrom']
                    for v in o.values():
                        r = find(v)
                        if r is not None:
                            return r
                elif isinstance(o, list):
                    for v in o:
                        r = find(v)
                        if r is not None:
                            return r
            return find(comp)
    return 0.0


def hms(s):
    s = int(s); return f'{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}'


def main():
    tab = B.clock_table()
    cf = clock_from()
    f0 = int(math.ceil(cf * B.FPS - 1e-6))
    prev, pf, bad, n = None, None, [], 0
    for f in range(f0, len(tab)):
        if tab[f] is None:
            continue
        n += 1
        sec = math.floor(tab[f][0])
        if prev is not None and sec < prev:
            bad.append((pf, f, prev, sec))
        prev, pf = sec, f
    first = next(t for t in tab[f0:] if t)
    last = [t for t in tab if t][-1]
    print(f'clock_check: {n} frames from {cf:.3f} s (frame {f0}), {hms(first[0])} -> {hms(last[0])}')
    for a, b, x, y in bad:
        print(f'  BACKWARDS {a / B.FPS:8.3f} s -> {b / B.FPS:8.3f} s (frames {a}->{b}): {hms(x)} -> {hms(y)}')
    print('clock_check: PASS, the strip clock never decreases' if not bad else f'clock_check: FAIL, {len(bad)} backwards step(s)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
