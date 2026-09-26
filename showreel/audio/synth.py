#!/usr/bin/env python3
"""Procedural soundtrack engine for the showreel. numpy + stdlib only, fully deterministic.

    python3 audio/synth.py [--cues audio/cues.json] [--out dist/soundtrack.wav] [--stems]

Renders a 48 kHz / 24-bit / stereo WAV of exactly DURATION seconds (720000 frames): 128 BPM, 4/4, F minor.

  1. ARRANGEMENT  data only: grid, chords, per-bar step patterns, FX list, mix table   <- edit this part
  2. DSP core     polyBLEP oscillators, envelopes, TPT state-variable filter, FFT-applied biquads,
                  synthesized-IR convolution reverb, tempo-synced ping-pong delay, dynamics, loudness
  3. Sounds       drum / bass / synth voices and the R.sfx vocabulary
  4. Sequencer    patterns -> parts -> buses, sidechain, music-bus edits (gate, stutter, glitch, tapestop)
  5. Master + IO  glue compressor, oversampled soft clipper, true-peak limiter, LUFS targeting, WAV, report

Picture sync: tools/cues.mjs exports scene windows, R.cue FX cues and R.sfx sound events to audio/cues.json.
Every R.sfx event is rendered on the SFX bus at its exact sample. FX cues add optional reinforcement layers
(FX_CUE_SOUNDS) unless a sound event lands within DEDUPE_WINDOW. Scene cuts get an optional sweetener
(SCENE_SWEETENER). Arrangement FX yield to picture events of the same type nearby (YIELD_WINDOW), so once
the picture declares its own hits the built-in ones step aside instead of doubling up.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import zlib

import numpy as np

# =====================================================================================================
# 1. ARRANGEMENT: everything musical lives in this section. Re-map it to the storyboard by editing data.
# =====================================================================================================
BPM = 128
BARS = 8
DURATION = 15.0                 # seconds; the file is always exactly DURATION * SR frames
KEY = 'F minor'
SEED = 1280                     # every random choice derives from this (same input -> bit-identical output)
TARGET_LUFS = -14.0             # integrated loudness target (EBU R128 / BS.1770-4)
CEILING_DBTP = -1.0             # true-peak ceiling

BEAT = 60.0 / BPM               # 0.46875 s
BAR = 4.0 * BEAT                # 1.875 s   bar n (1-based) starts at (n - 1) * BAR
S16 = BEAT / 4.0                # 0.1171875 s
SWING = 0.08                    # fraction of a 16th that the off-16ths ("e" and "a") are pushed late
SWING_PARTS = ('hat', 'shaker', 'rim', 'tick')

# Step patterns ----------------------------------------------------------------------------------------
# One string per part per bar. Its length sets the step size: 16 = 16ths, 8 = 8ths, 32 = 32nds,
# 12 = 8th-note triplets, 4 = quarters. Spaces and '|' are ignored (use them to group beats).
#   .  rest        x  hit (0.85)     X  accent (1.0)     o  soft (0.55)     g  ghost (0.3)
#   1-9  velocity 0.2 .. 1.0         _  tie: the previous note holds one more step (tonal parts)
#   tom: h m l = high / mid / low (uppercase = accent)
# Tonal parts (sub, bass, stab, saw, pad) play the chord of the moment. '<part>_notes' overrides the
# pitches with note names cycled over that bar's hits, e.g. bass_notes='F2 F2 Ab2 C3'.
#
# Per-bar keys
#   section     label (report only)           energy  0..1 macro: drum velocity, reverb amount
#   chords      'Fm9', or evenly spaced changes 'Fm9 . Dbmaj7 .' ('.' holds the previous chord)
#   <part>      step pattern for a part in PARTS
#   <part>_cut  (start, end) filter brightness 0..1 swept across the bar (0.5 = 1.2 kHz, 1.0 = 12 kHz)
#   gate        step pattern gating the tonal bus (sub/bass/synths + their reverb/delay): x open, . shut
#   stutter     per-step edits of the whole music bus: 2 3 4 6 8 = retrigger the step's head N times,
#               r = reverse, b = replay the first step of the beat, x = mute, d = bitcrush, t = tape-slow
#   level       music-bus level in dB for this bar (number, or (start, end) for a ramp); default 0
#   hp / lp     (start_hz, end_hz) highpass / lowpass sweep on the tonal bus across the bar
#   mute        list of parts silenced in this bar           snare_rise  semitones a roll climbs over the bar
PARTS = ('kick', 'clap', 'snare', 'tom', 'hat', 'ohat', 'shaker', 'rim', 'tick',
         'sub', 'bass', 'stab', 'saw', 'pad')
DRUM_PARTS = PARTS[:9]

FOUR = 'x...x...x...x...'
CLAP = '....x.......x...'
OFFH = '..x...x...x...x.'

SONG = [
    dict(  # bar 1 · 0.000 s · HOOK: filtered stab motif, sparse ticks, sub impact on the 1, reverse into 2
        section='hook', energy=0.3, chords='Fm9',
        stab='x..x ..x. ..x. .x..', stab_cut=(0.30, 0.40),
        tick='..x. .... x... .x..',
    ),
    dict(  # bar 2 · 1.875 s · GROOVE IN: four-on-the-floor, ducked sub, offbeat hats, clap on 2 & 4
        section='groove', energy=0.55, chords='Fm9 . Dbmaj7 .', level=-2.5,
        kick=FOUR, clap=CLAP, ohat=OFFH,
        sub='5_______ 5_______',
        stab='x..x ..x. ..x. .x..', stab_cut=(0.40, 0.50),
        tick='..x. .... x... .x..',
    ),
    dict(  # bar 3 · 3.750 s · GROOVE: 16th hats, shaker and rim join, the stab keeps opening
        section='groove', energy=0.65, chords='Abmaj7 . Eb .', level=-2.0,
        kick=FOUR, clap=CLAP, ohat=OFFH,
        hat='.o.o .o.o .o.o .o.o', shaker='4242 4242 4242 4252', rim='.... ..x. .... ..x.',
        sub='6_______ 6_______',
        stab='x..x ..x. ..x. .x..', stab_cut=(0.50, 0.60),
    ),
    dict(  # bar 4 · 5.625 s · BUILD: stab variation, toms + snare fill over beats 3-4, riser into the drop
        section='build', energy=0.75, chords='Dbmaj7 . Csus4 C', level=(-2.0, -0.5), hp=(20, 380),
        kick='x...x...x.......', clap='....x...........', ohat='..x...x.........',
        hat='.o.o .o.o .... ....', shaker='4242 4242 4252 5262',
        tom='.... .... hhml ....',
        snare='........ ........ ........ 6789XXXX',
        sub='6_______ 6___....',
        stab='x..x ..x. x.x. x...', stab_cut=(0.60, 0.74),
        gate='xxxx xxxx xxxx xxx.',
    ),
    dict(  # bar 5 · 7.500 s · DROP: impact, rolling bass, supersaw stabs, 16th hats, extra percussion
        section='drop', energy=1.0, chords='Fm9',
        kick=FOUR, clap=CLAP, ohat=OFFH,
        hat='ox.x ox.x ox.x ox.x', shaker='x5x5 x5x5 x5x5 x5x5', rim='..x. .x.. ..x. .x..',
        sub='x_______ x_______',
        bass='..x. ..xx ..x. ..xx', bass_notes='F2 F2 Ab2 F2 F2 C3',
        saw='x..x ..x. ..x. .x..', saw_cut=(0.74, 0.80),
        stab='x..x ..x. ..x. .x..', stab_cut=(0.80, 0.80),
    ),
    dict(  # bar 6 · 9.375 s · DROP 2: same energy, harmony moves, clap pickup into the climax
        section='drop', energy=1.0, chords='Dbmaj7 . Eb .',
        kick=FOUR, clap='....x.......x.xx', ohat=OFFH,
        hat='ox.x ox.x ox.x ox.x', shaker='x5x5 x5x5 x5x5 x5x5', rim='..x. .x.. ..x. .x..',
        sub='x_______ x_______',
        bass='..x. ..xx ..x. ..xx', bass_notes='Db2 Db2 F2 Eb2 Eb2 G2',
        saw='x..x ..x. ..x. .x..', saw_cut=(0.78, 0.84),
        stab='x..x ..x. ..x. .x..', stab_cut=(0.80, 0.84),
    ),
    dict(  # bar 7 · 11.250 s · CLIMAX: an edit on every beat, gated synths, bigger riser, snare roll into 8
        section='climax', energy=1.0, chords='Fm9 . Eb .',
        kick=FOUR, clap=CLAP, ohat=OFFH,
        hat='ox.x ox.x ox.x ox.x', shaker='x5x5 x5x5 x5x5 x5x5',
        sub='x_______ x_______',
        bass='.xxx .xxx .xxx .xxx', bass_notes='F2 F2 F3 F2 F2 F3 Eb2 Eb2 Eb3 Eb2 Eb2 Eb3',
        saw='x_______ x_______', saw_cut=(0.72, 0.90),
        stab='x..x ..x. ..x. .x..', stab_cut=(0.82, 0.90),
        snare='3...3...4...4... 5.5.6.6. 789XXXXX', snare_rise=5,
        gate='xx.x x.xx .xx. xx.x',
        stutter='...4 ..b. ..2r ..88',
    ),
    dict(  # bar 8 · 13.125 s · RESOLVE: huge impact + sub drop, everything cuts to a sustained Fm9 pad
        section='resolve', energy=0.2, chords='Fm9',
        pad='x_______________',
        stab='x...............', stab_cut=(0.52, 0.52),
    ),
]

# Arrangement FX: same vocabulary and options as R.sfx. Position: 'bar.beat.16th' (1-based bar and beat,
# 0-based 16th) or seconds. anchor='end' makes the position the landing / peak point (riser, reverse,
# whoosh) instead of the start. Each one steps aside if the picture declares the same type within
# YIELD_WINDOW of its anchor (set 'keep': True to always play it).
FX = [
    ('1.1.0', 'impact', dict(amt=0.75, tone='sub')),
    ('2.1.0', 'reverse', dict(dur=2 * BEAT, anchor='end', amt=0.9)),
    ('5.1.0', 'riser', dict(dur=BAR, anchor='end')),
    ('5.1.0', 'impact', dict(amt=1.0)),
    ('8.1.0', 'riser', dict(dur=BAR, anchor='end', amt=1.25)),
    ('8.1.0', 'impact', dict(amt=1.35, tone='huge')),
    ('8.1.0', 'subdrop', dict(amt=1.0)),
    ('8.1.0', 'shimmer', dict(dur=1.6, amt=0.55)),
]

# Mix table. gain in dB; pan -1..1; room/hall/delay = send levels (linear); duck = sidechain depth in dB
# (keyed to the kick part). Parts are normalized one-shots, so gains are the whole level story.
MIX = {
    'kick':   dict(gain=0.0),
    'clap':   dict(gain=-8.5, room=0.30, hall=0.05),
    'snare':  dict(gain=-11.0, room=0.30, hall=0.08),
    'tom':    dict(gain=-9.0, room=0.25, hall=0.05),
    'hat':    dict(gain=-19.0, pan=0.18, room=0.06),
    'ohat':   dict(gain=-17.5, pan=0.18, room=0.08, duck=2.0),
    'shaker': dict(gain=-23.0, pan=-0.30, room=0.10),
    'rim':    dict(gain=-19.0, pan=-0.22, room=0.12, delay=0.20),
    'tick':   dict(gain=-17.0, pan=0.25, room=0.10, delay=0.35),
    'sub':    dict(gain=-11.0, duck=15.0),
    'bass':   dict(gain=-10.0, duck=7.0),
    'stab':   dict(gain=-12.5, hall=0.22, delay=0.24, duck=3.0),
    'saw':    dict(gain=-15.0, hall=0.20, delay=0.10, duck=4.5),
    'pad':    dict(gain=-9.0, hall=0.38),
}
RETURNS = dict(room=-6.0, hall=-7.0, delay=-10.0, fxverb=-7.0)   # return levels, dB
RETURN_DUCK = 3.0               # sidechain depth (dB) on the hall/delay returns: the space pumps too
MUTE = []                       # parts or buses to silence, e.g. ['saw', 'sfx']  (buses: drums tonal sfx)
SOLO = []                       # if not empty only these parts / buses play

# Picture-driven sound design (R.sfx vocabulary + internal reinforcement sounds). gain dB, verb = send to
# the FX reverb, duck = dB the music dips under the hit.
SFX_MIX = {
    'impact':   dict(gain=-2.0, verb=0.22, duck=3.0),
    'whoosh':   dict(gain=-8.0, verb=0.18),
    'swish':    dict(gain=-10.0, verb=0.12),
    'click':    dict(gain=-15.0, verb=0.06),
    'tick':     dict(gain=-16.0, verb=0.06),
    'pop':      dict(gain=-14.0, verb=0.08),
    'blip':     dict(gain=-17.0, verb=0.15),
    'glitch':   dict(gain=-11.0, verb=0.04),
    'riser':    dict(gain=-9.0, verb=0.22),
    'reverse':  dict(gain=-8.0, verb=0.10),
    'subdrop':  dict(gain=-4.0, duck=2.0),
    'shimmer':  dict(gain=-15.0, verb=0.55),
    'type':     dict(gain=-15.0, verb=0.05),
    'tapestop': dict(gain=0.0),
    'air':      dict(gain=-21.0, verb=0.35),
    'thump':    dict(gain=-9.0),
    'zap':      dict(gain=-22.0, verb=0.05),
}
# R.cue reinforcement. min_amt uses the cue's own units (flash 0..1, shake px, chroma px).
FX_CUE_SOUNDS = {
    'flash':  dict(sound='air', min_amt=0.8),
    'shake':  dict(sound='thump', min_amt=6.0),
    'chroma': dict(sound='zap', min_amt=8.0),
    'invert': dict(sound='zap', min_amt=0.0),
}
CUE_AMT_DEFAULT = dict(flash=1.0, shake=12.0, chroma=8.0, invert=1.0)   # engine.js defaults
SCENE_SWEETENER = dict(enabled=True, type='swish', amt=0.4, guard=0.25)   # on every scene cut after 0
DEDUPE_WINDOW = 0.030           # an R.cue reinforcement is dropped if any sound event is this close
YIELD_WINDOW = 0.12             # arrangement FX yield to a same-type picture event this close
END_FADE = 0.12                 # final fade to digital silence

# =====================================================================================================
# 2. DSP CORE
# =====================================================================================================
SR = 48000
N_FRAMES = int(round(DURATION * SR))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 2.0 * math.pi
LN1000 = math.log(1000.0)       # exp(-LN1000 * t / rt60) reaches -60 dB at t = rt60
SFX_TYPES = ('impact', 'whoosh', 'swish', 'click', 'tick', 'pop', 'blip', 'glitch', 'riser', 'reverse',
             'subdrop', 'shimmer', 'type', 'tapestop')
INTERNAL_SFX = ('air', 'thump', 'zap')
WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print('warning: ' + msg, file=sys.stderr)


def undb(d):
    return 10.0 ** (d / 20.0)


def todb(x):
    return 20.0 * math.log10(max(float(x), 1e-12))


def hz(midi):
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


def smp(t):
    return int(math.floor(t * SR + 0.5))


def tvec(n):
    return np.arange(n) / SR


def rng_for(*keys):
    """Deterministic generator per (keys, SEED). Never uses hash(), which is salted per process."""
    s = '|'.join(repr(k) if isinstance(k, float) else str(k) for k in keys)
    return np.random.default_rng([SEED, zlib.crc32(s.encode('utf-8'))])


def fft_len(n):
    """Smallest 2^a 3^b 5^c >= n (fast pocketfft sizes)."""
    n = max(int(n), 1)
    best = 1 << (n - 1).bit_length()
    p5 = 1
    while p5 < best:
        p35 = p5
        while p35 < best:
            p = p35
            while p < n:
                p *= 2
            best = min(best, p)
            p35 *= 3
        p5 *= 5
    return best


# ---- biquads (RBJ cookbook), applied exactly through one zero-padded FFT ------------------------------
def biquad(kind, f0, q=0.7071, gain_db=0.0):
    f0 = min(max(float(f0), 1.0), 0.49 * SR)
    w0 = TAU * f0 / SR
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    A = 10.0 ** (gain_db / 40.0)
    if kind == 'lp':
        b, a = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2], [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'hp':
        b, a = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2], [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'bp':        # 0 dB peak
        b, a = [alpha, 0.0, -alpha], [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'notch':
        b, a = [1.0, -2 * cw, 1.0], [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'peak':
        b, a = [1 + alpha * A, -2 * cw, 1 - alpha * A], [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind in ('lowshelf', 'highshelf'):
        sq = 2.0 * math.sqrt(A) * alpha
        if kind == 'lowshelf':
            b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sq)]
            a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sq]
        else:
            b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sq)]
            a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sq]
    elif kind in ('lp1', 'hp1'):  # one-pole (bilinear)
        k = math.tan(w0 / 2.0)
        if kind == 'lp1':
            b, a = [k / (1 + k), k / (1 + k), 0.0], [1.0, (k - 1) / (k + 1), 0.0]
        else:
            b, a = [1 / (1 + k), -1 / (1 + k), 0.0], [1.0, (k - 1) / (k + 1), 0.0]
    else:
        raise ValueError('unknown biquad ' + kind)
    return np.array(b) / a[0], np.array(a) / a[0]


def onepole_ba(tau):
    """Exponential smoother y += (x - y) / (tau * SR), as (b, a)."""
    p = math.exp(-1.0 / max(tau * SR, 1e-9))
    return np.array([1.0 - p]), np.array([1.0, -p])


def _response(sections, L):
    w = np.exp(-1j * TAU * np.arange(L // 2 + 1) / L)
    H = np.ones(L // 2 + 1, complex)
    for b, a in sections:
        H *= np.polyval(np.asarray(b)[::-1], w) / np.polyval(np.asarray(a)[::-1], w)
    return H


def _tail(sections, cap=4 * SR):
    r = 0.0
    for _, a in sections:
        a = np.trim_zeros(np.asarray(a, float), 'b')
        if len(a) > 1:
            r = max(r, float(np.max(np.abs(np.roots(a)))))
    if r <= 1e-9:
        return 64
    if r >= 1.0:
        return cap
    return int(min(cap, max(64, math.log(1e-10) / math.log(r))))


def iir(x, sections, tail=None):
    """Causal IIR sections [(b, a), ...] along the last axis. Exact for LTI filters: one FFT, padded past
    the impulse-response decay so nothing wraps around."""
    x = np.asarray(x, float)
    n = x.shape[-1]
    if n == 0:
        return x.copy()
    L = fft_len(n + (_tail(sections) if tail is None else tail))
    return np.fft.irfft(np.fft.rfft(x, L) * _response(sections, L), L)[..., :n]


def filt(x, *stages):
    """Cascade of RBJ biquads in one FFT pass: filt(x, ('hp', 30), ('peak', 2500, 1.0, 3.0))."""
    return iir(x, [biquad(*s) for s in stages])


def zerophase(x, gain_fn):
    """Zero-phase magnitude filter: multiply the spectrum by gain_fn(freqs_hz). Used for M/S crossovers."""
    n = x.shape[-1]
    L = fft_len(n + SR // 2)
    f = np.fft.rfftfreq(L, 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x, L) * gain_fn(f), L)[..., :n]


# ---- TPT state-variable filter (Zavalishin / Cytomic), per-sample cutoff & Q modulation --------------
def _svf_loop(xs, a1s, a2s, a3s):
    ic1 = ic2 = 0.0
    n = len(xs)
    o1 = [0.0] * n
    o2 = [0.0] * n
    i = 0
    for x0, a1, a2, a3 in zip(xs, a1s, a2s, a3s):
        v3 = x0 - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = v1 + v1 - ic1
        ic2 = v2 + v2 - ic2
        o1[i] = v1
        o2[i] = v2
        i += 1
    return o1, o2


def svf(x, fc, q=0.7071, mode='lp'):
    """Trapezoidal (zero-delay-feedback) SVF. fc / q: scalars or per-sample arrays. mode: lp hp bp
    (0 dB peak) notch. Stable under any modulation. Works on (n,) or (channels, n)."""
    x = np.asarray(x, float)
    if x.ndim > 1:
        return np.stack([svf(ch, fc, q, mode) for ch in x])
    n = x.shape[0]
    fcv = np.clip(np.broadcast_to(np.asarray(fc, float), (n,)), 8.0, 0.45 * SR)
    g = np.tan(np.pi * fcv / SR)
    k = 1.0 / np.broadcast_to(np.asarray(q, float), (n,))
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    o1, o2 = _svf_loop(x.tolist(), a1.tolist(), a2.tolist(), a3.tolist())
    bp, lp = np.array(o1), np.array(o2)
    if mode == 'lp':
        return lp
    if mode == 'bp':
        return k * bp
    if mode == 'hp':
        return x - k * bp - lp
    if mode == 'notch':
        return x - k * bp
    raise ValueError('svf mode ' + mode)


# ---- oscillators (band-limited, vectorized) ----------------------------------------------------------
def _phase(freq, n, phase0=0.0):
    inc = np.broadcast_to(np.asarray(freq, float) / SR, (n,))
    return (phase0 + np.cumsum(inc) - inc) % 1.0, inc


def _blep(ph, dt):
    out = np.zeros(ph.shape)
    m = ph < dt
    x = ph[m] / dt[m]
    out[m] = x + x - x * x - 1.0
    m = ph > 1.0 - dt
    x = (ph[m] - 1.0) / dt[m]
    out[m] = x * x + x + x + 1.0
    return out


def saw(freq, n, phase0=0.0):
    """polyBLEP sawtooth; freq may be a per-sample array (glides)."""
    ph, dt = _phase(freq, n, phase0)
    return 2.0 * ph - 1.0 - _blep(ph, dt)


def square(freq, n, phase0=0.0):
    ph, dt = _phase(freq, n, phase0)
    return np.where(ph < 0.5, 1.0, -1.0) + _blep(ph, dt) - _blep((ph + 0.5) % 1.0, dt)


def sine(freq, n=None, phase0=0.0):
    """Sine from a frequency (scalar or per-sample array). Starts exactly at phase0 (0 -> sample 0 is 0)."""
    f = np.asarray(freq, float)
    if f.ndim == 0:
        return np.sin(TAU * (f * tvec(n) + phase0))
    return np.sin(TAU * ((np.cumsum(f) - f[0]) / SR + phase0))


def supersaw(freqs, n, voices=7, detune=0.25, spread=0.8, rng=None):
    """Stereo stack of detuned polyBLEP saws per note (detune = total spread in semitones, panned across
    +-spread). freqs: list of scalars or per-sample arrays. Returns (2, n)."""
    rng = rng if rng is not None else rng_for('supersaw')
    out = np.zeros((2, n))
    for f in freqs:
        for j in range(voices):
            u = 2.0 * j / (voices - 1) - 1.0 if voices > 1 else 0.0
            det = 0.5 * detune * u * (0.55 + 0.45 * abs(u))
            v = saw(np.asarray(f) * 2.0 ** (det / 12.0), n, rng.random())
            v *= 1.0 if abs(u) < 1e-9 else 0.8
            p = spread * u
            out[0] += v * (1.0 - max(p, 0.0))
            out[1] += v * (1.0 + min(p, 0.0))
    return out / math.sqrt(max(1, len(freqs) * voices))


# ---- envelopes, fades, panning, mixing ---------------------------------------------------------------
def fades(x, fin=0.001, fout=0.004):
    """Raised-cosine fade in/out in place (first and last samples become exactly 0). Returns x."""
    n = x.shape[-1]
    a = min(int(fin * SR), n // 2)
    b = min(int(fout * SR), n // 2)
    if a > 0:
        x[..., :a] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if b > 0:
        x[..., n - b:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, b + 1) / b)
    return x


def adsr(n, attack, decay, sustain, release, gate=None):
    """Raised-cosine attack, exponential decay (time constant) to sustain, exponential release from the
    gate time. Ends at exactly 0."""
    t = tvec(n)
    a = max(attack, 1e-4)

    def level(tt):
        return np.where(tt < a, 0.5 - 0.5 * np.cos(np.pi * np.minimum(tt, a) / a),
                        sustain + (1.0 - sustain) * np.exp(-np.maximum(tt - a, 0.0) / max(decay, 1e-4)))
    env = level(t)
    if gate is not None and gate < n / SR:
        g0 = float(level(np.array([gate]))[0])
        env = np.where(t < gate, env, g0 * np.exp(-np.maximum(t - gate, 0.0) / max(release, 1e-4)))
    return fades(env, 0.0, 0.003)


def hann(n):
    return 0.5 - 0.5 * np.cos(TAU * (np.arange(n) + 0.5) / n)


def norm(x, peak=1.0):
    m = float(np.max(np.abs(x))) if x.size else 0.0
    return x * (peak / m) if m > 1e-12 else x


def stereo(x, pan=0.0):
    """Mono -> (2, n) with a balance pan law (center = unity per side); stereo input gets balanced."""
    gl, gr = 1.0 - max(pan, 0.0), 1.0 + min(pan, 0.0)
    if x.ndim == 1:
        return np.stack([x * gl, x * gr])
    return np.stack([x[0] * gl, x[1] * gr]) if pan else x


def mix_into(bus, buf, s, gain=1.0):
    """Add buf into bus starting at sample s (clipped to the bus). Handles mono/stereo combos."""
    if gain == 0.0:
        return
    if bus.ndim == 1 and buf.ndim == 2:
        buf = buf.mean(axis=0)
    elif bus.ndim == 2 and buf.ndim == 1:
        buf = np.stack([buf, buf])
    n, m = bus.shape[-1], buf.shape[-1]
    a, b = max(0, s), min(n, s + m)
    if b > a:
        bus[..., a:b] += gain * buf[..., a - s:b - s]


def noise_st(rng, n, corr=0.7):
    """Stereo noise with partial L/R correlation (0 = independent, 1 = mono)."""
    c = rng.standard_normal(n)
    return np.stack([corr * c + math.sqrt(1 - corr * corr) * rng.standard_normal(n),
                     corr * c + math.sqrt(1 - corr * corr) * rng.standard_normal(n)])


def crush(x, bits=8, down=4):
    """Bitcrusher: sample-and-hold decimation + quantization."""
    n = x.shape[-1]
    idx = (np.arange(n) // max(1, int(down))) * max(1, int(down))
    q = 2.0 ** (bits - 1)
    return np.round(x[..., idx] * q) / q


# ---- space: synthesized-IR convolution reverb and a feedback ping-pong delay -------------------------
_IR_CACHE = {}


def make_ir(name, length, rt_low, rt_high, predelay=0.012, hp=160.0, lp=13000.0, er=0.35, width=1.0,
            onset=0.008):
    """Stereo reverb impulse response: decorrelated noise split into octave bands (raised-cosine
    crossovers, partition of unity), each band decaying with its own RT60 (air/wall absorption: highs
    die first), a smooth density build-up, sparse early reflections, band-limited, energy-normalized."""
    key = (name, length, rt_low, rt_high, predelay, hp, lp, er, width, onset)
    if key in _IR_CACHE:
        return _IR_CACHE[key]
    n = int(length * SR)
    t = tvec(n)
    rng = rng_for('ir', name)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    lf = np.log2(np.maximum(f, 15.0) / 1000.0)
    centers = np.arange(-4, 5)                      # 62.5 Hz .. 16 kHz
    rts = rt_low + (rt_high - rt_low) * np.clip((centers + 2.0) / 5.5, 0.0, 1.0)
    tp = np.maximum(t - predelay, 0.0)
    env_on = np.where(t >= predelay, 1.0 - np.exp(-tp / onset), 0.0)
    ir = np.zeros((2, n))
    for ch in range(2):
        S = np.fft.rfft(rng.standard_normal(n))
        acc = np.zeros(n)
        for i, (c, rt) in enumerate(zip(centers, rts)):
            w = np.cos(0.5 * np.pi * np.clip(lf - c, -1.0, 1.0)) ** 2
            if i == 0:
                w = np.where(lf < c, 1.0, w)
            if i == len(centers) - 1:
                w = np.where(lf > c, 1.0, w)
            acc += np.fft.irfft(S * w, n) * np.exp(-LN1000 * tp / rt)
        ir[ch] = acc * env_on
        # early reflections: a few smoothed taps in the first ~70 ms, different per side
        taps = np.sort(rng.uniform(0.003, 0.07, 9)) + predelay * 0.4
        for tt in taps:
            s = int(tt * SR)
            if s + 4 < n:
                g = er * 5.0 * math.exp(-tt / 0.045) * (1 if rng.random() < 0.5 else -1)
                ir[ch, s:s + 4] += g * np.array([0.25, 0.75, 0.75, 0.25])
    ir = filt(ir, ('hp', hp, 0.7), ('lp', lp, 0.7))
    k = int(0.2 * n)
    ir[:, n - k:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, k + 1) / k)
    m, s = 0.5 * (ir[0] + ir[1]), 0.5 * (ir[0] - ir[1]) * width
    ir = np.stack([m + s, m - s])
    ir /= math.sqrt(float(np.sum(ir * ir)) / 2.0) + 1e-12
    _IR_CACHE[key] = ir
    return ir


def convolve(x, ir, keep_tail=False):
    """Mono (n,) or stereo (2, n) input folded to mono, convolved with a stereo IR via FFT -> (2, n)."""
    if x.ndim == 2:
        x = x.mean(axis=0)
    n, m = x.shape[-1], ir.shape[-1]
    L = fft_len(n + m)
    y = np.fft.irfft(np.fft.rfft(x, L)[None, :] * np.fft.rfft(ir, L, axis=-1), L, axis=-1)
    return y[:, :n + m - 1] if keep_tail else y[:, :n]


def pingpong(x, delay_s, feedback=0.42, lp=4500.0, hp=320.0):
    """Tempo-synced ping-pong delay (mono in, stereo out, wet only). The whole feedback network (echo
    alternating L/R, loop filters in every repeat) is evaluated exactly as a transfer function in the
    frequency domain: L = X z H / (1 - G^2), R = X z H G / (1 - G^2), G = fb H z, z = e^{-jwD}."""
    if x.ndim == 2:
        x = x.mean(axis=0)
    n = x.shape[-1]
    D = delay_s * SR
    reps = max(4, int(math.log(1e-5) / math.log(max(feedback, 1e-3))) + 2)
    L = fft_len(n + int(reps * D))
    H = _response([biquad('lp', lp, 0.6), biquad('hp', hp, 0.6)], L)
    z = np.exp(-1j * TAU * np.arange(L // 2 + 1) * D / L)
    G = feedback * H * z
    X = np.fft.rfft(x, L) * H * z / (1.0 - G * G)
    return np.stack([np.fft.irfft(X, L)[:n], np.fft.irfft(X * G, L)[:n]])


# ---- dynamics ----------------------------------------------------------------------------------------
def _blocks(v, ctl, fn):
    n = v.shape[-1]
    nb = -(-n // ctl)
    pad = np.concatenate([v, np.full(nb * ctl - n, v[-1])])
    return fn(pad.reshape(nb, ctl), axis=1)


def compressor(x, thr_db, ratio, attack, release, knee_db=6.0, rms_ms=5.0, ctl=16, key=None):
    """Feed-forward envelope-follower compressor, stereo-linked. RMS detector -> soft-knee gain computer
    -> attack/release ballistics on the gain (control rate = SR/ctl) -> interpolated gain.
    Returns (y, gain_reduction_db per sample)."""
    k = x if key is None else key
    p = (k * k).mean(axis=0) if k.ndim == 2 else k * k
    n = p.shape[0]
    w = max(1, int(rms_ms * 1e-3 * SR))
    c = np.concatenate([np.zeros(w), np.cumsum(p)])
    ms = (c[w:] - c[:-w]) / w
    lv = 10.0 * np.log10(_blocks(ms, ctl, np.max) + 1e-12)
    over = lv - thr_db
    gr = np.where(2 * over < -knee_db, 0.0,
                  np.where(2 * over > knee_db, over * (1.0 / ratio - 1.0),
                           (1.0 / ratio - 1.0) * (over + knee_db / 2.0) ** 2 / (2.0 * knee_db)))
    aa = math.exp(-ctl / (attack * SR))
    ar = math.exp(-ctl / (release * SR))
    s = 0.0
    out = []
    for g in gr.tolist():
        s = (aa * s + (1 - aa) * g) if g < s else (ar * s + (1 - ar) * g)
        out.append(s)
    grs = np.interp(np.arange(n), (np.arange(len(out)) + 0.5) * ctl, np.array(out))
    return x * 10.0 ** (grs / 20.0), grs


def duck_env(key, release=0.09, attack=0.0015, lookahead=0.003, ctl=16):
    """Sidechain envelope 0..1 keyed to a signal: instant-attack peak follower with exponential release
    (vectorized as a running max in the dB domain), a short attack smoother, and a small lookahead so the
    ducked part is already down when the key's transient lands."""
    k = np.abs(key).max(axis=0) if key.ndim == 2 else np.abs(key)
    n = k.shape[0]
    ref = float(k.max())
    if ref < 1e-9:
        return np.zeros(n)
    pk_db = 20.0 * np.log10(_blocks(k / ref, ctl, np.max) + 1e-9)
    r = 8.685889638 * ctl / (release * SR)            # dB per control step for time constant `release`
    ramp = np.arange(pk_db.shape[0]) * r
    env = 10.0 ** ((np.maximum.accumulate(pk_db + ramp) - ramp) / 20.0)
    b, a = onepole_ba(attack / ctl)
    env = iir(env, [(b, a)])
    pos = (np.arange(env.shape[0]) + 0.5) * ctl - lookahead * SR
    return np.clip(np.interp(np.arange(n), pos, env), 0.0, 1.0)


def upsample(x, factor):
    """Band-limited (ideal, FFT) upsampling along the last axis."""
    n = x.shape[-1]
    X = np.fft.rfft(x, axis=-1)
    if n % 2 == 0:
        X[..., -1] *= 0.5
    Y = np.zeros(x.shape[:-1] + (n * factor // 2 + 1,), complex)
    Y[..., :X.shape[-1]] = X
    return np.fft.irfft(Y, n * factor, axis=-1) * factor


def downsample(y, factor):
    m = y.shape[-1]
    n = m // factor
    Y = np.fft.rfft(y, axis=-1)[..., :n // 2 + 1]
    return np.fft.irfft(Y, n, axis=-1) / factor


def true_peak(x, os_factor=4):
    return float(np.max(np.abs(upsample(x, os_factor))))


def soft_clip(x, ceiling=1.0, knee=0.7, os_factor=4):
    """Transparent below knee*ceiling, tanh-shaped above, asymptote at ceiling. 4x oversampled."""
    up = upsample(x, os_factor)
    T = knee * ceiling
    r = ceiling - T
    a = np.abs(up)
    y = np.where(a > T, np.sign(up) * (T + r * np.tanh((a - T) / r)), up)
    return downsample(y, os_factor)


def sliding_min(x, L):
    """y[i] = min(x[i : i+L]) in O(n) (van Herk / Gil-Werman)."""
    n = x.shape[0]
    nb = -(-(n + L) // L)
    pad = np.full(nb * L, np.inf)
    pad[:n] = x
    blk = pad.reshape(nb, L)
    pre = np.minimum.accumulate(blk, axis=1).ravel()
    suf = np.minimum.accumulate(blk[:, ::-1], axis=1)[:, ::-1].ravel()
    i = np.arange(n)
    return np.minimum(suf[i], pre[i + L - 1])


def limiter(x, ceiling_db=-1.0, lookahead=0.005, release_db_s=30.0, os_factor=4):
    """Lookahead true-peak limiter. Detector: 4x oversampled peak per sample. Gain: forward sliding min
    over the lookahead window, release limited to release_db_s (a dB-domain running min, i.e. exponential
    recovery), then a moving average over the same window so each gain dip is a smooth ramp that is
    complete by the time the peak arrives (every value averaged is <= the gain that peak needs)."""
    n = x.shape[-1]
    row = np.abs(upsample(x, os_factor)).max(axis=0).reshape(n, os_factor).max(axis=1)
    pk = np.maximum(np.maximum(row, np.concatenate([[0.0], row[:-1]])), np.abs(x).max(axis=0))
    g = np.minimum(1.0, undb(ceiling_db) / np.maximum(pk, 1e-9))
    L = max(1, int(lookahead * SR))
    m = sliding_min(g, L + 1)
    gdb = 20.0 * np.log10(np.maximum(m, 1e-9))
    ramp = np.arange(n) * (release_db_s / SR)
    gdb = np.minimum.accumulate(gdb - ramp) + ramp
    gg = np.concatenate([np.ones(L), 10.0 ** (gdb / 20.0)])
    c = np.concatenate([[0.0], np.cumsum(gg)])
    ga = (c[L + 1:] - c[:-L - 1]) / (L + 1)
    return x * ga, ga


# ---- loudness (ITU-R BS.1770-4 / EBU R128) -----------------------------------------------------------
K_WEIGHTING = [
    (np.array([1.53512485958697, -2.69169618940638, 1.19839281085285]),
     np.array([1.0, -1.69065929318241, 0.73248077421585])),
    (np.array([1.0, -2.0, 1.0]), np.array([1.0, -1.99004745483398, 0.99007225036621])),
]


def lufs(x):
    """Integrated loudness (gated) of a (2, n) 48 kHz signal."""
    y = iir(x, K_WEIGHTING)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    n = y.shape[-1]
    if n < blk:
        return -70.0
    c = np.concatenate([np.zeros((y.shape[0], 1)), np.cumsum(y * y, axis=1)], axis=1)
    starts = np.arange(0, n - blk + 1, hop)
    z = ((c[:, starts + blk] - c[:, starts]) / blk).sum(axis=0)
    ld = -0.691 + 10.0 * np.log10(z + 1e-15)
    z1 = z[ld > -70.0]
    if z1.size == 0:
        return -70.0
    rel = -0.691 + 10.0 * np.log10(z1.mean()) - 10.0
    z2 = z[(ld > -70.0) & (ld > rel)]
    return float(-0.691 + 10.0 * np.log10(z2.mean()))


# ---- WAV IO ------------------------------------------------------------------------------------------
def write_wav(path, x, bits=24):
    """(channels, n) float -> WAV. bits 24 (PCM, clipped, rounded) or 32 (IEEE float)."""
    x = np.atleast_2d(np.asarray(x, float))
    ch, n = x.shape
    if bits == 24:
        q = np.clip(np.round(x.T * 8388607.0), -8388608, 8388607).astype('<i4')
        data = q.reshape(-1).view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
        fmt = (1, ch, SR, SR * ch * 3, ch * 3, 24)
    else:
        data = x.T.astype('<f4').tobytes()
        fmt = (3, ch, SR, SR * ch * 4, ch * 4, 32)
    import struct
    hdr = b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE'
    hdr += b'fmt ' + struct.pack('<IHHIIHH', 16, *fmt)
    hdr += b'data' + struct.pack('<I', len(data))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(hdr)
        fh.write(data)


def read_wav(path):
    """Minimal reader for the files this script writes (PCM 16/24/32, float 32). -> (channels, n), sr."""
    import struct
    with open(path, 'rb') as fh:
        raw = fh.read()
    pos, fmt, data = 12, None, None
    while pos + 8 <= len(raw):
        cid, size = raw[pos:pos + 4], struct.unpack('<I', raw[pos + 4:pos + 8])[0]
        body = raw[pos + 8:pos + 8 + size]
        if cid == b'fmt ':
            fmt = struct.unpack('<HHIIHH', body[:16])
        elif cid == b'data':
            data = body
        pos += 8 + size + (size & 1)
    tag, ch, sr, _, _, bits = fmt
    if tag == 3:
        a = np.frombuffer(data, '<f4').astype(float)
    elif bits == 24:
        b = np.frombuffer(data, np.uint8).reshape(-1, 3)
        a = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        a = np.where(a >= 1 << 23, a - (1 << 24), a) / 8388608.0
    else:
        a = np.frombuffer(data, '<i%d' % (bits // 8)).astype(float) / 2.0 ** (bits - 1)
    return a.reshape(-1, ch).T, sr


# =====================================================================================================
# 3. SOUNDS
# =====================================================================================================
F1 = hz(29)                     # 43.65 Hz: kick tail, sub and impacts are tuned to the key


# ---- drums --------------------------------------------------------------------------------------------
def v_kick(seed=0, length=0.42, f_hi=185.0, f_lo=F1, tau_p=0.030, decay=0.115, hold=0.016, click=0.33,
           drive=2.2):
    """Sine body with a fast pitch envelope (~185 Hz -> F1) + click transient + soft saturation."""
    n = int(length * SR)
    t = tvec(n)
    f = f_lo + (f_hi - f_lo) * np.exp(-t / tau_p) + 300.0 * np.exp(-t / 0.0022)
    amp = np.where(t < hold, 1.0, np.exp(-np.maximum(t - hold, 0.0) / decay))
    body = sine(f) * amp
    rng = rng_for('kick', seed)
    nz = filt(rng.standard_normal(n), ('hp', 2200, 0.7), ('lp', 8500, 0.7)) * np.exp(-t / 0.0014)
    cl = 0.6 * norm(nz) + 0.4 * np.sin(TAU * 1650.0 * t) * np.exp(-t / 0.0025)
    x = np.tanh(drive * (body + click * cl)) / math.tanh(drive)
    x = filt(x, ('hp', 24, 0.7))
    return norm(fades(x, 0.0003, 0.03))


def v_clap(seed=0):
    """Four offset bandpassed noise bursts + a tail, with a built-in short room."""
    n = int(0.42 * SR)
    t = tvec(n)
    rng = rng_for('clap', seed)
    src = noise_st(rng, n, 0.8)
    env = np.zeros(n)
    offs = np.array([0.0, 0.0105, 0.0205, 0.031]) + np.concatenate([[0.0], rng.uniform(-0.0012, 0.0012, 3)])
    for o, a in zip(offs, (0.8, 0.7, 0.85, 1.0)):
        tt = t - o
        env += np.where(tt >= 0, a * np.exp(-np.maximum(tt, 0.0) / 0.0033), 0.0)
    tt = t - offs[-1]
    env += np.where(tt >= 0, 0.75 * np.exp(-np.maximum(tt, 0.0) / 0.10), 0.0)
    x = filt(src * env, ('hp', 820, 0.7), ('peak', 1250, 1.4, 7.0), ('peak', 3200, 1.0, 2.5), ('lp', 10500, 0.7))
    room = convolve(x, make_ir('clap-room', 0.3, 0.32, 0.18, predelay=0.004, hp=400, lp=9000, er=0.6))
    x = norm(x) + 0.28 * norm(room)
    return norm(fades(x, 0.0003, 0.02))


HAT_OSC = (263.0, 400.0, 421.0, 474.0, 587.0, 845.0)   # TR-808 metal oscillator bank


def v_hat(open_=False, seed=0):
    """Metallic hat: six band-limited squares at inharmonic ratios + noise, steep highpass."""
    n = int((0.5 if open_ else 0.11) * SR)
    t = tvec(n)
    rng = rng_for('hat', open_, seed)
    det = rng.uniform(0.985, 1.015)
    metal = sum(square(f * det, n, rng.random()) for f in HAT_OSC) / 6.0
    x = 0.6 * metal[None, :] + 0.55 * noise_st(rng, n, 0.75)
    x = filt(x, ('hp', 6800, 0.75), ('hp', 6800, 0.75), ('peak', 10500, 1.0, 3.0), ('lp', 17000, 0.7))
    env = np.exp(-t / 0.17) * (0.8 + 0.2 * np.exp(-t / 0.02)) if open_ else np.exp(-t / 0.019)
    return norm(fades(x * env, 0.0002, 0.04 if open_ else 0.012))


def v_snare(seed=0, tight=False, pitch=1.0):
    n = int((0.24 if tight else 0.36) * SR)
    t = tvec(n)
    rng = rng_for('snare', seed)
    body = (sine(188.0 * pitch * (1 + 0.12 * np.exp(-t / 0.008)))
            + 0.55 * sine(332.0 * pitch * (1 + 0.08 * np.exp(-t / 0.008)))) * np.exp(-t / (0.035 if tight else 0.05))
    nz = filt(noise_st(rng, n, 0.8), ('hp', 1300, 0.7), ('peak', 5200, 0.9, 4.0), ('lp', 12000, 0.7))
    nz = norm(nz) * np.exp(-t / (0.07 if tight else 0.12))
    x = 0.7 * body[None, :] / 1.55 + 0.8 * nz
    x = np.tanh(1.6 * x) / math.tanh(1.6)
    return norm(fades(x, 0.0003, 0.02))


def v_tom(f0, seed=0):
    n = int(0.5 * SR)
    t = tvec(n)
    rng = rng_for('tom', f0, seed)
    body = sine(f0 * (1 + 0.55 * np.exp(-t / 0.014))) * np.exp(-t / 0.17)
    skin = norm(filt(rng.standard_normal(n), ('bp', 2.3 * f0, 1.0))) * np.exp(-t / 0.018) * 0.3
    x = np.tanh(1.5 * (body + skin)) / math.tanh(1.5)
    return norm(fades(x, 0.0003, 0.03))


def v_rim(seed=0):
    n = int(0.09 * SR)
    t = tvec(n)
    rng = rng_for('rim', seed)
    x = 0.8 * np.sin(TAU * 1710 * t) * np.exp(-t / 0.009) + 0.6 * np.sin(TAU * 820 * t) * np.exp(-t / 0.016)
    x = x + 0.5 * norm(filt(rng.standard_normal(n), ('hp', 2500, 0.7))) * np.exp(-t / 0.0012)
    return norm(fades(x, 0.0002, 0.01))


def v_shaker(seed=0, accent=False):
    n = int(0.13 * SR)
    t = tvec(n)
    rng = rng_for('shaker', seed)
    x = filt(noise_st(rng, n, 0.6), ('bp', 7200, 1.1), ('hp', 4200, 0.7))
    env = (1.0 - np.exp(-t / 0.006)) * np.exp(-t / (0.034 if accent else 0.026))
    return norm(fades(x * env, 0.001, 0.01))


def v_tick(pitch=1.0, seed=0):
    """Short glassy tick: two sine pings + a hair of highpassed noise."""
    n = int(0.06 * SR)
    t = tvec(n)
    rng = rng_for('tick', seed)
    x = 0.7 * np.sin(TAU * 3150 * pitch * t) * np.exp(-t / 0.0055)
    x += 0.35 * np.sin(TAU * 1180 * pitch * t) * np.exp(-t / 0.003)
    x += 0.5 * norm(filt(rng.standard_normal(n), ('hp', 4500, 0.7))) * np.exp(-t / 0.0009)
    return norm(fades(x, 0.0002, 0.008))


# ---- tonal voices -------------------------------------------------------------------------------------
def v_bass(midi, gate, vel=1.0, seed=0):
    """Plucky mid bass: two detuned saws + square, resonant SVF lowpass with a decaying cutoff envelope,
    saturation, highpassed so the sine sub owns the lows."""
    f = hz(midi)
    n = int((gate + 0.08) * SR)
    t = tvec(n)
    rng = rng_for('bass', seed)
    x = saw(f * 2 ** (-6 / 1200), n, rng.random()) + saw(f * 2 ** (6 / 1200), n, rng.random())
    x += 0.45 * square(f, n, rng.random())
    fc = 150.0 + (1300.0 + 1600.0 * vel) * np.exp(-t / 0.07)
    y = svf(x, fc, q=1.3) * adsr(n, 0.0015, 0.11, 0.55, 0.025, gate)
    y = np.tanh(1.8 * y) / math.tanh(1.8)
    y = filt(y, ('hp', 75, 0.7))
    return norm(fades(y, 0.0005, 0.004), vel)


def v_stab(notes, cut, vel=1.0, gate=0.1, seed=0):
    """Hook chord stab: per note two detuned saws (split L/R) + a centered square; resonant lowpass whose
    cutoff opens with velocity and snaps shut; pluck envelope."""
    n = int((gate + 0.45) * SR)
    t = tvec(n)
    rng = rng_for('stab', seed)
    x = np.zeros((2, n))
    for m in notes:
        f = hz(m)
        a = saw(f * 2 ** (-9 / 1200), n, rng.random())
        b = saw(f * 2 ** (9 / 1200), n, rng.random())
        c = 0.35 * square(f, n, rng.random())
        x[0] += a + 0.35 * b + c
        x[1] += b + 0.35 * a + c
    fc = np.minimum(cut * (1.0 + 3.0 * vel * np.exp(-t / 0.05)), 16000.0)
    y = svf(x, fc, q=0.95) * adsr(n, 0.0012, 0.14, 0.0, 0.08, gate)
    y = filt(np.tanh(1.3 * y), ('hp', 170, 0.7))
    return norm(fades(y, 0.0005, 0.01), vel)


def v_saw(notes, cut, vel=1.0, gate=0.2, seed=0):
    """Drop chord: 7-voice supersaw per note, wide, filter envelope, sustained body."""
    n = int((gate + 0.4) * SR)
    t = tvec(n)
    rng = rng_for('saw', seed)
    x = supersaw([hz(m) for m in notes], n, voices=7, detune=0.30, spread=0.9, rng=rng)
    fc = np.minimum(cut * (1.0 + 1.6 * np.exp(-t / 0.12)), 17000.0)
    y = svf(x, fc, q=0.8) * adsr(n, 0.003, 0.25, 0.55, 0.16, gate)
    y = filt(y, ('hp', 190, 0.7))
    return norm(fades(y, 0.001, 0.01), vel)


def v_pad(notes, length, seed=0):
    """Resolve pad: 5-voice supersaw per note + a sine an octave under the root, slowly closing filter,
    held then decaying to near-silence by the end of its window."""
    n = int(length * SR)
    t = tvec(n)
    rng = rng_for('pad', seed)
    x = supersaw([hz(m) for m in notes], n, voices=5, detune=0.16, spread=1.0, rng=rng)
    x += 0.25 * sine(hz(notes[0]), n)[None, :]
    fc = 600.0 + 3000.0 * np.exp(-t / (0.3 * length))
    y = svf(x, fc, q=0.7)
    env = np.where(t < 0.2, 1.0, np.exp(-np.maximum(t - 0.2, 0.0) / (0.2 * length)))
    y *= env * (1.0 - np.exp(-t / 0.006))
    return norm(fades(y, 0.0, 0.05))


def render_sub(notes, n):
    """Whole-song sine sub (one continuous oscillator, so note changes never click): frequency track with a
    short glide, gate track smoothed to ~5 ms, gentle saturation for small-speaker harmonics."""
    if not notes:
        return np.zeros(n)
    tf = np.zeros(n)
    ta = np.zeros(n)
    has = np.zeros(n, bool)
    for t0, t1, m, v in sorted(notes):
        s0, s1 = max(0, smp(t0)), min(n, smp(t1))
        tf[s0:s1] = hz(m)
        ta[s0:s1] = v
        has[s0:s1] = True
    idx = np.maximum.accumulate(np.where(has, np.arange(n), 0))
    first = int(np.argmax(has))
    tf = np.where(np.arange(n) < first, tf[first], tf[idx])
    f = tf[0] + iir(tf - tf[0], [onepole_ba(0.008)])
    a = iir(ta, [onepole_ba(0.005)])
    x = sine(f)
    x = np.tanh(1.7 * (x + 0.15 * x * x)) / math.tanh(1.7)
    return filt(x, ('hp', 18, 0.7)) * a


# ---- R.sfx vocabulary -----------------------------------------------------------------------------------
# Each renderer returns (stereo buffer, offset seconds relative to the event time t).
def s_impact(amt=1.0, tone='std', seed=0, **_):
    """Layered hit: kick transient + sub boom (F1) + swept noise burst + body thud + a faint metallic
    clang, glued with saturation and a short built-in room."""
    huge, subby = tone == 'huge', tone == 'sub'
    n = int((2.4 if huge else 1.6) * SR)
    t = tvec(n)
    rng = rng_for('impact', seed)
    kick = np.zeros(n)
    k = v_kick(seed=seed, length=0.9, f_hi=165.0, f_lo=F1 * 0.97, tau_p=0.04, decay=0.28 if huge else 0.2,
               hold=0.03, click=0.45, drive=2.6)
    kick[:k.shape[0]] = k
    boom = sine(F1 * (1 + 0.45 * np.exp(-t / 0.05))) * (1 - np.exp(-t / 0.003)) * np.exp(-t / (0.5 if huge else 0.32))
    boom = np.tanh(1.8 * boom) / math.tanh(1.8)
    nz = svf(noise_st(rng, n, 0.5), 600.0 + 9500.0 * np.exp(-t / (0.16 if huge else 0.11)), q=0.75)
    nz = norm(nz) * (1 - np.exp(-t / 0.0015)) * (0.75 * np.exp(-t / 0.09) + 0.25 * np.exp(-t / (0.4 if huge else 0.3)))
    thud = norm(filt(rng.standard_normal(n), ('bp', 120, 1.2))) * np.exp(-t / 0.08)
    clang = sum(np.sin(TAU * f * t + rng.uniform(0, TAU)) * np.exp(-t / d)
                for f, d in ((233, 0.5), (377, 0.35), (611, 0.25), (947, 0.18), (1433, 0.12))) / 3.0
    clang *= 1 - np.exp(-t / 0.002)
    w = (dict(k=0.5, b=1.0, n=0.18, t=0.25, c=0.0) if subby else
         dict(k=1.0, b=1.0, n=0.7, t=0.45, c=0.12) if huge else dict(k=0.9, b=0.8, n=0.55, t=0.35, c=0.07))
    mono = w['k'] * kick + w['b'] * boom + w['t'] * thud + w['c'] * clang
    x = mono[None, :] + w['n'] * nz
    x = x + 0.3 * norm(convolve(x, make_ir('impact-room', 0.9, 0.8, 0.45, predelay=0.006))) * np.max(np.abs(x))
    x = np.tanh(1.2 * x) / math.tanh(1.2)
    return norm(fades(x, 0.0003, 0.12), amt), 0.0


def s_whoosh(dur=0.3, dir='up', amt=1.0, seed=0, lo=320.0, hi=5200.0, **_):
    """Air movement that swells to its peak at t + dur: stereo noise through a swept resonant bandpass
    (+ a lowpassed body layer), panning across, short tail after the peak."""
    dur = float(np.clip(dur, 0.05, 6.0))
    tail = max(0.07, 0.3 * dur)
    n = int((dur + tail) * SR)
    t = tvec(n)
    rng = rng_for('whoosh', seed)
    x = t / dur
    u = np.minimum(x, 1.0) + 0.15 * np.maximum(x - 1.0, 0.0)
    if dir == 'down':
        u = 1.0 - u
    fc = lo * (hi / lo) ** np.clip(u, 0.0, 1.2)
    nz = noise_st(rng, n, 0.55)
    air = svf(nz, fc, q=1.6, mode='bp') + 0.35 * svf(nz, fc * 0.3, q=0.7)
    env = np.minimum(x, 1.0) ** 2.6 * np.exp(-np.maximum(t - dur, 0.0) / (tail / 3.5))
    p = (-0.65 + 1.3 * np.minimum(x, 1.0)) * (1 if dir != 'down' else -1)
    out = np.stack([air[0] * (1.0 - np.maximum(p, 0.0)), air[1] * (1.0 + np.minimum(p, 0.0))]) * env
    return norm(fades(out, 0.003, 0.01), amt), 0.0


def s_swish(amt=1.0, seed=0, **_):
    buf, _ = s_whoosh(dur=0.11, dir='up', amt=amt, seed=seed, lo=900.0, hi=7500.0)
    return buf, 0.0


def s_click(pitch=1.0, amt=1.0, seed=0, **_):
    n = int(0.03 * SR)
    t = tvec(n)
    rng = rng_for('click', seed)
    x = 0.6 * np.sin(TAU * 2100 * pitch * t) * np.exp(-t / 0.0025)
    x += 0.5 * np.sin(TAU * 520 * pitch * t) * np.exp(-t / 0.004)
    x += 0.5 * norm(filt(rng.standard_normal(n), ('bp', 3500 * pitch, 1.5))) * np.exp(-t / 0.0012)
    return stereo(norm(fades(x, 0.0002, 0.005), amt)), 0.0


def s_tick(pitch=1.0, amt=1.0, seed=0, **_):
    return stereo(v_tick(pitch * 1.15, seed) * amt), 0.0


def s_pop(pitch=1.0, amt=1.0, seed=0, **_):
    n = int(0.07 * SR)
    t = tvec(n)
    rng = rng_for('pop', seed)
    f = (380.0 + 900.0 * (1 - np.exp(-t / 0.012))) * pitch
    x = sine(f) * (1 - np.exp(-t / 0.0008)) * np.exp(-t / 0.018)
    x += 0.25 * norm(filt(rng.standard_normal(n), ('hp', 3000, 0.7))) * np.exp(-t / 0.0008)
    return stereo(norm(fades(x, 0.0002, 0.006), amt)), 0.0


def s_blip(pitch=1.0, amt=1.0, seed=0, **_):
    n = int(0.14 * SR)
    t = tvec(n)
    f = hz(84) * pitch * (1 + 0.03 * (1 - np.exp(-t / 0.02)))     # C6: the fifth of F
    x = (sine(f) + 0.25 * sine(2 * f) + 0.08 * sine(3 * f)) * (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.045)
    return stereo(norm(fades(x, 0.0005, 0.01), amt)), 0.0


def s_glitch_layer(dur=0.2, amt=1.0, seed=0, **_):
    """The SFX-bus half of a glitch (the music-bus buffer-repeat is edit_glitch): gated bandpassed noise
    chopped at 64ths + short pitched square zaps, bitcrushed."""
    n = max(1, int(dur * SR))
    rng = rng_for('glitch-layer', seed)
    out = np.zeros((2, n))
    g = int(S16 / 4 * SR)
    for s in range(0, n, g):
        if rng.random() < 0.5:
            m = min(g, n - s)
            nz = noise_st(rng, m, 0.3) * rng.uniform(0.3, 1.0)
            out[:, s:s + m] += fades(nz, 0.0008, 0.0008)
    out = filt(out, ('bp', rng.uniform(2500, 6000), 0.8))
    for _ in range(int(rng.integers(1, 4))):
        m = int(rng.uniform(0.015, 0.04) * SR)
        s = int(rng.uniform(0, max(1, n - m)))
        f = rng.uniform(600, 2600)
        z = square(f * (1 - 0.4 * tvec(m) / max(m / SR, 1e-3)), m, 0.0) * 0.5
        mix_into(out, stereo(fades(z, 0.001, 0.003), rng.uniform(-0.5, 0.5)), s)
    out = crush(out, bits=int(rng.integers(5, 8)), down=int(rng.integers(3, 8)))
    return norm(fades(out, 0.002, 0.004), amt), 0.0


def s_riser(dur=BAR, amt=1.0, seed=0, **_):
    """Tension build ending at t + dur: noise through a bandpass sweeping 250 Hz -> 11 kHz with rising
    resonance and width, plus a supersaw gliding up two octaves under an accelerating tremolo."""
    dur = float(np.clip(dur, 0.1, 8.0))
    n = int(dur * SR)
    t = tvec(n)
    rng = rng_for('riser', seed)
    x = t / dur
    fc = 250.0 * (11000.0 / 250.0) ** (x ** 1.4)
    nz = noise_st(rng, n, 0.6)
    nzf = svf(nz, fc, q=0.8 + 2.2 * x * x, mode='bp') + 0.25 * svf(nz, fc * 0.5, q=0.7)
    m, s = 0.5 * (nzf[0] + nzf[1]), 0.5 * (nzf[0] - nzf[1]) * (0.3 + 0.7 * x)
    nzf = norm(np.stack([m + s, m - s])) * (0.06 + 0.94 * x ** 2.2)
    f0 = hz(53) * 2.0 ** (24.0 * x ** 1.6 / 12.0)           # F3 -> F5
    syn = supersaw([f0, f0 * 1.5], n, voices=5, detune=0.35, spread=0.8, rng=rng)
    syn = svf(syn, 500.0 * 24.0 ** x, q=1.1)
    rate = (2.0 / BEAT) * 2.0 ** (2.0 * x)                  # 8ths -> 32nds
    trem = 0.55 + 0.45 * np.cos(TAU * (np.cumsum(rate) - rate[0]) / SR)
    syn = norm(syn) * trem * x ** 2.5
    out = 0.8 * nzf + 0.5 * syn
    return norm(fades(out, 0.02, 0.005), amt), 0.0


def s_reverse(dur=0.47, amt=1.0, seed=0, chord_notes=None, **_):
    """Reverse swell landing at t + dur: a bright chord stab + noise burst is convolved with a long
    synthesized room, time-reversed and trimmed so its tail swells into the landing point."""
    dur = float(np.clip(dur, 0.05, 6.0))
    rng = rng_for('reverse', seed)
    notes = chord_notes or [56, 60, 63, 67]
    src = v_stab(notes, 5000.0, vel=1.0, gate=0.12, seed=seed).mean(axis=0)
    hit = norm(filt(rng.standard_normal(int(0.08 * SR)), ('hp', 3000, 0.7))) * np.exp(-tvec(int(0.08 * SR)) / 0.015)
    src[:hit.shape[0]] += 0.5 * hit
    ir = make_ir('reverse', dur + 0.6, 3.0, 1.8, predelay=0.0, hp=250, lp=12000, er=0.0, onset=0.006)
    wet = convolve(src, ir, keep_tail=True)[:, ::-1]
    m = int(dur * SR)
    seg = wet[:, -m:] if wet.shape[1] >= m else np.pad(wet, ((0, 0), (m - wet.shape[1], 0)))
    seg = seg * (np.linspace(0.0, 1.0, m) ** 1.5)
    return norm(fades(seg, 0.01, 0.003), amt), 0.0


def s_subdrop(amt=1.0, seed=0, **_):
    """808-style sub drop: sine falling from F2 to ~28 Hz, saturated for audible harmonics."""
    n = int(1.7 * SR)
    t = tvec(n)
    f = 28.0 + (hz(41) - 28.0) * np.exp(-t / 0.3)
    x = sine(f) * (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.42)
    x = filt(np.tanh(2.2 * x) / math.tanh(2.2), ('lp', 500, 0.7), ('hp', 22, 0.7))
    return stereo(norm(fades(x, 0.0005, 0.1), amt)), 0.0


def s_shimmer(dur=0.9, amt=1.0, seed=0, **_):
    """Airy sparkle: random high sine grains on the F minor pentatonic (C6..A#7), random pans."""
    dur = float(np.clip(dur, 0.05, 8.0))
    n = int((dur + 0.15) * SR)
    rng = rng_for('shimmer', seed)
    midis = [m for m in range(84, 107) if m % 12 in (5, 8, 10, 0, 3)]
    out = np.zeros((2, n))
    for _ in range(max(6, int(dur * 60))):
        tg = dur * rng.random() ** 1.3
        L = int(rng.uniform(0.03, 0.09) * SR)
        f = hz(float(rng.choice(midis))) * (1 + rng.uniform(-0.002, 0.002))
        tt = tvec(L)
        g = (np.sin(TAU * f * tt) + 0.2 * np.sin(TAU * 2 * f * tt)) * hann(L)
        g *= rng.uniform(0.35, 1.0) * (1.0 - 0.6 * tg / dur)
        mix_into(out, stereo(g, rng.uniform(-0.9, 0.9)), smp(tg))
    return norm(fades(out, 0.002, 0.02), amt), 0.0


def s_type(count=6, dur=0.3, amt=1.0, seed=0, **_):
    """Typewriter / letter-by-letter: count key ticks at t + i * dur / count."""
    count = int(np.clip(count, 1, 400))
    dur = float(np.clip(dur, 0.0, 30.0))
    step = dur / count
    k = int(0.05 * SR)
    t = tvec(k)
    out = np.zeros((2, int(dur * SR) + k + 1))
    for i in range(count):
        rng = rng_for('type', seed, i)
        p = rng.uniform(0.92, 1.08)
        x = norm(filt(rng.standard_normal(k), ('bp', 2600 * p, 1.4))) * np.exp(-t / 0.0025)
        x += 0.5 * np.sin(TAU * 185 * p * t) * np.exp(-t / 0.01) + 0.25 * np.sin(TAU * 5200 * p * t) * np.exp(-t / 0.0015)
        mix_into(out, stereo(fades(x, 0.0002, 0.005) * rng.uniform(0.75, 1.0), rng.uniform(-0.2, 0.2)), smp(i * step))
    return norm(out, amt), 0.0


def s_air(amt=1.0, seed=0, **_):
    """Soft air / crash wash for bright flashes."""
    n = int(1.4 * SR)
    t = tvec(n)
    rng = rng_for('air', seed)
    metal = sum(square(f * 2.6, n, rng.random()) for f in HAT_OSC[:4]) / 4.0
    x = noise_st(rng, n, 0.2) + 0.25 * metal[None, :]
    x = filt(x, ('hp', 4200, 0.7), ('lp', 14500, 0.7))
    x = norm(x) * (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.38)
    return norm(fades(x, 0.001, 0.1), amt), 0.0


def s_thump(amt=1.0, seed=0, **_):
    """Low body thump for camera shakes."""
    n = int(0.35 * SR)
    t = tvec(n)
    rng = rng_for('thump', seed)
    x = sine(42.0 + 28.0 * np.exp(-t / 0.03)) * np.exp(-t / 0.1)
    x += 0.3 * norm(filt(rng.standard_normal(n), ('lp', 300, 0.7))) * np.exp(-t / 0.03)
    return stereo(norm(fades(np.tanh(1.5 * x), 0.0005, 0.03), amt)), 0.0


def s_zap(amt=1.0, seed=0, **_):
    """Tiny digital zap for chroma / invert cues."""
    n = int(0.045 * SR)
    t = tvec(n)
    rng = rng_for('zap', seed)
    f0 = rng.uniform(1200, 2400)
    x = square(f0 * (1 - 0.5 * t / t[-1]), n, 0.0) * np.exp(-t / 0.012)
    x = crush(x, bits=5, down=3)
    return stereo(norm(fades(x, 0.0005, 0.005), amt), rng.uniform(-0.4, 0.4)), 0.0


RENDERERS = dict(impact=s_impact, whoosh=s_whoosh, swish=s_swish, click=s_click, tick=s_tick, pop=s_pop,
                 blip=s_blip, glitch=s_glitch_layer, riser=s_riser, reverse=s_reverse, subdrop=s_subdrop,
                 shimmer=s_shimmer, type=s_type, air=s_air, thump=s_thump, zap=s_zap)
DEFAULT_DUR = dict(whoosh=0.3, swish=0.15, glitch=0.2, riser=BAR, reverse=0.47, shimmer=0.9, type=0.3,
                   tapestop=0.3)


# ---- music-bus edits ----------------------------------------------------------------------------------
def splice(bus, s0, seg, xf=48):
    """Replace bus[:, s0:s0+len(seg)] with seg, raised-cosine crossfading xf samples at both edges."""
    n = seg.shape[-1]
    a, b = max(0, s0), min(bus.shape[-1], s0 + n)
    if b <= a:
        return
    seg = seg[:, a - s0:b - s0]
    m = b - a
    w = np.ones(m)
    k = min(xf, m // 2)
    if k > 0:
        r = 0.5 - 0.5 * np.cos(np.pi * (np.arange(k) + 0.5) / k)
        w[:k] = r
        w[m - k:] = r[::-1]
    bus[:, a:b] = bus[:, a:b] * (1.0 - w) + seg * w


def tile_grain(grain, n, xf=32):
    """Repeat a grain to length n, each repetition micro-faded (no clicks at the seams)."""
    g = fades(grain.copy(), min(xf, grain.shape[-1] // 4) / SR, min(xf, grain.shape[-1] // 4) / SR)
    reps = -(-n // max(1, g.shape[-1]))
    return np.tile(g, (1, reps))[:, :n]


def tape_read(src, s0, n, dur_s, stop=True):
    """Read src from s0 with the speed ramping linearly 1 -> 0 over dur_s (tape stop)."""
    tau = tvec(n)
    pos = s0 + (tau - tau * tau / (2.0 * dur_s)) * SR if stop else s0 + tau * SR
    i0 = np.clip(np.floor(pos).astype(int), 0, src.shape[-1] - 2)
    fr = pos - np.floor(pos)
    return src[:, i0] * (1 - fr) + src[:, i0 + 1] * fr


def edit_stutter(bus, orig, bar_i, pattern, rng):
    """Per-step music-bus edits for one bar (see 'stutter' in the ARRANGEMENT notes)."""
    steps, hits = parse_pattern(pattern, keep_ties=False)
    st = BAR / steps
    for i, ch in hits:
        s0 = smp(bar_i * BAR + i * st)
        n = smp(bar_i * BAR + (i + 1) * st) - s0
        src = orig[:, s0:s0 + n]
        if src.shape[1] < n:
            continue
        if ch in '234568':
            seg = tile_grain(src[:, :n // int(ch)], n)
        elif ch == 'r':
            seg = src[:, ::-1].copy()
        elif ch == 'b':
            beat0 = smp(bar_i * BAR + math.floor(i * st / BEAT + 1e-9) * BEAT)
            seg = orig[:, beat0:beat0 + n].copy()
        elif ch == 'x':
            seg = np.zeros_like(src)
        elif ch == 'd':
            seg = crush(src, bits=6, down=6)
        elif ch == 't':
            seg = tape_read(orig, s0, n, n / SR * 1.6) * np.linspace(1, 0.3, n)
        else:
            continue
        splice(bus, s0, seg, xf=48)


def edit_gate(bus, bar_i, pattern, xf=0.002):
    steps, hits = parse_pattern(pattern, keep_ties=False)
    st = BAR / steps
    g = np.zeros(smp(BAR) + 1)
    for i, ch in hits:
        g[smp(i * st):smp((i + 1) * st)] = VEL.get(ch, 1.0) if ch not in 'xX' else 1.0
    k = max(1, int(xf * SR))
    g = np.convolve(g, np.ones(k) / k, mode='same')
    s0 = smp(bar_i * BAR)
    m = min(g.shape[0], bus.shape[1] - s0)
    bus[:, s0:s0 + m] *= g[:m]


def edit_glitch(bus, orig, t, dur, rng):
    """Buffer-repeat burst on the music bus: grains of 1/32..1/256 note captured at the event start (or
    played through), repeated 1-3x, some reversed, bitcrushed."""
    s0 = smp(t)
    n = max(1, int(dur * SR))
    if s0 >= bus.shape[1] or s0 + n <= 0:
        return
    s0c = max(0, s0)
    lens = [int(S16 / 2 * SR), int(S16 / 4 * SR), int(S16 / 8 * SR), int(S16 / 16 * SR)]
    out = np.zeros((2, n))
    pos = 0
    while pos < n:
        L = int(rng.choice(lens, p=[0.3, 0.35, 0.25, 0.1]))
        a = s0c if rng.random() < 0.6 else min(s0c + pos, bus.shape[1] - L - 1)
        grain = orig[:, a:a + L]
        if grain.shape[1] < L:
            break
        if rng.random() < 0.2:
            grain = grain[:, ::-1]
        k = min(int(rng.integers(1, 4)) * L, n - pos)
        out[:, pos:pos + k] = tile_grain(grain, k, xf=24)
        pos += k
    crushed = crush(out, bits=int(rng.integers(6, 9)), down=int(rng.integers(3, 9)))
    splice(bus, s0, 0.45 * out + 0.55 * crushed, xf=96)


def edit_tapestop(bus, orig, t, dur, resume=None):
    """Pitch-down stop of the music bus over dur, then silence until `resume` (default: next beat)."""
    s0 = smp(t)
    n = max(2, int(dur * SR))
    if s0 >= bus.shape[1]:
        return
    seg = tape_read(orig, max(0, s0), n, dur)
    k = int(0.3 * n)
    seg[:, n - k:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, k + 1) / k)
    splice(bus, s0, seg, xf=96)
    if resume is None:
        resume = (math.floor((t + dur) / BEAT + 1e-6) + 1) * BEAT
    s1, s2 = min(bus.shape[1], s0 + n), min(bus.shape[1], max(s0 + n, smp(resume)))
    bus[:, s1:s2] = 0.0
    fi = min(int(0.004 * SR), bus.shape[1] - s2)
    if fi > 0:
        bus[:, s2:s2 + fi] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(fi) / fi)


# =====================================================================================================
# 4. SEQUENCER
# =====================================================================================================
VEL = {'x': 0.85, 'X': 1.0, 'o': 0.55, 'g': 0.3, 'h': 0.85, 'm': 0.85, 'l': 0.85, 'H': 1.0, 'M': 1.0, 'L': 1.0}
VEL.update({str(d): 0.1 + 0.1 * d for d in range(1, 10)})
_NOTE_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
CHORD_TYPES = {
    '': (0, 4, 7), 'maj': (0, 4, 7), 'M': (0, 4, 7), 'm': (0, 3, 7), 'min': (0, 3, 7), '5': (0, 7),
    'sus2': (0, 2, 7), 'sus4': (0, 5, 7), 'sus': (0, 5, 7), 'dim': (0, 3, 6), 'aug': (0, 4, 8),
    '6': (0, 4, 7, 9), 'm6': (0, 3, 7, 9), '7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11), 'M7': (0, 4, 7, 11),
    'm7': (0, 3, 7, 10), 'm7b5': (0, 3, 6, 10), 'dim7': (0, 3, 6, 9), '7sus4': (0, 5, 7, 10),
    'add9': (0, 4, 7, 14), 'madd9': (0, 3, 7, 14), '9': (0, 4, 7, 10, 14), 'maj9': (0, 4, 7, 11, 14),
    'm9': (0, 3, 7, 10, 14), 'm11': (0, 3, 7, 10, 14, 17), '7b9': (0, 4, 7, 10, 13),
}


def note_midi(name):
    """'F1', 'Ab2', 'C#4' (octave defaults to 4) or a number -> MIDI note."""
    if isinstance(name, (int, float)):
        return float(name)
    m = re.fullmatch(r'\s*([A-Ga-g])([#b]*)(-?\d+)?\s*', str(name))
    if not m:
        raise ValueError('bad note name %r' % name)
    pc = _NOTE_PC[m.group(1).upper()] + m.group(2).count('#') - m.group(2).count('b')
    return float((int(m.group(3)) if m.group(3) else 4) * 12 + 12 + pc)


def parse_chord(sym):
    m = re.fullmatch(r'\s*([A-G][#b]?)([^/\s]*)(?:/([A-G][#b]?))?\s*', sym)
    if not m or m.group(2) not in CHORD_TYPES:
        raise ValueError('bad chord %r' % sym)
    root = int(note_midi(m.group(1) + '0')) % 12
    bass = int(note_midi(m.group(3) + '0')) % 12 if m.group(3) else root
    return dict(sym=sym.strip(), root=root, ivs=CHORD_TYPES[m.group(2)], bass=bass)


def voicing(ch, center=62.0, rootless=True):
    """Close-position voicing whose average pitch sits nearest `center`, avoiding semitone clusters.
    Rootless for 5+ note chords (the bass carries the root): Fm9 -> Ab3 C4 Eb4 G4, the minor-9 stab."""
    ivs = list(ch['ivs'])
    if rootless and len(ivs) >= 5:
        ivs = ivs[1:]
    pcs = [(ch['root'] + iv) % 12 for iv in ivs]
    best, best_score = None, 1e9
    for r in range(len(pcs)):
        order = pcs[r:] + pcs[:r]
        stack = [order[0]]
        for pc in order[1:]:
            stack.append(stack[-1] + ((pc - stack[-1]) % 12 or 12))
        k = round((center - sum(stack) / len(stack)) / 12.0)
        stack = [s + 12 * k for s in stack]
        score = abs(sum(stack) / len(stack) - center) + 0.1 * (stack[-1] - stack[0])
        score += 1.5 * sum(1 for a, b in zip(stack, stack[1:]) if b - a == 1)
        if score < best_score:
            best, best_score = stack, score
    return [float(v) for v in best]


def in_range(pc, lo):
    """MIDI note of pitch class pc inside [lo, lo + 12)."""
    return float(lo + (pc - lo) % 12)


def parse_pattern(pat, keep_ties=True):
    """-> (steps, [(index, char)]) ; with keep_ties the '_' characters are returned too."""
    s = str(pat).replace(' ', '').replace('|', '')
    ev = [(i, c) for i, c in enumerate(s) if c not in '.-' and (keep_ties or c != '_')]
    return max(1, len(s)), ev


def pos_to_sec(p):
    """'bar.beat.16th' (1-based bar and beat, 0-based 16th; later parts optional) or seconds."""
    if isinstance(p, (int, float)):
        return float(p)
    parts = [float(v) for v in str(p).split('.')] + [1.0, 0.0]
    bar, beat, six = parts[0], parts[1], parts[2]
    return (bar - 1) * BAR + (beat - 1) * BEAT + six * S16


class Song:
    """The compiled arrangement: chord timeline and per-part hit lists."""

    def __init__(self, song, mute=(), solo=()):
        self.bars = song
        self.chords = []
        for bi, bd in enumerate(song):
            toks = str(bd.get('chords', '')).split() or ['.']
            for j, tok in enumerate(toks):
                t0 = bi * BAR + j * BAR / len(toks)
                if tok in ('.', '-', '_') and self.chords:
                    continue
                if tok in ('.', '-', '_'):
                    tok = 'Fm'
                self.chords.append((t0, parse_chord(tok)))
        self.mute, self.solo = set(mute), set(solo)

    def chord_at(self, t):
        cur = self.chords[0][1]
        for t0, ch in self.chords:
            if t0 <= t + 1e-9:
                cur = ch
            else:
                break
        return cur

    def audible(self, part):
        bus = 'drums' if part in DRUM_PARTS else 'tonal'
        return (part not in self.mute and bus not in self.mute
                and (not self.solo or part in self.solo or bus in self.solo))

    def hits(self, part):
        """All hits of a part: dicts t, vel, ch, length (s, ties included), bar, energy, i (index in bar)."""
        out = []
        for bi, bd in enumerate(self.bars):
            pat = bd.get(part)
            if not pat or part in bd.get('mute', ()) or not self.audible(part):
                continue
            steps, ev = parse_pattern(pat)
            st = BAR / steps
            notes = str(bd.get(part + '_notes', '')).split()
            k = 0
            for j, (i, ch) in enumerate(ev):
                if ch == '_':
                    continue
                ties = 0
                for i2, c2 in ev[j + 1:]:
                    if c2 == '_' and i2 == i + ties + 1:
                        ties += 1
                    else:
                        break
                t = bi * BAR + i * st
                if part in SWING_PARTS and steps % 16 == 0:
                    p16 = i * 16 / steps
                    if abs(p16 - round(p16)) < 1e-9 and int(round(p16)) % 2 == 1:
                        t += SWING * S16
                h = dict(t=t, vel=VEL.get(ch, 0.85), ch=ch, length=(1 + ties) * st, bar=bi,
                         energy=float(bd.get('energy', 1.0)), i=i, steps=steps)
                if notes:
                    h['note'] = note_midi(notes[k % len(notes)])
                k += 1
                out.append(h)
        return out

    def cut(self, part, t):
        bi = min(int(t // BAR), len(self.bars) - 1)
        c0, c1 = self.bars[bi].get(part + '_cut', (0.6, 0.6))
        u = (t - bi * BAR) / BAR
        return 120.0 * 100.0 ** (c0 + (c1 - c0) * u)


def render_parts(song, n):
    """Render every part of the arrangement into its own stereo bus + the mono send buses."""
    parts = {p: np.zeros((2, n)) for p in PARTS}
    sends = {k: np.zeros(n) for k in ('room', 'hall', 'delay')}
    cache = {}

    def once(key, fn):
        if key not in cache:
            cache[key] = fn()
        return cache[key]

    def place(part, buf, t, gain, energy=1.0):
        mx = MIX.get(part, {})
        g = undb(mx.get('gain', 0.0)) * gain
        buf = stereo(buf, mx.get('pan', 0.0))
        s = smp(t)
        mix_into(parts[part], buf, s, g)
        space = 1.35 - 0.5 * energy
        for k in ('room', 'hall', 'delay'):
            if mx.get(k):
                mix_into(sends[k], buf, s, g * mx[k] * (space if k != 'delay' else 1.0))

    def dyn(h):
        return h['vel'] * (0.8 + 0.2 * h['energy'])

    for h in song.hits('kick'):
        place('kick', once('kick', v_kick), h['t'], dyn(h), h['energy'])
    for j, h in enumerate(song.hits('clap')):
        place('clap', once(('clap', j % 3), lambda j=j: v_clap(j % 3)), h['t'], dyn(h), h['energy'])
    ch_hat = song.hits('hat')
    for j, h in enumerate(ch_hat):
        place('hat', once(('hat', j % 6), lambda j=j: v_hat(False, j % 6)), h['t'], dyn(h), h['energy'])
    closed_t = sorted(h['t'] for h in ch_hat)
    for j, h in enumerate(song.hits('ohat')):
        buf = once(('ohat', j % 4), lambda j=j: v_hat(True, j % 4)).copy()
        nxt = [c for c in closed_t if c > h['t'] + 1e-6]
        if nxt and nxt[0] - h['t'] < buf.shape[1] / SR:          # choke by the next closed hat
            s = smp(nxt[0] - h['t'])
            k = int(0.012 * SR)
            buf[:, s:s + k] *= np.linspace(1, 0, min(k, buf.shape[1] - s))
            buf[:, s + k:] = 0.0
        place('ohat', buf, h['t'], dyn(h), h['energy'])
    for j, h in enumerate(song.hits('shaker')):
        place('shaker', once(('shaker', j % 4), lambda j=j: v_shaker(j % 4, j % 2 == 0)), h['t'], dyn(h), h['energy'])
    for j, h in enumerate(song.hits('rim')):
        place('rim', once(('rim', j % 3), lambda j=j: v_rim(j % 3)), h['t'], dyn(h), h['energy'])
    for j, h in enumerate(song.hits('tick')):
        p = (1.0, 1.12, 0.94)[j % 3]
        place('tick', once(('tick', j % 3), lambda j=j, p=p: v_tick(p, j)), h['t'], dyn(h), h['energy'])
    toms = {'h': hz(48), 'm': hz(44), 'l': hz(41)}                 # C3 Ab2 F2
    for h in song.hits('tom'):
        c = h['ch'].lower()
        if c in toms:
            pan = {'h': 0.3, 'm': 0.0, 'l': -0.3}[c]
            buf = stereo(once(('tom', c), lambda c=c: v_tom(toms[c])), pan)
            place('tom', buf, h['t'], dyn(h), h['energy'])
    sn = song.hits('snare')
    for j, h in enumerate(sn):
        bd = song.bars[h['bar']]
        rise = float(bd.get('snare_rise', 0.0)) * (h['t'] - h['bar'] * BAR) / BAR
        tight = h['length'] < S16 * 1.01
        buf = v_snare(seed=j % 5, tight=tight, pitch=2.0 ** (rise / 12.0))
        place('snare', buf, h['t'], dyn(h), h['energy'])

    # sub: one continuous oscillator; notes = chord bass in F1..E2 unless sub_notes is given
    subs = []
    for h in song.hits('sub'):
        m = h.get('note', in_range(song.chord_at(h['t'] + 1e-6)['bass'], 29))
        subs.append((h['t'], h['t'] + h['length'], m, h['vel']))
    if subs:
        mix_into(parts['sub'], stereo(render_sub(subs, n)), 0, undb(MIX['sub'].get('gain', 0.0)))
    for j, h in enumerate(song.hits('bass')):
        m = h.get('note', in_range(song.chord_at(h['t'] + 1e-6)['bass'], 36))
        gate = max(0.05, h['length'] * 0.8)
        place('bass', v_bass(m, gate, h['vel'], seed=j), h['t'], 1.0, h['energy'])
    for j, h in enumerate(song.hits('stab')):
        ch = song.chord_at(h['t'] + 1e-6)
        notes = [h['note']] if 'note' in h else voicing(ch, 62.0)
        buf = v_stab(notes, song.cut('stab', h['t']), h['vel'], gate=min(h['length'], 0.12), seed=j)
        place('stab', buf, h['t'], 1.0, h['energy'])
    for j, h in enumerate(song.hits('saw')):
        ch = song.chord_at(h['t'] + 1e-6)
        v = voicing(ch, 64.0)
        notes = [h['note']] if 'note' in h else [v[0] - 12 + ((ch['root'] - v[0]) % 12)] + v
        buf = v_saw(notes, song.cut('saw', h['t']), h['vel'], gate=max(0.1, h['length'] * 0.9), seed=j)
        place('saw', buf, h['t'], 1.0, h['energy'])
    for j, h in enumerate(song.hits('pad')):
        ch = song.chord_at(h['t'] + 1e-6)
        root = in_range(ch['bass'], 41)
        notes = [root, root + 7] + voicing(ch, 65.0)
        length = min(h['length'] + 0.2, (n / SR) - h['t'])
        place('pad', v_pad(notes, length, seed=j), h['t'], 1.0, h['energy'])
    return parts, sends


def load_cues(path):
    """-> (scenes, fx cues, sound events). Missing / empty / invalid files give empty lists + a warning."""
    empty = ([], [], [])
    if not path or not os.path.exists(path):
        warn('cues file not found (%s): rendering the arrangement only' % path)
        return empty
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            txt = fh.read()
        data = json.loads(txt) if txt.strip() else {}
    except (OSError, ValueError) as e:
        warn('could not read %s (%s): rendering the arrangement only' % (path, e))
        return empty
    if not isinstance(data, dict):
        warn('%s is not a JSON object: ignored' % path)
        return empty
    if data.get('bpm') not in (None, BPM):
        warn('cues bpm %r != arrangement BPM %r: the picture grid is assumed to be %r' % (data.get('bpm'), BPM, BPM))
    if data.get('duration') not in (None, DURATION):
        warn('cues duration %r != %r: output stays %r s' % (data.get('duration'), DURATION, DURATION))

    def num(v, d):
        try:
            v = float(v)
            return v if math.isfinite(v) else d
        except (TypeError, ValueError):
            return d

    scenes = []
    for s in data.get('scenes') or []:
        if isinstance(s, dict):
            scenes.append(dict(id=str(s.get('id', '?')), start=num(s.get('start'), 0.0), end=num(s.get('end'), 0.0)))
    fx = []
    for c in data.get('fx') or []:
        if isinstance(c, dict) and isinstance(c.get('type'), str) and num(c.get('t'), None) is not None:
            fx.append(dict(c, t=num(c.get('t'), 0.0)))
    sounds = []
    for s in data.get('sounds') or []:
        if not isinstance(s, dict) or num(s.get('t'), None) is None:
            warn('malformed sound event ignored: %r' % (s,))
            continue
        sounds.append(dict(s, t=num(s.get('t'), 0.0)))
    return sorted(scenes, key=lambda s: s['start']), fx, sounds


def normalize_event(e, source):
    """Validate one sound event and fill defaults. Returns None (with a warning) if unusable."""
    typ = e.get('type')
    if typ not in SFX_TYPES and typ not in INTERNAL_SFX:
        warn('unknown sfx type %r at t=%s (%s): ignored' % (typ, e.get('t'), source))
        return None

    def num(k, d, lo, hi):
        try:
            v = float(e.get(k, d))
        except (TypeError, ValueError):
            v = d
        return float(np.clip(v if math.isfinite(v) else d, lo, hi))

    ev = dict(type=typ, t=float(e['t']), source=source, amt=num('amt', 1.0, 0.0, 2.0))
    ev['dur'] = num('dur', DEFAULT_DUR.get(typ, 0.3), 0.01, 10.0)
    ev['pitch'] = num('pitch', 1.0, 0.25, 4.0)
    ev['count'] = int(num('count', 6, 1, 400))
    ev['dir'] = 'down' if str(e.get('dir', 'up')).lower() == 'down' else 'up'
    ev['tone'] = str(e.get('tone', 'huge' if typ == 'impact' and ev['amt'] >= 1.3 else 'std'))
    if e.get('resume') is not None:
        ev['resume'] = num('resume', 0.0, 0.0, DURATION)
    if not (-ev['dur'] - 1.0 <= ev['t'] < DURATION):
        warn('sfx %s at t=%.3f is outside the reel: ignored' % (typ, ev['t']))
        return None
    ev['seed'] = '%s@%d' % (typ, int(round(ev['t'] * 1000)))
    ev['anchor'] = ev['t'] + (ev['dur'] if typ in ('whoosh', 'riser', 'reverse') else 0.0)
    ev['keep'] = bool(e.get('keep', False))
    return ev


def build_events(fx_cues, sounds, scenes):
    """Merge picture sfx, arrangement FX, scene sweeteners and R.cue reinforcements into one list."""
    pic = [ev for ev in (normalize_event(s, 'picture') for s in sounds) if ev]
    arr = []
    for p, typ, o in FX:
        o = dict(o)
        t = pos_to_sec(p)
        if o.pop('anchor', 'start') == 'end':
            t -= float(o.get('dur', DEFAULT_DUR.get(typ, 0.0)))
        ev = normalize_event(dict(o, t=t, type=typ), 'arrangement')
        if not ev:
            continue
        if not ev['keep'] and any(q['type'] == ev['type'] and abs(q['anchor'] - ev['anchor']) <= YIELD_WINDOW for q in pic):
            continue
        arr.append(ev)
    events = pic + arr
    anchors = [ev['anchor'] for ev in events] + [ev['t'] for ev in events]
    if SCENE_SWEETENER.get('enabled'):
        for sc in scenes:
            cut = sc['start']
            if cut <= 1e-6 or cut >= DURATION:
                continue
            if any(abs(a - cut) <= SCENE_SWEETENER.get('guard', 0.25) for a in anchors):
                continue
            typ = SCENE_SWEETENER.get('type', 'swish')
            lead = 0.11 if typ == 'swish' else float(SCENE_SWEETENER.get('dur', 0.3)) if typ == 'whoosh' else 0.0
            ev = normalize_event(dict(t=cut - lead, type=typ, amt=SCENE_SWEETENER.get('amt', 0.4),
                                      dur=SCENE_SWEETENER.get('dur', 0.3)), 'scene:' + sc['id'])
            if ev:
                events.append(ev)
    all_t = [ev['t'] for ev in events] + [ev['anchor'] for ev in events]
    for c in fx_cues:
        rule = FX_CUE_SOUNDS.get(c.get('type'))
        if not rule:
            continue
        try:
            amt = float(c.get('amt', CUE_AMT_DEFAULT.get(c.get('type'), 1.0)))
        except (TypeError, ValueError):
            continue
        if amt < rule.get('min_amt', 0.0) or any(abs(a - c['t']) <= DEDUPE_WINDOW for a in all_t):
            continue
        scale = {'shake': 1 / 14.0, 'chroma': 1 / 12.0}.get(c.get('type'), 1.0)
        ev = normalize_event(dict(t=c['t'], type=rule['sound'], amt=min(1.2, amt * scale)), 'fx:' + c['type'])
        if ev:
            events.append(ev)
    return sorted(events, key=lambda e: (e['t'], e['type'], e['source']))


# =====================================================================================================
# 5. MASTER + IO
# =====================================================================================================
def render(cues_path, mute=(), solo=(), verbose=True):
    t_start = time.time()
    n = N_FRAMES
    mute, solo = set(MUTE) | set(mute), set(SOLO) | set(solo)
    song = Song(SONG, mute, solo)
    scenes, fx_cues, sounds = load_cues(cues_path)
    events = build_events(fx_cues, sounds, scenes)

    parts, sends = render_parts(song, n)
    # sidechain: every part with a duck depth pumps against the kick
    env = duck_env(parts['kick'])
    for p, mx in MIX.items():
        if mx.get('duck'):
            parts[p] *= 10.0 ** (-mx['duck'] * env / 20.0)
    room = convolve(filt(sends['room'], ('hp', 250, 0.7)), make_ir('room', 0.9, 0.55, 0.3, predelay=0.006, er=0.5))
    hall = convolve(filt(sends['hall'], ('hp', 220, 0.7)), make_ir('hall', 2.6, 1.9, 0.8, predelay=0.022, er=0.3))
    dly = pingpong(sends['delay'], 0.75 * BEAT, feedback=0.42)
    space = 10.0 ** (-RETURN_DUCK * env / 20.0)
    hall *= undb(RETURNS['hall']) * space
    dly *= undb(RETURNS['delay']) * space
    room *= undb(RETURNS['room'])

    drums = sum(parts[p] for p in DRUM_PARTS) + room
    tonal = sum(parts[p] for p in ('sub', 'bass', 'stab', 'saw', 'pad')) + hall + dly
    for bi, bd in enumerate(song.bars):
        if bd.get('gate'):
            edit_gate(tonal, bi, bd['gate'])
    music = drums + tonal
    orig = music.copy()
    for bi, bd in enumerate(song.bars):
        if bd.get('stutter'):
            edit_stutter(music, orig, bi, bd['stutter'], rng_for('stutter', bi))

    # SFX bus + music-bus edits from the picture
    sfx = np.zeros((2, n))
    fxsend = np.zeros(n)
    counts = {}
    duck_trig = np.zeros(n)
    for ev in events:
        typ = ev['type']
        mx = SFX_MIX.get(typ, {})
        if typ in ('glitch', 'tapestop'):
            orig = music.copy()
            if typ == 'glitch':
                edit_glitch(music, orig, ev['t'], ev['dur'], rng_for('glitch', ev['seed']))
            else:
                edit_tapestop(music, orig, ev['t'], ev['dur'], ev.get('resume'))
        if typ == 'tapestop':
            counts[typ] = counts.get(typ, 0) + 1
            continue
        kw = dict(ev)
        kw.pop('type')
        if typ == 'reverse':
            kw['chord_notes'] = voicing(song.chord_at(ev['t'] + ev['dur'] + 1e-6), 64.0)
        buf, off = RENDERERS[typ](**kw)
        g = undb(mx.get('gain', 0.0))
        s = smp(ev['t'] + off)
        mix_into(sfx, buf, s, g)
        if mx.get('verb'):
            mix_into(fxsend, buf, s, g * mx['verb'])
        if mx.get('duck'):
            mix_into(duck_trig, np.full(1, mx['duck'] * ev['amt']), s)
        counts[typ] = counts.get(typ, 0) + 1
    fxverb = convolve(filt(fxsend, ('hp', 200, 0.7)), make_ir('fxverb', 2.6, 1.8, 0.8, predelay=0.015, er=0.2))
    sfx += fxverb * undb(RETURNS['fxverb'])
    if 'sfx' in mute or (solo and 'sfx' not in solo):
        sfx[:] = 0.0
        counts = {}
    # music dips under big hits (trigger -> 5 ms attack, 280 ms release, in dB)
    if duck_trig.any():
        d = iir(duck_trig, [onepole_ba(0.28)]) * (0.28 * SR)
        d = iir(d, [onepole_ba(0.005)])
        music *= 10.0 ** (-np.minimum(d, 9.0) / 20.0)

    mixbus = music + sfx
    stems = dict(kick=parts['kick'], drums=drums, tonal=tonal, music=music, sfx=sfx)
    master, info = master_chain(mixbus, verbose)
    info.update(counts=counts, events=events, scenes=scenes, render_s=time.time() - t_start)
    for k in stems:
        stems[k] = stems[k] * info['pregain']
    stems['master'] = master
    return master, stems, info


def master_chain(x, verbose=True):
    """HP 20 Hz, mono lows (M/S: side highpassed at 120 Hz), glue compressor, then drive into a 4x
    oversampled soft clipper and a true-peak limiter, drive iterated to TARGET_LUFS."""
    n = x.shape[-1]
    ef = int(END_FADE * SR)
    x = filt(x, ('hp', 20, 0.7), ('highshelf', 9000, 0.7, 1.0))
    m, s = 0.5 * (x[0] + x[1]), 0.5 * (x[0] - x[1])
    s = zerophase(s, lambda f: f ** 4 / (f ** 4 + 120.0 ** 4))
    x = np.stack([m + s, m - s])
    x[:, n - ef:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, ef + 1) / ef)
    pre = lufs(x)
    g0 = undb(-20.0 - pre) if pre > -69 else 1.0
    x = x * g0
    x, gr = compressor(x, thr_db=-17.0, ratio=1.8, attack=0.025, release=0.25, knee_db=8.0, rms_ms=25.0)
    ceiling = CEILING_DBTP - 0.15
    drive = float(np.clip(TARGET_LUFS - lufs(x), -20.0, 30.0))
    y = x
    for _ in range(6):
        y = soft_clip(x * undb(drive), ceiling=undb(ceiling + 1.2), knee=0.72)
        y, _ga = limiter(y, ceiling)
        cur = lufs(y)
        if abs(cur - TARGET_LUFS) < 0.03 or cur <= -69.0:
            break
        drive = float(np.clip(drive + TARGET_LUFS - cur, -20.0, 30.0))
    y[:, n - ef:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, ef + 1) / ef)
    y[:, -1] = 0.0
    fi = int(0.001 * SR)
    y[:, :fi] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(fi) / fi)
    tp = true_peak(y)
    if tp > undb(ceiling):
        y *= undb(ceiling) / tp
    return y, dict(pregain=g0 * undb(drive), drive_db=drive, glue_gr_max=float(-gr.min()), lufs_internal=lufs(y),
                   true_peak_db=todb(true_peak(y)), peak_db=todb(np.max(np.abs(y))))


def find_ffmpeg():
    for c in (os.environ.get('FFMPEG'), shutil.which('ffmpeg')):
        if c and os.path.exists(c):
            return c
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def ffmpeg_loudness(path):
    ff = find_ffmpeg()
    if not ff:
        return None
    try:
        r = subprocess.run([ff, '-hide_banner', '-nostats', '-i', path, '-af', 'loudnorm=print_format=json',
                            '-f', 'null', '-'], capture_output=True, text=True, timeout=120)
        blob = r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}') + 1]
        return json.loads(blob)
    except Exception as e:
        warn('ffmpeg loudness measurement failed: %s' % e)
        return None


def main(argv=None):
    global SEED
    ap = argparse.ArgumentParser(description='Render the showreel soundtrack (48 kHz / 24-bit / stereo).')
    ap.add_argument('--cues', default=os.path.join(ROOT, 'audio', 'cues.json'), help='cues.json from tools/cues.mjs')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist', 'soundtrack.wav'), help='output WAV')
    ap.add_argument('--stems', action='store_true', help='also write per-bus float WAVs to .cache/stems/')
    ap.add_argument('--mute', default='', help='comma list of parts/buses to mute (QA)')
    ap.add_argument('--solo', default='', help='comma list of parts/buses to solo (QA)')
    ap.add_argument('--seed', type=int, default=None, help='override SEED')
    ap.add_argument('--no-ffmpeg', action='store_true', help='skip the ffmpeg loudness check')
    a = ap.parse_args(argv)
    if a.seed is not None:
        SEED = a.seed
    split = [v.strip() for v in a.mute.split(',') if v.strip()], [v.strip() for v in a.solo.split(',') if v.strip()]
    master, stems, info = render(a.cues, *split)
    write_wav(a.out, master, 24)
    if a.stems:
        d = os.path.join(ROOT, '.cache', 'stems')
        for k, v in stems.items():
            write_wav(os.path.join(d, k + '.wav'), v, 32)
    meas = None if a.no_ffmpeg else ffmpeg_loudness(a.out)
    counts = info['counts']
    print('soundtrack  %s' % os.path.relpath(a.out))
    print('  duration  %.3f s  (%d samples @ %d Hz, 24-bit stereo)' % (master.shape[1] / SR, master.shape[1], SR))
    print('  peak      %.2f dBFS   true peak %.2f dBTP (4x)' % (info['peak_db'], info['true_peak_db']))
    if meas:
        print('  loudness  %s LUFS integrated, %s dBTP, LRA %s LU  (ffmpeg loudnorm)' % (
            meas.get('input_i'), meas.get('input_tp'), meas.get('input_lra')))
    print('  loudness  %.2f LUFS (internal BS.1770)   drive %+.1f dB, glue GR max %.1f dB' % (
        info['lufs_internal'], info['drive_db'], info['glue_gr_max']))
    print('  scenes    %d   sfx events %d: %s' % (len(info['scenes']), sum(counts.values()),
                                               ', '.join('%s %d' % kv for kv in sorted(counts.items())) or 'none'))
    src = {}
    for ev in info['events']:
        k = ev['source'].split(':')[0]
        src[k] = src.get(k, 0) + 1
    print('  sources   %s' % (', '.join('%s %d' % kv for kv in sorted(src.items())) or 'none'))
    print('  render    %.1f s%s' % (info['render_s'], ('   warnings: %d' % len(WARNINGS)) if WARNINGS else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
