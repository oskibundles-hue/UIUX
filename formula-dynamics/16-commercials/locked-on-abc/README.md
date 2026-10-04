# `locked-on-abc`: classic FD Locked-On with the abc-mix 3D moments

Approved by Omarie on 2026-10-04 ("Can I get an ABC mix for Locked On as well? I love the Locked On. That's the classic
way to go", then "Approve, add next to 30s PPF" and "Save + push to FD branch"), on the 30-second MC20 PPF "full
process" ad, v2. Delivered: Dropbox `Portfolio/14 FD Commercials/2026-10-03 Shop videos - MC20 PPF full process (30s)/`,
file 02, next to the abc-mix cut (01). Post one or the other, not back to back.

`per-shot-sheet-v2.jpg` shows one frame per shot of the approved v2.

| Part | Look |
|---|---|
| Base | Classic FD Locked-On: frame-0 hook panel over dimmed footage, tracked lock-on brackets with mono tags, kinetic step cards (STEP 01–06 / 06), whips between steps, impacts inside a step and on the drop |
| A film step (squeegee) | abc-mix A: the 3D FILM / CLEAR COAT / PAINT chip rises with the stroke |
| A tool step (trim) | abc-mix B: extruded red-black step name standing on the red rail line |
| An edge step (wrap the edges) | abc-mix C: scan curtain and mesh over the traced edge |
| Reveal | abc-mix A's layer split over the finished panel (fades and grows in place), then FD end card v4 built the Locked-On way (`lib/fdc.js`) |

It is **not** abc-mix: no frosted glass panels. The footage stays flat and full-frame, cut on the beat.

## Rules that came with it (the v1 review, 4 Oct)
- **A lock lives only inside its own shot.** No bracket or tag may show on any sub-frame of the next shot. Check with
  `qa/lockaudit.js` (0 violations on v2). v1 failed review on one stray FILM EDGE lock.
- **Frame 0 is a hook over footage**, not a card on black: both approved FD Locked-On ads put the panel over the picture
  (here #36, the installer at the front fender, at 42 % brightness).
- **Nothing next to the SE shirt emblem.** FD ads shot at the shop can show the installer's shirt; keep cards and tags
  clear of it (WRAP card capped at 560 px wide, ~88 px gap). Two brands never share a frame.
- **Drop a lock rather than force it** into a keep-out (badge, tool, face, the shirt). v2 dropped the #32 lock.
- A tracked lock holds its last good position while it exits, so the exit animation always finishes.
- Brand: FD red #FE0F13, Bebas Neue, IBM Plex Mono (`../../07-fonts/`), FD logos (`../../02-logos/`), end card v4.
  No SE colours or fonts. `lib/sekit.js` is the shared Locked-On component library; here it loads the FD logos only.
- Step names say only what's on camera. Music only for real-footage FD ads; the second drop lands on the reveal.
  -14 LUFS, true peak ≤ -1.5 dBTP after AAC. Text inside the 4:5 band (`qa/inkaudit2.js`).

## Running it
Same layout and footage as `../abc-mix/` (it reuses that cut's shots, src windows, timing and music), so the kit
expects the work-folder layout `~/.local/vlogtools/work/fd_ppf30_1003/`: `fonts/`, `logos/`, `plates/` and `.work/<D>/`
beside these files. Footage: Dropbox `Shop videos/` (read-only, shared: copy out, never move).
1. Build the abc-mix scene first (`.work/H/scene.js` and `.work/H/mix.wav`): see `../abc-mix/README.md` steps 1–3.
2. Hook plate: `ADS_MOD=lo2plan python plates.py M_h36`.
3. Scene: `python lo_data.py M` writes `.work/M/scene.js` (shots, edit plan, lock tracks, wrap homographies) and
   `.work/M/kitdata.js` (end card). Lock tracks are in `tracks/locks.json`; `lo_track.py` re-tracks the #37 microfibre.
4. Render: `D=M PAGE=lo.html OUTNAME="<name>" ./render_lo.sh`. Detached, 2 capture workers, memory watchdog: layer
   capture with true motion blur → lossless composite (`compose_lo.py`) → two-pass x264 ~11.5 Mb/s, BT.709, AAC 256k.
5. Checks: `PW_MODULE=<playwright> node qa/lockaudit.js lo.html` (its `bad` list must be empty), and QA stills with
   `./stills_lo.sh <tag> t1,t2,…`.
`lo.html` holds every on-screen word and every graphic's timing. Python is the instagram-one-post venv (numpy, OpenCV).
