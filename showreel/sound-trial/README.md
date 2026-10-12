# Showreel sound trial: recorded CC0 sounds in place of the synth hits

This is an A/B trial. The 15 s showreel's picture and score stay as they are, and the 95 synthesized hits from
`audio/synth.py` are swapped for recordings from the 1,139-sound CC0 kit of
[opus-sound-layer](https://github.com/Bodila51/opus-sound-layer) (commit `52ac266`, 2026-10-10). The synth
version in `dist/showreel.mp4` is unchanged. Listen to both, starting with [LISTEN.md](LISTEN.md).

The trial mp4 (13.9 MB) is delivered separately and isn't committed. Rebuild it with the steps below.

## What's here

| file | what |
|---|---|
| `convert.py` | turns the picture's own cue export (`audio/cues.json`, from `tools/cues.mjs`) into a sound-layer cue sheet. Each synth type maps to a sound picked with `sfx.py browse`, and the comments give the reason for each round's change |
| `cues.json` | the cue sheet that was mixed: 50 cues, 4 of them heroes |
| `mix-report.json` | the mixer's report: gain, alignment and band for every event, plus master loudness |
| `qa-report.json`, `qa.png` | `qa.py`'s results and its picture (waveform, spectrogram and motion, with every cue marked) |
| `CREDITS.md` | the 28 recordings the mix plays |
| `LISTEN.md` | five timecodes to check by ear, and every sound left out |

## Rebuild

```sh
git clone https://github.com/Bodila51/opus-sound-layer sound-layer   # outside this repo
mkdir -p trial/audio trial/out && cd trial
uv run -q ../sound-layer/scripts/sfx.py kit                           # audio/kit: 1,139 CC0 sounds
(cd <repo>/showreel && python3 audio/synth.py --mute hits --out <trial>/audio/music.wav)  # score + its swells
python3 <repo>/showreel/sound-trial/convert.py <repo>/showreel/audio/cues.json audio/cues.json
ffmpeg -y -i <repo>/showreel/dist/showreel.mp4 -map 0:v -c:v copy video.mp4
uv run -q ../sound-layer/scripts/mix.py audio/cues.json
ffmpeg -y -i video.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out/final.mp4
uv run -q ../sound-layer/scripts/qa.py out/final.mp4
```

`--mute hits` mutes the synth's sound effects but keeps three things: its music-bus edits (the glitch and
tape-stop), its duck under each hit, and the swells it lets through the score's two dead stops (before the drop at
7.27–7.50 s and before the final hit at 13.01–13.13 s). `--mute sfx` mutes those swells too, which is what
left the gap before the drop in rounds 1–3.

## What the checks show

The trial followed the sound-layer prompt: fix FAILs by changing cues or sounds, for at most 2 rounds, without
touching the scripts or the thresholds. Round 4 came after the A/B, by request, to fill the gap before the drop.

| run | cues | FAIL | what changed |
|---|---|---|---|
| round 1 | 102 | 59 | first pass: one sound per synth event |
| round 2 | 75 | 33 | faster-rising hero layers, brighter whooshes, one key per typing burst, louder overrides for buried sounds, clusters thinned |
| round 3 | 51 | 11 | sounds measured as buried in round 2 dropped, the cold open aligned to frame 0, a new boom under the final hit |
| fix | 52 | 11 | a bug, not a tuning round: the per-time sound overrides also caught the swells ending at those times, so reverse-7.500 played a shimmer and the whooshes at 11.13 and 12.19 played a cork pop. Each swell now plays its own family, and reverse-8.438 (dropped after being measured on the wrong file) is back |
| round 4 | 50 | 11 | the gap before the drop filled: the bed now keeps the synth's own swells through the score's dead stops (`--mute hits`), and the two recorded reverses that landed there (reverse-7.500 and reverse-13.125, solved at −41 and −46 dB against a silent bed) are dropped. 7.20–7.47 s now averages −24.2 dB, against −25.3 dB in the synth version and −51.5 dB before |

Final run, passing:
- offset 0 ms
- −14.10 LUFS
- true peak −1.87 dBTP
- music level steady, no dips
- no silences flagged
- the unfold, drop and final hit 0 frames from their cues; the cold open starts on frame 0 (start-aligned, so QA has no sync row for it)
- the drop's picture cut on frame 450

The 11 FAILs left:
- audible, under the score in their own band (needs 1.5 dB):
  - tick-3.047: 1.0 dB
  - impact-8.438: 0.7 dB
  - blip-9.609: 1.5 dB
  - whoosh-11.133: 0.8 dB
  - glitch-11.953: 1.2 dB
  - whoosh-12.188: 0.7 dB
  - key-12.188: 1.3 dB
- sync: tick-6.357 (2.12 frames), blip-10.898 (2.85 frames), pop-13.594 (3.04 frames, under the braam's tail)
- hero body: final-hit lifted 2.1 dB in 125–250 Hz (needs 3). Swapping its boom in round 3 took it from 2.9 to 2.1.

The 5 warnings: the landing pops at 2.344, 2.578, 2.812, 2.930 and 13.594 sit where the picture's whole-frame
motion doesn't stop. The landing dot is too small to register.

Round 4 changed no FAIL. The drop now stands out by 5.0 dB (it was 6.7 dB), because the swell runs right up to it.
That's still a pass.

Why rounds 1–3 had the gap: the mixer gives each support sound the smallest gain that lifts it over the bed, and it
floors a silent bed at −60 dB. A sound placed inside a dead stop is therefore nearly silent. The swell has to come
from the bed.
