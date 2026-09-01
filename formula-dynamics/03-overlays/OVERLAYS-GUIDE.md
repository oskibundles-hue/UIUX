# Overlays — the drag-and-drop layer

Everything here is a transparent PNG built to sit **on top of footage**.
Full-frame overlays are rendered at exact canvas size, so they land in position
with no scaling.

---

## `corner-logo-bugs/` — your logo on every video

`bug_{canvas}_{position}_{type}-{tone}.png`

Example: `bug_9x16_top-left_logo-white.png`

- **canvas** — `9x16` · `4x5` · `1x1` · `16x9`
- **position** — `top-left` · `top-center` · `top-right` · `bottom-left`
- **type** — `logo` (full horizontal lockup) · `monogram` (bare FD mark)
- **tone** — `white` (dark footage) · `black` (light footage)

Positions already clear the platform UI: nothing sits under the TikTok caption
block or the like/share rail. **Pick one position and use it on every video** —
that consistency is what makes a brand look established.

---

## `lower-thirds/` — name the service or partner

`lt_{canvas}_{kind}_{name}.png` — available in `9x16` and `16x9`.

- `lt_9x16_service_exhaust.png` — service name + descriptor
- `lt_9x16_partner_ipe.png` — "OFFICIAL PARTNER" plate
- `lt_9x16_cta_book-your-build.png` — call to action
- `lt_9x16_cta_follow.png` — follow prompt

Sits above the bottom keep-out zone so the caption never covers it.
Bring it in around 1–2 s, hold 3–4 s, out. Slide from the left or a quick fade.

---

## `title-cards/` — open the video

`title_{canvas}_{name}_{tone}.png`

Two stacked lines: white (or black) on top, red italic beneath, split by the
accent stripe. Soft shadow keeps it readable over footage — no grey box.

Available: `body-kits` · `exhaust` · `wheels` · `tuning` · `before-after` ·
`install-day` · `sound-check` · `dyno-results` · `the-build` · `full-send`

`tone`: `dark` = white top line for dark footage · `light` = black top line for
bright footage.

---

## `end-cards/` — close the video

`endcard_{canvas}_{tone}.png`

Full-frame, **not transparent** — a finished last shot. Logo, tagline, website,
Instagram. Hold for 1.5–2.5 s. Long enough to read, short enough not to lose
the viewer before the loop.

---

## `service-badges/` — chips for feature callouts

`badge_{service}_{dark|light}.png` — one chip per service, red outline.

`badge-strip_lead-services_{dark|light}.png` — body kits, exhaust, wheels and
tuning in a single row, matching the campaign posters.

Use `dark` on dark footage, `light` on bright footage.

---

## `accent-bars/` — the racing stripe

`fd-accent-stripe_{width}w-{thin|bold}.png` — four-colour stripe
`fd-red-bar_{width}w-{thin|bold}.png` — solid red

Widths 1080, 1920 and 2160. Uses: underline a title, divide a split screen,
wipe across a cut, or bracket a stat.

A stripe **animating across the frame** is the cheapest on-brand transition you
can make: drop the bar in, keyframe its position left-to-right over 6–10 frames.
