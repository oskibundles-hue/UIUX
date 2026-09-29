# Vlog kit, set 2: seven more Locked-On variations (G3, B4, C4, C5, I4, I5, I6)

**What it is.** Omarie asked (29 Sept 2026) for "new variations of our vlog kit using your best capabilities of dynamic
motion graphic", in the **Locked-On** style, picking three of the proposed groups: *depth titles*, *through-shot
transitions* and *car trace*, on the same Sep 15 clip as the first 22 (DJI_0029, Red Rock Casino garage, 22:49). Set 2 adds
what set 1 could not do: graphics **behind** people and cars, **windows** cut through the picture, **light on the car
itself**, a lock that **turns with the car**, and true **slow motion** from the camera's 59.94 fps. **Status: reviewed.** Nothing here has been posted.

**Reviewed 29 Sept 2026: B4 (name behind) and C4 (car trace) are kept.** Omarie: *"the name behind and the car trace
were the only things i like from that"*. G3, C5, I4, I5 and I6 were not picked; their code stays here for reference but they
are not part of the kit's offer.

Set 1 is untouched: the 22 variations, `kit.html`, `build.py` and `README.md` render exactly as before. Set 2 has its own
page (`kit2.html`), components (`lib/sekit2.js`), compositor (`lib/compose2.py`), build (`build2.py`), config
(`config2.json`) and outputs, and reuses set 1's helpers. Codes continue set 1's groups, so both sets can be mixed in one
vlog: "use A2, G3, H1, C4, I4".

| Deliverable | Path |
|---|---|
| Review reel, 17.6 s, 1080x1920, 29.97 fps, corner code tags | `exports/vlog-kit-set2-reel.mp4` |
| One still per variation (transitions as three-frame strips) | `mockups/set2/G3_depth-title.jpg` … `mockups/set2/I6_freeze-sweep.jpg` |
| Board | `mockups/set2/BOARD.jpg` |
| QA stills and summary | `exports/qa-set2/` (`qa_summary.json`) |

## The seven

| Code | Type | What it does | Use it for | Breaks when |
|---|---|---|---|---|
| **G3** | `depthTitle` | The chapter title stands **between the background and the cars**: the letters rise from behind the lineup (the cars and the guest cover their lower edge through a matte), with a 2.5D push where the background, the title and the cars scale at three rates | A chapter open on a still or a locked-off shot of the cars | The shot moves (use a still, as here) or nothing tall enough stands in front of the title |
| **B4** | `nameBehind` | The host's name, huge, **behind him**: his hair and shoulders cover its lower edge (a person matte on every frame), HOST · @NQ.YOUNG in front; the name drifts at 30-60 % of his motion so it belongs to the scene | Introducing the host (or a guest, by their company) on a selfie shot | The face track is lost, or the head sits too low for the name to tuck behind it |
| **C4** | `carTrace` | The picture **freezes** with a flash, the world outside the car darkens and loses colour, a gold line **traces the car's outline** with a live tip and a dashed offset line, ticks mark front, rear and roof, a light pulse runs the finished outline, the make locks in; then the line un-draws and the picture moves again | Introducing a hero car once | The car is cut by the frame edge, or another car touches it (fixed here by hand: see *Mattes*) |
| **C5** | `orbitLock` | Brackets **pinned to the side of the car** by a planar track, so they skew and turn as the camera moves round it; the lock bends from a flat box onto the surface, a perspective grid and a scan line sweep the panel, a ruler runs along the sill. Here on a true 0.5x slow motion from the 59.94 fps source | A car the camera moves past (walk-by, slow-mo pass) | The side panel leaves the frame, or blur is too heavy to track (the track holds 86+ inlier points on every frame here) |
| **I4** | `letterWindow` | The next chapter's title rises as solid letters, the white drains out and **the next shot is inside the letters**, then the camera **flies into the B** until the next shot fills the frame | Big chapter changes | The title is long (keep it to two short lines) |
| **I5** | `stripeShutter` | The 78/22 stripe draws across the middle, **opens to fill the frame** (three frames of SE gold and white with the mark knocked out in black), the shot switches underneath, and the stripe closes back into its line | A hard, branded cut between chapters or into a hook | Used more than once or twice a vlog: it is loud |
| **I6** | `freezeSweep` | The chapter's last shot **freezes** and cools, letterbox bars close into the phone's own UI bands, a slanted studio light **sweeps across the car's body** (lit through its matte, catching the paint's highlights) and END OF CH 04 sets in; the clip's own sound **tape-stops** under it | The end of a chapter, into I4 or a cut | The car has no highlights to catch (a matte black car reads flat) |

All seven keep the kit's rules: gold #FBD101 is the only accent, the 78/22 stripe is always horizontal, Bebas and
Michroma only, text inside x 54-907 / y 269-1536, exits reverse their own entrance, and every fast move has true sub-frame
motion blur (up to 16 samples over a 270-degree shutter).

## How set 2 works

- **Passes.** A component can draw on three layers: front (as in set 1), **back** (composited over the plate, then the
  subject is laid back on top through its matte, so type sits behind people and cars) and **mask** (white shapes whose
  alpha is a window onto the shot's B plate). `lib/kcapture2.js` captures each pass a frame uses as its own PNG
  (`NNNNN.png`, `NNNNN_back.png`, `NNNNN_mask.png`); `lib/compose2.py` puts them together.
- **Mattes.** Apple's own Vision framework, on the Mac, with no model download (`lib/matte.swift`): foreground instances for
  the cars, person segmentation (accurate) for the host on every frame. They are committed in `lib/data/mattes2/` so the
  build also runs where Vision is not available; `python3 build2.py --stage mattes` re-cuts them on a Mac. Vision merged a
  dark car parked behind the Urus into its matte at the roof; `config2.json` carries a hand exclusion polygon along the hood
  line for it (the same kind of hand correction the ads' type-behind-the-car shots get).
- **2.5D push (G3).** The background is the still with the subject inpainted out (OpenCV Telea on a dilated matte); it
  scales 1.30 → 1.335, the title 1.00 → 1.055 on top of it, and the cars and the guest 1.30 → 1.40, so the title visibly sits
  between them.
- **Planar track (C5).** `lib/plane_track.py`: Shi-Tomasi features inside the side panel and the car's matte, pyramidal
  Lucas-Kanade with a forward-backward check, a RANSAC homography per 59.94 fps frame chained out from an anchor frame, and
  a light Gaussian over time. The result is `lib/data/plane.json` (quad per source frame); the page draws the lock through
  that homography, so the grid and the ruler are in true perspective.
- **Slow motion.** `hfr` plates read the 59.94 fps source directly (`.work2/plates/rooftop60/`): 0.5x plays one source
  frame per reel frame, with no blended frames.
- **Outline (C4).** The largest outer contour of the frozen frame's matte, simplified, starting at the front of the car and
  running over the roof first; a dilated copy gives the dashed offset line.
- **Light (I6).** A slanted band, eased only at its ends so it takes about a third of a second to cross the car, strong
  through the car's matte and weighted by the paint's own brightness, faint (6 %) elsewhere.
- **Tape stop (I6).** The SUV shot's sound carries on past the freeze with its playback rate falling to zero over 0.5 s.

## The reel (17.6 s)

| Time | Footage | Codes |
|---|---|---|
| 0.00-2.20 | DJI_0029 0.0-2.2 s, host | B4 |
| 2.20-2.80 | the shutter into the lineup | I5 |
| 2.80-5.81 | 4K still of the lineup (clip frame 252), 2.5D push | G3 THE LINEUP |
| 5.81-7.54 | the Urus pass at 0.5x (59.94 fps source frames 280-331) | C5 LAMBORGHINI URUS |
| 7.54-9.94 | freeze on the Urus (frame 166) | C4 |
| 9.94-10.34 | the picture moves again | |
| 10.34-11.28 | DJI_0029 3.3-4.3 s, the SUV | |
| 11.28-12.81 | freeze on the SUV (frame 128) | I6 END OF CH 04 |
| 12.81-14.15 | into the host (from clip frame 346) | I4 THE DRIVE BACK |
| 14.15-15.61 | host | |
| 15.61-17.62 | index card | all seven codes |

## Placeholders and things to confirm before publishing

| On screen | Where | What to do |
|---|---|---|
| LAMBORGHINI · URUS | C4, C5 | The grey widebody car is an Urus body (set 1's README identified it). If it is SE's Mansory Urus, the tag can say so; it does not claim it now |
| The dark SUV | I6 | Not identified, so nothing names it (I6 never shows a make) |
| The guest in the lineup | G3 | The same stand-in as set 1's B3; confirm she is happy to be shown |
| CH 04 · RED ROCK, CH 05 | G3, I6, I4 | Chapter numbers are illustrative; number them to the real vlog |

## Every on-screen line and its source

| Line | Source |
|---|---|
| OMARIE, @NQ.YOUNG, HOST | the approved follow card; HOST is his role in the vlog |
| THE LINEUP, THE DRIVE BACK, CH 04 · RED ROCK, CH 05 | set 1's chapter names (the rally cut's chapters); RED ROCK from the footage survey |
| LAMBORGHINI, URUS | identified on the footage (set 1 README); make and body only |
| END OF CH 04 | the chapter it closes |
| VLOG KIT · SET 2, the codes | review annotations, not part of the kit |

No speeds, horsepower, prices, guest names or client logos anywhere.

## How to render

```bash
python3 build2.py                  # prep, layer (3 Chromium processes, ~1 min), reel (~6 min), mocks, qa
python3 build2.py --stage reel     # layer + composite + audio -> exports/vlog-kit-set2-reel.mp4
python3 build2.py --stage mocks    # mockups/set2/*.jpg + BOARD.jpg
python3 build2.py --stage qa       # safe-zone audit (every pass), probe, check stills -> exports/qa-set2/
python3 build2.py --stills 1.4,9.2 # single reel times -> .work2/stills/
```

Needs what set 1 needs (Python 3 with numpy, Pillow and OpenCV; Node with Playwright; ffmpeg) and the camera file
(`ROOFTOP_RAW`). Where Playwright's own Chromium is not installed, point `PW_MODULE` at a playwright package and `PW_EXEC`
at any Chromium or headless-shell binary (on the Mac, Remotion's bundled `chrome-headless-shell` works). Layer frames are
cached in `.work2/layer/` by frame number: delete the ones you changed after an edit.

`kit2.html#only=G3,C4` previews single codes; `#chip=0` hides the code chip.

## How it was checked (`exports/qa-set2/qa_summary.json`, rebuilt by `--stage qa`)

- **Safe zones, every pass:** the box of every visible text line on the front, back and mask layers at every 0.1 s of the
  reel and at every still (189 times): **0 outside** x 54-907 / y 269-1536. The only crossings are I4's letters during the
  fly-through (39 boxes, all after 13.33 s), which is the effect. The first audit caught two real breaks, both fixed: B4's
  name drifting right with the face to x 938 (now clamped, 740 px wide) and G3's title growing past both edges during its
  push (now 770 px wide and pushed about the safe area's centre).
- **Every frame looked at:** the decoded reel on contact sheets (every 5th frame, 528 frames): no pop at the freeze, the
  resume, the window or the index card. Stills at the entry, middle and exit of every code are in `exports/qa-set2/` (24).
- **Tracks and mattes:** the C5 plane drawn on its source frames (8 frames on a QA sheet; 86-plus RANSAC inliers on every
  frame); every matte laid over its frame and looked at; the Urus matte fixed by hand where Vision merged a parked car into
  its roof.
- **Set 1 unchanged:** three set-1 layer frames re-rendered after the set-2 changes are pixel-identical to the renders made
  before them (f45, f142, f390).
- **Export:** H.264 High, yuv420p bt709, 1080x1920, 29.97 fps, 17.62 s, CRF 17, 16.2 MiB, AAC 48 kHz, +faststart. Audio
  -22.4 LUFS, true peak -11.3 dBTP (the clip's own sound, low, like set 1), the last 50 ms silent.
- Fixes made after looking at the renders: I4 opened on the far lineup instead of the host (the window now starts at clip
  frame 346); I6's light crossed the car in two frames (now about a third of a second, weighted by the paint's own
  brightness so it reads as a reflection, not a flat gold wash); B4's HOST · handle row was cramped; C5's lock covered only
  the door and barely showed its perspective (now the whole side, wheels included); stills that caught a glint mid-sweep
  read as silver type (retimed).
