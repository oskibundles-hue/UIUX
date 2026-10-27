# SFX pack

Synthesised, 48 kHz stereo, peak -3 dBFS. `audition.wav` plays every sound in this order with a short gap.

| file | length |
|---|---|
| ui_click_soft.wav | 0.02 s |
| ui_click_hard.wav | 0.03 s |
| key_thock.wav | 0.06 s |
| key_space.wav | 0.09 s |
| tick.wav | 0.01 s |
| impact_low.wav | 0.70 s |
| impact_deep.wav | 1.00 s |
| hit_snap.wav | 0.35 s |
| whoosh_short.wav | 0.80 s |
| whoosh_long.wav | 1.40 s |
| swish.wav | 0.50 s |
| riser_air.wav | 1.20 s |
| riser_tone.wav | 2.00 s |
| pop.wav | 0.12 s |
| ding.wav | 0.90 s |
| shutter.wav | 0.14 s |
| reverse_whoosh.wav | 0.60 s |

Where they are used: `intro_sfx.py` (key clicks, thock, space, impact, whoosh, riser). Drop real recordings with the same names into this folder to replace any of them.


## Kit v2 (`kit-v2/`, added 2026-10-27)

Synthesised by `experiments/edit-refs/gen_sfx_kit.py` (numpy, fixed seeds, no downloads), 48 kHz 24-bit
stereo, peak -1 dBFS. Free to use: see `kit-v2/LICENCE.md`. `kit-v2/audition.wav` plays them all in this
order with 0.4 s gaps. `kit-v2/kit.json` holds each length and **hit**: the time inside the file where the
transient lands, so a sound placed at `cut_time - hit` hits on the frame.

| file | length | hit | what |
|---|---|---|---|
| kit-v2/rapid_click_3f.wav | 1.02 s | 0.00 s | click train, one every 3 frames (9.99/s) at 29.97 fps; 1 s |
| kit-v2/rapid_click_2f.wav | 1.02 s | 0.00 s | click train, one every 2 frames (15/s); 1 s |
| kit-v2/rapid_click_1f.wav | 1.02 s | 0.00 s | click train, one per frame (30/s); 1 s |
| kit-v2/rapid_click_ramp.wav | 1.02 s | 0.00 s | click train accelerating from 6/s to 30/s; 1 s |
| kit-v2/mech_click_a.wav | 0.16 s | 0.00 s | mechanical key, linear thock: down and up stroke |
| kit-v2/mech_click_b.wav | 0.16 s | 0.00 s | mechanical key, clicky switch: double click down, up stroke |
| kit-v2/button.wav | 0.14 s | 0.00 s | UI press: click plus a short blip, then release |
| kit-v2/whoosh.wav | 0.75 s | 0.62 s | band-passed noise sweep, L to R; peak at 0.62 s |
| kit-v2/big_flash.wav | 0.90 s | 0.00 s | bright transient: crack, burst, falling zap, sub, airy tail; hit at 0 |
| kit-v2/whoosh_flash.wav | 1.52 s | 0.62 s | whoosh into big_flash; flash hit at 0.62 s |
| kit-v2/glitch_1.wav | 0.55 s | 0.00 s | bit-crush and sample-rate reduction, stepped |
| kit-v2/glitch_2.wav | 0.55 s | 0.00 s | stutter: one slice gated, speeding up |
| kit-v2/glitch_3.wav | 0.55 s | 0.00 s | buffer repeat: a grain repeated, halving each time |
| kit-v2/zoom_riser.wav | 1.00 s | 1.00 s | riser for the rapid zoom; peak at the end (1.0 s), place its end on the land |

Where they are used: `experiments/edit-refs/rapid_zoom.py --sfx` (rapid_click_3f on the 3-frame run,
zoom_riser into the land, whoosh_flash on the land). The rest are for placing by hand or by spec
(build_kinetic.py `audio` entries take a `file`).
