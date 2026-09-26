# Final build cue: "LOCKED ON" GT3 RS showcase (as built)

This is the director/judge cue the build follows, condensed. `lib/edl.py` holds the beat table as data
and `front.html` holds the front-layer graphics. Where the build differs from the cue, the change is
listed under **Deviations** at the end with the reason for it.

## Output
- 1080x1920, 24000/1001 fps, 432 frames (18.018 s picture; the bed is 18.000 s).
- libx264 High, crf 16, preset slow, yuv420p, bt709. AAC 192k 48 kHz stereo from `audio/bed_hero.wav`,
  used as-is (-14.00 LUFS / -2.02 dBTP in the WAV; fix r1 bed: tape stop and swell a quarter bar each). No loudnorm. +faststart.
- Plates are cut by **frame number** only (the source is decoded in order into `.work/src_gt.npy`).
  `-ss` is never used because it lands about 2 frames late on these .mov files.

## Layer stack, per output frame
1. PLATE (`lib/plate.py`, built on `lib/fx.py`): frame-exact source sample (blend / shutter / optical
   flow), then NightGrade fitted per shot, then streaks, then push/punch/shake, then whip or impact,
   then light leak.
2. WAREHOUSE, 12.0-18.0 (`lib/warehouse.py`, refactored from rnd-matte `demo_occlusion.render_frame`):
   background graded to 55 % above the car, behind-car type (GT3, $1,200, floor hairline), car matte
   with 2.5D push about the tyre contact point, light wrap, light sweep across the car (fix r1).
3. FRONT (`front.html`): kinetic.js + lock.js/tracks.js. Captured by `lib/kcapture.js` as transparent
   PNG with sub-frame motion blur (k=10, 180 deg; k=28 / 270 deg on [3.24,3.43], [6.39,6.75],
   [8.23,8.36], [8.60,9.50], [14.32,14.58]).
4. FINISH: vignette 0.42, then grain 0.035 last (it keeps moving through the freeze).

## Licence plates
- Drive-away, source f226-246: the Montana plate is readable at full resolution. It is tracked
  (`lib/data/plate_track.json`), the box is padded 14 px into a rounded rect (r 8) with a 6 px feather,
  and the inside gets two gaussian passes at sigma 12.
- Rear-wing shot, source f9-22: the plate corner at the bottom right showed "...332 / MONTANA".
  It is tracked (`lib/data/plate2_track.json`) and blurred the same way.
- Rear tracking shot, source f206-224 (beat 15 since fix r1): "ERE332 / MONTANA" is fully readable.
  It is tracked (`lib/data/plate3_track.json`, box 262,943,118,59 on f206) and blurred the same way.

## Beat table (output time in s; src = 0-based source frames of GT3RS_livery.mov)
| # | Out | Source | Retime | Plate FX | Sound |
|---|---|---|---|---|---|
| 1 | 0.000-0.643 | f34-44 tunnel side pass | 0.71x blend, frame 0 = f34 | push 1.00->1.03 over beats 1-5 (outCubic to 3.25); shake 6 px + RGB split on frames 1-8; no flash | impact_open 0.000 |
| 2 | 0.643-1.714 | f9-22 rear wing, badge | 0.545x blend | amber leak burst at 0.643, 0.25, right | blips |
| 3 | 1.714-2.143 | f46-59 DRIVE MODE knob | 1.26x | whip right, k=3 | whoosh 1.714 |
| 4 | 2.143-3.000 | f62-72 dial Normal -> Sport (skips f60-61 gauges) | ~0.5x frame-hold (no blend) | push-in 1.00->1.04 | rev |
| 5 | 3.000-3.429 | f73-78 pedal | ~0.56x optical flow f73-78 x4 | 2-frame zoom punch 1.03 at 3.214 | engine_rev_peak |
| 6 | 3.429-3.857 | f156-166 hood stripes | 0.97x | whip up, k=3; leak 0.2 | groove 3.429 |
| 7 | 3.857-4.286 | f168-177 GT3RS door script | 0.9x | hard cut | |
| 8 | 4.286-4.714 | f0-7 wing strut | 0.78x | hard cut | clap |
| 9 | 4.714-5.143 | f188-195 swan neck + wheel | 0.68x | hard cut | |
| 10 | 5.143-5.571 | f196-205 endplate + taillight | 0.87x | streaks 0.9 | |
| 11 | 5.571-6.429 | f226-246 drive-away (plate blurred) | 1.02x | whip left, k=3; streaks 1.0 | whoosh 5.571 |
| 12 | 6.429-8.357 | f80-108 Porsche crest | 0.605x blend (no minterpolate) | streaks 0.8; leak pulse 0.3 | riser 6.857 |
| 13 | 8.380-8.571 | black, 5 frames (201-205) | | | drop gap |
| 14 | 8.571-10.714 | f121-154 tunnel front 3/4 | ramp keys (0,1.6),(0.28,0.45),(1,0.55); optical flow f129-154 x4 | fx.impact k=0..15 (flash on k0,k1); streaks 0.8 (thresh .93, point .25, r 60) above and below y 820; warm-hue protect 0.75; leak 0.35 | DROP 8.571 |
| 15 | 10.714-11.571 | f206-224 rear tracking in tunnel (plate blurred) | 0.9x | picture lowered 210 px (top fades to black); whip left, k=3; streaks 0.7 | whoosh 10.714 |
| 16 | 11.571-12.000 | f279-287 chrome PORSCHE script | 0.78x | streaks 0.7 | |
| 17 | 12.000-13.714 | warehouse f291-309 | 0.45x cross-blend | impact_2: 1-frame 25 % luma lift, zoom 1.04->1.0; continuous push (below); streaks 0.8 | impact_2 12.0 |
| 18 | 13.714-14.250 | warehouse, tape stop | speed 0.45*(1-u)^3 over 13.714-14.143, then frozen on src 12.951 s until 14.25 (~7 frames) | -15 % luma, -20 % sat (easeIn), recovers 14.143-14.571; light sweep 13.93-14.47; floor hairline 14.00-14.40 | tapestop 13.714, swell 14.143 |
| 19 | 14.250-18.000 | warehouse, resumes | 6-frame ease-in, then 0.267x to src 13.91 s | impact_3 at 14.571: 1-frame 20 % lift; leak drift 0.15; bottom scrim 0->55 % y 1250-1920 | endcard 14.571, bells |

Push (beats 17-19, fix r1): s(t) = 1 + A*u + B*outCubic((t-14.571)/1.2), u = (t-12)/6.018, with A/B =
bg .018/.010, type .037/.018, car .050/.020. It never pauses, and the end is 1.028 / 1.055 / 1.070.

## Front-layer graphics (positions are ink top-left; copy is templated from config.json)
- **A. Hook, 0-3.429.** #000 86 % panel x 54-900, y 280-690 (fix r1: it matches the stripe cap and the
  offer panel). The 78/22 stripe cap is 8 px. FLASH SPECIAL (Michroma 36 gold, y 318),
  TODAY ONLY (Bebas 210, y 370) and ENDS {endTime} (Bebas 96 gold, y 596). Fix r1: ENDS is set on
  frame 0, with a re-hit at 0.429 (a 4-frame 1.06 pulse and a gold glint). The white SCE lockup (240 px)
  sits on the ENDS row, right edge x 866. A glint crosses TODAY ONLY at 0.857-1.307. Each line whips up
  (dy -300) at 3.25 / 3.27 / 3.29.
- **B. Door flash, 3.857-4.286.** Gold brackets (4 px, 34 px arms, 45 % black under-stroke) locked to
  TRACKS.door, acquire j/5, collapsing over the last 2 frames.
- **C. Crest callout, 6.402-8.357.** The brackets fly in from off-frame over 7 frames, starting on the cut (fix r1), then lock to TRACKS.crest at
  the plate's source time. A leader line draws up to the label panel (x 54-560, y 470-710), which
  follows the crest. PORSCHE flips in per glyph, {model} wipes in, {year} · {cls} tracking-collapses.
  Glint at 7.71-8.10, whip-out at 8.235.
- **D. Offer, 8.655-12.0.** #000 88 % panel x 54-900, y 280-820. It scales 1.08->1.0 and shakes with the
  plate for 2 frames. {hours} HOURS tracking-collapses. The {price} slot reels land at 9.000 / 9.107 /
  9.214 / 9.429 with a 4-frame 1.04 pulse on each. Then a stripe, OUT THE DOOR wipes in, a glint at
  10.29-10.75, and a fade over 11.917-12.0.
- **E. Behind the car (Python).** Giant {giant} ("RS", 720 px, auto-fitted) rises from the floor line
  (y 1088) at 12.05 / 12.13 and sinks at 13.714-14.15 (order S, R). The motion blur samples scale with
  glyph travel (6-28). A gold floor hairline draws at 14.00-14.40.
- **F. Requirements, 12.857-15.43.** Top scrim. YOU NEED / VALID DRIVER'S LICENSE / 21+ · INSURANCE
  rise at 12.857 / 12.930 / 13.000, a stripe draws at 12.90-13.20, whip-out at 14.471.
- **G. End card, 14.33-18.0 (TE = 14.571).** {price} (360 px) rises from behind the car and lands on TE,
  with glints at TE+0.86 and TE+2.55. The logo (y 282) wipes in at TE+0.214. Below it, one logo-height
  clear: {brand} {model} (Michroma 30, y 384, tracking collapse), 5 HOURS · OUT THE DOOR (Bebas 100,
  y 430), the stripe (y 522), TODAY ONLY · ENDS {endTime} (Bebas 72 gold, y 544). At the bottom:
  CALL OR DM TO BOOK (Bebas 80, y 1318), {phone} · {url} (Bebas 60, y 1396, up by TE+0.67), and
  21+ · VALID LICENSE · INSURANCE (Michroma 28, full opacity, y 1462). The last frame is a complete
  still with no fade.

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
6. **Beat 4 (dial)** is frame-held instead of blended. The dial UI switches Normal from red to white
   between f63 and f64, so a blend or optical flow gave a doubled red/white word. **Beat 5 (pedal)**
   uses optical flow instead of a blend. Both were needed to pass QA gate 4 (no doubled edges).
7. **The black gap** gets no light leak, so it stays pure #000.
8. **Warehouse** frames also get the per-clip NightGrade, so the look matches the tunnel shots.
9. **Fix round 1** (review): the giant word is "RS" (GT3 was the wrong model; "GT3 RS" hides behind the
   roof at the width-limited size). Beat 15 uses the rear tracking shot f206-224 instead of the lamp
   flares. The warehouse freeze is ~7 frames with a light sweep inside it, and the end card lands at
   14.571 (the bed was re-rendered with a quarter-bar tape stop and swell). The end card names the car,
   respects the logo clear space, and uses larger contact/requirement lines. The hook is complete and
   branded on frame 0. The beat-14 wheel is protected from the grade and streaks. The crest brackets
   start on the cut. Details are in README.md, "Fix round 1".
