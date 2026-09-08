# Aventador S — full build · 9:16 campaign ad

The same 14.04s ad rendered **twice**, from one shared cue sheet, so the two
pipelines can be compared directly.

| | File | Size |
|---|---|---|
| Pillow + ffmpeg | `exports/formula-dynamics-aventador-14s-9x16.mp4` | 6.9 MB |
| Remotion (React) | `exports/formula-dynamics-aventador-14s-9x16-remotion.mp4` | 12.7 MB |

Both are 1080×1920, 30fps, H.264, with the clip's own engine audio.

## The edit lives in cue.json

`cue.json` is the single source of truth — copy, beat timings, layout fractions
and the grade. `build_ad.py` reads it; `remotion/src/AventadorAd.tsx` imports
the same file. Change the edit once, re-render both.

```
ELEMENT            IN     OUT   HOLD   CONTENT
Title block      0.40    8.30   7.90   AVENTADOR S / FULL BUILD
Ticker           0.90    8.30   7.40   FORMULA DYNAMICS / AVENTADOR S / PERFORMANCE
Hook             1.30    4.00   2.70   FULL AERO. NOTHING LEFT STOCK.
Build sheet      4.60    8.30   3.70   AERO KIT · WHEELS · STAGE 1 TUNE · SUSPENSION
CTA              9.90   11.35   1.45   cta_9x16_booking_book-your-build_bar.png
End card        11.60   14.04   2.44   endcard_9x16_dark.png
```

`python3 build_ad.py --dry-run` prints this.

## Why this edit differs from the 765LT

The footage is a **twelve-cut montage** — roughly a cut per second, longest shot
2.6s — against the McLaren's single locked-off take. Three consequences:

- **No callouts.** A leader line anchored to the car is invalid at the next cut.
- **No corner logo bug.** A 4fps brightness survey puts the top band between 23
  (interior) and 239 (blown desert sky); neither a white nor a black bug
  survives both. The monogram lives in the scrimmed title block, as on the Roma.
- **Hook and build sheet sit in the mid band** (y .40–.60), the stable dark zone
  at mean 59 — not the upper third the 765LT used.

Even in the mid band the clip runs a lit tachometer close-up at ~6.2s, so the
type carries a scrim, the same fix `06-video-system/AUTO-EDIT.md` prescribes for
the GT3 RS.

## Copy

Hook is verbatim from `05-copy-library/hooks-and-captions.md` → Body kits.
CTA is `book-your-build`, which the `reveal` (body kits / aero) template uses.

**The build sheet lists only confirmed work** — aero kit (wing, skirts, lip),
wheels, Stage 1 tune, lowered. No horsepower figures: the voice guide asks for
specifics, and there is no dyno sheet for this car. Add one and the rows take
numbers.

## Variations

Four cuts of the same ad. **Footage, build sheet, timings and layout are
identical** — only the hook and the CTA change, so a test isolates the message
rather than the edit.

| Variant | Hook | CTA | Angle |
|---|---|---|---|
| **a** (base) | FULL AERO. / NOTHING LEFT STOCK. | BOOK YOUR BUILD | Booking — highest intent, for an audience that already knows the shop |
| **b** | THIS IS WHAT IT / SHOULD HAVE BEEN. | GET A QUOTE | Quote — sold on the look, now wants a number |
| **c** | THE STANCE / CHANGED EVERYTHING. | WHAT WOULD YOU FIT NEXT? | Engagement — drives comments, which drives reach |
| **d** | CARBON, FROM / EVERY ANGLE. | SEE WHAT FITS YOUR CAR | Fitment — likes the work, hasn't pictured it on their own car |

Every hook is from the body-kit section of
`05-copy-library/hooks-and-captions.md`; every CTA is a stock overlay from
`03-overlays/cta-captions/`, grouped by intent exactly as `fd_brand.CTA_GROUPS`
describes. Run **c** to widen the audience, then retarget with **a**.

```bash
python3 build_ad.py --all                              # base + every variant
python3 build_ad.py --cue variants/cue-b-get-a-quote.json
python3 build_ad.py --all --dry-run                    # all four cue sheets
```

Adding a fifth is a new file in `variants/` — copy one, change `hook`,
`ctaOverlay`, `variant` and `variantAngle`. Nothing else needs touching, and
Remotion renders the same variants:

```bash
cd remotion && ./prepare-assets.sh ../variants/cue-c-what-would-you-fit.json
npm run render
```

## Comparing the two renderers

Measured in this container, same 421 frames:

| | Pillow + ffmpeg | Remotion |
|---|---|---|
| Render | **~64s** single process | ~2 min at `--concurrency=2` |
| Output | 6.9 MB (4.0 Mbps) | 12.7 MB (7.3 Mbps) at defaults |
| Install | 3 Python packages | 255 npm packages, **517 MB** `node_modules` |
| Preview | render a still (`--stills`) | live studio, hot reload (`npm start`) |
| Layout | absolute pixels, computed in Python | CSS/flexbox, browser text engine |
| Runtime need | ffmpeg | ffmpeg **and** a Chromium |

**Where each wins.** The Pillow pipeline is faster, far lighter to install, and
gives exact pixel control — worth it for a repeatable house format. Remotion is
much nicer to iterate in: the studio previews the timeline live instead of
re-rendering stills, and layout is CSS, so a new component is a React component
rather than a set of paste coordinates.

**They are visually equivalent, not pixel-identical.** Two different text
engines. At t=2.6 the hook block measures ink-top 800 / height 282 in Pillow
against 774 / 287 in Remotion — within 26px of position and 5px of height. Two
causes, both documented in the code:

- `fd_render.with_shadow` pads each layer before pasting, so Pillow's real ink
  lands 32px below the nominal band top and lines advance by their *padded*
  height. Remotion matches the measured output rather than the nominal values.
- CSS `letter-spacing` adds a trailing gap after the last glyph, so the hook
  overflowed the type column until it was fitted with `@remotion/layout-utils`
  `fitText` — the direct equivalent of `fd_render.fit_text`.

The grade also differs slightly: ffmpeg's `vignette` is approximated with a CSS
radial gradient, and Remotion's sky reads a touch brighter.

## Rebuilding

```bash
# Pillow
pip install Pillow cairosvg imageio-ffmpeg
python3 build_ad.py

# Remotion
cd remotion && npm install
npm run render
```

**The `--browser-executable` flag is required here.** Remotion defaults to a
Chrome that has removed old headless mode and the launch fails; the
pre-installed `chromium_headless_shell` works — `npm run render` passes it for
you.

`remotion/public/` is generated by `./prepare-assets.sh` (also run by
`npm run render`), which copies in the plate, Bebas Neue, the CTA and end-card
overlays and the FD monogram. Remotion can only serve assets from `public/`, so
these are duplicated at build time rather than committed twice — `public/` is
gitignored.

## Source

`source/plate-1080x1920.mp4` — 30fps transcode of the supplied 14.04s clip
(1080×1920, 23.08fps source, audio mean −11.5 dB peaking at 0.0 dB). Shot
2025-09-27, golden hour, Red Rock Canyon, NV.

**The car:** Lamborghini Aventador S (LP 740-4), gloss black — S-specific front
bumper with deep splitter and vertical vanes, Y-shaped tail lights,
"Lamborghini" engine-deck script, single hexagonal centre-exit exhaust. Shop
work confirmed: fixed rear wing, carbon side skirts, front lip, aftermarket
wheels, Stage 1 tune, lowered.

A second car appears in convoy at ~5s, frame left. Confirmed as not relevant, so
nothing in the edit draws attention to it.
