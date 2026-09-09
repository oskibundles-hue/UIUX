# Service Reels — R1–R7

Eight 15-second vertical service reels — one per service line, plus the annual
service package. Rendered from
HTML scenes through headless Chromium, then muxed with a sound-design bed cut
from the FD SFX pack.

`1080 x 1920 · 30 fps · 15.00 s · H.264`

| Reel | Service | Hook | Master | With SFX |
|---|---|---|---|---|
| R1 | Exhaust — Larini | "They hear you before they see you." | 3.1 MB | 3.4 MB · 18 cues |
| R2 | ECU calibration | "Stock is a starting point." | 2.4 MB | 2.7 MB · 14 cues |
| R3 | Paint protection film | "The paint is the expensive part." | 2.7 MB | 2.9 MB · 19 cues |
| R4 | Complete builds | "A build isn't a parts list." | 2.7 MB | 2.9 MB · 18 cues |
| R5 | 20 years / authority | "Years. One obsession." | 3.0 MB | 3.2 MB · 17 cues |
| R6 | Forged wheels — NV Forged | "Wheels are the first thing anyone sees." | 2.7 MB | 2.9 MB · 15 cues |
| R7 | Body kits — aero & carbon | "Aero isn't decoration." | 2.2 MB | 2.5 MB · 15 cues |
| R8 | **Annual service package, $3,999** | "A year of service, bought once." | 1.9 MB | 2.6 MB · 17 cues |

## Two versions, on purpose

**Picture masters** (`FD-Rn-*.mp4`) carry no audio track. They are the ones to
hand to an editor or drop into Ads Manager with a licensed music bed under them.

**SFX cuts** (`FD-Rn-*-SFX.mp4`) carry the sound-design bed only — risers,
impacts, key clicks, the engine one-shots — placed against the same beat times
the scenes animate to, so every hit lands on the motion. Still no music: the bed
is built to sit *under* a track, not to replace one. Limited to -1.5 dBTP.

## R8 is the first one that carries a price

R1–R7 make no price or performance claim at all, deliberately: nothing was
verified when they were written. R8 puts **$3,999** on screen because the shop
confirmed it, and it counts up rather than cutting in — the number is the reel's
whole argument, so it gets the moment.

Two inclusions are stated on screen rather than buried:

- **Oil service — oil included.**
- **Brake service — labour and fluid, pads not included.**

That second line is unusual in an ad and it stays. An exclusion a customer
discovers at pickup costs more than the one they read before booking.

## The partner URL graphic

`partner.js` mounts a lower-third carrying an exhaust manufacturer's name and
their own public URL, typed on character by character. Facts and addresses come
from `PARTNERS.md`, which was taken off the manufacturers' own sites.

```js
mountPartner('ryft');        // in build()
partnerUrl(t, 6.4, 10.2);    // in frame(t)
```

Two rules it enforces by construction:

- **Only on a video where that exhaust actually appears.** A URL bar on a cut
  that doesn't feature the product is noise. R8 has no exhaust in it, so R8
  doesn't carry one.
- **Type, never a partner logo.** Manufacturer marks are third-party IP and are
  not generated in this kit — `mountPartner` throws for any brand without a
  verified entry rather than guessing a URL.

Currently verified: **RYFT** (`ryft.co`) and **iPE** (`ipeofficial.com`). Larini
and Opus have no published entry yet — see `PARTNERS.md`.

## Rebuilding

The SFX cuts are not tracked; regenerate them from the masters in a few seconds:

```bash
python3 tools/build_audio.py            # all seven
python3 tools/build_audio.py FD-R3-PPF  # just one
```

Re-rendering a master from its scene is the slow path (~4 min per reel, Chromium
captures 450 frames):

```bash
npm i playwright-core
node tools/render.js scenes/r3-ppf.html renders/FD-R3-PPF.mp4 30 1080 1920
```

`render.js` drives each scene through `window.seek(t)`, waiting on
`window.__ready` and reading `window.SCENE_DURATION`, so the scene file itself
is the single source of timing — change a beat in the HTML and both the picture
and the cue placement follow from it.

## Cue sheets

Cue times live in `tools/build_audio.py` as `(sound, seconds, gain)` triples,
one list per reel. They are written against the scene's own beats, so if you
retime a scene, retime its cue list in the same pass. Sounds resolve out of
`sfx-fd/` — 47 files, catalogued in `sfx-fd/MANIFEST.md`, with the engine
one-shots (`fd_engine_low`, `fd_engine_peak`, `fd_engine_settle`) recorded in
the shop and documented in `sfx-fd/FD-RECORDINGS.md`.

R1 is the one worth reading as an example: the engine is deliberately held back
at `fd_engine_low` while the valve is closed at 8.95 s, then the valve opens at
10.25 s and `sub_drop` + `fd_engine_peak` land together. The sound design is
making the product's argument, not decorating it.

## Where these came from

The scenes were built on the `claude/formula-dynamics-meta-reels-h2hzvr` branch,
where `out/` is gitignored — which is why the rendered files went missing and
had to be re-rendered from source. They live here now, outside any ignored path.
