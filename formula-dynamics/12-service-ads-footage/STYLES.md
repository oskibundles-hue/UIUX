# Overlay styles

Same footage, same offer, different treatments. **The footage is never re-cut or
re-ordered between variations — the overlay is the only thing that changes.**
Each source clip plays whole, in its own order, exactly as it was shot.

---

## The house treatment: frosted glass

`--spec-style panel`

The service words sit on **frosted glass made out of the footage itself**. That
rectangle of picture is cropped out, blurred, darkened and composited straight
back, so the car keeps moving behind the words:

```
[fc]crop=850:210:54:1104,boxblur=20:2,eq=brightness=-0.12,
    format=yuva420p,fade=t=in:alpha=1,fade=t=out:alpha=1[fg];
[fb][fg]overlay=54:1104:enable='between(t,8.1,9.4)'
```

One fixed rectangle for the whole run, so four services read as **one component
changing its contents** rather than four separate objects appearing. The only
furniture is a short red rule along the bottom edge; there is no border and no
drawn plate.

It came out of the experimental cuts and graduated because it solves the
problem the old chip had: it puts words on screen legibly without a container
that looks stuck on, because the container is part of the picture.

**The bordered chip is retired.** `--spec-style chip` still exists for old cut
sheets. Nothing new uses it — a red-outlined box over film never looks seamless,
it looks like a UI element someone pasted on.

---

## The other treatments

Kept because each is a different layout, not a restyle, and any of them can be
swapped in without touching the edit.

| Style | What it is | Where it earns its place |
|---|---|---|
| `panel` | frosted glass, words on blurred picture | **the house default** |
| `rule` | word over a red rule, low-left | quietest; when the footage should carry |
| `index` | numeral hard left, word hard right, counting 01/04 | when a run of items needs a sense of length |
| `tab` | slim red bar up the left edge, word rotated inside | leaves the whole frame clear |

---

## Copy rules learned the hard way

**A property is not a service.** "Self-healing" describes what the film does; it
is not a job the shop performs, so it does not belong in the service run. It can
sit in the ticker as a descriptor. The service run lists work.

**No model names.** These ads sell a service, and the car is already on screen.
Naming the car spends a line on something the viewer can see.

---

## Built

| Car | Offer | Length |
|---|---|---|
| Ferrari Roma | Full car PPF, ceramic included | 25.7 s |
| Ferrari SF90 | Annual service, $3,999 | 22.2 s |
| Porsche GT3 RS | Windshield PPF $899, headlights free | 28.7 s |
| Lamborghini Aventador S | Free ECU tune with a RYFT or Opus exhaust | 14.0 s |

All in `--spec-style panel`, plain and `--motion` (sound-designed).

**Chip count follows clip length.** Four items need roughly 22 seconds to be
readable; the Aventador at 14 s takes two.

**No corner logo on any of them.** Measured per whole clip — the share of frames
where each colour would be lost in the bug's own rectangle:

| Clip | White fails | Black fails |
|---|---|---|
| Roma | 22.3% | 27.2% |
| SF90 | 9.0% | 23.6% |
| GT3 RS | 54.8% | 9.6% |
| Aventador | 73.2% | 12.5% |

Nothing clears the bar, so the monogram lives in the title plate and the end
card instead.

**No partner plate on the tune ad.** `lt_9x16_partner_ryft.png` is one flag away
(`--partner ryft`) but goes on only where a RYFT exhaust is actually fitted.
