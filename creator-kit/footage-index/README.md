# Footage index

One file per shoot. Each records what is in every clip, its exposure, and any
edit made from it, so nothing has to be re-watched to find a shot.

## Dropbox layout

```
/Anti Stock Media/
  01 Raw D-Log/YYYY-MM-DD/    camera originals, named "YYYY-MM-DD HH-MM-SS"
  02 Published Edits/         finished posts (captions burned in)
  03 Grade Reference/         what grades are matched against
  04 Exports/                 finished Reels ready to post
```

Filenames are ISO timestamps so they sort chronologically. The originals were
named `Video Sep 03 2026, 10 04 33 PM.mov`, which sorts 10 PM before 8 AM.

**04 Exports has to be filled by hand.** The Dropbox connector here can read
files but cannot write binaries, so finished Reels are delivered through chat
and you drop them in that folder.

## Reading the numbers

`YAVG` is average luma out of 255, `SAT` average saturation. On this camera:

| | YAVG | SAT |
|---|---|---|
| Raw D-Log M | 80–115 | 3–10 |
| Graded (your look) | ~46 | ~5 |

Raw log sits in a narrow band with no true black. Low saturation alone does
**not** mean unconverted — your own published grade is deliberately
desaturated. The tell is range: log has YMIN ~30 and never reaches 255,
whereas a finished grade uses the full 0–255.

One gotcha when measuring: run `signalstats` **before** any `format=gbrp16le`
in the chain, or the numbers come back on a 16-bit scale and read ~257x too
high.
