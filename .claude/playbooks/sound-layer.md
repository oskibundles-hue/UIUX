# Playbook: Sound layer (recorded sound effects synced to picture)

Hits, booms, whooshes, UI ticks and pops placed on a video's own timing, from real recordings, with a QA that
checks each one. It uses [opus-sound-layer](https://github.com/Bodila51/opus-sound-layer): MIT scripts and a
1,139-sound CC0 kit. Any workstream can use it, with the workstream's own music, loudness and brand. Read by
`nq-build`, `nq-fix` and `nq-check` when the brief names this playbook.

Added 2026-10-12, after the showreel A/B (PR #54, `showreel/sound-trial/`). Omarie heard the recorded version
against the synth one and asked for it in the playbooks. That folder is the worked example. Its `convert.py`
turns the picture's own cue export (`showreel/audio/cues.json`) into a cue sheet, and its README lists every
round and what each one changed.

## Setup

- Clone it **outside the repo**, into the scratchpad, and check out the reviewed commit:
  `git clone https://github.com/Bodila51/opus-sound-layer sound-layer && git -C sound-layer checkout 52ac266`.
  It's third-party code that downloads files. Read the diff before moving to a newer commit, and never vendor
  the scripts into this repo.
- Needs `ffmpeg` and `uv`; run every script as `uv run -q sound-layer/scripts/<script>.py`.
- `sfx.py kit` downloads the kit on its first run. Run it in the background with a 10-minute timeout.
- The scripts' own prompt is `sound-layer/PROMPT.md`. Its rules stand, and the sections below add what the
  showreel trial taught.

## The run

1. **Music bed** as `audio/music.wav`: the workstream's own track or score, with its sound effects muted.
2. **Cues** in `audio/cues.json`, generated from the picture's own timing (springs, easings, cut frames).
   Never type frames by hand. `mix.py --schema` prints the format. Tag each cue `cut`, `move`, `land` or
   `appear`, and give a cue `weight: hero` only for the big moments, about one every 4 s.
3. **Sounds:** pick every one with `sfx.py browse --type <type> --like "<material, weight, mood>"`, look
   at `audio/browse.png`, and put the id in the cue. Keep one sonic family per film. A sound from outside
   the kit needs a licence that allows it, and it goes in through `sfx.py add --credit`.
4. **Build:** `mix.py audio/cues.json`, then
   `ffmpeg -i video.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out/final.mp4`,
   then `qa.py out/final.mp4`. Pipe the logs through `tail` or `grep`.
5. **Fix** each FAIL by changing cues or sounds, **at most 2 rounds**. Never edit the scripts or loosen a
   threshold, because then the QA no longer measures anything.
6. **Deliver** the video with `CREDITS.md` and a `LISTEN.md` of 5 timecodes to check by ear. When it already
   has a sound version, deliver both for an A/B. Report what the checks show and never call the sound good.
   Videos go through the Dropbox / Video Drop rules in `CLAUDE.md`.

## What the showreel trial taught

- **A sound placed inside a silence comes out nearly silent.** The mixer gives each support sound the
  smallest gain that lifts it over the bed, and it floors a silent bed at −60 dB. So a reverse ending in the
  dead stop before the drop was mixed at −41 dB. Keep the swell in the music bed instead (the showreel's
  `synth.py --mute hits`), and leave no recorded sound ending inside a silence.
- **The cue sheet has no volume control for a hit.** The mixer solves each hero's gain itself, from its main
  band (a 5 dB lift with `energy: punchy`). QA's hero check needs 3 dB there, and the showreel's heroes
  measured 2.1 to 3.9. A heavier hit has to come from layering (`"sound": "hit/a+boom/b+boom/c"`, which
  lines up the layers' peaks).
- **Pick layers by mixing the options side by side.** Make a copy of the folder for each layer set, with the
  kit, bed and video symlinked and only the hero's `sound` changed. Run them in parallel and compare the
  hero check, the FAIL count and `ffmpeg -af volumedetect` over the hit against the old version. Six sets for
  the final hit took a few minutes on 4 CPUs.
- **The ear can overrule the QA, and that's Omarie's call.** For the final hit he picked bass drop +
  rugged sub, the loudest set, though it fails the hero check (2.5 of 3 dB). Give him the passing set and
  the louder set with the numbers, and write down which one he picked and why.
- **In a busy passage, drop the small sounds the QA measures as buried** rather than forcing them up. Thin out
  sounds that peak within 60 ms of one that carries the action.
- **Key per-cue overrides by cue id or type, never by time alone.** An override keyed by time also caught
  the swells ending at that time, so a reverse played a shimmer.
- **A hit on frame 0 needs `align: start`,** because there's no room before frame 0 for the run-up to its
  peak. QA then has no sync row for it.
- **Keep the picture untouched.** Mux with `-c:v copy` and compare the video stream's MD5 against the
  original (`ffmpeg -i f.mp4 -map 0:v -c copy -f md5 -`), so the A/B changes only the sound.
