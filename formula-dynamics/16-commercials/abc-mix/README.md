# `abc-mix`: FD process commercial, flat footage + 3D graphics per step

Approved by Omarie on 2026-10-03 ("approve the 30s PPF", then "save the abc mix layout"), on the 30-second MC20 PPF
"full process" ad. Delivered: Dropbox `Portfolio/14 FD Commercials/2026-10-03 Shop videos - MC20 PPF full process (30s)/`.

`style-frames-ABC.jpg` shows the three style frames it mixes. Omarie sent that sheet back with "like this" and picked
"mix all 3, in that order":

| Step type | Look | From frame |
|---|---|---|
| Hook, prep, peel, lay | frosted glass title panel cut from the picture: mono kicker, Bebas step name, short red rule | A / C |
| A step where the film itself is the point (squeegee) | 3D FILM / CLEAR COAT / PAINT chip rising from the panel with a red dashed footprint and leader labels, sealing after the stroke | A · Film Layers |
| A tool step (trim) | extruded red-black 3D step name standing on a red rail line, skewed kicker | B · Spatial Rail |
| An edge or panel step (wrap the edges) | the traced, tracked edge glowing red, a scan curtain and mesh, depth pins naming what's on camera | C · Surface Map |
| Reveal | the layer split again over the finished panel, then the approved FD end card v4 | A |

**The footage is always flat and full-frame**, cut on the beat. Omarie: "we dont have to make the whole video frame 3
dimensional". The 3D-cards version ("3D rail") was built and kept as an alternate, not the standard. It is **not
Locked-On**: no lock-on boxes, kinetic step cards or whips.

## Rules that came with it
- Brand: FD red #FE0F13, Bebas Neue, IBM Plex Mono (`../../07-fonts/`), FD logos (`../../02-logos/`), end card v4. No SE colours or fonts.
- Step names say only what's on camera. With no blade-on-film clip, "cut the film" became PEEL THE FILM. No counts, prices or figures.
- Frosted panels never sit empty over a face, and never cut across someone's head. They grow with the type.
- Keep labels off badges (the trident) and tools (the squeegee) the shot is about.
- Real-footage FD ads are music only. The second drop lands on the reveal. -14 LUFS, true peak ≤ -1.5 dBTP after AAC.
- Gentle per-shot gamma match so hard cuts don't pump bright/dark. No look change.
- Text inside the 4:5 band (x 54–907, y 285–1536 on 1080x1920). Audit it with `qa/inkaudit2.js`.

## Running it
The kit expects the original work-folder layout (`~/.local/vlogtools/work/fd_ppf30_1003/`): `fonts/`, `logos/` (FD
white logos + `fd_endcard__v4_nogrid_9x16.jpg`) and `.work/<D>/` beside these files. The footage comes from Dropbox
`Shop videos/` (read-only, shared: copy out, never move).
1. `python full30.py`, then `python v2data.py` writes the timeline and `.work/<D>/scene.js` (shots, src windows, beats).
2. Plates: `ADS_MOD=v2plan python plates.py <key>`. Tracks for the C steps: `CHAIN=1 MOTION=affine python track30.py <shot> …`.
3. Music: `python music.py <ad> "<track wav>" --splice <drop1>,<riser>,<drop2> --bar0 <s>`, then copy `mix.wav` into `.work/<D>/`.
4. Render: `D=<D> PAGE=v3.html OUTNAME="<name>" bash render_v2.sh`. It runs detached, with 2 capture workers and a
   memory watchdog: layer capture with true motion blur → lossless composite → two-pass x264 ~11.5 Mb/s, BT.709.
`v3.html` holds every on-screen word and every graphic's timing. Python is the instagram-one-post venv (numpy, OpenCV).
