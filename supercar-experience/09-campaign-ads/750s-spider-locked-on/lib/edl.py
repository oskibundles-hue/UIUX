"""
edl.py -- edit decision list for "ROOF DOWN" (McLaren 750S Spider, LOCKED ON standard), 18.018 s 9:16.

Timing and plate FX only. No copy or figures live here (those are in ../config.json).

Conventions (as in the approved GT3 RS showcase, ../flash-special-showcase/lib/edl.py)
  * Output: 432 frames at 24000/1001 fps. Output frame i is shown at t = i / FPS.
  * Source positions p are 0-based SOURCE FRAME numbers of SCE_McLaren-750S_no-branding.mov, decoded in
    order (never with -ss). Fractional p = blend of floor(p) and floor(p)+1 (or optical flow in S1).
  * speed = source frames per output frame (same fps, so also source-seconds per output-second).
  * span = shutter span in source frames (180 deg: 0.5 * speed).

Music grid. The clip's own music runs at 130.0 BPM; its beats sit at G0 + k * BEAT with G0 = 0.1154 s
(fitted on the spectral-flux onsets of orig 5-18 s; the intro fits the same phase). Bars start on
k = 2, 6, 10, ... The low end enters on k = 10 (4.731 s: THE DROP) and the loudest hit, a crash, is on
k = 26 (12.115 s). The music plays from orig 0.000 with no edit, so output time = music time and every
cut below is a beat of the track.
"""
import math

FPS = 24000 / 1001
NF = 432
DUR = NF / FPS                      # 18.018 s

BPM = 130.0
BEAT = 60.0 / BPM                   # 0.461538 s
G0 = 0.1154                         # first beat (orig seconds)


def g(k):
    """time of beat k of the clip's music (s)"""
    return G0 + k * BEAT


def fr(t):
    """time (s) -> output frame index"""
    return int(round(t * FPS + 1e-9))


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


def ST(gain, thresh=0.85, point=0.12, point_radius=90):
    return dict(thresh=thresh, point=point, point_radius=point_radius, gain=gain)


# ---------------------------------------------------------------------------------- key times
T_DROP = g(10)                      # 4.731 bass drop: impact, offer panel
T_CRASH = g(26)                     # 12.115 crash: light impact, glint on the giant word
T_STOP0, T_END = g(29), g(30)       # 13.500 tape stop starts; 13.962 end-card hit (bar downbeat)
T_RESUME = T_END + 0.25             # the roof starts moving again under the end card

# ------------------------------------------------------------------------------ BEAT TABLE
# a/b: cue times (s) on the music grid. fa/fb: first/last usable source frame of the shot (the sampler
# never blends across a source cut). speed: source frames per output frame, or keys (eased ramp).
# Shot boundaries in the source (cut detection, 0-based): S1 0-67 roof, S3 77-95 pass, S4 96-111 roadside,
# S5 112-124 hands, S6 125-134 exhaust (RYFT marks: not used), S7 135-157 headlight, S8 158-170 intake,
# S9 171-203 wheel/line, S10 204-225 POV badge, S11 226-250 bridge wheel, S12 251-282 approach,
# S13 283-301 hands, S14 302-312 intake, S15 313-334 front/cactus, S16 335-347 POV, S17 348-368 rear chase
# (plate), S18 369-379 front 3/4 + 380-392 front hero, S19 393-434 POV, S20 435-583 wide valley.
BEATS = [
    dict(id=1, a=0.0, b=g(2), fa=380, fb=392, speed=0.5, streak=ST(0.55, thresh=0.9, point=0.2, point_radius=60),
         what='HOOK: front hero, LED headlights, 0.5x'),
    # review r2: 1.0x on whole source frames (at 1.3x the optical flow melted the car as it neared the lens)
    dict(id=2, a=g(2), b=g(4), fa=261, fb=282, speed=1.0, what='HOOK: locked-off canyon approach, whole frames'),
    dict(id=3, a=g(4), b=g(6), fa=313, fb=334, speed=1.0, what='HOOK: front approach, saguaro road'),
    dict(id=4, a=g(6), b=g(9) + 0.75 * BEAT, fa=204, fb=225, speed=0.525, span_min=1.0,
         what='BADGE: POV wheel, McLaren speedmark (tracked: badge), bridge'),
    dict(id=5, a=g(9) + 0.75 * BEAT, b=g(10), black=True, what='BLACK (drop gap, 2 frames)'),
    dict(id=6, a=g(10), b=g(12), fa=173, fb=203, keys=[(0, 1.9), (0.3, 0.8), (1.0, 0.8)],
         what='DROP: low wheel tracking along the white line, ramp 1.9x -> 0.8x'),
    dict(id=7, a=g(12), b=g(14), fa=226, fb=250, speed=1.0, lift=0.85, streak=ST(0.6, thresh=0.93, point=0.25, point_radius=60),
         what='under the bridge, sun flares on the wheel'),
    dict(id=8, a=g(14), b=g(15), fa=138, fb=157, speed=1.0, streak=ST(0.5, thresh=0.9, point=0.2, point_radius=60),
         what='headlight glide (tracked: headlight)'),
    dict(id=9, a=g(15), b=g(16), fa=158, fb=170, speed=1.0, what='side intake, red accent'),
    dict(id=10, a=g(16), b=g(17), fa=112, fb=122, speed=1.0, lift=0.85, what='hands on the carbon wheel'),
    dict(id=11, a=g(17), b=g(18), fa=352, fb=368, speed=1.0, what='rear chase on the curve (licence plate blurred)'),
    dict(id=12, a=g(18), b=g(20), fa=466, fb=583, speed=1.0, what='REQUIREMENTS: wide valley, the car on the road'),
    dict(id=13, a=g(20), b=g(21), fa=99, fb=111, speed=1.0, what='roadside pass, the car enters past the rock'),
    dict(id=14, a=g(21), b=g(22), fa=369, fb=379, speed=0.95, what='front 3/4, rocks'),
    dict(id=15, a=g(22), b=g(23), fa=79, fb=95, speed=1.3, what='whip-pan pass (natural blur)'),
    dict(id=16, a=g(23), b=DUR + 0.001, roof=True, fa=0, fb=67,
         what='ROOF DOWN: locked-off rear, the roof stows; giant SPIDER behind the car; end card'),
]
for B in BEATS:
    B['i0'], B['i1'] = fr(B['a']), min(fr(B['b']), NF)

# whips: (boundary frame, direction). WHIP_K frames each side of the boundary.
WHIPS = [(BEATS[6]['i0'], 'left'), (BEATS[11]['i0'], 'up'), (BEATS[15]['i0'], 'left')]
WHIP_K = 3

# impacts: (frame, strength, seed, frames)
IMPACTS = [(BEATS[5]['i0'], 1.0, 5, 16)]
# the crash (12.115 s) is NOT a plate impact (review r1: punching the plate after the sky matte was cut slid the
# behind-car type over the car for 10 frames, then snapped back). build.py applies it to the composite of plate +
# matted type instead: a zoom punch 1.035 -> 1.0 over CRASH_N frames (outCubic) and a one-frame 5 % luma lift.
CRASH_F, CRASH_N, CRASH_PUNCH, CRASH_LIFT = fr(T_CRASH), 10, 0.035, 0.05

# leak bursts: (centre s, peak, side, sigma frames)
LEAKS = [(g(2), 0.18, 'right', 3.0), (g(6), 0.22, 'left', 3.5), (g(14), 0.22, 'right', 3.0),
         (g(23), 0.26, 'left', 4.0), (T_CRASH, 0.24, 'right', 4.0), (T_END, 0.16, 'left', 6.0)]

# continuous push on the hook (beats 1-3): scale 1.00 -> 1.04, outCubic over the hook
PUSH_HOOK = (0.0, g(6), 1.00, 1.04)

# roof shot (beat 16): the plate runs these speeds (source frames per output frame, S1 is optical-flow
# densified 4x so slow speeds stay smooth). Tape stop 13.500 -> 13.962 decelerates to a freeze; the roof
# resumes under the end card and finishes stowing near the end.
ROOF_F0 = 0.0
ROOF_V1 = 0.55                      # g(23) -> crash
ROOF_V2 = 0.50                      # crash -> tape stop
ROOF_LAST = 64.0                    # last source frame reached at the end
# 2.5D push on the roof shot: plate scale 1.000 -> PUSH_ROOF over the shot (about the car's taillight)
PUSH_ROOF = 1.045
PUSH_ROOF_C = (540.0, 1130.0)


def _fit(fa, fb, n, v):
    return min(v, (fb - fa) / max(n - 1, 1))


def _roof(n0, i0):
    """per-frame source positions for the roof shot"""
    out = []
    p = ROOF_F0
    i_crash, i_stop, i_end, i_res = fr(T_CRASH), fr(T_STOP0), fr(T_END), fr(T_RESUME)
    for i in range(i0, i0 + n0):
        t = i / FPS
        if i < i_crash:
            v = ROOF_V1
        elif i < i_stop:
            v = ROOF_V2
        else:
            v = None
        if v is not None:
            out.append((p, 0.5 * v))
            p += v
            continue
        if i < i_res:                                     # tape stop decel then freeze
            out.append((p, 0.0))
            for k in range(8):
                tt = t + (k + 0.5) / 8 / FPS
                u = (tt - T_STOP0) / (T_END - T_STOP0)
                p += (ROOF_V2 * (1 - min(max(u, 0), 1)) ** 3 if tt < T_END else 0.0) / 8
            continue
        out.append(None)                                  # filled below
    # resume: 8-frame ease-in, then constant, landing on ROOF_LAST at the last frame
    j0 = next(k for k, o in enumerate(out) if o is None)
    n_res = len(out) - j0
    ramp = [smootherstep(min(1.0, (j + 1) / 8)) for j in range(n_res)]
    v = (ROOF_LAST - p) / sum(ramp[:-1])
    for j in range(n_res):
        out[j0 + j] = (p, 0.5 * v * ramp[j])
        p += v * ramp[j]
    return out


def build():
    """Per output frame: dict(i, t, beat, j, p, span)."""
    out = [None] * NF
    for B in BEATS:
        n = B['i1'] - B['i0']
        if B.get('black'):
            ps = [(None, 0)] * n
        elif B.get('roof'):
            ps = _roof(n, B['i0'])
        elif 'keys' in B:
            p, ps = float(B['fa']), []
            for j in range(n):
                s = speed_at(j / max(n - 1, 1), B['keys'])
                ps.append((p, s * 0.5))
                for k in range(8):
                    p += speed_at((j + (k + 0.5) / 8) / max(n - 1, 1), B['keys']) / 8
            assert ps[-1][0] <= B['fb'], (B['id'], ps[-1][0])
        else:
            v = _fit(B['fa'], B['fb'], n, B['speed'])
            ps = [(B['fa'] + v * j, 0.5 * v) for j in range(n)]
        for j, (p, span) in enumerate(ps):
            i = B['i0'] + j
            out[i] = dict(i=i, t=i / FPS, beat=B['id'], j=j, p=p, span=span)
    assert all(o is not None for o in out)
    return out


def beat(bid):
    return BEATS[bid - 1]


if __name__ == '__main__':
    tl = build()
    for B in BEATS:
        a, b = tl[B['i0']], tl[B['i1'] - 1]
        fmt = lambda o: None if o['p'] is None else round(o['p'], 2)
        print(f"beat {B['id']:2d} {B['a']:6.3f}-{B['b']:6.3f} frames {B['i0']:3d}-{B['i1'] - 1:3d} ({B['i1'] - B['i0']:3d})"
              f"  p {fmt(a)} -> {fmt(b)}   {B['what']}")
    print('drop', fr(T_DROP), 'crash', fr(T_CRASH), 'stop', fr(T_STOP0), 'end', fr(T_END), 'resume', fr(T_RESUME))
