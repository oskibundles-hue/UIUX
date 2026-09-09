# Plates — where each car's footage comes from, and what it measured

A plate is 15 s of 1080×1920 at 30 fps in `<car>/source/plate-1080x1920.mp4`.
Nothing here is stock: every frame is either Formula Dynamics shop footage of the
actual rental car or Supercar Experience's own car reel from the site.

Plates are gitignored (they are hundreds of megabytes). `source/zones.json`
next to each one is committed and holds the recipe, so any plate rebuilds from
its own record.

## Porsche 911 GT3 RS

| | |
|---|---|
| Source | Dropbox `Anti Stock Media/01 Raw D-Log/2026-09-03/2026-09-03 23-10-09 gt3 rolling in.mov` |
| Camera | 2160×3840, 60 fps, HEVC, D-Log M |
| Window | 84 s → 99 s — side profile into wheel into front 3/4, no hands in frame |
| Look | `signature` (D-Log rescue → NQ Signature) |
| Layout | `hud` |

```
bug (top 11-19%)    mean  58   range   1-110   white type
mid band (40-60%)   mean 105   range  62-149   white type
cta band (62-72%)   mean  83   range  14-190   wide, but the bar CTA is opaque
lower third         mean  61   range  12-143   white type
```

Dark garage throughout, so type sits straight on the picture.

## Ferrari Tempesta

| | |
|---|---|
| Source | `supercarexp.vip/cars/2023-ferrari-tempesta-las-vegas` — the car reel on the listing |
| Camera | 1080×1920, 24 fps, already graded and delivered |
| Window | 4 s → 19 s — rear 3/4 on gravel, glass detail, exhausts, the road run |
| Look | `none` — the reel is a finished grade; a D-Log rescue on top would double-grade it |
| Layout | `hud` |

```
bug (top 11-19%)    mean 124   range   9-226   too wide -> no corner logo
mid band (40-60%)   mean  65   range  23-117   white type
cta band (62-72%)   mean  47   range  14-96    white type
lower third         mean  41   range  10-99    white type
```

The site's own reel ends on a Supercar Experience card; the window stops well
short of it so our end card is the only one in the cut. No corner logo bug —
the sky swings 9 to 226 in that band, so the monogram lives in the scrimmed
title block instead. Same call as the Ferrari edit in the Formula Dynamics record.

## McLaren 750S Spider

| | |
|---|---|
| Source | Dropbox `Anti Stock Media/01 Raw D-Log/2026-09-04/DJI_20260904140634_0006_D.MP4` |
| Camera | 3840×3840 square, 60 fps, HEVC, D-Log M |
| Window | 7 s → 22 s — rear 3/4, front 3/4, doors up, side |
| Crop | `1728:3072:1056:768` — a 9:16 window out of the square frame, bottom-weighted so the car sits high and the tarmac carries the type |
| Look | `rescue` (D-Log rescue only — `signature` turned the tarmac orange and the car is white) |
| Layout | `panel` |

```
bug (top 11-19%)    mean 121   range  25-238   too wide
mid band (40-60%)   mean 160   range 106-221   too wide
cta band (62-72%)   mean 103   range  34-193   too wide
lower third         mean 136   range  37-203   too wide
```

Midday sun on pale tarmac with a white car and a black shop doorway: every band
swings too far for type on its own, so this car runs the `panel` layout — a
solid card behind the copy — and the lockup under it carries its own scrim.
That is the one place the panel needed fixing: its lockup used to sit at 0.845,
the same line as the ticker, and the two stacked. It now sits at 0.762.

## Rebuilding a plate

```bash
python3 make_plate.py --raw <file> --car <slug> --start <s> --dur 15 \
        --look <none|rescue|signature|golden|dark> [--crop w:h:x:y]
```

It writes the plate and re-measures it. Read the report before choosing a
layout — the layout is a measurement, not a preference.
