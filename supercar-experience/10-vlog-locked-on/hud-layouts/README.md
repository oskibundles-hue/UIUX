# SE driving HUD layouts (HUD-1, HUD-2)

Two saved layout options for Supercar Experience driving clips, built on 5 Oct 2026 and kept by Omarie as options for
future clips ("instead of saving both clips how about saving both layouts, I'm creating layout options for future
clips"). They are the vlog kit's own components (`../vlog-kit`, the Locked-On language: black plates with the 78/22
gold/white stripe cap, gold #FBD101 as the only accent, Bebas + Michroma) plus one new plate, DRV. HUD-2 has since
moved to dark glass + SE orange #FF4F16 (see Themes below), HUD-1 followed the same day, and on 6 Oct both were
decluttered into one strip (see "One strip" below). **Status: saved as
options, not approved for posting yet.**

Say the code: "use HUD-1 on this clip".

| Code | Camera | What is on screen | Preview |
|---|---|---|---|
| **HUD-1 · Cabin cam** (one strip, dark glass + SE orange; 6 Oct) | Mounted behind the driver's seat, looking forward past the driver | STRIP across the top (SE mark, camera clock + place, heading, side G, progress scrubber); B1 lock-on on the driver with OMARIE · @NQ.YOUNG for the first 4 s | `previews/hud-1-cabin.jpg` |
| **HUD-2 · Hood cam** (one strip, dark glass + SE orange; 6 Oct) | Mounted on the hood or dash, looking down the road (also works on a roof mount looking back down the road; see the Oct 4 build) | STRIP across the top with a route line under it (the stop you're on, then NEXT); C3 lock on the car ahead (CONVOY / CAR AHEAD) for the first 4.5 s | `previews/hud-2-hood.jpg` |

**No road line in either.** Omarie, 5 Oct: "I don't like the road cursor for this point of view and it's not
supercar experience theme". The first look (Wayline, a gold line drawn on the road) is kept only on its page.

## Themes and progress bar (5 Oct)

Omarie, 5 Oct: "change the progress bar and give me some mockups on different themes ... like glass ... and
supercarexperince colors weve used in the past im not digging the yellow". From four mockups he picked **dark glass +
SE orange** (`glass-orange`) with the **clock scrubber** for HUD-2, then "switch HUD-1 to dark glass too". Both
`layouts/hud-*.json` now carry `"theme": "glass-orange"`, A2 `"rail": false` and a PRG `underline`. The other themes
and progress styles stay options. Over a dark cabin (HUD-1) the glass reads as smoky black; over sky (HUD-2) it shows.

- **Themes**, `themes/*.json`, chosen with `build_hud.py --theme themes/<name>.json`:
  - `glass`: frosted, white.
  - `glass-orange`: dark glass with SE orange #FF4F16, the F1 race-weekend Day look.
  - `night-orange`: black plates with SE orange, the race-weekend Night colours.
  - `chrome`: black, white and silver only.
  - `gold`: the current look, the same as no `--theme`.
- **Progress bar**, PRG (`hud_progress.js`), with A2 `"rail": false`. Three styles:
  - `underline`: a scrubber inside the clock plate.
  - `edge`: a lap line across the top of the HUD.
  - `led`: segments down the banner.
- **Glass blurs the footage behind it**, so the capture needs the footage behind each frame: extract the base's frames
  and add `--bg` to kcapture (build step 5). The frames come out already composited; `tools/encode.sh` is unchanged.
  A glass still: `tools/hud_still.js page.html <t> frame.png out.png`.

## One strip (6 Oct)

Omarie, 6 Oct: "i feel like its too clutteres can we fix that plz". Of two lighter versions he picked **A · One
strip**: `drive_strip.js` (STRIP) puts the SE mark, camera clock + place, heading, side G and the progress scrubber
in one dark-glass bar across the top, in place of the A2 banner, D1 clock, DRV plate and PRG bar. HUD-2's route
becomes one line under the strip (`STRIP.route`: the stop you're on, then NEXT). The lock (B1 / C3) now leaves after
its intro (`exit` 4.0 / 4.5 s). The older components still work for other layouts; B ("trimmed": DRV `compact`,
D1 with no `date`) is on file but not used.

## Rules that come with them

- **No speed anywhere** (Omarie, 5 Oct: "No MPH"). Blur the car's own speedometer for the whole clip (HUD-1 reference:
  a feathered gaussian over the cluster, 128x96 at 520,892 in 1080x1920).
- **Number plates** of other cars are blurred, tracked through the shot (`tools/plate_blur.py`). Check every 2nd-3rd
  frame at 3x; single edge letters are acceptable, readable text is not.
- **Never use a stretch where the driver holds a phone.** The Oct 3 clip has it at 194-196 s and at 486 s and 625 s;
  the cut starts after it.
- **Heading is an estimate** until a clip carries GPS (the Osmo Action 6 has no GPS of its own; DJI's GPS Bluetooth
  Remote records it). Side G is real: the camera's own accelerometer, low-passed over 1 s (`tools/side_g.py`).
- **Only name a car when it is identified for sure**; otherwise CONVOY / CAR AHEAD (a camera looking back: REAR VIEW /
  CAR BEHIND). Clients and guests as text only.
- **Camera looking back** (roof or engine-cover mount): the heading is the car's, the opposite of what the camera faces,
  and a left turn shifts the picture to the right. Work it out from the signs and the sun (the Oct 4 build has the method).
- Banner label, route and place lines must be real for the clip (file names, the guide's briefing, a sign in shot).

## What to change per clip

| Field | HUD-1 (`layouts/hud-1-cabin.json`) | HUD-2 (`layouts/hud-2-hood.json`) |
|---|---|---|
| `STRIP.start` | camera clock at the cut's first frame (file name time + in-point) | same |
| `STRIP.place` | e.g. AT THE WHEEL | e.g. OLD TOWN SCOTTSDALE |
| `STRIP.range`, every `t1` | the cut's length | the cut's length |
| tracks | `host` (driver's head, kit tracker `../vlog-kit/lib/track.py`) | `car` (car ahead, `tools/track_csrt.py`; the kit tracker drifted at night) |
| `STRIP.route.waypoints`, `.steps` | none | the route and when each stop goes active; `k` is the 0-based index of the stop you're on |
| `STRIP.heading` / `STRIP.hdgKeys` | one heading | heading keyframes through turns |
| `C3.kicker`, `C3.name`, `C3.exit` | none | CONVOY / CAR AHEAD unless the car is identified (camera looking back: REAR VIEW / CAR BEHIND); `exit` drops the lock before the tracker loses the car |

## Build a new clip

1. **Find the footage without downloading it** (`tools/peek.py`): `index` fetches the tail (the Osmo's index is at
   the end) into a sparse local file; `keys` gives keyframe byte ranges for a contact sheet; `span` + `fill` fetch
   just the cut. Each Dropbox download link is single-use, so ask `download_link` for the same file id once per request.
2. **Cut a base** at 1080x1920, 30000/1001 fps: `ffmpeg -ss <in> -i clip.mp4 -t <len> -vf "scale=1080:1920,fps=30000/1001" ...`
   (square 3840 Osmo footage: crop 2160x3840 first, e.g. `crop=2160:3840:360:0` on the Oct 3 clip). Apply the speedometer blur here.
3. **Track** the driver or the car ahead (`tools/track_csrt.py base.mov x,y,w,h tracks.json car [frames]`, the box on
   the first frame); **blur plates** with `tools/plate_blur.py`. Arizona cars often have no front plate; check at 3x anyway.
4. **Side G**: `tools/side_g.py clip.mp4 <in> <len> side_g.json [--turn a,b,right|left --level]` (needs `pip install
   pyosmogps`). `--level` re-zeroes the straight driving outside the turn; use it when the turn fills much of the cut.
5. **Layer page**: `python3 build_hud.py --scene <your scene>.json --tracks tracks.json --side-g side_g.json --name <name>`
   then `cd ../vlog-kit && node lib/kcapture.js "file://$PWD/.hud_<name>.html" <outDir> seq 30000/1001 <len> --workers 3`
   (needs Pillow for `lib/accum.py`). About 45-65 s for 12 s on a cloud box. **Glass themes (HUD-2):** first
   `ffmpeg -i base.mov -q:v 1 -start_number 0 bg/%05d.jpg`, then add `--bg bg` to the kcapture line (about 200 s for 12 s).
6. **Deliver**: `tools/encode.sh base.mov <outDir> out.mp4` (two-pass H.264 ~11.5 Mb/s, AAC 48 kHz, the clip's own sound at -14 LUFS).

## Reference builds

| | HUD-1: `examples/2026-10-03-at-the-wheel/` | HUD-2: `examples/2026-09-15-drive-back/` |
|---|---|---|
| Source | `NQ Studio/raw footage/2026-10-03/DJI_20261003141901_0152_D.MP4`, 199.0-211.0 s | `NQ Studio/raw footage/2026-09-15/DJI_20260915230003_0032_D.MP4`, 1117.0-1129.0 s |
| Clock | 14:22:20 (file 14:19:01 + 199 s) | 23:18:40 (file 23:00:03 + 1117 s) |
| Real data | camera clock; side G (x axis, left/right not yet confirmed) | camera clock; the route from the guide's briefing (as in the approved rally vlog); side G calibrated on the right turn into the Venetian (about 0.1 g) |
| Estimated | heading | heading (north on Las Vegas Blvd, east through the turn) |
| Redacted | dash speedometer, whole clip | the purple convoy car's plate, tracked; a second car's plate was already unreadable |

Each folder holds the `scene.json`, `tracks.json` and `side_g.json` used. No footage is stored here.

### HUD-2 on a camera looking back: `examples/2026-10-04-old-town/`

The first clip a layout was put on by its code ("put HUD-2 on the next drive clip", 5 Oct). The R8 to the Supercar
Experience lounge in Scottsdale, camera on the roof looking back over the engine cover and the wing.

| | |
|---|---|
| Source | `NQ Studio/raw footage/2026-10-04/DJI_20261004094505_0165_D.MP4`, 898.0-910.0 s; crop `2160:3840:840:0` on the square 3840 footage |
| Clock | 10:00:03 (file 09:45:05 + 898 s) |
| Real data | camera clock; street signs in shot (Indian School Rd at 899 s, Scottsdale Rd through the turn); Old Town (the Sugar Bowl at 911 s); the drive ends at the SE Scottsdale lounge (clip 0167, about 80 s in); side G with `--turn 7,11.5,left --level`, peak 0.31 g in the left turn |
| Estimated | heading: south on Scottsdale Rd, then east after the left turn. With the camera looking back, the facades it sees are lit, so the sun (azimuth 133 degrees at 10:00 MST) is behind the camera |
| Redacted | nothing: the following car has no front plate and the other plates are unreadable at 3x |
