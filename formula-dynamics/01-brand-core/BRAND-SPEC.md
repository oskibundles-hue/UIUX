# Brand Specification

Transcribed from the official brand guide (`brand-guide-master.png`).
That image is the authority — this file is the working copy.

---

## 1. Colour palette

| Colour | Hex | RGB | Role |
|---|---|---|---|
| Red | `#FE0F13` | 254, 15, 19 | Primary accent. CTAs, key words, underlines, highlights. |
| White | `#FFFFFF` | 255, 255, 255 | Logo + headline colour on dark footage. |
| Black | `#000000` | 0, 0, 0 | Primary background. Logo colour on light footage. |
| Green | `#1DB14B` | 29, 177, 75 | Racing stripe only. |
| Yellow | `#FFDE00` | 255, 222, 0 | Racing stripe only. |

**Green and yellow are stripe colours, not brand colours.** They appear only
inside the four-colour accent stripe. Never set a headline in green, never fill
a background with yellow.

Solid 1080 × 1080 swatches for use as CapCut backgrounds: `color-swatches/`.

### The accent stripe
**Five** segments, left to right, measured off the master artwork:

| Segment | Share |
|---|---|
| Red | 36.7% |
| Black | 21.4% |
| White | 19.4% |
| Green | 17.0% |
| Yellow | 5.5% |

The stripe carries **both** a black and a white segment. Whichever one matches
the background reads as a gap — on black footage you see red / gap / white /
green / yellow; on white you see red / black / gap / green / yellow. That is
the artwork, not a rendering fault. Do not "simplify" it back to four segments.

Ready-made bars: `../03-overlays/accent-bars/`.

---

## 2. Typography

| Role | Typeface | Status |
|---|---|---|
| Headlines | **Bebas Neue** Bold Condensed | Bundled in `../07-fonts/`, free (OFL) |
| Performance / accent | **Neuropol X** | Commercial licence — not bundled |

Bebas Neue is uppercase-only by design. Set headlines in caps with slight
letter-spacing. Full notes, including what to use in CapCut when Neuropol X
isn't installed: `../07-fonts/FONTS.md`.

---

## 3. Logo

### Clear space
Keep clear space equal to **the height of the "FD" icon** on all four sides.
Nothing — text, edges, other graphics — inside that margin.

### Minimum size
| Medium | Minimum width |
|---|---|
| Print | 25 mm |
| Digital / screen | **120 px** |

On a 1080-wide video frame, 120 px is 11% of the width. The supplied logo bugs
sit at 30% width, comfortably clear.

### Variations
Primary horizontal · Compact stacked · Icon / monogram.
Which file to use when: `../02-logos/LOGO-USAGE.md`.

### Master artwork — the one rule for anyone regenerating logos

**`logo-source/fd-primary-horizontal_master.png` is the logo.** Every lockup,
PNG, overlay and end card in this kit is traced from it.

Never trace logo artwork out of `brand-guide-master.png`. That raster carries
the lockup at 596×250 px and the mark at just 149×114 px. Tracing it and
scaling up is exactly what produced the soft, round-cornered mark that shipped
in the first version of this kit — 8.7% mean error against the master, against
0.84% (the anti-aliasing floor) for a trace of the master itself.

If a new master export arrives, replace that file and re-run
`99-toolkit/build_logos.py`; it finds the mark, wordmark, stripe and
PERFORMANCE by occupancy rather than fixed pixel boxes.

---

## 4. Usage rules

**Do**
- Use approved logo files from `../02-logos/`.
- Maintain clear space.
- Use approved brand colours.
- Ensure legibility at every size.

**Don't**
- Stretch or distort the logo. *(Always scale with the aspect ratio locked —
  in CapCut, drag a corner handle, never an edge handle.)*
- Change logo colours or add effects — no glow, no drop shadow on the logo
  itself, no gradients.
- Recreate or redraw the logo.
- Place it on a busy background. Use the mono white/black version, or move it
  to a calmer part of the frame.

---

## 5. Brand values

| Value | Meaning |
|---|---|
| **Performance** | Relentless pursuit of speed and results. |
| **Precision** | Engineered with exacting accuracy. |
| **Passion** | Driven by motorsport. Fueled by passion. |
| **Quality** | Premium materials. Proven reliability. |

**Brand description** — Formula Dynamics Performance is a premium
motorsport-inspired brand built on precision, engineering excellence, and
relentless performance. We deliver advanced solutions and components for those
who demand the highest standards on and off the track. Every detail reflects our
commitment to innovation, technical mastery, and pushing the limits of what's
possible.

---

## 6. Contact

- **Web** — formuladynamicsperformance.com
- **Instagram** — @formuladynamicsperformance
- **Email** — info@formuladynamicsperformance.com

---

## 7. Machine-readable tokens

`brand-tokens.json` and `brand-tokens.css` carry the same values for use in web
projects, design tools, and scripts.
