# Brand spec

Canonical values. `fd_brand.py` is the source of truth — if this file and the code disagree, the
code wins and this file needs updating.

## Colour

| Role | Hex | Note |
|---|---|---|
| Red | `#FE0F13` | The brand red. `#DE1A22` is **wrong** and has shipped by mistake |
| Black | `#000000` | |
| White | `#FFFFFF` | |
| Green | `#1DB14B` | |
| Yellow | `#FFDE00` | |

### The accent stripe

Five segments, left to right:

| Segment | Width |
|---|---|
| Red | 36.7% |
| Black | 21.4% |
| White | 19.4% |
| Green | 17.0% |
| Yellow | 5.5% |

Two failure modes:

1. **Read as four colours.** Whichever of black/white matches the background reads as a gap. On a
   black poster the stripe *looks* like red / white / green / yellow. It is five.
2. **Hairline seams.** Segment edges on fractional pixels leave a one-pixel line of whatever is
   underneath — on a transparent overlay, a sliver of raw video. Snap segments to whole pixels.

`ACCENT_STRIPE` asserts the segments sum to 1.0 so an edit cannot leave it lopsided.

## Type

| Role | Face | Licence |
|---|---|---|
| Display | Bebas Neue | OFL — ships with the kit |
| Accent | Neuropol X | **Licensed.** Named in the spec, deliberately not bundled. Buy it |

## The logo

The shipped logo was originally reconstructed by tracing it out of the brand-guide scan. It
looked right. Measured against the master artwork it carried **8.71% mean pixel error**.
Re-traced from the supplied master, that fell to **0.84%** — which is as close as a traced vector
gets to an anti-aliased raster, i.e. measurement noise rather than error.

**Anything exported before the re-trace carries the 8.71% logo.** If a logo was already dragged
into a CapCut project, pull it again from `02-logos/` rather than trusting the copy in the
timeline.

## Canvases

Overlays render as full-frame PNGs at the exact canvas size, so they land in position when
dropped on a timeline.

- `1080×1920` — 9:16 vertical (the default)
- `1080×1350` — 4:5
- `1080×1080` — 1:1
- `1920×1080` — 16:9

## Partners

NV Forged, iPE Exhaust and RYFT marks are their property and are **deliberately not generated**.
Request official files and place them in `03-overlays/partner-logos/`.

A partner name earns a full plate rather than a chip — a named partner is what earns the reshare.

## Audio

- Master to **−14 LUFS**, limiter 0.84, so a set of spots plays as one campaign.
- Sound-designed cuts carry SFX on the animation's own beats and **no music**, so a licensed
  track sits under them cleanly.
- Picture-only masters carry no audio track at all — for handing to an editor, or a platform that
  supplies its own audio.

> Music lifted from another client's footage is **not cleared** for paid use on this brand. Check
> before it runs as an ad.

## Rebuild

```bash
python3 99-toolkit/build_all.py
```

Bundles build before the index. If a rebuild reports success, confirm the generated file count
actually changed — a generator that is never called fails silently.
