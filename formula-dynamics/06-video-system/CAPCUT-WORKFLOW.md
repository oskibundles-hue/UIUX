# CapCut Workflow

A repeatable build order. Follow it and every video comes out on-brand without
thinking about it.

---

## One-time setup

1. **Import the kit once.** In CapCut, `Media → Import` and select these folders:
   - `03-overlays/corner-logo-bugs/` (just the canvas you use, e.g. `9x16`)
   - `03-overlays/lower-thirds/`
   - `03-overlays/title-cards/`
   - `03-overlays/end-cards/`
   - `03-overlays/accent-bars/`
   - `03-overlays/service-badges/`

   Desktop CapCut keeps them in the project media pool. On mobile, save the
   PNGs to your camera roll in an album called **FD Brand**.

2. **Install Bebas Neue** so on-the-fly text matches the kit.
   File: `07-fonts/BebasNeue-Regular.ttf`. See `07-fonts/FONTS.md`.

3. **Set the canvas ratio *before* you add overlays** — `Ratio → 9:16`.
   Overlays only land in position if the canvas matches their filename.

---

## Build order

Work top-down. Each step is a new track above the last.

| # | Track | What goes on it |
|---|---|---|
| 1 | Footage | Rough cut. Get the timing right before any graphics. |
| 2 | Title card | First 1–2 s. `title-cards/` |
| 3 | Logo bug | Full duration. `corner-logo-bugs/` |
| 4 | Lower third | 1–2 s in, hold 3–4 s. `lower-thirds/` |
| 5 | Badges / stats | On the feature shots. `service-badges/` |
| 6 | End card | Last 1.5–2.5 s. `end-cards/` |
| 7 | Audio | Music, engine audio, VO |
| 8 | Captions | Auto-captions, restyled (see below) |

**Cut the picture first.** Adding graphics before the edit is locked means
redoing them.

---

## Adding an overlay

1. Drag the PNG from Media onto a track **above** the video.
2. **Do not resize it.** It is already frame-size and positioned.
3. Drag its ends to set duration.

If an overlay looks wrong-sized, the canvas ratio doesn't match the filename.
Fix the ratio — don't scale the overlay.

---

## Animating overlays

Keep it fast and mechanical. Motorsport, not wedding video.

| Element | In | Out |
|---|---|---|
| Title card | Scale 105% → 100% over 8 frames + fade | Fade 4 frames |
| Logo bug | Fade in over 6 frames | Hold to end |
| Lower third | Slide from left over 8 frames | Slide out or fade |
| Badge | Pop: scale 90% → 100% over 5 frames | Fade |
| End card | Cut straight in, no fade | — |

In CapCut: select the clip, open **Animation → In/Out**, or set keyframes on
Scale/Position/Opacity. `Zoom In` and `Rise` are the closest built-ins.

**Transition between clips:** drop `accent-bars/fd-accent-stripe_1080w-bold.png`
on the cut and keyframe its X position across the frame over 6–10 frames.

---

## Captions

Auto-captions, then restyle:

- **Font** — Bebas Neue
- **Colour** — white, with black outline or a subtle shadow
- **Emphasis** — key word in red `#FE0F13` (part number, horsepower figure,
  price, the payoff word)
- **Position** — above the bottom keep-out zone; check against
  `04-templates/safe-zone-guides/safe-zones_9x16.png`

Don't outline in red or fill body text in red. Red is for emphasis only.

---

## Checking your framing

Drag `04-templates/safe-zone-guides/safe-zones_9x16.png` onto the **top**
track while editing.

- **Red bands** — platform UI will cover this. No logos, no text, no faces.
- **White lines** — thirds grid.
- **Green cross** — exact centre.

**Hide or delete that layer before exporting.**

---

## Common mistakes

| Symptom | Cause | Fix |
|---|---|---|
| Logo in a different spot each video | Overlay was manually scaled/moved | Re-add the bug, don't touch it |
| Logo looks stretched | Dragged an edge handle | Undo; drag a **corner** handle |
| Text cut off on TikTok | Sat inside the keep-out zone | Check the safe-zone guide |
| Overlay too small / letterboxed | Canvas ratio ≠ file canvas | Set ratio first, re-add |
| Logo invisible on light footage | Used `-white` on white | Use the `-black` bug |
| Logo lost on busy paint | Full-colour on a detailed panel | Use `mono-white` / `mono-black` |
