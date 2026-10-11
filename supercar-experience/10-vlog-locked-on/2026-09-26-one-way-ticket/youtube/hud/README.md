# One-way ticket: the personal driving HUD and the 720p rough cut

Style **Lifestyle**, personal channel @nq.young, 16:9, personal brand only (Anton, #DE1A22, #FBD101, white; no SE
orange/gold, no SE HUD). Omarie, 2026-10-09: "is there no animations or hud driving?", picked "Personal HUD on drives".
Spec: `../PLAN.md`, section "Driving HUD". The HUD is an overlay on the assembled picture; no chapter is re-rendered.

## Files

| file | what |
|---|---|
| `make_hud.py` | the driving-shot list (`DRIVE`, with place and why per shot), run merging, title avoidance, camera clock and trip progress -> `hud.json` |
| `hud.json` | every run: chapter and global times and frames, and per shot: clip, source in, place, clock, progress |
| `render_hud.py` | draws the HUD at any height (`H`; all sizes scale from it) -> one qtrle RGBA clip per run + `runs.json` |
| `assemble.py` | the rough cut: wav concat and join check, one encode with the HUD, loudness, chat copies, chapter markers, gate sheets |

Big files live in `/home/user/day-owt/roughcut/` (not in git).

## Rebuild

    python3 make_hud.py                                         # -> hud.json (prints the run list)
    python3 render_hud.py /home/user/day-owt/roughcut/hud720 720 --stills   # HUD clips + design_sheet.png
    python3 assemble.py audio       # mix_full.wav / nomusic_full.wav, audio_report.txt
    python3 assemble.py video       # one_way_ticket_roughcut_720p.mp4 (+ _NOMUSIC remux)
    python3 assemble.py loud
    python3 assemble.py send        # _send_part1.mp4 / _send_part2.mp4 (960x540, under 29 MiB each)
    python3 assemble.py chapters    # chapters.txt
    python3 assemble.py gate        # gate/hud_runs_*.jpg, gate/joins_*.jpg

For the 4K pass: `render_hud.py OUT/hud2160 2160` draws the same HUD at 4K (the clip is only the panel's box; place it
at `runs.json` x, y). `assemble.py` would need its scale and paths switched to the 4K masters.

## Which shots carry it

Only shots where the car is being driven (cabin, side camera, windscreen, rear deck, moving). Not on parked talk, gas
stations, the shop, the airport or the plane, so Ch1, Ch2, Ch5 and Ch6 carry none. The opening's **hook** (0:00-0:16,
including the two 0121 desert cutaways) stays clean because the approved 12 points say the hook has no text; the
opening's story-montage drives do carry it (`OPENING_DRIVES = True` turns that off). The 0090 roll-up in Ch3 (staff
bringing the car out, before the trip starts) is not counted. Shots closer than 1 s merge into one run; each run fades
and slides in and out over 0.3 s. Runs stop 0.1 s before a chapter title and resume 0.1 s after it, and never end on
a sliver (under 1 s) of a new shot.

## What it shows

- **Place** (Anton): the chapter's own place or what he says in the shot; the state where the town isn't known:
  SEATTLE, WA (Ch3 title) / WASHINGTON (0093-0098: after the shop, before Oregon; 0098 shows the I-90 "Easton" exit
  sign) / OREGON (0100, spoken) / NEVADA (Ch7 title; 0121 and 0122 42.4 where the city isn't in view) /
  LAS VEGAS, NV (0122 skyline, the Ch8 "LAS VEGAS" shots).
- **Clock** (Archivo 600): the DJI camera clock, ticking by the minute = the clip's file-name timestamp
  (`clips.json` `clock`) + the source offset of the frame (re-timed shots count source time). The MP4 `creation_time`
  is the same instant in UTC (0114: 01:29:01 in the name, 08:29:01Z in the metadata), so the camera is on UTC-7 (PDT),
  the same clock as the Ch6 "1:29 A.M." title.
- **Route line**: a stylised zig-zag Seattle -> Oregon -> Idaho -> Nevada -> Las Vegas (no map, roads or distances),
  white ahead, red travelled, a yellow dot with a slow pulse ring. At a run's start the red line draws in to the dot;
  at a shot change the dot glides.
- **Progress bar**: the same position as a thin bar (red fill, yellow cap), no numbers or %.
- Position = camera clock interpolated between five node moments where he is on camera in that place: Seattle 0092
  139.95 (11:59 AM), Oregon 0100 18.2 ("we passed the welcome to Oregon sign", 4:06 PM), Idaho 0106 283.3 ("I am in
  Nampa, Idaho", 7:44 PM), Nevada 0116 4.55 (Ch7 "Sunrise · Nevada", 6:24 AM), Las Vegas 0122 552.6 (the skyline,
  9:06 AM). A schematic, not a measured route.

## Look

Lower-left at the chapter titles' x (5.5 % in), bottom at 92 % of the height; about 250 x 90 px at 720p
(`SCALE = 0.85`). Soft dark backing (black at 42 %, rounded). It never sits under a title card. Blur boxes on the
driving shots (cluster, TFT, plates, hoodie print) sit at mid-frame or right of it; the gate sheet is the check.
