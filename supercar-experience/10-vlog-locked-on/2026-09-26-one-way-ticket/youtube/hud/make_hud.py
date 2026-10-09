#!/usr/bin/env python3
"""One-way ticket: the personal driving HUD plan -> hud.json.

Reads each piece's edl (opening + Ch1-8), takes the driving shots listed in DRIVE below (decided from the edl notes
and one contact sheet per chapter), merges shots closer than MERGE s into runs, keeps every run off the chapter title
card, and stamps each shot with its place, camera-clock time and trip progress. Writes hud.json beside this file;
render_hud.py draws it, assemble.py burns it into the rough cut.

Clock: the DJI camera clock = the clip's file-name timestamp (DJI_YYYYMMDDhhmmss_NNNN_D.MP4, /home/user/day-owt/
clips.json 'clock' = seconds after midnight) + the source offset of the frame. The MP4 creation_time is the same
instant in UTC (0114: file name 01:29:01, creation_time 2026-09-27T08:29:01Z), so the camera runs on UTC-7 = PDT.
Progress: camera clock interpolated between the five nodes of the schematic (NODES), each anchored on a clip where
he is on camera in that place. Schematic only: no distances, no map.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
YT = os.path.dirname(HERE)
DAY = '/home/user/day-owt'
FPS = 30000 / 1001
MERGE = 1.0        # merge driving shots closer than this (s)
FADE = 0.3         # fade/slide in and out (s)
TITLE_GAP = 0.1    # keep the HUD this far clear of a title card (s)
OPENING_DRIVES = False  # Omarie 2026-10-09: "Drop it there" (was True: the opening's story-montage drives (the hook stays clean: 12 points, no text in the hook)

PIECES = [  # name, edl, frames, title window (chapter time) or None
    ('opening', 'opening-test/edl_B2.json', 1541, None),
    ('ch1', 'ch1/edl.json', 1618, (0.6, 3.9)),
    ('ch2', 'ch2/edl.json', 1137, (0.6, 3.9)),
    ('ch3', 'ch3/edl.json', 4767, (0.6, 3.9)),
    ('ch4', 'ch4/edl.json', 2174, (0.6, 3.9)),
    ('ch5', 'ch5/edl.json', 1715, 'edl'),
    ('ch6', 'ch6/edl.json', 1383, 'edl'),
    ('ch7', 'ch7/edl.json', 2121, 'edl'),
    ('ch8', 'ch8/edl.json', 2495, 'edl'),
]

# piece -> {shot index: (place, why it is a drive)}; place source in the note
WA = 'WASHINGTON'   # 0093-0098: left the Seattle shop, Oregon not reached (0098 shows the I-90 "Easton" exit sign); town not named, so the state
DRIVE = {
    'opening': {
        5: (WA, 'montage: top down through the trees, moving (0093, 4 min after the shop)'),
        14: ('NEVADA', 'montage: morning drive, cabin camera, moving (0118; Ch7 "Sunrise · Nevada")'),
        15: ('NEVADA', 'montage: same take, moving (0118)'),
        16: ('LAS VEGAS, NV', 'montage: Las Vegas skyline from the rear deck, moving (0122; the Ch8 "LAS VEGAS" skyline)'),
    },
    'ch3': {
        21: ('SEATTLE, WA', 'drive cutaway, top down, moving, a hand on the wheel (0092; chapter place "Seattle, WA")'),
        22: ('SEATTLE, WA', 'payoff line, top down, the street moving behind him (0092; chapter place)'),
    },
    'ch4': {i: (WA, w) for i, w in [(0, 'side camera, roof down, moving (0093)'), (1, 'side camera, moving (0093)'),
                                      (2, 'forest road, rear camera, moving (0094)'), (3, 'forest road cutaway (0095)'),
                                      (4, 'forest road cutaway (0095)'), (5, 'forest road cutaway (0095)'),
                                      (6, 'montage, forest road (0095)'), (7, 'montage (0095)'), (8, 'montage (0095)'),
                                      (9, 'montage (0095)'), (10, 'montage, highway, pines (0098)'), (11, 'montage (0098)'),
                                      (12, 'montage (0098)'), (13, 'montage (0098)'), (14, 'montage (0098)'),
                                      (15, 'montage, scenery crop (0098, the "Easton" exit sign)'), (16, 'montage (0098)'),
                                      (17, 'montage (0098)')]},
    'ch7': {i: ('NEVADA', w) for i, w in [(0, 'side camera, driving at sunrise (0116)'), (1, 'windscreen cutaway, moving (0116)'),
                                            (2, 'windscreen cutaway, moving (0116)'), (3, 'side camera, one hand on the wheel (0116)'),
                                            (4, 'windscreen cutaway, fields (0117)'), (5, 'windscreen cutaway (0117)'),
                                            (6, 'windscreen cutaway (0117)'), (7, 'cabin, rear camera, driving (0118)'),
                                            (8, 'cabin, driving (0118)'), (9, 'cabin, driving (0118)'), (10, 'cabin, driving (0118)'),
                                            (11, 'pulling in to the station, still rolling, both hands on the wheel (0119)')]},
    'ch8': {**{i: ('NEVADA', w) for i, w in [(2, 'rear deck, leaving the station (0121)'), (3, 'rear deck (0121)'),
                                               (4, 'rear deck (0121)'), (5, 'rear deck (0121)'), (6, 'rear deck (0121)'),
                                               (7, 'rear deck (0121)'), (8, 'rear camera, "almost to the shop" (0122); city not seen, so the state')]},
            **{i: ('LAS VEGAS, NV', 'skyline from the rear deck, moving with traffic (0122; chapter title "LAS VEGAS")')
               for i in (9, 10, 11, 12, 13)}},
}
DRIVE['ch4'][18] = ('OREGON', 'rear camera, moving: "We are in Oregon, we passed the welcome to Oregon sign" (0100)')
DRIVE['ch4'][19] = ('OREGON', 'rear camera, moving: "we just got into Oregon" (0100)')
if not OPENING_DRIVES:
    DRIVE['opening'] = {}

CLIPS = json.load(open(f'{DAY}/clips.json'))
NODES = [  # (name, clip, source s): the place he is on camera in, at that camera-clock moment
    ('Seattle', '0092', 139.95),   # leaving the shop (Ch3 "Seattle, WA")
    ('Oregon', '0100', 18.2),      # "we passed the welcome to Oregon sign"
    ('Idaho', '0106', 283.3),      # "I am in Nampa, Idaho"
    ('Nevada', '0116', 4.55),      # Ch7 "Sunrise · Nevada"
    ('Las Vegas', '0122', 552.6),  # the Las Vegas skyline (Ch8 "LAS VEGAS")
]


def abs_clock(clip, s):
    """Camera clock in seconds since 2026-09-26 00:00 (camera time, PDT)."""
    c = CLIPS[clip]
    day = 0 if '20260926' in c['name'] else 86400
    return day + c['clock'] + s


def clock_str(sec):
    sec = int(sec) % 86400
    h, m = sec // 3600, (sec % 3600) // 60
    return f'{(h % 12) or 12}:{m:02d} {"AM" if h < 12 else "PM"}'


def progress(clk):
    ts = [abs_clock(c, s) for _, c, s in NODES]
    if clk <= ts[0]:
        return 0.0
    for i in range(len(ts) - 1):
        if clk <= ts[i + 1]:
            return (i + (clk - ts[i]) / (ts[i + 1] - ts[i])) / (len(ts) - 1)
    return 1.0


def main():
    out = {'fps': '30000/1001', 'fade': FADE, 'nodes': [], 'pieces': [], 'runs': []}
    for n, c, s in NODES:
        out['nodes'].append(dict(name=n, clip=c, src=s, clock=clock_str(abs_clock(c, s))))
    f0 = 0
    for name, edl, frames, tw in PIECES:
        e = json.load(open(f'{YT}/{edl}'))
        if tw == 'edl':
            tw = (e['title']['t0'], e['title']['t1'])
        g0 = f0 / FPS
        out['pieces'].append(dict(name=name, frame0=f0, frames=frames, t0=round(g0, 4), title=tw))
        shots = []
        for i, s in enumerate(e['shots']):
            if i not in DRIVE.get(name, {}):
                continue
            place, why = DRIVE[name][i]
            sp = s.get('speed', 1.0) or 1.0
            c0 = abs_clock(s['src'], s['in'])
            c1 = abs_clock(s['src'], s['in'] + s['dur'] * sp)
            shots.append(dict(shot=i, clip=s['src'], src_in=s['in'], t=s['t'], dur=s['dur'], speed=sp, place=place,
                              why=why, clock0=c0, clock1=c1, clock=clock_str(c0), clock_end=clock_str(c1),
                              p0=round(progress(c0), 4), p1=round(progress(c1), 4)))
        # merge into runs
        runs = []
        for s in shots:
            if runs and s['t'] - (runs[-1]['t1']) < MERGE:
                runs[-1]['shots'].append(s); runs[-1]['t1'] = s['t'] + s['dur']
            else:
                runs.append(dict(t0=s['t'], t1=s['t'] + s['dur'], shots=[s]))
        # keep off the title card: split a run around it
        fixed = []
        for r in runs:
            if tw and r['t0'] < tw[1] + TITLE_GAP and r['t1'] > tw[0] - TITLE_GAP:
                if r['t0'] < tw[0] - TITLE_GAP - 2 * FADE - 0.5:
                    fixed.append(dict(r, t1=tw[0] - TITLE_GAP))
                if r['t1'] > tw[1] + TITLE_GAP + 2 * FADE + 0.5:
                    fixed.append(dict(r, t0=tw[1] + TITLE_GAP))
            else:
                fixed.append(r)
        chapter_end = frames / FPS
        for r in fixed:
            r['t1'] = min(r['t1'], chapter_end)
            # never end a run on a sliver of a new shot (a place/clock change right before the fade-out)
            last = [s for s in r['shots'] if s['t'] < r['t1']][-1]
            if r['t1'] - last['t'] < 1.0 and last['t'] > r['t0'] + 1.0:
                r['t1'] = last['t']
            sh = [s for s in r['shots'] if s['t'] < r['t1'] and s['t'] + s['dur'] > r['t0']]
            # a run whose shots play out of clock order holds its earliest time, so the clock never steps back
            # (Omarie 2026-10-09, Ch3 end: "Hold 11:58")
            if any(b['clock0'] // 60 < a['clock0'] // 60 for a, b in zip(sh, sh[1:])):   # a visible step back
                lo = min(s['clock0'] for s in sh)
                for s in sh:
                    s.update(clock_hold=lo, clock=clock_str(lo), clock_end=clock_str(lo),
                             p0=round(progress(lo), 4), p1=round(progress(lo), 4))
            out['runs'].append(dict(piece=name, t0=round(r['t0'], 4), t1=round(r['t1'], 4),
                                    g0=round(g0 + r['t0'], 4), g1=round(g0 + r['t1'], 4),
                                    f0=f0 + round(r['t0'] * FPS), f1=f0 + round(r['t1'] * FPS), shots=sh))
        f0 += frames
    out['total_frames'] = f0
    json.dump(out, open(f'{HERE}/hud.json', 'w'), indent=1)
    for r in out['runs']:
        print(f"{r['piece']:8s} ch {r['t0']:7.2f}-{r['t1']:7.2f}  global {r['g0']:7.2f}-{r['g1']:7.2f}  "
              + ' | '.join(f"{s['clip']}#{s['shot']} {s['place']} {s['clock']} p{s['p0']:.2f}" for s in r['shots']))
    print('total frames', f0, 'nodes', [(n['name'], n['clock']) for n in out['nodes']])


if __name__ == '__main__':
    main()
