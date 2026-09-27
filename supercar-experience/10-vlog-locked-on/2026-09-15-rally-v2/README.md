# Rally vlog v2, Sep 15 (Egnyte rally day): rebuilt from the raw footage, Locked-On for vlogs (9:16)

**What it is.** Omarie Young's ask: "remake the whole video from scratch using our raw footage… make the video and the
dynamic motion graphics like you did here and the overlays… catching all key moments… show me your skills like you did the
Porsche video but in vlog format… I still want the Supercarexperience banner on the side". Omarie added on 27 Sept that the
rally was for **Egnyte**: the name appears as text only (no Egnyte marks anywhere). This folder renders the approved edit
decisions (the EDL, 174.5 s) at the `locked-on` standard (`../../09-campaign-ads/HOUSE-STYLE.md`): a new picture edit and grade
from the camera files, a new sound mix, and a Locked-On layer built from the vlog kit (`../vlog-kit/`) plus this vlog's own
components. **Status: not reviewed yet.**

**Exports** (`exports/`, git-ignored; `2026-09-15 rally day (Egnyte) - SE LOCKED-ON vlog v2 …`):

| File | What |
|---|---|
| `… - 1080x1920.mp4` | **the master.** H.264 High, yuv420p bt709, 1080x1920, 29.97 fps, two-pass 10.95 Mb/s, AAC-LC 48 kHz stereo 256k, +faststart, **238.8 MB**. 5230 frames = 174.508 s; video / audio tracks 174.508 / 174.507 s. Loudness on the mp4 (ffmpeg loudnorm): **-14.11 LUFS integrated, -1.82 dBTP true peak**, LRA 3.0; the last 101 ms decode to digital silence |
| `… - NO MUSIC - 1080x1920.mp4` | the same picture stream with dialog + nat + SFX only (for a trending sound in Instagram): 227.4 MiB, -14.06 LUFS, -1.89 dBTP |
| `… - PREVIEW 720x1280.mp4` | phone preview, two-pass 1.15 Mb/s, AAC 160k (the mix 0.5 dB lower so AAC holds the true peak): **27.5 MiB** (< 30 MiB), -14.63 LUFS, -2.05 dBTP |
| `… - music-stem.wav` | the music alone, exactly as it sits in the master (ducked, at the master's gain), 24-bit 48 kHz, 50 MB |
| `poster.jpg`, `contact-sheet.jpg` | frame 0 (the complete hook: the story preview) and one frame every 2 s |
| `qa/` | first / middle / last frame of every EDL beat (`beat_*`), in / middle / out of every graphic (`el_*`), `beats-sheet.jpg`, `elements-sheet.jpg`, `shots-sheet.jpg` (every shot's first / middle / last frame: the grade check), the tracker sheets `track_*.jpg`, and `qa_summary.json` |

No `_DELIVERY` copy: the master is already 10.95 Mb/s, under the 11.5 Mb/s delivery rate.

## What is on screen

| # | Element | When (s) | Where |
|---|---|---|---|
| HOOK | **Hook panel**, complete on frame 0 (the story preview): SUPERCAR EXPERIENCE × EGNYTE · RALLY DAY, THE RALLY, LAS VEGAS · SEP 15 2026, SE lockup. Glints on the hold, masked exit | 0 – 1.87 | x 54-907, y 330-790 |
| A2 | **SE side banner** (vlog kit A2 edge tab, the kit's recommendation): SE mark, live dot, SUPERCAR EXPERIENCE / RALLY DAY · LAS VEGAS set vertically, a gold progress rail that fills with the video | slides in 1.62, out at the end card 170.02 | right edge x 992-1080, y 300-900; never meets the captions (x 130-830) |
| G1 ×7 | **Chapter slams** (kit G1): camera-clock tag HH:MM · CH 0N / 07 over the title, 1.55x → 1 slam with motion blur, stripe, glint, a plate punch | 7.05 RALLY DAY · 26.08 THE LINEUP · 54.29 EGNYTE ARRIVES · 79.04 ROLL OUT · 87.74 RED ROCK · 116.81 THE DRIVE BACK · 147.97 THE VERDICT (≈1.9 s each) | top band, title y 350 (faces stay clear) |
| I1 ×6 | **Gold light sweep** at every chapter change: the layer draws the band, the plate switches along its centre line (old shot keeps playing on the right) | 25.88 · 54.09 · 78.84 · 87.54 · 116.61 · 147.77 (0.36 s) | full frame |
| B1 | **Host name lock** (kit B1): OMARIE · @NQ.YOUNG on the tracked face | 9.2 – 11.35 | tracked |
| C1 | **Convoy lock-on hop** (kit C1 + I2 lock lost / re-acquire) while Omarie names the lineup, counter CAR 0N / 06: LAMBORGHINI URUS → CORVETTE Z06 → LAMBORGHINI HURACÁN EVO → MERCEDES-AMG GT BLACK SERIES → PORSCHE 911 GT3 RS → ROLLS-ROYCE CULLINAN. A car that leaves frame on a pan is released with LOCK LOST and the next one is locked once it is in frame; a direct hop only while both cars are in frame | Urus 30.96; LOCK LOST 32.30 → Corvette 33.03; Huracán 35.08; LOCK LOST 35.86 → Black Series 36.57; GT3 RS 37.18 (on "GT3s"); LOCK LOST 37.80 → Cullinan 38.64; out 40.45 | tracked on the lineup walk |
| CTA | **CTA chip**: TEXT OR DM TO BOOK · (725) 425-3583 · @SUPERCAR_EXPERIENCE_ | 45.15 – 54.0 ("If you ever need to book with us for a large event…") | top-left |
| SLAM | **SAFELY.** kinetic slam | lands 63.66 on the word (63.63), out 64.6 | top band |
| R8 | **Lock-on** LOCKED ON · AUDI R8 | 67.85 – 69.5 | tracked |
| C3 | **Lead-car lock** (kit C3, climbing lead chevrons): LEAD CAR · ROLLS-ROYCE CULLINAN | 74.9 – 77.0 | tracked |
| E-CH4 | **Route card** under the CH4 slam: VENETIAN → BLUE DIAMOND → RED ROCK, a comet ticks each stop | 79.3 – 82.8 | panel x 54-907, y 800-1250 |
| D1 | **Clock + place stamp** (kit D1): 21:39 → 21:40 with the camera's own seconds ticking, LOTUS OF SIAM · RED ROCK CASINO, SEP 15 2026 | 94.35 – 101.65 | top-left |
| F1 | **Host's pick card** (kit F1 quote card): header tab FAVOURITE OF THE FLEET, label OMARIE · @NQ.YOUNG, Omarie's words verbatim, word by word, with a live meter driven by their own audio | 101.8 – 110.45 | top, y 340, header tab above its right end (Omarie's face is lower in frame) |
| ROMA | **Lock-on** OMARIE'S PICK · FERRARI ROMA (on the red colour-shift coupe once the camera turns to the garage) | 106.35 – 108.25 | tracked, label below |
| PLACE | **Place tag** TEAM DINNER · YARD HOUSE | 110.62 – 116.4 | top-left |
| E1 | **Route line** (kit E1 language, laid out as a strip): 215 → 15 NORTH → FLAMINGO → LAS VEGAS BLVD → VENETIAN → LEVEL 9. 215 and 15 NORTH flash gold when the guide names them (129.74, 132.37); each stop ticks on its montage shot (135.77, 137.77, 139.77, 141.77, 144.27, 146.27), counter 00 → 06 / 06 | 129.45 – 147.72 | top band y 290-534 (the briefing's faces fill the upper left, so the kit's corner panel would cover them) |
| D1 | **Rolling camera clock** 23:00:08 → 23:20:06, BACK TO THE VENETIAN (each montage shot shows its own real time) | 135.9 – 147.7 | bottom-left |
| URUS | **Lock-on** FOLLOW THAT CAR · LAMBORGHINI URUS on the purple Urus ahead | 141.95 – 144.2 | tracked |
| WALL | **Quote wall**: EGNYTE ON THE DAY, then WONDERFUL · GOOD TIME · AWESOME · AMAZING · GOOD EXPERIENCE, each chip slamming in as it is said | 150.55 – 161.5 (words at 150.84 / 152.16 / 156.07 / 156.85 / 160.62) | top band |
| H1 | **Captions** (kit H1 boxed karaoke), active word on a gold box | every dialog piece 4.0 – 170.0 | y 1190-1382 (62-72 %), x 130-830 |
| END | **End card** (the approved rally layer's) | 170.02 – end | full frame |

Every in / out time and how each anchor was found: `cue.md`. All copy lives in `config.json` (`layer.comps`).

## Every on-screen line and its source

| Line | Source |
|---|---|
| SUPERCAR EXPERIENCE × EGNYTE · RALLY DAY (hook eyebrow) | the brief; EGNYTE: Omarie, 27 Sept ("the rally was for the company Egnyte"), text only |
| THE RALLY / LAS VEGAS · SEP 15 2026 (hook title) | the approved v1 hook ("THE RALLY,"); the place (Venetian, Red Rock) and the date are the camera files' (DJI_20260915…) |
| SE lockup, stacked SE logo, SE mark | `02-logos/png/` |
| SUPERCAR EXPERIENCE · RALLY DAY · LAS VEGAS (side banner) | the vlog kit's A2 banner copy |
| HH:MM · CH 0N / 07 and the chapter titles | titles: the EDL (`chapters`); CH 03 is EGNYTE ARRIVES (Omarie, 27 Sept). Clocks: the camera clock of the chapter's first frame = the file name's start time + the shot's in-point (see "Clocks" below) |
| OMARIE · @NQ.YOUNG | the approved follow card ("Omarie Young @nq.young") |
| CAR 0N / 06 + LAMBORGHINI URUS, CORVETTE Z06, LAMBORGHINI HURACÁN EVO, MERCEDES-AMG GT BLACK SERIES, PORSCHE 911 GT3 RS, ROLLS-ROYCE CULLINAN; LOCK LOST | Omarie naming the lineup on camera ("Black Series, Uruses, Corvette, Huracán EVOs, GT3s, Rolls-Royce Cullinan"), each label only on the car that is in frame and identified on the footage (see "Lock-ons") |
| TEXT OR DM TO BOOK · (725) 425-3583 · @SUPERCAR_EXPERIENCE_ (CTA chip) | the approved Locked-On end card and `brand-tokens.json` `phones.text`; shown while Omarie says "If you ever need to book with us for a large event…" |
| SAFELY. | Omarie's own word ("That's our number one thing. Safely."), on the word |
| LOCKED ON · AUDI R8 | Omarie: "you'll get the R8… the R8, Audi R8"; the car on screen |
| LEAD CAR · ROLLS-ROYCE CULLINAN | Omarie: "I am in the all black Cullinan. I'll be leading everybody." |
| THE ROUTE · VENETIAN → BLUE DIAMOND → RED ROCK | the brief, and Omarie on camera: "straight up Blue Diamond into Red Rock Loop" (0015, about 6:43), named again in 0019 and 0022 (CH4 route card) |
| 21:39:xx · LOTUS OF SIAM · RED ROCK CASINO · SEP 15 2026 | the iPhone clip's clock (P2139a, 21:39:36); Omarie: "I'm going to go down to Lotus of Siam"; the brief |
| FAVOURITE OF THE FLEET · OMARIE · @NQ.YOUNG + the quote | Omarie's own words (0021, the selfie at the Red Rock table, answering a guest's question about their favourite car), verbatim from the audio in the cut (captions.json), word by word; "…" marks where the edit drops words ("maybe", and the rest of the last sentence). Handle: the approved follow card |
| OMARIE'S PICK · FERRARI ROMA | Omarie: "Out of all those cars, I would say … the Roma" |
| TEAM DINNER · YARD HOUSE | Omarie: "We are currently eating at Yard House."; the brief |
| THE ROUTE · 215 → 15 NORTH → FLAMINGO → LAS VEGAS BLVD → VENETIAN → LEVEL 9 | the guide's briefing ("take 215 out of here… to the 15 North") and the brief; 215 and 15 NORTH flash when the guide says them |
| 23:00:xx → 23:20:xx · BACK TO THE VENETIAN | the camera clock of each montage shot (0032, 23:00:03 + in-point); Omarie: "We're gonna go back to the Venetian" |
| FOLLOW THAT CAR · LAMBORGHINI URUS | the guide: "look at what car is in front of you. Follow that car."; the purple Urus ahead |
| EGNYTE ON THE DAY + WONDERFUL · GOOD TIME · AWESOME · AMAZING · GOOD EXPERIENCE | the guests' own words in CH7 (captions.json), each stacked as it is said; header wording: Omarie, 27 Sept |
| Captions | captions.json (corrected word timings), active word in gold; hidden while the SAFELY. slam, the host's pick card or the quote wall already shows the same words. "Ignite" (a Whisper mishearing of Egnyte) would be corrected to "Egnyte"; none of the pieces in the cut contains it |
| End card: A RIDE OF A LIFETIME. · TEXT OR DM TO BOOK · (725) 425-3583 · SUPERCAREXP.VIP · @SUPERCAR_EXPERIENCE_ · LAS VEGAS · SCOTTSDALE · BOISE · RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE · FILMED BY @NQ.YOUNG | the approved rally layer's end card (`../2026-09-15-rally/README.md` has every source) |

No speeds, horsepower, prices (other than the site's underage fee on the end card), guest names or Formula Dynamics marks
in the graphics. Omarie's shirt in the footage is untouched.

## Sound

**Music: original, and easy to remove.** The raw footage has no music and Omarie said "if you want music use whatever to
make it happen, just make it easy to remove in case I don't like it, and make it lower when anyone's speaking". The bed is
made here from scratch (`lib/music.py` on the showcase's `synth.py`: numpy only, fixed seeds, no samples), so it is ours to
use. F minor, i-VI-III-VII (Fm Db Ab Eb), 105.11 BPM, trap-house kit with a light swing on the off-16ths, an 808 on the
chord roots, a detuned saw pad, a returning two-bar pluck hook (C Ab G F | Ab F Eb C), one-bar risers into every chapter
change, a riser and a 1/8-bar gap into the CH6 convoy montage (the drop, +6 dB over the verse), a breakdown under the
guests in CH7, the music's own tape stop (168.88–169.45 s) and a bell sting on the end card. The tempo is set by the cut:
the drop (135.77 s) and the end card (170.02 s) are exactly 15 bars apart, so both land on a downbeat. Checked on its own:
peak -3.0 dBFS (no clipping), nothing under 32 Hz, the sub band cut 6 dB under 70 Hz (phones cannot play it), a soft roll-off
over 12.5 kHz (no harsh hats).

- **Switch it off:** set `"enabled": false` in `config.json` → `music`, or run `MUSIC=0 ./render.sh --stage audio,compose,qa`.
  The master is then dialog + nat + SFX. The **no-music master is exported every time anyway**, for a trending sound in
  Instagram.
- **Swap it:** drop a licensed track at `audio/music.wav` (48 kHz stereo) and set `bpm`, `downbeat0` and `offset` in
  `config.json` → `music`. The mixer levels it, ducks it under speech and tape-stops it at `tapeStop`, before the end card hit.
- **Stem:** `exports/… - music-stem.wav` is the music exactly as it sits in the master (ducked, at the master's gain).

**Ducking.** The music is side-chained from every spoken line: every dialog piece, plus the one nat clip with transcribed
speech (the cold open's "GT3s", 3.0–4.0 s). -11 dB, 60 ms raised-cosine attack before the words, 400 ms release after them,
gaps under 0.6 s held down (no pumping between sentences). Measured under every one of the 31 dialog pieces
(`.work/mix.json` `duck_check`): the music sits 11.0 dB under its own unducked level and 11.4–17.8 dB (RMS) under the voice.

**Dialog.** 31 pieces from the mezzanine audio (the 30 EDL pieces + the cold-open guest line): ffmpeg `highpass=80 Hz`,
`afftdn` (8 dB, noise tracking), a slow 2:1 compressor, centred mono, each levelled to -16 LUFS (BS.1770, gains -12…+18 dB;
the two far-mic briefing pieces needed +16/+17 dB), 12 ms edge fades. Four EDL edges were moved a few frames to the gap in
the audio where a neighbouring word leaked in (pieces 1, 2, 17, 18: the tail of "where", "…know", the onsets of "With" and
"the cars"; `config.json` `audio.trims`).

**Nat.** Under the B-roll: the cold-open shots, the CH1 shop, the CH3 arrivals, the R8, the timelapse (0016 60–64 s, in the
car), the dinner montage (each clip's own room sound, in sync with its picture) and the convoy montage (0032 5–18 s), levelled
per clip and ducked 10 dB under speech. Five B-roll clips whose own audio has someone else talking over the dialog were left
silent (0010 34 s, 0004 47 s, 0015 163 s, 0025 36 s, 0005 55 s: "apparently Roma pulling in" would talk over Omarie's Roma line).

**Locked-On accents** (the SE-LO pack, `10-motion-sfx/locked-on-sfx/`): the open hit on frame 0, whooshes on every whip, the
banner slide, the sweeps and the cards, a drop hit on each chapter slam and on SAFELY., acquire/lock ticks on every lock-on,
convoy hop and re-lock (a lock lost is silent), reel ticks on every route stop, a tick per quote-wall word, the end-card hit. Each is set to 45 % of the
music's unducked RMS over the accent's own energetic span and ducked a further 6 dB under speech (every cue and its gain:
`cue.md`).

**Master:** sum → 30 Hz high-pass → 4x-oversampled true-peak limiter at -2.0 dBTP → gain iterated to -14.0 LUFS (BS.1770 in
numpy), the last 60 ms exact zeros. On the delivered master: -14.11 LUFS integrated, -1.82 dBTP true peak, the last 101 ms exact zeros. Caption sync (`qa_summary.json` `caption_sync`): per caption piece the lag that best lines the caption word mask up with the speech-band energy of the dialog in the mix is +20 ms (median over 31 pieces, largest 160 ms, which is Whisper's own word-timing spread); the captions and the audio use the same source-to-timeline mapping, including the four trimmed edges.

## Picture

- **The cut** is the EDL: 53 shots, 5,230 frames at 29.97 fps (174.508 s); one source slip (shot 17, below). 59.94 fps sources drop every other frame at 1x;
  ramps pick and shutter-average source frames (a 180° shutter over the frames the ramp crosses).
- **Reframe:** DJI 1920x1920 open-gate clips are cropped to 9:16 with a per-shot window and a slow 4 % push (config
  `shots`); the lineup walk (CH2) is a 1.12x window anchored low with pan keys that follow the cars, so the cars sit above the
  captions; portrait iPhone and DJI clips are full frame.
- **Speed ramps:** the cold open (garage lineup 1.8x → 0.6x; the purple Urus 0.5x slow motion → 2.2x into the whip) and the
  CH6 montage (1.6x → 0.7x → 1.6x per shot; the DROP opens at 0.6x).
- **Transitions:** whips (3+3 frames, `fx.whip`) at 1.8, 3.0, 6.0, 7.0 and between every montage shot; an impact cut at
  4.0 s and on the DROP (135.77); the gold light sweep at every chapter change; the chapter-slam plate punch; hard cuts
  everywhere else. The end card wipes up over the last shot, which runs on 0.35 s under it.
- **Grade:** one night look (`fx.NightGrade`: per-shot normalisation of the black / white points and a gamma that puts the
  shot's median luma on the look's target, filmic S-curve, cool shadows / warm highlights, reds kept rich, everything else a
  little quieter) baked into a 33³ LUT per shot and applied by ffmpeg `lut3d`, with a shadow white balance that removes each
  shot's own night cast. Five variants of the same family: `night` (street, freeway, rooftop), `garage` (the parking decks),
  `interior` (the SE shop, Lotus of Siam, the casino, Yard House; keeps skin natural), `face` (the convoy briefing, one look for
  its three shots) and `day` (CH1's in-car daylight, which stays daylight). Shots of one scene share one look (the cold-open
  guest in the car uses the CH7 garage look, the same clip). Every shot's first / middle / last frame and its luma are in `exports/qa/shots-sheet.jpg` and
  `qa_summary.json`.
- **Licence plates** readable at phone size are tracked and blurred: the purple Urus and the car beside it on Las Vegas Blvd
  (the hook frame and the montage), the black R8 in the Roma cutaway, the Urus on the Venetian garage ramp. (Not in the brief:
  the approved v1 cut had its plates blurred.)
- **Lock-ons** are tracked on the rendered shots with `lib/track_mid.py` from a sharp anchor frame, both ways (QA sheets:
  `exports/qa/track_*.jpg`). Labels only where the car is identified on the footage: the widebody Urus, the white C8 Corvette
  Z06 (front fascia), the blue Huracán EVO, the orange Mercedes-AMG GT Black Series (fixed rear wing; the car Omarie names first, identified in review), the white 911 GT3 RS (swan-neck wing, hood vents), the black Cullinan (Pantheon
  grille), the white R8, the red colour-shift Roma (rear lights, matte red-grey wrap; the car in front of it is a black R8), the
  purple Urus.
- **Clocks:** camera clock = the file name's start time + the in-point (DJI_20260915HHMMSS, iPhone creation time UTC-7).
  CH1 16:10:24, CH2 18:46:41, CH3 18:53:08, CH4 19:13:07, CH5 20:12:35, CH6 22:45:29, CH7 23:33:26; dinner 21:39:36;
  montage 23:00:08 / 23:07:43 / 23:12:43 / 23:13:45 / 23:19:04 / 23:20:06.

## How to rebuild

```bash
./render.sh                          # = python3 build.py: everything
python3 build.py --stage join,prep,front,compose,qa    # after a layer or transition change
python3 build.py --stage prep,audio,compose,qa         # after a sound change (music slot, levels)
python3 build.py --stills 0,776,4200                   # composite single output frames -> .work/stills/
```

Needs Python 3 with numpy and Pillow, Node 22 with Playwright at `/opt/node22/lib/node_modules/playwright` (Chromium is
preinstalled; never run `playwright install`), and the static ffmpeg (`config.json` `paths.ffmpeg`, or `FFMPEG=`). Inputs: the
EDL, captions and mezzanines in the session scratchpad (`config.json` `paths`).

Stages (cached in `.work/`): `shots` (every EDL shot graded and reframed from the mezzanine) → `track` (lock-ons and plates on
the rendered shots) → `join` (transitions, plate blurs, punches → `.work/plate.mov`) → `prep` (scene, clock, SFX cues) → `audio`
(music bed if no track is supplied, the mix) → `front` (the layer, frame by frame) → `compose` (exports) → `qa`.

## Files

| Path | What |
|---|---|
| `config.json` | paths, per-shot reframe / look / ramp, source slips, transitions, plate blurs, clocks, tracks, music slot, audio levels, every on-screen element |
| `cue.md` | every element and transition with its in / out and how it was placed |
| `story.html` | the layer page: `window.renderAt(t)`, a pure function of t |
| `lib/sekit.js` | the vlog kit's component library, copied from `../vlog-kit/lib/sekit.js` (27 Sept, 03:27). Five changes, each marked `rally-v2 copy`: more internal helpers are exported (`SEK.helpers`); an accented capital (HURACÁN) sits on the H cap height instead of pushing its word down; the G1 slam exit lifts 0.35 cap and fades (it used to travel 1.2 caps up, out of the safe area); in the C1 hop, a LOCK LOST phase whose next car is not tracked yet (still out of frame) holds on the last car's rect instead of hiding the whole lock; the F1 quote card takes an optional small header tab (FAVOURITE OF THE FLEET) |
| `lib/v2kit.js` | this vlog's own components (hook, CTA chip, SAFELY. slam, route card / route panel, place tag, quote wall, car lock, end card) |
| `lib/plate.py` | the picture edit and grade |
| `lib/music.py`, `lib/mix.py` | the placeholder music bed and the mix |
| `lib/kinetic.js`, `lib/kcapture.js`, `lib/accum.py`, `lib/track.py`, `lib/track_mid.py`, `lib/trackqa.py`, `lib/fx.py`, `lib/synth.py` | copied unchanged from the kit / showcase / v1 |
| `lib/srcsheet.py`, `lib/shotview.py`, `lib/gridview.py` | planning and QA sheets |
| `lib/data/tracks.json` | every tracked box (output frames, output px) |
| `build.py`, `render.sh` | the one-command build |

## Where this differs from the EDL / brief, and why

1. **Chapter clocks are computed, not copied.** File-name start + in-point gives CH3 **18:53** (the EDL and the Egnyte note
   say 18:52; the shot is 6 min 28 s into DJI_20260915184641_0013, i.e. 18:53:08), CH6 **22:45** (EDL 22:36 is the briefing
   clip; the chapter opens on the rooftop clip P2245 at 22:45:29) and CH7 **23:33** (EDL 23:24 is before clip 0034 even
   starts, at 23:26:18). The others match. To use the EDL's values instead, edit the `tag` of G1-03/06/07 in `config.json`.
2. **The cold-open guest line** ("Wonderful time. Good time.") plays on its own shot at 4.1 s. The EDL placed that audio at
   0.0 s, 4 s before its picture. It is captioned there too.
3. **Dinner nat** plays in sync with each dinner clip (the EDL stacked both at 94.25 s).
4. **Four dialog edges** moved by 0.015–0.13 s where a neighbouring syllable leaked in (see Sound).
5. **The Roma lock-on** comes when the camera turns to the garage (106.35 s), not on the word "Roma" (104.5 s): before that
   the shot is inside a car. The red coupe is the Roma; the black car in front of it is an R8.
6. **Host's pick card:** the CH5 Roma quote is Omarie (0021, pondering through the pause), not a guest, so the card is their
   pick (FAVOURITE OF THE FLEET, OMARIE · @NQ.YOUNG) and the lock says OMARIE'S PICK (review, 27 Sept). "…" marks where
   the edit drops words ("I would say … the Roma": Omarie said "maybe"; the last sentence runs on past the cut). The kit's
   F1 card has no header slot; my copy of `lib/sekit.js` adds an optional one (marked `rally-v2 copy`).
7. **Plate blurs** added (not in the brief; the approved v1 cut blurred plates).
8. **Nat audio** of five B-roll clips muted because someone else talks over the dialog in them.
9. **Accents** are 45 % of the unducked music, then a further 6 dB down under speech (so ticks never step on words).
10. **CH6 route** is a horizontal strip in the top band (the kit's corner panel would cover the guide's and the guests' faces).
11. **_DELIVERY copy:** not made: the master is 10.95 Mb/s, already under the 11.5 Mb/s delivery rate.
12. **Shot 17 (59.79 s, guests signing in) is slipped:** the EDL's 0015 340.0–342.4 s opens on an arm and a ring over the
    lens for 1.2 s. It now plays the clean rest of the take, 341.36–343.16 s, at 0.75x (59.94p source, so the slow motion is
    smooth); its nat is slipped with it. `config.json` `slips` holds it; delete the entry to go back to the EDL.
13. **CH2 lineup hop: six cars and three LOCK LOSTs** (review, 27 Sept). The Urus, Huracán and GT3 RS each leave frame on a
    pan before the next car is in; their tracks ran on off-screen, so the brackets and leader pointed at the frame edge or the
    wrong car. Each is now released with the kit's I2 LOCK LOST treatment as it leaves, and the orange AMG GT Black Series
    has its own lock. The other locks (R8, lead Cullinan, Roma, Urus on the strip) stay on their car to the exit (QA sheets).

## Open items

1. **Listen before posting.** All sound checks are numeric (loudness, true peak, the duck under every piece, stem balance,
   spectrum). Nobody has listened: mainly the music bed (a placeholder Omarie may replace), the far-mic briefing (lifted
   +16/+17 dB, so its room noise comes up too) and the piece edges listed above.
2. **CORVETTE Z06, HURACÁN EVO** are read from the cars' fronts and Omarie's own naming ("Corvette, Huracán EVOs"); if
   either is a different trim, change `make` in `config.json` `C1.segs` (MAKE only, e.g. CHEVROLET CORVETTE, is the safe fallback).
3. **The "Black Series" Omarie names first is not in frame** when they say it (30.1 s), so the hop starts on the Urus they
   name next; the orange AMG GT Black Series gets its own lock when the walk reaches it (36.57 s, CAR 04 / 06). Its lock is
   0.6 s (it shares the frame with the GT3 RS, which takes the next 0.6 s on the word "GT3s").
4. **Music rights:** the bed is original (synthesised here). If Omarie picks a track, see Sound → Swap it.

