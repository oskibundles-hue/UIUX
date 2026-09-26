"""
edl.py -- the edit decision list for the SE flash-special showcase ("LOCKED ON", GT3 RS), 18.0 s.

Everything here is timing and plate FX. No copy and no figures live here (those are in
../config.json). The beat table is the judge's final build cue (../cue.md), written as data.

Conventions
  * Output: 432 frames at 24000/1001 fps. Output frame i is shown at t = i * 1001 / 24000 s.
    A cue time T (s) maps to frame round(T * FPS), which matches bed_hero_sync.json "f23976".
  * Source positions p are 0-based SOURCE FRAME numbers of GT3RS_livery.mov (decoded in order,
    never with -ss). Fractional p = blend of floor(p) and floor(p)+1.
  * speed = source frames per output frame (= source-seconds per output-second, same fps).
  * span = shutter span in source frames (180 deg shutter: 0.5 * speed).
"""
import math

FPS = 24000 / 1001
NF = 432
DUR = NF / FPS  # 18.018 s of picture; the bed is 18.000 s


Q = 60 / 140 / 4   # 1/16 note at 140 BPM; cue times are this grid rounded to 3 decimals


def snap(t):
    """Undo the cue's 3-decimal rounding: 8.571 -> 8.5714286 (the bed's real grid time)."""
    g = round(t / Q) * Q
    return g if abs(g - t) < 0.0015 else t


def fr(t):
    """cue time (s) -> output frame index (same rounding as bed_hero_sync.json f23976)."""
    return int(round(snap(t) * FPS + 1e-9))


def smootherstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (x * 6 - 15) + 10)


def speed_at(u, keys):
    if u <= keys[0][0]:
        return keys[0][1]
    for (u0, s0), (u1, s1) in zip(keys, keys[1:]):
        if u <= u1:
            return s0 + (s1 - s0) * smootherstep((u - u0) / max(u1 - u0, 1e-9))
    return keys[-1][1]


# streak presets (fx.streaks kwargs)
def ST(gain, thresh=0.85, point=0.12, point_radius=90):
    return dict(thresh=thresh, point=point, point_radius=point_radius, gain=gain)


# ------------------------------------------------------------------------------ BEAT TABLE
# a/b: cue times (s). fa/fb: first/last usable source frame of the shot (hard limits: the
# sampler never blends across a source cut). speed: nominal source frames per output frame.
BEATS = [
    dict(id=1, a=0.000, b=0.643, fa=34, fb=44, speed=0.71, what='tunnel side pass, red wheels'),
    dict(id=2, a=0.643, b=1.714, fa=9, fb=22, speed=0.545, what='rear wing, light bar, badge'),
    dict(id=3, a=1.714, b=2.143, fa=46, fb=59, speed=1.26, what='hand on DRIVE MODE knob'),
    dict(id=4, a=2.143, b=3.000, fa=62, fb=72, speed=0.535, hold=True,
         what='mode dial Normal -> Sport (skips f60-61 gauges); frame-hold, the UI switches colour between f63 and f64'),
    dict(id=5, a=3.000, b=3.429, fa=73, fb=78, speed=0.58, dense=(73, 78, 4), what='foot on pedal'),
    dict(id=6, a=3.429, b=3.857, fa=156, fb=166, speed=0.97, what='hood, stripes'),
    dict(id=7, a=3.857, b=4.286, fa=168, fb=177, speed=0.97, what='GT3RS door script (tracked: door)'),
    dict(id=8, a=4.286, b=4.714, fa=0, fb=7, speed=0.78, what='wing strut close, dark'),
    dict(id=9, a=4.714, b=5.143, fa=188, fb=195, speed=0.68, what='swan-neck + red wheel'),
    dict(id=10, a=5.143, b=5.571, fa=196, fb=205, speed=0.87, what='wing endplate + taillight', streak=ST(0.9)),
    dict(id=11, a=5.571, b=6.429, fa=226, fb=246, speed=1.02, what='drive-away rear 3/4 (licence plate blurred)',
         streak=ST(1.0)),
    dict(id=12, a=6.429, b=8.357, fa=80, fb=108, speed=0.605, what='Porsche crest on carbon (tracked: crest)',
         streak=ST(0.8)),
    # 5 black frames (201-205); frame 200 still belongs to the crest so the callout whip completes
    dict(id=13, a=8.380, b=8.571, black=True, what='BLACK (drop gap)'),
    dict(id=14, a=8.571, b=10.714, fa=121, fb=154, keys=[(0, 1.6), (0.28, 0.45), (1.0, 0.55)],
         dense=(129, 154, 4), what='tunnel front 3/4, headlights (ramp + optical-flow slow-mo)',
         # fix r1: stricter point-source test (the white body no longer streaks into a smear that
         # boxed in the front wheel) + lower gain below y 820; warm-hue protect keeps the copper wheel
         streak_split=(820, ST(0.8, thresh=0.93, point=0.25, point_radius=60),
                       ST(0.8, thresh=0.93, point=0.25, point_radius=60)),
         warm_protect=0.75),
    # fix r1: was f256-276 ceiling-lamp flares (a 12 Hz full-frame strobe). Now the unused rear
    # tracking shot f206-224 (plate tracked + blurred, lib/data/plate3_track.json), lowered 210 px
    # so the car sits under the price panel, not behind it.
    dict(id=15, a=10.714, b=11.571, fa=206, fb=224, speed=0.9, what='rear tracking in tunnel (plate blurred)',
         streak=ST(0.7), drop=210),
    dict(id=16, a=11.571, b=12.000, fa=279, fb=287, speed=0.78, what='chrome PORSCHE rear script',
         streak=ST(0.7)),
    dict(id=17, a=12.000, b=13.714, ware=True, what='warehouse, 0.45x'),
    dict(id=18, a=13.714, b=14.250, ware=True, what='warehouse, tape stop to a short freeze (~7 frames)'),
    dict(id=19, a=14.250, b=18.020, ware=True, what='warehouse, resumes; end card hit at 14.571'),
]
for B in BEATS:
    B['i0'], B['i1'] = fr(B['a']), min(fr(B['b']), NF)   # frames [i0, i1)
# the black gap: cue says 5 frames; 8.380 rounds to 201, so the crest owns 154..200
assert BEATS[12]['i0'] == 201 and BEATS[12]['i1'] == 206, (BEATS[12]['i0'], BEATS[12]['i1'])
BEATS[11]['i1'] = 201

# whips: (boundary cue time, direction). k=3 frames each side.
WHIPS = [(1.714, 'right'), (3.429, 'up'), (5.571, 'left'), (10.714, 'left')]
WHIP_K = 3

# leak bursts: (centre s, peak, side, sigma frames)
LEAKS = [(0.643, 0.25, 'right', 3.5), (3.429, 0.20, 'left', 3.5), (6.429, 0.30, 'right', 3.5),
         (8.571 + 2 / FPS, 0.35, 'left', 4.0)]

# beat 1-5 continuous push, beat 4 push-in, beat 5 punch, beat 1 shake
PUSH_A = (0.0, 3.25, 1.00, 1.03)       # outCubic
DROP_FRAME = fr(8.571)                 # 206 -> fx.impact k = i - 206, k 0..15
IMPACT_SEED = 5
PUNCH_T = 3.214                        # 2-frame zoom punch 1.03

# warehouse (beats 17-19)
WARE_F0 = 290                          # ware frames = source frames 290..334 (track.json index 0 = f290)
WARE_START = 291
# fix r1: the freeze was 25 frames (14.17-15.18) and the end card only landed at 15.429. Tape stop
# and swell are now a quarter bar each (bed_hero.py --tapestop-len 0.25 --swell-len 0.25), so the
# end card lands at bar 8.5 = 14.571 s, 0.857 s earlier, and the phone number reads for ~2.8 s.
T_STOP0, T_STOP1 = 13.714, 14.143      # tape stop decel (speed 0.45*(1-u)^3)
T_RESUME = 14.250                      # plate resumes (beat 19): frozen ~13.97-14.25
T_SWELL, T_END = 14.143, 14.571        # grade recovers over the swell; end card hit (impact_3)
SWEEP = (13.93, 14.47)                 # light sweep across the car body, inside the freeze
HAIRLINE = (14.00, 14.40)              # gold floor hairline draws during the freeze
WARE_LAST = 333.5                      # 13.91 s


def _fit(fa, fb, n, v):
    return min(v, (fb - fa) / max(n - 1, 1))


def build():
    """Per output frame: dict(i, t, beat, j, p, span)."""
    out = [None] * NF
    for B in BEATS:
        n = B['i1'] - B['i0']
        if B.get('black'):
            for j in range(n):
                i = B['i0'] + j
                out[i] = dict(i=i, t=i / FPS, beat=B['id'], j=j, p=None, span=0)
            continue
        if B.get('ware'):
            continue
        if 'keys' in B:
            p, ps = float(B['fa']), []
            for j in range(n):
                u = j / max(n - 1, 1)
                s = speed_at(u, B['keys'])
                ps.append((p, s * 0.5))
                for k in range(8):
                    uu = (j + (k + 0.5) / 8) / max(n - 1, 1)
                    p += speed_at(uu, B['keys']) / 8
            assert ps[-1][0] <= 6.40 * FPS, ('beat 14 overruns 6.40 s', ps[-1][0] / FPS)
            assert ps[-1][0] <= B['fb'], ps[-1][0]
        else:
            v = _fit(B['fa'], B['fb'], n, B['speed'])
            ps = [(B['fa'] + v * j, 0.5 * v) for j in range(n)]
        for j, (p, span) in enumerate(ps):
            i = B['i0'] + j
            out[i] = dict(i=i, t=i / FPS, beat=B['id'], j=j, p=p, span=span)

    # ---- warehouse: 17 at 0.45x, 18 tape stop (speed 0.45*(1-u)^3) then freeze, 19 resumes
    i17, i18, i19 = BEATS[16]['i0'], BEATS[17]['i0'], BEATS[18]['i0']
    p = float(WARE_START)
    for i in range(i17, i18):
        out[i] = dict(i=i, t=i / FPS, beat=17, j=i - i17, p=p, span=0.225)
        p += 0.45
    for i in range(i18, i19):
        t = i / FPS
        out[i] = dict(i=i, t=t, beat=18, j=i - i18, p=p, span=0)
        # integrate the decel over this frame (8 sub-steps)
        for k in range(8):
            tt = t + (k + 0.5) / 8 / FPS
            u = (tt - T_STOP0) / (T_STOP1 - T_STOP0)
            s = 0.45 * (1 - min(max(u, 0), 1)) ** 3 if tt < T_STOP1 else 0.0
            p += s / 8
    p_freeze = p
    n19 = NF - i19
    ramp = [min(1.0, (j + 1) / 7) for j in range(n19)]           # 6-frame ease-in, then constant
    ramp = [smootherstep(r) if r < 1 else 1.0 for r in ramp]
    v = (WARE_LAST - p_freeze) / sum(ramp[:-1])
    for j in range(n19):
        i = i19 + j
        out[i] = dict(i=i, t=i / FPS, beat=19, j=j, p=p, span=0)
        p += v * ramp[j]
    assert all(o is not None for o in out)
    meta = dict(p_freeze=p_freeze, v19=v, p_last=out[-1]['p'])
    return out, meta


def beat(bid):
    return BEATS[bid - 1]


if __name__ == '__main__':
    tl, meta = build()
    for B in BEATS:
        a, b = tl[B['i0']], tl[B['i1'] - 1]
        print(f"beat {B['id']:2d} frames {B['i0']:3d}-{B['i1'] - 1:3d} ({B['i1'] - B['i0']:2d})  "
              f"p {a['p'] if a['p'] is None else round(a['p'], 2)} -> "
              f"{b['p'] if b['p'] is None else round(b['p'], 2)}   {B['what']}")
    print(meta, 'freeze src s', meta['p_freeze'] / FPS)
