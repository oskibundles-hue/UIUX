#!/usr/bin/env python3
"""
build_locked_on_sfx.py -- the Supercar Experience "Locked-On" SFX pack.

Every sound designed for the GT3 RS "LOCKED ON" showcase (26 Sept 2026), rendered one by one as
clean 48 kHz / 24-bit WAVs, plus an audition file and a manifest. Omarie, 26 Sept: "I'd like to take
the sounds from that GT3RS video as well and add it to our collection."

All of it is synthesised with numpy (the showcase's audio/synth.py and the accent generators in
audio/bed_music.py), with fixed seeds, so a re-run gives the same files. Nothing here is taken
from the GT3 RS clip's own music. That track came with the footage, its rights are unverified,
and it stays out of the pack.

    python3 build_locked_on_sfx.py [--ffmpeg /path/to/ffmpeg] [--out locked-on-sfx]
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, '..', '09-campaign-ads', 'flash-special-showcase', 'audio')
sys.path.insert(0, AUDIO)
import synth as S          # noqa: E402
import bed_music as BM     # noqa: E402  (tick, noise_riser, cymbal_swell, read_audio, write_wav24)

SR = S.SR
SCRATCH = '/tmp/claude-0/-home-user-UIUX/2e2fc1bb-c45d-5ce1-ba97-afbf7647f193/scratchpad'


def stereo(x):
    x = np.asarray(x, dtype=np.float64)
    return np.stack([x, x], 1) if x.ndim == 1 else x


def finish(x, peak_db=-1.0, tail_ms=8):
    """Stereo, trimmed of trailing silence, short fade-out, peak-normalised."""
    x = stereo(x)
    env = np.abs(x).max(1)
    last = np.nonzero(env > 10 ** (-70 / 20))[0]
    if len(last):
        x = x[: last[-1] + 1]
    n = min(len(x), int(SR * tail_ms / 1000))
    x[-n:] *= np.linspace(1, 0, n)[:, None]
    x[:16] *= np.linspace(0, 1, 16)[:, None]
    return x * (10 ** (peak_db / 20) / (np.abs(x).max() + 1e-12))


def build(ff):
    beat = 60 / 140
    out = []                     # (file stem, category, signal, what, where it is heard)

    def add(name, cat, sig, what, where, peak=-1.0):
        out.append((name, cat, finish(sig, peak), what, where))

    rng = np.random.default_rng(11)
    hall = S.reverb_ir(rng, t60=2.6, damp=0.3)
    room = S.reverb_ir(rng, t60=0.9, damp=0.5, predelay=0.008)

    # ---- hits (the three impacts of the final cut)
    add('hit_open', 'Hits', S.impact(np.random.default_rng(101), hall, size=0.8),
        'Cold-open hit: sub drop, body thud, noise crack and a metal ring into a hall.', 'frame 0, under the hook panel')
    add('hit_drop', 'Hits', S.impact(np.random.default_rng(102), hall, size=1.0),
        'The drop hit, bigger body. Pair with a 1/8-bar silence right before it.', '8.57 s, price reel after the black gap')
    add('hit_endcard', 'Hits', S.impact(np.random.default_rng(103), hall, size=1.3, dur=3.3),
        'End-card hit with a long hall tail.', '14.57 s, end card lands')

    # ---- transitions
    add('whoosh_left_to_right', 'Transitions', S.whoosh(np.random.default_rng(201), dur=0.7, peak=0.62, direction=1),
        'Air past camera, pans left to right. Its peak is at 62% of its length: line that up with the cut.', 'whips at 1.71, 5.57, 12.86 s')
    add('whoosh_right_to_left', 'Transitions', S.whoosh(np.random.default_rng(202), dur=0.7, peak=0.62, direction=-1),
        'The same whoosh panned right to left, for alternating whips.', 'whips at 3.43, 10.71 s')
    add('riser_noise_1.5s', 'Transitions', BM.noise_riser(np.random.default_rng(203), 1.5),
        'Band-noise riser, 1.5 s, no pitch, so it sits under any music.', '6.86 to 8.36 s, into the black gap')
    add('riser_full_2s', 'Transitions', S.riser(np.random.default_rng(204), 2.0),
        'Full riser: noise sweep plus saw stack and an accelerating snare roll (F minor).', 'first cut (synthetic bed)')
    add('swell_cymbal_reverse', 'Transitions', BM.cymbal_swell(np.random.default_rng(205), hall, 0.9),
        'Reversed open-cymbal bloom that sucks into the next hit.', '14.14 to 14.57 s, into the end card')
    add('swell_chord_reverse', 'Transitions', S.reverse_swell(np.random.default_rng(206), hall, 1.0),
        'Reversed F-minor chord bloom. Musical, so use it on the synthetic beat, not over other music.', 'first cut (synthetic bed)')

    # ---- lock-on UI
    add('tick_acquire', 'Lock-on UI', BM.tick(np.random.default_rng(301), 0.8),
        'Bracket acquire tick: noise click plus a short inharmonic metal ping with no pitch.', '3.84 s, door-script brackets')
    add('tick_lock', 'Lock-on UI', BM.tick(np.random.default_rng(302), 1.0),
        'Bracket lock tick, the harder one.', '4.02 s door lock, 6.69 s crest lock')
    reel = np.zeros((int(0.9 * SR), 2))
    for t, lv, sd in ((0.0, 0.8, 303), (0.107, 0.8, 304), (0.214, 0.8, 305), (0.429, 1.0, 306)):
        S.place(reel, BM.tick(np.random.default_rng(sd), lv), t, 1.0)
    add('tick_reel_lands', 'Lock-on UI', reel,
        'Four ticks as slot-reel digits land (three quick, one final).', '9.00 to 9.43 s, $1,200 lands')

    # ---- engines (the synthetic GT3 RS flat-six and an AMG-style V8)
    rpm, thr = S.rpm_sim(3.8, [(1.0 * beat, 1.3 * beat, 0.75), (2.0 * beat, 2.25 * beat, 0.9),
                               (3.0 * beat, 3.3, 1.0)], redline=9000)
    eng = S.engine(np.random.default_rng(401), rpm, thr, 'flat6')
    eng *= np.minimum(1, (3.8 - S.tax(len(eng))) / 0.25)[:, None]
    add('engine_flat6_blip_blip_rev', 'Engines', eng,
        'Synthesised flat-six (GT3 RS character): two throttle blips, then a full rev into the 9,000 rpm limiter.', 'first cut, cold open')
    ib, vdur = 0.86, 2.6
    rpm2, thr2 = S.rpm_sim(vdur, [(ib - 0.42, ib - 0.36, 0.8), (ib - 0.2, ib - 0.14, 0.85), (ib, 1.9, 1.0),
                                  ('shift', ib + 0.6, 0.72)], idle=1400, redline=9000, up=5.0, down=1.6, r0=7600)
    v8 = S.engine(np.random.default_rng(402), rpm2, thr2, 'v8')
    v8 *= np.minimum(1, (vdur - S.tax(len(v8))) / 0.3)[:, None]
    add('engine_v8_burble_upshift', 'Engines', v8,
        'Synthesised cross-plane V8 (AMG burble): overrun pops, two blips, pull, upshift, lift-off pops.', 'versus concept (AMG GT Black Series)')

    # ---- beat kit + stings (F minor, 140 BPM family)
    add('kick', 'Beat kit', S.kick(np.random.default_rng(501)), 'Trap kick, tight punch.', 'first cut groove')
    add('808_F1', 'Beat kit', S.e808(np.random.default_rng(502), S.midi(29), 1.4), '808 on F1 (43.7 Hz), saturated.', 'first cut, end card low end')
    add('clap_room', 'Beat kit', S.reverb(S.clap(np.random.default_rng(503)), room, wet=0.35), 'Layered clap in a small room.', 'first cut groove, beat 3')
    add('hat_closed', 'Beat kit', S.hat(np.random.default_rng(504), 0.045), 'Closed hat.', 'first cut groove')
    add('hat_open', 'Beat kit', S.hat(np.random.default_rng(505), open_=True), 'Open hat.', 'first cut groove')
    add('braam_F', 'Stings', S.braam(np.random.default_rng(506), S.midi(41), 2.2), 'Trailer braam on F2.', 'first cut, drop and end card')
    sting = np.zeros((int(2.6 * SR), 2))
    for i, m in enumerate([77, 80, 84, 89]):
        bl = S.reverb(S.bell(np.random.default_rng(510 + i), S.midi(m)), hall, wet=0.4)
        S.place(sting, S.pan(bl.mean(1), [-0.4, -0.1, 0.2, 0.45][i]) * 1.2, 0.5 * beat * (i + 1), 0.3)
    add('logo_sting_bells_F', 'Stings', sting, 'FM-bell logo sting, F5 Ab5 C6 F6, panned left to right.', 'first cut, end card')

    # ---- the tape stop, as an effect demo on the synthetic beat (rights-clean)
    bed = BM.read_audio(ff, os.path.join(AUDIO, 'bed_hero.wav'))
    a, L = int(8.571 * SR), int(0.8 * SR)
    seg = bed[a - int(1.2 * SR): a + L].copy()
    u = np.arange(L) / L
    stopped = S.varispeed(seg[-L:].copy(), (1 - u) ** 1.3)
    stopped = S.fft_filter(stopped, hi=9000)
    stopped *= np.minimum(1, (L - np.arange(L)) / S.n_of(0.02))[:, None]
    seg[-L:] = stopped
    add('tapestop_on_beat', 'FX', seg,
        'The tape stop: 1.2 s of the synthetic beat, then the whole mix varispeeds to a halt over 0.8 s. In the final cut the same effect runs on the clip music.', '13.71 to 14.14 s (effect)')

    # ---- the full synthetic bed from the first cut
    out.append(('bed_locked_on_140bpm_18s', 'Beds', stereo(bed), 'The whole synthetic Locked-On bed from the first cut: F-minor trap/cinematic at 140 BPM, 18 s, with its own tape stop and end card. Already -14 LUFS, left as is.', 'first cut (replaced by the clip music in the final)'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ffmpeg', default=os.path.join(SCRATCH, 'ffmpeg'))
    ap.add_argument('--out', default=os.path.join(HERE, 'locked-on-sfx'))
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)
    sounds = build(A.ffmpeg)
    rows, gap = [], np.zeros((int(0.45 * SR), 2))
    audition, t = [], 0.0
    for i, (stem, cat, x, what, where) in enumerate(sounds, 1):
        fn = f'SE-LO_{i:02d}_{stem}.wav'
        BM.write_wav24(os.path.join(A.out, fn), x)
        dur = len(x) / SR
        rows.append(dict(n=i, file=fn, category=cat, seconds=round(dur, 2), what=what, heard=where, audition_at=round(t, 2)))
        if not stem.startswith('bed_'):
            audition += [x * 0.8, gap]
            t += dur + 0.45
    au = np.concatenate(audition)
    BM.write_wav24(os.path.join(A.out, '_audition.wav'), au)
    subprocess.run([A.ffmpeg, '-y', '-loglevel', 'error', '-i', os.path.join(A.out, '_audition.wav'), '-c:a', 'libmp3lame', '-b:a', '192k',
                    os.path.join(A.out, 'SE-LO_audition - all sounds in one pass.mp3')], check=True)
    os.remove(os.path.join(A.out, '_audition.wav'))
    json.dump(rows, open(os.path.join(A.out, 'manifest.json'), 'w'), indent=1)
    lines = ['# Supercar Experience — Locked-On SFX pack', '',
             f'{len(rows)} sounds, made for the GT3 RS "LOCKED ON" showcase (26 Sept 2026) and approved with it.',
             'They are 48 kHz / 24-bit stereo WAVs, peak-normalised to -1 dBFS (the bed is left at -14 LUFS). Everything is synthesised',
             "with numpy using fixed seeds, so it's ours to use. The GT3 RS clip's own music is not included: it came with the footage and",
             'its rights are unverified.', '',
             '`SE-LO_audition - all sounds in one pass.mp3` plays every one-shot in order (the bed is left out). `audition_at` is where',
             'each one starts in it.', '',
             '| # | File | Type | Length | What it is | Where it is in the GT3 RS cut | Audition at |',
             '|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['n']} | `{r['file']}` | {r['category']} | {r['seconds']} s | {r['what']} | {r['heard']} | "
                     f"{'—' if r['file'].find('bed_') > 0 else str(r['audition_at']) + ' s'} |")
    lines += ['', '## How they sit in a mix (the Locked-On rule)', '',
              "- Over the clip's own music: accents at about 45% of the music's RMS (about -7 dB) over each accent's own energetic span.",
              '  Leave out the pitched ones (braam, bells, chord swell, 808, full riser) because they clash with the key.',
              '- On the synthetic beat: anything goes. It is all F minor at 140 BPM.',
              '- Tape stop: hand the music over to its own stop. Never layer a stopped copy on top of the running track.',
              '', 'Rebuild: `python3 build_locked_on_sfx.py` (UIUX repo, `supercar-experience/10-motion-sfx/`).']
    open(os.path.join(A.out, 'MANIFEST.md'), 'w').write('\n'.join(lines) + '\n')
    print(f'{len(rows)} sounds -> {A.out}')


if __name__ == '__main__':
    main()
