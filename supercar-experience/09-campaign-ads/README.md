# Supercar Experience — campaign ads

Vertical 9:16 rental ads cut from car footage, on the same system as the
Formula Dynamics ads: a cue file describes the edit, `build_ad.py` renders it
with Pillow + ffmpeg. Re-cutting with different copy is a one-line change.

## Layout

```
09-campaign-ads/
  build_ad.py          shared renderer (one copy for every car)
  layouts.py           hud / centred / panel / rail treatments
  recut.py             re-cut a plate from a shot list
  make_cues.py         THE source of truth for copy: edit the table, re-run
  <car>/
    cue.json           base cut  (= variant a-price)
    variants/cue-*.json  five angles: a-price b-experience c-occasion d-offer e-engage
    source/plate-1080x1920.mp4   the graded, vertical footage (not in git)
    exports/           rendered MP4s and stills
  _grade/              D-Log LUTs + the vlog grade scripts, for building a plate
  _fd-reference/       the Aventador / 765LT originals this was adapted from
```

## Render

```bash
python3 build_ad.py --car porsche-gt3rs --dry-run          # cue sheet, no footage needed
python3 build_ad.py --car porsche-gt3rs --stills 2.6 6.0 11.5   # verify stills FIRST
python3 build_ad.py --car porsche-gt3rs --all               # base + five variants
```

Cars: `porsche-gt3rs`, `mclaren-750s-spider`, `ferrari-tempesta`.
The 750S Spider cue runs on the 765LT footage and the Tempesta on the Roma
footage, named as the site lists them — per Omarie.

## Building a plate

The renderer wants a clean 1080x1920 clip at `<car>/source/plate-1080x1920.mp4`.
From an Osmo D-Log M raw:

```bash
ffmpeg -i raw.mov -ss START -t 15 \
  -vf "lut3d=_grade/luts/AK_DLogM_Rescue.cube,scale=-2:1920,crop=1080:1920" \
  -r 30 -c:v libx264 -crf 18 -an <car>/source/plate-1080x1920.mp4
```

`_grade/cut_clip.sh --look vlog` is the full house grade (85% histogram match,
greys +2.0 R-B, lift 0.03, knee 0.08, sat 0.92) and needs the reference
frames from "03 Grade Reference"; the LUT above is the quick path.

## Rules carried over

Hook clears before the HUD; HUD clears 1.6s before the ask; the CTA never
touches the end card; keep-out zones top 11% / bottom 20% / right 16% / left 5%.
Every line on screen is on supercarexp.vip — prices, specs, promos,
requirements, locations, the tagline. `_source` on each cue says where.
