# FD C63 - "Cut Back" reel (exhaust) - Wed 28 Oct 2026

Style: **Cut Back** (new, picked by Omarie 2026-10-12). One car, one question: open on the payoff,
cut back to how it got there. Not Locked-On: no brackets, callout lines, step cards or whips.
Same silver C63 AMG in every clip; the bench parts went on it (Omarie, 2026-10-12).

Build: `python3 build.py --raw <folder with IMG_0325/0579/0590.MOV> [--work <scratch>]`
(`--stills` writes check stills only; `--audio-only` rebuilds sound and re-muxes).
Needs ffmpeg 6+, numpy, Pillow, opencv-python-headless. Brand values come from `99-toolkit/fd_brand.py`.
Source footage and the mp4 are not committed.

Output: `exports/FD C63 - Cut Back (exhaust, 15s) - INSTAGRAM 1080x1920.mp4`, 1080x1920, 30 fps,
H.264 High, yuv420p/bt709 (tv range), AAC 48 kHz stereo 192k, 15.17 s (455 frames, none dropped: the audio is built to exactly 455/30 s and the mux no longer uses `-shortest`).

v2 (2026-10-13), after nq-check: part brands off screen (hang tag and the can's etched name/text
framed out), lift and third-party branding off the "before" shot, no synthetic sound, parts section
cut from 6.65 s to 2.9 s, "NEW." moved onto the X-pipe, a close-up of the new piping under the
bumper added to the payoff, hook text 40 px lower.

v3 (2026-10-13), after nq-check failed v2: colour matrix fixed (see Colour), the near-silent bench gap
(6.0-8.3 s) closed by trimming parts3 to 0.5 s and sliding the cold start in behind it (fire now at 7.60 s),
the 0.8 s given back to the held rev; the last 4 end-card frames are no longer dropped by the mux.
Piping close-up unchanged: Omarie confirmed on 13 Oct 2026 that the gold pipe under the diffuser is FD's work.

## Colour

The rgb24 frames are converted with an explicit matrix in the encoder (`-vf scale=in_range=full:out_range=tv:
out_color_matrix=bt709`), because without it ffmpeg encoded BT.601 under a BT.709 tag and FD red decoded as
(255,38,15). Measured on the delivered mp4 decoded as BT.709/tv: hook underline (254,14,20) vs #FE0F13 (254,15,19);
end-card stripe red (254,14,19), green (30,174,75) vs #1DB14B (29,177,75), yellow (254,219,1) vs #FFDE00 (255,222,0),
all within 4. The cover jpg is written straight from the RGB frame (sRGB, no YUV step), so it is unaffected.

## Shot list (timeline / source)

| # | timeline | source | source in-out | framing |
|---|---|---|---|---|
| hook | 0.00-2.00 | IMG_0590 | 63.40-65.40 | tight right-rear, slow push (crop w 1260 to 1120 src px); strongest rev (onset 63.5) |
| before | 2.00-5.00 | IMG_0325 | 4.25-7.25 | rear three-quarter, crop top held at src y 1380 so the lift posts' maker name (above y 1290) never shows; stock revs at 4.3 and 7.0 |
| parts1 | 5.00-6.10 | IMG_0579 | 5.10-6.20 | X-pipe and its first brace; framed left of / above the hang tag every frame |
| parts2 | 6.10-6.60 | IMG_0579 | 7.45-7.95 | macro of the X-pipe brace, below the muffler can |
| parts3 | 6.60-7.10 | IMG_0579 | 10.35-10.85 | X-pipe outlets and the bent link pipe, above the muffler can |
| coldstart | 7.10-9.57 | IMG_0590 | 6.20-8.67 | wider rear; cold start fires at src 6.70 = timeline 7.60; its audio starts under parts3 at 6.60 |
| piping | 9.57-10.37 | IMG_0590 | 53.90-54.70 | close-up of the burnt piping under the bumper between the tip pairs (crop w 520 to 470, src y about 1100-2000; tips, plate and meter logo box out of frame); the rev burst lands on the cut |
| rev | 10.37-13.47 | IMG_0590 | 54.70-57.80 | held, uncut (3.1 s, was 2.3); burst at src 56.6 = timeline 12.27 |
| end | 13.47-15.17 | IMG_0590 | 57.80-59.50 | same framing, darkened 72% + soft blur over 6 frames |

Part brands: in IMG_0579 a branded hang tag (maker's logo, serial, address) hangs under the X-pipe's
second brace until about 7.4 s, and the muffler can carries the maker's name and lines of text etched on
its side (readable whenever the can's side faces the camera, about 7.4-13.9 s). Every parts shot is framed
so neither is in frame; `exports/qa/brandscan_parts_*.jpg` shows every frame of 5.00-7.90 at half size.
IMG_0570 is not used (different car). IMG_0590 windows avoid the person at the left edge (about 1,
37-41 and 69-73 s); the latest window now ends at 59.5 s.

## Text cards (all Bebas Neue, inside the 9:16 safe zone: top 11%, bottom 20%, left 5%, right 16%)

| card | in-out (s) | spec |
|---|---|---|
| WHAT DID WE DO / TO THIS C63? | 0.00-2.00 | white, 168 px, 2 lines, left at x 64, top y 281 (40 px lower than v1, so it clears the grid's 3:4 crop at y 240 with margin); FD red #FE0F13 underline under "C63" only; soft top scrim |
| SEP 29 | 2.00-3.00 | white 72 px top-left, typed 2 frames per character, light top scrim |
| OCT 7 | 5.00-6.00 | as SEP 29 |
| NEW. | 5.20-5.90 (6 frames in, 0.7 s) | FD red, 380 px, centred in safe zone over the X-pipe, hard on/off. Red, not white: the ground is white paper. Not used on any tip shot |
| End mark | 13.47-15.17 (6-frame fade in) | `fd-icon-mark-only--white` 380 px wide, the five-segment stripe drawn from `fd_brand.ACCENT_STRIPE` (red 36.7 / black 21.4 / white 19.4 / green 17.0 / yellow 5.5), "DM TO BOOK YOUR BUILD" 60 px white |

No figures, prices, part brands or material names. Copy passed SlopMonster 5/5 (unchanged from v1).

**Dates:** "SEP 29" and "OCT 7" are the camera creation dates in each clip's metadata
(`com.apple.quicktime.creationdate`): IMG_0325 2026-09-29T17:33:30-0700, IMG_0579
2026-10-07T12:34:34-0700, IMG_0590 2026-10-07T15:37:14-0700.

## Redaction (plates, the sound meter, third-party branding)

Box collapsed to a colour field (plates 6x3 blocks, meter LCD 3x4, livery 3x3, crate 3x2), 24 px
feathered outer edge; the box itself is always fully covered. Boxes are tracked per frame by template
match (OpenCV, half res, search +-90 px) and smoothed over 5 frames, in source space before the crop.

| window (timeline s) | what | tracker min score |
|---|---|---|
| 0.00-2.00 | 0590 plate (part in frame), meter (just off frame) | 1.00 / 0.98 |
| 2.00-5.00 | 0325 plate; another customer's car's sponsor logo and name (right edge); printed maker emblems on a parts box beside the tail light | 0.80 / 0.96 / 0.82 |
| 7.10-9.57 | 0590 plate + meter LCD | 1.00 / 0.98 |
| 9.57-10.37 | 0590 plate + meter LCD (both outside the piping crop; tracked anyway) | 1.00 / 0.99 |
| 10.37-13.47 | 0590 plate + meter LCD | 1.00 / 0.98 |
| 13.47-15.17 | 0590 plate + meter LCD (under the darken) | 1.00 / 0.99 |

Check sheets in `exports/qa/`: `redaction_<shot>_<box>.jpg` (every 2nd frame at 240 px tiles, cropped
around the box), `brandscan_parts_01-06.jpg` (every frame of the parts section, 5.00-7.10, 540x960 tiles),
`piping_every_frame_01-02.jpg` (every frame of the piping close-up), `render_every_0.5s.jpg` (whole render).

## Sound

The car's own sound only: no music, no added effects (v1's synthetic 58 Hz sub hits and noise whoosh are
gone). Each window's own audio with 8-12 ms fades at cuts, plus two real-audio overlaps: an L-cut where
the stock car's rev and idle (IMG_0325 7.25-8.45) carry 1.2 s into the parts with a 0.5 s fade, and a
J-cut where the cold start's own audio (IMG_0590 from 5.70) comes in 0.5 s under the start of parts3 (6.60 s) so
the starter is heard before the picture changes. Bench audio under the parts at 0 dB. 1.3 s fade on the
end. Mix peak-normalised, then two-pass loudnorm (I -14, TP -1.5, linear).

Measured on the delivered mp4 (ffmpeg ebur128, peak=true): **-13.9 LUFS integrated, LRA 4.4 LU,
true peak -2.5 dBTP.** Momentary minimum per second: 5-6 s -22.9, 6-7 s -39.7, 7-8 s -32.2 (this second holds the
deliberate breath before the fire at 7.60), 8-9 s -17.1 LUFS. The lowest stretch is about 6.3-7.35 s (below -30,
about 1 s): bench room tone under parts3, then the starter crank. Starting the J-cut earlier (0.7 s) was tried and
is quieter (the source is silent before 5.70), so it stays at 0.5 s.

## Grade

One LUT on all three clips: slight S-contrast, blacks lifted to about 3.5%, a touch of warmth
(R x1.025, B x0.965), 8% desaturation so the gloss (0325) and satin-looking (0590) shots sit together;
exposure trims 0590 1.00, 0325 0.96, 0579 0.97.

## Font licence

Bebas Neue Regular (Dharma Type), SIL Open Font License 1.1. The build uses the repo's bundled copy,
`formula-dynamics/07-fonts/BebasNeue-Regular.ttf`, with its licence `07-fonts/OFL-BebasNeue.txt`, because
`fd_brand.FONT_BEBAS` points there. The Google Fonts file
(https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf, same OFL) is a different
build byte-for-byte (sha256 b3e03aaa... vs 1551a5e5...); not swapped in, to keep FD's type identical across pieces.
