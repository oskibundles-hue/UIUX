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
