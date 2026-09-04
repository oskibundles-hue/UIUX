# FORMULA DYNAMICS — 9:16 social ad

A 15.7s vertical ad for a performance tuning shop, built by compositing animated
typography onto supplied shop footage (McLaren 765LT, doors up, wet floor).

**Deliverable:** `exports/formula-dynamics-15s-9x16.mp4` — 1080×1920, 30fps, H.264
high profile, AAC audio from the source clip, `+faststart`. 6.4 MB.
Poster frame: `exports/poster.jpg`.

## Cut

| Time | Beat | Copy |
|---|---|---|
| 0.35 – 12.3 | Persistent HUD lockup, hairline draws in under it | `FORMULA DYNAMICS` · `PERFORMANCE ENGINEERING` |
| 1.05 – 4.3 | Headline A — lines wipe in from the left, staggered, accent rule under | **STOCK IS A / STARTING POINT.** |
| 4.8 – 8.6 | Spec readout — three rows, values count up from stock to tuned | `STAGE 2 · MCLAREN 765LT` |
| 9.1 – 12.1 | Headline B | **BUILT ON DATA. / TUNED BY HAND.** |
| 12.4 – 15.7 | End card — scrim, tach emblem sweeps, wordmark, CTA | `BOOK A DYNO SESSION` · `FORMULADYNAMICS.COM` |

## Design system

- **Display:** Big Shoulders Bold — condensed, uppercase, negative tracking. Headline
  size auto-fits the type column, so longer copy shrinks instead of overflowing.
- **Labels / data:** Geist Mono — uppercase, wide tracking, for anything that should
  read as instrumentation rather than marketing.
- **Palette:** ink `#EDEAE4`, dim `#96928A`, signal red `#FF3B21`. The red is pulled
  from the car's tail light bar so the accent belongs to the footage.
- **Grade:** `contrast 1.05 / saturation 0.95`, vignette. Deliberately restrained —
  the plate is already dark and heavy grading falls apart under platform re-encode.
- **Legibility:** gradient scrims under the HUD, the spec block, and the lower type
  block instead of boxes or drop shadows.
- **Emblem:** tachometer arc with tick marks and an FD monogram, drawn in code
  (supersampled 4× then downsampled), sweeping up as the end card resolves.

## Safe areas

All type sits inside 96px side margins, below y=150 and above y=1590, clearing the
Reels / TikTok / Shorts caption band and the right-hand action rail. The spec block
sits in the upper third specifically to stay clear of the right rail, which occupies
roughly y=1000–1600.

Check it any time with:

```bash
python3 build_ad.py --safe --stills 2.6 6.8 13.9
```

Cyan = type-safe box, yellow = right action-rail edge.

## ⚠️ Spec figures are placeholders

`SPECS` in `build_ad.py` currently reads 755 → 902 HP, 590 → 701 LB-FT, 2.7 → 2.4 sec.
The stock column is factory 765LT; **the tuned column is invented for layout purposes.**
Replace it with real dyno numbers from the actual build sheet before this runs as paid
media — advertised performance claims need to be ones the shop can substantiate.
Same for `DOMAIN`, which is a placeholder.

## Rebuilding

```bash
pip install Pillow imageio-ffmpeg
python3 build_ad.py                          # full render -> exports/
python3 build_ad.py --stills 2.6 6.8 13.9    # preview single composited frames
python3 build_ad.py --crf 23                 # smaller file
```

Everything editable — copy, timing, spec rows, palette — lives in the `CONFIG` block
at the top of `build_ad.py`. The drawing code reads from it; don't hardcode strings
further down.

Render takes ~80s: Pillow writes 471 RGBA overlay frames to `.frames/` (gitignored,
~23 MB), then ffmpeg composites them over the plate in one pass.

## Files

```
build_ad.py                      renderer (Pillow overlay + ffmpeg composite)
source/plate-1080x1920.mp4       graded-neutral footage plate, 30fps (re-render input)
fonts/                           Big Shoulders + Geist Mono (SIL OFL, licenses included)
exports/                         the ad, poster, key stills
```

The plate is a compressed transcode of the original 28 MB ProRes-ish `.mov` so the
render is reproducible from the repo alone. Re-cut from the camera original if you
need a higher-quality master.
