# Poster frames cut from the shop's own footage

Thirty-one frames pulled 22 Sept from the vlog rushes in Dropbox
`/NQ Studio/raw footage/`. They exist because the stills library is entirely
wheel and brake photography, which the shop rejected for the oil set.

## Why footage beats the stills

Every clip below is shot **2160x3840** — vertical, 4K. A poster is 1080x1920,
so a frame is a straight 2:1 downscale with nothing to crop and nothing to aim.
The stills are 3:2 landscape, where a 9:16 poster keeps about 30% of the width
and the crop has to guess which 30%.

More importantly the footage shows **work being done**. A wheel off, a bare
rotor, a gloved hand on a caliper, a car raised on the lift. No still in the
library shows a job in progress.

## The frames

| frame | source clip | ~s in | carries |
|---|---|---|---|
| LIFT_020 | 2026-09-03 23-40-46 black car on the lift.mov | 40 | black car raised on the lift, shop steel above |
| LIFT_024 | 2026-09-03 23-40-46 black car on the lift.mov | 48 | same, car higher, body fills the frame |
| LIFT_027 | 2026-09-03 23-40-46 black car on the lift.mov | 54 | same, tightest on the underside |
| GT3IN_047 | 2026-09-03 23-10-09 gt3 rolling in.mov | 94 | white GT3 RS, bay wall behind |
| GT3IN_048 | 2026-09-03 23-10-09 gt3 rolling in.mov | 96 | white GT3 RS square on the lift ramps |
| REDCAR_002 | 2026-09-04 00-15-30 red supercar.mov | 4 | red SF90 side on, polished floor |
| REDCAR_029 | 2026-09-04 00-15-30 red supercar.mov | 58 | red SF90 three-quarter in the bay |
| ASTON_013 | 2026-09-03 23-44-19 aston martin brakes.mov | 26 | rotor and caliper in the wheel arch |
| ASTON_017 | 2026-09-03 23-44-19 aston martin brakes.mov | 34 | gloved hand at a teal caliper, wheel off |
| ASTON_029 | 2026-09-03 23-44-19 aston martin brakes.mov | 58 | gloved hand on a bare rotor, daylight |
| TEALBRK_019 | 2026-09-03 23-55-54 teal brakes and ryft wheels.mov | 38 | underside, suspension and exhaust |
| TEALBRK_022 | 2026-09-03 23-55-54 teal brakes and ryft wheels.mov | 44 | wheel off, hub and rotor |
| ASTON_009 | 2026-09-03 23-44-19 aston martin brakes.mov | 18 | hand and rotor together |
| ASTON_010 | 2026-09-03 23-44-19 aston martin brakes.mov | 20 | rotor and teal caliper, wheel off |
| ASTON_012 | 2026-09-03 23-44-19 aston martin brakes.mov | 24 | rotor and caliper, wheel arch |
| ASTON_020 | 2026-09-03 23-44-19 aston martin brakes.mov | 40 | hub and rotor with the tyre |
| ASTON_021 | 2026-09-03 23-44-19 aston martin brakes.mov | 42 | teal caliper and rotor, close |
| ASTON_044 | 2026-09-03 23-44-19 aston martin brakes.mov | 88 | matte car in the bay, wheel off |
| TEALBRK_048 | 2026-09-03 23-55-54 teal brakes and ryft wheels.mov | 96 | rotor and teal caliper on the red mats |
| TEALBRK_052 | 2026-09-03 23-55-54 teal brakes and ryft wheels.mov | 104 | caliper and wheel arch |
| TEALBRK_062 | 2026-09-03 23-55-54 teal brakes and ryft wheels.mov | 124 | rotor and teal caliper |
| TEALBRK_063 | 2026-09-03 23-55-54 teal brakes and ryft wheels.mov | 126 | same, wider |
| TEALBRK_093 | 2026-09-03 23-55-54 teal brakes and ryft wheels.mov | 186 | car in the bay, wheel off |

Saved as JPEG at quality 94 with no chroma subsampling. They are already at
poster resolution, so re-encoding them further loses detail that cannot be got
back without the clips.

## To cut more

    ffmpeg -i "<clip>" -vf "fps=1/2,scale=1080:1920" frames/%03d.png

One frame every two seconds. Anything shot landscape needs `scale=1920:1080`
and a crop decision, which is why the vertical clips are worth preferring.

## What was looked at and rejected

Sixteen clips were pulled and framed. These did not yield anything usable:

- **the shop tour** (`IMG_2804`) — the new location mid-build, ladders and bare
  walls, handheld blur, and only 1080p landscape
- **the forklift, the garage walkthrough, the two pieces to camera** — vlog
  content: a person talking, not a car being worked on
- **the 2026-09-09 day** — the footage index labels it "shop work, blue car on
  the lift". What is actually in it is a piece to camera and a tape measure on
  a workbench. Three more clips from that day, about 6 GB, were left unpulled
  once the first two showed what the day really was.
- **the two 2026-09-09 stills** — accidental shutter presses, a hand over the
  lens at a desk

## Still open

These show a car in a shop, which is honest and is better than a brake caliper
over the words OIL SERVICE. **None of them shows oil.** An engine bay, a fill
cap, a drain plug or oil actually pouring is still the thing that would make an
oil ad about oil.

Anyone recognisable in a frame is a permission question before it is a design
one. The picks above favour gloved hands and cars over faces, but the wider
rushes are full of staff and the shop should clear a face before it runs.

## Added with the footage brake set (22 Sept)

Eleven more frames, all from the two brake clips, chosen by sharpness ranked
**within each clip**. Ranking the two together was wrong: a global median kept
6 of 46 Aston frames against 87 of 140 teal ones, which threw the Aston
material away rather than judging it. The teal clip is simply sharper.

The daylight trade is worth knowing before picking from these. Measured under
the headline the brake frames average 142-164 luminance where the studio stills
average 25-50, so the scrim works about three times harder and the picture
reads darker than the photograph is. The layout was built for dark car
photography; a bright shop frame pays for the white type.

## Added with the oil set (22 Sept) - the oil-change footage

Eight frames from two phone clips shot 17 Sept, in `Mobile Uploads/2026-09-17/`:
`Video Sep 17 2026, 4 13 12 PM.mov` (red 911 on the lift, "Oil change going
down") and `Video Sep 17 2026, 4 22 49 PM.mov` (oil bottles, extraction rig,
white 911, "All your oil change needs in house").

| frame | carries |
|---|---|
| P1613_001 P1613_002 P1613_003 | red Porsche 911 up on the lift, shop behind |
| P1622_001 | a bench of oil jugs - the literal subject |
| P1622_002 | the orange extraction rig and a gloved hand |
| P1622_003 | white 911 rear in the bay (**customer plate CBS112 is readable**) |
| P1622_004 P1622_006 | white car panels, a tech working |

**The bottom 18% of each is cropped.** Both clips carry a burned-in story
caption near the foot of frame. Verified by eye across twelve renders that no
caption survives the crop. Clean exports without the overlay would give back
18% of the picture.

**P1613 is 720x1280**, upscaled 1.5x to fill a 1080x1920 poster. Every other
frame here is at or above poster size and `cars()` refuses anything smaller;
this is a deliberate override because no other clip has the subject. It holds
at phone size and will look soft next to the 4K frames.

## How the clips were found, and the index worth building

Phone files are named only by timestamp, so neither clip could be found by
name. They were found by scoring every frame for **dominant colour** and
searching pink/magenta: the two oil clips scored 21.2% and 19.8% of frame
area, everything else that day under 7%. Pure arithmetic - no model, no
network.

That generalises. Cheap per-frame signals that need only numpy and PIL, and
would have saved most of the searching done today:

| signal | answers |
|---|---|
| dominant hues | "the pink car", "the red one", "teal calipers" |
| sharpness (edge stddev) | skip motion blur - already used to pick the brake set |
| mean and 97th-percentile luma | night clip or daylight, and how hard the scrim will work |
| orientation | is it poster-native 9:16 |
| frame-to-frame difference | a static bench shot against a walkthrough |
| skin fraction | which clips have people in them, which is the permission question |

Plus one contact sheet per clip, stored once. Sixteen clips were downloaded
today - about 11 GB - to learn things a stored sheet would have answered in a
glance, such as that the 09-09 "shop work" day is a tape measure on a bench.

Object recognition on top of this needs CLIP or similar. Not possible in this
container - no torch, no cv2, no transformers, and installing them would die
with the session - so that column has to be filled by a one-time job on a
machine that persists. The CSV is designed to take it later without rework.
