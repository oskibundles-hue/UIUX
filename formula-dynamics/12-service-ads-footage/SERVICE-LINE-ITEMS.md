# Service line items — needs the shop's tick

**These were written by me, not supplied by the shop.** On 10 Sept the shop said
to add detail and to make it up, so I did: standard line items a performance
shop of this kind would normally perform. They are plausible. They are not
verified.

That matters because **an on-screen line item is a promise at the counter.**
One wrong entry is a customer arguing with the service writer while holding up
their phone. Read the list, cross off anything the shop does not actually do,
and these get re-rendered in one pass — a single word each.

Until then this file is the record of what is asserted and on whose authority.

---

## Oil service · $1,199 · Ferrari 296

### Video ad

| On screen | Verified? |
|---|---|
| Oil and filter | ☐ |
| Multi-point inspection | ☐ |
| Fluids topped off | ☐ |
| Oil, not just labor *(ticker)* | ✅ shop's own correction, 9 Sept |

### Poster — layout J approved 22 Sept, photography rejected

| On screen | Verified? |
|---|---|
| Oil & filter — replaced | ☐ |
| Multi-point inspection | ☐ |
| Fluids — topped off | ☐ |
| Oil service **from** $1,199 | ✅ "from" is accurate |
| The oil is included | ✅ shop's own correction, 9 Sept |

**The layout is approved; the pictures are not, and neither are three of these
claims.** All fifteen renders are built on brake photography, which the shop
rejected on 22 Sept: a wheel and a caliper above the words OIL SERVICE tells
the customer the wrong story. The crop was given a second aim that hunts panel
and paint instead of spokes, which fixed eight of the fifteen; eight is not a
set, and `DSC07650` is a caliper edge to edge with nothing else in frame to
find. **Nothing in `/Portfolio/10 Oil Service Ads/` is cleared to post.**

What unblocks it: an engine bay, an oil fill cap, a drain plug, a car on the
lift, oil pouring, a tech at the bay. The template does not change - new frames
drop into `build_service_posters.py oil --cars` and the set re-renders.

**The vlog footage is a source of exactly those frames** (Omarie, 22 Sept).
`/NQ Studio/raw footage/2026-09-03/23-40-46 black car on the lift.mov` is a car
raised on the lift with no brake hardware in frame, and the 09-09 day is
indexed as "shop work, blue car on the lift". Two things make this better than
shooting stills: the clips are already 2160x3840 vertical, so a poster is a
straight 2:1 downscale with no crop to aim, and the shop already owns them.

One defect measured before anything is cut from it: these are night garage
frames, a black car under hard point lights, and the scrim solves on mean
luminance. The mean lands on target (29-52 against a target of 40) while the
brightest 3% reaches 179-222, against 80-123 for the stills library. Fine print
disappears into a tail light and lens flares land on the phone number. The
scrim has to solve on the bright tail before any of this footage ships.

## Brake service · $499 · Porsche 911 GT3 RS

### Video ad

| On screen | Verified? |
|---|---|
| Rotors inspected | ☐ |
| Fluid flushed and bled | ☐ |
| Calipers cleaned | ☐ |
| Parts sold separately *(ticker)* | ✅ shop's own wording, 14 Sept |

### Poster — layout J, approved 14 Sept

The poster carries five lines where the video carries three. Four of the five
are still the writer's wording, not the lane's.

| On screen | Verified? |
|---|---|
| Rotors — inspected & measured | ☐ |
| Brake fluid — flushed & bled | ☐ |
| Calipers — cleaned & checked | ☐ |
| Pads — factory & performance | ✅ from formuladynamics.com, "Brake Upgrades" |
| Full safety inspection | ☐ |
| Brake service **from** $499 | ✅ "from" is accurate — parts are extra |
| Parts sold separately | ✅ shop's own wording, 14 Sept — replaced "pads", which under-declared it |

**The design is approved; four of these claims are not.** Approval of the
layout is not verification of the copy, and the four boxes above still want a
minute with whoever runs the lane.

## Suspension · Ferrari Roma

| On screen | Verified? |
|---|---|
| Ride height set | ☐ |
| Bushings checked | ☐ |
| Four-wheel alignment | ☐ |
| In the annual package *(ticker)* | ✅ from the specials list |

## Diagnostics · $499 · Mansory Urus

| On screen | Verified? |
|---|---|
| Full ECU scan | ☐ |
| Written report | ☐ |
| Two in the annual package *(ticker)* | ✅ from the specials list |

## Full car PPF · Ferrari Roma

| On screen | Verified? |
|---|---|
| Exterior ceramic coating | ✅ from the specials list |
| Interior ceramic coating | ✅ from the specials list |
| Every painted panel | ☐ |
| Edges and jambs wrapped | ☐ |
| Self-healing film *(ticker)* | ✅ a property of the film, not a service |

## Windshield PPF · $899 · Porsche 911 GT3 RS

| On screen | Verified? |
|---|---|
| Headlight PPF, free | ✅ from the specials list |
| Rock chip protection | ☐ |
| Edge-to-edge coverage | ☐ |
| Optical clarity *(ticker)* | ☐ |

## Free ECU tune · Ferrari Roma

| On screen | Verified? |
|---|---|
| RYFT titanium, fitted here | ✅ shop confirmed the Roma's fitment |
| Custom calibration | ☐ |
| Road tested | ☐ |
| With a RYFT or Opus exhaust | ✅ from the specials list |

## Custom gradient PPF · Mansory Urus

| On screen | Verified? |
|---|---|
| Color matched to you | ☐ |
| Every panel wrapped | ☐ |
| Ceramic coating | ✅ pattern of the PPF offers |

---

## The rule this sits under

`COPY-RULES.md` §5 says claims need a source, and that still stands as the
default. This file is the documented exception: the shop asked for invented
detail with its eyes open, and everything invented is listed here rather than
scattered through render commands where it would quietly become fact.

**Nothing in the ☐ column should be treated as something the shop has said.**
