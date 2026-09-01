# Toolkit

The scripts that generated every asset in this kit. You never *have* to run
them — the output is committed. Run them when something needs to change.

## Why generate instead of hand-designing

Change the brand red once, re-run one command, and all 190+ files update
together. No file gets forgotten and nothing drifts out of spec.

## Setup

```bash
pip install Pillow numpy potracer cairosvg
```

Python 3.9+.

## Rebuild everything

```bash
cd 99-toolkit
python3 build_all.py
```

## Files

| File | Does |
|---|---|
| `fd_brand.py` | **Single source of truth.** Colours, type, services, partners, contact, canvas sizes. |
| `fd_render.py` | Shared rendering helpers — logo loading, text, accent stripe. |
| `build_logos.py` | Extracts logo lockups from the brand guide and traces them to SVG. |
| `build_overlays.py` | Builds swatches, bars, bugs, lower thirds, badges, titles, end cards, safe zones. |
| `build_tokens.py` | Writes `brand-tokens.json` / `.css`. |
| `build_index.py` | Regenerates `ASSET-INDEX.md`. |
| `build_all.py` | Runs everything in order. |

## Common changes

**Change a colour** — edit the constant in `fd_brand.py`, run `build_all.py`.

**Add a service** — add a row to `SERVICES` and an entry to `SERVICE_SUBLINE`,
run `build_all.py`. You get a lower third and badge in every format.

**Add or rename a partner** — edit `PARTNERS`, run `build_all.py`.

**Change contact details** — edit `WEBSITE` / `INSTAGRAM` / `EMAIL`, run
`build_all.py`. End cards regenerate.

**Add a title card** — add a row to `TITLES` in `build_overlays.py`.

**Swap in original vector logos** — see the last section of
`../02-logos/LOGO-USAGE.md`.

## How the logo extraction works

The brand guide is a raster, so `build_logos.py` reconstructs vectors from it:

1. **Crop** each lockup from `brand-guide-master.png`.
2. **Key** the artwork off the black background. Each pixel is fitted as
   `alpha × ink` against the five brand colours; the best-fitting ink wins.
   That produces a clean alpha channel *and* snaps every colour to an exact
   brand hex, removing compression drift.
3. **Smooth** each ink's alpha before thresholding. The source has soft, noisy
   edges; without this the noise traces through as visible wobble on straight
   strokes.
4. **Trace** each ink layer to bezier curves with potrace, then assemble one
   SVG per colour variant.

The monogram is taken from the primary lockup rather than the small icon
swatch, where it is rendered about 25% larger.
