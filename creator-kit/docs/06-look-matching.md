# Matching a look from a reference video

Two tools, used together, copy a grade you only have as a finished video.

`match_grade.py` (histogram matching) copies **tone** and overall balance. It
cannot copy **saturation** or **split-toning**, because those are relations
between channels, not per-channel curves. For a filmic reference (flat mids,
half the chroma, warm highlights) it barely moves the picture.

`look_stats.py` + `look_lut.py` close that gap by measuring and then dialling:

```bash
# frames from the reference and from the footage to be graded, 216x384 PPM
ffmpeg -ss 4 -i FILM_LUT.mov -frames:v 1 -vf scale=216:384 -pix_fmt rgb24 ref_04.ppm
ffmpeg -ss 5 -i master.mp4   -frames:v 1 -vf scale=216:384 -pix_fmt rgb24 src_05.ppm

# measure both: luma percentiles, saturation and R-B / green balance per band
python3 scripts/look_stats.py "ref_*.ppm" "src_*.ppm"

# build a LUT from explicit controls, apply to the source frames, re-measure
python3 scripts/look_lut.py --out look.cube --gamma 0.80 --black 8 --sat 0.55 \
    --sat-high 0.7 --shadow 0 2 1 --mid 0 5 1 --high 0 1 0 --shoulder 0.4
ffmpeg -i src_05.ppm -vf lut3d=look.cube -pix_fmt rgb24 t_05.ppm
python3 scripts/look_stats.py "t_*.ppm"
```

Iterate two or three times until the bands line up, then look at paired
before/after frames next to the reference. Numbers get you close; the eye
decides, because the measured bands are content-weighted (a red car in frame
drags the mid-band R-B up regardless of grade).

## The FILM_LUT reference (2026-09-05)

Measured against the trial Reel master (already in the published look):

| | reference | published look | delivered (v6) |
|---|---|---|---|
| luma median | 55 | 31 | 38 |
| mid saturation | 0.13 | 0.29 | 0.16 |
| high saturation | 0.07 | 0.20 | 0.10 |
| grey point R−B | +1.8 | +1.7 | +1.8 |
| grey point green | +3.5 | −0.6 | +2.3 |

Reading: the reference lifts the midtones (gamma 0.80 here, a little less
than the 0.76 the percentiles suggest, because lifting further amplifies
shadow compression noise), keeps true blacks (1–5th percentile at 0), halves
the chroma with highlights desaturated further, and sits slightly green in
the greys. No warmth is added anywhere: the first attempt (v4) added warm
offsets from content-weighted band averages and its greys measured +8.3 R−B,
which read as red.
`luts/AK_Film_Test_Match.cube` is the result. It is built to sit **on top of
the published look**, not on D-Log; to grade raw footage into it, run
`cut_clip.sh` as usual and then apply this LUT to the export.
