# `race-weekend`: SE event ads (Night + Day)

Approved by Omarie on 2026-10-03 ("approve all 3 f1 ads", then "save the layouts"). It started as the F1-inspired
direction "C · Countdown"; the countdown was removed at his request. The ads it made are in Dropbox
`SCE Ads/2026-10-03 F1 Weekend/` and `Supercar Experience/07 F1 Weekend Ads (2026-10-03)/`.

| Folder | Variant | Built on | Look |
|---|---|---|---|
| `night/` | Night (final: Night v5 RENT) | Car Scenes "Duo AMG x SF90 No Logo" (Las Vegas, night) | black scrims, flat chequer bands, chequered wipes, whips, sector strip, lock-on gates |
| `day/` | Day (final: Day-Duo v3 RENT) | Car Scenes "Day Time Duo 1" (Arizona desert, day) | dark glass panels for bright sky, skewed flag strips, sun-flare wipes, heat-shimmer cuts (edges clamped) |

Shared: SE orange #FF4F16, Hanken Grotesk + JetBrains Mono, sector strip (S1 THU · S2 FRI · S3 SAT · RACE NIGHT), the
end card (RENT A SUPERCAR · BOOK NOW · TEXT (725) 425-3583 · supercarexp.vip · @supercar_experience_ · DRIVERS 25+).

## Copy rules that came with it
- Rental first: RENT A SUPERCAR on frame 0 and on the end card. Car names only as small labels on that car's own
  shot, held at least 1 s ("you can mention car names just make it subtle").
- No countdown. Event words only: F1 WEEKEND, NOV 19–21, THU · FRI · SAT, RACE NIGHT. F1 / Formula 1 in plain text,
  no logos or official fonts. No prices in this set.
- Never LAS VEGAS over desert footage; PICK UP IN LAS VEGAS inside the booking panel is fine.
- Never name a car that isn't on the city's rental list (the SF90 isn't on the Vegas list). Confirm cars in Car Scenes
  clips by frame match to SE's own listing footage in `01 Car Footage/`.
- Music: the clip's own Car Scenes audio. Organic posts only until Car Scenes confirms paid use.

## Running it
Each `build.py` expects a work folder laid out like the original (`~/.local/vlogtools/work/se_f1_week_1003/`):
`src/` holding the Car Scenes clip copied out of Dropbox `Unbranded/` (copy, never move: it's a shared folder),
`.venv/` with numpy + Pillow, and this kit as `build_*/`. Stages are resumable (plate → front → audio → comp → encode);
`front.html` holds every on-screen word and the timings, `edl.json` the cut list. The `--post-date` / `config.js`
countdown parameter is left over from the countdown version and no longer shows on screen.
QA before delivery: frame-by-frame look, stray frames vs the source's own cuts, slow-mo wheel smear, one-sample audio
jumps, -14 LUFS / true peak ≤ -1.5 dBTP, BT.709, text inside the 4:5 band, slopmonster on all copy.
