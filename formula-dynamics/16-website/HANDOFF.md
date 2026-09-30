# HANDOFF — Formula Dynamics site, "The Job Board" (built 30 Sept 2026)

Branch: `claude/fd-website-render` (from `claude/formula-dynamics-assets-bnlnkm`). Never push to main.
Render service: `formula-dynamics-job-board`, live at
`https://formula-dynamics-job-board.onrender.com` since 30 Sept 2026, 2:07 PM Pacific. It auto-deploys on every push to
this branch. It was created with the Render connector, not as a Blueprint, so `/render.yaml` is not linked to it:
change settings in the Render dashboard (publish directory `formula-dynamics/16-website`, build command a no-op
echo). The 7-day `Cache-Control` on `/media/*` from `render.yaml` isn't set on the live service; add it under
Settings → Headers if wanted. The share pages and the canonical/og URLs at the top of `index.html` use that URL
(`BASE` in `../16-website-tools/make_episode_pages.py`).

## What it is
The FD counterpart of the Supercar Experience site (supercar-experience-garage.onrender.com). Four jobs at once:
1. **Vlogs first.** All 12 FD episodes play in full in "In the bay", chapters as labor lines.
2. **What we install and sell.** "The parts counter": the 21 store-ad products, each linking to formuladynamics.com.
3. **Behind the scenes.** The episodes are the proof; the service menu links each service to the jobs on camera.
4. **Before and afters.** Real frame pairs from the same job.

## Look (The Job Board, approved 30 Sept 2026)
- Episodes are work-order tickets (paper #F2F2F2, black ink, red magnet pin, "JOB 07 · SEP 09", ruler divider, service pills)
  in five lanes: The shop / Tuning / Exhaust / Suspension / Detail & PPF.
- The FD vlog chapter-bar ruler is the motif: the scroll progress bar (with the current section as its label), the section
  heads (they draw themselves in), the player's scrubber, the before/after handle.
- Brand: red #FE0F13, white, black; green #1DB14B and yellow #FFDE00 only inside the five-segment stripe. Neutral greys
  only. Bebas Neue caps +0.02em for headlines, Barlow body, JetBrains Mono labels, all self-hosted in `media/fonts/` (OFL).
  Logo from `../02-logos/svg-vector/`, 150 px wide in the header.

## Motion (Locked-On techniques, web versions)
Hero: the lift raises Job 12's muted loop off the checker floor while the post rulers tick red, pointer parallax on the
floor, kinetic headline (per-word rise with blur, red glint), slot-reel counters (12, 20+). Board: tickets drop in with a
magnet snap, hover tilt, hover plays the ticket's 8 s loop, lane chips re-lay the board with FLIP. Film grain.
Parts: tag cards, the store ad loops on hover (phones: the cards nearest the middle of the screen). Before/after sliders
sweep once on first view. `prefers-reduced-motion` settles everything to its end state.

## Phone and performance rules (from the SE site, keep them)
- Every autoplaying muted loop goes through `watchLoop()` (the `LOOPS` map): it gets its source only while on screen or
  hovered, and drops it when it leaves. All loops are freed while an episode plays (`freeLoops()` on `play`).
- Nothing over the player uses `backdrop-filter`. `[hidden]{display:none!important}` must stay in the CSS.
- On Save-Data or 2G/3G nothing autoplays (hover or tap still plays). Phones get one moving ticket and two moving parts at a
  time. Episodes use `preload="metadata"`, loops `preload="none"`, images `loading="lazy"`.

## Data (the JSON block `<script id="data">` in index.html)
`EP` (episodes), `LANES`, `BA` (before/after pairs), `PARTS`, `CATS`, `ADS`, `SERVICES`, `MAKES`, `JOBS` (form checkboxes).
All media paths go through `const M="media/"`.

### Adding an episode (into `media/ep/`)
1. Web copy: `ffmpeg -i SRC -vf scale=720:1280:flags=lanczos -c:v libx264 -preset slow -crf 24 -maxrate 2000k -bufsize 4000k -profile:v high -level 4.0 -pix_fmt yuv420p -g 60 -c:a aac -b:a 128k -ac 2 -ar 48000 -movflags +faststart <k>.mp4`
   (≈33–46 MB for a 2:50 episode; keep every file under 100 MB for GitHub).
2. Add `<k>` to `LOOP` and `COVER` in `../16-website-tools/build_media.py` (pick both off a contact sheet; skip frames
   with hp callouts or spec cards) and run `python3 build_media.py --src <folder> --only eps`. It writes the 8 s loop
   (360x640, no audio), the cover (540 wide) and the scrub sprite (96x170 tiles, 6 across, one every 5 s, 42 max = 3:30).
3. Add a row to `EP` (k, no, d, car, t, len, sec, lane, tags, work, s, alt, ch) and the key to its lane in `LANES`.
   `ch` = the chapters burned into the episode, `[start second, name]`, using the first second each label is fully typed
   (a 2 fps crop of the chapter-bar region, then read the crops). Episodes with no chapter bars get `"nochap":true`
   and their on-screen title card as the one line.
4. Run `python3 ../16-website-tools/make_episode_pages.py` (Node Playwright + Chromium). It writes `ep/<k>/index.html`
   and `media/share/<k>.jpg` and redraws `media/share/series.jpg`. Update "Twelve jobs" in the page's og/twitter text.
The newest episode in `EP` is the one on the lift in the hero.

### Adding a product
Put its store ad in the store folder, add it to `products.json` (`store_ads_21`), run `build_media.py --only products`,
and add a row to `PARTS` (n, cat, make, vendor, title as on the store, min, max, url). Prices show as the store's; when
min ≠ max the card says "from". Re-check prices on formuladynamics.com and update the date in the parts note.
The store photo is only resized, never graded.

## Settled facts (checked by the facts floor, 30 Sept; don't regress)
- Episode titles, dates, car labels and lengths: the table in the brief (`EP`). The car in Jobs 10–12 is the F8 Spider.
- The hero: exhaust jobs reach the test drive; the tune is bench work and the lowering job ends "NOT DONE YET".
- Job 11's frame shows the rear bumper off. Free-tune ads read "Free ECU tune with a RYFT or Opus exhaust".
- The ads are not "the shop's own footage" (some is Supercar Experience fleet footage); no count on "approved ads".
- GT3 RS brake ad sits under Maintenance & repair. Urus ads = Mansory Urus; the annual ad's car = SF90.
- Shop details, hours, the nine services, the ten makes and the disclaimer: formuladynamicsperformance.com, 30 Sept.
- The valve controller on the store ($349, Valvetronic Designs) is the part fitted in Jobs 11–12 (Omarie, 30 Sept).
- No performance figures anywhere (no hp, 0–60, gains). Loops and covers avoid the episodes' hp callouts.

## Open items
- **Dry ice blasting** and **Turbo upgrades** use lines from the shop's own service pages (`/services/dry-ice-blasting`, `/services/turbo-upgrades`, 30 Sept). Swap in anything the shop prefers.
- Jobs 09 and 10 have no burned-in chapter bars; each has one line from its title card.
- Job 12 has a brief "00:07 The fix" label; it's left out of the labor lines (two seconds after "One actuator live").
- Vendor tag for RYFT products is written "ryft" (prose rule); the product titles are the store's own and keep "RYFT".
- Several store listing photos are the store's own AI-generated images (file names "Gemini_Generated_Image…",
  "ChatGPT_Image…"). They're used as the store shows them; the shop may want real photos.
- Not yet checked on a real iPhone. H.264 playback was tested with VP9 stand-ins (the test Chromium has no H.264).
- The approved 12th ad (white 911 oil service) isn't in the repo, so it's not in the rail.

### Job 06 (mc20) web copy: one callout blurred
The source episode carries a burned-in callout "POWERTRAIN · 3.0L TWIN-TURBO V6" from about 1:20.1 to 1:23.7, pointing at the
F8 Spider's taillight cavity. The F8 Spider has a 3.9 L twin-turbo V8 (ferrari.com); 3.0 L V6 is the MC20's engine. The site's copy
blurs that label, its POWERTRAIN tag and the reticle for those seconds only (logo, captions, length and chapters unchanged). The
approved episode in Dropbox is untouched. Rebuild it with:
`ffmpeg -i mc20.mp4 -filter_complex "[0:v]split=4[m][x][y][z];[x]crop=470:135:430:445,boxblur=luma_radius=30:luma_power=3:chroma_radius=15:chroma_power=2[a];[y]crop=280:55:430:395,boxblur=luma_radius=20:luma_power=3:chroma_radius=10:chroma_power=2[b];[z]crop=420:420:270:555,boxblur=luma_radius=40:luma_power=3:chroma_radius=20:chroma_power=2[c];[m][a]overlay=430:445:enable='between(t,80.05,83.8)'[m1];[m1][b]overlay=430:395:enable='between(t,80.05,83.8)'[m2];[m2][c]overlay=270:555:enable='between(t,80.05,83.8)',scale=720:1280:flags=lanczos[v]" -map "[v]" -map 0:a` plus the usual web-copy encode settings above.

### Valve-controller spotlight (media/parts/valve-spot.mp4): trimmed web copy
The approved spotlight master (`01 Valve controller - the build (video, 20s, sound on) (v4, graded).mp4`, posted 26 Sept) opens
with a "FERRARI F8 SPYDER" title card for its first ~3.6 s. The model is the F8 Spider, so the site's copy starts at 3.9 s
(first frame "02 ON THE LIFT") and the poster is the 4.5 s frame. `build_media.py` does this (`-ss 3.9`); re-encoding
straight from the master would bring the misspelling back. The master itself is untouched.

