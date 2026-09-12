# 15 — Ad Ratios

The approved ads rebuilt for the Meta and Google placements that will not take
a 9:16 file. Built by `99-toolkit/fd_reframe.py`.

## What gets made

| Ratio | Pixels | Placements | Picture width |
|---|---|---|---|
| 4x5 | 1080x1350 | Facebook + Instagram Feed | 758px — 70% of canvas |
| 1x1 | 1080x1080 | Facebook Marketplace, square feed, FB right column, Google Demand Gen / Discover / Gmail | 608px — 56% of canvas |

9:16 is the source shape and is unchanged — it covers Reels, Stories, Shorts,
TikTok and Demand Gen vertical, and it already exists in
`12-service-ads-footage/approved/`.

## Why fit-and-fill rather than crop

The graphics are burned into the approved files. Measured on the frame: the
spec panel occupies y 1074–1314 with the title block directly beneath it and
the logo bug up top. Going to 4:5 means losing 570px of height and going to
1:1 means losing 840px — keep the top and the title block and CTA go, keep the
bottom and the title card and bug go. There is no crop window that spares all
three.

So nothing is cropped. The whole frame is scaled to fit the new canvas and the
remainder is filled with a blurred, darkened copy of itself. Every graphic
survives at full height; the cost is the picture percentages in the table.

No border on the picture edge — the shop's rule is translucent, never bordered,
and a red frame around the video would break it for a flourish.

Audio is copied through with `-c:a copy`. These files are already mastered to
−14 LUFS / −1.0 dBTP and re-encoding would undo that.

## 16:9 is deliberately absent

1920x1080 needs 1920px of width and the source has 1080, so a derived version
puts the picture at 32% of the canvas — a thin strip between two blur bars.
Google treats 16:9 as optional, so going without beats running that.

Real 16:9 wants a re-cut from the original camera files (`sf90.mp4`, `gt3.mov`,
`roma.mov`, the Urus clip) on a wide canvas with the panels and safe zones laid
out for that shape. `fd_brand.CANVASES` already carries a `16x9` entry and
`build_edit.py` picks its canvas off the footage, so the pipeline is ready for
it — only the footage is missing.

## Running it

```bash
python3 ../99-toolkit/fd_reframe.py 4x5 ../12-service-ads-footage/approved -o 4x5
python3 ../99-toolkit/fd_reframe.py 1x1 ../12-service-ads-footage/approved -o 1x1
python3 ../99-toolkit/fd_reframe.py 4x5 clip.mp4 --dry-run   # geometry only
```

The rendered files are not committed — they are derived, and
`fd_reframe.py` plus `12-service-ads-footage/approved/` reproduce them exactly.
