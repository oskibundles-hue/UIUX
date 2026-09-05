# Fixed overlays — re-cut from sharp logo artwork

**Every overlay in `03-overlays/` and every bundle in `08-download-bundles/` was
regenerated.** If you downloaded a pack before this, delete it and download
again. The filenames are unchanged, so anything already on a CapCut timeline
keeps working — swap the file and it lands in the same position.

---

## What was wrong

The logo was soft. Corners that should be hard came out rounded, and the FD
monogram in particular looked melted at large sizes — most visible on end cards
and title cards, where the mark is biggest.

The cause was the source, not the tracer. The first version of this kit traced
its logo artwork out of `01-brand-core/brand-guide-master.png`, a 1491×1055
raster in which the lockup occupies 596×250 px and the mark just **149×114 px**.
Every logo in the kit was a trace of that, scaled up — and the tracer was also
blurring the source by 0.7 px before tracing, which rounded the corners further.

Measured against the supplied master artwork, at matched size:

| | Mean error vs master |
|---|---|
| Logo that shipped in v1 | **8.71%** |
| Trace of the master (now) | **0.84%** — the anti-aliasing floor |

0.84% is as close as a traced vector gets to an anti-aliased raster; it is
measurement noise, not error.

## What changed

- **`01-brand-core/logo-source/fd-primary-horizontal_master.png` is now the
  source of truth.** It is the supplied master: transparent background, exact
  brand hexes, no compression drift.
- `99-toolkit/build_logos.py` was rewritten to trace from it. It finds the four
  components — mark, wordmark, accent stripe, PERFORMANCE — by occupancy rather
  than fixed pixel boxes, so a future master export drops straight in.
- No source blur, `alphamax` 0.7 (below potrace's 1.0 default) and
  `opttolerance` 0.2, at 8× supersample: corners stay corners.
- All four lockups — `primary-horizontal`, `stacked`, `icon`, `icon-mark-only` —
  plus all four variants and all three PNG widths were rebuilt.
- All 254 overlay and template files, all 10 download bundles, the printable
  brand guide PDF and `ASSET-INDEX.md` were regenerated from them.

Nothing was redrawn. `primary-horizontal` is the master itself; the other three
lockups are the master's own components restacked into the arrangement those
lockups already used.

## The accent stripe is five segments, not four

Reading the master turned up a second error. The stripe was specified here as
four segments — red / white / green / yellow at 42 / 24 / 20 / 14. The real
artwork has **five**: red 36.7%, black 21.4%, white 19.4%, green 17.0%,
yellow 5.5%.

It carries both a black and a white segment, and whichever matches the
background reads as a gap. On black footage: red / gap / white / green / yellow.
On white: red / black / gap / green / yellow. `fd_brand.ACCENT_STRIPE` now holds
all five, so the stripe is correct on either background.

## Also fixed: the HUD ticker sat under the caption

Unrelated to the logo, found in the same pass. `fd_hud.ticker` defaulted to
`y=0.845` — inside the 9:16 bottom keep-out band
(`SAFE_ZONES_9X16["bottom"] = 0.20`, i.e. below `y=0.80`), where the Reels and
TikTok caption covers it. The default is now `0.775`, and `title_block` moved
from `0.705` to `0.665` to keep the pair clear of each other.

---

## The standing rule for future overlays

**Build logo artwork from `02-logos/`, which is traced from the master.**

- Do not trace the logo out of `brand-guide-master.png`. That raster is a
  reference image of the brand guide, not artwork.
- Do not redraw or approximate the mark in code. `BRAND-SPEC.md` §4 forbids it,
  and a hand-drawn FD will not match.
- In code, load logos through `fd_render.logo(stem, width=…)`, which rasterises
  the SVG at the exact pixel size needed — never upscale a PNG.
- Changing the logo means replacing the master and re-running
  `99-toolkit/build_logos.py`, then `build_overlays.py`, then
  `build_bundles.py`. `build_all.py` does the whole chain.

## Verifying

```bash
cd 99-toolkit
pip install Pillow numpy potracer cairosvg reportlab
python3 build_all.py
```

To check sharpness after any change, rasterise a lockup at the master's own size
and compare coverage against the master. Anything above ~2% mean error means
the artwork is being sourced from the wrong place again.
