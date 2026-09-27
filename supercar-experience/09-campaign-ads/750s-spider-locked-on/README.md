# "ROOF DOWN": McLaren 750S Spider, LOCKED ON, 18 s 9:16 story

**Status: DRAFT for Omarie's review. It is not approved and has not been posted anywhere.** It is built to
THE STANDARD for SE ads (`locked-on`, `../HOUSE-STYLE.md` on the SE branch). It started from the approved GT3
RS showcase's settings and library (`../flash-special-showcase/`, whose `lib/` modules are vendored here).

![poster](exports/poster.jpg) ![end card](exports/poster-endcard.jpg)

It is an evergreen rental ad for the 2026 McLaren 750S Spider in Las Vegas, cut from SE's own clip of that
car (Dropbox `Supercar Experience/01 Car Footage/SCE_McLaren-750S_no-branding.mov`: "the car in the 750S
Spider reel on the rental listing"). The idea comes from the footage. The clip's last shot is a locked-off
view of the car's tail while the retractable roof stows. There, the giant word SPIDER rises out of the sky
**behind** the car as the roof folds away, the buttresses and rear deck stay in front of it, and then the
price rises from behind the car for the end card.

## On screen, and where each line comes from

| Line | Source |
|---|---|
| MCLAREN · 750S SPIDER · 2026 · EXOTIC | supercarexp.vip/cars/2026-mclaren-750s-spider-las-vegas, read 27 Sept 2026 ("2026 McLaren 750S Spider", listed under Exotic) |
| LAS VEGAS | same listing (Las Vegas is the only location it lists) |
| 5 HOURS · $1,299 (hook, slot reel, end card) | same listing: "5-Hour Rental $1,299" |
| FULL DAY · $1,799 | same listing: "Full Day Rental $1,799" |
| YOU NEED · VALID DRIVER'S LICENSE · INSURANCE | supercarexp.vip: "Valid driver's license and valid matching insurance required"; the approved showcase's wording |
| 25+ · AGES 21–24 WITH $299 UNDERAGE FEE / RENTERS 25+ · … | supercarexp.vip, 27 Sept 2026: "Renter Must Be 25+ (Ages 21–24 With $299 Underage Fee)". Omarie, 26 Sept (rally vlog): include the age requirement as the site words it |
| TEXT OR DM TO BOOK · (725) 425-3583 · SUPERCAREXP.VIP · @SUPERCAR_EXPERIENCE_ | the approved GT3 RS showcase (Omarie, 26 Sept: the site-wide text line on Las Vegas footage, TEXT not CALL, and the handle). The site still shows "Questions? Text Us (725) 425-3583" on 27 Sept |
| SPIDER (giant, behind the car) | the model's name. It is set as the roof stows, which is what makes it a Spider |
| SE lockups | `../../02-logos/png/sce-primary-horizontal--white.png` |

Every figure is in `config.json`, with its source. The ad shows no horsepower, 0-60, top speed, discount,
"save $X", testimonial or countdown. The site's standing promo ("50% Off 2nd Day or 3rd Day Free") is left off
because the approved ads carry no discount unless one is given for the ad. The slot reels only ever show
blurred intermediates, and they land on the true digits.

## Defaults I chose (change any of them and re-render)

These were the open decisions in the brief. Each default follows the newest approved precedent.

| Decision | Default used | Why |
|---|---|---|
| Car | 2026 McLaren 750S Spider | a priority car; its footage is the listing's own reel; it has no LOCKED ON ad yet (the GT3 RS has one) |
| Offer | the site's standing rates: 5 hours $1,299, full day $1,799 | the 26 Sept flash offers are expired and must not be reposted; a new promo needs Omarie's figures |
| City and phone | Las Vegas; the text line (725) 425-3583, TEXT OR DM TO BOOK | the approved LV showcase uses this exact line after fix r2; the listing is LV only |
| Age line | 25+ with the site's $299 underage-fee wording | Omarie's 26 Sept decision on the rally vlog (newer than the 21+ on the older ads) |
| Music | the clip's own music | house rule 7 and Omarie ("Keep music as well"). **Its rights are not verified: confirm before any paid use** |
| Delivery | the files are sent to the requester only | nothing is posted and nothing is uploaded to Dropbox without a per-action go |

## Change a figure

Edit `config.json`, then run `python3 build.py`. Only the layers that changed re-render.

## Re-render

```bash
FOOTAGE=/path/to/folder/with/the/clip python3 build.py   # every stage, cached; ~10 min on 4 CPUs
python3 build.py --frames 0,113,300,431                  # stills -> .work/stills/
python3 build.py --qa                                    # QA on the delivered file -> exports/qa/
```

The clip is `SCE_McLaren-750S_no-branding.mov` from Dropbox `Supercar Experience/01 Car Footage/` (84 MB,
2160x3840 H.264 High 10 at 10-bit, 23.976 fps, 24-bit PCM stereo, 24.36 s). The default footage folder is `.work/footage/`.
The build needs Python 3 with numpy and Pillow, ffmpeg with libx264, and Node 22 with Playwright
(`/opt/node22/lib/node_modules/playwright`).

Stages, each cached in `.work/` (ignored by git):

1. `source`: frame-exact decode to 1080x1920, never with `-ss`.
2. `dense`: 4x optical-flow in-betweens of the roof shot, via `lib/dense.py` (ffmpeg minterpolate).
3. `prep`: the config, timeline and tracks as JS for the pages.
4. `plate`: `lib/plate.py`.
5. `front`: `front.html`.
6. `mid`: `mid.html`.
7. `audio`: `audio/bed.py`.
8. `finish`: composite, then the master and delivery encodes.
9. `qa`.

## Files

| Path | What |
|---|---|
| `config.json` | every figure and claim string, with sources |
| `cue.md` | the build cue as built: beat table, layer stack, graphics positions |
| `front.html` / `mid.html` | the front motion layer / the behind-the-car type layer (`window.renderAt(t)`) |
| `build.py` | the one-command build |
| `lib/edl.py` | the beat table on the music's 130 BPM grid (timing and plate FX, no copy) |
| `lib/plate.py` | the plate: sampling, day grade, streaks, pushes, whips, impacts, leaks, plate blur, grad, light sweep |
| `lib/sky.py` | the sky matte that puts type behind the car (no roto: the shot is locked off against open sky) |
| `lib/dense.py` | optical-flow slow motion for the roof shot |
| `lib/track_npy.py`, `lib/data/tracks.json` | template tracks of the McLaren speedmark on the steering wheel (f204-225) and the headlight (f136-157), via the approved `lib/track.py` |
| `lib/plate_find.py`, `lib/data/plate_track.json` | the licence-plate box on the rear chase shot (f348-368) |
| `audio/bed.py` (+ `bed.wav`, `bed_sync.json`) | the sound bed: the clip's music plus accents, mastered |
| `lib/fx.py`, `kinetic.js`, `lock.js`, `kcapture.js`, `accum.py`, `track.py`, `audio/synth.py` | vendored unchanged from `../flash-special-showcase/` |
| `exports/` | `poster.jpg` (frame 0, the complete hook), `poster-endcard.jpg`, `contact-sheet.jpg`, `qa/` |
