# One-way ticket, Part 1 (Sep 26 2026): SE vlog v2, rally v2 standard + the dark-glass strip, SE orange

**What it is.** Part 1 of the two-part vlog of the McLaren 600LT trip (README one level up has the plan). Omarie flies out
before dawn on Sat Sep 26, picks up the black McLaren 600LT with the red interior, and drives it back toward Las Vegas.
Part 1 runs from the airport at 04:56 to the 16:47 fuel stop in Oregon and ends on a tease for Part 2 (the night drive).
Style (Omarie, 6 Oct): **the Sep 15 rally v2 build (the SE vlog standard) + the dark-glass one-strip HUD, SE orange
#FF4F16 everywhere** ("go ahead build part 1 keep the orange and its a mclaren 600 lt"). His own talk carries the story.

**Status: v2, cut 2 (7 Oct).** v1 was delivered on 6 Oct. v2 is Omarie's 6 Oct notes (in-car music and exhaust instead of
synth music, the ONE-WAY TICKET chapter card, the strip replaces the side banner, the voice fixes, no price on the end card)
plus the nq-check fixes of 7 Oct. Cut 2 (7 Oct, Omarie's decision after nq-facts blocked the first line under HOUSE-STYLE
"never use ... fleet faults") takes two spoken lines out of CH2, below. It goes back through nq-check and the facts panel
before delivery.

Every technique is the rally v2's (`../../2026-09-15-rally-v2/`): the same build, caching, gates, capture, mix and QA. This
folder is a copy of that build with this vlog's cut, config and the changes under "Where this differs from rally v2".

## The two lines cut in cut 2 (7 Oct)

| Line | Was (episode, v2) | Source | Now |
|---|---|---|---|
| "I think you guys just put a brand new engine in it." | 68.55-70.5 s (sound), caption from 68.58 s | 0087 55.04-57.0 (voice ends 57.0 on the voice-band envelope) | out: the 0087 SYNC shot opens at 57.758 (was 54.9), its piece at 57.90, in the pause before "I gotta drive it all the way back to Vegas." (kept) |
| "So they got one more hour until they're done with the car." | 73.61-79.06 s (the whole beat) | 0088 0.2-5.65 (shot), 0.40-5.59 (piece) | out with its shot, sound and caption |

Together the cut is **243 frames (8.108 s) shorter**: 186.44 s became **178.33 s** (5,345 frames). Nothing before 68.41 s
moved. Everything after the old 0089 shot (79.06 s) moved back by 243 frames: beats, the CH3 slam and sweep, the car
lock-on, the strip's ROUTE span, the place and tease tags, the bed segments, the end card. `tools/remap_cut2.py` moved
config.json (times after 79.06 s, shot indices after the dropped 0088 shot); the EDL times come from `tools/make_edl.py`.

**The join (68.41 s).** Heard: "... from Supercar Experience." (its 400 ms tail fades out at 68.45), 0.10 s of room, then
"I gotta drive it all the way back to Vegas." from 68.55, whose tail runs 0.07 s under the next shot (L-cut), then "So right
now he's gonna go grab the 600 LT from the warehouse" from 71.00. Seen: the same handheld SYNC take at the shop door
(0087 52.0-53.85, then 0087 57.758-60.3: a jump cut inside one take, as the cut already had at 54.9), then the hard cut
outside the shop (0089) at 70.95.

## Exports

`exports/`, git-ignored; `2026-09-26 One-way ticket Part 1 v2 - SE LOCKED-ON vlog …`:

| File | What |
|---|---|
| `… - 1080x1920.mp4` | **delivery, upload this one.** The master's picture re-encoded two-pass at 11.1 Mb/s (under the 11.5 Mb/s spec), the master mix (in-car bed). EXPORT_MAIN |
| `… - 1080x1920 - NO MUSIC.mp4` | **delivery, for a trending sound.** The same video stream; every in-car song swapped for road/exhaust nat of the same length. EXPORT_NOMUS |
| `… - 1080x1920 (master CRF).mp4`, `… - NO MUSIC (master).mp4` | the CRF 17.3 masters the delivery pair is encoded from |
| `… - PREVIEW 720x1280.mp4` | phone preview, under 30 MiB |
| `… - in-car bed stem.wav` | the bed as it sits in the master |
| `poster.jpg`, `contact-sheet.jpg` | frame 0 and one frame every 2 s |
| `qa/` | first / middle / last frame of every beat and every graphic, the sheets, `gates.md`, `qa_summary.json`, `in_car_tracks_part1.md`, `v2-cut-sheet.jpg` (cut 2: the join, OREGON, the ROUTE strip, the end card) |

Spec (lead, 6 Oct): -14 LUFS integrated, true peak at or under -1.5 dBTP, video under 11.5 Mb/s, both delivery files the
same duration, voice at least 10 dB over the bed under every dialog piece (`.work/mix.json`).

## What is on screen (cut 2 timings)

| # | Element | When (s) |
|---|---|---|
| HOOK | hook panel, complete on frame 0: SUPERCAR EXPERIENCE · ROAD TRIP, ONE-WAY TICKET, PART 1 · SEP 26 2026; masked exit | 0 - 2.0 |
| STRIP | the dark-glass strip (`lib/drive_strip.js` seStrip), the one progress element: compact (SE mark, camera clock, ONE-WAY TICKET · PART 1, scrubber) from 1.9 s; it expands to the full HUD-1 strip (clock + place, ROUTE · SEATTLE → VEGAS) over the two cabin-cam shots: INTO THE MOUNTAINS 126.42, OPEN ROAD 136.22, back to compact at 144.22; retracts at 172.53 | 1.9 - 172.93 |
| G1 ×3 | chapter slams ONE-WAY TICKET · THE PICKUP · HIT THE ROAD (no clock tag) | 12.7 · 60.21 · 110.32 |
| I1 ×3 | orange light sweep at every chapter change | 12.5 · 60.01 · 110.12 |
| B1 | host name lock OMARIE · @NQ.YOUNG on his tracked face ("This is a Supercar Experience vlog") | 21.86 - 24.56 |
| D1 | IN THE AIR · SEP 26 2026 over the plane window (no clock digits) | 49.81 - 54.51 |
| LOCK | LOCKED ON · MCLAREN 600LT on the car as it rolls up | 77.97 - 79.55 |
| PLACE | JUST GOT INTO · OREGON, on "We're in Oregon!" | 145.52 - 148.52 |
| TEASE | TO BE CONTINUED · PART 2: THE NIGHT | 167.73 - 172.83 |
| H1 | captions (rally v2 boxed karaoke, active word on an orange box), 25 dialog pieces | 2.0 - 172.93 |
| END | end card (the rally card's layout, accents orange, **no price**) | 172.93 - 178.33 |

Every in / out time: `cue.md` (generated). All copy lives in `config.json` (`layer.comps`).

## Every on-screen line and its source

| Line | Source |
|---|---|
| SUPERCAR EXPERIENCE · ROAD TRIP / ONE-WAY TICKET / PART 1 · SEP 26 2026 (hook), ONE-WAY TICKET · PART 1 (strip) | the storyboard Omarie approved on 6 Oct (`../mockup/storyboard-part1.jpg`); the date is the camera files' (DJI_20260926…) |
| ONE-WAY TICKET, THE PICKUP, HIT THE ROAD | the approved storyboard; CH1 renamed ONE-WAY TICKET in Omarie's 6 Oct notes |
| camera clock in the strip | file-name start + in-point (DJI_20260926HHMMSS, local time); cutaways read the clock of the voice under them (`config.json` `shots.N.clockAs`), so it never runs backwards (`tools/clock_check.py`) |
| OMARIE · @NQ.YOUNG | the approved follow card ("Omarie Young @nq.young"), as in rally v2 |
| IN THE AIR · SEP 26 2026 | the approved storyboard; the window shots are clip 0082 (08:59:59) |
| LOCKED ON · MCLAREN 600LT | Omarie, 6 Oct ("its a mclaren 600 lt"); he names it on camera (0075, 0087, 0091). No trim or spec added |
| INTO THE MOUNTAINS / OPEN ROAD | the approved storyboard; what the shot shows. No road or town named |
| ROUTE · SEATTLE → VEGAS | his own words: "from Seattle to Vegas" (0090) and "drive it all the way back to Vegas" (0087) |
| JUST GOT INTO · OREGON | his words in 0100 ("We're in Oregon!") and 0102 ("we are in Oregon") |
| TO BE CONTINUED · PART 2: THE NIGHT | the approved storyboard |
| captions | his own words, `data/captions.json` (small.en word timings, every piece re-checked with medium.en; readings that differ in `data/caption_fixes.json` and `tools/make_captions.py` FIX) |
| end card: A RIDE OF A LIFETIME. · TEXT OR DM TO BOOK · (725) 425-3583 · SUPERCAREXP.VIP · @SUPERCAR_EXPERIENCE_ · LAS VEGAS · SCOTTSDALE · BOISE · RENTERS 25+ · AGES 21–24 WITH UNDERAGE FEE · FILMED BY @NQ.YOUNG | the rally end card's copy with the $299 taken out (Omarie, 6 Oct: "take the price off the end card"); the rest as sourced in `../../2026-09-15-rally/README.md` |

No speeds, prices, distances or specs in the graphics; the spoken figures in the footage (miles, gas price, "12 hours",
the speed-limit line) are not in the cut. The pickup shop is not named. Cut 2 removes the one line about work done to the
car ("brand new engine").

## Sound (v2: no music of ours)

- **The bed is the car itself** (`config.json` `bed`, `lib/mix.py`): the in-car stereo as it played, in sync where the
  picture is from the same clip (hook, the forest montage, both HUD-1 shots), exhaust (the car rolling up, the roof
  bridge, the outro under the end card) and room nat. Every transcribed word inside a bed segment is muted (40 ms ramps), so
  no third-party speech rides in the bed. No synth or library music; `lib/music.py` is retired (`music.enabled: false`).
- **NO MUSIC version**, exported every time: each music segment is swapped for road/exhaust nat of the same length from a
  speech-free, song-free span of 0095. The dialog keeps its own cabin audio, so a faint stereo under the voice stays.
- **In-car songs** (Shazam on the exact placed spans, `tools/track_list.py` → `exports/qa/in_car_tracks_part1.md`):
  TRACKLIST
- **Dialog**: 25 pieces, the fix-B chain (HP 90 Hz, afftdn, -2 dB at 300 Hz, +2.5 dB at 3.5 kHz, de-esser, 3:1), each
  levelled to -16 LUFS; every out-point at least 350 ms after the last word (here 400 ms, `tools/make_edl.py` `tail`) with a
  100 ms fade, running on under the next shot where the picture cuts first (L-cut), never into the next voice
  (`tools/tail_check.py`). Music ducks -14 dB under the voice, exhaust and nat -12 dB.
- **Accents**: the SE-LO pack (`10-motion-sfx/locked-on-sfx/`) on the slams, sweeps, locks, tags and the end card.
- **Master**: 30 Hz high-pass, 4x true-peak limiter at -2.0 dBTP, gain to -14.0 LUFS, the last 60 ms zeros.

## Picture

- **The cut**: `data/edl.json` (`tools/make_edl.py`): 43 shots + the end card, 5,345 frames at 29.97 fps (178.33 s), 25
  dialog pieces. Osmo Action 6 open-gate clips as 1920x1920 mezzanines (`/home/user/day/mezz1`). No source span is used twice
  (asserted).
- **Reframe**: 1080x1920 centred on the square frame, rally v2's slow 4 % push; the HUD shots hold still.
- **Rotation**: 0090 turned 90° clockwise, 0079 turned 180° (`config.json` `shots.N.rot`).
- **Speed ramp**: the roof going down (0092): 1x on "let's make sure this top work", then 3x.
- **Transitions**: whips in the hook and the forest montage, an impact cut onto the McLaren, the orange sweep at every
  chapter change, the end card wipes up. Hard cuts elsewhere.
- **Grade**: rally v2's per-shot LUT families (`day`, `terminal`, `cabin`).
- **Speedometer blurred** on every cabin-cam shot (`config.json` `speedo`, 16 boxes). No licence-plate blur (Omarie, 6 Oct).
- **Hands on the wheel**: where he gestures, holds a phone or turns to the camera while driving, the picture cuts away to
  the road with his voice running on (0095 and 0099 cutaways, `tools/make_edl.py` notes); phone-in-hand spans are in
  `config.json` `forbidden`.
- **The HUD glass**: the strip's dark tint is drawn by the layer; the frosting (22 px blur, 1.3 saturation) is drawn in the
  picture inside the strip's visible rect, frame by frame.

## Where this differs from rally v2

1. SE orange #FF4F16 for every accent the rally layer draws in gold.
2. The dark-glass strip (`lib/drive_strip.js`, a copy of `../../hud-layouts/drive_strip.js`) is the one progress element; no
   side banner.
3. The bed is the car's own sound, not synth music (above).
4. Captions start a new page at every dialog piece and after any 0.45 s pause (`lib/sekit.js` `capPages`).
5. Rotation and static blur boxes (`lib/plate.py`).
6. No CTA chip, quote card, route card or quote wall (not in the approved storyboard for Part 1).

## Rebuild

    python3 tools/make_edl.py && python3 tools/make_captions.py
    python3 build.py --stage shots,track,join,prep,audio,gates
    python3 build.py --stage front,compose,qa
    python3 tools/tail_check.py && python3 tools/clock_check.py && python3 tools/track_list.py

## Open items

1. **Listen before posting.** Every sound check is numeric. In particular the cut-2 join (68.4-71.0 s) and the edges of
   the 25 pieces.
2. **Held lines** (lead, 6 Oct): the fuel-stop "I'm just gonna run it the whole way", the shop's name, the gas price, the
   miles and the "12 hours" lines. Cut 2 adds "brand new engine" and "one more hour until they're done with the car".
3. The hook's first shot (0097 10.4-12.6) shows a lit phone lying on his lap, not held: both facts voters noted it, neither
   blocked; left to Omarie.
