# The Kinetic Cut

An experimental look, separate from the Fast Cut recipe. Where Fast Cut is warm,
graded and readable, this one is monochrome, letterboxed and deliberately harsh:
a slow moody build, a strobing montage on the drop, and staircase type that
lands one word at a time.

It exists because Omarie sent a reference edit and asked to recreate it. Nothing
below is guessed — every number was measured off that file frame by frame.

## What was measured

| element | measurement |
|---|---|
| canvas | 9:16, 30 fps |
| band | anchored at the **bottom** (0.658 of frame height); only the top edge moves |
| band shape | 1.30:1 through the build, 1.90:1 through the strobe, 1.77:1 to finish |
| grade | saturation near zero, contrast up, blacks crushed |
| colour | appears **only** on the smear frames and on one accent word per block |
| cuts | 2-3 s for the first 8 s, then 0.12-0.45 s for about 7 s, then long again |
| transitions | directional RGB smears cut in as their own 3-6 frame shots; single white flash frames |
| type | heavy caps, left aligned, each line stepped further right, last line back to the margin |
| bug | handle centred in the top black bar, not over the picture |

The bottom-anchored band is the part that is easy to get wrong. The picture does
not sit in the middle of the frame: it sits high, with more black below than
above, and the top edge slides when the section changes. That asymmetry is most
of why the reference reads as designed rather than cropped.

## Running it

```bash
python3 build_kinetic.py --spec spec_k1.json \
  --footage /path/to/clips --work work --out K1.mp4
```

`spec_k1.json` holds everything: the shot list, the band keyframes, the grade,
the audio placement. A second piece is a second spec, not a code change.

Shots are one of three kinds:

```json
{"clip": "18 red supercar.mp4", "in": 12.0, "dur": 2.4}
{"fx": "smear", "dur": 0.2, "angle": 0}
{"fx": "flash", "dur": 0.07}
```

A smear freezes the last frame of the shot before it, squeezes the frame to a
sliver along one axis and stretches it back (that is what makes the blur
directional), then pulls the red and blue channels apart with `rgbashift`. It is
the only saturated thing on screen, which is why it reads as an impact rather
than an effect.

`type_frames.py` renders the type as a transparent PNG sequence. Words in a
block are spread over the first 70% of its time and the finished line holds for
the rest. One word per block may carry the accent colour and a 3 px RGB split.

## K1, the first build

19 s. Words are Omarie's own, lifted from the take where he is talking about
working with Alex and Nate:

> You can't be selfish when you're doing this. You guys are making the magic
> happen. I'm just here to help make it happen. It just helps everyone out.

His recorded voice carries those lines; the type follows it. Built at 1080x1920
for iteration speed — the spec is resolution-independent, so a 4K master is the
same command with `--width 2160 --height 3840`.

## Where this differs from the reference

The reference is someone else's edit and their words. What is reproduced here is
technique: band geometry, cut rhythm, the smear, the staircase. The footage,
voice, handle and accent colour are Omarie's own, and the accent red is the
Formula Dynamics `#FE0F13`.
