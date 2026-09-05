# McLaren 765LT — Stage 2 · 9:16 campaign ad

A 15.7s vertical ad cut from shop footage (765LT, doors up, wet floor), built on
the kit rather than beside it: brand constants from `99-toolkit/fd_brand.py`,
type and logo from `fd_render.py`, and the HUD component set from `fd_hud.py` —
the same title block / ticker / callout system used on the **Ferrari Roma** edit.
The CTA caption and end card are composited straight from `03-overlays/`.

**Deliverable:** `exports/formula-dynamics-765lt-15s-9x16.mp4` — 1080×1920, 30fps,
H.264 high, AAC audio from the source clip, `+faststart`. 6.2 MB.
Poster: `exports/poster.jpg`.

## Cue sheet

```
ELEMENT              IN     OUT   HOLD   CONTENT
Title block        0.40   10.90  10.50   MCLAREN 765LT / STAGE 2 BUILD
Ticker             0.90   10.90  10.00   FORMULA DYNAMICS / 765LT / PERFORMANCE
Hook               1.20    4.20   3.00   STOCK IS A STARTING POINT.
Spec readout       4.60    8.40   3.80   STAGE 2 · BUILD SHEET
Callout 001        8.60   10.40   1.80   REAR WING
Callout 002        9.40   10.90   1.50   FORGED WHEELS
CTA               11.30   12.75   1.45   cta_9x16_booking_book-your-build_bar.png
End card          12.90   15.70   2.80   endcard_9x16_dark.png
```

`python3 build_ad.py --dry-run` prints this without rendering.

Timing follows `06-video-system/AUTO-EDIT.md`: the HUD clears the frame 0.4s
before the ask so there is never more than one thing to read, the CTA lands on
the payoff rather than the last frame, and the end card is a hard cut.

## What comes from the kit

| Element | Source |
|---|---|
| Title block (bracket + FD monogram + accent stripe) | `fd_hud.title_block` |
| Ticker (red-slash segments) | `fd_hud.ticker` |
| Callouts (open square, elbow leader, indexed label) | `fd_hud.callout` |
| Accent stripe under the spec heading | `fd_render.accent_stripe` |
| All type — Bebas Neue, tracked | `fd_render.text` / `fit_text` |
| Red `#FE0F13`, white, safe zones, canvases | `fd_brand` |
| CTA caption, end card | `03-overlays/` (full-frame, drop-in) |

All of it renders from the logo artwork traced off
`01-brand-core/logo-source/fd-primary-horizontal_master.png` — see
`FIXED-OVERLAYS.md` at the kit root.

The only thing drawn from scratch is the **spec readout** — the three-row
stock→tuned counter. It is set in Bebas with the brand stripe and red arrows, so
it belongs to the same system.

## One deliberate deviation

**No corner logo bug**, following the Roma look. The FD monogram lives inside
the scrimmed title block instead, where it survives every shot.

The ad previously overrode the `fd_hud` title-block and ticker positions,
because the defaults put the ticker inside the 9:16 bottom keep-out band. That
was fixed upstream in `fd_hud` (0.845 → 0.775 for the ticker, 0.705 → 0.665 for
the title block), so this ad now just uses the defaults.

## Callout anchors

Read off a full-size frame at 9.6s, not a contact sheet, per the AUTO-EDIT note.
The car's true extent was measured with a brightness mask (x 0.33→1.00,
y 0.43→0.70) and the label zones were sampled across four frames spanning the
callout window:

| Zone | Mean | p95 |
|---|---|---|
| 001 label (wing, routed right) | 25 | 84 |
| 002 label (wheels, routed left) | 10 | 59 |

Both are far below the threshold where white type struggles, so the callouts
carry no scrim. Both route **upward** (`drop=-0.11`) so the leader lines clear
the title block, and both labels run toward frame centre.

## ⚠️ Placeholders to replace before this runs as paid media

- **Spec figures.** The stock column is factory 765LT; **the tuned column
  (902 HP / 701 LB-FT / 2.4 SEC) is invented for layout.** Swap in the real dyno
  sheet. The heading says "BUILD SHEET" rather than "DYNO VERIFIED" precisely
  because nothing here is verified yet.
- **Callout labels.** `REAR WING` and `FORGED WHEELS` describe what is visible in
  the frame, not confirmed work orders. Confirm against the real build before
  publishing — a callout on a customer car reads as a claim about what the shop
  fitted.

## Rebuilding

```bash
pip install Pillow cairosvg imageio-ffmpeg
python3 build_ad.py                       # ~65s -> exports/
python3 build_ad.py --dry-run             # cue sheet only
python3 build_ad.py --stills 2.6 6.6 9.9  # preview composited frames
python3 build_ad.py --safe --stills 6.6   # with safe-zone guides
```

`cairosvg` is needed because `fd_render.logo` rasterises the logo SVGs — same
dependency as `99-toolkit/build_all.py`.

Overlay frames land in `.frames/` (gitignored, ~23 MB) and are composited over
the plate in one ffmpeg pass.

## Files

```
build_ad.py                  the edit — all copy and timing in the CONFIG block
source/plate-1080x1920.mp4   compressed 30fps transcode of the 28 MB original
exports/                     the ad, poster, key stills
```

Re-cut from the camera original if you need a higher-quality master.
