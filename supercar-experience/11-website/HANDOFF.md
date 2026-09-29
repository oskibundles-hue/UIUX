# HANDOFF — Supercar Experience site (from claude.ai chat, 28 Sept 2026)

Pick up here in Claude Code. Branch: `claude/se-website-render` (never push to main).

## What this is
A static site for Supercar Experience (Las Vegas fleet rentals) plus Omarie's SE vlogs.
- Live: https://supercar-experience-garage.onrender.com (Render static site, auto-deploys on push to this branch; config in `/render.yaml`, `rootDir: supercar-experience/11-website`).
- Design mockup (3 artboards: desktop home, GT3 RS car bay, mobile): claude.ai canvas "Supercar Experience Site Mockup".

## Files
- `index.html` — one self-contained page (HTML + CSS + JS, no build). Google Fonts: Bebas Neue, Figtree, JetBrains Mono.
- `media/` — 9 ads (720p, from Dropbox `Supercar Experience/EXPVIP scottsdale ads` + `04 Flash Special Stories`) and 7 vlog previews `v_*.mp4` (12 s, 540p, from `05 Vlogs` v2.3 and the SE story reels in `NQ Studio/04 Exports`), each with a `.jpg` poster.

## Sections (in page order)
Hero canvas road + reticle · promo ribbon · Garage (cards from `cars[]`, hover preview, tap opens `#bay` video drawer, compare 2) · Build a drive (price dial, 50% off 2nd day / 3rd day free, $299 under-25) · On air (ad reels) · Vlogs (player + preview grid from `EP[]`) · Rally countdown (Apr 9–12, 2027) · Booking plate (725) 425-3583.

## Rules (from SE standards)
- Text line (725) 425-3583. 25+ to drive, $299 underage fee. Egnyte as text only, never a logo.
- Rates are from supercarexp.vip/cars (checked 28 Sept). Don't invent specs (hp, 0–60) — research first.
- The car ads are Scottsdale cuts; Vegas versions and ads for the other ~28 cars still to make.
- `[hidden]{display:none!important}` must stay in the CSS — without it the closed car bay blocks every tap (the 28 Sept bug).

## Open next steps
- Accent color: Omarie is choosing between SE gold, vlog red, HUD blue, white.
- Replace mockup placeholders (mileage allowance, insurance terms) with real terms.
- Add more cars from the fleet once footage exists.
