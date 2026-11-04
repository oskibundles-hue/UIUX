# FD x Asset Appeal: VIP card (5x7, two-sided, black tie)

Nate (Formula Dynamics) asked on Tue 3 Nov 2026 for "a VIP offer / flyer design in association with Asset Appeal",
"black tie & elegance esque", with some wordplay, about 100 printed and ready early Thursday (5 Nov). The offers
are confirmed on Wednesday, so this build ships as a **DRAFT** until they're in.

Look: new, built around Nate's brief (Omarie's pick). The front is a formal invitation, the back is a black-tie
dinner menu of offers. FD brand: black ground, white, FD red used sparingly, Bebas Neue headlines, official FD vector
logos, five-segment accent stripe. Cormorant Garamond italic is the black-tie accent for the small connecting lines.

Wordplay: back **"A different asset class."** (Asset Appeal's name, with cars as assets). The front is one of four
headlines below. There is no actual dress code (Omarie, 4 Nov), so no front says there is; the black tie is only the
feel. ("PRECISION has a DRESS CODE." was dropped for that reason.)

Four fronts for Nate to pick from, numbered as on `out/FD-x-AssetAppeal_VIP-card_5x7_front-options.png`; the back
is the same on all four. Each has its own copy file; build one with `CARD=<file> node build.js`, and its files are
named `FD-x-AssetAppeal_VIP-card_5x7_<variant>_*`.

1. **"TIME & TORQUE."**: watches (Asset Appeal) and torque (FD). `card_time-and-torque.json`
2. **"TAILORED for SPEED."**: black-tie tailoring and FD's fitment and tuning. `card.json` (the default build)
3. **"CARATS & HORSEPOWER."**: Asset Appeal's jewellery and FD's tuning. `card_carats-and-horsepower.json`
4. **"BLACK TIE at FULL THROTTLE."**: the black-tie feel with the throttle open. `card_black-tie-full-throttle.json`

Four backs, lettered as on `out/FD-x-AssetAppeal_VIP-card_5x7_back-options.png`; any front goes with any back. The
back option files carry the TIME & TORQUE front only so their previews match: to use one, copy its `back` block into
the chosen front's copy file.

- **A, "VIP PRIVILEGES / A different asset class."**: the dinner-menu layout with roman numerals. Already in every
  front file.
- **B, "APPRECIATING ASSETS / Some assets are meant to be driven."**: numerals in a column, offers left-aligned
  (`layout: rows`). `card_back-appreciating-assets.json`
- **C, "THE FINER THINGS / Finely tuned."**: no numerals, small red diamonds between the offers, and a "Reserved for
  ____" line to write a guest's name on (`layout: certificate`; delete `reserved_line` to drop the line).
  `card_back-finer-things.json`
- **D, "POLE POSITION / Front of the grid, reserved for you."**: P1, P2, P3 in FD red (`layout: rows`,
  `numbering: pole`). `card_back-pole-position.json`

## Finish it on Wednesday (about 2 minutes)

1. Put the confirmed offers and the end date into the copy file of the front Nate picked
   (`back.offers[].title / detail`, `back.terms`).
   Titles are short Bebas lines, e.g. `PAINT PROTECTION FILM`; details are one italic line.
2. Asset Appeal's emblem (green and gold, front) is cut from their Instagram avatar for now: fine at its printed
   0.66 in, but soft. If Nate can get their original logo file (SVG/PDF, or PNG 1000 px+), save it in `assets/`
   and point `partner.logo` at it (`partner.logo_h` sets its printed height in inches).
3. Run `CARD=<that file> NODE_PATH=$(npm root -g) node build.js`. While any `[bracket]` is left, the placeholders print in red and
   the print files carry a red "DRAFT · NOT FOR PRINT" stamp. With none left, it prints `FINAL` and drops the stamp
   and the `_DRAFT` from the file names. It also prints `overflow: none` when every line fits; if a long offer
   overflows, shorten it. (`CARD=` and `OUT=` point it at another copy file or output folder.)
4. Send `out/FD-x-AssetAppeal_VIP-card_5x7_<variant>_print-bleed.pdf` to the printer.

## Print spec (for the shop)

| | |
|---|---|
| Finished size | 5 x 7 in, portrait |
| File | PDF, 2 pages (1 front, 2 back), 5.25 x 7.25 in = 0.125 in bleed all round, TrimBox set to the 5 x 7 cut, fonts embedded, vector logos |
| Safe zone | all copy is 0.6 in or more inside the trim; the double-rule frame (0.75 pt) sits 0.34 and 0.40 in inside the trim. Ask for an accurate cut, since a frame shows drift |
| Sides | double-sided, flip on the long edge (head to head) |
| Quantity | about 100 |
| Stock | 16 pt matte, or soft-touch laminate for the black-tie feel. Avoid gloss, which shows fingerprints on black |
| Black | the file's black is RGB #000000. Ask for it to print as **rich black** (e.g. C60 M40 Y40 K100), not black ink only, or the large black areas print greyish |

## Files

- `card.json` and `card_<variant>.json`: all the words on the card, one file per front option. `line1_amp` sets
  the italic ampersand, `line2` the small italic middle line, `max_pt` the largest headline size; the build shrinks
  the headline until it fits the width and leaves air in the column
- `out/FD-x-AssetAppeal_VIP-card_5x7_front-options.png` and `..._back-options.png`: the four fronts (1-4) and the
  four backs (A-D), each on one sheet, for picking
- `build.js`: layout and renderer (Playwright/Chromium). Writes `out/`: the print PDF, 300 dpi PNGs of each side
  (with bleed) and a trimmed side-by-side preview
- `assets/`: FD vector logos from `formula-dynamics/02-logos` on
  `claude/formula-dynamics-assets-bnlnkm` (the stripe is drawn to BRAND-SPEC proportions); Bebas Neue (OFL);
  Cormorant Garamond (OFL, via @fontsource)
