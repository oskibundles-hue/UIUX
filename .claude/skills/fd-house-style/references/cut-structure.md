# Cut structure

## The three shape rules

These show up as shapes on a cue sheet rather than as opinions:

1. **The hook clears before the HUD arrives.**
2. **The HUD clears before the ask.**
3. **The CTA never touches the end card.**

The gap between the CTA bar and the end card is deliberate — a full second of clean footage so
the ask lands on its own before contact details replace it.

**Two asks in one frame is zero asks.**

## Lane vocabulary

| Lane | What sits in it |
|---|---|
| HOOK | Opening line, 1.8–3.0 s, clears early |
| BUG | Logo bug, top corner; can run most of the clip, stops where the end card takes over branding |
| PLATE | Partner plate — a full plate, not a chip |
| SPEC | Spec chips, rundown of services |
| HUD | Title block + ticker (the telemetry look) |
| CALLOUT | Numbered pointers at real parts of the car |
| CTA | The single ask |
| END | End card |

## Reference timings

Read straight from `build_edit.py --dry-run`. Three worked examples:

**Porsche GT3 RS — 28.8 s, `sound-check` template, black bug / white title**
Five services, so the specs run as a chip rundown. iPE takes a full partner plate.

- Hook 0.40 → 3.00
- Bug 0.60 → 25.86
- Partner plate 4.02 → 8.02
- Five spec chips 8.52 → 20.17
- CTA 20.86 → 24.86
- End card 25.86 → 28.78

**Ferrari SF90 Stradale — 22.3 s, `reveal` template, white HUD / no top logo**
The hook holds 1.8 s, then the title block takes over — the two never share the lower band.

- Hook 0.40 → 2.20
- HUD 2.60 → 14.41
- Five callouts 2.50 → 14.40
- CTA 15.01 → 19.01
- End card 20.01 → 22.28

**Ferrari Roma — 25.7 s, `reveal` template, white HUD / no top logo**
Same treatment, longer runway. The HUD clears 0.6 s before the ask.

- Hook 0.40 → 3.00
- HUD 3.40 → 17.52
- Five callouts 4.20 → 18.05
- CTA 18.12 → 22.12
- End card 23.12 → 25.74

## HUD components

Built in `fd_hud.py` as three composable pieces.

| Component | Draws | Placement |
|---|---|---|
| `callout()` | Open square on the feature, elbow leader line, red index number, white label over a red rule | Side and drop derive from the anchor — the leader goes right if the anchor sits left of centre, and rises if the anchor sits low |
| `title_block()` | Bracket carrying the FD monogram, scrim, name, subline, accent stripe | `y = 0.705` by default, clear of the platform caption band |
| `ticker()` | Spec segments split by red slash marks | `y = 0.845` |

## Spec chip timing

Chips overlap on short clips unless the hold is clamped:

```
hold = min(2.8, max(1.0, slot × 0.8), slot − 0.2)
```

## Pipeline

1. **Detect the cuts.** `ffmpeg select='gt(scene,0.28)'` finds shot boundaries, so graphics land
   on a cut rather than halfway through a pan.
2. **Sample the zones.** Luminance mean *and range* under each graphic's box across the whole
   clip. Tone is decided here, before anything is drawn.
3. **Read the anchors off full-size frames.** Colour mask to isolate the car. Never off
   contact-sheet thumbnails.
4. **Compose the overlays.** Full-frame PNG at the exact canvas size.
5. **Verify a still.** Composite one frame per cue and look at it.
6. **Burn and export.** Stills must be fed as `-loop 1 -framerate N -t D` or fades do nothing.

## Getting volume without making one more ad

Three axes combine; they are not a queue.

| Axis | Options | Driven by |
|---|---|---|
| Layout | 4 — where type, HUD and bug sit | `layouts.py` |
| Cut | Shot order and duration | `recut.py` + `shots.json` |
| Variant | Tone, copy, CTA group, spec chips | `cue.json` |

Every result is reproducible from a shot list rather than from a timeline someone remembers.
