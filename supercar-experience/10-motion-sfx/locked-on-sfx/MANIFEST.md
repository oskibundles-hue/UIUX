# Supercar Experience — Locked-On SFX pack

23 sounds, made for the GT3 RS "LOCKED ON" showcase (26 Sept 2026) and approved with it.
They are 48 kHz / 24-bit stereo WAVs, peak-normalised to -1 dBFS (the bed is left at -14 LUFS). Everything is synthesised
with numpy using fixed seeds, so it's ours to use. The GT3 RS clip's own music is not included: it came with the footage and
its rights are unverified.

`SE-LO_audition - all sounds in one pass.mp3` plays every one-shot in order (the bed is left out). `audition_at` is where
each one starts in it.

| # | File | Type | Length | What it is | Where it is in the GT3 RS cut | Audition at |
|---|---|---|---|---|---|---|
| 1 | `SE-LO_01_hit_open.wav` | Hits | 3.49 s | Cold-open hit: sub drop, body thud, noise crack and a metal ring into a hall. | frame 0, under the hook panel | 0.0 s |
| 2 | `SE-LO_02_hit_drop.wav` | Hits | 3.5 s | The drop hit, bigger body. Pair with a 1/8-bar silence right before it. | 8.57 s, price reel after the black gap | 3.94 s |
| 3 | `SE-LO_03_hit_endcard.wav` | Hits | 3.3 s | End-card hit with a long hall tail. | 14.57 s, end card lands | 7.89 s |
| 4 | `SE-LO_04_whoosh_left_to_right.wav` | Transitions | 0.7 s | Air past camera, pans left to right. Its peak is at 62% of its length: line that up with the cut. | whips at 1.71, 5.57, 12.86 s | 11.64 s |
| 5 | `SE-LO_05_whoosh_right_to_left.wav` | Transitions | 0.7 s | The same whoosh panned right to left, for alternating whips. | whips at 3.43, 10.71 s | 12.79 s |
| 6 | `SE-LO_06_riser_noise_1.5s.wav` | Transitions | 1.5 s | Band-noise riser, 1.5 s, no pitch, so it sits under any music. | 6.86 to 8.36 s, into the black gap | 13.94 s |
| 7 | `SE-LO_07_riser_full_2s.wav` | Transitions | 2.0 s | Full riser: noise sweep plus saw stack and an accelerating snare roll (F minor). | first cut (synthetic bed) | 15.89 s |
| 8 | `SE-LO_08_swell_cymbal_reverse.wav` | Transitions | 0.89 s | Reversed open-cymbal bloom that sucks into the next hit. | 14.14 to 14.57 s, into the end card | 18.34 s |
| 9 | `SE-LO_09_swell_chord_reverse.wav` | Transitions | 0.99 s | Reversed F-minor chord bloom. Musical, so use it on the synthetic beat, not over other music. | first cut (synthetic bed) | 19.68 s |
| 10 | `SE-LO_10_tick_acquire.wav` | Lock-on UI | 0.05 s | Bracket acquire tick: noise click plus a short inharmonic metal ping with no pitch. | 3.84 s, door-script brackets | 21.11 s |
| 11 | `SE-LO_11_tick_lock.wav` | Lock-on UI | 0.05 s | Bracket lock tick, the harder one. | 4.02 s door lock, 6.69 s crest lock | 21.61 s |
| 12 | `SE-LO_12_tick_reel_lands.wav` | Lock-on UI | 0.48 s | Four ticks as slot-reel digits land (three quick, one final). | 9.00 to 9.43 s, $1,200 lands | 22.11 s |
| 13 | `SE-LO_13_engine_flat6_blip_blip_rev.wav` | Engines | 3.8 s | Synthesised flat-six (GT3 RS character): two throttle blips, then a full rev into the 9,000 rpm limiter. | first cut, cold open | 23.04 s |
| 14 | `SE-LO_14_engine_v8_burble_upshift.wav` | Engines | 2.6 s | Synthesised cross-plane V8 (AMG burble): overrun pops, two blips, pull, upshift, lift-off pops. | versus concept (AMG GT Black Series) | 27.29 s |
| 15 | `SE-LO_15_kick.wav` | Beat kit | 0.55 s | Trap kick, tight punch. | first cut groove | 30.34 s |
| 16 | `SE-LO_16_808_F1.wav` | Beat kit | 1.4 s | 808 on F1 (43.7 Hz), saturated. | first cut, end card low end | 31.34 s |
| 17 | `SE-LO_17_clap_room.wav` | Beat kit | 1.02 s | Layered clap in a small room. | first cut groove, beat 3 | 33.19 s |
| 18 | `SE-LO_18_hat_closed.wav` | Beat kit | 0.07 s | Closed hat. | first cut groove | 34.66 s |
| 19 | `SE-LO_19_hat_open.wav` | Beat kit | 0.35 s | Open hat. | first cut groove | 35.18 s |
| 20 | `SE-LO_20_braam_F.wav` | Stings | 2.2 s | Trailer braam on F2. | first cut, drop and end card | 35.98 s |
| 21 | `SE-LO_21_logo_sting_bells_F.wav` | Stings | 2.6 s | FM-bell logo sting, F5 Ab5 C6 F6, panned left to right. | first cut, end card | 38.63 s |
| 22 | `SE-LO_22_tapestop_on_beat.wav` | FX | 2.0 s | The tape stop: 1.2 s of the synthetic beat, then the whole mix varispeeds to a halt over 0.8 s. In the final cut the same effect runs on the clip music. | 13.71 to 14.14 s (effect) | 41.68 s |
| 23 | `SE-LO_23_bed_locked_on_140bpm_18s.wav` | Beds | 18.0 s | The whole synthetic Locked-On bed from the first cut: F-minor trap/cinematic at 140 BPM, 18 s, with its own tape stop and end card. Already -14 LUFS, left as is. | first cut (replaced by the clip music in the final) | — |

## How they sit in a mix (the Locked-On rule)

- Over the clip's own music: accents at about 45% of the music's RMS (about -7 dB) over each accent's own energetic span.
  Leave out the pitched ones (braam, bells, chord swell, 808, full riser) because they clash with the key.
- On the synthetic beat: anything goes. It is all F minor at 140 BPM.
- Tape stop: hand the music over to its own stop. Never layer a stopped copy on top of the running track.

Rebuild: `python3 build_locked_on_sfx.py` (UIUX repo, `supercar-experience/10-motion-sfx/`).
