# Rally vlog, Sep 15: the Locked-On layer (reel cut, 9:16)

**What it is.** The vlog version of the `locked-on` standard (`../../09-campaign-ads/HOUSE-STYLE.md`), built on
top of Omarie Young's approved 2:09 vlog of the Sep 15 rally (T7 cut, "The rally, dinner & the drive back").
Omarie chose this vlog and this option: *"Full vlog + Locked-On layer: keep your cut, voice, captions and music;
add car badge lock-ons, kinetic chapter cards and the Locked-On end card."* The cut, the voice, the captions,
the music and the plate blurs are untouched. Only a motion-graphics layer goes on top, plus quiet sound accents
and 1.6 s of end card.

**Export:** `exports/01 2026-09-15 the rally, dinner and the drive back (reel cut) SE LOCKED-ON - INSTAGRAM 1080x1920.mp4`.
H.264 High, yuv420p (bt709), 1080x1920, 29.97 fps, two-pass 11 Mb/s (10.98 Mb/s video), AAC-LC 48 kHz stereo
256k (245 kb/s average), +faststart (moov before mdat), **183.4 MB**. It has 3,914 frames = 130.597 s: the source is
128.995 s, and 48 frames of end card are added. Video and audio tracks run 130.598 / 130.597 s. Loudness on the mp4
(ffmpeg loudnorm, print): **-14.01 LUFS integrated, -1.66 dBTP true peak, LRA 8.8**, and the last 121 ms decode to
digital silence. The mp4 is git-ignored.
Also in `exports/`: `poster.jpg` (frame 0: the complete hook), `contact-sheet.jpg` (one frame every 2 s), and
`qa/` (a still at the entry, middle and exit of every element, the frame edges of every covering check,
`element-sheet.jpg` and `qa_summary.json`).

## What is on screen

| # | Element | When | Where |
|---|---|---|---|
| A | **Hook panel**, complete on frame 0 (the Instagram preview) | 0-2.60 s, masked exit to 2.98 s | x 54-909, y 362-751. It covers the burned-in title on every frame the title is visible (f3-f77) |
| B | **Chapter cards** CH 01-05 / 05 | 4.47 / 15.58 / 66.77 / 104.07 / 113.68 s | centred, y 388-538. 01 and 02 sit exactly over the burned-in pills |
| C | **THE ROUTE** telemetry card: a gold tick lands on each waypoint on the frame the guide says it | 69.13-88.78 s | top-left, x 54-493, y 222-519, above the guide's head, left of the SE bug |
| D1 | **Lock-on** on the Spirit of Ecstasy: OUR RIDE / ROLLS-ROYCE | 105.00-107.27 s (leaving the lot) | tracked, lower right |
| D2 | **Lock-on** on the lead car: LEAD CAR / LAMBORGHINI URUS | 107.37-113.54 s (on the Strip) | tracked brackets on the Urus, label above-left |
| E | **Locked-On end card**, full frame, replacing the burned-in card | 127.13 s to the end (130.60 s) | full frame |

Every in and out time, and how each anchor was measured on the footage: `cue.md`.

## Every on-screen line and its source

All copy lives in `config.json` (`copy`).

| Line | Source |
|---|---|
| SUPERCAR EXPERIENCE · RALLY DAY | the brief for this layer (hook eyebrow) |
| THE RALLY, / DINNER & THE DRIVE BACK | the approved T7 title "The rally, dinner & the drive back.", set in caps |
| SE lockup in the hook | `02-logos/png/sce-primary-horizontal--white.png` |
| CH 01 / 05 PARKED CARS, CH 02 / 05 WALKING TO DINNER | the approved cut's own beat pills (burned in at 4.7 and 15.9 s), numbered in the order the day ran |
| CH 03 / 05 THE CONVOY BRIEFING, CH 04 / 05 THE DRIVE BACK, CH 05 / 05 LEVEL NINE | the brief's chapter list. LEVEL NINE is the parking structure ("going up to the ninth floor") |
| THE ROUTE | the brief |
| 15 NORTH · OFF ON FLAMINGO · LEFT ON LAS VEGAS BLVD · BACK TO VENETIAN · NINTH FLOOR | **the guide's own words** from the burned-in captions: "It's in a 15 north. We'll be getting off on Flamingo ... taking a left on Las Vegas Boulevard to go back to Venetian ... up to the ninth floor". See the open items for the three labels that differ from the brief |
| counter 0 / 5 to 5 / 5 | derived (the number of waypoints called) |
| OUR RIDE / ROLLS-ROYCE | the Spirit of Ecstasy hood ornament is in frame on the drive back (brand only, no model) |
| LEAD CAR / LAMBORGHINI URUS | the car ahead, identified by its rear light bar and quad exhaust. The rally's plate notes call it "the freeway Urus". No year, variant or spec is given |
| stacked SE logo | `02-logos/png/sce-stacked--white.png` |
| A RIDE OF A LIFETIME. | SE's own tagline: the approved T7 end card, and supercarexp.vip ("A ride of a lifetime. Waiting for you.") |
| TEXT OR DM TO BOOK | the approved Locked-On showcase end card (Omarie, fix r2) |
| (725) 425-3583 | the site-wide text line: supercarexp.vip header "Questions? Text Us (725) 425-3583", `brand-tokens.json` `phones.text`, the T7 card |
| SUPERCAREXP.VIP | the site, and the T7 card |
| @SUPERCAR_EXPERIENCE_ | supercarexp.vip contact page, the T7 card |
| LAS VEGAS · SCOTTSDALE · BOISE | supercarexp.vip ("Las Vegas · Scottsdale · Boise"), and the T7 card's locations |
| RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE | Omarie, 26 Sept: include the age requirement as the site words it. supercarexp.vip booking steps: "Renter Must Be 25+ (Ages 21–24 With $299 Underage Fee)", checked 26 Sept. Set in the house requirements style (Bebas 44, white, gold dot), between the locations and the credit |
| FILMED BY @NQ.YOUNG | Omarie's handle, as on the approved follow card ("Omarie Young @nq.young") |

There are no prices, specs, horsepower, years or offers anywhere. The one figure on screen is the site's own underage
fee, in the requirement line.

## Sound

The vlog's own audio (his voice and the music) is the main track, unedited: no EQ, no ducking, no cuts.
It gets one static gain (+0.44 dB, -14.44 to -14.00 LUFS for the whole mix), an L/R true-peak limiter at
-1.75 dBTP that touches 0.06 % of the samples by at most 0.2 dB, and a 40 ms fade on its last samples, where it
ended on a non-zero sample. The showcase also limited a 0.707·(L+R) mono fold-down. This vlog's master already
breaks that rule by about 3 dB on centred content, so enforcing it would have squashed the approved mix (a first
try limited 15 % of the samples by more than 0.5 dB). It was dropped. Accents
(`lib/mix.py`, synthesised with the showcase's `synth.py`, so they are original):

- a soft whoosh on each chapter card (5)
- lock-on ticks: acquire and lock on each car lock (4), and one on each route waypoint, landing on the spoken
  word (5)
- an impact on the end card (1)

Each accent's loudest 50 ms sits **20 dB under the programme around it**, and the whole accent bus is ducked
**a further 6 dB while a word is being spoken**. Measured on the accent bus (`.work/accents.wav`) against the
programme: the 6 unducked accents (the whooshes for CH 02 and CH 05, and the four car-lock ticks) sit at -19.7 to
-20.0 dB. The 8 accents under speech (the whooshes for CH 01, CH 03 and CH 04, and the five route ticks) sit at
-25.9 to -26.1 dB. The end-card impact, which starts as his last words end, sits at -23.7 dB. The speech signal is the burned-in caption word highlight
(`lib/data/captions.json`). The route ticks land on words by design, so they are always ducked.

The tail: the picture runs 1.6 s past the source audio. The music's own decay carries on (a wet-only reverb of its
last 0.8 s, with no dry repeat) under the end-card impact's tail. It fades to silence, and the last 65 ms are
exact zeros. Measured on the delivered mp4 with `ffmpeg loudnorm` (print): see `exports/qa/qa_summary.json`.

## How to rebuild

```bash
./render.sh                        # = python3 build.py: everything, ~13 min on the 4-CPU box
python3 build.py --stage qa        # QA only, on the existing export
python3 build.py --stills 0,142,2114,3810   # composite single frames -> .work/stills/ (no mp4)
```

Needs Python 3 with numpy and Pillow, Node 22 with Playwright at `/opt/node22/lib/node_modules/playwright`
(Chromium preinstalled; never run `playwright install`), and the static ffmpeg (`config.json` `source.ffmpeg`, or
`--ffmpeg`/`FFMPEG=`). The source video path is `config.json` `source.video` (or `--video`/`VIDEO=`).

Stages (cached in `.work/`): `prep` (config and tracks to JS, and the page's timing tables) -> `front` (story.html
captured with sub-frame motion blur, only the ~1,400 frames where something is on screen, 3 Chromium processes,
~2 min) -> `audio` (`lib/mix.py`, ~2.5 min) -> `compose` (ffmpeg: source + 48 black frames, overlay the PNG layer
in RGB, bt709, x264 two-pass, ~6 min) -> `qa` (~2 min). Every layer PNG is kept RGBA. Chromium writes an opaque
screenshot as RGB, and a sequence that switches pixel format makes ffmpeg re-initialise the overlay graph, which
dropped the layer on 5 end-card frames in one build. `lib/accum.py` and `build.py` both normalise it now, and QA
catches it.

To change a line, edit `config.json` and rerun. To re-measure, the anchors are also in `config.json`
(`anchors`). `lib/capscan.py` re-scans the captions, and `lib/track.py` re-tracks a car:

```bash
python3 lib/track.py --video SRC --ffmpeg FF --name urus --f0 3215 --f1 3406 --box 372,912,320,213 --out lib/data/tracks.json
python3 lib/track.py --video SRC --ffmpeg FF --name soe  --f0 3119 --f1 3214 --box 730,1222,175,178 --out lib/data/tracks.json
```

## How it was verified (`exports/qa/qa_summary.json`, rebuilt on every run)

- **Hook covers the old title:** the layer's alpha is 255 over the title box (+6 px) on every frame from f0 to f77.
  The old title is visible f3-f77 (measured), and the exit starts on f78. The mp4 frames were also checked one by one
  from f0 to f4 and from f76 to f90.
- **CH 01 and CH 02 cover the pills:** alpha 255 over each pill box (x1.05 for its scale-in, +4 px) from one frame
  before the pill appears to its last visible frame (f141-f205, f475-f538). The edge frames were checked on the mp4.
- **Nothing on the SE bug** (any frame before the end card), **the follow card** (33.5-38.5 s) **or the captions**
  (every frame within ±20 frames of a highlighted word): the layer's alpha there is 0.
- **Route ticks on the word:** for each waypoint, the tick box has no gold on the frame before the word is
  highlighted and a gold fill on the word frame (f2114, f2161, f2374, f2405, f2548).
- **End card:** alpha 255 over the full frame from f3814 to the last frame. The old card's first darkening is at
  ~f3815 and its logo at f3817. The card is fully built at 127.727 s and readable for 2.87 s.
- **End to end:** the whole mp4 is decoded, and on every layer frame the opaque interior of the layer matches the
  delivered pixels (worst mean difference 3.5 levels, from x264).
- **Locks:** stills across both shots show the brackets on the Urus from acquire to exit with no drift (tracker
  conf >= 0.98, forward/backward error <= 0.1 %) and on the Spirit of Ecstasy throughout (conf >= 0.90).
- **Audio:** loudnorm print on the mp4, the decoded tail, the track durations, and the accent levels on the accent bus.

## Files

| Path | What |
|---|---|
| `config.json` | every on-screen line, plus the measured frame anchors |
| `cue.md` | every element with its in and out times, and how each anchor was measured |
| `story.html` | the layer: `window.renderAt(t)`, a pure function of t (no CSS animation, no clock) |
| `build.py`, `render.sh` | the one-command build |
| `lib/kinetic.js`, `lib/kcapture.js`, `lib/accum.py`, `lib/track.py`, `lib/lock.js` | copied from `09-campaign-ads/flash-special-showcase/lib/`. `kcapture.js` adds a `list` mode, fps as a fraction, and fatal page errors. `track.py` runs at 30000/1001 fps. `lock.js` is kept for reference: `story.html` draws its own brackets in the same style |
| `lib/synth.py` | copied from `flash-special-showcase/audio/`, unchanged |
| `lib/mix.py` | the sound (see above) |
| `lib/capscan.py`, `lib/data/captions.json` | the caption word-highlight scan (speech activity and the caption-clear check) |
| `lib/data/tracks.json` | the two tracks (Urus f3215-3406, conf 0.98-0.99, forward/backward error <= 0.1 %; Spirit of Ecstasy f3119-3214, conf 0.90-0.98, <= 1.1 %) |
| `lib/pageinfo.js` | prints the page's timing tables for the build |

## Open items

1. **Three route labels differ from the brief's wording,** because the brief also said to use the guide's own words.
   The brief's "OFF AT FLAMINGO" is now OFF ON FLAMINGO ("getting off on Flamingo"), "THE VENETIAN" is BACK TO
   VENETIAN ("to go back to Venetian"), and "LEVEL 9" is NINTH FLOOR ("up to the ninth floor"). "15 NORTH" is
   captioned "It's in a 15 north": he says I-15. Change `config.json` `copy.route.waypoints` if the brief's wording is preferred.
2. **215.** The guide opens with "We are going to take 215 out of here" (67.6 s). It is not on the card, because the
   brief listed five waypoints starting at 15 NORTH. Adding it is one line in `config.json`, but the card would need
   a sixth row.
3. **Nobody has listened yet.** All audio checks were numeric (loudness, true peak, the accent levels against the
   programme, the ducking, the silent tail). Listen on a phone speaker and on headphones, mainly for the ticks
   under the briefing and the end-card tail.
4. **Chapters 01 and 02 hold for 2.2 s**, a little over the brief's 1.6-2.0 s, because the burned-in pills are
   on screen for 2.1 s and the cards have to cover them for the whole time. 03-05 hold for 1.7-1.9 s.
5. **The route card starts at y 222 (11.6 %),** above the brief's "about 15 %". Five readable lines have to fit
   above the guide's head, whose top is at y 520-580, and his raised hand reaches y ~480. At that size the card cannot
   sit lower without covering his head. It stays left of the SE bug and well clear of the captions.
6. **The Rolls-Royce lock overlaps the end of CH 04** for about 1.3 s (105.0-106.3 s). The ornament shot is only
   3.2 s long, and the label needs 1.2 s of clean read. The card is in the top band and the lock in the lower half.
7. **The brief placed the SE bug at y 3-5 %.** It is at y 296-338 (15.4-17.6 %) on this cut. Everything is laid
   out against the measured position.
8. **Music rights**: this is the vlog's own track, unchanged. It is cleared as far as the approved T7 cut is.
