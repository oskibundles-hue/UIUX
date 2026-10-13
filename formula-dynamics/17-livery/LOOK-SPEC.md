# LIVERY: an FD look (proposed 2026-10-13, not yet approved)

The reel is dressed in a race livery. FD's own five-segment accent stripe, raked at 12 degrees, is
the transition. Each beat gets a number on a white race-number board, and every word on screen
uses the same 12-degree rake. One idea runs through all of it: **the stripe from the logo, turned
into a livery and sent across the frame.**

Why it's new: Locked-On tracks brackets onto a badge, uses kinetic type and puts type behind the car.
Quick-Promo is flat promo cards. Now Boarding is a departure board and Paste-Up is collage. FD's own
treatments (frosted panel, rule, index, tab, HUD, Editorial, Plate, Glass Panels) are all static
containers. LIVERY has no container at all: the graphics are the brand stripe and the race number.

## Typography
- Bebas Neue only (`07-fonts/BebasNeue-Regular.ttf`), always uppercase, with tracking +4% (+6 to 8% on small lines).
- **Every word is sheared forward 12 degrees** (affine shear tan 12 = 0.2126), the way race-car lettering
  is. Nothing on screen stands upright except the FD logo, which is never sheared, recoloured or shadowed.
- Sizes at 1080x1920: beat word 112 px, beat sub-line 46 px, end-card CTA 150 px and 230 px, URL and handle 58 px.

## Colour
- FD red `#FE0F13`, white and black from `fd_brand.py`, nothing else.
- Green and yellow appear only inside the stripe (pass and end-card band), as the brand spec requires.
  On dark footage the stripe's black band disappears. That's correct; don't fix it.
- Accent rule: one red element per graphic (the tape under the beat word; the payoff word on the end card).

## Graphics
- **Number board**: a 150 px white rounded square (radius 14%) with a black raked numeral (01, 02 ...),
  placed at the top-left of the 9:16 safe area (x 68, y 251). The beat word sits beside it in white with a
  soft 55% shadow, and a 12 px raked red tape runs under the word.
- All graphics stay inside FD's keep-out zones (top 11%, bottom 20%, right 16%, left 5%).

## Motion
- Beat plates fade up over 0.2 s while sliding 70 px along the line (cubic ease-out), hold 1.8 s, then fade out over 0.2 s.
  Each one lands just after its stripe pass clears.
- No other moving graphics. The footage carries the reel, and the plate is the only thing on screen.

## Transitions
- **Stripe pass** (the signature): five full-height raked bands in the brand order and shares (red 36.7,
  black 21.4, white 19.4, green 17.0, yellow 5.5), with red leading. They sweep left to right in 10 frames
  (0.33 s at 30 fps), easing out into full cover and easing in out of frame. The frame is fully covered on
  frames 4 to 6, and the hard cut sits on frame 5, under the cover.
- Use it only between beats and into the end card, so three or four times a reel. Cuts inside a beat are straight.
  If every cut gets a pass, it reads as a glitch (the Locked-On reviewers flagged this kind of thing).
- Sound: `10-motion-sfx/sfx/whoosh-in.wav` under each pass, at 0.45 gain under the real sound.

## Grade
- Reels: **R2 "HD reel+"** (`~/.local/vlogtools/gR2.cube` + `hqdn3d=2:1.5:3:3,unsharp=5:5:0.45:5:5:0`),
  Omarie's reel pick on 2026-09-14. One grade across every shot. Shop lights get R2's highlight roll-off.
- `build.py` refuses to render without `--lut` unless you pass `--ungraded`, which is for test renders only.

## End card (2.6 s, entered under the last stripe pass)
- Black ground, the white FD primary horizontal logo (600 px), and a full-bleed raked stripe band (30 px).
- **Build** variant: BOOK YOUR (white) / BUILD (red), FORMULADYNAMICSPERFORMANCE.COM, @FORMULADYNAMICSPERFORMANCE.
- **Store** variant: SHOP F8 PARTS (white) / ONLINE (red), FORMULADYNAMICS.COM, handle. Store posts never use the shop site.
- No prices, no figures.

## Sound and delivery
- Real sound on: each clip's own audio, never replaced. Whooshes under the passes, and the last 50 ms fades to silence.
- Loudness: `99-toolkit/fd_master.py`, -14 LUFS integrated, -1.0 dBTP, two-pass with a limiter, 48 kHz stereo.
- One Instagram-ready file per reel: 1080x1920, 30 fps, H.264 High at CRF 17 (12 Mb/s cap), AAC 192k,
  fast start. Named `FD <name> - INSTAGRAM 1080x1920.mp4`.

## Recipe (reuse)
1. Pick shots per beat, then write a cut sheet (`cuts/<id>.json`): beats, each with `num`, `word` and
   shots (`src`, `in`, `out`, and `blur` boxes `[t0, t1, x, y, w, h]` for plates and faces, in output pixels and seconds into the shot).
2. Make the pre-render frame sheet of every shot as it will render (after the 9:16 crop), check plates,
   faces and hands, and put a blur box on every plate.
3. `python3 build.py cuts/<id>.json --lut ~/.local/vlogtools/gR2.cube`. The output goes to `renders/`, with a manifest
   of beats, shot sources and pass times.
4. Copy goes through SlopMonster (5/5). Any figure on screen needs a named source; this look carries none by design.
5. Graphics only: `python3 livery.py stills <dir>` (end cards, a sample plate and a look-test sheet).

Files: `livery.py` (graphics), `build.py` (render), `cuts/` (cut sheets), `captions/` (caption .txt).
