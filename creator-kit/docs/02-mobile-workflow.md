# Mobile workflow — DJI Mimo + CapCut → Instagram

You edit on mobile, so this is built around that. The goal is to get D-Log M
converted correctly, graded consistently, and out of CapCut without throwing
away the quality you paid for at capture.

## The pipeline

```
Action 6 (D-Log M 10-bit)
   │
   ├─ 1. CONVERT   D-Log M → Rec.709      (DJI Mimo, or CapCut LUT import)
   │
   ├─ 2. LOOK      creative grade          (LUT, or CapCut sliders)
   │
   ├─ 3. EDIT      cuts, text, sound       (CapCut)
   │
   └─ 4. EXPORT    1080×1920 H.264         (settings below — this step
                                             is where most quality is lost)
```

**Step 1 is not optional and not creative.** D-Log M is a transfer curve, not a
look. Ungraded it is flat and milky; if you try to fix that with contrast and
saturation sliders you will tear the image apart. Convert first, *then* grade.

## Step 1 — the conversion

DJI does not publish the D-Log M maths, so any "D-Log M → Rec.709" LUT built
from scratch by a third party (or by an AI) is guesswork. **Use DJI's official
one.** Download it free from <https://www.dji.com/lut> — pick the Osmo Action
entry, or the closest current Action/Pocket model.

Two ways to apply it on mobile:

- **DJI Mimo** — import your clips, apply the D-Log M → Rec.709 LUT, export.
  This is the most reliable mobile path because Mimo knows the format.
- **CapCut** — Filters → Import LUT. This works on CapCut *Desktop* reliably;
  on mobile it depends on your app version. If you do not see an import option,
  use Mimo for the conversion, or use the slider recipes below.

## Step 2 — the look

The `luts/` folder in this kit holds six looks. They go **after** the
conversion, never instead of it.

| Look | Use it for |
|---|---|
| `AK_Neutral_Punch` | Daily driver. Clean, safe, when in doubt. |
| `AK_Golden_Vlog` | Golden hour, cafés, interiors, anything warm and inviting. |
| `AK_Garage_Chrome` | Garages, workshops, showrooms, car builds, walkthroughs. |
| `AK_Nordic_Steel` | Overcast, combat, winter, dramatic beats. |
| `AK_Film_Halation` | Montages, B-roll, anything cut to music. |
| `AK_Night_City` | Night vlogs, bars, streets, torch and firelight. |

Each one already carries mild compensation for Instagram's encoder: a slight
black lift so shadows band less, a guard on extreme reds (the first thing to
smear in 4:2:0 chroma), and a highlight rolloff so skies compress instead of
clipping.

### If you cannot import LUTs — CapCut slider recipes

These approximate the same looks using CapCut's Adjust panel. Apply them
**after** the D-Log M conversion. They are close, not identical.

| | Neutral Punch | Golden Vlog | Garage | Nordic Steel | Film Halation | Night City |
|---|---|---|---|---|---|---|
| Brightness | 0 | 0 | 0 | 0 | 0 | +8 |
| Contrast | +18 | +16 | +22 | +28 | +10 | +12 |
| Saturation | +10 | +8 | −4 | −16 | −8 | −10 |
| Temperature | 0 | +12 | −5 | −14 | +6 | −4 |
| Tint | 0 | 0 | +2 | 0 | 0 | +3 |
| Highlights | −5 | −8 | −6 | −10 | −12 | −6 |
| Shadows | +5 | +8 | +10 | +8 | +14 | +22 |
| Fade | 0 | +4 | +5 | +4 | +12 | +8 |
| Sharpen | +25 | +25 | +25 | +30 | +20 | +15 |
| HSL | — | — | Blue: Sat +10 | Orange: Sat +15 | — | — |

Save your favourite as a CapCut template so you are not rebuilding it every
edit. Consistency across posts is itself a growth lever — it makes your grid
recognisable in the feed.

## Step 3 — editing for retention

Watch time is the number one ranking signal, and the average Reel is watched
for about **8.5 seconds**. Everything below exists to get past that.

- **First frame is a hard cut into motion.** No fades, no logo, no slow push in.
- **Shot length 1.5–3 seconds** for most of the edit. When a shot outlives its
  information, cut.
- **Cut on motion** — mid-gesture, mid-step, mid-swing. Cuts on stillness feel
  like stops.
- **Pattern interrupt every 5–7 seconds**: speed ramp, sound drop, angle change,
  text card.
- **Design the loop.** If your last frame matches your first, the replay is
  seamless and replays count as watch time. This is free reach.
- **Captions burned in.** Most people watch muted first. CapCut auto-captions,
  then fix the proper nouns — it will mangle car models and brand names every time.

## Step 4 — export (do not skip this)

CapCut export settings:

| Setting | Value |
|---|---|
| Resolution | **1080p** |
| Frame rate | **30fps** (60 only if the whole piece is motion) |
| Bitrate | **Higher** / custom **10–12 Mbps** |
| Codec | **H.264** |
| Format | **MP4** |
| Smart HDR | **Off** |

**Export 1080p, not 4K.** Instagram downscales anything above 1080 on the long
edge and its downscaler is worse than CapCut's. Handing it a clean 1080×1920
means you control the resampling and the sharpening. A 4K upload usually comes
back *softer*, not sharper.

**Turn Smart HDR off.** HDR metadata that Instagram does not honour is the
usual cause of a Reel that looks washed out or blown on some phones and fine on
yours.

## Step 5 — upload settings

On Instagram, once:

- Settings → Data usage and media quality → **Upload at highest quality: ON**
- **Data Saver: OFF**
- **Upload on Wi-Fi.** On a weak connection Instagram compresses harder to get
  the file through. This is real and very visible.

## The desktop option

If you have access to a laptop, `scripts/ig_export.sh` in this kit does steps
1, 2, 4 and the sharpening in one pass, at higher quality than any mobile app:

```bash
./ig_export.sh clip.mp4 \
  -c ~/Downloads/DJI_DLogM_to_Rec709.cube \
  -l luts/AK_Garage_Chrome.cube \
  -m fill -f 30 -o reel.mp4
```

It outputs exactly 1080×1920, square pixels, H.264 High, yuv420p, correctly
tagged bt709, faststart, with audio normalised to −14 LUFS (Instagram's own
target, so your Reels do not jump in volume against everyone else's).

Run `./ig_export.sh --help` for all options.
