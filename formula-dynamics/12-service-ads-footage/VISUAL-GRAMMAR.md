# What the reference clips actually do

Measured 23 Sept off the twelve clips in `NQ Studio/07 Inspiration/tiktok sfx
and animations`, at 8-12 frames per second. **Nothing here is copied.** What
was taken is the technique; the implementations are ours, in our own kit.

## The assumption that was wrong

TikTok reference is supposed to mean fast cutting. It does not. Cut rates
across the twelve run **0.00 to 0.71 per second**, and most sit at zero.
`tk02` is 69 seconds long and **85% of its frames are frozen** - 476 of 556.

These are long holds with something animating on top, not montages.

## Where the motion is

Share of all frame-to-frame change, by vertical fifth:

| clip | top | upper | mid | lower | bottom | reading |
|---|---|---|---|---|---|---|
| `tk02` | 1.0% | 20.9% | **71.1%** | 5.9% | 1.1% | one band |
| `tk07` | **0.0%** | 17.5% | **63.5%** | 18.9% | **0.0%** | one band |
| `watermark5` | 1.4% | 17.2% | **56.7%** | 22.5% | 2.1% | one band |
| `tk01` | 5.4% | 18.3% | 30.8% | **42.1%** | 3.4% | lower third |
| `tk05` | 18.5% | 19.5% | 20.6% | 20.7% | 20.6% | whole frame |
| `watermark4` | 13.8% | 20.8% | 24.4% | 20.9% | 20.1% | whole frame |

**The discipline is the finding.** `tk07` has literally 0.0% motion in the top
and bottom fifths. The graphic moves; the frame does not. Everything below
follows from that.

## The three moves, and how each was told apart

Within the moving band, tracking the left and right edges of the changing
region over time:

| clip | left wander | right wander | width trend | move |
|---|---|---|---|---|
| `tk01` | 0.032 | 0.156 | **+0.51** | **type-on** - anchored left, grows right |
| `watermark5` | 0.084 | 0.112 | **+0.39** | **scale-pop** - grows from the middle |
| `tk02` `tk07` | ~0.20 | ~0.20 | -0.08 | **swap-in-place** - content replaces itself |

A reveal anchors one edge. A slide moves both edges together. Growing from the
centre moves both apart. Content swapping moves both, randomly, without the
width trending anywhere. That is enough to separate them without looking.

## When and why to use each

The rule is not "this looks good". It is what the cue has to do, against how
much room the cut gives it and what the footage underneath is already doing.

| move | use it for | why | do not |
|---|---|---|---|
| **type-on** | the hook | Being written is itself attention - the viewer waits for the end of the sentence. | Never for a figure. A price that types out reads as uncertain. |
| **swap-in-place** | a list of facts | Four facts through one slot cost one slot's worth of screen. This is the move that survives a short cut, where sequential chips do not. | Never for one item. A slot that swaps once looks broken. |
| **scale-pop** | a single number | Growing in place says *this is the thing*, and a figure is short enough to carry 8.5% of frame height. | Never for a sentence - it will not fit and the move reads as a mistake. |
| **hold still** | busy footage | When the picture is already moving, a moving graphic competes with it and both lose. | - |

Two constraints from our own measurements, not from the reference:

**Length decides whether a sequence is possible at all.** The spec window is
derived from the duration; on the 11.3 s oil cut it computed to a negative
span and the chips were dropped. Four chips need about 22 seconds to hold 1.4 s
each. Under that, `swap-in-place` is the only way to carry four facts.

**The footage votes.** Where the clip's own motion is spread across the whole
frame rather than concentrated (`tk05` and `watermark4` above, at roughly 20%
per fifth), a graphic that also moves has nothing to sit against. Lock it.

## What is implemented

`99-toolkit/fd_motion.py` gains `swap-in-place` and `scale-pop`. `type-on` was
already there and matches what `tk01` does.

**No inward whoosh exists in the reference** either visually or in its audio -
every move in those twelve clips goes away from camera, never toward it. Worth
knowing if someone wonders why the kit has no arrival move from this source.

## Re-reading new reference

    python3 99-toolkit/fd_visual_read.py <dir-or-files>...

Prints the same three tables. Run it on new reference rather than trusting an
impression of what a clip does - the cut-rate finding above is exactly the kind
of thing an impression gets backwards.
