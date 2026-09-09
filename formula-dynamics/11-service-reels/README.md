# Service Reels — R1–R7

Seven 15-second vertical service reels, one per service line. Rendered from
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

## Two versions, on purpose

**Picture masters** (`FD-Rn-*.mp4`) carry no audio track. They are the ones to
hand to an editor or drop into Ads Manager with a licensed music bed under them.

**SFX cuts** (`FD-Rn-*-SFX.mp4`) carry the sound-design bed only — risers,
impacts, key clicks, the engine one-shots — placed against the same beat times
the scenes animate to, so every hit lands on the motion. Still no music: the bed
is built to sit *under* a track, not to replace one. Limited to -1.5 dBTP.

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
