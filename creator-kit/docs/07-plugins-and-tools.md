# Plugins and tools: what is worth installing

Short version: nothing needs installing for the pipeline here. Everything I
run (window selection, grade match, silence cut, captions, compose) is
ffmpeg, Python and Remotion inside this session. The list below is for
**your** machine, for the days you grade or edit by hand.

## Colour (DaVinci Resolve)

| Tool | What it does for you | Verdict |
|---|---|---|
| **DaVinci Resolve Studio** (paid, one-off) | Unlocks noise reduction, Magic Mask, Resolve Color Management, and 4K 60 timelines without the free-tier limits. The free version cannot temporal-denoise D-Log M shadows, and that is the single biggest quality lever on Osmo footage. | Buy this before any plugin |
| **DJI D-Log M to Rec.709 LUT** (free, dji.com/lut) | The manufacturer's own conversion. Use it as the first node, then grade on top. Guessing the log curve by eye is how flat, grey footage happens. | Install |
| **Resolve Color Management, DaVinci Wide Gamut** | Set the input colour space per clip to "DJI D-Log M" and Resolve does the conversion mathematically, no LUT needed. Cleaner highlights than the LUT. | Use this instead of the LUT once you are comfortable |
| **Colourlab Ai** (paid) | Grade-matching: point it at a reference and it matches your shots to it, which is what `match_grade.py` does here. Worth it if you grade a lot of clips by hand. | Optional |
| **Dehancer** or **FilmConvert Nitrate** (paid) | Film-stock emulation with grain and halation. Only if you want that look; your approved reference does not have it. | Skip for now |
| **Neat Video** (paid) | Best temporal denoiser available. Resolve Studio's built-in one is close enough for this footage. | Skip unless you stay on the free Resolve |

## Editing

| Tool | Why | Verdict |
|---|---|---|
| **Instagram Edits app** | Upload path that keeps 4K sharpest, as already in the workflow. | Keep |
| **Resolve Studio transcription** (Speech to Text) | Built-in word-level transcripts for cutting by text. Same job as `transcribe.py` here. | Comes with Studio |
| **CapCut Pro** | Fast phone captions. The caption look here was measured off a CapCut-style edit, so it stays consistent. | Only if you edit on the phone |

## Do not bother

- LUT packs sold as "cinematic looks". Your look is already measured and reproducible.
- Auto-reframe plugins. Everything is shot vertical.
- AI upscalers. The source is 4K; upscaling adds nothing.

## What would actually speed things up

1. Shoot with **orientation lock on** (clip 12 was inverted).
2. Keep the Osmo at **4K 60 D-Log M, 10-bit**, shutter at 1/120 in the shop. Consistent exposure makes the per-clip grade match tighter.
3. Say the car and the job out loud on camera. The captions and spec cards come from what you say, and a name spoken on camera is worth a lot more than one typed on later.
