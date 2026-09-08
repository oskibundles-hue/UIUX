# Aventador S — 9:16 campaign ad (in progress)

Footage plate cut and analysed; the edit is not built yet, pending confirmation
of what the shop actually did to the car.

## Source

`source/plate-1080x1920.mp4` — 30fps transcode of the supplied 14.04s clip
(1080×1920, 23.08fps source, loud engine audio: mean −11.5 dB, peaks 0.0 dB).
Shot 2025-09-27, golden hour, Red Rock Canyon, NV.

## Shot structure — a cut roughly every second

Twelve scene changes in 14 seconds. This does **not** behave like the 765LT
clip, which was one locked-off shot in a dark bay.

| Time | Shot |
|---|---|
| 0.0–1.2 | Carbon rocker / sill macro, very tight |
| 1.2–2.1 | Rolling front wheel — yellow caliper, Lamborghini centre cap |
| 2.1–3.9 | Interior: hand on wheel, extended paddle shifter |
| 3.9–4.3 | Rear tracking, low |
| 4.3–5.9 | Rear 3/4 — wing, diffuser (a second car is in convoy, frame left) |
| 5.9–6.7 | Interior |
| 6.7–8.0 | Rear follow |
| 8.0–10.6 | Front 3/4 tracking against the escarpment |
| 10.6–14.0 | Rear follow into the sunset, wing in silhouette |

## The car

**Lamborghini Aventador S (LP 740-4), gloss black.** Identified from the
S-specific front bumper with deep splitter and vertical vanes, the Y-shaped
tail lights, the "Lamborghini" engine-deck script, and the single hexagonal
centre-exit exhaust. Not an SVJ.

### Visible modifications

1. **Large fixed rear wing** on tall pedestals with upswept endplates. The
   Aventador S ships a low, body-coloured *retractable* spoiler, so this is an
   added fixed wing. It appears in five of the twelve shots and is the car's
   silhouette in the closing sunset follow — the headline mod.
2. **Carbon side skirts / rockers** — the opening macro is a clean read on real
   twill weave.
3. **Front lip / splitter** — an added lower element at 9.2s catching light
   separately from the bumper.
4. **Dark multi-spoke wheels**, gloss black/anthracite; look aftermarket forged,
   brand not readable at this resolution.

### Not confirmed — do not put on screen without the build sheet

Exhaust (centre outlet is in shadow, factory vs aftermarket unreadable), wheel
brand, ride height, and the yellow calipers (a factory option, so not
necessarily shop work).

## Brightness survey — why the overlay must differ from the 765LT

Sampled at 4fps across the whole clip:

| Band | Min | Max | Mean | Swing |
|---|---|---|---|---|
| Top (y .05–.20) | 23 | **239** | 188 | **216** |
| Mid (y .40–.60) | 25 | 82 | **59** | 56 |
| Lower (y .62–.80) | 6 | 93 | 44 | 87 |

- **No corner logo bug.** The top band runs from blown-out desert sky (239) to
  near-black interior (23); neither a white nor a black bug survives both ends.
  This is the case `06-video-system/AUTO-EDIT.md` documents for the GT3 RS. The
  FD monogram goes inside the scrimmed title block, as on the Roma and 765LT.
- **Hook and any spec readout belong in the mid band**, the stable dark zone
  (mean 59, max 82) — not the upper third used on the 765LT.
- **Callouts are a poor fit here.** A leader line anchored to the car is invalid
  the moment the shot cuts, and the longest shot is 2.6s. Recommend dropping
  them and letting the cuts carry the pace.

## Next

Two builds off one shared cue sheet, for comparison:
1. The existing Python/Pillow + ffmpeg pipeline (as `mclaren-765lt-stage2`).
2. A Remotion project rendering the identical edit. Verified available:
   Remotion 4.0.522 on the npm registry, Node v22.22.2, and Chromium
   pre-installed at `/opt/pw-browsers/chromium` for the render.
