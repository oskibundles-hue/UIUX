# One-way ticket, chapter 5 "Nampa, Idaho · night"

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 0:57.22 (1715 frames at 30000/1001; planned about
1:45). Built file-for-file on `../ch4/` so it joins straight after Ch4 (ends on 0100 "We're in Oregon!"). **720p proxy only** (Omarie,
2026-10-09: "do it in 720 first then 4k"); `render.py master` is kept for the 4K pass.

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch5work/`)

| file | what |
|---|---|
| `proxy_video.mp4` | 1280x720 H.264 High, yuv420p, 30000/1001, timescale 30000, bt709, crf 20 preset fast, no audio, 1715 frames (the four chapters join with a stream copy) |
| `mix.wav`, `nomusic.wav` | the two mixes, 48 kHz 24-bit, exactly 2746744 samples, 12 ms fade at head and tail |
| `gate/shotNN_*.jpg` | the pre-render frame gate on `proxy_video.mp4` (one frame every 0.3 s, 640 px tiles, 4x3, stamped chapter, shot, timeline time and source clip:time) |

## Rebuild

    cd youtube/ch5
    python3 make_edl.py                                  # -> edl.json (asserts no block flag is used)
    python3 words_medium.py && python3 words_agree.py    # medium.en timings; words both models hear -> words_agree.json
    python3 music.py /home/user/day-owt/ch5work/bed.wav 59
    python3 mix.py /home/user/day-owt/ch5work            # -> mix.wav, nomusic.wav, mix.json
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
| 0 | 0102:17.50-25.90 | 0:00.00-0:08.40 | OREGON GAS STOP (selfie stick, parked): "As you can see I got my Red Bull and my snacks because we are going to starve ourselves until we can get to In-N-Out, that's the goal." |
| 1 | 0102:58.45-63.12 | 0:08.40-0:13.07 | SELFIE at the pump: "I don't think I'm going to go to sleep. I think I'm just gonna run it the whole way there." |
| 2 | 0105:4.92-6.78 | 0:13.07-0:14.93 | NIGHT, In-N-Out lot (selfie), under the "NAMPA, IDAHO · NIGHT" title: "We finally made it." |
| 3 | 0105:7.70-11.82 | 0:14.93-0:19.05 | JUMP: "To In-N-Out. Appreciate you. Thank you. We finally gonna eat." |
| 4 | 0105:12.45-14.22 | 0:19.05-0:20.82 | JUMP (past "God damn"): "I've been trying to eat all day." |
| 5 | 0106:283.30-296.88 | 0:20.82-0:34.40 | LOT (camera on the car, parked; he leans on it with his phone): "...to let you know where I'm at, I am in Nampa, Idaho, currently at Treasure Valley Marketplace just west of Boise, looking at about 300 miles from Sandy, five hours away." |
| 6 | 0107:232.30-238.06 | 0:34.40-0:40.16 | IN-N-OUT TABLE (static, eating): "I gotta have to put some actual oil inside the car because like it's been like over 500 miles." |
| 7 | 0112:13.75-19.85 | 0:40.16-0:46.26 | CABIN (parked at the pump, door up): "We gots up, shawty! You feel me? We are gassed up, we are ready to leave." |
| 8 | 0112:23.10-26.45 | 0:46.26-0:49.61 | JUMP: "So, right here as you can see." (shows the route on his phone) |
| 9 | 0112:27.95-35.58 | 0:49.61-0:57.24 | JUMP (past "Oh shit"): "We got 9 hours, 27 minutes to go. It's light work." |

## Changes from PLAN.md, and why

* 0102 17.4-25.4 starts at 17.50: "Oregon" (the end of "we are in Oregon") runs to 17.48 (medium.en), so the piece starts on "As you can see".
* 0102 58.3-62.7 starts at 58.45, after "break." (the previous sentence).
* 0105 4.9-13.8 becomes 4.92-6.78, 7.70-11.82 and 12.45-14.22: the 1.3 s pause before "To In-N-Out" and "God damn" (11.90-12.30, flags.json profanity) are cut.
* 0112 13.8-32.6 becomes 13.75-19.85, 23.10-26.45 and 27.95-35.58: "Oh shit" (26.5-27.1) and a door/chime run (20.1-22.2) are cut; the last piece runs to "It's light work" (35.3), past the plan's 32.6, so the chapter ends on a whole line.
* The "NAMPA, IDAHO · NIGHT" title sits on the first night shot (0105, 0:13.07), not on 0102, which is the Oregon gas stop in daylight.
* Runtime 0:57.2 against the plan's about 1:45: cut to the content, no padding (brief).

## Music

The temp bed is **original**: `music.py` (ch4's, own key and seed) synthesizes it in numpy: 80 BPM, G major, Gmaj9-Em9-Cmaj9-Dsus2, seed 51. No sample,
library track or footage audio. Music comes up only in montages (brief): -39.5 LUFS everywhere else, -21 LUFS in the
montage shots, ducked under talk.

**Music-flag check:** `make_edl.py` asserts that no shot, dialog or audio range touches a flags.json block flag (music,
stranger, hands-off, phone-driving); it passes. No car-stereo, venue or PA music is used.

**Loudness:** `mix.wav` -14.01 LUFS, -1.8 dBTP; `nomusic.wav` -14.0 LUFS,
-1.8 dBTP. Voice over music: at least 14.5 dB per word (159 words, none under 12);
lowest voiced 50 ms frame 10.1 dB (0 of 1016 frames under 10).

**Tone scan** (0.5 s windows over every used range, a spectral peak holding > 40 % of the energy): see the note at the
top of `mix.py`; notches 57 Hz on 0112 (nat) and 107 Hz on 0123 (nat and dialog), applied before levelling.

**Cuts:** every in and out was set from the voice-band envelope and both ASR models' word times, 0.5 s either side
(the driving clips 0116-0118 from word times only: road and wind fill the voice band).

**Speakers:** 0112 "You feel me?" (16.1-16.8) scores OTHER 0.33 on the speaker model; by ear on the ASR it is his line mid-sentence ("We gassed up, shawty! You feel me?"). Every other used line is HOST.

## Blur (Omarie, 2026-10-09: "only blur should be the dash")

None. Every shot is parked or on foot (0102 gas stop, 0105 In-N-Out lot, 0106 lot, 0107 table, 0112 parked at the pump with the door up), so no dash blur under the 2026-10-09 rule.

## Hands check

No driving frames in this chapter (0112 is parked at the pump: the door is up).

## Captions

`words_agree.json`: 132 words both small.en and medium.en hear, chapter times. Gaps (small.en words medium.en
does not confirm): 40.22 (0112 13.81 "We"); 42.54 (0112 16.13 "You"); 42.54 (0112 16.13 "feel"); 42.84 (0112 16.43 "me?").

## For nq-facts

* Title "NAMPA, IDAHO · NIGHT": he says "I am in Nampa, Idaho" (0106 286.8); night from the footage.
* Spoken (stay spoken, not on screen): "Treasure Valley Marketplace just west of Boise", "about 300 miles from Sandy, five hours away" (0106), "over 500 miles" (0107), "9 hours 27 minutes to go" (0112).
* On screen in the footage: his phone's nav map in 0112 (0:46.3-0:49.6) shows a route and an arrival time ("6:43 AM" in the frame); it is footage, not a graphic, but it is a figure on screen: lead to decide (crop, keep, or cut shot 8). **Decided (Omarie, 2026-10-09, click):** "Keep it": the nav map stays as filmed.
* "In-N-Out" is named (spoken and the restaurant sign in 0105).
