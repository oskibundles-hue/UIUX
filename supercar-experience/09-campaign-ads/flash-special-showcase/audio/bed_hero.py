#!/usr/bin/env python3
"""
bed.py -- hybrid trap / cinematic sound bed for the Supercar Experience showcase story, plus a
beat/sync map the picture edit cuts to. numpy + ffmpeg only; every sound comes from synth.py.

USAGE
  python3 bed.py                                   # 18.0 s @ 140 BPM -> out/bed.wav + out/bed_sync.json
  python3 bed.py --duration 15 --bpm 128 --seed 7 --out out/bed15
  python3 bed.py --cue drop=4.5 --cue impact_2=6.5  # override cue positions (in BARS from 0)
  python3 bed.py --whoosh 1,2,3,3.5,6,7.5           # whoosh peak positions (BARS) = your shot cuts
  python3 bed.py --no-engine                        # drop the synthesized engine layers
  python3 bed.py --ffmpeg /path/to/ffmpeg

ARRANGEMENT (reference: 10.5 bars = 18.0 s at 140 BPM, 4/4, key F minor)
  bar 0     impact_open   cold-open hit; flat-six (GT3 RS) blip, blip, full rev to the limiter
  bar 2     groove        half-time trap: kick + 808 + clap on 3 + hats with rolls; Fm|Fm|Db|Eb pad
  bar 4     riser_start   kick/808 drop out, noise+saw riser, accelerating snare roll
  bar 4.875 drop_gap      1/8-bar of silence (everything cut) -> the drop lands harder
  bar 5     drop          = impact_1 = price_1 reveal (GT3 RS $1,200): impact + braam + full beat
  bar 6.5   v8_burble     cross-plane V8 (AMG) overrun pops + downshift blips
  bar 7     impact_2      = price_2 reveal (Black Series $800): impact + braam + V8 on throttle
  bar 8     tapestop      whole mix tape-stops over half a bar
  bar 8.5   swell_start   reversed chord/cymbal bloom
  bar 9     endcard       = impact_3: big hit + braam + Fm pad + FM-bell logo sting, rings out
  bar 10.5  end
  For other durations the front section (0 .. tapestop) is scaled and snapped to half bars; the
  tape stop, swell and end card keep fixed musical lengths (0.5 / 0.5 / >=1.5 bars).

OUTPUT
  <out>.wav        48 kHz / 24-bit stereo, loudnorm'd to -14 LUFS integrated, true peak <= -1.5 dBTP
  <out>_sync.json  bpm, beat/bar grid, sections, named hits (seconds + frame numbers at 24 and
                   23.976 fps), every kick/clap/whoosh time, suggested cut points, master readings,
                   and the exact regeneration parameters.

MASTERING
  numpy pre-master (HP 28 Hz, glue saturation, gain iteration + 4x-oversampled look-ahead limiter
  at -2.2 dBTP) so ffmpeg loudnorm can run in LINEAR mode (no dynamic pumping); then a second
  loudnorm print pass verifies the file. Readings go in the JSON.
"""
import argparse, sys
sys.path.insert(0, '/tmp/claude-0/-home-user-UIUX/2e2fc1bb-c45d-5ce1-ba97-afbf7647f193/scratchpad/showcase/rnd-sound')
import json
import os
import re
import subprocess
import sys
import time
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S  # noqa: E402
from synth import SR, n_of, db, midi  # noqa: E402

DEFAULT_FFMPEG = '/tmp/claude-0/-home-user-UIUX/2e2fc1bb-c45d-5ce1-ba97-afbf7647f193/scratchpad/ffmpeg'
REF_BARS = 10.5
REF_CUES = {  # bars
    'impact_open': 0.0, 'groove': 2.0, 'riser_start': 4.0, 'drop': 5.0,
    'v8_burble': 6.5, 'impact_2': 7.0, 'tapestop': 8.0,
}
REF_WHOOSH = [1.0, 2.0, 3.0, 6.0, 7.5]
PROG = [  # (808 midi, pad voicing) per bar, cycles
    (29, [53, 56, 60, 65]),   # Fm
    (29, [53, 56, 60, 65]),   # Fm
    (25, [53, 56, 61, 65]),   # Db
    (27, [55, 58, 63, 67]),   # Eb
]


# ----------------------------------------------------------------- arrangement
def plan(duration, bpm, overrides):
    beat = 60.0 / bpm
    bar = 4 * beat
    total = duration / bar
    end_len = max(1.5, np.ceil((2.5 / bar) * 2) / 2)             # end card >= 2.5 s, half-bar snap
    endcard = np.floor((total - end_len) * 2) / 2
    cues = {}
    front = endcard - 1.0                                          # tapestop position
    k = front / REF_CUES['tapestop']
    for name, b in REF_CUES.items():
        cues[name] = np.round(b * k * 2) / 2
    cues['tapestop'] = front
    cues['v8_burble'] = cues['impact_2'] - 0.5
    cues.update({k2: float(v) for k2, v in overrides.items()})
    cues['drop_gap'] = cues['drop'] - 0.125
    cues['swell_start'] = cues['tapestop'] + 0.5
    cues['endcard'] = cues['tapestop'] + 1.0
    order = ['impact_open', 'groove', 'riser_start', 'drop', 'v8_burble', 'impact_2', 'tapestop', 'endcard']
    for a, b in zip(order, order[1:]):
        if cues[b] <= cues[a]:
            raise SystemExit(f'cue {b} ({cues[b]}) must come after {a} ({cues[a]}); '
                             f'track too short for this BPM? try --duration or --bpm')
    return beat, bar, total, cues


def build(duration=18.0, bpm=140, seed=11, overrides=None, whoosh_bars=None, engine=True):
    rng = np.random.default_rng(seed)
    beat, bar, total, cues = plan(duration, bpm, overrides or {})
    step = beat / 4
    T = lambda b: b * bar                                          # bars -> seconds
    N = n_of(duration)
    bus = {k: np.zeros((N + n_of(4), 2)) for k in ('drums', 'bass', 'music', 'fx', 'engine')}
    events = {'kick': [], 'clap': [], 'whoosh_peak': [], 'impact': []}
    ir_hall = S.reverb_ir(rng, t60=2.6, damp=0.3)
    ir_room = S.reverb_ir(rng, t60=0.9, damp=0.5, predelay=0.008)

    g, rs, dp, i2, ts, ec = (cues[k] for k in ('groove', 'riser_start', 'drop', 'impact_2', 'tapestop', 'endcard'))

    # --- one-shot kits (render once, reuse)
    K = S.kick(rng)
    C = S.reverb(S.clap(rng), ir_room, wet=0.35)
    HAT = [S.hat(rng, 0.045) for _ in range(4)]
    OH = S.hat(rng, open_=True)

    def section(b):
        if b < g: return 'intro'
        if b < rs: return 'groove'
        if b < dp: return 'riser'
        if b < ts: return 'drop'
        return 'end'

    # --- drums + 808, 16th-step sequencer
    total_steps = int(np.ceil(ec * 16))
    for s_i in range(total_steps):
        b = s_i / 16
        st = s_i % 16
        barno = int(b)
        sec = section(b)
        t = T(b)
        if sec in ('groove', 'drop'):
            kicks = [0, 10] if (barno % 2 == 0 or sec == 'groove') else [0, 7, 10]
            if st in kicks:
                S.place(bus['drums'], K, t, 1.15)
                events['kick'].append(t)
            if st == 8:
                S.place(bus['drums'], C, t, 1.4)
                events['clap'].append(t)
            # 808
            root = PROG[(barno - int(g)) % 4][0]
            if st == 0:
                S.place(bus['bass'], S.e808(rng, midi(root), 9 * step), t, 1.0)
            elif st == 10:
                S.place(bus['bass'], S.e808(rng, midi(root), 3 * step), t, 0.9)
            elif st == 13 and sec == 'drop':
                S.place(bus['bass'], S.e808(rng, midi(root), 3 * step, glide_from=midi(root + 12)), t, 0.9)
        if sec == 'riser' and st == 8 and b < cues['drop_gap']:
            S.place(bus['drums'], C, t, 0.55)
            events['clap'].append(t)
        # hats
        if sec in ('groove', 'drop', 'riser') or (sec == 'intro' and b >= 1.0):
            base = 2 if sec in ('intro', 'groove') else 1
            roll_zone = (st >= 12 and barno % 2 == 1 and sec in ('groove', 'drop'))
            if roll_zone:
                div = 3 if barno % 4 == 1 else 2               # 16th triplets or 32nds
                for r in range(div):
                    tt = t + r * step / div
                    if T(cues['drop_gap']) <= tt < T(dp):
                        continue
                    S.place(bus['drums'], HAT[r % 4], tt, 0.45 + 0.15 * r / div)
            elif st % base == 0 and not (T(cues['drop_gap']) <= t < T(dp)):
                v = 0.65 if st % 4 == 0 else 0.42
                if sec == 'intro':
                    v *= 0.55
                S.place(bus['drums'], HAT[st % 4], t, v)
            if sec == 'drop' and st == 6:
                S.place(bus['drums'], OH, t, 0.3)

    # --- pad (chord per bar), filter opens through the intro, closes in the riser
    for barno in range(int(np.ceil(ts))):
        sec = section(barno)
        chord = PROG[max(0, barno - int(g)) % 4][1] if sec != 'intro' else PROG[0][1]
        cutoff = {'intro': 500 + 700 * barno, 'groove': 1600, 'riser': 900, 'drop': 2400}[sec]
        p = S.pad(rng, chord, bar + 0.3, cutoff=cutoff)
        S.place(bus['music'], p, T(barno), 0.55 if sec != 'intro' else 0.45)
    # --- pluck arp (8ths over the bar's chord, up an octave); quiet in groove, forward in the drop
    ARP = [0, 1, 2, 3, 2, 1, 3, 2]
    for barno in range(int(g), int(np.ceil(ts))):
        sec = section(barno)
        if sec == 'riser':
            continue
        chord = PROG[(barno - int(g)) % 4][1]
        for k in range(8):
            m = chord[ARP[k]] + 12
            pl = S.pluck(rng, midi(m), 0.45, bright=1.3 if sec == 'drop' else 0.8)
            pl = S.pan(pl, 0.35 if k % 2 else -0.35)
            S.place(bus['music'], S.reverb(pl, ir_room, wet=0.25), T(barno) + k * 2 * step,
                    (0.22 if sec == 'drop' else 0.13) * (1.0 if k % 2 == 0 else 0.75))
    # hard cut of everything in the drop gap
    # (applied after mixing below)

    # --- cinematic hits
    for name, b, size, br in (('impact_open', cues['impact_open'], 0.8, False),
                              ('impact_1', dp, 1.0, True), ('impact_2', i2, 1.0, True)):
        S.place(bus['fx'], S.impact(rng, ir_hall, size=size), T(b), 1.9 if b > 0 else 1.4)
        if br:
            S.place(bus['fx'], S.braam(rng, midi(41 + (0 if name == 'impact_1' else 3)), 1.8), T(b), 0.4)
        events['impact'].append(T(b))
    # riser into the drop gap
    rz = S.riser(rng, T(cues['drop_gap']) - T(rs))
    S.place(bus['fx'], rz, T(rs), 2.2)
    # whooshes: peak lands on the given bar positions
    for wb in (whoosh_bars if whoosh_bars is not None else _scaled_whoosh(cues)):
        if wb >= ts:
            continue
        w = S.whoosh(rng, dur=0.7, peak=0.62, direction=1 if len(events['whoosh_peak']) % 2 == 0 else -1)
        S.place(bus['fx'], w, T(wb) - 0.7 * 0.62, 0.45)
        events['whoosh_peak'].append(T(wb))

    # --- engines
    if engine:
        e_end = T(g) + 0.35
        rpm, thr = S.rpm_sim(e_end, [(1.0 * beat, 1.3 * beat, 0.75), (2.0 * beat, 2.25 * beat, 0.9),
                                     (3.0 * beat, T(g) - 0.5 * beat, 1.0)], redline=9000)
        eng = S.engine(rng, rpm, thr, 'flat6')
        eng *= np.minimum(1, (e_end - S.tax(len(eng))) / 0.25)[:, None]
        S.place(bus['engine'], eng, 0.0, 0.95)
        v0 = T(cues['v8_burble'])
        vdur = T(i2) - v0 + bar * 0.9
        ib = T(i2) - v0
        rpm2, thr2 = S.rpm_sim(vdur, [(ib - 0.42, ib - 0.36, 0.8), (ib - 0.2, ib - 0.14, 0.85),
                                      (ib, vdur - 0.25, 1.0), ('shift', ib + bar * 0.55, 0.72)],
                               idle=1400, redline=9000, up=5.0, down=1.6, r0=7600)
        v8 = S.engine(rng, rpm2, thr2, 'flat6')  # HERO: single-car GT3 RS -> second engine pass is the flat-six, not the AMG V8
        v8 *= np.minimum(1, (vdur - S.tax(len(v8))) / 0.3)[:, None]
        S.place(bus['engine'], v8, v0, 0.75)

    # --- sidechain: duck music + engine under kicks
    duck = np.ones(len(bus['music']))
    dn = n_of(0.22)
    shape = 1 - 0.55 * np.exp(-np.arange(dn) / SR / 0.07)
    for kt in events['kick']:
        s0 = n_of(kt)
        duck[s0:s0 + dn] = np.minimum(duck[s0:s0 + dn], shape[:len(duck[s0:s0 + dn])])
    bus['music'] *= duck[:, None]
    bus['engine'] *= (0.5 + 0.5 * duck)[:, None]

    drums = S.saturate(bus['drums'] * 0.9, 1.4)
    stems = {'drums': drums * 0.9, 'bass': bus['bass'] * 0.36, 'music': bus['music'] * 2.6,
             'fx': bus['fx'] * 0.9, 'engine': bus['engine']}
    mix = sum(stems.values())

    # drop gap: hard mute (reverb tails too) for the 1/8 bar before the drop
    a, b_ = n_of(T(cues['drop_gap'])), n_of(T(dp))
    mix[a:b_] = 0
    mix[a - n_of(0.004):a] *= np.linspace(1, 0, n_of(0.004))[:, None]

    # --- tape stop over [tapestop, swell_start), then silence
    t0, t1 = n_of(T(ts)), n_of(T(cues['swell_start']))
    L = t1 - t0
    u = np.arange(L) / L
    rate = (1 - u) ** 1.3
    stopped = S.varispeed(mix[t0:t0 + L], rate)
    stopped = S.fft_filter(stopped, hi=9000)
    stopped *= np.minimum(1, (L - np.arange(L)) / n_of(0.02))[:, None]
    mix[t0:t1] = stopped
    mix[t1:] = 0

    # --- reverse swell into the end card, then the end card
    sw = S.reverse_swell(rng, ir_hall, T(ec) - T(cues['swell_start']))
    S.place(mix, sw, T(ec) - len(sw) / SR, 1.5)
    endbus = np.zeros_like(mix)
    S.place(endbus, S.impact(rng, ir_hall, size=1.3, dur=4.0), T(ec), 1.9)
    S.place(endbus, S.braam(rng, midi(41), 2.6), T(ec), 0.5)
    S.place(endbus, S.pad(rng, PROG[0][1], duration - T(ec) + 0.5, cutoff=1800), T(ec), 1.4)
    S.place(endbus, S.e808(rng, midi(29), min(1.6, duration - T(ec))), T(ec), 0.35)
    for i, m in enumerate([77, 80, 84, 89]):                     # F5 Ab5 C6 F6 logo sting
        bl = S.bell(rng, midi(m))
        bl = S.reverb(bl, ir_hall, wet=0.4)
        S.place(endbus, S.pan(bl.mean(1), [-0.4, -0.1, 0.2, 0.45][i]) * 1.2, T(ec) + (0.5 + i * 0.5) * beat, 0.3)
    events['impact'].append(T(ec))
    mix += endbus

    mix = mix[:N]
    fade = np.ones(N)
    fl = n_of(1.2)
    fade[-fl:] = np.linspace(1, 0, fl) ** 2
    mix *= fade[:, None]

    grid = _grid(duration, beat, bar)
    hits = {
        'impact_open': T(cues['impact_open']), 'engine_rev_peak': T(g) - 0.5 * beat,
        'groove': T(g), 'riser_start': T(rs), 'drop_gap': T(cues['drop_gap']),
        'drop': T(dp), 'impact_1': T(dp), 'price_1': T(dp),
        'v8_burble': T(cues['v8_burble']), 'impact_2': T(i2), 'price_2': T(i2),
        'tapestop_start': T(ts), 'tapestop_end': T(cues['swell_start']),
        'swell_start': T(cues['swell_start']), 'endcard': T(ec), 'impact_3': T(ec),
        'logo_sting': T(ec) + 0.5 * beat, 'end': duration,
    }
    sections = [
        {'name': 'intro', 'start': 0.0, 'end': T(g)},
        {'name': 'groove', 'start': T(g), 'end': T(rs)},
        {'name': 'riser', 'start': T(rs), 'end': T(dp)},
        {'name': 'drop', 'start': T(dp), 'end': T(ts)},
        {'name': 'tapestop', 'start': T(ts), 'end': T(cues['swell_start'])},
        {'name': 'swell', 'start': T(cues['swell_start']), 'end': T(ec)},
        {'name': 'endcard', 'start': T(ec), 'end': duration},
    ]
    cut_suggestions = sorted(set(round(x, 4) for x in (
        [T(cues['impact_open'])] + events['whoosh_peak'] + [T(dp), T(i2), T(ec)]
        + [T(b) for b in np.arange(dp, ts, 0.5)])))
    meta = {'cues_bars': {k: float(v) for k, v in cues.items()}, 'events': events,
            'grid': grid, 'hits': hits, 'sections': sections, 'cut_suggestions': cut_suggestions}
    return mix, meta, {k: v[:N] for k, v in stems.items()}


def _scaled_whoosh(cues):
    k = cues['tapestop'] / REF_CUES['tapestop']
    return [np.round(b * k * 2) / 2 for b in REF_WHOOSH]


def _grid(duration, beat, bar):
    beats = list(np.round(np.arange(0, duration - 1e-6, beat), 5))
    down = list(np.round(np.arange(0, duration - 1e-6, bar), 5))
    return {'beats': [float(x) for x in beats], 'downbeats': [float(x) for x in down]}


# ----------------------------------------------------------------- IO + mastering
def write_wav24(path, x):
    x = np.clip(x, -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    b = i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(path, 'wb') as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(b)


def read_audio(ff, path):
    """Decode any audio file to float32 stereo via ffmpeg (handles WAVE_FORMAT_EXTENSIBLE)."""
    r = subprocess.run([ff, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, '<f4').reshape(-1, 2).astype(np.float64)


def loudnorm_measure(ff, path, extra=''):
    af = f'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json{extra}'
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', path, '-af', af, '-f', 'null', '-'],
                       capture_output=True, text=True)
    js = re.findall(r'\{[^{}]+\}', r.stderr)
    return json.loads(js[-1])


def master(mix, ff, work, target=-14.0, pre_ceiling=-2.2):
    x = S.fft_filter(mix, lo=28, slope=3)
    x = S.saturate(0.9 * x / np.abs(x).max(), 1.1)       # level-independent gentle glue
    tmp = os.path.join(work, '_pre.wav')
    gain_db = 0.0
    for _ in range(4):
        y = S.limiter(x * db(gain_db), pre_ceiling)
        write_wav24(tmp, y)
        m = loudnorm_measure(ff, tmp)
        err = target - float(m['input_i'])
        if abs(err) < 0.25:
            break
        gain_db += err
    return y, tmp, m


def finalize(ff, pre, out_wav, m1):
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=20:measured_I={m1['input_i']}:measured_TP={m1['input_tp']}:"
          f"measured_LRA={m1['input_lra']}:measured_thresh={m1['input_thresh']}:offset={m1['target_offset']}:"
          f"linear=true:print_format=json")
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-y', '-i', pre, '-af', af, '-ar', str(SR),
                        '-c:a', 'pcm_s24le', out_wav], capture_output=True, text=True)
    pass2 = json.loads(re.findall(r'\{[^{}]+\}', r.stderr)[-1])
    verify = loudnorm_measure(ff, out_wav)
    return pass2, verify


def rms_per_second(x):
    out = []
    for s in range(0, len(x), SR):
        seg = x[s:s + SR]
        r = np.sqrt((seg ** 2).mean())
        out.append(round(float(20 * np.log10(max(r, 1e-9))), 1))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--duration', type=float, default=18.0)
    ap.add_argument('--bpm', type=float, default=140)
    ap.add_argument('--seed', type=int, default=11)
    ap.add_argument('--cue', action='append', default=[], help='name=bar, e.g. drop=5')
    ap.add_argument('--whoosh', default=None, help='comma list of bar positions for whoosh peaks')
    ap.add_argument('--no-engine', action='store_true')
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'bed'))
    ap.add_argument('--ffmpeg', default=DEFAULT_FFMPEG)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    ov = dict((k, float(v)) for k, v in (c.split('=') for c in a.cue))
    wb = [float(v) for v in a.whoosh.split(',')] if a.whoosh else None
    t0 = time.time()
    mix, meta, _stems = build(a.duration, a.bpm, a.seed, ov, wb, not a.no_engine)
    t_synth = time.time() - t0
    pre, pre_path, m1 = master(mix, a.ffmpeg, os.path.dirname(a.out) or '.')
    pass2, verify = finalize(a.ffmpeg, pre_path, a.out + '.wav', m1)
    os.remove(pre_path)
    final = read_audio(a.ffmpeg, a.out + '.wav')
    fr = lambda t, fps: int(round(t * fps))
    meta['hits'] = {k: {'sec': round(v, 4), 'f24': fr(v, 24), 'f23976': fr(v, 24000 / 1001)}
                    for k, v in meta['hits'].items()}
    meta.update({
        'file': os.path.basename(a.out) + '.wav', 'sample_rate': SR, 'duration': a.duration,
        'bpm': a.bpm, 'beat_sec': 60 / a.bpm, 'bar_sec': 240 / a.bpm, 'time_signature': '4/4', 'key': 'F minor',
        'regenerate': {'cmd': 'python3 bed.py', 'duration': a.duration, 'bpm': a.bpm, 'seed': a.seed,
                       'cue_overrides_bars': ov, 'whoosh_bars': wb, 'engine': not a.no_engine},
        'master': {'pre_measure': m1, 'loudnorm_pass': {k: pass2[k] for k in ('output_i', 'output_tp', 'normalization_type')},
                   'verify': {k: verify[k] for k in ('input_i', 'input_tp', 'input_lra')}},
        'rms_dbfs_per_second': rms_per_second(final),
        'render_sec': {'synth': round(t_synth, 1), 'total': round(time.time() - t0, 1)},
    })
    with open(a.out + '_sync.json', 'w') as f:
        json.dump(meta, f, indent=1, default=float)
    print(json.dumps({k: meta[k] for k in ('master', 'rms_dbfs_per_second', 'render_sec')}, indent=1))
    print(json.dumps({k: v['sec'] for k, v in meta['hits'].items()}))


if __name__ == '__main__':
    main()
