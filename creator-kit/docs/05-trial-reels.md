# Trial Reels: combine, caption, check

A Trial Reel is shown to non-followers only, so it is the honest test of a
cut. Anything over three minutes will not be recommended; 30–60 seconds is
the target for a shop-day story.

The pipeline takes finished exports (already cut, graded and white-balanced)
and joins ordered pieces of them into one Reel with captions, punch-ins, a
hook card, an end card and the brand's logo bug. Footage order is never
changed: segments are listed in shooting order and the assembler keeps it.

## Steps

```bash
# 1. Transcribe the exports you plan to draw from (word timings, once per clip)
python3 scripts/transcribe.py exports/09*.mp4 exports/14*.mp4 ... -o trial/

# 2. Write the plan: which clip, which seconds, in order
#    (see trial/plan.json in this session for the shape)

# 3. Join the segments and carry the words onto the new timeline
python3 scripts/assemble_reel.py trial/plan.json trial/master.mp4 trial/props.json

# 4. Add hook / handle / endCard / punches to props.json, then render the
#    GRAPHICS ONLY on alpha (set "overlayOnly": true in a copy of the props)
cd remotion && REMOTION_ALPHA=1 npx remotion render src/index.ts Reel4K out/overlay.mov \
  --props=../trial/props_overlay.json --codec=prores --prores-profile=4444 \
  --pixel-format=yuva444p10le --image-format=png \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell

# 5. One pass: footage + look LUT + punch-ins + graphics + logo + sharpen + loudness
scripts/compose_reel.sh trial/master.mp4 remotion/out/overlay.mov trial/props.json \
  exports/trial.mp4 --lut luts/AK_Film_Test_Match.cube \
  --logo "overlays/FD-00-VERTICAL-STARTER-PACK 3/corner-logo-bugs/bug_9x16_top-right_logo-white.png"

# 6. Pre-flight
python3 scripts/reel_check.py exports/trial.mp4 --props trial/props.json
```

Why the graphics are rendered separately: the first version pushed the
footage itself through Remotion (JPEG frame capture, then another H.264
encode) and then a size-capped delivery encode. Three lossy generations at
4K read as soft. Now the footage is decoded from the master once and encoded
once, at CRF 17 with a 28 Mbps ceiling instead of a 75 MB target; files land
around 150-200 MB, still inside the 10-35 Mbps upload window.

## The plan file

```json
{
  "fps": 29.97,
  "fix": {"Astin": "Aston"},
  "segments": [
    {"clip": "exports/09 gt3 rolling in.mp4", "words": "trial/a09.json",
     "in": 0.0, "out": 3.6, "captions": false},
    {"clip": "exports/09 gt3 rolling in.mp4", "words": "trial/a09.json",
     "in": 38.9, "out": 42.7}
  ]
}
```

`in`/`out` are seconds in the export's own timeline. `captions: false` keeps
a segment silent on screen (an establishing shot, a garbled line). `fix`
corrects the transcriber's spelling of names; the words are otherwise
verbatim, because putting words in the speaker's mouth is worse than a gap.

## Props the renderer understands

| Prop | What it does |
|---|---|
| `words` | Word-level captions from the assembler. Wins over `phrases`. |
| `hook` | Text card at frame one, gone by 2.6s. |
| `punches` | `[{at, hold, scale}]` quick zooms on a beat. Two or three per minute. |
| `handle` | Small watermark, top left. |
| `endCard` / `endCardAt` | One line aimed at sends, over the last beat. |
| `durationSeconds` | Sizes the composition; written by the assembler. |

## reel_check.py

Scores what the ranking rewards and the file can show: length, hook speed
(text at 0s, first speech, first cut), shot rhythm against the ~4s reference,
caption coverage of speech, loudness, dark frames, and the delivery spec.
80+ is post-ready; 60–79 fix the flags; under 60 rework.

It cannot judge whether the content is interesting. Higgsfield's
`virality_predictor` would be the second opinion for that (hook strength,
attention, retention risk), but it needs the Basic plan and accepts only
clips of 16s or shorter, so the test would be the hook excerpt, not the
Reel. Not available on the current free account; the local checker is the
gate until that changes.
