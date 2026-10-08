# Vlog kit: the Locked-On layer for vlogs (22 variations, 9 components)

**What it is.** Omarie asked for "variations of the locked on layer specifically for vlogging … custom create the
overlays as well because I still want the Supercarexperience banner on the side but get creative". This folder is
that kit: a reusable, config-driven set of animated components in the `locked-on` language
(`../../09-campaign-ads/HOUSE-STYLE.md`), with a still of every variation over real footage and a review reel that
animates each one. It builds on the approved rally layer (`../2026-09-15-rally/`) and reuses the showcase's
libraries (`kinetic.js`, `kcapture.js`, `track.py`, `fx.py`). **Status: not reviewed yet.** Nothing here has been
posted.

| Deliverable | Path |
|---|---|
| All components, one page, `window.renderAt(t)` | `kit.html` + `lib/sekit.js` |
| One still per variation (1080x1920 JPG over real frames) | `mockups/A1_corner-bug.jpg` … `mockups/I3_whip-pan-helper.jpg` |
| Board with every variation labelled | `mockups/BOARD.jpg` |
| Review reel, 39.2 s, 1080x1920, 29.97 fps, corner code tags | `exports/vlog-kit-reel_DELIVERY.mp4` (two-pass, under 30 MiB). The CRF master `exports/vlog-kit-reel.mp4` (32 MiB) is git-ignored |
| QA stills and summary | `exports/qa/` (`qa_summary.json`) |

Say the codes: "use A2, B1, H1".

## Footage

- **DJI_0029** (14.4 s, 4K HEVC 10-bit portrait, 59.94 fps). Camera clock: file `DJI_20260915224905_0029`,
  creation time 05:49:06Z = **22:49:05** local, Sep 15 2026. **This is the Red Rock Casino parking garage**, after dinner
  at Lotus of Siam (inside Red Rock), with the guests lining up to drive back to the Venetian (footage survey, 27 Sep).
  The brief called it the Venetian rooftop; the survey corrected that, so every place stamp over it reads RED ROCK CASINO
  (VENETIAN appears only as a stop on the route line, which is where the drive back went).
  Converted to a 1080x1920 29.97 fps mezzanine (every other frame, Lanczos, CRF 12) in `.work/src/`. Stills of single
  frames are pulled from the 4K source, so Ken Burns pushes up to 2x stay sharp.
- **The approved rally cut** (`rally_ig.mp4`): two caption-free frames, f3180 (the drive back, Rolls-Royce hood) and f3300
  (Las Vegas Blvd, the Strip). A low-anchored zoom (1.30x or more) keeps its burned-in SE bug (y 296-338) out of frame;
  `build.py` asserts it.
- Sound: the clip's own audio at low level (-9 dB, about -21 LUFS while it plays) only where DJI_0029 plays at 1x,
  crossfaded through the whip and faded under the first sweep. Silence over the stills. No music, nothing synthesised.

## The components and their variations

Every component is a factory in `lib/sekit.js` (`SEK.<type>(cfg)`, `cfg = {code, t0, t1, p}`), a pure function of t.
Defaults live in the factory; any param can be set per instance (the reel's instances are in `build.py`,
`scene_components`). Common to all: black plates with the horizontal 78/22 stripe cap, gold #FBD101 as the only
accent, Bebas for display, Michroma for labels, glyph-level kinetic type (rise, tracking collapse, glints) and true
sub-frame motion blur on every fast move.

### A. SE side banner (persistent)

| Code | Type | What | Params |
|---|---|---|---|
| **A1** | `bannerBug` | The approved top-right bug, refined: black plate with a stripe cap, the white lockup with a gold glint every 5.5 s, a live dot, RALLY DAY and the optional co-billing × EGNYTE on the same row. Plate y 292-390, right edge x 1040 | `x1, y, label, cobill, built, glintAt, glintEvery, morphOut` |
| **A2** | `bannerTab` | A slim tab flush with the right edge, x 992-1080, from y 300 (it grows to fit, never past y 1056): stripe cap (horizontal), the SE mark, a pulsing live dot, SUPERCAR EXPERIENCE (+ × EGNYTE in gold) and RALLY DAY · LAS VEGAS set vertically, and a gold progress rail that fills with the video | `w, y, h, name, label, cobill, enter ('built'/'slide'), progress [t0, t1], exit` |
| **A3** | `bannerBreathe` | Rests as a 96 px tile with the mark (and an optional × EGNYTE strip under it); at each chapter change it inhales left with the chapter tag and name (back-out ease, a ring ripple, the mark pulses), holds 1.9 s and exhales | `x1, y, size, cobill, chapters [{t, tag, title, hold}], enter, exit` |

All three sit inside the banner zone (right edge, y 269-1056) and above the caption band, so they never meet the
captions or the Reels buttons. They are solid black plates (0.9) with white/gold content and a soft shadow, so they read
on the blown concrete and on the night sky alike (the A1 mockup is on the brightest frame of the clip).

### B. Person lock-on (tracked with `lib/track.py`)

| Code | Type | What | Params |
|---|---|---|---|
| **B1** | `personLock` | Corner brackets fly in from 1.8x and snap onto the face, a lock ping, a leader up into the name tag OMARIE / @NQ.YOUNG. The tag follows at 40 % of the face's motion so the type stays calm | `track, name, handle, acquire, exit, maxBottom (clears the captions), whip, follow` |
| **B2** | `personReticle` | A HUD reticle: the ring draws on while it shrinks onto the face, four arc segments spin in and settle, a counter-rotating tick crown, crosshair gaps, LOCKED · HOST, and a compact tag on a 45-degree leader | `track, name, handle, acquire, exit, status, follow` |
| **B3** | `guestLock` | Full-body brackets from an upper-body track, a scan line sweeps down the guest on lock, EGNYTE GUEST / LOCKED ON above the head (the label is `name`, set from `config.json` `copy.guest`) | `track, name, kicker, acquire, exit, legs, head, follow` |

### C. Convoy lock-on

| Code | Type | What | Params |
|---|---|---|---|
| **C1** | `convoyHop` | One bracket set hops car to car (outExpo with an arc, a dashed ghost of the last lock), counter CAR 01 / 03 and the make. The label wipes out with the old car and back in on the new one, so no type flies across the frame | `segs [{track, t, make, placeholder, mode: acquire/hop/relock, lost}], total, exit, follow` |
| **C2** | `convoyScan` | A scan beam sweeps across the lineup; each car it passes gets small brackets and a numbered chip; a panel counts 00 → 05 LOCKED | `targets [{track}], ts, sweep, x0, x1, title, px, py, exit` |
| **C3** | `leadLock` | Lead-car lock: brackets, three gold chevrons climbing above the car, LEAD CAR / ROLLS-ROYCE CULLINAN and Omarie's own line "I'LL BE LEADING EVERYBODY" | `track, kicker, name, quote, quoteBy, acquire, exit, side, follow` |

### D. Clock and place

| Code | Type | What | Params |
|---|---|---|---|
| **D1** | `clockStamp` | 22:49 in Bebas with gold seconds that tick from the file's clock (each second rolls over in its last 0.16 s), RED ROCK CASINO, SEP 15 2026 | `x, y, start ('22:49:05'), place, date, built, fixed, handoff` |
| **D2** | `clockJump` | Time-jump transition: a black card wipes up, HH:MM slot reels roll from the last clip's clock to the next (blurred while fast, landing gold on the true digits), the gap (+2 H 25 MIN) and the place track in, then the clock flies into the D1 stamp | `from, to, place, date, lands, handoff {x, y, size}` |

### E. Route line (schematic, no map)

| Code | Type | What | Params |
|---|---|---|---|
| **E1** | `routeCompact` | Corner panel: a metro-style line with two 45-degree jogs through 215 → 15 NORTH → FLAMINGO → LAS VEGAS BLVD → VENETIAN → LEVEL 9; done segments gold, the rest dashed; a comet runs to each new stop, the active stop pulses and underlines, counter 04 / 06 | `x, y, title, waypoints, steps [{t, k}], exit` |
| **E2** | `routeFull` | Full frame over a scrim: the same route snaking down the frame, big labels, the comet travels the whole drive, each stop lands with a ripple, LEVEL 9 blooms; slow push | `title, sub, waypoints, steps, scrim, exit` |

### F. Guest testimonial

| Code | Type | What | Params |
|---|---|---|---|
| **F1** | `quoteCard` | Card in the lower middle: a hanging gold quote mark, EGNYTE GUEST (`label`) with a live dot, a 14-bar live audio meter with peak caps, the quote revealed word by word (each word rises in and flashes gold) | `label, quote or words [{w, t}], wordGap, start, footer, meter, y, exit` |
| **F2** | `quoteSplit` | Q&A split: host on the top half, guest on the bottom, a horizontal stripe seam; Q chip + HOW WAS IT? slams in on top, A chip + EGNYTE GUEST (`label`) + meter + the answer word by word below | `q, host, handle, a, label, qt, at, wordGap, meter, seam, exit` |

### G. Chapter slam

| Code | Type | What | Params |
|---|---|---|---|
| **G1** | `chapterSlam` | A huge Bebas title slams down (1.55x → 1 with 270-degree motion blur), the plate takes a small zoom punch and a two-frame shake, the gold stripe wipes under it with a light edge, the tag tracks in, a glint. Works as an opening hook too; an optional co-billing line (`cobill`, e.g. SUPERCAR EXPERIENCE × EGNYTE) tracks in under the stripe | `tag, title, y, maxW, maxS, cobill, exit, punch` |
| **G2** | `chapterGlass` | For busy shots: the title sits on frosted glass (the compositor blurs and dims the plate inside the panel), the glass unrolls from its stripe cap, a sheen crosses it | `tag, title, x, y, w, maxS, exit` |

### H. Captions (y 58-72 %, centred on the safe area, x 480)

| Code | Type | What | Params |
|---|---|---|---|
| **H1** | `captionsBox` | Boxed karaoke: every word of the phrase on black line plates, spoken words white, upcoming words dim, the active word on a gold box that glides word to word | `words [[t0, t1, w]], size, yBottom, maxLines, maxW, cx` |
| **H2** | `captionsStrip` | Speaker strip: a gold speaker tab (OMARIE), words pop on as spoken (scale and rise), the newest word in gold, one line that pages | `words, speaker, size, y, maxW, cx` |

### I. Transition kit

| Code | Type | What |
|---|---|---|
| **I1** | `sweep` | Gold light sweep: a slanted band with a white core crosses the frame; the compositor switches plates along its centre line (new shot on the left) with a soft edge. Params `angle, width` |
| **I2** | `convoyHop` mode `relock` | Lock lost / re-acquire across a cut: the brackets open up, pull into the frame and breathe while the label reads LOCK LOST, then fly to the new target and snap with a ping. No flicker, no RGB split (`lost` sets the search time) |
| **I3** | shot `fx: 'whip'` | Whip-pan helper: `lib/fx.py` `whip()` between the last frames of shot A and the first of shot B (config `aTail`, `bHead`, `dir`); a lock can ride it (`personLock` `whip` param) and kcapture blurs it at 270 degrees |

## Recommended set for the vlog

**A2 · B1 · B3 · C1 (+ I2) · C3 · D1 · D2 · E1 · F1 · G1 · H1 · I1**, with **G2** instead of G1 on busy shots.

- **A2** as the persistent banner: it keeps the SE name on screen for the whole vlog in the one place nothing else
  uses (the right edge, above the buttons), it is the smallest footprint of the three, and its progress rail gives the
  side banner a job. With × EGNYTE on for this client vlog (it costs nothing in layout: the tab just grows). Keep **A1** if Omarie prefers the familiar bug; **A3** is the lighter chapter marker for vlogs
  with many short chapters.
- **B1** introduces the host with the follow-card details; **B3** is the same system for a guest. B2 is the showier
  option, better for a single hero moment than for every appearance.
- **C1** reads one car at a time with a counter, so each make is readable; **I2** keeps the lock alive across cuts.
  **C3** is the lead-car moment, with Omarie's own line. C2 looks great in motion but its chips are small on a phone.
- **D1** at every new place, **D2** for the big jumps (arrival → after dinner).
- **E1** during the convoy briefing (it sits beside the guide); **E2** works as a transition card before the drive.
- **H1** as the default captions: the plates keep them readable on the bright garage floor and on night sky. H2 for fast
  back-and-forth talk.
- **G1** on clean shots; **G2** on the Strip and other busy frames.

## Placeholders and things to confirm before publishing

| On screen | Where | What to do |
|---|---|---|
| `[MAKE]` (dashed box) | C1, CAR 02 (grey convertible with Y-spoke wheels, red calipers, 6.0 s into DJI_0029) | Probably a Lamborghini Huracán, not certain. Replace in `config.json` `copy.cars.convertible` |
| `[GUEST QUOTE GOES HERE, VERBATIM, WORD FOR WORD FROM THE CLIP]` | F1 | A real guest's words, verbatim, with word times from the clip (`words`) |
| `[GUEST ANSWER, VERBATIM]` | F2 | Same |
| `HOW WAS IT?` | F2 | The brief's example question; use what the host actually asks |
| EGNYTE GUEST on the woman in the lineup | B3, F1, F2 | She is a stand-in from the lineup shot; confirm she is one of the Egnyte group (or use a confirmed guest) and that she is happy to be shown |
| Meter levels | F1, F2 | Demo data: the band levels of the host's own speech in DJI_0029, 7.0-10.6 s (`lib/data/meter.json`). In a real cut, run `make_meter` on the guest's audio |
| Captions | H1, H2 | From the auto transcript of DJI_0029 (whisper, word level, `lib/data/transcript_0029.json`). Check the words against the audio |
| CAR 0N / 03 | C1 | 03 is the number of cars the brackets visit in that shot, not the rally's car count |
| CH 04 / 05 / 06 | G1, G2, A3 | Chapter numbers are illustrative; number them to the real vlog |

## Every on-screen line and its source

| Line | Source |
|---|---|
| OMARIE · @NQ.YOUNG | the approved follow card ("Omarie Young @nq.young") |
| EGNYTE GUEST, LOCKED ON | the rally was for Egnyte and the guests are the Egnyte group (coordinator, 27 Sep). The brief's RALLY GUEST is the fallback: set `copy.guest`. Text only, no Egnyte logo |
| × EGNYTE (co-billing on A1, A2, A3) | same; optional (`copy.banner.cobill`, set it to null to drop it). Text only |
| EGNYTE RALLY DAY · SEP 15 2026 · LAS VEGAS (F1 footer) | same, with the brief's date and city |
| SUPERCAR EXPERIENCE lockup, mark | `02-logos/png/` |
| RALLY DAY · LAS VEGAS | the brief |
| 22:49:05 and the ticking seconds | DJI_0029's clock (22:49:05 local) plus the clip time of the frame on screen |
| RED ROCK CASINO | footage survey: DJI_0029 is the Red Rock Casino garage (the CASINO sign is in shot) |
| SEP 15 2026 | the brief and the file dates |
| 20:24 (D2 from) | DJI_0019's clock (creation 03:24:37Z = 20:24 local), the "couple more of the group just landed … collect your keys" clip at Red Rock |
| +2 H 25 MIN | derived: 22:49 minus 20:24 |
| 215, 15 NORTH, FLAMINGO, LAS VEGAS BLVD, VENETIAN, LEVEL 9 | the brief, from the guide's briefing ("215 out of here", "15 north", "Flamingo", "Las Vegas Boulevard", "Venetian", "the ninth floor") |
| RED ROCK TO THE VENETIAN | footage survey: the drive back ran from Red Rock to Venetian level 9 |
| LAMBORGHINI (grey widebody Urus, red Urus) | identified on the footage: both are Urus bodies (SE's own Mansory-bodied Urus is in `brand-tokens.json`). Make only |
| LEAD CAR · ROLLS-ROYCE CULLINAN | footage survey: Omarie leads the convoy in the all-black Cullinan; its Spirit of Ecstasy is visible on the hood at 12.5 s |
| "I'LL BE LEADING EVERYBODY" — OMARIE | Omarie on camera (footage survey transcript) |
| THE LINEUP, THE DRIVE BACK, LEVEL 9 | chapter names: the lineup is what is on screen (and Omarie's own "we got the lineup right here"), the others the rally cut's chapters |
| Caption words | DJI_0029, what the host says (auto transcript) |
| Reel code chip (top-left), LOCKED-ON · VLOG KIT index card | review annotations only, not part of the kit |

No speeds, horsepower, prices, guest names or client logos anywhere.

## Layout rules the kit enforces

- Text stays in x 54-907, y 269-1536 (top 14 %, bottom 20 %, left 5 %, right 16 % kept clear). Only the banner (A1-A3)
  may use the right edge, between y 269 and 1056. Tags clamp into the safe area as their targets move.
- Captions (H1, H2) live in y 1114-1382, centred on the safe area; B1 takes `maxBottom` so its brackets stop above them.
- The 78/22 stripe is always horizontal: caps on every plate, the tab's cap, the chapter wipes, the split seam.
- Nothing is half-built on frame 0 of the reel: A1, D1, H1 and the code chip are complete on the first frame.
- Glints, pings and flashes are short and soft (the slam flash was toned down after the first render to avoid a halo).

## How to render

```bash
./render.sh                          # = python3 build.py: prep, layer, reel, delivery copy, mockups + board, QA (~15 min)
python3 build.py --stage reel        # layer capture (3 Chromium processes, ~5 min) + composite + audio -> exports/
python3 build.py --stage mocks       # mockups/*.jpg + BOARD.jpg (~30 s)
python3 build.py --stage deliver     # two-pass copy under 30 MiB
python3 build.py --stage qa          # safe-zone audit, probe, check stills -> exports/qa/
python3 build.py --stills 1.5,12.3   # composite single reel times -> .work/stills/
```

Needs Python 3 with numpy and Pillow, Node 22 with Playwright at `/opt/node22/lib/node_modules/playwright` (Chromium is
preinstalled; never run `playwright install`), and the static ffmpeg (`config.json` `tools.ffmpeg`, or `FFMPEG=`).
Layer frames are cached in `.work/layer/` by frame number: delete the frames you changed (or the folder) after an edit.

Stages: `prep` (mezzanine, plate JPGs, 4K stills, `.work/scene.js`, `.work/tracks.js`, `.work/kitdata.js` with the meter
data and the logo masks) → `layer` (`kit.html` through `lib/kcapture.js`: 1 sample on holds, up to 16 over a 270-degree
shutter on whips, slams and reels; the page's `window.FX` goes to a per-frame sidecar) → `reel` (`lib/compose.py`: plate
mapping identical to the page's, Ken Burns, whip, sweep line, glass blur, the G1 punch, then the layer; x264 CRF 17,
AAC) → `deliver` → `mocks` (`lib/mockcap.js` renders each code alone at its hero time) → `qa`.

### Using a component in a new vlog

1. Put the copy in `config.json` `copy`, the shots in `reel.shots` (clip frames or stills), and add instances in
   `build.py` `scene_components` (code, type, t0, t1, params). `kit.html#only=B1,A2` previews single codes.
2. Track a target (one shot, no cut inside) with the showcase tracker, or from a sharp middle frame with the wrapper:

```bash
python3 lib/track_mid.py --video .work/src/rooftop_mezz.mov --ffmpeg FF --name cullinan --f0 352 --f1 413 --anchor 375 \
    --box 72,270,340,322 --scale-pen 0.2 --out lib/data/tracks.json
python3 lib/trackqa.py --video .work/src/rooftop_mezz.mov --ffmpeg FF --tracks lib/data/tracks.json --names cullinan --out qa.jpg
```

Tracks in `lib/data/tracks.json` (DJI_0029 mezzanine frames): `face1` f0-64 (conf 0.85-0.93), `face2` f348-429
(0.77-0.95), `urusG` f150-194 (0.74-0.97), `conv` f170-208, `urusR` f228-300 (good to f282), `guest` f236-312 (good
f252-296), `far1`-`far5` f296-336 (small cars; checked on the QA sheet), `cullinan` f352-413 (good to f402). Every
track was checked on a contact sheet of boxes drawn on the frames.

## The reel (39.2 s)

| Time | Footage | Codes |
|---|---|---|
| 0.00-2.14 | DJI_0029 0.0-2.1 s, host | A1 · B1 · D1 · H1 |
| 2.14-2.40 | whip into the cars | I3 |
| 2.40-5.71 | DJI_0029 3.7-7.0 s, the lineup | G1 (THE LINEUP) → C1 CAR 01 LAMBORGHINI → CAR 02 [MAKE] |
| 5.71-7.71 | cut, 7.9-9.8 s | I2 LOCK LOST → CAR 03 LAMBORGHINI, then B3 EGNYTE GUEST; A2 slides in |
| 7.71-9.38 | 9.9-10.9 s at 0.6x | C2 lineup scan |
| 9.38-12.31 | 10.9-13.8 s, host | B2 · H2 · A2 |
| 12.31-12.81 | sweep to the Strip | I1 |
| 12.81-16.12 | rally f3300, Las Vegas Blvd | G2 THE DRIVE BACK, A3 breathes |
| 16.12-19.32 | rally f3180, the drive back | E1 |
| 19.32-19.82 | sweep | I1 |
| 19.82-23.56 | DJI_0029 still, lineup | E2, A3 breathes LEVEL 9 on arrival |
| 23.56-27.56 | still, guest in the lineup | F1 |
| 27.56-31.76 | stills, host / guest | F2 |
| 31.76-34.77 | time card | D2 20:24 → 22:49 |
| 34.77-37.17 | still, host and the Cullinan | D1 (hand-off) · C3 · A1 |
| 37.17-39.17 | index card | all codes |

## How it was checked (`exports/qa/qa_summary.json`, rebuilt by `--stage qa`)

- **Safe zones:** the ink box of every visible text line, clipped by its masks, at every 0.1 s of the reel and at every
  mockup time (417 times): **0 outside** x 54-907 / y 269-1536 (banner text allowed on the right edge, y 269-1056). Six
  hits are transitional only: G1's first slam frames at 1.55x and A2 sliding in and out past the frame edge.
- **Captions:** 0 caption boxes outside y 1114-1382.
- **Frame 0** of the reel has A1, D1, H1 and the code chip fully built (checked on the decoded delivery file).
- **Locks:** every track was drawn on its source frames and checked (`lib/trackqa.py`); stills at the entry, middle and
  exit of every component are in `exports/qa/` (60 stills), and all of them were looked at: the brackets sit on the face,
  the cars, the guest and the Cullinan.
- **Export:** master H.264 High, yuv420p bt709, 1080x1920, 29.97 fps, 39.17 s, CRF 17, 32.1 MiB (git-ignored);
  delivery two-pass 5.8 Mb/s, **25.8 MiB**, AAC 48 kHz, +faststart. Audio -21.7 LUFS, true peak -10.5 dBTP (the clip's
  own sound, low), the last 50 ms silent.
- Fixes made after looking at the renders: the caption gold box was under its plate; the D1 seconds showed the previous
  second; tags followed faces 1:1 and blurred (now 40-50 %); the C1 counter changed beside the old make; the lock-lost
  brackets sat off-frame in white (now gold, pulled into frame); the sweep band read as a blown beam (now a narrow core);
  the G1 impact glow read as a halo (toned down); G1 was centred on the frame and crossed x 907 (now centred on the safe
  area); the D2 reels showed a readable 22:47 on the way (faster reels now); the logo glints never showed because CSS
  masks are blocked on file:// (the logos now go in as data URIs).

## Files

| Path | What |
|---|---|
| `kit.html` | the page: builds the scene's components, `window.renderAt(t)`, `window.setOnly`, `window.inkAudit` |
| `lib/sekit.js` | the component library (all codes) |
| `config.json` | copy, footage, reel shots |
| `build.py`, `render.sh` | scene builder and the one-command build |
| `lib/compose.py` | the compositor (plates, Ken Burns, whip, sweep, glass, punch, layer) |
| `lib/kcapture.js` | copied from the rally layer; adds the per-frame `window.FX` sidecar |
| `lib/mockcap.js` | mockup capture (one code at a time) |
| `lib/track_mid.py`, `lib/trackqa.py` | track from a middle frame both ways (wraps `track.py`); QA sheet of tracked boxes |
| `lib/audit.js`, `lib/qa.py` | safe-zone audit (clip-aware ink boxes), probe, check stills |
| `lib/kinetic.js`, `lib/accum.py`, `lib/track.py`, `lib/lock.js`, `lib/fx.py` | copied unchanged from the showcase / rally layer |
| `lib/data/` | tracks, the DJI_0029 transcript, the meter demo data |
