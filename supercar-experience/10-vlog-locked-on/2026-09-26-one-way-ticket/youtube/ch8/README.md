# One-way ticket, chapter 8 "Las Vegas"

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 1:23.25 (2495 frames at 30000/1001; planned about
1:45). Built file-for-file on `../ch4/` so it joins straight after Ch7 (ends on 0119 "Donezo."). **720p proxy only** (Omarie,
2026-10-09: "do it in 720 first then 4k"); `render.py master` is kept for the 4K pass.

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch8work/`)

| file | what |
|---|---|
| `proxy_video.mp4` | 1280x720 H.264 High, yuv420p, 30000/1001, timescale 30000, bt709, crf 20 preset fast, no audio, 2495 frames (the four chapters join with a stream copy) |
| `mix.wav`, `nomusic.wav` | the two mixes, 48 kHz 24-bit, exactly 3995992 samples, 12 ms fade at head and tail |
| `gate/shotNN_*.jpg` | the pre-render frame gate on `proxy_video.mp4` (one frame every 0.3 s, 640 px tiles, 4x3, stamped chapter, shot, timeline time and source clip:time) |

## Rebuild

    cd youtube/ch8
    python3 make_edl.py                                  # -> edl.json (asserts no block flag is used)
    python3 words_medium.py && python3 words_agree.py    # medium.en timings; words both models hear -> words_agree.json
    python3 music.py /home/user/day-owt/ch8work/bed.wav 85
    python3 mix.py /home/user/day-owt/ch8work            # -> mix.wav, nomusic.wav, mix.json
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
| 0 | 0119:84.60-92.00 | 0:00.00-0:07.40 | SHELL STATION SELFIE (parked): "Pahranagat Valley, we are about an hour and some change from Vegas. We're in the final countdown." |
| 1 | 0119:227.50-234.20 | 0:07.40-0:14.10 | AT THE PUMP: "Man, so I think for the last bit of the drive, I'm gonna have you guys like in the back" |
| 2 | 0121:80.00-82.40 | 0:14.10-0:16.50 | MONTAGE rear deck: leaving the station |
| 3 | 0121:87.00-89.40 | 0:16.50-0:18.90 | MONTAGE rear deck: the truck stop |
| 4 | 0121:93.50-95.90 | 0:18.90-0:21.30 | MONTAGE rear deck: trees |
| 5 | 0121:99.00-101.40 | 0:21.30-0:23.70 | MONTAGE rear deck: the green road |
| 6 | 0121:107.00-109.40 | 0:23.70-0:26.10 | MONTAGE rear deck: the desert hills |
| 7 | 0121:115.00-117.60 | 0:26.10-0:28.70 | MONTAGE rear deck: the valley |
| 8 | 0122:42.40-47.77 | 0:28.70-0:34.07 | REAR CAMERA (sound in sync): "Alright, we're almost to the shop... minutes out." (the number differs between small.en and medium.en: not captioned) |
| 9 | 0122:552.60-555.60 | 0:34.07-0:37.07 | MONTAGE skyline, under the "LAS VEGAS" title (0:34.67-0:37.97): Las Vegas behind, the dump truck closing in |
| 10 | 0122:558.50-561.50 | 0:37.07-0:40.07 | MONTAGE skyline: cars passing |
| 11 | 0122:565.00-568.00 | 0:40.07-0:43.07 | MONTAGE skyline |
| 12 | 0122:584.00-587.00 | 0:43.07-0:46.07 | MONTAGE skyline |
| 13 | 0122:594.50-597.50 | 0:46.07-0:49.07 | MONTAGE skyline: the van passing |
| 14 | 0123:4.90-12.02 | 0:49.07-0:56.19 | BACK AT THE SHOP: "we just got back to the shop. Joey and John here. I swear we got that last part. I don't know what we got, honestly," |
| 15 | 0123:17.05-24.20 | 0:56.19-1:03.34 | JUMP: "Hopefully I got the driving part. Damn. The last little driving piece is pretty gnarly. I'm not gonna lie." |
| 16 | 0123:39.90-59.80 | 1:03.34-1:23.24 | THE OUTRO (as filmed): "So that concludes today's episode... And until next time, peace." |

## Changes from PLAN.md, and why

* 0119 84.9-91.5 starts at 84.60 ("Pahranagat" from 84.64 in medium.en).
* 0119 227.8-245 becomes 227.50-234.20: 238.5-245 says "in the back" twice more.
* 0121 80-120: a montage of six 2.4-2.6 s pieces (bed up; the montage carries the road sound at -22 LUFS).
* 0122 43.3-47.4 starts at 42.40: medium.en hears "Alright, we're almost to the shop" from 42.49.
* Skyline 0122 552-570 and 582-600: five 3 s pieces, bed up, camera sound muted (flags.json car-stereo blocks at 510-552 and 570-582 either side).
* 0123 4.1-12.4 becomes 4.90-12.02 ("Apparently not, but" answers someone before the clip; it ends on "honestly,").
* 0123 17.1-27.2 becomes 17.05-24.20: "Pretty, pretty gnarly" repeats the line.
* The outro 39.9-59.4 runs as filmed to 59.80 ("peace." ends 59.40).
* Runtime 1:23.2 against about 1:45.

## Music

The temp bed is **original**: `music.py` (ch4's, own key and seed) synthesizes it in numpy: 86 BPM, B-flat major, Bbmaj9-Gm9-Ebmaj9-Fsus2, seed 81. No sample,
library track or footage audio. Music comes up only in montages (brief): -39.5 LUFS everywhere else, -21 LUFS in the
montage shots, ducked under talk.

**Music-flag check:** `make_edl.py` asserts that no shot, dialog or audio range touches a flags.json block flag (music,
stranger, hands-off, phone-driving); it passes. No car-stereo, venue or PA music is used.

**Loudness:** `mix.wav` -14.0 LUFS, -1.8 dBTP; `nomusic.wav` -14.0 LUFS,
-1.8 dBTP. Voice over music: at least 15.9 dB per word (147 words, none under 12);
lowest voiced 50 ms frame 9.5 dB (1 of 782 frames under 10).

**Tone scan** (0.5 s windows over every used range, a spectral peak holding > 40 % of the energy): see the note at the
top of `mix.py`; notches 57 Hz on 0112 (nat) and 107 Hz on 0123 (nat and dialog), applied before levelling.

**Cuts:** every in and out was set from the voice-band envelope and both ASR models' word times, 0.5 s either side
(the driving clips 0116-0118 from word times only: road and wind fill the voice band).

**Speakers:** A man in a "10" jersey passes behind in 0123 before 4.9 (not used). Every used line is HOST.

## Blur (Omarie, 2026-10-09: "only blur should be the dash")

None. Per Omarie 2026-10-09 ("only blur should be the dash"), no plate, billboard ("$6.99"), SE sign or phone-number blur. The moving shots are the rear-deck camera looking back (0121, 0122): no dash in frame. 0119 and 0123 are parked or on foot.

## Hands check

No driving frames show him (the rear-deck camera looks back over the engine cover).

## Captions

`words_agree.json`: 133 words both small.en and medium.en hear, chapter times. Gaps (small.en words medium.en
does not confirm): 31.17 (0122 44.87 "minutes"); 72.34 (0123 48.90 "and").

## For nq-facts

* Title "LAS VEGAS": on the first shot, which is Pahranagat Valley "about an hour and some change from Vegas"; lead or nq-facts to decide if it should sit on the skyline (0:34.07) instead. **Decided (Omarie, 2026-10-09, click):** "Move to the skyline": the title now runs 0:34.67-0:37.97 on shot 9 (`TITLE_AT = 9`).
* Spoken: "Pahranagat Valley" (small.en "Farangit", medium.en "Farragut"), "an hour and some change from Vegas", "... minutes out" (small.en "Seven", medium.en "11": not captioned), "Joey and John", "we just did our straight 15 and a half".
* The outro names the shop out loud: "We dropped it off here at Supercar Experience at headquarters" (0123 42.3-45.1); the SE banner, phone number, web address and window lettering are in frame, unblurred per the 2026-10-09 rule. PLAN keeps the outro as filmed; Ch3 cut a spoken SE line (PLAN 3.2). Lead to decide. **Decided (Omarie, 2026-10-09, click):** "Keep as filmed", spoken line included; the SE thank-you stays in the description.
* Background in frame: Rio and Starbucks digital billboards (skyline), the dump truck's plate behind (not blurred, per the rule).
