# One-way ticket, Part 2 (Sep 26–27 2026): SE vlog, rally v2 standard + the HUD strip, SE orange

**Status (v2, 7 Oct): recut done, no render yet.** v2 cut 2:51.7 (171.7 s), 48 shots + end card, 31 dialog pieces; in-car stereo bed filled; strip re-timed. Next: fetch the mezzanines (`/tmp/claude-0/p2day/fetch/request.json`), the frame gate sheets for nq-check, then the render. v1 (delivered 6 Oct, 2:25.1) is described below the v2 section.
v1 was built from `../part1/` (same build, kit, gates, mix, DELIVERY at 11.1M). Style named by the lead from Omarie's pick (6 Oct): rally v2 + the dark-glass one-strip HUD, SE orange #FF4F16, the
car reads MCLAREN 600LT. The full README (every element, every line's source, sound, picture) is written after the render.


## v2 recut (7 Oct): Omarie's v2 notes (`../HANDOFF-v2-both.md`)

Style unchanged: rally v2 + the dark-glass one-strip HUD, SE orange #FF4F16, MCLAREN 600LT. `tools/make_edl.py` -> `data/edl.json`.

- **New moments** (programme time): food break, the In-N-Out cut-in 0105 6.0-10.2 in sync under "...to In-N-Out. Appreciate
  you, thank you." (0:09.8), then 0107 14.5-20.3, eating at the car, "I ain't gonna lie, nothing like doom-scrolling while
  eating. No cap." (0:17.2, 19:52, after the 0106 beat in day order); talk-to-camera 0116 142.35-147.25 + 153.3-161.75 (jump
  cut), "I wish it was like more like, you feel me, side missions we could have done," / "But yeah, so appreciate y'all being
  in the mirror, hanging out, hope you guys enjoy the content. And yeah, ..." (1:11.8-1:25.15); 0121 28.5-36.5, "You guys can
  hear me, you guys can hear the car, you guys can hear everything." then the engine fires (~34.8 s) and idles (1:52.05-2:00.05),
  into STRIP-1.
- **Out:** 0105 10.6-13.8 "We finally gonna eat ..." (the profanity at 11.9-12.3 has a 280 ms gap after it, no clean cut;
  the models differ on its first words); 0116 147.25-153.3 (the models differ: "but shout out to God" / "but you got what you
  got"); 0122 322.0 (the freeway beat was timed to the retired music's bars).
- **Fix A:** `tail()` is Part 1's (measured end of voice, `NEXT_ONSET`); seven v1 shots are 0.1-0.25 s longer so no two voices
  overlap. `tools/tail_check.py`: 31 pieces, min gap 350 ms. `data/words_small_fix.json`: small.en beam 5 re-runs where the day
  index missed words (0116 after "content.", 0121 28.66-32.3: the index's "let's hear the car" was a beam-1 miss; both models
  on the window hear "you guys can hear the car").
- **Captions** (two-model rule): not captioned where the models differ: "being in the mirror" (medium.en on the piece:
  "being in there"), the last word of the 0116 sign-off ("out you" / "out to").
- **Clock:** `clockAs` on 7 cutaways (config `shots`); `tools/clock_check.py` (ported from Part 1, overnight wrap allowed):
  PASS, the strip clock never decreases from 0:07.8.
- **Bed** (config `bed.segs`, no library music): 3 in-car songs, each with a NO MUSIC `sub` from 0121 road/exhaust nat (no song
  in its clip scan, no speech after 32.6 s); exhaust 0121 32.6-36.5 (the engine start), STRIP-1 0121 120-128, 0121 110-112.5 and
  an outro under the end card; nat in sync elsewhere. Songs: `exports/qa/in_car_tracks_part2.md` (`tools/track_list.py`; clip
  scan only until Shazam runs on the placed spans, `data/shazam_spans.json`). Mix (prep + audio stages): -14.05 LUFS, TP -2.0,
  voice over bed min 19.5 dB (NO MUSIC 17.8).
- **Strip:** STRIP 1.9 -> 166.3 (end card), expand SOMEWHERE IN NEVADA 120.25-127.85, INTO LAS VEGAS 142.745-150.345.
- **Speedo:** boxes on the two 0116 talk shots at the same place as the 0116 103.6 shot (same mount): check on the gate sheet.
- **Held out:** unchanged (the list below and `config.json` `forbidden`). The end card reads RENTERS 25+ · AGES 21–24 WITH
  UNDERAGE FEE; no "$" anywhere.

## v1 (6 Oct)

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

## Round 1 (nq-check, 6 Oct)

- **16:9 fill:** `lib/plate.py reframe()` drew every source at 1/s source px per output px, right only for the 1920-high
  mezzanines; the 1080-high ones (0113 / 0114 / 0115) played as a small window on black. It now uses (src_h / 1920) / s,
  the same scale `windows()` uses, and shots 11-19 take the default s 1.0-1.04 (full height, sides cropped).
- **0115 selfie:** 10.2-12.2 only (before it turns sideways), then 0115 20.8-23.5, the McLaren at the pump, doors up (shot with
  the phone on its side: `rot` 90; `shot_mezz()` swaps w / h for a turned 16:9 file). His audio runs on.
- **Hands:** hook 0116 4.0 -> 0121 128.0 road; CH2 slam 0116 103.6 -> 0116 126.5 (right hand on the wheel; slam clock
  06:24:37 + 126.5 = 06:26, unchanged); 0116 121.1 -> 0121 155.0 road. Dialog placement unchanged (sync -> at). 0113 120.0 ->
  118.0 (the hand left the wheel at 120.6, seen once the fill was fixed). Shots from 20 on are one index later.
- **Speedo:** 0116 box on the cluster right of the wheel (880,980); 0112 boxes moved off his face onto the cluster (640,960);
  0119 box moved right onto the digits (180,1090). Check sheet: `exports/qa/round1-replacements-speedo.jpg` (`tools/shot_sheet.py`).
- **Caption sync:** four pieces shifted later by the gate's own measure (`tools/make_captions.py` SHIFT): gates now 0 warnings.

## Round 2 (nq-check, 6 Oct)

- **CH2 slam lip sync:** 0116 126.5-129.8 showed him talking under another line. The slam is now 0116 103.6-106.9, the picture of
  his own "It was actually perfect weather this time" (104.50, at 0.9): in sync. Right hand on the wheel throughout, no phone
  (sheet `exports/qa/round2-ch2-slam-sync.jpg`). Clock 06:24:37 + 103.6 = 06:26, unchanged. Dialog and captions unchanged.
- Master 9.78 Mb/s (under 11.5, so build.py makes no re-encoded _DELIVERY); the _DELIVERY path holds a copy of the master.


## Delivered (6 Oct 2026)

- Video Drop card `se-one-way-ticket-p2` (page version 11), 9 parts. The rejoined file's SHA-256 matches the master: 57bc6ae1526bcca8a432fef144cbaa4214b4b23b51d2ac1808e8d8c47b72efc5, 177,192,792 bytes, 2:25.1, 9.77 Mb/s, −14.1 LUFS, −1.6 dBTP.
- Dropbox folder: `Supercar Experience / 05 Vlogs / 2026-09-26 One-way ticket Part 2`.
- Checks: nq-check needed two fix rounds (16:9 fill bug in `lib/plate.py`, hands and phone cutaways, speedo box placement, then lip sync at 56 s). nq-facts and nq-second both voted CLEAR.
- **Hands rule, clarified by Omarie (6 Oct, a click):** one hand on the wheel while he talks is fine. A phone or camera in hand, or both hands off the wheel, while moving or stopped in traffic means a cutaway.
- Noted on the card: the shop's own banner at about 2:10 shows a different phone number (888-678-…, cropped). It's in the footage, not an overlay.
