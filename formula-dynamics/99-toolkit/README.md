# Toolkit

The scripts that generated every asset in this kit. You never *have* to run
them — the output is committed. Run them when something needs to change.

## Why generate instead of hand-designing

Change the brand red once, re-run one command, and all 190+ files update
together. No file gets forgotten and nothing drifts out of spec.

## Setup

```bash
pip install Pillow numpy potracer cairosvg reportlab
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
| `build_pdf.py` | Builds the printable brand guide PDF. |
| `build_bundles.py` | Zips the kit into downloadable bundles. |
| `build_edit.py` | Burns the overlays into a video clip. Not part of `build_all`. |
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


## SFX kits (23 Sept)

Every approved ad opens on `riser-short` into `impact-hard` and closes the same
way, because `LAYER_SFX` in `fd_sfx.py` is one fixed voicing per layer. Eleven
ads that sound identical read as one ad run eleven times.

`ALTERNATES` gives the loud layers - title, CTA, title block, endcard, spec,
lower-third - more than one way to speak, built entirely from the seventeen
sounds already in the kit. No new assets.

| kit | character |
|---|---|
| `signature` | exactly what the approved ads use. The default. |
| `deep` | long riser, sub-drop over impact. Heavier, slower. |
| `tight` | whoosh and `impact-tight`, key-clicks instead of ui-ticks. Drier. |
| `minimal` | one soft hit per cue. For a short cut or a quiet clip. |
| `auto` | derives kit and seed from the output filename, so a set of ads differs and each still re-renders identically. |

    --sfx-kit auto            # recommended for a set
    --sfx-kit deep --sfx-seed 7

**Pitch does the rest.** Seventeen wavs is not much, so each hit is resampled a
little (±0.8 to ±1.6 semitones by kit) with a deterministic per-hit seed. The
third ui-tick in a run no longer lands on the same note as the first. Gain
moves ±8% and timing ±12 ms with it.

### Measured

Spectral distance on the SFX bed alone, where voicing is the only variable:

| | |
|---|---|
| `deep` vs `minimal` | 0.297 |
| `deep` vs `tight` | 0.256 |
| `signature` vs `deep` | 0.198 |
| two entirely different approved ads (whole mix) | 0.272 - 0.476 |
| same kit, different seed | 0.019 - 0.029 |
| **`signature`, any seed** | **0.000** |

`deep` against `minimal` moves the bed further than the gap between two
approved ads that share nothing - different car, footage, length and music.
Seed alone is deliberately subtle: it breaks repetition inside a cut, it does
not change the character.

**`signature` is bit-identical to the old behaviour**, and provably so rather
than by inspection: `voicing_for(fam, "signature")` returns the original
`LAYER_SFX` object itself and `KIT_JITTER["signature"]` is 0.0, so no resample,
gain or timing shift runs. Re-rendering an approved ad cannot change its sound.
