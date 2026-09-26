/*
 * s01-axis — Axis: LIGHT / HEAVY / NARROW / WIDE            0.000 → 1.875 s · frames 0–112 · z 10 · Ink
 *
 * Cold open. Every word performs the axis it names, one per beat, all on one Archivo size FS1 (solved at
 * setup so WIDE 900/125 inks exactly 1422 px). The full stop is born as WIDE's hanging period on the and-of-4,
 * the letters fall through the baseline and the lone dot is handed to s02 at (1731,656), Ø88.
 *
 * Techniques
 *  - Metrics from the pipeline's own Archivo: per-glyph advance, ink bearings and pair kerning sampled along
 *    wght (9 samples @ wdth 100) and wdth (11 samples @ wght 900) with fixed-axis FontFace clones on a canvas
 *    (advance = measureText, ink = coverage-weighted pixel scan). update() interpolates; it never reads layout.
 *  - Seven persistent letter columns, each an overflow-hidden slot whose bottom edge is baseline + 8:
 *    rise (LIGHT) → vertical slot swap (HEAVY) → inward horizontal rolls + a centre pinch (NARROW: the two R's
 *    squeeze the A out) → outward rolls + centre collapse (WIDE) → drop through the baseline.
 *  - Every frame the row is laid out from interpolated advances + kerning + tracking and centred on x = 960 by
 *    its INK box; rest poses are blended onto whole-pixel glyph origins so resting type never shimmers.
 *  - Squash & stretch as a container scale about the baseline (960,700): TIGHT impulse (HEAVY), POP spring
 *    (NARROW), keyed squash → overshoot → settle (WIDE), 3-frame anticipations before NARROW and WIDE.
 *  - Blueprint: Volt construction lines at the baseline and the live cap line, a Volt-light mono axis readout
 *    with odometer digits, a construction circle that predicts the full stop, then the lines retract into it.
 */
(function () {
  'use strict';

  const E = R.ease;
  const PAL = R.pal;
  const clamp = R.clamp;
  const lerp = R.lerp;
  const VOLT_LIGHT = '#718EF8';

  // ------------------------------------------------------------------------------------------ timing (grid)
  const T_BREATH = R.E8; //                 0.234375  LIGHT breathes
  const T_HEAVY = R.pos(1, 2); //           0.46875   beat 2 — THE HOOK SLAM
  const T_SWAP = 0.52734375; //                       slot swap LIGHT → HEAVY
  const T_NARROW = R.pos(1, 3); //          0.9375    beat 3
  const T_WIDE = R.pos(1, 4); //            1.40625   beat 4
  const T_DOT = R.pos(1, 4, 2); //          1.640625  and-of-4: the dot is born
  const T_EXIT = R.pos(1, 4, 3); //         1.7578125 last 16th: exit
  const T_RETRACT_END = 1.8411; //                    construction lines gone
  const T_REST = R.bar(2) - 2 / 60; //      1.841667  rest pose, held to the cut
  const AXD = R.E16; //                               axis tweens (outExpo)
  const ANT = 3 / 60; //                              anticipation length
  const FLIP = R.E16; //                              squeeze-flip length (NARROW, WIDE)
  const SPLIT = 0.3; //                               share of a flip spent folding the old letter
  const SPLIT_W = 0.2; //                             WIDE folds faster: a quick gather, then the burst
  const AX62 = { wg: 900, wd: 62 };

  // ------------------------------------------------------------------------------------------ geometry
  const BASE = 700;
  const CX = 960;
  const MASK_BELOW = 8; //                  slot bottom edge = baseline + 8
  const DOT_X = 1731, DOT_Y = 656, DOT_R = 44;
  const WIDE_INK = 1422;
  const TRACK = -0.01; //                   house tracking (em)
  const READ_X = 96;
  const READ_SIZE = 16;

  // ------------------------------------------------------------------------------------------ type data
  // Persistent letter columns. seq = the glyph each column shows in LIGHT, HEAVY, NARROW, WIDE.
  // side: -1 left of centre, +1 right (roll directions); rank: centre-out stagger index (frames).
  const COLS = [
    { seq: ['L', 'H', 'N', 'W'], side: -1, rank: 2, kern: ['LI', 'HE', 'NA', 'WI'] },
    { seq: ['I', 'E', 'A', 'I'], side: -1, rank: 1, kern: ['IG', 'EA', 'AR', 'ID'] },
    { seq: ['G', 'A'], side: 0, rank: 0, kern: ['GH', 'AV'] }, //   A is pinched out by the two R's
    { seq: ['H', 'V', 'O', 'D'], side: 1, rank: 1, kern: ['HT', 'VY', 'OW', 'DE'] },
    { seq: ['T', 'Y', 'W', 'E'], side: 1, rank: 2, kern: [null, null, null, null] },
    { seq: ['R'], side: -1, rank: 0, kern: ['RR'] }, //                NARROW's first R
    { seq: ['R'], side: 1, rank: 0, kern: ['RO'] }, //                 NARROW's second R
  ];
  const ROW = [0, 1, 5, 2, 6, 3, 4]; // visual order, left → right

  const WG = [100, 200, 300, 400, 500, 600, 700, 800, 900]; //          wght samples (wdth 100)
  const WD = [62, 69, 76, 83, 90, 97, 100, 104, 111, 118, 125]; //    wdth samples (wght 900)
  const WG_GLYPHS = 'LIGHTEAVY';
  const WD_GLYPHS = 'HEAVYNROWID';
  const WG_PAIRS = ['LI', 'IG', 'GH', 'HT', 'HE', 'EA', 'AV', 'VY'];
  const WD_PAIRS = ['HE', 'EA', 'AV', 'VY', 'NA', 'AR', 'RR', 'RO', 'OW', 'WI', 'ID', 'DE'];

  // ------------------------------------------------------------------------------------------ helpers
  const seg = (t, t0, dur, ease) => R.seg(t, t0, t0 + dur, ease);
  function interp(xs, ys, x) {
    const n = xs.length;
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 1;
    while (xs[i] < x) i++;
    return ys[i - 1] + ((ys[i] - ys[i - 1]) * (x - xs[i - 1])) / (xs[i] - xs[i - 1]);
  }
  /** outBack with a chosen overshoot constant (s = 3.4 peaks at ≈1.30). */
  function backOut(x, s) {
    x = clamp(x) - 1;
    return 1 + (s + 1) * x * x * x + s * x * x;
  }
  /** Impulse response of a damped spring (starts at 0, first peak = peak, rings back to 0). */
  function impulse(u, k, c, peak) {
    if (u <= 0) return 0;
    const w0 = Math.sqrt(k), z = c / (2 * w0), wd = w0 * Math.sqrt(1 - z * z), a = z * w0;
    const tp = Math.atan2(wd, a) / wd;
    return (peak * Math.exp(-a * u) * Math.sin(wd * u)) / (Math.exp(-a * tp) * Math.sin(wd * tp));
  }
  /** Chain of eased segments [[t, v], [t, v, ease], ...] (R.kf without colour handling). */
  function keys(t, ks) {
    if (t <= ks[0][0]) return ks[0][1];
    for (let i = 1; i < ks.length; i++) {
      if (t < ks[i][0]) {
        const a = ks[i - 1], b = ks[i];
        return lerp(a[1], b[1], R.easeFn(b[2] || 'linear')((t - a[0]) / (b[0] - a[0])));
      }
    }
    return ks[ks.length - 1][1];
  }

  // Axis values (global for the whole word).
  const wghtAt = (t) => (t < T_HEAVY ? 100 : 100 + 800 * E.outExpo(clamp((t - T_HEAVY) / AXD)));
  function wdthAt(t) {
    if (t < T_NARROW) return 100;
    if (t < T_WIDE) return 100 - 38 * E.outExpo(clamp((t - T_NARROW) / AXD));
    return 62 + 63 * E.outExpo(clamp((t - T_WIDE) / AXD));
  }
  function trackAt(t) {
    if (t < T_BREATH) return TRACK;
    if (t < T_HEAVY) return TRACK + 0.03 * E.inOutSine((t - T_BREATH) / (T_HEAVY - T_BREATH));
    return lerp(TRACK + 0.03, TRACK, E.outExpo(clamp((t - T_HEAVY) / AXD)));
  }

  // Container scale about (960, BASE): returns [sx, sy].
  const POP = { stiffness: 380, damping: 18 };
  function scaleAt(t) {
    // HEAVY: TIGHT impulse 1 → 1.06 → 1, faded to exactly 1 before the NARROW anticipation.
    if (t < T_NARROW - ANT) {
      if (t < T_HEAVY) return [1, 1];
      const u = t - T_HEAVY;
      const s = 1 + impulse(u, 420, 26, 0.06) * (1 - R.smoothstep(0.25, 0.4, u));
      return [s, s];
    }
    // Anticipation into NARROW: widen and squat a touch.
    if (t < T_NARROW) {
      const a = E.inOutSine((t - (T_NARROW - ANT)) / ANT);
      return [1 + 0.012 * a, 1 - 0.012 * a];
    }
    const narrow = (tt) => {
      const p = R.spring(tt - T_NARROW, POP);
      return [lerp(1.012, 1, p), lerp(0.988, 1.14, p)];
    };
    if (t < T_WIDE - ANT) return narrow(t);
    const pre = narrow(T_WIDE - ANT);
    // Anticipation into WIDE: pinch in and rise.
    const a0 = E.inOutSine(clamp((t - (T_WIDE - ANT)) / ANT));
    const ax = pre[0] - 0.014 * a0, ay = pre[1] + 0.014 * a0;
    if (t < T_WIDE) return [ax, ay];
    // WIDE: squash 0.92, overshoot 1.03, settled by 1.64 (horizontal follow-through mirrors it).
    const sx0 = pre[0] - 0.014, sy0 = pre[1] + 0.014;
    const T1 = T_WIDE + 0.05, T2 = T1 + 0.07, T3 = T2 + 0.06, T4 = T3 + 0.05;
    const sy = keys(t, [[T_WIDE, sy0], [T1, 0.92, 'outCubic'], [T2, 1.03, 'inOutSine'], [T3, 0.995, 'inOutSine'], [T4, 1, 'inOutSine']]);
    const sx = keys(t, [[T_WIDE, sx0], [T1, 1.04, 'outCubic'], [T2, 0.985, 'inOutSine'], [T3, 1.0025, 'inOutSine'], [T4, 1, 'inOutSine']]);
    return [sx, sy];
  }

  // ------------------------------------------------------------------------------------------ measurement
  /**
   * Measure Archivo along the two axis families with fixed-axis FontFace clones (canvas font-stretch only
   * takes keywords; a face whose descriptors pin weight/stretch clamps the variation to exactly that
   * instance). All values are returned in em.
   */
  async function measureArchivo() {
    const buf = await (await fetch('fonts/archivo-latin-wdth-normal.woff2')).arrayBuffer();
    const faces = [];
    async function face(wght, wdth) {
      const fam = `s01ax_${wght}_${String(wdth).replace('.', '_')}`;
      const f = new FontFace(fam, buf, { weight: String(wght), stretch: `${wdth}%` });
      await f.load();
      document.fonts.add(f);
      faces.push(f);
      return fam;
    }
    const REF = 1000; //                     advances / kerning
    const INK = 400, CW = 760, CH = 460, OX = 140, OY = 380; // ink scans
    const cv = document.createElement('canvas');
    cv.width = CW;
    cv.height = CH;
    const ctx = cv.getContext('2d', { willReadFrequently: true });
    const adv = (fam, w, txt) => {
      ctx.font = `${w} ${REF}px "${fam}"`;
      return ctx.measureText(txt).width / REF;
    };
    // Coverage-weighted ink extents of one glyph: [left, right, top, bottom] in em (x from origin, y up from baseline).
    function ink(fam, w, ch) {
      ctx.clearRect(0, 0, CW, CH);
      ctx.font = `${w} ${INK}px "${fam}"`;
      ctx.fillStyle = '#fff';
      ctx.textBaseline = 'alphabetic';
      ctx.fillText(ch, OX, OY);
      const d = ctx.getImageData(0, 0, CW, CH).data;
      const col = new Float32Array(CW), row = new Float32Array(CH);
      for (let y = 0; y < CH; y++) {
        let o = y * CW * 4 + 3;
        for (let x = 0; x < CW; x++, o += 4) {
          const a = d[o];
          if (a) {
            if (a > col[x]) col[x] = a;
            if (a > row[y]) row[y] = a;
          }
        }
      }
      let l = 0, r = CW - 1, t = 0, b = CH - 1;
      while (l < CW && !col[l]) l++;
      while (r > 0 && !col[r]) r--;
      while (t < CH && !row[t]) t++;
      while (b > 0 && !row[b]) b--;
      return [(l + 1 - col[l] / 255 - OX) / INK, (r + col[r] / 255 - OX) / INK, (OY - (t + 1 - row[t] / 255)) / INK, (b + row[b] / 255 - OY) / INK];
    }
    async function family(xs, fixed, glyphs, pairs, isWeight) {
      const F = { xs, adv: {}, inkL: {}, inkR: {}, kern: {} };
      for (const ch of new Set(glyphs)) { F.adv[ch] = []; F.inkL[ch] = []; F.inkR[ch] = []; }
      for (const p of pairs) F.kern[p] = [];
      for (const x of xs) {
        const w = isWeight ? x : fixed, s = isWeight ? fixed : x;
        const fam = await face(w, s);
        for (const ch of new Set(glyphs)) {
          F.adv[ch].push(adv(fam, w, ch));
          const k = ink(fam, w, ch);
          F.inkL[ch].push(k[0]);
          F.inkR[ch].push(k[1]);
        }
        for (const p of pairs) F.kern[p].push(adv(fam, w, p) - adv(fam, w, p[0]) - adv(fam, w, p[1]));
      }
      return F;
    }
    const M = {};
    M.wg = await family(WG, 100, WG_GLYPHS, WG_PAIRS, true);
    M.wd = await family(WD, 900, WD_GLYPHS, WD_PAIRS, false);
    // Vertical metrics: flat cap (H) and round overshoot (O) at 900/100.
    const famV = await face(900, 100);
    M.cap = ink(famV, 900, 'H')[2];
    M.roundTop = ink(famV, 900, 'O')[2];
    for (const f of faces) document.fonts.delete(f);
    return M;
  }

  /** Distance from an element's top to its text baseline for a given CSS font + line-height (DOM truth). */
  function baselineOffset(font, lineHeight) {
    const probe = R.el('div', { style: { font, lineHeight, whiteSpace: 'pre', visibility: 'hidden' } }, document.body);
    probe.textContent = 'H';
    const mk = document.createElement('span');
    Object.assign(mk.style, { display: 'inline-block', width: '0px', height: '0px', verticalAlign: 'baseline' });
    probe.appendChild(mk);
    const off = mk.getBoundingClientRect().top - probe.getBoundingClientRect().top;
    probe.remove();
    return off;
  }

  // ------------------------------------------------------------------------------------------ scene
  R.scene({
    id: 's01-axis',
    start: 0,
    end: 1.875,
    z: 10,
    bg: PAL.ink,

    async setup(root) {
      // ---- global FX + sound (time-based; registered here so the post-FX and the soundtrack see them)
      R.cue(0.0, 'shake', { amt: 4, dur: 0.15 }); //                cold-open impact
      R.cue(0.0, 'zoom', { amt: 0.03, dur: 0.2 }); //               cold-open punch: frame 0 lands 3% zoomed
      R.cue(0.46875, 'shake', { amt: 10, dur: 0.2 }); //            HEAVY slam
      R.cue(0.46875, 'zoom', { amt: 0.06, dur: 0.234375 }); //      HEAVY slam: THE HOOK
      R.cue(0.9375, 'zoom', { amt: 0.025, dur: 0.15 }); //          NARROW squeeze
      R.cue(1.40625, 'chroma', { amt: 4, dur: 0.12 }); //           WIDE chroma kiss
      R.cue(1.40625, 'zoom', { amt: 0.035, dur: 0.18 }); //         WIDE

      R.sfx(0.0, 'impact', { amt: 0.8, tone: 'sub' }); //            cold open
      R.sfx(0.0, 'shimmer', { dur: 0.46875, amt: 0.3 }); //         glassy LIGHT bed
      R.sfx(0.46875, 'impact', { amt: 1.0 }); //                    HEAVY slam
      R.sfx(0.9375, 'swish', { amt: 0.5 }); //                      NARROW squeeze
      R.sfx(1.40625, 'impact', { amt: 0.55 }); //                   WIDE stab
      R.sfx(1.640625, 'pop', { pitch: 2.0 }); //                    the dot is born
      R.sfx(1.7578125, 'whoosh', { dur: 0.1171875, dir: 'down' }); // letters drop

      // ---- measure (fonts first)
      await document.fonts.load(`900 100px ${R.font.display}`, 'WIDE');
      await document.fonts.load(`500 16px ${R.font.mono}`, 'wght 0123456789');
      await document.fonts.ready;
      const M = await measureArchivo();
      this.M = M;

      // FS1: WIDE (900/125, house tracking) inks exactly WIDE_INK px.
      const g = (F, key, ch, x) => interp(F.xs, F[key][ch], x);
      const kn = (F, p, x) => interp(F.xs, F.kern[p], x);
      const wideEm =
        g(M.wd, 'adv', 'W', 125) + kn(M.wd, 'WI', 125) + TRACK +
        g(M.wd, 'adv', 'I', 125) + kn(M.wd, 'ID', 125) + TRACK +
        g(M.wd, 'adv', 'D', 125) + kn(M.wd, 'DE', 125) + TRACK +
        g(M.wd, 'inkR', 'E', 125) - g(M.wd, 'inkL', 'W', 125);
      const FS = (this.FS = WIDE_INK / wideEm);
      this.CAP = M.cap * FS;
      this.maskTop = BASE - M.roundTop * FS - MASK_BELOW;
      this.maskH = BASE + MASK_BELOW - this.maskTop;
      const fontFS = `900 ${FS}px ${R.font.display}`;
      this.glyphTop = BASE - baselineOffset(fontFS, `${FS}px`) - this.maskTop; // glyph span top inside a slot
      this.pad = 0.03 * FS;

      // ---- construction lines (behind the type)
      const line = () => R.el('div', { style: { height: '1px', background: PAL.volt, display: 'none' } }, root);
      this.lineBase = line();
      this.lineCap = line();

      // ---- construction circle predicting the full stop (SVG so the stroke can draw on)
      const svg = R.svgLayer(root);
      this.cc = R.svg('circle', { cx: DOT_X, cy: DOT_Y, r: DOT_R + 0.5, fill: 'none', stroke: PAL.volt, 'stroke-width': 1, transform: `rotate(-90 ${DOT_X} ${DOT_Y})` }, svg);
      this.ccH = R.svg('path', { d: `M${DOT_X - 14} ${DOT_Y + 0.5}H${DOT_X + 14}M${DOT_X + 0.5} ${DOT_Y - 14}V${DOT_Y + 14}`, stroke: PAL.volt, 'stroke-width': 1, fill: 'none' }, svg);
      this.ccLen = 2 * Math.PI * (DOT_R + 0.5);
      this.svg = svg;

      // ---- the word: container scaled about (960, BASE); one overflow-hidden slot per column
      this.word = R.el('div', { style: { width: R.W + 'px', height: R.H + 'px', transformOrigin: `${CX}px ${BASE}px` } }, root);
      this.cols = COLS.map((c) => {
        const slot = R.el('div', { style: { top: this.maskTop + 'px', height: this.maskH + 'px', overflow: 'hidden', display: 'none' } }, this.word);
        const glyphs = c.seq.map((ch) =>
          R.el('span', {
            text: ch,
            style: {
              top: this.glyphTop + 'px', fontFamily: R.font.display, fontSize: FS + 'px', lineHeight: FS + 'px', fontWeight: '900',
              whiteSpace: 'pre', color: PAL.paper, transformOrigin: '0 0', fontKerning: 'none', display: 'none',
            },
          }, slot));
        return Object.assign({ slot, glyphs }, c);
      });

      // ---- axis readout: JetBrains Mono 500 16 px, Volt-light, fixed cells (tabular), odometer digits
      const RS = READ_SIZE, cellW = 0.6 * RS + 0.12 * RS, cellH = 20;
      this.readCell = cellW;
      this.readBase = baselineOffset(`500 ${RS}px ${R.font.mono}`, cellH + 'px');
      this.read = R.el('div', { style: { left: READ_X + 'px', width: Math.ceil(19 * cellW + 4) + 'px', height: cellH + 'px', font: `500 ${RS}px ${R.font.mono}`, lineHeight: cellH + 'px', color: VOLT_LIGHT } }, root);
      const text = 'wght 100   wdth 100';
      this.cells = [];
      for (let i = 0; i < text.length; i++) {
        const cell = R.el('div', { style: { left: (i * cellW).toFixed(3) + 'px', width: Math.ceil(cellW) + 'px', height: cellH + 'px', overflow: 'hidden' } }, this.read);
        const a = R.el('span', { text: text[i], style: { whiteSpace: 'pre' } }, cell);
        const b = R.el('span', { text: '', style: { whiteSpace: 'pre', display: 'none' } }, cell);
        this.cells.push({ cell, a, b, ch: text[i] });
      }
      // digit changes: [cell index, values over events]
      this.odo = [
        { i: 5, ev: [[T_HEAVY, '1', '9', 0]] },
        { i: 16, ev: [[T_NARROW, '1', ' ', 0], [T_WIDE, ' ', '1', 0]] },
        { i: 17, ev: [[T_NARROW, '0', '6', 1], [T_WIDE, '6', '2', 1]] },
        { i: 18, ev: [[T_NARROW, '0', '2', 2], [T_WIDE, '2', '5', 2]] },
      ];
      this.cursor = R.el('div', { style: { width: Math.round(cellW - 2) + 'px', height: '13px', background: VOLT_LIGHT, display: 'none' } }, this.read);

      // ---- the dot: canvas arc (same primitive as s02, so the shared still is pixel-identical)
      const dc = R.canvas(root);
      this.dctx = dc.ctx;
    },

    // ---------------------------------------------------------------------------------------- per-glyph metrics
    /** Metrics of glyph ch at the current axes, in px. */
    gm(ch, ax) {
      const M = this.M, FS = this.FS;
      const F = ax.wd === 100 ? M.wg : M.wd;
      const x = ax.wd === 100 ? ax.wg : ax.wd;
      return { adv: interp(F.xs, F.adv[ch], x) * FS, inkL: interp(F.xs, F.inkL[ch], x) * FS, inkR: interp(F.xs, F.inkR[ch], x) * FS };
    },
    kern(p, ax) {
      if (!p) return 0;
      const M = this.M;
      const F = ax.wd === 100 ? M.wg : M.wd;
      const x = ax.wd === 100 ? ax.wg : ax.wd;
      return interp(F.xs, F.kern[p], x) * this.FS;
    },

    /**
     * State of one column at time t: allocation width w (pen advance, before kern/track), trailing kern,
     * tracking presence, ink bearings for centring, mask [mL, mR] relative to the pen and the visible glyphs
     * [{k: glyph index, x, y, sx}] (x relative to the pen, y relative to rest).
     */
    column(ci, t, ax) {
      const c = COLS[ci], FS = this.FS, pad = this.pad, D = 1.1 * FS;
      const st = { w: 0, kern: 0, trk: 0, inkL: 0, inkR: 0, mL: 0, mR: 0, gl: [] };
      const side = c.side;
      if (ci >= 5) {
        // the two R's: unfold out of the A's slot in NARROW, fold away in WIDE
        if (t < T_NARROW) return st;
        const m = this.gm('R', ax), kr = this.kern(c.kern[0], ax);
        if (t < T_WIDE) return this.flip(st, null, m, 0, kr, (t - T_NARROW - c.rank / 60) / FLIP);
        return this.flip(st, this.gm('R', AX62), null, this.kern(c.kern[0], AX62), 0, (t - T_WIDE - c.rank / 60) / FLIP, 0, 0, AX62);
      }

      if (t < T_NARROW) {
        // LIGHT rises out of the baseline; at T_SWAP each slot rolls up to HEAVY.
        const rise = E.swift(clamp((t - (-0.06 + ci / 60)) / 0.28));
        const e = E.swift(clamp((t - (T_SWAP + ci / 60)) / 0.1));
        const a = this.gm(c.seq[0], ax), b = this.gm(c.seq[1], ax);
        st.w = lerp(a.adv, b.adv, e);
        st.kern = lerp(this.kern(c.kern[0], ax), this.kern(c.kern[1], ax), e);
        st.trk = 1;
        st.inkL = lerp(a.inkL, b.inkL, e);
        st.inkR = lerp(a.inkR, b.inkR, e);
        st.mL = Math.min(0, a.inkL, e > 0 ? b.inkL : 0) - pad;
        st.mR = Math.max(a.adv, a.inkR, e > 0 ? Math.max(b.adv, b.inkR) : 0) + pad;
        if (e < 1) st.gl.push({ k: 0, x: 0, y: D * (1 - rise) - D * e, sx: 1 });
        if (e > 0) st.gl.push({ k: 1, x: 0, y: D * (1 - e), sx: 1 });
        return st;
      }

      if (t < T_WIDE) {
        // HEAVY → NARROW: squeeze-flips staggered from the centre out; the A folds away and the two R's unfold
        const q = (t - T_NARROW - c.rank / 60) / FLIP;
        if (ci === 2) return this.flip(st, this.gm('A', ax), null, this.kern('AV', ax), 0, q, 1);
        return this.flip(st, this.gm(c.seq[1], ax), this.gm(c.seq[2], ax), this.kern(c.kern[1], ax), this.kern(c.kern[2], ax), q, 1, 2);
      }

      // WIDE: NARROW → WIDE flips, then the drop through the baseline (right → left from E).
      if (ci === 2) return st;
      const q = (t - T_WIDE - c.rank / 60) / FLIP;
      // outgoing NARROW letters keep their width while they fold; incoming WIDE letters ride the tween
      this.flip(st, this.gm(c.seq[2], AX62), this.gm(c.seq[3], ax), this.kern(c.kern[2], AX62), this.kern(c.kern[3], ax), q, 2, 3, AX62, null, SPLIT_W);
      if (t >= T_EXIT) {
        const order = [3, 2, null, 1, 0][ci]; // E first, then D, I, W
        const qd = clamp((t - (T_EXIT + order / 120)) / 0.07);
        const y = D * E.inCubic(qd);
        for (const gl of st.gl) gl.y += y;
      }
      return st;
    },

    /**
     * Squeeze-flip inside one slot: glyph a folds to zero width (linear, SPLIT of the time), then glyph b
     * unfolds (swift). a = null → unfold only; b = null → fold only (the slot then closes for good).
     * The allocation follows the glyph, so in the centred row every letter folds about its own centre.
     */
    flip(st, a, b, kA, kB, q, ia = 0, ib = 0, axA = null, axB = null, split = SPLIT) {
      const pad = this.pad;
      let m, f, k, kn, gax;
      if (q < split) {
        if (!a) return st;
        f = 1 - clamp(q / split);
        m = a; k = ia; kn = kA; gax = axA;
      } else {
        if (!b) return st;
        f = E.swift(clamp((q - split) / (1 - split)));
        m = b; k = ib; kn = kB; gax = axB;
      }
      if (f <= 0) return st;
      st.w = m.adv * f;
      st.kern = kn * f;
      st.trk = a && b ? 1 : f;
      st.inkL = m.inkL * f;
      st.inkR = m.inkR * f;
      st.mL = Math.min(0, st.inkL) - pad;
      st.mR = Math.max(st.w, st.inkR) + pad;
      st.gl.push({ k, x: 0, y: 0, sx: f, ax: gax });
      return st;
    },

    update(t) {
      if (!this.M) return;
      const rest = t >= T_REST;
      const ax = { wg: wghtAt(t), wd: wdthAt(t) };
      const [sx, sy] = scaleAt(t);
      const FS = this.FS;

      // ------------------------------------------------ the word
      this.word.style.display = rest ? 'none' : 'block';
      this.word.style.transform = sx === 1 && sy === 1 ? 'none' : `scale(${sx.toFixed(5)},${sy.toFixed(5)})`;
      const trackPx = trackAt(t) * FS;
      const states = [];
      let x = 0;
      for (let r = 0; r < ROW.length; r++) {
        const ci = ROW[r];
        const s = this.column(ci, t, ax);
        s.x = x;
        states[ci] = s;
        if (r < ROW.length - 1) x += s.w + s.kern + s.trk * trackPx;
      }
      const inkLeft = states[0].x + states[0].inkL;
      const inkRight = states[4].x + states[4].inkR;
      const shift = CX - (inkLeft + inkRight) / 2;
      const wStr = ax.wg.toFixed(2), sStr = ax.wd.toFixed(3) + '%';
      for (let ci = 0; ci < COLS.length; ci++) {
        const col = this.cols[ci], s = states[ci];
        const vis = !rest && s.gl.length > 0 && s.mR - s.mL > 0.5;
        col.slot.style.display = vis ? 'block' : 'none';
        const left = shift + s.x + s.mL;
        col.slot.style.left = left.toFixed(3) + 'px';
        col.slot.style.width = Math.max(0, s.mR - s.mL).toFixed(3) + 'px';
        for (let k = 0; k < col.glyphs.length; k++) col.glyphs[k].style.display = 'none';
        if (!vis) continue;
        for (const gl of s.gl) {
          const el = col.glyphs[gl.k];
          el.style.display = 'block';
          el.style.fontWeight = gl.ax ? gl.ax.wg.toFixed(2) : wStr;
          el.style.fontStretch = gl.ax ? gl.ax.wd.toFixed(3) + '%' : sStr;
          const gx = gl.x - s.mL;
          el.style.transform = `translate(${gx.toFixed(3)}px,${gl.y.toFixed(3)}px)` + (gl.sx !== 1 ? ` scale(${gl.sx.toFixed(5)},1)` : '');
        }
      }

      // ------------------------------------------------ construction lines
      const capY = BASE - this.CAP * sy;
      const shoot = E.outCubic(clamp((t + 0.02) / (R.E8 + 0.02)));
      const ret = E.inCubic(clamp((t - T_EXIT) / (T_RETRACT_END - T_EXIT)));
      let xL = lerp(CX - CX * shoot, DOT_X, ret), xR = lerp(CX + (R.W - CX) * shoot, DOT_X, ret);
      const yB = lerp(BASE, DOT_Y, ret), yC = lerp(capY, DOT_Y, ret);
      const linesOn = !rest && t < T_RETRACT_END && xR - xL >= 1;
      for (const [el, y] of [[this.lineBase, Math.round(yB)], [this.lineCap, Math.round(yC) - 1]]) {
        el.style.display = linesOn ? 'block' : 'none';
        el.style.left = Math.round(xL) + 'px';
        el.style.width = Math.max(0, Math.round(xR) - Math.round(xL)) + 'px';
        el.style.top = y + 'px';
      }

      // ------------------------------------------------ construction circle (predicts the full stop)
      const ccIn = seg(t, T_WIDE + 0.07, 0.15, 'swift');
      const ccOn = !rest && ccIn > 0 && t < T_DOT + 0.05;
      this.svg.style.display = ccOn ? 'block' : 'none';
      this.cc.style.strokeDasharray = `${(this.ccLen * ccIn).toFixed(2)} ${this.ccLen.toFixed(2)}`;
      this.ccH.style.opacity = ccIn.toFixed(3);

      // ------------------------------------------------ readout
      const baseY = Math.round(capY - 16);
      this.read.style.display = rest ? 'none' : 'block';
      this.read.style.top = baseY - this.readBase + 'px';
      const typed = (t - 0.03) / (0.12 / 19);
      for (let i = 0; i < this.cells.length; i++) {
        const c = this.cells[i];
        c.cell.style.display = typed >= i + 1 ? 'block' : 'none';
        c.a.style.transform = 'none';
        c.b.style.display = 'none';
        c.a.textContent = c.ch;
      }
      for (const o of this.odo) {
        const c = this.cells[o.i];
        let cur = c.ch;
        for (const [tc, from, to, k] of o.ev) {
          if (t < tc) break;
          const q = E.swift(clamp((t - tc - (k * 2) / 60) / R.E16));
          cur = to;
          if (q < 1) {
            c.a.textContent = from;
            c.b.textContent = to;
            c.a.style.transform = `translateY(${-Math.round(20 * q)}px)`;
            c.b.style.display = 'block';
            c.b.style.transform = `translateY(${Math.round(20 * (1 - q))}px)`;
          } else {
            c.a.textContent = to;
          }
        }
        if (t < o.ev[0][0]) c.a.textContent = o.ev[0][1];
      }
      const typing = t >= 0.03 && t < 0.03 + 0.12 + 1 / 60;
      this.cursor.style.display = typing ? 'block' : 'none';
      this.cursor.style.left = (Math.min(19, Math.floor(Math.max(0, typed))) * this.readCell + 1).toFixed(2) + 'px';
      this.cursor.style.top = '4px';
      const wipe = E.inCubic(clamp((t - T_EXIT) / (T_RETRACT_END - T_EXIT)));
      this.read.style.clipPath = wipe > 0 ? `inset(0 0 0 ${(wipe * 100).toFixed(2)}%)` : 'none';

      // ------------------------------------------------ the dot
      const ctx = this.dctx;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, R.W, R.H);
      if (t >= T_DOT) {
        const s = rest ? 1 : backOut((t - T_DOT) / AXD, 3.4);
        if (s > 0) {
          ctx.setTransform(s, 0, 0, s, DOT_X, DOT_Y);
          ctx.beginPath();
          ctx.arc(0, 0, DOT_R, 0, R.TAU);
          ctx.setTransform(1, 0, 0, 1, 0, 0);
          ctx.fillStyle = PAL.signal;
          ctx.fill();
        }
      }
    },
  });
})();
