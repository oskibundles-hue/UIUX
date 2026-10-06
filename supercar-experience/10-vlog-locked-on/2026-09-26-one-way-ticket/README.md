# One-way ticket, Sep 26–27: SE vlog in two parts (mockup stage)

**What it is.** The next vlog in filming order, after Sep 21 + 24. Omarie flies out before dawn on Sat Sep 26, picks up a
black McLaren convertible with a red interior and drives it back overnight. He pulls up at Supercar Experience Las Vegas
at 09:10 on Sun Sep 27.

- **Style:** Omarie picked rally v2 + HUDs, 6 Oct. That is the Sep 15 rally v2 build (`../2026-09-15-rally-v2/`) with
  the dark-glass one-strip HUD (`../hud-layouts/`, STRIP) on the driving parts.
- **Length:** Omarie, 6 Oct: "if you have to make multiple vlogs of this thats fine but it has 2 be 2 minumum". So it
  is two parts, each about 2:45.

**Status:** storyboard mockup only (`mockup/storyboard-part1.jpg`, `mockup/storyboard-part2.jpg`). The full build waits on
his OK.

## Footage

- **Clips:** `NQ Studio/raw footage/2026-09-26/` holds 0075–0115, 04:37 Sep 26 to 02:47 Sep 27; after-midnight clips
  are filed with the night before. `2026-09-27/` holds 0116–0123, 06:24–09:10.
- **Format:** 3840x3840 open gate, except 0104 and 0114, which are 3840x2160. Clock times below are the camera clock
  from the file names.

| Time | Clips | What |
|---|---|---|
| 04:37–06:12 | 0075–0081 | leaving before dawn, the airport |
| 09:00–09:37 | 0082–0086 | in the air (window), arrivals, the garage |
| 10:14–12:02 | 0087–0093 | the shop (red building), first sit in the McLaren |
| 12:10–16:06 | 0094–0100 | the drive: forest, mountains, open plains (cabin cam) |
| 16:35–16:48 | 0101–0102 | fuel stop |
| 19:23–20:20 | 0103–0113 | night: In-N-Out (19:53), gas station, driving |
| 01:29–02:47 | 0114–0115 | still driving |
| 06:24–07:35 | 0116–0121 | sunrise at the wheel, gas stop (doors up), rear-deck cam on the road |
| 08:57–09:10 | 0122–0123 | the freeway into Las Vegas, arrival at the SE Las Vegas shop (sign in shot) |

## The two parts (draft)

- **Part 1, about 2:45:**
  - Hook: 0096.
  - CH 01 WHEELS UP: 04:56.
  - Name lock: OMARIE · @NQ.YOUNG.
  - Clock stamp: IN THE AIR.
  - CH 02 THE PICKUP: 10:14.
  - CH 03 HIT THE ROAD: 12:10.
  - HUD-1 strip: twice.
  - Ends on TO BE CONTINUED · PART 2: THE NIGHT.
- **Part 2, about 2:45:**
  - Hook: the 06:26 sunrise.
  - CH 01 NIGHT SHIFT: 19:23.
  - Place tag: PIT STOP · IN-N-OUT.
  - Clock stamp: 01:29 STILL DRIVING.
  - CH 02 FIRST LIGHT: 06:24.
  - Lock-on: LOCKED ON · MCLAREN, at the 07:26 gas stop.
  - CH 03 HOME STRETCH: 07:32.
  - HUD-2 strip: into Las Vegas.
  - Place tag: 09:10 · ARRIVED · SUPERCAR EXPERIENCE.
  - End card.

**Open before the full build:**
- The McLaren model, the pickup city and the title. ONE-WAY TICKET is a working title.
- Gold or orange: the mockup runs dark glass + SE orange throughout, to match the HUD pick. The rally standard is gold.
- **HEADING and SIDE G:** the mockup shows placeholders.
  - In the full build, side G comes from `tools/side_g.py`.
  - Heading is estimated from signs, turns and the sun, as for the Oct 4 HUD cuts.
- Captions come from the transcript.
- Plates get blurred.
- Phone-in-hand stretches stay out of the HUD shots.

## Mockup

`mockup/gen.py` builds one page with a 10 s slot per still. The page uses:
- the vlog kit's `lib/sekit.js` (themed);
- the rally's `lib/v2kit.js`, with gold swapped for the theme accent;
- `hud-layouts/drive_strip.js`.

`hud-layouts/tools/hud_still.js` draws each still over its 9:16 frame. `mockup/board.py` lays out the two boards.
