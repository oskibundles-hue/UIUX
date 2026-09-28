#!/usr/bin/env python3
"""fetchneeds.py -- what this build reads from each camera clip, as an edl.json for the engine's `plan` (v2.4).

The engine plans from an EDL's shots / dialog / audio_extra plus handles. The render reads a little more than the EDL
says: sweep and end-card post-roll, speed ramps, the shot 17 slip (config `slips`), the per-piece trims, the cold-open
guest line (audio.extraDialog) and the nat clips (audio.nat). This writes exactly those source ranges, so a mezzanine exists for every read:

    python3 lib/fetchneeds.py OUT.json        -> then: python3 ../engine/vlog.py plan DAY --edl OUT.json --audio-only-vo

Shots are written with their real source range (speed 1.0: the engine only needs the range); the keyframe timelapse
stays a `keyframes` shot. A summary per clip (seconds of picture, seconds of audio only) is printed.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate as PL  # noqa: E402

A = PL.CFG['audio']


def needs():
    shots, dialog, extra = [], [], []
    for k, s in enumerate(PL.SHOTS):
        if s['src'] == 'card':
            continue
        if s['speed'] == 'keyframes':
            shots.append(dict(src=s['src'], **{'in': s['in'], 'out': s['out']}, speed='keyframes', t=s['t'], dur=s['dur'], shot=k))
            continue
        ts = PL.src_times(k, PL.post_frames(k))
        a, b = min(t for t, _ in ts), max(t for t, _ in ts)
        # a ramp's shutter average and the slow-motion blend read one source frame either side
        shots.append(dict(src=s['src'], **{'in': round(max(0.0, a - 0.05), 3), 'out': round(b + 0.05, 3)}, speed=1.0, t=s['t'], dur=s['dur'], shot=k))
    for i, d in enumerate(PL.EDL['dialog']):
        tr = A['trims'].get(str(i), {})
        dialog.append(dict(src=d['src'], **{'in': round(d['in'] + tr.get('in', 0.0), 3), 'out': round(d['out'] + tr.get('out', 0.0), 3)}, t=d['t'], piece=i))
    for d in A.get('extraDialog', []):
        extra.append(dict(src=d['src'], **{'in': d['in'], 'out': d['out']}, t=d['t'], kind='dialog', why='extraDialog'))
    for e in A['nat']:
        extra.append(dict(src=e['src'], **{'in': e['a'], 'out': e['b']}, t=e['t'], kind='nat', why='nat'))
    # the dealarm reference pieces (audio.dealarm refs, read with 0.4 s pre-roll) are dialog pieces with their own sync
    # shot, whose mezzanine starts 0.85 s early (0.05 + the 0.8 s handle), so they need no range of their own
    return dict(fps=PL.EDL['fps'], duration=PL.EDL['duration'], shots=shots, dialog=dialog, audio_extra=extra,
                note='written by lib/fetchneeds.py from data/edl.json + config.json (what the render reads)')


def summary(e, handles=0.8, gap=2.0):
    def merge(rs):
        out = []
        for a, b in sorted(rs):
            if out and a <= out[-1][1] + gap:
                out[-1][1] = max(out[-1][1], b)
            else:
                out.append([a, b])
        return out
    rows = {}
    for s in e['shots']:
        r = rows.setdefault(s['src'], {'v': [], 'a': [], 'kf': 0})
        if s['speed'] == 'keyframes':
            r['kf'] += s['out'] - s['in']
        else:
            r['v'].append([max(0, s['in'] - handles), s['out'] + handles])
    for d in e['dialog'] + e['audio_extra']:
        rows.setdefault(d['src'], {'v': [], 'a': [], 'kf': 0})['a'].append([max(0, d['in'] - handles), d['out'] + handles])
    out = {}
    for src, r in sorted(rows.items()):
        v = merge(r['v'])
        a_only = [x for x in merge(r['a']) if not any(va <= x[0] + 1e-6 and x[1] <= vb + 1e-6 for va, vb in v)]
        out[src] = dict(video_s=round(sum(b - a for a, b in v), 2), video_ranges=len(v), audio_only_s=round(sum(b - a for a, b in a_only), 2),
                        audio_only_ranges=len(a_only), timelapse_s=round(r['kf'], 1))
    return out


if __name__ == '__main__':
    e = needs()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PL.ROOT, '.work', 'plan_edl.json')
    json.dump(e, open(out, 'w'), indent=1)
    sm = summary(e)
    for src, r in sm.items():
        print(f"{src:7s} picture {r['video_s']:7.2f} s in {r['video_ranges']} range(s)   audio only {r['audio_only_s']:6.2f} s in {r['audio_only_ranges']}"
              + (f"   timelapse over {r['timelapse_s']} s" if r['timelapse_s'] else ''))
    print(f"total picture {sum(r['video_s'] for r in sm.values()):.1f} s, audio only {sum(r['audio_only_s'] for r in sm.values()):.1f} s, "
          f"{sum(r['video_ranges'] for r in sm.values())} + {sum(r['audio_only_ranges'] for r in sm.values())} ranges, {len(sm)} clips -> {out}")
