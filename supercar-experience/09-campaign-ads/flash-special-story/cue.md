# SE: LAMBORGHINI HURACÁN STO: 2-HOUR FLASH SPECIAL, Story 9:16 (FINAL CUE)

This is the judge's final cue as built. Where the build departs from it, the change is listed first with the
reason. Everything else in `story.html` / `build_story.py` follows the text below.

## As built: deviations from the cue

| # | Cue said | Built | Why |
|---|---|---|---|
| D1 | B2 0.7x with `minterpolate=mi_mode=blend` | `fps=24` frame repeat for B2 only (the cue's own fallback) | Blend frames double-printed the LAMBORGHINI lettering on the crest (plate frames 52, 59, 62). B3 blend was clean and is kept. |
| D2 | Plate as JPEG frames, composited in Chromium | Plate as RGB PNG (BT.709 limited → full-range RGB, explicit matrix), overlay rendered transparent by `story.html` + `render_overlay.js`, composited with ffmpeg `overlay` in RGB | The build rules ask for a transparent seekable overlay + ffmpeg composite. PNG also avoids decoding BT.709 data through the JPEG (BT.601) matrix. Same pixels, same layer order. |
| D3 | Plate one-pass command ends `concat,fps=24,...` | `concat,settb=1/24,setpts=N,...` and `-fps_mode passthrough` | The cue command wrote 332 frames, not 328 (image2 duplicated frames on the 10-bit source's timestamps). With passthrough it writes exactly 328. Same source ranges. |
| D4 | B6 CSS push on the plate `<img>` | Same push (1.00→1.03 linear in t, origin 50% 45%) applied to plate frames 188–238 with Pillow Lanczos | The plate is not in the page (D2). |
| D5 | B3 STO lock box fixed at x 20–80% | Box tracks the lettering: x `20 − 3.07·(t−3.5)`% to `80 + 2.27·(t−3.5)`% | Measured on the plate, the STO lettering grows from x 23.2–76.1% (3.5 s) to 19.8–78.8% (4.583 s); a fixed box ends up touching the letters. |
| D6 | B8 soft brackets: box linear in t (6–82/41–58 → 5–95/40–58.5) | Same end points, eased on `1−exp(−(t−11)/0.8)` (normalised) | The in-camera push decelerates: car nose at x 81.5% (11.00), 88% (11.58), 93.5% (13.29). A linear box let the nose poke past the bracket around 12 s. Checked on stills at 11.58 and 13.29. |
| D7 | Visibility windows | Evaluated on the 24 fps frame grid (`round(t·24)`) | Cue times are 3-decimal frame boundaries (9.417 = frame 226 = 9.41667). Comparing raw decimals left frame 226 with the rows still on; now it is clean as the cue intends. |
| D8 | Mix → `loudnorm=I=-14:TP=-1.0:LRA=7` | Mix gets a gentle tanh saturation (drive 2.2), then two-pass linear loudnorm with TP −1.5. Final file: −14.2 LUFS integrated, −1.4 dBTP | The raw sub thumps set the peak, so linear loudnorm stopped at −14.5 and the AAC encode overshot to −0.7 dBTP. Saturating the thumps lowers the crest factor (and adds harmonics so the hits read on phone speakers); the TP −1.5 target leaves room for AAC overshoot. |
| D9 | Build rules say prefer the clip's own audio | Original synthesised bed only (cue section 5) | Provenance of the reel audio is unknown and the edit reorders the shots. The cue's alternate master applies only if Omarie confirms the reel audio is licensed. |

---

1080x1920, **24 fps**, **372 frames = 15.500 s**, H.264 yuv420p. Treatment: house `hud` (approved), in motion.

## Colours and fonts

- GOLD `#FBD101` is the single accent.
- WHITE `#FFFFFF` is the headline colour.
- BLACK `#000000`.
- STRIPE = a horizontal bar, gold for the left 78% of its length and white for the right 22%. Never vertical.
- Fonts, loaded via @font-face and awaiting `document.fonts.ready`:
  - `07-fonts/BebasNeue-Regular.ttf` (headlines).
  - `07-fonts/Michroma-Regular.ttf` (readouts).
- Glyphs verified: Á, ·, –, +, @ and ' are present in both fonts. **◆ is missing from both**: separators are CSS 9x9px gold squares rotated 45°.

## Positions, easing and timing

- All positions are fractions of the frame (x of 1080, y of 1920).
- "cap top" means the top of the capital letters. Every text line is placed by its cap top: at load, `actualBoundingBoxAscent('H')` versus `fontBoundingBoxAscent` per font/size (canvas measureText) offsets each absolutely positioned line box.
- Tracking values are in em (CSS letter-spacing).
- Easings: `easeOutExpo = 1-2^(-10p)`, `easeOutCubic = 1-(1-p)^3`, `easeInCubic = p^3`, `easeInOutCubic`, `easeOutBack(s=1.2)`.
- "Masked rise" = the line sits in an overflow:hidden box of its own line height and translates from +105% to 0.
- Every animation is a pure function of t = frame/24. No CSS transitions or animations.

## 0. Pipeline

`python3 build_story.py` runs all of it (plate → overlay → audio → encode → QA). Source ranges:

| # | t0 | t1 | out frames | src frames | speed | shot |
|---|---|---|---|---|---|---|
| B1 HOOK | 0.000 | 1.833 | 0–43 | 393–436 | 1.0 | STO front-on, driving at camera at night, headlights on |
| B2 BRAND LOCK | 1.833 | 3.083 | 44–73 | 56–76 | 0.7 (frame repeat, D1) | LAMBORGHINI crest close-up on lime body |
| B3 MODEL LOCK | 3.083 | 4.750 | 74–113 | 148–179 | 0.8 (blend) | 'STO' lettering on the carbon deck |
| B4 FLASH WINDOW | 4.750 | 6.542 | 114–156 | 279–321 | 1.0 | 3/4 front rolling past the city → low-front headlights |
| B5 REQUIREMENTS A | 6.542 | 7.833 | 157–187 | 324–354 | 1.0 | side profile tracking, yellow caliper |
| B6 REQUIREMENTS B + HUD OUT | 7.833 | 9.958 | 188–238 | 182–232 | 1.0 | front-on under the white canopy; push 1.00→1.03 |
| B7 CLEAN BREATH | 9.958 | 11.000 | 239–263 | 358–382 | 1.0 | wide: car rolls past a lit canopy |
| B8 THE ASK | 11.000 | 13.667 | 264–327 | 498–561 | 1.0 | parked at the Las Vegas Convention Center, in-camera push |
| B9 END CARD | 13.667 | 15.500 | 328–371 | none | none | solid #000 |

Grade: `eq=contrast=1.04:saturation=0.96:gamma=1.0,vignette=angle=PI/5` only (the source is already a finished reel grade). No LUT, no hue or saturation push that could clip the lime paint.

Encode: `libx264 -preset slow -crf 17 -profile:v high`, BT.709 limited range yuv420p, AAC 192k 48 kHz stereo, `+faststart`.

Verify stills: t = 0.000, 1.000, 2.500, 3.900, 5.900, 7.500, 8.800, 10.400, 12.200, 14.900 (Á renders; 'VALID DRIVER'S LICENSE' right edge ≤ x 84%; nothing in the top 14% or bottom 20% except the ticker bar edge and the transit scan lines).

**Measured band luma** (0–255, x 5–84%, mean (min–max) p98), the reasons for every placement:

- B1: 14–22% 29 (22–36, p98 110 street-lamp glow); 22–30% 29; 30–35% 39; headlights 46–58% 108 (p98 249).
- B2: 14–21% 130 (63–201); 21–31% 133 (67–203). Swings widely, so the tag goes on a solid plate.
- B3: 14–34% 22; 34–46% 27 (rock-steady dark); 58–80% 218 (lime, so no type there).
- B4: mid 35.5–66.5% 94 (p98 241); 64.5–80% 56.
- B5: mid 111 (p98 250); 64.5–80% 39.
- B6: mid 79 (p98 230); 64.5–80% 16.
- B7: mid 97 (p98 226). No type.
- B8: facade 14–46% 148 (p98 255, third-party IBIE banner at y 14–25%, so no type there); car 44–59% 62; 58–66% 20; 66–75% 24; 75–80% 23.

**House rules check:**
- Hook clears at 1.833, before any HUD furniture (4.75).
- The HUD is fully clear at 9.417 (frame 226) and the ask starts at 11.042 (1.625 s ≥ 1.6).
- The CTA is gone at 13.417 (frame 322) and the end card hard-cuts at 13.667 (0.25 s clean footage).
- Scrim or plate wherever the shot changes under type (B4→B5→B6).
- No corner logo bug (top band swings 20→148): the SE mark lives inside the title block.
- The stripe is horizontal everywhere.

## 2. Beat-by-beat graphics

### B1 HOOK 0.000–1.833
- Hook scrim `linear-gradient(to bottom, rgba(0,0,0,0) 12%, rgba(0,0,0,.45) 18%, rgba(0,0,0,.45) 32%, rgba(0,0,0,0) 38%)`, opacity 1 from frame 0, fades 1.667–1.833 (linear).
- '2-HOUR' Bebas 210px GOLD, x 7.5%, cap top 15.0%. Frame 0 fully opaque at scale 1.06 → 1.00 over 0–0.292 (easeOutExpo), origin left bottom.
- 'FLASH SPECIAL' Bebas 150px WHITE, x 7.5%, cap top 24.2%. Fully opaque on frame 0; scale 1.04 → 1.00 over 0.083–0.333.
- 'ENDS 1PM TODAY' Michroma 34px, tracking 0.18em, cap top 31.6%; '1PM' GOLD. Opacity + translateY 20→0 over 0.292–0.625 (easeOutCubic).
- Stripe 180x8, top 33.9%, reveals L→R over 0.417–0.792.
- Exit 1.667–1.833: translateY 0→−30, opacity 1→0 (easeInCubic); stripe retracts R→L.
- Transition: hard cut; 3px GOLD scan line at 70% sweeps y 14%→86% over frames 43–45.

### B2 BRAND LOCK 1.833–3.083
- Brackets 6px/70px arms: start box x 5–95%, y 15–80%, fade in over 2 frames; contract to lock box x 6–94%, y 32–77% over 1.875–2.250 (easeOutExpo); 8px inward tick 2.250–2.375; exit 3.000–3.083 jump 20px out + fade.
- Tag plate rgba(0,0,0,.85), x 5–62%, y 19.5–30.0%; 6px stripe on its bottom edge drawn L→R 2.000–2.333; plate slides +24px from the left with opacity over 1.875–2.208.
- 'BRAND' Michroma 22 GOLD 0.22em, cap top 21.2%, fades 1.958–2.208.
- 'LAMBORGHINI' Bebas 110 WHITE, cap top 23.4%, masked rise 1.917–2.250 (easeOutExpo).
- Plate and text hard-cut out with the shot at 3.083.

### B3 MODEL LOCK 3.083–4.750
- Brackets 6px/50px arms re-enter from the frame corners at 3.083 and contract to the STO box (y 45.5–53.5%; x tracks the lettering, D5) over 3.125–3.500; 8px tick 3.500–3.625; exit 4.583–4.667.
- 'MODEL · 2023' Michroma 22 GOLD 0.22em, cap top 34.2%, clip-wipe L→R 3.250–3.583.
- 'HURACÁN STO' Bebas 120 WHITE, cap top 37.2%, masked rise 3.167–3.542.
- No plate (34–46% band is 26–29 luma); both lines `text-shadow: 0 2px 18px rgba(0,0,0,.45)`.
- Exit 4.583–4.708: both lines slide up in their masks (easeInCubic). Nothing on the lime lower half.

### B4 FLASH WINDOW 4.750–6.542 (HUD builds)
- Mid scrim `linear-gradient(to bottom, rgba(0,0,0,0) 34%, rgba(0,0,0,.80) 38%, rgba(0,0,0,.80) 62%, rgba(0,0,0,0) 66%)`, in 4.667–4.875, holds to the HUD exit.
- Title block (4.79–9.42): plate rgba(0,0,0,.80) x 5–84%, y 64.5–74.0%; GOLD 4px/40px brackets TL + BR (draw on 5.000–5.250); SE icon mark (white, 56px tall) at x 7.5% centred on y 69.25%; 'LAMBORGHINI HURACÁN STO' Bebas 64 WHITE cap top 66.2% at x 197px; '2023 · LAS VEGAS' Michroma 22 GOLD 0.2em cap top 70.3%; 200x6 stripe 24px after the subline. Entry translateY 30→0 + opacity 4.792–5.250.
- Ticker (4.79–9.42): bar rgba(0,0,0,.85) y 76.2–78.8%, wipes on 4.792–5.125; Michroma 22 WHITE 0.14em centred on y 77.5%; `SUPERCAR EXPERIENCE ◆ 2-HOUR FLASH SPECIAL ◆ 11AM – 1PM TODAY ◆ SUPERCAREXP.VIP ◆` ×3, `x(t) = 54 − 60·(t−4.792)` mod loop; edge alpha mask 3%/7%/93%/97%.
- 'FLASH WINDOW · TODAY' Michroma 24 GOLD 0.2em cap top 41.0%, 4.792–5.125; stripe 8px top 43.2%, 0→300px 4.875–5.375.
- Track 6px WHITE 35% at y 49.0%, x 7.5–80%, 3x24 end ticks; scaleX 0→1 4.917–5.208.
- Fill 10px GOLD 0→100% over 5.208–6.125 (easeInOutCubic) with an 18px GOLD dot on the leading edge; holds full. No digits, no countdown.
- Arrival pulse at 6.125: 2px GOLD ring on the right tick, 24→64px, opacity 0.8→0 over 0.35 s.
- '11AM' Bebas 96 WHITE x 7.5% cap top 51.2%, pop 5.000–5.250 (easeOutBack 1.2). '1PM' right-aligned to x 80%, pop 5.083–5.333; at 6.125 WHITE→GOLD over 2 frames with a 1.00→1.08→1.00 bump over 0.25 s.
- Readout exit 6.417–6.542: translateX 0→−40 + fade. Scrim, title block and ticker stay.

### B5 + B6 REQUIREMENTS 6.542–9.417, then HUD OUT
- 'REQUIREMENTS' Michroma 24 GOLD 0.2em cap top 40.0%, 6.583–6.875; stripe 8px top 42.2%, 0→300px 6.625–7.083.
- Rows (client's words, possessive added): index Michroma 26 GOLD at x 7.5% on the row baseline; label Bebas 80 WHITE at x 16%; cap tops 45.0 / 50.6 / 56.2%: `01 VALID DRIVER'S LICENSE`, `02 21+`, `03 INSURANCE`.
- Row reveal at s_i = 6.708 + 0.167·i: 4px GOLD scan line x 7.5%→80% over 0.25 s (easeInOutQuad), label clip follows it; index fades in 0.1 s; scan fades over 0.08 s; 14px GOLD pip at x 80% pops at s_i + 0.25 (easeOutBack, 0.2 s).
- All rows in by 7.292, static to 9.250.
- HUD OUT: rows clip L→R 9.250–9.417 behind a leading scan line; heading/stripe fade 9.250–9.375; title block, ticker and mid scrim fade 9.208–9.417. Frame clean from 9.417 (frame 226).

### B7 CLEAN BREATH 9.958–11.000
- No type. 3px GOLD scan line at 60% sweeps y 14%→86% over 10.792–11.000. Hard cut.

### B8 THE ASK 11.000–13.667
- No scrim (asphalt band 16–27 luma); `text-shadow: 0 2px 14px rgba(0,0,0,.35)`.
- 'BOOK BEFORE 1PM' Bebas 140 cap top 61.0%, '1PM' GOLD, masked rise 11.042–11.458.
- 'CALL (888) 678-6079' Michroma 36 0.04em cap top 68.4%, number GOLD, 11.250–11.583.
- Stripe 320x8 top 71.4%, 11.417–11.792.
- Soft lock brackets GOLD 50%, 4px/40px, fly in 11.208–11.583 (easeOutExpo); box follows the camera push (D6).
- Exit 13.250–13.417 fade + translateY 0→12. 13.417–13.667 clean footage. Hard cut to black at 13.667.

### B9 END CARD 13.667–15.500
- #000. Stacked SE logo (white) 560px wide, top 28.5%, opacity + scale 0.96→1 13.667–14.083.
- Stripe 360x8 top 48.6%, reveals outward from the centre 13.833–14.208.
- 'FLASH SPECIAL ENDS 1PM' Bebas 92 GOLD cap top 51.0%, masked rise 13.917–14.250.
- 'SUPERCAREXP.VIP' Michroma 32 0.16em cap top 57.6%; '(888) 678-6079' Michroma 32 0.08em cap top 61.0%; '@SUPERCAR_EXPERIENCE_' Michroma 24 WHITE 75% 0.12em cap top 64.4%. Each 0.292 s from 14.042 / 14.167 / 14.292.
- Holds to the last frame. No fade-out.

## 3. Safe zones (stories)
- Type spans x 7.5% to ≤ 80% (title plate edge 84%) and y 15.0%–71.8% on footage.
- Title plate bottom 74.0%, ticker bar 76.2–78.8%, clear of the reply bar (> 80%).
- Top 14% is empty apart from the transit scan lines (under 0.2 s).

## 4. Claims ledger
- '2-HOUR FLASH SPECIAL', 'ENDS 1PM TODAY', '11AM – 1PM TODAY', 'BOOK BEFORE 1PM', 'FLASH SPECIAL ENDS 1PM': the client's brief (2-hour flash special until 1 o'clock, today 2026-09-26).
- No %, no $, no prices, no specs, no countdown digits. The timeline bar fills once as a graphic.
- LAMBORGHINI / HURACÁN STO: tokens label (accent restored) and the badges visible in the footage.
- 2023 and LAS VEGAS: tokens ('2023 - Exotic - Las Vegas'); the site lists '2023 Lamborghini STO'.
- VALID DRIVER'S LICENSE / 21+ / INSURANCE: client's words, possessive only.
- supercarexp.vip, (888) 678-6079, @supercar_experience_: tokens.

## 5. Audio
Source AAC not used (unknown provenance). Original bed synthesised in numpy (seed 20260926), 48 kHz stereo:
drone 55/110 Hz; sub thumps at 0.000 and 13.667 (the end one longer with a lowpassed pink tail); pink-noise
whooshes (bandpass 0.9–3.6 kHz, 0.3 s, −12 dBFS) centred on 1.833, 3.083, 4.750, 6.542, 7.833, 9.958, 11.000;
double lock ticks at 2.250, 3.500, 11.583; fill sweep 300→900 Hz over 5.208–6.125; arrival ping at 6.125; row
ticks at 6.958, 7.125, 7.292; high-passed noise riser 9.55–11.00; CTA pop at 11.042. Two-pass loudnorm
(I −14, TP −1.0, LRA 7). The ad reads fully muted.

Optional alternate master, only if Omarie confirms the reel audio is licensed for ads: the source audio
continuous from 0.0 to 15.5 with the SFX at −6 dB relative and a 0.5 s fade-out from 15.0, same loudnorm.

## 6. Risks and checks
1. Timing: the copy says TODAY / ENDS 1PM with no date. Post by about 11:00 AM PT; expire or delete at 1 PM. Never repost on another day.
2. The IBIE trade-show banner on the LVCC facade (y 14–25%) is background only. If the client objects, darken y 12–30% with a 50% gradient in B8.
3. B2 0.7x: blend ghosted, frame-repeat fallback used (D1).
4. Á glyph verified in the render at 3.9 s.
5. Michroma licence: tokens mark it `bundled:false`; used under SE's existing licence.
6. Location: 'LAS VEGAS' comes from the car's listing. Confirm the flash special applies to the Las Vegas STO.
7. The flash rate is unnamed (no figure given). Staff must know the rate when people call or DM.
