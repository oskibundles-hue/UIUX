---
name: fd-house-style
description: "House rules for Formula Dynamics and Anti Stock Media vertical video. Use when cutting, grading, captioning, rendering or reviewing any short-form vertical spot, reel, vlog or ad; when placing overlays, logo bugs, HUD callouts, spec chips, CTAs or end cards; when picking graphic tone or colour against footage; when building or rebuilding brand assets; or when checking a cut before it is posted. Covers: the five-segment accent stripe, FD red #FE0F13, keep-out zones, cue ordering, the vlog grade, pop captions, -14 LUFS, Pillow/ffmpeg overlay burn-in, and the fault log of traps that have already cost a render."
license: MIT
metadata:
  author: Anti Stock Media
  version: "1.0.0"
---

# FD House Style

The standing rules for Formula Dynamics and Anti Stock Media vertical video. These are not
preferences — each one was paid for with a broken render, a wrong export, or a client question
that could not be answered.

## The five rules that override everything

1. **One source of truth.** Colours, services, partners, canvases and captions live in
   `fd_brand.py`. Change it there and re-run `build_all.py`. **Never edit a generated file** —
   the next rebuild silently reverts it.

2. **Measure before you choose.** Tone, placement and anchors come from the footage, not from
   taste. Sample the luminance in the graphic's own zone and read the *range*, not just the mean:
   a bug that vanishes for two seconds of dark interior is a bug that failed.

3. **Verify a still before you render.** Composite one frame per cue and look at it. A 60-second
   render to discover a callout missed the wheel is 60 seconds wasted; a composited frame costs
   one. Every anchor error in this project was caught — or missed — at this step.

4. **Only publish numbers you can substantiate.** Any dyno, horsepower or performance figure on
   screen must be one that survives a customer asking where it came from. Placeholder figures
   used for layout must never reach an export.

5. **Archive, never delete.** Superseded cuts, grades and iterations stay reachable with a note
   saying what replaced them and when. They are how a decision gets traced back.

## Brand constants

Do not retype these from memory — read `references/brand-spec.md` before touching any asset.

| | |
|---|---|
| FD red | `#FE0F13` — **not** `#DE1A22`, which has shipped by mistake before |
| Green / Yellow | `#1DB14B` / `#FFDE00` |
| Accent stripe | **Five** segments, not four — red 36.7%, black 21.4%, white 19.4%, green 17.0%, yellow 5.5% |
| Display face | Bebas Neue (OFL, ships with the kit) |
| Accent face | Neuropol X — **licensed, not bundled.** Named in the spec, never shipped |
| Loudness | −14 LUFS, limiter 0.84 |

The stripe carries both a black and a white segment. Whichever matches the background reads as a
gap — on a black poster the black segment disappears and the stripe *looks* like four colours.
It is five. `ACCENT_STRIPE` asserts the segments sum to 1.0; segments snap to whole pixels or
you get a one-pixel seam of whatever is underneath.

Partner marks (NV Forged, iPE Exhaust, RYFT) are **their property** and are deliberately not
generated. Request official files and drop them into `03-overlays/partner-logos/`.

## Cut structure

Three rules decide every cue sheet. Read `references/cut-structure.md` for the timings.

- The hook clears before the HUD arrives.
- The HUD clears before the ask.
- The CTA never touches the end card — leave a full second of clean footage between them.

**Two asks in one frame is zero asks.**

### Keep-out zones, 9:16

Nothing load-bearing inside these bands; the platform draws its own UI there.

- **Top 11%** — status bar
- **Bottom 20%** — caption, handle, CTA button
- **Right 16%** — like / comment / share rail
- **Left 5%**

## Picking tone against footage

Sample the luminance (0–255) in the graphic's own zone across the whole clip, then choose. Each
element gets its own answer — `build_edit.py` takes `--bug-tone`, `--title-tone`, `--badge-tone`
and `--endcard-tone` separately, because one clip is not uniformly bright.

| Range in zone | Call |
|---|---|
| High mean, tight range | Black graphic |
| Low mean, tight range | White graphic |
| Very wide range (e.g. 6–228) | **No graphic in that band at all** — move it, or fold the mark into the title block |

When something reads badly, the fix is almost never "make it bigger". Sample the zone, then pick.
Judgement calls get an A/B of rendered stills, not an opinion.

## Rendering

Pillow + ffmpeg is the pipeline. Remotion was tested head-to-head and stays in the repo only as a
cross-check — it cost ~2 min and 255 npm packages against ~64 s and 3 pip packages for no visible
gain, and the two do not agree to the pixel.

Overlays render as **full-frame PNGs at the exact canvas size** (1080×1920, 1080×1350, 1080×1080
or 1920×1080), so dropping one on a CapCut timeline puts it already in position.

> **A still PNG is one frame at PTS 0.** Feed it as `-loop 1 -framerate N -t D` or every fade
> silently does nothing. This trap has burned a full render more than once.

## Anti Stock grade and captions

The approved vlog look — natural, not red, not sharp:

- Black floor 4–11 (lift 0.03), saturation 92% of source, **sharpen 0**
- 2160×3840, 29.97 fps, H.264
- Captions in **pop** style: gold pill on the spoken word

**Caption coverage is a publish gate.** The QC checker reports what percentage of speech is
captioned. On a platform that autoplays muted, uncaptioned dialogue is lost dialogue — anything
under ~65% gets fixed before posting, not after.

## Before anything is posted

Run this list. Any "no" blocks the post.

- [ ] Every on-screen figure is one you can substantiate
- [ ] Red is `#FE0F13`
- [ ] Stripe has five segments and no hairline seams
- [ ] Nothing load-bearing inside the keep-out zones
- [ ] CTA and end card do not touch
- [ ] Caption coverage checked
- [ ] Loudness at −14 LUFS
- [ ] Any music cleared for the use — footage borrowed from another client is not cleared for paid use
- [ ] Partner marks are official files, not regenerated
- [ ] Overlays pulled fresh from `03-overlays/`, not reused from an old timeline

## When something breaks

**Read `references/fault-log.md` before debugging.** Nine failures are logged there with their
actual cause, and most of them looked like something else first — invisible fades that were not a
filter-graph bug, wobbly vectors that were not a potrace setting, callouts pointing at nothing
that were not a seek-accuracy problem. Checking the log first is faster than re-deriving them.
