# Flash special story: Lamborghini Huracán STO (polished cut)

This is a 15.5 s Instagram/Facebook story (9:16, 1080x1920, 24 fps) for a two-hour flash special on the
Lamborghini Huracán STO. It runs today, 2026-09-26, from 11 AM to 1 PM. It uses the house `hud` treatment
in motion. The whole edit is specified in `cue.md`, which also lists every place the build departs from the
judge's cue and why. The quick cut in `../flash-special-quick-cut/` went out first. This version replaces it.

**Deliverable:** `exports/SCE_Lamborghini-Huracan-STO_Flash-Special-11AM-1PM_15s-9x16.mp4`. The file is H.264
High, yuv420p BT.709, CRF 17, with AAC 48 kHz stereo audio at 192k, faststart, and measures −14.2 LUFS. The MP4
is not committed (house rule), so share it as a download. True peak is −1.4 dBTP. The stills, the poster and the contact sheet are kept
in `exports/`.

**Posting:** the copy says TODAY and ENDS 1PM PT and gives no date. Post it by about 11:00 AM PT and delete or
expire it at 1 PM PT. Don't repost it on another day.

## Beats

| t (s) | Shot | On screen |
|---|---|---|
| 0.00–1.83 | STO driving at camera, night | **2-HOUR** / **FLASH SPECIAL** / ENDS TODAY · **1PM PT** |
| 1.83–2.79 | LAMBORGHINI crest close-up (whole take, 1.0x, strobe removed) | brackets lock on the crest; tag: BRAND / LAMBORGHINI |
| 2.79–4.46 | 'STO' lettering on the carbon deck | brackets lock on the badge; MODEL · 2023 / HURACÁN STO |
| 4.46–5.83 | STO front-on through the city | RENTAL FLASH WINDOW · TODAY: an 11AM → 1PM bar fills and lands on the cut. The title block and ticker come in here |
| 5.83–8.29 | side profile, then wide roll-by | 1PM turns gold on the cut, then REQUIREMENTS: 01 VALID DRIVER'S LICENSE · 02 21+ · 03 INSURANCE |
| 8.29–10.13 | STO head-on under the canopy, slow push | no type (the hero shot, clean) |
| 10.13–13.04 | STO parked at the Las Vegas Convention Center | **BOOK BEFORE 1PM PT** / CALL FOR THE FLASH RATE / **(888) 678-6079** |
| 13.04–15.50 | black end card | SE stacked logo / RENTAL FLASH SPECIAL / **ENDS TODAY · 1PM PT** / SUPERCAREXP.VIP / (888) 678-6079 / @SUPERCAR_EXPERIENCE_ |

## Where each on-screen claim comes from

| Line | Source |
|---|---|
| 2-HOUR FLASH SPECIAL · ENDS TODAY · 1PM PT · 11AM – 1PM PT TODAY · BOOK BEFORE 1PM PT | Omarie's brief: "a two hour flash special till 1 o'clock on our rental car", today. PT is the brief's time zone |
| RENTAL FLASH SPECIAL · RENTAL FLASH WINDOW | Omarie's brief ("on our rental car") |
| CALL FOR THE FLASH RATE | a call to action; it names no figure |
| VALID DRIVER'S LICENSE · 21+ · INSURANCE | Omarie's brief, word for word except for the added possessive |
| LAMBORGHINI · HURACÁN STO | `01-brand-core/brand-tokens.json` label "LAMBORGHINI HURACAN STO" (with the accent restored). The crest and the STO badge also appear in the footage |
| 2023 · LAS VEGAS | brand tokens ("2023 - Exotic - Las Vegas"). The site lists "2023 Lamborghini STO" |
| SUPERCAREXP.VIP · (888) 678-6079 · @SUPERCAR_EXPERIENCE_ | brand tokens |

The ad shows no discount, dollar figure, price, spec or countdown number, because the client gave no figure.
The regular $999 / 4 HRS rate is left off on purpose, since it would confuse a "special". The timeline bar fills
once as a graphic and is not a clock. The copy scored 5/5 on SlopMonster.

**Before posting, confirm with Omarie:**

- **Location.** "LAS VEGAS" comes from the car's listing and "PT" from the brief. SE also lists the 2023 STO in
  Scottsdale and Boise, and Boise is on Mountain time. If the special covers every location, drop "LAS VEGAS" from the
  title block (`R.titleSub`) and restate the time for each market.
- **21+.** The site says "Renter Must Be 25+ (Ages 21–24 With $299 Underage Fee)". "21+" is Omarie's own wording, so it
  stays as written. If he wants the fee shown, a small line such as "21–24 UNDERAGE FEE APPLIES" (quoted from the site)
  fits under row 02. Either way, staff should mention the fee on calls.
- **The flash rate.** No rate is named on screen, so staff need to know it when people call or DM.

Third-party marks behind the ask (the IBIE trade-show banner, its sponsor logos, a door sign and a poster face on the
Las Vegas Convention Center) are darkened and defocused in the build, so the ask frame carries no other brand.

## Footage and sound

The footage is SE's own STO reel (`STO.mp4`, from Dropbox `Supercar Experience/01 Car Footage/`). It is
1080x1920 at 24 fps in 10-bit H.264. The build converts it to 8-bit and applies only the house STO grade:
contrast 1.04, saturation 0.96 and a vignette. Two shots get extra treatment, done in 16-bit before the grade:

- The crest close-up has a light strobe baked in, so each frame's brightness is matched to the take's average.
- The parked shot at the convention center has white-balance jumps from the reel's grade, so every frame is matched
  to its blue-white state.

The reel's audio is **not used**, because nobody knows where it came from and the edit reorders the shots.
Instead, `build_story.py` synthesises an original sound bed with a fixed seed. It is voiced for phone speakers: a
mid-range pad, impacts on the hook and the end card, whooshes into each cut, lock ticks, the fill sweep and a bell,
a riser into the ask and a pop on the CTA. The ad also reads fully with the sound off. The client can swap in
Instagram music in the story composer. If Omarie confirms the reel audio is licensed for ads, `cue.md` §5
describes an alternate master that uses it.

## Re-render

```bash
python3 build_story.py                        # everything: plate, overlay, audio, encode, QA (~4 min)
python3 build_story.py --src /path/to/STO.mp4 --ffmpeg /path/to/ffmpeg
python3 build_story.py --skip-plate           # after editing story.html only
python3 build_story.py --skip-plate --skip-overlay   # after editing the audio only
node render_overlay.js --times 3.9,12.2 .work/spot  # spot-check overlay frames (transparent PNGs)
```

- `story.html` is the motion-graphics layer. `window.renderAt(t)` sets every element for time t as a pure
  function, with no CSS animation, no transitions, no rAF and no clock. It places text by cap top from font
  metrics measured at load. Fonts come from `../../07-fonts/` and logos from `../../02-logos/png/`. You can
  open it in a browser and call `renderAt(5.9)` from the console.
- `render_overlay.js` screenshots it frame by frame with a transparent background, using 4 pages in parallel.
- `build_story.py` cuts and grades the plate (the ranges are in `BEATS`). It tone-locks B2 and B8, cleans the
  convention-center facade (`b8_cleanup`), applies the B6 push and adds the black end-card frames. It then renders
  the overlay and converts every frame to RGBA, synthesises and loudness-normalises the bed, composites and encodes.
  Last, it writes the QA stills (`exports/still-SS_CCs.jpg`, meaning seconds_centiseconds), the poster
  (t = 1.0 s), the contact sheet and a safe-zone report. It also runs a sync check that compares MP4 frames with
  plate plus overlay, and saves stream info to `.work/probe.json`.

Scratch files go in `.work/`, which is gitignored.

## Changing the end time or the copy

All the copy is in `story.html`, in `build()`. To move the end time (for example to 2PM), change these strings:

- hook: `ENDS TODAY · <span class="g">1PM PT</span>` (`R.h3`)
- ticker: `11AM – 1PM PT TODAY` (`tickerHTML`)
- readout labels: `11AM` (`R.l11`) and `1PM` (`R.l1`)
- ask: `BOOK BEFORE <span class="g">1PM PT</span>` (`R.ask1`)
- end card: `ENDS TODAY · 1PM PT` (`R.endH`)

Then run `python3 build_story.py --skip-plate` and look at the stills. Lines are left-aligned from x 7.5%, so a
longer line grows to the right. Keep type inside x 80%: "BOOK BEFORE 1PM PT" (Bebas 120) ends at x 79% today, so something
like "BOOK BEFORE 12:30PM PT" would need a smaller size. If the window is no longer two hours, change "2-HOUR" in
the hook (`R.h1`) and in the ticker too. Run any new copy through SlopMonster, but don't rewrite the client's
own words.
