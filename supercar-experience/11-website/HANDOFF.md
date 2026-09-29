# HANDOFF — Supercar Experience site (from claude.ai chat, 28 Sept 2026; redesign live 29 Sept)

Pick up here in Claude Code. Branch: `claude/se-website-render` (never push to main).

## What this is
A static site for Supercar Experience (Las Vegas fleet rentals) plus Omarie's SE vlogs.
- Live: https://supercar-experience-garage.onrender.com (Render static site, auto-deploys on push to this branch; config in `/render.yaml`, `rootDir: supercar-experience/11-website`).
- Design mockup (3 artboards: desktop home, GT3 RS car bay, mobile): claude.ai canvas "Supercar Experience Site Mockup".

## Look (29 Sept 2026, Omarie's picks)
- Style: **Locked-On** (his standard). Colours: supercarexp.vip's **orange #FF4F16, black and white** ("def not this yellow theme"). The old gold version is in git history (commit 78d4417 and before).
- Type: Hanken Grotesk (their site uses Overused Grotesk, which isn't on Google Fonts) + JetBrains Mono for labels.
- Their components: white top bar, dark menu with a city pill, round-ended buttons with an arrow disc, price chips on photos, orange offer tags, orange offers strip, count tile, numbered steps, "Text to book" side tab.
- Locked-On on the web: lock-on brackets on the footage, kinetic headlines (blur + orange glint), slot-reel prices (only the final figure is readable), whip cuts between cars, a freeze on the cut.
- `/v2/` now just redirects to the main page (it was the preview).

## Files
- `index.html` — one self-contained page (HTML + CSS + JS, no build). All media paths go through `const M="media/"`.
- `media/` — 9 ads (720p, from Dropbox `Supercar Experience/EXPVIP scottsdale ads` + `04 Flash Special Stories`) and 7 vlog previews `v_*.mp4` (12 s, 540p, from `05 Vlogs` v2.3 and the SE story reels in `NQ Studio/04 Exports`), each with a `.jpg` poster.
- `media/stills/` — one clean driving frame per car (from the ads at 9.2–10.6 s), used on the cards and behind the hero.
- `media/brand/` — SE logo PNGs copied from `supercar-experience/02-logos/png`.

## Sections (in page order)
Hero viewfinder (7 cars, whip cuts) · offers strip · Garage (cards from `cars[]`, hover preview, tap opens `#bay`, compare 2, count tile) · Build a drive (price dial, 50% off 2nd day / 3rd day free, $299 under-25) · On air (ad reels) · Vlogs (player + grid from `EP[]`) · Rally (Apr 9–11, 2027, countdown) · How booking works (3 steps) · Booking band (725) 425-3583.

## Rules (from SE standards)
- Text line (725) 425-3583. 25+ to drive, $299 underage fee. Egnyte as text only, never a logo. Instagram @supercar_experience_ (checked on supercarexp.vip, 29 Sept).
- Rates are the Las Vegas listings on supercarexp.vip/cars (day and 5-hour, all 7 cars re-checked 28 Sept). Don't invent specs (hp, 0–60) — research first.
- Rally facts follow supercarexp.vip/rally (Omarie's call, 28 Sept): 3 days, Apr 9–11 2027, 2 hotel nights, $1,599 per car, Las Vegas → San Diego → Santa Barbara. Its /cars page still lists the rally at $2,999, its home page says Apr 9–12, and the approved rally ads say Apr 9–12 with Las Vegas / Scottsdale / Boise; those conflicts are for the client to settle.
- **The car ads are Scottsdale cuts**: their graphics say 4 HOURS and 21+ (the site says 5 hours and 25+), and a gold RESERVE button fades in at 10.9 s. The hero and card hovers play only the clean shot, 9.25–10.8 s, at 0.55x (`S0`, `S1`, `RATE`); a video is shown only inside that window and freezes on the cut. The car bay and On air still play the full ads. Vegas versions and ads for the other ~28 cars are still to make.
- `[hidden]{display:none!important}` must stay in the CSS — without it the closed car bay blocks every tap (the 28 Sept bug).

## Open next steps
- Vegas cuts of the ads (fixes the 4 hours / 21+ text in the bay and On air).
- "Type behind the car" (the one Locked-On effect not on the site): needs a matte and a clean frame per car.
- Replace mockup placeholders (mileage allowance, insurance terms) with real terms. Insurance line and tap-to-text links were offered on 28 Sept and not chosen.
- Add more cars from the fleet once footage exists.
- Not yet checked on a real phone.
