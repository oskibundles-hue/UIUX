# Layout library: 51 slide layouts from FD-BFCM-75

Every layout below shipped in the approved Black Friday run. Each entry points at a real slide in `../30-bfcm-75/source/`
(read as `date slot slide`, so `11-20 2_sale 3` is `../30-bfcm-75/source/2026-11-20/2_sale/slide-03.html`). Each slide's
own CSS is inline, but every slide from Nov 23 and Nov 25 to Dec 4 also links its day's `../day.css` (the day-wide rules,
such as where `.fine.pin` sits). Copy that `day.css` into your date folder with the slide, or move the rules it uses inline.

**Borrowing one:** copy the slide file into your carousel folder, keep the `.run` header and its counter, swap the photo
for one of yours in `assets/photos/` (the relative paths work at the same folder depth), rewrite every word, and run the
checker. The photos themselves are not in git; to see a slide as it shipped, open the campaign's delivery folder at
`exports/<date>/<slot>/0N.jpg`, or render the source with `tools/render.py` once the photo is in place.

**Vary the sequence.** The five posts of one day never share a sequence, and a carousel is judged by its idea, not its
paint: a new headline, colour or crop on the same layout is not a new concept.

## Slide 1: stop the scroll
| layout | what it does | example |
|---|---|---|
| Full-bleed hero | one real FD photo edge to edge, the headline low on the dark part of the frame | `11-20 1_products 1` |
| Hero with a ring | full-bleed photo with a red ring and short label on the one thing the post is about | `11-20 3_cars 1`, `11-26 3_cars 1`, `11-27 1_products 1` |
| Photo band over type | the photo takes the top third or half, the headline sits on black below | `11-24 2_sale 1`, `12-03 1_products 1`, `12-04 1_products 1` |
| Split | question on black at the left, the product listing photo at the right | `11-24 4_education 1` |
| Photo strip | a narrow photo strip at the left, a tall headline at the right | `12-04 2_sale 1` |
| Date strip | a row of day cells (a 15-day run, the last 3 days) with today or the last day in red | `11-20 2_sale 1`, `11-30 2_sale 1`, `12-01 5_reminder 1` |
| Big countdown | one huge number of days left over a photo | `11-27 5_reminder 1`, `12-02 5_reminder 1` |
| Receipt | no photo: a receipt card as the cover, two listing lines, the total and the saving | `11-23 5_reminder 1` |
| Cut-out hero | the part cut out on black (a round wheel spacer) with the headline beside it | `11-28 5_reminder 1` |
| Type hero | no photo: one big red glyph (a ÷ sign) and a headline. A glyph 200 px and up may cross the margin | `12-04 4_education 1` |

## The middle: prove it or teach it
| layout | what it does | example |
|---|---|---|
| Ring on the part | the photo zoomed onto the part, one red ring and a label, two lines of body | `11-20 1_products 2`, `11-24 3_cars 2`, `12-03 4_education 2` |
| Numbered ring pins | two to four numbered rings on the part, a key list under the photo (`.pin` may cross the margin) | `11-24 1_products 2`, `11-25 5_reminder 2`, `11-26 4_education 2` |
| Side-by-side photos | two photos, one label each: before and after, this car and that one | `11-23 1_products 2`, `12-02 4_education 2` |
| Side-by-side cards | two cards on black comparing two variants, two models or two choices | `11-22 2_sale 3`, `11-27 3_cars 2`, `11-29 1_products 2`, `12-02 2_sale 2` |
| Two-column size card | FRONT and REAR (or left and right) as two columns of measured figures | `11-20 3_cars 2` |
| Tier board | the discount tiers set as type, biggest first, with the categories under each | `11-20 2_sale 2` |
| Price ladder | three to five rows from cheapest to dearest, was and now on each | `11-21 5_reminder 3`, `11-25 2_sale 2`, `12-04 1_products 2` |
| Budget ladder | rows with progress bars and a running total, then the total saved | `11-22 2_sale 2` |
| Dollar bar chart | bars to scale for three listings' savings: a small percent on a big price wins | `11-27 2_sale 2` |
| Big stat | one figure set huge ("239 of 1,152" listings on sale) over a small count grid | `11-28 2_sale 2` |
| Spec card | a dark card of rows (Fits, Finish, In the box), from the listing word for word | `11-20 4_education 3`, `11-22 3_cars 2`, `11-25 1_products 2` |
| Model index | no photo: how many models a part is listed for, by make, and one price block | `11-21 1_products 2` |
| Listing titles, boxed | three near-identical listing titles with the model underlined and the part number boxed | `11-20 5_reminder 2` |
| Listing tiles | small tiles of real listings: photo, title, price | `11-30 2_sale 2`, `11-30 5_reminder 2` |
| Fitment tiles | six tiles, one per car the part fits, each with its price | `12-02 1_products 3` |
| Fit line as a document | the listing's fit line set as text with numbered underlines and a key | `11-24 4_education 2` |
| Annotated listing | a listing drawn as a diagram with numbered markers and a worked sum beside it | `12-04 4_education 2` |
| On your car vs on the listing | a two-column table: what to look at on the car, what to check on the listing | `12-01 5_reminder 2` |
| Cross-section diagram | an SVG or CSS diagram: rubber vs braided line, closed vs open, a wheel's gap to the fender | `11-20 4_education 2`, `11-25 4_education 2`, `11-23 4_education 2` |
| Conversion diagram | the factory part number to the upgrade's code, under a badge photo band, with the fit line | `11-21 3_cars 2` |
| Motion diagrams | side-by-side line drawings of a part moving (damper compressing, extending) | `11-27 4_education 2` |
| Care loop | no photo: three numbered stops around a ring, the yearly rhythm in the middle | `11-22 4_education 2` |
| Signal path | three nodes in a line, showing where a part sits in the chain | `11-29 4_education 2` |
| Swatch grid | a macro crop, then the four finishes a part comes in as named swatches | `11-28 1_products 3` |
| Paper service sheet | a white card styled as a shop sheet, sale items ticked and full-price ones not | `11-24 2_sale 2` |
| Checklist | three to five numbered checks before ordering | `11-21 5_reminder 2`, `11-22 5_reminder 2`, `11-30 4_education 2` |
| Weekend plan | a numbered plan for a set of days, one action each | `11-27 5_reminder 2` |
| Recap list | the day's posts in one list, one row each with its time | `12-04 5_reminder 2` |
| Gift tag | one gift tag (one piece, one price line) under a macro crop of the part | `11-29 5_reminder 2` |
| Message card | no photo: the one line to send your installer, with the two listing titles | `11-22 5_reminder 3` |
| DM template | the exact message to send the shop, ready to copy | `12-03 5_reminder 2` |

## The last slide: turn it into an action
| layout | what it does | example |
|---|---|---|
| Facts plus SHOP NOW | numbered facts on how it's done, then the store CTA and the wordmark | the starter's slide 3, `11-20 1_products 3` |
| Cart arithmetic | the pieces in a cart, was, now and the saving, then SHOP NOW | `11-20 3_cars 3`, `11-21 2_sale 2`, `11-29 2_sale 2`, `11-30 1_products 3`, `12-02 3_cars 3` |
| Equation card | was total minus now total equals the saving, set as one sum | `12-03 2_sale 3`, `11-23 4_education 3` |
| Q&A | three owner questions and short answers from the listing notes | `11-20 2_sale 3`, `11-26 1_products 3`, `12-04 3_cars 3` |
| Spring matrix | a grid of spring options for one car, with fine print | `12-03 3_cars 3` |
| Budget fork | goals on the left, arrows to the part and price that fits each | `12-01 2_sale 3` |
| Giant date | the last day as one huge date, then SHOP NOW | `11-24 2_sale 3` |
| Send us your car | four fields to send the shop about your car, then BOOK YOUR BUILD | `12-01 4_education 3` |
| BOOK YOUR BUILD | the shop's CTA with the site and handle, for install or shop work only | `11-28 3_cars 3`, `11-30 4_education 3` |
| Checklist close | the before-you-order checklist as the last word, then SHOP NOW | `12-04 1_products 3` |
