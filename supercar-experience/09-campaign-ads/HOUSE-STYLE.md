# Ad house style — approved treatments

**Read this before building an ad.** It records what the shop has actually
signed off on, so a new ad starts from a known-good treatment instead of a fresh
guess. `06-video-system/AUTO-EDIT.md` covers timing and the overlay tool; this
covers which look to reach for.

---

## THE STANDARD: `locked-on` (Supercar Experience ads)

**Made the standard by Omarie on 2026-09-26:** "That is amazing make that a standard."
**Made the standard for all his work on 2026-09-28:** "My locked on artifact is my standard for any work I work on."
The style guide page below is the standard for every job, in every workstream (Supercar Experience, Formula
Dynamics, Anti Stock): its techniques, process and quality bar apply to all of them. Each keeps its own brand
(the page's gold on black is SE's), and two brands never share a video.
**Ask which style first, then build it all the way (2026-09-28):** "make sure every session/branch/everything knows
and implements it no matter what when creating any work but ask beforehand what style should be used." Before any new
piece of work, ask Omarie which style to use, as a click with a recommendation: the approved styles (Locked-On;
Quick-Promo for a promo needed in under ~30 minutes; the workstream formats such as the SE vlog standard below) and,
marked as proposed, the looks on the same page (Now Boarding, Paste-Up; `750s-spider-locked-on/ --look`). Skip the
question only when he has named the style for this piece. Specialist agents never ask him; the lead names the style
in the brief.
Every SE car ad starts from this treatment unless the job says otherwise. Style guide page: https://claude.ai/artifact/WCe1qHhTrMDw7bkDaskeQm (source in `flash-special-showcase/style-guide/`). Reference build:
`flash-special-showcase/` ("LOCKED ON", GT3 RS, 18 s 9:16). Read its README before you start. Second approved
build: `750s-spider-locked-on/` ("ROOF DOWN", 750S Spider, 18 s, in 9:16, 4:5 and 1:1), the reference for feed cuts.

What makes an ad `locked-on`, in order of appearance:

1. **Hook on frame 0.** A black panel with the offer headline (e.g. FLASH SPECIAL / TODAY ONLY / ENDS 1 PM)
   and the SE lockup, fully built on the first frame so the story preview reads.
2. **Badge lock-on.** Gold corner brackets and a leader line *tracked* onto the maker's badge in
   the footage (`lib/track.py`, numpy template tracking). The brand, model and year · class callout types on
   beside it. Needs a shot of at least 1 s where the badge moves smoothly. A turning car won't track
   (the Black Series grille failed), so use a headlight or the badge instead.
3. **Kinetic type** with true sub-frame motion blur and gold glints (`lib/kinetic.js` +
   `lib/kcapture.js`). The price lands in a **slot reel** with no readable wrong digit on the way.
4. **Type behind the car.** A giant word (model designation or price) sits *between* the background
   and the car, with a 2.5D push (`lib/matte_lib.py`, `lib/warehouse.py`). This only works on a
   **locked-off shot**: tracing one car takes about 20 min, and a moving shot needs frame-by-frame roto,
   so don't promise it.
5. **Edit energy.** Whip transitions, eased speed ramps, a short freeze with a light sweep across the
   car, and one night grade across all shots (`lib/fx.py`, `lib/edl.py`). On sunlit footage keep one day grade
   instead: a night look reads fake there (ROOF DOWN, desert daylight, was approved that way). Keep the FX
   tasteful; the reviewers flagged anything that read as a glitch (blown wheels, halos).
6. **End card.** Car name, offer lines, the price whole and clear of the car, TEXT OR DM TO BOOK,
   the phone for the ad's city, the site and @SUPERCAR_EXPERIENCE_, plus the requirements line.
7. **Sound.** The clip's own music, continuous and never chopped at cuts, extended by whole bars if
   it's short (no time-stretch). Designed accents (ticks, whooshes, impacts) sit about 45% under it, and the
   music drops into its own tape stop before the end-card hit. -14 LUFS, true peak <= -1.5 dBTP,
   last 50 ms silent (`audio/bed_music.py`).
8. **Process.** Every figure is sourced, copy passes SlopMonster 5/5, then review under four lenses
   (claims, brand, legibility, craft) until nothing is blocking. Deliver **one Instagram-ready file per edit**
   (9:16 two-pass ~11.5 Mb/s, H.264 High, AAC 48 kHz, fast start) and nothing else: Omarie, 28 Sept 2026, "I just
   need Instagram ready reels for these edits, I don't need 2 videos per video". No separate master.

**Feed cuts: 4:5 and 1:1.** Approved by Omarie on 2026-09-27 on ROOF DOWN ("approve video"). Get the 9:16
approved first, then cut the feed sizes from the same build: `python3 build.py --format 4x5` or `--format 1x1`
(`750s-spider-locked-on/`, windows in `lib/formats.py`). The edit, plate, sky matte, graphics timing, copy and
sound stay those of the 9:16.
- **4:5** (1080×1350) is a straight crop of the 9:16 (plate y 228–1578). Every 9:16 line sits in the story safe
  zone (y 269–1536), which fits, so nothing is moved or redrawn.
- **1:1** (1080×1080) gets its own hook panel and end card (`front_1x1.html`); every other frame reuses the
  approved 9:16 graphics. Keep the car whole: where it drives at the lens, drop the picture lower than the
  graphics (ROOF DOWN's hook and front 3/4 pass), and move the window on a tracked lock-on so the brackets stay
  in frame.
- Once a size is approved, pin its SHA-256 in `lib/formats.py` `APPROVED`: the build then refuses to re-encode
  over it without `--force`. Don't edit the approved 9:16 front page for a feed cut. Changing it re-renders
  that layer, and Chromium's text raster isn't bit-for-bit repeatable.

**Use `quick-promo` instead** only when the ad has to go out in under ~30 minutes. `locked-on`
takes a few hours of build and review.

## THE STANDARD for vlogs: `locked-on` vlog

**Made the vlog standard by Omarie on 2026-09-27:** "This is the standard for making vlogs." Every SE vlog
starts from this build unless the job says otherwise. Style guide page (Vlog and How it was made
sections): https://claude.ai/artifact/WCe1qHhTrMDw7bkDaskeQm.

The vlog standard is built on the Sep 15 Egnyte rally (`10-vlog-locked-on/2026-09-15-rally-v2/`,
components and 22 variations in `10-vlog-locked-on/vlog-kit/`, codes A1–I3). On top of the eight rules:
survey and transcribe every clip before cutting and pick moments by what people say; keep the day in
order and stamp each chapter with the camera clock; keep the SE banner on the side (A2 edge tab,
right edge between 14% and 55%); tag a car only when it is positively identified in frame and release
the tag with LOCK LOST when the car leaves on a pan; caption every line (H1); check who is speaking
before labelling a quote; label guests by company only (EGNYTE GUEST), never by name, and show a client
as text, never their logo; duck the music about 11 dB under all speech. Deliver one Instagram-ready video per
vlog (28 Sept 2026: no second video); the no-music version and the music stem stay in the build unless he asks. Never use passwords, speed talk, unsafe-driving talk, fleet faults, weapons
or anything someone asks to have taken out. The style guide page has a Vlog section.

**How a vlog is made now (the fast path, 2026-09-27).** Omarie asked for the 6 h 45 min Sep 15 process to be "extremely
faster without cutting performance". The fast path goes like this:
1. `10-vlog-locked-on/engine/vlog.py links → ingest → index` surveys the day from Dropbox unattended.
   - It streams every clip once and keeps only audio and keyframes, so no original sits on disk.
   - It writes transcripts, HOST/OTHER speaker labels, ranked moments (`moments.md`) and never-use flags (`flags.json`).
2. Cut from `moments.md` and check each pick against `flags.json`.
3. `vlog.py plan → fetch` pulls only the byte ranges the cut uses.
4. In the day's build folder, run `./render.sh --draft` for a 540×960 review cut. Gates run first: lock-on, caption
   swaps, blocked shots, caption sync, loudness and quote-card speaker.
5. Run `./render.sh` for the full-quality render. Review fixes re-render only what they touch.

Measured on Sep 15:

| step | before | now |
|---|---|---|
| survey (169 GB, 46 clips) | 80 min | 19 min |
| moments and flags | 30–40 min by hand | 103 s |
| full render | about 27 min | about 18 min |
| lock-on fix re-render | 25–35 min | about 4.5 min |
| review draft | none | about 2 min |

The new master scores at least as well as the approved one (SSIM 0.9918 against 0.9912 on its own source), and the
mix is bit-identical.

---

## Approved layouts

Two treatments are approved and **equal**. Pick per job, on the footage — not by
rule.

### `hud` — the house look

Bracketed title block bottom-left with the FD monogram inside it, ticker beneath,
left-aligned type in a mid band.

Signed off on the **McLaren 765LT** and the **Aventador S** base cut. What was
approved is the *treatment itself* — the title block, ticker and mid-band type.
It is not tied to what fills the type band: the 765LT ran an animated spec
counter and indexed callouts, the Aventador a static build sheet, and both were
fine. Fill the band with whatever the car's material supports.

### `centred` — poster treatment

Mark above the hook, everything on the vertical axis, lockup centred at the foot.

Signed off on the **Aventador S**, called "very fitting". Approved on par with
`hud`, not a fallback.

### The other two

`panel` and `rail` are built and available in `layouts.py` but have **not** been
signed off. `panel` remains the right technical answer for footage so busy or
bright that nothing else stays legible — it ignores what is underneath — so
reach for it on that basis, not on preference.

### `quick-promo` — the quick story ad for promotions

Approved by Omarie on 2026-09-26 as **the** treatment for quick story ads for promotions:
"I approve those ads for when we need quick story ads for promotions." It was signed off on
three stories cut the same morning: the Huracán STO 2-hour flash special, the GT3 RS
(5 hours, $1,200 out the door) and the AMG GT Black Series (5 hours, $800 out the door).

It is a 15 s 9:16 story in six beats, each carried by an HTML motion layer rendered frame by
frame over a plate cut from one Dropbox clip:

| Beat | Time | Shot | On screen |
|---|---|---|---|
| Hook | 0–1.5 s | strongest car shot; first frame must work as the preview | SUPERCAR EXPERIENCE tag, gold line + white FLASH SPECIAL slam, gold stripe wipe; bottom scrim |
| Brand | 1.5–2.9 s | the maker's badge in the footage | black panel top band: year · class tag, brand in white; gold corner brackets lock on the badge |
| Model | 2.9–4.4 s | model badge / script, or a full car shot | model slides up in gold under the brand |
| Offer | 4.4–7.4 s | moving shots, panel over them | time window with a filling bar, or hours + price + OUT THE DOOR |
| Requirements | 7.4–10.4 s | moving shots, panel over them | TO DRIVE IT, YOU NEED · VALID DRIVER'S LICENSE · AGE 21+ · INSURANCE, gold checks |
| End card | 10.4–15 s | a calm or locked-off shot | stacked SE logo, then the panel: ends-time line, CALL OR DM TO BOOK, phone in gold, site + handle |

Code and how to make the next one: `flash-special-quick-cut/` (README). `story2.html` is the
config-driven version: add a car to its `CARS` block and its cut list to `plate.py`.
It takes about 15 minutes per ad, most of it choosing cut points on real frames.

---

## Rules learned the hard way

Each of these cost a render or a rebuild. They apply to any new layout.

**Never stand the four-colour accent stripe on end.** It carries a black segment
(see `01-brand-core/BRAND-SPEC.md` §1). Horizontally on dark footage that reads
as a designed gap; vertically it reads as a broken line, like a rendering fault.
`rail` uses solid red and keeps the stripe as a horizontal cap.

**The ticker sits at `y=0.775`.** Any layout placing a lockup near there will
collide. `rail` sits at `0.688`, `centred` at `0.845`.

**Measure the footage before choosing a treatment.** Sample mean brightness in
the band each element will occupy, across the whole clip, before committing:

- 765LT: dark throughout, so type went in the upper third with light scrims.
- Aventador: top band swung 23 → 239 (blown desert sky to black interior), so
  there is **no corner logo bug** — neither white nor black survives both ends —
  and the type moved to the mid band, the stable zone at mean 59.

**No corner logo bug on footage with a wide brightness swing.** The monogram
lives inside the scrimmed title block instead. Established on the Ferrari Roma
edit, held on both ads since.

**Callouts need a shot that lasts.** A leader line anchored to the car is invalid
at the next cut. Fine on the 765LT's single locked-off take; dropped on the
Aventador, which cuts roughly every second.

**Type carries a scrim wherever the shot changes underneath it.** Same fix
`AUTO-EDIT.md` prescribes for the GT3 RS.

**Keep the music if the source video has any.** Omarie, 2026-09-26: "Keep music as well if
the videos ever have any." Play the clip's own audio continuously from one start point, not
chopped at every picture cut, and lay the designed accents (impacts, whooshes, ticks) under
it at about 45%. A synthesised pad or drone would clash with the music, so drop it. Use a
fully synthesised bed only when the source is silent. `flash-special-story/build_story.py`
implements this (`--music-start`, `--no-music`).

**Match the phone number to the ad's city.** `brand-tokens.json` `brand.phone` is the
Scottsdale line. Use `brand.phones.text` (the site-wide text line) unless the ad is for one
city, and then use that city's line.

---

## Copy and claims

**Only put on screen what the shop can substantiate.** Both ads shipped with this
enforced:

- The 765LT's tuned column (902 HP / 701 lb-ft / 2.4 s) is **invented for
  layout** and flagged in that ad's README as replace-before-publish. Its heading
  reads "BUILD SHEET", not "DYNO VERIFIED", precisely because nothing is verified.
- The Aventador lists only confirmed work — aero kit, wheels, Stage 1 tune,
  lowered — and carries **no horsepower figures**, because there is no dyno sheet
  for that car.

A callout naming a part reads as a claim about what the shop fitted. Confirm
against the real build before publishing.

Hooks come from `05-copy-library/hooks-and-captions.md`, CTAs from
`03-overlays/cta-captions/`, grouped by intent as `fd_brand.CTA_GROUPS`
describes. `06-video-system/AUTO-EDIT.md` maps templates to CTAs.

---

## The three axes of variation

An ad folder can vary along three independent axes, all as cue files:

| Folder | Varies | Keeps |
|---|---|---|
| `layouts/` | the arrangement on the frame | cut, copy |
| `cuts/` | shot order, length, beat structure | copy, layout |
| `variants/` | hook and CTA | cut, layout, build sheet |

Keeping them separate is deliberate: a test on one axis stays interpretable.
`python3 build_ad.py --all` renders every combination present.

---

## Feedback log

| Date | Ad | Note |
|---|---|---|
| 2026-09-08 | McLaren 765LT, Aventador S base | "I love the very first video" — approved the `hud` treatment itself, independent of counters vs build sheet |
| 2026-09-08 | Aventador S, layout variations | "the third was very fitting" — `centred` approved, on par with `hud`, chosen per job |
| 2026-09-26 | SE flash-special quick cuts: Huracán STO, GT3 RS, AMG GT Black Series | "That was amazing", then "I approve those ads for when we need quick story ads for promotions" — `quick-promo` approved as the go-to for promo stories |
| 2026-09-26 | Polished STO flash special (HUD lock-on) | "These animated graphics are way better... keep these up. I wanna implement these in my vlogs too" — the animated HUD level is the bar; vlog versions to follow. Also: "Keep music as well if the videos ever have any" |
| 2026-09-26 | GT3 RS showcase "LOCKED ON" (tracked lock-on, type behind the car, kinetic price reel, clip music) | "Approved" — the showcase techniques are signed off for SE ads |
| 2026-09-26 | GT3 RS showcase "LOCKED ON" | "That is amazing make that a standard" — `locked-on` is now THE standard for SE ads (section at the top) |
| 2026-09-27 | Sep 15 rally vlog rebuilt from raw footage (v2) | "This is the standard for making vlogs" — the v2 build, the vlog kit and the process on the style guide page are now THE vlog standard (section near the top) |
| 2026-09-27 | Sep 15 rally vlog rebuilt from raw footage (`10-vlog-locked-on/2026-09-15-rally-v2/`, kit in `vlog-kit/`) | "This is great, a few minor changes but this is overall 99% great" — the rebuilt vlog and the vlog kit are the bar for SE vlogs; "how it was made" added to the style guide page. Minor changes pending |
| 2026-09-27 | Sep 15 rally vlog with the Locked-On layer (`10-vlog-locked-on/2026-09-15-rally/`) | "That was great save this" — saved to Dropbox `/Supercar Experience/05 Vlogs/`. Next ask: rebuild the vlog from the raw footage with vlog-specific Locked-On variations, keeping the SE banner on the side, and catch the key moments (team dinner, guests on how they enjoyed it, leading the convoy on the freeway) |
| 2026-09-27 | McLaren 750S Spider "ROOF DOWN" (`750s-spider-locked-on/`, the second `locked-on` build: SPIDER rises out of the sky behind the car as the roof stows, then the price rises from behind it) | Approved for ads, with every open question signed off (the clip's own music among them) and the defaults kept: one day grade on the sunlit desert footage, the text line on Las Vegas footage. Not posted |
| 2026-09-27 | ROOF DOWN 4:5 and 1:1 feed cuts | "approve video". The feed-cut recipe is under THE STANDARD. Not posted |
| 2026-09-28 | ROOF DOWN deliveries | "I just need Instagram ready reels for these edits I don't need 2 videos per video" — one Instagram-ready file per edit from now on (rule 8 and the vlog rules); the build no longer writes a master |
| 2026-09-28 | Every session and branch | "make sure every session/branch/everything knows and implements it no matter what when creating any work but ask beforehand what style should be used" — ask which style first (a click), then build it fully (THE STANDARD) |
| 2026-09-28 | Now Boarding and Paste-Up looks on ROOF DOWN | Two more graphics packages asked for ("impress me... give them unique names and store them in the same artifact"); proposed, not approved; on the style guide page |
| 2026-09-28 | Locked-On style guide page | "My locked on artifact is my standard for any work I work on" — the page is the standard for every job in every workstream, each in its own brand. The page now has the feed cuts and the day-grade rule from ROOF DOWN (version 5) |

Add a row when the shop reacts to something. This file is the reason a future ad
does not have to re-litigate a settled look.
