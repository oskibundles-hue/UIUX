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

EXPORTS_TABLE

## What is on screen

| # | Element | When (s) | Where |
|---|---|---|---|
| HOOK | **Hook panel**, complete on frame 0: SUPERCAR EXPERIENCE · ROAD TRIP, ONE-WAY TICKET, PART 1 · SEP 26 2026, SE lockup; masked exit | 0 – 1.87 | x 54-907, y 330 |
| A2 | **SE side banner**: SE mark, live dot, SUPERCAR EXPERIENCE / ONE-WAY TICKET · PART 1, an orange progress rail that fills with the video | 1.62 – 174.8 | right edge |
| G1 ×3 | **Chapter slams**, camera-clock tag HH:MM · CH 0N / 03 | 9.8 WHEELS UP (04:57) · 54.0 THE PICKUP (10:14) · 113.0 HIT THE ROAD (12:10) | top band |
| I1 ×3 | **Orange light sweep** at every chapter change (plate switches along its centre line) | 9.6 · 53.8 · 112.8 | full frame |
| B1 | **Host name lock** OMARIE · @NQ.YOUNG on his tracked face, while he says "This is our Supercar Experience vlog" | 18.2 – 20.9 | tracked |
| D1 | **Clock stamp** 09:00 with the camera's own seconds, IN THE AIR, SEP 26 2026, over the plane window (right after "make like a flying animation") | 43.6 – 48.3 | top-left |
| LOCK | **Lock-on** LOCKED ON · MCLAREN 600LT on the car as it rolls up to the shop | 78.95 – 80.5 | tracked |
| STRIP-1 | **HUD-1 strip** (dark glass, SE orange): SE mark, camera clock 13:28:xx + INTO THE MOUNTAINS, HEADING, SIDE G, scrubber | 129.1 – 136.9 | top, x 54-907, y 292-432 |
| STRIP-2 | **HUD-1 strip**: camera clock 15:42:xx + OPEN ROAD, HEADING, SIDE G, scrubber | 139.1 – 146.9 | same |
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
| HH:MM · CH 0N / 03 and the chapter titles WHEELS UP, THE PICKUP, HIT THE ROAD | titles: the approved storyboard. Clocks: the camera clock of the chapter's first frame = file-name start + in-point: 0076 04:56:12 + 58.0 s = **04:57** (the storyboard said 04:56, the clip's start), 0087 10:14:14 + 4.0 s = 10:14, 0094 12:10:21 + 2.2 s = 12:10 |
| OMARIE · @NQ.YOUNG | the approved follow card ("Omarie Young @nq.young"), as in rally v2 |
| 09:00:xx · IN THE AIR · SEP 26 2026 | the camera clock of clip 0082 (DJI_20260926085959: 08:59:59 + 2.0 s); the window shots are the plane on approach; place line from the approved storyboard |
| LOCKED ON · MCLAREN 600LT | Omarie, 6 Oct ("its a mclaren 600 lt"); he names it on camera ("pick up a McLaren 600 LT", 0075; "I'm here to pick up the 600LT", 0087; "We are in the 600 LT", 0091). No trim or spec added |
| 13:28:xx / 15:42:xx (strip clocks) | the camera clock of each frame: 0096 13:27:35 + 38.0 s…, 0099 15:39:50 + 166.0 s… |
| INTO THE MOUNTAINS / OPEN ROAD (strip place lines) | the approved storyboard; what the shot shows (mountains ahead in 0096, open plains in 0099). No road or town is named |
| HEADING E 095 / SE 135 (± a slow drift of 2°) | **an estimate**, see "HEADING and SIDE G" |
| SIDE G 0.00-0.3x G | the camera's own accelerometer, `../../hud-layouts/tools/side_g.py` on the fetched source span (see below) |
| JUST GOT INTO · OREGON | his words in 0100 ("we just got into Oregon", "We're in Oregon!") and 0102 ("we are in Oregon") |
| TO BE CONTINUED · PART 2: THE NIGHT | the approved storyboard (Part 2 is the night drive, README one level up) |
| Captions | his own words, `data/captions.json` (word timings from the day index, small.en; every piece re-checked with medium.en; the 10 readings that differ are in `data/caption_fixes.json`) |
| End card: A RIDE OF A LIFETIME. · TEXT OR DM TO BOOK · (725) 425-3583 · SUPERCAREXP.VIP · @SUPERCAR_EXPERIENCE_ · LAS VEGAS · SCOTTSDALE · BOISE · RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE · FILMED BY @NQ.YOUNG | the approved rally layer's end card, copy byte-identical (`build`: asserted against the rally v2 config); sources in `../../2026-09-15-rally/README.md` |

Places only where he says them or a sign shows them: Seattle (Washington), Vegas / Las Vegas, Oregon, Supercar Experience
are in his captions; the pickup shop is not named (its name in 0087 is unclear by ear). No speeds, prices, distances or
specs anywhere in the graphics; the spoken figures in the footage (miles, gas price, "12 hour") are cut out. Copy written
here went through SlopMonster: 5/5.

### HEADING and SIDE G

- **HEADING** is an estimate; the clips carry no GPS.
  - STRIP-1 (0096, 13:28): **E 095**. The sun at 13:28 PDT on Sep 26 near 47° N sits at about 195° (SSW); the trees on the
    left of the road are lit on their road-facing (south) side and the mountain ahead-right is lit, so the sun is to the
    right of the car: heading about east, into the mountains.
  - STRIP-2 (0099, 15:42): **SE 135**. Set from the trip, not the frame: 24 minutes later he crosses into Oregon (0100,
    "we passed the welcome to Oregon sign"), and Oregon is south of every road in the area. **The frame does not confirm
    it**: the driver's cap is lit on its left, which with the sun at about 220° would put the heading nearer north-west.
    Treat STRIP-2's heading as the weakest number on screen; change `heading` in `config.json` if Omarie knows the road.
- **SIDE G** comes from the camera's metadata track (djmd, Osmo Action 6 accelerometer), read with
  `../../hud-layouts/tools/side_g.py <clip> <start> <dur>` on the fetched byte span (`vlog.py fetch --keep-sparse`):
  0096 32-52 s and 0099 158-182 s, saved as `data/side_g_*.json`. No `--turn`: there is no turn in either window to
  calibrate the axis, so left/right is not confirmed (the bead may swing the wrong way); the magnitude is the sensor's.

## Sound

SOUND_SECTION

## Picture

PICTURE_SECTION

## Where this differs from rally v2, and why

DIFF_SECTION

## Open items

OPEN_SECTION
