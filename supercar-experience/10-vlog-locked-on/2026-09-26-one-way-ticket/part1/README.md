# One-way ticket, Part 1 (Sep 26 2026): SE vlog, rally v2 standard + the HUD-1 strip, SE orange

**What it is.** Part 1 of the two-part vlog of the McLaren 600LT trip (README one level up has the plan). Omarie flies out
before dawn on Sat Sep 26, picks up the black McLaren 600LT with the red interior, and drives it back toward Las Vegas.
Part 1 runs from the 04:37 Uber at home to the 16:47 fuel stop in Oregon and ends on a tease for Part 2 (the night drive).
Style named by the lead from Omarie's pick (6 Oct): **the Sep 15 rally v2 build (the SE vlog standard) + the dark-glass
one-strip HUD, with SE orange #FF4F16 everywhere** ("go ahead build part 1 keep the orange and its a mclaren 600 lt").
His own talk carries the story. **Status: not reviewed yet.**

Every technique is the rally v2's (`../../2026-09-15-rally-v2/`): the same build, caching, gates, capture, mix and QA. This
folder is a copy of that build with this vlog's cut, config and the changes listed under "Where this differs from rally v2".

**Exports** (`exports/`, git-ignored; `2026-09-26 One-way ticket Part 1 - SE LOCKED-ON vlog …`):

| File | What |
|---|---|
| `… - 1080x1920.mp4` | **the master.** H.264 High, yuv420p bt709, 1080x1920, 29.97 fps, x264 medium CRF 17.3 (VBV 16M / 22M), AAC-LC 48 kHz 256k, +faststart: **314.6 MB (300.0 MiB), 13.97 Mb/s**. 5401 frames = 180.21 s. Loudness on the mp4 (ffmpeg loudnorm): **-14.11 LUFS integrated, -1.79 dBTP true peak**, LRA 4.0; the last 102 ms are digital silence |
| `… - 1080x1920_DELIVERY.mp4` | the master re-encoded two-pass at 11.1 Mb/s video (the build makes it whenever the master is over 11.5 Mb/s, the Instagram delivery rate), same audio: 244.9 MiB (256,852,775 bytes, 11.40 Mb/s overall), -14.11 LUFS, -1.79 dBTP. **Upload this one** |
| `… - NO MUSIC - 1080x1920.mp4` | the same video stream with dialog + nat + SFX only: 298.7 MiB, -14.04 LUFS, -1.92 dBTP |
| `… - PREVIEW 720x1280.mp4` | phone preview, two-pass 1.1 Mb/s from the master (the single-pass CRF preview came out at 38.8 MiB): **27.4 MiB** (< 30 MiB), -14.63 LUFS, -1.98 dBTP |
| `… - music-stem.wav` | the music alone, as it sits in the master |
| `poster.jpg`, `contact-sheet.jpg` | frame 0 (the hook) and one frame every 2 s |
| `qa/` | first / middle / last frame of every beat and every graphic, `beats-sheet.jpg`, `elements-sheet.jpg`, `shots-sheet.jpg`, `caption-swaps-sheet.jpg`, `track_*.jpg`, `gates.md`, `swapcheck.json`, `qa_summary.json` |

**QA gates** (`exports/qa/gates.md`, `qa_summary.json`): 0 errors before the render. Loudness: every export inside -14 ±0.5
LUFS (preview -14.63 against its -14.5 ±0.6 target) and ≤ -1.5 dBTP. Caption sync: median lag 0 ms over 27 pieces,
largest 120 ms (0076 "a little tired" and 0093, the two pieces whose heads moved: the word before the first caption word is not captioned, and 0093 opens on cabin noise, so the energy match is loose, corr 0.57-0.65). Swap check: 59 caption page changes, 0 frames with two pages or mixed texts. Safe zone: 2 of 361 sampled
times touch the edge, both the first frame of a chapter slam (THE PICKUP at 54.02 s, HIT THE ROAD at 113.02 s), where the
kit's G1 slam enters at 1.55x scale with motion blur for a frame or two before it settles inside the safe area (the
rally's slams do the same; its samples did not land on them).

## What is on screen

| # | Element | When (s) | Where |
|---|---|---|---|
| HOOK | **Hook panel**, complete on frame 0: SUPERCAR EXPERIENCE · ROAD TRIP, ONE-WAY TICKET, PART 1 · SEP 26 2026, SE lockup; masked exit | 0 – 1.87 | x 54-907, y 330 |
| A2 | **SE side banner**: SE mark, live dot, SUPERCAR EXPERIENCE / ONE-WAY TICKET · PART 1, an orange progress rail that fills with the video | 1.62 – 174.8 | right edge |
| G1 ×3 | **Chapter slams**, camera-clock tag HH:MM · CH 0N / 03 | 9.8 WHEELS UP (04:57) · 54.0 THE PICKUP (10:14) · 113.0 HIT THE ROAD (12:17) | top band |
| I1 ×3 | **Orange light sweep** at every chapter change (plate switches along its centre line) | 9.6 · 53.8 · 112.8 | full frame |
| B1 | **Host name lock** OMARIE · @NQ.YOUNG on his tracked face, while he says "This is a Supercar Experience vlog" | 18.2 – 20.9 | tracked |
| D1 | **Clock stamp** 09:00 with the camera's own seconds, IN THE AIR, SEP 26 2026, over the plane window (right after "make like a flying animation") | 43.6 – 48.3 | top-left |
| LOCK | **Lock-on** LOCKED ON · MCLAREN 600LT on the car as it rolls up to the shop | 78.95 – 80.5 | tracked |
| STRIP-1 | **HUD-1 strip** (dark glass, SE orange): SE mark, camera clock 13:28:xx + INTO THE MOUNTAINS, ROUTE SEATTLE → VEGAS, scrubber (no side-G readout) | 129.1 – 136.9 | top, x 54-907, y 292-432 |
| STRIP-2 | **HUD-1 strip**: camera clock 15:42:xx + OPEN ROAD, ROUTE SEATTLE → VEGAS, scrubber (no side-G readout) | 139.1 – 146.9 | same |
| PLACE | **Place tag** JUST GOT INTO · OREGON, on "We're in Oregon!" | 148.2 – 151.2 | top-left |
| TEASE | **Tease tag** TO BE CONTINUED · PART 2: THE NIGHT, on "so we are about to keep on going" | 169.6 – 174.7 | top-left |
| H1 | **Captions** (rally v2 H1 boxed karaoke), active word on an orange box | every dialog piece 2.0 – 174.8 | y 1190-1382, x 130-830 |
| END | **End card** (the approved rally card, copy unchanged, accents orange) | 174.8 – end | full frame |

Every in / out time: `cue.md` (generated). All copy lives in `config.json` (`layer.comps`).

## Every on-screen line and its source

| Line | Source |
|---|---|
| SUPERCAR EXPERIENCE · ROAD TRIP / ONE-WAY TICKET / PART 1 · SEP 26 2026 (hook) | the storyboard Omarie approved on 6 Oct (`../mockup/storyboard-part1.jpg`, `../mockup/gen.py`); the date is the camera files' (DJI_20260926…) |
| SUPERCAR EXPERIENCE · ONE-WAY TICKET · PART 1 (side banner) | the approved storyboard |
| SE lockup, SE mark, stacked SE logo | `02-logos/png/` |
| HH:MM · CH 0N / 03 and the chapter titles WHEELS UP, THE PICKUP, HIT THE ROAD | titles: the approved storyboard. Clocks: the camera clock of the chapter's first frame = file-name start + in-point: 0076 04:56:12 + 58.0 s = **04:57** (the storyboard said 04:56, the clip's start), 0087 10:14:14 + 4.0 s = 10:14, CH3 = 0095 12:17:04 + 21.4 s (the slam's first frame, 113.0 s, is 0.2 s into the 0095 cutaway that opens at 21.2; round 5) = 12:17:25 = **12:17**; the slam's last frame (114.95 s) is 0095 23.35 s = 12:17:27, so the whole slam sits inside 12:17 (it was 0094 12:10:21 + 2.2 s = 12:10 until the 7 Oct cutaway, then 0095 27.4 s = 12:17:31) |
| OMARIE · @NQ.YOUNG | the approved follow card ("Omarie Young @nq.young"), as in rally v2 |
| 09:00:xx · IN THE AIR · SEP 26 2026 | the camera clock of clip 0082 (DJI_20260926085959: 08:59:59 + 2.0 s); the window shots are the plane on approach; place line from the approved storyboard |
| LOCKED ON · MCLAREN 600LT | Omarie, 6 Oct ("its a mclaren 600 lt"); he names it on camera ("pick up a McLaren 600 LT", 0075; "I'm here to pick up the 600LT", 0087; "We are in the 600 LT", 0091). No trim or spec added |
| 13:28:xx / 15:42:xx (strip clocks) | the camera clock of each frame: 0096 13:27:35 + 32.6 s…, 0099 15:39:50 + 166.0 s… |
| INTO THE MOUNTAINS / OPEN ROAD (strip place lines) | the approved storyboard; what the shot shows (mountains ahead in 0096, open plains in 0099). No road or town is named |
| ROUTE · SEATTLE → VEGAS (both strips; static) | his own words: "from Seattle to Vegas" (0090, "the 600LT that we will be driving from Seattle to Vegas") and "drive it all the way back to Vegas" (0087). It replaces the two HEADING readings (E 095 / SE 135), which were estimates with no sourced figure. `config.json` `p.route_text`; `lib/drive_strip.js` draws the arrow and fits the text to the column |
| JUST GOT INTO · OREGON | his words in 0100 ("we just got into Oregon", "We're in Oregon!") and 0102 ("we are in Oregon") |
| TO BE CONTINUED · PART 2: THE NIGHT | the approved storyboard (Part 2 is the night drive, README one level up) |
| Captions | his own words, `data/captions.json` (word timings from the day index, small.en; every piece re-checked with medium.en; the 11 readings that differ are in `data/caption_fixes.json`) |
| End card: A RIDE OF A LIFETIME. · TEXT OR DM TO BOOK · (725) 425-3583 · SUPERCAREXP.VIP · @SUPERCAR_EXPERIENCE_ · LAS VEGAS · SCOTTSDALE · BOISE · RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE · FILMED BY @NQ.YOUNG | the approved rally layer's end card, copy byte-identical (`build`: asserted against the rally v2 config); sources in `../../2026-09-15-rally/README.md` |

Places only where he says them or a sign shows them: Seattle (Washington), Vegas / Las Vegas, Oregon, Supercar Experience
are in his captions; the pickup shop is not named (its name in 0087 is unclear by ear). No speeds, prices, distances or
specs anywhere in the graphics; the spoken figures in the footage (miles, gas price, "12 hour") are cut out. Copy written
here went through SlopMonster: 5/5.

### HEADING and SIDE G (both dropped)

- **HEADING was removed from both strips** (lead, 6 Oct): it had no sourced figure; the strips show ROUTE · SEATTLE → VEGAS
  instead (`heading` stays in the config, unused, if a sourced reading is ever added and `route_text` is taken out). What it was:
  an estimate; the clips carry no GPS.
  - STRIP-1 (0096, 13:28): **E 095**. The sun at 13:28 PDT on Sep 26 near 47° N sits at about 195° (SSW); the trees on the
    left of the road are lit on their road-facing (south) side and the mountain ahead-right is lit, so the sun is to the
    right of the car: heading about east, into the mountains.
  - STRIP-2 (0099, 15:42): **SE 135**. Set from the trip, not the frame: 24 minutes later he crosses into Oregon (0100,
    "we passed the welcome to Oregon sign"), and Oregon is south of every road in the area. **The frame does not confirm
    it**: the driver's cap is lit on its left, which with the sun at about 220° would put the heading nearer north-west.
    Treat STRIP-2's heading as the weakest number on screen; change `heading` in `config.json` if Omarie knows the road.
- **SIDE G was removed from both strips** (6 Oct, second facts voter): its value came from one camera accelerometer axis that was never shown to be lateral (0.30 G on a straight road), so it was an unsourced figure, and a g-number on a rental client's car invites a "driving hard" reading. The strips are now clock + place | ROUTE (`config.json` `layer.comps` STRIP-1 / STRIP-2 `hide_g`; `lib/drive_strip.js`); the `sideG` config and the `data/side_g_*.json` series are no longer read. What it was (kept for the record): the djmd accelerometer read with `../../hud-layouts/tools/side_g.py`, 0096 32-52 s and 0099 158-182 s, no `--turn`.

## Sound

**Music: original and easy to remove.** The bed is rally v2's synth bed (`lib/music.py`: numpy only, fixed seeds, no
samples, so it is ours to use), re-timed to this cut: F minor, 104.73 BPM, the DROP on the vibes montage (119.8 s) through
both HUD strips, a no-kick breath under the plane window (43.4-48.4 s), a lift as the car rolls up (78.9 s), risers into
every chapter, a breakdown from Oregon (146.9 s), the music's own tape stop (173.65-174.23 s) and the bell sting on the end
card (174.8 s). DROP and end card are exactly 24 bars apart, so both land on a downbeat.

- **Switch it off:** `"enabled": false` in `config.json` → `music`, or `MUSIC=0 ./render.sh --stage audio,compose,qa`. The
  **NO MUSIC master is exported every time anyway** (for a trending sound in Instagram).
- **Swap it:** drop a licensed track at `audio/music.wav` (48 kHz stereo) and set `bpm`, `downbeat0`, `offset`.
- **Stem:** `exports/… - music-stem.wav` is the music as it sits in the master.

**Ducking** as rally v2: side-chained from every dialog piece, -11 dB, 60 ms attack, 400 ms release, gaps under 0.6 s held
down (`.work/mix.json` `duck_check` has the level under each of the 27 pieces).

**Dialog.** 27 pieces from the mezzanine audio, rally v2's chain: high-pass 80 Hz, `afftdn`, a slow 2:1 compressor, centred
mono, each levelled to -16 LUFS, 12 ms edge fades. Piece edges sit in the pauses of the word timings (no trims needed); four were moved into pauses in the 6 Oct review.

**Nat.** (Third-party speech in the beds is muted, config `audio.nat[].mute`: 0102 15.6-17.6, 0076 58.0-59.25 and 59.95-62.2, 0078 30.0-33.95.) Only under B-roll shots with no dialog: the terminal and escalator, the gate, the plane window (engines, -24 LUFS),
the red shop building, the car rolling up (-20 LUFS: the engine as it arrives), the roof opening, the hook montage. **The
driving clips 0094-0099 carry no nat**: he says "we're gonna play some music too" in 0094 (12:11) and 0092 has a song on the
car stereo, so their own sound could carry a copyrighted track; the music bed covers them.

**Accents** (the SE-LO pack, `10-motion-sfx/locked-on-sfx/`), placed by the build from the layer: open hit, whooshes on the
whips and sweeps, a drop hit on each chapter slam, acquire / lock ticks on the name lock and the car lock, a tick on the
clock stamp, the place and tease tags, the end-card hit; 45 % of the music's unducked RMS, a further 6 dB down under speech.

**Master:** sum → 30 Hz high-pass → 4x-oversampled true-peak limiter at -2.0 dBTP → gain to -14.0 LUFS, the last 60 ms
zeros. On the delivered master: -14.11 LUFS integrated, -1.69 dBTP true peak.

## Picture

- **The cut** is `data/edl.json` (`tools/make_edl.py`): 43 shots + the end card, 5,401 frames at 29.97 fps (180.2 s),
  27 dialog pieces. Sources are the Osmo Action 6 open-gate clips (3840x3840 59.94p), fetched as 1920x1920 mezzanines
  (`vlog.py plan` / `fetch`); 59.94 sources drop every other frame at 1x.
- **Reframe:** a 1080x1920 window centred on the square frame with rally v2's slow 4 % push; the two HUD shots hold still
  (no push under the strip).
- **Rotation (new):** 0090 (the car arriving, the red interior) was filmed with the camera on its side and is turned 90°
  clockwise; 0079 (at the gate) was upside down and is turned 180° (`config.json` `shots.N.rot`, applied before the crop).
- **Speed ramp:** the roof going down (0092): 1x while he says "let's make sure this top work", then 3x through the roof.
- **Transitions:** whips through the hook montage and the forest montage, into the snow peaks and the second HUD shot; an
  impact cut onto the McLaren on "McLaren 600 LT" (7.6 s); the orange light sweep at every chapter change; the chapter-slam
  plate punch; the end card wipes up over the last shot. Hard cuts elsewhere.
- **Grade:** rally v2's grade family per shot (a 33³ LUT fitted on the shot's own frames): `day` for the daylight
  exteriors, `terminal` (a lifted interior look) for the airport, `cabin` for the cabin-cam and passenger-cam driving
  shots. `exports/qa/shots-sheet.jpg` has every shot's first / middle / last frame.
- **Speedometer blurred:** the McLaren's digital cluster is readable at phone size on the cabin-cam shots (the digits show
  in the raw frames), so a feathered static blur sits over it on every cabin-cam shot (`config.json` `speedo`, 14 boxes; the old frame-range box 3501-3589 became a box on shot 31 only, so it no longer overlaps cutaway shot 30).
- **Licence plates are not blurred** (Omarie, 6 Oct: "we dont need plate blur"); `config.json` `blurs` is empty and no
  plate is tracked.
- **Lock-ons** are tracked on the rendered shots with `lib/track_mid.py` from a sharp anchor frame (QA sheets
  `exports/qa/track_*.jpg`): his face at the terminal doors (B1) and the McLaren as it rolls up (LOCK). The lock-on gate
  checks both frame by frame.
- **The HUD glass:** the strip's plate is the glass-orange theme's dark tint (rgba(8,8,10,.58) and its 1 px edge) drawn by
  the layer; the frosting is drawn in the picture: inside the strip's visible rect, frame by frame (following its unroll
  and retract), the plate is blurred (22 px) and saturated (1.3), exactly what the theme's `backdrop-filter` does in a
  browser over the footage. The layer is captured transparent, so a CSS backdrop-filter would have nothing behind it.
- **Clocks:** camera clock = file-name start + in-point (DJI_20260926HHMMSS, local time). CH1 04:57:10, CH2 10:14:18,
  CH3 12:17:25; IN THE AIR 09:00:01; STRIP-1 13:28:08; STRIP-2 15:42:36.

## Where this differs from rally v2, and why

1. **SE orange #FF4F16 for every accent** the rally layer draws in gold (stripes, slams, ticks, the banner rail, lock-ons,
   sweeps, the caption box, the end card's accents), pale gold highlights moved to pale orange. End-card copy unchanged.
2. **The HUD-1 strip** (`lib/drive_strip.js`, a copy of `../../hud-layouts/drive_strip.js`, changes marked `part1 copy`):
   the glass is drawn in the picture (above), the strip can retract (`exit`), its clock is the build's camera clock and its
   side G is the build's per-strip series.
3. **Glass only on the strip.** The storyboard mockup themed every panel as glass; the brief names the rally v2 build plus
   the glass strip, so the rally's black plates stay (lead's call, 6 Oct).
4. **Captions** start a new page at every dialog piece and after any pause of 0.45 s (the rally's pager only broke on
   sentence ends, and this footage's transcripts often have none), `lib/sekit.js` `capPages`, marked `part1 copy`.
5. **Rotation** of sideways / upside-down shots and **static blur boxes** (`speedo`) in `lib/plate.py`.
6. **Music** re-timed (above); `lib/mix.py` writes an empty meter when there is no quote card.
7. **Paths** one level deeper (`../../../07-fonts`, `../../../02-logos`).
8. **CH1's clock reads 04:57**, not the storyboard's 04:56: the chapter's first shot is 58 s into 0076 (04:56:12).
9. **No CTA chip, quote card, route card or quote wall**: none of them was in the approved storyboard for Part 1.

## Open items

1. **Listen before posting.** Every sound check is numeric. Nobody has listened. In particular:
   - whether the car stereo is playing a song under 0094's "get the vibes" line (12:10, 0094 12:10:21 + 2-9 s) and the "trees and nature" line;
   - the caption readings in `data/caption_fixes.json` (two whisper models; "look at us" vs "look at this" at 0076 50.8 s,
     "I was" vs "That's" before "a little tired" at 0076 25.3 s: captioned as "a little tired" only);
   - the edges of the 27 pieces.
2. **Review fixes applied (6 Oct, lead's decisions)**: 0077 "Seattle's treating you well today" is out of the cut (small.en and
   medium.en both hear "training", the lead heard "treating you": unconfirmed, so no caption and no sound; its shot stays as
   the phone picture, with the music under it). 0089 reads "gonna" (not "finna"). 0094's caption is "I like it. I want y'all to,
   you know what I'm saying, get the vibes, so you feel me. We gon' catch the vibes right now." (`OVERRIDE` in
   `tools/make_captions.py`; timings medium.en + small.en). Piece edges: 0092 opens at 7.93 s (no "damn"), 0093 opens in the pause
   before "It is beautiful" (4.42 s), 0076's "a little tired" opens in the pause at 25.25 s, 0089 opens in the pause at 140.55 s.
   The HEADING readings are gone (ROUTE · SEATTLE → VEGAS instead) and every gold fallback is SE orange.
3. **Side G is off both strips** (6 Oct): see "HEADING and SIDE G".
4. **Held lines** (lead, 6 Oct): the fuel-stop "I don't think I'm going to go to sleep, I'm just gonna run it the whole
   way" (reads as a drowsy-driving boast), the shop's name, the gas price, the miles and the "12 hours" lines.
5. **Phone in hand while driving** in 0094 176-232 s, 0096 41.8-47 s and 0094 5.6-7.5 s (the junction, under "you feel me" / "we gon' catch the vibes") is out (config `forbidden`); 112.8-116.0 s is a cutaway to the road (0095 21.2-24.4 s, round 5: both hands on the wheel, car rolling through forest, speedometer blurred; the span is used nowhere else in the cut, so no gesture repeats) over his hands-off-the-wheel gesture (0094 2.2-5.4 s), and 116.0-118.2 s is a cutaway to the road (0095 33.9-36.1 s, both hands on the wheel, speedometer blurred) with his audio and captions running on; STRIP-1 now sits on 0096 32.6-40.6 s and the hook's 0096 frames on 39.0-40.8 s (both hands on the wheel, checked frame by frame; every other cabin-cam shot was swept for a held phone: none); a water bottle in hand shows briefly in a
   few driving frames elsewhere and was avoided where the footage allowed.
6. **The index missed one speed line** (0093 1:55.8-2:00.2, "speed limit 35 we're going 45"): not in the cut, and added to
   config `forbidden`.
