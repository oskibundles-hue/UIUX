# Final build cue: "LOCKED ON" GT3 RS showcase (as built)

This is the director/judge cue the build follows, condensed. `lib/edl.py` holds the beat table as data
and `front.html` holds the front-layer graphics. Where the build differs from the cue, the change is
listed under **Deviations** at the end with the reason for it.

## Output
- 1080x1920, 24000/1001 fps, 432 frames (18.018 s picture; the bed is 18.000 s).
- libx264 High, crf 16, preset slow, yuv420p, bt709. AAC 192k 48 kHz stereo from `audio/bed_hero.wav`,
  used as-is (-13.99 LUFS / -2.12 dBTP in the WAV). No loudnorm. +faststart.
- Plates are cut by **frame number** only (the source is decoded in order into `.work/src_gt.npy`).
  `-ss` is never used because it lands about 2 frames late on these .mov files.

## Layer stack, per output frame
1. PLATE (`lib/plate.py`, built on `lib/fx.py`): frame-exact source sample (blend / shutter / optical
   flow), then NightGrade fitted per shot, then streaks, then push/punch/shake, then whip or impact,
   then light leak.
2. WAREHOUSE, 12.0-18.0 (`lib/warehouse.py`, refactored from rnd-matte `demo_occlusion.render_frame`):
   background graded to 55 % above the car, behind-car type (GT3, $1,200, floor hairline), car matte
   with 2.5D push about the tyre contact point, light wrap.
3. FRONT (`front.html`): kinetic.js + lock.js/tracks.js. Captured by `lib/kcapture.js` as transparent
   PNG with sub-frame motion blur (k=10, 180 deg; k=28 / 270 deg on [3.24,3.43], [8.23,8.36],
   [8.60,9.50], [15.18,15.44]).
4. FINISH: vignette 0.42, then grain 0.035 last (it keeps moving through the freeze).

## Licence plates
- Drive-away, source f226-246: the Montana plate is readable at full resolution. It is tracked
  (`lib/data/plate_track.json`), the box is padded 14 px into a rounded rect (r 8) with a 6 px feather,
  and the inside gets two gaussian passes at sigma 12.
- Rear-wing shot, source f9-22: the plate corner at the bottom right showed "...332 / MONTANA".
  It is tracked (`lib/data/plate2_track.json`) and blurred the same way.

## Beat table (output time in s; src = 0-based source frames of GT3RS_livery.mov)
| # | Out | Source | Retime | Plate FX | Sound |
|---|---|---|---|---|---|
| 1 | 0.000-0.643 | f34-44 tunnel side pass | 0.71x blend, frame 0 = f34 | push 1.00->1.03 over beats 1-5 (outCubic to 3.25); shake 6 px + RGB split on frames 1-8; no flash | impact_open 0.000 |
| 2 | 0.643-1.714 | f9-22 rear wing, badge | 0.545x blend | amber leak burst at 0.643, 0.25, right | blips |
| 3 | 1.714-2.143 | f46-59 DRIVE MODE knob | 1.26x | whip right, k=3 | whoosh 1.714 |
| 4 | 2.143-3.000 | f62-72 dial Normal -> Sport (skips f60-61 gauges) | ~0.5x blend | push-in 1.00->1.04 | rev |
| 5 | 3.000-3.429 | f73-78 pedal | ~0.56x | 2-frame zoom punch 1.03 at 3.214 | engine_rev_peak |
| 6 | 3.429-3.857 | f156-166 hood stripes | 0.97x | whip up, k=3; leak 0.2 | groove 3.429 |
| 7 | 3.857-4.286 | f168-177 GT3RS door script | 0.9x | hard cut | |
| 8 | 4.286-4.714 | f0-7 wing strut | 0.78x | hard cut | clap |
| 9 | 4.714-5.143 | f188-195 swan neck + wheel | 0.68x | hard cut | |
| 10 | 5.143-5.571 | f196-205 endplate + taillight | 0.87x | streaks 0.9 | |
| 11 | 5.571-6.429 | f226-246 drive-away (plate blurred) | 1.02x | whip left, k=3; streaks 1.0 | whoosh 5.571 |
| 12 | 6.429-8.357 | f80-108 Porsche crest | 0.605x blend (no minterpolate) | streaks 0.8; leak pulse 0.3 | riser 6.857 |
| 13 | 8.380-8.571 | black, 5 frames (201-205) | | | drop gap |
| 14 | 8.571-10.714 | f121-154 tunnel front 3/4 | ramp keys (0,1.6),(0.28,0.45),(1,0.55); optical flow f129-154 x4 | fx.impact k=0..15 (flash on k0,k1); streaks 0.8 above y 820 / 1.2 below; leak 0.35 | DROP 8.571 |
| 15 | 10.714-11.571 | f256-276 ceiling lamps | 1.0x | whip left, k=3; streaks 1.0 | whoosh 10.714 |
| 16 | 11.571-12.000 | f279-287 chrome PORSCHE script | 0.78x | streaks 0.7 | |
| 17 | 12.000-13.714 | warehouse f291-309 | 0.45x cross-blend | impact_2: 1-frame 25 % luma lift, zoom 1.04->1.0; push to bg 1.012 / type 1.019 / car 1.024 (inOutCubic); streaks 0.8 | impact_2 12.0 |
| 18 | 13.714-15.429 | warehouse, tape stop | speed 0.45*(1-u)^3 over 13.714-14.30, freeze on src 12.969 s | -15 % luma, -20 % sat (easeIn), recovers 14.571-15.429; push paused | tapestop, swell |
| 19 | 15.429-18.000 | warehouse, resumes | 3-frame ease-in, then 0.379x to src 13.91 s | impact_3: 1-frame 20 % lift; push to 1.025 / 1.040 / 1.050 (outCubic); leak drift 0.15; bottom scrim 0->55 % y 1250-1920 | endcard, bells |

## Front-layer graphics (positions are ink top-left; copy is templated from config.json)
- **A. Hook, 0-3.429.** #000 86 % panel x 54-1080, y 280-690 (it bleeds off the right edge over the
  NO PARKING sign). The 78/22 stripe cap is 8 px. FLASH SPECIAL (Michroma 36 gold, y 318),
  TODAY ONLY (Bebas 210, y 370) and ENDS {endTime} (Bebas 96 gold, y 596, per-glyph rise at 0.429).
  A glint crosses TODAY ONLY at 0.857-1.307. Each line whips up (dy -300) at 3.25 / 3.27 / 3.29.
- **B. Door flash, 3.857-4.286.** Gold brackets (4 px, 34 px arms, 45 % black under-stroke) locked to
  TRACKS.door, acquire j/5, collapsing over the last 2 frames.
- **C. Crest callout, 6.300-8.357.** The brackets fly in from off-frame, then lock to TRACKS.crest at
  the plate's source time. A leader line draws up to the label panel (x 54-560, y 470-710), which
  follows the crest. PORSCHE flips in per glyph, {model} wipes in, {year} · {cls} tracking-collapses.
  Glint at 7.71-8.10, whip-out at 8.235.
- **D. Offer, 8.655-12.0.** #000 88 % panel x 54-900, y 280-820. It scales 1.08->1.0 and shakes with the
  plate for 2 frames. {hours} HOURS tracking-collapses. The {price} slot reels land at 9.000 / 9.107 /
  9.214 / 9.429 with a 4-frame 1.04 pulse on each. Then a stripe, OUT THE DOOR wipes in, a glint at
  10.29-10.75, and a fade over 11.917-12.0.
- **E. Behind the car (Python).** Giant {giant} rises from the floor line (y 1088) at 12.05 / 12.13 /
  12.21 and sinks at 13.714-14.15 (order 3, T, G). A gold floor hairline draws at 14.80-15.30.
- **F. Requirements, 12.857-15.43.** Top scrim. YOU NEED / VALID DRIVER'S LICENSE / 21+ · INSURANCE
  rise at 12.857 / 12.930 / 13.000, a stripe draws at 12.90-13.20, whip-out at 15.33.
- **G. End card, 15.18-18.0.** {price} rises from behind the car and lands on 15.429, with a glint at
  16.29-16.75. The logo wipes in at 15.643, then 5 HOURS · OUT THE DOOR, the stripe,
  TODAY ONLY · ENDS {endTime}, CALL OR DM TO BOOK, {phone} · {url}, and
  21+ · VALID LICENSE · INSURANCE. The last frame is a complete still with no fade.

## Deviations from the judge's cue
1. **Giant type sizes.** The cue asks for GT3 at 730 px and $1,200 at 384 px with ink at x 58. At full
   push (type layer x1.040 about x 560) that ink would reach x ~912, past the 907 safe edge. The build
   uses GT3 at 720 px from x 64 and $1,200 at 372 px from x 76, which reach at most x ~905.
2. **Beat 14 optical flow** starts at f129, not f137. The ramp is already at slow speed from f131, and
   frame blending there doubled the car's edges.
3. **Black gap** is output frames 201-205 (5 frames, as the cue asks). Frame 200 still shows the crest,
   so the callout's whip-out completes over the picture.
4. **Second plate blur** on f9-22 (see above). The cue said that corner was unreadable; at 100 % it was
   partly readable.
5. **Top scrim** stays on under the end card's top block, for legibility over the warehouse ceiling.
6. **Warehouse** frames also get the per-clip NightGrade, so the look matches the tunnel shots.
