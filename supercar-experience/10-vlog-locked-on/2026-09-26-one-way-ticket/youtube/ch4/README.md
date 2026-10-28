# One-way ticket, chapter 4 "Into Oregon"

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 1:12.56 (planned about 2:00). Built file-for-file
on `../ch2/` and `../test-ch3/` so it concatenates straight after Ch3 (which ends on 0092 "We out here in Seattle...").

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch4work/`)

| file | what |
|---|---|
| `ch4_master.mp4` | 3840x2160 29.97p H.264 (encode identical to test-ch3 `render.py master`), from the square open-gate frame; AAC 320k; measured -14.0 LUFS, -1.8 dBTP; 72.54 s (877.7 MB) |
| `ch4_master_NOMUSIC.mp4` | the same picture, dialog + natural sound only; measured -14.0 LUFS, -1.8 dBTP |
| `ch4_preview_720p.mp4` | 1280x720 review copy (10.7 MB) |
| `mix.wav`, `nomusic.wav` | the two mixes (48 kHz stereo) |
| `gate/timeline.mp4`, `gate/shotNN_*.jpg` | 640x360 gate render and the pre-render frame gate (one frame every 0.3 s, 640 px tiles, 4x3, timeline and source-time stamps), on the timeline as it renders (graded, cropped, blurred, titled) |

## Rebuild

    cd youtube/ch4
    python3 make_edl.py                                  # -> edl.json (shots, dialog; asserts no block flag is used, dialog included)
    python3 words_medium.py                              # medium.en word timings -> words_medium.json
    python3 words_agree.py                               # words both models hear, chapter times -> words_agree.json
    python3 music.py /home/user/day-owt/ch4work/bed.wav 41
    python3 mix.py /home/user/day-owt/ch4work            # -> mix.wav, nomusic.wav, mix.json
    # WORK/raw_shots/sNN.mp4: the 640x360 gate shots rendered with no blurs; the tracker reads them
    PYTHONPATH=/home/user/day-owt/pycv python3 track_blur.py   # TFT + cluster (template-tracked), hoodie print (badge-anchored) -> look.json
    # trailer plate in shot 19: CSRT on the trailer rear panel (seed 451,45,65,60 at 2.0 s), plate box at its lower left -> look.json '19' (auto 'plate')
    python3 render.py gate && python3 render.py sheets   # 640x360 timeline + frame-gate sheets
    python3 render.py master                             # 4K masters + preview
    python3 render.py remux                              # audio-only change: re-mux onto the existing master_video.mp4

New in Ch4: `make_edl.py` takes `dur: None` (runs to the dialog out) and `dur: 'REST'` (a picture-only cutaway that runs
to the end of the dialog under it). `track_blur.py` tracks the dash on every frame (the rear camera shakes with the car)
at the seed scale, and caps a run at 90 keys, because `render.py` nests one `if()` per key and ffmpeg's expression parser
stops near 100 levels (a 129-key run failed the crop). `mix.py` high-passes the 0094 and 0100 dialog at 170 Hz (the
engine's firing-order fundamental glides 118-146 Hz under the talk) and lifts the montage nat to -22 LUFS.

## Shots

| # | clip:in-out | chapter time | what |
|---|---|---|---|
| 0 | 0093:3.45-8.40 | 0:00.00-0:04.95 | side camera, roof down, under the "INTO OREGON" title: "I ain't gonna lie, it is beautiful out here, like gorgeous." |
| 1 | 0093:127.84-140.70 | 0:04.95-0:17.81 | "But I just want to let you guys know... 12-hour non-stop all the way to Salt Lake... overnight at the Hamptons" |
| 2 | 0094:151.15-155.00 | 0:17.81-0:21.66 | forest road, scenery crop (cy 0.28): "This place is so nice, it's fresh air..." (the 0094 line runs to 165.90 under shots 3-5) |
| 3 | 0095:18.60-22.20 | 0:21.66-0:25.26 | cutaway, forest road ("I miss trees and nature") |
| 4 | 0095:22.30-25.80 | 0:25.26-0:28.76 | cutaway ("...some fire hiking trails out here") |
| 5 | 0095:31.00-34.80 | 0:28.76-0:32.56 | cutaway ("so nice out here") |
| 6-9 | 0095:14.40-16.40, 35.00-37.10, 49.00-51.30, 53.00-55.30 | 0:32.56-0:41.26 | montage, forest road |
| 10-14 | 0098:0.60-3.00, 3.60-5.90, 6.60-8.90, 9.60-11.90, 12.30-14.30 | 0:41.26-0:52.56 | montage, highway through the pines |
| 15-17 | 0098:47.00-49.40, 51.00-53.30, 55.40-57.80 | 0:52.56-0:59.66 | montage, scenery crop (cy 0.28): the exit sign, mountains, valley |
| 18 | 0100:18.20-21.45 | 0:59.66-1:02.91 | desert: "Oregon! We are in Oregon, we passed the welcome to Oregon sign." |
| 19 | 0100:28.15-37.80 | 1:02.91-1:12.56 | "But we just got into Oregon. So that's a quick little update... We're in Oregon!" |

Montage: about 27 s (0:32.56-0:59.66), 12 changes at 2.0-2.4 s each; 15.7 picture changes a minute over the chapter.

## Music

The temp bed is **original**. `music.py` (a copy of test-ch3's with its own key and tempo) synthesizes it in numpy:
82 BPM, A major, Amaj9-F#m9-Dmaj9-Esus2, seed 41 (test-ch3 78 BPM F, Ch1 72 BPM E-flat, Ch2 75 BPM D). It uses no sample,
library track or footage audio. It runs under talk at -39.5 LUFS and in the gaps and the montage at -21 LUFS, as in
test-ch3; the montage carries the camera's own engine sound at -22 LUFS under it.

**Music-flag check:** the only music flag near a used range is 0094 39.9-151.0, which ends before the 151.15 in point;
`make_edl.py` asserts that no shot or dialog range touches a block flag. By measurement (persistent spectral peaks, and
Shazam on every window of 0093 2-10 and 126-144, 0094 149-167, 0095 0-58, 0098 0-63, 0100 18-41: no match), the steady
peaks in 0094, 0095 and 0100 are one harmonic series gliding smoothly with the revs (the engine), and 0098 is road
noise. The 0094 pauses (152.8-154.0, 156.1-157.0, 162.4-163.8) show no music. No car-stereo, venue or PA music is used.

**Loudness:** `mix.wav` -14.01 LUFS, -1.8 dBTP; `nomusic.wav` -14.02 LUFS, -1.8 dBTP (limiter `CEIL` -1.8, so the AAC
masters land <= -1.5). Voice over music: at least 15.1 dB per word (none under 10); 1 of 900 voiced 50 ms frames under
10 dB (minimum 9.7).

**Tone scan:** every dialog range was scanned in 0.5 s windows for a spectral peak holding >40 % of the energy. The
hits are the engine's fundamental under the 0094 and 0100 talk (118-146 Hz, gliding, handled by the 170 Hz dialog
high-pass) and one vowel (0093 133.8, 832 Hz, one window). No steady tone, so `NOTCH` is empty.

**Cuts** (voice-band envelope 0.5 s either side): every dialog in and out was set from the measured voice end and the
next onset (0093 8.05/8.50 -> out 8.40; 140.50/140.75 -> 140.70; 0094 165.54 -> 165.90; 0100 21.00/22.00 -> 21.45;
37.45/37.90 -> 37.80), so no word is clipped. Each cut on `nomusic.wav` shows a short crossfade dip and no word cut mid-syllable.

**Speakers:** every used line is Omarie. 0093 8.77 "Like I'm talking gorgeous" (scored OTHER) is cut by the 8.40 out;
0095 0.0 "you" (OTHER) is outside the used ranges.

## On screen

The only card is the "INTO OREGON" chapter title (0:00.6-0:03.9): Anton, white on a #DE1A22 box with a #FBD101
underline. The title rests on the spoken line in 0100 ("we passed the welcome to Oregon sign"), so nq-facts has to clear
it. No word pops. No figure, price or speed word on screen; the "Easton / Sparks Road" exit sign in shot 15 is real
footage, not a graphic.

**Wardrobe: the "SUPERCAR EXPERIENCE" print on Omarie's hoodie is BLURRED** in every frame it shows: the left-chest
print in the 0093 side-camera shots (0-1), anchored on the green sleeve badge beside it and sized generously over the
belt, the "Hidden Hills" script and the print. In the rear-camera shots the chest is turned away and the back print sits
below the 16:9 window. The other prints (HR, Hidden Hills Club, BASED, 22) are not SE and stay.

## Blur list

Feathered round patches, keyed every 3rd frame or wider (at most 90 keys a run), box size the largest over the run:

| shot | what | source | chapter time |
|---|---|---|---|
| 0 | SE hoodie print | 0093 3.45-8.40 | 0:00.00-0:04.95 (whole shot) |
| 1 | SE hoodie print | 0093 127.84-140.70 | 0:04.95-0:17.81 (whole shot) |
| 3-14 | centre TFT (nav/media) and the driver's cluster (speed/gear), template-tracked | 0095 and 0098, every rear-camera shot | 0:21.66-0:52.56 (every shot, whole length) |
| 18 | TFT and cluster | 0100 18.20-21.45 | 0:59.66-1:02.91 |
| 19 | TFT and cluster | 0100 28.15-37.80 | 1:02.91-1:12.56 |
| 19 | licence plate, Flagstaff travel trailer ahead (CSRT on its rear panel, three runs so the box stays small) | 0100 28.15-32.66 | 1:02.91-1:07.41 (then the car is alongside and the rear is out of view) |

Shots 2 and 15-17 are scenery crops: the dash is below the frame. The black pickup in shot 19 keeps its plate below the
windshield frame line. The 0093 side view shows no cluster. Other traffic is side-on, motion-blurred or too far for a
plate to read at 640; nq-check should confirm at 4K.

## Deviations from PLAN.md

- **Runtime** is 1:12.56, not about 2:00: cut to the content, no padding.
- **0093:3.9-8.2** becomes 3.45-8.40, so "I ain't gonna lie" opens the chapter whole; 8.40 ends before another voice's "Like I'm talking gorgeous".
- **0093:127.8-142.1** becomes 127.84-140.70: drops the dangling "and once we're there".
- **0094:151.2-165.5** keeps its sound (151.15-165.90), but the picture is a scenery crop for 3.85 s and then 0095
  cutaways, because 0094 shows his phone in his hand near the wheel.
- **The montage** is about 27 s from 0095 and 0098 (0098 only 0-14.3 with the cockpit in view, where both hands are on
  the wheel; 47-58 as scenery crops, because the phone is out there).
- **0100:20.1-38.7** becomes 18.2-21.45 and 28.15-37.80: it opens on "We are in Oregon, we passed the welcome to Oregon
  sign"; 21.45-28.15 is cut (a swear, "god damn", and an aside about a map graphic); it ends on "We're in Oregon!"
  because he reaches for the camera from about 38.3 and "Alright, I'll see you guys later" follows.
- **Hoodie print** blurred (see above), against test-ch3's wardrobe note, as the brief ordered.
