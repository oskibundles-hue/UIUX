# SE driving HUD layouts (HUD-1, HUD-2)

Two saved layout options for Supercar Experience driving clips, built on 5 Oct 2026 and kept by Omarie as options for
future clips ("instead of saving both clips how about saving both layouts, I'm creating layout options for future
clips"). They are the vlog kit's own components (`../vlog-kit`, the Locked-On language: black plates with the 78/22
gold/white stripe cap, gold #FBD101 as the only accent, Bebas + Michroma) plus one new plate, DRV. **Status: saved as
options, not approved for posting yet.**

Say the code: "use HUD-1 on this clip".

| Code | Camera | What is on screen | Preview |
|---|---|---|---|
| **HUD-1 · Cabin cam** | Mounted behind the driver's seat, looking forward past the driver | A2 SE banner tab (right edge), D1 camera clock + place (top left), DRV drive plate (top right), B1 lock-on on the driver with OMARIE · @NQ.YOUNG | `previews/hud-1-cabin.jpg` |
| **HUD-2 · Hood cam** | Mounted on the hood or dash, looking down the road | A2 SE banner tab, E1 route plate stepping stop to stop (top left), DRV drive plate (top right), C3 lead lock on the car ahead (CONVOY / CAR AHEAD), D1 camera clock + place (bottom left, over the hood) | `previews/hud-2-hood.jpg` |

**No road line in either.** Omarie, 5 Oct: "I don't like the road cursor for this point of view and it's not
supercar experience theme". The first look (Wayline, a gold line drawn on the road) is kept only on its page.

## Rules that come with them

- **No speed anywhere** (Omarie, 5 Oct: "No MPH"). Blur the car's own speedometer for the whole clip (HUD-1 reference:
  a feathered gaussian over the cluster, 128x96 at 520,892 in 1080x1920).
- **Number plates** of other cars are blurred, tracked through the shot (`tools/plate_blur.py`). Check every 2nd-3rd
  frame at 3x; single edge letters are acceptable, readable text is not.
- **Never use a stretch where the driver holds a phone.** The Oct 3 clip has it at 194-196 s and at 486 s and 625 s;
  the cut starts after it.
- **Heading is an estimate** until a clip carries GPS (the Osmo Action 6 has no GPS of its own; DJI's GPS Bluetooth
  Remote records it). Side G is real: the camera's own accelerometer, low-passed over 1 s (`tools/side_g.py`).
- **Only name a car when it is identified for sure**; otherwise CONVOY / CAR AHEAD. Clients and guests as text only.
- Banner label, route and place lines must be real for the clip (file names, the guide's briefing, a sign in shot).

## What to change per clip

| Field | HUD-1 (`layouts/hud-1-cabin.json`) | HUD-2 (`layouts/hud-2-hood.json`) |
|---|---|---|
| `D1.start` | camera clock at the cut's first frame (file name time + in-point) | same |
| `D1.place`, `D1.date` | e.g. AT THE WHEEL, OCT 3 2026 | e.g. BACK TO THE VENETIAN, SEP 15 2026 |
| `A2.label` | e.g. ON THE ROAD · OCT 3 | e.g. RALLY DAY · LAS VEGAS |
| `A2.progress`, every `t1` | the cut's length | the cut's length |
| tracks | `host` (driver's head, kit tracker `../vlog-kit/lib/track.py`) | `car` (car ahead, `tools/track_csrt.py`; the kit tracker drifted at night) |
| `E1.waypoints`, `E1.steps` | none | the route and when each stop goes active; `k` is the 0-based index of the active stop |
| `DRV.heading` / `DRV.hdgKeys` | one heading | heading keyframes through turns |
| `C3.kicker`, `C3.name` | none | CONVOY / CAR AHEAD unless the car is identified |

## Build a new clip

1. **Find the footage without downloading it** (`tools/peek.py`): `index` fetches the tail (the Osmo's index is at
   the end) into a sparse local file; `keys` gives keyframe byte ranges for a contact sheet; `span` + `fill` fetch
   just the cut. Each Dropbox download link is single-use, so ask `download_link` for the same file id once per request.
2. **Cut a base** at 1080x1920, 30000/1001 fps: `ffmpeg -ss <in> -i clip.mp4 -t <len> -vf "scale=1080:1920,fps=30000/1001" ...`
   (square 3840 Osmo footage: crop 2160x3840 first, e.g. `crop=2160:3840:360:0` on the Oct 3 clip). Apply the speedometer blur here.
3. **Track** the driver or the car ahead; **blur plates** with `tools/plate_blur.py`.
4. **Side G**: `tools/side_g.py clip.mp4 <in> <len> side_g.json [--turn a,b,right]` (needs `pip install pyosmogps`).
5. **Layer page**: `python3 build_hud.py --scene <your scene>.json --tracks tracks.json --side-g side_g.json --name <name>`
   then `cd ../vlog-kit && node lib/kcapture.js "file://$PWD/.hud_<name>.html" <outDir> seq 30000/1001 <len> --workers 3`
   (needs Pillow for `lib/accum.py`). About 45-65 s for 12 s on a cloud box.
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
