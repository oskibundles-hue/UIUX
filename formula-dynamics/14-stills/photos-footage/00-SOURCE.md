# Poster frames cut from the shop's own footage

Twenty-three frames pulled 22 Sept from the vlog rushes in Dropbox
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
