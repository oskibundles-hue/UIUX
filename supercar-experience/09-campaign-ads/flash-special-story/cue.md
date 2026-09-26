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
| D10 | B2 0.7x frame-repeat (D1) over src 56–76 | B2 = the whole crest take at **1.0x** (src 55–77, 23 frames, 1.833–2.792), **tone-locked** in 16-bit: each frame's luma is quantile-matched to the take's mean luma distribution and applied as an RGB gain, then a luma-neutral per-channel balance | Round-1 review: the 4-3-3 repeat cadence juddered and the source's baked-in light strobe (luma 50↔160 every 2–3 frames) gave ~3 flashes/s. The crest take is only 23 frames long, so 1.0x is the whole take. Final B2 luma 66.9–71.8, largest frame step 2.0 (was 30–107). Per-channel matching was tried first and lifted the shield black to navy, hence luma-only. |
| D11 | B8 src 498–561 as graded | B8 = src 498–567 (70 frames, 10.125–13.042), **per-channel quantile-matched** in 16-bit to the blue-white state (src 510–530) | The reel's grade steps white balance inside the locked-off take (src 507 and 547: facade, car and asphalt all shift, so it is a whole-frame grade change). Facade band now holds (88,97,107)→(91,99,110), max frame step 2.5 (was 8.5 in the source). |
| D12 | §6: darken y 12–30% only if the client objects | Applied now in B8: full-width graduated defocus + ×0.45 darken above y 23% (eases out by 27.5%, clear of the LAS VEGAS lettering); the small IBIE door sign and the doorway poster face softened in place | Round-1 review: IBIE / ABA / BEMA marks and a readable face sat behind the CTA. Positions measured on plate frames 243/312 by template match (background drift +1.1% x, −0.6% y: the camera dollies toward the car). A boxed blur was tried first and read as a censor patch. |
| D13 | Timeline B4 → B5 → B6 (reqs) → B7 (breath) → B8 | B4 → B5+B7 (reqs) → **B6 clean hero** → B8; B4 = src 279–311 ends exactly on the fill arrival | Round-1 review: the hero head-on shot sat under the requirements (clean 0.58 s) and the 1PM payoff landed on a near-black frame. Now the requirements live on the side profile + wide roll-by (one continuous source range 323–381, in-source cut on 7.250), HUD is out at 8.292 and B6 runs clean 1.83 s with its push; the 1PM gold beat lands on the first frames of the bright B5 side profile. Ask starts 10.167, 1.875 s after HUD out (≥ 1.6). |
| D14 | B8 soft brackets eased to a fixed end box | Right edge follows the measured nose (+2%): 83.5% @10.125 → 94.6% @12.875 (table `NOSE` in story.html); brackets release 12.208–12.375 while the text holds | New source range; keeps the box inside x 95.5%. |
| D15 | Mid scrim 0.80 throughout the HUD | 0.62 over B4, 0.80 from the B5 cut | The B4 plate mid band is 68–122 luma; at 0.80 it read as black. The readout (Bebas 96 + gold bar) holds at 0.62. |
| D16 | Copy | 'ENDS TODAY · 1PM PT' (hook), 'RENTAL FLASH WINDOW · TODAY', ticker '2-HOUR RENTAL FLASH SPECIAL ◆ 11AM – 1PM PT TODAY', ask 'BOOK BEFORE 1PM PT' (Bebas 120) / 'CALL FOR THE FLASH RATE' / '(888) 678-6079', end card 'RENTAL FLASH SPECIAL' / 'ENDS TODAY · 1PM PT' | Round-1 review: nothing said rental, and 1PM had no time zone (SE also lists the STO in Boise, on Mountain time). PT is the brief's zone and the car's listing is Las Vegas. All lines 5/5 CLEAN on SlopMonster. '21+' left exactly as the client wrote it (see §6). |
| D17 | End card: lines staggered 0.125 s from 14.042, handle 24 px at 75% | End card 13.042–15.500 (2.46 s); contacts in together (0.042 s stagger) from 13.375; handle Michroma 26, 100% white | Round-1 review: handle held 1.00 s, phone 1.17 s. Now every contact line is complete by 13.625 and held ≥ 1.88 s (measured on the MP4). |
| D18 | (build bug) | Overlay PNGs normalised to RGBA; `verify_sync` compares 13 MP4 frames to plate+overlay | Chromium writes a fully opaque page (the end card) as RGB PNG; the format change re-initialised ffmpeg's filter graph and slipped the end card 7 frames late (in round 0 too). |
| D19 | Sound bed: sub drone + sub hits | Re-voiced for phone speakers: A-minor pad 220–880 Hz with harmonics, impacts = sub + saturated 240→70 Hz body + 1.5–8 kHz crack + metallic ring, 0.7–6 kHz whooshes, harmonic fill sweep, bell ping | Round-1 review: bed was 100% below 150 Hz. Now 86% of the pad is in 150–500 Hz; through a 200 Hz high-pass (phone sim) momentary loudness never drops below −24 LUFS (median −16.7); round 0 was below −30 for 47% of the runtime. Loudnorm TP −2.0 → −14.2 LUFS, −1.4 dBTP after AAC. |

---

1080x1920, **24 fps**, **372 frames = 15.500 s**, H.264 yuv420p. Treatment: house `hud` (approved), in motion. Round-1 fixes: D10–D19.

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
| B2 BRAND LOCK | 1.833 | 2.792 | 44–66 | 55–77 | 1.0, tone-locked (D10) | LAMBORGHINI crest close-up on lime body |
| B3 MODEL LOCK | 2.792 | 4.458 | 67–106 | 148–179 | 0.8 (blend) | 'STO' lettering on the carbon deck |
| B4 FLASH WINDOW | 4.458 | 5.833 | 107–139 | 279–311 | 1.0 | front-on rolling past the city, headlights (fill lands on the cut) |
| B5+B7 REQUIREMENTS | 5.833 | 8.292 | 140–198 | 323–381 | 1.0 | side profile, yellow caliper → (in-source cut at 7.250) wide roll-by past a lit canopy |
| B6 CLEAN HERO | 8.292 | 10.125 | 199–242 | 189–232 | 1.0 | front-on under the white canopy; push 1.00→1.03; no type |
| B8 THE ASK | 10.125 | 13.042 | 243–312 | 498–567 | 1.0, colour-locked + facade cleanup (D11, D12) | parked at the Las Vegas Convention Center, in-camera dolly |
| B9 END CARD | 13.042 | 15.500 | 313–371 | none | none | solid #000 |

Grade: `eq=contrast=1.04:saturation=0.96:gamma=1.0,vignette=angle=PI/5` only (the source is already a finished reel grade). No LUT, no hue or saturation push that could clip the lime paint.

Encode: `libx264 -preset slow -crf 17 -profile:v high`, BT.709 limited range yuv420p, AAC 192k 48 kHz stereo, `+faststart`.

Verify stills: t = 0.000, 1.000, 2.500, 3.600, 5.500, 5.958, 7.100, 8.000, 9.400, 11.000, 12.500, 14.600 (Á renders; every line ≤ x 80%; nothing in the top 14% or bottom 20% except the transit scan lines). `verify_sync` checks MP4 frames 0, 43, 44, 106, 140, 198, 199, 242, 243, 312, 313, 330, 371 against plate+overlay.

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
- The HUD is fully clear at 8.292 (frame 199) and the ask starts at 10.167 (1.875 s ≥ 1.6).
- The CTA is gone at 12.750 (frame 306) and the end card hard-cuts at 13.042 (0.29 s clean footage).
- Scrim or plate wherever the shot changes under type (B4→B5, B5→B7).
- No corner logo bug (top band swings 20→148): the SE mark lives inside the title block.
- The stripe is horizontal everywhere.

## 2. Beat-by-beat graphics

**Round 1 timing (supersedes the times below where they differ).** B1 unchanged. B2 runs 1.833–2.792: brackets contract
1.875–2.208, tick 2.208–2.333, release 2.708–2.792; tag plate 1.875–2.167, stripe 1.958–2.250, BRAND 1.917–2.125,
LAMBORGHINI rise 1.875–2.208. B3, the HUD entry, the B4 readout and the requirements build keep the motion below
shifted 7 frames earlier (story.html `u = t + 7/24`): B4 fill 4.917–5.833 and the 1PM gold/pulse at 5.833 (the B5 cut);
readout exit 6.125–6.250; REQUIREMENTS 6.292, rows 6.417 / 6.583 / 6.750. HUD OUT in real time: title/ticker/scrim fade
8.083–8.292, rows clip 8.125–8.292. B6 8.292–10.125 carries no type; scan line 9.917–10.125. The ask keeps its entry
motion shifted 21 frames (`v = t + 21/24`): headline rise 10.167–10.583, 'CALL FOR THE FLASH RATE' 10.375–10.708,
phone 10.458–10.792, stripe 10.542–10.917; brackets fly in 10.333–10.708, follow the nose, release 12.208–12.375;
text exit 12.583–12.750. End card from 13.042: logo 13.042–13.458, stripe 13.208–13.583, 'RENTAL FLASH SPECIAL'
13.250–13.500, 'ENDS TODAY · 1PM PT' rise 13.292–13.625, contacts 13.375 / 13.417 / 13.458 (+0.25 s each). Copy per D16.

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
- Type spans x 7.5% to ≤ 80% (title plate edge 84%) and y 15.0%–73.0% on footage (measured overlay ink y 14.4–79.9% incl. brackets and ticker bar; no out-of-band frames).
- Title plate bottom 74.0%, ticker bar 76.2–78.8%, clear of the reply bar (> 80%).
- Top 14% is empty apart from the transit scan lines (under 0.2 s).

## 4. Claims ledger
- '2-HOUR FLASH SPECIAL', 'ENDS TODAY · 1PM PT', '11AM – 1PM PT TODAY', 'BOOK BEFORE 1PM PT', 'ENDS TODAY · 1PM PT': the client's brief (2-hour flash special until 1 o'clock, today 2026-09-26); PT = the brief's time zone.
- 'RENTAL' / 'RENTAL FLASH SPECIAL' / 'RENTAL FLASH WINDOW': the client's brief ('on our rental car').
- 'CALL FOR THE FLASH RATE': a CTA, names no figure.
- No %, no $, no prices, no specs, no countdown digits. The timeline bar fills once as a graphic.
- LAMBORGHINI / HURACÁN STO: tokens label (accent restored) and the badges visible in the footage.
- 2023 and LAS VEGAS: tokens ('2023 - Exotic - Las Vegas'); the site lists '2023 Lamborghini STO'.
- VALID DRIVER'S LICENSE / 21+ / INSURANCE: client's words, possessive only.
- supercarexp.vip, (888) 678-6079, @supercar_experience_: tokens.

## 5. Audio
Source AAC not used (unknown provenance). Original bed synthesised in numpy (seed 20260926), 48 kHz stereo, voiced for
phone speakers (D19): A-minor pad (55–880 Hz, weight on 220–660, slow tremolo, detuned L/R) + 3–9 kHz air, fading
14.7–15.5; impacts at 0.000 and 13.042 (sub + saturated 240→70 Hz body + 1.5–8 kHz crack + 523/1244/2093/3322 Hz ring
+ 200–1200 Hz boom); whooshes into each cut (1.833, 2.792, 4.458, 5.833, 7.250, 8.292, 10.125; pink noise 0.7–6 kHz
+ shimmer, panned); double lock ticks at 2.208, 3.208, 10.708; row ticks at 6.667, 6.833, 7.000; harmonic fill sweep
220→880 Hz over 4.917–5.833 and a bell at 5.833; riser 8.90–10.125 (band noise + rising tone); CTA pop at 10.167.
tanh saturation (drive 1.6), two-pass linear loudnorm (I −14, TP −2.0, LRA 7). Final: −14.2 LUFS, −1.4 dBTP.
Phone check: through a 200 Hz high-pass the momentary loudness stays between −19.8 (p10) and −14.4 (p90) LUFS.
The ad reads fully muted.

Optional alternate master, only if Omarie confirms the reel audio is licensed for ads: the source audio
continuous from 0.0 to 15.5 with the SFX at −6 dB relative and a 0.5 s fade-out from 15.0, same loudnorm.

## 6. Risks and checks
1. Timing: the copy says TODAY / ENDS 1PM PT with no date. Post by about 11:00 AM PT; expire or delete at 1 PM PT. Never repost on another day.
2. Third-party marks on the LVCC facade (IBIE banner, sponsor logos, door sign, poster face) are knocked back in B8 (D12). The generic 'WELCOME / REGISTRATION & EXHIBITS' venue signage stays.
3. B2 is the whole crest take at 1.0x, tone-locked (D10). The bull's specular glint still varies frame to frame, which reads as light play, not flicker.
4. Á glyph verified in the render at 3.6 s and in the title block.
5. Michroma licence: tokens mark it `bundled:false`; used under SE's existing licence.
6. **Confirm with Omarie: location.** 'LAS VEGAS' comes from the car's listing, and 'PT' from the brief's time zone. SE also lists the 2023 STO in Scottsdale and Boise (Boise is on Mountain time). If the special covers every location, drop 'LAS VEGAS' from the title block and restate the time per market.
7. **Confirm with Omarie: 21+.** The site says 'Renter Must Be 25+ (Ages 21–24 With $299 Underage Fee)'. '21+' is the client's own wording and stays as written. If he wants it, a small line such as '21–24 UNDERAGE FEE APPLIES' (quoted from the site) fits under row 02. Either way, staff must mention the fee on calls.
8. The flash rate is unnamed (no figure given). Staff must know the rate when people call or DM ('CALL FOR THE FLASH RATE').
