# One-way ticket, chapter 3 "Seattle, WA" (TEST CHAPTER)

Style **Lifestyle**, for Omarie's personal channel @nq.young. 16:9, 2:39.0 (planned about 2:50). This is the test
build for the long-form plan in `../PLAN.md`.

## Files (not committed; the videos live outside git)

| file | what |
|---|---|
| `OneWayTicket_Ch3_test_master.mp4` | 3840x2160 29.97p H.264, cut from the full open-gate frame; AAC 320k, -14 LUFS integrated, -1.5 dBTP |
| `OneWayTicket_Ch3_test_master_NOMUSIC.mp4` | the same picture, dialog + natural sound only, -14 LUFS, -1.5 dBTP |
| `preview_720p.mp4` | 1280x720 review copy, under 29 MiB |

## Rebuild

    cd youtube/test-ch3
    python3 make_edl.py                                  # -> edl.json (shots, dialog, audio_extra, mutes, bleep)
    python3 ../../../engine/vlog.py plan /home/user/day-owt --edl edl.json
    VLOG_MEZZ_LONG=3840 python3 ../../../engine/vlog.py fetch /home/user/day-owt --out /home/user/day-owt/mezz
    python3 words_medium.py                              # medium.en word timings -> words_medium.json
    python3 music.py /home/user/day-owt/ch3work/bed.wav 165
    python3 mix.py /home/user/day-owt/ch3work            # -> mix.wav, nomusic.wav, mix.json (LUFS, margins)
    python3 render.py gate                               # 640x360 timeline for the frame gate
    python3 render.py master                             # 4K masters + preview_720p.mp4

`look.json` sets the framing for each shot: rotation (0090 is clockwise), the crop centre, and the blurs. The rear
plate in shot 11 is tracked with `track_plate.py` (OpenCV CSRT). The cluster blur in shot 13 is a rounded, feathered
patch keyed by hand to the cluster. `pops.json` lists the three word pops.

## Music

The temp bed is **original**. `music.py` synthesizes it here in numpy: 78 BPM, C major, Fmaj9-Em7-Dm9-Cmaj7, with a
pad, sub, Rhodes-like plucks, a soft kick and a shaker. It uses no sample or library track and nothing from the
footage. It is a placeholder until Omarie's Epidemic Sound account is set up. Under talk it sits at -39.5 LUFS, with
3 dB more ducking at 1:27.4-1:31.8. In the gaps it sits at -21 LUFS. It is off for the 0090 arrival, where the
engine plays alone. No car-stereo or venue music is used: Shazam checked every used range.

Voice over music: at least 12.0 dB per word, and at least 10.4 dB on every voiced 50 ms frame.

## On screen

The only card is the "Seattle, WA" title: Anton, white on a #DE1A22 box with a #FBD101 underline. There are three
word pops (Archivo 800, yellow with a black stroke and a red shadow): OH YEAH, IMPOSSIBLE and LONG DRIVE. small.en
and medium.en both hear each of them. Nothing on screen carries a figure, price or speed word.

**Wardrobe:** the "SUPERCAR EXPERIENCE" print on Omarie's hoodie stays unblurred. Omarie ruled it wardrobe, not
branding. This applies to this and every chapter.

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
