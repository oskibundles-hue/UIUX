# Flash special showcase: "LOCKED ON" (Porsche 911 GT3 RS), 18 s 9:16 story

**Status: APPROVED by Omarie, 26 Sept 2026.** Delivered to Dropbox: `Supercar Experience/04 Flash Special Stories (2026-09-26)/05 GT3 RS Showcase - LOCKED ON/`.

This is the motion-graphics version of the 26 Sept 2026 flash special. It carries the same offer as the
approved quick cuts (`../flash-special-quick-cut/`), built with the full toolkit:

- tracked callouts locked to the car (door script, Porsche crest)
- slot-reel price with real sub-frame motion blur
- giant type that rises from the floor **behind** the car in the warehouse, using a matte and a 2.5D push
- whips, a drop impact, optical-flow slow motion, anamorphic streaks and light leaks
- a cohesive night grade
- the clip's own music as the bed (fix r2), extended by one musical phrase, with designed accents (whooshes,
  impacts, lock-on ticks, a noise riser, the tape-stop moment) under it

Output: `exports/SCE_Flash-Special-Showcase_GT3RS-Locked-On_18s-9x16.mp4`. The file is H.264 High,
yuv420p, 1080x1920, 23.976 fps (the source rate, so there is no 24->30 judder), CRF 16, with
AAC 48 kHz stereo 192k at -14 LUFS (true peak <= -2 dBTP, also for the -3 dB mono fold-down; the last
~68 ms are digital silence) and +faststart. Audio and picture are both 18.018 s. Also in `exports/`: `poster.jpg` (the first frame:
the complete hook with ENDS 1 PM and the SCE lockup), `poster-endcard.jpg` (the held last frame, an
alternate cover with the logo, the car name, the price, the text line and the Instagram handle), `contact-sheet.jpg`, and `qa/` (check stills and the loudness/probe summary). The mp4 is not committed
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
| TEXT OR DM TO BOOK · (725) 425-3583 · SUPERCAREXP.VIP · SE logo | Omarie, 26 Sept (fix r2): the footage is Las Vegas, and (888) 678-6079 is the Scottsdale location line on supercarexp.vip, so the spot uses the site-wide text line (725) 425-3583 and says TEXT, not CALL |
| @SUPERCAR_EXPERIENCE_ (end card, fix r2) | Omarie, 26 Sept: show the handle so a DM has somewhere to go |
| 21+ · VALID DRIVER'S LICENSE · INSURANCE (end card) | Omarie's brief; fix r2 uses the same wording as the requirements beat |

The ad shows no horsepower, 0-60, top speed, discount, "save $X", testimonial or countdown. The slot
reels only ever show blurred intermediates and land on the true digits; every reel frame was checked at
100 %. All copy scored 5/5 CLEAN in SlopMonster (`deslop.py`).

## Change the price, hours or end time

Edit **`config.json`**, the only place figures live, then run `python3 build.py`.

```json
{"endTime":"1 PM","hours":5,"price":"$1,200","reelDigits":"1200","brand":"PORSCHE","model":"911 GT3 RS",
 "year":"2025","cls":"EXOTIC","giant":"RS","phone":"(725) 425-3583","url":"SUPERCAREXP.VIP",
 "cta":"TEXT OR DM TO BOOK","handle":"@SUPERCAR_EXPERIENCE_"}
```

The HTML layer reads it through `.work/config.js`, which the build writes. The behind-car Python layer
reads it directly. Both layers re-render on their own: the plate and front caches are keyed to a
signature of their code and inputs, so a `config.json` change re-renders the warehouse frames and the
front layer. The decoded source and optical-flow caches are reused.

After a copy change, check the width. `$1,200` at 330 px fills the offer panel, so a longer price
needs a smaller size in `front.html`. The behind-car words in `lib/warehouse.py` are auto-fitted
(`fit_size`): each takes the largest size, up to its cap, whose ink stays inside x 58-900 at the type
layer's push. The giant word caps at 720 px. The price caps at 332 px on baseline y 911 (fix r2: was
372 px -> 360 on y 968), so every digit clears the car's roof and wing at full push, with at least 14 px to spare. A longer
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
   views in place (f226-246, f9-22, and f206-224, the r1 beat-15 shot, which is no longer in the cut).
2. `dense`: optical-flow in-betweens for the beat-14 slow motion.
3. `timeline`: the per-frame source map from `lib/edl.py`.
4. `plate`: `lib/plate.py` + `lib/warehouse.py`.
5. `front`: `front.html` captured by `lib/kcapture.js` with sub-frame motion blur.
6. `audio` (fix r2): `audio/bed_music.py` -> `audio/bed_music.wav`, rebuilt when the script is newer.
7. `finish`: alpha over, vignette, grain, then x264 with the bed muxed as-is.
8. `qa`: stills from the delivered mp4, contact sheet, loudnorm print, ffprobe, and (fix r2) the
   last-50 ms silence, the mono fold-down peaks and the A/V durations.

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
| `audio/bed_music.wav` (+ `bed_music_sync.json`, `bed_music.py`, `synth.py`) | fix r2: the delivered bed. The clip's own music, extended by one phrase, with the designed accents under it (-14.0 LUFS, -2.0 dBTP, 18.018 s). `build.py` rebuilds it when the script changes (`python3 audio/bed_music.py`). It is muxed as-is; do not loudnorm it again. |
| `audio/bed_hero.wav` (+ `bed_hero_sync.json`, `bed_hero.py`) | the r1 synthetic trap/cinematic bed. It is no longer used and is kept for reference. |

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
| `audio/bed_hero.py` | `showcase/direct-hero/` | fix r1: `--tapestop-len` / `--swell-len`, and it imports the vendored `audio/synth.py`, not the scratchpad copy (not used since fix r2) |
| `audio/bed_music.py` | new (fix r2) | the music bed; imports `audio/synth.py` for the accents |
| `audio/synth.py` | `showcase/rnd-sound/synth.py` | none (vendored in fix r1) |

## Footage and sound

The footage is SE's own `GT3RS_livery.mov` (Dropbox `Supercar Experience/01 Car Footage`, cleared,
unbranded), night tunnel and warehouse, and it is the only clip in the picture. The daytime clip
(`GT3RS_white.mov`) and the Black Series are not in this cut.

**Sound (fix r2).** Omarie: "Keep music as well if the videos ever have any." The bed is now the clip's
own music track (`audio/bed_music.py`). It plays continuously and is never cut at a picture cut. The
music is 13.97 s and the picture 18.018 s, so it had to be extended. The options were tried in order:

1. **Continue from `GT3RS_white.mov`: not possible.** Its audio is a different track. 2 s windows of the
   livery music cross-correlate against the whole white audio at |NCC| 0.10-0.11 at best (the same
   recording would be above 0.8). It has no stable ~130 BPM pulse, and its spectrum differs (34 % of the
   energy under 120 Hz, against 68 %).
2. **Used: a beat-matched loop extension.** The livery music repeats its phrase every 5.4914 s
   (12 beats at ~131 BPM). Orig 0.7-2.2 s matches 6.2-7.7 s at NCC 0.79-0.82, with the lag refined to the
   sample (263 587). The music plays through that phrase once more: after orig 6.476 s it continues
   from orig 0.985 s. Both sides of that point are a quiet spot (a -26 dB envelope dip) just before the
   phrase's downbeat, and the join is a 12 ms equal-power crossfade. The head is trimmed by 0.976 s (the
   thinnest part of the intro), so the clip's strongest transient (orig 4.056 s) lands on the DROP at
   8.571 s and a kick (orig 10.041 s) lands on the end-card hit at 14.571 s (15 ms early). The join sits at
   5.500 s, 71 ms before the whip into beat 11. There is no time-stretch at all.
3. The tape-stop fallback was not needed.

The designed accents sit under the music at 45 % (-7 dB) of its RMS over each accent's own span (the
end-card impact at 50 %): the open impact, five whooshes, lock-on ticks (door bracket 3.84 / 4.02, crest
6.69, the four reel lands 9.000-9.429), a noise riser into the black gap, the drop impact, impact_2 at
12.0, the tape-stop moment (the running music, varispeed-stopped, 13.714-14.143, with the main music
dipped 4 dB until the end-card hit), a reversed cymbal swell, and the end-card impact. Every synthetic
musical layer that would clash with the track has been removed: pad, 808, the kick/clap/hat pattern, the
pluck arp, braams, bells, the riser's saw stack, the swell's chord, and the synthetic flat-six engines.
The mix is limited with a detector that includes the -3 dB mono sum, then gained to -14.0 LUFS. It ends
on a fade from 17.35 s to digital silence at 17.95 s.

Nobody has listened to it yet: all audio checks were numeric (loudness, peaks, envelopes,
cross-correlation). **Before posting, Omarie should listen on a phone speaker and on headphones**,
mainly to the phrase join at 5.50 s and the tape-stop moment at 13.7 s. Also confirm the music is cleared
for paid use: it came with SE's own clip, but the track itself was not identified.

## Known limits

- The carbon roof is nearly the same value as the warehouse background, so the matte edge over the
  white GT3 has a ~1 px soft dark rim. It is invisible at phone size.
- Fix r2: the behind-car `$1,200` now clears the roof and wing completely (every digit is whole). The
  depth comes from the price rising out from behind the car and from the 2.5D push.
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

## Fix round 2 (review findings and Omarie's decisions, 26 Sept)

| Finding / decision | Fix |
|---|---|
| Phone: (888) 678-6079 is the Scottsdale line, and the footage is Las Vegas | `config.json` `phone` is the site-wide text line (725) 425-3583. The CTA is TEXT OR DM TO BOOK (`cta`). |
| Show the Instagram handle so a DM has somewhere to go | @SUPERCAR_EXPERIENCE_ (`handle`), Bebas 60 under the contact line. The bottom stack is CTA y 1310, contact 1384, handle 1440, requirements 1500; all ink stays above y 1536 (bottom safe zone). |
| Keep the clip's music | See "Footage and sound". Option (b) was used: a beat-matched extension by one whole phrase, with no time-stretch. |
| End click (the file ended on a thump cut mid-waveform) | The music and the accents fade 17.35-17.95 s, and the last ~68 ms are exact zeros (checked on the mp4 decode, `exports/qa/qa_summary.json`). |
| Matte seam: a dark crescent trailed the rear quarter during the push | The clean plate was swapped into a 9 px ring OUTSIDE the matte, and the r1 diffusion fill there was darker than the real floor/wall. The swap now covers only the car itself (matte + 2 px), so the real plate is kept next to the car, and the fill is a pull-push inpaint (nearest background, never black) built from the 9 px-dilated hole. `lib/warehouse.py`. |
| Blown wheels in beat 15 | In the rear tracking shot (f206-224) the spinning wheels are pale, spoke-less discs in the source itself (wheel-box p95 228/230/231 before any FX). A lower FX gain cannot make them red, so beat 15 now uses the tunnel side pass (f27-39, see the next table): the car is revealed from behind a passing dark car and its red wheels read. It has strict point-source streaks at 0.5 and full warm-hue protect, so the grade cannot crush the wheels. No plate is visible. |
| End card said VALID LICENSE | Now 21+ · VALID DRIVER'S LICENSE · INSURANCE. Michroma 28 cannot fit that inside x 907, so the line is set in Bebas 40, as the requirement lines of beat F are. Its cap height is about 29 px, larger than the ~20 px it had. |
| Roof/wing covered the bottom of the "00" | The behind-car price is 332 px on baseline 911 (was 360 px on 968). Checked on every end-card frame: the minimum gap between digit ink and the car's top edge is 15 px. |
| Mono fold-down on big hits | The limiter's detector includes 0.707·(L+R), so the -3 dB mono fold-down true peak stays under the same -2 dBTP ceiling as L and R. |

## Fix round 2, review (26 Sept)

| Finding | Fix |
|---|---|
| Beat 15's front wheel sat in a dark box, with a blue-white bloom on the mirror (stale plate cache) | The r2 `plate.done.json` was a bare list of frame numbers, so frames rendered before the last `lib/edl.py` edit were never redone. It now stores a signature per frame: the plate and fx code, the source cache markers, the edl constants, the frame's timeline row and beat, and for warehouse frames the warehouse code, matte data and `config.json`. A whip window shares one signature. The front layer has a signature file too (`.work/front.sig`). The r3 build re-rendered all 432 plate frames and the whole front layer from the current code. On the mp4, f262-f276 show a clean white front arch and red rims with visible spokes, and no box or bloom. |
| For the first frames of beat 15 the only car under the price was the passing dark sedan, and the 0.63x blend doubled its wheel and headlight over the GT3 RS | Beat 15 now starts at f27, where the GT3 RS front is already in frame, and f27-29 sit inside the whip. The sedan's exit (f27-32) plays at 1.0x on whole source frames, so nothing is blended and no double image is possible. Then the speed eases to 0.45x once the GT3 RS is alone (f32 to f39.3, `keys` in `lib/edl.py`). The sedan-only frames f24-26 are gone. Beat 15 and the hook now share f34-39 of the same side pass, 10.7 s apart and framed differently (lowered 120 px, under the price panel). |



## Audio fix after review round 2 (lead session, 26 Sept 2026)

- **Tape stop.** The running music now hands over to its own varispeed stop at 13.714 s. The track fades out
  over 60 ms and comes back on the end-card hit at 14.571 s, so the stop is the music itself and no longer a
  copy playing on top of it. Before this, the two doubled at near equal level. Measured on the mp4:
  13.75 s -12.2 dB, 14.30 s -44.7 dB (the break), 14.60 s -13.5 dB.
- **Start.** An 8 ms fade-in on the music removes the step on sample 0.
- Loudness after the change: I -14.10 LUFS, TP -2.18 dBTP.
- **Delivery copy.** The master is about 68 MB at CRF because of the grain. A two-pass 11.5 Mb/s copy (about 25 MB) is
  what goes to the phone and Dropbox, since Instagram re-encodes anyway.
- **Still open (should-fix from craft review r2).** Beat 15 reuses the hook's tunnel side pass, and
  GT3RS_livery.mov has no other clean side shot. A second clip of this car would fix it.
