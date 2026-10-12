# FD C63 - "Cut Back" reel (exhaust) - Wed 28 Oct 2026

Style: **Cut Back** (new, picked by Omarie 2026-10-12). One car, one question: open on the payoff,
cut back to how it got there. Not Locked-On: no brackets, callout lines, step cards or whips.
Same silver C63 AMG in every clip; the bench parts went on it (Omarie, 2026-10-12).

Build: `python3 build.py --raw <folder with IMG_0325/0579/0590.MOV> [--work <scratch>]`
(`--stills` writes check stills only; `--audio-only` rebuilds sound and re-muxes).
Needs ffmpeg 6+, numpy, Pillow, opencv-python-headless. Brand values come from `99-toolkit/fd_brand.py`.
Source footage and the mp4 are not committed.

Output: 1080x1920, 30 fps, H.264 High, yuv420p/bt709, AAC 48 kHz stereo 192k, 17.50 s.

## Shot list (timeline / source)

| # | timeline | source | source in-out | framing |
|---|---|---|---|---|
| hook | 0.00-2.00 | IMG_0590 | 63.40-65.40 | tight right-rear, slow push (crop w 1260 to 1120 src px); strongest rev (onset 63.5) |
| before | 2.00-5.00 | IMG_0325 | 4.25-7.25 | trunk open, stock revs at 4.3 and 7.0; speech (0.1-2.1) avoided |
| parts1 | 5.00-6.00 | IMG_0579 | 7.20-8.20 | tips close, push |
| parts2 | 6.00-7.00 | IMG_0579 | 8.30-9.30 | pull |
| parts3 | 7.00-8.30 | IMG_0579 | 9.60-10.90 | push |
| parts4 | 8.30-9.50 | IMG_0579 | 11.10-12.30 | tight |
| parts5 | 9.50-11.00 | IMG_0579 | 12.35-13.85 | wide of all parts |
| coldstart | 11.00-13.45 | IMG_0590 | 6.15-8.60 | wider rear; cold start fires at src 6.7 = timeline 11.55 |
| rev | 13.45-16.00 | IMG_0590 | 54.45-57.00 | held, uncut; bursts at src 54.6 and 56.6 |
| end | 16.00-17.50 | IMG_0590 | 57.00-58.50 | same framing, darkened 72% + soft blur over 6 frames |

0579 starts at 7.2 s on purpose: from 0 to about 7.0 s a branded hang tag (part maker's logo, a serial
number and an address) hangs off the pipes in frame. IMG_0570 is not used (different car).
IMG_0590 windows avoid the person at the left edge (about 1, 37-41 and 69-73 s).

## Text cards (all Bebas Neue, inside the 9:16 safe zone: top 11%, bottom 20%, left 5%, right 16%)

| card | in-out (s) | spec |
|---|---|---|
| WHAT DID WE DO / TO THIS C63? | 0.00-2.00 | white, 168 px, 2 lines, left at x 64, y 241; FD red #FE0F13 underline under "C63" only; soft top scrim |
| SEP 29 | 2.00-3.00 | white 72 px top-left, typed 2 frames per character, light top scrim |
| OCT 7 | 5.00-6.00 | as SEP 29 |
| NEW. | 5.233-5.933 (7 frames in, 0.7 s) | FD red, 380 px, centred in safe zone, hard on/off. Red, not white: the ground is white paper |
| End mark | 16.00-17.50 (6-frame fade in) | `fd-icon-mark-only--white` 380 px wide, the five-segment stripe drawn from `fd_brand.ACCENT_STRIPE` (red 36.7 / black 21.4 / white 19.4 / green 17.0 / yellow 5.5), "DM TO BOOK YOUR BUILD" 60 px white |

No figures, prices, part brands or material names. Copy passed SlopMonster 5/5.

## Redaction (plates and the sound meter)

Box collapsed to a colour field (plates 6x3 blocks, meter LCD 3x4), 24 px feathered outer edge; the box
itself is always fully covered. Boxes are tracked per frame by template match (OpenCV, half res,
search +-90 px) and smoothed over 5 frames, in source space before the crop.

| window (timeline s) | what | tracker min score |
|---|---|---|
| 0.00-2.00 | 0590 plate (part in frame), meter (just off frame) | 1.00 / 0.98 |
| 2.00-5.00 | 0325 plate | 0.80 |
| 11.00-13.45 | 0590 plate + meter LCD | 1.00 / 0.98 |
| 13.45-16.00 | 0590 plate + meter LCD | 1.00 / 0.98 |
| 16.00-17.50 | 0590 plate + meter LCD (under the darken) | 1.00 / 0.99 |

Check sheets: `exports/qa/redaction_<shot>_<plate|meter>.jpg`, every 2nd frame at 240 px tiles, cropped
around the box. `exports/qa/render_every_0.5s.jpg` is the whole render at 1 frame per 0.5 s.

## Sound

Car sound only, no music. Each window's own audio, 8-12 ms fades at cuts (0579 at -4 dB under the
parts). Self-made: 58 Hz sub hits at 5.0, 6.0, 7.0, 8.3, 9.5 and 11.0 s, a noise whoosh 10.55-11.0 s,
1.3 s fade on the end. Mix peak-normalised to -3.1 dBFS, then two-pass loudnorm (I -14, TP -1.5, linear).

Measured on the delivered mp4 (ffmpeg ebur128, peak=true): **-14.0 LUFS integrated, LRA 8.7 LU,
true peak -1.5 dBTP.**

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
