# Fault log

Nine failures, with what each one actually turned out to be. Most presented as something else
first; the wrong diagnosis is recorded alongside the right one, because the wrong one is the
trap that costs the time.

---

### Every fade invisible in the burned video

**Looked like:** a filter-graph bug.
**Actually:** a still PNG is one frame at PTS 0, so a fade with a start time after zero never
fires.
**Fix:** feed stills as `-loop 1 -framerate N -t D`.

---

### Traced vectors came out wobbly

**Looked like:** potrace parameters. They were tried, and changed nothing.
**Actually:** the source raster has soft, noisy edges.
**Fix:** blur each ink's alpha by 0.7 px before thresholding, then trace.

---

### potrace produced inverted shapes

**Actually:** potrace treats `0` / `False` as foreground.
**Fix:** invert masks before tracing.

---

### Type clipped at the top — "BODY" rendered as "BUUY"

**Actually:** the baseline was placed at `size × 0.4`, pushing glyph tops off the canvas.
**Fix:** size the canvas from `font.getmetrics()`, never from a fraction of the point size.

---

### Letter-spacing leaked into every paragraph of the PDF

**Actually:** `Tc` is graphics state and survives `ET`. One tracked heading silently re-spaced the
rest of the document until text ran off the page.
**Fix:** reset `setCharSpace(0)` inside the same text object.

---

### HUD callouts pointed at nothing

**Looked like:** fast-vs-accurate ffmpeg seeking. Tested — the frames were byte-identical, so
that was not it.
**Actually:** two anchors were read off **300 px contact-sheet thumbnails** and were out by
roughly 0.15 of the frame width.
**Fix:** this one was method, not code. Read anchors from full-size frames using a colour mask
for the car's true extent, and verify a composited still before rendering.

---

### Spec chips overlapped on short clips

**Actually:** a 1.6 s hold floor exceeded the 1.35 s slot on a 22-second clip with four chips.
**Fix:** clamp — `hold = min(2.8, max(1.0, slot × 0.8), slot − 0.2)`.

---

### The asset index listed the wrong bundles

**Actually:** build order. `build_all.py` generated the index before the ZIPs existed.
**Fix:** bundles run first.

---

### Red type died on the yellow tach shot

**Fix:** four treatments were rendered as stills and compared side by side. A soft scrim won.
Judgement calls get an A/B, not an opinion.

---

## Two silent-failure classes worth naming

**A generator that is never called.** `build_cta_captions()` was not wired into `build_all.py`,
so a full rebuild silently skipped all 64 CTA overlays and they would have kept a stale stripe
indefinitely. When a rebuild "succeeds", check the file count changed.

**A figure drawn on a background that hides part of it.** The stripe figure drawn straight onto a
white PDF page read as a gap where the white segment sat — the exact confusion the correction
existed to end. Put multi-segment figures on a neutral plate with per-segment labels.
