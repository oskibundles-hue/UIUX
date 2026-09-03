# Creator Kit — Osmo Action 6 → Instagram

A colour and delivery pipeline for vlog / lifestyle / LARP content shot on a
DJI Osmo Action 6 in D-Log M, plus the packaging and growth playbook that goes
with it.

```
creator-kit/
├── luts/                  6 creative look LUTs (.cube, 33³)
├── scripts/
│   ├── build_luts.py      regenerates the LUT pack (pure stdlib)
│   └── ig_export.sh       Osmo clip → Instagram-ready 1080×1920 master
└── docs/
    ├── 01-capture-settings.md    what to set on the camera
    ├── 02-mobile-workflow.md     DJI Mimo + CapCut → upload
    ├── 03-hooks-and-captions.md  hooks, captions, covers
    └── 04-growth-system.md       pillars, cadence, 30-day plan
```

## Start here

1. **Camera** — `docs/01-capture-settings.md`. Shoot 4K 4:3, 60fps, D-Log M
   10-bit, manual white balance, 1/120 shutter.
2. **Convert** — download DJI's official D-Log M → Rec.709 LUT from
   <https://www.dji.com/lut>. This kit deliberately does not ship one; see below.
3. **Grade** — apply a look from `luts/` on top of that conversion.
4. **Deliver** — `docs/02-mobile-workflow.md` for CapCut, or `ig_export.sh` on
   a laptop.

## Why there is no conversion LUT in this kit

DJI does not publish the D-Log M transfer function. A conversion LUT generated
without it is guesswork, and a wrong conversion is worse than none — it bakes
in a colour error that every later adjustment amplifies.

So this kit ships **look** LUTs only. They expect footage already in Rec.709 and
are applied after DJI's official conversion:

```
D-Log M clip → DJI official conversion → look LUT from this kit
```

## The looks

| LUT | For |
|---|---|
| `AK_Neutral_Punch` | Daily driver. Clean contrast and colour, nothing stylistic. |
| `AK_Golden_Vlog` | Golden hour, cafés, interiors. Warm midtones, cool shadows. |
| `AK_Forest_LARP` | Woodland. Deepens foliage, protects skin, cools shadows. |
| `AK_Nordic_Steel` | Overcast, combat, winter. Cold, high contrast, desaturated. |
| `AK_Film_Halation` | Montage and B-roll. Lifted matte blacks, faded film feel. |
| `AK_Night_City` | Low light, firelight, streets. Opens shadows without noise bloom. |

Every look carries mild compensation for Instagram's encoder baked in: a small
black floor lift so shadows band less after transcode, a guard on extreme reds
(the first thing 4:2:0 chroma subsampling smears), and a highlight rolloff so
skies compress instead of clipping.

Regenerate or tweak them:

```bash
python3 scripts/build_luts.py            # writes luts/*.cube
python3 scripts/build_luts.py --size 65  # finer, larger files
```

The generator validates every look before writing: output stays inside the
legal 0–1 cube, the neutral ramp stays monotonic (no posterising on grey
gradients), and black and white points land in range. A look that fails
validation is not written.

## The export script

```bash
./scripts/ig_export.sh clip.mp4 \
  -c ~/Downloads/DJI_DLogM_to_Rec709.cube \
  -l luts/AK_Forest_LARP.cube \
  -m fill -f 30 -o reel.mp4
```

Produces 1080×1920, square pixels, H.264 High, yuv420p, tagged bt709, faststart,
audio normalised to −14 LUFS. Reframe modes are `fill` (centre crop), `fit`
(letterbox) and `blur` (blurred background fill).

Requires ffmpeg with `libx264`, `lut3d`, `unsharp` and `loudnorm`. Run
`--help` for all options.

**Why it targets 1080×1920 rather than 4K:** Instagram re-encodes everything and
downscales anything above 1080 on the long edge. Delivering a clean 1080×1920
master means you control the resampling and sharpening instead of their
encoder. 4K uploads typically come back softer, not sharper.
