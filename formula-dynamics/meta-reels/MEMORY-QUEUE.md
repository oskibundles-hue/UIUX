# Queued for Vertiso Memory

Approved for saving on 2026-09-08, but the memory write allowance was already
at 20/20 for the month. **Save these when the allowance resets on 1 October**
(or sooner if the plan is upgraded). Written here so nothing is lost.

---

## 1. Formula Dynamics brand spec — authoritative values
*Type: constraint · importance: high · tags: formula-dynamics, brand, design*

**Authority:** `formula-dynamics/01-brand-core/BRAND-SPEC.md` and
`brand-tokens.json`, on branch `claude/formula-dynamics-ad-qpuh4m` in
`oskibundles-hue/UIUX`. Read that file — do not work from recalled hex values.

The five brand colours (there are no others):

| Colour | Hex | Role |
|---|---|---|
| Red | `#FE0F13` | Primary accent — CTAs, key words, underlines |
| White | `#FFFFFF` | Logo + headline on dark footage |
| Black | `#000000` | Primary background |
| Green | `#1DB14B` | **Accent stripe only** — never a headline or ground |
| Yellow | `#FFDE00` | **Accent stripe only** — never a headline or ground |

Type: **Bebas Neue** (bundled, OFL) for headlines, uppercase with slight
tracking. Neuropol X is the accent face but is commercially licensed and not
bundled.

Accent stripe: **five** segments — red 36.7%, black 21.4%, white 19.4%,
green 17.0%, yellow 5.5%. On a black ground the black segment reads as a gap;
that is the artwork. Never stand it on end, never simplify to four.
`brand-tokens.json` still carries an older four-segment version — BRAND-SPEC.md
is the corrected authority.

9×16 safe zones: top 11%, bottom 20%, left 5%, right **16%**. The right margin
is wider because Instagram's action rail sits there.

Logo: official artwork in `formula-dynamics/02-logos/png-transparent/`. The
mark is the FD monogram with the accent stripe *underneath* it. Minimum digital
width 120 px, clear space one FD-icon height.

---

## 2. Lesson: the vlog palette is not the Formula Dynamics palette
*Type: lesson · tags: formula-dynamics, brand*

On 2026-09-08 a whole set of reels was built on `#DE1A22` red, `#FBD101` gold
and Anton — then rebuilt from scratch when the real spec surfaced.

**Why it happened:** those values are the **Anti Stock Media / vlog** palette
(they appear in the "Anti Stock Downloads" artifact's own CSS and in the vlog
caption spec, where they are correct). They are not Formula Dynamics' brand
colours. Recall surfaced them next to Formula Dynamics context and they were
taken as the brand palette without checking a spec file.

Compounding it: the earlier FD ad session's cue sheet records beat 01 as
"invented palette — wrong" and beat 02 as "found the real brand kit in git".
The memory carried forward the discarded first pass.

**The rule:** two brands are in play — Formula Dynamics (client) and Anti Stock
Media / the personal vlog. Their palettes differ. Before any FD design work,
open `BRAND-SPEC.md` on `claude/formula-dynamics-ad-qpuh4m`. A hex value
recalled from memory is a hint, never an authority.

---

## 3. Partner status — offered vs delivered
*Type: observation · tags: formula-dynamics, partners*

Confirmed by Omarie 2026-09-08: Formula Dynamics offers the full service list,
but the partner brands actually **fitted in real work to date** are **NV Forged,
iPE and Ryft**.

Larini appears in the Instagram bio as "Larini Systems North American
Distributor" — that is a distributorship claim and is accurate as written, but
it does not assert completed installs. `brand-tokens.json` omits Larini from
its `partners` list; the two sources should be reconciled.

Consequence for ad copy: name a partner only where the work supports it. The
wheels reel names NV Forged ("fitted in-house by"); the body-kits reel names no
partner, because none of the three delivered partners supply aero.

---

## 4. Fast Cut beats Vlog Cut by a wide margin
*Type: observation · tags: formula-dynamics, content-strategy*

From the "Anti Stock Downloads" artifact, comparing the same source material
cut two ways:

- **Fast Cut** (MR1–MR8, ~55 s): scored **85–97**
- **Vlog Cut** (VR1–VR8, ~90 s): scored **58–73**

Same footage, same grade, same captions — the difference is length and pacing.
Shorter and tighter wins decisively. This is why the Meta ad reels are cut at
15 s, and it is worth applying to organic posting too.
