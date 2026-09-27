# Build cue: "ROOF DOWN" McLaren 750S Spider (as built)

`lib/edl.py` holds the beat table as data. `front.html` holds the front-layer graphics and `mid.html` the
behind-the-car type. Times are output seconds. `src` is the 0-based source frame of
`SCE_McLaren-750S_no-branding.mov` (decoded in order, never with `-ss`).

## Output
- 1080x1920, 24000/1001 fps (the source rate), 432 frames = 18.018 s.
- Master: libx264 High@4.2, CRF 16, preset slow, yuv420p, BT.709 tagged. Delivery: the same picture, two-pass
  at 11.5 Mb/s (16 Mb/s max). Both carry AAC 48 kHz 192k from `audio/bed.wav`, muxed as-is, with +faststart.
- Sound: the clip's own music, orig 0.000 to 18.018 s, with no edit and no time-stretch. The picture is cut
  to its 130 BPM grid, beat k = 0.1154 + k x 0.4615 s. The designed accents sit at 45 % of the music's RMS.
  The track hands over to its own tape stop at 13.500 s and comes back on the end-card downbeat at 13.962 s.
  Master: -14.0 LUFS, true peak -2.6 dBTP (limiter ceiling -2 dBTP, the -3 dB mono fold-down included); the
  delivered AAC measures -14.1 LUFS / -2.7 dBTP. The last 50 ms are digital silence.

## Layer stack, per output frame
1. PLATE (`lib/plate.py` on `lib/fx.py`):
   - frame-exact sample: whole frames at 1.0x; every shot at another speed samples 4x optical-flow in-betweens
     (`lib/dense.py`, one minterpolate pass per shot), shutter-averaged at speed;
   - the licence-plate blur (beat 11);
   - on the roof shot: the push, then the sky matte (`lib/sky.py`);
   - the day grade, then on the roof shot a sky chroma lift, then streaks;
   - on the roof shot: the grad ND on the sky (0.28), the end-card ND (up to 45 % on the sky and the horizon
     haze, the car and hills held out, from 13.84 s), and the light sweep across the car body (13.62-14.05 s);
   - the hook push;
   - whips, the drop impact (on a reflect-padded frame, its scale floor eased out), light leaks.
2. MID (`mid.html`, roof shot only): MCLAREN 750S, the giant SPIDER and the end-card price. It is multiplied
   by the sky matte, so the car, the stowing roof and the hills stay in front of it.
3. FRONT (`front.html`): hook, brackets, badge label, offer, requirements, end card. Both HTML layers are
   captured by `lib/kcapture.js` with sub-frame motion blur: k=10 at 180 degrees, and 20-28 samples at 270
   degrees on the fast spans (see `KT_PLAN` in each page).
4. FINISH (`build.py`): plate, vignette 0.36 (picture only), matted mid, the crash punch on both together
   (12.115 s: 1.035 to 1.0 over 10 frames, a one-frame 5 % lift), then the front layer, then grain 0.02.

## Beat table
| # | Out (s) | Frames | Source | Retime | Plate FX | Graphics | Sound |
|---|---|---|---|---|---|---|---|
| 1 | 0.000-1.038 | 0-24 | f380-392 front hero, LED headlights | 0.5x | push 1.00 to 1.04 over beats 1-3; point streaks | HOOK complete on frame 0; offer re-hit + glint on beat 1 (0.577) | impact_open 0.000 |
| 2 | 1.038-1.962 | 25-46 | f261-282 locked-off canyon approach | 1.0x, whole frames | leak 0.18 right | hook; glint on 750S SPIDER on beat 2 | |
| 3 | 1.962-2.885 | 47-68 | f313-334 front approach, saguaro road | 1.0x | | hook whips up at 2.715-2.88 | whoosh 2.735 |
| 4 | 2.885-4.615 | 69-110 | f204-225 POV wheel, McLaren speedmark | 0.525x (optical flow, each frame averaged over a whole source frame) | leak 0.22 left; instrument cluster defocused | brackets fly in from off-frame over 5 frames and lock to the speedmark (the medallion track carried to the logo); label MCLAREN / 750S SPIDER / 2026 · EXOTIC, every line set by 3.26 s; glint on beat 8; whip-out 4.489-4.609, gone before the gap | ticks 2.86 / 3.07; noise riser 3.23-4.60; whoosh 4.50 |
| 5 | 4.615-4.731 | 111-112 | black | | | | drop gap |
| 6 | 4.731-5.654 | 113-135 | f173-194 low wheel tracking along the white line | ramp 1.9x to 0.8x (optical flow) | impact k=0..15 (flash on k0, k1) | OFFER: 5 HOURS, LAS VEGAS, then $1,299 in slot reels landing 5.192 / 5.308 / 5.423 / 5.654 | DROP impact 4.731; reel ticks |
| 7 | 5.654-6.577 | 136-157 | f226-247 under the bridge, sun on the wheel | 1.0x | whip left (3+3 frames); point streaks | stripe (y 728, clear of the comma); FULL DAY · $1,799 wipes in | whoosh 5.654 |
| 8 | 6.577-7.038 | 158-168 | f138-148 headlight glide | 1.0x | leak 0.22 right; streaks | brackets lock to TRACKS.headlight, clamped below the offer panel (y >= 836), collapse over the last 2 frames; price glint | ticks 6.58 / 6.79 |
| 9 | 7.038-7.500 | 169-179 | f158-168 side intake, red accent | 1.0x | | offer | |
| 10 | 7.500-7.962 | 180-190 | f112-122 hands on the carbon wheel | 1.0x | | offer figures fade 7.75-7.85, the panel whips up 7.83-7.96 | whoosh 7.842 |
| 11 | 7.962-8.423 | 191-201 | f352-362 rear chase on the curve | 1.0x | licence plate blurred | REQUIREMENTS panel from 8.00: YOU NEED / VALID DRIVER'S LICENSE / INSURANCE (5 words, held about 2.6 s) | |
| 12 | 8.423-9.346 | 202-223 | f466-487 wide valley, the car on the road | 1.0x | whip up | requirements | whoosh 8.423 |
| 13 | 9.346-9.808 | 224-234 | f99-109 roadside, the car enters past the rock | 1.0x | | requirements | |
| 14 | 9.808-10.269 | 235-245 | f369-378 front 3/4, rocks | 0.95x (optical flow) | | requirements | |
| 15 | 10.269-10.731 | 246-256 | f79-92 whip-pan pass (natural blur) | 1.3x (optical flow) | | requirements: the rows fade as the panel whips up 10.60 | |
| 16 | 10.731-18.018 | 257-431 | f0-64 ROOF DOWN, locked-off rear (the roof stows) | 0.55x, then 0.5x after the crash, tape stop 13.500-13.962, frozen to 14.21, then eases in to 0.31x | whip left in; optical flow 4x; push 1.000 to 1.045 (outQuad, never stops); grad ND + sky chroma lift; crash punch on the composite at 12.115; light sweep 13.62-14.05; end-card sky ND from 13.84 | mid: MCLAREN 750S tracks in 11.14; SPIDER rises glyph by glyph from 11.192; crash pulse + glint 12.115; sinks 13.50-13.88; END CARD 13.962: price fades up from behind the car, logo, MCLAREN 750S SPIDER, 5 HOURS · LAS VEGAS, TEXT OR DM TO BOOK, phone · site, handle, both requirement lines | whoosh 10.731, 11.242; crash impact 12.115; tape stop 13.500; swell; END impact 13.962 |

## Front-layer graphics (ink top-left; copy is templated from config.json)
- Every whip exit fades all its text rows from 1 frame before to 2.5 frames into the whip, so a smear can
  never form a readable wrong figure and no panel sits empty.
- **Hook** (0-2.88): panel #000 86 % at x 54-900, y 280-712, with the 78/22 stripe cap. MCLAREN · LAS VEGAS
  (Michroma 34 gold, y 318). 750S SPIDER (Bebas, fitted to 776 px, y 372). 5 HOURS · $1,299 (Bebas 96 gold,
  y 528). The white SCE lockup (240 px) sits at y 642. Every line is set on frame 0, so `poster.jpg` is a
  complete ad.
- **Badge callout** (2.88-4.71): the brackets are padded 6 % around the tracked medallion. The label panel is
  640x240 at (54, 930) and follows the badge on a spring (gain 0.25). A leader line draws from the bracket
  up to the panel.
- **Offer** (4.73-7.96): panel #000 88 % at x 54-900, y 280-820. 5 HOURS (Bebas 120, y 305). LAS VEGAS
  (Michroma 30 gold, right edge x 866). $1,299 slot reels (Bebas 330 gold, y 430). The stripe is at y 728,
  then FULL DAY · (Bebas 60, y 752, wipes in) and $1,799 (Bebas 60 gold, arrives whole 3 frames after). The
  panel scales 1.08 to 1.0 and shakes with the plate for 2 frames.
- **Requirements** (8.00-10.73): panel at x 54-900, y 280-572. YOU NEED (Michroma 30 gold), then VALID
  DRIVER'S LICENSE and INSURANCE (Bebas 84). The age requirement, in the site's own wording, is on the end card.
- **End card** (13.962 to the end):
  - The SCE lockup (360 px) is at y 282, then MCLAREN 750S SPIDER (Michroma 30, MCLAREN in gold) at y 384
    and 5 HOURS · LAS VEGAS (Bebas 64) at y 428.
  - The price $1,299 (mid layer, Bebas 236 gold, baseline 676, a close dark halo) fades up as one word from
    TE+0.03 (a 14 px rise, outCubic over 0.42 s, the fade over its first 0.14 s), so its comma never dips
    behind the buttress; glints at TE+0.9 and TE+2.6. SPIDER has sunk by 13.88 s. The top block carries dark
    halos. The sky behind the block is taken down by the end-card ND (the band plus a haze key, holding out
    the car and hills).
  - The bottom stack runs over a scrim, under a 78/22 stripe at y 1224: TEXT OR DM TO BOOK (Bebas 80,
    y 1246), (725) 425-3583 · SUPERCAREXP.VIP (Bebas 60, y 1328), @SUPERCAR_EXPERIENCE_ (Bebas 60, y 1384),
    RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE (Bebas 44, y 1440), and VALID DRIVER'S LICENSE · INSURANCE
    (Bebas 44, y 1486). All ink stays above y 1536.
  - The last frame is a complete still; the sound fades out under it.
