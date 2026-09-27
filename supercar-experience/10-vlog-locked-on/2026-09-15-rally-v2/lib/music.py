#!/usr/bin/env python3
"""
music.py -- the ORIGINAL placeholder music bed for the rally vlog v2 (dark, driving, F minor, 105.11 BPM).

The raw footage has no music and Omarie has not chosen a track yet, so this is a swappable placeholder:
the mixer (lib/mix.py) uses `audio/music.wav` when it exists (config.json `music`), and this synthesised
bed otherwise. Everything is generated with lib/synth.py (numpy only, fixed seeds): it is ours to use.

Tempo and grid are chosen from the cut, not the other way round:
  * the CH6 convoy montage (the DROP) starts at 135.77 s and the end card lands at 170.02 s; those are
    34.25 s = exactly 15 bars apart at 105.11 BPM, so both sit on a downbeat;
  * the first downbeat is at 1.0533 s (bar 0); t = 0 is a pickup hit under the hook panel.
Sections (seconds): OPEN 0-7 (full groove, riser + 1/16 gap into CH1) | VERSE 7-78.84 (half-time groove,
fills at chapter changes) | LIFT 78.84-87.54 (roll out: 16th hats, arp) | DINNER 87.54-116.61 (softer; the
dinner montage 94.25-101.75 has no kick so the room sound breathes) | BUILD 116.61-135.77 (pulse, opening
filter, snare roll + riser, 1/8-bar gap) | DROP 135.77-147.77 (everything, braam) | VERDICT 147.77-168.88
(breakdown under the guests, kick back for the last line) | TAPE STOP 168.88-169.45 (the music itself
varispeeds to a halt) | SWELL 169.45-170.02 | END CARD 170.02- (pad, 808, bell sting, fade to silence).

    python3 lib/music.py --out .work/music_synth.wav --sync .work/music_synth.json --dur 174.508
"""
import argparse
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import synth as S  # noqa: E402
from synth import SR, n_of, midi, db  # noqa: E402

DROP, END = 135.77, 170.02
BAR = (END - DROP) / 15.0            # 2.28333 s
BPM = 240.0 / BAR                    # 105.11
BEAT = BAR / 4
STEP = BEAT / 4
G0 = DROP - 59 * BAR                 # first downbeat (bar 0) = 1.0533 s
TS0 = END - 0.5 * BAR                # tape stop 168.878 -> 169.449
TS1 = END - 0.25 * BAR
GAP_OPEN = (7.0 - STEP, 7.0)         # 1/16 silence before CH1
GAP_DROP = (DROP - 0.5 * BEAT, DROP) # 1/8-bar silence before the drop

# i - VI - III - VII in F minor: (808 root midi, pad voicing)
PROG = [(29, [53, 56, 60, 65]),      # Fm
        (25, [53, 56, 61, 65]),      # Db
        (32, [51, 56, 60, 63]),      # Ab
        (27, [51, 55, 58, 63])]      # Eb


def T(b):
    return G0 + b * BAR


def section(t):
    if t < 7.0: return 'open'
    if t < 78.84: return 'verse'
    if t < 87.54: return 'lift'
    if t < 116.61: return 'dinner'
    if t < DROP: return 'build'
    if t < 147.77: return 'drop'
    if t < TS0: return 'verdict'
    return 'end'


def write_wav24(path, x):
    x = np.clip(x, -1, 1 - 2 ** -23)
    i = np.round(x * (2 ** 23 - 1)).astype('<i4')
    b = i.view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR); w.writeframes(b)


def build(dur, seed=23):
    rng = np.random.default_rng(seed)
    N = n_of(dur)
    pad_n = N + n_of(6)
    bus = {k: np.zeros((pad_n, 2)) for k in ('drums', 'bass', 'music', 'fx')}
    ir_hall = S.reverb_ir(rng, t60=2.6, damp=0.3)
    ir_room = S.reverb_ir(rng, t60=0.9, damp=0.5, predelay=0.008)
    K = S.kick(rng)
    Ksoft = S.kick(rng, punch=0.3) * 0.8
    C = S.reverb(S.clap(rng), ir_room, wet=0.35)
    SN = S.snare(rng, 0.2, tone=205)
    HAT = [S.hat(rng, 0.045) for _ in range(4)]
    OH = S.hat(rng, open_=True)
    ev = {'kick': [], 'clap': [], 'hits': []}

    def gapped(t):
        return GAP_OPEN[0] <= t < GAP_OPEN[1] or GAP_DROP[0] <= t < GAP_DROP[1] or t >= TS0

    # ---------------------------------------------------------------- drums + 808 (16th sequencer)
    s_first = int(np.floor((0 - G0) / STEP))
    s_last = int(np.ceil((TS1 - G0) / STEP))
    for si in range(s_first, s_last):
        t = G0 + si * STEP
        if t < -1e-9 or gapped(t):
            continue
        st = si % 16
        barno = si // 16
        sec = section(t)
        chord_i = barno % 4
        root = PROG[chord_i][0]
        # --- kick / clap patterns per section
        kicks, clapstep, hatdiv, hatv = [], None, 0, 0.0
        if sec == 'open':
            kicks = [0, 7, 10] if barno % 2 else [0, 10]; clapstep = 8; hatdiv = 1; hatv = 0.55
        elif sec == 'verse':
            kicks = [0, 10]; clapstep = 8; hatdiv = 2; hatv = 0.42
        elif sec == 'lift':
            kicks = [0, 7, 10]; clapstep = 8; hatdiv = 1; hatv = 0.5
        elif sec == 'dinner':
            montage = 94.25 <= t < 101.75
            kicks = [] if montage else [0]
            clapstep = None if montage else 8
            hatdiv = 4 if montage else 2; hatv = 0.3
        elif sec == 'build':
            # pulse: soft kick on every beat in the last 4 bars, snare roll in the last 2
            to_drop = DROP - t
            kicks = [0, 4, 8, 12] if to_drop < 4 * BAR else [0]
            hatdiv = 2 if to_drop < 6 * BAR else 4; hatv = 0.28 + 0.25 * max(0, 1 - to_drop / (8 * BAR))
            if to_drop < 2 * BAR:
                div = 2 if to_drop > BAR else 1          # 8ths -> 16ths
                if st % div == 0:
                    S.place(bus['drums'], SN, t, 0.25 + 0.55 * (1 - to_drop / (2 * BAR)) ** 1.5)
        elif sec == 'drop':
            kicks = [0, 7, 10] if barno % 2 else [0, 3, 10]; clapstep = 8; hatdiv = 1; hatv = 0.58
        elif sec == 'verdict':
            late = t >= 161.52
            kicks = ([0, 10] if t >= 166.52 else [0]) if late else []
            clapstep = 8 if t >= 166.52 else None
            hatdiv = 2 if late else 4; hatv = 0.26
        if st in kicks:
            S.place(bus['drums'], K if sec not in ('build', 'verdict') else Ksoft, t, 1.1)
            ev['kick'].append(t)
        if clapstep is not None and st == clapstep:
            S.place(bus['drums'], C, t, 1.25 if sec in ('drop', 'open') else 1.0)
            ev['clap'].append(t)
        if hatdiv and st % hatdiv == 0:
            roll = sec in ('drop', 'open', 'lift') and st >= 12 and barno % 2 == 1
            if roll:
                for r in range(2):
                    S.place(bus['drums'], HAT[r], t + r * STEP / 2, hatv * (0.8 + 0.2 * r))
            else:
                S.place(bus['drums'], HAT[st % 4], t, hatv * (1.0 if st % 4 == 0 else 0.7))
        if sec in ('drop', 'lift') and st == 6:
            S.place(bus['drums'], OH, t, 0.28)
        # --- 808
        if sec in ('open', 'verse', 'lift', 'drop') or (sec == 'dinner' and not (94.25 <= t < 101.75)) or \
                (sec == 'verdict' and t >= 161.52):
            if st == 0:
                S.place(bus['bass'], S.e808(rng, midi(root), 9 * STEP), t, 1.0)
            elif st == 10:
                S.place(bus['bass'], S.e808(rng, midi(root), 3 * STEP), t, 0.85)
            elif st == 13 and sec == 'drop':
                S.place(bus['bass'], S.e808(rng, midi(root), 3 * STEP, glide_from=midi(root + 12)), t, 0.85)
        elif sec == 'build' and st % 2 == 0:
            # driving 8th-note sub pulse, filter opening towards the drop
            S.place(bus['bass'], S.e808(rng, midi(29), 1.8 * STEP, drive=2.0), t, 0.45 + 0.35 * max(0, 1 - (DROP - t) / (8 * BAR)))
    # pickup hit at t = 0 (under the hook panel)
    S.place(bus['drums'], K, 0.0, 1.2); ev['kick'].append(0.0)
    S.place(bus['bass'], S.e808(rng, midi(29), 1.0, glide_from=midi(41)), 0.0, 1.0)

    # ---------------------------------------------------------------- pad (one chord per bar)
    b0, b1 = int(np.floor((0 - G0) / BAR)), int(np.ceil((TS1 - G0) / BAR))
    for barno in range(b0, b1):
        t = T(barno)
        tm = max(0.0, t)
        sec = section(tm + 0.01)
        chord = PROG[barno % 4][1]
        cutoff = {'open': 1500, 'verse': 1100, 'lift': 1700, 'dinner': 900, 'build': 700 + 1900 * max(0, 1 - (DROP - t) / (8 * BAR)),
                  'drop': 2600, 'verdict': 1000, 'end': 1000}[sec]
        gain = {'open': 0.5, 'verse': 0.42, 'lift': 0.48, 'dinner': 0.45, 'build': 0.5, 'drop': 0.55, 'verdict': 0.5, 'end': 0.5}[sec]
        p = S.pad(rng, chord, BAR + 0.35, cutoff=cutoff)
        if t < 0:
            p = p[n_of(-t):]
        S.place(bus['music'], p, tm, gain)
    # ---------------------------------------------------------------- pluck arp (8ths) in open / lift / drop / late verdict
    ARP = [0, 1, 2, 3, 2, 1, 3, 2]
    for barno in range(b0, b1):
        for k in range(8):
            t = T(barno) + k * 2 * STEP
            if t < 0 or gapped(t):
                continue
            sec = section(t)
            if sec not in ('open', 'lift', 'drop', 'verdict', 'verse'):
                continue
            if sec == 'verse' and not (54.09 <= t < 78.84):
                continue
            if sec == 'verdict' and k % 2:
                continue
            m = PROG[barno % 4][1][ARP[k]] + 12
            pl = S.pluck(rng, midi(m), 0.45, bright=1.3 if sec == 'drop' else 0.8)
            pl = S.pan(pl, 0.35 if k % 2 else -0.35)
            lvl = {'open': 0.16, 'lift': 0.16, 'drop': 0.22, 'verdict': 0.13, 'verse': 0.09}[sec]
            S.place(bus['music'], S.reverb(pl, ir_room, wet=0.25), t, lvl * (1.0 if k % 2 == 0 else 0.75))

    # ---------------------------------------------------------------- fx inside the music (musical ones only)
    S.place(bus['fx'], S.riser(rng, 7.0 - STEP - 5.9), 5.9, 0.9)                       # into CH1
    S.place(bus['fx'], S.riser(rng, GAP_DROP[0] - (DROP - 4 * BAR)), DROP - 4 * BAR, 1.6)  # into the drop
    S.place(bus['fx'], S.braam(rng, midi(41), 2.2), DROP, 0.42)
    S.place(bus['fx'], S.impact(rng, ir_hall, size=0.9), DROP, 1.3); ev['hits'].append(DROP)
    for tc in (25.88, 54.09, 78.84, 87.54, 116.61, 147.77):                               # chapter swells
        sw = S.reverse_swell(rng, ir_hall, 0.9)
        S.place(bus['fx'], sw, tc - len(sw) / SR, 0.55)

    stems = {'drums': S.saturate(bus['drums'] * 0.9, 1.4) * 0.9, 'bass': bus['bass'] * 0.34,
             'music': bus['music'] * 2.5, 'fx': bus['fx'] * 0.8}
    # sidechain: music + bass breathe under the kick
    duck = np.ones(pad_n)
    dn = n_of(0.2)
    shape = 1 - 0.5 * np.exp(-np.arange(dn) / SR / 0.07)
    for kt in ev['kick']:
        s0 = n_of(kt)
        e = min(pad_n, s0 + dn)
        duck[s0:e] = np.minimum(duck[s0:e], shape[:e - s0])
    stems['music'] *= duck[:, None]
    stems['bass'] *= (0.4 + 0.6 * duck)[:, None]
    mix = sum(stems.values())
    # hard gaps (tails included)
    for a, b in (GAP_OPEN, GAP_DROP):
        ia, ib = n_of(a), n_of(b)
        mix[ia - n_of(0.004):ia] *= np.linspace(1, 0, n_of(0.004))[:, None]
        mix[ia:ib] = 0

    # ---------------------------------------------------------------- tape stop (the music itself), swell, end card
    t0, t1 = n_of(TS0), n_of(TS1)
    L = t1 - t0
    u = np.arange(L) / L
    stopped = S.varispeed(mix[t0:t0 + L], (1 - u) ** 1.3)
    stopped = S.fft_filter(stopped, hi=9000)
    stopped *= np.minimum(1, (L - np.arange(L)) / n_of(0.02))[:, None]
    mix[t0:t1] = stopped
    mix[t1:] = 0
    sw = S.reverse_swell(rng, ir_hall, END - TS1)
    S.place(mix, sw, END - len(sw) / SR, 1.3)
    endbus = np.zeros_like(mix)
    tail = dur - END
    S.place(endbus, S.pad(rng, PROG[0][1], tail + 0.4, cutoff=1600), END, 1.3)
    S.place(endbus, S.e808(rng, midi(29), min(1.8, tail)), END, 0.4)
    S.place(endbus, S.braam(rng, midi(41), 2.4), END, 0.35)
    for i, m in enumerate([77, 80, 84, 89]):                     # F5 Ab5 C6 F6 sting
        bl = S.reverb(S.bell(rng, midi(m)), ir_hall, wet=0.4)
        S.place(endbus, S.pan(bl.mean(1), [-0.4, -0.1, 0.2, 0.45][i]) * 1.1, END + (0.5 + i * 0.5) * BEAT, 0.26)
    mix += endbus
    mix = mix[:N]
    # fade to digital silence: 1.1 s fade ending 60 ms before the end
    fe = N - n_of(0.06)
    fl = n_of(1.1)
    g = np.ones(N)
    g[fe - fl:fe] = np.linspace(1, 0, fl) ** 2
    g[fe:] = 0
    mix *= g[:, None]
    mix -= mix.mean(0) * 0            # (no DC offset is generated; kept explicit)
    sync = {'bpm': round(BPM, 4), 'bar_s': round(BAR, 5), 'downbeat0': round(G0, 5),
            'downbeats': [round(T(b), 4) for b in range(0, int((dur - G0) / BAR) + 1)],
            'drop': DROP, 'tapestop': [round(TS0, 4), round(TS1, 4)], 'endcard': END,
            'gaps': [list(map(lambda v: round(v, 4), GAP_OPEN)), list(map(lambda v: round(v, 4), GAP_DROP))],
            'hits': ev['hits']}
    return mix, sync


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--sync', required=True)
    ap.add_argument('--dur', type=float, required=True)
    A = ap.parse_args()
    mix, sync = build(A.dur)
    pk = np.abs(mix).max()
    mix = mix / pk * db(-3)                   # headroom; the mixer sets the level
    write_wav24(A.out, mix)
    json.dump(sync, open(A.sync, 'w'), indent=1)
    print('music', A.out, f'{len(mix) / SR:.3f}s', 'bpm', sync['bpm'], 'downbeat0', sync['downbeat0'])


if __name__ == '__main__':
    main()
