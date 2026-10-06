# One-way ticket, Part 2 (Sep 26–27 2026): SE vlog, rally v2 standard + the HUD strip, SE orange

**Status: rendered 6 Oct (phase B), awaiting nq-check and the facts panel.** DELIVERY (render host, git-ignored): `exports/2026-09-26 One-way ticket Part 2 - SE LOCKED-ON vlog - 1080x1920_DELIVERY.mp4`, 2:25.1, 8.70 Mb/s, -14.1 LUFS, -1.6 dBTP. Built from `../part1/` (same build, kit, gates, mix, DELIVERY at
11.1M). Style named by the lead from Omarie's pick (6 Oct): rally v2 + the dark-glass one-strip HUD, SE orange #FF4F16, the
car reads MCLAREN 600LT. The full README (every element, every line's source, sound, picture) is written after the render.

- **The cut:** `tools/make_edl.py` -> `data/edl.json`: 44 shots + end card, 37 dialog pieces, 165.7 s (2:45.7).
  OPEN (hook, "somewhere in Nevada") · CH1 NIGHT SHIFT 19:32 (In-N-Out, Nampa, the Corvette joke, gassed up, the 01:29 nap
  stamp, 02:46 freezing gas stop) · CH2 FIRST LIGHT 06:26 (weather, side missions, the empty desert, the gas station,
  LOCKED ON · MCLAREN 600LT) · CH3 HOME STRETCH 07:32 (rear-deck cam, STRIP-1 SOMEWHERE IN NEVADA, his reflection,
  STRIP-2 INTO LAS VEGAS, 09:10 ARRIVED · SUPERCAR EXPERIENCE) · end card.
- **Captions:** every piece was transcribed twice (small.en, the day index; medium.en beam 5 on the piece). Only pieces whose
  words both models share are in the cut; pieces where they differ were cut, not guessed. `tools/make_captions.py` FIX.
- **Held out:** every speed, distance, hours, price and gas-dollar line; "go fast"; "no hotel, no nothing"; "they stole our
  car"; the oil / coolant hunt; third-party talk and TikTok audio; people's names (`config.json` `forbidden`).
- **Phase B (after the fetch):** one contact sheet; hands / phone check on every driving shot (cutaways from the fetched
  rear-deck and freeway pool, audio runs on); `speedo` boxes on every cabin shot; the `mclaren` lock track; look per shot.

## Phase B (6 Oct)

- **Music:** Part 1's track and tempo (104.727 BPM) for the series; the cut is re-timed so the end card lands 21 bars after
  the DROP on STRIP-1 (`tools/make_edl.py` asserts it, `lib/music.py` asserts it agrees with `data/edl.json`).
- **Fix A, sentence tails:** `make_edl.py tail()` sets every out-point >= 350 ms after the last word (small.en, the captions'
  timing), before the next word (later of the two models' starts), run-on sentences extended (4 pieces); the voice fades over
  100 ms (`audio.edgeFadeOut`) and runs on under the next shot (L-cut). `tools/tail_check.py` lists every gap and fails any
  under 300 ms; it runs inside the gates. Pieces that could not get a clean tail were cut (list at the top of `make_edl.py`).
- **Fix B, voice:** `audio.dialogFilter` = HP 90 Hz, afftdn nr 10, -2 dB @ 300 Hz, +2.5 dB @ 3.5 kHz, de-esser, 3:1 comp;
  music ducked -14 dB, nat -12 dB; the gates fail any piece with voice < 10 dB over music + nat.
- **Hands / phone:** 0117 (phone in hand while driving in every desert shot) and 0116 25.0 (phone in hand) are covered by
  road cutaways (0121), his audio runs on; 0113 104 / 128.5 swapped for hands-on-wheel spans. `speedo`: 10 boxes.
- **Lock-on:** MCLAREN 600LT on 0119 74.6-78.2 (the car behind him at the pump), tracked (`exports/qa/track_mclaren.jpg`).
