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
// Split grounds: where a hard ground edge crosses the HUD (s03's Paper wall opening out, f305–307; the
// s05 → s06 whip seam, f549–562) the HUD takes its colour per side of the edge. A text block crossed by an
// edge is cut by two whole-pixel overflow:hidden masks (the original and a clone in the other colour);
// crop marks and meter squares take the colour of the ground under their horizontal centre.
(() => {
  const PAPER = R.pal.paper, INK = R.pal.ink, SIGNAL = R.pal.signal;
  const FPS = R.FPS;
  const fr = (t) => Math.ceil(t * FPS - 1e-6); // first frame on which a grid event at t is visible
  const frameOf = (t) => Math.floor(t * FPS + 1e-6);

  // HUD colour schedule (storyboard "Handoff protocol"): exact frames, no fades.
  //   3.7 (f222)      Ink:   s02's dive disc covers every corner (Signal ground), through s03's Signal field
  //   4.6875 (f282)   Paper: ROLL 2 + RUSH, the corridor walls darken toward Ink
  //   307/60 (f307)   Ink:   s03's Paper wall fills the frame bar two thin side strips (WALL_BAND splits them);
  //                          written as 307/60 because fr(5.1166667) = 308
  const COLOR_SCHEDULE = [
    [0, PAPER], [3.7, INK], [4.6875, PAPER], [307 / 60, INK], [7.03125, PAPER], [9.375, INK], [9.84375, PAPER],
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
  // s03's Paper far wall opens out as a full-height band across the dark rush corridor and reaches the
  // corners on 308. Its edges at the HUD rows [left, right] (top row y 62–78, bottom row y 1002–1018), measured
  // on s03's render (L = 120 crossing, mean over the row band). Ink inside the band, Paper outside.
  // (f304: 351 → 1571, clear of every HUD part.)
  const WALL_BAND = {
    305: { top: [281, 1636], bot: [286, 1641] },
    306: { top: [198, 1714], bot: [207, 1724] },
    307: { top: [98, 1812], bot: [109, 1823] },
  };
  // The crop-mark corners are 1058 px from centre, beyond the disc on frame 222 (R ≈ 1033): they sit on
  // Ink for that one frame and take the Ink switch on 223 (R ≈ 1396), when the disc covers the whole frame.
  const CORNERS_ON_DISC_F = 223;

  // s05 → s06 whip overlap (storyboard "Shared whip function"): s06's opaque panel sits at x = 1920 − P(t).
  // On these frames HUD parts right of the seam take the colour the schedule switches to at the landing.
  const WHIP_T0 = 9.140625, WHIP_DUR = 0.234375;
  const WHIP_F = [fr(WHIP_T0), fr(WHIP_T0 + WHIP_DUR)]; // 549 → 562 inclusive (563 is the landing)
  // s06 smears its leading edge with a Paper ramp just left of the panel, as long as the edge's travel over
  // half a frame (0.5·|P'|/60, drawn when ≥ 2 px). The split sits at the ramp's midpoint: Paper type over
  // the darker half, Ink over the lighter half, so no glyph is ever Paper-on-near-Paper inside the ramp.
  const whipSeam = (t) => {
    const u = (t - WHIP_T0) / WHIP_DUR;
    const x = 1920 - 1920 * R.ease.inOutCubic(R.clamp(u));
    const dP = u <= 0 || u >= 1 ? 0 : (1920 / WHIP_DUR) * (u < 0.5 ? 12 * u * u : 3 * (2 - 2 * u) * (2 - 2 * u));
    const blur = (0.5 * dP) / FPS;
    return Math.round(blur >= 2 && x < 1920 ? x - blur / 2 : x);
  };

  // Ground split on frame f: null (the whole HUD takes the schedule colour) or, per HUD row, the x where the
  // colour changes (`edges`, ascending) and the colours between them (`cols`, one more than edges).
  const groundSplit = (f, t) => {
    if (f >= WHIP_F[0] && f < WHIP_F[1]) {
      const row = { edges: [whipSeam(t)], cols: [hudColorAt(f), hudColorAt(WHIP_F[1])] };
      return { top: row, bot: row };
    }
    const band = WALL_BAND[f];
    if (band) {
      const row = (e) => ({ edges: e, cols: [PAPER, INK, PAPER] });
      return { top: row(band.top), bot: row(band.bot) };
    }
    return null;
  };
  const rowColAt = (row, x) => {
    let i = 0;
    while (i < row.edges.length && x >= row.edges[i]) i++;
    return row.cols[i];
  };

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
      // Timecode mask: the timecode moves into it only on frames where a ground edge cuts it, and lives on the
      // root (its original place) otherwise. (Parked in an overflow:hidden div for the whole reel, it
      // rasterised 1–2 levels differently under the camera shake/zoom of the later hits.)
      const tcLeft = Math.round(X_RIGHT - boxW(this.tcLen)), tcTop = topFor(BASE_BOT);
      const tcBox = { x0: tcLeft - PAD, x1: Math.ceil(tcLeft + boxW(this.tcLen)) + PAD };
      const tcMask = R.el('div', { style: { left: tcBox.x0 + 'px', top: tcTop - PAD + 'px', width: tcBox.x1 - tcBox.x0 + 'px', height: FS + 2 * PAD + 'px', overflow: 'hidden', display: 'none' } }, root);
      this.tcMask = tcMask;
      this.tcHome = { left: this.tc.style.left, top: this.tc.style.top, inLeft: tcLeft - tcBox.x0 + 'px', inTop: PAD + 'px' };
      // Split ground: every text block gets a second mask that holds a clone in the other colour.
      this.splitTargets = [...this.wipeTargets, { el: this.tc, left: tcLeft, base: BASE_BOT, mask: tcMask, box: tcBox }].map((w) => {
        const dup = R.el('div', { style: { top: topFor(w.base) - PAD + 'px', height: FS + 2 * PAD + 'px', overflow: 'hidden', display: 'none' } }, root);
        return Object.assign(w, { dup });
      });
      for (const e of [this.cursor, ...this.edges]) root.appendChild(e); // keep cursor + hairlines above the text
      this.tcHome.next = this.tc.nextSibling; // the timecode's slot in the root's stacking order
      // No cues or sfx of its own (storyboard: "No sound of its own").
    },

    // Mask a wiped label from its left edge: `cut` whole px of the label are hidden.
    setMask(w, cut) {
      const x0 = cut > 0 ? w.left + cut : w.box.x0;
      w.mask.style.left = x0 + 'px';
      w.mask.style.width = Math.max(0, w.box.x1 - x0) + 'px';
      w.el.style.left = w.left - x0 + 'px';
    },

    // Timecode in its split mask (a ground edge cuts it) or back in its own slot on the root.
    setTcMasked(inMask) {
      const h = this.tcHome;
      if (inMask) {
        if (this.tc.parentNode !== this.tcMask) this.tcMask.appendChild(this.tc);
        this.tc.style.left = h.inLeft;
        this.tc.style.top = h.inTop;
        this.tcMask.style.display = 'block';
      } else {
        if (this.tc.parentNode === this.tcMask) this.tcMask.parentNode.insertBefore(this.tc, h.next);
        this.tc.style.left = h.left;
        this.tc.style.top = h.top;
        this.tcMask.style.display = 'none';
      }
    },

    update(lt, p, t) {
      const f = frameOf(t);
      const col = hudColorAt(f);
      // Split ground: a mark takes the colour of the ground under its horizontal centre.
      const split = groundSplit(f, t);
      const colAt = (bottom, cx) => (split ? rowColAt(bottom ? split.bot : split.top, cx) : col);
      const swift = R.ease.swift, whip = R.ease.whip;

      // ---- crop marks: draw from each vertex outward along the frame edges
      const arm = ARM * swift(R.clamp((t + 1 / FPS) / CROP_DRAW));
      for (let i = 0; i < 4; i++) {
        const [x, y, dx, dy] = CROP_V[i];
        const pth = this.crops[i];
        pth.setAttribute('d', `M${(x + dx * arm).toFixed(3)} ${y}H${x}V${(y + dy * arm).toFixed(3)}`);
        const cropCol = f >= SIGNAL_GROUND[0] && f < CORNERS_ON_DISC_F ? hudColorAt(SIGNAL_GROUND[0] - 1) : colAt(y > 540, x + (dx * ARM) / 2);
        pth.setAttribute('stroke', cropCol);
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

      // ---- split ground: original left of the edge, a clone in the other colour right of it (whole-pixel masks)
      for (const w of this.splitTargets) {
        const { x0, x1 } = w.box;
        const row = split && (w.base === BASE_BOT ? split.bot : split.top);
        const cut = row ? row.edges.find((e) => e > x0 && e < x1) : undefined;
        if (row) w.el.style.color = rowColAt(row, cut === undefined ? (x0 + x1) / 2 : cut - 1);
        if (w.el === this.tc) this.setTcMasked(cut !== undefined);
        // (split frames are all before WIPE_F0, so a wipe mask is at its full box whenever it is narrowed here)
        if (cut === undefined) {
          if (row) w.mask.style.width = x1 - x0 + 'px';
          w.dup.style.display = 'none';
          w.dup.replaceChildren();
          continue;
        }
        w.mask.style.width = cut - x0 + 'px';
        const clone = w.el.cloneNode(true);
        clone.style.left = w.left - cut + 'px';
        clone.style.color = rowColAt(row, cut);
        w.dup.replaceChildren(clone);
        w.dup.style.left = cut + 'px';
        w.dup.style.width = x1 - cut + 'px';
        w.dup.style.display = 'block';
      }

      // ---- beat meter
      const beatIdx = Math.floor(t / R.BEAT + 1e-9);
      const lit = beatIdx % 4;
      const beatF = fr(beatIdx * R.BEAT);
      const full = f >= FULL_BAR_F;
      for (let i = 0; i < 4; i++) {
        const m = this.meter[i];
        const on = full || i === lit;
        const mcol = colAt(true, m.x + SQ / 2);
        m.outline.setAttribute('stroke', mcol);
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
        m.fill.setAttribute('fill', downbeat || onSignal(f) ? mcol : SIGNAL);
      }
    },
  });
})();
