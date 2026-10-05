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
| 11–19 | 22–37 s | White card "Booking request received.", the race-weekend pass builds in the SE Concierge booking window, THU · FRI · SAT day bars, "HI, I'M REV!", "Pull the fleet for race weekend.", the Las Vegas fleet list with AVAILABLE ticks, booking kit, sector keyframes |
| 20–26 | 37–49.6 s | "Map the drive from pickup to the Strip.", ROUTE! slam, "Mapped.", map island builds, "Pulling every stop…", route map with 5 pins, photo cards, cursor click |
| 27–30 | 49.6–60 s | Semi whips past the GT3 RS, "Hold the GT3 RS for race weekend.", glow-ring reveal, RACE WEEKEND poster with badge stamp |
| 31–35 | 60–76.5 s | "Lock it in and send the confirmation!", AMG speed cut, "Looks perfect! Booked." text, REV hops with the booking line, end card |

`shots.json` holds every shot: timing, the reference shot, our shot, the animation moves, and the footage source + in-point.

## Files

```
src/
  Ad.tsx       the edit: one <Sequence> per shot, the T[] timing table; plays public/audio/soundtrack.wav
  theme.ts     palette, fonts, s2f(), easing helpers
  core.tsx     Plate (footage + push/drift/grade/shake), TextBubble, PromptBar, StatusCard, FloatWords, Flash, Bokeh, HandleBug, Finish
  pixel.tsx    REV sprite + morphs (coupe, wedge), PixelFire, Sparks, PixelCode
  editor.tsx   Badge (staged build), EditorChrome, LayerStack, KeyframeStreak, ProjectPanel, AssetBoard
  map.tsx      MapIsland (Las Vegas valley), MapBuild, MapFull (pins, photo cards, cursor)
  poster.tsx   GlowReveal, Poster, TitleLockup, EndCard
audio/synth.py    generates music.wav (76.5 s bed) and the synth SFX into public/audio/ (all original, numpy only)
sfx/events.json   spotting list for the SFX engine: every on-screen event, frame-exact, taken from the animation code
sfx/cuesheet.md   engine output: every sound placed and every event skipped, each with its reason (rules R1–R23)
sfx/cues.json     the same as data, plus loudness, density and per-cue audibility
tools/cut_plates.py  cuts public/plates/sNN.mp4 from the raw clips using shots.json
tools/finish.py      masters the sound (house limiter, -14 LUFS, last 50 ms silent) and writes the one Instagram file
public/brand/     SE logo + monogram, vectorised from the overlay-kit PNGs
public/stills/    frames used by the map cards and the poster
```

Not in git (regenerate them): `public/plates/`, `public/audio/`, `raw/`, `out/`, `node_modules/`.
`public/audio/soundtrack.wav` comes from `npm run sfx`, which needs the engine and sound library in `~/.local/vlogtools/sfx/`
(on this Mac only). Without it the render has no sound.

## Set up and render

```bash
cd supercar-experience/09-campaign-ads/f1-weekend-remake
npm install
npx remotion browser ensure          # headless Chrome for rendering
pip install numpy && npm run audio   # writes public/audio/*.wav
mkdir raw                            # copy the 8 clips listed in tools/cut_plates.py out of Dropbox (copy, never move)
npm run plates                       # writes public/plates/s01..s34.mp4
npm run sfx                          # SFX engine -> public/audio/soundtrack.wav + sfx/cuesheet.md (needs uv)
npm run sfx:check                    # re-measures every cue in the rendered audio: timing, level, audibility
npm run studio                       # live preview with a timeline; or:
npm run still -- --frame=1680        # one frame
npm run render                       # full master, ~13 min on 2 cores
npm run finish                       # -> out/..._IG.mp4: -14 LUFS, true peak <= -1.5, house Instagram encode
```

`cut_plates.py` lists exactly which clip is missing and its Dropbox path if `raw/` is incomplete. The short names it
expects: `sto.mp4, amg.mov, mcl750.mov, sf90.mov, urus.mp4, gt3_white.mov, gt3_livery.mov, rally1.mov`.

## Editing

- **Change a shot's timing or footage:** edit `shots.json` (`src`, `ss` in-point, optional `speed`), re-run
  `python3 tools/cut_plates.py --raw raw --only <id>`, and keep `T[]` in `src/Ad.tsx` in step with `t0/t1`.
- **Change words:** they all live in `src/Ad.tsx` (prompts, captions, bubbles) and `src/poster.tsx` (title, poster, end card).
- **Swap the hero car:** the poster and the prompts name the GT3 RS; the stills are `public/stills/gt3_*`.
- **Sound:** see *SFX engine* below. To change what gets a sound, edit `sfx/events.json` and run `npm run sfx`; the music bed is shaped by `sections` in `audio/synth.py`.
- Instagram file: `npm run finish` (HOUSE-STYLE rule 8: one Instagram-ready file per edit, two-pass ~11.5 Mb/s).

## SFX engine

`~/.local/vlogtools/sfx/engine.py` (shared tool, outside this repo) places every sound effect. Made 2026-10-05.

- **Input:** `sfx/events.json`, the spotting list. Each entry is a shot, the shot-local frame, the kind of event
  (`stamp`, `bubble`, `typing`, …) and, for anything that springs in, its `[damping, stiffness]`. The engine works out
  the frame it lands on from the spring. `cuts` flags which cuts are `section`, `whip`, `speed` or `punch` cuts.
- **Sounds:** only sounds we own. The synth set in `public/audio/` plus 10 cut from the Formula Dynamics PPF ad
  (`~/.local/vlogtools/sfx/lib/higgsfield_ppf/`), measured once into `~/.local/vlogtools/sfx/palette.json` by `palette.py`.
- **Rules:** `~/.local/vlogtools/sfx/research.md` (R1–R23, with sources). The engine's rule table maps each event kind to a
  sound role, priority and level over the music. It then:
  - groups bursts to first + last (R9);
  - sounds only flagged cuts (R7);
  - clears small sounds out of a hero hit's window (R10);
  - caps a repeating move (R8);
  - puts each sound's hit, not its file start, on the frame (R1–R4);
  - sets levels against the music in the phone band;
  - adds a mid crack under sub-heavy hits so phones hear them (R15);
  - dips the music under heroes (R14);
  - finally checks every cue for masking on the real render, raising or dropping it (R10).
- **Output:** `public/audio/soundtrack.wav` (music + SFX, −14 LUFS), `sfx/cuesheet.md`, `sfx/cues.json`, `sfx/sfx_stem.wav`.
- **Reference timing:** an optional `sfx/reference.json` (hits learned from the Higgsfield reel) promotes events the reel
  also sounds. Timing only; no reel audio is used.
- **Spotting render:** `npx remotion render src/index.ts RaceWeekend sfx/gfx.mp4 --scale=0.25 --props='{"gfxOnly":true}'` blanks the
  footage and grain (`GFX_ONLY` in `src/core.tsx`) so motion analysis sees only the graphics.

## Open items before posting

1. ~~Age line~~ **Done 2026-10-05.** End card now reads `RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE` /
   `VALID DRIVER'S LICENSE · INSURANCE` (supercarexp.vip wording, checked 2026-10-05; Omarie picked it).
2. ~~Drive times~~ **Done 2026-10-05.** Dropped (unchecked estimates): cards show stop names only, chips are
   5 STOPS · 1 ROUTE, status line "Five stops. One route."
3. **House QA.** SlopMonster 5/5 on the on-screen copy (138 words, 2026-10-05). Sound since 2026-10-05: the engine's
   soundtrack (see `sfx/cuesheet.md`), mastered by `npm run finish`. Still to do: a full-speed watch-through of the finished file.
4. **Footage notes:** shot 6–10 use the SF90 clip, which isn't on the Vegas rental list. It is never named on screen;
   keep it that way. Shot 21 is the rally day-1 selfie, slowed to half speed.
5. 9:16 only. The reference was 16:9; a landscape cut needs its own layout pass.
