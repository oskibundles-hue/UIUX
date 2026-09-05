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
python3 scripts/look_lut.py --out look.cube --gamma 0.76 --black 8 --sat 0.5 \
    --sat-high 0.65 --shadow 4 2 -2 --mid 3 7 -3 --high 3 0 -3 --shoulder 0.5
ffmpeg -i src_05.ppm -vf lut3d=look.cube -pix_fmt rgb24 t_05.ppm
python3 scripts/look_stats.py "t_*.ppm"
```

Iterate two or three times until the bands line up, then look at paired
before/after frames next to the reference. Numbers get you close; the eye
decides, because the measured bands are content-weighted (a red car in frame
drags the mid-band R-B up regardless of grade).

## The FILM_LUT reference (2026-09-05)

Measured against the trial Reel master (already in the published look):

| | reference | published look | delivered (v4) |
|---|---|---|---|
| luma median | 55 | 31 | 47 |
| mid saturation | 0.13 | 0.29 | 0.20 |
| high saturation | 0.07 | 0.20 | 0.10 |
| mid green balance | +2.9 | −7.8 | +3.2 |

Reading: the reference lifts the midtones by roughly gamma 0.76, keeps true
blacks (1–5th percentile at 0), halves the chroma with highlights desaturated
further, and sits slightly green in the mids with warm highlights.
`luts/AK_Film_Test_Match.cube` is the result. It is built to sit **on top of
the published look**, not on D-Log; to grade raw footage into it, run
`cut_clip.sh` as usual and then apply this LUT to the export.
