# The sound kit — 39 sounds

17 originals plus 22 lifted out of the shop's own reference clips on 23 Sept.
**Rights on the extracted set were confirmed by the shop**; they are used in
the `street` and `cut` kits.

## The originals (17)

`impact-hard` `impact-soft` `impact-tight` · `key-click-1..3` ·
`riser-long` `riser-short` · `scramble` · `sub-drop` `sub-thump` ·
`ui-tick-1..3` `ui-tick-soft` · `whoosh-in` `whoosh-out`

## Extracted, named by family and character (21 + audition)

Cut with `99-toolkit/fd_sfx_extract.py` from the twelve clips in
`NQ Studio/07 Inspiration/tiktok sfx and animations`. 164 candidates were cut,
120 rejected as music, speech or junk, and 44 kept — then deduped to 21,
because the same transition repeats up to seven times inside one clip.

| name | character | what it is |
|---|---|---|
| `tk-tick-bright-1` `-2` | centroid above 5.5 kHz | a UI tick with air on it |
| `tk-tick-soft-1` `-2` | below 5.5 kHz | the same gesture, duller |
| `tk-impact-hard-1`..`-6` | full-scale, under 0.35 s | the transition hit |
| `tk-impact-soft-1` `-2` | longer, lower peak | a landing rather than a hit |
| `tk-whoosh-out-1`..`-3` | energy falls across the sound | a move away |
| `tk-sub-drop-1` | pitch falls through the sound | the classic drop |
| `tk-sub-rumble-1` `-2` | over 0.35 s | a floor under a title |
| `tk-sub-thump-1`..`-3` | under 0.35 s | a full stop |

Character is measured, not labelled by ear: direction from the energy in the
first third against the last, weight from peak and duration, brightness from
the spectral centroid, and `drop` from the centroid actually falling between
the start and the end of the sound.

**No `whoosh-in` came out of the reference clips** — every whoosh in them moves
away from the camera, never toward it. The originals still cover that.

## Kits

| kit | built from | character |
|---|---|---|
| `signature` | originals | what every approved ad uses. Bit-identical default. |
| `deep` | originals | long riser, sub-drop over the impact |
| `tight` | originals | whoosh and impact-tight, key-clicks |
| `minimal` | originals | one soft hit per cue |
| `street` | extracted | hard transition hit with a sub under it |
| `cut` | extracted | tick on, whoosh off, nothing sustained |

Measured across all six on one cue sheet, `deep` and `cut` sit furthest apart
at 0.332, and `deep` against `street` at 0.317 — both wider than the 0.272 that
separates the two most similar approved ads.
