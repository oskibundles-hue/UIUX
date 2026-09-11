---
name: vertical-ad-cut
description: "Production rules for short vertical video ads (9:16 Reels, Stories, TikTok, in-feed) — opening-hook thresholds, block structure and shot dwell, on-screen copy and label logic, claim substantiation, platform keep-out zones, and the pre-delivery QC checklist. Use this whenever the task involves cutting, reviewing, speccing, or QC-ing a vertical video ad or reel; writing on-screen copy, captions, price panels or end cards; deciding video-vs-static for a paid social placement; or checking whether a cut is safe to ship. Also use it when someone asks why an ad underperformed, where captions or overlays should sit, how long a shot should hold, or whether an on-screen number is safe to claim — even if they never say the words 'ad', 'reel' or 'playbook'."
---

# Vertical Ad Cut

Production rules for short vertical video ads. Every rule here was paid for
once — it comes from an ad that shipped, or one that had to be re-cut. Apply
them when building a cut, and cite the clause code when rejecting one, so the
person on the other end knows which rule they hit rather than feeling
second-guessed on taste.

The rules are deliberately measurable. "It feels slow" starts an argument;
"panel 3 holds 0.7 s, below the 1.0 s floor" ends one.

## When this applies

Any fixed-canvas vertical video intended for a feed: Reels, Stories, TikTok,
in-feed 9:16, Shorts. The thresholds assume a viewer holding a phone at arm's
length with the sound off, which is the condition almost all of this work is
actually consumed under.

Wide-format video, YouTube long-form and responsive web UI are out of scope —
their attention economics are different and these numbers do not transfer.

## O — The first two seconds

Most viewers see only this. Spend it on the subject, not on context.

| Code | Rule |
|---|---|
| **O-1** | Open on the subject already in motion, mid-detail — not a wide establishing shot that resolves into the subject. Frame one should already be worth looking at. |
| **O-2** | The subject fills **more than 45% of the frame at the 2.0 s mark**. |
| **O-3** | Never open on branding. No logo card, no storefront, no name plate first. |

O-2 is measurable, so measure it: pull the actual frame at 2.0 s rather than
scrubbing near it. Below that threshold the cut reads as scenery, and the
drop-off shows up in the retention curve before it shows up in anyone's
opinion.

O-3 is the one people argue with. Branding is the payoff, not the entry fee —
a viewer who does not yet care about the subject has no reason to care whose
logo it is. The name plate belongs in the second block, once the footage has
earned the attention.

## S — Structure and dwell

Five blocks, in order:

**Title → Name plate + ticker → Panels → CTA → End card**

| Code | Rule |
|---|---|
| **S-1** | The order is structural, not stylistic. Do not reorder. |
| **S-2** | Panels dwell **~2.8 s** each. |
| **S-3** | **No shot under 1.0 s.** Hard floor. |

On a 28 s cut, five panels at 2.8 s is 14 s — half the runtime in panels. That
looks wrong on a timeline and correct on a phone.

2.8 s is roughly what it takes to read a two-line caption at a heavy display
weight without pausing. So if the copy does not fit in 2.8 s, **cut the copy,
not the panel** — stretching the panel to fit long copy slows the whole cut to
protect a line that was too long to begin with.

S-3 exists because sub-second shots read as a mistake on a small screen and
wreck the caption timing underneath them. A shot worth only 0.6 s is not worth
including.

## C — On-screen copy

Most re-cuts are copy problems, not picture problems.

| Code | Rule |
|---|---|
| **C-1** | Name the service as a service — "full respray", not "paint". Write for someone who has never been to the business and is reading at arm's length with the sound off. |
| **C-2** | Anything thrown in is explicitly marked as included. An unmarked extra reads as an upsell the viewer will be billed for — marking it is the entire value of listing it. |
| **C-3** | No model or product names typed on screen. Show the badge if it is in frame; do not type it. Typing it invites a trademark argument and dates the ad the moment that unit leaves. |
| **C-4** | Panels sit on frosted glass over the footage, never a bordered box. A bordered box on moving picture is the fastest way to make a cut look like a template. |

### Label logic

Four labels that look interchangeable and are not. Picking the wrong one is a
re-cut, not a note — because each one makes a different promise about money.

| Label | Use when | Never use for |
|---|---|---|
| `SERVICE` | The line is the thing being sold — the job being booked. | An add-on, or anything with a number attached. |
| `INCLUDED` | It comes with the service at no separate charge and is a normal part of the job. | Something otherwise chargeable — that is `INCLUDED FREE`. |
| `INCLUDED FREE` | It has a standalone price elsewhere and is being given away with this booking. | Anything never chargeable. Using it there makes the whole panel read as inflated. |
| `PRICE` | A figure the customer will actually be charged, in full, no asterisk. | "From" pricing, deposits, or anything conditional on an offer window. |

The distinction that matters most is `INCLUDED` vs `INCLUDED FREE`. The second
one claims the item has real standalone value. If it does not, a viewer who
knows the category reads the whole panel as padded — and stops believing the
price too.

## V — Substantiating a number

| Code | Rule |
|---|---|
| **V-1** | Every figure on screen traces to a document — spec sheet, dyno printout, invoice, or the business's own measurement — recorded **before** approval, not after someone questions it. |
| **V-2** | A plausible number is not a sourced number. |

V-2 is the failure mode worth internalising. Figures that sound right for the
subject pass review *because* they sound right — plausibility is what makes an
unsourced number dangerous, not what makes it safe. A figure nobody queried is
not a figure anybody checked.

When a figure has no document: the panel loses the number and keeps the
picture. That is a fine outcome. Shipping the guess is not — and it is the
business, not the editor, that carries the consequence.

## P — Finishing

Four checks, run on the export at delivery resolution, not on the timeline.

| Code | Rule |
|---|---|
| **P-1** | Measure luminance banding — do not eyeball it. Banding in graded sky and flat paint is invisible on a laptop and obvious on a phone at full brightness. |
| **P-2** | Verify stills, not the scrub. Pull real frames at the marks that matter: 2.0 s for O-2, the first frame of each panel for caption fit, the end card. Scrubbing hides exactly the errors these checks exist to catch. |
| **P-3** | Captions cover **100%** of speech, measured as a percentage — not "captions are present". |
| **P-4** | Nothing that matters enters a keep-out zone. |

P-3 deserves emphasis because it fails silently. A set can pass a visual check
— captions are clearly there — while covering half the audio. Delivered sets
have measured **18%**, **51%** and **53%** coverage this way. Measure the
number; anything under 100% is unfinished.

### Keep-out zones (9:16)

The platform draws its own furniture over your frame:

| Edge | Reserve | What lives there |
|---|---|---|
| Top | **11%** | Account handle, platform header |
| Bottom | **20%** | Caption stack, audio credit, progress bar |
| Right | **16%** | Action rail — like, comment, share, profile |
| Left | **5%** | Narrow but real |

Captions, prices and the end-card lockup all sit inside the remaining safe box.
The bottom band is the deepest and the one end-card lockups keep drifting into.

## F — Format selection

| Code | Rule |
|---|---|
| **F-1** | Build the video. Measured at roughly **28× cheaper per play** than the static alternative. |
| **F-2** | Never run statics in a Reels placement. |

F-1's multiple is large enough to survive any reasonable argument about
production time: the build costs more once and less every day after. F-2
follows from it — the placement is priced for motion, so a static there pays
motion rates for a still frame. Statics have their own placements.

## Working checklist

Before calling a cut finished:

- [ ] Frame at 2.0 s pulled; subject >45% (**O-2**)
- [ ] Opens in motion, mid-detail, no branding (**O-1**, **O-3**)
- [ ] Five blocks in order (**S-1**)
- [ ] No shot under 1.0 s (**S-3**)
- [ ] Every label checked against the label-logic table (**C-2**)
- [ ] No model/product names typed on screen (**C-3**)
- [ ] Every on-screen figure has a document attached (**V-1**)
- [ ] Banding measured on the export (**P-1**)
- [ ] Caption coverage computed as a percentage, = 100% (**P-3**)
- [ ] Overlays checked against all four keep-out edges (**P-4**)

## Client-specific rules and open risks

This skill holds craft rules only. Per-client brand rules, approved-ad
references, offer expiry dates and unresolved claim risks live in that client's
own private documentation — check it before shipping, because a cut can satisfy
every clause here and still be blocked by an open claim or an expired offer.

See `references/extending.md` for how to add a client layer without putting
confidential material in this repository.
