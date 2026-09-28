# Rally vlog v2.4, Sep 15 (Egnyte rally day): rebuilt from the raw footage, Locked-On for vlogs (9:16)

**What it is.** Omarie Young's ask: "remake the whole video from scratch using our raw footage… make the video and the
dynamic motion graphics like you did here and the overlays… catching all key moments… show me your skills like you did the
Porsche video but in vlog format… I still want the Supercarexperience banner on the side". Omarie added on 27 Sept that the
rally was for **Egnyte**: the name appears as text only (no Egnyte marks anywhere). This folder renders the approved edit
decisions (the EDL, 174.5 s) at the `locked-on` standard (`../../09-campaign-ads/HOUSE-STYLE.md`): a new picture edit and grade
from the camera files, a new sound mix, and a Locked-On layer built from the vlog kit (`../vlog-kit/`) plus this vlog's own
components. **Status: v2.4 code, data and config done (28 Sept); the v2.4 render needs the footage fetched again (see
"Render on a machine with little disk"), then a reviewer pass.**

## v2.4 (28 Sept): the v2.3 fixes made at the source, plus the graphics fixes

v2.3 was a patch on the v2 masters (scratch scripts). v2.4 makes the same fixes inside the build, so a re-render keeps
them, and adds the graphics fixes a patch could not make. Numbers marked *sim* come from the build's own code on the
raw clip 0013 audio (0-85 s) before the footage was fetched again; the render re-measures them (`exports/qa/audio_v24.json`).

1. **Car alarm (clip 0013, source 0-19 s: dialog pieces 3 and 4, the cold-open nat).** Removed in the audio stage,
   before the pieces are levelled (config `audio.dealarm`, `lib/dealarm_dfn.py` in the DeepFilterNet3 venv): the voice
   is separated with DeepFilterNet3, the alarm bands (2.85-3.75 kHz, 6.0-7.25 kHz, -45 dB) are cut from the non-voice
   rest only, the voice is tone-matched to the same clip's clean pieces 5-8, and any alarm tone left in it is clamped
   to 4 dB over the neighbouring bands (then the "s" range the clamp took is given back). *Sim:* the alarm band in the
   span 40.0 → 15.7 dB (second band 16.4 → 14.1); the 95th-percentile tone over the neighbours in the voice 15.6 / 11.0 →
   6.7 / 6.6 dB, the same as the clean pieces' own voice (5.6 / 7.1). Levelled after the clean-up, the voice-only
   loudness of pieces 3 / 4 is -17.08 / -17.49 LUFS against -16.88 / -18.54 / -18.39 for pieces 5-7 (mean -17.94):
   +0.86 / +0.45 dB (v2: -1.86 / -6.53 dB, the lineup levelled with the alarm counted as voice). The -0.6 dB on pieces
   3 and 4 (`audio.trims`) is there because, once the alarm is gone, they are nearly all voice while 5-8 carry garage
   ambience inside their -16 LUFS. The Locked-On accents are mixed after the dialog, so the notch never reaches the
   lock ticks (30.96-38.94) or the 26.06 sweep whoosh; `lib/audiocheck.py` checks it on the render (each accent's gain in
   the alarm bands against 1-2 kHz, within 1 dB).
2. **"Black" was clipped.** Piece 4 started at source 5.40; "Black" starts at 5.26 (voice envelope). It now starts at
   5.20 (`data/edl.json`), so its audio runs from 29.86 s; the picture cut stays at 30.06 (a 0.2 s J-cut; from 30.06 the
   picture and the sound are the same source time again).
2b. **"Cullinan" finishes (Omarie, 28 Sept: "let it finish").** Piece 4 used to end at source 16.45, on "Culli-" (the word
   runs to 16.95 on the DeepFilterNet voice). It now ends at 16.98, and 0.53 s of the silent gap between "GT3s" and
   "Rolls-Royce" (voice silent 14.12-15.41) is closed up (`data/edl.json` dialog 4 `drop`, 14.465-14.995, 40 ms
   equal-power crossfade in `lib/mix.py`), so the piece still ends at 41.11 and nothing after it moves. Piece 5 had no
   room: its "So" starts 0.085 s after its in-point, and its picture is in sync. Omarie is behind the camera in the
   lineup walk (cars only), so "Rolls-Royce Cullinan" sitting 0.53 s earlier against the picture does not show; it now
   lands nearer the Cullinan's own lock (38.64). *Sim:* Whisper on the placed pieces reads "…GT3s, Rolls-Royce Cullinan"
   to 41.08, then "So right now" from 41.12; the ambience across the splice stays level (-27 to -34 dB, no dip or click).
3. **Flash frame at 54.087 s (frame 1621).** The CH3 shot starts at 54.09 s, which rounds to frame 1621 (54.0874 s),
   just before the sweep's t0 (54.09); `lib/plate.py` masked only frames at or after t0, so that one frame showed the new
   shot in full before the sweep. Every frame of the new shot before the sweep ends is now masked (0 before t0, so the old
   shot keeps playing). Only the 54.09 sweep was affected (the other five start on or after their t0).
4. **Captions.** Piece 4 reads "Black Series, Mansory Uruses, Corvette, Huracán EVOs, GT3s, Rolls-Royce Cullinan"
   (Omarie's words; "Mansory" was missing). Pieces 1, 3 and 4 are retimed from real word timings (DeepFilterNet voice +
   faster-whisper small.en word timestamps + the speech envelope): piece 1's "if you guys ever want to go" lit up
   0.5-1.37 s early, piece 3's "See," 0.9 s early. The gold highlight box now sits above the words with a black copy of
   the words clipped to it (`lib/sekit.js`), so while the box glides to the next word no frame hides part of a word
   (v2: the new word turned black at once, black on the black plate until the box arrived, e.g. "USE." at 111.97 s).
5. **Convoy lock-on (C1):** LAMBORGHINI URUS → **LAMBORGHINI MANSORY URUS** (Omarie, 28 Sept; `brand-tokens.json`
   `mansory-urus`). The label spans x 86-761 in its box (safe area 54-907; ink audit over 30.9-40.8 s: nothing outside).
   **CORVETTE Z06** stays: Omarie confirmed it on 28 Sept.
6. **Spelling:** the pick card's header tab is **FAVORITE OF THE FLEET** (US, like Omarie's "favorite").
7. **Quote wall "Wonderful".** Checked: the chip (150.84) is on the word it shows. There are two: a quieter "I had a
   wonderful time" at 149.38-150.55 (the one a Whisper pass over the whole stretch puts at about 149.6-150.5) and the
   louder "Wonderful time." at 150.92-151.62 that the captions, the chip and the cold open (0034 431.5) all use. The chip
   lands 2 frames before that word's voiced onset. Not moved (see Open items).
8. **Output: the master only.** `… vlog v2.4 - 1080x1920.mp4`. The NO MUSIC master is still built (config `exports`)
   but not delivered; the 720x1280 preview and the music-stem copy are off.

Also in v2.4: the build cache lives where `config.json` `paths.work` says (`.work` is a link to it); the lock-on tracks
key on the shot's content, not on the mezzanine file, so fresh mezzanines do not re-run the reviewed tracks
(`lib/data/tracks.json` signatures moved to the new key, boxes unchanged); the cold open's music duck under "GT3s"
comes from `audio.natSpeech` (the v2 transcripts are gone); `lib/fetchneeds.py` writes what the render reads for the
engine's `plan`.

**Exports** (`exports/`, git-ignored; `2026-09-15 rally day (Egnyte) - SE LOCKED-ON vlog v2.4 …`). The table below is
the v2 render's; the v2.4 numbers go in after the v2.4 render:

| File | What |
|---|---|
| `… - 1080x1920.mp4` | **the master.** H.264 High, yuv420p bt709, 1080x1920, 29.97 fps, x264 medium CRF 17.3 (VBV 16M / 22M) 11.16 Mb/s, AAC-LC 48 kHz stereo 256k, +faststart, **243.4 MB**. 5230 frames = 174.508 s; video / audio tracks 174.508 / 174.507 s. Loudness on the mp4 (ffmpeg loudnorm): **-14.11 LUFS integrated, -1.82 dBTP true peak**, LRA 3.0; the last 101 ms decode to digital silence |
| `… - NO MUSIC - 1080x1920.mp4` | **v2.4: built, not delivered.** The same video stream (stream copy) with dialog + nat + SFX only (for a trending sound in Instagram): 231.8 MiB, -14.06 LUFS, -1.89 dBTP |
| `… - PREVIEW 720x1280.mp4` | **off in v2.4** (config `exports.preview`). Phone preview, x264 medium CRF 28.5 (VBV 2M) from the same composite pass, AAC 160k (the mix 0.5 dB lower so AAC holds the true peak): **27.7 MiB** (< 30 MiB), -14.63 LUFS, -2.05 dBTP |
| `… - music-stem.wav` | **off in v2.4** (config `exports.musicStem`; the stem stays in `.work/music_stem.wav`). The music alone, exactly as it sits in the master (ducked, at the master's gain), 24-bit 48 kHz, 50 MB |
| `poster.jpg`, `contact-sheet.jpg` | frame 0 (the complete hook: the story preview) and one frame every 2 s |
| `qa/` | first / middle / last frame of every EDL beat (`beat_*`), in / middle / out of every graphic (`el_*`), `beats-sheet.jpg`, `elements-sheet.jpg`, `shots-sheet.jpg` (every shot's first / middle / last frame: the grade check), the tracker sheets `track_*.jpg`, `caption-swaps-sheet.jpg` (the last frame of every caption page and the first of the next: one page per frame, 64 page changes), `swapcheck.json` and `qa_summary.json` |

No `_DELIVERY` copy: the master is already 11.16 Mb/s, under the 11.5 Mb/s delivery rate.

## What is on screen

| # | Element | When (s) | Where |
|---|---|---|---|
| HOOK | **Hook panel**, complete on frame 0 (the story preview): SUPERCAR EXPERIENCE × EGNYTE · RALLY DAY, THE RALLY, LAS VEGAS · SEP 15 2026, SE lockup. Glints on the hold, masked exit | 0 – 1.87 | x 54-907, y 330-790 |
| A2 | **SE side banner** (vlog kit A2 edge tab, the kit's recommendation): SE mark, live dot, SUPERCAR EXPERIENCE / RALLY DAY · LAS VEGAS set vertically, a gold progress rail that fills with the video | slides in 1.62, out at the end card 170.02 | right edge x 992-1080, y 300-900; never meets the captions (x 130-830) |
| G1 ×7 | **Chapter slams** (kit G1): camera-clock tag HH:MM · CH 0N / 07 over the title, 1.55x → 1 slam with motion blur, stripe, glint, a plate punch | 7.05 RALLY DAY · 26.08 THE LINEUP · 54.29 EGNYTE ARRIVES · 79.04 ROLL OUT · 87.74 RED ROCK · 116.81 THE DRIVE BACK · 147.97 THE VERDICT (≈1.9 s each) | top band, title y 350 (faces stay clear) |
| I1 ×6 | **Gold light sweep** at every chapter change: the layer draws the band, the plate switches along its centre line (old shot keeps playing on the right; v2.4: also on a new shot's frames that start just before the sweep, the 54.09 flash) | 25.88 · 54.09 · 78.84 · 87.54 · 116.61 · 147.77 (0.36 s) | full frame |
| B1 | **Host name lock** (kit B1): OMARIE · @NQ.YOUNG on the tracked face | 9.2 – 11.35 | tracked |
| C1 | **Convoy lock-on hop** (kit C1 + I2 lock lost / re-acquire) while Omarie names the lineup, counter CAR 0N / 06: LAMBORGHINI MANSORY URUS → CORVETTE Z06 → LAMBORGHINI HURACÁN EVO → MERCEDES-AMG GT BLACK SERIES → PORSCHE 911 GT3 RS → ROLLS-ROYCE CULLINAN. A car that leaves frame on a pan is released with LOCK LOST and the next one is locked once it is in frame; a direct hop only while both cars are in frame | Urus 30.96; LOCK LOST 32.30 → Corvette 33.03; Huracán 35.08; LOCK LOST 35.86 → Black Series 36.57; GT3 RS 37.18 (on "GT3s"); LOCK LOST 37.80 → Cullinan 38.64; out 40.45 | tracked on the lineup walk |
| CTA | **CTA chip**: TEXT OR DM TO BOOK · (725) 425-3583 · @SUPERCAR_EXPERIENCE_ | 45.15 – 54.0 ("If you ever need to book with us for a large event…") | top-left |
| SLAM | **SAFELY.** kinetic slam | lands 63.66 on the word (63.63), out 64.6 | top band |
| R8 | **Lock-on** LOCKED ON · AUDI R8 | 67.85 – 69.5 | tracked |
| C3 | **Lead-car lock** (kit C3, climbing lead chevrons): LEAD CAR · ROLLS-ROYCE CULLINAN | 74.9 – 77.0 | tracked |
| E-CH4 | **Route card** under the CH4 slam: VENETIAN → BLUE DIAMOND → RED ROCK, a comet ticks each stop | 79.3 – 82.8 | panel x 54-907, y 800-1250 |
| D1 | **Clock + place stamp** (kit D1): 21:39 → 21:40 with the camera's own seconds ticking, LOTUS OF SIAM · RED ROCK CASINO, SEP 15 2026 | 94.35 – 101.65 | top-left |
| F1 | **Host's pick card** (kit F1 quote card): header tab FAVORITE OF THE FLEET, label OMARIE · @NQ.YOUNG, Omarie's words verbatim, word by word, with a live meter driven by their own audio | 101.8 – 110.45 | top, y 340, header tab above its right end (Omarie's face is lower in frame) |
| ROMA | **Lock-on** OMARIE'S PICK · FERRARI ROMA (on the red colour-shift coupe once the camera turns to the garage) | 106.35 – 108.25 | tracked, label below |
| PLACE | **Place tag** TEAM DINNER · YARD HOUSE | 110.62 – 116.4 | top-left |
| E1 | **Route line** (kit E1 language, laid out as a strip): 215 → 15 NORTH → FLAMINGO → LAS VEGAS BLVD → VENETIAN → LEVEL 9. 215 and 15 NORTH flash gold when the guide names them (129.74, 132.37); each stop ticks on its montage shot (135.77, 137.77, 139.77, 141.77, 144.27, 146.27), counter 00 → 06 / 06 | 129.45 – 147.72 | top band y 290-534 (the briefing's faces fill the upper left, so the kit's corner panel would cover them) |
| D1 | **Rolling camera clock** 23:00:08 → 23:20:06, BACK TO THE VENETIAN (each montage shot shows its own real time) | 135.9 – 147.7 | bottom-left |
| URUS | **Lock-on** FOLLOW THAT CAR · LAMBORGHINI URUS on the purple Urus ahead | 141.95 – 144.2 | tracked |
| WALL | **Quote wall**: EGNYTE ON THE DAY, then WONDERFUL · GOOD TIME · AWESOME · AMAZING · GOOD EXPERIENCE, each chip slamming in as it is said | 150.55 – 161.5 (words at 150.84 / 152.16 / 156.07 / 156.85 / 160.62; WONDERFUL checked in v2.4: on the louder "Wonderful time." at 150.92, see v2.4 item 7) | top band |
| H1 | **Captions** (kit H1 boxed karaoke), active word on a gold box (v2.4: the box above the words, black letters clipped to it, so the glide never hides a word) | every dialog piece 4.0 – 170.0 | y 1190-1382 (62-72 %), x 130-830 |
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
| CAR 0N / 06 + LAMBORGHINI MANSORY URUS, CORVETTE Z06, LAMBORGHINI HURACÁN EVO, MERCEDES-AMG GT BLACK SERIES, PORSCHE 911 GT3 RS, ROLLS-ROYCE CULLINAN; LOCK LOST | Omarie naming the lineup on camera ("Black Series, Mansory Uruses, Corvette, Huracán Evos, GT3s, Rolls-Royce Cullinan"), each label only on the car that is in frame and identified on the footage (see "Lock-ons"). MANSORY URUS: Omarie's choice, 28 Sept, as in `brand-tokens.json` (`mansory-urus`). CORVETTE Z06: Omarie confirmed on 28 Sept that it is a Z06 |
| TEXT OR DM TO BOOK · (725) 425-3583 · @SUPERCAR_EXPERIENCE_ (CTA chip) | the approved Locked-On end card and `brand-tokens.json` `phones.text`; shown while Omarie says "If you ever need to book with us for a large event…" |
| SAFELY. | Omarie's own word ("That's our number one thing. Safely."), on the word |
| LOCKED ON · AUDI R8 | Omarie: "you'll get the R8… the R8, Audi R8"; the car on screen |
| LEAD CAR · ROLLS-ROYCE CULLINAN | Omarie: "I am in the all black Cullinan. I'll be leading everybody." |
| THE ROUTE · VENETIAN → BLUE DIAMOND → RED ROCK | the brief, and Omarie on camera: "straight up Blue Diamond into Red Rock Loop" (0015, about 6:43), named again in 0019 and 0022 (CH4 route card) |
| 21:39:xx · LOTUS OF SIAM · RED ROCK CASINO · SEP 15 2026 | the iPhone clip's clock (P2139a, 21:39:36); Omarie: "I'm going to go down to Lotus of Siam"; the brief |
| FAVORITE OF THE FLEET · OMARIE · @NQ.YOUNG + the quote (US spelling, as Omarie says "favorite"; v2.4) | Omarie's own words (0021, the selfie at the Red Rock table, answering a guest's question about their favourite car), verbatim from the audio in the cut (captions.json), word by word; "…" marks where the edit drops words ("maybe", and the rest of the last sentence). Handle: the approved follow card |
| OMARIE'S PICK · FERRARI ROMA | Omarie: "Out of all those cars, I would say … the Roma" |
| TEAM DINNER · YARD HOUSE | Omarie: "We are currently eating at Yard House."; the brief |
| THE ROUTE · 215 → 15 NORTH → FLAMINGO → LAS VEGAS BLVD → VENETIAN → LEVEL 9 | the guide's briefing ("take 215 out of here… to the 15 North") and the brief; 215 and 15 NORTH flash when the guide says them |
| 23:00:xx → 23:20:xx · BACK TO THE VENETIAN | the camera clock of each montage shot (0032, 23:00:03 + in-point); Omarie: "We're gonna go back to the Venetian" |
| FOLLOW THAT CAR · LAMBORGHINI URUS | the guide: "look at what car is in front of you. Follow that car."; the purple Urus ahead |
| EGNYTE ON THE DAY + WONDERFUL · GOOD TIME · AWESOME · AMAZING · GOOD EXPERIENCE | the guests' own words in CH7 (captions.json), each stacked as it is said; header wording: Omarie, 27 Sept |
| Captions | captions.json (corrected word timings; v2.4: pieces 1, 3 and 4 retimed from the audio, "Mansory" added to piece 4 from Omarie's words), active word in gold; hidden while the SAFELY. slam, the host's pick card or the quote wall already shows the same words. "Ignite" (a Whisper mishearing of Egnyte) would be corrected to "Egnyte"; none of the pieces in the cut contains it |
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
speech (the cold open's "GT3s", 3.0–4.0 s; since v2.4 written in `audio.natSpeech`, clip time 12.865-14.005, because
the v2 transcripts are gone; any transcript in `paths.transcripts` still adds its words). -11 dB, 60 ms raised-cosine attack before the words, 400 ms release after them,
gaps under 0.6 s held down (no pumping between sentences). Measured under every one of the 31 dialog pieces
(`.work/mix.json` `duck_check`): the music sits 11.0 dB under its own unducked level and 11.4–17.8 dB (RMS) under the voice.

**Car alarm (v2.4).** Clip 0013 has a loud car alarm in source 0-19 s (dialog pieces 3 and 4, the cold-open nat). Before
the dialog chain, `lib/mix.py` has the span cleaned once by `lib/dealarm_dfn.py` in the DeepFilterNet3 venv
(`paths.dfnPython`; torch never goes into the build's own python) and caches it as `.work/dealarm/0013_<a>-<b>.wav` with a
report (`.json`) and a key (`.key`, rebuilt when the mezzanine, the config or the code changes). Every dialog or nat read
inside that span takes the cleaned audio instead of the mezzanine. Settings: config `audio.dealarm` (see v2.4 item 1).
Without the venv the audio stage stops with a clear message rather than put the alarm back. On a Mac: make a Python venv
with `torch`, `deepfilternet`, `huggingface_hub`, `safetensors`, `scipy` and `pyloudnorm`, and set `paths.dfnPython` in
`config.local.json`.

**Dialog.** 31 pieces from the mezzanine audio (the 30 EDL pieces + the cold-open guest line): ffmpeg `highpass=80 Hz`,
`afftdn` (8 dB, noise tracking), a slow 2:1 compressor, centred mono, each levelled to -16 LUFS (BS.1770, gains -12…+18 dB;
the two far-mic briefing pieces needed +16/+17 dB; v2.4: pieces 3 and 4 -0.6 dB, see v2.4 item 1), 12 ms edge fades. A
piece can close up a silent source range inside itself (`drop`, 40 ms crossfade; v2.4 piece 4, item 2b). Four EDL edges were moved a few frames to the gap in
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
  4.0 s and on the DROP (135.77); the gold light sweep at every chapter change (the new shot is masked on every frame
  before the sweep ends, including a first frame that rounds to just before the sweep: v2.4, the 54.087 s flash); the chapter-slam plate punch; hard cuts
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

## Render on a machine with little disk (v2.4, cloud session)

The v2 caches and mezzanines are gone, so v2.4 fetches the footage again with the engine, then renders in steps that free
space as they go. Everything lives under `paths.scratch` (`rally24/`): `day/` (engine), `mezz/`, `work/` (the build cache).

1. `python3 lib/fetchneeds.py <scratch>/day/plan_edl.json`: what the render reads from each clip (shots with post-roll,
   ramps and the shot 17 slip; dialog with trims; the cold-open line; nat).
2. Engine, tail-only survey (`../engine/vlog.py tails`): one link per DJI clip, two per phone clip, one call for this cut;
   then `plan --audio-only-vo --waves-gb X` and `fetch --budget-gb Y`. The fetch keeps the spans on disk under the budget,
   asks for the next wave's links through `day/fetch/links/NEED.json` when the disk can take it, and frees each span once
   its cuts are done. See `../engine/README.md` "Rebuilding a cut with little disk".
3. Render in steps: `--stage shots,join,prep,gates` (the gates scan the shots now and cache it) → delete
   `.work/shots/*.mov` (the `.sig` files stay) → `--stage audio` → keep each mezzanine's audio as `<src>_<t0>-<t1>.wav`
   and delete the `.mov` files (a later re-mix still works; a picture fix needs the footage again) →
   `--stage gates,front,compose,qa`.

## Render and review loop

**Any machine.** `config.json` `paths` hold this build's defaults. The EDL and captions are in `data/`; the
mezzanines and transcripts are in the cloud scratch folder. A git-ignored `config.local.json` overrides any of them
per machine (`lib/cfg.py`). `render.sh` reads `../vlog.env`, which gives it the machine's Python, ffmpeg,
Playwright and core count. The Mac setup and how to rebuild the Sep 15 mezzanines there are in
`../MAC-SETUP.md`. A Mac's Chromium rasterizes text slightly differently from the cloud's, so a Mac render matches a
cloud render to the eye but not bit for bit.

The first version took about 6 hours from brief to approval. About 2 h 45 min of that went to the first render, which included writing the code, and each of the 4 review fixes then cost a full 25 to 35 minute re-render. The loop is now built so that **a problem is caught before a render, a
reviewable cut takes minutes, and a fix only re-renders what it touches.**

```bash
./render.sh --draft          # 1. review cut: gates, then a 540x960 draft -> exports/draft/  (about 2 min warm, 7 min the first time)
                             #    read exports/qa/gates.md: errors, automatic fixes, warnings, human checks
                             # 2. fix config.json, run --draft again (only the changed frames are re-drawn)
./render.sh                  # 3. full quality -> exports/ (every stage cached; stops on a gate error unless --force)
                             # 4. a review fix: edit config.json, ./render.sh again (a lock-on fix: about 4.5 min, see the timings)
python3 lib/cmpmaster.py --approved <dir>   # optional: compare a new render with an approved one
```

**What is cached and how** (all under `.work/`; nothing to clear by hand; `--force-front` recaptures the whole layer):

| Stage | Re-runs when | How |
|---|---|---|
| shots | a shot's EDL line, reframe, look or mezzanine changes | per-shot signature (`.work/shots/NN.mov.sig`) |
| track | that track's box or its shot changes | per-track signature in `lib/data/tracks.json` |
| join | any shot, transition, blur or slam punch changes | `.work/stage_join.sig` |
| audio | the mix inputs change (config audio/music/master/sfx, the SFX cue list, mezzanines, code) | `.work/stage_audio.sig`; inside it the dialog and nat buses are cached (`.work/cache/`) |
| front | a frame's layer state changes | per-frame hash of every visible component's DOM (styles, text, SVG) at every motion-blur sample + the page CSS, fonts, logos and capture code (`.work/front/index.json`); identical frames are captured once |
| compose | a 120-frame segment's layer frames or plate GOPs change | per-segment hash (layer frame hashes + plate packet MD5s of the GOPs it decodes from + encoder settings); changed segments are re-encoded, then all are joined by stream copy and muxed with the AAC (encoded once per mix) |

**Gates** (`lib/gates.py`, stage `gates`, before any capture; report `exports/qa/gates.md`):
- **Lock-ons:** each lock is checked frame by frame against its tracked box while it is on screen. If less than 40 % of the box is in frame, or the tracker loses the car, the lock is released automatically: a convoy hop becomes a LOCK LOST that snaps to the next car once that car is in frame, and a single lock exits early. Replayed on the reviewed CH2 lineup, the gate finds exactly the three drifts from the review and releases them at 32.37, 35.97 and 37.91 s (the hand fix was 32.30, 35.86 and 37.80). On the current cut it changes nothing.
- **Swap check:** no frame shows two caption pages, and no frame's motion-blur samples mix two different texts.
- **Shot scan:** every rendered shot is sampled at 10 fps for black, near-constant and lens-blocked stretches (detail collapses against the shot's own median while a large area goes flat). It finds the arm over the lens in the EDL's original shot 17 (59.79 to 60.69 s) and nothing in the current cut.
- **Captions:** each caption piece must be within 0.2 s of the speech.
- **Loudness:** -14 LUFS ±0.5 and true peak at or below -1.5 dBTP, checked on the mix and again on the delivered files.
- **Quote cards:** every card is listed for a human to confirm the speaker, because the transcripts have no speaker labels. A card labelled GUEST is flagged as a warning.

Errors stop a full render. Automatic fixes, warnings and human checks are listed in `gates.md`.

**Draft:** the layer is captured at half size with one sample per frame (no motion blur) into `.work/front_draft/`, over a half-size copy of the plate that is made once per plate, then encoded with x264 veryfast. The full-quality caches are not touched.

**Capture determinism:** the kit's split glyphs are composited layers (`will-change: transform`), and Chromium keeps a layer's raster state from the frames it drew before. As a result, the same frame used to come out slightly different depending on which frames a capture process had drawn first. Text edges moved by up to 210/255, and the approved layer only reproduces with the original 3-process interleave. `lib/kcap2.js` commits an empty frame before every frame, so each frame is drawn from the same state in any order and any process. Across 100 frames in shuffled order, one frame differed by 1 level. Without this, re-capturing only the changed frames would not match a full run.

**Timings on this build** (4 shared cores; the "before" numbers come from this build's review re-renders on 27 Sept, and the
"now" numbers were measured on the same cut and config; seconds):

| Stage | Before | Now: first full render | Now: a lock-on fix | Why |
|---|---|---|---|---|
| audio (mix) | 252 | 153 | 153 (skipped, 0 s, when the cues do not move) | the two masters are limited in parallel; a redundant limiter pass is skipped; dialog and nat buses are cached; output bit-identical |
| gates | none | 8 (58 the first time: the shot scan) | 7 | new |
| layer capture | 460-482 (every change = all 5230 frames) | 498 (hash 14 + capture 484) | 31 (83 changed frames) | per-frame state hash; order-independent capture |
| compose (master, no-music, preview) | 818 (pass 1 219 + pass 2 456 + no-music remux and two-pass preview 143) | 394 | 43 (2 of 44 segments + mux) | single pass, vignette gain map computed once, filter threads, preview from the same pass, per-segment cache |
| QA | 94 | 36 | 38 | the master is decoded once for every still and sheet; loudness runs in parallel |
| join | 347 whenever run | cached | cached | stage signature |
| **total** | **about 27 min** (a review fix cost 25-35 min) | **about 18 min** | **about 4.5 min** (about 2 min when the fix does not move a sound cue) | |

The fix measured is the CH2 GT3 RS hop moved by 0.07 s (`.work/timings_demo_fix.json`); it ran at 6 min 16 s with the old
serial mix (258 s), the audio row is the new mix code on the same input. The draft is 540x960 with no motion blur. Its times (1 min 48 s warm, 6 min 40 s the first time, including the one-off
half-size plate) were measured while another CPU-heavy job shared the machine (load 8-12), so they are upper bounds.

**Tried and not used for the full-size capture.** It stays at about 8 minutes because each Chromium screenshot has a fixed
cost of about 40 ms (frame production), and throughput levels off at about 55 screenshots/s on 4 cores. The things tried:
- **Raw RGBA from CDP:** not offered (PNG, JPEG and WebP only). `optimizeForSpeed` was already on.
- **Dirty-rect clip:** about 10 % faster, but it changes up to 4 levels on 45 % of the motion-blurred frames, so it is off
  (`--noclip`).
- **Empty or duplicate frames:** there are almost none to skip. The SE banner's progress rail moves every frame, so only 16 of
  5,230 frames repeat.
- **4 processes instead of 3:** helps only a few percent.
- **Piping frames straight to ffmpeg:** would lose the per-frame cache.

The per-frame cache is where the time is saved.

**Checked against the approved render** (`lib/cmpmaster.py --approved .work/approved`, every 10th frame, 523 frames):

| | Approved (27 Sept 08:00, old path) | This render (new path) |
|---|---|---|
| master vs its own lossless composite | SSIM 0.99116, PSNR 47.52 dB, 10.95 Mb/s | SSIM 0.99181, PSNR 47.88 dB, 11.16 Mb/s |
| preview vs its own composite (720x1280) | SSIM 0.97781, PSNR 40.36 dB, 27.5 MiB | SSIM 0.97822, PSNR 40.41 dB, 27.7 MiB |
| mix.wav, mix_nomusic.wav | | bit-identical |
| AAC tracks (master, no music, preview) | -14.11 / -1.82, -14.06 / -1.89, -14.63 / -2.05 (LUFS / dBTP) | bit-identical streams, same loudness |
| layer frames | | 2,416 of 5,230 identical; the others differ at text edges (premultiplied PSNR 42.6 dB) |

The cut, the grade, the graphics and the mix are unchanged. The layer differences come from the capture history described
above. In the approved render some text was rasterised soft, for example the LEAD CAR / ROLLS-ROYCE CULLINAN label at 76 s.
It is now drawn crisp every time. New master vs approved master directly: SSIM 0.99123, PSNR 43.3 dB.

Needs Python 3 with numpy and Pillow, Node 22 with Playwright at `/opt/node22/lib/node_modules/playwright` (Chromium is
preinstalled; never run `playwright install`), and the static ffmpeg (`config.json` `paths.ffmpeg`, or `FFMPEG=`). Inputs: the
EDL, captions and mezzanines in the session scratchpad (`config.json` `paths`).

Stages: `shots` (every EDL shot graded and reframed from the mezzanine) → `track` (lock-ons and plates on the rendered shots)
→ `join` (transitions, plate blurs, punches → `.work/plate.mov`) → `prep` (scene after the lock-on gate, clock, SFX cues) →
`audio` (music bed if no track is supplied, the mix) → `gates` → `front` (the layer, changed frames only) → `compose`
(changed segments, then the exports) → `qa`. `python3 build.py --stage compose,qa` runs a subset; `--stills 0,776,4200`
composites single frames into `.work/stills/`.

## Files

| Path | What |
|---|---|
| `config.json` | paths, per-shot reframe / look / ramp, source slips, transitions, plate blurs, clocks, tracks, music slot, audio levels, every on-screen element |
| `cue.md` | every element and transition with its in / out and how it was placed |
| `story.html` | the layer page: `window.renderAt(t)`, a pure function of t |
| `lib/kcap2.js`, `lib/accum2.py` | the layer capture: per-frame state hashes, order-independent frames, premultiplied motion-blur average (replaces `kcapture.js` / `accum.py` here) |
| `lib/gates.py` | the pre-render gates (lock-ons, shot scan, captions, loudness, quote cards) |
| `lib/cmpmaster.py` | compares a render with an approved one (layer frames, SSIM / PSNR, audio) |
| `lib/sekit.js` | the vlog kit's component library, copied from `../vlog-kit/lib/sekit.js` (27 Sept, 03:27). Seven changes, each marked `rally-v2 copy`: more internal helpers are exported (`SEK.helpers`); an accented capital (HURACÁN) sits on the H cap height instead of pushing its word down; the G1 slam exit lifts 0.35 cap and fades (it used to travel 1.2 caps up, out of the safe area); in the C1 hop, a LOCK LOST phase whose next car is not tracked yet (still out of frame) holds on the last car's rect instead of hiding the whole lock; the F1 quote card takes an optional small header tab (FAVORITE OF THE FLEET); (v2.4) the H1 gold box is drawn above the words with a black copy of the words clipped to it, so a gliding box never hides part of a word; hard swaps land on a frame boundary: a caption page is on screen for whole frames and the next page's pre-roll never overlaps it (the kit showed both pages for up to two frames at each page change), and a gap of 3 frames or less between two pages is closed (no one-frame blink), and captions, the convoy label's text swaps (make → LOCK LOST → make) and the clock's HH:MM are drawn on the frame time, so no motion-blurred frame mixes two texts. `story.html`: the camera clock of a motion-blur sample is read from its own frame, so the first frame of a new shot never mixes two clocks |
| `lib/v2kit.js` | this vlog's own components (hook, CTA chip, SAFELY. slam, route card / route panel, place tag, quote wall, car lock, end card) |
| `lib/plate.py` | the picture edit and grade |
| `lib/dealarm_dfn.py`, `lib/audiocheck.py` | (v2.4) the car-alarm clean-up, run in the DeepFilterNet3 venv by `lib/mix.py`; the sound checks on the render (`exports/qa/audio_v24.json`) |
| `lib/fetchneeds.py` | (v2.4) what the render reads from each clip, as an EDL for the engine's `plan` |
| `lib/music.py`, `lib/mix.py` | the placeholder music bed and the mix |
| `lib/kinetic.js`, `lib/kcapture.js` and `lib/accum.py` (kept, no longer used), `lib/track.py`, `lib/track_mid.py`, `lib/trackqa.py`, `lib/fx.py`, `lib/synth.py` | copied unchanged from the kit / showcase / v1 |
| `lib/srcsheet.py`, `lib/shotview.py`, `lib/gridview.py` | planning and QA sheets |
| `lib/swapcheck.js` | QA (run by the qa stage): evaluates every frame at each of its motion-blur samples and fails a frame that shows two caption pages at once or whose samples disagree on the caption page, the convoy label text or the clock; result in `exports/qa/swapcheck.json` and `qa_summary.json` `hard_swaps` |
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
   pick (FAVORITE OF THE FLEET, OMARIE · @NQ.YOUNG) and the lock says OMARIE'S PICK (review, 27 Sept). "…" marks where
   the edit drops words ("I would say … the Roma": Omarie said "maybe"; the last sentence runs on past the cut). The kit's
   F1 card has no header slot; my copy of `lib/sekit.js` adds an optional one (marked `rally-v2 copy`).
7. **Plate blurs** added (not in the brief; the approved v1 cut blurred plates).
8. **Nat audio** of five B-roll clips muted because someone else talks over the dialog in them.
9. **Accents** are 45 % of the unducked music, then a further 6 dB down under speech (so ticks never step on words).
10. **CH6 route** is a horizontal strip in the top band (the kit's corner panel would cover the guide's and the guests' faces).
11. **_DELIVERY copy:** not made: the master is 11.16 Mb/s, already under the 11.5 Mb/s delivery rate.
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
2. **HURACÁN EVO** is read from the car's front and Omarie's own naming ("Huracán EVOs"); if it is a different trim,
   change `make` in `config.json` `C1.segs`. (CORVETTE Z06: confirmed by Omarie, 28 Sept. LAMBORGHINI MANSORY URUS: his
   choice, 28 Sept.)
3. **The "Black Series" Omarie names first is not in frame** when they say it (30.1 s), so the hop starts on the Urus they
   name next; the orange AMG GT Black Series gets its own lock when the walk reaches it (36.57 s, CAR 04 / 06). Its lock is
   0.6 s (it shares the frame with the GT3 RS, which takes the next 0.6 s on the word "GT3s").
4. **Music rights:** the bed is original (synthesised here). If Omarie picks a track, see Sound → Swap it.
5. **Listen:** the 0.2 s J-cut at 29.86-30.06 ("Black" over the end of the previous shot) and the closed-up gap before
   "Rolls-Royce" (39.1 s); the reviewer listens on the render. (WONDERFUL stays on the louder "Wonderful time.":
   Omarie, 28 Sept.)

