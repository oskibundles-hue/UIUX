# Flash special showcase: "LOCKED ON" (Porsche 911 GT3 RS), 18 s 9:16 story

This is the motion-graphics version of the 26 Sept 2026 flash special. It carries the same offer as the
approved quick cuts (`../flash-special-quick-cut/`), built with the full toolkit:

- tracked callouts locked to the car (door script, Porsche crest)
- slot-reel price with real sub-frame motion blur
- giant type that rises from the floor **behind** the car in the warehouse, using a matte and a 2.5D push
- whips, a drop impact, optical-flow slow motion, anamorphic streaks and light leaks
- a cohesive night grade
- a synthesized trap/cinematic bed cut to the grid, with a tape stop into the end card

Output: `exports/SCE_Flash-Special-Showcase_GT3RS-Locked-On_18s-9x16.mp4`. The file is H.264 High,
yuv420p, 1080x1920, 23.976 fps (the source rate, so there is no 24->30 judder), CRF 16, with
AAC 48 kHz stereo 192k at -14 LUFS and +faststart. Also in `exports/`: `poster.jpg` (the first frame:
the complete hook with ENDS 1 PM and the SCE lockup), `poster-endcard.jpg` (the held last frame, an
alternate cover with the logo, the car name, the price and the contact line), `contact-sheet.jpg`, and `qa/` (check stills and the loudness/probe summary). The mp4 is not committed
(`.gitignore`); it is delivered.

## On screen, and where each line comes from

| Line | Source |
|---|---|
| FLASH SPECIAL · TODAY ONLY · ENDS 1 PM + SCE lockup (hook, frame 0) | Omarie's brief, 26 Sept 2026 ("today only", ends 1 PM); logo `02-logos/png/sce-primary-horizontal--white.png` |
| PORSCHE · 911 GT3 RS · 2025 · EXOTIC | `01-brand-core/brand-tokens.json` / supercarexp.vip listing ("2025 · Exotic") |
| 5 HOURS · $1,200 · OUT THE DOOR | Omarie's brief ("5 hours, $1,200 out the door") |
| RS (giant, behind the car) | the model's designation (911 GT3 **RS**). Fix r1: it read "GT3", a different, cheaper model. "GT3 RS" does not fit: at the width-limited size (408 px) the "RS" sits behind the roof and only its top third shows. "RS" alone runs at 720 px on the left, where the hood is low, and reads cleanly. The full name is on the crest callout and on the end card. |
| YOU NEED · VALID DRIVER'S LICENSE · 21+ · INSURANCE | Omarie's brief (requirements) |
| PORSCHE 911 GT3 RS (end card, fix r1) | brand tokens (`C.brand` + `C.model`) |
| 5 HOURS · OUT THE DOOR · TODAY ONLY · ENDS 1 PM · $1,200 (end card) | Omarie's brief |
| CALL OR DM TO BOOK · (888) 678-6079 · SUPERCAREXP.VIP · SE logo | brand tokens |
| 21+ · VALID LICENSE · INSURANCE (end card) | Omarie's brief |

The ad shows no horsepower, 0-60, top speed, discount, "save $X", testimonial or countdown. The slot
reels only ever show blurred intermediates and land on the true digits; every reel frame was checked at
100 %. All copy scored 5/5 CLEAN in SlopMonster (`deslop.py`).

## Change the price, hours or end time

Edit **`config.json`**, the only place figures live, then run `python3 build.py`.

```json
{"endTime":"1 PM","hours":5,"price":"$1,200","reelDigits":"1200","brand":"PORSCHE","model":"911 GT3 RS",
 "year":"2025","cls":"EXOTIC","giant":"RS","phone":"(888) 678-6079","url":"SUPERCAREXP.VIP"}
```

The HTML layer reads it through `.work/config.js`, which the build writes. The behind-car Python layer
reads it directly. Delete `.work/plate.done.json` and `.work/front/` so both layers re-render;
the decoded source and optical-flow caches are reused.

After a copy change, check the width. `$1,200` at 330 px fills the offer panel, so a longer price
needs a smaller size in `front.html`. The behind-car words in `lib/warehouse.py` are auto-fitted
(`fit_size`): each takes the largest size, up to its cap, whose ink stays inside x 58-900 at the type
layer's push. The giant word caps at 720 px and the price at 372 px, landing at 360 px. A longer
`giant` word gets smaller automatically. Check that it still clears the car's roof (see the "RS" note
above).

## Re-render

```bash
python3 build.py            # or ./render.sh; ~10-12 min on the 4-CPU box
python3 build.py --qa       # QA gate: only the check frames -> exports/qa/gate_*.jpg (about 1.5 min)
python3 build.py --frames 0,206,370   # single frames -> .work/stills/
```

Defaults: ffmpeg is `scratchpad/ffmpeg`, footage is `scratchpad/footage/`. Override with `--ffmpeg` /
`--footage` or `FFMPEG=`. The build needs Python 3 with numpy + Pillow, and Node 22 with Playwright
at `/opt/node22/lib/node_modules/playwright`.

Stages (each is cached in `.work/`):
1. `source`: decode `GT3RS_livery.mov` in frame order (never `-ss`), then blur the three licence-plate
   views in place (f226-246, f9-22, and f206-224 for the beat-15 rear tracking shot).
2. `dense`: optical-flow in-betweens for the beat-14 slow motion.
3. `timeline`: the per-frame source map from `lib/edl.py`.
4. `plate`: `lib/plate.py` + `lib/warehouse.py`.
5. `front`: `front.html` captured by `lib/kcapture.js` with sub-frame motion blur.
6. `finish`: alpha over, vignette, grain, then x264 with the bed muxed as-is.
7. `qa`: stills from the delivered mp4, contact sheet, loudnorm print and ffprobe.

## Files

| Path | What |
|---|---|
| `config.json` | every figure / claim string (edit here) |
| `cue.md` | the final build cue as built, including the deviations and the reason for each |
| `front.html` | the front motion layer, `window.renderAt(t)`, fonts via `../../07-fonts/`, logo via `../../02-logos/png/` |
| `build.py` / `render.sh` | the one-command build |
| `lib/edl.py` | the beat table (timing and plate FX only, no copy) |
| `lib/plate.py` | the plate renderer: frame-exact sampling, plate blur, optical flow, whips, impact, leaks |
| `lib/warehouse.py` | the behind-car type, matte, 2.5D push and warehouse FX |
| `audio/bed_hero.wav` (+ `bed_hero_sync.json`, `bed_hero.py`, `synth.py`) | the mastered 18.0 s bed (-14.00 LUFS / -2.02 dBTP), with the tape stop and swell at a quarter bar each, so the end card lands at 14.571 s. It is used as-is; do not loudnorm it again. Regenerate with `python3 audio/bed_hero.py --whoosh 1,2,3.25,6.25,7.5 --tapestop-len 0.25 --swell-len 0.25 --out audio/bed_hero`. |

The R&D modules in `lib/` are copies, not symlinks:

| File | Source in the session scratchpad | Changes |
|---|---|---|
| `lib/fx.py` | `showcase/rnd-fx/fx.py` | none |
| `lib/matte_lib.py` | `showcase/rnd-matte/matte_lib.py` | none |
| `lib/data/matte_ref.png`, `lib/data/ware_track.json` | `showcase/rnd-matte/out/` | none. The index k of `ware_track.json` is source frame 290 + k. |
| `lib/kinetic.js` | `showcase/rnd-type/kinetic.js` | none |
| `lib/accum.py` | `showcase/rnd-type/accum.py` | none |
| `lib/kcapture.js` | `showcase/rnd-type/kcapture.js` | adds a `frames` mode and fractional fps |
| `lib/lock.js`, `lib/track.py`, `lib/data/tracks.json` | `showcase/rnd-track/` | none |
| `lib/data/plate_track.json` | `judge/plate_track.json` | none |
| `lib/data/plate2_track.json` | new | tracked with `lib/track.py`, f9-22, box 880,1730,90,188 |
| `lib/data/plate3_track.json` | new (fix r1) | tracked with `lib/track.py --scale-pen 0.3`, f206-224, box 262,943,118,59 (conf mean 0.92, FB error at most 0.5 %) |
| `audio/bed_hero.py` | `showcase/direct-hero/` | fix r1: `--tapestop-len` / `--swell-len`, and it imports the vendored `audio/synth.py`, not the scratchpad copy |
| `audio/synth.py` | `showcase/rnd-sound/synth.py` | none (vendored in fix r1) |

## Footage and sound

The footage is SE's own `GT3RS_livery.mov` (Dropbox `Supercar Experience/01 Car Footage`, cleared,
unbranded), night tunnel and warehouse. Nothing else is used. The daytime clip and the Black Series are
not in this cut. The clip's own audio is not used.

The bed is synthesized in numpy (`audio/bed_hero.py`): 140 BPM, F minor, with engine layers from a
firing-pulse model. Nobody has listened to it yet: all audio checks were numeric (loudness, peaks,
spectrograms). **Before posting, Omarie should listen on a phone speaker and on headphones.** If the
synthetic engine sounds fake, re-render the bed with `python3 audio/bed_hero.py --no-engine` and
rebuild.

## Known limits

- The carbon roof is nearly the same value as the warehouse background, so the matte edge over the
  white GT3 has a ~1 px soft dark rim. It is invisible at phone size.
- The last "0" of the behind-car `$1,200` is partly hidden by the rear-wing endplate (about 10 % of the
  word). This is deliberate, because it sells the depth, and the price still reads.
- The warehouse shot is only 1.84 s of source stretched to 6 s (0.45x / a ~7-frame freeze / 0.267x
  cross-blend). The camera is locked off, so the motion comes from the layers: a continuous 2.5D push
  (car 1.00 -> 1.070, type -> 1.055, background -> 1.028, which never pauses), the giant RS rise and
  sink, a light sweep across the car inside the freeze, the gold floor hairline, the $1,200 rise and two
  price glints.

## Fix round 1 (review findings)

| Finding | Fix |
|---|---|
| Giant word "GT3" names the wrong model | It is now "RS" at 720 px (see the table above). `config.json` `giant`. |
| End card never names the car | "PORSCHE 911 GT3 RS" (Michroma 30, PORSCHE in gold) above the offer line, from `C.brand` + `C.model`. |
| Logo clear space on the end card | The stack starts at y 384, 52 px under the lockup's ink (282-332). One icon height is 50 px. |
| Hook panel bleeds off the right edge; no brand in the first 3 s | The panel is 846 wide, matching the stripe cap and the offer panel. The white SCE lockup (240 px) sits on the ENDS row from frame 0. |
| Frame 0 / poster missing ENDS 1 PM | ENDS 1 PM is set on frame 0. At 0.429 s it gets a re-hit: a 4-frame 1.06 pulse and a gold glint. `poster.jpg` is frame 0, and `poster-endcard.jpg` is the last frame. |
| Contact and requirements too small and too brief | The phone and URL are Bebas 60, one line, cap height about 43 px (was Michroma 28, about 20 px). The requirements are Michroma 28 at full opacity. The end card now lands at 14.571 s, not 15.429, and the phone line is fully up from 15.24 s, which is 2.78 s on screen. |
| Dead 25-frame freeze | The tape stop and the audio swell are now a quarter bar each. The picture is effectively frozen for about 7 frames (13.97-14.25 s) and resumes with a 6-frame ease-in. Inside the freeze: a light sweep across the car body (13.93-14.47) and the gold floor hairline (14.00-14.40). The push never pauses, and a second price glint runs at 17.13-17.73 s so the last 2 s keep moving. |
| Beat-15 flare strobe | The shot is replaced with the unused rear tracking shot f206-224, 0.9x, lowered 210 px so the car sits under the price panel. Its plate is tracked and blurred. |
| Beat-14 wheel turns into a dark box | The streaks use a stricter point-source test (thresh 0.93, point 0.25, radius 60) at gain 0.8 above and below y 820. A warm-hue protect (0.75) pulls orange/red source pixels back toward the source, so the copper wheel stays round and lit. |
| Crest brackets fly in before the cut, stepped blur | The fly-in starts on the cut (6.402 s) and runs over 7 frames, captured at k=28 / 270 deg (6.39-6.75 s). |
