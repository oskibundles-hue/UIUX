# One-way ticket, chapter 6 "1:29 a.m."

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 0:46.15 (1383 frames at 30000/1001; planned about
1:15). Built file-for-file on `../ch4/` so it joins straight after Ch5 (ends on 0112 "It's light work"). **720p proxy only** (Omarie,
2026-10-09: "do it in 720 first then 4k"); `render.py master` is kept for the 4K pass.

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch6work/`)

| file | what |
|---|---|
| `proxy_video.mp4` | 1280x720 H.264 High, yuv420p, 30000/1001, timescale 30000, bt709, crf 20 preset fast, no audio, 1383 frames (the four chapters join with a stream copy) |
| `mix.wav`, `nomusic.wav` | the two mixes, 48 kHz 24-bit, exactly 2215013 samples, 12 ms fade at head and tail |
| `gate/shotNN_*.jpg` | the pre-render frame gate on `proxy_video.mp4` (one frame every 0.3 s, 640 px tiles, 4x3, stamped chapter, shot, timeline time and source clip:time) |

## Rebuild

    cd youtube/ch6
    python3 make_edl.py                                  # -> edl.json (asserts no block flag is used)
    python3 words_medium.py && python3 words_agree.py    # medium.en timings; words both models hear -> words_agree.json
    python3 music.py /home/user/day-owt/ch6work/bed.wav 48
    python3 mix.py /home/user/day-owt/ch6work            # -> mix.wav, nomusic.wav, mix.json
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
| 0 | 0114:3.70-5.65 | 0:00.00-0:01.95 | NIGHT CABIN (parked, Club 93 lot), under the "1:29 A.M." title: "I'm not gonna lie, chat," |
| 1 | 0114:7.40-11.15 | 0:01.95-0:05.70 | JUMP: "I definitely did take a nice McLaren nap." |
| 2 | 0114:13.20-16.95 | 0:05.70-0:09.45 | JUMP: "I'm in the Club 93 parking lot." |
| 3 | 0114:19.70-22.85 | 0:09.45-0:12.60 | JUMP: "Pretty nice parking lot. Reminds me of Vegas." |
| 4 | 0114:25.60-30.75 | 0:12.60-0:17.75 | JUMP: "I took a nice, supposed to be hour nap, probably hour and 30 minute nap." |
| 5 | 0114:87.80-89.25 | 0:17.75-0:19.20 | CABIN (parked, phone in hand): "My wrist hurts." |
| 6 | 0115:1.78-15.02 | 0:19.20-0:32.44 | GAS STOP, 02:46 (selfie, camera on its side: turned upright): "Alright chat, so we're about six hours out, six-five hours out, gassing up. Dude, it is freezing." |
| 7 | 0115:31.15-37.20 | 0:32.44-0:38.49 | JUMP: "Whoo, six more hours it is. When I say it's cold, it's cold outside, like it's really cold outside, so" |
| 8 | 0115:15.00-22.65 | 0:38.49-0:46.14 | END (back in the take): "I'm not gonna lie to you, car still holding up good, brand new engine in her, she's still doing great." |

## Changes from PLAN.md, and why

* 0114 3.9-30.5 becomes five pieces (3.70-5.65, 7.40-11.15, 13.20-16.95, 19.70-22.85, 25.60-30.75): the pauses between the lines go.
* 0114 87.9-89 runs to 89.25 so "hurts" is whole.
* 0115 2.3-14.7 starts at 1.78 ("Alright", medium.en from 1.96) and runs to 15.02 ("freezing" ends 15.04).
* 0115 30.7-36.8 becomes 31.15-37.20 (the line starts at 31.2; the rotate note in PLAN is covered: the whole clip is on its side and is turned upright, transpose cw).
* The chapter ends on 0115 15.00-22.65 "...she's still doing great": the brief's 14.7-30.7 ending, cut at "great" (22.28); 24-29.6 ("post it up at the uh, what is this, Sinclair...") is cut. It plays after 31.15-37.20, so clock order breaks for this one line (the brief asked to keep clock order; the line is the better last word for the setback). Lead to decide; swapping shots 7 and 8 restores clock order. **Decided (Omarie, 2026-10-09, click):** "Keep it": the chapter ends on "she's still doing great".
* Runtime 0:46.1 against about 1:15.

## Music

The temp bed is **original**: `music.py` (ch4's, own key and seed) synthesizes it in numpy: 66 BPM, C minor, Cm9-Abmaj7-Fm9-Gsus4, seed 61, low-pass 900 Hz, one pluck every other bar, kick on beat 1 only, no shaker (the setback: darker and sparser). No sample,
library track or footage audio. Music comes up only in montages (brief): -39.5 LUFS everywhere else, -21 LUFS in the
montage shots, ducked under talk.

**Music-flag check:** `make_edl.py` asserts that no shot, dialog or audio range touches a flags.json block flag (music,
stranger, hands-off, phone-driving); it passes. No car-stereo, venue or PA music is used.

**Loudness:** `mix.wav` -14.03 LUFS, -1.8 dBTP; `nomusic.wav` -14.04 LUFS,
-1.8 dBTP. Voice over music: at least 18.3 dB per word (102 words, none under 12);
lowest voiced 50 ms frame 11.3 dB (0 of 703 frames under 10).

**Tone scan** (0.5 s windows over every used range, a spectral peak holding > 40 % of the energy): see the note at the
top of `mix.py`; notches 57 Hz on 0112 (nat) and 107 Hz on 0123 (nat and dialog), applied before levelling.

**Cuts:** every in and out was set from the voice-band envelope and both ASR models' word times, 0.5 s either side
(the driving clips 0116-0118 from word times only: road and wind fill the voice band).

**Speakers:** Every used line is HOST.

## Blur (Omarie, 2026-10-09: "only blur should be the dash")

None. 0114 is parked (Club 93 lot) and 0115 is on foot at the pump, so no dash blur.

## Hands check

No driving frames (0114 parked, 0115 on foot).

## Captions

`words_agree.json`: 88 words both small.en and medium.en hear, chapter times. Gaps (small.en words medium.en
does not confirm): 19.73 (0115 2.31 "Alright"); 32.11 (0115 14.69 "I'm").

## For nq-facts

* Title "1:29 A.M.": from the DJI camera clock on 0114 (time zone as the camera was set; PLAN.md chapter 6). nq-facts to confirm the zone.
* Spoken: "Club 93 parking lot" (0114), "about six hours out, six-five hours out" (0115 1.8), "six more hours" (0115 31.2), "brand new engine in her" (0115 19).
