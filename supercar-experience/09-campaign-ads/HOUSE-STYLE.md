# Ad house style — approved treatments

**Read this before building an ad.** It records what the shop has actually
signed off on, so a new ad starts from a known-good treatment instead of a fresh
guess. `06-video-system/AUTO-EDIT.md` covers timing and the overlay tool; this
covers which look to reach for.

---

## Approved layouts

Two treatments are approved and **equal**. Pick per job, on the footage — not by
rule.

### `hud` — the house look

Bracketed title block bottom-left with the FD monogram inside it, ticker beneath,
left-aligned type in a mid band.

Signed off on the **McLaren 765LT** and the **Aventador S** base cut. What was
approved is the *treatment itself* — the title block, ticker and mid-band type.
It is not tied to what fills the type band: the 765LT ran an animated spec
counter and indexed callouts, the Aventador a static build sheet, and both were
fine. Fill the band with whatever the car's material supports.

### `centred` — poster treatment

Mark above the hook, everything on the vertical axis, lockup centred at the foot.

Signed off on the **Aventador S**, called "very fitting". Approved on par with
`hud`, not a fallback.

### The other two

`panel` and `rail` are built and available in `layouts.py` but have **not** been
signed off. `panel` remains the right technical answer for footage so busy or
bright that nothing else stays legible — it ignores what is underneath — so
reach for it on that basis, not on preference.

---

## Rules learned the hard way

Each of these cost a render or a rebuild. They apply to any new layout.

**Never stand the four-colour accent stripe on end.** It carries a black segment
(see `01-brand-core/BRAND-SPEC.md` §1). Horizontally on dark footage that reads
as a designed gap; vertically it reads as a broken line, like a rendering fault.
`rail` uses solid red and keeps the stripe as a horizontal cap.

**The ticker sits at `y=0.775`.** Any layout placing a lockup near there will
collide. `rail` sits at `0.688`, `centred` at `0.845`.

**Measure the footage before choosing a treatment.** Sample mean brightness in
the band each element will occupy, across the whole clip, before committing:

- 765LT: dark throughout, so type went in the upper third with light scrims.
- Aventador: top band swung 23 → 239 (blown desert sky to black interior), so
  there is **no corner logo bug** — neither white nor black survives both ends —
  and the type moved to the mid band, the stable zone at mean 59.

**No corner logo bug on footage with a wide brightness swing.** The monogram
lives inside the scrimmed title block instead. Established on the Ferrari Roma
edit, held on both ads since.

**Callouts need a shot that lasts.** A leader line anchored to the car is invalid
at the next cut. Fine on the 765LT's single locked-off take; dropped on the
Aventador, which cuts roughly every second.

**Type carries a scrim wherever the shot changes underneath it.** Same fix
`AUTO-EDIT.md` prescribes for the GT3 RS.

---

## Copy and claims

**Only put on screen what the shop can substantiate.** Both ads shipped with this
enforced:

- The 765LT's tuned column (902 HP / 701 lb-ft / 2.4 s) is **invented for
  layout** and flagged in that ad's README as replace-before-publish. Its heading
  reads "BUILD SHEET", not "DYNO VERIFIED", precisely because nothing is verified.
- The Aventador lists only confirmed work — aero kit, wheels, Stage 1 tune,
  lowered — and carries **no horsepower figures**, because there is no dyno sheet
  for that car.

A callout naming a part reads as a claim about what the shop fitted. Confirm
against the real build before publishing.

Hooks come from `05-copy-library/hooks-and-captions.md`, CTAs from
`03-overlays/cta-captions/`, grouped by intent as `fd_brand.CTA_GROUPS`
describes. `06-video-system/AUTO-EDIT.md` maps templates to CTAs.

---

## The three axes of variation

An ad folder can vary along three independent axes, all as cue files:

| Folder | Varies | Keeps |
|---|---|---|
| `layouts/` | the arrangement on the frame | cut, copy |
| `cuts/` | shot order, length, beat structure | copy, layout |
| `variants/` | hook and CTA | cut, layout, build sheet |

Keeping them separate is deliberate: a test on one axis stays interpretable.
`python3 build_ad.py --all` renders every combination present.

---

## Feedback log

| Date | Ad | Note |
|---|---|---|
| 2026-09-08 | McLaren 765LT, Aventador S base | "I love the very first video" — approved the `hud` treatment itself, independent of counters vs build sheet |
| 2026-09-08 | Aventador S, layout variations | "the third was very fitting" — `centred` approved, on par with `hud`, chosen per job |

Add a row when the shop reacts to something. This file is the reason a future ad
does not have to re-litigate a settled look.
