# Formula Dynamics — Meta ad reels

Five business-driven vertical reels for paid Meta placement, plus a Formula
Dynamics Instagram overlay pack. Everything here is **generated motion
graphics** — no vlog footage is used, and none of the "Anti Stock Media" cut
footage appears in any reel.

Built on the brand language established in the earlier ad session: FD red
`#DE1A22`, gold `#FBD101`, Anton headline type, and the 5-segment stripe.

---

## The reels

All five are **1080×1920, 30 fps, H.264 High, yuv420p, 15.0s** — Meta's
recommended Reels/Stories ad spec, and each sits well under the 4 GB cap.

| # | File | Angle | Hook | CTA |
|---|------|-------|------|-----|
| R1 | `FD-R1-Exhaust-Larini.mp4` | Exhaust / Larini | "They hear you before they see you." | Shop Exhaust |
| R2 | `FD-R2-Tuning.mp4` | ECU calibration | "Stock is a starting point." | Book a Tune |
| R3 | `FD-R3-PPF.mp4` | Paint protection film | "The paint is the expensive part." | Book PPF |
| R4 | `FD-R4-Builds.mp4` | Complete builds | "A build isn't a parts list." | Start a Build |
| R5 | `FD-R5-20-Years.mp4` | Brand authority | "20+ years. One obsession." | Shop Now |

R5 is the top-of-funnel/prospecting ad. R1–R4 are service-specific and work
better for retargeting or interest-targeted sets.

### Built for muted autoplay

Meta autoplays with sound off, so every reel carries its whole message
visually — there is no voiceover and no audio track at all. That is
deliberate, not an omission: you can drop a licensed music bed on in Ads
Manager or your editor without re-cutting anything, and the reels read
correctly if the viewer never unmutes.

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

`logo/fd_mark.svg` is a true vector rebuild of the Formula Dynamics mark —
the monogram traced from the official profile image, the tachometer arc
(green → yellow → red) redrawn as real geometry so it stays crisp at any
size. Variants: `fd_mark_dark` (for light grounds), `fd_mark_flat_white` and
`fd_mark_flat_ink` (monogram only, no disc).

---

## Brand tokens

| Token | Value | Use |
|-------|-------|-----|
| `--fd-red` | `#DE1A22` | Bars, underlines, wipes, CTA |
| `--fd-gold` | `#FBD101` | Highlights, valve accent |
| `--ink` | `#0C0F14` | Ground — matches the IG dark theme |
| `--tach-green` | `#57B752` | Tach arc, sampled from the mark |
| `--tach-yellow` | `#F9FC68` | Tach arc |
| `--tach-red` | `#E4362B` | Tach arc / redline |

Headlines Anton (scaleX .94), supporting type Barlow Condensed, body Inter.
