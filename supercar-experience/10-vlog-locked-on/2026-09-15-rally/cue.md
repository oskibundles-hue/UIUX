# Cue: 2026-09-15 rally vlog, Locked-On layer

Timeline: the approved T7 reel cut (`rally_ig.mp4`), 30000/1001 fps. Frame *n* is on screen from
*n* × 1001/30000 s. The source has 3,866 frames (128.995 s); the delivery adds 48 frames of end card,
so it has **3,914 frames (130.597 s)**. All times are in seconds, and each one is derived in `story.html`
from the frame anchors in `config.json`, so moving an anchor moves the element.

## What was measured on the source, and how

| Anchor | Value | How |
|---|---|---|
| Old title "[ SUPERCAR EXPERIENCE ] The rally, dinner & the drive back." | visible **f3 to f77** (0.100 to 2.569 s), gone at f78. Ink box x 74-888, y 406-627 | bright and red pixel counts in the title zone on every frame from f0 to f120, plus full-res frames at f0, f3, f5-f8, f10, f14, f60, f70-f78 |
| SE wordmark bug | x 685-985, y **296-338** (15.4-17.6 %, not 3-5 %). It fades in f3-f6 and out f3803-f3810 | full-res frame f60, bug-region brightness f3800-f3825 |
| Pill "PARKED CARS" | box x 314-765, y 409-512. Scale/fade in on **f142**, full f143, fade out f200-f205, gone f206 | pill-colour and text pixel counts on every frame from f120 to f260, full-res crops f140-f144 and f198-f205 |
| Pill "WALKING TO DINNER" | box x 232-849, y 409-512. In **f476**, full f477, fade f533-f538, gone f539 | same, f440-f620 |
| Follow card "Omarie Young @nq.young Follow" | top-left, 34.2-37.9 s | contact sheet + caption-box scan |
| Captions | box y ~1280-1450 (66.7-75.5 %). The word being spoken sits in a white box | `lib/capscan.py`, every frame -> `lib/data/captions.json` |
| Cuts used | f134 (4.471), f467 (15.582), f2001 (66.767, briefing), f3119 (104.071, drive back), f3215 (107.274, the Strip), f3407 (113.680, parking structure), f3503 (116.884) | frame-difference scan of the whole cut |
| His closing caption ("I know, right? It's an obsession. Oh, God.") | last frame **f3809** | caption scan |
| Old end card | the bug fades f3803-f3810, the frame darkens from ~f3815, the SE logo appears **f3817**, full card by ~f3835 | per-frame luma + full-res frames f3808-f3865 |
| Route words | onset of the white highlight box, frame by frame (0.033 s), between 66.8 and 104.1 s | caption crops at every frame around each word; overview every 0.5 s (`.work/brief_*.jpg` during the build) |

Route word onsets (the tick lands on the first frame the word is highlighted):

| Waypoint (on screen) | Guide's words (burned-in caption) | Tick frame | Time |
|---|---|---|---|
| 15 NORTH | "It's in a 15 **north**." | f2114 | 70.537 |
| OFF ON FLAMINGO | "We'll be getting off on **Flamingo**." | f2161 | 72.105 |
| LEFT ON LAS VEGAS BLVD | "taking a left on Las Vegas **Boulevard**" | f2374 | 79.212 |
| BACK TO VENETIAN | "to go back to **Venetian**." | f2405 | 80.247 |
| NINTH FLOOR | "up to the ninth **floor**" | f2548 | 85.018 |

Other word onsets checked on the way: "15" f2105, "left" <= f2344, "on" f2352, "Las" f2362, "Vegas" f2368,
"ninth" f2540. Each tick is keyed to the **last word of the phrase**, so the box ticks as the waypoint is completed.

## Elements, in and out

| # | Element | In (building) | Fully up | Out starts | Gone | Notes |
|---|---|---|---|---|---|---|
| A | Hook panel: stripe, SUPERCAR EXPERIENCE · RALLY DAY, THE RALLY, / DINNER & THE DRIVE BACK, SE lockup | f0 (complete on frame 0) | 0.000 | 2.603 (f78) | 2.983 | x 54-909, y 362-751. It covers the old title box + 6 px on every frame from f0 to f77. Gold glint 0.30-0.80, white glint 0.95-1.45, stripe light sweep 1.55-2.05. Exit: the content lifts 70 px as one unit while the panel retracts up into its stripe (2.603-2.883, with a gold edge on the boundary), then the stripe wipes off to the right (2.803-2.983) |
| B1 | CH 01 / 05 PARKED CARS | 4.471 (f134, the cut) | panel 4.691, title 4.78 | 6.874 (f206) | 7.174 | x 260-819. It covers the pill from f141 to f206 (the pill is on screen f142-f205). Glint 5.19-5.65 |
| B2 | CH 02 / 05 WALKING TO DINNER | 15.582 (f467) | panel 15.802, title 16.23 | 17.985 (f539) | 18.285 | x 180-899. It covers the pill from f475 to f539 (the pill is on screen f476-f538). Glint 16.30-16.76 |
| B3 | CH 03 / 05 THE CONVOY BRIEFING | 66.767 (f2001) | panel 66.987, title 67.45 | 68.847 | 69.147 | x 198-881, y 388-537, clear of the guide's head |
| C | THE ROUTE (telemetry card) | 69.127 | 69.87 (rows dim) | 88.400 | 88.78 | x 54-493, y 222-519. Ticks and the counter (1/5 to 5/5) on the word frames f2114, f2161, f2374, f2405 and f2548 (70.537, 72.105, 79.212, 80.247, 85.018). Each tick starts on the frame boundary just before the word frame, so the frame before is clean and the word frame shows it slamming in: the gold fill at 1.45x settles to 1x (back-out, 0.10 s), a flash, the check draws (+0.03 to +0.17 s), the row wipes to full white (0.22 s), a gold glint (+0.12 to +0.54 s), the counter rolls (0.09 s) and the gold rail draws down to the ticked box. Exit: the content lifts as one unit while the panel retracts (88.40-88.66), then the stripe wipes off (88.60-88.78) |
| B4 | CH 04 / 05 THE DRIVE BACK | 104.071 (f3119) | panel 104.291, title 104.68 | 105.971 | 106.271 | x 274-806 |
| D1 | Lock: OUR RIDE / ROLLS-ROYCE (Spirit of Ecstasy) | 105.000 acquire (brackets fly in from 1.7x over 7 frames) | brackets 105.23, leader 105.20-105.46, label 105.28-105.72 | 107.034 | 107.274 (the cut, f3215) | track `soe` f3119-3214 (conf 0.90-0.98, FB error <= 1.1 %). Readable 105.72-107.03 (1.31 s). It overlaps the end of B4 by ~1.3 s, in the lower half of the frame. No captions are on screen (the last caption word is at 104.3 s) |
| D2 | Lock: LEAD CAR / LAMBORGHINI URUS | 107.374 (f3218) | brackets 107.60, leader 107.57-107.83, label 107.65-108.09 | 113.300 | 113.540 | brackets around the car's rear (tracked box x 372-692, y 912-1125, +44 px pad), label x ~198-640 above-left. Track `urus` f3215-3406 (conf 0.98-0.99, FB error <= 0.1 %). Readable 108.09-113.30 (5.2 s). Glint 108.35-108.81 |
| B5 | CH 05 / 05 LEVEL NINE | 113.680 (f3407) | panel 113.900, title 114.25 | 115.750 | 116.050 | x 339-741 |
| E | Locked-On end card | 127.127 (f3810) | opaque 127.245 (fully opaque from f3814), content 127.727 | none | 130.597 (end) | It wipes up from the bottom with a 90 px feathered edge on the first frame after his closing caption, and is fully opaque before the old card's first darkening (~f3815) and its logo (f3817). A gold light blooms down from the top edge as it lands (127.225-127.545). Content: logo wipe 127.19-127.43, stripe 127.25-127.47, tagline 127.27-127.67, CTA 127.33-127.66, phone 127.35-127.71, site 127.41-127.63, handle 127.45-127.67, locations 127.43-127.73, requirement line (RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE, y 1290) 127.47-127.69, rule 127.49-127.71, credit 127.51-127.73. Readable from 127.727 to 130.597 (2.87 s). Slow push 1.000 -> 1.018, and glints on the phone (128.23-128.78) and the tagline (129.18-129.78) |

Chapter card anatomy (B1-B5): black panel (opaque, so the pills cannot show through), 8 px gold 78 % / white
22 % stripe on top, drawn left to right in 0.22 s (expo) with a light edge, the panel unrolls down from the
stripe (masked reveal), the Michroma tag collapses its tracking, the Bebas title rises glyph by glyph through its
mask, a gold glint crosses the title ~0.7 s in. Out: the content and panel retract up into the stripe (0.24 s,
cubic) with a gold edge on the boundary, then the stripe wipes off to the right (expo).

Motion blur (`window.KT_PLAN`): 1 sample on held frames; 12-14 samples over a 200-220° shutter on the hook exit, every
chapter in and out, the lock acquires and exits; 8 on the route entry and each tick; 32 samples over 270° on the
end-card wipe; 10 on the end-card build.

## Sound (lib/mix.py)

The vlog's own audio is the main track, unedited apart from one static gain (+0.44 dB), an L/R true-peak limiter at
-1.75 dBTP (it touches 0.06 % of the samples, by at most 0.2 dB) and a 40 ms fade on its last samples. Accents, each 20 dB under the programme around it, and a further 6 dB down while a
word is highlighted in the captions:

| Accent | Time (peak / hit) | Ducked under speech |
|---|---|---|
| whoosh, CH 01 | 4.671 | yes (his "Oh. It was weird. Oh.") |
| whoosh, CH 02 | 15.782 | no |
| whoosh, CH 03 | 66.967 | yes |
| tick x5, route | 70.537, 72.105, 79.212, 80.247, 85.018 | yes, all (they land on his words by design) |
| whoosh, CH 04 | 104.271 | yes (end of "Wild Wild West out here") |
| ticks, Rolls-Royce lock | 105.000 acquire, 105.230 lock | no |
| ticks, Urus lock | 107.374 acquire, 107.604 lock | no |
| whoosh, CH 05 | 113.880 | no |
| impact, end card | 127.127 | yes (tail of "Oh, God") |

Tail: the source audio ends at 128.981 s on a non-zero sample, so it gets a 40 ms fade. A wet-only reverb of its
last 0.8 s (a synthetic hall with T60 1.6 s) carries the music's own decay on, with the end-card impact's tail
under it. Everything fades from 129.50 s and is exact zeros from 130.532 s (the last 65 ms; the AAC decode shows ~119 ms of silence).
