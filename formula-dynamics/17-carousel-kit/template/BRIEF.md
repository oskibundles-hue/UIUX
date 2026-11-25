# {{CODE}} build brief (for the lead and any builder agent)

Formula Dynamics (FD, a luxury car shop with a parts store at formuladynamics.com): {{TITLE}}, {{START}} to {{END}}.
{{COUNT}} Instagram carousels, {{SLIDES}} slides each, 1080x1350 sRGB. Work folder: this folder.
Made from the FD carousel kit (`formula-dynamics/17-carousel-kit/`). The kit's README has the steps; this file has the
campaign's own facts. Fill the three double-bracket placeholders below before the first build.

## The bar
Each carousel is built around one specific thing an owner can **see on a real FD car or part** or **learn** before buying.
A top agency would ship: a real FD photo cropped with intent, one clear idea per carousel, a slide 1 that stops the
scroll, a middle that proves or teaches, a last slide that turns it into an action. Every figure true to the store listing.
The weak version to beat: generic headlines over random car shots, the same layout every post, prices with no stage or
qualifier, a part named that the photo doesn't show. A new headline, colour or crop is NOT a new concept.
[[Name this campaign's own weak version, if there is one (an earlier draft, a competitor's post), and why it is weak.]]

## The posts each day
{{SLOT_TABLE}}
Two sale posts on the same day must give different reasons to buy. Planned topics per day are in campaign.json `plan`
(they show in PROGRESS.md). Use the planned topic unless no real photo or verified listing supports it; then swap to a
nearby topic and say why in the ledger `notes`.

## Discounts and dates (the only source)
[[Where the discount tiers and dates come from: the public sale email, the shop's own post, a signed brief. Paste the
tiers here, one line each, and say which file or link they were read from. Nothing else counts: not a draft, not a
guess, not an earlier campaign.]]

## Hard rules
1. **Real FD photos only.** Sources: the Google Drive master media folder (`~/Library/CloudStorage/GoogleDrive-*/`,
   shortcut "MASTER MEDIA & CONTENT FOLDER": FDP CARS = customer cars by folder "YYYY.MM MAKE | model | work | customer";
   FDP PRODUCTS and FDP CAMPAIGNS = part and vendor shots; FDP BUILDING = the shop) and the Dropbox `Portfolio/`
   originals. Search the UIUX repo's `formula-dynamics/99-toolkit/video-index/` first (`fd_index.py search ... --colour`) to find clips
   without downloading. Videos are mostly 4K vertical: pick the sharpest frame (ffmpeg, test a few offsets) and save a
   2160-wide JPEG q92 as `assets/photos/<subject>_<view>.jpg`. Never overwrite a photo you did not make; check the
   name is free first. A store listing image is allowed for a product only if it carries no "+HP/+TQ" or performance
   graphics.
2. **Verify before naming.** Car model from the folder name AND the body in frame. A part brand only if the listing
   says it or it is legible in the frame. If the part on the car can't be identified, don't claim it was installed:
   show the car and a verified catalog feature, worded as available for that model, never as work done on that car.
   Photo tag pattern: "Shown: <car> at the FD shop". **Never print a customer name** (folder names carry them; the
   ledger writes `<customer>` instead).
3. **Prices.** Every price on a slide matches the store listing saved in `ref/store/` (Shopify products.json:
   `curl -s 'https://formuladynamics.com/products.json?limit=250&page=N' > ref/store/pN.json`; `price` = now,
   `compare_at_price` = was). Find a listing by its title, not its body text. Name the variant or stage when variants
   differ in price. Print a fine-print source line with any price. A listing with no compare-at price is not on sale:
   don't call it that.
4. **Never print** a discount code, horsepower, torque, "faster" or any performance claim (listing marketing copy about
   gains is not usable), a customer name, a phone number no source file confirms, or anything not checked. The words
   the checker blocks are in campaign.json `never_print`.
5. **One FD mark per slide**: `assets/logos/fd-icon-white.png` (corner icon) OR the store wordmark
   `assets/logos/store-wordmark-white.png`, never both. Store CTA: `SHOP NOW · FORMULADYNAMICS.COM`. The shop's CTA
   (only for install or shop work): `BOOK YOUR BUILD · formuladynamicsperformance.com · @formuladynamicsperformance`.
6. **Plates.** Blur every readable plate with `tools/plate_blur.py IN OUT x0,y0,x1,y1` on the photo asset, then crop
   the blurred area and look at it to confirm it's unreadable. Background cars count.
7. **Phone check.** `tools/lint.py` checks margins (72 px sides, 64 px top and bottom), type sizes (body 30 px and up,
   fine print 21 px and up), clipping, overlaps, marks, counters and blocked words. It cannot judge a busy background,
   whether a ring sits on the part, or whether the slide reads well: look at the phone sheet for those.
8. Don't publish, post, email or contact the shop. Ask before any push.

## How to build
- Start a carousel from `source/_starter/1_products/` (copy the folder to `source/<date>/<slot>/`) or from a slide in
  the kit's layout library (`17-carousel-kit/LAYOUTS.md`) that fits the idea.
- Shared CSS is `source/styles.css` (fonts, colours, `.run` header with counter, `.kicker`, `.display`, `.body`,
  `.fine`, `.tag`, `.mark.icon`). Don't edit it; put day-wide additions in `source/<date>/day.css`, slide CSS inline.
  Every slide keeps the running header (left: a short section label; right: `0N / 0M`).
- **Vary the visual sequence.** The posts of one day use different sequences (see LAYOUTS.md for the repertoire).
- Caption.txt: 40 to 90 words, plain owner-to-owner English, no hashtags, no emoji, few dashes, no sales cliches
  ("elevate", "unleash", "game-changer"). Say the specific thing, the qualifier (variant, through which date), end
  with where to shop. Every figure in it checked like the slides.
- Ledger: one CSV per carousel, `ledger/rows/<date>_<slot>.csv`, header in `ledger/HEADER.csv`. Photo originals are
  written as paths inside the source folder ("MASTER MEDIA/FDP CARS/..."), never a full path with an account in it.

## Cross-day lanes
[[When a car, part or topic repeats across days, give each day its own angle here so repeats don't read as reruns.
Example from FD-BFCM-75: "Brake lines: Nov 20 education = what a braided line is; Nov 21 spotlight = FD lines by model
and price; Nov 23 reminder = lines and pads in one order."]]

## Report back (120 words or fewer)
Per carousel: concept in 8 words or fewer, photo used, any topic swap or doubt. Then the count delivered.
