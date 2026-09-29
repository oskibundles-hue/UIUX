# HANDOFF — Supercar Experience site (from claude.ai chat, 28 Sept 2026; vlog-first version live 29 Sept)

Pick up here in Claude Code. Branch: `claude/se-website-render` (never push to main).

## What this is
**Behind the Wheel**: Omarie's Supercar Experience vlog series comes first (the behind-the-scenes of getting the car to the customer), with SE's Las Vegas rentals, ads and the rally underneath.
- Live: https://supercar-experience-garage.onrender.com (Render static site, auto-deploys on push to this branch; config in `/render.yaml`, `rootDir: supercar-experience/11-website`). Render serves byte ranges, which the episode player needs for seeking.
- `/v2/` redirects to the main page and keeps `#watch-<episode>` links working (it was the preview).
- Earlier versions are in git history: gold (78d4417 and before), orange rental-first (3e84fd5).

## Look (29 Sept 2026, Omarie's picks)
- Style: **Locked-On** (his standard). Colours: supercarexp.vip's **orange #FF4F16, black and white** ("def not this yellow theme").
- Type: Hanken Grotesk + JetBrains Mono for labels.
- Data saver: on Save-Data or a 2G/3G connection nothing autoplays (still frames; a loop still plays on hover or tap), and phones get 2 moving tiles in the hero wall instead of 4.
- Motion: a moving wall of episode footage (tiles recycled as they leave the top), kinetic headlines (blur + orange glint), lock-on brackets, slot-reel numbers, scroll progress bar, film grain, a scroll-driven sideways timeline. `prefers-reduced-motion` settles everything to stills.

## Episodes (`EP[]` in index.html)
The current approved versions from `NQ Studio/04 Exports/00 POSTING PLAN.md` (28 Sept), SE only:
| # | Filmed | Title | Source |
|---|---|---|---|
| 1 | Sep 7 | Scottsdale and back | `04 Exports/2026-09-12 Reel Cut/06 … v3 SE - INSTAGRAM 1080x1920.mp4` |
| 2 | Sep 11 | The shoot and the V12 | `04 Exports/2026-09-19 Sep 11 Hybrid Story/… Extended (v2 coworker captions) - INSTAGRAM` |
| 3 | Sep 12 | 27th birthday | `04 Exports/2026-09-15 Story Reels/01 …` |
| 4 | Sep 13 | Pickup day | `04 Exports/2026-09-15 Story Reels/02 …` |
| 5 | Sep 13 | The flat tyre | `04 Exports/2026-09-15 Story Reels/03 …` |
| 6 | Sep 15 | Rally day with Egnyte (v2.5, approved final) | `Supercar Experience/05 Vlogs/2026-09-15 Rally v2.5 - Egnyte (final)/` |

**Adding an episode** (e.g. Sep 24, the Seattle McLaren trip, once approved), all into `media/ep/`:
1. Full episode: `ffmpeg -i SRC -vf scale=720:1280:flags=lanczos -c:v libx264 -preset slow -crf 24 -maxrate 3000k -bufsize 6000k -profile:v high -level 4.0 -pix_fmt yuv420p -g 60 -c:a aac -b:a 128k -ac 2 -ar 48000 -movflags +faststart <k>.mp4` (keep each file under 100 MB for GitHub).
2. Loop: 8 s, `-an -vf scale=360:640,fps=30 -crf 29` → `<k>-loop.mp4`. Cover: one frame `scale=540:-2 -q:v 4` → `<k>.jpg`. Scrub sprite: `-vf fps=1/5,scale=96:170,tile=6x7 -frames:v 1 -q:v 6` → `<k>-thumbs.jpg` (the player expects 96x170 tiles, 6 across, one every 5 s, 42 max = 3:30).
3. Add a row to `EP[]` (k, d, t, s, len, sec, where, mo = [seconds, moment title, moment line]).
4. Run `python3 ../website-tools/make_episode_pages.py` (needs Google Chrome). It writes `ep/<k>/index.html` and `media/share/<k>.jpg` for every episode and redraws `media/share/series.jpg` with the new count. Update "Six episodes" in the page's og/twitter description by hand.
Pick loops and covers from a contact sheet; skip frames with speed readouts or spec cards.

## Files
- `index.html` — one self-contained page (HTML + CSS + JS, no build). All media paths go through `const M="media/"`.
- `ep/<k>/` — one small page per episode, so a shared link previews with that episode's own picture and title (Open Graph + X cards + VideoObject data). It sends the visitor straight on to `/#watch-<k>`. The player's Share / Copy link button gives this link.
- `media/share/` — the 1200x630 preview pictures (one per episode + `series.jpg` for the main page), drawn from `../website-tools/share-card.html`.
- `media/ep/` — the 6 episodes (720p web copies, 37–57 MB), loops, covers, scrub sprites.
- `media/` — 9 car ads (720p Scottsdale cuts) with posters; `v_*.mp4` are the old 12-second vlog previews, no longer used.
- `media/stills/` — one clean driving frame per car; `media/brand/` — SE logo PNGs.

## Sections (in page order)
Hero (footage wall, latest episode card) · episode title strip · Episodes rail (resume bars) · Theatre (full-episode player, queue) · What it takes (scroll timeline, one moment per episode, opens the episode at that second) · The ads · Rentals (cars, compare, trip builder) · Rally (Apr 9–11, 2027) · Booking band (725) 425-3583.

## Rules (from SE standards)
- Text line (725) 425-3583. 25+ to drive, $299 underage fee. Egnyte as text only, never a logo. Instagram @supercar_experience_ (checked on supercarexp.vip, 29 Sept). Full episodes play on the site, never linked out to Instagram (Omarie, 29 Sept: they aren't on his Instagram).
- Rates are the Las Vegas listings on supercarexp.vip/cars (day and 5-hour, all 7 cars re-checked 28 Sept). Don't invent specs (hp, 0–60) — research first.
- Rally facts follow supercarexp.vip/rally (Omarie's call, 28 Sept): 3 days, Apr 9–11 2027, 2 hotel nights, $1,599 per car, Las Vegas → San Diego → Santa Barbara. Its /cars page still lists the rally at $2,999, its home page says Apr 9–12, and the approved rally ads say Apr 9–12 with Las Vegas / Scottsdale / Boise; those conflicts are for the client to settle.
- **The car ads are Scottsdale cuts**: their graphics say 4 HOURS and 21+ (the site says 5 hours and 25+), and a gold RESERVE button fades in at 10.9 s. Car-card hovers play only the clean shot, 9.25–10.8 s, at 0.55x (`S0`, `S1`, `RATE`). The car bay and the ads row still play the full ads.
- `[hidden]{display:none!important}` must stay in the CSS — without it a closed overlay blocks every tap (the 28 Sept bug).

## Open next steps
- Some cars from the full rental list are missing (Omarie, 29 Sept: "we'll worry about that later").
- Add Sep 24 and the Seattle McLaren trip episodes once approved.
- Vegas cuts of the car ads (fixes the 4 hours / 21+ text in the bay and ads row).
- "Type behind the car" (the one Locked-On effect not on the site): needs a matte and a clean frame per car.
- Not yet checked on a real phone.
