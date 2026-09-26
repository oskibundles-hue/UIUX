// s06-range-1 — Range I: C · L · A · U   (9.140625 → 11.25 s, frames 549–674, z 60, transparent root)
//
// A centre-locked, one-beat montage. Four vignette renderers share one opaque "world panel":
//   C  HALFTONE  canvas halftone of the C (22 px lattice at 15°), rings rippling out of the dot
//   L  GRID      13 × 7 Swiss module grid; 20 modules fill the L, then morph square → circle
//   A  LIQUID    SVG goo (blur + alpha threshold): blobs converge into an A, the dot drips through
//   U  DATA      bars + half-donut sweep + counters form a U with the dot at the chart origin
// The panel whip-pans in on top of s05 along the shared camera function P(t) = 1920·inOutCubic(u)
// (panel x = 1920 − P(t)); left of the panel edge the root is transparent. The protagonist (a flat
// Signal disc Ø112) is locked to (960,540) on every cut and squash-pops there.
//
// Pure function of t: glyph rasters, halftone coverage, the A's counter/contour and all font metrics
// are measured once in setup(); update() only evaluates closed-form motion and redraws.
(() => {
  'use strict';
  const { ink: INK, paper: PAPER, signal: SIGNAL, volt: VOLT, graphite: GRAPHITE, fog: FOG } = R.pal;
  const VOLT_LIGHT = '#718EF8'; // mix(Volt, Paper, 0.35): small Volt labels on Ink
  const FPS = R.FPS, TAU = Math.PI * 2, W = R.W, H = R.H;
  const E = R.ease, clamp = R.clamp, lerp = R.lerp;
  const MONO = R.font.mono, DISPLAY = R.font.display;
  const fr = (t) => Math.ceil(t * FPS - 1e-6); // first frame on which a grid event at t is visible
  const fOf = (t) => Math.round(t * FPS); // frame index being rendered

  // ---------------------------------------------------------------- timing (grid seconds)
  const T_IN = 9.140625, WHIP = R.E8;
  const T_C = 9.375, T_C_AND = 9.609375;
  const T_L = 9.84375, T_L_AND = 10.078125;
  const T_A = 10.3125, T_A_SET = 10.4296875, T_A_DRIP = 10.546875;
  const T_U = 10.78125, T_U_R = 10.8984375, T_U_LOCK = 11.1328125, T_END = 11.25;
  const CUTS = [T_C, T_L, T_A, T_U];
  const GROUND = [PAPER, INK, VOLT, PAPER];
  const HUD_COL = [INK, PAPER, PAPER, INK]; // storyboard HUD colour schedule: frames 563 / 591 / 647
  const CAPTIONS = ['C — HALFTONE', 'L — GRID', 'A — LIQUID', 'U — DATA'];
  const vignetteAt = (t) => (t < T_L ? 0 : t < T_A ? 1 : t < T_U ? 2 : 3);

  const AX = 960, AY = 540, DOT = 112, DOT_R = 56;
  const TIGHT = { stiffness: 420, damping: 26 };
  const POP = { stiffness: 380, damping: 18 };
  const WOBBLE = { stiffness: 300, damping: 10 };
  const BAR_SPRING = { stiffness: 260, damping: 18 };

  // ---------------------------------------------------------------- shared whip (handoff protocol)
  const whipU = (t) => clamp((t - T_IN) / WHIP);
  const P = (t) => 1920 * E.inOutCubic(whipU(t));
  const dP = (t) => {
    const u = (t - T_IN) / WHIP;
    if (u <= 0 || u >= 1) return 0;
    return (1920 / WHIP) * (u < 0.5 ? 12 * u * u : 3 * (2 - 2 * u) * (2 - 2 * u));
  };
  const DP_MAX = (1920 / WHIP) * 3; // 24 576 px/s at u = 0.5

  // ---------------------------------------------------------------- motion helpers
  /** Impulse response of a damped spring, normalised to a peak of 1 (0 → 1 → small undershoot → 0). */
  function impulse(tau, sp) {
    if (tau <= 0) return 0;
    const w0 = Math.sqrt(sp.stiffness), z = sp.damping / (2 * w0), wd = w0 * Math.sqrt(1 - z * z);
    const tp = Math.atan2(wd, z * w0) / wd;
    const peak = Math.exp(-z * w0 * tp) * Math.sin(wd * tp);
    return (Math.exp(-z * w0 * tau) * Math.sin(wd * tau)) / peak;
  }
  /** First time the step response of a spring crosses 1 (s). */
  function springCross(sp) {
    const w0 = Math.sqrt(sp.stiffness), z = sp.damping / (2 * w0), wd = w0 * Math.sqrt(1 - z * z);
    return (Math.PI - Math.atan2(wd, z * w0)) / wd;
  }
  const POP_CROSS = springCross(POP);
  /** Cut squash-pop: 1.25 × 0.8 on the cut frame, back through rest by the 3rd frame (POP at 2.3× speed). */
  const POP_SPEED = 2.3;
  function cutDeform(t) {
    let tc = -1;
    for (const c of CUTS) if (t >= c) tc = c;
    if (tc < 0) return 0;
    const d = 1 - R.spring((t - tc) * POP_SPEED, POP);
    return Math.abs(d) < 5e-4 ? 0 : d;
  }
  const smoothstep = R.smoothstep;
  const quadBez = (a, c, b, q) => {
    const m = 1 - q;
    return [m * m * a[0] + 2 * m * q * c[0] + q * q * b[0], m * m * a[1] + 2 * m * q * c[1] + q * q * b[1]];
  };

  // ---------------------------------------------------------------- measurement helpers (setup only)
  function glyphRaster(ch, weight, size, x, y) {
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    const g = c.getContext('2d', { willReadFrequently: true });
    g.font = `${weight} ${size}px ${DISPLAY}`;
    g.fontStretch = 'normal';
    g.fillStyle = '#fff';
    g.textBaseline = 'alphabetic';
    g.fillText(ch, x, y);
    const d = g.getImageData(0, 0, W, H).data;
    const a = new Uint8Array(W * H);
    for (let i = 0; i < W * H; i++) a[i] = d[i * 4 + 3];
    return a;
  }
  function inkBox(a) {
    let x0 = W, x1 = -1, y0 = H, y1 = -1;
    for (let y = 0; y < H; y++) {
      const row = y * W;
      for (let x = 0; x < W; x++) {
        if (a[row + x] > 127) {
          if (x < x0) x0 = x;
          if (x > x1) x1 = x;
          if (y < y0) y0 = y;
          y1 = y;
        }
      }
    }
    return { x0, x1: x1 + 1, y0, y1: y1 + 1 }; // half-open box, like the storyboard's "x 560→1323"
  }
  function monoMetrics(weight, size) {
    const g = document.createElement('canvas').getContext('2d');
    g.font = `${weight} ${size}px ${MONO}`;
    return { adv: g.measureText('0000000000').width / 10, cap: g.measureText('H').actualBoundingBoxAscent };
  }

  // =================================================================================================
  R.scene({
    id: 's06-range-1',
    start: T_IN,
    end: T_END,
    z: 60,
    // bg: none — transparent root; during the overlap only the opaque world panel covers s05.

    setup(root) {
      root.style.pointerEvents = 'none';
      this.panel = R.el('div', { style: { width: W + 'px', height: H + 'px', overflow: 'hidden', background: PAPER } }, root);
      // Motion-blurred leading edge of the whip: a Paper ramp just LEFT of the (fully opaque) panel, as
      // long as the edge's travel over half a frame (the same 180° shutter s05 uses for its streaks), so
      // the seam smears like the rest of the one camera move.
      this.edge = R.el('div', { style: { width: '1px', height: H + 'px', transformOrigin: '0 0', background: `linear-gradient(to right, ${R.rgba(PAPER, 0)}, ${R.rgba(PAPER, 1)})`, display: 'none' } }, root);
      const cv = R.canvas(this.panel);
      this.ctx = cv.ctx;

      this.setupC();
      this.setupL();
      this.setupA();
      this.setupU();

      // The protagonist: one flat Signal disc, Ø112, centred on the anchor (x 904→1016, y 484→596).
      this.dot = R.el('div', {
        style: { left: AX - DOT_R + 'px', top: AY - DOT_R + 'px', width: DOT + 'px', height: DOT + 'px', borderRadius: '50%', background: SIGNAL, transformOrigin: '50% 50%' },
      }, this.panel);

      // Montage caption: JetBrains Mono 500 20 px, uppercase, tracking 0.12em, HUD colour, x 72, baseline 976.
      const CAP_FS = 20, CAP_LS = 0.12 * CAP_FS;
      const capStyle = { font: `500 ${CAP_FS}px ${MONO}`, letterSpacing: CAP_LS + 'px', lineHeight: CAP_FS + 'px', textTransform: 'uppercase', whiteSpace: 'pre', fontKerning: 'none', fontVariantNumeric: 'tabular-nums' };
      // (scene roots are display:none during setup, so the probe lives on <body>)
      const probe = R.el('div', { style: Object.assign({}, capStyle, { visibility: 'hidden' }) }, document.body);
      probe.textContent = '0000000000';
      const adv10 = probe.getBoundingClientRect().width;
      const mark = R.el('span', { style: { position: 'static', display: 'inline-block', width: '0px', height: '0px', verticalAlign: 'baseline' } });
      probe.appendChild(mark);
      const baseOff = mark.getBoundingClientRect().top - probe.getBoundingClientRect().top;
      document.body.removeChild(probe);
      this.capAdv = adv10 / 10;
      this.capCapH = monoMetrics(500, CAP_FS).cap;
      this.caption = R.el('div', { style: Object.assign({}, capStyle, { left: '72px', top: Math.round(976 - baseOff) + 'px' }) }, this.panel);
      // Block cursor (the HUD's typing language): Signal, 0.6 em × cap height, rides the insertion point.
      this.cursor = R.el('div', { style: { width: Math.round(0.6 * CAP_FS) + 'px', height: Math.round(this.capCapH) + 'px', top: Math.round(976 - this.capCapH) + 'px', background: SIGNAL } }, this.panel);

      // ------------------------------------------------------------ global FX cues (storyboard)
      R.cue(9.375, 'shake', { amt: 6, dur: 0.15 }); // whip lands on C
      R.cue(9.375, 'zoom', { amt: 0.04, dur: 0.15 }); // whip lands on C
      R.cue(9.84375, 'chroma', { amt: 3, dur: 0.1 }); // cut to L
      R.cue(9.84375, 'shake', { amt: 4, dur: 0.1 }); // cut to L
      R.cue(10.3125, 'chroma', { amt: 3, dur: 0.1 }); // cut to A
      R.cue(10.3125, 'shake', { amt: 4, dur: 0.1 }); // cut to A
      R.cue(10.78125, 'chroma', { amt: 3, dur: 0.1 }); // cut to U
      R.cue(10.78125, 'shake', { amt: 4, dur: 0.1 }); // cut to U

      // ------------------------------------------------------------ sound (storyboard)
      R.sfx(9.375, 'glitch', { dur: 0.1 }); // halftone fizz
      R.sfx(9.609375, 'blip', { pitch: 1.5 }); // ripple pulse
      R.sfx(9.84375, 'tick', { pitch: 1.0 }); // module fill
      R.sfx(9.9609375, 'tick', { pitch: 1.0 }); // module fill
      R.sfx(10.078125, 'blip', { pitch: 0.75 }); // square→circle
      R.sfx(10.1953125, 'tick', { pitch: 1.0 }); // module click
      R.sfx(10.3125, 'pop', { pitch: 0.5 }); // liquid bloop
      R.sfx(10.3125, 'swish', { amt: 0.4 }); // blobs rush in
      R.sfx(10.546875, 'pop', { pitch: 2.5 }); // drip plip
      R.sfx(10.78125, 'blip', { pitch: 1.0 }); // data
      R.sfx(10.8984375, 'blip', { pitch: 1.19 }); // data
      R.sfx(11.015625, 'blip', { pitch: 1.5 }); // data
      R.sfx(10.8984375, 'whoosh', { dur: 0.234375, dir: 'up' }); // arc sweep
      R.sfx(11.1328125, 'pop', { pitch: 2.0 }); // data point locked
    },

    // ============================================================================ C — HALFTONE
    setupC() {
      // Reference placement (storyboard): Archivo 900 / 100%, 1109 px, origin x 510, baseline 922
      // → ink x 560→1323, y 146→935. Re-derived here: if this Chromium's ink box drifts, re-centre it.
      let ox = 510, oy = 922;
      let a = glyphRaster('C', 900, 1109, ox, oy);
      let box = inkBox(a);
      const dx = Math.round((560 + 1323 - box.x0 - box.x1) / 2), dy = Math.round((146 + 935 - box.y0 - box.y1) / 2);
      if (dx || dy) { ox += dx; oy += dy; a = glyphRaster('C', 900, 1109, ox, oy); box = inkBox(a); }
      this.cBox = box;

      // Square lattice, pitch 22, rotated 15° about the anchor. Coverage = mean glyph alpha over the
      // rotated cell (6 × 6 supersamples), sampled once.
      const PITCH = 22, cs = Math.cos(R.deg(15)), sn = Math.sin(R.deg(15));
      const cells = [];
      for (let j = -32; j <= 32; j++) {
        for (let i = -32; i <= 32; i++) {
          const x = AX + (i * cs - j * sn) * PITCH, y = AY + (i * sn + j * cs) * PITCH;
          if (x < box.x0 - PITCH || x > box.x1 + PITCH || y < box.y0 - PITCH || y > box.y1 + PITCH) continue;
          let acc = 0;
          for (let b = 0; b < 6; b++) {
            for (let q = 0; q < 6; q++) {
              const u = ((q + 0.5) / 6 - 0.5) * PITCH, v = ((b + 0.5) / 6 - 0.5) * PITCH;
              const sx = Math.round(x + u * cs - v * sn), sy = Math.round(y + u * sn + v * cs);
              if (sx >= 0 && sx < W && sy >= 0 && sy < H) acc += a[sy * W + sx];
            }
          }
          const cov = acc / (36 * 255);
          if (cov < 0.03) continue;
          const d = Math.hypot(x - AX, y - AY);
          // Heat bloom: mix(Ink, Signal, clamp(1 − d/260)), quantised to 1/64 steps for batching.
          const heat = Math.round(clamp(1 - d / 260) * 64);
          cells.push({ x, y, cov, d, heat });
        }
      }
      cells.sort((p, q) => p.heat - q.heat);
      const n = cells.length;
      this.cX = new Float32Array(n); this.cY = new Float32Array(n); this.cC = new Float32Array(n); this.cD = new Float32Array(n);
      this.cBuckets = [];
      for (let k = 0; k < n; k++) {
        const c = cells[k];
        this.cX[k] = c.x; this.cY[k] = c.y; this.cC[k] = c.cov; this.cD[k] = c.d;
        const last = this.cBuckets[this.cBuckets.length - 1];
        if (!last || last.heat !== c.heat) this.cBuckets.push({ heat: c.heat, i0: k, i1: k + 1, color: R.mixColor(INK, SIGNAL, c.heat / 64) });
        else last.i1 = k + 1;
      }
    },

    drawC(ctx, t, smear) {
      const phase = (4 * (t - T_C)) / R.BEAT; // 4 rings per beat
      const amp = 0.28 + 0.32 * impulse(t - T_C_AND, TIGHT); // the and: 0.28 → 0.6 → 0.28
      const X = this.cX, Y = this.cY, C = this.cC, D = this.cD;
      const smeared = smear > 1.001;
      for (const bk of this.cBuckets) {
        ctx.fillStyle = bk.color;
        ctx.beginPath();
        for (let k = bk.i0; k < bk.i1; k++) {
          const dia = 21 * C[k] * (0.72 + amp * Math.sin(TAU * (D[k] / 200 - phase)));
          if (dia < 0.6) continue;
          const r = dia / 2, x = X[k], y = Y[k];
          if (smeared) { ctx.moveTo(x + r * smear, y); ctx.ellipse(x, y, r * smear, r, 0, 0, TAU); }
          else { ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, TAU); }
        }
        ctx.fill();
      }
    },

    // ============================================================================ L — GRID
    setupL() {
      // 13 × 7 modules, 112 px, pitch 128: centres x = 960 + 128(c − 7), y = 540 + 128(r − 4).
      const mods = [];
      const push = (c, r) => mods.push({ c, r, x: 960 + 128 * (c - 7), y: 540 + 128 * (r - 4) });
      // Fill order follows the stroke: stem top → corner (cols 5–6, rows 1–6), then the foot (cols 7–10, rows 5–6).
      for (let r = 1; r <= 6; r++) { push(5, r); push(6, r); }
      for (let c = 7; c <= 10; c++) { push(c, 5); push(c, 6); }
      mods.forEach((m, k) => {
        m.pair = k >> 1;
        // Square → circle wave radiates from the protagonist: ≤ 3.3 frames of spread.
        m.morphDelay = (Math.hypot(m.x - AX, m.y - AY) - 128) / 128 / FPS;
      });
      this.lMods = mods;
      this.lFill0 = fr(T_L); // first L frame: pair k lands on frame lFill0 + k (2 modules / frame)
      const lab = monoMetrics(500, 14);
      this.lLabAdv = lab.adv + 0.12 * 14;
      this.lLS = 0.12 * 14;
    },

    drawL(ctx, t) {
      const f = fOf(t);
      // ---- module grid outlines: Graphite 1 px (Fog on the 2 cut frames), knocked out behind the caption.
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, W, H);
      ctx.rect(62, 948, 150, 40);
      ctx.clip('evenodd');
      ctx.beginPath();
      for (let c = 1; c <= 13; c++) {
        const x0 = 960 + 128 * (c - 7) - 56;
        for (let r = 1; r <= 7; r++) ctx.rect(x0 + 0.5, 540 + 128 * (r - 4) - 56 + 0.5, 111, 111);
      }
      ctx.lineWidth = 1;
      ctx.strokeStyle = f - this.lFill0 < 2 ? FOG : GRAPHITE;
      ctx.stroke();
      ctx.restore();

      // ---- the L: 20 Paper modules; each pops 0.6 → 1 (swift, 4 frames), 2 per frame along the stroke;
      // on the and every module morphs square → circle (corner radius 0 → 56, POP).
      // POP runs at 1.6× so it resolves inside the half-beat: corners round until the spring first
      // reaches 1, then the overshoot pops the fresh circle outward (≤ +9 %) and it settles to Ø112,
      // with the last few % of residual eased out before the cut so the final L is exact.
      const MORPH_SPEED = 1.6;
      const settle = 1 - smoothstep(10.25, 10.3, t);
      ctx.fillStyle = PAPER;
      ctx.beginPath();
      for (const m of this.lMods) {
        const t0 = (this.lFill0 + m.pair) / FPS;
        if (t < t0 - 1e-6) continue;
        const s = 0.6 + 0.4 * E.swift(clamp((t - t0) / (4 / FPS)));
        const tm = (t - (T_L_AND + m.morphDelay)) * MORPH_SPEED;
        const mt = R.spring(tm, POP);
        const crossed = tm >= POP_CROSS;
        const round = crossed ? 1 : clamp(mt);
        const over = crossed ? (mt - 1) * settle : 0;
        const size = DOT * s * (1 + 0.5 * over);
        ctx.roundRect(m.x - size / 2, m.y - size / 2, size, size, (size / 2) * round);
      }
      ctx.fill();

      // ---- dimension lines: Volt 1 px, 6 px end ticks; Volt-light labels typed at 2 chars/frame
      const f0 = this.lFill0;
      ctx.strokeStyle = VOLT;
      ctx.lineWidth = 1;
      ctx.fillStyle = VOLT_LIGHT;
      ctx.font = `500 14px ${MONO}`;
      ctx.letterSpacing = this.lLS + 'px';
      ctx.textBaseline = 'alphabetic';
      ctx.textAlign = 'left';
      const typed = (txt, fStart) => txt.slice(0, clamp(2 * (f - fStart + 1), 0, txt.length));
      const drawP = (fStart) => E.swift(clamp((t - fStart / FPS) / 0.1));
      // COL 05–06: x 648 → 888 at y 880, label centred at (768, 904)
      {
        const fs = f0 + 6, p = drawP(fs);
        if (f >= fs) {
          ctx.beginPath();
          ctx.moveTo(648, 880.5); ctx.lineTo(648 + 240 * p, 880.5);
          ctx.moveTo(648.5, 877); ctx.lineTo(648.5, 883);
          if (p > 0.999) { ctx.moveTo(887.5, 877); ctx.lineTo(887.5, 883); }
          ctx.stroke();
          const txt = 'COL 05–06';
          const w = txt.length * this.lLabAdv - this.lLS;
          ctx.fillText(typed(txt, fs), Math.round(768 - w / 2), 904);
        }
      }
      // GUTTER 16: bracket x 888 → 904 at y 880, label left at (912, 904)
      {
        const fs = f0 + 8, p = drawP(fs);
        if (f >= fs) {
          ctx.beginPath();
          ctx.moveTo(888, 880.5); ctx.lineTo(888 + 16 * p, 880.5);
          ctx.moveTo(888.5, 877); ctx.lineTo(888.5, 883);
          if (p > 0.999) { ctx.moveTo(903.5, 877); ctx.lineTo(903.5, 883); }
          ctx.stroke();
          ctx.fillText(typed('GUTTER 16', fs), 912, 904);
        }
      }
      // MODULE 112 × 112: vertical x 1414, y 612 → 724, label left at (1424, 680)
      {
        const fs = f0 + 10, p = drawP(fs);
        if (f >= fs) {
          ctx.beginPath();
          ctx.moveTo(1414.5, 612); ctx.lineTo(1414.5, 612 + 112 * p);
          ctx.moveTo(1411, 612.5); ctx.lineTo(1417, 612.5);
          if (p > 0.999) { ctx.moveTo(1411, 723.5); ctx.lineTo(1417, 723.5); }
          ctx.stroke();
          ctx.fillText(typed('MODULE 112 × 112', fs), 1424, 680);
        }
      }
      ctx.letterSpacing = '0px';
    },

    // ============================================================================ A — LIQUID
    setupA() {
      // Reference placement: Archivo 600 / 100%, 1109 px, origin x 572, baseline 913 → ink x 578→1353,
      // y 152→913, counter incircle Ø178 centred on the anchor. Re-derived: find the enclosed counter,
      // its largest inscribed circle, and shift the glyph so that circle is centred on (960,540).
      let ox = 572, oy = 913;
      const a = glyphRaster('A', 600, 1109, ox, oy);
      const box = inkBox(a);
      const bx0 = box.x0 - 2, bx1 = box.x1 + 2, by0 = box.y0 - 2, by1 = box.y1 + 2, bw = bx1 - bx0, bh = by1 - by0;
      const ink = new Uint8Array(bw * bh), out = new Uint8Array(bw * bh);
      for (let y = 0; y < bh; y++) for (let x = 0; x < bw; x++) ink[y * bw + x] = a[(y + by0) * W + x + bx0] > 127 ? 1 : 0;
      const stack = [];
      for (let x = 0; x < bw; x++) stack.push(x, (bh - 1) * bw + x);
      for (let y = 0; y < bh; y++) stack.push(y * bw, y * bw + bw - 1);
      while (stack.length) {
        const i = stack.pop();
        if (out[i] || ink[i]) continue;
        out[i] = 1;
        const x = i % bw, y = (i / bw) | 0;
        if (x > 0) stack.push(i - 1);
        if (x < bw - 1) stack.push(i + 1);
        if (y > 0) stack.push(i - bw);
        if (y < bh - 1) stack.push(i + bw);
      }
      const hole = [], edge = [];
      let hy1 = 0;
      for (let y = 1; y < bh - 1; y++) {
        for (let x = 1; x < bw - 1; x++) {
          const i = y * bw + x;
          if (!ink[i] && !out[i]) { hole.push(x, y); if (y > hy1) hy1 = y; }
          else if (ink[i]) {
            const isHole = (j) => !ink[j] && !out[j];
            if (isHole(i - 1) || isHole(i + 1) || isHole(i - bw) || isHole(i + bw)) edge.push(x, y);
          }
        }
      }
      let best = 0, cx = 0, cy = 0;
      for (let k = 0; k < hole.length; k += 2) {
        const x = hole[k], y = hole[k + 1];
        let m = Infinity;
        for (let e = 0; e < edge.length && m > best * best; e += 2) {
          const dx = edge[e] - x, dy = edge[e + 1] - y, d = dx * dx + dy * dy;
          if (d < m) m = d;
        }
        const r = Math.sqrt(m);
        if (r > best) { best = r; cx = x; cy = y; }
      }
      const shx = AX - (cx + bx0), shy = AY - (cy + by0);
      const sx = Math.abs(shx) > 1 ? Math.round(shx) : 0, sy = Math.abs(shy) > 1 ? Math.round(shy) : 0;
      ox += sx; oy += sy;
      this.aCounter = { cx: cx + bx0 + sx, cy: cy + by0 + sy, r: best };
      this.aOrigin = [ox, oy];
      this.aBaseY = oy; // wobble pivot: the baseline

      // Row runs (ink spans per scanline) → crossbar and outer contour.
      const runsAt = (yy) => {
        const y = yy - by0, runs = [];
        let s = -1;
        for (let x = 0; x < bw; x++) {
          const v = ink[y * bw + x];
          if (v && s < 0) s = x;
          if (!v && s >= 0) { runs.push([s + bx0 + sx, x + bx0 + sx]); s = -1; }
        }
        if (s >= 0) runs.push([s + bx0 + sx, bw + bx0 + sx]);
        return runs;
      };
      const cbTop = hy1 + by0 + 1; // first ink row under the counter
      let cbBot = cbTop;
      while (runsAt(cbBot + 1).length === 1) cbBot++; // last row where the crossbar still spans both legs
      this.aCrossTop = cbTop + sy;
      this.aCrossBot = cbBot + 1 + sy; // exclusive (first row with two runs)
      const Y0 = box.y0, Y1 = box.y1; // ink rows [Y0, Y1)
      const pts = [];
      const seg = {};
      seg.leftOuter = [pts.length];
      for (let y = Y0; y < Y1; y++) { const r = runsAt(y); pts.push([r[0][0], y + sy]); } // left outer edge ↓
      seg.leftOuter.push(pts.length - 1);
      { const r = runsAt(Y1 - 1); pts.push([r[0][0], Y1 + sy], [r[0][1], Y1 + sy]); } // left foot →
      for (let y = Y1 - 1; y > cbBot; y--) { const r = runsAt(y); pts.push([r[0][1], y + sy]); } // left inner ↑
      { const r = runsAt(cbBot + 1); pts.push([r[0][1], cbBot + 1 + sy], [r[1][0], cbBot + 1 + sy]); } // crossbar underside →
      for (let y = cbBot + 1; y < Y1; y++) { const r = runsAt(y); pts.push([r[1][0], y + sy]); } // right inner ↓
      { const r = runsAt(Y1 - 1); pts.push([r[1][0], Y1 + sy], [r[1][1], Y1 + sy]); } // right foot →
      seg.rightOuter = [pts.length];
      for (let y = Y1 - 1; y >= Y0; y--) { const r = runsAt(y); pts.push([r[r.length - 1][1], y + sy]); } // right outer ↑
      seg.rightOuter.push(pts.length - 1);
      { const r = runsAt(Y0); pts.push([r[r.length - 1][1], Y0 + sy], [r[0][0], Y0 + sy]); } // apex ←
      // Arc-length bookkeeping so the travelling bumps can be routed along the outer flanks only
      // (never across the crossbar underside, which belongs to the drip).
      const cum = [0];
      for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
      const total = cum[pts.length - 1] + Math.hypot(pts[0][0] - pts[pts.length - 1][0], pts[0][1] - pts[pts.length - 1][1]);
      const segAt = (sg, f) => cum[sg[0]] + f * (cum[sg[1]] - cum[sg[0]]);
      // Three bumps, all flowing downhill: two down the left flank, one down the right flank.
      this.aBumpPlan = [
        { s0: segAt(seg.leftOuter, 0.07), dir: 1 },
        { s0: segAt(seg.rightOuter, 0.9), dir: -1 },
        { s0: segAt(seg.leftOuter, 0.52), dir: 1 },
      ];
      // Resample by arc length (≈ 6 px) and attach outward normals (tested against the ink).
      const cont = R.poly.resample(pts, Math.round(total / 6), true);
      const inkAt = (x, y) => {
        const ix = Math.round(x) - sx - bx0, iy = Math.round(y) - sy - by0;
        return ix >= 0 && ix < bw && iy >= 0 && iy < bh && ink[iy * bw + ix] === 1;
      };
      const nrm = cont.map((p, i) => {
        const q0 = cont[(i - 3 + cont.length) % cont.length], q1 = cont[(i + 3) % cont.length];
        let nx = q1[1] - q0[1], ny = -(q1[0] - q0[0]);
        const l = Math.hypot(nx, ny) || 1;
        nx /= l; ny /= l;
        if (inkAt(p[0] + nx * 4, p[1] + ny * 4)) { nx = -nx; ny = -ny; }
        return [nx, ny];
      });
      this.aCont = cont;
      this.aNrm = nrm;
      this.aContLen = total;
      this.aStep = total / cont.length;

      // ---- SVG goo layer
      const NS = 's06-';
      const svg = R.svgLayer(this.panel, { style: 'position:absolute;left:0;top:0;overflow:hidden;display:none' });
      const defs = R.svg('defs', {}, svg);
      const filt = R.svg('filter', { id: NS + 'goo', filterUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H, 'color-interpolation-filters': 'sRGB' }, defs);
      R.svg('feGaussianBlur', { in: 'SourceGraphic', stdDeviation: 14 }, filt);
      R.svg('feColorMatrix', { type: 'matrix', values: '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9' }, filt);
      const clip = R.svg('clipPath', { id: NS + 'reveal', clipPathUnits: 'userSpaceOnUse' }, defs);
      const mask = R.svg('mask', { id: NS + 'slot', maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, defs);
      R.svg('rect', { x: 0, y: 0, width: W, height: H, fill: '#fff' }, mask);
      this.aSlot = R.svg('rect', { x: 0, y: 0, width: 0, height: 0, fill: '#000' }, mask);
      const goo = R.svg('g', { filter: `url(#${NS}goo)`, fill: PAPER }, svg);
      this.aBody = R.svg('g', {}, goo);
      const txt = R.svg('text', { x: ox, y: oy, 'clip-path': `url(#${NS}reveal)`, mask: `url(#${NS}slot)`, style: `font-family:${DISPLAY};font-weight:600;font-size:1109px;font-stretch:100%;font-kerning:none` }, this.aBody);
      txt.textContent = 'A';
      this.aBumps = [0, 1, 2].map(() => R.svg('circle', { cx: 0, cy: 0, r: 0 }, this.aBody));
      // each bump drags a smaller wake circle behind it, so in stills it reads as a travelling swell
      this.aWakes = [0, 1, 2].map(() => R.svg('circle', { cx: 0, cy: 0, r: 0 }, this.aBody));

      // Seven Paper blobs rush in from beyond the frame edges on curved paths and land on the A's strokes.
      const S = [sx, sy];
      const at = (x, y) => [x + S[0], y + S[1]];
      this.aBlobs = [
        { from: [-190, 1270], to: at(676, 852), d: 210, bend: 0.2, delay: 0 }, // bottom-left → left foot
        { from: [2110, 1270], to: at(1252, 852), d: 200, bend: -0.2, delay: 0.6 }, // bottom-right → right foot
        { from: [-240, 420], to: at(798, 530), d: 150, bend: -0.16, delay: 1.2 }, // left → left leg
        { from: [2160, 660], to: at(1124, 520), d: 160, bend: 0.16, delay: 0.3 }, // right → right leg
        { from: [-170, -210], to: at(918, 262), d: 120, bend: 0.18, delay: 0.9 }, // top-left → apex
        { from: [2090, -220], to: at(1004, 236), d: 96, bend: -0.18, delay: 1.5 }, // top-right → apex
        { from: [930, 1290], to: at(960, 692), d: 70, bend: 0.1, delay: 1.8 }, // bottom → crossbar
      ].map((b) => {
        const dx = b.to[0] - b.from[0], dy = b.to[1] - b.from[1], L = Math.hypot(dx, dy);
        b.ctrl = [(b.from[0] + b.to[0]) / 2 - (dy / L) * L * b.bend, (b.from[1] + b.to[1]) / 2 + (dx / L) * L * b.bend];
        // Pre-rolled one frame so the cut lands mid-rush (cut on action): the first A frame already
        // shows liquid streaking in from every edge.
        b.t0 = T_A - 1 / FPS + b.delay / FPS;
        // trailing droplets along the path behind the head: the goo fuses them into a tapered streak
        b.trail = [0, 1, 2].map(() => R.svg('circle', { cx: 0, cy: 0, r: 0 }, goo));
        b.el = R.svg('ellipse', { cx: 0, cy: 0, rx: 0, ry: 0 }, goo);
        b.clip = R.svg('circle', { cx: b.to[0], cy: b.to[1], r: 0 }, clip);
        return b;
      });
      // Rounded, convex ends for the two crossbar halves while the slot is open (they reach for the dot).
      this.aEnds = [0, 1].map(() => R.svg('circle', { cx: AX, cy: 0, r: 0 }, goo));
      // Meniscus: the crossbar surface wets up both sides of the dot while it presses into the membrane.
      this.aMenisci = [0, 1].map(() => R.svg('circle', { cx: AX, cy: 0, r: 0 }, goo));
      this.aBulge = R.svg('circle', { cx: AX, cy: 0, r: 0 }, goo);
      this.aNeck = [0, 1, 2, 3, 4].map(() => R.svg('circle', { cx: AX, cy: 0, r: 0 }, goo));
      this.aDrops = [0, 1].map(() => R.svg('circle', { cx: AX, cy: 0, r: 0, fill: PAPER }, svg));
      this.aSvg = svg;
      this.aFilter = filt;
    },

    /** Dot state inside the A vignette (screen space): sinks onto the crossbar, then drips through. */
    aDot(t) {
      if (t < T_A_SET) return { y: AY, sx: 1, sy: 1 };
      if (t < T_A_DRIP) {
        const q = (t - T_A_SET) / (T_A_DRIP - T_A_SET);
        const y = AY + 50 * E.inQuad(q);
        const press = clamp((y + DOT_R - (this.aCrossTop - 16)) / 30); // squashes as it presses the membrane
        const sx = 1 + 0.08 * press;
        return { y, sx, sy: 1 / sx };
      }
      const tau = t - T_A_DRIP;
      const V0 = 1800, G = 13000; // the membrane snaps: launched at 1800 px/s, then gravity
      return { y: 590 + V0 * tau + 0.5 * G * tau * tau, sx: 0.8, sy: 1.25 };
    },

    drawA(t) {
      const lt = t - T_A;
      const filt = this.aFilter;
      // Filter region: full frame while blobs fly in from the edges, then clipped to the A box + 160 px.
      if (lt < 0.1) { filt.setAttribute('x', 0); filt.setAttribute('y', 0); filt.setAttribute('width', W); filt.setAttribute('height', H); }
      else { filt.setAttribute('x', 418); filt.setAttribute('y', 0); filt.setAttribute('width', 1095); filt.setAttribute('height', H); }

      // ---- WOBBLE: the liquid A lands squashed and settles with overshoot, pivoting on its baseline.
      const tw = T_A + 2 / FPS;
      const w = 1 - R.spring(t - tw, WOBBLE); // 1 → −0.39 → … → 0
      const syA = 1 - 0.05 * w, sxA = 1 / Math.pow(syA, 0.7);
      const by = this.aBaseY;
      this.aBody.setAttribute('transform', `matrix(${sxA.toFixed(5)} 0 0 ${syA.toFixed(5)} ${(AX * (1 - sxA)).toFixed(3)} ${(by * (1 - syA)).toFixed(3)})`);
      const toScreenY = (y) => by + (y - by) * syA;
      const toLocalY = (y) => by + (y - by) / syA;
      const toLocalX = (x) => AX + (x - AX) / sxA;
      const cbTop = toScreenY(this.aCrossTop), cbBot = toScreenY(this.aCrossBot);

      // ---- converge: blobs on curved paths (swift), stretched along their velocity, then absorbed
      const DUR = R.E16; // the converge is one 16th
      for (const b of this.aBlobs) {
        const tau = t - b.t0;
        if (tau < 0) {
          b.el.setAttribute('rx', 0); b.el.setAttribute('ry', 0); b.clip.setAttribute('r', 0);
          for (const c of b.trail) c.setAttribute('r', 0);
          continue;
        }
        const q = E.swift(clamp(tau / DUR)), q2 = E.swift(clamp((tau - 1 / 240) / DUR));
        const p = quadBez(b.from, b.ctrl, b.to, q), p2 = quadBez(b.from, b.ctrl, b.to, q2);
        const vx = (p[0] - p2[0]) * 240, vy = (p[1] - p2[1]) * 240, sp = Math.hypot(vx, vy);
        const st = 1 + Math.min(0.8, sp / 4000);
        // absorbed into the letter so the A reads clean by ≈10.43
        const absorb = E.inOutQuad(clamp((tau - 0.05) / 0.075));
        const r = (b.d / 2) * (1 - absorb);
        const ang = (Math.atan2(vy, vx) * 180) / Math.PI;
        b.el.setAttribute('cx', p[0].toFixed(2)); b.el.setAttribute('cy', p[1].toFixed(2));
        b.el.setAttribute('rx', (r * st).toFixed(2)); b.el.setAttribute('ry', (r / Math.sqrt(st)).toFixed(2));
        b.el.setAttribute('transform', sp > 1 ? `rotate(${ang.toFixed(2)} ${p[0].toFixed(2)} ${p[1].toFixed(2)})` : '');
        // trail: three tapering droplets behind the head along the same curve; the spacing scales with
        // speed, so the streak is long mid-rush and collapses into the head as it lands
        const lag = 0.05 * clamp(sp / 2500);
        for (let k = 0; k < 3; k++) {
          const pk = quadBez(b.from, b.ctrl, b.to, Math.max(0, q - (k + 1) * lag));
          const c = b.trail[k];
          c.setAttribute('cx', pk[0].toFixed(2)); c.setAttribute('cy', pk[1].toFixed(2));
          c.setAttribute('r', (r * (0.8 - 0.17 * k)).toFixed(2));
        }
        // Reveal: a circle floods out of each landing point (r 0 → 700, swift).
        const rv = 700 * E.swift(clamp((tau - 0.03) / 0.2));
        b.clip.setAttribute('r', rv.toFixed(2));
      }

      // ---- three Ø40 bumps ride the outer flanks at 900 px/s (downhill). Their centres sit 6 px INSIDE
      // the edge, so the goo turns each into a smooth swell (≈14 px proud) rather than a knob, and a
      // Ø24 wake 26 px behind stretches it into a travelling ripple. They grow in on the settle and
      // flatten out before the cut, so the A reads clean on the drip and on the last frames.
      const bumpIn = E.swift(clamp((t - T_A_SET) / 0.06)) * (1 - E.inOutQuad(clamp((t - 10.69) / 0.07)));
      const n = this.aCont.length;
      const onCont = (s, off) => {
        const k0 = Math.floor(s), fk = s - k0;
        const ia = ((k0 % n) + n) % n, ib = (((k0 + 1) % n) + n) % n;
        const pa = this.aCont[ia], pb = this.aCont[ib], na = this.aNrm[ia], nb = this.aNrm[ib];
        const nx = lerp(na[0], nb[0], fk), ny = lerp(na[1], nb[1], fk);
        return [lerp(pa[0], pb[0], fk) + nx * off, lerp(pa[1], pb[1], fk) + ny * off];
      };
      for (let i = 0; i < 3; i++) {
        const bp = this.aBumpPlan[i];
        const s = (bp.s0 + bp.dir * 900 * (t - T_A_SET)) / this.aStep;
        const [x, y] = onCont(s, -6);
        const el = this.aBumps[i];
        el.setAttribute('cx', x.toFixed(2)); el.setAttribute('cy', y.toFixed(2));
        el.setAttribute('r', (20 * bumpIn).toFixed(2));
        const [wx, wy] = onCont(s - (bp.dir * 26) / this.aStep, -8);
        const wk = this.aWakes[i];
        wk.setAttribute('cx', wx.toFixed(2)); wk.setAttribute('cy', wy.toFixed(2));
        wk.setAttribute('r', (12 * bumpIn).toFixed(2));
      }

      // ---- the dot sinks onto the crossbar (membrane bulges below), then drips through
      const dot = this.aDot(t);
      const sinkQ = t < T_A_SET ? 0 : t < T_A_DRIP ? E.inQuad((t - T_A_SET) / (T_A_DRIP - T_A_SET)) : 1;
      const tauD = t - T_A_DRIP;
      const dotTop = dot.y - DOT_R * dot.sy;
      // crossbar slot: opens on the snap, follows the dot through, rejoins (goo) once it has passed
      const tClear = (-1800 + Math.sqrt(1800 * 1800 + 2 * 13000 * (this.aCrossBot + DOT_R * 1.25 - 590))) / 13000;
      let slotW = 0;
      if (tauD >= 0) {
        const open = E.outCubic(clamp(tauD / (1.5 / FPS)));
        const close = E.swift(clamp((tauD - tClear) / (3 / FPS)));
        slotW = 132 * open * (1 - close);
      }
      const cbMid = (cbTop + cbBot) / 2, endR = 0.4 * (cbBot - cbTop);
      if (slotW > 0.5) {
        const yT = toLocalY(cbTop - 40), yB = toLocalY(Math.min(dot.y + 20, cbBot + 40));
        const x0 = toLocalX(AX - slotW / 2), x1 = toLocalX(AX + slotW / 2);
        this.aSlot.setAttribute('x', x0.toFixed(2)); this.aSlot.setAttribute('width', (x1 - x0).toFixed(2));
        this.aSlot.setAttribute('y', yT.toFixed(2)); this.aSlot.setAttribute('height', Math.max(0, yB - yT).toFixed(2));
      } else {
        this.aSlot.setAttribute('width', 0); this.aSlot.setAttribute('height', 0);
      }
      // the parted halves end in convex, rounded blobs that bulge 20 px into the gap (and meet as it closes)
      const cut = slotW > 0.5 ? clamp((Math.min(dot.y + 20, cbBot + 40) - cbTop) / (cbBot - cbTop)) : 0;
      for (let k = 0; k < 2; k++) {
        const sgn = k ? 1 : -1;
        const el = this.aEnds[k];
        el.setAttribute('cx', (AX + sgn * (slotW / 2 + endR - 20)).toFixed(2));
        el.setAttribute('cy', (cbTop + (cbMid - cbTop) * cut + endR * (1 - cut) * 0.2).toFixed(2));
        el.setAttribute('r', slotW > 0.5 ? (endR * (0.55 + 0.45 * cut)).toFixed(2) : 0);
      }
      // meniscus: grows with the press, pulled down through the slot with the dot on the snap
      {
        const press = tauD < 0 ? clamp((dot.y + DOT_R * dot.sy - (cbTop - 6)) / 24) : 1 - clamp(tauD / (2 / FPS));
        const halfW = DOT_R * dot.sx;
        for (let k = 0; k < 2; k++) {
          const el = this.aMenisci[k];
          el.setAttribute('cx', (AX + (k ? 1 : -1) * (halfW * 0.86)).toFixed(2));
          el.setAttribute('cy', (cbTop + 5).toFixed(2));
          el.setAttribute('r', (17 * E.outQuad(clamp(press))).toFixed(2));
        }
      }
      // membrane bulge: pushed below the crossbar by the dot's weight; heals on WOBBLE after the snap
      const L_BREAK = 96;
      const neckLen = dotTop - cbBot;
      const tBreak = (-1800 + Math.sqrt(1800 * 1800 + 2 * 13000 * (this.aCrossBot + L_BREAK + DOT_R * 1.25 - 590))) / 13000;
      let bulgeY, bulgeR = 30;
      if (tauD < 0) bulgeY = cbBot - 30 + 38 * sinkQ;
      else {
        const heal = R.spring(tauD - tBreak, WOBBLE);
        bulgeY = cbBot - 30 + 38 * (1 - heal) + (tauD < tBreak ? 10 * clamp(tauD / tBreak) : 10 * (1 - heal));
        bulgeR = 30 - 6 * clamp(tauD / 0.1);
      }
      this.aBulge.setAttribute('cy', bulgeY.toFixed(2));
      this.aBulge.setAttribute('r', t < T_A_SET - 0.02 ? 0 : bulgeR.toFixed(2));
      // neck: a tapering chain from the crossbar underside to the falling dot; snaps at L_BREAK and retracts
      for (let k = 0; k < this.aNeck.length; k++) {
        const el = this.aNeck[k];
        let r = 0, y = cbBot;
        if (tauD >= 0 && neckLen > -DOT_R) {
          const u = (k + 1) / this.aNeck.length;
          if (tauD < tBreak) {
            const L = Math.max(0, neckLen);
            y = cbBot - 6 + (L + 16) * u;
            r = lerp(22, 15, u) * (1 - 0.35 * clamp(L / L_BREAK));
          } else {
            const back = E.swift(clamp((tauD - tBreak) / 0.09));
            const yBreak = cbBot - 6 + (L_BREAK + 16) * u;
            y = lerp(yBreak, cbBot - 18, back);
            r = lerp(22, 15, u) * 0.65 * (1 - back * 0.9);
          }
        }
        el.setAttribute('cy', y.toFixed(2));
        el.setAttribute('r', r.toFixed(2));
      }
      // droplets (Ø18, Ø10): flung from the snapped neck, trail the dot, then reabsorbed into the crossbar
      // before the cut (surface tension pulls them back up)
      for (let k = 0; k < 2; k++) {
        const el = this.aDrops[k];
        const td = tauD - tBreak - k * (1 / FPS);
        const T_DOWN = 0.035, T_UP = 0.055;
        if (td < 0 || td > T_DOWN + T_UP) { el.setAttribute('r', 0); continue; }
        const yStart = cbBot + L_BREAK * (k ? 0.72 : 0.9);
        const down = 40 - k * 12;
        const y = td < T_DOWN ? yStart + down * E.outQuad(td / T_DOWN) : lerp(yStart + down, cbBot - 6, E.inOutQuad((td - T_DOWN) / T_UP));
        const shrink = 1 - E.inQuad(clamp((td - T_DOWN - 0.03) / (T_UP - 0.03)));
        el.setAttribute('cx', (AX + (k ? -9 : 7)).toFixed(2));
        el.setAttribute('cy', y.toFixed(2));
        el.setAttribute('r', ((k ? 5 : 9) * shrink).toFixed(2));
      }
      return dot;
    },

    // ============================================================================ U — DATA
    setupU() {
      this.u14 = monoMetrics(500, 14);
      this.u28 = monoMetrics(700, 28);
      this.u56 = monoMetrics(700, 56);
      this.uTicks = [];
      for (let k = 0; k <= 10; k++) this.uTicks.push({ x: 160 + 160 * k, label: String(k - 5).replace('-', '−') });
    },

    drawU(ctx, t) {
      const lt = t - T_U;
      // ---- dashed Fog 2 px axis at y 540 (x 160 → 1760, dash 12/8), drawn out from the hub
      const reach = 800 * E.swift(clamp((lt + 2 / FPS) / 0.2)); // pre-rolled 2 frames: the cut lands mid-draw
      ctx.save();
      ctx.beginPath();
      ctx.rect(AX - reach, 530, 2 * reach, 20);
      ctx.clip();
      ctx.beginPath();
      ctx.setLineDash([12, 8]);
      ctx.moveTo(160, 540); ctx.lineTo(1760, 540);
      ctx.lineWidth = 2;
      ctx.strokeStyle = FOG;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
      // tick labels every 160 px (−5 … 5), set as the axis reaches them
      ctx.letterSpacing = '0px';
      ctx.font = `500 14px ${MONO}`;
      ctx.fillStyle = FOG;
      ctx.textBaseline = 'alphabetic';
      ctx.textAlign = 'left';
      for (const tk of this.uTicks) {
        if (Math.abs(tk.x - AX) > reach + 0.5) continue;
        const w = tk.label.length * this.u14.adv;
        ctx.fillText(tk.label, Math.round(tk.x - w / 2), 570);
      }
      // ---- bars (stems): Ink, 150 wide, grow y 540 → 150 on a spring (260/18); residual eased out before rest
      const settle = 1 - smoothstep(11.1, 11.2, t);
      const barH = (t0) => {
        if (t < t0) return 0;
        const s = R.spring(t - t0, BAR_SPRING);
        return 390 * (1 + (s - 1) * settle);
      };
      const bars = [[570, barH(T_U), T_U], [1200, barH(T_U_R), T_U_R]];
      ctx.fillStyle = INK;
      for (const [x, h] of bars) if (h >= 0.5) ctx.fillRect(x, 540 - h, 150, h);
      // value labels: JetBrains Mono 700 28 px, centred above each bar, counting 0 → 100 with its height
      ctx.font = `700 28px ${MONO}`;
      for (const [x, h, t0] of bars) {
        if (t < t0) continue; // no stray "0" on the axis before its bar starts
        const v = String(Math.round(100 * clamp(h / 390)));
        const w = v.length * this.u28.adv;
        ctx.fillText(v, Math.round(x + 75 - w / 2), Math.round(540 - h - 16));
      }
      // ---- bowl: Ink half-donut (r 240 → 390) sweeping left stem → bottom → right stem (inOutCubic),
      // flat start, round leading cap, built as one filled path (no seams).
      const sw = E.inOutCubic(clamp((t - T_U_R) / (T_U_LOCK - T_U_R)));
      if (sw > 0) {
        const th = Math.PI * sw, phi = Math.PI - th;
        const ex = AX + 315 * Math.cos(phi), ey = AY + 315 * Math.sin(phi);
        ctx.beginPath();
        ctx.moveTo(AX - 390, AY);
        ctx.arc(AX, AY, 390, Math.PI, phi, true);
        ctx.arc(ex, ey, 75, phi, phi - Math.PI, true);
        ctx.arc(AX, AY, 240, phi, Math.PI, false);
        ctx.closePath();
        ctx.fill();
      }
      // Fog 1 px ticks every 10 % outside the bowl, set as the sweep passes them
      ctx.beginPath();
      for (let k = 0; k <= 10; k++) {
        if (sw < k / 10 - 1e-6) continue;
        const a = Math.PI - (Math.PI * k) / 10, c = Math.cos(a), s = Math.sin(a);
        ctx.moveTo(AX + 402 * c, AY + 402 * s);
        ctx.lineTo(AX + 418 * c, AY + 418 * s);
      }
      ctx.lineWidth = 1;
      ctx.strokeStyle = FOG;
      ctx.stroke();
      // readout: JetBrains Mono 700 56 px, centred at (960, baseline 340): 0% → 100%
      ctx.font = `700 56px ${MONO}`;
      ctx.fillStyle = INK;
      const txt = Math.round(100 * sw) + '%';
      ctx.fillText(txt, Math.round(AX - (txt.length * this.u56.adv) / 2), 340);
    },

    // ============================================================================ frame
    update(lt, p, t) {
      const v = vignetteAt(t);
      const f = fOf(t);
      const ctx = this.ctx;

      // ---- world panel: whip-pans in on the shared P(t), then locks at x = 0
      const px = 1920 - P(t);
      this.panel.style.transform = px > 0.001 ? `translate3d(${px.toFixed(3)}px,0,0)` : 'none';
      this.panel.style.background = GROUND[v];
      const speed = Math.abs(dP(t)) / DP_MAX; // 0..1
      const smear = 1 + 2.5 * speed; // halftone smear: peak 3.5 mid-whip, 1.0 on landing
      const blurLen = (0.5 * Math.abs(dP(t))) / FPS; // 180° shutter: ≤ 205 px at peak speed
      if (blurLen >= 2 && px < W) { // (sub-2 px on the first/last overlap frames: panel only, per the handoff)
        this.edge.style.display = 'block';
        // overlaps the panel by 2 px so the two antialiased edges never leave a conflation hairline
        this.edge.style.transform = `translate3d(${(px - blurLen).toFixed(3)}px,0,0) scaleX(${(blurLen + 2).toFixed(3)})`;
      } else this.edge.style.display = 'none';

      ctx.clearRect(0, 0, W, H);
      let dx = 0, dy = 0, sx = 1, sy = 1, dotVisible = true;
      this.aSvg.style.display = v === 2 ? 'block' : 'none';
      if (v === 0) {
        this.drawC(ctx, t, smear);
        // the dot rides in with the world, smeared like it, then pulses with the ripple on the and
        const k = 1 + 0.6 * speed; // stretch along the pan, volume-preserving (craft note 4)
        sx *= k; sy *= 1 / k;
        const pulse = 1 + 0.07 * impulse(t - T_C_AND, TIGHT);
        sx *= pulse; sy *= pulse;
      } else if (v === 1) {
        this.drawL(ctx, t);
        const pulse = 1 + 0.08 * impulse(t - T_L_AND, POP);
        sx *= pulse; sy *= pulse;
      } else if (v === 2) {
        const d = this.drawA(t);
        dy = d.y - AY; sx *= d.sx; sy *= d.sy;
        if (d.y - DOT_R * d.sy > H + 2) dotVisible = false;
      } else {
        this.drawU(ctx, t);
        // DATA POINT LOCKED: 1 → 1.2 (outCubic) → 1 (inOutSine), settled before the rest frames
        const s = R.kf(t, [[T_U_LOCK, 1], [11.162109375, 1.2, 'outCubic'], [11.2109375, 1, 'inOutSine']]);
        sx *= s; sy *= s;
      }
      // centre-lock squash-pop on every cut (1.25 × 0.8 → 1)
      const d = cutDeform(t);
      sx *= 1 + 0.25 * d; sy *= 1 - 0.2 * d;

      const dot = this.dot;
      dot.style.display = dotVisible ? 'block' : 'none';
      const still = Math.abs(sx - 1) < 1e-4 && Math.abs(sy - 1) < 1e-4 && Math.abs(dx) < 1e-3 && Math.abs(dy) < 1e-3;
      dot.style.transform = still ? 'none' : `translate(${dx.toFixed(3)}px,${dy.toFixed(3)}px) scale(${sx.toFixed(5)},${sy.toFixed(5)})`;

      // ---- caption: types on at 3 chars/frame from the cut, behind a Signal block cursor
      const cap = this.caption, cur = this.cursor;
      if (t < T_C) {
        cap.style.display = 'none';
        cur.style.display = 'none';
      } else {
        const text = CAPTIONS[v];
        const since = f - fr(CUTS[v]);
        const n = Math.min(text.length, 3 * (since + 1));
        cap.style.display = 'block';
        cap.textContent = text.slice(0, n);
        cap.style.color = HUD_COL[v];
        const typing = since < Math.ceil(text.length / 3) + 2;
        cur.style.display = typing ? 'block' : 'none';
        if (typing) cur.style.left = Math.round(72 + n * this.capAdv) + 'px';
      }
    },
  });
})();
