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

QA: `python3 audio/synth.py --stems && python3 audio/qa.py` prints integrity / loudness / kick-grid / click
checks and writes waveform + spectrogram PNGs to .cache/audio-qa/.

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
import struct
import subprocess
import sys
import time
import zlib

import numpy as np

# =====================================================================================================
# 1. ARRANGEMENT: everything musical lives in this section. Re-map it to the storyboard by editing data.
# =====================================================================================================
# Re-mapping cheat sheet (all data, no DSP code):
#   - a bar's role / density / harmony ....... its dict in SONG (patterns, chords, level, hp/lp, gate, stutter)
#   - hits, risers, reverses, sweeps ......... FX (musical positions) or SCENE_FX (anchored to scene ids)
#   - balance ................................ MIX (music parts), RETURNS, SFX_MIX (picture sounds)
#   - quick A/B .............................. MUTE / SOLO here, or --mute / --solo on the command line
# The picture's own R.sfx events always play; a built-in FX of the same type within YIELD_WINDOW of one
# steps aside, so the defaults below never double up with the storyboard's hits.
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
HUMANIZE = 0.06                 # +- velocity variation (deterministic) on HUMANIZE_PARTS
HUMANIZE_PARTS = ('hat', 'ohat', 'shaker', 'rim', 'tick')

# Step patterns ----------------------------------------------------------------------------------------
# One string per part per bar. Its length sets the step size: 16 = 16ths, 8 = 8ths, 32 = 32nds,
# 12 = 8th-note triplets, 4 = quarters. Spaces and '|' are ignored (use them to group beats).
#   .  rest        x  hit (0.85)     X  accent (1.0)     o  soft (0.55)     g  ghost (0.3)
#   1-9  velocity 0.2 .. 1.0         _  tie: the previous note holds one more step (tonal parts)
#   tom: h m l = high / mid / low (uppercase = accent)
# Tonal parts (sub, boom, bass, stab, saw, pad, arp, pluck) play the chord of the moment. '<part>_notes'
# overrides the pitches with tokens cycled over that bar's hits: a note ('F2'), a stacked chord
# ('F3+Ab3+C4+G4') or '*' (the chord of the moment), e.g. bass_notes='F2 F2 Ab2 C3'.
#
# Per-bar keys
#   section     label (report only)           energy  0..1 macro: drum velocity, reverb amount
#   chords      'Fm9', or evenly spaced changes 'Fm9 . Dbmaj7 .' ('.' holds the previous chord)
#   <part>      step pattern for a part in PARTS
#   <part>_cut  (start, end) filter brightness 0..1 swept across the bar (0.5 = 1.2 kHz, 1.0 = 12 kHz)
#   <part>_opts voice options for that part in this bar (keyword arguments of its v_* voice, e.g. stab
#               bend / mode, saw spread / detune, pad attack / decay_db, boom drive / decay) plus mix
#               overrides: gain (dB offset), room / hall / delay (send levels)
#   gate        step pattern gating bass + synths + their reverb/delay (not sub / boom): x open, . shut
#   stutter     per-step edits of the whole music bus: 2 3 4 6 8 = retrigger the step's head N times,
#               r = reverse, b = replay the first step of the beat, x = mute, d = bitcrush, t = tape-slow,
#               p = the 8th before the step re-triggered in 32nds and bitcrushed
#   silence     step pattern of hard silence (x) on the music AND the sfx bus (reverb returns included).
#               Only swells (END_ANCHORED sounds) that land exactly where a silence ends pass through it.
#               silence_fade = seconds the sound takes to die into it (default 1.5 ms: it stops dead)
#   duck        0..1 depth of the kick sidechain in this bar (default 1)
#   level       music-bus level in dB for this bar (number, or (start, end) for a ramp); default 0
#   hp / lp     (start_hz, end_hz) highpass / lowpass sweep on the tonal bus (sub included) across the bar
#   mute        list of parts silenced in this bar           snare_rise  semitones a roll climbs over the bar
PARTS = ('kick', 'clap', 'snare', 'tom', 'hat', 'ohat', 'shaker', 'rim', 'tick', 'crash',
         'sub', 'boom', 'bass', 'stab', 'saw', 'pad', 'arp', 'pluck')
DRUM_PARTS = PARTS[:10]
LOW_PARTS = ('sub', 'boom')                                   # tonal low end: never gated
SYNTH_PARTS = ('bass', 'stab', 'saw', 'pad', 'arp', 'pluck')  # gated (with the hall / delay returns)

FOUR = 'x...x...x...x...'
CLAP = '....x.......x...'
OFFH = '..x...x...x...x.'
ROLL = 'oxXx oxXx oxXx oxXx'        # rolling 16th hats, accent on the off-8th

# The score follows STORYBOARD.md "Music plan, bar by bar". Times in the comments are the picture-lock
# hits; the picture's own R.sfx (cues.json) play on top and the FX below yield to them.
SONG = [
    dict(  # bar 1 · 0.000 s · COLD OPEN / AXIS: hits only, one per word, no groove
        #   0.0 LIGHT: kick (+ the picture's 'sub' impact) over quiet high-passed glassy 16ths F5 Ab5 C6 F6
        #   0.46875 HEAVY slam: kick + clap + distorted sub + low tom + room
        #   0.9375 NARROW: band-passed saw chord squeezing down 5 semitones in 0.1 s
        #   1.40625 WIDE: wide 7-voice supersaw Fm stab; its reverse-cymbal tail swells into the groove (FX)
        section='hook', energy=0.35, chords='Fm9', duck=0.0,
        kick='x...x...........', clap='....x...........', tom='....L...........',
        boom='....x...........', boom_opts=dict(drive=3.5, decay=0.2),
        pluck='gggg............', pluck_notes='F5 Ab5 C6 F6',
        stab='........X.......', stab_cut=(0.52, 0.52), stab_opts=dict(bend=-5.0, bend_time=0.1, mode='bp', gate=0.12),
        saw='............X...', saw_cut=(0.88, 0.88), saw_notes='F3+C4+F4+Ab4+C5',
        saw_opts=dict(spread=1.0, detune=0.38, gate=0.3, hall=0.4),
    ),
    dict(  # bar 2 · 1.875 s · GROOVE IN / TIMING: four-on-the-floor, off-8th closed hats, sub 8ths F1 F1 Ab1 C2,
        #   clap on 2 & 4 (2.34375 = the first landing, 3.28125 = notices the camera). The stab is thinned to
        #   three soft hits that dodge the landings (2.344 2.578 2.813 2.930 3.047 3.281) so the picture's
        #   plucks sit on top. Reverse swell 3.515625 -> 3.75 into the dive (picture; FX fallback).
        section='groove', energy=0.55, chords='Fm9 . Dbmaj7 .', level=-1.5,
        kick=FOUR, clap=CLAP, hat=OFFH,
        sub='x.x.x.x. x.x.x.x.', sub_notes='F1 F1 Ab1 C2',
        stab='o..o .... ...o ....', stab_cut=(0.40, 0.48),
    ),
    dict(  # bar 3 · 3.750 s · SPACE -> EASING: 3.75 sub boom + door (picture), pad Abmaj7 -> Eb at 4.6875, a 16th
        #   F-minor-pentatonic arp opening its filter, roll clunks (low tom + the picture's click) on 4.21875
        #   and 4.6875, riser 4.6875 -> 5.15625 cut clean (FX); from 5.15625 the drums thin: kick + rim + soft hat
        section='space', energy=0.65, chords='Abmaj7 . Eb .', level=-1.5,
        kick=FOUR, clap='....x...........', hat='.o.o .o.o .o.o ..g.', shaker='4242 4242 4242 ....',
        rim='.... .... .... x...', tom='.... l... l... ....',
        sub='x.x.x.x. x.x.....',
        pad='x_______ x_______', pad_opts=dict(attack=0.12, decay_db=10.0),
        arp='xxxx xxxx xxxx xxxx', arp_cut=(0.28, 0.80),
        arp_notes='F4 Ab4 C5 Eb5 F5 Eb5 C5 Ab4 Bb4 C5 Eb5 F5 Ab5 F5 Eb5 C5',
    ),
    dict(  # bar 4 · 5.625 s · EASING -> BREATH: kick on 1 (5.625 = cursor press), rim on 2 & 4, soft 16th hats,
        #   snare roll from 6.5625 (8ths, then 16ths from 6.796875) under the picture's noise + saw riser, a C
        #   chord on 7.03125 for the TAPE-STOP (picture tapestop 0.18 s; FX fallback) to dive. Then near-silence
        #   to 7.5: only the swells that land on the drop pass (reverse, reverse cymbal, sub inhale 30 -> 55 Hz)
        section='breath', energy=0.75, chords='Dbmaj7 . Csus4 C', level=(-2.0, -0.5), hp=(20, 380),
        kick='x...............', rim='....x.......x...', hat='gogo gogo gogo gogo',
        snare='.... .... 5.67 8...',
        sub='x.x.x.x. x.x.x...',
        pad='x_______ x___x___', pad_opts=dict(attack=0.06, decay_db=8.0),
        stab='.... .... .... x...', stab_cut=(0.62, 0.62),
        silence='.... .... .... ..xx', silence_fade=0.04,
    ),
    dict(  # bar 5 · 7.500 s · DROP / ENERGY: kick + crash under the picture's mega impact + sub drop, then the full
        #   groove: four-on-the-floor, clap 2 & 4, rolling accented 16th hats, pumping 8th sub, rolling mid bass,
        #   supersaw stabs on the off-8ths (Fm9 -> Dbmaj7) and a bright stab on the 8.4375 RANGE snap
        section='drop', energy=1.0, chords='Fm9 . Dbmaj7 .',
        kick=FOUR, clap=CLAP, crash='x...............', hat=ROLL, ohat=OFFH,
        sub='x.x.x.x. x.x.x.x.',
        bass='..x. ..xx ..x. ..xx', bass_notes='F2 F2 Ab2 Db2 Db2 F2',
        saw='..x. ..x. ..x. ..x.', saw_cut=(0.72, 0.80),
        stab='.... .... X... ....', stab_cut=(0.95, 0.95),
    ),
    dict(  # bar 6 · 9.375 s · RANGE I (C L A U): the groove continues under the picture's per-cut signatures (the
        #   9.375 halftone glitch crushes the downbeat stab); snare fill in 16ths 11.015625 -> 11.25
        section='range', energy=1.0, chords='Dbmaj7 . Eb .',
        kick=FOUR, clap='....x.......x.xx', hat=ROLL, ohat=OFFH,
        snare='.... .... .... ..xX',
        sub='x.x.x.x. x.x.x.x.',
        bass='..x. ..xx ..x. ..xx', bass_notes='Db2 Db2 F2 Eb2 Eb2 G2',
        saw='..x. ..x. ..x. ..x.', saw_cut=(0.76, 0.84),
        stab='x... .... .... ....', stab_cut=(0.80, 0.80),
    ),
    dict(  # bar 7 · 11.250 s · RANGE II -> SQUEEZE: 11.25 the previous 8th re-triggered in 32nds + crushed (stutter p),
        #   11.484375 stab + snare, F Ab C plucks on 11.71875 / 11.8359375 / 11.953125 that the picture's row-pop
        #   glitches stutter, buffer repeat on 12.0703125 (stutter b), 12.1875 big Fm(add9) stab + clap.
        #   12.65625 drums out: a 32nd snare roll under the riser, the sub inhale and the final swell (FX); the
        #   last 16th (13.0078125 -> 13.125) is total silence except the swell peaking into the final hit
        section='squeeze', energy=1.0, chords='Fm9 . Fmadd9 Eb', snare_rise=4,
        kick='x...x...x.......', clap='....x...x.......', hat='oxXx oxXx oxXx ....', ohat='..x...x...x.....',
        snare='....x... ........ ........ 6789XX..',
        sub='x.x.x.x. x.x.....',
        bass='.xxx .xxx .xxx ....', bass_notes='F2 F2 F3',
        stab='..X. .... .... ....', stab_cut=(0.90, 0.90),
        arp='.... XXX. .... ....', arp_notes='F5 Ab5 C6', arp_cut=(0.85, 0.85),
        saw='.... .... X... ....', saw_notes='F3+Ab3+C4+G4+C5', saw_cut=(0.90, 0.90),
        gate='xxxx xxxx xxxx xxx.',
        stutter='pp.. ...b .... ....',
        silence='.... .... .... ...x',
    ),
    dict(  # bar 8 · 13.125 s · FINAL HIT + TAIL: kick + crash + a wide Fm(add9) supersaw stab into a long hall under
        #   the picture's massive impact (40 Hz boom) + sub drop; the pad sustains and decays to ~-42 dB by the
        #   end. No drums after the hit.
        section='resolve', energy=0.2, chords='Fmadd9', duck=0.0,
        kick='x...............', crash='X...............',
        saw='X...............', saw_notes='F3+Ab3+C4+G4+C5', saw_cut=(0.78, 0.78),
        saw_opts=dict(gate=0.5, spread=1.0, detune=0.34, hall=0.75),
        pad='x_______________',
    ),
]

# Arrangement FX: same vocabulary and options as R.sfx (plus the internal 'revcym' and 'inhale'), and
# 'verb' to override the FX-reverb send. Position: 'bar.beat.16th' (1-based bar and beat, 0-based 16th) or
# seconds. anchor='end' makes the position the landing / peak point (riser, reverse, whoosh, revcym,
# inhale) instead of the start. Each one steps aside if the picture declares the same type within
# YIELD_WINDOW of its anchor (set 'keep': True to always play it), so every hit the storyboard gives to the
# picture is listed here as a fallback and is heard exactly once.
FX = [
    ('1.1.0', 'impact', dict(amt=0.8, tone='sub')),               # 0.0 LIGHT cold-open impact
    ('1.2.0', 'impact', dict(amt=1.0)),                           # 0.46875 HEAVY slam
    ('1.4.0', 'impact', dict(amt=0.55)),                          # 1.40625 WIDE
    ('2.1.0', 'revcym', dict(dur=BEAT, anchor='end', amt=0.8)),   # WIDE's reverse-cymbal tail into the groove
    ('3.1.0', 'reverse', dict(dur=2 * S16, anchor='end')),        # dive swell 3.515625 -> 3.75
    ('3.1.0', 'impact', dict(amt=0.7, tone='sub')),               # 3.75 sub boom
    ('3.4.0', 'riser', dict(dur=BEAT, anchor='end', verb=0.0)),   # 4.6875 -> 5.15625, cut clean (no verb tail)
    ('4.4.0', 'riser', dict(dur=BEAT, anchor='end')),             # noise + saw riser over the snare roll
    ('4.4.0', 'tapestop', dict(dur=0.18)),                        # 7.03125 tape-stop of the music bus
    ('5.1.0', 'reverse', dict(dur=BEAT, anchor='end')),           # reversed-impact swell into the drop
    ('5.1.0', 'revcym', dict(dur=BEAT, anchor='end')),            # reverse cymbal into the drop
    ('5.1.0', 'inhale', dict(dur=BEAT, anchor='end')),            # sub inhale 30 -> 55 Hz into the drop
    ('5.1.0', 'impact', dict(amt=1.2, tone='huge')),              # 7.5 THE DROP
    ('5.1.0', 'subdrop', dict(amt=1.0)),
    ('5.1.0', 'shimmer', dict(dur=2 * BEAT, amt=0.6)),            # particle glitter
    ('5.2.0', 'impact', dict(amt=0.5)),                           # 7.96875 secondary impact
    ('5.3.0', 'reverse', dict(dur=S16, anchor='end')),            # 8.3203 -> 8.4375 zip into the bright stab
    ('6.1.0', 'whoosh', dict(dur=2 * S16, anchor='end', dir='down')),  # 9.140625 whip R -> L into 9.375
    ('7.4.3', 'riser', dict(dur=3 * S16, anchor='end')),          # 12.65625 -> 13.0078125, stops dead
    ('7.4.3', 'inhale', dict(dur=3 * S16, anchor='end')),         # sub inhale, stops dead with it
    ('8.1.0', 'reverse', dict(dur=BEAT, anchor='end')),           # the final swell: the only sound in the gap
    ('8.1.0', 'impact', dict(amt=1.3, tone='huge')),              # 13.125 FINAL HIT
    ('8.1.0', 'subdrop', dict(amt=1.0)),
    ('8.1.0', 'shimmer', dict(dur=1.6, amt=0.5)),
]

# Mix table. gain in dB; pan -1..1; room/hall/delay = send levels (linear); duck = sidechain depth in dB
# (keyed to the kick part). Parts are normalized one-shots, so gains are the whole level story.
MIX = {
    'kick':   dict(gain=0.0),
    'clap':   dict(gain=0.5, room=0.30, hall=0.05),
    'snare':  dict(gain=-9.0, room=0.30, hall=0.08),
    'tom':    dict(gain=-7.0, room=0.30, hall=0.06),
    'hat':    dict(gain=-11.0, pan=0.18, room=0.06),
    'ohat':   dict(gain=-13.0, pan=0.18, room=0.08, duck=2.0),
    'shaker': dict(gain=-16.0, pan=-0.30, room=0.10),
    'rim':    dict(gain=-6.5, pan=-0.22, room=0.12, delay=0.30),
    'tick':   dict(gain=-8.0, pan=0.25, room=0.10, delay=0.45),
    'crash':  dict(gain=-10.0, room=0.10, hall=0.12),
    'sub':    dict(gain=-8.0, duck=12.0),
    'boom':   dict(gain=-4.0, room=0.15),
    'bass':   dict(gain=-1.5, duck=6.0),
    'stab':   dict(gain=-4.0, hall=0.30, delay=0.50, duck=3.0),
    'saw':    dict(gain=-2.5, hall=0.25, delay=0.15, duck=4.5),
    'pad':    dict(gain=1.0, hall=0.40, duck=2.0),
    'arp':    dict(gain=-9.0, pan=0.15, hall=0.20, delay=0.40, duck=3.0),
    'pluck':  dict(gain=-6.0, hall=0.30, delay=0.45),
}
RETURNS = dict(room=-6.0, hall=-4.0, delay=-6.0, fxverb=-7.0)   # return levels, dB
RETURN_DUCK = 3.0               # sidechain depth (dB) on the hall/delay returns: the space pumps too
DUCK_SHAPE = 1.8                # ducking = depth * key_envelope ** DUCK_SHAPE (>1: snappier recovery)
MUTE = []                       # parts or buses to silence, e.g. ['saw', 'sfx']  (buses: drums tonal sfx)
SOLO = []                       # if not empty only these parts / buses play

# Picture-driven sound design (R.sfx vocabulary + internal sounds). gain dB, verb = send to the FX reverb,
# duck = dB the music dips under the hit.
SFX_MIX = {
    'impact':   dict(gain=-2.0, verb=0.22, duck=3.0),
    'whoosh':   dict(gain=-4.0, verb=0.18),
    'swish':    dict(gain=-4.0, verb=0.12),
    'click':    dict(gain=-8.0, verb=0.06),
    'tick':     dict(gain=-9.0, verb=0.06),
    'pop':      dict(gain=-14.0, verb=0.08),
    'blip':     dict(gain=-17.0, verb=0.15),
    'glitch':   dict(gain=-11.0, verb=0.04),
    'riser':    dict(gain=-4.0, verb=0.22),
    'reverse':  dict(gain=-3.0, verb=0.10),
    'subdrop':  dict(gain=-15.0, duck=2.0),
    'shimmer':  dict(gain=-13.0, verb=0.55),
    'type':     dict(gain=-8.0, verb=0.05),
    'tapestop': dict(gain=0.0),
    'revcym':   dict(gain=-8.0, verb=0.08),
    'inhale':   dict(gain=-6.0),
    'air':      dict(gain=-17.0, verb=0.35),
    'thump':    dict(gain=-10.0),
    'zap':      dict(gain=-19.0, verb=0.05),
}
# R.cue reinforcement. min_amt uses the cue's own units (flash 0..1, shake px, chroma px).
FX_CUE_SOUNDS = {
    'flash':  dict(sound='air', min_amt=0.8),
    'shake':  dict(sound='thump', min_amt=6.0),
    'chroma': dict(sound='zap', min_amt=8.0),
    'invert': dict(sound='zap', min_amt=0.0),
}
CUE_AMT_DEFAULT = dict(flash=1.0, shake=12.0, chroma=8.0, invert=1.0)   # engine.js defaults
SCENE_SWEETENER = dict(enabled=True, type='swish', amt=0.6, guard=0.25)   # on every scene cut after 0,
#                               unless any sound event (picture, FX, SCENE_FX) sits within `guard` s of it
# Scene-anchored sounds, keyed by the scene ids in cues.json (ids not present are ignored). Anchor: 'start',
# 'end', or seconds after the scene start; opts as in FX (anchor='end' = the sound lands on that point).
SCENE_FX = {
    # 's05-energy': [('start', 'impact', dict(amt=1.0))],
    # 's07-range-2': [('end', 'riser', dict(dur=BAR, anchor='end'))],
}
DEDUPE_WINDOW = 0.030           # an R.cue reinforcement is dropped if any sound event is this close
YIELD_WINDOW = 0.12             # arrangement FX yield to a same-type picture event this close
PASS_WINDOW = 0.03              # a swell passes a silence if it lands this close to the silence's end
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
INTERNAL_SFX = ('revcym', 'inhale', 'air', 'thump', 'zap')    # arrangement swells + R.cue reinforcements
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


def dc_block(x, r=0.9995):
    """Classic DC blocker y[n] = x[n] - x[n-1] + r*y[n-1] (corner ~ (1 - r) * SR / 2pi = 3.8 Hz at 48 kHz)."""
    return iir(x, [(np.array([1.0, -1.0]), np.array([1.0, -r]))])


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
    gg = 10.0 ** (gdb / 20.0)
    gg = np.concatenate([np.full(L, gg[0]), gg])       # a hit on sample 0 is already limited
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
    hdr = b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE'
    hdr += b'fmt ' + struct.pack('<IHHIIHH', 16, *fmt)
    hdr += b'data' + struct.pack('<I', len(data))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(hdr)
        fh.write(data)


def read_wav(path):
    """Minimal reader for the files this script writes (PCM 16/24/32, float 32). -> (channels, n), sr."""
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
def v_kick(seed=0, length=0.42, f_hi=185.0, f_lo=F1, tau_p=0.030, decay=0.09, hold=0.012, click=0.33,
           drive=2.0):
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
    x = filt(src * env, ('hp', 750, 0.7), ('peak', 1200, 1.3, 7.0), ('peak', 2800, 1.0, 2.0), ('lp', 7500, 0.6),
             ('lp', 9000, 0.7))
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
    x = filt(x, ('hp', 6800, 0.75), ('hp', 6800, 0.75), ('peak', 10500, 1.0, 1.5), ('lp', 16000, 0.7))
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


CRASH_OSC = (412.0, 537.0, 611.0, 727.0, 853.0, 941.0, 1091.0, 1247.0, 1406.0, 1673.0)


def v_crash(seed=0, length=2.0, tau=0.5):
    """Crash cymbal: ten inharmonic squares (their upper partials make the shimmer) + decorrelated noise,
    highpassed hard, a bright splash that dies in ~60 ms over a wash decaying with time constant tau."""
    n = int(length * SR)
    t = tvec(n)
    rng = rng_for('crash', seed)
    metal = sum(square(f * rng.uniform(0.99, 1.01), n, rng.random()) for f in CRASH_OSC) / len(CRASH_OSC)
    x = 0.5 * metal[None, :] + 0.8 * noise_st(rng, n, 0.3)
    x = filt(x, ('hp', 3000, 0.7), ('hp', 3000, 0.7), ('peak', 6200, 0.8, 3.0), ('lp', 15500, 0.7))
    env = (1.0 - np.exp(-t / 0.0012)) * (0.62 * np.exp(-t / tau) + 0.38 * np.exp(-t / 0.06))
    return norm(fades(x * env, 0.0002, min(0.3, 0.25 * length)))


# ---- tonal voices -------------------------------------------------------------------------------------
def v_boom(midi, length=0.6, vel=1.0, seed=0, drive=2.5, decay=0.25, bend=0.6, **_):
    """Tuned 808-style sub hit: sine with a fast downward pitch blip, exponential decay, driven into tanh
    (drive > 3 = the distorted sub of the SLAM: strong odd harmonics that read on small speakers)."""
    n = int(max(length, 5.0 * decay) * SR)
    t = tvec(n)
    f = hz(midi) * (1.0 + bend * np.exp(-t / 0.025))
    x = sine(f) * (1.0 - np.exp(-t / 0.0015)) * np.exp(-t / decay)
    x = np.tanh(drive * x) / math.tanh(drive)
    x = filt(x, ('hp', 28, 0.7), ('lp', 2200, 0.7))
    return norm(fades(x, 0.0003, 0.03), vel)


def v_pluck(midi, vel=1.0, seed=0, hp=450.0, decay=0.16, **_):
    """Glassy pluck: 1:2 FM bell whose index collapses in ~35 ms, an inharmonic glint (x3.76) and a
    highpass so it floats above everything (the bar-1 LIGHT bed)."""
    n = int((5.0 * decay + 0.02) * SR)
    t = tvec(n)
    f = hz(midi)
    rng = rng_for('pluck', midi, seed)
    idx = 1.6 * np.exp(-t / 0.035)
    x = np.sin(TAU * f * t + idx * np.sin(TAU * 2.0 * f * t)) * np.exp(-t / decay)
    x += 0.22 * np.sin(TAU * 3.76 * f * t + rng.uniform(0.0, TAU)) * np.exp(-t / 0.018)
    x *= 1.0 - np.exp(-t / 0.0006)
    x = filt(x, ('hp', hp, 0.7))
    return norm(fades(x, 0.0002, 0.02), vel)


def v_arp(midi, cut, vel=1.0, gate=0.07, seed=0, **_):
    """Arp pluck: two detuned saws + a sub-octave square through a resonant lowpass with a snappy envelope
    on top of the bar's cutoff sweep (arp_cut opens the filter across the bar)."""
    n = int((gate + 0.25) * SR)
    t = tvec(n)
    f = hz(midi)
    rng = rng_for('arp', seed)
    x = saw(f * 2 ** (-5 / 1200), n, rng.random()) + saw(f * 2 ** (5 / 1200), n, rng.random())
    x += 0.5 * square(f / 2.0, n, rng.random())
    fc = np.minimum(cut * (1.0 + 2.5 * vel * np.exp(-t / 0.035)), 15000.0)
    y = svf(x, fc, q=1.4) * adsr(n, 0.001, 0.09, 0.0, 0.05, gate)
    y = filt(np.tanh(1.2 * y), ('hp', 180, 0.7))
    return norm(fades(y, 0.0005, 0.01), vel)


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


def v_stab(notes, cut, vel=1.0, gate=0.1, seed=0, bend=0.0, bend_time=0.1, mode='lp', q=None, **_):
    """Hook chord stab: per note two detuned saws (split L/R) + a centered square; resonant lowpass whose
    cutoff opens with velocity and snaps shut; pluck envelope. bend = semitones the chord slides over
    bend_time; mode 'bp' = band-passed at `cut` (the NARROW squeeze: the band follows the bend down)."""
    n = int((gate + 0.45) * SR)
    t = tvec(n)
    rng = rng_for('stab', seed)
    br = 2.0 ** (bend * np.minimum(t / max(bend_time, 1e-3), 1.0) ** 0.7 / 12.0) if bend else 1.0
    x = np.zeros((2, n))
    for m in notes:
        f = hz(m) * br
        a = saw(f * 2 ** (-9 / 1200), n, rng.random())
        b = saw(f * 2 ** (9 / 1200), n, rng.random())
        c = 0.35 * square(f, n, rng.random())
        x[0] += a + 0.35 * b + c
        x[1] += b + 0.35 * a + c
    env = adsr(n, 0.0012, 0.14, 0.0, 0.08, gate)
    if mode == 'bp':
        fc = np.minimum(cut * br * (1.0 + 0.8 * vel * np.exp(-t / 0.03)), 16000.0)
        y = svf(x, fc, q=q or 2.4, mode='bp') * env
        y = filt(np.tanh(2.2 * y), ('hp', 220, 0.7))
    else:
        fc = np.minimum(cut * (1.0 + 3.0 * vel * np.exp(-t / 0.05)), 16000.0)
        y = svf(x, fc, q=q or 0.95) * env
        y = filt(np.tanh(1.3 * y), ('hp', 170, 0.7), ('peak', 320, 1.0, -2.5))
    return norm(fades(y, 0.0005, 0.01), vel)


def v_saw(notes, cut, vel=1.0, gate=0.2, seed=0, voices=7, detune=0.30, spread=0.9, **_):
    """Drop chord: 7-voice supersaw per note, wide, filter envelope, sustained body."""
    n = int((gate + 0.4) * SR)
    t = tvec(n)
    rng = rng_for('saw', seed)
    x = supersaw([hz(m) for m in notes], n, voices=int(voices), detune=detune, spread=spread, rng=rng)
    fc = np.minimum(cut * (1.0 + 1.6 * np.exp(-t / 0.12)), 17000.0)
    y = svf(x, fc, q=0.8) * adsr(n, 0.003, 0.25, 0.55, 0.16, gate)
    y = filt(y, ('hp', 190, 0.7), ('peak', 320, 1.0, -2.5))
    return norm(fades(y, 0.001, 0.01), vel)


def v_pad(notes, length, seed=0, attack=0.018, decay_db=42.0, **_):
    """Pad: 5-voice supersaw per note + a sine on the root, slowly closing filter, a raised attack, held
    briefly, then decaying exponentially by decay_db over its window (42 = the resolve pad that is about
    -42 dB at the end of the reel; ~8 = a sustained bed). attack = seconds to ~95 %."""
    n = int(length * SR)
    t = tvec(n)
    rng = rng_for('pad', seed)
    x = supersaw([hz(m) for m in notes], n, voices=5, detune=0.16, spread=1.0, rng=rng)
    x += 0.25 * sine(hz(notes[0]), n)[None, :]
    fc = 600.0 + 3000.0 * np.exp(-t / (0.3 * length))
    y = svf(x, fc, q=0.7)
    hold = min(0.25, 0.2 * length)
    tau = max(0.05, (length - hold - 0.08) / math.log(10 ** (max(decay_db, 0.5) / 20)))
    env = np.where(t < hold, 1.0, np.exp(-np.maximum(t - hold, 0.0) / tau))
    y *= env * (1.0 - np.exp(-t / max(attack, 1e-4) * 3.0))
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
    x = np.tanh(1.7 * (x + 0.15 * x * x)) / math.tanh(1.7)     # asymmetric -> even harmonics (and DC)
    return dc_block(x) * a


# ---- R.sfx vocabulary -----------------------------------------------------------------------------------
# Each renderer returns (stereo buffer, offset seconds relative to the event time t).
def s_impact(amt=1.0, tone='std', seed=0, **_):
    """Layered hit: kick transient + sub boom (F1) + swept noise burst + body thud + a faint metallic
    clang, glued with saturation and a short built-in room."""
    huge, subby = tone == 'huge', tone == 'sub'
    n = int((2.0 if huge else 1.6) * SR)
    t = tvec(n)
    rng = rng_for('impact', seed)
    kick = np.zeros(n)
    k = v_kick(seed=seed, length=0.9, f_hi=165.0, f_lo=F1 * 0.97, tau_p=0.04, decay=0.28 if huge else 0.2,
               hold=0.03, click=0.45, drive=2.6)
    kick[:k.shape[0]] = k
    boom = sine(F1 * (1 + 0.45 * np.exp(-t / 0.05))) * (1 - np.exp(-t / 0.003)) * np.exp(-t / (0.38 if huge else 0.3))
    boom = np.tanh(1.8 * boom) / math.tanh(1.8)
    nz = svf(noise_st(rng, n, 0.5), 600.0 + 9500.0 * np.exp(-t / (0.16 if huge else 0.11)), q=0.75)
    nz = norm(nz) * (1 - np.exp(-t / 0.0015)) * (0.75 * np.exp(-t / 0.09) + 0.25 * np.exp(-t / (0.4 if huge else 0.3)))
    thud = norm(filt(rng.standard_normal(n), ('bp', 120, 1.2))) * np.exp(-t / 0.08)
    clang = sum(np.sin(TAU * f * t + rng.uniform(0, TAU)) * np.exp(-t / d)
                for f, d in ((233, 0.5), (377, 0.35), (611, 0.25), (947, 0.18), (1433, 0.12))) / 3.0
    clang *= 1 - np.exp(-t / 0.002)
    w = (dict(k=0.5, b=1.0, n=0.18, t=0.25, c=0.0) if subby else
         dict(k=1.0, b=0.6, n=0.75, t=0.4, c=0.14) if huge else dict(k=0.9, b=0.8, n=0.55, t=0.35, c=0.07))
    mono = w['k'] * kick + w['b'] * boom + w['t'] * thud + w['c'] * clang
    x = mono[None, :] + w['n'] * nz
    x = x + 0.3 * norm(convolve(x, make_ir('impact-room', 0.9, 0.8, 0.45, predelay=0.006))) * np.max(np.abs(x))
    x = np.tanh(1.2 * x) / math.tanh(1.2)
    return norm(fades(x, 0.0003, 0.55 * n / SR), amt), 0.0


def s_whoosh(dur=0.3, dir='up', amt=1.0, seed=0, lo=320.0, hi=5200.0, **_):
    """Air movement that swells to its peak at t + dur: stereo noise through a swept resonant bandpass
    (+ a lowpassed body layer), panning across, short tail after the peak."""
    dur = float(np.clip(dur, *DUR_RANGE['whoosh']))
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
    air = svf(nz, fc, q=1.6, mode='bp') + 0.35 * filt(svf(nz, fc * 0.3, q=0.7), ('hp', 90, 0.7))
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


POP_BASE = hz(65)               # F4 = pitch 1.0 for pop and blip: the storyboard's landing plucks F4 Ab4 C5 F5
#                                 are pitch 1, 1.189, 1.498, 2 and its F6 full-stop tick is blip pitch 4


def s_pop(pitch=1.0, amt=1.0, seed=0, **_):
    """Woody 'bloop' pluck on F4 * pitch: a sine that chirps up into its note in ~10 ms, a marimba-like
    x3.98 partial, a soft low thud and a tick of noise."""
    n = int(0.24 * SR)
    t = tvec(n)
    rng = rng_for('pop', seed)
    f0 = POP_BASE * pitch
    f = f0 * (1.0 - 0.4 * np.exp(-t / 0.007))
    x = sine(f) * (1 - np.exp(-t / 0.0006)) * np.exp(-t / 0.06)
    x += 0.3 * np.sin(TAU * 3.98 * f0 * t) * np.exp(-t / 0.012)
    x += 0.35 * norm(filt(rng.standard_normal(n), ('lp', 260, 0.7))) * np.exp(-t / 0.006)
    x += 0.15 * norm(filt(rng.standard_normal(n), ('hp', 3000, 0.7))) * np.exp(-t / 0.0006)
    return stereo(norm(fades(x, 0.0002, 0.02), amt)), 0.0


def s_blip(pitch=1.0, amt=1.0, seed=0, **_):
    """UI blip on F4 * pitch: sine + 2nd / 3rd harmonics with a hair of upward bend; the higher the blip
    the shorter and purer it is (pitch 4 = the clean ~40 ms F6 tick of the full stop)."""
    n = int(0.14 * SR)
    t = tvec(n)
    f = POP_BASE * pitch * (1 + 0.03 * (1 - np.exp(-t / 0.02)))
    h = 1.0 / max(1.0, pitch)
    x = (sine(f) + 0.3 * h * sine(2 * f) + 0.1 * h * sine(3 * f)) * (1 - np.exp(-t / 0.002))
    x *= np.exp(-t / (0.045 / math.sqrt(max(1.0, pitch))))
    return stereo(norm(fades(x, 0.0005, 0.01), amt)), 0.0


def s_glitch_layer(dur=0.2, amt=1.0, seed=0, pitch=1.0, pitched=False, **_):
    """The SFX-bus half of a glitch (the music-bus buffer-repeat is edit_glitch): gated bandpassed noise
    chopped at 64ths + short square zaps, bitcrushed. With an explicit pitch the zaps are tuned to
    F5 * pitch (the row pops rise F -> Ab -> C) instead of random falling ones."""
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
        if pitched:
            z = square(hz(77) * pitch, m, 0.0) * 0.5
        else:
            z = square(f * (1 - 0.4 * tvec(m) / max(m / SR, 1e-3)), m, 0.0) * 0.5
        mix_into(out, stereo(fades(z, 0.001, 0.003), rng.uniform(-0.5, 0.5)), s)
    out = crush(out, bits=int(rng.integers(5, 8)), down=int(rng.integers(3, 8)))
    return norm(fades(out, 0.002, 0.004), amt), 0.0


def s_riser(dur=BAR, amt=1.0, seed=0, **_):
    """Tension build ending at t + dur: noise through a bandpass sweeping 250 Hz -> 11 kHz with rising
    resonance and width, plus a supersaw gliding up two octaves under an accelerating tremolo."""
    dur = float(np.clip(dur, *DUR_RANGE['riser']))
    n = int(dur * SR)
    t = tvec(n)
    rng = rng_for('riser', seed)
    x = t / dur
    fc = 250.0 * (11000.0 / 250.0) ** (x ** 1.4)
    nz = noise_st(rng, n, 0.6)
    nzf = svf(nz, fc, q=0.8 + 2.2 * x * x, mode='bp') + 0.25 * filt(svf(nz, fc * 0.5, q=0.7), ('hp', 150, 0.7))
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
    dur = float(np.clip(dur, *DUR_RANGE['reverse']))
    rng = rng_for('reverse', seed)
    notes = chord_notes or [56, 60, 63, 67]
    src = v_stab(notes, 5000.0, vel=1.0, gate=0.12, seed=seed).mean(axis=0)
    hit = norm(filt(rng.standard_normal(int(0.08 * SR)), ('hp', 3000, 0.7))) * np.exp(-tvec(int(0.08 * SR)) / 0.015)
    src[:hit.shape[0]] += 0.5 * hit
    ir = make_ir('reverse', dur + 0.6, 3.0, 1.8, predelay=0.0, hp=250, lp=12000, er=0.0, onset=0.006)
    wet = convolve(src, ir, keep_tail=True)[:, ::-1]
    env = np.convolve(np.abs(wet).max(axis=0), np.ones(240) / 240, mode='same')
    tail = wet.shape[1] - int(0.3 * SR)                        # end the swell at its loudest point
    wet = wet[:, :tail + int(np.argmax(env[tail:])) + 1]
    m = int(dur * SR)
    seg = wet[:, -m:] if wet.shape[1] >= m else np.pad(wet, ((0, 0), (m - wet.shape[1], 0)))
    seg = seg * (np.linspace(0.0, 1.0, m) ** 1.5)
    return norm(fades(seg, 0.01, 0.003), amt), 0.0


def s_revcym(dur=0.47, amt=1.0, seed=0, **_):
    """Reverse cymbal landing at t + dur: a crash whose decay spans the swell, time-reversed, so it rises
    ~35 dB into the landing point and stops on it."""
    dur = float(np.clip(dur, *DUR_RANGE['revcym']))
    m = int(dur * SR)
    cr = v_crash(seed=seed, length=dur + 0.05, tau=dur / 4.0)[:, ::-1]
    seg = cr[:, -m:] * np.linspace(0.0, 1.0, m) ** 1.2
    return norm(fades(seg, 0.005, 0.002), amt), 0.0


def s_inhale(dur=0.47, amt=1.0, seed=0, f0=30.0, f1=55.0, **_):
    """Sub 'inhale' landing at t + dur: a sine sweeping f0 -> f1 Hz that swells into the landing point,
    driven for small-speaker harmonics, with a breath of rising band-passed air; it stops dead there."""
    dur = float(np.clip(dur, *DUR_RANGE['inhale']))
    n = int(dur * SR)
    t = tvec(n)
    x = t / dur
    rng = rng_for('inhale', seed)
    body = np.tanh(2.4 * sine(f0 * (f1 / f0) ** x)) / math.tanh(2.4) * x ** 1.6
    air = norm(svf(rng.standard_normal(n), 250.0 * 6.0 ** x, q=1.2, mode='bp')) * 0.12 * x ** 2.5
    y = filt(body + air, ('hp', 22, 0.7))
    return stereo(norm(fades(y, 0.004, 0.004), amt)), 0.0


def s_subdrop(amt=1.0, seed=0, **_):
    """808-style sub drop: sine falling from F2 towards F1 / 33 Hz, saturated for audible harmonics, with a
    long raised-cosine release so it is gone within 1.5 s."""
    n = int(1.5 * SR)
    t = tvec(n)
    f = 33.0 + (hz(41) - 33.0) * np.exp(-t / 0.28)
    x = sine(f) * (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.4)
    x = filt(np.tanh(2.0 * x) / math.tanh(2.0), ('lp', 500, 0.7), ('hp', 24, 0.7))
    return stereo(norm(fades(x, 0.0005, 0.6), amt)), 0.0


def s_shimmer(dur=0.9, amt=1.0, seed=0, **_):
    """Airy sparkle: random high sine grains on the F minor pentatonic (C6..A#7), random pans."""
    dur = float(np.clip(dur, *DUR_RANGE['shimmer']))
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
        g *= rng.uniform(0.35, 1.0) * (1.0 - tg / dur) ** 1.6
        mix_into(out, stereo(g, rng.uniform(-0.9, 0.9)), smp(tg))
    return norm(fades(out, 0.002, 0.15), amt), 0.0


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
                 shimmer=s_shimmer, type=s_type, revcym=s_revcym, inhale=s_inhale, air=s_air, thump=s_thump,
                 zap=s_zap)
DEFAULT_DUR = dict(whoosh=0.3, swish=0.15, glitch=0.2, riser=BAR, reverse=0.47, shimmer=0.9, type=0.3,
                   tapestop=0.3, revcym=0.47, inhale=0.47)
# (min, max) dur in seconds, shared by the renderers and normalize_event so the scheduled anchor always matches
# the rendered sound. END_ANCHORED types land at t + dur: a longer request keeps its landing point and starts
# later instead (the quiet first part of the build is dropped).
DUR_RANGE = dict(whoosh=(0.05, 10.0), riser=(0.1, 10.0), reverse=(0.05, 10.0), shimmer=(0.05, 10.0),
                 revcym=(0.05, 10.0), inhale=(0.05, 10.0))
DUR_RANGE_DEFAULT = (0.01, 10.0)
END_ANCHORED = ('whoosh', 'riser', 'reverse', 'revcym', 'inhale')


# ---- music-bus edits ----------------------------------------------------------------------------------
def splice(bus, s0, seg, xf=48, xf_out=None):
    """Replace bus[:, s0:s0+len(seg)] with seg, raised-cosine crossfading xf samples at the start and
    xf_out (default xf) at the end, where the original signal fades back in."""
    n = seg.shape[-1]
    a, b = max(0, s0), min(bus.shape[-1], s0 + n)
    if b <= a:
        return
    seg = seg[:, a - s0:b - s0]
    m = b - a
    w = np.ones(m)
    for k, head in ((min(xf, m // 2), True), (min(xf if xf_out is None else xf_out, m // 2), False)):
        if k > 0:
            r = 0.5 - 0.5 * np.cos(np.pi * (np.arange(k) + 0.5) / k)
            if head:
                w[:k] = r
            else:
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
        elif ch == 'p':                               # the 8th before this step, re-triggered in 32nds + crushed
            p0 = s0 - smp(2 * S16)
            if p0 < 0:
                continue
            seg = tile_grain(orig[:, p0:p0 + max(2, n // 2)], n)
            seg = 0.45 * seg + 0.55 * crush(seg, bits=7, down=4)
        elif ch == 't':
            seg = tape_read(orig, s0, n, n / SR * 1.6) * np.linspace(1, 0.3, n)
        else:
            continue
        splice(bus, s0, seg, xf=48)


def edit_gate(bus, bar_i, pattern, xf=0.002):
    """Trance gate for one bar: per-step gain (x = open, . = shut, digits / o / g = partial), every edge
    smoothed over xf seconds, open (1.0) on both sides of the bar so the bar boundaries never dip."""
    steps, hits = parse_pattern(pattern, keep_ties=False)
    st = BAR / steps
    k = max(2, int(xf * SR))
    L = smp(BAR)
    g = np.ones(L + 2 * k)
    g[k:k + L] = 0.0
    for i, ch in hits:
        g[k + smp(i * st):k + smp((i + 1) * st)] = 1.0 if ch in 'xX' else VEL.get(ch, 1.0)
    g = np.convolve(np.pad(g, (k // 2, k - 1 - k // 2), mode='edge'), np.ones(k) / k, mode='valid')
    s0 = smp(bar_i * BAR) - k
    a, b = max(0, s0), min(bus.shape[1], s0 + g.shape[0])
    if b > a:
        bus[:, a:b] *= g[a - s0:b - s0]


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


def tapestop_resume(t, dur):
    """Where the music comes back after a tape-stop: the first beat at or after the stop's end."""
    return math.ceil((t + dur) / BEAT - 1e-6) * BEAT


def edit_tapestop(bus, orig, t, dur, resume=None):
    """Pitch-down stop of the music bus over dur, then silence until `resume` (default: next beat)."""
    s0 = smp(t)
    n = max(2, int(dur * SR))
    if s0 >= bus.shape[1]:
        return
    if resume is None:
        resume = tapestop_resume(t, dur)
    seg = np.zeros((2, max(n, smp(resume) - s0)))      # tape-read, then silence until the resume point
    seg[:, :n] = tape_read(orig, max(0, s0), n, dur)
    k = int(0.3 * n)
    seg[:, n - k:n] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, k + 1) / k)
    splice(bus, s0, seg, xf=96, xf_out=int(0.004 * SR))


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
        score += 6.0 * sum(1 for a, b in zip(stack, stack[1:]) if b - a == 1)     # QA: was 1.5, too weak to avoid them
        if score < best_score:
            best, best_score = stack, score
    return [float(v) for v in best]


def in_range(pc, lo):
    """MIDI note of pitch class pc inside [lo, lo + 12)."""
    return float(lo + (pc - lo) % 12)


def parse_notes(tok):
    """A '<part>_notes' token -> list of MIDI notes: 'F2' -> [41.0], 'F3+Ab3+C4' -> a stacked chord,
    '*' -> None (play the chord of the moment)."""
    tok = str(tok).strip()
    if tok in ('*', ''):
        return None
    return [note_midi(v) for v in tok.split('+')]


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
            notes = [parse_notes(v) for v in str(bd.get(part + '_notes', '')).split()]
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
                if notes and notes[k % len(notes)]:
                    h['notes'] = notes[k % len(notes)]
                k += 1
                out.append(h)
        return out

    def opts(self, part, bar):
        """The bar's '<part>_opts' split into (voice keyword arguments, mix overrides)."""
        o = dict(self.bars[bar].get(part + '_opts') or {})
        mix = {k: o.pop(k) for k in MIX_OPTS if k in o}
        return o, mix

    def cut(self, part, t):
        bi = min(int(t // BAR), len(self.bars) - 1)
        c0, c1 = self.bars[bi].get(part + '_cut', (0.6, 0.6))
        u = (t - bi * BAR) / BAR
        return 120.0 * 100.0 ** (c0 + (c1 - c0) * u)


BAR_KEYS = {'section', 'energy', 'chords', 'level', 'hp', 'lp', 'gate', 'stutter', 'mute', 'snare_rise',
            'silence', 'silence_fade', 'duck'}
MIX_OPTS = ('gain', 'pan', 'room', 'hall', 'delay')          # '<part>_opts' keys that are mix overrides
PATTERN_CHARS = dict(part=set('.-_xXog123456789'), tom=set('.-_hmlHML'), gate=set('.-xXog123456789'),
                     stutter=set('.-234568rbxdtp'), silence=set('.-xX'))


def check_song(song):
    """Warn (never fail) about ARRANGEMENT typos that would otherwise be silently ignored or misread:
    unknown bar keys, unknown pattern characters, muting a part that does not exist, bar count."""
    if len(song) != BARS:
        warn('SONG has %d bars but BARS = %d (the file stays %.3f s)' % (len(song), BARS, DURATION))
    known = (BAR_KEYS | set(PARTS) | {p + '_cut' for p in PARTS} | {p + '_notes' for p in PARTS}
             | {p + '_opts' for p in PARTS})
    for bi, bd in enumerate(song):
        for k, v in bd.items():
            if k not in known:
                warn('SONG bar %d: unknown key %r ignored' % (bi + 1, k))
                continue
            if k.endswith('_opts') and not isinstance(v, dict):
                warn('SONG bar %d: %s must be a dict' % (bi + 1, k))
            if k.endswith('_notes'):
                for tok in str(v).split():
                    try:
                        parse_notes(tok)
                    except ValueError as e:
                        warn('SONG bar %d: %s: %s' % (bi + 1, k, e))
            kind = ('tom' if k == 'tom' else 'part' if k in PARTS else
                    k if k in ('gate', 'stutter', 'silence') else None)
            if kind:
                bad = sorted(set(str(v).replace(' ', '').replace('|', '')) - PATTERN_CHARS[kind])
                if bad:
                    warn('SONG bar %d: %s pattern %r has unknown characters %s' % (bi + 1, k, v, ''.join(bad)))
        for p in bd.get('mute', ()):
            if p not in PARTS:
                warn('SONG bar %d: mute %r is not a part' % (bi + 1, p))


def epoch_of(cuts, t):
    """Index of the epoch a sound triggered at t belongs to (cuts = sorted resume points of hard stops) and
    the time it has to be gone by (the next resume point, or None)."""
    e = int(np.searchsorted(np.asarray(cuts, float), t + 1e-9, side='right')) if len(cuts) else 0
    return e, (cuts[e] if e < len(cuts) else None)


def kill_after(buf, s, kill, fade=0.002):
    """buf placed at sample s, silent from time `kill` on (a raised-cosine fade that ends there): what was
    playing before a hard stop (tape-stop, silence) never comes back after it. Copies only when it cuts."""
    if kill is None:
        return buf
    end = smp(kill) - s
    if end >= buf.shape[-1]:
        return buf
    out = buf.copy()
    if end <= 0:
        return out * 0.0
    f = min(int(fade * SR), end)
    out[..., end:] = 0.0
    out[..., end - f:end] *= 0.5 + 0.5 * np.cos(np.pi * (np.arange(f) + 1) / f)
    return out


def render_parts(song, n, cuts=()):
    """Render every part of the arrangement into its own stereo bus + the mono send buses, one set of sends
    per epoch (content triggered between two hard stops); every hit is cut at the next resume point."""
    parts = {p: np.zeros((2, n)) for p in PARTS}
    sends = [{k: np.zeros(n) for k in ('room', 'hall', 'delay')} for _ in range(len(cuts) + 1)]
    cache = {}

    def once(key, fn):
        if key not in cache:
            cache[key] = fn()
        return cache[key]

    def place(part, buf, t, gain, energy=1.0, over=None):
        mx = dict(MIX.get(part, {}), **(over or {}))
        g = undb(MIX.get(part, {}).get('gain', 0.0) + float((over or {}).get('gain', 0.0))) * gain
        s = smp(t)
        e, kill = epoch_of(cuts, t)
        buf = kill_after(stereo(buf, mx.get('pan', 0.0)), s, kill)
        mix_into(parts[part], buf, s, g)
        space = 1.35 - 0.5 * energy
        for k in ('room', 'hall', 'delay'):
            if mx.get(k):
                mix_into(sends[e][k], buf, s, g * mx[k] * (space if k != 'delay' else 1.0))

    def dyn(h, part=None):
        v = h['vel'] * (0.8 + 0.2 * h['energy'])
        if part in HUMANIZE_PARTS:
            v *= 1.0 + HUMANIZE * (2.0 * rng_for('hum', part, h['bar'], h['i']).random() - 1.0)
        return v

    def chord_notes(h, default):
        """Explicit '<part>_notes' pitches of a hit, else default(chord of the moment)."""
        return h['notes'] if h.get('notes') else default(song.chord_at(h['t'] + 1e-6))

    for h in song.hits('kick'):
        place('kick', once('kick', v_kick), h['t'], dyn(h), h['energy'], song.opts('kick', h['bar'])[1])
    for j, h in enumerate(song.hits('clap')):
        place('clap', once(('clap', j % 3), lambda j=j: v_clap(j % 3)), h['t'], dyn(h), h['energy'],
              song.opts('clap', h['bar'])[1])
    ch_hat = song.hits('hat')
    for j, h in enumerate(ch_hat):
        place('hat', once(('hat', j % 6), lambda j=j: v_hat(False, j % 6)), h['t'], dyn(h, 'hat'), h['energy'],
              song.opts('hat', h['bar'])[1])
    closed_t = sorted(h['t'] for h in ch_hat)
    for j, h in enumerate(song.hits('ohat')):
        buf = once(('ohat', j % 4), lambda j=j: v_hat(True, j % 4)).copy()
        nxt = [c for c in closed_t if c > h['t'] + 1e-6]
        if nxt and nxt[0] - h['t'] < buf.shape[1] / SR:          # choke by the next closed hat
            s = smp(nxt[0] - h['t'])
            k = int(0.012 * SR)
            buf[:, s:s + k] *= np.linspace(1, 0, min(k, buf.shape[1] - s))
            buf[:, s + k:] = 0.0
        place('ohat', buf, h['t'], dyn(h, 'ohat'), h['energy'], song.opts('ohat', h['bar'])[1])
    for j, h in enumerate(song.hits('shaker')):
        place('shaker', once(('shaker', j % 4), lambda j=j: v_shaker(j % 4, j % 2 == 0)), h['t'], dyn(h, 'shaker'),
              h['energy'], song.opts('shaker', h['bar'])[1])
    for j, h in enumerate(song.hits('rim')):
        place('rim', once(('rim', j % 3), lambda j=j: v_rim(j % 3)), h['t'], dyn(h, 'rim'), h['energy'],
              song.opts('rim', h['bar'])[1])
    for j, h in enumerate(song.hits('tick')):
        p = (1.0, 1.12, 0.94)[j % 3]
        place('tick', once(('tick', j % 3), lambda j=j, p=p: v_tick(p, j)), h['t'], dyn(h, 'tick'), h['energy'],
              song.opts('tick', h['bar'])[1])
    for j, h in enumerate(song.hits('crash')):
        vo, over = song.opts('crash', h['bar'])
        key = ('crash', j % 2) + tuple(sorted(vo.items()))
        place('crash', once(key, lambda j=j, vo=vo: v_crash(j % 2, **vo)), h['t'], dyn(h), h['energy'], over)
    toms = {'h': hz(48), 'm': hz(44), 'l': hz(41)}                 # C3 Ab2 F2
    for h in song.hits('tom'):
        c = h['ch'].lower()
        if c in toms:
            pan = {'h': 0.3, 'm': 0.0, 'l': -0.3}[c]
            buf = stereo(once(('tom', c), lambda c=c: v_tom(toms[c])), pan)
            place('tom', buf, h['t'], dyn(h), h['energy'], song.opts('tom', h['bar'])[1])
    sn = song.hits('snare')
    for j, h in enumerate(sn):
        bd = song.bars[h['bar']]
        rise = float(bd.get('snare_rise', 0.0)) * (h['t'] - h['bar'] * BAR) / BAR
        tight = h['length'] < S16 * 1.01
        buf = v_snare(seed=j % 5, tight=tight, pitch=2.0 ** (rise / 12.0))
        place('snare', buf, h['t'], dyn(h), h['energy'], song.opts('snare', h['bar'])[1])

    # sub: one continuous oscillator; notes = chord bass in F1..E2 unless sub_notes is given
    subs = []
    for h in song.hits('sub'):
        m = h['notes'][0] if h.get('notes') else in_range(song.chord_at(h['t'] + 1e-6)['bass'], 29)
        g = undb(float(song.opts('sub', h['bar'])[1].get('gain', 0.0)))
        kill = epoch_of(cuts, h['t'])[1]
        subs.append((h['t'], min(h['t'] + h['length'], kill if kill is not None else DURATION), m, h['vel'] * g))
    if subs:
        mix_into(parts['sub'], stereo(render_sub(subs, n)), 0, undb(MIX['sub'].get('gain', 0.0)))
    for j, h in enumerate(song.hits('boom')):
        vo, over = song.opts('boom', h['bar'])
        m = h['notes'][0] if h.get('notes') else in_range(song.chord_at(h['t'] + 1e-6)['bass'], 29)
        place('boom', v_boom(m, h['length'], h['vel'], seed=j, **vo), h['t'], 1.0, h['energy'], over)
    for j, h in enumerate(song.hits('bass')):
        vo, over = song.opts('bass', h['bar'])
        m = h['notes'][0] if h.get('notes') else in_range(song.chord_at(h['t'] + 1e-6)['bass'], 36)
        gate = max(0.05, h['length'] * 0.8)
        place('bass', v_bass(m, gate, h['vel'], seed=j), h['t'], 1.0, h['energy'], over)
    for j, h in enumerate(song.hits('stab')):
        vo, over = song.opts('stab', h['bar'])
        notes = chord_notes(h, lambda ch: voicing(ch, 62.0))
        vo = dict(dict(gate=min(h['length'], 0.12)), **vo)
        buf = v_stab(notes, song.cut('stab', h['t']), h['vel'], seed=j, **vo)
        place('stab', buf, h['t'], 1.0, h['energy'], over)
    for j, h in enumerate(song.hits('saw')):
        vo, over = song.opts('saw', h['bar'])

        def with_root(ch):
            v = voicing(ch, 64.0)
            return [v[0] - 12 + ((ch['root'] - v[0]) % 12)] + v
        notes = chord_notes(h, with_root)
        vo = dict(dict(gate=max(0.1, h['length'] * 0.9)), **vo)
        buf = v_saw(notes, song.cut('saw', h['t']), h['vel'], seed=j, **vo)
        place('saw', buf, h['t'], 1.0, h['energy'], over)
    for j, h in enumerate(song.hits('pad')):
        vo, over = song.opts('pad', h['bar'])
        ch = song.chord_at(h['t'] + 1e-6)
        root = in_range(ch['bass'], 41)
        notes = h['notes'] if h.get('notes') else [root, root + 7] + voicing(ch, 65.0)
        length = min(h['length'] + 0.2, (n / SR) - h['t'])
        place('pad', v_pad(notes, length, seed=j, **vo), h['t'], 1.0, h['energy'], over)
    for part, spread in (('arp', 0.2), ('pluck', 0.35)):
        for j, h in enumerate(song.hits(part)):
            vo, over = song.opts(part, h['bar'])
            if h.get('notes'):
                m = h['notes'][0]
            else:
                v = voicing(song.chord_at(h['t'] + 1e-6), 72.0)
                m = v[h['i'] % len(v)]
            if part == 'arp':
                buf = v_arp(m, song.cut('arp', h['t']), h['vel'], seed=j, **dict(dict(gate=min(h['length'], 0.07)), **vo))
            else:
                buf = v_pluck(m, h['vel'], seed=j, **vo)
            place(part, stereo(buf, spread * (1 if j % 2 else -1)), h['t'], 1.0, h['energy'], over)
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
        if not txt.strip():
            warn('cues file %s is empty: rendering the arrangement only' % path)
            return empty
        data = json.loads(txt)
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
    lo, hi = DUR_RANGE.get(typ, DUR_RANGE_DEFAULT)
    dur = num('dur', DEFAULT_DUR.get(typ, 0.3), lo, 1e4)
    if dur > hi and typ in END_ANCHORED:     # keep the landing point, start later
        ev['t'] += dur - hi
    ev['dur'] = min(dur, hi)
    ev['pitch'] = num('pitch', 1.0, 0.25, 4.0)
    ev['count'] = int(num('count', 6, 1, 400))
    ev['dir'] = 'down' if str(e.get('dir', 'up')).lower() == 'down' else 'up'
    ev['tone'] = str(e.get('tone', 'huge' if typ == 'impact' and ev['amt'] >= 1.3 else 'std'))
    ev['pitched'] = e.get('pitch') is not None
    if e.get('resume') is not None:
        ev['resume'] = num('resume', 0.0, 0.0, DURATION)
    if e.get('verb') is not None:                # per-event FX-reverb send override (0 = dry, e.g. a clean cut)
        ev['verb'] = num('verb', 0.0, 0.0, 2.0)
    if not (-ev['dur'] - 1.0 <= ev['t'] < DURATION):
        warn('sfx %s at t=%.3f is outside the reel: ignored' % (typ, ev['t']))
        return None
    ev['seed'] = '%s@%d' % (typ, int(round(ev['t'] * 1000)))
    ev['anchor'] = ev['t'] + (ev['dur'] if typ in END_ANCHORED else 0.0)
    ev['keep'] = bool(e.get('keep', False))
    return ev


def build_events(fx_cues, sounds, scenes, yielded=None):
    """Merge picture sfx, arrangement FX, scene sweeteners and R.cue reinforcements into one list. Arrangement
    FX that step aside for a picture event are appended to `yielded` (if given) as (fx event, picture event)."""
    pic = [ev for ev in (normalize_event(s, 'picture') for s in sounds) if ev]

    def rival(ev):
        return next((q for q in pic if q['type'] == ev['type'] and abs(q['anchor'] - ev['anchor']) <= YIELD_WINDOW),
                    None)
    arr = []
    for p, typ, o in FX:
        o = dict(o)
        t = pos_to_sec(p)
        if o.pop('anchor', 'start') == 'end':
            t -= float(o.get('dur', DEFAULT_DUR.get(typ, 0.0)))
        ev = normalize_event(dict(o, t=t, type=typ), 'arrangement')
        if not ev:
            continue
        q = None if ev['keep'] else rival(ev)
        if q is not None:
            if yielded is not None:
                yielded.append((ev, q))
            continue
        arr.append(ev)
    ids = {sc['id']: sc for sc in scenes}
    for sid, items in SCENE_FX.items():
        sc = ids.get(sid)
        if sc is None:
            continue
        for where, typ, o in items:
            o = dict(o)
            t = sc['start'] if where == 'start' else sc['end'] if where == 'end' else sc['start'] + float(where)
            if o.pop('anchor', 'start') == 'end':
                t -= float(o.get('dur', DEFAULT_DUR.get(typ, 0.0)))
            ev = normalize_event(dict(o, t=t, type=typ), 'scene-fx:' + sid)
            if not ev:
                continue
            q = None if ev['keep'] else rival(ev)
            if q is None:
                arr.append(ev)
            elif yielded is not None:
                yielded.append((ev, q))
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
    reinforced = []
    for c in sorted(fx_cues, key=lambda c: c['t']):
        rule = FX_CUE_SOUNDS.get(c.get('type'))
        if not rule:
            continue
        try:
            amt = float(c.get('amt', CUE_AMT_DEFAULT.get(c.get('type'), 1.0)))
        except (TypeError, ValueError):
            continue
        if amt < rule.get('min_amt', 0.0) or any(abs(a - c['t']) <= DEDUPE_WINDOW for a in all_t):
            continue
        if any(s == rule['sound'] and abs(a - c['t']) <= DEDUPE_WINDOW for s, a in reinforced):
            continue                                 # two cues of one kind in a row: one layer, not two
        scale = {'shake': 1 / 14.0, 'chroma': 1 / 12.0}.get(c.get('type'), 1.0)
        ev = normalize_event(dict(t=c['t'], type=rule['sound'], amt=min(1.2, amt * scale)), 'fx:' + c['type'])
        if ev:
            events.append(ev)
            reinforced.append((rule['sound'], c['t']))
    return sorted(events, key=lambda e: (e['t'], e['type'], e['source']))


# =====================================================================================================
# 5. MASTER + IO
# =====================================================================================================
def bar_curve(song, key, n, idle, log=False, ramp=0.01):
    """Per-sample automation from a per-bar key: a number holds for the bar, (start, end) ramps across
    it (geometric if log). Bars without the key sit at `idle`. Changes complete by each downbeat (a short
    forward-looking smoothing), so a new value is already in place when the bar's first hit lands.
    Returns None if no bar uses the key."""
    if not any(key in bd for bd in song.bars):
        return None
    cur = np.full(n, float(idle))
    for bi, bd in enumerate(song.bars):
        if key not in bd:
            continue
        v = bd[key]
        a, b = (v, v) if isinstance(v, (int, float)) else (float(v[0]), float(v[1]))
        s0, s1 = smp(bi * BAR), min(n, smp((bi + 1) * BAR))
        u = np.arange(s1 - s0) / max(1, s1 - s0)
        cur[s0:s1] = a * (b / a) ** u if log and a > 0 and b > 0 else a + (b - a) * u
    w = max(1, int(ramp * SR))
    c = np.concatenate([[0.0], np.cumsum(np.concatenate([cur, np.full(w, cur[-1])]))])
    return (c[w:w + n] - c[:n]) / w


def silence_spans(song):
    """[(t0, t1, fade)] from the per-bar 'silence' patterns; consecutive silent steps merge into one span."""
    spans = []
    for bi, bd in enumerate(song.bars):
        if not bd.get('silence'):
            continue
        steps, hits = parse_pattern(bd['silence'], keep_ties=False)
        st = BAR / steps
        fade = float(bd.get('silence_fade', 0.0015))
        for i, ch in hits:
            if ch not in 'xX':
                continue
            t0, t1 = bi * BAR + i * st, bi * BAR + (i + 1) * st
            if spans and abs(spans[-1][1] - t0) < 1e-9:
                spans[-1] = (spans[-1][0], t1, spans[-1][2])
            else:
                spans.append((t0, t1, fade))
    return spans


def silence_mask(spans, n):
    """Gain curve: 0 inside every span, 1 elsewhere. The sound dies over `fade` seconds that end exactly
    where the span starts (it stops dead on the grid) and comes back over 0.5 ms from the span's end."""
    m = np.ones(n)
    for t0, t1, fade in spans:
        s0, s1 = max(0, smp(t0)), min(n, smp(t1))
        k = max(1, int(fade * SR))
        a = max(0, s0 - k)
        ramp = 0.5 + 0.5 * np.cos(np.pi * (np.arange(a, s0) - (s0 - k) + 1) / k)
        m[a:s0] = np.minimum(m[a:s0], ramp)
        m[s0:s1] = 0.0
        r = min(int(0.0005 * SR), n - s1)
        if r > 0:
            m[s1:s1 + r] = np.minimum(m[s1:s1 + r], 0.5 - 0.5 * np.cos(np.pi * (np.arange(r) + 0.5) / r))
    return m


def render(cues_path, mute=(), solo=()):
    t_start = time.time()
    n = N_FRAMES
    mute, solo = set(MUTE) | set(mute), set(SOLO) | set(solo)
    check_song(SONG)
    song = Song(SONG, mute, solo)
    scenes, fx_cues, sounds = load_cues(cues_path)
    yielded = []
    events = build_events(fx_cues, sounds, scenes, yielded)
    spans = silence_spans(song)
    # hard stops: nothing triggered before a resume point sounds after it (the drop and the final hit start
    # clean). Music bus: tape-stop resumes + silence ends; sfx bus: silence ends only.
    stops = [ev.get('resume') or tapestop_resume(ev['t'], ev['dur']) for ev in events if ev['type'] == 'tapestop']
    music_cuts = sorted(set([t1 for _, t1, _ in spans] + stops))
    sfx_cuts = sorted(set(t1 for _, t1, _ in spans))

    parts, sends = render_parts(song, n, music_cuts)
    # sidechain: every part with a duck depth pumps against the kick (per-bar 'duck' scales the depth)
    env = duck_env(parts['kick']) ** DUCK_SHAPE
    dk = bar_curve(song, 'duck', n, 1.0)
    if dk is not None:
        env = env * np.clip(dk, 0.0, 1.0)
    for p, mx in MIX.items():
        if mx.get('duck'):
            parts[p] *= 10.0 ** (-mx['duck'] * env / 20.0)
    room, hall, dly = np.zeros((2, n)), np.zeros((2, n)), np.zeros((2, n))
    for e, snd in enumerate(sends):              # each epoch's space dies at the next hard stop
        kill = music_cuts[e] if e < len(music_cuts) else None
        if snd['room'].any():
            room += kill_after(convolve(filt(snd['room'], ('hp', 250, 0.7)),
                                        make_ir('room', 0.9, 0.55, 0.3, predelay=0.006, er=0.5, lp=9000.0)), 0, kill)
        if snd['hall'].any():
            hall += kill_after(convolve(filt(snd['hall'], ('hp', 220, 0.7)),
                                        make_ir('hall', 2.6, 1.9, 0.8, predelay=0.022, er=0.3, lp=10000.0)), 0, kill)
        if snd['delay'].any():
            dly += kill_after(pingpong(snd['delay'], 0.75 * BEAT, feedback=0.42), 0, kill)
    space = 10.0 ** (-RETURN_DUCK * env / 20.0)
    hall *= undb(RETURNS['hall']) * space
    dly *= undb(RETURNS['delay']) * space
    room *= undb(RETURNS['room'])

    drums = sum(parts[p] for p in DRUM_PARTS) + room
    synths = sum(parts[p] for p in SYNTH_PARTS) + hall + dly
    for bi, bd in enumerate(song.bars):          # the trance gate chops synths + space, never the sub
        if bd.get('gate'):
            edit_gate(synths, bi, bd['gate'])
    tonal = sum(parts[p] for p in LOW_PARTS) + synths
    for key, mode, idle in (('hp', 'hp', 10.0), ('lp', 'lp', 20000.0)):
        curve = bar_curve(song, key, n, idle, log=True)
        if curve is not None:
            tonal = svf(tonal, curve, q=0.75, mode=mode)
    music = drums + tonal
    level = bar_curve(song, 'level', n, 0.0)
    if level is not None:
        music *= 10.0 ** (level / 20.0)
    orig = music.copy()
    for bi, bd in enumerate(song.bars):
        if bd.get('stutter'):
            edit_stutter(music, orig, bi, bd['stutter'], rng_for('stutter', bi))

    # SFX bus + music-bus edits from the picture. Swells that land where a silence ends go to sfx_pass,
    # which the silence mask leaves alone (the gap before the final hit holds only its reverse swell).
    sfx = np.zeros((2, n))
    sfx_pass = np.zeros((2, n))
    fxsend = [np.zeros(n) for _ in range(len(sfx_cuts) + 1)]
    counts = {}
    duck_trig = np.zeros(n)
    for ev in events:
        ev['passes'] = ev['type'] in END_ANCHORED and any(abs(ev['anchor'] - t1) <= PASS_WINDOW for _, t1, _ in spans)
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
        e, kill = epoch_of(sfx_cuts, ev['t'] + off)
        if not ev['passes']:
            buf = kill_after(buf, s, kill)
        mix_into(sfx_pass if ev['passes'] else sfx, buf, s, g)
        verb = ev.get('verb', mx.get('verb'))
        if verb:
            mix_into(fxsend[e], buf, s, g * verb)
        if mx.get('duck'):
            mix_into(duck_trig, np.full(1, mx['duck'] * ev['amt']), s)
        counts[typ] = counts.get(typ, 0) + 1
    fxverb = np.zeros((2, n))
    for e, snd in enumerate(fxsend):
        if snd.any():
            kill = sfx_cuts[e] if e < len(sfx_cuts) else None
            fxverb += kill_after(convolve(filt(snd, ('hp', 200, 0.7)),
                                          make_ir('fxverb', 2.6, 1.8, 0.8, predelay=0.015, er=0.2)), 0, kill)
    sfx += fxverb * undb(RETURNS['fxverb'])
    if 'sfx' in mute or (solo and 'sfx' not in solo):
        sfx[:] = 0.0
        sfx_pass[:] = 0.0
        counts = {}
    # music dips under big hits (trigger -> 5 ms attack, 280 ms release, in dB)
    if duck_trig.any():
        d = iir(duck_trig, [onepole_ba(0.28)]) * (0.28 * SR)
        d = iir(d, [onepole_ba(0.005)])
        music *= 10.0 ** (-np.minimum(d, 9.0) / 20.0)
    if spans:                                    # hard silences on both buses (reverb returns included)
        mask = silence_mask(spans, n)
        music *= mask
        sfx *= mask
    sfx += sfx_pass

    mixbus = music + sfx
    stems = dict(kick=parts['kick'], drums=drums, tonal=tonal, music=music, sfx=sfx, swell=sfx_pass)
    stems.update(('part-' + p, parts[p]) for p in PARTS if parts[p].any())
    stems.update({'ret-room': room, 'ret-hall': hall, 'ret-delay': dly, 'ret-fxverb': fxverb * undb(RETURNS['fxverb'])})
    xpre, pre_info = master_pre(mixbus)
    master, drive = master_finish(xpre, TARGET_LUFS)
    info = master_info(master, pre_info, drive)
    info.update(counts=counts, events=events, scenes=scenes, render_s=time.time() - t_start, xpre=xpre,
                yielded=yielded, spans=spans)
    return master, stems, info


def master_pre(x):
    """Mastering, fixed part: DC blocker + HP 20 Hz, -1.5 dB shelf above 9 kHz, lows made mono (M/S: side highpassed at 120 Hz,
    zero-phase), pre-fade of the tail, level-normalized to -20 LUFS so the glue compressor always sees
    the same program level, then gentle glue (1.8:1, 25 ms RMS, 25/250 ms)."""
    n = x.shape[-1]
    ef = int(END_FADE * SR)
    x = filt(dc_block(x), ('hp', 20, 0.7), ('highshelf', 9000, 0.7, -1.5))
    m, s = 0.5 * (x[0] + x[1]), 0.5 * (x[0] - x[1])
    s = zerophase(s, lambda f: f ** 4 / (f ** 4 + 120.0 ** 4))
    x = np.stack([m + s, m - s])
    x[:, n - ef:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, ef + 1) / ef)
    pre = lufs(x)
    g0 = undb(-20.0 - pre) if pre > -69 else 1.0
    x, gr = compressor(x * g0, thr_db=-17.0, ratio=1.8, attack=0.025, release=0.25, knee_db=8.0, rms_ms=25.0)
    return x, dict(g0=g0, glue_gr_max=float(-gr.min()))


def master_finish(x, target):
    """Mastering, loudness part: drive into the 4x oversampled soft clipper and the true-peak limiter,
    drive iterated until the internal BS.1770 meter reads `target`; then the end fade to digital
    silence and a 1 ms safety fade-in. Returns (y, drive_db)."""
    n = x.shape[-1]
    ef = int(END_FADE * SR)
    ceiling = CEILING_DBTP - 0.15
    drive = float(np.clip(target - lufs(x), -20.0, 30.0))
    y = x
    prev = None
    for _ in range(10):
        y = soft_clip(x * undb(drive), ceiling=undb(ceiling + 1.2), knee=0.72)
        y, _ga = limiter(y, ceiling)
        cur = lufs(y)
        if abs(cur - target) < 0.03 or cur <= -69.0:
            break
        slope = 1.0                                  # secant step: limiting makes loudness grow < 1 dB/dB
        if prev is not None and abs(drive - prev[0]) > 1e-6:
            slope = float(np.clip((cur - prev[1]) / (drive - prev[0]), 0.15, 1.5))
        prev = (drive, cur)
        drive = float(np.clip(drive + (target - cur) / slope, -20.0, 30.0))
    y[:, n - ef:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, ef + 1) / ef)
    y[:, -1] = 0.0
    fi = int(0.001 * SR)
    y[:, :fi] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(fi) / fi)
    tp = true_peak(y)
    if tp > undb(ceiling):
        y *= undb(ceiling) / tp
    return y, drive


def master_info(y, pre_info, drive):
    return dict(pre_info, pregain=pre_info['g0'] * undb(drive), drive_db=drive, lufs_internal=lufs(y),
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
    t0 = time.time()
    if a.seed is not None:
        SEED = a.seed
    split = [v.strip() for v in a.mute.split(',') if v.strip()], [v.strip() for v in a.solo.split(',') if v.strip()]
    master, stems, info = render(a.cues, *split)
    write_wav(a.out, master, 24)
    meas = None if a.no_ffmpeg else ffmpeg_loudness(a.out)
    for _ in range(2):          # calibrate to ffmpeg loudnorm (it can read ~0.2 LU off BS.1770 on dynamic material)
        if not meas or abs(float(meas.get('input_i', TARGET_LUFS)) - TARGET_LUFS) <= 0.05:
            break
        offset = float(meas['input_i']) - info['lufs_internal']
        master, drive = master_finish(info['xpre'], TARGET_LUFS - offset)
        info.update(master_info(master, info, drive))
        write_wav(a.out, master, 24)
        meas = ffmpeg_loudness(a.out)
    if a.stems:
        d = os.path.join(ROOT, '.cache', 'stems')
        if os.path.isdir(d):                     # drop part stems of parts that no longer play
            for f in sorted(os.listdir(d)):
                if f.startswith('part-') and f.endswith('.wav') and f[:-4] not in stems:
                    os.remove(os.path.join(d, f))
        for k, v in stems.items():
            write_wav(os.path.join(d, k + '.wav'), v * info['pregain'], 32)
        write_wav(os.path.join(d, 'master.wav'), master, 32)
        keys = ('type', 't', 'anchor', 'dur', 'amt', 'pitch', 'pitched', 'count', 'dir', 'tone', 'verb', 'source',
                'seed', 'passes')
        side = dict(cues=os.path.abspath(a.cues) if a.cues else None, pregain=info['pregain'],
                    silences=[list(sp) for sp in info['spans']],
                    events=[dict({k: ev[k] for k in keys if k in ev}, gain_db=SFX_MIX.get(ev['type'], {}).get('gain', 0.0))
                            for ev in info['events']],
                    yielded=[dict(type=f['type'], anchor=f['anchor'], picture_t=q['t']) for f, q in info['yielded']])
        with open(os.path.join(d, 'render.json'), 'w', encoding='utf-8') as fh:
            json.dump(side, fh, indent=1)
    info['render_s'] = time.time() - t0
    counts = info['counts']
    print('soundtrack  %s' % os.path.relpath(a.out))
    print('  duration  %.3f s  (%d samples @ %d Hz, 24-bit stereo)' % (master.shape[1] / SR, master.shape[1], SR))
    print('  peak      %.2f dBFS   true peak %.2f dBTP (4x)' % (info['peak_db'], info['true_peak_db']))
    if meas:
        print('  loudness  %s LUFS integrated, %s dBTP, LRA %s LU  (ffmpeg loudnorm)' % (
            meas.get('input_i'), meas.get('input_tp'), meas.get('input_lra')))
    print('  loudness  %.2f LUFS (internal BS.1770, matches ffmpeg ebur128)   drive %+.1f dB, glue GR max %.1f dB' % (
        info['lufs_internal'], info['drive_db'], info['glue_gr_max']))
    cuts = ' '.join('%.3f' % sc['start'] for sc in info['scenes'] if sc['start'] > 1e-6)
    print('  scenes    %d%s' % (len(info['scenes']), ('  (cuts at %s s)' % cuts) if cuts else ''))
    by_type = ', '.join('%s %d' % kv for kv in sorted(counts.items())) or 'none'
    print('  sfx       %d events: %s' % (sum(counts.values()), by_type))
    src = {}
    for ev in info['events']:
        k = ev['source'].split(':')[0]
        src[k] = src.get(k, 0) + 1
    print('  sources   %s' % (', '.join('%s %d' % kv for kv in sorted(src.items())) or 'none'))
    if info['yielded']:
        print('  yielded   %d arrangement FX stepped aside for the picture: %s' % (len(info['yielded']), ' '.join(
            '%s@%.3f' % (f['type'], f['anchor']) for f, _ in info['yielded'])))
    for t0, t1, _ in info['spans']:
        thru = [ev for ev in info['events'] if ev.get('passes') and abs(ev['anchor'] - t1) <= PASS_WINDOW]
        print('  silence   %.4f-%.4f s  (passing: %s)' % (t0, t1, ', '.join(
            '%s %s %.3f->%.3f' % (ev['source'].split(':')[0], ev['type'], ev['t'], ev['anchor']) for ev in thru) or 'nothing'))
    print('  render    %.1f s%s' % (info['render_s'], ('   warnings: %d' % len(WARNINGS)) if WARNINGS else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
