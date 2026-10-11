# One-way ticket, chapter 2 "Seattle · morning"

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 0:37.95 (planned about 0:50). Built file-for-file
on `../ch1/` and `../test-ch3/` so it concatenates straight after Ch1 (which ends on 0081 "finally getting on the plane").

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch2work/`)

| file | what |
|---|---|
| `ch2_master.mp4` | 3840x2160 29.97p H.264 (encode identical to test-ch3 `render.py master`), from the square open-gate frame; AAC 320k; measured -14.1 LUFS, -1.7 dBTP; 37.94 s |
| `ch2_master_NOMUSIC.mp4` | the same picture, dialog + natural sound only; measured -14.0 LUFS, -1.7 dBTP |
| `ch2_preview_720p.mp4` | 1280x720 review copy (5.9 MB) |
| `mix.wav`, `nomusic.wav` | the two mixes (48 kHz stereo) |
| `gate/timeline.mp4`, `gate/shotNN_*.jpg` | 640x360 gate render and the pre-render frame gate (one frame every 0.3 s, 640 px tiles, 4x3, source-time stamps), on the timeline as it renders (graded, cropped, blurred, titled) |

## Rebuild

    cd youtube/ch2
    python3 make_edl.py                                  # -> edl.json (shots, dialog; asserts no block flag is used)
    python3 words_medium.py                              # medium.en word timings -> words_medium.json
    python3 words_agree.py                               # words both models hear, chapter times -> words_agree.json
    python3 music.py /home/user/day-owt/ch2work/bed.wav 42
    python3 mix.py /home/user/day-owt/ch2work            # -> mix.wav, nomusic.wav, mix.json
    # WORK/raw_shots/sNN.mp4: the 640x360 gate shots rendered with no blurs; the trackers read them
    PYTHONPATH=/home/user/day-owt/pycv python3 track_plate.py raw_shots/s05.mp4 '[[0.5,513,283,27,15,0.0,2.55]]' plate_dbg/s05.json
    PYTHONPATH=/home/user/day-owt/pycv python3 track_print.py   # hoodie-print keys -> look.json (keeps the plate entry)
    python3 render.py gate && python3 render.py sheets   # 640x360 timeline + frame-gate sheets (run from /home/user/day-owt/ch2work)
    python3 render.py master                             # 4K masters + preview
    python3 render.py remux                              # audio-only change: re-mux onto the existing master_video.mp4

`look.json` holds the per-shot framing (`cy`, the 16:9 window's centre as a fraction of the square) and blurs. New in
Ch2: `cy_keys` in `render.py`, a moving 16:9 window (smoothstep between keys) so shot 4's full-length fit check tilts
down to the shoes at "Rick Owens". Keyed blurs now carry half a frame of slack each side (the last frame of a tracked
run was falling outside `between()`); the shot-cache tag is `pad+mask v3`.

## Shots

| # | clip:in-out | chapter time | what |
|---|---|---|---|
| 0 | 0082:1.00-5.50 | 0:00.00-0:04.50 | landing: wing and engine over the Seattle suburbs, under the "SEATTLE · MORNING" title (picture + nat) |
| 1 | 0082:9.00-13.00 | 0:04.50-0:08.50 | landing: low over the trees to the airport car park (picture + nat) |
| 2 | 0084:1.25-14.40 | 0:08.50-0:21.65 | "All right, so we was just on a tram talking to Jordan Carter... we going up to the baggage claim. I got no bags. I don't know where I'm at" |
| 3 | 0085:49.80-52.60 | 0:21.65-0:24.45 | garage selfie: "You wanna see the fit check?" |
| 4 | 0085:58.40-69.35 | 0:24.45-0:35.40 | camera on the bench, full length: "Got the Hidden Hills jacket on, you see the back... the Rick Owens on, tough, huh" |
| 5 | 0086:31.90-34.45 | 0:35.40-0:37.95 | "Second time in Seattle, Washington." |

Framing (`cy`): shot 2 0.42, shot 3 0.28 (top clamp; the forehead is still trimmed a little), shot 4 tilts 0.36 -> 0.62
over 7.5-8.4 s, shot 5 0.55; shots 0-1 centred.

## Music

The temp bed is **original**. `music.py` (a copy of test-ch3's with its own key and tempo) synthesizes it in numpy:
75 BPM, D major, Dmaj9-Bm9-F#m7(add13)-Asus2, seed 23 (test-ch3 is 78 BPM F, Ch1 72 BPM E-flat). It uses no sample,
library track or footage audio. It runs under talk at -39.5 LUFS and in the gaps at -21 LUFS, as in test-ch3.

**Music-flag check:** `flags.json` has no music flag on 0082, 0084, 0085 or 0086. The only block flag on these clips is
0086 35.0-51.1 (a stranger), outside the used range (ends 34.45); `make_edl.py` asserts that no shot or audio range
touches a block flag. 0082 (the landing) has engine nat only, no speech or PA. No car-stereo, venue or PA music is used.

**Loudness** (ffmpeg ebur128, on the files): `mix.wav` -14.04 LUFS, -1.8 dBTP; `nomusic.wav` -14.02 LUFS, -1.8 dBTP
(limiter `CEIL` -1.8, so the AAC masters land <= -1.5). Voice over music: at least 13.9 dB per word (none under 10),
at least 11.0 dB on every voiced 50 ms frame (404 frames).

**Tone scan:** every dialog range was scanned in 0.5 s windows for a spectral peak holding >40 % of the energy. The
only hits are vowel harmonics (e.g. 0084 12.0-12.5 "bags", 662 -> 650 Hz, moving) and the 86-96 Hz engine drone in the
0082 landing nat, which is the scene. No steady tone, so `NOTCH` and `EXTRA_DUCK` are empty.

**Cuts** (envelope 0.5 s either side, on `nomusic.wav`): no clipped word. 8.50: "All" starts 0.1 s after the cut (the
0084 camera audio is digital silence 0.65-1.25, hence the in point). 21.65, 24.45, 35.40: the last word ends 0.35-0.5 s
before and the next starts 0.2-0.25 s after. The end (37.95) has about 0.4 s of room after "Washington".

**Speakers:** every used line is Omarie. 0085 "I got a fit." (scored OTHER) and "You're filming." (52.6-58.4) are cut;
0086's stranger block is outside the range.

## On screen

The only card is the "SEATTLE · MORNING" chapter title (0:00.6-0:03.9): Anton, white on a #DE1A22 box with a #FBD101
underline. "Morning" comes from the DJI camera clock (0082 08:59:59; 0084-0085 about 09:24-09:37), so nq-facts has to
clear it (which time zone the camera clock was set to). No word pops. No figure, price or speed word on screen.

**Wardrobe: the "SUPERCAR EXPERIENCE" print on Omarie's hoodie is BLURRED** in every frame it shows (front chest, and
the second SE logo on the back under the helmet print in shot 4). The other prints (RYFT, Hidden Hills Club, HR, BASED,
22) are not SE and stay.

## Blur list

Tracked, feathered round patches over the SE print (`track_print.py`, CSRT), plus one plate:

| shot | what | source | chapter time |
|---|---|---|---|
| 2 | SE print (chest, as the camera swings down) | 0084 12.73-14.06 | 0:19.98-0:21.31 |
| 3 | SE print | 0085 49.80-52.57 | 0:21.65-0:24.42 (whole shot) |
| 4 | SE print front, then the back SE logo under the helmet, then front | 0085 58.40-66.58 | 0:24.45-0:32.63 (after it the tilt puts the chest out of the window) |
| 5 | SE print | 0086 32.37-34.40 | 0:35.87-0:37.90 (before, the print is below the frame) |
| 5 | licence plate, black SUV behind him (track_plate.py, padded 35 %) | 0086 31.90-32.72 | 0:35.40-0:36.22 (then the plate is behind his arm and the SUV leaves) |

Shots 0-1: the car-park cars are seen from altitude and no plate is readable. No cluster or speedometer: Ch2 has no driving.

## Deviations from PLAN.md

- **Runtime** is 0:37.95, not about 0:50: cut to the content, no padding.
- **0082:0-12** becomes 1.0-5.5 and 9.0-13.0: the two cleanest landing views; 13.0 is inside the fetch padding.
- **0084:1-14.1** becomes 1.25-14.40: the camera audio is digital silence until 1.25; the out runs to 14.40 so "at" isn't clipped.
- **0085:50-69** becomes 49.8-52.6 and 58.4-69.35: drops 52.6-58.4 ("I got a fit." by another voice, "You're filming."
  and the camera set-down), and runs to 69.35 so "huh" isn't clipped.
- **0086:32-33.5** becomes 31.9-34.45 so "Washington" ends whole; the next word ("Tacoma", 35.02) is left out.
- **Hoodie print** blurred (see above), against test-ch3's wardrobe note, as the brief ordered.
