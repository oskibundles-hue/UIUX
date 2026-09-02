# Auto-Edit — burning the overlays into a clip

`99-toolkit/build_edit.py` takes a cut clip and renders a finished, on-brand
video: title card, logo bug, service plate, feature badge, one CTA, end card —
timed, animated and positioned automatically.

**It does not cut your footage.** Feed it a clip you've already edited to
length. It adds the graphics layer, which is the repetitive part.

---

## Use

```bash
cd 99-toolkit
pip install imageio-ffmpeg           # only if ffmpeg isn't already installed

# See the timing without rendering anything
python3 build_edit.py clip.mp4 --template reveal --dry-run

# Render it
python3 build_edit.py clip.mp4 --template reveal -o finished.mp4
```

Aspect ratio and frame rate are read from your clip and matched automatically.

---

## Templates

One per shot formula in `SHOT-LISTS.md`. Each picks the title, service plate,
badge and CTA that suit that kind of video.

| `--template` | For | CTA it uses |
|---|---|---|
| `reveal` | Body kits / aero | BOOK YOUR BUILD |
| `sound-check` | Exhaust | DM FOR PRICING |
| `fitment` | Wheels | SEE WHAT FITS YOUR CAR |
| `dyno` | Tuning | BOOK NOW |
| `before-after` | Any service | WHAT WOULD YOU FIT NEXT? |
| `install-day` | Timelapse | NOW BOOKING |
| `service` | Maintenance | WE SERVICE WHAT WE BUILD |

---

## Options

| Flag | Does |
|---|---|
| `--tone light` | Black graphics, for bright footage (default is `dark`) |
| `--cta-style panel` | Black CTA panel instead of the red bar — **use on red cars** |
| `--bug top-right` | Move the logo bug |
| `--cta get-a-quote` | Swap any single element |
| `--title` `--service` `--badge` | Same, for the other slots |
| `--none badge` | Drop a slot entirely (repeatable) |
| `--bitrate 25M` | Override the 20 Mbps default |

```bash
# Red Ferrari, exhaust clip, quote CTA instead of the default
python3 build_edit.py ferrari.mp4 -t sound-check --cta-style panel --cta get-a-quote
```

---

## How the timing is decided

Beats are proportional to clip length with absolute limits, so a 15-second clip
and a 45-second clip both come out paced correctly.

| Element | Timing | Why |
|---|---|---|
| Title card | In at 0.4 s, ~2.5 s long | The hook. Fixed length — a hook is a hook at any duration. |
| Logo bug | 0.6 s → end card | Off before the end card, which already carries the logo. |
| Lower third | ~14% in, ~4 s | Names the service while they're still watching. |
| Badge | ~46% in, ~3 s | The payoff shot. |
| CTA | Ends 1 s before the end card | **On the payoff, not the last frame** — most viewers leave before the end. |
| End card | Last 2–3 s, hard cut | It's the closing shot, not a graphic. |

**The gap between the CTA and the end card is deliberate.** Two asks on screen
at once is zero asks. If a clip is too short to fit both cleanly, the CTA is
dropped automatically rather than crowded in.

Animation: fades throughout, a short slide-in on the lower third, and a hard
cut for the end card.

---

## Notes

- Rendering is roughly 4× realtime — a 20-second clip takes about 90 seconds.
  Every overlay is a full-frame layer, which is what makes placement exact.
- Output is H.264, 20 Mbps, `+faststart`, audio passed through as 320k AAC —
  matching `EXPORT-SPECS.md`.
- Prefer CapCut? Use `--dry-run` and read the cue sheet as your build order.
  The timings transfer directly.

---

## Worked example — Porsche GT3 RS (white)

A five-service build on fast-cut footage. The command that produced it:

```bash
python3 build_edit.py GT3RS.mov -t sound-check \
  --title-text "GT3 RS|BUILD" --title-tone dark --title-scrim \
  --partner ipe --none badge \
  --spec "IPE EXHAUST" --spec "STAGE 2 TUNE" --spec "PPF" \
  --spec "CERAMIC TINT" --spec "CERAMIC COATING" \
  --badge-tone dark --bug-tone light --endcard-tone dark \
  --cta book-your-build --cta-style bar \
  -o GT3RS_FD.mp4
```

**Why each choice**, since the same reasoning applies to any car:

- **`--bug-tone light` (black logo).** Measured the logo-bug corner across ten
  frames: mean brightness 170/255, peaking at 232 — it's sky in most shots. A
  white logo would have disappeared.
- **`--title-tone dark` (white type).** The title window is the *opposite*: the
  opening shots are dark road and a black tachometer, mean 72. This is why tone
  is per-element rather than one global setting — real footage is rarely
  uniformly bright or dark.
- **`--title-scrim`.** Shot detection showed cuts roughly every second. No ink
  colour survives sky, dark concrete *and* a yellow tach face, so the title
  needs a soft band under it. Without it, the red "BUILD" landed on the yellow
  dial — the weakest colour pairing in the whole clip.
- **`--partner ipe`.** iPE is a partner, so the exhaust gets the full plate
  rather than a chip. Partner plates earn the reshare.
- **`--spec`, five of them.** A multi-service build earns a rundown. Chips are
  opaque, so they stay legible as the shots change underneath.
- **`--cta book-your-build`.** A finished five-service build is peak desire.
- **`--endcard-tone dark`.** The footage is bright and airy throughout; closing
  on black is deliberate contrast and reads as a brand stamp.

**Finding the numbers yourself:** sample frames with ffmpeg and measure the mean
brightness of the zone each overlay occupies. Guessing from the thumbnail is how
you end up with a white logo on a white sky.

---

## Worked example 2 — Ferrari SF90 Stradale (gold)

Same tool, opposite answers, because the footage is the opposite.

```bash
python3 build_edit.py SF90.mp4 -t reveal --service ppf --none badge \
  --title-text "SF90 STRADALE|BUILD" --title-tone dark --title-scrim \
  --spec "CUSTOM WHEELS" --spec "LOWERED" \
  --spec "UPGRADED EXHAUST" --spec "STAGE 2 TUNE" \
  --badge-tone light --bug-tone dark --endcard-tone dark \
  --cta book-your-build --cta-style bar -o SF90_FD.mp4
```

| | GT3 RS (white) | SF90 (gold) |
|---|---|---|
| Logo-bug zone brightness | 170 (sky) | 115, range 2–198 |
| Logo colour | **black** | **white** |
| Spec chips | dark | **light** |

The GT3's frame is bright almost everywhere, so a black logo was safe. The
SF90 opens on dark interior shots — a black logo vanished completely there,
while white stayed legible on both those and the blue sky. Chips flipped the
same way: white chips separate from gold bodywork and dark tarmac, where the
dark chips used on the white car would have sunk into the road.

**Test before you commit.** Composite the overlay onto the darkest and
brightest frames it will cover and look at them side by side. It takes a
minute and costs nothing, versus a full render.

Two assumptions that did *not* survive testing here, both worth checking
rather than reasoning about:

- The red CTA bar looked like it would clash with gold paint. It didn't —
  saturated red separates cleanly from muted bronze, and it carries more
  urgency than the black panel. Kept the bar.
- The `--spec` spacing had a real bug on short clips: the minimum hold was
  applied before the slot width, so on a 22 s clip with four chips the hold
  (1.6 s) exceeded the slot (1.35 s) and two chips would have been on screen
  at once. Hold is now clamped to the slot.

---

## The HUD look — annotation callouts, title block, ticker

A second visual system, for spec-annotation style edits: indexed leader lines
that point at parts of the car, a persistent name plate, and a bottom ticker.
Built in `99-toolkit/fd_hud.py`, all in the brand palette and Bebas Neue.

```bash
python3 build_edit.py ROMA.mov -t reveal --none badge --none title --none bug \
  --title-block "FERRARI ROMA|2024 BUILD" \
  --ticker "FORMULA DYNAMICS|ROMA|PERFORMANCE" \
  --callout "001|QUAD EXHAUST|0.40,0.80|11.0|12.4" \
  --callout "002|WHEELS|0.84,0.66|17.0|18.05" \
  --endcard-tone dark --cta book-your-build --cta-style panel \
  -o ROMA_FD.mp4
```

### Components

| Component | What it is |
|---|---|
| **Title block** | Name plate with the FD monogram in a bracket, subline, accent stripe, on a soft scrim. Replaces the big title card and the lower third. |
| **Ticker** | Full-width strip of short segments split by red slashes. |
| **Callout** | Open square on the feature, elbow leader line, indexed red number plus white label with a red rule under it. |

### Placing a callout

`--callout "IDX|LABEL|x,y|start|end"` — `x,y` are fractions of the frame.

Direction is automatic: the label runs **toward frame centre** so it never
falls off the edge, and the elbow routes **upward** when the anchor is low
(`y > 0.58`) so the line clears the title block.

**Anchor on a still moment.** Grid a frame from the middle of the shot, read
the fractions off it, and keep the callout short. The first attempt here put
the wheel callout at `0.61,0.66`, which was correct for the frame that was
gridded but landed on the front splitter once the car moved through the shot.

### Two layout rules the tool enforces

- **The title block and ticker clear the frame before the CTA.** All three
  occupy the same lower band; stacking them would put three things in one
  place. The HUD fades out about 1.6 s before the ask.
- **The top logo bug is dropped on this look** (`--none bug`). On footage that
  swings from near-black interiors to blown-out sky, neither a white nor a
  black corner logo survives — tested both on the extremes and each failed at
  one end. The FD monogram lives inside the scrimmed title block instead,
  where it is legible on every shot.
