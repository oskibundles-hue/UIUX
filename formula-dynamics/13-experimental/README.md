# Experimental

Kept apart from the house ads on purpose. These borrow devices off the dealer
templates and test whether they survive contact with the brand. Nothing here is
approved for spend; it exists to be looked at and argued with.

Nothing is traced from the templates — every element is generated from the
brand kit.

## EXP-1 — Glass panels · SF90 · 22.2 s

From the BMW dealer template: twin figure panels, a staged build, a fine-print
line, and the circular swipe affordance.

The model name has since been dropped from the house ads - these sell a service,
not a car, and the car is already on screen.

**The panels are real frosted glass, not flat plates.** Each panel's rectangle
is cropped out of the picture, blurred and darkened, then composited back in
place, so the car keeps moving behind the glass exactly as it does in the
reference:

```
[c1]crop=400:240:54:1180,boxblur=22:2,eq=brightness=-0.13[g1];
[b0][g1]overlay=54:1180:enable='gte(t,3.2)'
```

The build is staged the way the reference stages it — name, then the price
panel, then the second panel, then the fine print, then the arrow — so the
viewer reads one thing at a time instead of meeting a finished layout.

## EXP-2 — Detail grid · thrown away

Built, looked at, rejected. Hero picture over a strip of three detail panes
from the same clip, with a vertical tab and a caption plate. The strip cut the
hero picture in half and the whole thing read as a brochure page rather than a
piece of film.

The vertical tab was the one part worth keeping, and it survives on its own as
`--spec-style tab`. Nothing else was carried over and the code is gone rather
than commented out.

## What is worth keeping

The frosted panel is the strongest idea of the two. It solves the problem the
bordered chip has — it puts a figure on screen legibly without a container that
looks stuck on, because the container is made of the footage itself.

The vertical tab already graduated: it is now `--spec-style tab` in
`99-toolkit/fd_spec.py` and ships on the GT3 RS windshield ad.

## Rebuild

```bash
python3 build_experimental.py exp1 /path/to/clip.mp4
```
