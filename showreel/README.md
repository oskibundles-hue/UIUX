# Showreel 2026 — Claude, Motion Designer

A 15-second, 1080p60 motion-graphics showreel that is **written entirely in code**: DOM, CSS, SVG and Canvas 2D,
rendered frame by frame in headless Chromium and scored with a procedurally synthesized soundtrack locked to a
128 BPM grid. There is no footage, stock art or sample library. Every pixel and every sample is generated.

- **Watch:** `dist/showreel.mp4` (H.264 1080p60 + AAC)
- **Play it live in a browser:** serve this folder and open `index.html?play` (click to start, sound on)
- **Storyboard:** [`STORYBOARD.md`](STORYBOARD.md)

## Build it

Requirements: Node 18+, Playwright with a Chromium build, Python 3 with `numpy`, and an ffmpeg that has libx264
(`pip install imageio-ffmpeg numpy` provides both Python pieces).

```bash
cd showreel
python3 audio/synth.py                 # -> dist/soundtrack.wav (reads audio/cues.json)
node tools/cues.mjs                    # (re)export picture-driven sound cues -> audio/cues.json
node tools/render.mjs                  # -> dist/showreel.mp4 (1080p60, muxes the soundtrack)
node tools/render.mjs --preview        # fast 540p30 check -> .cache/preview.mp4
node tools/stills.mjs --scene s03 --count 12 --sheet   # QA stills + labelled contact sheet
```

## How it works

```
index.html            stage, @font-face, interactive player (?play)
src/engine.js         deterministic runtime: timing grid, easing, springs, keyframes, noise, DOM/SVG/canvas
                      helpers, point sets for morphs/particles, pseudo-3D, global post-FX, scene registry
src/scenes/*.js       one module per scene; manifest.js lists the load order
tools/render.mjs      Chromium frame capture (parallel pages) -> ffmpeg (BT.709, yuv420p)
tools/stills.mjs      stills + contact sheets for visual QA
tools/determinism.mjs checks a scene renders identically in order and shuffled
tools/scaffold.mjs    manifest + placeholder scenes from storyboard.json
tools/cues.mjs        exports scene windows, FX cues and sound events -> audio/cues.json
audio/synth.py        numpy soundtrack: drums, sub, stabs, risers, impacts; picture-synced from cues.json
fonts/                Archivo (variable wght+wdth), Instrument Serif, JetBrains Mono (all SIL OFL 1.1)
```

Everything is a pure function of time. The renderer seeks to `t = frame / 60`, calls `R.render(t)` and screenshots the
page, so frames can be rendered out of order and in parallel, and every render is bit-for-bit repeatable.

---

## Scene builder guide

### Contract

```js
R.scene({
  id: 's03-shapes',            // must match the storyboard id
  start: 3.75, end: 5.625,     // global seconds, window is [start, end). Snap to the grid: R.pos(bar, beat, 16th)
  z: 30,                       // stacking order; higher draws on top (matters during overlaps)
  bg: R.pal.ink,               // optional root background (omit for a transparent root during overlaps)
  setup(root) { /* build DOM/SVG/canvas once; register R.cue / R.sfx here */ },
  update(lt, p, t) { /* every visible frame: lt = local seconds, p = 0..1, t = global seconds */ },
});
```

- `root` is a 1920×1080 `div` with `overflow:hidden`. Its children are absolutely positioned at 0,0 by default (`R.el`).
- Keep state on `this` (the scene object) or in closures. `update` must set **every** animated property on every
  frame (no incremental `+=`), because frames can be rendered out of order.
- **Determinism:** never use `Math.random`, `Date`, `performance.now`, CSS transitions/animations, or `requestAnimationFrame`.
  Use `R.rand(seed)`, `R.hash(i, j)`, `R.noise2/3`, `R.fbm`, `R.wiggle`, and `R.sim` for stepped simulations.
- **Performance:** aim for under 40 ms per frame. Prefer one canvas for many particles over many DOM nodes, cache
  geometry in `setup`, and avoid layout thrash such as reading `getBoundingClientRect` inside `update`.

### Timing

| helper | meaning |
|---|---|
| `R.BEAT` `R.BAR` `R.E8` `R.E16` | 0.46875 s, 1.875 s, 0.234375 s, 0.1171875 s |
| `R.pos(bar, beat=1, sixteenth=0)` | musical position (1-based bar/beat) to seconds |
| `R.bar(n)` / `R.beat(n)` | bar start (1-based) / global beat (0-based) to seconds |
| `R.seg(t, t0, t1, ease)` | eased 0..1 progress through a window |
| `R.remap(v, a, b, c, d, ease)` | clamped, eased range map |
| `R.kf(t, [[t0, v0], [t1, v1, 'swift'], ...])` | AE-style keyframes for numbers, arrays or `#hex` colors; the ease on a key shapes motion *into* it |
| `R.stagger(t, i, n, {start, each, dur, ease, from})` | per-item eased progress; `from`: `start`, `end`, `center`, `edges` or `random` |
| `R.spring(t, {stiffness, damping, mass})` | analytic damped spring from 0 to 1 (overshoots when underdamped) |
| `R.since(t, R.BEAT)` | seconds since the last beat, for per-beat pulse envelopes |
| `R.stepped(t, 12)` | quantize time for an "on twos" look |

### Easing: the house curves

`R.ease.snap` (hard in-out) · `swift` (fast launch, long glide: the default "arrive" curve) · `whip` (accelerate
into a cut) · `glide` · `punch` (overshoot) · `anticipate` (dips back first). Standard Penner set: `inOutCubic`,
`outExpo`, `outBack`, `outElastic`, `outBounce` and the rest. `R.cubicBezier(x1,y1,x2,y2)` creates custom curves.
Any API that takes an ease also accepts a name string or a `[x1,y1,x2,y2]` array.

### Drawing

- `R.el(tag, {style, text, html, class, attrs}, parent)`, `R.svg(tag, attrs, parent)`, `R.svgLayer(parent)`,
  `R.canvas(parent, {w, h})` returns `{canvas, ctx}`.
- `R.tf({x, y, z, r, rx, ry, s, sx, sy, skx, sky, p})` builds a transform string. For 3D, set `perspective` on
  the parent or use `p` for per-element perspective.
- `R.split(el, text)` returns `{chars, words}`: inline-block spans for kinetic type.
- `R.drawStroke(pathEl, p, from)` draws an SVG stroke on by fraction.
- Variable type in the DOM: `style.fontStretch = '62%'..'125%'` (Archivo width), `fontWeight = 100..900`.
  In canvas: `ctx.font = '900 200px Archivo'`, plus `ctx.fontStretch = 'ultra-condensed'...'ultra-expanded'` (keywords only).
- Point sets: `R.shapes.circle/polygon/rect/star(...)` with the same point count morph cleanly via `R.poly.lerp`.
  `R.poly.resample`, `R.poly.trace(ctx, pts)`, `R.poly.toPath(pts)`, `R.textPoints(text, {size, weight, x, y, step})`
  (particles that assemble into type), `R.pathPoints(d, n)`.
- Pseudo-3D: `R.v3.rotX/rotY/rotZ`, `R.v3.project(p, {fov, dist, cx, cy})` returns `[sx, sy, scale, depth]`,
  `R.v3.fibSphere(n)`, `R.v3.torus(R0, r0, nu, nv)`.
- Color: `R.pal.{ink, paper, signal, volt, acid, graphite, fog}`, `R.mixColor(a, b, t)`, `R.rgba(hex, a)`.
- Fonts: `R.font.display` (Archivo), `R.font.serif` (Instrument Serif), `R.font.mono` (JetBrains Mono).

### Global post-FX and sound cues

Register these in `setup` (they are global and time-based, so the engine and the soundtrack both read them):

```js
R.cue(t, 'flash', {amt: 0.9, dur: 0.12, color: '#fff'});
R.cue(t, 'shake', {amt: 14, dur: 0.3});
R.cue(t, 'chroma', {amt: 10, dur: 0.2});
R.cue(t, 'zoom', {amt: 0.05, dur: 0.3});
R.cue(t, 'invert', {dur: 0.05});
R.cue(t, 'letterbox', {amt: 110, dur: 1.2});
R.cue(t, 'vignette', {amt: 0.5, dur: 0.47, in: 0.1, out: 0.03});
R.sfx(t, 'impact' | 'whoosh' | 'swish' | 'click' | 'tick' | 'pop' | 'blip' | 'glitch' | 'riser' | 'reverse' | 'subdrop' | 'shimmer' | 'type' | 'tapestop', {...});
```

### QA loop for every scene

```bash
node tools/stills.mjs --scene s03 --count 12 --sheet          # whole scene, labelled contact sheet
node tools/stills.mjs --only s03 --from 4.1 --to 4.4 --every 2 --sheet   # motion check, every 2nd frame
node tools/stills.mjs --times 3.75,5.617 --name handoff        # both sides of a handoff (all scenes)
node tools/determinism.mjs --scene s03                          # in-order vs shuffled render must match
```

`stills.mjs` exits non-zero and prints any page error, so fix those first. Look at the actual PNGs: check
composition, legibility, the handoff frames and whether the motion reads.
