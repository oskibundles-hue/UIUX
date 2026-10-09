# One-way ticket: opening A/B look test

Style **Lifestyle**, for Omarie's personal channel @nq.young, in his personal brand only. Two openings to watch back to
back before the full cut:

- **A, HiddenQuan style (cold talk):** the hook, then straight into the start of chapter 1.
- **B, Brez Scales style:** the same hook, then a 20.0 s whole-trip montage (no talk, the music up, cuts on the beat, in
  trip order), then the same chapter 1 start.

Nothing is drawn on screen: no title, no word pops, no captions and no "4:30 a.m." card. No SE logo, HUD, strip, end
card or SE colour. The grade is the approved test chapter's warm look (`GRADE` and the crop/blur code are imported from
`../test-ch3/render.py`). These are look-test previews only; no 4K masters.

## Files (the videos are not committed; they live outside git)

| file | what |
|---|---|
| `opening_A_preview_720p.mp4` | 1280x720 29.97p H.264 + AAC 192k, 22.56 s, 10.6 MiB |
| `opening_B_preview_720p.mp4` | 1280x720 29.97p H.264 + AAC 192k, 42.54 s, 20.6 MiB |
| `gate/opening_A_shots_in_mid_out.png`, `gate/opening_B_shots_in_mid_out.png` | in, mid and out frames of every shot, 1920 px wide (B holds every shot of both) |
| `gate/gate_A_01..07.jpg`, `gate/gate_B_01..12.jpg` | the vlog frame gate: a frame every 0.3 s, 640 px tiles, 12 a sheet, timeline time stamped |
| `mix_A.json`, `mix_B.json` | mix report: dialog gains, natural sound, bed, loudness, voice-over-music margins |

## Rebuild

    cd youtube/opening-test
    python3 make_edl.py          # -> edl_A.json, edl_B.json
    python3 mix.py A; python3 mix.py B        # -> /home/user/day-owt/openwork/mix_<A|B>.wav (+ bed_<A|B>.wav from ../test-ch3/music.py)
    python3 render.py gate A; python3 render.py gate B      # timeline + gate sheets
    python3 render.py preview A; python3 render.py preview B

The source is the 3840 open-gate mezzanines in `/home/user/day-owt/mezz_open` (vlog.py fetch, `spans.json`). Framing,
rotation and blurs are set per shot in `look.json`, keyed `<clip>:<in>`.

## Shot list

| shot | at | kind | source span (s) | dur | what |
|---|---|---|---|---|---|
| 00 | 0:00.00 | cutaway | 0121 152.00-154.27 (picture) | 2.27 | over HOOK 1, 0117 100.85-103.12: "(I have) no cell service, not an SOS." Rear camera, desert highway |
| 01 | 0:02.27 | cutaway | 0099 176.30-178.52 (picture) | 2.22 | over HOOK 2, 0117 111.40-113.62: "We're gonna have to make it, we don't have a choice." Eastern Oregon plains |
| 02 | 0:04.49 | talk | 0075 56.45-60.95 | 4.50 | HOOK 3: "It's 4:30 in the morning. I got my Uber coming right now." |
| 03 | 0:08.99 | talk | 0075 69.32-77.02 | 7.70 | HOOK 4 (jump cut): "So we are heading to Seattle, Washington to go pick up a McLaren 600 LT." |
| **A** 04 | 0:16.69 | talk | 0075 80.50-86.38 | 5.88 | CH1: "So let's head up out of here. Alright famo." + tail |
| **B** 04 | 0:16.69 | montage | 0092 19.00-22.08 | 3.08 | Seattle, top down, cabin side (parked) |
| B 05 | 0:19.77 | montage | 0094 27.50-29.81 | 2.31 | forest road POV (1.4x top-anchored window, mirror out of frame) |
| B 06 | 0:22.07 | montage | 0095 8.80-10.34 | 1.54 | green forest road (2 beats; clear of the flares) |
| B 07 | 0:23.61 | montage | 0098 97.35-100.43 | 3.08 | trees and highway (1.4x top-anchored window, mirror out of frame; 4 beats) |
| B 08 | 0:26.69 | montage | 0099 179.00-181.31 | 2.31 | eastern Oregon plains (source muted) |
| B 09 | 0:29.00 | montage | 0121 148.40-151.48 | 3.08 | desert highway, rear camera |
| B 10 | 0:32.07 | montage | 0122 583.40-588.02 | 4.62 | Las Vegas, Rio billboard and skyline, rear camera (last; source muted) |
| B 11 | 0:36.69 | talk | 0075 80.50-86.38 | 5.88 | CH1: "So let's head up out of here. Alright famo." + tail |

0075 is rotated 90 degrees clockwise (the camera was on its side). The montage cuts on the bed's beats at 78 BPM:
4+3+3+3+3+4+6 beats = 20.0 s, starting on a chord change.

## Frame-gate fixes (7 Oct, second pass)

1. **0098** had his phone in the rear-view mirror in every window; no clean window exists, so the shot is now a 1.4x window anchored at the top of the square (mirror and dash below frame). The crop centre was already clamped at the top, so zoom was the only way out. Same for **0094** (his arm in the mirror) and the hook cutaway **0099 176.3** (his raised hand shows in the mirror at about 3.3-4.3 s of the opening; this one wasn't on the checker's list). Look.json keys: `zoom`, `cy 0`. Road is a thin strip in these; sky and trees carry them.
2. **CH1 tail** (0075 80.5-86.38): "famo" ends 85.55 and the picture is a darkening silhouette there (luma 61 to 35 on the 0-255 scale), so no lit end exists within the 350 ms rule. A gentle gamma ramp (1.0 at 1.6 s to 1.55 at 5.5 s, before the grade) lifts it: shot mean 73 vs 74 for the hook talk, darkest sample 65. The cut INTO CH1 in B (0122's white sky, luma 163, to 85) is the source footage; not touched.
3. **Blurs** are now gaussian blurs of the real pixels with a feathered edge (render.py `_patch`); the cluster patch runs to the frame edge with no ramp there (2 px sliver gone); the 0122 truck patch is 43x23 px on the plate only (the plate is static in the window: checked at start, mid, end).
4. **0095** is 2 beats (8.80-10.34); its spare beat went to 0098. The montage is still 20.0 s on the beat grid.
5. **Hook seam (2.27):** "SOS." ends 102.74 so it already has a 0.38 s tail, and "We're" starts at about 111.44 (in-point 111.40). Left the times; the seam dip (74 to 57 dB, 40 ms) is filled by running HOOK1's audio 40 ms past the cut under HOOK2's fade-in (`tail` in the EDL); the dip is now 67 dB.

## Sound and loudness

| | integrated | true peak | voice over music (min, every voiced 50 ms frame) |
|---|---|---|---|
| A (AAC file) | -14.1 LUFS | -2.2 dBTP | 12.7 dB |
| B (AAC file) | -14.1 LUFS | -2.1 dBTP | 12.8 dB |

B's montage measures -16.8 LUFS short-term (median of 3 s windows; -18.9 to -15.9). The bed is `../test-ch3/music.py`
(original, synthesized here, no sample or library track), regenerated at the length needed. Under talk it sits at
-39.5 LUFS and in gaps at -21, as in the approved chapter. In the montage the duck is off; it snaps back for CH1. In the
montage the source sound sits low (-30 LUFS, engine, road and wind, with any word reduced to its < 250 Hz rumble).
**0099 and 0122 carry no source sound**, because Shazam found car-stereo songs there (below). Every voice in the used
ranges is Omarie's (speakers.json scores all HOST), so nothing is muted for strangers. No word needed a bleep.

**Stereo check** (`/home/user/day-owt/qa/shz.py`, 8 s windows every 4 s, 7 Oct): no match on any used range except
0099 175-183 (Mrs. Trendsetter, Lil Baby), 0122 552-560 (spend the money, Fousheé) and 0122 583-591 (COMË N GO, Yeat).

## Deviations from the brief

1. **The 0117 hook lines play over cutaways.** In 0117 100-114 he holds a phone in his right hand while driving (the
   desert through the window is motion-blurred). This range isn't in flags.json; the frame check here found it. His
   0117 voice and road sound run on under 0121 (rear camera, desert) and 0099 (plains). Both cutaway clips also appear in
   B's montage, at different seconds (0121 148.4 vs 152.0; 0099 179.0 vs 176.3).
2. **HOOK 2 starts at 111.40, not 111.9.** small.en heard "I have to make it" at 111.86. medium.en hears "we're going to
   have to make it" from 111.44, so a cut at 111.9 would clip "gonna". The line now reads "We're gonna have to make it,
   we don't have a choice."
3. **HOOK 1 starts at 100.85.** medium.en hears "I have no cell service" with "I have" at 100.96, after "You feel me?"
   (ends 100.80). The line may open on "I have".
4. **The hook runs 16.7 s, not about 15.** It's the four lines with the word-level trims; nothing could be cut without
   cutting a word.
5. **0116 (sunrise) is dropped from the montage.** He holds a lit phone while driving in every frame of the fetched
   window (18-24). **0122 553-559 is dropped too**: it's the same rear-camera frame (Rio billboard and skyline) as 584-590,
   so the two read as one shot. The montage is 7 shots; 0092 and 0121 run a bar (4 beats) and 0122 six beats, to keep 20 s.
6. **The POV shots (0094, 0095, 0098, 0099 x2) use a high 16:9 window** (crop centre 0.30 of the square, not 0.5): road
   and sky, with the dash top at the bottom. In 0094 at about 28.6 he holds a lit phone in his right hand low in the
   frame, and the high window puts it outside the picture. The edge of the instrument cluster still shows at the bottom,
   so each of these shots carries a soft blur box over it. The lead decides whether a phone that is out of frame passes
   the hands rule.
7. **0122 blurs the front plate of the truck** behind the car (a fixed box over its bumper). The cars further back are a
   few pixels wide at 720p and aren't blurred; the checker should confirm on the 0.3 s gate sheets.
8. **CH1 ends at 86.38, not 86.6**, because the fetched mezzanine stops at 86.4. That still leaves 0.83 s after "famo".
9. **The limiter ceiling is -2.3 dBTP, not -1.5**, because the AAC encode added about 0.5 dB of true peak (B measured
   -1.2, then -1.49). The files measure -2.18 / -2.07 dBTP.
10. **music.py fix, done locally:** music.py fails when its last chord is shorter than its 1.2 s attack, so mix.py asks
    for a length rounded up to a whole chord + 3 s and trims it. `../test-ch3/music.py` is unchanged.

## On-screen and spoken claims

Nothing is drawn. Spoken lines carry "4:30 in the morning", "McLaren 600 LT" and "Seattle, Washington", in his own
voice from the day's footage. The Rio billboard in the last shot shows "OCTOBER 10" (third-party signage, unblurred).

## v2 (8 Oct): A2 and B2 (v2.2: re-cut after nq-check, then Omarie's two touch-ups on B2)

Omarie picked montage B, with the note "the montage could be more dramatic but its good its just full of shots of me
driving no critical moments interactions breaks, gas runs, etc". So B2 is a sound-bite trailer: real turning points cut
to the 78 BPM bed, with his short lines punching through. The empty-tank hook isn't resolved (the 0119 "Yes Lord" is out).
His two fixes are in both A2 and B2: a desert road cutaway under HOOK 2, and his face lifted in the dark CH1 tail. The v1
files are unchanged.

| file | what |
|---|---|
| `opening_A2_preview_720p.mp4` | 1280x720 29.97p H.264 + AAC, 22.56 s, 9.79 MiB, -14.1 LUFS, -2.2 dBTP (measured on the AAC) |
| `opening_B2_preview_720p.mp4` | 1280x720 29.97p H.264 + AAC, 51.42 s, 24.14 MiB, -14.1 LUFS, -2.1 dBTP (measured on the AAC); Omarie's pick for the full cut |
| `edl_A2.json`, `edl_B2.json`, `mix_A2.json`, `mix_B2.json` | timelines and mix reports. Smallest voice-over-music margin: A2 12.7 dB, B2 12.5 dB |
| `look_v2.json` | v2 framing, blurs (a blur may carry `from`, the shot second it starts) and the CH1 `subject_lift` |
| `subject_lift.py`, `lift_track_0075_80.5.json` | the CH1 face lift and its CSRT face track |
| `shazam_B2.txt` | Shazam on every used range |
| `gate/opening_{A2,B2}_shots_in_mid_out.png` | in, mid and out frames of every shot |
| `gate/gate_{A2,B2}_NN.jpg` | the frame gate on the whole timeline: a frame every 0.3 s, 640 px tiles, 12 a sheet, timeline time |
| `gate/gate_B2_shotNN_kk.jpg`, `gate/gate_A2_shot04_kk.jpg` | the same, per changed shot (every montage shot, the HOOK 2 cutaway, CH1), stamped with timeline time and source |

Rebuild:

    python3 make_edl.py                    # also writes edl_A2.json and edl_B2.json
    python3 mix.py A2; python3 mix.py B2
    python3 render.py gate A2; python3 render.py gate B2
    python3 render.py preview A2; python3 render.py preview B2

### B2 shot list

P means parked or on foot; M means moving. Cuts land on the beat grid, in whole, half or quarter beats (1 beat = 0.769 s).

| at | source (picture) | dur | heard | P/M |
|---|---|---|---|---|
| 0:00.00 | 0121 152.00 rear cam | 2.27 | HOOK 1 (0117) "no cell service, not an SOS" | M |
| 0:02.27 | **0121 199.60 desert road** | 2.22 | HOOK 2 (0117) "We're gonna have to make it, we don't have a choice" | M |
| 0:04.49 | 0075 56.45 | 4.50 | talk (as in v1) | P |
| 0:08.99 | 0075 69.32 | 7.70 | talk (as in v1) | P |
| 0:16.69 | 0091 7.30 | 2.31 | "(Spider) top goes down"; SE chest wordmark blurred (box extended 25 px down in v2.2) | P |
| 0:19.00 | 0093 6.20 | 2.31 | "out here, like gorgeous" | M, top down, one hand on the wheel |
| 0:21.31 | 0102 19.45 | 1.54 | "Red Bull and my snacks" | P, gas stop |
| 0:22.84 | 0105 7.30 | 1.54 | "To In-N-Out." | P |
| 0:24.38 | 0107 254.75 (picture) | 3.08 | 0106 182.05-184.35 "Where the [bleep] is the oil in this [bleep]?", held a beat | P, phone in hand |
| 0:27.46 | 0111 47.40 | 3.85 | "It's a McLaren." / "Everyone can say I'm a Corvette too" (nat muted) | P, on foot |
| 0:31.31 | 0112 13.90 | 1.92 | "gassed up, shawty" (pump panel blurred) | P |
| 0:33.23 | 0114 8.70 | 2.69 | "take a nice McLaren nap" (hoodie print and the lit TFT blurred) | P |
| 0:35.92 | 0114 42.65 | 3.08 | "We back in business, baby" (hoodie print and the lit TFT blurred) | P |
| 0:39.00 | 0115 12.75 | 2.31 | "It is freezing." (SE bolt logo blurred from +1.25 s) | P, on foot |
| 0:41.31 | 0118 83.60 | 2.50 | "No hotel, no nothing." (cluster blurred) | M, left hand on the wheel |
| 0:43.81 | 0118 90.05 | 1.35 | "But you know, we dug it out" (cluster blurred) | M, left hand on the wheel |
| 0:45.15 | 0122 583.40 rear cam | 1.92 | bed only (plate and LED billboard blurred) | M |
| 0:47.07 | 0075 82.04 | 4.34 | CH1 "So let's head up out of here. Alright famo." (J-cut: the line starts 1.54 s early, under 0122) | P |

The montage runs 0:16.69-0:47.07: 14 shots, 39.5 beats, 30.38 s. In v2.2 the 0118 night drive was trimmed from 5.0 to 3.85 s (3.25 + 1.75 beats), with both bites whole. Quick cuts (1.5-1.9 s) run through the gas and food run;
the oil scare, the counter, the nap, "back in business" and the night trouble get longer holds (2.7-3.9 s). A2 is the v1 A
with the new HOOK 2 cutaway and the lifted CH1 tail.

### CH1 face lift (0075 80.5-86.38)

`subject_lift.py` tracks his face with CSRT from four hand-set anchors. It then applies a gamma lift weighted by a soft
ellipse around the face times a luma key, which is hole-closed and eroded so the edge stays inside his silhouette. The
lift is solved per frame so the face-core median reaches 47 (gamma capped at 2.4), smoothed over 0.5 s, and then eased to
nothing over source 82.5-83.0 (`LIFT_END`). Frames with no lift pass through untouched, so from 83.0 the tail falls to
his natural silhouette, with no flat cutout and no glow on the wall. Face-core median luma (0-255), A2:

| s | 80.5 | 81.0 | 81.5 | 82.0 | 82.5 | 83.0 | 83.5 | 84.0 | 84.5 | 85.0 | 85.5 | 86.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| before (no lift) | 27 | 30 | 25 | 17 | 11 | 11 | 3 | 3 | 3 | 3 | 3 | 2 |
| after (v5) | 46 | 46 | 45 | 45 | 45 | 9 | 3 | 3 | 3 | 2 | 2 | 2 |

### Spoken names and figures (B2)

Spider (top), Red Bull, In-N-Out, McLaren (twice), Corvette; the hook keeps "4:30 in the morning", "Seattle, Washington"
and "McLaren 600 LT". No speed words, no prices ("$300 in gas", "Club 93" and "six hours out" are left out). Two words are
bleeped in the 0106 line.

### v2 deviations and drops

- 0090 is out: a whip pan, plus the McLaren's rear plate and a red car in frame. 0091 opens the montage instead.
- 0105 4.85 ("We finally made it") is out: its picture is near-black. The cut goes straight to the In-N-Out sign.
- 0123 is out: SE signage, SE print on his shirt, a stranger in frame, and the names "Joey and John". The end beat is 0122.
- 0100 is out, for length. 0099 179 is out, per the brief.
- The 0106 oil-scare picture is near-black, so its audio plays over 0107 254.75 (him parked at In-N-Out, gesturing, then
  looking up the oil cap on his phone). There's no hood-up or engine-bay shot on disk: only 0106 173.7-185.8 (near-black)
  and 0107 254.7-262.8 are cut. So the line is held a beat longer instead.
- 0111 is allowed despite a stranger flag (`ALLOW2`): the clerks are out of frame and his words only are heard.
- CH1 gets a mild whole-frame hqdn3d (3:2:6:5) before the lift.
- The personal-brand blurs (feathered, static boxes sized to cover the print's drift) are visible as soft patches:
  - 0091: the chest, for the whole shot.
  - 0114: the chest, on both shots.
  - 0115: the lower hoodie, from +1.25 s.
- 0122 583-588.5 matched "COMË N GO" (Yeat) on Shazam. It's picture plus bed only, with the nat muted, so it isn't heard.
  Every other range: no match.

## 4K master (9 Oct)

The approved B2 v2.2, unchanged in cut, framing, blurs and lift, rendered at 3840x2160 so it can sit in front of the
chapters with a stream copy. The videos live outside git, in `/home/user/day-owt/openwork/`:

| file | what |
|---|---|
| `master_video.mp4` | 3840x2160 H.264 High L5.1, yuv420p, 30000/1001, timebase 1/30000, bt709 tags, no audio; 1541 frames, 51.418 s, 271 MiB |
| `mix_B2.wav` | the B2 mix, 24-bit 48 kHz, 2,468,066 samples (51.418 s), -14.0 LUFS, -1.8 dBTP |
| `nomusic_B2.wav` | NO MUSIC: the same dialog and natural-sound buses (same gains), no bed, -14.0 LUFS, -1.8 dBTP |
| `opening_B2_master_preview_720p.mp4` | the 720p preview, cut from the music master (`../ch3`'s preview encode) |
| `mix_B2_master.json` (here) | the mix report: gains, margins per 50 ms frame and per word, both masters |

The two muxed masters (`opening_B2_master.mp4`, `_NOMUSIC.mp4`, AAC 320k) are made by `render.py master B2` and were
measured, then deleted for disk: -14.0 LUFS / -1.7 dBTP and -14.0 LUFS / -1.8 dBTP. Re-mux them from
`master_video.mp4` and the two wavs with `../ch3/render.py`'s `mux()` (or re-run `render.py master B2`: it reuses
`master_video.mp4` while `master_video.mp4.ok` exists).

Rebuild:

    python3 mix.py B2                  # mix_B2.wav + nomusic_B2.wav, CEIL -1.8 (`python3 mix.py B2 preview` keeps -2.3)
    python3 render.py master B2        # 4K shots -> master_video.mp4 -> both muxed masters -> 720p preview

What changed in the code:

- `render.py`: a `master` mode (and `timeline`). Every pixel value (blur boxes, feathers, blur sigma) is worked out
  on the 1280x720 design exactly as before and multiplied by one scale factor `S = W // 1280` (3 at 4K), so the
  blurs sit where the approved ones sit. The final encode and the mux are `../ch3/render.py`'s own `assemble()` and
  `mux()`, so the x264 options match the chapters' (checked against `ch1_master.mp4`: codec, profile, level, pix_fmt,
  rate, timebase, colour tags, SAR and the x264 option string are identical). `MEZZ` is `/home/user/day-owt/mezz`
  only. The per-shot intermediates are deleted once `master_video.mp4` exists. The system ffmpeg is used when the
  imageio build is missing.
- `subject_lift.py`: `lift_pipe_hi`. The face track, weight map and per-frame gamma are solved on a 720p area
  downscale of each 4K frame (the approved design), the weight map is upscaled by S, and the gamma is applied to the
  full-resolution luma. Frames are streamed twice, so a 4K shot is never held in memory. Peak gamma 1.82, as at 720p.
- `mix.py`: CEIL -1.8 (as the chapters, for AAC 320k), the NO MUSIC mix, and the margin per word (small.en word
  windows, as `../ch3/mix.py`).
- `words_b2.py`: two new ranges (0117 99.5-114.5, 0075 55.5-87) for the hook and CH1 captions. **Not transcribed
  yet**: faster-whisper 1.2.1 fails on this machine's PyAV 19.0.1 (`open() got an unexpected keyword argument
  'metadata_errors'`). `words_agree_B2.py` writes `words_agree_B2.json` for the montage only and lists the five
  hook/CH1 pieces under `missing`.

Checks:

- **Sound vs the approved mix:** bed, offset (1.772 s), natural sound and bleeps match. Dialog gains match except
  0091 (+4.8 dB against +4.7: the system ffmpeg's denoiser). Smallest margin 12.5 dB per 50 ms frame (as approved),
  18.1 dB per word.
- **Picture vs the approved gate sheets** (`gate/gate_B2_NN.jpg`, rebuilt from the master at 640 px, stamp masked,
  same colour matrix): mean PSNR 35.2 dB, SSIM 0.936 on 171 tiles. The 720p timeline from the same code scores 35.4,
  and 4K against 720p differs by 1.1 dB at most on any tile. The weakest tiles are 0118 83.6 (41.7-43.5), at about 27 dB:
  the new mezzanine's frame phase puts that shot one frame (33 ms) later than the preview.
- **The end:** 1541 frames. The last frame (index 1540) is at 51.3847 s and shows 0075 86.343. The picture ends at
  51.4180 s. The wav ends at sample 2,468,065 (51.41802 s). The last 60 ms are digital silence and the bed fades
  out over the last 1.2 s. The AAC track in the mux reads 51.413 s. The CH1 picture starts at frame 1411 (47.0804 s).
- **Not scaled:** the CH1 `hqdn3d=3:2:6:5` runs at 4K with the same strengths. Its spatial pass is a strength, not
  a radius, so at 4K it is a little lighter per pixel. The temporal pass is unchanged.
