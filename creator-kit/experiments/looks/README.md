# Talking-head looks

One talking-head take in, several styled cuts out, so Omarie can pick a look instead
of describing one. It started from a reel Oski passed on (one clip, a grid of
caption looks); the six looks here are new, made for @nq.young in the kit's
colours, and every one is **proposed** until Omarie picks.

| look | what it is |
|---|---|
| Highlighter | Archivo 800 captions; the word being said gets a yellow marker swipe |
| One Word | one word at a time in big Anton, key words yellow, a pop on each word |
| Tag Stack | black-on-yellow tag boxes that stack as he talks; orange hook tab up top |
| Framed | yellow page, the take in a rounded card, black Anton headline, caption pill |
| Mono | black and white, only the yellow survives: karaoke caps and a thin border |
| Headline | editorial black band (serif + Anton hook), serif/Anton captions on a pill, orange progress bar |

## Running it

```bash
# 1. cut the keep ranges, grade with the kit LUT, normalise the audio once
python3 build_looks.py base  --spec spec_sep03.json --src take.mov --work work
# 2. compose every look over the same base (or --only mono,framed)
python3 build_looks.py looks --spec spec_sep03.json --work work
# 3. grid still, review contact sheet, 3x2 grid video, cycle reel
python3 build_looks.py sheets --spec spec_sep03.json --work work
# 4. before nq-check
python3 qa.py --spec spec_sep03.json --work work --transcript words_large.json
```

A new take is a new spec, not a code change. The spec holds:

- `keep`: the source ranges to use. The pauses between them are cut, and the jump
  cuts are covered by alternating `punch` zooms. Use Silero VAD speech regions
  (threshold 0.35, 150 ms minimum silence) inside the stretch you want, because
  shop noise makes a plain energy gate useless.
- `phrases`: the captions, word by word, with source times from the transcript
  (faster-whisper large-v3 with word timestamps). Fix spelling and punctuation
  here, never the words. Leave out a word the model wasn't sure of rather than guess.
- `hook` / `hook_alt`: headline lines, which must be phrases he actually says.
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
  records the face box (`mouth` is the mean y of the two mouth corners), so check
  new layouts against it.

## Outputs (in `--work`, not committed)

`<look>.mp4` for each look (1080x1920, 30 fps, H.264 + AAC), `grid.png`,
`contact_sheet.jpg` (each look at four moments, for nq-check), `grid.mp4` (3x2),
`cycle.mp4` (the take once, a different look on each phrase), `manifest.json`
(every on-screen line with its box, which qa.py reads), and `timeline.json`.

These are 1080x1920 review drafts. Fast Cut delivers 2160x3840, so the look Omarie
picks still needs a 4K pass (W, H at the top of build_looks.py). Product names go
through nq-facts and nq-second before anything ships.
