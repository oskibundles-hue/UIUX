# Overlay styles

Same footage, same offer, three treatments. **The footage is never re-cut or
re-ordered between variations — the overlay is the only thing that changes.**
That is what makes them comparable: whatever performs better did so because of
the overlay, not because it got a different edit.

Each source clip plays whole, in its own order, exactly as it was shot.

---

## A — HUD

The dense one. Opening title card over a scrim, then a persistent name plate
with the monogram, a bottom ticker, and spec chips landing one at a time.

Everything the offer needs is on screen and nothing waits for the caption. Best
where the offer has conditions or a price that must be read — the annual package
and the priced PPF jobs. It is also the busiest, so it fights beautiful footage.

`--title-text --title-scrim --title-block --ticker --spec ×N --none badge`

## B — Editorial

The clean one. A title card at the top, a service plate, one badge on the money
shot, and a panel CTA. No ticker, no chips, long stretches of untouched picture.

Best where the car is the argument and the offer is simple enough to say once.
It gives the footage room, which on the Roma and the Aventador is most of the
value. It cannot carry conditions — there is nowhere legible to put them.

`--title-text --title-scrim --cta-style panel`

## C — Plate

The middle. No big title card at all: a lower-third service plate names the job,
chips carry the detail, a ticker holds the conditions, bar CTA.

It opens on picture rather than on type, which is the most patient of the three
and the least like an ad. Good for organic feed where a hard title card reads as
paid.

`--none title --none badge --ticker --spec ×N`

---

## Built

| Car | Offer | Length | A | B | C |
|---|---|---|---|---|---|
| Ferrari Roma | Full car PPF, ceramic included | 25.7 s | ✓ | ✓ | ✓ |
| Ferrari SF90 | Annual service, $3,999 | 22.2 s | ✓ | ✓ | ✓ |
| Porsche GT3 RS | Windshield PPF $899, headlights free | 28.7 s | ✓ | ✓ | ✓ |
| Lamborghini Aventador S | Free ECU tune with a RYFT or Opus exhaust | 14.0 s | ✓ | ✓ | ✓ |

**Chip count follows clip length.** Four chips need roughly 22 seconds to be
readable; the Aventador at 14 s gets two.

**No corner logo on any of them.** Measured on each whole clip — the share of
frames where each colour would be lost in the bug's own rectangle:

| Clip | White fails | Black fails |
|---|---|---|
| Roma | 22.3% | 27.2% |
| SF90 | 9.0% | 23.6% |
| GT3 RS | 54.8% | 9.6% |
| Aventador | 73.2% | 12.5% |

Nothing clears the 8% bar, so the bug comes off and the monogram lives in the
title plate and the end card — the same decision the original Roma and Aventador
ads made. Style B has no title plate, so on that one the brand rests on the
title card and end card alone; that is a real trade and it is why B is the
choice for footage-led placements rather than for brand-building ones.

**No partner plate on the tune ad.** `lt_9x16_partner_ryft.png` exists and is
one flag away (`--partner ryft`), but it goes on only where a RYFT exhaust is
actually fitted. The offer is stated in type instead, which is true regardless
of what is on the car in shot.
