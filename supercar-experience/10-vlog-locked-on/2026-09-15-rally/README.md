# Rally vlog, Sep 15: the Locked-On layer (reel cut, 9:16)

**What it is.** The vlog version of the `locked-on` standard (`../../09-campaign-ads/HOUSE-STYLE.md`), built on
top of Omarie Young's approved 2:09 vlog of the Sep 15 rally (T7 cut, "The rally, dinner & the drive back").
Omarie chose this vlog and this option: *"Full vlog + Locked-On layer: keep your cut, voice, captions and music;
add car badge lock-ons, kinetic chapter cards and the Locked-On end card."* The cut, the voice, the captions,
the music and the plate blurs are untouched. Only a motion-graphics layer goes on top, plus quiet sound accents
and 1.6 s of end card.

**Export:** `exports/01 2026-09-15 the rally, dinner and the drive back (reel cut) SE LOCKED-ON - INSTAGRAM 1080x1920.mp4`.
H.264 High, yuv420p (bt709), 1080x1920, 29.97 fps, two-pass 11 Mb/s, AAC 48 kHz stereo 256k, +faststart,
3,914 frames = 130.597 s (the source is 128.995 s, and 48 frames of end card are added). The mp4 is git-ignored.
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
| FILMED BY @NQ.YOUNG | Omarie's handle, as on the approved follow card ("Omarie Young @nq.young") |

There are no prices, specs, horsepower, years or offers anywhere. The age requirement is left off on purpose (see
the open items).

## Sound

The vlog's own audio (his voice and the music) is the main track, sample for sample: no EQ, no ducking, no edits.
It gets one static gain from -14.5 to -14.0 LUFS, a transparent true-peak limiter that only touches the few peaks
above -2.3 dBTP, and a 40 ms fade on its last samples, where it ended on a non-zero sample. Accents
(`lib/mix.py`, synthesised with the showcase's `synth.py`, so they are original):

- a soft whoosh on each chapter card (5)
- lock-on ticks: acquire and lock on each car lock (4), and one on each route waypoint, landing on the spoken
  word (5)
- an impact on the end card (1)

Each accent's loudest 50 ms sits **20 dB under the programme around it**, and the whole accent bus is ducked
**a further 6 dB while a word is being spoken**. The speech signal is the burned-in caption word highlight
(`lib/data/captions.json`). The route ticks land on words by design, so they are always ducked.

The tail: the picture runs 1.6 s past the source audio. The music's own decay carries on (a wet-only reverb of its
last 0.8 s, with no dry repeat) under the end-card impact's tail. It fades to silence, and the last 65 ms are
exact zeros. Measured on the delivered mp4 with `ffmpeg loudnorm` (print): see `exports/qa/qa_summary.json`.

## How to rebuild

```bash
./render.sh                        # = python3 build.py: everything, ~12 min on the 4-CPU box
python3 build.py --stage qa        # QA only, on the existing export
python3 build.py --stills 0,142,2114,3810   # composite single frames -> .work/stills/ (no mp4)
```

Needs Python 3 with numpy and Pillow, Node 22 with Playwright at `/opt/node22/lib/node_modules/playwright`
(Chromium preinstalled; never run `playwright install`), and the static ffmpeg (`config.json` `source.ffmpeg`, or
`--ffmpeg`/`FFMPEG=`). The source video path is `config.json` `source.video` (or `--video`/`VIDEO=`).

Stages (cached in `.work/`): `prep` (config and tracks to JS, and the page's timing tables) -> `front` (story.html
captured with sub-frame motion blur, only the ~1,400 frames where something is on screen, 3 Chromium processes,
~2 min) -> `audio` (`lib/mix.py`, ~2 min) -> `compose` (ffmpeg: source + 48 black frames, overlay the PNG layer
in RGB, bt709, x264 two-pass, ~8 min) -> `qa`.

To change a line, edit `config.json` and rerun. To re-measure, the anchors are also in `config.json`
(`anchors`). `lib/capscan.py` re-scans the captions, and `lib/track.py` re-tracks a car:

```bash
python3 lib/track.py --video SRC --ffmpeg FF --name urus --f0 3215 --f1 3406 --box 372,912,320,213 --out lib/data/tracks.json
python3 lib/track.py --video SRC --ffmpeg FF --name soe  --f0 3119 --f1 3214 --box 730,1222,175,178 --out lib/data/tracks.json
```

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

1. **Age requirement, left off the end card.** It conflicts: supercarexp.vip says "Renter Must Be 25+ (Ages 21-24
   With $299 Underage Fee)", the approved T7 card says "25+ Renter must be 25+", and today's ads say 21+. Decide
   the line and add it to the card if it should be there.
2. **Three route labels differ from the brief's wording,** because the brief also said to use the guide's own words.
   The brief's "OFF AT FLAMINGO" is now OFF ON FLAMINGO ("getting off on Flamingo"), "THE VENETIAN" is BACK TO
   VENETIAN ("to go back to Venetian"), and "LEVEL 9" is NINTH FLOOR ("up to the ninth floor"). "15 NORTH" is
   captioned "It's in a 15 north": he says I-15. Change `config.json` `copy.route.waypoints` if the brief's wording is preferred.
3. **215.** The guide opens with "We are going to take 215 out of here" (67.6 s). It is not on the card, because the
   brief listed five waypoints starting at 15 NORTH. Adding it is one line in `config.json`, but the card would need
   a sixth row.
4. **Nobody has listened yet.** All audio checks were numeric (loudness, true peak, the accent levels against the
   programme, the ducking, the silent tail). Listen on a phone speaker and on headphones, mainly for the ticks
   under the briefing and the end-card tail.
5. **Chapters 01 and 02 hold for 2.2 s**, a little over the brief's 1.6-2.0 s, because the burned-in pills are
   on screen for 2.1 s and the cards have to cover them for the whole time. 03-05 hold for 1.7-1.9 s.
6. **The route card starts at y 222 (11.6 %),** above the brief's "about 15 %". Five readable lines have to fit
   above the guide's head, whose top is at y 520-580, and his raised hand reaches y ~480. At that size the card cannot
   sit lower without covering his head. It stays left of the SE bug and well clear of the captions.
7. **The Rolls-Royce lock overlaps the end of CH 04** for about 1.3 s (105.0-106.3 s). The ornament shot is only
   3.2 s long, and the label needs 1.2 s of clean read. The card is in the top band and the lock in the lower half.
8. **The brief placed the SE bug at y 3-5 %.** It is at y 296-338 (15.4-17.6 %) on this cut. Everything is laid
   out against the measured position.
9. **Music rights**: this is the vlog's own track, unchanged. It is cleared as far as the approved T7 cut is.
