# Experimental

Kept apart from the house ads on purpose. These borrow devices off the dealer
templates and test whether they survive contact with the brand. Nothing here is
approved for spend; it exists to be looked at and argued with.

Nothing is traced from the templates — every element is generated from the
brand kit.

## EXP-1 — Glass panels · SF90 · 22.2 s

From the BMW dealer template: twin figure panels, a staged build, a fine-print
line, and the circular swipe affordance.

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

## EXP-2 — Detail grid · GT3 RS · 28.7 s

From the Ferrari dealer template: a vertical red section tab, a header bar, and
a strip of detail panes under the hero picture. The three panes are pulled from
other moments of the same clip (2.0 s, 3.2 s, 16.0 s) — the chrono, the forged
wheel, the arch — so one clip does the work of a multi-camera shoot.

The caption sits on its own dark plate. Laid straight over picture it fought the
Porsche crest and the carbon weave and neither read; the plate fixed it.

## What is worth keeping

The frosted panel is the strongest idea of the two. It solves the problem the
bordered chip has — it puts a figure on screen legibly without a container that
looks stuck on, because the container is made of the footage itself.

The vertical tab already graduated: it is now `--spec-style tab` in
`99-toolkit/fd_spec.py` and ships on the GT3 RS windshield ad.

## Rebuild

```bash
python3 build_experimental.py exp1 /path/to/sf90.mp4
python3 build_experimental.py exp2 /path/to/gt3.mov
```
