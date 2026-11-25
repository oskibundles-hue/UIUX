# FD-BFCM-75 build brief (for day-builder agents)

Formula Dynamics (FD, a luxury car shop with a parts store at formuladynamics.com) Black Friday sale, Nov 20 to Dec 4, 2026.
75 Instagram carousels: 15 days x 5 posts x 3 slides, 1080x1350 sRGB. Work folder: this folder (`formula-dynamics/30-bfcm-75/`).
The style is decided: owner-focused luxury automotive editorial in the FD brand. Do not ask anyone about style.

## The bar
Each carousel is built around one specific thing an owner can **see on a real FD car or part** or **learn** before buying.
A top agency would ship: a real FD photo cropped with intent, one clear idea per carousel, a slide 1 that stops the
scroll, slide 2 that proves or teaches, slide 3 that turns it into an action. Every figure true to the store listing.
The weak version to beat (Codex's proofs): generic headlines over random car shots, the same layout every post, prices
with no stage or qualifier, a part named that the photo doesn't show. A new headline, colour or crop is NOT a new concept.

## The five posts each day (slot folder names are fixed)
| slot | role | posted (Pacific) |
|---|---|---|
| `1_products` | product spotlight: one store product, what it is, who it fits, its sale price | 9 AM |
| `2_sale` | sale guide: one reason to buy now (how to shop the sale, a tier, a budget, a date) | 11 AM |
| `3_cars` | car with product: a real FD car and a part/product that applies to it | 1 PM |
| `4_education` | education: one thing an owner learns (how a part works, how to read fitment) | 4 PM |
| `5_reminder` | sale reminder: a second, different reason to buy (save links, pair parts, deadline) | 7 PM |
Both sale posts in a day must give different reasons to buy. Planned topics per day are in `ref/boss.txt` (Codex's proof
book, also the calendar in PROGRESS.md). Use the planned topic unless no real photo or verified listing supports it;
then swap to a nearby topic and say why in the ledger `notes`.

## Hard rules
1. **Real FD photos only.** Sources: Google master media
   `~/Library/CloudStorage/GoogleDrive-<your account>/.shortcut-targets-by-id/1UPxExSmoVZ9JG0HmypD5jpoCIN4xozhl/MASTER MEDIA & CONTENT FOLDER/`
   (FDP CARS = customer cars by folder "YYYY.MM MAKE | model | work | customer"; FDP PRODUCTS and FDP CAMPAIGNS = part
   and vendor shots; FDP BUILDING = the shop) and Dropbox `~/Library/CloudStorage/Dropbox/Portfolio/` originals.
   Also `formula-dynamics/99-toolkit/video-index/` (INDEX.csv + contact sheets; `fd_index.py search ... --colour`)
   at the worktree root, to find clips without downloading. Videos are mostly 4K vertical: pick the sharpest frame
   (ffmpeg, test a few offsets), save a 2160-wide JPEG q92 into `assets/photos/<subject>_<view>.jpg`. Never overwrite
   a photo you did not make; check the name is free first. Store listing images are allowed for a product only if they
   carry no "+HP/+TQ" or performance graphics.
2. **Verify before naming.** Car model from the folder name AND the body in frame. A part brand only if the listing
   says it or it is legible in the frame. If the part on the car can't be identified, don't claim it was installed:
   show the car and a verified catalog feature, worded as available for that model, never as work done on that car.
   Photo tag pattern: "Shown: <car> at the FD shop". **Never print a customer name** (folder names carry them).
3. **Prices and discounts.** Discounts come ONLY from the tier list in `ref/codex-campaign-review.md`:
   20% FD brake lines, FD brake pads, ECU tuning, ECM modules / 15% FD suspension, wheel spacers, drive-by-wire
   modules, air filters / 10% Larini exhaust, service kits, oil kits / 5% KW coilovers, Brembo big brake kits,
   wheels. "Up to 20% on selected parts through Dec 4." Every price on a slide must match the store listing in
   `ref/store/p1-6.json` (Shopify products.json; `price` = sale, `compare_at_price` = was). Re-fetch live with
   `curl -s 'https://formuladynamics.com/products.json?limit=250&page=N'` if needed. Find listings by title, not body
   text. Name the variant/stage when variants differ in price. Print a fine-print source line with any price.
   If a product's listing shows no compare-at (not discounted), don't call it on sale.
4. **Never print** the VIP list code or any code, horsepower/torque/"faster"/performance claims (listing marketing copy about
   gains is not usable), customer names, or anything not checked.
5. **One FD mark per slide**: `assets/logos/fd-icon-white.png` (corner icon) OR the store wordmark
   `assets/logos/store-wordmark-white.png`, never both. Store CTA: `SHOP NOW · FORMULADYNAMICS.COM`. The shop's CTA
   (only for install/shop work): `BOOK YOUR BUILD · formuladynamicsperformance.com · @formuladynamicsperformance`.
6. **Plates.** Blur every readable plate with `tools/plate_blur.py IN OUT x0,y0,x1,y1` on the photo asset, then crop
   the blurred area and look at it to confirm it's unreadable. Background cars count.
7. **Phone check.** Text inside 72px side / 64px top-bottom margins; body text ≥ 30px, fine print ≥ 21px; nothing
   clipped or overlapping; text never on a busy area without a shade. After rendering, hstack the three
   `_phone/*.png` (390 px wide) into one sheet and look at it. Also zoom-check that any ring/arrow sits on the part.
8. Codex's earlier proofs (zips, kit, PDF, gallery) are read-only. Don't publish, post, email, commit or push.

## How to build (copy the system, don't reinvent it)
- Reference carousel: `source/2026-11-20/1_products/` (slide-01..03.html + Caption.txt) and shared `source/styles.css`
  (fonts, colours, `.run` header with counter, `.kicker`, `.display`, `.body`, `.fine`, `.tag`, `.mark.icon`).
  Don't edit styles.css; put day-wide additions in `source/<date>/day.css` if needed, slide-specific CSS inline.
  Every slide keeps the running header (left: a short section label; right: `0N / 03`).
- Photos are `<img>` in `.photo`, cropped by CSS (`object-position`, `--zoom`), so they stay replaceable.
- **Vary the visual sequence.** Repertoire: full-bleed hero; photo-top + price table; ring/arrow callout on a part;
  numbered steps; side-by-side comparison (A vs B, stage vs stage, stock vs upgraded part from listings);
  checklist ("before you order"); macro crop of a detail; spec card from the listing; cart arithmetic (was/now/save);
  date strip/countdown; Q&A. The 5 posts of a day must use 5 different sequences, and none may copy the reference
  sequence (hero / table+ring / numbered steps) exactly.
- Render: `~/.local/bin/uv run -q --with playwright --with pillow python tools/render.py out/<date>/<slot> source/<date>/<slot>/slide-0{1,2,3}.html`
  (writes 01-03.jpg and _phone/). Iterate until clean. Then deliver: `tools/deliver.sh <date> <slot>` (renders into
  the Drive delivery folder and refreshes PROGRESS.md).
- Caption.txt: 40–90 words, plain owner-to-owner English, no hashtags, no emoji, few dashes, no sales clichés
  ("elevate", "unleash", "game-changer"). Say the specific thing, the qualifier (variant, through Dec 4), end with
  where to shop. Every figure in it verified like the slides.
- Ledger: one CSV per carousel `ledger/rows/<date>_<slot>.csv`, same header and level of detail as
  `ledger/rows/2026-11-20_1_products.csv` (concept, angle, visual_sequence, photos, photo_originals with source path
  and timestamp but customer name replaced by `<customer>`, vehicle_verified, parts named, part_verification,
  prices_shown, price_source, discount_source, plate_blur, notes).

## Cross-day lanes (so repeated topics get different angles)
- Ferrari F8 cars: Nov 20 = wheel-to-fender gap and spacer fitment check; Nov 28 = rear/exhaust-tip detail
  (brand only if vendor-verified); Dec 4 = one car, the sale's parts that list for the F8 (verified listings only).
  Nov 20 post 1 already used the blue F8 Spider rear 3/4, underside and front 3/4 frames: other F8 posts use other frames.
- Brake lines: Nov 20 edu = what a braided line is (pedal feel, factual); Nov 21 spotlight = FD lines by model and
  price; Nov 23 reminder = lines + pads in one order (both 20%).
- Throttle: Nov 25 sale guide = the drive-by-wire module offer; Nov 29 edu = how a drive-by-wire pedal works (no gains).
- Repeated cars (SF90 Nov 26 / Dec 2; Ghibli Nov 23 / Dec 1; GranTurismo Nov 27 / Dec 3): use different frames and a
  different part each time; earlier date gets wheels/brakes, later date gets another system.
- Filters: Nov 22 edu = air filter care; Nov 30 = BMC filter spotlight; Dec 2 = cabin filter + filter shopping.

## Report back (≤ 120 words, caveman OK)
Per slot: concept in ≤ 8 words, photo used, any topic swap or doubt. Then counts: carousels delivered N/5.
