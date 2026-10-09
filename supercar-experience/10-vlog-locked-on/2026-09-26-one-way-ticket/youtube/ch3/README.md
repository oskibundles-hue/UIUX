# One-way ticket, chapter 3 "Seattle, WA"

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 2:39.0 (planned about 2:50). Built from the approved
`../test-ch3/` (left untouched as the reference): same cut, grade, framing, title card, word pops and bed. What changed:
the blur code (ch2/ch4's pad+mask superellipse feather, cache tag "pad+mask v3"), the shot-13 cluster blur is off (parked),
the limiter ceiling (-1.8 dBTP) and the caption words (`words_agree.json`).

## Files (not committed; the videos live outside git, in `/home/user/day-owt/ch3work/`)

| file | what |
|---|---|
| `master_video.mp4` | 3840x2160 29.97p H.264, picture only (encode identical to test-ch3 `render.py master`); the lead muxes the wavs |
| `mix.wav`, `nomusic.wav` | the two mixes (48 kHz stereo): -14.0 LUFS, -1.8 dBTP each (ffmpeg ebur128) |
| `ch3_preview_720p.mp4` | 1280x720 review copy |
| `gate/timeline.mp4`, `gate/shotNN_*.jpg` | 640x360 gate render and the pre-render frame gate (every 0.3 s, 640 px tiles, 4x3, timeline + source stamps) |

## Rebuild

    cd youtube/ch3
    python3 make_edl.py                                  # -> edl.json (shots, dialog, audio_extra, mutes, bleep)
    python3 ../../../engine/vlog.py plan /home/user/day-owt --edl edl.json
    VLOG_MEZZ_LONG=3840 python3 ../../../engine/vlog.py fetch /home/user/day-owt --out /home/user/day-owt/mezz
    python3 words_medium.py                              # medium.en word timings -> words_medium.json
    python3 words_agree.py                               # words both models hear, chapter times -> words_agree.json
    python3 music.py /home/user/day-owt/ch3work/bed.wav 165
    python3 mix.py /home/user/day-owt/ch3work            # -> mix.wav, nomusic.wav, mix.json (LUFS, margins)
    python3 render.py gate && python3 render.py sheets   # 640x360 timeline + frame-gate sheets (run from /home/user/day-owt/ch3work)
    python3 render.py master                             # 4K masters + preview

`look.json` sets the framing for each shot: rotation (0090 is clockwise), the crop centre, and the blurs. The rear
plate in shot 11 is tracked with `track_plate.py` (OpenCV CSRT); those entries carry `"clamp": true`, which keeps test-ch3's
approved placement (the box held inside the picture) on the new padded blur frame. `track_blur.py` (ch4's) is copied for
reference only: Ch3 needs no automatic dash tracking (see the blur list). `pops.json` lists the three word pops.

## Music

The temp bed is **original**. `music.py` synthesizes it here in numpy: 78 BPM, C major, Fmaj9-Em7-Dm9-Cmaj7, with a
pad, sub, Rhodes-like plucks, a soft kick and a shaker. It uses no sample or library track and nothing from the
footage. It is a placeholder until Omarie's Epidemic Sound account is set up. Under talk it sits at -39.5 LUFS (BED_TALK), with
3 dB more ducking at 1:27.4-1:31.8. In the gaps it sits at -21 LUFS. It is off for the 0090 arrival, where the
engine plays alone. No car-stereo or venue music is used: Shazam checked every used range.

Master: true-peak limiter at -1.8 dBTP (was -1.5 in test-ch3), as in Ch1/Ch2/Ch4, so the AAC masters land at or under
-1.5 dBTP. Measured (ffmpeg ebur128): `mix.wav` -14.0 LUFS, -1.8 dBTP; `nomusic.wav` -14.0 LUFS, -1.8 dBTP (mix.py: -14.01 both).

Voice over music: at least 12.0 dB per word (none under 10), and at least 10.4 dB on every voiced 50 ms frame (1990 frames).

## On screen

The only card is the "Seattle, WA" title: Anton, white on a #DE1A22 box with a #FBD101 underline. There are three
word pops (Archivo 800, yellow with a black stroke and a red shadow): OH YEAH, IMPOSSIBLE and LONG DRIVE. small.en
and medium.en both hear each of them. Nothing on screen carries a figure, price or speed word.

**Wardrobe:** the "SUPERCAR EXPERIENCE" print on Omarie's hoodie stays **unblurred**, per Omarie (2026-10-09, via the
lead), which reverses the brief's earlier blur order for this chapter.

## Blur list

Cluster/speedometer rule (Omarie, 2026-10-09, via the lead): blur the cluster only while the car is moving.

| shot | what | source | chapter time | car |
|---|---|---|---|---|
| 11 | rear plate, tracked (CSRT), two runs | 0090 19.40-21.40, 23.00-25.74 | 1:02.25-1:04.25, 1:05.85-1:08.59 | arriving, rolling |
| 11 | rear plate at the right edge (box) | 0090 22.30-22.97 | 1:05.15-1:05.82 | rolling |
| 11 | rear plate sliver at the right bumper edge (box) | 0090 19.00-19.45 | 1:01.85-1:02.30 | rolling |
| 13 | instrument cluster: **blur removed** | 0090 114.85-118.35 | 1:21.44-1:24.94 | parked at the shop (interior tour after arrival) |

Checked on the survey and gate sheets with no blur added: shots 19-20 and 22 (0092, seated, side camera from the passenger
side) and the shot-21 drive cutaway: the cluster sits behind the wheel rim and is not readable from that angle, and no
centre screen shows. The lot cars (shots 0-12) show no readable plate (the arriving 600 LT carries no front plate; the
Bentley in shot 9 has none). Not blurred and not in the brief's list: the German AutoHaus shop sign with its phone number
(shots 9 and 11, a third-party business), as approved in test-ch3.

## Captions

`words_agree.py` -> `words_agree.json`: 249 words both small.en and medium.en hear, chapter seconds. The bleeped word
(0092 90.81-91.69) is left out. Lines where the models disagree (hand-caption these): 0087 9.5 "I don't (even) think...
I think I'm a [clowns / McLaren's rat]"; 0090 21.9 "Oh yeah, brand new engine" (only "engine" agrees; the OH YEAH pop sits
here); 0091 2.1 "We are in the 600 LT. Spider" (only "Top goes down" agrees); 0091 59.0 "Impossible" (the IMPOSSIBLE pop);
0092 7.52 "That's what we... Oh yeah, [I mean again / in the game]... Whoo, it's gonna"; 0090 110.15 "gonna / going to",
"Little red gut(s)"; 0089 140.5 "finna / gonna", "600 LT"; 0092 26.5 "lift on this car. Alright cool." (small.en stops at
"have").

## Deviations from PLAN.md

- **Runtime** is 2:39.0, not about 2:50. The cuts below remove dead air and every music-flagged span.
- **"noon"** is left off the card. The title reads "Seattle, WA" because the lead's brief allows only that title.
- **0087:44.5 starts at 44.25** and **0087:55.1 at 55.0**, so the first words aren't clipped. "From Supercar
  Experience" (51.1-53.5) is cut as planned.
- **0089:139.6-152.5** becomes 140.5-152.0. It starts on "right now"; the end is set by the measured voice end
  (151.4) and the next onset (152.6).
- **0089:186.5-194.2** becomes 187.8-194.63, which starts after the other speaker's "be right back", with a gap of
  at least 0.1 s. This drops "I'll show you when he pulls up with the car."
- **0090:102.3-118.0** is split into 103.72-109.71 and 110.15-118.35. The cluster is blurred at about 115.6-118.35.
- **0091:22.1-30.0** ends at 30.55, on the measured voice end.
- **0092:7.6-44.0** becomes 7.52-22.92 plus 26.5-37.35. The second piece runs on to "...lift on this car. Alright
  cool.", because medium.en shows the sentence continues. 37.6-43.6 is used as room tone.
- **Drive cutaways (picture only)** fill 6 s before the last line, over the parked room tone: 0092 139.95-143.75
  at 0.633x. 0092 is 59.94 fps, so this is real slow motion. At the frame gate, 0092 126.5-129.5 failed the hands
  rule (both hands off the wheel at 128.6), and no other fetched drive span has a hand on the wheel in every frame.
- **0092:88.2-92.6** dialog starts at 88.62 and its natural sound at 88.8, after the car stereo ("Phantom") cuts
  out. The swear is bleeped (90.81-91.69).
- A 2.2 s cutaway (0087 38.2-40.4, the white McLaren) covers the 0089 line.
- **Strangers** are muted at 0090 1.40-2.85 and 10.40-12.30. The staff member at the end of shot 11 is seen from
  behind, with no face.
