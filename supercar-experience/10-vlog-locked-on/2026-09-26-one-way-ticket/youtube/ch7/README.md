# One-way ticket, chapter 7 "Sunrise · Nevada"

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 1:10.77 (2121 frames at 30000/1001; planned about
2:15). Built file-for-file on `../ch4/` so it joins straight after Ch6 (ends on 0115 "she's still doing great"). **720p proxy only** (Omarie,
2026-10-09: "do it in 720 first then 4k"); `render.py master` is kept for the 4K pass.

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch7work/`)

| file | what |
|---|---|
| `proxy_video.mp4` | 1280x720 H.264 High, yuv420p, 30000/1001, timescale 30000, bt709, crf 20 preset fast, no audio, 2121 frames (the four chapters join with a stream copy) |
| `mix.wav`, `nomusic.wav` | the two mixes, 48 kHz 24-bit, exactly 3396994 samples, 12 ms fade at head and tail |
| `gate/shotNN_*.jpg` | the pre-render frame gate on `proxy_video.mp4` (one frame every 0.3 s, 640 px tiles, 4x3, stamped chapter, shot, timeline time and source clip:time) |

## Rebuild

    cd youtube/ch7
    python3 make_edl.py                                  # -> edl.json (asserts no block flag is used)
    python3 words_medium.py && python3 words_agree.py    # medium.en timings; words both models hear -> words_agree.json
    python3 render.py raw                                # 640x360 graded, cropped, no blur -> WORK/raw_shots (the tracker reads them)
    PYTHONPATH=/home/user/day-owt/pycv python3 track_blur.py   # -> look.json blur keys
    python3 music.py /home/user/day-owt/ch7work/bed.wav 73
    python3 mix.py /home/user/day-owt/ch7work            # -> mix.wav, nomusic.wav, mix.json
    python3 render.py proxy && python3 render.py sheets  # -> proxy_video.mp4 + gate/
    python3 render.py master                             # later: 4K from VLOG_MEZZ_4K (default /home/user/owt/mezzB)

`render.py` and `mix.py` are one file shared by ch5-ch8 (WORK comes from the folder name). New since ch4: `render.py`
cuts each shot on the rounded chapter clock so the frame total equals edl `frames`, reads the title from edl.json, takes
a look.json `zoom` window and edl `rotate`, and has `raw` (tracker input) and `proxy` modes; `mix.py` sizes the wavs to
the frame count, fades head and tail 12 ms instead of zeroing the last 60 ms, mutes edl `mute` ranges, and brings the bed
up only in montage shots.

## Shots

| # | clip:in-out | chapter time | what |
|---|---|---|---|
| 0 | 0116:4.55-7.55 | 0:00.00-0:03.00 | SUNRISE, side camera, driving, under the "SUNRISE · NEVADA" title: "As of right now you see the beautiful desert..." |
| 1 | 0116:7.55-13.40 | 0:03.00-0:08.85 | CUTAWAY (windscreen zoom, same moment): "...You see that? Actually, let me take a video of that because it actually looks amazing" (the phone comes up) |
| 2 | 0116:51.95-55.09 | 0:08.85-0:11.99 | CUTAWAY (windscreen zoom; sound in sync): "186 miles till we're back home." |
| 3 | 0116:121.30-128.11 | 0:11.99-0:18.80 | SIDE CAMERA, one hand on the wheel: "We got the beautiful view to us right here. Life's been good, you feel me?" |
| 4 | 0117:74.80-81.82 | 0:18.80-0:25.82 | CUTAWAY (windscreen zoom, fields; sound in sync): "As you can see, it's just all field. And there's a flock of crows right in front of me that are about to get obliterated." |
| 5 | 0117:100.85-104.15 | 0:25.82-0:29.12 | THE HOOK IN CONTEXT (windscreen zoom; sound in sync): "No cell service, not an SOS. Crazy as [bleep]." |
| 6 | 0117:111.85-113.60 | 0:29.12-0:30.87 | JUMP: "I have to make it, we don't have a choice." |
| 7 | 0118:61.85-63.58 | 0:30.87-0:32.60 | CABIN, rear camera, driving: "Trip has been cool..." |
| 8 | 0118:69.40-73.82 | 0:32.60-0:37.02 | JUMP: "It's been pretty fire. Wow, really nice scenery." |
| 9 | 0118:75.50-88.52 | 0:37.02-0:50.04 | JUMP: "It was lots of beautiful trees and scenery and all kinds of [bleep] out in Seattle. I can't believe I just did the whole thing. No, no hotel, no nothing. That was the crazy part," |
| 10 | 0118:89.95-91.63 | 0:50.04-0:51.72 | JUMP: "but you know, we thug it out." |
| 11 | 0119:0.90-12.10 | 0:51.72-1:02.92 | PULLING IN (rear camera, both hands on the wheel): "Why ya chat, we Gucci. I'm looking at the gas station. Oh, thank the Lord. Thank the Lord, that we were toast." |
| 12 | 0119:51.90-59.75 | 1:02.92-1:10.77 | AT THE PUMP: "I ain't gonna lie, I thought we were donezo. Over with, no return, call somebody to come get us. Donezo." |

## Changes from PLAN.md, and why

* 0116 4.6-13.0: him for 3 s under the title (one hand on the wheel), then the windscreen zoom from where the phone comes up ("let me take a video of that").
* 0116 52.1-54.7, 0117 74.9-81.4 and the hook 0117 100.9-113.2: sound in sync over the windscreen zoom (look.json `zoom`: a 0.45-wide 16:9 window on the windscreen of the same camera), because the picture shows the phone in his hand or both hands off the wheel while moving (brief). The hook is 100.85-104.15 + 111.85-113.60; 7 s of silence between is cut; "fuck" (103.8-104.0) is bleeped.
* 0118 61.9-91.2 becomes 61.85-63.58 + 69.40-73.82 + 75.50-88.52 + 89.95-91.63: "is this focusing on me?" (to the camera) and two pauses are cut; "shit" (79.0-79.1) is bleeped.
* 0119 1.0-11.7 runs 0.90-12.10 ("toast." ends 11.74); 0119 52.0-59.1 runs 51.90-59.75.
* No word pop in the hook line (the brief allowed at most one): the windscreen cutaway carries it; lead to decide.
* Runtime 1:10.8 against about 2:15.

## Music

The temp bed is **original**: `music.py` (ch4's, own key and seed) synthesizes it in numpy: 84 BPM, E major, Emaj9-C#m9-Amaj9-Bsus2, seed 71. No sample,
library track or footage audio. Music comes up only in montages (brief): -39.5 LUFS everywhere else, -21 LUFS in the
montage shots, ducked under talk.

**Music-flag check:** `make_edl.py` asserts that no shot, dialog or audio range touches a flags.json block flag (music,
stranger, hands-off, phone-driving); it passes. No car-stereo, venue or PA music is used.

**Loudness:** `mix.wav` -14.0 LUFS, -1.8 dBTP; `nomusic.wav` -14.0 LUFS,
-1.8 dBTP. Voice over music: at least 18.3 dB per word (186 words, none under 12);
lowest voiced 50 ms frame 10.2 dB (0 of 1348 frames under 10).

**Tone scan** (0.5 s windows over every used range, a spectral peak holding > 40 % of the energy): see the note at the
top of `mix.py`; notches 57 Hz on 0112 (nat) and 107 Hz on 0123 (nat and dialog), applied before levelling.

**Cuts:** every in and out was set from the voice-band envelope and both ASR models' word times, 0.5 s either side
(the driving clips 0116-0118 from word times only: road and wind fill the voice band).

**Speakers:** 0118 "No," at 83.22 scores OTHER 0.19; it is inside his sentence ("No, no hotel, no nothing"). Every other used line is HOST.

## Blur (Omarie, 2026-10-09: "only blur should be the dash")

* s00 (0:00.00-0:03.00) and s03 (0:11.99-0:18.80), 0116 side camera, moving: a static round box over the driver cluster, seen edge-on behind the wheel ([0.68, 0.50, 0.13, 0.18] of the frame), the whole shot.
* s07-s10 (0:30.87-0:51.72), 0118 rear camera, moving: centre screen and cluster, template-tracked every frame (scores: screen median 0.88-0.90, cluster 0.95-0.99; s09 has one lost screen frame that holds the last box).
* s11 (0:51.72-1:02.92), 0119 pulling in, moving: centre screen and cluster, tracked (median 0.96 / 0.90).
* The windscreen zooms (s01, s02, s04-s06) show no dash readout; s12 (0119 at the pump) is parked: no blur.

## Hands check

Checked on the 0.3 s gate tiles: s00 one hand on the wheel (the other gesturing); s03 one hand on the wheel, the other at his chest; s07-s10 one hand on the wheel, the other gesturing by the console (no phone seen); s11 both hands on the wheel. Every phone-in-hand moment of 0116/0117 is under the windscreen cutaway. nq-check to confirm on the sheets (tiles at 640 px).

## Captions

`words_agree.json`: 171 words both small.en and medium.en hear, chapter times. Gaps (small.en words medium.en
does not confirm): 8.97 (0116 52.07 "186"); 45.48 (0118 83.96 "no").

## For nq-facts

* Title "SUNRISE · NEVADA": sunrise from the footage and the 06:24 camera clock; Nevada from PLAN.md chapter 7 (nq-facts to confirm the state at 0116).
* Spoken: "186 miles till we're back home" (0116 52), "no cell service, not an SOS" (0117), "out in Seattle" (0118), "no hotel".
