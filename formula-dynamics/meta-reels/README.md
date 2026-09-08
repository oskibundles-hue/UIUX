# Formula Dynamics — Meta ad reels

Five business-driven vertical reels for paid Meta placement, plus a Formula
Dynamics Instagram overlay pack. Everything here is **generated motion
graphics** — no vlog footage is used, and none of the "Anti Stock Media" cut
footage appears in any reel.

Built on the **official brand kit** — `formula-dynamics/01-brand-core/BRAND-SPEC.md`
and `brand-tokens.json` on branch `claude/formula-dynamics-ad-qpuh4m` in this
repo. Colours, type, logo artwork and safe zones are transcribed from that
spec, not inferred.

---

## The reels

All seven are **1080×1920, 30 fps, H.264 High, yuv420p, 15.0s** — Meta's
recommended Reels/Stories ad spec, and each sits well under the 4 GB cap.

| # | File | Angle | Hook | CTA |
|---|------|-------|------|-----|
| R1 | `FD-R1-Exhaust-Larini.mp4` | Exhaust / Larini | "They hear you before they see you." | Shop Exhaust |
| R2 | `FD-R2-Tuning.mp4` | ECU calibration | "Stock is a starting point." | Book a Tune |
| R3 | `FD-R3-PPF.mp4` | Paint protection film | "The paint is the expensive part." | Book PPF |
| R4 | `FD-R4-Builds.mp4` | Complete builds | "A build isn't a parts list." | Start a Build |
| R5 | `FD-R5-20-Years.mp4` | Brand authority | "20+ years. One obsession." | Shop Now |
| R6 | `FD-R6-Wheels-NVForged.mp4` | Wheels / NV Forged | "Wheels are the first thing anyone sees." | Shop Wheels |
| R7 | `FD-R7-Body-Kits.mp4` | Body kits / aero | "Aero isn't decoration." | Shop Body Kits |

R5 is the top-of-funnel/prospecting ad. The rest are service-specific and
work better for retargeting or interest-targeted sets. R1, R2, R6 and R7
cover all four `priorityServices` — exhaust, tuning, wheels and body kits.

### Built for muted autoplay, with sound design on top

Meta autoplays with sound off, so every reel carries its whole message
visually — no voiceover, nothing that depends on audio. Each reel then ships
in two versions:

- `FD-Rn-*.mp4` — picture only, no audio track.
- `FD-Rn-*-SFX.mp4` — the same picture with a sound-design bed cued to the
  motion (riser on the tach sweep, metal impact on the redline, a sub drop
  when the valve opens, a ratchet under the wheel fitment).

### The sound pack

`sfx/` holds 37 sounds in two halves.

**Recorded (11)** — curated from Kenney's CC0 libraries. Kenney releases
everything under Creative Commons Zero: public domain, no attribution
required, commercial use permitted. Sources and the reason each was picked
are in `sfx/KENNEY-SOURCES.md`.

**Designed (26)** — synthesised from scratch, original work.

The split is not arbitrary. Kenney's libraries are game assets, and most of
the 753 files (lasers, footsteps, space engines, casino chips) are wrong for
a luxury automotive ad. But their *mechanical* recordings beat synthesis
outright — the irregularity of a real object being struck is exactly what
synthesis approximates badly, so every switch, click and metal impact here
is a recording. The reverse holds for the cinematic layer: Kenney has no sub
drops, long risers or drones, so those stay designed.

Selections were made by measuring duration, peak and spectral centroid
across 71 candidates, not by filename.

Each sound is built in three layers — a transient to give the ear a point to
lock onto, a body carrying the character, and a tail setting the size of the
space. Impacts add a sub sweep underneath: phone speakers roll off below
~200 Hz, so that weight is felt through the body's harmonics rather than
heard directly.

| Group | Sounds |
|---|---|
| Impacts (designed) | `impact_deep` `impact_low` `sub_drop` |
| Impacts (recorded) | `k_impact_plate` `k_impact_plate2` `k_impact_metal` `k_impact_sub` |
| Mechanical (recorded) | `k_switch_heavy` `k_switch_mid` `k_click_tight` `k_click_low` `k_select` `k_tick_metal` `k_glass` |
| Whooshes | `whoosh_short` `whoosh_long` `whoosh_reverse` `whoosh_pass` `swish_fine` |
| Risers | `riser_air` `riser_tone` `riser_stutter` |
| UI (designed) | `click_soft` `click_hard` `tick` `thock` `switch` `ratchet` |
| Accents | `pop` `ding` `chime_low` `shimmer` `reverse_tail` |
| Texture | `drone_low` `air_bed` |

48 kHz, 16-bit stereo, peak -3 dBFS throughout. Rebuild with:

```bash
python3 tools/build_sfx.py     # the 26 designed sounds (seeded, reproducible)
python3 tools/fetch_sfx.py     # re-download Kenney's CC0 packs
python3 tools/curate_sfx.py    # re-cut the 11 picks from them
```

`fetch_sfx.py` checks each pack's page for CC0 before downloading, so a
licence change upstream surfaces as a skip rather than a silent bad grab.

**More recorded material** is available from Freesound and Pixabay, both of
which need an API key. Supply one and the same curation approach applies.

The SFX version peaks at about -3.5 dBFS with a mean near -23 dBFS, so there
is real headroom to drop a **licensed music bed** underneath without
re-cutting or clipping. Do not use Instagram's consumer music library on a
paid ad — it isn't cleared for that.

Rebuild or retime the audio with `python3 tools/build_audio.py`; the cue
lists sit at the top of that file and use the same beat times the scenes
animate to.

### Safe areas

Content is composed inside a safe band — top 250 px and bottom 420 px are
left clear for Meta's own UI (profile row, caption, CTA button). Nothing
important is ever covered.

---

## Copy that needs your sign-off

I kept every on-screen claim either to Formula Dynamics' own published bio
or to non-numeric process description. Two things to check before spending:

1. **R2 makes no power claim.** The dyno plot is drawn with unlabelled
   POWER/RPM axes and the gain shown as a shaded area — no horsepower or
   torque figure appears anywhere. If you want real numbers on screen, send
   verified dyno results and I'll add them.
2. **Service descriptions are placeholders written from your bio.** Lines
   like "Road and dyno tested", "Bumper, hood, fenders, mirrors" and
   "Reversible to stock" describe a typical shop process — confirm they
   match what Formula Dynamics actually does before these run as paid ads.

Claims taken directly from the Instagram bio and left as-is: "#1 Maserati
Specialists", "Over 20 years", "Larini Systems North American Distributor",
"Upgrades · Enhancements · Tuning".

---

## The Instagram overlay pack

`out/overlays/` — the FD equivalent of the personal overlay set, exported at
2160×3840 so it composites onto 4K footage without scaling.

| Part | Use |
|------|-----|
| `ov-bug` | Logo bug, top-left. Persistent brand mark. |
| `ov-handle` | Handle pill + link pill. |
| `ov-lower` | Lower third — service name + qualifier. |
| `ov-spec` | Build sheet / spec card. |
| `ov-end` | Full end card with CTA. |

Each ships twice: `-alpha.png` (transparent, for compositing over footage)
and `-plate.png` (on a neutral ground, so you can judge the look).

---

## Rebuilding and editing

Requires Node with `playwright-core`, Chromium, and ffmpeg (the
`imageio-ffmpeg` wheel provides a static build).

```bash
# one reel
node tools/render.js scenes/r1-exhaust.html out/FD-R1-Exhaust-Larini.mp4 30 1080 1920

# key-frame contact sheet, for checking a change without a full render
node tools/frames.js scenes/r1-exhaust.html build/r1_kf.png "1.5,4.0,9.0,13.0"

# overlay pack
node tools/build_overlays.js

# logo variants from the traced monogram
python3 tools/build_logo.py
```

### How a scene works

Each scene is one HTML file with a `frame(t)` function that is a **pure
function of time** — it rebuilds every style from `t` alone. `render.js`
seeks frame by frame and pipes PNGs into ffmpeg, so output is deterministic
and a re-render always produces an identical file.

Editing copy means editing the HTML. Retiming means changing the `S` object
at the top of the scene's script block, which holds the in/out point of each
beat:

```js
const S = { HOOK:[0.35,3.6], LAR:[4.0,8.4], SCH:[8.8,11.8], END:[12.2,15.0] };
```

`engine.js` provides the easing and entrance helpers (`riseIn`, `wipeIn`,
`typeOn`, `countTo`, `band`). To change the reel length, change `duration`
and shift `S` to match.

### The logo

The reels use the **official artwork** from `formula-dynamics/02-logos/`,
not a reconstruction:

- `brandkit/fd-icon-white.png` — icon lockup, used as the corner bug.
- `brandkit/fd-horizontal-white.png` — primary horizontal lockup, used on
  every end card.

Both are the 2000px transparent exports. Minimum digital width is 120px and
clear space is one FD-icon height on all four sides.

---

## Brand tokens

Transcribed from `BRAND-SPEC.md`. These are the five brand colours — there
are no others.

| Token | Value | Role |
|-------|-------|------|
| `--fd-red` | `#FE0F13` | Primary accent: CTAs, key words, underlines |
| `--fd-white` | `#FFFFFF` | Logo + headline on dark footage |
| `--fd-black` | `#000000` | Primary background |
| `--fd-green` | `#1DB14B` | **Accent stripe only** — never a headline or ground |
| `--fd-yellow` | `#FFDE00` | **Accent stripe only** — never a headline or ground |

Headlines **Bebas Neue** (bundled, OFL), uppercase with slight tracking.
Supporting type Barlow Condensed, body Inter. Neuropol X is the brand's
accent face but is commercially licensed and not bundled, so it is not used
here.

### The accent stripe

Five segments, measured off the master artwork: red 36.7%, black 21.4%,
white 19.4%, green 17.0%, yellow 5.5%. On the black ground the black segment
reads as a gap — that is the artwork, not a rendering fault. Never stand the
stripe on end, and never simplify it back to four segments.

Note: `brand-tokens.json` still carries the older **four**-segment stripe
(red .42 / white .24 / green .20 / yellow .14). `BRAND-SPEC.md` is the
corrected authority and is what these reels use. Worth reconciling the JSON.

### Safe zones

From `brand-tokens.json` `safeZones["9x16"]`: top 11%, bottom 20%, left 5%,
right **16%**. The right margin is wider than the left because Instagram's
action rail sits there — symmetric gutters put content under the buttons.

---

## Fit with the approved house style

`formula-dynamics/09-campaign-ads/HOUSE-STYLE.md` records what the shop has
signed off. These reels comply with it:

- **The accent stripe is only ever horizontal.** The house rule is never to
  stand it on end, because its black segment reads as a broken line
  vertically. Every stripe here is horizontal.
- **No ticker**, so the `y=0.775` collision rule doesn't bind.
- **Nothing on screen the shop can't substantiate** — the house rule that
  produced the 765LT's flagged spec column. R2 carries no power figure at all.
- The end cards are a `centred` treatment (mark above, everything on the
  vertical axis, lockup at the foot), which is signed off and equal to `hud`.

The brightness-survey rule doesn't apply yet — these are generated on a black
ground, not footage. It becomes the first step the moment product B-roll goes
in behind them.

## Service coverage and partner claims

All four `priorityServices` are now covered: exhaust (R1), tuning (R2),
wheels (R6) and body kits (R7). PPF (R3) and complete builds (R4) sit
alongside them, and R5 carries the brand. The service list is expected to
grow as the shop does, so `scenes/` is designed to take new reels without
touching the engine.

**Partner claims, confirmed 2026-09-08.** Formula Dynamics offers the full
service list, but the partner brands actually fitted in real work to date are
**NV Forged, iPE and Ryft**. That distinction drives two decisions:

- **R6 names NV Forged** and says "fitted in-house by" — a delivered
  relationship, not a catalogue one.
- **R7 names no partner at all.** None of the three delivered partners supply
  aero, so naming one there would outrun the work. Add one when that changes.
- **R1 keeps Larini**, on the Instagram bio's "Larini Systems North American
  Distributor". That is a distributorship claim and is accurate as written;
  it does not assert completed installs.

The kit's `partners` list in `brand-tokens.json` omits Larini. Worth adding
so the two sources agree.

The kit's official service sublines, for any future reel:

| Service | Subline |
|---|---|
| Tuning | ECU & TCU CALIBRATION |
| Exhaust | VALVETRONIC & CATBACK SYSTEMS |
| Wheels | FORGED WHEEL FITMENT |
| Body kits | AERO & CARBON FIBRE |
| PPF | PAINT PROTECTION FILM |
