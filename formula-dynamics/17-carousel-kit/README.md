# `17-carousel-kit`: FD Instagram carousels, from a plan to a delivered set

Approved by Omarie on 2026-11-20, after the FD-BFCM-75 run (75 Black Friday carousels, Nov 20 to Dec 4, 225 slides):
"This was a axing good job who made this", then "Great save the system". That campaign is the worked example and lives
in `../30-bfcm-75/`. Its delivery went to the shop's Google Drive sale folder; a private review page was published as a
claude.ai artifact.

The kit makes a campaign folder that holds everything one run needs: the slide system, the tools, the brief, the
ledger. Each campaign gets its own copy of the tools, so a campaign keeps working after the kit changes.

## What a carousel is here
- 1 to 20 slides (3 by default), each an HTML page at **1080 x 1350**, rendered in the installed Chrome to an sRGB JPEG
  (q95, no chroma subsampling), plus a `Caption.txt`.
- The look: FD black ground, white type, FD red `#FE0F13` as the only accent; Bebas Neue for display, Barlow Condensed
  for body, IBM Plex Mono for figures and labels. All in `template/source/styles.css`, with the fonts and white FD
  logos copied into each campaign's `assets/`.
- A running header on every slide: a short section label on the left, the counter `01 / 03` on the right.
- One idea per carousel. Slide 1 stops the scroll, the middle proves or teaches, the last slide turns it into an action.
- Default day: five posts at 9 AM (product spotlight), 11 AM (sale guide), 1 PM (a real FD car with a part that fits it),
  4 PM (education) and 7 PM (sale reminder), Pacific. `--slots` changes that.

## Rules that came with it
The full list, with the reasons, is in the brief every campaign gets (`template/BRIEF.md`). The ones that bite:
- **Real FD photos only**, from the Google Drive master media folder or the Dropbox `Portfolio/` originals. No stock, no
  AI pictures, no listing image with "+HP" graphics on it. Never overwrite a photo you did not make.
- **Verify before naming.** The car from its folder name and the body in frame; a part brand only if the listing says
  it or it can be read in the frame. Can't tell what's on the car? Show the car and word the part as available for
  that model, never as work done on it. Never print a customer name.
- **Prices match the store listing** saved that day, with the variant or stage named and a fine-print source line. A
  listing with no compare-at price isn't on sale. Discount tiers come only from the shop's public sale email or its own
  post: nothing else counts.
- **Never print** a discount code meant for a private list, horsepower, torque, "faster", a customer name, or a phone
  number no source file confirms.
- **One FD mark per slide**: the corner icon or the store wordmark, never both. Store CTA `SHOP NOW ·
  FORMULADYNAMICS.COM`; the shop's `BOOK YOUR BUILD · formuladynamicsperformance.com · @formuladynamicsperformance` only
  for install or shop work.
- **Margins** 72 px at the sides, 64 px top and bottom. Body text 30 px and up, fine print 21 px and up.
- **Blur every readable plate**, background cars included, then look at the blurred crop.
- **Look at it phone size** (390 px wide) before it ships. The checker measures; it can't judge.
- Don't publish, post, email or contact the shop. Ask before any push.

## Running it
Python 3.10+ with Playwright and Pillow, run through `uv` (the system Python is too old and has no Pillow). Playwright
drives the installed Google Chrome, so there is no browser download. Every command runs from inside the campaign
folder. Paste this line once into each new Terminal tab; after that, `RUN` in the steps below means "run with uv":

    RUN() { ~/.local/bin/uv run -q --with playwright --with pillow python "$@"; }

1. **Make the campaign** (from the repo root; standard library only, so plain `python3` works):

       python3 formula-dynamics/17-carousel-kit/new_campaign.py formula-dynamics/31-spring-sale \
           --code FD-SPRING-30 --title "Spring service sale" --start 2027-03-01 --end 2027-03-06 \
           --delivery "~/Library/CloudStorage/GoogleDrive-*/My Drive/<sale folder>/<delivery folder>"

   It refuses a folder that already exists. `--never "CODE1,CODE2"` adds words the checker must block (a private sale
   code, say). Leave `--delivery` out to deliver into the campaign's own `out/delivery/`.
2. **Fill the campaign's facts.** Every `[[...]]` in `BRIEF.md` (the weak version to beat, the discount tiers and where
   they were read, the lanes for topics that repeat across days). In `campaign.json`: the `plan` (one topic per post per
   day; `"-"` drops a post that day), `notes` (a line per day for the review page, such as "Black Friday"), `drive_link`
   once the folder is shared, and the `page` words (`{carousels}`, `{slides}` and `{days}` in them become the real
   counts at build time).
3. **Save the store listings** on the day you build (prices are checked against these). Posts for a later date are
   still built from today's listings; if a price may change before the post goes out, save them again the day before
   and re-run the checker on that carousel:

       mkdir -p ref/store; for n in 1 2 3 4 5 6; do curl -s "https://formuladynamics.com/products.json?limit=250&page=$n" > ref/store/p$n.json; done

4. **Build a carousel.** Copy `source/_starter/1_products/` to `source/<date>/<slot>/`, or start from a slide in
   [LAYOUTS.md](LAYOUTS.md) that fits the idea. Photos go in `assets/photos/` as `<subject>_<view>.jpg` (about 2160 wide,
   JPEG q92). Plates: `RUN tools/plate_blur.py IN OUT x0,y0,x1,y1`. Write `Caption.txt` (40 to 90 words) and the
   ledger row `ledger/rows/<date>_<slot>.csv` (header in `ledger/HEADER.csv`): how the car, the part and every
   price were checked. Delivery refuses a carousel with no row.
5. **Check it:** `RUN tools/lint.py source/<date>/<slot>`. Fix every FAIL. Read every warn.
6. **Look at it:** `RUN tools/render.py out/check/<date>_<slot> source/<date>/<slot>/slide-*.html`, then
   `RUN tools/phone_sheet.py out/check/<date>_<slot>` and open `out/check/<date>_<slot>/_phone/sheet.png`. Is the ring on
   the part? Does the type read over the photo? Would you stop scrolling?
7. **Deliver it:** `RUN tools/deliver.py <date> <slot>`. It stops on a missing ledger row or a lint FAIL, renders into
   `<delivery>/exports/<date>/<slot>/`, copies the editable source across and rebuilds the merged ledger and
   `PROGRESS.md`.
8. **When the set is done:**
   - `RUN tools/deliver_all.py --verify-only` checks every export against its source (slide count, 1080 x 1350, the
     caption, no slide repeated between carousels). Drop `--verify-only` to re-render everything first.
   - `RUN tools/finish.py` writes the contact sheet, a gallery page and the review PDF into the delivery folder.
   - `RUN tools/build_page.py out/page checks.txt` builds the review page. `checks.txt` (in the campaign folder) is one
     paragraph saying what was really checked. Publish `out/page` (index.html, fd-icon.png and every `s/*.jpg`) with the
     artifacts `publish_files` tool; it starts private.
   - `RUN tools/page_pdf.py out/page` saves that page as two PDFs in the delivery folder, so someone without the
     artifact (the shop) sees the same page; Drive shows an HTML file as code. `00 <code> review page.pdf` is the laptop
     version, one day per page. `00 <code> review page - phone.pdf` is 430 px wide with one carousel per page, each
     naming its day. Every page is as tall as what is on it, and the covers and "All covers" links work inside the
     PDF. It stops if a picture fails to load. `--out FILE` writes somewhere else (no `campaign.json` needed).

Many builders at once? Give each one a day or a slot and its own `ledger/rows/` files: nothing else is shared, and
`progress.py` merges the rows.

## The checker (`tools/lint.py`)
It loads each slide in Chrome at 1080 x 1350 and measures the glyphs, not the text boxes, so a big Bebas headline is
judged by where its ink sits.
- **FAIL** (blocks delivery): ink outside the margins; text under 21 px; text cut off by its box; two text elements whose
  ink overlaps; a broken image, the kit's placeholder photo or `[[...]]` left in; more than one FD mark; a font that
  didn't load; a counter that doesn't match the slide's place; a `never_print` word on a slide or in the caption; no
  `Caption.txt`, or one still holding `[[...]]`.
- **warn** (a person looks): no FD mark on a slide; a photo blown up past 1.25x; a caption outside 40 to 90 words or
  with hashtags or emoji; a `$` figure that is no listing's price, was-price or saving (a cart total is fine, but add it
  up by hand).
- **Allowed past the margin on purpose:** anything inside `.pin` or marked `data-free` (a marker sitting on the part in
  the photo), and a one- or two-character graphic glyph 200 px and up (a giant ÷ or %).
- Calibration: on the 75 approved BFCM carousels it found exactly 2 real slips (ink 7 and 9 px into the side margin)
  and nothing false. Both were fixed.
- It can't see a busy background behind type, a ring that misses the part, a weak idea, or a claim the photo doesn't
  support. That is what step 6 is for.

## `campaign.json`
| field | what it is |
|---|---|
| `code`, `title` | short code used in file names (`FD-BFCM-75`) and the campaign's plain name |
| `start`, `end`, `slides` | first and last post dates (YYYY-MM-DD) and slides per carousel |
| `slots` | the posts each day: `id` (the folder name), `role`, `time` (Pacific) |
| `plan` | per date, one topic per slot; `""` is unplanned, `"-"` means no post that day |
| `notes` | per date, a short line shown on the review page (a sale day, the last day) |
| `never_print` | words the checker fails on, slides and captions |
| `delivery_dir` | where finished files go. One `*` may stand for the account part of a Drive path, so no address is written into the repo; it must match exactly one folder |
| `drive_link` | the shared link to the delivery folder, for the review page |
| `store_json` | where the saved listings are (default `ref/store/*.json`) |
| `date_label`, `price_note` | the review PDF's subtitle and its price line |
| `open_notes` | lines listed at the end of `PROGRESS.md` for whoever picks it up next |
| `page` | the review page's `title`, `h1`, `lede`, `hot_figure` (`["20%", "top tier, through Dec 4"]`) and `warning` |

`--to DIR` on deliver, deliver_all, progress, finish and build_page overrides `delivery_dir` for one run (a test, say).

## Changing the kit
Fix tools here, in `tools/`, then copy the fixed file into any campaign still running. Never fix a tool only inside a
campaign: the next campaign would get the old one. Photos, `ref/` and `out/` are kept out of git by each campaign's
`.gitignore`; the exports live in the delivery folder.
