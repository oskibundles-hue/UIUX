# FD x Asset Appeal: VIP card (5x7, two-sided, black tie)

Nate (Formula Dynamics) asked on Tue 3 Nov 2026 for "a VIP offer / flyer design in association with Asset Appeal",
"black tie & elegance esque", with some wordplay, about 100 printed and ready early Thursday (5 Nov). The offers
are confirmed on Wednesday, so this build ships as a **DRAFT** until they're in.

Look: new, built around Nate's brief (Omarie's pick). The front is a formal invitation, the back is a black-tie
dinner menu of offers. FD brand: black ground, white, FD red used sparingly, Bebas Neue headlines, official FD vector
logos, five-segment accent stripe. Cormorant Garamond italic is the black-tie accent for the small connecting lines.

Wordplay: front **"PRECISION has a DRESS CODE."** (FD's Precision value plus black tie). Back **"A different asset
class."** (Asset Appeal's name, with cars as assets).

Two fronts for Nate to pick from; the back is the same on both:

- **A, "PRECISION has a DRESS CODE."**: `card.json`, files named `FD-x-AssetAppeal_VIP-card_5x7_*`.
- **B, "TIME & TORQUE."**: watches (Asset Appeal) and torque (FD). `card_time-and-torque.json`, files named
  `FD-x-AssetAppeal_VIP-card_5x7_time-and-torque_*`. Build it with `CARD=card_time-and-torque.json`.

## Finish it on Wednesday (about 2 minutes)

1. Put the confirmed offers and the end date into `card.json` (`back.offers[].title / detail`, `back.terms`).
   If Nate picks version B, make the same edits in `card_time-and-torque.json` instead.
   Titles are short Bebas lines, e.g. `PAINT PROTECTION FILM`; details are one italic line.
2. Asset Appeal's emblem (green and gold, front) is cut from their Instagram avatar for now: fine at its printed
   0.66 in, but soft. If Nate can get their original logo file (SVG/PDF, or PNG 1000 px+), save it in `assets/`
   and point `partner.logo` at it (`partner.logo_h` sets its printed height in inches).
3. Run `NODE_PATH=$(npm root -g) node build.js`. While any `[bracket]` is left, the placeholders print in red and
   the print files carry a red "DRAFT · NOT FOR PRINT" stamp. With none left, it prints `FINAL` and drops the stamp
   and the `_DRAFT` from the file names. It also prints `overflow: none` when every line fits; if a long offer
   overflows, shorten it. (`CARD=` and `OUT=` point it at another copy file or output folder.)
4. Send `out/FD-x-AssetAppeal_VIP-card_5x7_print-bleed.pdf` (or `..._time-and-torque_print-bleed.pdf` for B) to
   the printer.

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

- `card.json`: all the words on the card (version A)
- `card_time-and-torque.json`: the same, with the TIME & TORQUE front (version B). `line1_amp` sets the italic
  ampersand, `max_pt` the largest headline size; the build shrinks the headline until it fits the width and leaves
  air in the column
- `build.js`: layout and renderer (Playwright/Chromium). Writes `out/`: the print PDF, 300 dpi PNGs of each side
  (with bleed) and a trimmed side-by-side preview
- `assets/`: FD vector logos from `formula-dynamics/02-logos` on
  `claude/formula-dynamics-assets-bnlnkm` (the stripe is drawn to BRAND-SPEC proportions); Bebas Neue (OFL);
  Cormorant Garamond (OFL, via @fontsource)
