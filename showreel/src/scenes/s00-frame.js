// s00-frame — The Frame: persistent editorial HUD (0 s → 15 s, z 900, transparent root).
//
// Crop marks, four mono labels, a frame-accurate timecode and a four-square beat meter that lights on
// every kick. Chapter changes roll their digits up out of a one-line mask (staggered odometer) and
// re-type the word at 1 char/frame behind a Signal block cursor. On the final hit the TL/TR/BL labels
// wipe out left→right (whip) with a hairline leading edge; on the final tick the meter fills.
//
// Everything is a pure function of the frame index f = floor(t·60): colour switches, beat index,
// timecode and typing are all integer-frame exact. Font metrics are measured once in setup().
//
// Render-order safety: every animated text offset is a whole-pixel LAYOUT value (odometer `top`, wipe mask
// `left`/`width`). No fractional compositor translates and no clip-path on text: both rasterised a few
// glyph pixels differently depending on which frame was rendered before, which broke determinism.
// On a Signal ground (s02's dive disc → s03's corridor, frames 222–307) the Signal marks (lit square,
// typing cursor) take the HUD colour so the metronome never vanishes.
(() => {
  const PAPER = R.pal.paper, INK = R.pal.ink, SIGNAL = R.pal.signal;
  const FPS = R.FPS;
  const fr = (t) => Math.ceil(t * FPS - 1e-6); // first frame on which a grid event at t is visible
  const frameOf = (t) => Math.floor(t * FPS + 1e-6);

  // HUD colour schedule (storyboard "Handoff protocol"): exact frames, no fades.
  const COLOR_SCHEDULE = [
    [0, PAPER], [3.75, INK], [7.03125, PAPER], [9.375, INK], [9.84375, PAPER],
    [10.78125, INK], [11.25, PAPER], [11.484375, INK], [11.71875, PAPER],
  ].map(([t, c]) => [fr(t), c]);
  const hudColorAt = (f) => {
    let c = COLOR_SCHEDULE[0][1];
    for (const [f0, col] of COLOR_SCHEDULE) if (f >= f0) c = col;
    return c;
  };

  // Frames on which the HUD corners sit on a solid Signal ground: s02's dive disc covers the meter from
  // frame 222 (R ≈ 1033 > 826 px to the meter), and s03's near walls stay Signal until its Paper rest pose
  // at 308. A Signal mark would vanish there, so the lit square and the typing cursor take the HUD colour.
  const SIGNAL_GROUND = [222, 308];
  const onSignal = (f) => f >= SIGNAL_GROUND[0] && f < SIGNAL_GROUND[1];

  const CHAPTERS = [
    [0, '01', 'WEIGHT'], [1.875, '02', 'TIMING'], [3.75, '03', 'SPACE'],
    [5.15625, '04', 'EASING'], [7.5, '05', 'ENERGY'], [9.375, '06', 'RANGE'],
  ].map(([t, num, word]) => ({ t, f: fr(t), num, word }));

  // Type spec: JetBrains Mono 500, 15 px, uppercase, tracking 0.12em, opacity 0.9.
  const FS = 15, LS = 0.12 * FS; // 1.8 px
  const TEXT_OPACITY = 0.9;
  const X_LEFT = 72, X_RIGHT = 1848, BASE_TOP = 76, BASE_BOT = 1016;

  // Crop marks
  const CROP_V = [[32, 32, 1, 1], [1888, 32, -1, 1], [32, 1048, 1, -1], [1888, 1048, -1, -1]];
  const ARM = 28, CROP_DRAW = 0.2;

  // Beat meter
  const METER_X = [1614, 1630, 1646, 1662], METER_Y = 1005, SQ = 10, OUTLINE = 1.5;
  const FULL_BAR_F = fr(14.53125);
  const POP_FRAMES = 2; // a lit square kicks 1 px outward for its first 2 frames

  // Chapter change choreography
  const ROLL_DUR = 0.1171875, ROLL_STAGGER = 2 / FPS; // digits roll up out of a one-line mask
  const CURSOR_TAIL = 2; // frames the block cursor lingers after the word completes

  // Exit wipe (TL, TR, BL): left→right through a mask, whip, 13.125 → 13.359375. Progress is counted in
  // frames so the mask completes ON the last frame inside the window (801): that frame shows only the
  // leading-edge hairline at the end of each label, and frame 802 is clean. No label remnant pops off.
  const WIPE_F0 = fr(13.125), WIPE_F1 = fr(13.359375) - 1; // 788 → 801

  const MONO = R.font.mono;
  const textStyle = {
    font: `500 ${FS}px ${MONO}`,
    letterSpacing: LS + 'px',
    lineHeight: FS + 'px',
    textTransform: 'uppercase',
    whiteSpace: 'pre',
    fontVariantNumeric: 'tabular-nums',
    fontKerning: 'none',
    opacity: String(TEXT_OPACITY),
  };

  R.scene({
    id: 's00-frame',
    start: 0,
    end: 15,
    z: 900,
    // bg: none — transparent root, drawn over every scene

    setup(root) {
      root.style.pointerEvents = 'none';

      // ---- measure the mono face in this Chromium (baseline offset, advance incl. tracking, cap height)
      // (the scene root is display:none during setup, so the probe lives on <body>)
      const probe = R.el('div', { style: Object.assign({}, textStyle, { left: '0px', top: '0px', visibility: 'hidden' }) }, document.body);
      probe.textContent = '0000000000';
      const adv10 = probe.getBoundingClientRect().width;
      const mark = R.el('span', { style: { position: 'static', display: 'inline-block', width: '0px', height: '0px', verticalAlign: 'baseline' } });
      probe.appendChild(mark);
      const baseOff = mark.getBoundingClientRect().top - probe.getBoundingClientRect().top;
      document.body.removeChild(probe);
      const cv = document.createElement('canvas').getContext('2d');
      cv.font = `500 ${FS}px ${MONO}`;
      const capH = cv.measureText('H').actualBoundingBoxAscent;
      this.adv = adv10 / 10; // advance incl. letter-spacing (≈ 10.8)
      this.baseOff = baseOff; // baseline below the line-box top (≈ 0.86 em)
      this.capH = capH;
      const topFor = (baseline) => Math.round(baseline - baseOff);
      const boxW = (n) => n * this.adv - LS; // advance box without the trailing tracking
      this.topFor = topFor;

      // ---- SVG: crop marks + beat meter (crisp: integer / half-pixel aligned geometry)
      const svg = R.svgLayer(root);
      this.crops = CROP_V.map(() => R.svg('path', { fill: 'none', 'stroke-width': 2, 'stroke-linecap': 'square', 'stroke-linejoin': 'miter' }, svg));
      this.meter = METER_X.map((x) => ({
        x,
        outline: R.svg('rect', { x: x + OUTLINE / 2, y: METER_Y + OUTLINE / 2, width: SQ - OUTLINE, height: SQ - OUTLINE, fill: 'none', 'stroke-width': OUTLINE }, svg),
        fill: R.svg('rect', { x, y: METER_Y, width: SQ, height: SQ, fill: SIGNAL }, svg),
      }));

      // ---- text
      const mk = (text, left, baseline) => {
        const e = R.el('div', { text, style: Object.assign({}, textStyle, { left: left + 'px', top: topFor(baseline) + 'px' }) }, root);
        return e;
      };
      const TL = 'CLAUDE — MOTION DESIGNER', TR = 'SHOWREEL 2026';
      this.tl = mk(TL, X_LEFT, BASE_TOP);
      this.tr = mk(TR, Math.round(X_RIGHT - boxW(TR.length)), BASE_TOP);
      this.tlW = boxW(TL.length); this.trW = boxW(TR.length);
      // Timecode: right-aligned at 1848; fixed width (14 chars) so its left edge never moves.
      this.tcLen = 'TC 00:00:00:00'.length;
      this.tc = mk('TC 00:00:00:00', Math.round(X_RIGHT - boxW(this.tcLen)), BASE_BOT);

      // Chapter "NN / WORD": two masked digit odometers + static " / " + typed word + block cursor.
      const ch = mk('', X_LEFT, BASE_BOT);
      this.ch = ch;
      this.digits = [0, 1].map(() => {
        const mask = R.el('span', { style: { position: 'relative', left: 'auto', top: 'auto', display: 'inline-block', verticalAlign: 'top', height: FS + 'px', overflow: 'hidden' } }, ch);
        const stack = R.el('span', { style: { position: 'relative', left: '0px', top: '0px', display: 'block' } }, mask);
        const a = R.el('span', { text: '0', style: { position: 'relative', left: 'auto', top: 'auto', display: 'block', height: FS + 'px' } }, stack);
        const b = R.el('span', { text: '0', style: { position: 'relative', left: 'auto', top: 'auto', display: 'block', height: FS + 'px' } }, stack);
        return { mask, stack, a, b };
      });
      this.sep = R.el('span', { text: ' / ', style: { position: 'static' } }, ch);
      this.word = R.el('span', { text: '', style: { position: 'static' } }, ch);
      this.chW = boxW(5 + CHAPTERS[CHAPTERS.length - 1].word.length); // "06 / RANGE" is on screen at the wipe
      // Block cursor (Signal, 0.6 em × cap height), positioned on the character grid.
      this.cursor = R.el('div', { style: { width: Math.round(0.6 * FS) + 'px', height: Math.round(capH) + 'px', background: SIGNAL, top: Math.round(BASE_BOT - capH) + 'px' } }, root);

      // Hairline leading edge that rides each exit wipe.
      this.edges = [0, 1, 2].map(() => R.el('div', { style: { width: '1px', height: Math.round(capH + 6) + 'px' } }, root));
      // Each wiped label sits in an overflow:hidden mask div. The wipe moves the mask's left edge and
      // counter-offsets the label by the same whole-pixel amount, so the glyphs never move. (A clip-path
      // wipe rasterised a few text pixels differently depending on render order: not deterministic.)
      const PAD = 4;
      this.wipeTargets = [
        { el: this.tl, left: X_LEFT, w: this.tlW, base: BASE_TOP, lag: 0 },
        { el: this.ch, left: X_LEFT, w: this.chW, base: BASE_BOT, lag: 1, maxW: boxW(5 + Math.max(...CHAPTERS.map((c) => c.word.length))) },
        { el: this.tr, left: Math.round(X_RIGHT - this.trW), w: this.trW, base: BASE_TOP, lag: 2 },
      ].map((w) => {
        const top = topFor(w.base);
        const box = { x0: w.left - PAD, x1: Math.ceil(w.left + (w.maxW || w.w)) + PAD };
        const mask = R.el('div', { style: { left: box.x0 + 'px', top: top - PAD + 'px', width: box.x1 - box.x0 + 'px', height: FS + 2 * PAD + 'px', overflow: 'hidden' } }, root);
        mask.appendChild(w.el);
        w.el.style.top = PAD + 'px';
        return Object.assign(w, { mask, box });
      });
      for (const e of [this.cursor, ...this.edges]) root.appendChild(e); // keep cursor + hairlines above the text
      // No cues or sfx of its own (storyboard: "No sound of its own").
    },

    // Mask a wiped label from its left edge: `cut` whole px of the label are hidden.
    setMask(w, cut) {
      const x0 = cut > 0 ? w.left + cut : w.box.x0;
      w.mask.style.left = x0 + 'px';
      w.mask.style.width = Math.max(0, w.box.x1 - x0) + 'px';
      w.el.style.left = w.left - x0 + 'px';
    },

    update(lt, p, t) {
      const f = frameOf(t);
      const col = hudColorAt(f);
      const swift = R.ease.swift, whip = R.ease.whip;

      // ---- crop marks: draw from each vertex outward along the frame edges
      const arm = ARM * swift(R.clamp((t + 1 / FPS) / CROP_DRAW));
      for (let i = 0; i < 4; i++) {
        const [x, y, dx, dy] = CROP_V[i];
        const pth = this.crops[i];
        pth.setAttribute('d', `M${(x + dx * arm).toFixed(3)} ${y}H${x}V${(y + dy * arm).toFixed(3)}`);
        pth.setAttribute('stroke', col);
      }

      // ---- text colour
      for (const e of [this.tl, this.tr, this.tc, this.ch]) e.style.color = col;

      // ---- timecode (pure function of the frame index)
      const ss = Math.floor(f / FPS), ff = f % FPS;
      this.tc.textContent = `TC 00:00:${String(ss).padStart(2, '0')}:${String(ff).padStart(2, '0')}`;

      // ---- chapter index
      let ci = 0;
      for (let i = 0; i < CHAPTERS.length; i++) if (f >= CHAPTERS[i].f) ci = i;
      const chap = CHAPTERS[ci], prev = CHAPTERS[Math.max(0, ci - 1)];
      const dtc = t - chap.t;
      for (let j = 0; j < 2; j++) {
        const d = this.digits[j];
        const u = ci === 0 ? 1 : swift(R.clamp((dtc - j * ROLL_STAGGER) / ROLL_DUR));
        if (u >= 1) {
          d.a.textContent = chap.num[j];
          d.b.textContent = chap.num[j];
          d.stack.style.top = '0px';
        } else {
          d.a.textContent = prev.num[j];
          d.b.textContent = chap.num[j];
          // Whole-pixel layout offset: crisp glyphs on every roll frame and bit-exact in any render order
          // (a fractional translate on a promoted layer rasterised differently depending on history).
          d.stack.style.top = -Math.round(FS * u) + 'px';
        }
      }
      const typed = ci === 0 ? chap.word.length : Math.min(chap.word.length, f - chap.f + 1);
      this.word.textContent = chap.word.slice(0, typed);
      const showCursor = ci > 0 && f - chap.f + 1 < chap.word.length + 1 + CURSOR_TAIL;
      this.cursor.style.display = showCursor ? 'block' : 'none';
      if (showCursor) {
        const cx = X_LEFT + (5 + typed) * this.adv;
        this.cursor.style.left = Math.round(cx) + 'px';
        this.cursor.style.background = onSignal(f) ? col : SIGNAL;
      }

      // ---- exit wipe on the final hit (TL, BL, TR), then gone
      for (let i = 0; i < this.wipeTargets.length; i++) {
        const w = this.wipeTargets[i], edge = this.edges[i];
        const f0 = WIPE_F0 + w.lag;
        if (f < WIPE_F0) {
          this.setMask(w, 0);
          w.mask.style.display = 'block';
          edge.style.display = 'none';
        } else if (f > WIPE_F1) {
          w.mask.style.display = 'none';
          edge.style.display = 'none';
        } else {
          const u = whip(R.clamp((f - f0 + 1) / (WIPE_F1 - f0 + 1))); // 1 exactly on frame 801
          const cut = Math.round((w.w + 2) * u); // whole px clipped from the left
          w.mask.style.display = 'block';
          this.setMask(w, cut);
          const show = cut >= 1; // no idle bar before the mask moves; on 801 the edge alone ends the move
          edge.style.display = show ? 'block' : 'none';
          if (show) {
            edge.style.background = col;
            edge.style.left = Math.round(w.left + cut) + 'px';
            edge.style.top = Math.round(w.base - this.capH - 3) + 'px';
          }
        }
      }
      if (f >= WIPE_F0) this.cursor.style.display = 'none';

      // ---- beat meter
      const beatIdx = Math.floor(t / R.BEAT + 1e-9);
      const lit = beatIdx % 4;
      const beatF = fr(beatIdx * R.BEAT);
      const full = f >= FULL_BAR_F;
      for (let i = 0; i < 4; i++) {
        const m = this.meter[i];
        const on = full || i === lit;
        m.outline.setAttribute('stroke', col);
        m.outline.style.display = on ? 'none' : 'inline';
        m.fill.style.display = on ? 'inline' : 'none';
        if (!on) continue;
        const onsetF = full ? FULL_BAR_F : beatF;
        const since = f - onsetF;
        const pop = since < POP_FRAMES ? 1 : 0;
        m.fill.setAttribute('x', m.x - pop);
        m.fill.setAttribute('y', METER_Y - pop);
        m.fill.setAttribute('width', SQ + 2 * pop);
        m.fill.setAttribute('height', SQ + 2 * pop);
        // Bar downbeat: the first square flashes the HUD colour for 2 frames before turning Signal.
        const downbeat = !full && i === 0 && since < 2;
        m.fill.setAttribute('fill', downbeat || onSignal(f) ? col : SIGNAL);
      }
    },
  });
})();
