# `f1-weekend-remake`: SE remake of the Higgsfield × Claude Opus 5.5 reel

A 76.5 s, 9:16 Supercar Experience ad that follows the Higgsfield MCP motion-design reel shot for shot (35 shots,
same timings), built in code with Remotion over SE's own car footage. Made 2026-10-04 in a chat session; Omarie's
reaction: "this was actually amazing". Not yet marked approved for posting.

- Storyboard (every Higgsfield shot next to the matching frame of this ad): https://claude.ai/artifact/UpQ9XkvM3gA4FDHTjmsLAT
- Rendered file: `SCE_F1-Weekend_Remake_76s-9x16.mp4` was delivered in that chat (the master is not in Dropbox yet).
- Look: SE gold (#F2C500) on black. Mascot **REV** is an original pixel supercar, not the reference's cat.

## Story (acts)

| Shots | Time | What happens |
|---|---|---|
| 1–3 | 0–8 s | Title lockup (SUPERCAR EXPERIENCE × REV, F1 WEEKEND, "for Las Vegas"), the Sphere, the STO on the Strip |
| 4–10 | 8–22 s | Client text "Need a supercar for F1 weekend. ASAP." REV pops in, morphs coupe → spider, pixel fire, pixel code, "Wait / No / Let me book it", prompt bar |
| 11–19 | 22–37 s | White agent card, SE race badge builds in an editor window, layer stack, "HI, I'M REV!", project files, asset board, keyframe streaks |
| 20–26 | 37–49.6 s | "Map the drive…", ROUTE! slam, map island builds, route map with 5 pins, photo cards, cursor click |
| 27–30 | 49.6–60 s | Truck whip, "Create a hero poster of the GT3 RS", glow-ring reveal, THE GT3 RS poster with badge stamp |
| 31–35 | 60–76.5 s | "Render the final…", AMG pass, "Looks perfect! Booked." text, REV hops with the booking line, end card |

`shots.json` holds every shot: timing, the reference shot, our shot, the animation moves, and the footage source + in-point.

## Files

```
src/
  Ad.tsx       the edit: one <Sequence> per shot, the T[] timing table, sound cues
  theme.ts     palette, fonts, s2f(), easing helpers
  core.tsx     Plate (footage + push/drift/grade/shake), TextBubble, PromptBar, StatusCard, FloatWords, Flash, Bokeh, HandleBug, Finish
  pixel.tsx    REV sprite + morphs (coupe, wedge), PixelFire, Sparks, PixelCode
  editor.tsx   Badge (staged build), EditorChrome, LayerStack, KeyframeStreak, ProjectPanel, AssetBoard
  map.tsx      MapIsland (Las Vegas valley), MapBuild, MapFull (pins, photo cards, cursor)
  poster.tsx   GlowReveal, Poster, TitleLockup, EndCard
audio/synth.py    generates music.wav (76.5 s bed) and every SFX into public/audio/ (all original, numpy only)
tools/cut_plates.py  cuts public/plates/sNN.mp4 from the raw clips using shots.json
public/brand/     SE logo + monogram, vectorised from the overlay-kit PNGs
public/stills/    frames used by the map cards and the poster
```

Not in git (regenerate them): `public/plates/`, `public/audio/`, `raw/`, `out/`, `node_modules/`.

## Set up and render

```bash
cd supercar-experience/09-campaign-ads/f1-weekend-remake
npm install
npx remotion browser ensure          # headless Chrome for rendering
pip install numpy && npm run audio   # writes public/audio/*.wav
mkdir raw                            # copy the 8 clips listed in tools/cut_plates.py out of Dropbox (copy, never move)
npm run plates                       # writes public/plates/s01..s34.mp4
npm run studio                       # live preview with a timeline; or:
npm run still -- --frame=1680        # one frame
npm run render                       # full master, ~13 min on 2 cores
```

`cut_plates.py` lists exactly which clip is missing and its Dropbox path if `raw/` is incomplete. The short names it
expects: `sto.mp4, amg.mov, mcl750.mov, sf90.mov, urus.mp4, gt3_white.mov, gt3_livery.mov, rally1.mov`.

## Editing

- **Change a shot's timing or footage:** edit `shots.json` (`src`, `ss` in-point, optional `speed`), re-run
  `python3 tools/cut_plates.py --raw raw --only <id>`, and keep `T[]` in `src/Ad.tsx` in step with `t0/t1`.
- **Change words:** they all live in `src/Ad.tsx` (prompts, captions, bubbles) and `src/poster.tsx` (title, poster, end card).
- **Swap the hero car:** the poster and the prompts name the GT3 RS; the stills are `public/stills/gt3_*`.
- **Sound:** cues are the `at(shot, frame, file, volume)` lines in `src/Ad.tsx`; the bed is shaped by `sections` in `audio/synth.py`.
- Instagram upload copy: re-encode the master at CRF 25 to get under ~26 MB.

## Open items before posting

1. **Age line.** The end card says `21+ · VALID DRIVER'S LICENSE · INSURANCE` (as in the approved Locked-On GT3 RS
   ad). The race-weekend set and the Dropbox notes use **DRIVERS 25+**. Confirm which one with Omarie, then fix
   `src/poster.tsx` and re-render.
2. **Drive times on the map** (30 / 25 / 5 / 35 min) are estimates, not looked up. Check them or drop the times.
3. **Not yet run through the house QA** in `../HOUSE-STYLE.md`: −14 LUFS (the render measures −12.8 LUFS integrated),
   true peak, slopmonster on the copy, a full-speed watch-through.
4. **Footage notes:** shot 6–10 use the SF90 clip, which isn't on the Vegas rental list. It is never named on screen;
   keep it that way. Shot 21 is the rally day-1 selfie, slowed to half speed.
5. 9:16 only. The reference was 16:9; a landscape cut needs its own layout pass.
