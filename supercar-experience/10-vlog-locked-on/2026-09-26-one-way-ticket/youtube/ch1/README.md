# One-way ticket, chapter 1 "4:30 a.m."

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 0:54.0 (planned about 1:30). Built file-for-file
on `../test-ch3/` so it concatenates behind the approved opening (`../opening-test/`, B2 v2.2), which already ends on
the 0075 80.7-85.6 line; this chapter starts at 0076.

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch1work/`)

| file | what |
|---|---|
| `ch1_master.mp4` | 3840x2160 29.97p H.264 (encode identical to test-ch3 `render.py master`), cut from the full open-gate frame; AAC 320k, -14 LUFS integrated, -1.5 dBTP |
| `ch1_master_NOMUSIC.mp4` | the same picture, dialog + natural sound only, -14 LUFS, -1.5 dBTP |
| `ch1_preview_720p.mp4` | 1280x720 review copy, under 29 MiB |
| `mix.wav`, `nomusic.wav` | the two mixes (48 kHz stereo) |
| `gate/timeline.mp4`, `gate/shotNN_*.jpg`, `gate/zoom/z_*.jpg` | 640x360 gate render, the pre-render frame gate (one frame every 0.3 s, 640 px tiles), and chest-region zoom sheets for the print blur |

## Rebuild

    cd youtube/ch1
    python3 make_edl.py                                  # -> edl.json (shots, dialog; asserts no block flag is used)
    python3 words_medium.py                              # medium.en word timings -> words_medium.json
    python3 words_agree.py                               # words both models hear, chapter times -> words_agree.json
    python3 music.py /home/user/day-owt/ch1work/bed.wav 60
    python3 mix.py /home/user/day-owt/ch1work            # -> mix.wav, nomusic.wav, mix.json (LUFS, margins)
    # WORK/raw_shots/sNN.mp4: the 640x360 gate shots rendered with no blurs (look.json blur lists empty); the tracker reads them
    PYTHONPATH=/home/user/day-owt/pycv python3 track_print.py   # hoodie-print blur keys -> look.json
    python3 render.py gate && python3 render.py sheets   # 640x360 timeline + frame-gate sheets
    python3 render.py master                             # 4K masters + ch1_preview_720p.mp4

`look.json` holds the per-shot blurs (no rotation or crop offsets in Ch1). `track_print.py` tracks the hoodie print
with OpenCV CSRT (from opencv-contrib in `/home/user/day-owt/pycv`), following the "Hidden Hills" script or, in the dark
kerb shot, the pink HR logo, and sets the blur box relative to it. `render.py` pads the frame by a quarter height before
the blurs, so a box at the bottom edge keeps its opaque centre on the print, and feathers each patch with a static
superellipse mask.

## Shots

| # | clip:in-out | chapter time | what |
|---|---|---|---|
| 0 | 0076:21.15-23.05 | 0:00.00-0:01.90 | airport kerb at night (picture + nat only) under the "4:30 A.M." title |
| 1 | 0076:24.90-34.84 | 0:01.90-0:11.84 | "That's a little tired, but we up now..." |
| 2 | 0076:89.20-90.30 | 0:11.84-0:12.94 | terminal: "So I" |
| 3 | 0076:91.15-93.45 | 0:12.94-0:15.24 | "have Muse make me like a route" |
| 4 | 0076:113.10-124.80 | 0:15.24-0:26.94 | "...straight from Seattle Tacoma to Sandy Utah, which is like 830 miles, 12 hours..." |
| 5 | 0076:125.65-127.85 | 0:26.94-0:29.14 | "420 miles, six hours." |
| 6 | 0076:132.40-135.95 | 0:29.14-0:32.69 | "It's looking like a 18 hour drive, Chad. I ain't gonna lie." |
| 7 | 0077:78.30-81.00 | 0:32.69-0:35.39 | the tram: "I'm gonna miss this little tram. Oh my God." |
| 8 | 0077:82.35-88.15 | 0:35.39-0:41.19 | "Should I run? Nope, not doing it. It's already closing." |
| 9 | 0077:91.40-93.72 | 0:41.19-0:43.51 | "I think it's gonna close on her." |
| 10 | 0080:49.10-54.46 | 0:43.51-0:48.87 | the bagel: "It's a little lopsided but I got it with the cream cheese..." |
| 11 | 0081:2.85-7.99 | 0:48.87-0:54.01 | "I'm finally getting on the plane..." |

## Music

The temp bed is **original**. `music.py` (a copy of test-ch3's with its own key and tempo) synthesizes it here in numpy:
72 BPM, E-flat major, Abmaj9-Gm7-Fm9-Ebmaj7, with a pad, sub, Rhodes-like plucks, a soft kick and a shaker. It uses no
sample or library track and nothing from the footage. It is a placeholder until Omarie's Epidemic Sound account is set
up. Under talk it sits at -39.5 LUFS and in the gaps at -21 LUFS, as in test-ch3. It runs the whole chapter.

**Music-flag check:** `flags.json` has no music flag on 0076, 0077 or 0080. 0081's PA/music block (53.0-97.5) and
0080's cut_request block (89.58-111.9) are far outside the used ranges; `make_edl.py` asserts that no shot or audio
range touches any block flag. The tram's airport PA ("Please stand clear of the tram doors", 0077 98.11) is cut: the
tram ends at 93.72. No car-stereo, venue or PA music is used.

Voice over music: at least 14.4 dB per word (129 words), and at least 10.5 dB on every voiced 50 ms frame
(test-ch3: 12.0 and 10.4).

**Loudness** (ffmpeg ebur128, measured on the files): `mix.wav` -14.0 LUFS integrated, -1.5 dBTP, LRA 4.0 LU;
`nomusic.wav` -14.0 LUFS integrated, -1.5 dBTP, LRA 4.1 LU. After the AAC 320k encode both masters measure
-14.0 LUFS and -1.4 dBTP (the codec adds about 0.1 dB of inter-sample peak; the mux step is test-ch3's, unchanged).

## On screen

The only card is the "4:30 A.M." chapter title (0:00.6-0:03.9): Anton, white on a #DE1A22 box with a #FBD101
underline. It is a clock time from the camera clock, so nq-facts has to clear it (which time zone the camera clock was set to; the scene is Harry Reid airport, Las Vegas). There are
no word pops in Ch1. Nothing on screen carries a figure, price or speed word; the route figures (830 miles, 12 hours,
420 miles, six hours, 18 hour) are spoken only.

**Wardrobe: the "SUPERCAR EXPERIENCE" print on Omarie's hoodie is BLURRED** in every frame it shows (the lead's Ch1
brief overrides test-ch3's "unblurred" note: personal brand only). The other prints on the hoodie (RYFT, Hidden Hills
Club, HR Hidden Hills Racing, BASED) are not SE and stay.

## Blur list

All are the tracked, feathered round patch over the SE print (`look.json`, from `track_print.py`):

| shot | source | chapter time | note |
|---|---|---|---|
| 1 | 0076 24.90-34.81 | 0:01.90-0:11.84 | night kerb; tracked from the HR logo then Hidden Hills; tracker losses at 2.37 and 3.34 s bridged by interpolation |
| 3 | 0076 91.98-93.42 | 0:13.77-0:15.24 | before 13.77 the print is below the frame |
| 4 | 0076 113.10-124.78 | 0:15.24-0:26.94 | whole shot |
| 5 | 0076 125.65-127.82 | 0:26.94-0:29.14 | whole shot |
| 6 | 0076 132.40-135.90 | 0:29.14-0:32.69 | whole shot |
| 7 | 0077 78.63-80.23 | 0:33.02-0:34.62 | outside it the print is below the frame or turned away |
| 9 | 0077 91.40-93.70 | 0:41.19-0:43.51 | whole shot |
| 10 | 0080 49.10-53.44 | 0:43.51-0:47.85 | from 47.85 the bagel and hands cover the chest |

Shots 0, 2, 8 and 11 show no SE print (checked on the gate zoom sheets). There are no plates readable in Ch1 (the cars
at the 0076 kerb are distant and unreadable) and no cluster or speedometer: Ch1 has no driving.

## Deviations from PLAN.md

- **Runtime** is 0:54.0, not about 1:30. The 0076 route talk is trimmed at word level and the pauses are cut, as the
  brief asked ("cut to the content, no padding").
- **0075:80.7-85.6** is not in Ch1: the opening already ends on it.
- **Opens on 0076:21.15-23.05** (the airport kerb, inside the fetch padding) so the title sits on an establishing shot.
  His words under it are reduced to their < 250 Hz content in the nat bus.
- **0076:24.9-34.4** runs to 34.84 so "...what we got" isn't clipped.
- **0076:88.4-134.4** becomes 89.2-90.3, 91.15-93.45, 113.1-124.8, 125.65-127.85 and 132.4-135.95. It drops the
  "Jason recommended..." aside and a false start (93.45-113.1), the other "oh," (124.8-125.65) and "So it's about a
  18." (said again next). The last piece runs 1.5 s past the PLAN end to finish "I ain't gonna lie"; the speaker model
  scores that phrase OTHER 0.63 but it runs on without a gap, so nq-check should listen to it.
- **0077:78.4-98** becomes 78.3-81.0, 82.35-88.15 and 91.4-93.72. It ends on "...close on her." because 96.47-98.03 is
  a stranger and 98.11 is the airport PA.
- **0080:51.7-54.1** becomes 49.1-54.46, so the line starts on its own beginning.
- **0081:2.9-7.6** becomes 2.85-7.99, so the last word isn't clipped (next voice is a stranger at 9.03).
- **Strangers:** every transcribed word in the nat bus is reduced to < 250 Hz, so the only voice is Omarie's dialog.
- **Hoodie print** blurred (see above), against test-ch3's wardrobe note, as the brief ordered.
