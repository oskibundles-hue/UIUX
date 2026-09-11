# Fast Cut — how MR8 was made, and how to make another one

MR8 "sf90 pulls up" is the reference reel: 0:58, local score 93. Everything here reproduces it.
Nothing in this folder needs the container that built it.

## What the recipe is

Under 60 seconds, target 56. 4K vertical 2160x3840 at 29.97 fps.

| element | setting |
|---|---|
| Title | hook split on the first comma into two lines, auto-fitting, holds 2.6 s |
| First shot | 3.0 s, every other shot 4.5 s or less |
| Grade | vlog look: 85% match to reference, greys +2.0 R−B, lift 0.03, knee 0.08, saturation 92%, no sharpening |
| Captions | uniform size, no key word, no gold pill. Top edge 70.5% of frame height, size 2.35%, Archivo 800 |
| Voice | only Omarie's lines captioned; everyone else dropped by speaker match |
| Colour | Formula Dynamics red `#FE0F13`, gold `#FBD101` for highlights. No orange |
| Chapter bar | left-aligned, clear of the logo bug; text from the take label |
| Callouts | dot callouts only when a genuinely red car is on screen |
| Cards | Instagram card at 8 s, YouTube card in the next long speech gap |
| Outro | card outro 3 s from the end. **No call to action** |
| Audio | −14 LUFS, limiter at 0.84 |

`Motion.tsx` currently ships `RED = "#DE1A22"`, which is wrong — it does not match the FD logo bug.
Set it to `#FE0F13` before building anything new.

## Prerequisites

- `ffmpeg` and `ffprobe` on PATH
- Python 3 with `numpy`, `librosa`, `torch` (CPU), `resemblyzer`
- Node with the Remotion project installed: `cd creator-kit/remotion && npm install`
- A headless Chromium for Remotion; point `CHROME` at it
- A voice profile at `creator-kit/voice/omarie_profile.json` (already in the repo)

## Step 1 — cut and grade each take

One graded single per take, named `NN a few words.mp4`. The number matters: the build reads it
to group shots into chapters.

```bash
creator-kit/scripts/cut_clip.sh raw/take.mov "cuts/01 garage walkthrough.mp4" \
  --window 60 --look vlog
```

`--window 60` keeps the best 60 seconds. `--look vlog` is the approved grade. Add `--rotate 180`
for a clip shot upside down.

## Step 2 — transcribe and identify his voice

```bash
python3 creator-kit/scripts/transcribe.py "cuts/01 garage walkthrough.mp4" \
  -o work/tx --model medium.en

python3 creator-kit/scripts/who_speaks.py tag "cuts/01 garage walkthrough.mp4" \
  work/tx/a01.json --profile creator-kit/voice/omarie_profile.json \
  -o work/drop_01.json
```

The second command writes the time ranges where somebody else is talking. Those ranges get
dropped from the captions later. His similarity scores run 0.72 to 0.89; other people land
around 0.64; the threshold is 0.70.

## Step 3 — label the clips (optional but better)

```bash
cp creator-kit/fastcut/labels.json.example work/labels.json   # then edit it
```

Chapter bars and lower thirds use these. Without the file the build falls back to the words in
each cut's filename, which is usually good enough.

## Step 4 — build the reel

```bash
ROOT=$PWD CUTS=$PWD/cuts WORK=$PWD/work OUTDIR=$PWD/exports \
LOGO="overlays/FD-00-VERTICAL-STARTER-PACK 3/corner-logo-bugs/bug_9x16_top-right_logo-white.png" \
creator-kit/fastcut/build_reel.sh MR1 "the shop before" "THE SHOP, BEFORE ANYTHING" 01 02
```

Arguments are: reel id, slug for the filename, hook line, then the clip numbers in order.
It prints the score, any flags, the output path and a six-frame QC strip. Look at the strip
before you deliver anything.

## What each stage does

1. `plan_reel.py --target 56` picks the best window of each take by speech density, sliding the
   window back when the only speech sits late, and ignoring other people's lines when choosing.
2. `split_plan.py` breaks the plan into shots: first 3.0 s, the rest 4.5 s or less.
3. `assemble_reel.py` concatenates the shots into a master and records where every cut lands.
4. `rewords.py` maps word timings through the plan and removes the other-voice ranges.
5. `props.py` builds the overlay spec: title, chapters, lower thirds, follow cards, outro.
6. Remotion renders the overlay **alone** with alpha, as ProRes 4444.
7. `compose_reel.sh` composites overlay onto master, burns the logo bug, normalises to −14 LUFS
   and limits at 0.84.
8. `reel_check.py` scores it and flags problems.

## Known traps

- **A shell loop that runs ffmpeg or curl inside `while read` swallows the rest of the list.**
  Read from a separate file descriptor: `while read -u 3 …; done 3< list.tsv`, and give the
  tools `</dev/null`.
- **Presigned upload slots expire after about two hours.** Request each slot when its build
  starts, not up front for the whole batch.
- **Never run two builds of the same reel at once.** They write the same master file and the
  render reads a half-written file.
- **Low caption coverage is a planning problem, not a captioning problem.** If the checker says
  captions cover under half the speech, the window landed on a stretch where other people are
  talking. Pick a different window. Do not loosen the voice threshold.

## Scores from the reference batch

MR1 96, MR2 97, MR3 91, MR4 85, MR5 94, MR6 93, MR7 94, MR8 93. MR4 is low because that part
(forklift, GT3 rolling in) has very little of his own speech in it.
