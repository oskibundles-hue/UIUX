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
| Source | `supercarexp.vip/cars/2025-porsche-gt3rs-las-vegas` — the car reel on the listing |
| Camera | 720x1280, 24 fps, already graded; upscaled to 1080x1920 |
| Window | 12 s → 27 s — rear wing, side rolling, front 3/4, the head-on highway pass |
| Look | `none` — already graded |
| Layout | `panel` |

```
bug (top 11-19%)    mean 180   range  91-246   too wide -> no corner logo
mid band (40-60%)   mean 104   range  54-156   white with shadow
cta band (62-72%)   mean  79   range  21-167   too wide
lower third         mean  89   range  28-154   white with shadow
```

Open desert sky behind the type, so this car runs `panel` as well. The window
stops before the Supercar Experience card the reel ends on.

**This replaced an earlier cut.** The first version used Formula Dynamics shop
footage of a GT3 RS, but that is a different car from the one on the rental
listing. Rental ads run on the rental car — the shop clip is a Formula Dynamics
asset, not a Supercar Experience one.

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
| Source | Dropbox `Supercar Experience/01 Car Footage/SCE_McLaren-750S_no-branding.mov` |
| Camera | 2160x3840, 24 fps, already graded, no on-screen branding |
| Window | 2 s -> 17 s - front 3/4 past the rocks, wheel, the bridge, the head-on desert pass |
| Look | `none` - already graded |
| Layout | `hud` |

```
bug (top 11-19%)    mean 130   range  56-211   too wide -> no corner logo
mid band (40-60%)   mean  63   range  12-115   white type
cta band (62-72%)   mean  54   range   6-136   white type
lower third         mean  57   range   4-155   scrimmed by the title block
```

This is the master of the reel the rental listing runs - same dark car, same
canyon road - at full 4K vertical, so it downscales to 1080x1920 instead of
being upscaled. It is the best source of the three.

**This replaced two earlier attempts.** The first ran on Formula Dynamics shop
footage of a white McLaren, which is a different car. The second could not be
made at all: the video on the rental listing is 124x224 at 468 KB, a broken
upload. Omarie supplied the master on 9 Sept and the car was unblocked.

Note the layout flipped from `panel` to `hud` when the footage changed. That is
the process working: the shop footage was midday sun on pale tarmac and needed a
card behind the type; this one is a dark car on a dark road and does not.

## Fall Rally 2026 — a montage, not a plate

| | |
|---|---|
| Source | six clips from Dropbox `Supercar Experience/01 Car Footage/` |
| Built by | `make_montage.py`, not `make_plate.py` |
| Length | 18 s — six cuts of 3 s |
| Look | `none` — every clip is already graded |
| Layout | `panel` |

Cut order, and why:

| # | Clip | In | Why here |
|---|---|---|---|
| 1 | Urus | 0.0 | Two cars on a desert road. A rally is a convoy, so the first frame says so. |
| 2 | Tempesta (Roma) | 12.0 | Red car on open road, sun low. |
| 3 | SF90 gold | 2.5 | Highway roll, different colour and direction from cut 2. |
| 4 | F8 Tributo black | 0.0 | Black against pale sky, the strongest contrast in the set. |
| 5 | SF90 gold | 20.0 | Gold car through poppies at golden hour — the best image in the folder, so the CTA beat lands on it. |
| 6 | Mixed fleet | 7.5 | Runs under the end card, so it carries the least. |

```
bug (top 11-19%)    mean 181   range  88-250   too wide -> no corner logo
mid band (40-60%)   mean 100   range  50-178   white with shadow
cta band (62-72%)   mean  68   range   8-121   white type
lower third         mean  69   range  15-119   white type
```

A montage cuts under the type every three seconds, so the copy sits on the
`panel` card regardless of what any single band measures.

**Cut 5 was moved on purpose.** In the first assembly the poppy-field shot was
last, which put it almost entirely behind the end card. Swapping cuts 5 and 6
puts it under the call to action instead.

Rebuild it with:

```bash
python3 make_montage.py --car fall-rally --fps 30 \
    --clip "<file>@<in>:<dur>" ...     # repeat, in cut order
python3 make_plate.py --car fall-rally --measure-only --dur 18
```

## Ferrari F8 Tributo

| | |
|---|---|
| Source | Dropbox `Supercar Experience/01 Car Footage/SCE_Ferrari-F8-Tributo_black_no-branding.mov` |
| Camera | delivered graded, 15.6 s — the whole clip is used |
| Window | 0.3 s → 15.3 s |
| Look | `none` — Omarie's own grade |
| Layout | `panel` |

```
bug (top 11-19%)    mean 159   range  54-250   too wide -> no corner logo
mid band (40-60%)   mean  79   range  21-144   white type
cta band (62-72%)   mean  84   range  14-191   too wide
lower third         mean  96   range   6-184   too wide
```

Three of four bands come back too wide, so the copy sits on the card. The edit
cuts about once a second and several of those cuts are detail shots — a seat,
a wheel arch, asphalt — which is exactly the case the panel exists for. The
master is 15.6 s and the plate is 15 s, so there is no better window to pick;
the clip's closing fade to black lands under the end card.

## Lamborghini STO

| | |
|---|---|
| Source | Dropbox `Supercar Experience/01 Car Footage/SCE_Lamborghini-Huracan-STO_green_no-branding.mp4` |
| Camera | delivered graded, 24.8 s |
| Window | 6.0 s → 21.0 s — the Strip run, past the opening static frames |
| Look | `none` |
| Layout | `panel` |

```
bug (top 11-19%)    mean  74   range  14-167   too wide -> no corner logo
mid band (40-60%)   mean  94   range  53-130   white type
cta band (62-72%)   mean  55   range  16-221   too wide
lower third         mean  50   range  11-220   too wide
```

Night footage, so the means are low, but the two lower bands top out over 220
where the sun catches the rear wing and the street lights pass. A low mean with
a 200-point swing is the worst case for type on its own: it reads for most of
the cut and then disappears. Card.

## AMG GT Black Series

| | |
|---|---|
| Source | Dropbox `Supercar Experience/01 Car Footage/SCE_Mercedes-AMG-GT-Black-Series_no-branding.mov` |
| Camera | delivered graded, 17.9 s |
| Window | 2.0 s → 17.0 s |
| Look | `none` |
| Layout | `hud` |

```
bug (top 11-19%)    mean  25   range   2-96    white type
mid band (40-60%)   mean  48   range  15-91    white type
cta band (62-72%)   mean  37   range   4-85    white type
lower third         mean  37   range   3-115   white type
```

The only one of the four that takes type direct on the picture. Every band
stays under 115 and no mean goes over 96 — night shooting, with the car lit
against dark ground rather than sky. The corner logo bug is safe here,
unlike the other three.

## Lamborghini Novitec Urus

| | |
|---|---|
| Source | Dropbox `Supercar Experience/01 Car Footage/SCE_Lamborghini-Urus_purple_scottsdale_no-branding.mp4` |
| Camera | delivered graded, 16.9 s |
| Window | 0.5 s → 15.5 s |
| Look | `none` |
| Layout | `panel` |

```
bug (top 11-19%)    mean  90   range  21-169   too wide -> no corner logo
mid band (40-60%)   mean  54   range  24-108   white type
cta band (62-72%)   mean  85   range  13-171   too wide
lower third         mean 115   range  14-199   too wide
```

The lower third is the brightest of any plate in this set — mean 115 — because
the desert road fills the bottom of frame under open sky. That is the band the
price rows live in, so the card is not optional here.

Matching the master to a listing took a check: Supercar Experience rents four
Urus variants, and only the Novitec Wide Body is purple. The Mansory is silver,
the 2022 is red, the Urus S is black. Confirmed against each listing's hero image.

## What the site can and cannot supply

Every car listing on supercarexp.vip carries its own reel, and 21 of the 22 are
usable — 5 to 229 MB, mostly 720x1280. They are the safest source for a rental
ad because they show the actual rental car.

The exception is the **McLaren 750S Spider**: its video is 124x224 at 15 fps,
468 KB. That is a broken upload, not a low-quality one, and no amount of
upscaling makes a 1080x1920 ad out of it. That car is on hold until real
footage exists.

There is also a Rally reel on the site, `supercar-experience-presents-the-rally`,
15 MB — enough for a Rally spot when one is wanted.

## Rebuilding a plate

```bash
python3 make_plate.py --raw <file> --car <slug> --start <s> --dur 15 \
        --look <none|rescue|signature|golden|dark> [--crop w:h:x:y]
```

It writes the plate and re-measures it. Read the report before choosing a
layout — the layout is a measurement, not a preference.
