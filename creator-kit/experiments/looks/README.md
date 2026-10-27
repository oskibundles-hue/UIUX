# Talking-head looks

One talking-head take in, several styled cuts out, so Omarie can pick a look instead
of describing one. It started from a reel Oski passed on (one clip, a grid of
caption looks); the six looks here are new, made for @nq.young in the kit's
colours. On 2026-10-25 Omarie picked **Mono** as the default, so set `"picked"` in
the spec. The other five stay proposed.

| look | what it is |
|---|---|
| Highlighter | Archivo 800 captions; the word being said gets a yellow marker swipe |
| One Word | one word at a time in big Anton, key words yellow, a pop on each word |
| Tag Stack | black-on-yellow tag boxes that stack as he talks; orange hook tab up top |
| Framed | yellow page, the take in a rounded card, black Anton headline, caption pill |
| **Mono** (picked) | black and white, only the yellow survives: karaoke caps and a thin border |
| Headline | editorial black band (serif + Anton hook), serif/Anton captions on a pill, orange progress bar |

## Running it

```bash
# 1. cut the keep ranges, grade with the kit LUT, normalise the audio once
python3 build_looks.py base  --spec spec_sep03.json --src take.mov --work work
# 1b. paint out the spec's "retouch" marks (skip if it has none)
python3 retouch.py --spec spec_sep03.json --work work
# 2. compose every look over the same base (or --only mono,framed)
python3 build_looks.py looks --spec spec_sep03.json --work work
# 3. grid still, review contact sheet, 3x2 grid video, cycle reel, 2x2 grid
python3 build_looks.py sheets --spec spec_sep03.json --work work
# 4. before nq-check
python3 qa.py --spec spec_sep03.json --work work --transcript words_large.json
```

**Size.** `--size WxH` on any step, else the spec's `"size"`, else 1080x1920. The
Sep 3 spec says 2160x3840 (Fast Cut delivery). Every layout constant is written at
1080 wide and goes through `px()`, so the 4K render is the 1080 layout scaled (at
1080 it is pixel-identical to the first build). `base` records the size in
`timeline.json`; `looks`, `sheets` and `qa.py` stop if asked for another one, so
rebuild `base` to change size. For a 4K pass, build only what's needed:
`looks --only mono,highlighter,one_word,tag_stack` covers Mono and the 2x2 grid.

**Retouch.** The spec's `"retouch"` list names marks to paint out, each with the time
it is seeded at and its centre there in base pixels. `retouch.py` tracks a mark one jump
cut at a time, never across one. Each cut is anchored on the frame where the mark's
saturation template matches best near where YuNet's landmarks put it. From there optical
flow (Lucas-Kanade) follows the skin around the mark frame to frame and snaps back to the
template when it is close; a template search alone lost it on fast head turns and slid
onto his eye. A frame is painted only when his face is in shot at a reasonable size with
skin around the track, so the wide cutaway and the can held over his brow are left alone.
The mask is the pixels near the track that are as grey and as dark as the mark itself
(eye whites and brow hair stay out), filled with Telea inpainting. The untouched base is
kept as `base_src.mp4` and every position, with how it was found, goes to `retouch.json`.
On the Sep 3 take it paints 328 of 344 frames and skips f47-62 (the can and the cutaway).
Re-run it after `base`, which writes a fresh `base.mp4` (delete `base_src.mp4` first so it
is refreshed too).

**Audio.** Two-pass loudnorm to -14 LUFS, then the 0.84 limiter at 4x oversampling (so
it catches inter-sample peaks) and 0.3 dB of headroom for the AAC encode. The last cut
fades out 110 ms before its end, and the fade is applied again after the limiter, whose 4x
resample smears it, so the final 70 ms is digital zero. Sep 3: -14.9 LUFS,
-1.8 dBTP in the delivered file.

A new take is a new spec, not a code change. The spec holds:

- `keep`: the source ranges to use. The pauses between them are cut, and the jump
  cuts are covered by alternating `punch` zooms. Use Silero VAD speech regions
  (threshold 0.35, 150 ms minimum silence) inside the stretch you want, because
  shop noise makes a plain energy gate useless.
- `phrases`: the captions, word by word, with source times from the transcript
  (faster-whisper large-v3 with word timestamps). Fix spelling and punctuation
  here, never the words. Leave out a word the model wasn't sure of rather than guess.
- `hook` / `hook_alt`: headline lines, which must be phrases he actually says.
- `grid2x2`: four looks for the 2x2 grid, top-left first (Mono plus the next three
  in spec order, Omarie 2026-10-27).
- `lut`: the kit LUT. `AK_Garage_Dark` held the blacks on the Sep 3 shop take
  (mean luma 0.32-0.40, 2nd percentile 0.02-0.05); `AK_DLogM_Rescue` crushed them.

## Rules it keeps

- **Only his words on screen.** Before captioning, run `scripts/who_speaks.py` to
  make sure the stretch is his voice. On Sep 3 an off-camera voice comes in at
  about 38 s, so the cut stops at 27 s. qa.py checks that every caption and hook is
  a run of transcript words, in order.
- **Instagram safe zone** from `theme.ts` (top .135, bottom .245, left .067, right
  .176) for all text. Pictures and borders may run under the UI. Text may not.
- **Loudness** -14 LUFS through two-pass loudnorm, then
  `alimiter=limit=0.84:level=false`. Leave `level=false` in: alimiter's auto-level
  pushes the output back up to 0 dBFS (the first build measured -13.1 LUFS with
  true peak 0.0 until it was set).
- Crops and punch-ins centre on the median face box from YuNet
  (`face_detection_yunet_2023mar.onnx`, from opencv_zoo, MIT licence; needs
  `opencv-python-headless`). Don't go back to the Haar cascade. On the Sep 3 take
  it put the face at y 695, 184 px tall. YuNet found it at y 808, 588 px tall, with
  the mouth at y 942, and the captions built on the Haar box sat on his mouth.
- Text sits under his chin or off the picture, never over his mouth. `timeline.json`
  records the face box (`mouth` is the mean y of the two mouth corners); each look
  records where the mouth lands after its crop (`mouths` in `manifest.json`), and
  qa.py fails any text box that covers it.

## Outputs (in `--work`, not committed)

`<look>.mp4` for each look (W x H, 30 fps, H.264 + AAC), `grid.png`,
`contact_sheet.jpg` (each built look at four moments, for nq-check), `grid.mp4` (3
across) and `cycle.mp4` (the take once, a different look on each phrase) when two or
more looks are built, `grid2x2.mp4`, `manifest.json` (every on-screen line with its
box, which qa.py reads), and `timeline.json`.

`grid2x2.mp4` is @aslaniedits' format (relayed by Muse, nq-agent-channel #58): four
looks in one full-size frame, each quadrant playing the whole take in sync, split by
a thin black cross, with no labels, so the only words on screen are his. Each look
keeps its own safe zone inside its quadrant, but the quadrants' text can't all keep
the full frame's: qa.py reports that as WARN for Omarie to judge, not as a pass.

Product names go through nq-facts and nq-second before anything ships.
