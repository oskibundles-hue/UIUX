"""Natural car sound: every footage shot plays its own clip's engine and road sound under the music.

The raw clips are Supercar Experience's own fleet footage ("01 Car Footage", no-branding exports), and their audio is
the cars themselves: engine, revs, tyres, pass-bys. This lines each shot's audio up with its plate (same in-point,
same speed: slow shots are slowed with the picture, so they drop in pitch), levels it by the shot's role, and ducks
the music where a car leads. Rally selfie (21) is speech, and the STO clip is silent after 20 s (12, 14, 34): no sound.

  role     car level (LUFS, in the engine's mix scale)   music while it plays
  under    -28   texture, 13 LU under the music bed      as is
  feature  -21   you notice the car                      -3 dB
  hero     -15   the car leads                           -6 dB (shot 30: its own curve, below)

The music bed sits near -15 LUFS in that scale (music_roar at -9.7 LUFS x the engine's 0.55 gain).
Shot 30's curve: -3 dB over the start button and the SPORT dial (so the clicks read), the engine fires on its frame 36
(the 30 s cut's music drop lands there too), the music sits 9 dB down for 0.8 s while the engine leads, then comes back.

Writes public/audio/car<cut>.wav (the car stem) and public/audio/bed<cut>.wav (music x gain x ducks + car stem: the
SFX engine's "music", so every cue is set against music and engine together), sfx/car_audio<cut>.json (what each shot
got, and why) and src/rev_env.ts (shot 30's engine envelope, per frame, for the rev meter).

  uv run --no-project --quiet --with numpy --with scipy --with soundfile --with pyloudnorm python tools/car_audio.py --cut 76
"""
import argparse, json, os, subprocess
from fractions import Fraction
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly

SR = 48000
here = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(here, '..')
RAW = os.path.join(P, 'raw')

CUTS = {
    '76': dict(shots='shots.json', music='public/audio/music_roar.wav', total=2295),
    '30': dict(shots='shots30.json', music='public/audio/music_roar30.wav', total=900),
}
MUSIC_GAIN = 0.55          # the engine's music gain before this tool existed; the bed carries it now (events: gain 1.0)

ROLE = {2: 'under', 3: 'under', 4: 'feature', 5: 'feature', 6: 'under', 7: 'under', 8: 'feature', 9: 'under',
        10: 'under', 15: 'under', 20: 'under', 22: 'under', 27: 'feature', 28: 'under', 30: 'hero', 31: 'feature',
        32: 'hero', 33: 'under'}
WHY = {2: 'Sphere establishing: AMG idle under the push-in', 3: 'STO cruising the Strip', 4: 'McLaren POV, slowed 0.45x: a low drone under the text bubble',
       5: 'STO start button: the click and the start', 6: 'SF90 under REV', 7: 'SF90 under the thought bubble', 8: '"Launch?": AMG pulls hard under the flames',
       9: 'SF90 under the pixel code', 10: 'SF90 under "Let me book it"', 15: '750S in the desert', 20: 'Urus on the desert road',
       22: 'wheel on the road line', 27: 'the semi whips past the GT3 RS', 28: 'GT3 RS tracking shot',
       30: 'GT3 RS start-up: button, SPORT, foot down, the engine fires (frame 36), the launch', 31: 'GT3 RS revs build under the riser',
       32: 'AMG pulls out of the night', 33: 'GT3 RS in the garage, slowed 0.55x'}
TARGET = {'under': -28.0, 'feature': -21.0, 'hero': -15.0}
DUCK = {'under': 0.0, 'feature': -3.0, 'hero': -6.0}
DUCK_CURVE = {30: [(0.0, -3), (1.1, -3), (1.2, -9), (2.0, -9), (2.6, -3)]}   # shot-local s -> dB; holds the last value
MAX_GAIN, MIN_GAIN = 12.0, -24.0
TAIL_INTO_GFX, TAIL_INTO_CAR, FADE_IN = 0.30, 0.03, 0.008


def decode(src, ss, dur):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{ss:.4f}', '-t', f'{dur:.4f}', '-i', os.path.join(RAW, src), '-map', '0:a:0',
                        '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(r, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(round(dur * SR))
    return np.pad(x, ((0, max(0, n - len(x))), (0, 0)))[:n]


def shot_audio(s, length):
    """The shot's own clip audio for `length` s of screen time, lined up with its plate (parts joined, varispeed)."""
    speed = s.get('speed', 1)
    parts = s.get('parts') or [dict(ss=s['ss'], len=length)]
    segs, used = [], 0.0
    for i, pt in enumerate(parts):
        ln = (length - used) if i == len(parts) - 1 else min(pt['len'], length - used)
        if ln <= 0:
            break
        x = decode(s['src'], pt['ss'], ln * speed)
        if speed != 1:
            fr = Fraction(speed).limit_denominator(100)
            x = resample_poly(x, fr.denominator, fr.numerator, axis=0)
        n = int(round(ln * SR))
        x = np.pad(x, ((0, max(0, n - len(x))), (0, 0)))[:n]
        if segs:                                     # 5 ms crossfade at the join
            k = int(0.005 * SR)
            w = np.linspace(0, 1, k)[:, None]
            segs[-1][-k:] = segs[-1][-k:] * (1 - w) + x[:k] * w
            x = x[k:]
        segs.append(x.copy())
        used += ln
    return np.concatenate(segs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cut', default='76', choices=sorted(CUTS))
    cut = ap.parse_args().cut
    c = CUTS[cut]
    shots = sorted((s for s in json.load(open(os.path.join(P, c['shots']))) if s['t1'] > s['t0']), key=lambda s: s['t0'])
    n = int(round(c['total'] / 30 * SR))
    car = np.zeros((n + SR, 2))
    meter = pyln.Meter(SR, block_size=0.4)
    duck = np.zeros(int(c['total'] / 30 * 100) + 2)          # music duck in dB, 10 ms steps
    report = []
    for i, s in enumerate(shots):
        role = ROLE.get(s['id']) if s.get('src') else None
        if not role:
            report.append(dict(shot=s['id'], t=s['t0'], role='none', why='graphics shot, speech (21) or the clip is silent here (12, 14, 34)'
                               if s['id'] in (12, 14, 21, 34) else 'graphics or title shot'))
            continue
        L = s['t1'] - s['t0']
        nxt = shots[i + 1] if i + 1 < len(shots) else None
        tail = TAIL_INTO_CAR if nxt and ROLE.get(nxt['id']) and nxt.get('src') else TAIL_INTO_GFX
        x = shot_audio(s, L + tail)
        body = x[:int(L * SR)]
        lufs = meter.integrated_loudness(body) if len(body) > 0.45 * SR else -70.0
        if not np.isfinite(lufs) or lufs < -60:
            report.append(dict(shot=s['id'], t=s['t0'], role='none', why=f'clip is silent here ({lufs:.0f} LUFS)'))
            continue
        g = float(np.clip(TARGET[role] - lufs, MIN_GAIN, MAX_GAIN))
        x *= 10 ** (g / 20)
        k = int(FADE_IN * SR)
        x[:k] *= np.linspace(0, 1, k)[:, None]
        kt = int(tail * SR)
        x[-kt:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, kt)))[:, None]
        i0 = int(round(s['t0'] * SR))
        car[i0:i0 + len(x)] += x[:len(car) - i0]
        a, b = int(round(s['t0'] * 100)), int(round(s['t1'] * 100))
        if s['id'] in DUCK_CURVE:
            ts, vs = zip(*DUCK_CURVE[s['id']])
            duck[a:b] = np.minimum(duck[a:b], np.interp(np.arange(b - a) / 100, ts, vs))
        else:
            duck[a:b] = np.minimum(duck[a:b], DUCK[role])
        report.append(dict(shot=s['id'], t=s['t0'], role=role, src=s['src'], ss=s.get('ss'), speed=s.get('speed', 1),
                           clip_lufs=round(lufs, 1), gain_db=round(g, 1), target_lufs=TARGET[role],
                           capped=bool(g in (MAX_GAIN, MIN_GAIN)), duck_db=DUCK_CURVE.get(s['id'], DUCK[role]),
                           tail_s=tail, why=WHY.get(s['id'], '')))
    car = car[:n]
    # music: the engine's gain, then the ducks (smoothed over 40 ms so they never click)
    mus, msr = sf.read(os.path.join(P, c['music']), always_2d=True)
    assert msr == SR
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n] * MUSIC_GAIN
    duck = np.convolve(duck, np.ones(4) / 4, 'same')
    d = np.interp(np.arange(n) / SR * 100, np.arange(len(duck)), duck)
    bed = mus * (10 ** (d / 20))[:, None] + car
    sf.write(os.path.join(P, 'public', 'audio', f'car{cut}.wav'), car.astype(np.float32), SR, subtype='FLOAT')
    sf.write(os.path.join(P, 'public', 'audio', f'bed{cut}.wav'), bed.astype(np.float32), SR, subtype='FLOAT')
    car_l = meter.integrated_loudness(car)
    mus_l = meter.integrated_loudness(mus)
    json.dump(dict(cut=cut, music=c['music'], music_gain=MUSIC_GAIN, music_lufs=round(mus_l, 1), car_stem_lufs=round(car_l, 1),
                   bed_peak_dbfs=round(20 * np.log10(np.abs(bed).max() + 1e-12), 1), shots=report),
              open(os.path.join(P, 'sfx', f'car_audio{cut}.json'), 'w'), indent=1)

    # shot 30's engine envelope (its own clip, before any gain) for the rev meter: 0..1 per frame, plate length
    s30 = next((s for s in shots if s['id'] == 30), None)
    if s30:
        x = shot_audio(s30, 4.0).mean(axis=1)
        hop = SR // 30
        rms = np.array([np.sqrt((x[j * hop:(j + 1) * hop] ** 2).mean()) for j in range(len(x) // hop)])
        lv = np.clip((20 * np.log10(rms + 1e-9) + 42) / 40, 0, 1)
        open(os.path.join(P, 'src', 'rev_env.ts'), 'w').write(
            '// Shot 30 engine loudness per frame (0..1, -42..-2 dBFS), from the GT3 RS clip\'s own audio. Made by tools/car_audio.py.\n'
            f'export const REV_ENV = [{", ".join(f"{v:.2f}" for v in lv)}];\n')

    roles = {}
    for r in report:
        roles[r['role']] = roles.get(r['role'], 0) + 1
    print(f'cut {cut}: car stem {car_l:.1f} LUFS vs music {mus_l:.1f} LUFS; shots {roles}; '
          f'capped {[r["shot"] for r in report if r.get("capped")]}; wrote car{cut}.wav, bed{cut}.wav, sfx/car_audio{cut}.json')


if __name__ == '__main__':
    main()
