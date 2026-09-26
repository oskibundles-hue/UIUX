# FULL STOP.

**CLAUDE — Motion Designer — Showreel 2026**  
`15.000 s · 900 frames · 1920×1080 · 60 fps · 128 BPM · 4/4 · 8 bars · F minor`

> A single Signal-orange full stop is born at the end of a word, learns to move, and travels through every discipline of motion design (weight, timing, space, easing, energy, print, grid, liquid, data, glitch, shape) until it lands, with a squash and two small bounces, as the period after CLAUDE.

This is the final storyboard, written by the executive creative director. It synthesizes four pitches (scores and provenance at the end). Every scene below is built in parallel by a separate engineer who sees only this document and `src/engine.js`, so every handoff is specified as an exact, held rest pose. The machine-readable twin is [`storyboard.json`](storyboard.json); run `node tools/scaffold.mjs` from it to generate the manifest.

## Contents

1. [Concept, motif, arc](#concept)
2. [House style: palette, type, grid, easing, springs](#house-style)
3. [Handoff protocol](#handoff-protocol)
4. [Timing table](#timing)
5. [s00-frame: The Frame — persistent editorial HUD](#s00-frame)
6. [s01-axis: Axis — LIGHT / HEAVY / NARROW / WIDE](#s01-axis)
7. [s02-timing: Timing — the dot learns to move](#s02-timing)
8. [s03-space: Space — the corridor](#s03-space)
9. [s04-easing: Easing — the graph editor](#s04-easing)
10. [s05-energy: Energy — breath, drop, chaos into RANGE](#s05-energy)
11. [s06-range-1: Range I — C · L · A · U](#s06-range-1)
12. [s07-range-2: Range II — D · E · the specimen row · the squeeze](#s07-range-2)
13. [s08-fullstop: Full Stop — the name card](#s08-fullstop)
14. [Global FX cue list](#global-fx-cue-list)
15. [Music plan, bar by bar](#music-plan)
16. [Picture-lock hit list](#hit-list)
17. [Craft notes for builders](#craft-notes-for-builders)
18. [Pitch scores and provenance](#scores-and-provenance)
19. [Open questions](#open-questions)

<a id="concept"></a>
## Concept, motif, arc

**Motif: the full stop.** One flat Signal #FF4A1C disc is the protagonist and the connective tissue of every transition. It is born as the period of WIDE, becomes a character that stamps 'Timing is everything.' into existence, a portal we dive through, the light at the end of a type corridor, the object a live bezier curve eases, the seed of a 12,000-particle explosion, the ripple source of a halftone, a module of a grid, a bubble in liquid, the origin of a chart, the heart of a glitch, the full stop of an E, and finally the hanging period of 'CLAUDE.' and the dot of the original 'C.' monogram. Rules: (1) at every handoff the dot is a perfect flat circle (no stroke, glow or gradient); (2) it is the only object that crosses cuts; (3) in the montage it is centre-locked (Ø112 at (960,540)) on every cut so the eye never has to search; (4) typographic rule of the reel: the full stop always HANGS outside the measure (WIDE. / Timing is everything. / CLAUDE.). Around it sits one editorial system: a Swiss grid, Volt blueprint lines, JetBrains Mono annotations and a persistent HUD frame whose beat meter proves the picture is locked to the music.

| Act | Window | What happens |
|---|---|---|
| **HOOK** | 0.000–1.875 (bar 1) | Frame 0 is already moving: hairline LIGHT rises while blueprint lines shoot out, then SLAMS into black HEAVY on beat 2. Every word performs the axis it names (LIGHT, HEAVY, NARROW, WIDE), one per beat, and the dot is born on the and-of-4 as WIDE's hanging full stop. |
| **BUILD** | 1.875–7.031 (bars 2–4) | One continuous take with no hard cut. The dot learns to move (12 principles, stamping 'Timing is everything.'), dives into itself (exponential zoom) into a Signal field that unfolds into a 3D type corridor, rushes into a Paper wall that becomes a bezier graph editor where a cursor drags a handle out of the box and the dot is literally eased with overshoot. |
| **BREATH** | 7.031–7.500 (bar 4, beat 4) | Lights out. Tape-stop, letterbox, a ring implodes and the dot compresses and trembles: the reel's biggest anticipation, one beat of near-silence. |
| **DROP** | 7.500–9.375 (bar 5) | The dot detonates into 12,000 particles, curls into two vortices, breathes again, then snaps into a crisp dot-matrix RANGE. Whip-pan. |
| **RANGE** | 9.375–12.656 (bars 6–7) | A centre-locked montage that accelerates from beats to 8ths to 16ths: C halftone, L grid, A liquid, U data, D glitch, E shape. It covertly spells the name, revealed on beat 3 of bar 7 as a specimen row 'CLAUDE.' when the dot lands as its period. |
| **SQUEEZE** | 12.656–13.125 (bar 7, beat 4) | The row flattens to plain type and condenses to width 62 with a tremble; the drums drop out; the last 16th is silent. |
| **RESOLVE** | 13.125–15.000 (bar 8) | The final hit releases the name to width 125 (anticipation and release applied to a logotype). The dot is flung, lands as the hanging period and bounces twice. Role, year, tagline and monogram set in; everything is locked by 14.0625; on beat 4 a tiny dot drops into the 'C.' monogram; the card holds. |

**Why it wins.** It is one idea carried all the way through, so fifteen seconds of range read as authorship rather than a tech demo. The plainest mark in typography becomes a character, a portal, a vanishing point, an eased object, a particle seed, a halftone cell, a grid module, a bubble, a data origin and finally the period after the name. Type is the spine and the variable axes carry meaning: LIGHT is hairline, NARROW is condensed, and the name's closing width-62 squeeze and width-125 release is anticipation and release applied to a logotype. It speaks to motion people in their own language (onion skins, spacing charts, a live bezier editor whose overshoot leaves its box) while giving everyone else a hook on beat 2, a drop, a montage that secretly spells CLAUDE and a satisfying landing. The rhythm is composed: a slam per beat, a continuous take, a silent breath, the drop, cuts accelerating from beats to 8ths to 16ths, a silent 16th and the final hit, then a held beat. And it is built to be built: every handoff is a rest pose held for two frames (a dot at exact pixels, a solid colour field, or one canonical text element), the one overlap shares a single whip formula, and all type numbers come from measurements taken in the pipeline's own Chromium.

<a id="house-style"></a>
## House style

### Palette (locked)

| Token | Hex | Role |
|---|---|---|
| **Ink** | `#0B0B0F` | Primary ground. Statements, energy, the end card. |
| **Paper** | `#F3F0EA` | Type on Ink; ground for "systems" moments (graph editor, halftone, data). |
| **Signal** | `#FF4A1C` | THE DOT, plus heat: impact flashes, the corridor, cursors and handles, one flash colour. Never body text. |
| **Volt** | `#2B59FF` | Blueprint accent: construction lines, dimension lines, bezier handles; one full-frame moment (A, liquid). |
| **Acid** | `#D7FF3A` | Sparingly: ≤3% of pixels anywhere, except the single E (shape) 8th and its row cell. |
| **Graphite** | `#1C1C22` | Secondary surfaces, grid lines on Ink. |
| **Fog** | `#8A8A93` | Annotations, ghosts, onion skins, secondary labels. |
| Volt-light | `#718EF8` | mix(Volt, Paper, 0.35): small Volt labels on Ink (legibility). |
| Signal-deep | `#541E13` | mix(Signal, Ink, 0.70): the far end of the corridor shading. |
| any mix()/alpha of two palette colours |  | Allowed. No other hues, no pure white or black (except engine flash white and letterbox black), no blurred drop shadows. |

### Type (locked)

| Face | Usage and measured metrics |
|---|---|
| **Archivo (variable)** | Hero display. wght 100–900, width via CSS font-stretch 62%–125% (canvas: keywords only, extra-condensed = 62.5%, expanded = 125%). Default tracking -0.01em, never tighter than -0.03em. Measured: flat cap height 0.6875 em, round overshoot 0.700 em, baseline overshoot 0.0125 em, x-height 0.531 em; with line-height 1 the baseline sits 0.833 em below the line-box top. |
| **Instrument Serif italic** | One editorial line per act only: "Timing is everything" and "Motion Designer". Cap 0.734 em; line-height 1 baseline at 0.84 em. |
| **JetBrains Mono** | Labels, readouts, timecode, code. 500 weight, uppercase, tracking 0.12em (labels) / 0.24em (the end-card year line); tabular figures; advance 0.6 em; line-height 1 baseline at 0.86 em. |
| **Sizes** | Must-read words: ≥ 48 px display / ≥ 26 px mono, on screen and fully static ≥ 0.35 s (key messages ≥ 0.5 s). Annotations may be 14–16 px (decorative, never must-read). |

### Grid

- Frame 1920×1080, centre C = (960,540). Safe area x 96→1824, y 96→984. The outer band belongs to the HUD (s00) and the montage captions (x = 72).
- Editorial grid: 12 columns, 96 px margins, 16 px gutters (column 129.33 px). Hairlines when shown: Fog 1 px at 8% (20% on arrival flashes).
- Montage anchor: (960,540). Glyph vignettes use cap ≈ 780 px so the cut rhythm reads as one system.
- End-card measure: x 200→1720 (the name spans it exactly); the period hangs outside at x 1734→1794.

### Easing language (engine names)

| Name | Curve | Use |
|---|---|---|
| `R.ease.swift` | `cubic-bezier(0.16, 1, 0.30, 1)` | Default "arrive": reveals, draws, snaps into place. |
| `R.ease.snap` | `cubic-bezier(0.85, 0, 0.15, 1)` | Hard in-out between two held poses (dot relocations, the squeeze). |
| `R.ease.whip` | `cubic-bezier(0.70, 0, 0.84, 0)` | Accelerate into a cut: exits, rushes, retracts. |
| `R.ease.glide` | `cubic-bezier(0.45, 0, 0.10, 1)` | Camera moves and cursor travel. |
| `R.ease.punch` | `cubic-bezier(0.20, 1.6, 0.40, 1)` | Overshoot pops (arms, badges). |
| `R.ease.anticipate` | `cubic-bezier(0.60, -0.40, 0.40, 1)` | Moves that dip back first. |
| `inOutCubic` | `Penner` | The shared whip-pan P(t) and drags. |

### House springs (`R.spring(t, {...})`)

| Name | Params | Character |
|---|---|---|
| **TIGHT** | `{stiffness: 420, damping: 26}` | ζ≈0.63, ~8% overshoot, settles ≈0.30 s: type and UI snaps. |
| **POP** | `{stiffness: 380, damping: 18}` | ζ≈0.46, ~19% overshoot, settles ≈0.44 s: landings, pops, letter eruptions. |
| **SOFT** | `{stiffness: 180, damping: 16}` | ζ≈0.60, ~10% overshoot, settles ≈0.50 s: big masses (particles to targets). |
| **WOBBLE** | `{stiffness: 300, damping: 10}` | ζ≈0.29, ~39% overshoot: liquid and settle wobbles only. |
| **HINGE** | `{stiffness: 240, damping: 19}` | Corridor unfold (~9% overshoot past 90°). |
| **ROLL** | `{stiffness: 320, damping: 22}` | Corridor 90° rolls. |

<a id="handoff-protocol"></a>
## Handoff protocol

- A scene is visible on frame f iff start ≤ f/60 < end (engine rule). An event at grid time T first appears on frame ceil(60·T); audio hits land exactly on T (picture ≤ 16.7 ms late, well inside lip-sync tolerance).
- REST POSE: at a hard handoff time T the outgoing scene reaches the specified handoff state no later than T - 2/60 and holds it (its last rendered frame is ≤ T - 1/60). The incoming scene draws that identical state at local time 0 and starts moving on its first frame.
- 2D OVERRIDE: when a handoff is reached through 3D or an exponential zoom, the outgoing scene hides that machinery for the rest frames and draws the handoff state as a flat 2D layer, so rounding can never leak across the cut.
- Canonical text: any word shared across a cut is ONE text element with identical CSS in both scenes (specified in the handoff); it is never rebuilt from per-letter spans on the handoff frames.
- The only overlap (9.140625–9.375) uses one shared pan function P(t); the incoming scene is on top and transparent outside its own panel.

**Shared whip function** (s05 → s06 overlap only): `u = (t − 9.140625) / 0.234375`, `P(t) = 1920 · inOutCubic(u)`. s05 draws its layer at `x = −P(t)`; s06 draws its opaque world panel at `x = 1920 − P(t)` on top. One camera move, one seam.

**HUD colour schedule** (the s00 text, crop marks and meter outlines switch on these exact frames, with no fades):

| From (s) | Frame | Colour | Because |
|---|---|---|---|
| 0.0 | 0 | Paper `#F3F0EA` | s01/s02 on Ink |
| 3.75 | 225 | Ink `#0B0B0F` | s03 opens on a solid Signal field, then the corridor |
| 7.03125 | 422 | Paper `#F3F0EA` | lights out (covered by the letterbox until 7.5) |
| 9.375 | 563 | Ink `#0B0B0F` | C on Paper |
| 9.84375 | 591 | Paper `#F3F0EA` | L on Ink, A on Volt |
| 10.78125 | 647 | Ink `#0B0B0F` | U on Paper |
| 11.25 | 675 | Paper `#F3F0EA` | D on Ink |
| 11.484375 | 690 | Ink `#0B0B0F` | E on Acid |
| 11.71875 | 704 | Paper `#F3F0EA` | row, squeeze and end card on Ink, to the end |

<a id="timing"></a>
## Timing table

Grid: beat 0.46875 s · bar 1.875 s · 8th 0.234375 s · 16th 0.1171875 s. Bar n starts at (n − 1) × 1.875 s. Positions are `bar.beat.16th` (1-based, as in the engine debug overlay).

| Scene | Window (s) | Frames | Musical | Length | z | In | Out |
|---|---|---|---|---|---|---|---|
| **s00-frame** The Frame | 0.0 → 15.0 | 0–899 | 1.1.1 → 8.4.4 | 32 beats | 900 | — | — |
| **s01-axis** Axis | 0.0 → 1.875 | 0–112 | 1.1.1 → 1.4.4 | 4 beats | 10 | cold open, frame 0 in motion | shared still: the lone dot |
| **s02-timing** Timing | 1.875 → 3.75 | 113–224 | 2.1.1 → 2.4.4 | 4 beats | 20 | shared still | exponential dive → solid Signal |
| **s03-space** Space | 3.75 → 5.15625 | 225–309 | 3.1.1 → 3.3.4 | 3 beats | 30 | Signal field unfolds | rush → Paper wall + dot |
| **s04-easing** Easing | 5.15625 → 7.03125 | 310–421 | 3.4.1 → 4.3.4 | 4 beats | 40 | Paper + dot | lights-out match cut on the dot |
| **s05-energy** Energy | 7.03125 → 9.375 | 422–562 | 4.4.1 → 5.4.4 | 5 beats | 50 | lights out | whip-pan (8th overlap) |
| **s06-range-1** Range I | 9.140625 → 11.25 | 549–674 | 5.4.3 → 6.4.4 | 4 beats + 8th overlap | 60 | whip-pan landing | centre-locked match cut |
| **s07-range-2** Range II | 11.25 → 13.125 | 675–787 | 7.1.1 → 7.4.4 | 4 beats | 70 | centre-locked cut | flash + identical word |
| **s08-fullstop** Full Stop | 13.125 → 15.0 | 788–899 | 8.1.1 → 8.4.4 | 4 beats | 80 | final hit | end (held beat) |

**Shot rhythm** (what the eye perceives): 4 × 1-beat word slams → a 4-beat continuous character take → a 3-beat corridor → a 4-beat UI take → a 1-beat silent breath → a 3.5-beat drop + 8th whip → 4 × 1-beat vignettes → 2 × 8th vignettes → 16th pops into a 2-beat reveal → a 1-beat squeeze with a silent 16th → a 4-beat resolve whose last 2 beats hold.

<a id="s00-frame"></a>
## s00-frame: The Frame — persistent editorial HUD

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 0.0 → 15.0 s | 0–899 | 1.1.1 → 8.4.4 | 32 beats | 900 | none (transparent) |

**Showcases:** Swiss editorial system as art-direction glue · UI typography and odometer micro-interactions · rhythm made visible (a beat meter that lands on every kick)

**Layout and fixed geometry**

- Drawn above every scene (z 900) and below the engine post-FX (so shake and zoom move it with the picture). Root has NO background.
- All text: JetBrains Mono 500, 15 px, uppercase, letter-spacing 0.12em, opacity 0.9, colour = HUD colour (schedule below). Crisp: no filters; translate only.
- Crop marks: four L-corners, arms 28 px, stroke 2 px, square caps; corner vertices at (32,32), (1888,32), (32,1048), (1888,1048); arms run inward along the frame edges.
- TL: "CLAUDE — MOTION DESIGNER", left x=72, baseline 76 (≈259 px wide).
- TR: "SHOWREEL 2026", right-aligned x=1848, baseline 76.
- BL: chapter index "NN / WORD", left x=72, baseline 1016.
- BR: timecode "TC 00:00:SS:FF" right-aligned x=1848, baseline 1016 (≈151 px wide); SS = floor(t), FF = floor(t·60) mod 60, zero-padded, pure function of t (last frame reads TC 00:00:14:59).
- BR beat meter: four 10×10 squares with top y=1005, left x = 1614, 1630, 1646, 1662. The square at index floor(t/0.46875) mod 4 is filled Signal; the others are 1.5 px outlines in the HUD colour. On each bar downbeat the first square is Paper for 2 frames before turning Signal.

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 0.0 → 0.2 | 0 | 1.1.1 | Crop marks draw from each vertex outward: arm = 28·swift(clamp((t + 1/60)/0.2)); frame 0 already shows ~43%. All labels are fully set on frame 0 (the hook needs no fade). |
| 0.0 | 0 | 1.1.1 | Chapter "01 / WEIGHT". |
| 1.875 | 113 | 2.1.1 | Chapter "02 / TIMING". On every change the digits roll up out of a one-line mask (0.117 s, swift, 2-frame stagger per digit) and the word re-types left→right at 1 char/frame. |
| 3.75 | 225 | 3.1.1 | Chapter "03 / SPACE". |
| 5.15625 | 310 | 3.4.1 | Chapter "04 / EASING". |
| 7.03125 → 7.5 | 422 | 4.4.1 | Letterbox bars (110 px, engine) cover the HUD for the breath. This is intended: the frame goes dark. |
| 7.5 | 450 | 5.1.1 | Chapter "05 / ENERGY" (changes as the bars snap out). |
| 9.375 | 563 | 6.1.1 | Chapter "06 / RANGE" (holds through the montage and the squeeze). |
| 13.125 → 13.359375 | 788 | 8.1.1 | TL, TR and BL texts wipe out left→right through a mask (whip). Crop marks, timecode and beat meter stay to the last frame. The BL slot is free for the s08 monogram. |
| 14.53125 → 15.0 | 872 | 8.4.1 | THE FULL BAR: the beat meter stops advancing and all four squares stay filled Signal to the end. |

**On-screen text:** "CLAUDE — MOTION DESIGNER" · "SHOWREEL 2026" · "01 / WEIGHT … 06 / RANGE" · "TC 00:00:SS:FF"

**Handoff in:** Present from frame 0. Crop marks mid-draw; all labels set.

> **Handoff out:** Final frame 899: crop marks (Paper), BR timecode "TC 00:00:14:59" and the beat meter with all four squares Signal. No TL/TR/BL text.

**Overlap ownership:** Spans the whole film on top of every scene. The montage captions (s06/s07, x=72, baseline 976) sit directly above the BL chapter line and are drawn by those scenes.

**Sound:** No sound of its own. The lit square must coincide with every kick: it is the visual metronome that proves picture and sound lock.

**Build notes and risks:** Colour switches must happen on exact frames (use the schedule; no fades). Keep text crisp: no transforms except the odometer and wipe masks. Grid collisions: scenes keep critical content inside the safe area.

<a id="s01-axis"></a>
## s01-axis: Axis — LIGHT / HEAVY / NARROW / WIDE

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 0.0 → 1.875 s | 0–112 | 1.1.1 → 1.4.4 | 4 beats | 10 | Ink |

**Showcases:** variable-font weight AND width animation on the beat · self-describing kinetic typography · per-letter mask reveals and slot swaps · squash & stretch on type (volume preserved) · blueprint construction lines · birth of the protagonist

**Layout and fixed geometry**

- Words: Archivo, Paper, one font-size FS1 for the whole scene, solved at setup so WIDE (wght 900, font-stretch 125%) has an ink width of exactly 1422 px (reference FS1 ≈ 422 px; flat cap 290 px). Baseline y=700; each word centred on x=960 by its INK box.
- Reference ink widths at FS1: LIGHT (100/100%) ≈ 1166, HEAVY (900/100%) ≈ 1576, NARROW (900/62%) ≈ 1395, WIDE (900/125%) = 1422 → WIDE ink box x 249→1671.
- Each letter lives in its own overflow-hidden slot whose bottom edge is baseline + 8 px, so letters can rise from and fall through the baseline. Precompute per-letter advances at setup for each word at 5 samples along each axis tween and interpolate (no layout reads in update).
- Construction lines: Volt 1 px, full width, at the baseline (y=700) and at the live cap line y = 700 − 290·scaleY.
- Axis readout: JetBrains Mono 500 16 px, Volt-light #718EF8, left x=96, baseline 16 px above the live cap line: "wght 100   wdth 100"; changed digits roll (odometer, 0.117 s).

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 0.0 → 0.234375 | 0 | 1.1.1 | Frame 0 is mid-motion. "LIGHT" at wght 100, font-stretch 100%. Letters rise out of the baseline mask (translateY 110%→0, swift, 0.28 s, 1-frame stagger L→R); the tween clock of the first letter starts at t = −0.06, so frame 0 catches the stagger mid-wave (L 78%, I 66%, G 48%, H 21%, T just starting). Construction lines shoot outward from x=960 to both edges (outCubic, 0→0.234). Readout types on 0.03→0.15. |
| 0.234375 → 0.46875 | 15 | 1.1.3 | LIGHT breathes: letter-spacing −0.01em → +0.02em (inOutSine), so nothing is ever static. |
| 0.46875 → 0.69 | 29 | 1.2.1 | THE HOOK SLAM (beat 2): wght 100→900 over 0.117 s (outExpo) on the LIGHT glyphs; at 0.52734375 each slot swaps glyph (old exits up 0→−110%, new enters from below 110%→0, 0.1 s, 1-frame stagger L→R) → "HEAVY". A local TIGHT scale spring 1.0→1.06→1.0 on top of the global zoom punch. Readout rolls to "wght 900". |
| 0.9375 → 1.2 | 57 | 1.3.1 | NARROW (beat 3): font-stretch 100%→62% over 0.117 s (outExpo) with volume-preserving stretch: scaleY 1.0→1.14 on a POP spring (peaks ≈1.18, settles 1.14 by 1.2). Slots re-flow 5→6: old letters collapse to zero slot width while new letters slide in horizontally through their masks, staggered from the centre outward (1 frame). The cap construction line rides up to y≈369. Readout "wdth 62". |
| 1.40625 → 1.640625 | 85 | 1.4.1 | WIDE (beat 4): font-stretch 62%→125% over 0.117 s (outExpo) with squash: scaleY 1.14→0.92 then springs to 1.0 (overshoot 1.03, settled by 1.64). Slots 6→4. WIDE at rest: ink box x 249→1671, y 410→700. Readout "wdth 125". |
| 1.640625 → 1.7578125 | 99 | 1.4.3 | THE DOT IS BORN (and-of-4): Signal disc Ø88 centred (1731,656), its bottom on the baseline and its left edge 16 px right of WIDE's ink: a hanging full stop, "WIDE.". Scale 0→1.3→1.0 (outBack, 0.117 s). Absolute position; it does not depend on font measurement. |
| 1.7578125 → 1.8528 | 106 | 1.4.4 | Exit (last 16th): WIDE's letters drop through the baseline mask (0→110%, inCubic, 0.07 s each, stagger 1/120 s right→left starting at E; all gone by 1.853). Construction lines retract toward (1731,656) (inCubic, done 1.8411). Readout wipes out. |
| 1.8417 → 1.875 | 111 | 1.4.4 | REST POSE: Ink, only the dot. |

**On-screen text:** "LIGHT" · "HEAVY" · "NARROW" · "WIDE" · "." · "wght 100 → wght 900" · "wdth 100 → wdth 62 → wdth 125"

**Handoff in:** Film start. Ink. Nothing inherited.

> **Handoff out:** @1.875 (rest from 1.8417): Ink #0B0B0F; exactly one element, a flat Signal disc Ø88 centred (1731,656), scale 1, no squash, no rotation. No lines, no text.

**Overlap ownership:** None. Hard handoff on a shared still frame (the lone dot).

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(0.0, 'shake', {amt: 4, dur: 0.15});  // cold-open impact
R.cue(0.0, 'zoom', {amt: 0.03, dur: 0.2});  // cold-open punch: frame 0 lands 3% zoomed
R.cue(0.46875, 'shake', {amt: 10, dur: 0.2});  // HEAVY slam
R.cue(0.46875, 'zoom', {amt: 0.06, dur: 0.234375});  // HEAVY slam: THE HOOK
R.cue(0.9375, 'zoom', {amt: 0.025, dur: 0.15});  // NARROW squeeze
R.cue(1.40625, 'chroma', {amt: 4, dur: 0.12});  // WIDE chroma kiss
R.cue(1.40625, 'zoom', {amt: 0.035, dur: 0.18});  // WIDE
```

**Sound:** Bar 1 is a cold open: hits only, no groove. 0.000 impact (kick + sub F1 + 20 ms noise transient) under a very quiet high-passed bed of glassy 16th plucks (F5 Ab5 C6 F6) for LIGHT. 0.46875 the SLAM: kick + clap + distorted sub + low tom + short room. 0.9375 a 'squeeze' stab (band-passed saw chord bending down 5 semitones over 0.1 s). 1.40625 a wide 7-voice detuned supersaw Fm stab with a reverse-cymbal tail. 1.640625 the dot's 'bloop' (sine 400→1200 Hz, 60 ms). 1.7578 a short falling whoosh.

```js
R.sfx(0.0, 'impact', {amt: 0.8, tone: "sub"});  // cold open
R.sfx(0.0, 'shimmer', {dur: 0.46875, amt: 0.3});  // glassy LIGHT bed
R.sfx(0.46875, 'impact', {amt: 1.0});  // HEAVY slam
R.sfx(0.9375, 'swish', {amt: 0.5});  // NARROW squeeze
R.sfx(1.40625, 'impact', {amt: 0.55});  // WIDE stab
R.sfx(1.640625, 'pop', {pitch: 2.0});  // the dot is born
R.sfx(1.7578125, 'whoosh', {dur: 0.1171875, dir: "down"});  // letters drop
```

**Build notes and risks:** font-stretch changes glyph advances every frame: position slots from precomputed advances, never from per-frame layout reads. Slot counts change 5→6→4 (zero-width collapse). Keep font-stretch within 62–125% and express overshoot with scaleX/scaleY only. Wait for document.fonts before measuring FS1.

<a id="s02-timing"></a>
## s02-timing: Timing — the dot learns to move

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 1.875 → 3.75 s | 113–224 | 2.1.1 → 2.4.4 | 4 beats | 20 | Ink |

**Showcases:** character animation with the 12 principles (anticipation, squash & stretch, arcs, slow in/out, follow-through, timing) · decaying bounce rhythm mapped to the grid (3 16ths → 8th → 8th → 16th) · animator notation: onion skins, motion-path arcs, spacing ticks, principle labels · editorial serif kinetic type stamped into existence by impacts; type that takes the hit · exponential dive into the dot

**Layout and fixed geometry**

- Ground line: Fog 1.5 px @40% at y=780, drawing outward from x=1731 to both edges 1.875→2.109 (swift).
- Sentence "Timing is everything" (the dot is its period): Instrument Serif italic 200 px, Paper, baseline 780, placed so its ink starts at x=200. Reference ink boxes (measure at setup): Timing 200→741 (centre 470), is 765→882 (centre 823), everything 917→1699 (centre 1308). Words are invisible until stamped: each letter scales from scaleY 0 anchored at the baseline (no mask, so descenders are safe).
- Dot: Signal Ø88 (r 44). Grounded pose = bottom on y=780 (centre y 736).
- Hops are analytic: x linear in time, y(τ) = y0 + (y1−y0)·τ − 4h·τ(1−τ), τ ∈ [0,1] over the hop window. Stretch 1.25 along / 0.8 across the velocity in flight; squash anchored at the contact point on landing.
- Notation: JetBrains Mono 500 14 px uppercase Volt-light #718EF8 labels with 1 px Volt leader lines. Onion skins: Fog 1.5 px outline circles Ø88 at the analytic positions for t − 2k/60 (k = 1..6), opacity 0.45→0.08. Motion path: Volt 2 px dashed (8 on / 10 off) parabola, drawn 0.06 s ahead of the dot.

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 1.875 → 1.9921875 | 113 | 2.1.1 | ANTICIPATION (one 16th): the dot squashes to scaleX 1.3 / scaleY 0.77 anchored at its bottom (y=700, WIDE's old baseline, an invisible floor) and leans left (skewX 8°). Label "ANTICIPATION" right-aligned at (1700, baseline 596), leader to the top of the dot. |
| 1.9921875 → 2.34375 | 120 | 2.1.2 | LEAP (three 16ths): arc from (1731,656) to (470,736), y0 656, y1 736, h = 445.1 (apex y≈250 near τ 0.48). Stretched along velocity; onion skins and the dashed path show the arc. Label "ARCS" centred at (1110, baseline 222). |
| 2.34375 → 2.578125 | 141 | 2.2.1 | LAND 1 on the snare, on "Timing": 2-frame squash 1.5 × 0.667 at the contact point; Paper 1.5 px impact ring r 44→140 fading over 0.2 s. "Timing" erupts: per-letter scaleY 0→1.12→1 from the baseline (POP), 1-frame stagger outward from the impact x. The word takes the hit: whole-word scaleY 0.94 at impact, recovering on TIGHT. Label "SQUASH & STRETCH" centred at (470, baseline 560). Rebound hop to "is": (470,736)→(823,736), h = 266 (apex 470). |
| 2.578125 → 2.8125 | 155 | 2.2.3 | LAND 2 on "is": squash 1.4 × 0.71; "is" erupts. Label "SLOW IN / SLOW OUT" centred at (646, baseline 412) above a Volt spacing chart: small ticks along the hop arc at the dot's positions every 2 frames, bunched at the apex. Hop to "everything": (823,736)→(1308,736), h = 216 (apex 520). |
| 2.8125 → 2.9296875 | 169 | 2.3.1 | LAND 3 on beat 3: "everything" erupts as a ripple both ways from the impact (1 frame per letter). 16th hop to the full-stop position (1759,736) (ink right edge of "everything" + 60), h = 96 (apex 640). |
| 2.9296875 → 3.046875 | 176 | 2.3.2 | THE FULL STOP LANDS (2.9297): squash 1.3 × 0.77, then a micro-hop in place, h = 36 (apex 700), landing 3.0469. Labels ANTICIPATION, ARCS, SQUASH & STRETCH and SLOW IN / SLOW OUT fade out 2.9297→3.0469; "FOLLOW-THROUGH" appears centred at (1759, baseline 640). |
| 3.046875 → 3.1640625 | 183 | 2.3.3 | Settle wobble on WOBBLE: scale 1.06 × 0.95 decaying to 1. Onion skins and paths gone by 3.1. "FOLLOW-THROUGH" fades 3.164→3.281. The sentence reads "Timing is everything." cleanly from ≈2.95 to 3.52 (≥0.56 s). |
| 3.28125 → 3.3984375 | 197 | 2.4.1 | Beat 4: the dot NOTICES THE CAMERA. Anticipation toward the viewer: uniform scale 1→0.85 (inOutSine, 0.117 s), held; a single Paper 1 px outline pulse r 44→70 fading. |
| 3.515625 → 3.7167 | 211 | 2.4.3 | THE DIVE: the dot flies at the camera. u = t − 3.515625; radius R(u) = 37.4·e^(18u); centre = lerp((1759,736), (960,540), inOutCubic(min(1, u/0.1875))). The sentence layer scales 1→2.2 about the dot (inExpo) and blurs 0→6 px (CSS blur on this small layer only). Reference radii: frame 219 R 420, frame 221 R 765, frame 222 R 1033, frame 223 R 1395 (the frame is covered; the corner distance is 1101.5). |
| 3.7167 → 3.75 | 224 | 2.4.4 | REST POSE (frames 223–224): 2D override, the whole frame flat Signal #FF4A1C. Nothing else. |

**On-screen text:** "Timing is everything." · "ANTICIPATION" · "ARCS" · "SQUASH & STRETCH" · "SLOW IN / SLOW OUT" · "FOLLOW-THROUGH"

**Handoff in:** Identical to s01 out: Ink, Signal disc Ø88 at (1731,656), at rest.

> **Handoff out:** @3.75 (rest from 3.7167): 100% flat Signal #FF4A1C, full frame. Nothing else.

**Overlap ownership:** None. s03 opens on the identical solid-Signal frame.

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(2.34375, 'shake', {amt: 4, dur: 0.12});  // dot lands on "Timing"
R.cue(2.8125, 'shake', {amt: 5, dur: 0.14});  // dot lands on "everything"
R.cue(3.515625, 'vignette', {amt: 0.45, dur: 0.234375, in: 0.2, out: 0.02});  // OPTIONAL engine extension: tunnel vision during the dive
```

**Sound:** The groove starts at 1.875: four-on-the-floor kick, off-8th closed hats, sub bass in 8ths (F1 F1 Ab1 C2), clap on 2.34375 and 3.28125 (the first landing IS the clap). Character foley: an anticipation 'stretch' (sine bending up an octave over 0.12 s) at 1.875; a leap whoosh panned right→left from 1.99; woody marimba plucks with a soft thud per landing climbing the F-minor triad (F4 2.34375, Ab4 2.578125, C5 2.8125, F5 2.9297 for the full stop); tiny ticks for the micro-hop; a soft 'blink' click at 3.28125; a reverse swell sucked into the bar-3 downbeat.

```js
R.sfx(1.875, 'blip', {pitch: 0.5});  // anticipation stretch
R.sfx(1.9921875, 'whoosh', {dur: 0.3515625, dir: "up"});  // leap (lands 2.34375)
R.sfx(2.34375, 'pop', {pitch: 1.0});  // land 1, F4
R.sfx(2.578125, 'pop', {pitch: 1.189});  // land 2, Ab4
R.sfx(2.8125, 'pop', {pitch: 1.498});  // land 3, C5
R.sfx(2.9296875, 'pop', {pitch: 2.0});  // full stop, F5
R.sfx(3.046875, 'tick', {pitch: 2.0});  // micro-hop
R.sfx(3.28125, 'click', {pitch: 1.2});  // notices the camera
R.sfx(3.515625, 'reverse', {dur: 0.234375});  // dive, lands 3.75
```

**Build notes and risks:** Arcs and onion skins are the same analytic path sampled at earlier times, never stored history. Italic overhang makes word boxes lie: measure ink bounds for landing targets at setup. The dive must use the 2D override from frame 223 so no disc edge can survive into s03.

<a id="s03-space"></a>
## s03-space: Space — the corridor

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 3.75 → 5.15625 s | 225–309 | 3.1.1 → 3.3.4 | 3 beats | 30 | Ink |

**Showcases:** CSS 3D architecture (perspective, preserve-3d) built from type · hinge/unfold transition from a flat colour field into depth · camera dolly and rush; rotational springs with overshoot on the beat · variable axes snapping inside 3D space · depth rings as a Swiss grid in perspective

**Layout and fixed geometry**

- Scene root: perspective 1000px, perspective-origin 960px 540px. A "world" div (preserve-3d, transform-origin 960px 540px 0) with transform translateZ(D) rotateZ(roll).
- Corridor cross-section: a square 1920×1920 centred on (960,540): x 0→1920, y −420→1500; depth z 0 (near) → −4200 (far).
- Build ONE wall (the floor, the plane y=1500, 1920 wide × 4200 deep) and clone it three times, rotated about the corridor axis by 90°, 180° and 270°. This gives exact 4-fold symmetry, so every 90° roll lands on an identical corridor.
- Each wall is 12 slabs of 350 px depth (hide a slab while its near edge z > 900 after the dolly; overlap slab seams by 2 px).
- Wall surface: Signal, plus an Ink shading overlay graded along depth from 0% (near) to 70% (far, reads Signal-deep #541E13) whose opacity equals the unfold progress.
- Depth rings: an Ink 4 px line across each wall at every slab boundary (11 per wall, forming concentric squares); labels "03.1"…"03.12" in JetBrains Mono 500 20 px Ink, 40 px in from each boundary's left end.
- Wall type: "SPACE" in Archivo 440 px, Ink, two instances per wall starting at depths 150 and 2250, baseline parallel to the depth axis, reading near→far. Glyph tops point to screen-left on the floor (the clones carry the orientation round). Reference lengths: ≈1894 px at 900/125%, ≈1797 px at 100/125%, ≈1053 px at 900/62%.
- Far wall: a Paper square 1920×1920 at z = −4200 with a Signal disc of world Ø56 at its centre (on screen Ø10.8 at scale 0.192 before the dolly).

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 3.75 | 225 | 3.1.1 | First frame: all four walls are folded flat into the screen plane (fold angle 0°), covering the frame in uniform Signal. Shading overlay, text and rings are at opacity 0. The frame is identical to s02's last frame. |
| 3.75 → 4.21875 | 225 | 3.1.1 | UNFOLD: each wall hinges on its near edge (floor about y=1500, ceiling y=−420, left x=0, right x=1920). Fold angle θ = 90°·spring(t − 3.75, HINGE), overshooting to ≈98° near 3.97 and settling by ≈4.17: a box unfolding into a corridor. Shading opacity = min(1, θ/90°). Text and rings fade 0→1 between 3.8671875 and 3.984375 (hides z-fighting while the walls are near-coplanar). The far Paper square and its dot show through the opening flaps from the first frames. |
| 4.21875 → 4.6875 | 254 | 3.2.1 | ROLL 1 on the snare: roll 0→90° (ROLL spring, ≈9% overshoot, settled ≈4.55). On the same frame every wall word snaps to wght 100 (hairline): a hard switch, no tween. DOLLY: D 0→1200 (glide) over 4.21875→4.6875. |
| 4.6875 → 5.1229 | 282 | 3.3.1 | ROLL 2 on beat 3: roll 90→180° (ROLL spring). Words snap to wght 900 + font-stretch 62%. RUSH: D 1200→4200 over 4.6875→5.1229 (whip / inExpo), bringing the far wall to scale 1. RING CHASE on every 16th (4.6875, 4.8046875, 4.921875, 5.0390625): a Paper pulse runs along the depth rings from the far wall toward the camera, one ring per frame, each ring Paper for 2 frames. |
| 5.1229 → 5.15625 | 308 | 3.3.4 | REST POSE (frames 308–309): 2D override that hides the 3D world and draws full-frame Paper + Signal disc Ø56 at (960,540). This is exact and independent of any 3D rounding or residual roll. |

**On-screen text:** "SPACE (×8, two per wall, in perspective)" · "03.1 … 03.12"

**Handoff in:** @3.75: 100% flat Signal (s02 rest pose). Walls coplanar and flat on frame 225.

> **Handoff out:** @5.15625 (rest from 5.1229): full-frame Paper #F3F0EA; one flat Signal disc Ø56 centred (960,540). Nothing else.

**Overlap ownership:** None. Ends on beat 4 of bar 3 (a snare): the cut into the graph editor is an accent.

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(3.75, 'chroma', {amt: 8, dur: 0.2});  // through the dot into the corridor
R.cue(3.75, 'zoom', {amt: 0.04, dur: 0.2});  // box unfold starts
R.cue(4.21875, 'chroma', {amt: 3, dur: 0.1});  // roll 1
R.cue(4.6875, 'chroma', {amt: 4, dur: 0.1});  // roll 2 + rush
R.cue(4.921875, 'chroma', {amt: 5, dur: 0.1171875, curve: 0});  // rush ramp step 1 (curve 0 = held)
R.cue(4.921875, 'vignette', {amt: 0.5, dur: 0.2008, in: 0.15, out: 0.02});  // OPTIONAL engine extension: rush tunnel vision
R.cue(5.0390625, 'chroma', {amt: 9, dur: 0.0838, curve: 0});  // rush ramp step 2, hard off at 5.1229 so the rest frames are clean
```

**Sound:** 3.75 sub boom + a low 'door' whoosh (filtered noise sweeping down) as the box unfolds. The pad enters on Abmaj7 and moves to Eb at 4.6875; a 16th F-minor-pentatonic arp opens its filter across the bar. Roll 'clunks' (low tom + metallic click) on 4.21875 and 4.6875. Ring-chase ticks on 16ths from 4.6875, climbing. 4.6875→5.15625: an accelerating whoosh with a pitch riser, cut clean on 5.15625.

```js
R.sfx(3.75, 'impact', {amt: 0.7, tone: "sub"});  // box unfolds
R.sfx(3.75, 'whoosh', {dur: 0.3515625, dir: "down"});  // door
R.sfx(4.21875, 'swish', {amt: 0.5});  // roll 1
R.sfx(4.21875, 'click', {pitch: 0.5});  // roll 1 clunk
R.sfx(4.6875, 'swish', {amt: 0.6});  // roll 2
R.sfx(4.6875, 'click', {pitch: 0.5});  // roll 2 clunk
R.sfx(4.6875, 'tick', {pitch: 1.0});  // ring chase
R.sfx(4.8046875, 'tick', {pitch: 1.12});  // ring chase
R.sfx(4.921875, 'tick', {pitch: 1.26});  // ring chase
R.sfx(5.0390625, 'tick', {pitch: 1.5});  // ring chase
R.sfx(4.6875, 'whoosh', {dur: 0.46875, dir: "up"});  // rush, lands 5.15625
```

**Build notes and risks:** preserve-3d with 4200-deep planes: slab culling near the camera, 2 px seam overlaps, and tiny distinct z offsets while coplanar. Never put a filter on the world or on a wall (filters flatten preserve-3d); blur leaf text layers only, if at all. Springs are closed-form. The 2D rest override makes the handoff exact. Fallback if Chromium clips badly: shorten the corridor to 3000 deep and rush to D = 3000.

<a id="s04-easing"></a>
## s04-easing: Easing — the graph editor

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 5.15625 → 7.03125 s | 310–421 | 3.4.1 → 4.3.4 | 4 beats | 40 | Paper |

**Showcases:** UI/product micro-interactions (cursor travel, hover, press, drag, ripple, odometer, type-on) · motion tooling as subject: a live cubic-bezier editor whose overshoot leaves its box · easing literacy: spacing chart with ghosts and a real overshoot · variable-font width driven by an eased value · line draw-on / un-draw

**Layout and fixed geometry**

- Paper background. Swiss 12-column hairlines (Fog 1 px at every column edge; margins 96, gutters 16) at 20% from 5.15625 to 5.2734375, then 8%.
- LEFT, graph editor: plot square x 240→720, y 340→820 (480×480), origin (240,820); normalized (u,v) → px (240 + 480u, 820 − 480v). Axes Ink 2 px; inner 8×8 grid Fog 1 px @30%; labels JetBrains Mono 500 14 px Fog: "TIME" right-aligned at (720, baseline 848), "VALUE" rotated −90° centred at (212,580), "0" at (228,848), "1" at (716,848) and at (220,346).
- Curve: Ink 5 px, round caps, P0 (240,820) → P3 (720,340). Handles: Volt 2 px lines P0→P1 and P3→P2; P1 and P2 are Signal 18×18 squares; P0 and P3 are Ink Ø12 discs. Initial curve cubic-bezier(0.70, 0.00, 0.20, 1.00): P1 = (576,820), P2 = (336,340).
- Header: JetBrains Mono 500 26 px Ink, left x=240, baseline 900: "cubic-bezier(0.70, 0.00, 0.20, 1.00)".
- RIGHT, preview: track Ink 2 px from (1040,400) to (1680,400), Ink 12 px end ticks, Fog 8 px ticks at every 1/8 (x = 1040 + 80k); Fog 14 px mono "0" and "1" centred under the ends (baseline 432).
- "EASE": Archivo wght 800, 200 px, Ink, ink-left x=1040, baseline 700. font-stretch = (62 + 63·clamp(v,0,1))%; for v > 1 add scaleX = 1 + 0.5·(v − 1) (origin left). Reference ink width 360 px at 62% and 678 px at 125%.
- Readout: JetBrains Mono 500 26 px Ink, left x=1040, baseline 770: "v 0.00" (tabular, 2 decimals).
- Dot: Signal Ø56. Cursor: classic arrow 34 px tall, Ink fill, 2 px Paper outline, hotspot at the tip.

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 5.15625 | 310 | 3.4.1 | First frame: Paper and the dot at (960,540) (s03 rest pose). Arrival flash cue 0.35. |
| 5.15625 → 5.390625 | 310 | 3.4.1 | The dot hops from (960,540) to the track start (1040,400) on a short arc (outBack) and lands with a 2-frame squash (1.25 × 0.8) on the line. Axes draw from the origin outward (swift); plot grid fades in; the track and ticks draw left→right from ≈5.2 (swift). |
| 5.2 → 5.5167 | 312 | 3.4.1 | Header types on at 2 chars/frame (37 chars) behind a 2 px Ink caret. |
| 5.2734375 → 5.44921875 | 317 | 3.4.2 | "EASE" rises out of a baseline mask at font-stretch 62% (swift); "v 0.00" types on. |
| 5.2734375 → 5.5078125 | 317 | 3.4.2 | Cursor enters from (1500,1140) on a quadratic curve (control (1180,420)) to P2 at (336,340) (glide). |
| 5.5078125 → 5.625 | 331 | 3.4.4 | HOVER: the P2 square scales 1→1.2 (swift), the anticipation of the press. |
| 5.625 → 5.859375 | 338 | 4.1.1 | PRESS on the bar-4 downbeat: cursor scale 0.9 for 3 frames; P2 1.2→0.9→1.0 (POP); a Signal 1.5 px ripple ring from P2 (r 9→48, fading 0.2 s). DRAG (inOutCubic): P2 (336,340) → (336,100), i.e. y1 1.00 → 1.50, dragged OUT of the plot box (no clipping). The curve redraws live and its top bulges above the box. The header's last number rolls odometer-style "1.00" → "1.50" (per-digit roll, 2-frame stagger). |
| 5.859375 → 6.09375 | 352 | 4.1.3 | RELEASE: cursor pop 1.05 for 2 frames, then it glides to (760,1000) and fades out 6.09→6.21. The header now reads "cubic-bezier(0.70, 0.00, 0.20, 1.50)". |
| 6.09375 → 6.5625 | 366 | 4.2.1 | PLAY on the snare, exactly one beat. x = (t − 6.09375)/0.46875; v = cubicBezier(0.70, 0, 0.20, 1.50)(x), solved like R.cubicBezier. Dot x = 1040 + 640·v (y 400). A Signal 2 px playhead sweeps the plot at X = 240 + 480x with a Signal Ø10 dot riding the curve. SPACING CHART: every 3 frames a Fog 1.5 px outline circle Ø56 is stamped at the dot's position and stays (reference x 1040, 1049, 1082, 1162, 1365, 1646, 1731, 1745, 1728, 1695): bunched at the start, flung through the middle, ghosts beyond the end. "EASE" stretches lock-step with v. The readout counts with v and flashes "v 1.10" in Signal for 3 frames at the peak (6.4357, v 1.102, dot x 1745). Track ticks pop (scale 1→1.6→1 over 4 frames) as the dot passes them: 6.2230, 6.2577, 6.2784, 6.2929, 6.3048, 6.3166, 6.3316 and the end tick at 6.3566. |
| 6.5625 → 6.796875 | 394 | 4.3.1 | HOLD on beat 3: the dot sits exactly at 1680 (v = 1). "EASE" is at full width and legible, the readout says "v 1.00", and the spacing chart is complete. |
| 6.796875 → 6.9979 | 408 | 4.3.3 | RETRACT: everything un-draws (reverse dash offset, inCubic). The curve and handles retract into P0, the axes into the origin and the track right→left. The header deletes right→left at 3 chars/frame, "EASE" wipes down through its mask (whip), the readout clears and the hairlines fade to 0. The ghosts slide into the dot like beads pulled on a string (inCubic, 1-frame stagger). The dot arcs from (1680,400) back to (960,540) (snap) and arrives at 6.9979. |
| 6.9979 → 7.03125 | 420 | 4.3.4 | REST POSE (frames 420–421): Paper and the dot Ø56 at (960,540). |

**On-screen text:** "cubic-bezier(0.70, 0.00, 0.20, 1.00) → cubic-bezier(0.70, 0.00, 0.20, 1.50)" · "EASE" · "TIME" · "VALUE" · "0" · "1" · "v 0.00 → v 1.00 (peak v 1.10)"

**Handoff in:** @5.15625: full-frame Paper, Signal disc Ø56 at (960,540) (s03 rest pose).

> **Handoff out:** @7.03125 (rest from 6.9979): full-frame Paper; one flat Signal disc Ø56 centred (960,540). Nothing else. s05 cuts the ground to Ink on frame 422 while the dot stays identical (a lights-out match cut).

**Overlap ownership:** None.

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(5.15625, 'flash', {amt: 0.35, dur: 0.1, color: "#FFFFFF"});  // arrival into the Paper UI
R.cue(5.625, 'shake', {amt: 2, dur: 0.08});  // cursor press
```

**Sound:** The drums thin to kick + rim on 2 and 4 + soft hats (UI lightness). 5.15625 a soft bloom chime; key ticks for the header; a faint air whoosh for the cursor; 5.625 the press is a crisp click plus a high 'tink' (on the kick); the drag is a sine glide rising a fifth; 5.859 a release pop; 6.09375 a pitched 'swoop' whose pitch follows v, including the overshoot bend; hat-like ticks as the dot passes the track ticks; from 6.5625 a snare roll (8ths, then 16ths from 6.797) with noise and saw risers; 6.797 a reverse zip for the retract. The tape-stop on 7.03125 belongs to s05.

```js
R.sfx(5.15625, 'blip', {pitch: 2.0});  // arrival bloom
R.sfx(5.2, 'type', {count: 19, dur: 0.3167});  // header typing
R.sfx(5.625, 'click', {pitch: 1.0});  // press
R.sfx(5.625, 'tick', {pitch: 3.0});  // tink
R.sfx(5.625, 'swish', {amt: 0.25});  // drag glide
R.sfx(5.859375, 'pop', {pitch: 1.5});  // release
R.sfx(6.09375, 'whoosh', {dur: 0.46875, dir: "up"});  // play swoop
R.sfx(6.223, 'tick', {pitch: 1.0});  // tick 1/8
R.sfx(6.2577, 'tick', {pitch: 1.06});  // tick 2/8
R.sfx(6.2784, 'tick', {pitch: 1.12});  // tick 3/8
R.sfx(6.2929, 'tick', {pitch: 1.19});  // tick 4/8
R.sfx(6.3048, 'tick', {pitch: 1.26});  // tick 5/8
R.sfx(6.3166, 'tick', {pitch: 1.33});  // tick 6/8
R.sfx(6.3316, 'tick', {pitch: 1.41});  // tick 7/8
R.sfx(6.3566, 'tick', {pitch: 1.5});  // end tick
R.sfx(6.5625, 'riser', {dur: 0.46875});  // build into the tape-stop
R.sfx(6.796875, 'reverse', {dur: 0.1875});  // retract zip
```

**Build notes and risks:** Solve the bezier exactly like R.cubicBezier (Newton + bisection) so the preview matches the plotted curve. The curve bulge above y=340 must not be clipped. Ghosts and tick times are analytic (positions at play start + 3k/60). The cursor path is a pure function of t.

<a id="s05-energy"></a>
## s05-energy: Energy — breath, drop, chaos into RANGE

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 7.03125 → 9.375 s | 422–562 | 4.4.1 → 5.4.4 | 5 beats | 50 | Ink |

**Showcases:** macro anticipation: a one-beat held breath before the drop · generative particle system (12k Canvas 2D particles, curl noise, vortices, streaks) · shockwave · emergent typography: chaos snapping into a Swiss dot-matrix · whip-pan exit on a shared camera function

**Layout and fixed geometry**

- One full-frame canvas on Ink. Letterbox (110 px) comes from the engine cue; never draw bars.
- Particles: 12,000; colours 64% Signal (source-over), 22% Paper and 11% Volt (both "lighter", capped alpha 0.8), 3% Acid. Drawn as velocity-aligned streaks, length |v|/60 × 1.5 (min 1.5 px), width 1.5–3 px, batched into one path per colour.
- Simulation: R.sim with dt 1/120 from 7.5, deterministic seeds. Radial launch 700–2800 px/s (exponential distribution) plus 12% tangential swirl; drag 2.2/s; curl-noise advection from R.noise3 (scale 0.0022, time 0.35, strength 380 px/s); two counter-rotating vortex fields centred (640,540) and (1280,540), tangential 520 px/s × exp(−d/420).
- RANGE targets: R.textPoints("RANGE", {weight 900, stretch "expanded", size ≈326, x 960, y 540, step 5}), with the size solved so the ink width is 1520 (x 200→1720, cap ≈224), giving ≈7,000 targets. Assign particles to targets by sorting both by angle around (960,540), so the paths swirl coherently.
- Shared whip function (also used by s06): u = (t − 9.140625)/0.234375, P(t) = 1920·inOutCubic(u). s05 content x-offset = −P(t).

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 7.03125 | 422 | 4.4.1 | LIGHTS OUT (hard cut, beat 4): Ink, the dot Ø56 at (960,540) identical to s04's last frame. Letterbox snaps in (engine). |
| 7.03125 → 7.5 | 422 | 4.4.1 | THE BREATH: the dot compresses Ø56→Ø26 (inCubic) with a growing tremble (R.wiggle ≈40 Hz, amplitude 0→3 px). A thin Signal 2 px ring implodes from Ø1400 to Ø26 (inQuart), arriving at 7.44140625 (one 32nd before the drop), trailed by 3 fainter Fog 1 px rings at 1-frame delays (alpha 0.5, 0.35, 0.2). From 7.4414 to 7.5 the dot holds at Ø26, trembling. |
| 7.5 → 7.96875 | 450 | 5.1.1 | THE DROP: the dot detonates into 12,000 particles (all spawned inside the Ø26 disc). A Paper 3 px shockwave ring r 0→1500 (outQuart, 0.35 s, alpha 1→0). The particles bloom outward and curl into the two counter-rotating vortices. |
| 7.96875 → 8.4375 | 479 | 5.2.1 | Beat 2: a second impulse, every particle kicked radially outward from (960,540) by +600 px/s. The frame breathes. |
| 8.4375 → 8.55 | 507 | 5.3.1 | ORDER FROM CHAOS on beat 3: particles spring to their RANGE targets (SOFT spring from each particle's cached state at its start time; start delay 0–0.117 s proportional to distance). On arrival (progress > 0.95) each lerps over 4 frames into a 3×3 px Paper square at its target, so by ≈8.55 the letters read as a crisp dot-matrix. The ≈5,000 spare particles keep orbiting as a low Signal/Volt haze (alpha 0.3) behind. Letter squares jitter ±1 px (R.noise2 per target, 12 Hz). |
| 8.4375 → 9.140625 | 507 | 5.3.1 | "RANGE" holds, legible for 0.70 s. |
| 9.140625 → 9.375 | 549 | 5.4.3 | WHIP (and-of-4): the whole layer translates x = −P(t); streak length grows by \|P'(t)\|/60 × 1.2 (up to ≈200 px) as horizontal motion blur. Fully off-screen at 9.375. s06 enters on top along the same curve. |

**On-screen text:** "RANGE"

**Handoff in:** @7.03125: Ink (cut from Paper); Signal disc Ø56 at (960,540), identical to s04's last frame.

> **Handoff out:** Overlap 9.140625–9.375: s06 (on top) slides in its opaque world panel at x = 1920 − P(t) while s05 keeps drawing its layer at x = −P(t) underneath. At 9.375 s05 is fully covered and stops.

**Overlap ownership:** s06 overlaps 9.140625–9.375 (one 8th) and is ON TOP. s05 renders its full layer offset by −P(t) until 9.375.

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(7.03125, 'grain', {amt: 0.04, dur: 0.46875});  // breath texture
R.cue(7.03125, 'letterbox', {amt: 110, dur: 0.46875, in: 0.1, out: 0.05});  // bars snap in on lights-out, out on the drop (fully gone at 7.5)
R.cue(7.03125, 'vignette', {amt: 0.6, dur: 0.46875, in: 0.1, out: 0.03});  // OPTIONAL engine extension: breath darkness
R.cue(7.5, 'chroma', {amt: 12, dur: 0.3});  // drop
R.cue(7.5, 'flash', {amt: 1.0, dur: 0.1, color: "#FFFFFF"});  // THE DROP (white)
R.cue(7.5, 'shake', {amt: 18, dur: 0.45});  // drop
R.cue(7.5, 'zoom', {amt: 0.08, dur: 0.3});  // drop
R.cue(7.96875, 'shake', {amt: 5, dur: 0.15});  // second particle impulse
R.cue(7.96875, 'zoom', {amt: 0.03, dur: 0.15});  // second particle impulse
R.cue(8.4375, 'flash', {amt: 0.3, dur: 0.08, color: "#FF4A1C"});  // Signal flash: particles snap into RANGE
R.cue(8.4375, 'shake', {amt: 6, dur: 0.15});  // RANGE snap
R.cue(9.140625, 'chroma', {amt: 14, dur: 0.234375, angle: 0});  // whip smear, horizontal split
```

**Sound:** 7.03125 TAPE-STOP: the whole mix pitch-dives to zero over 0.18 s, then near-silence; a reverse cymbal plus a reversed impact swell from 7.03 into 7.5, and a sub 'inhale' (30→55 Hz) matched to the ring implosion. 7.5 DROP: a mega impact (kick + long 808 on F1 + noise burst + crash) and a sub drop, then the full groove: four-on-the-floor, clap on 2 and 4, rolling 16th hats with accents, a pumping 8th sub-bass line, supersaw stabs on off-beat 8ths (Fm9 → Dbmaj7), and a granular glitter layer for the particles. 7.96875 a secondary impact. 8.32→8.4375 a reverse zip into a bright stab on the RANGE snap. 9.140625 a whoosh right→left into 9.375.

```js
R.sfx(7.03125, 'tapestop', {dur: 0.18});  // lights out
R.sfx(7.03125, 'reverse', {dur: 0.46875});  // swell into the drop
R.sfx(7.5, 'impact', {amt: 1.2, tone: "huge"});  // THE DROP
R.sfx(7.5, 'subdrop', {amt: 1.0});  // drop
R.sfx(7.5, 'shimmer', {dur: 0.9375, amt: 0.6});  // particle glitter
R.sfx(7.96875, 'impact', {amt: 0.5});  // second impulse
R.sfx(8.3203125, 'reverse', {dur: 0.1171875});  // zip into the snap
R.sfx(8.4375, 'impact', {amt: 0.45});  // RANGE snap
R.sfx(8.4375, 'shimmer', {dur: 0.46875, amt: 0.4});  // snap sparkle
R.sfx(9.140625, 'whoosh', {dur: 0.234375, dir: "down"});  // whip R→L
```

**Build notes and risks:** Seekability: cache the sim from 7.5 (225 steps × 12k particles, typed arrays), re-initialised by R.sim on backward seeks; the snap and whip phases are analytic blends from cached states. "lighter" over Ink blows out quickly, so cap alpha. Target sampling needs the font loaded (fonts are ready before setup). Batch strokes per colour.

<a id="s06-range-1"></a>
## s06-range-1: Range I — C · L · A · U

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 9.140625 → 11.25 s | 549–674 | 5.4.3 → 6.4.4 | 4.5 beats | 60 | none (each vignette draws its own full-frame ground) |

**Showcases:** whip-pan landing on a shared camera function · halftone print texture (the dot multiplied) · Swiss modular grid and a square→circle module morph · liquid/metaball motion with a drip-through follow-through · data-viz animation (bars, half-donut sweep, counters) forming a letter · centre-locked one-beat montage

**Layout and fixed geometry**

- CENTRE-LOCK RULE: on every cut frame (9.375, 9.84375, 10.3125, 10.78125) the protagonist is a flat Signal disc Ø112 at (960,540). It does a 3-frame squash-pop on the cut (1.25 × 0.8 → 1, POP). Inside a vignette it may move, but it always starts at the anchor.
- Each vignette is one huge letter (cap ≈780) whose counter or negative space holds the anchor. Caption: JetBrains Mono 500 20 px uppercase, tracking 0.12em, HUD colour, left x=72, baseline 976 (directly above the HUD chapter line); types on at 3 chars/frame from the cut.
- Reference glyph placements, measured in the pipeline Chromium at font-size 1109 px (re-derive at setup with the same method: largest inscribed circle of the counter): C (900, 100%) origin x 510, baseline 922 → ink x 560→1323, y 146→935, counter r 150; D (900, 100%) origin x 516, baseline 922 → ink x 598→1329, y 159→922, counter r 118; A (wght 600, 100%) origin x 572, baseline 913 → ink x 578→1353, y 152→913, counter incircle Ø178 centred on the anchor.
- Structure the module as four vignette functions draw(localT) plus the whip wrapper; the root has no background, so everything left of the incoming panel is transparent during the overlap.

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 9.140625 → 9.375 | 549 | 5.4.3 | WHIP IN (on top of s05): the C world, fully alive with its ripple running, is drawn inside a wrapper at x = 1920 − P(t) (the same P as s05) with an opaque Paper background over its whole 1920×1080 rect. Halftone dots are smeared horizontally by 1 + \|P'(t)\|/5000 (peak ≈3.5 mid-whip, 1.0 on landing). |
| 9.375 → 9.84375 | 563 | 6.1.1 | C — HALFTONE (Paper): the C (placement above) rendered on canvas as a halftone. Square lattice, pitch 22 px, rotated 15°; each cell's coverage c is sampled once from an offscreen glyph raster. Dot Ø = 21·c·(0.72 + 0.28·sin(2π(d/200 − 4·(t − 9.375)/0.46875))), where d = distance from the anchor, so rings ripple outward from the protagonist 4 times per beat. Dot colour = mix(Ink, Signal, clamp(1 − d/260)): a heat bloom around the source. On the and (9.609375) the ripple amplitude pulses 0.28→0.6→0.28 (TIGHT). Caption "C — HALFTONE". |
| 9.84375 → 10.078125 | 591 | 6.2.1 | L — GRID (Ink): a 13 × 7 module grid, modules 112×112, pitch 128. Column centres x = 960 + 128(c − 7), c = 1..13; row centres y = 540 + 128(r − 4), r = 1..7. Graphite 1 px outlines (Fog for 2 frames on the cut). The L is 20 modules: stem = columns 5–6 × rows 1–6, foot = columns 7–10 × rows 5–6 (ink box x 648→1400, y 100→852). The anchor is module (7,4), nestled in the L's crook. Modules fill Paper along the stroke path (stem top → corner → foot end) at 2 modules/frame, each popping 0.6→1 (swift, 4 frames); complete by ≈10.01. Dimension lines Volt 1 px with 6 px end ticks and Volt-light JetBrains Mono 14 px labels typed at 2 chars/frame: "COL 05–06" (line x 648→888 at y 880, label centred (768, baseline 904)); "GUTTER 16" (bracket x 888→904 at y 880, label left (912, baseline 904)); "MODULE 112 × 112" (vertical line at x 1414, y 612→724, label left (1424, baseline 680)). |
| 10.078125 → 10.3125 | 605 | 6.2.3 | On the and: every L module morphs square → circle (corner radius 0→56, POP). The L becomes a dot-matrix of Paper Ø112 circles; the protagonist is the only Signal one. Caption "L — GRID". |
| 10.3125 → 10.4296875 | 619 | 6.3.1 | A — LIQUID (Volt): the Paper goo layer (SVG feGaussianBlur stdDeviation 14 + feColorMatrix alpha threshold "0 0 0 22 −9", container clipped to the A box + 160 px). CONVERGE (one 16th): 7 Paper blobs (Ø70–220) rush in from beyond the frame edges (bottom-left, bottom-right, left, right, top-left, top-right, bottom) on curved paths (swift) and merge; the A glyph inside the goo group is revealed by a union of circles growing from the blob arrival points (r 0→700, swift). The protagonist floats at the anchor inside the counter as the liquid closes around it. |
| 10.4296875 → 10.546875 | 626 | 6.3.2 | The A settles with liquid overshoot (WOBBLE). Three bumps (Ø40) ride its contour at 900 px/s. The dot sinks from y 540 to 590 (inQuad) onto the crossbar, and the membrane bulges down (a Ø60 goo blob pushed below the crossbar). |
| 10.546875 → 10.78125 | 633 | 6.3.3 | DRIP-THROUGH (and): the goo necks around the dot and snaps back (two crossbar blobs part and rejoin over 3 frames), and the dot falls through between the legs (v0 600 px/s, g 13,000 px/s², stretch 0.8 × 1.25 along velocity), exiting the bottom edge by ≈10.75. Two Paper droplets (Ø18, Ø10) trail it and are reabsorbed. The crossbar heals on WOBBLE. The A reads clean from ≈10.43 to 10.78. Caption "A — LIQUID". |
| 10.78125 → 11.1328125 | 647 | 6.4.1 | U — DATA (Paper): a dashed Fog 2 px axis at y=540 from x 160 to 1760 (dash 12/8), with JetBrains Mono 14 px Fog tick labels every 160 px. Stems are Ink bars 150 wide (x 570→720 and 1200→1350) growing from y 540 to 150 (POP-like spring stiffness 260, damping 18); left starts 10.78125, right starts 10.8984375. Value labels (JetBrains Mono 700 28 px Ink) centred above each bar count 0→100 with its height. Bowl: an Ink half-donut centred (960,540), inner r 240, outer r 390 (stroke 150), sweeping counter-clockwise on screen (9 o'clock → 6 o'clock → 3 o'clock) from the left stem through the bottom (960,930) to the right stem, 10.8984375→11.1328125 (inOutCubic), with a flat start and a round leading cap; Fog 1 px ticks every 10% outside it. Readout JetBrains Mono 700 56 px Ink centred at (960, baseline 340): "0%"→"100%". The protagonist sits at the hub (960,540), the origin of the chart, on the axis. The U ink box is x 570→1350, y 150→930. |
| 11.1328125 → 11.2167 | 668 | 6.4.4 | DATA POINT LOCKED: the sweep completes and the dot pops 1→1.2→1 (key frames 11.1328 → 11.1621 outCubic → 11.2109 inOutSine), settling before the rest frames. Caption "U — DATA". |
| 11.2167 → 11.25 | 674 | 6.4.4 | REST POSE (frames 673–674): the complete U chart on Paper; dot Ø112 at (960,540), scale 1. |

**On-screen text:** "C" · "L" · "A" · "U" · "C — HALFTONE" · "L — GRID" · "A — LIQUID" · "U — DATA" · "COL 05–06" · "GUTTER 16" · "MODULE 112 × 112" · "0 → 100" · "0% → 100%"

**Handoff in:** During 9.140625–9.375 s05 shows Ink particle streaks panning left at −P(t); s06 starts transparent except for its opaque world panel entering from x=1920.

> **Handoff out:** @11.25 (rest from 11.2167): the finished U chart on Paper, with the Signal disc Ø112 at (960,540), scale 1. s07 cuts to the glitched D on Ink with the dot at the SAME place and size (a centre-locked match cut).

**Overlap ownership:** ON TOP of s05 from 9.140625 to 9.375, drawing only its opaque world panel at x = 1920 − P(t) (transparent left of the panel edge). From 9.375 it covers the frame.

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(9.375, 'shake', {amt: 6, dur: 0.15});  // whip lands on C
R.cue(9.375, 'zoom', {amt: 0.04, dur: 0.15});  // whip lands on C
R.cue(9.84375, 'chroma', {amt: 3, dur: 0.1});  // cut to L
R.cue(9.84375, 'shake', {amt: 4, dur: 0.1});  // cut to L
R.cue(10.3125, 'chroma', {amt: 3, dur: 0.1});  // cut to A
R.cue(10.3125, 'shake', {amt: 4, dur: 0.1});  // cut to A
R.cue(10.78125, 'chroma', {amt: 3, dur: 0.1});  // cut to U
R.cue(10.78125, 'shake', {amt: 4, dur: 0.1});  // cut to U
```

**Sound:** The full groove continues (kick, clap on 9.84375 and 10.78125, 16th hats, pumping bass). Each cut layers its own signature on the beat: 9.375 a bitcrushed stab and downsampled hat fizz (halftone); 9.84375 clicky mechanical 16ths for the module fills and a square-wave blip on 10.078 for the square→circle morph (grid); 10.3125 a resonant filter 'bloop' and a bubbly gurgle, with a droplet 'plip' at 10.5469 (liquid); 10.78125 rising data blips on 16ths and a sine glide F4→F5 for the arc sweep (data). A snare fill in 16ths 11.015625→11.25.

```js
R.sfx(9.375, 'glitch', {dur: 0.1});  // halftone fizz
R.sfx(9.609375, 'blip', {pitch: 1.5});  // ripple pulse
R.sfx(9.84375, 'tick', {pitch: 1.0});  // module fill
R.sfx(9.9609375, 'tick', {pitch: 1.0});  // module fill
R.sfx(10.078125, 'blip', {pitch: 0.75});  // square→circle
R.sfx(10.1953125, 'tick', {pitch: 1.0});  // module click
R.sfx(10.3125, 'pop', {pitch: 0.5});  // liquid bloop
R.sfx(10.3125, 'swish', {amt: 0.4});  // blobs rush in
R.sfx(10.546875, 'pop', {pitch: 2.5});  // drip plip
R.sfx(10.78125, 'blip', {pitch: 1.0});  // data
R.sfx(10.8984375, 'blip', {pitch: 1.19});  // data
R.sfx(11.015625, 'blip', {pitch: 1.5});  // data
R.sfx(10.8984375, 'whoosh', {dur: 0.234375, dir: "up"});  // arc sweep
R.sfx(11.1328125, 'pop', {pitch: 2.0});  // data point locked
```

**Build notes and risks:** Four sub-renderers in one module (~600 lines): keep each a draw(ctx, localT) function. Halftone ≈1,500 dots per frame; sample coverage once. The goo filter is the expensive part: keep its container tight. The whip panel must be opaque over its whole rect. The pop must settle before 11.2167 so the dot is exactly Ø112 on the rest frames.

<a id="s07-range-2"></a>
## s07-range-2: Range II — D · E · the specimen row · the squeeze

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 11.25 → 13.125 s | 675–787 | 7.1.1 → 7.4.4 | 4 beats | 70 | Ink |

**Showcases:** glitch/datamosh texture with RGB split · shape-layer animation with overshoot, speed lines and a collision · an accelerating edit (8ths → 16ths) · a type-specimen layout revealing that the techniques spelled the name · anticipation squeeze on a logotype (width 62, tremble, silence)

**Layout and fixed geometry**

- Montage anchor as in s06: the dot is Ø112 at (960,540) on the D and E cut frames.
- SPECIMEN ROW: six cells 240×340 with 24 px gaps. Cell i (0..5) spans x = 142 + 264i → [142,382] [406,646] [670,910] [934,1174] [1198,1438] [1462,1702], y 370→710. Captions: JetBrains Mono 500 16 px Fog uppercase, centred on each cell, baseline 744.
- Mini letters: each cell shows its vignette's treatment at cap ≈200, i.e. the vignette geometry scaled by s = 0.2564 about the letter box centre and centred on the cell (cx, 540). There are no protagonist dots inside the minis. C: Paper cell, Ink halftone at pitch 8 px, slow ripple. L: Ink cell, Graphite micro-grid, 20 Paper circle-modules. A: Volt cell, Paper A (a light goo or rounded joins, 2 wobbling bumps). U: Paper cell, Ink bars and half-donut. D: Ink cell, Paper D with Signal/Volt split ±6 px and 5 slices ±8 px re-rolled every 4 frames. E: Acid cell, Ink rectangle E.
- Plain glyphs for the flatten: Archivo wght 900, font-stretch 100%, 291 px (flat cap 200), Paper, ink-centred in each cell.
- CANONICAL CONDENSED WORD (shared with s08): ONE element with textContent "CLAUDE", font-family Archivo; font-weight 900; font-stretch 62%; font-size 370px; line-height 1 (set after any font shorthand); letter-spacing 0; font-kerning normal; colour Paper; position absolute; left 0; width 1920px; text-align center; top = 670 − 0.833·370 ≈ 361.8 px (baseline y=670; measure the 0.833 ratio at setup with a 0×0 baseline marker). Reference ink box ≈ x 427→1496, flat cap top ≈416.

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 11.25 → 11.484375 | 675 | 7.1.1 | D — GLITCH (Ink): the D (placement in s06) in Paper, with a Signal copy at x −22 and a Volt copy at x +22 beneath it ("screen"). 14 horizontal slices of the D box, each offset by R.hash(slice, floor(frame/2)) mapped to ±90 px (re-rolled every 2 frames); the protagonist in the counter is sliced with it. 6 flicker blocks (Signal/Volt/Acid, 30–220 × 8–40 px) at seeded spots on alternate frames; 2 px Paper scanlines every 4 px at 8%. From 11.3671875 the offsets scale ×0.25 (the glitch half-resolves so the D reads). Caption "D — GLITCH". |
| 11.484375 → 11.71875 | 690 | 7.1.3 | E — SHAPE (Acid, the reel's only full-frame Acid moment): Ink rectangles; stem x 460→650, y 150→930; top arm x 650→1140, y 150→320; middle arm x 650→888, y 455→625; bottom arm x 650→1140, y 760→930. The stem drops from above (translateY −1100→0, swift, 5 frames) with a 1-frame landing squash (scaleY 0.92 at its base); the arms then extend out of the stem to the right (scaleX 0→1 from x 650, punch), 1-frame stagger top→bottom, each trailing three 4 px Ink speed lines that retract over 6 frames. The middle arm's overshoot kisses the protagonist, which squashes 0.85 × 1.18 and springs back (TIGHT): the E's full stop. Caption "E — SHAPE". |
| 11.71875 → 11.8359375 | 704 | 7.2.1 | THE ROW (Ink), accelerating to 16ths: cells pop in pairs, C+L on 11.71875, A+U on 11.8359375, D+E on 11.953125 (scale 0.7→1, swift, 5 frames, with a 1-frame Paper 2 px outline flash). The dot anticipates at the anchor (squash 1.3 × 0.77, drawn above the cells). |
| 11.8359375 → 12.1875 | 711 | 7.2.2 | The dot LEAPS (on the A+U pop): an arc from (960,540) to (1750,682), with y(τ) = 540 + 142τ − 4·407.9·τ(1−τ) (apex ≈200) and x linear, over 0.3515625 s, shrinking Ø112→Ø56 and stretched along its velocity. |
| 12.0703125 → 12.1875 | 725 | 7.2.4 | The whole row glitch-stutters: slices offset ±40 px for 7 frames (seeded on the frame index). |
| 12.1875 → 12.65625 | 732 | 7.3.1 | THE REVEAL on beat 3: the row snaps clean and legible, C L A U D E. The dot lands as its period at (1750,682), Ø56, bottom on the cell baseline y=710, with a 2-frame squash 1.4 × 0.71 and a TIGHT settle: "CLAUDE.". Captions type on at 2 chars/frame: HALFTONE, GRID, LIQUID, DATA, GLITCH, SHAPE. Each cell idles at low amplitude (ripple, wobble, flicker). Legible hold 0.47 s. |
| 12.65625 → 12.890625 | 760 | 7.4.1 | FLATTEN (beat 4, the drums drop out): captions wipe out right→left (0.1 s); each cell's ground and technique collapse toward the cell centre (clip-path inset, whip, 0.117 s, 1-frame stagger L→R), revealing a plain Paper glyph at the same position and size underneath. All six are plain Paper letters on Ink by ≈12.83. The dot stays put. |
| 12.890625 → 13.0917 | 774 | 7.4.3 | SQUEEZE (anticipation): each letter animates from its cell position to its slot in the canonical condensed word (per-letter x from Range rects on the canonical element measured at setup): font-size 291→370, font-stretch 100%→62%, snap ease, arriving 13.0917. The dot slides from (1750,682) Ø56 to (1542,638) Ø64 (snap). A tremble of ±2 px (R.noise2) on the word and dot, windowed by sin(π·u) over 13.0391→13.0917, returns to exactly 0. |
| 13.0917 → 13.125 | 786 | 7.4.4 | REST POSE (frames 786–787): swap the six spans for the single canonical element (no per-letter spans on the rest frames): Ink ground, condensed "CLAUDE", and the dot Ø64 at (1542,638). Nothing else. |

**On-screen text:** "D" · "E" · "D — GLITCH" · "E — SHAPE" · "C L A U D E (specimen row)" · "HALFTONE · GRID · LIQUID · DATA · GLITCH · SHAPE" · "CLAUDE."

**Handoff in:** @11.25: a hard cut from the U chart (Paper) to the glitched D (Ink), with the dot Ø112 locked at (960,540) across the cut.

> **Handoff out:** @13.125 (rest from 13.0917): Ink #0B0B0F; the canonical condensed "CLAUDE" (Archivo 900, font-stretch 62%, 370 px, letter-spacing 0, Paper, text-align centre across 1920, baseline 670 → top ≈361.8, ink ≈ x 427→1496); a flat Signal disc Ø64 centred (1542,638) (bottom on the baseline, 14 px right of the E). Nothing else.

**Overlap ownership:** None. The 13.125 white flash cue covers any sub-pixel mismatch.

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(11.25, 'chroma', {amt: 18, dur: 0.234375});  // glitch D
R.cue(11.25, 'shake', {amt: 6, dur: 0.15});  // glitch D
R.cue(11.484375, 'zoom', {amt: 0.05, dur: 0.12});  // Acid E punch
R.cue(11.71875, 'shake', {amt: 3, dur: 0.06});  // row pair 1
R.cue(11.8359375, 'shake', {amt: 3, dur: 0.06});  // row pair 2
R.cue(11.953125, 'shake', {amt: 3, dur: 0.06});  // row pair 3
R.cue(12.0703125, 'chroma', {amt: 10, dur: 0.1171875});  // row stutter
R.cue(12.1875, 'zoom', {amt: 0.02, dur: 0.12});  // CLAUDE. revealed
R.cue(12.65625, 'grain', {amt: 0.03, dur: 0.46875});  // tension
R.cue(12.65625, 'vignette', {amt: 0.45, dur: 0.46875, in: 0.35, out: 0.02});  // OPTIONAL engine extension: squeeze tension
R.cue(12.890625, 'shake', {amt: 1, dur: 0.05859375, curve: 0});  // rumble step 1 (held)
R.cue(12.94921875, 'shake', {amt: 2, dur: 0.05859375, curve: 0});  // rumble step 2 (held); stops dead at 13.0078 for the silent 16th
```

**Sound:** 11.25 a glitch stutter (the previous 8th of the mix re-triggered in 32nds, bitcrushed). 11.484375 a sharp synth stab + snare + three 'shwip's for the arms. 11.71875 / 11.8359 / 11.9531 16th glitch stutters rising F→Ab→C; a buffer-repeat on 12.0703. 12.1875 a big Fm(add9) stab + clap + a 'plip' as the period lands. 12.65625: the drums drop out, leaving a riser (noise + saw) that stops dead at 13.0078, a 32nd snare roll, a sub inhale, and the reverse swell of the final hit peaking into 13.125. 13.0078→13.125: silence except the swell's peak (the gap).

```js
R.sfx(11.25, 'glitch', {dur: 0.234375});  // D
R.sfx(11.484375, 'impact', {amt: 0.45});  // E stab
R.sfx(11.5677, 'swish', {amt: 0.35});  // arm 1
R.sfx(11.5844, 'swish', {amt: 0.35});  // arm 2
R.sfx(11.601, 'swish', {amt: 0.35});  // arm 3
R.sfx(11.71875, 'glitch', {dur: 0.06, pitch: 1.0});  // row pop F
R.sfx(11.8359375, 'glitch', {dur: 0.06, pitch: 1.189});  // row pop Ab
R.sfx(11.953125, 'glitch', {dur: 0.06, pitch: 1.498});  // row pop C
R.sfx(11.8359375, 'whoosh', {dur: 0.3515625, dir: "up"});  // dot leap (lands 12.1875)
R.sfx(12.0703125, 'glitch', {dur: 0.1171875});  // buffer repeat
R.sfx(12.1875, 'pop', {pitch: 2.0});  // period lands
R.sfx(12.1875, 'type', {count: 8, dur: 0.1333});  // captions
R.sfx(12.65625, 'riser', {dur: 0.3515625});  // tension, stops dead at 13.0078
R.sfx(12.65625, 'reverse', {dur: 0.46875});  // final-hit swell, peaks 13.125
R.sfx(12.890625, 'swish', {amt: 0.35});  // squeeze
```

**Build notes and risks:** The minis are simplified re-implementations of the s06 looks (spec above), not imports. Glitch randomness is keyed on frame index. The rest frames MUST use the single canonical element (s08 renders the identical element on its first frame).

<a id="s08-fullstop"></a>
## s08-fullstop: Full Stop — the name card

| Window | Frames | Musical | Length | z | Root bg |
|---|---|---|---|---|---|
| 13.125 → 15.0 s | 788–899 | 8.1.1 → 8.4.4 | 4 beats | 80 | Ink |

**Showcases:** logotype resolve through anticipation → release on the width axis · the protagonist's final bow: smear, arc, squash, two follow-through bounces · editorial hierarchy (grotesk / serif italic / mono) on a Swiss lockup with hanging punctuation · an original monogram built from a stroke draw and a dot drop · a held final beat with no dead frames

**Layout and fixed geometry**

- FINAL LOCKUP (everything below is static from 14.0625):
  - "CLAUDE": the canonical element restyled to Archivo 900, font-stretch 125%, font-size 284 px (solved so the ink width = 1520: 5.3525 px of ink per px of font-size), letter-spacing 0, Paper, text-align centre across 1920, baseline 600 → top = 600 − 0.833·284 ≈ 363.4. Ink box ≈ x 200→1720, flat cap top ≈405 (round ≈401).
  - Period: flat Signal disc Ø60 centred (1764,570), bottom on the baseline, 14 px right of the E. It HANGS outside the measure; the word stays centred.
  - Hairlines: Paper 1 px @35% at y=370 and y=648 from x 200 to 1720; 12 px registration crosses (Paper 1 px @60%) centred on the 4 hairline ends.
  - "SHOWREEL 2026": JetBrains Mono 500, 30 px, letter-spacing 0.24em, Paper @85%, ink-left x=200, baseline 336.
  - "Motion Designer": Instrument Serif italic 96 px, Paper, ink-left x=200, baseline 752 (≈570 px wide).
  - Tagline "EVERY FRAME, ON PURPOSE.": JetBrains Mono 400, 22 px, letter-spacing 0.16em, Fog, ink-right x=1720, baseline 752 (shares the role's baseline).
  - Monogram "C." (original mark): box x 200→272, y 944→1016 (the old HUD chapter slot, aligned to the name's left edge). A Paper ring centred (236,980), centreline radius 28, stroke 12, butt caps, with a 60° opening centred at 3 o'clock (angles measured clockwise from 3 o'clock in screen space: the arc runs from 30° through 6, 9 and 12 o'clock to 330°); plus a Signal Ø16 dot that lands in the opening at (264,980).
  - HUD (s00) keeps crop marks, timecode and the beat meter.

**Beat by beat**

| t (s) | Frame | Pos | Action |
|---|---|---|---|
| 13.125 → 13.359375 | 788 | 8.1.1 | FINAL HIT (the white flash covers the first frames). The first frame is the canonical condensed state. RELEASE over one 8th (swift): font-stretch 62%→125% and font-size 370→284 on the same ease; baseline 670→600; letter-spacing −0.03em → +0.02em → 0 on a POP spring (reaches exactly 0 by ≈13.55); an extra scaleX 1.04→1.0 overshoot (TIGHT). |
| 13.125 → 13.59375 | 788 | 8.1.1 | THE BOW: the expanding E shoves the dot up and out. τ = (t − 13.125)/0.46875; x(t) = E_right(t) + 46 − 2τ, where E_right(t) = 960 + inkWidth(t)/2 comes from the same precomputed ink-width interpolation that drives the release, so the dot always rides 14+ px clear of the E (reference x: 1609, 1694, 1731, 1747, 1755 on frames 788–792, then ≈1764); y(τ) = 638 − 68τ − 4·403.3·τ(1−τ) (apex ≈200 at τ 0.52, i.e. ≈13.37). Diameter 64→60. Smear frames on the first 2 frames (stretch 2.2 then 1.4 along velocity), then a normal stretch in flight: kicked up-right, then a clean vertical pop and drop onto the period position. |
| 13.2421875 → 13.59375 | 795 | 8.1.2 | Hairlines draw outward from x=960 to 200 and 1720 (swift); the registration crosses pop on at 13.59375. |
| 13.59375 → 13.83 | 816 | 8.2.1 | LANDING on beat 2 as the period at (1764,570): a 2-frame squash 1.45 × 0.69 anchored on the baseline (y 600), then micro-bounces: 34 px landing 13.7109375, 10 px landing 13.76953125, settled by 13.83 (TIGHT). "Motion Designer" rises through a baseline mask (translateY 100%→0, swift 0.234 s, stagger 1/120 s per letter), complete by ≈13.95. |
| 13.828125 → 14.0625 | 830 | 8.2.3 | On the and: "SHOWREEL 2026" types on at 1 char/frame (13 chars, done 14.045) behind a Signal block cursor (0.6 em × 0.75 em) that disappears on 14.0625. The tagline reveals left→right through a mask at 2 chars/frame (done ≈14.03). The monogram ring stroke-draws from 30° clockwise (screen space) to 330° (swift, done 14.0625). |
| 14.0625 → 14.53125 | 844 | 8.3.1 | LOCK on beat 3: every element final and still: CLAUDE, Motion Designer and SHOWREEL 2026 are fully legible from here to the end (0.94 s). A slow LINEAR push-in on a wrapper (s08 content only) begins: scale 1.000→1.012 about (960,540) by 15.0. |
| 14.53125 → 14.6484375 | 872 | 8.4.1 | THE FINAL TICK on beat 4: the Signal Ø16 dot drops into the monogram opening (from y 940, 3 frames, inQuad) with a 2-frame squash, so the mark reads "C.". On the same frame the big period blinks (scale 1→1.14→1: key frames 14.53125 → 14.5703 outCubic → 14.6484 inOutSine). The HUD beat meter fills all four squares Signal. |
| 14.6484375 → 15.0 | 879 | 8.4.2 | HELD: nothing moves except the push-in and the engine grain. Final frame 899 is the complete card. |

**On-screen text:** "CLAUDE." · "Motion Designer" · "SHOWREEL 2026" · "EVERY FRAME, ON PURPOSE." · "C. (original monogram)"

**Handoff in:** Identical to s07 out: Ink; canonical condensed "CLAUDE" (Archivo 900, 62%, 370 px, baseline 670, centred); Signal disc Ø64 at (1542,638).

> **Handoff out:** End of film. Frame 899: Ink; CLAUDE at 125% / 284 px (ink x 200→1720, baseline 600) with the hanging Signal period Ø60 at (1764,570); hairlines at y 370 and 648; SHOWREEL 2026 (200, 336); Motion Designer (200, 752); tagline right-aligned at 1720 (752); the C. monogram at (200,944)–(272,1016); push-in ≈1.012; HUD crop marks, TC 00:00:14:59, full meter.

**Overlap ownership:** None. It begins on s07's exact end state under the 13.125 white flash. The HUD removes its TL/TR/BL text by 13.36, which frees the monogram slot.

**Global FX cues this scene registers** (in `setup`):

```js
R.cue(13.125, 'chroma', {amt: 10, dur: 0.2});  // final hit
R.cue(13.125, 'flash', {amt: 1.0, dur: 0.15, color: "#FFFFFF"});  // FINAL HIT (masks the s07→s08 handoff)
R.cue(13.125, 'shake', {amt: 14, dur: 0.35});  // final hit
R.cue(13.125, 'zoom', {amt: 0.06, dur: 0.3});  // final hit
R.cue(13.59375, 'shake', {amt: 3, dur: 0.1});  // period lands
R.cue(14.53125, 'zoom', {amt: 0.01, dur: 0.12});  // the final tick
```

**Sound:** 13.125 the massive final impact: kick + 40 Hz sub boom (1.5 s decay) + crash + a wide Fm(add9) stab into a long hall. No drums after this. A soft upward whoosh for the dot's flight. 13.59375 the woody pluck on F5 (a callback to the bar-2 landings) with micro-bounce ticks on 13.7109 and 13.7695. An airy shimmer and soft keyboard ticks for the type-on from 13.828. 14.53125 THE FULL STOP: a clean sine tick on F6 (40 ms) + a soft sub click. The reverb tail decays to −40 dB by 14.98 and the engine's end fade makes the last frames near-silent.

```js
R.sfx(13.125, 'impact', {amt: 1.3, tone: "huge"});  // FINAL HIT
R.sfx(13.125, 'subdrop', {amt: 1.0});  // final hit
R.sfx(13.125, 'shimmer', {dur: 1.6, amt: 0.5});  // tail
R.sfx(13.125, 'whoosh', {dur: 0.234375, dir: "up"});  // dot flight
R.sfx(13.59375, 'pop', {pitch: 2.0});  // period lands, F5
R.sfx(13.7109375, 'tick', {pitch: 2.0});  // bounce
R.sfx(13.76953125, 'tick', {pitch: 2.5});  // bounce
R.sfx(13.828125, 'type', {count: 13, dur: 0.2167});  // SHOWREEL 2026
R.sfx(13.828125, 'shimmer', {dur: 0.5, amt: 0.3});  // reveal air
R.sfx(14.53125, 'blip', {pitch: 4.0});  // THE FULL STOP, F6 sine
R.sfx(14.53125, 'click', {pitch: 0.5});  // soft sub click
```

**Build notes and risks:** Use the canonical element and only restyle it (font-stretch, font-size, top, letter-spacing), so frame 788 matches s07. The 284 px size is solved from the measured ink ratio; re-measure at setup and keep the ink width at 1520. The monogram draw uses stroke-dasharray via R.drawStroke. Put the push-in on a wrapper and leave the HUD out of it.

<a id="global-fx-cue-list"></a>
## Global FX cue list

- Engine vocabulary (src/engine.js R.cue): flash {amt 0..1, dur, color}, shake {amt px, dur, freq}, chroma {amt px, dur, angle rad}, zoom {amt extra scale, dur}, letterbox {amt px, dur, in, out}, grain {amt, dur}.
- flash, shake, chroma and zoom decay as (1 − k)^curve with k = (t − t0)/dur (curve defaults to 2). curve 0 = held for dur (used for ramps as stair-steps).
- Base levels are engine constants: grain 0.045 and vignette 0.22. A grain cue adds its amt for dur.
- vignette cues are an OPTIONAL extension (not in the engine yet; R.fxAt ignores unknown types). Semantics if added: opacity eases from the 0.22 base to amt with E.snap over "in", holds, and returns over "out".
- Cues are global and registered by the owning scene in setup, so the soundtrack reinforcement (FX_CUE_SOUNDS in audio/synth.py) hears them.

| t (s) | Frame | Pos | Type | Amount | Dur (s) | Extra | Owner | Note |
|---|---|---|---|---|---|---|---|---|
| 0.0 | 0 | 1.1.1 | shake | 4 | 0.15 |  | s01 | cold-open impact |
| 0.0 | 0 | 1.1.1 | zoom | 0.03 | 0.2 |  | s01 | cold-open punch: frame 0 lands 3% zoomed |
| 0.46875 | 29 | 1.2.1 | shake | 10 | 0.2 |  | s01 | HEAVY slam |
| 0.46875 | 29 | 1.2.1 | zoom | 0.06 | 0.234375 |  | s01 | HEAVY slam: THE HOOK |
| 0.9375 | 57 | 1.3.1 | zoom | 0.025 | 0.15 |  | s01 | NARROW squeeze |
| 1.40625 | 85 | 1.4.1 | chroma | 4 | 0.12 |  | s01 | WIDE chroma kiss |
| 1.40625 | 85 | 1.4.1 | zoom | 0.035 | 0.18 |  | s01 | WIDE |
| 2.34375 | 141 | 2.2.1 | shake | 4 | 0.12 |  | s02 | dot lands on "Timing" |
| 2.8125 | 169 | 2.3.1 | shake | 5 | 0.14 |  | s02 | dot lands on "everything" |
| 3.515625 | 211 | 2.4.3 | vignette | 0.45 | 0.234375 | in 0.2, out 0.02 | s02 | OPTIONAL engine extension: tunnel vision during the dive |
| 3.75 | 225 | 3.1.1 | chroma | 8 | 0.2 |  | s03 | through the dot into the corridor |
| 3.75 | 225 | 3.1.1 | zoom | 0.04 | 0.2 |  | s03 | box unfold starts |
| 4.21875 | 254 | 3.2.1 | chroma | 3 | 0.1 |  | s03 | roll 1 |
| 4.6875 | 282 | 3.3.1 | chroma | 4 | 0.1 |  | s03 | roll 2 + rush |
| 4.921875 | 296 | 3.3.3 | chroma | 5 | 0.1171875 | curve 0 | s03 | rush ramp step 1 (curve 0 = held) |
| 4.921875 | 296 | 3.3.3 | vignette | 0.5 | 0.2008 | in 0.15, out 0.02 | s03 | OPTIONAL engine extension: rush tunnel vision |
| 5.0390625 | 303 | 3.3.4 | chroma | 9 | 0.0838 | curve 0 | s03 | rush ramp step 2, hard off at 5.1229 so the rest frames are clean |
| 5.15625 | 310 | 3.4.1 | flash | 0.35 | 0.1 | color #FFFFFF | s04 | arrival into the Paper UI |
| 5.625 | 338 | 4.1.1 | shake | 2 | 0.08 |  | s04 | cursor press |
| 7.03125 | 422 | 4.4.1 | grain | 0.04 | 0.46875 |  | s05 | breath texture |
| 7.03125 | 422 | 4.4.1 | letterbox | 110 | 0.46875 | in 0.1, out 0.05 | s05 | bars snap in on lights-out, out on the drop (fully gone at 7.5) |
| 7.03125 | 422 | 4.4.1 | vignette | 0.6 | 0.46875 | in 0.1, out 0.03 | s05 | OPTIONAL engine extension: breath darkness |
| 7.5 | 450 | 5.1.1 | chroma | 12 | 0.3 |  | s05 | drop |
| 7.5 | 450 | 5.1.1 | flash | 1.0 | 0.1 | color #FFFFFF | s05 | THE DROP (white) |
| 7.5 | 450 | 5.1.1 | shake | 18 | 0.45 |  | s05 | drop |
| 7.5 | 450 | 5.1.1 | zoom | 0.08 | 0.3 |  | s05 | drop |
| 7.96875 | 479 | 5.2.1 | shake | 5 | 0.15 |  | s05 | second particle impulse |
| 7.96875 | 479 | 5.2.1 | zoom | 0.03 | 0.15 |  | s05 | second particle impulse |
| 8.4375 | 507 | 5.3.1 | flash | 0.3 | 0.08 | color #FF4A1C | s05 | Signal flash: particles snap into RANGE |
| 8.4375 | 507 | 5.3.1 | shake | 6 | 0.15 |  | s05 | RANGE snap |
| 9.140625 | 549 | 5.4.3 | chroma | 14 | 0.234375 | angle 0 | s05 | whip smear, horizontal split |
| 9.375 | 563 | 6.1.1 | shake | 6 | 0.15 |  | s06 | whip lands on C |
| 9.375 | 563 | 6.1.1 | zoom | 0.04 | 0.15 |  | s06 | whip lands on C |
| 9.84375 | 591 | 6.2.1 | chroma | 3 | 0.1 |  | s06 | cut to L |
| 9.84375 | 591 | 6.2.1 | shake | 4 | 0.1 |  | s06 | cut to L |
| 10.3125 | 619 | 6.3.1 | chroma | 3 | 0.1 |  | s06 | cut to A |
| 10.3125 | 619 | 6.3.1 | shake | 4 | 0.1 |  | s06 | cut to A |
| 10.78125 | 647 | 6.4.1 | chroma | 3 | 0.1 |  | s06 | cut to U |
| 10.78125 | 647 | 6.4.1 | shake | 4 | 0.1 |  | s06 | cut to U |
| 11.25 | 675 | 7.1.1 | chroma | 18 | 0.234375 |  | s07 | glitch D |
| 11.25 | 675 | 7.1.1 | shake | 6 | 0.15 |  | s07 | glitch D |
| 11.484375 | 690 | 7.1.3 | zoom | 0.05 | 0.12 |  | s07 | Acid E punch |
| 11.71875 | 704 | 7.2.1 | shake | 3 | 0.06 |  | s07 | row pair 1 |
| 11.8359375 | 711 | 7.2.2 | shake | 3 | 0.06 |  | s07 | row pair 2 |
| 11.953125 | 718 | 7.2.3 | shake | 3 | 0.06 |  | s07 | row pair 3 |
| 12.0703125 | 725 | 7.2.4 | chroma | 10 | 0.1171875 |  | s07 | row stutter |
| 12.1875 | 732 | 7.3.1 | zoom | 0.02 | 0.12 |  | s07 | CLAUDE. revealed |
| 12.65625 | 760 | 7.4.1 | grain | 0.03 | 0.46875 |  | s07 | tension |
| 12.65625 | 760 | 7.4.1 | vignette | 0.45 | 0.46875 | in 0.35, out 0.02 | s07 | OPTIONAL engine extension: squeeze tension |
| 12.890625 | 774 | 7.4.3 | shake | 1 | 0.05859375 | curve 0 | s07 | rumble step 1 (held) |
| 12.94921875 | 777 | 7.4.3 | shake | 2 | 0.05859375 | curve 0 | s07 | rumble step 2 (held); stops dead at 13.0078 for the silent 16th |
| 13.125 | 788 | 8.1.1 | chroma | 10 | 0.2 |  | s08 | final hit |
| 13.125 | 788 | 8.1.1 | flash | 1.0 | 0.15 | color #FFFFFF | s08 | FINAL HIT (masks the s07→s08 handoff) |
| 13.125 | 788 | 8.1.1 | shake | 14 | 0.35 |  | s08 | final hit |
| 13.125 | 788 | 8.1.1 | zoom | 0.06 | 0.3 |  | s08 | final hit |
| 13.59375 | 816 | 8.2.1 | shake | 3 | 0.1 |  | s08 | period lands |
| 14.53125 | 872 | 8.4.1 | zoom | 0.01 | 0.12 |  | s08 | the final tick |

<a id="music-plan"></a>
## Music plan, bar by bar

128 BPM, 4/4, **F minor** (matches `audio/synth.py`), 8 bars. A global sidechain ducks pads and bass on every kick. Picture-driven sounds are declared by each scene with `R.sfx` (listed per scene) and exported by `tools/cues.mjs`; the arrangement below is the musical bed. The `SONG` hints map onto the synth's per-bar vocabulary.

| Bar | Starts | Section | Energy | Harmony | Plan | `SONG` hint |
|---|---|---|---|---|---|---|
| 1 | 0.0 | **COLD OPEN / AXIS** | 0.35 | Fm9 | Hits only, no groove: one hit per word. 1.1 impact (sub F1) under a quiet high-passed bed of glassy 16th plucks (F5 Ab5 C6 F6) for LIGHT; 1.2 SLAM (kick + clap + distorted sub + low tom + room) for HEAVY; 1.3 a squeeze stab (band-passed saw chord bending −5 st over 0.1 s) for NARROW; 1.4 a wide 7-voice detuned supersaw Fm stab with a reverse-cymbal tail for WIDE; 1.4.3 the dot 'bloop'; 1.4.4 a falling whoosh. | section 'hook', energy 0.35: kick 'x...x...........' (beats 1–2 only), clap '....x...........', tom '....l...........', stab '........x...x...' (beats 3–4) with stab_cut (0.45, 0.85), tick 'gggg............' (glassy 16ths under LIGHT only). |
| 2 | 1.875 | **GROOVE IN / TIMING** | 0.55 | Fm9 . Dbmaj7 . | Four-on-the-floor kick, off-8th closed hats, sub bass in 8ths F1 F1 Ab1 C2, clap on 2 and 4 (2.34375 = the first landing, 3.28125 = 'notices the camera'). The picture supplies marimba plucks climbing F4 Ab4 C5 F5 on the landings. A reverse swell 3.5156→3.75 into the dive. | as the current bar 2 (groove), with the stab thinned so the landing plucks sit on top. |
| 3 | 3.75 | **SPACE → EASING** | 0.65 | Abmaj7 . Eb . | 3.75 sub boom + door whoosh. A pad plus a 16th F-minor-pentatonic arp opening its filter. Roll clunks on 4.21875 and 4.6875; ring-chase ticks on 16ths from 4.6875; an accelerating whoosh and riser 4.6875→5.15625, cut clean. On beat 4 (5.15625) the drums THIN for the graph editor: kick + rim + soft hats, UI lightness. | kick FOUR; hats '.o.o .o.o .o.o ....'; rim '.... .... .... x...'; shaker only in beats 1–3. |
| 4 | 5.625 | **EASING → BREATH** | 0.75 | Dbmaj7 . Csus4 C | Kick on 1 (5.625 = the cursor press), rim on 2 and 4, soft 16th hats; UI foley on top (press click + tink, drag glide, the play swoop tracking v, tick pops). A snare roll from 6.5625 (8ths, then 16ths from 6.797) with noise and saw risers. 7.03125 TAPE-STOP: the whole music bus pitch-dives to zero over 0.18 s, then near-silence; a reverse cymbal, a reversed impact and a sub inhale (30→55 Hz) swell into 7.5. | snare '........ ........ 5.5.6.6. ........'; stutter e.g. '.... .... .... txxx' (tape-slow from 7.03125, then mute); hp sweep (20, 380); the tapestop SFX from s05 carries the pitch dive. |
| 5 | 7.5 | **DROP / ENERGY** | 1.0 | Fm9 → Dbmaj7 | A mega impact (kick + long 808 F1 + noise burst + crash) and a sub drop. Full groove: four-on-the-floor, clap on 2 and 4, rolling 16th hats with accents, a pumping 8th sub bass, supersaw stabs on off-beat 8ths, a granular glitter layer. 7.96875 a secondary impact; 8.32→8.4375 a reverse zip into a bright stab on the RANGE snap; 9.140625 a whoosh right→left. | as the current bar 5 (drop). |
| 6 | 9.375 | **RANGE I (C · L · A · U)** | 1.0 | Dbmaj7 . Eb . | The groove continues; each one-beat cut adds its signature from the picture (bitcrush fizz, mechanical clicks and a square blip, a resonant bloop and drip, data blips and a glide). A snare fill in 16ths 11.015625→11.25. | as the current bar 6 (drop 2), with clap '....x.......x.xx' feeding the fill. |
| 7 | 11.25 | **RANGE II → SQUEEZE** | 1.0 | Fm9 . Eb . | 11.25 a glitch stutter (the previous 8th re-triggered in 32nds, bitcrushed); 11.484375 a stab + snare + 3 shwips; 16th stutters rising F→Ab→C on the row pops; a buffer-repeat on 12.0703; 12.1875 a big Fm(add9) stab + clap + plip (the period lands). 12.65625 (beat 4): drums out, leaving a riser, a 32nd snare roll, a sub inhale and the reverse swell of the final hit. 13.0078125→13.125: total silence except the swell's peak (the gap). | kick 'x...x...x.......' and hats stop before beat 4; snare as a 32-step roll '........ ........ ........ 6789XX..' (the last 16th silent); gate 'xxxx xxxx xxxx xxx.'; stutter '22.. ...b .... ....' (32nd retrigger on beat 1, buffer-repeat on step 8 = 12.0703). The riser SFX ends at 13.0078 so the last 16th is silent except the reverse swell. |
| 8 | 13.125 | **FINAL HIT + TAIL** | 0.2 | Fm(add9) | 13.125 a massive impact (kick + 40 Hz sub boom with 1.5 s decay + crash + a wide Fm(add9) stab into a long hall). No drums after this. A dot-flight whoosh up; 13.59375 a woody pluck F5 (callback to bar 2) with two micro-bounce ticks; keyboard ticks and air under the reveals from 13.828; 14.53125 THE FULL STOP, a clean sine tick F6 (40 ms) + soft sub click. The tail decays to −40 dB by 14.98, then the engine fades to digital silence. | as the current bar 8 (resolve): pad sustained, a single stab; FX impact/subdrop/shimmer on 8.1.0 (picture declares the same, so arrangement FX yield). |

<a id="hit-list"></a>
## Picture-lock hit list

| t (s) | Frame | Pos | Event |
|---|---|---|---|
| 0.0 | 0 | 1.1.1 | cold-open impact, LIGHT |
| 0.46875 | 29 | 1.2.1 | HEAVY slam (the hook) |
| 0.9375 | 57 | 1.3.1 | NARROW squeeze |
| 1.40625 | 85 | 1.4.1 | WIDE stab |
| 1.640625 | 99 | 1.4.3 | the dot is born |
| 1.875 | 113 | 2.1.1 | groove in, anticipation |
| 2.34375 | 141 | 2.2.1 | land 1 "Timing" (clap) |
| 2.578125 | 155 | 2.2.3 | land 2 "is" |
| 2.8125 | 169 | 2.3.1 | land 3 "everything" |
| 2.9296875 | 176 | 2.3.2 | THE FULL STOP lands |
| 3.28125 | 197 | 2.4.1 | notices the camera (clap) |
| 3.75 | 225 | 3.1.1 | box unfolds |
| 4.21875 | 254 | 3.2.1 | roll 1 |
| 4.6875 | 282 | 3.3.1 | roll 2 + rush |
| 5.15625 | 310 | 3.4.1 | arrival in the graph editor |
| 5.625 | 338 | 4.1.1 | cursor press |
| 5.859375 | 352 | 4.1.3 | release |
| 6.09375 | 366 | 4.2.1 | PLAY |
| 6.4357 | 387 | 4.2.3 | overshoot peak v 1.10 (picture-derived) |
| 6.5625 | 394 | 4.3.1 | settle, snare roll starts |
| 7.03125 | 422 | 4.4.1 | LIGHTS OUT + tape-stop |
| 7.5 | 450 | 5.1.1 | THE DROP |
| 7.96875 | 479 | 5.2.1 | second impulse |
| 8.4375 | 507 | 5.3.1 | RANGE snap |
| 9.140625 | 549 | 5.4.3 | whip |
| 9.375 | 563 | 6.1.1 | C lands |
| 9.609375 | 577 | 6.1.3 | ripple pulse |
| 9.84375 | 591 | 6.2.1 | L |
| 10.078125 | 605 | 6.2.3 | square→circle |
| 10.3125 | 619 | 6.3.1 | A |
| 10.546875 | 633 | 6.3.3 | drip-through |
| 10.78125 | 647 | 6.4.1 | U |
| 11.1328125 | 668 | 6.4.4 | data point locked |
| 11.25 | 675 | 7.1.1 | D glitch |
| 11.484375 | 690 | 7.1.3 | E |
| 11.71875 | 704 | 7.2.1 | row pair 1 |
| 11.8359375 | 711 | 7.2.2 | row pair 2 + dot leap |
| 11.953125 | 718 | 7.2.3 | row pair 3 |
| 12.0703125 | 725 | 7.2.4 | row stutter |
| 12.1875 | 732 | 7.3.1 | CLAUDE. revealed |
| 12.65625 | 760 | 7.4.1 | drums out, flatten |
| 12.890625 | 774 | 7.4.3 | squeeze |
| 13.0078125 | 781 | 7.4.4 | SILENCE (the gap) |
| 13.125 | 788 | 8.1.1 | FINAL HIT |
| 13.59375 | 816 | 8.2.1 | period lands |
| 13.828125 | 830 | 8.2.3 | type-on |
| 14.0625 | 844 | 8.3.1 | lock |
| 14.53125 | 872 | 8.4.1 | THE FINAL TICK |

<details><summary>Full <code>R.sfx</code> timeline across all scenes</summary>

| t (s) | Scene | Type | Opts | Note |
|---|---|---|---|---|
| 0.0 | s01-axis | impact | `{"amt": 0.8, "tone": "sub"}` | cold open |
| 0.0 | s01-axis | shimmer | `{"dur": 0.46875, "amt": 0.3}` | glassy LIGHT bed |
| 0.46875 | s01-axis | impact | `{"amt": 1.0}` | HEAVY slam |
| 0.9375 | s01-axis | swish | `{"amt": 0.5}` | NARROW squeeze |
| 1.40625 | s01-axis | impact | `{"amt": 0.55}` | WIDE stab |
| 1.640625 | s01-axis | pop | `{"pitch": 2.0}` | the dot is born |
| 1.7578125 | s01-axis | whoosh | `{"dur": 0.1171875, "dir": "down"}` | letters drop |
| 1.875 | s02-timing | blip | `{"pitch": 0.5}` | anticipation stretch |
| 1.9921875 | s02-timing | whoosh | `{"dur": 0.3515625, "dir": "up"}` | leap (lands 2.34375) |
| 2.34375 | s02-timing | pop | `{"pitch": 1.0}` | land 1, F4 |
| 2.578125 | s02-timing | pop | `{"pitch": 1.189}` | land 2, Ab4 |
| 2.8125 | s02-timing | pop | `{"pitch": 1.498}` | land 3, C5 |
| 2.9296875 | s02-timing | pop | `{"pitch": 2.0}` | full stop, F5 |
| 3.046875 | s02-timing | tick | `{"pitch": 2.0}` | micro-hop |
| 3.28125 | s02-timing | click | `{"pitch": 1.2}` | notices the camera |
| 3.515625 | s02-timing | reverse | `{"dur": 0.234375}` | dive, lands 3.75 |
| 3.75 | s03-space | impact | `{"amt": 0.7, "tone": "sub"}` | box unfolds |
| 3.75 | s03-space | whoosh | `{"dur": 0.3515625, "dir": "down"}` | door |
| 4.21875 | s03-space | swish | `{"amt": 0.5}` | roll 1 |
| 4.21875 | s03-space | click | `{"pitch": 0.5}` | roll 1 clunk |
| 4.6875 | s03-space | swish | `{"amt": 0.6}` | roll 2 |
| 4.6875 | s03-space | click | `{"pitch": 0.5}` | roll 2 clunk |
| 4.6875 | s03-space | tick | `{"pitch": 1.0}` | ring chase |
| 4.6875 | s03-space | whoosh | `{"dur": 0.46875, "dir": "up"}` | rush, lands 5.15625 |
| 4.8046875 | s03-space | tick | `{"pitch": 1.12}` | ring chase |
| 4.921875 | s03-space | tick | `{"pitch": 1.26}` | ring chase |
| 5.0390625 | s03-space | tick | `{"pitch": 1.5}` | ring chase |
| 5.15625 | s04-easing | blip | `{"pitch": 2.0}` | arrival bloom |
| 5.2 | s04-easing | type | `{"count": 19, "dur": 0.3167}` | header typing |
| 5.625 | s04-easing | click | `{"pitch": 1.0}` | press |
| 5.625 | s04-easing | tick | `{"pitch": 3.0}` | tink |
| 5.625 | s04-easing | swish | `{"amt": 0.25}` | drag glide |
| 5.859375 | s04-easing | pop | `{"pitch": 1.5}` | release |
| 6.09375 | s04-easing | whoosh | `{"dur": 0.46875, "dir": "up"}` | play swoop |
| 6.223 | s04-easing | tick | `{"pitch": 1.0}` | tick 1/8 |
| 6.2577 | s04-easing | tick | `{"pitch": 1.06}` | tick 2/8 |
| 6.2784 | s04-easing | tick | `{"pitch": 1.12}` | tick 3/8 |
| 6.2929 | s04-easing | tick | `{"pitch": 1.19}` | tick 4/8 |
| 6.3048 | s04-easing | tick | `{"pitch": 1.26}` | tick 5/8 |
| 6.3166 | s04-easing | tick | `{"pitch": 1.33}` | tick 6/8 |
| 6.3316 | s04-easing | tick | `{"pitch": 1.41}` | tick 7/8 |
| 6.3566 | s04-easing | tick | `{"pitch": 1.5}` | end tick |
| 6.5625 | s04-easing | riser | `{"dur": 0.46875}` | build into the tape-stop |
| 6.796875 | s04-easing | reverse | `{"dur": 0.1875}` | retract zip |
| 7.03125 | s05-energy | tapestop | `{"dur": 0.18}` | lights out |
| 7.03125 | s05-energy | reverse | `{"dur": 0.46875}` | swell into the drop |
| 7.5 | s05-energy | impact | `{"amt": 1.2, "tone": "huge"}` | THE DROP |
| 7.5 | s05-energy | subdrop | `{"amt": 1.0}` | drop |
| 7.5 | s05-energy | shimmer | `{"dur": 0.9375, "amt": 0.6}` | particle glitter |
| 7.96875 | s05-energy | impact | `{"amt": 0.5}` | second impulse |
| 8.3203125 | s05-energy | reverse | `{"dur": 0.1171875}` | zip into the snap |
| 8.4375 | s05-energy | impact | `{"amt": 0.45}` | RANGE snap |
| 8.4375 | s05-energy | shimmer | `{"dur": 0.46875, "amt": 0.4}` | snap sparkle |
| 9.140625 | s05-energy | whoosh | `{"dur": 0.234375, "dir": "down"}` | whip R→L |
| 9.375 | s06-range-1 | glitch | `{"dur": 0.1}` | halftone fizz |
| 9.609375 | s06-range-1 | blip | `{"pitch": 1.5}` | ripple pulse |
| 9.84375 | s06-range-1 | tick | `{"pitch": 1.0}` | module fill |
| 9.9609375 | s06-range-1 | tick | `{"pitch": 1.0}` | module fill |
| 10.078125 | s06-range-1 | blip | `{"pitch": 0.75}` | square→circle |
| 10.1953125 | s06-range-1 | tick | `{"pitch": 1.0}` | module click |
| 10.3125 | s06-range-1 | pop | `{"pitch": 0.5}` | liquid bloop |
| 10.3125 | s06-range-1 | swish | `{"amt": 0.4}` | blobs rush in |
| 10.546875 | s06-range-1 | pop | `{"pitch": 2.5}` | drip plip |
| 10.78125 | s06-range-1 | blip | `{"pitch": 1.0}` | data |
| 10.8984375 | s06-range-1 | blip | `{"pitch": 1.19}` | data |
| 10.8984375 | s06-range-1 | whoosh | `{"dur": 0.234375, "dir": "up"}` | arc sweep |
| 11.015625 | s06-range-1 | blip | `{"pitch": 1.5}` | data |
| 11.1328125 | s06-range-1 | pop | `{"pitch": 2.0}` | data point locked |
| 11.25 | s07-range-2 | glitch | `{"dur": 0.234375}` | D |
| 11.484375 | s07-range-2 | impact | `{"amt": 0.45}` | E stab |
| 11.5677 | s07-range-2 | swish | `{"amt": 0.35}` | arm 1 |
| 11.5844 | s07-range-2 | swish | `{"amt": 0.35}` | arm 2 |
| 11.601 | s07-range-2 | swish | `{"amt": 0.35}` | arm 3 |
| 11.71875 | s07-range-2 | glitch | `{"dur": 0.06, "pitch": 1.0}` | row pop F |
| 11.8359375 | s07-range-2 | glitch | `{"dur": 0.06, "pitch": 1.189}` | row pop Ab |
| 11.8359375 | s07-range-2 | whoosh | `{"dur": 0.3515625, "dir": "up"}` | dot leap (lands 12.1875) |
| 11.953125 | s07-range-2 | glitch | `{"dur": 0.06, "pitch": 1.498}` | row pop C |
| 12.0703125 | s07-range-2 | glitch | `{"dur": 0.1171875}` | buffer repeat |
| 12.1875 | s07-range-2 | pop | `{"pitch": 2.0}` | period lands |
| 12.1875 | s07-range-2 | type | `{"count": 8, "dur": 0.1333}` | captions |
| 12.65625 | s07-range-2 | riser | `{"dur": 0.3515625}` | tension, stops dead at 13.0078 |
| 12.65625 | s07-range-2 | reverse | `{"dur": 0.46875}` | final-hit swell, peaks 13.125 |
| 12.890625 | s07-range-2 | swish | `{"amt": 0.35}` | squeeze |
| 13.125 | s08-fullstop | impact | `{"amt": 1.3, "tone": "huge"}` | FINAL HIT |
| 13.125 | s08-fullstop | subdrop | `{"amt": 1.0}` | final hit |
| 13.125 | s08-fullstop | shimmer | `{"dur": 1.6, "amt": 0.5}` | tail |
| 13.125 | s08-fullstop | whoosh | `{"dur": 0.234375, "dir": "up"}` | dot flight |
| 13.59375 | s08-fullstop | pop | `{"pitch": 2.0}` | period lands, F5 |
| 13.7109375 | s08-fullstop | tick | `{"pitch": 2.0}` | bounce |
| 13.76953125 | s08-fullstop | tick | `{"pitch": 2.5}` | bounce |
| 13.828125 | s08-fullstop | type | `{"count": 13, "dur": 0.2167}` | SHOWREEL 2026 |
| 13.828125 | s08-fullstop | shimmer | `{"dur": 0.5, "amt": 0.3}` | reveal air |
| 14.53125 | s08-fullstop | blip | `{"pitch": 4.0}` | THE FULL STOP, F6 sine |
| 14.53125 | s08-fullstop | click | `{"pitch": 0.5}` | soft sub click |

</details>

<a id="craft-notes-for-builders"></a>
## Craft notes for builders

1. Pure function of t. Set every animated property every frame. Seed all randomness with R.rand/R.hash keyed on an index or floor(frame/k). No CSS transitions or animations, Math.random, or Date.
2. Key poses land on grid frames. Accents go on the snare (beats 2 and 4) or off-beat 8ths; cuts go on downbeats or snares.
3. Anticipation before every big move (≥ 2 frames); follow-through after every stop (overshoot or settle wobble). Nothing starts or stops dead unless it is a deliberate hard cut.
4. Squash & stretch preserves volume (sx·sy = 1 ± 0.02), anchors at the contact point on impact, and aligns to the velocity vector in flight (rotate by atan2(vy, vx)).
5. Arcs, not lines: anything travelling more than 200 px follows a curve.
6. Staggers: 1 frame per letter by default, 2–3 frames per word; never more than 4 frames in the montage.
7. No cross-dissolves between scenes (cut, wipe, match, morph, whip or flash only). Opacity fades only on secondary elements and only up to 0.2 s.
8. Fake motion blur with streaks, smears (stretch along velocity) and onion skins. No CSS blur on full-frame or 3D layers except where a scene says so.
9. At rest, snap text translation to whole pixels so it does not shimmer.
10. Linear timing only for timecode, constant spins and the end-card push-in.
11. Global FX go through R.cue and sounds through R.sfx, registered in setup, so the soundtrack and the post-FX see them. Scenes never draw their own flashes, shakes or letterbox.
12. Never draw or imitate the Anthropic/Claude logo or spark. The only mark is the "C." monogram (a gapped ring plus a dot). No emails, URLs or phone numbers.

**QA before you hand in** (from the engine README): `node tools/stills.mjs --scene sNN --count 12 --sheet` for the whole scene, and `node tools/stills.mjs --times <T−2/60>,<T+1/60> --name handoff` for both sides of each of your handoffs. Compare the rest frame against the handoff spec in this document pixel for pixel.

<a id="scores-and-provenance"></a>
## Pitch scores and provenance

| Pitch | Hook | Range & wow | Coherence | Rhythm & sync | Ending | Feasibility & handoffs | Avg |
|---|---|---|---|---|---|---|---|
| **typographer**: FULL STOP. | 8 | 9 | 9 | 8 | 9 | 7 | 8.33 |
| **one-take**: FULL STOP. One dot, one take. | 8 | 8 | 7 | 6 | 7 | 9 | 7.50 |
| **generative**: ONE PIXEL | 8 | 8 | 6 | 8 | 7 | 7 | 7.33 |
| **principles**: PIP | 7 | 8 | 8 | 7 | 9 | 6 | 7.50 |

- **typographer**: Strongest spine: one motif, a self-describing variable-type hook, the only pitch with an insider showpiece (live bezier editor) and a climax that pays off as the name. Weak spots: the first half-second is a quiet hairline word with no hit on frame 0; six of eight modules are exactly one bar long; several handoffs break on the last rendered frame (the inExpo rush reaches scale 1 only on the cut frame, so the last corridor frame shows the far wall at ~0.74 with the walls still visible; the zoom-through's corner coverage on its last frame depends on an unspecified centre ease; s01's staggered letter drop runs to 1.908, past the 1.875 handoff); the end-card numbers assume cap 220 at 1440 px, but Archivo at width 125 measures a cap of ≈185–188 at that width; s07 has to re-implement six techniques in miniature.
- **one-take**: Best handoff discipline (rest poses held two frames, flat discs and colour fields, one shared portal formula) and a good exponential dive. But 'MAKE IT MOVE' is a stock line, the drop only arrives at 9.375 (62% in), which leaves 3.75 s of climax, and the ten portal worlds (14-frame texture strobes, planet and moon, op-art) dilute the art direction into a demo. The end card finishes typing at ≈14.3 (≈0.7 s of full hold), and the '00:00:15:00' timecode can never be shown (the last frame is 14:59).
- **generative**: Spectacular 0.234 s particle burst and good musical architecture (drop on bar 5, 8th hypercuts, silent tape-stop 8th). The shared whip formula across the only overlap is excellent. But the pixel motif disappears for long stretches, the 7-card bento dashboard reads as a SaaS promo and the wireframe/terrain act as a tech demo. The monogram-first ending is conventional, and the bento and hypercut modules are over budget and duplicate other scenes.
- **principles**: The only pitch with real character acting (a cast with timing, reactions, a leapfrog) and the most memorable last beat (smear-frame slam, the name erupting from the impact, a wink). But the first 0.47 s is a ball falling with no hit; the half-time bar 5 plus a drop at 9.375 sag the middle; and the cartoon register ('SMILES PER SECOND', eyes on everything) undercuts senior polish. Several cuts hand over mid-motion (the ball at ~1200 px/s), which two engineers would have to match in velocity, not just pose; the cast and panel scenes are each over 700 lines.

| Idea | Source |
|---|---|
| Spine: the full stop as protagonist, the LIGHT/HEAVY/NARROW/WIDE axis hook, the Timing oner with animator notation, the zoom-into-the-dot into a CSS-3D type corridor, the bezier graph editor, breath then drop then particle RANGE, the C-L-A-U-D-E technique montage, the specimen-row reveal, the width-62 squeeze and width-125 release, the HUD frame with beat meter, the C. monogram tick | typographer (P1) |
| Rest-pose handoff protocol (outgoing reaches the pose at T - 2/60 and holds; incoming renders it on its first frame); exponential dive d = d0·e^(k·u) so the zoom-through reaches full coverage by a known frame; handoffs as flat discs and colour fields | one-take (P2) |
| "Every frame, on purpose." tagline | one-take (P2) and generative (P3) |
| One shared whip-pan function for the only overlap (outgoing x = -P(t), incoming x = 1920 - P(t)), so the seam is one continuous camera move; the silent tape-stop 16th before the final hit | generative (P3) |
| Centre-locked montage match cuts (the dot at the same place and size on every cut); "type takes the impact" (words flex under landings); smear frames on the final flight; the multi-bounce settle; the incoming scene owns frame ceil(60·T) | principles (P4) |
| ECD fixes: a frame-0 impact with a camera punch and the LIGHT stagger caught mid-wave; re-timed modules to 4/4/3/4/5/4/4/4 beats; every handoff re-derived so the last rendered frame is exact (2D rest-pose overrides for the 3D rush and the dive); single-handle graph-editor drag (cause and effect is legible); A drips through its own crossbar; U built as a chart with the dot at its origin; hanging-punctuation end card on the grid; all type sizes solved from Archivo metrics measured in the pipeline Chromium; FX mapped to the engine's cue vocabulary and sounds to its R.sfx vocabulary; key moved to F minor to match audio/synth.py | ECD synthesis |

<a id="open-questions"></a>
## Open questions

- The engine has no "vignette" cue yet. The four vignette cues are marked OPTIONAL and are harmlessly ignored by R.fxAt until someone adds ~10 lines (semantics given).
- CSS 3D corridor: 4200-deep preserve-3d planes may clip or seam in headless Chromium. Slab culling and the 2D rest override contain the risk; fallback is a 3000-deep corridor.
- The A drip-through is ambitious for 28 frames (converge 7, settle 7, drip 14). Fallback: the dot drips off the crossbar edge without passing through the membrane.
- Canvas text uses stretch keywords only (normal / expanded / extra-condensed = 62.5%). DOM text uses exact percentages, so canvas-sampled type (RANGE targets, halftone C) differs by <1% from DOM type. No handoff depends on canvas type.
- Key: F minor (matches audio/synth.py). The typographer and generative pitches used A minor, one-take D minor, principles F major. Note names in the sound notes are written in F minor.
- All type metrics were measured in this Chromium build with the bundled woff2 files (Archivo flat cap 0.6875 em; "CLAUDE" ink 2.9075 / 5.3525 px per px of font-size at 62.5% / 125%). Builders re-measure at setup; handoff coordinates are absolute and do not move if measurements drift.
