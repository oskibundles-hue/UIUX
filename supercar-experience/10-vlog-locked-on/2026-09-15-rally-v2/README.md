# Rally vlog v2, Sep 15 (Egnyte rally day): rebuilt from the raw footage, Locked-On for vlogs (9:16)

**What it is.** Omarie Young's ask: "remake the whole video from scratch using our raw footage… make the video and the
dynamic motion graphics like you did here and the overlays… catching all key moments… show me your skills like you did the
Porsche video but in vlog format… I still want the Supercarexperience banner on the side". Omarie added on 27 Sept that the
rally was for **Egnyte**: the name appears as text only (no Egnyte marks anywhere). This folder renders the approved edit
decisions (the EDL, 174.5 s) at the `locked-on` standard (`../../09-campaign-ads/HOUSE-STYLE.md`): a new picture edit and grade
from the camera files, a new sound mix, and a Locked-On layer built from the vlog kit (`../vlog-kit/`) plus this vlog's own
components. **Status: not reviewed yet.**

__EXPORTS__

## What is on screen

__ONSCREEN__

Every in / out time and how each anchor was found: `cue.md`. All copy lives in `config.json` (`layer.comps`).

## Every on-screen line and its source

| Line | Source |
|---|---|
| SUPERCAR EXPERIENCE × EGNYTE · RALLY DAY (hook eyebrow) | the brief; EGNYTE: Omarie, 27 Sept ("the rally was for the company Egnyte"), text only |
| THE RALLY / LAS VEGAS · SEP 15 2026 (hook title) | the approved v1 hook ("THE RALLY,"); the place (Venetian, Red Rock) and the date are the camera files' (DJI_20260915…) |
| SE lockup, stacked SE logo, SE mark | `02-logos/png/` |
| SUPERCAR EXPERIENCE · RALLY DAY · LAS VEGAS (side banner) | the vlog kit's A2 banner copy |
| HH:MM · CH 0N / 07 and the chapter titles | titles: the EDL (`chapters`); CH 03 is EGNYTE ARRIVES (Omarie, 27 Sept). Clocks: the camera clock of the chapter's first frame = the file name's start time + the shot's in-point (see "Clocks" below) |
| OMARIE · @NQ.YOUNG | the approved follow card ("Omarie Young @nq.young") |
| CAR 0N / 05 + LAMBORGHINI URUS, CORVETTE Z06, LAMBORGHINI HURACÁN EVO, PORSCHE 911 GT3 RS, ROLLS-ROYCE CULLINAN | Omarie naming the lineup on camera ("Black Series, Uruses, Corvette, Huracán EVOs, GT3s, Rolls-Royce Cullinan"), each label only on the car that is in frame and identified on the footage (see "Lock-ons") |
| TEXT OR DM TO BOOK · (725) 425-3583 · @SUPERCAR_EXPERIENCE_ (CTA chip) | the approved Locked-On end card and `brand-tokens.json` `phones.text`; shown while Omarie says "If you ever need to book with us for a large event…" |
| SAFELY. | Omarie's own word ("That's our number one thing. Safely."), on the word |
| LOCKED ON · AUDI R8 | Omarie: "you'll get the R8… the R8, Audi R8"; the car on screen |
| LEAD CAR · ROLLS-ROYCE CULLINAN | Omarie: "I am in the all black Cullinan. I'll be leading everybody." |
| THE ROUTE · VENETIAN → BLUE DIAMOND → RED ROCK | the brief (CH4 route card) |
| 21:39:xx · LOTUS OF SIAM · RED ROCK CASINO · SEP 15 2026 | the iPhone clip's clock (P2139a, 21:39:36); Omarie: "I'm going to go down to Lotus of Siam"; the brief |
| EGNYTE GUEST + the testimonial words | the guest's own words, verbatim from the audio in the cut (captions.json), word by word; "…" marks where the edit drops words ("maybe", and the rest of the last sentence). No guest names |
| THE EGNYTE GUEST'S PICK · FERRARI ROMA | the guest: "Out of all those cars, I would say … the Roma" |
| TEAM DINNER · YARD HOUSE | Omarie: "We are currently eating at Yard House."; the brief |
| THE ROUTE · 215 → 15 NORTH → FLAMINGO → LAS VEGAS BLVD → VENETIAN → LEVEL 9 | the guide's briefing ("take 215 out of here… to the 15 North") and the brief; 215 and 15 NORTH flash when the guide says them |
| 23:00:xx → 23:20:xx · BACK TO THE VENETIAN | the camera clock of each montage shot (0032, 23:00:03 + in-point); Omarie: "We're gonna go back to the Venetian" |
| FOLLOW THAT CAR · LAMBORGHINI URUS | the guide: "look at what car is in front of you. Follow that car."; the purple Urus ahead |
| EGNYTE ON THE DAY + WONDERFUL · GOOD TIME · AWESOME · AMAZING · GOOD EXPERIENCE | the guests' own words in CH7 (captions.json), each stacked as it is said; header wording: Omarie, 27 Sept |
| Captions | captions.json (corrected word timings), active word in gold; hidden while the SAFELY. slam, the testimonial card or the quote wall already shows the same words. "Ignite" (a Whisper mishearing of Egnyte) would be corrected to "Egnyte"; none of the pieces in the cut contains it |
| End card: A RIDE OF A LIFETIME. · TEXT OR DM TO BOOK · (725) 425-3583 · SUPERCAREXP.VIP · @SUPERCAR_EXPERIENCE_ · LAS VEGAS · SCOTTSDALE · BOISE · RENTERS 25+ · AGES 21–24 WITH $299 UNDERAGE FEE · FILMED BY @NQ.YOUNG | the approved rally layer's end card (`../2026-09-15-rally/README.md` has every source) |

No speeds, horsepower, prices (other than the site's underage fee on the end card), guest names or Formula Dynamics marks
in the graphics. Omarie's shirt in the footage is untouched.

__SOUND__

__PICTURE__

## How to rebuild

```bash
./render.sh                          # = python3 build.py: everything
python3 build.py --stage join,prep,front,compose,qa    # after a layer or transition change
python3 build.py --stage prep,audio,compose,qa         # after a sound change (music slot, levels)
python3 build.py --stills 0,776,4200                   # composite single output frames -> .work/stills/
```

Needs Python 3 with numpy and Pillow, Node 22 with Playwright at `/opt/node22/lib/node_modules/playwright` (Chromium is
preinstalled; never run `playwright install`), and the static ffmpeg (`config.json` `paths.ffmpeg`, or `FFMPEG=`). Inputs: the
EDL, captions and mezzanines in the session scratchpad (`config.json` `paths`).

Stages (cached in `.work/`): `shots` (every EDL shot graded and reframed from the mezzanine) → `track` (lock-ons and plates on
the rendered shots) → `join` (transitions, plate blurs, punches → `.work/plate.mov`) → `prep` (scene, clock, SFX cues) → `audio`
(music bed if no track is supplied, the mix) → `front` (the layer, frame by frame) → `compose` (exports) → `qa`.

## Files

| Path | What |
|---|---|
| `config.json` | paths, per-shot reframe / look / ramp, transitions, plate blurs, clocks, tracks, music slot, audio levels, every on-screen element |
| `cue.md` | every element and transition with its in / out and how it was placed |
| `story.html` | the layer page: `window.renderAt(t)`, a pure function of t |
| `lib/sekit.js` | the vlog kit's component library, copied from `../vlog-kit/lib/sekit.js`. One change: more internal helpers are exported (`SEK.helpers`) |
| `lib/v2kit.js` | this vlog's own components (hook, CTA chip, SAFELY. slam, route card / route panel, place tag, quote wall, car lock, end card) |
| `lib/plate.py` | the picture edit and grade |
| `lib/music.py`, `lib/mix.py` | the placeholder music bed and the mix |
| `lib/kinetic.js`, `lib/kcapture.js`, `lib/accum.py`, `lib/track.py`, `lib/track_mid.py`, `lib/trackqa.py`, `lib/fx.py`, `lib/synth.py` | copied unchanged from the kit / showcase / v1 |
| `lib/srcsheet.py`, `lib/shotview.py`, `lib/gridview.py` | planning and QA sheets |
| `lib/data/tracks.json` | every tracked box (output frames, output px) |
| `build.py`, `render.sh` | the one-command build |

__OPEN__
