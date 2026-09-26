// s07-range-2 — Range II: D · E · the specimen row · the squeeze.
// Window 11.25 → 13.125 s (frames 675–787, bar 7), z 70, root Ink.
//
// Layers (bottom → top):
//   glyphs   DOM: six plain Paper letters (flatten + squeeze) and the ONE canonical condensed "CLAUDE" (rest frames)
//   stage    one full-frame canvas: the D glitch, the E shape build, the specimen row (cells, stutter, collapse)
//   dot      DOM Signal disc (the protagonist) from the E onward; inside the D it is drawn into the sliced canvas
//   captions DOM JetBrains Mono: the montage caption (x 72, baseline 976) and the six row captions (baseline 744)
//
// Everything is a pure function of t. All randomness is R.hash keyed on slice/block index and the frame index.
(() => {
  'use strict';
  const P = R.pal;
  const EZ = R.ease;
  const TAU = Math.PI * 2;

  // ----------------------------------------------------------------------------------------------------------
  // Timeline (global seconds)
  // ----------------------------------------------------------------------------------------------------------
  const T_IN = 11.25; //           7.1.1  D — GLITCH (hard cut from the U chart)
  const T_HALF = 11.3671875; //    glitch half-resolves (offsets x0.25)
  const T_E = 11.484375; //        7.1.3  E — SHAPE (the reel's one full-frame Acid 8th)
  const T_FIRE = 692 / 60; //      the stem slams home (squash frame) — arms fire from here
  const ARM_T0 = T_FIRE - 0.5 / 60; // arm k starts at ARM_T0 + k/60 (so arm 1 already shows on the squash frame)
  const T_ROW = 11.71875; //       7.2.1  specimen row, pair C+L
  const T_AU = 11.8359375; //      7.2.2  pair A+U, the dot leaps
  const T_DE = 11.953125; //       7.2.3  pair D+E
  const T_STUT = 12.0703125; //    7.2.4  row stutter
  const T_REV = 12.1875; //        7.3.1  THE REVEAL, the period lands
  const T_FLAT = 12.65625; //      7.4.1  flatten (drums out)
  const T_HOP_A = 766 / 60; //     the period re-seats onto the plain baseline: anticipation …
  const T_HOP_UP = 768 / 60; //    … take-off (as the E cell snaps shut) …
  const T_HOP_DN = 773 / 60; //    … and landing on baseline 640
  const T_SQ = 12.890625; //       7.4.3  squeeze
  const T_TREM = 13.0391; //       tremble window (sin-windowed, back to exactly 0)
  const T_REST = 13.0917; //       7.4.4  rest pose: the canonical element
  const T_END = 13.125;
  const LEAP_DUR = 0.3515625;
  const POP_DUR = 5 / 60;
  const COLLAPSE_DUR = 0.1171875;
  const TIGHT = { stiffness: 420, damping: 26 };

  // ----------------------------------------------------------------------------------------------------------
  // Geometry (frame px)
  // ----------------------------------------------------------------------------------------------------------
  const AX = 960, AY = 540; //                 montage anchor
  const CW = 240, CH = 340, CY0 = 370, CCY = 540; // specimen cells
  const cellX = (i) => 142 + 264 * i;
  const cellCx = (i) => 262 + 264 * i;
  const LETTERS = 'CLAUDE';
  const CAPTIONS = ['HALFTONE', 'GRID', 'LIQUID', 'DATA', 'GLITCH', 'SHAPE'];
  const GROUND = [P.paper, P.ink, P.volt, P.paper, P.ink, P.acid];
  const POP_T = [T_ROW, T_ROW, T_AU, T_AU, T_DE, T_DE];
  const PLAIN_SIZE = 291, PLAIN_BASE = 640; //  Archivo 900/100%, flat cap 200 centred on y 540
  const CANON_SIZE = 370, CANON_BASE = 670; //  canonical condensed word (shared with s08)
  const PERIOD = { x: 1750, y: 682, d: 56 }; // the row's full stop (bottom on the cell baseline 710)
  const FINAL = { x: 1542, y: 638, d: 64 }; //  handoff to s08 (bottom on the word's baseline 670)
  // E — SHAPE (full frame)
  const STEM = { x0: 460, x1: 650, y0: 150, y1: 930 };
  const ARMS = [
    { y0: 150, y1: 320, len: 490 },
    { y0: 455, y1: 625, len: 238 },
    { y0: 760, y1: 930, len: 490 },
  ];
  const ARM_DUR = 7 / 60;
  // Speed lines: offset from the arm's top (negative) or bottom (positive) edge, head gap behind the tip,
  // max length as a fraction of the arm, start delay. They trail the tip and shrink to nothing over 6 frames.
  const SPEED = [
    { edge: 'top', dy: -14, gap: 6, frac: 0.8, delay: 0 },
    { edge: 'top', dy: -28, gap: 34, frac: 0.46, delay: 0.5 / 60 },
    { edge: 'bot', dy: 14, gap: 18, frac: 0.62, delay: 1 / 60 },
  ];
  const PLAIN_TOP_SEAT = { y: 612 }; // the period's centre once re-seated on the plain baseline (bottom 640)

  // ----------------------------------------------------------------------------------------------------------
  // Small helpers
  // ----------------------------------------------------------------------------------------------------------
  const clamp = R.clamp, lerp = R.lerp;
  const firstFrame = (T) => Math.ceil(T * 60 - 1e-6);
  /** Glitch displacement from a hash: ~20% of slices stay put, the rest are biased small with rare big jumps. */
  function glitchOff(h, amp) {
    const v = 2 * h - 1, a = Math.abs(v);
    if (a < 0.2) return 0;
    return Math.sign(v) * amp * Math.pow((a - 0.2) / 0.8, 1.3);
  }
  function offscreen(w, h, read) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    return { c, g: c.getContext('2d', read ? { willReadFrequently: true } : undefined) };
  }
  /** Fractional ink bounds (relative to origin/baseline) from an alpha scan; measureText boxes are 1/64-em quantized. */
  function inkBox(font, text) {
    const size = parseFloat(/(\d+(?:\.\d+)?)px/.exec(font)[1]);
    const W = Math.ceil(size * (text.length * 1.1 + 1)), H = Math.ceil(size * 1.6);
    const { g } = offscreen(W, H, true);
    g.font = font;
    g.fillStyle = '#fff';
    const ox = Math.round(size * 0.5), oy = Math.round(size * 1.2);
    g.fillText(text, ox, oy);
    const d = g.getImageData(0, 0, W, H).data;
    const colMax = new Uint8Array(W), rowMax = new Uint8Array(H);
    let x0 = W, x1 = -1, y0 = H, y1 = -1;
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const a = d[(y * W + x) * 4 + 3];
        if (!a) continue;
        if (a > colMax[x]) colMax[x] = a;
        if (a > rowMax[y]) rowMax[y] = a;
        if (x < x0) x0 = x;
        if (x > x1) x1 = x;
        if (y < y0) y0 = y;
        if (y > y1) y1 = y;
      }
    }
    return { l: x0 + 1 - colMax[x0] / 255 - ox, r: x1 + colMax[x1] / 255 - ox, t: y0 + 1 - rowMax[y0] / 255 - oy, b: y1 + rowMax[y1] / 255 - oy };
  }
  /**
   * Largest inscribed circle of a glyph's enclosed counter (exact Felzenszwalb EDT), glyph drawn at (ox, oy).
   * Returns the centroid of the max-distance plateau (a D's counter is taller than wide) and the radius.
   */
  function counterCircle(font, ch, ox, oy) {
    const W = R.W, H = R.H;
    const { g } = offscreen(W, H, true);
    g.font = font;
    g.fillStyle = '#fff';
    g.fillText(ch, ox, oy);
    const d = g.getImageData(0, 0, W, H).data;
    const N = W * H, ink = new Uint8Array(N), outside = new Uint8Array(N);
    for (let i = 0; i < N; i++) ink[i] = d[i * 4 + 3] >= 128 ? 1 : 0;
    const st = [];
    for (let x = 0; x < W; x++) st.push(x, (H - 1) * W + x);
    for (let y = 0; y < H; y++) st.push(y * W, y * W + W - 1);
    while (st.length) {
      const i = st.pop();
      if (outside[i] || ink[i]) continue;
      outside[i] = 1;
      const x = i % W;
      if (x > 0) st.push(i - 1);
      if (x < W - 1) st.push(i + 1);
      if (i >= W) st.push(i - W);
      if (i < N - W) st.push(i + W);
    }
    const INF = 1e20, f = new Float64Array(N);
    for (let i = 0; i < N; i++) f[i] = ink[i] ? 0 : INF;
    const n = Math.max(W, H), v = new Int32Array(n), z = new Float64Array(n + 1), o = new Float64Array(n), tmp = new Float64Array(n);
    // 1-D squared-distance transform (lower envelope of parabolas); |s| stays < INF because f ≤ INF and q − p ≥ 1
    const sect = (q, p) => (tmp[q] + q * q - (tmp[p] + p * p)) / (2 * q - 2 * p);
    const pass = (len, stride, off) => {
      for (let q = 0; q < len; q++) tmp[q] = f[off + q * stride];
      let k = 0;
      v[0] = 0; z[0] = -INF; z[1] = INF;
      for (let q = 1; q < len; q++) {
        let s = sect(q, v[k]);
        while (s <= z[k]) { k--; s = sect(q, v[k]); }
        k++;
        v[k] = q; z[k] = s; z[k + 1] = INF;
      }
      k = 0;
      for (let q = 0; q < len; q++) {
        while (z[k + 1] < q) k++;
        const p = v[k];
        o[q] = (q - p) * (q - p) + tmp[p];
      }
      for (let q = 0; q < len; q++) f[off + q * stride] = o[q];
    };
    for (let x = 0; x < W; x++) pass(H, W, x);
    for (let y = 0; y < H; y++) pass(W, 1, y * W);
    let best = -1;
    for (let i = 0; i < N; i++) if (!ink[i] && !outside[i] && f[i] > best) best = f[i];
    const rmax = Math.sqrt(best);
    let sx = 0, sy = 0, cnt = 0;
    for (let i = 0; i < N; i++) {
      if (ink[i] || outside[i] || Math.sqrt(f[i]) < rmax - 0.75) continue;
      sx += i % W; sy += (i / W) | 0; cnt++;
    }
    return cnt ? { x: sx / cnt, y: sy / cnt, r: rmax } : null;
  }
  /** Sin-windowed ±2 px tremble (R.noise2) over [T_TREM, T_REST]; exactly 0 outside the window. */
  function tremble(t, ch) {
    if (t <= T_TREM || t >= T_REST) return [0, 0];
    const w = Math.sin(Math.PI * (t - T_TREM) / (T_REST - T_TREM));
    const nx = clamp(2.6 * R.noise2(t * 53, 3.1 + ch * 17.7), -1, 1);
    const ny = clamp(2.6 * R.noise2(t * 53 + 41.3, 9.7 + ch * 17.7), -1, 1);
    return [2 * w * nx, 2 * w * ny];
  }

  R.scene({
    id: 's07-range-2',
    start: T_IN,
    end: T_END,
    z: 70,
    bg: P.ink,

    setup(root) {
      const S = this;

      // ---- Global FX cues (storyboard: Global FX cue list, owner s07) ----
      R.cue(11.25, 'chroma', { amt: 18, dur: 0.234375 }); //               glitch D
      R.cue(11.25, 'shake', { amt: 6, dur: 0.15 }); //                     glitch D
      R.cue(11.484375, 'zoom', { amt: 0.05, dur: 0.12 }); //               Acid E punch
      R.cue(11.71875, 'shake', { amt: 3, dur: 0.06 }); //                  row pair 1
      R.cue(11.8359375, 'shake', { amt: 3, dur: 0.06 }); //                row pair 2
      R.cue(11.953125, 'shake', { amt: 3, dur: 0.06 }); //                 row pair 3
      R.cue(12.0703125, 'chroma', { amt: 10, dur: 0.1171875 }); //         row stutter
      R.cue(12.1875, 'zoom', { amt: 0.02, dur: 0.12 }); //                 CLAUDE. revealed
      R.cue(12.65625, 'grain', { amt: 0.03, dur: 0.46875 }); //            tension
      R.cue(12.65625, 'vignette', { amt: 0.45, dur: 0.46875, in: 0.35, out: 0.02 }); // squeeze tension
      R.cue(12.890625, 'shake', { amt: 1, dur: 0.05859375, curve: 0 }); // rumble step 1 (held)
      R.cue(12.94921875, 'shake', { amt: 2, dur: 0.05859375, curve: 0 }); // rumble step 2 (held); dead at 13.0078

      // ---- Picture-locked sound ----
      R.sfx(11.25, 'glitch', { dur: 0.234375 }); //                        D
      R.sfx(11.484375, 'impact', { amt: 0.45 }); //                        E stab
      R.sfx(ARM_T0, 'swish', { amt: 0.35 }); //                            arm 1 (picture: 11.5292)
      R.sfx(ARM_T0 + 1 / 60, 'swish', { amt: 0.35 }); //                   arm 2
      R.sfx(ARM_T0 + 2 / 60, 'swish', { amt: 0.35 }); //                   arm 3
      R.sfx(11.71875, 'glitch', { dur: 0.06, pitch: 1.0 }); //             row pop F
      R.sfx(11.8359375, 'glitch', { dur: 0.06, pitch: 1.189 }); //         row pop Ab
      R.sfx(11.953125, 'glitch', { dur: 0.06, pitch: 1.498 }); //          row pop C
      R.sfx(11.8359375, 'whoosh', { dur: 0.3515625, dir: 'up' }); //       dot leap (lands 12.1875)
      R.sfx(12.0703125, 'glitch', { dur: 0.1171875 }); //                  buffer repeat
      R.sfx(12.1875, 'pop', { pitch: 2.0 }); //                            period lands
      R.sfx(12.1875, 'type', { count: 8, dur: 0.1333 }); //                captions
      R.sfx(12.65625, 'riser', { dur: 0.3515625 }); //                     tension, stops dead at 13.0078
      R.sfx(12.65625, 'reverse', { dur: 0.46875 }); //                     final-hit swell, peaks 13.125
      R.sfx(12.890625, 'swish', { amt: 0.35 }); //                         squeeze

      // ---- DOM layers ----
      const full = { width: R.W + 'px', height: R.H + 'px' };
      S.glyphLayer = R.el('div', { style: full }, root);
      const cv = R.canvas(root);
      S.cv = cv.canvas;
      S.ctx = cv.ctx;
      S.dot = R.el('div', {
        style: { width: '112px', height: '112px', borderRadius: '50%', background: P.signal, transformOrigin: '0 0', display: 'none' },
      }, root);
      S.dotD = 112;
      const capLayer = R.el('div', { style: full }, root);
      // goo filter for the A mini (Paper shapes → blur → alpha threshold, as in s06's liquid A)
      const svg = R.svg('svg', { width: 0, height: 0, style: 'position:absolute;left:0;top:0' }, root);
      const flt = R.svg('filter', { id: 's07-goo', x: '-30%', y: '-30%', width: '160%', height: '160%', 'color-interpolation-filters': 'sRGB' }, svg);
      R.svg('feGaussianBlur', { stdDeviation: 3.4 }, flt);
      R.svg('feColorMatrix', { type: 'matrix', values: '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9' }, flt);

      // Six plain Paper letters (one span each; font-size stays 370 and the 291→370 size ramp is a scale about the
      // baseline origin, so no per-frame integer rounding of font metrics can make them jitter).
      S.spans = [];
      for (let i = 0; i < 6; i++) {
        const s = R.el('div', {
          text: LETTERS[i],
          style: {
            fontFamily: R.font.display, fontWeight: '900', fontStretch: '100%', fontSize: CANON_SIZE + 'px',
            letterSpacing: '0px', fontKerning: 'normal', color: P.paper, whiteSpace: 'pre', display: 'none',
          },
        }, S.glyphLayer);
        s.style.lineHeight = '1';
        S.spans.push(s);
      }
      // THE canonical condensed word (identical CSS in s08).
      S.canon = R.el('div', {
        text: 'CLAUDE',
        style: {
          fontFamily: R.font.display, fontWeight: '900', fontStretch: '62%', fontSize: CANON_SIZE + 'px',
          letterSpacing: '0px', fontKerning: 'normal', color: P.paper, left: '0px', width: '1920px', textAlign: 'center',
        },
      }, S.glyphLayer);
      S.canon.style.lineHeight = '1';

      // Captions
      const mono = R.font.mono;
      S.capM = R.el('div', {
        style: { left: '72px', fontFamily: mono, fontWeight: '500', fontSize: '20px', letterSpacing: '0.12em', whiteSpace: 'pre', display: 'none' },
      }, capLayer);
      S.capM.style.lineHeight = '1';
      S.caps = [];
      for (let i = 0; i < 6; i++) {
        const c = R.el('div', {
          style: { fontFamily: mono, fontWeight: '500', fontSize: '16px', letterSpacing: '0.12em', whiteSpace: 'pre', color: P.fog, display: 'none' },
        }, capLayer);
        c.style.lineHeight = '1';
        S.caps.push(c);
      }

      // ---- Measure (the root is display:none during setup; show it for layout reads, then restore) ----
      const prevDisplay = root.style.display;
      root.style.display = 'block';
      S.spans.forEach((s) => { s.style.display = 'block'; });
      S.capM.style.display = 'block';
      S.capM.textContent = 'D';
      S.caps.forEach((c) => { c.style.display = 'block'; c.textContent = 'X'; });
      const rr = root.getBoundingClientRect();
      const k = rr.width / R.W || 1;
      const baselineOf = (el) => {
        const mk = document.createElement('span');
        mk.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
        el.appendChild(mk);
        const v = (mk.getBoundingClientRect().top - el.getBoundingClientRect().top) / k;
        mk.remove();
        return v;
      };
      S.canonBase = baselineOf(S.canon); // 308 at 370 px (Chromium rounds the ascent)
      S.canon.style.top = (CANON_BASE - S.canonBase) + 'px';
      const tn = S.canon.firstChild, rng = document.createRange();
      S.canonX = [];
      for (let i = 0; i < 6; i++) {
        rng.setStart(tn, i);
        rng.setEnd(tn, i + 1);
        S.canonX.push((rng.getBoundingClientRect().left - rr.left) / k);
      }
      S.spanBase = S.spans.map((s) => baselineOf(s));
      S.spans.forEach((s, i) => { s.style.transformOrigin = `0px ${S.spanBase[i]}px`; });
      S.capMBase = baselineOf(S.capM);
      S.capM.style.top = Math.round(976 - S.capMBase) + 'px';
      S.capBase = baselineOf(S.caps[0]);
      // row captions: centre each on its cell (advance 0.6em + tracking 0.12em; drop the trailing tracking)
      const adv = S.caps[0].getBoundingClientRect().width / k;
      S.capAdv = adv;
      S.caps.forEach((c, i) => {
        const w = CAPTIONS[i].length * adv - 16 * 0.12;
        c.style.left = Math.round(cellCx(i) - w / 2) + 'px';
        c.style.top = Math.round(744 - S.capBase) + 'px';
        c.textContent = '';
        c.style.display = 'none';
      });
      S.capM.textContent = '';
      S.capM.style.display = 'none';
      S.spans.forEach((s) => { s.style.display = 'none'; });
      S.canon.style.display = 'none';
      root.style.display = prevDisplay;

      // ---- Plain glyph placements (ink-centred in the cells, shared baseline 640) and canonical slots ----
      S.plainX0 = [];
      S.plainInk = [];
      for (let i = 0; i < 6; i++) {
        const b = inkBox(`900 ${PLAIN_SIZE}px Archivo`, LETTERS[i]);
        S.plainInk.push(b);
        S.plainX0.push(Math.round(cellCx(i) - (b.l + b.r) / 2));
      }

      // ---- D — GLITCH: re-derive the placement so the counter's inscribed circle sits on the anchor ----
      const DFONT = '900 1109px Archivo';
      let dOx = 516, dOy = 922;
      const cc = counterCircle(DFONT, 'D', dOx, dOy);
      if (cc) { dOx += Math.round(AX - cc.x); dOy += Math.round(AY - cc.y); }
      S.dCounter = cc;
      S.dOrigin = [dOx, dOy];
      const dInk = inkBox(DFONT, 'D');
      // source region for the three layers (Paper, Signal, Volt)
      S.dRx = Math.floor(dOx + dInk.l) - 4;
      S.dRy = Math.floor(dOy + dInk.t) - 4;
      S.dRw = Math.ceil(dInk.r - dInk.l) + 8;
      S.dRh = Math.ceil(dInk.b - dInk.t) + 8;
      const dLayer = (col) => {
        const o = offscreen(S.dRw, S.dRh);
        o.g.font = DFONT;
        o.g.fillStyle = col;
        o.g.fillText('D', dOx - S.dRx, dOy - S.dRy);
        return o.c;
      };
      S.dPaper = dLayer(P.paper);
      S.dSignal = dLayer(P.signal);
      S.dVolt = dLayer(P.volt);
      // the D box that the 14 slices divide (whole pixels)
      S.dTop = Math.floor(dOy + dInk.t);
      S.dBot = Math.ceil(dOy + dInk.b);
      S.dSl = new Int32Array(15);
      // scanline pattern: 2 px Paper @ 8% every 4 px
      const sp = offscreen(4, 4);
      sp.g.fillStyle = R.rgba(P.paper, 0.08);
      sp.g.fillRect(0, 0, 4, 2);
      S.scan = S.ctx.createPattern(sp.c, 'repeat');

      // ---- Minis ----
      // C: halftone, pitch 8, lattice rotated 15°, coverage sampled once from the plain C raster
      {
        const x0 = cellX(0), ox = S.plainX0[0];
        const o = offscreen(CW, CH, true);
        o.g.font = `900 ${PLAIN_SIZE}px Archivo`;
        o.g.fillStyle = '#fff';
        o.g.fillText('C', ox - x0, PLAIN_BASE - CY0);
        const d = o.g.getImageData(0, 0, CW, CH).data;
        const b = S.plainInk[0];
        const inkCx = ox + (b.l + b.r) / 2;
        // ripple source: the C's counter (s06 anchor offset from the C ink centre, scaled 291/1109)
        const src = [inkCx + 18.5 * (PLAIN_SIZE / 1109), CCY];
        const ang = R.deg(15), pitch = 8;
        const ux = Math.cos(ang) * pitch, uy = Math.sin(ang) * pitch, vx = -uy, vy = ux;
        const xs = [], ys = [], cov = [], dist = [];
        for (let a = -40; a <= 40; a++) {
          for (let bb = -40; bb <= 40; bb++) {
            const px = src[0] + a * ux + bb * vx, py = src[1] + a * uy + bb * vy;
            if (px < x0 + 3 || px > x0 + CW - 3 || py < CY0 + 3 || py > CY0 + CH - 3) continue;
            const lx = Math.round(px - x0), ly = Math.round(py - CY0);
            let s = 0, n = 0;
            for (let yy = ly - 3; yy <= ly + 3; yy++) {
              for (let xx = lx - 3; xx <= lx + 3; xx++) {
                if (xx < 0 || yy < 0 || xx >= CW || yy >= CH) continue;
                s += d[(yy * CW + xx) * 4 + 3];
                n++;
              }
            }
            const c = n ? s / (n * 255) : 0;
            if (c < 0.04) continue;
            xs.push(px); ys.push(py); cov.push(c); dist.push(Math.hypot(px - src[0], py - src[1]));
          }
        }
        S.mC = { xs, ys, cov, dist, n: xs.length };
      }
      // L: module grid pitch 34, module 30 (the 20-module L is exactly 200 × 200), centred on the cell
      {
        const cx = cellCx(1);
        const at = (c, r) => [cx + 34 * (c - 7.5), CCY + 34 * (r - 3.5)];
        const grid = [];
        for (let c = 0; c <= 14; c++) for (let r = -2; r <= 9; r++) grid.push(at(c, r));
        const L = [];
        for (let r = 1; r <= 6; r++) for (let c = 5; c <= 6; c++) L.push(at(c, r)); //  stem, top → down
        for (let c = 7; c <= 10; c++) for (let r = 5; r <= 6; r++) L.push(at(c, r)); // foot, corner → end
        S.mL = { grid, L };
      }
      // A: Paper A (wght 600) through a light goo, two wobbling bumps riding its outer contour
      {
        const b = inkBox(`600 ${PLAIN_SIZE}px Archivo`, 'A');
        const ox = Math.round(cellCx(2) - (b.l + b.r) / 2);
        const GX = cellCx(2) - 130, GY = CCY - 130, GW = 260, GH = 260;
        const base = offscreen(GW, GH, true);
        base.g.font = `600 ${PLAIN_SIZE}px Archivo`;
        base.g.fillStyle = P.paper;
        base.g.fillText('A', ox - GX, PLAIN_BASE - GY);
        // outer edge path: left edge bottom → top, right edge top → bottom (smoothed)
        const d = base.g.getImageData(0, 0, GW, GH).data;
        const left = [], right = [];
        for (let y = 0; y < GH; y++) {
          let l = -1, r = -1;
          for (let x = 0; x < GW; x++) if (d[(y * GW + x) * 4 + 3] >= 128) { if (l < 0) l = x; r = x; }
          if (l >= 0) { left.push([l + GX, y + GY + 0.5]); right.push([r + 1 + GX, y + GY + 0.5]); }
        }
        const smooth = (pts) => pts.map((p, i) => {
          let sx = 0, n = 0;
          for (let j = Math.max(0, i - 3); j <= Math.min(pts.length - 1, i + 3); j++) { sx += pts[j][0]; n++; }
          return [sx / n, p[1]];
        });
        const path = R.poly.resample(smooth(left).reverse().concat(smooth(right)), 240, false);
        const nrm = path.map((p, i) => {
          const a = path[Math.max(0, i - 3)], c = path[Math.min(path.length - 1, i + 3)];
          const tx = c[0] - a[0], ty = c[1] - a[1], l = Math.hypot(tx, ty) || 1;
          return [ty / l, -tx / l]; // outward for this (clockwise-on-screen) traversal
        });
        let len = 0;
        for (let i = 1; i < path.length; i++) len += Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]);
        S.mA = { base: base.c, work: offscreen(GW, GH), GX, GY, GW, GH, path, nrm, len };
      }
      // D: Paper D with a Signal/Volt split (±6) and 5 slices (±8, re-rolled every 4 frames)
      {
        const x0 = cellX(4), b = S.plainInk[4], ox = S.plainX0[4];
        const layer = (col) => {
          const o = offscreen(CW, CH);
          o.g.font = `900 ${PLAIN_SIZE}px Archivo`;
          o.g.fillStyle = col;
          o.g.fillText('D', ox - x0, PLAIN_BASE - CY0);
          return o.c;
        };
        const top = Math.floor(PLAIN_BASE + b.t) - 1, bot = Math.ceil(PLAIN_BASE + b.b) + 1;
        const sl = [];
        for (let i = 0; i <= 5; i++) sl.push(Math.round(top + ((bot - top) * i) / 5));
        S.mD = { paper: layer(P.paper), signal: layer(P.signal), volt: layer(P.volt), sl };
      }
      // row buffer for the stutter
      S.rowBuf = offscreen(R.W, CH);
    },

    update(lt, p, t) {
      const S = this;
      const f = Math.round(t * 60);
      const g = S.ctx;
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.globalCompositeOperation = 'source-over';
      g.globalAlpha = 1;
      g.filter = 'none';
      g.clearRect(0, 0, R.W, R.H);
      if (t < T_E) drawD(S, g, t, f);
      else if (t < T_ROW) drawE(S, g, t);
      else drawRow(S, g, t, f);
      updateDot(S, t);
      updateCaptions(S, t, f);
      updateGlyphs(S, t);
    },
  });

  // ------------------------------------------------------------------------------------------------------------
  // D — GLITCH (11.25 → 11.484375)
  // ------------------------------------------------------------------------------------------------------------
  function drawD(S, g, t, f) {
    g.fillStyle = P.ink;
    g.fillRect(0, 0, R.W, R.H);
    const full = t < T_HALF;
    const amp = full ? 90 : 22.5; // from 11.3671875 the glitch half-resolves so the D reads
    const roll = Math.floor(f / 2); // re-rolled every 2 frames
    const cut = f === firstFrame(T_IN); // centre-lock: the protagonist is intact on the cut frame
    // 14 slices of the D box with seeded heights (datamosh bands are never evenly spaced)
    const sl = S.dSl;
    let sum = 0;
    for (let k = 0; k < 14; k++) sum += 0.35 + 1.3 * R.hash(k, roll, 703);
    let acc = 0;
    sl[0] = S.dTop;
    for (let k = 0; k < 14; k++) {
      acc += 0.35 + 1.3 * R.hash(k, roll, 703);
      sl[k + 1] = Math.round(S.dTop + ((S.dBot - S.dTop) * acc) / sum);
    }
    // full-strength phase only: one smeared band (pixel-stretch) and one band that drops the Paper plate
    const smearK = full ? Math.floor(R.hash(roll, 1, 704) * 14) : -1;
    const dropK = full ? (smearK + 3 + Math.floor(R.hash(roll, 2, 704) * 9)) % 14 : -1;
    for (let k = 0; k < 14; k++) {
      const y0 = sl[k], y1 = sl[k + 1], h = y1 - y0;
      if (h <= 0) continue;
      const off = Math.round(glitchOff(R.hash(k, roll, 701), amp));
      const split = 22 + Math.round((amp / 90) * 10 * (R.hash(k, roll, 702) - 0.5));
      const sy = y0 - S.dRy;
      let dx = S.dRx + off, dw = S.dRw;
      if (k === smearK) {
        // stretch the band horizontally about the anchor (a pixel-sort streak)
        const st = 1.6 + 1.2 * R.hash(roll, 3, 704);
        dx = AX + off + (S.dRx - AX) * st;
        dw = S.dRw * st;
      }
      g.globalCompositeOperation = 'source-over';
      g.drawImage(S.dSignal, 0, sy, S.dRw, h, dx - split, y0, dw, h);
      g.globalCompositeOperation = 'screen';
      g.drawImage(S.dVolt, 0, sy, S.dRw, h, dx + split, y0, dw, h);
      g.globalCompositeOperation = 'source-over';
      if (k !== dropK) g.drawImage(S.dPaper, 0, sy, S.dRw, h, dx, y0, dw, h);
      // the protagonist in the counter is sliced with the D
      if (y1 > AY - 56 && y0 < AY + 56) {
        g.save();
        g.beginPath();
        g.rect(0, y0, R.W, h);
        g.clip();
        g.fillStyle = P.signal;
        g.beginPath();
        if (cut || k !== smearK) g.arc(AX + (cut ? 0 : off), AY, 56, 0, TAU);
        else g.ellipse(AX + off, AY, 56 * (dw / S.dRw), 56, 0, 0, TAU);
        g.fill();
        g.restore();
      }
    }
    // flicker blocks on alternate frames (seeded spots hugging the slice seams)
    if ((f - firstFrame(T_IN)) % 2 === 0) {
      const cols = [P.signal, P.volt, P.acid];
      const n = t < T_HALF ? 6 : 4;
      for (let b = 0; b < n; b++) {
        const h1 = R.hash(b, f, 811), h2 = R.hash(b, f, 812), h3 = R.hash(b, f, 813), h4 = R.hash(b, f, 814);
        const w = Math.round(30 + 190 * h1 * h1), hh = Math.round(8 + 32 * h2 * h2);
        const seam = sl[1 + Math.floor(h3 * 13)];
        const y = seam + Math.round((h4 - 0.5) * 30) - (hh >> 1);
        const x = Math.round(470 + R.hash(b, f, 815) * (1450 - 470 - w));
        g.fillStyle = cols[Math.floor(R.hash(b, f, 816) * 3)];
        g.fillRect(x, y, w, hh);
      }
    }
    g.fillStyle = S.scan;
    g.fillRect(0, 0, R.W, R.H);
  }

  // ------------------------------------------------------------------------------------------------------------
  // E — SHAPE (11.484375 → 11.71875)
  // ------------------------------------------------------------------------------------------------------------
  const armTip = (k, t) => {
    const ta = T_LAND + k / 60;
    if (t < ta) return STEM.x1;
    return STEM.x1 + ARMS[k].len * EZ.punch(R.seg(t, ta, ta + ARM_DUR));
  };
  function drawE(S, g, t) {
    g.fillStyle = P.acid;
    g.fillRect(0, 0, R.W, R.H);
    g.fillStyle = P.ink;
    // stem: drops from above (swift, 5 frames), 1-frame landing squash anchored at its base
    const ty = -1100 * (1 - EZ.swift(R.seg(t, T_E, T_LAND)));
    let sy = 1;
    if (t >= T_LAND && t < T_LAND + 1 / 60) sy = 0.92;
    const sx = 1 / sy, cx = (STEM.x0 + STEM.x1) / 2;
    const w = (STEM.x1 - STEM.x0) * sx, h = (STEM.y1 - STEM.y0) * sy;
    g.fillRect(cx - w / 2, STEM.y1 + ty - h, w, h);
    // arms punch out of the stem, 1-frame stagger top → bottom, each trailing three speed lines
    for (let k = 0; k < 3; k++) {
      const ta = T_LAND + k / 60;
      if (t < ta) continue;
      const A = ARMS[k], tip = armTip(k, t);
      g.fillRect(STEM.x1, A.y0, tip - STEM.x1, A.y1 - A.y0);
      for (const L of SPEED) {
        const q = R.seg(t, ta + L.delay, ta + 6 / 60);
        if (q >= 1 || t < ta + L.delay) continue;
        const xe = tip - L.gap;
        const xs = STEM.x1 + 6 + (xe - STEM.x1 - 6) * EZ.inCubic(q);
        if (xe - xs < 2) continue;
        const y = Math.round(L.edge === 'top' ? A.y0 + L.dy : A.y1 + L.dy) - 2;
        g.fillRect(xs, y, xe - xs, 4);
      }
    }
  }
  /** The middle arm's overshoot kisses the dot: contact-driven squash to 0.85 × 1.18, then a TIGHT release. */
  function kissSquash(t) {
    const ta = T_LAND + 1 / 60;
    const tPeak = ta + 0.42 * ARM_DUR; // punch() peaks at u ≈ 0.42 (1.110)
    const peakTip = STEM.x1 + ARMS[1].len * 1.1102;
    const rest = AX - 56;
    if (t < tPeak) {
      const pen = armTip(1, t) - rest;
      if (pen <= 0) return 1;
      return 1 - 0.15 * clamp(pen / (peakTip - rest));
    }
    return 0.85 + 0.15 * R.spring(t - tPeak, TIGHT);
  }

  // ------------------------------------------------------------------------------------------------------------
  // THE ROW (11.71875 → ~12.86): pops, stutter, reveal, collapse
  // ------------------------------------------------------------------------------------------------------------
  function drawRow(S, g, t, f) {
    const stutter = t >= T_STUT && t < T_REV;
    const dst = stutter ? S.rowBuf.g : g;
    if (stutter) {
      dst.setTransform(1, 0, 0, 1, 0, -CY0);
      dst.clearRect(0, CY0, R.W, CH);
    }
    for (let i = 0; i < 6; i++) {
      const tp = POP_T[i];
      if (t < tp) continue;
      const tc = T_FLAT + i / 60;
      const q = EZ.whip(R.seg(t, tc, tc + COLLAPSE_DUR));
      if (q >= 1) continue;
      const s = 0.7 + 0.3 * EZ.swift(R.seg(t, tp, tp + POP_DUR));
      const x0 = cellX(i), cx = cellCx(i);
      dst.save();
      if (s !== 1) {
        dst.translate(cx, CCY);
        dst.scale(s, s);
        dst.translate(-cx, -CCY);
      }
      const ix = (q * CW) / 2, iy = (q * CH) / 2;
      dst.beginPath();
      dst.rect(x0 + ix, CY0 + iy, CW - 2 * ix, CH - 2 * iy);
      dst.clip();
      drawCell(S, dst, i, t, f);
      dst.restore();
      if (t - tp < 1 / 60) {
        // 1-frame Paper outline flash on the pop
        dst.save();
        dst.translate(cx, CCY);
        dst.scale(s, s);
        dst.strokeStyle = P.paper;
        dst.lineWidth = 2 / s;
        dst.strokeRect(-CW / 2 + 1 / s, -CH / 2 + 1 / s, CW - 2 / s, CH - 2 / s);
        dst.restore();
      }
    }
    if (stutter) {
      dst.setTransform(1, 0, 0, 1, 0, 0);
      const n = 10, h = CH / n;
      for (let k = 0; k < n; k++) {
        const off = Math.round(glitchOff(R.hash(k, f, 901), 40));
        const y0 = Math.round(k * h), y1 = Math.round((k + 1) * h);
        g.drawImage(S.rowBuf.c, 0, y0, R.W, y1 - y0, off, CY0 + y0, R.W, y1 - y0);
      }
    }
  }

  function drawCell(S, g, i, t, f) {
    const x0 = cellX(i);
    g.fillStyle = GROUND[i];
    g.fillRect(x0, CY0, CW, CH);
    switch (i) {
      case 0: miniC(S, g, t); break;
      case 1: miniL(S, g, t); break;
      case 2: miniA(S, g, t); break;
      case 3: miniU(S, g, t); break;
      case 4: miniD(S, g, t, f); break;
      default: miniE(g); break;
    }
  }

  // C — HALFTONE: Ink dots on Paper, slow ripple from the counter
  function miniC(S, g, t) {
    const m = S.mC;
    const ph = (t - T_ROW) / 0.46875; // one ring per beat
    g.fillStyle = P.ink;
    g.beginPath();
    for (let k = 0; k < m.n; k++) {
      const r = 3.8 * m.cov[k] * (0.76 + 0.24 * Math.sin(TAU * (m.dist[k] / 52 - ph)));
      if (r < 0.3) continue;
      g.moveTo(m.xs[k] + r, m.ys[k]);
      g.arc(m.xs[k], m.ys[k], r, 0, TAU);
    }
    g.fill();
  }

  // L — GRID: Graphite micro-grid, 20 Paper circle-modules with a slow pulse along the stroke
  function miniL(S, g, t) {
    const m = S.mL;
    g.strokeStyle = P.graphite;
    g.lineWidth = 1;
    g.beginPath();
    for (const [x, y] of m.grid) g.rect(Math.round(x - 15) + 0.5, Math.round(y - 15) + 0.5, 29, 29);
    g.stroke();
    const ph = (t - T_ROW) / 0.9375;
    g.fillStyle = P.paper;
    g.beginPath();
    for (let k = 0; k < m.L.length; k++) {
      const [x, y] = m.L[k];
      const r = 15 * (1 + 0.045 * Math.sin(TAU * (ph - k / 20)));
      g.moveTo(x + r, y);
      g.arc(x, y, r, 0, TAU);
    }
    g.fill();
  }

  // A — LIQUID: goo'd Paper A with two wobbling bumps riding the outer contour
  function miniA(S, g, t) {
    const m = S.mA, w = m.work.g;
    w.setTransform(1, 0, 0, 1, 0, 0);
    w.clearRect(0, 0, m.GW, m.GH);
    w.drawImage(m.base, 0, 0);
    w.fillStyle = P.paper;
    const lt = t - T_ROW;
    const B = [
      { s0: 0.1, dir: 1, ph: 0 },
      { s0: 0.52, dir: 1, ph: 2.1 },
    ];
    for (const b of B) {
      const s = clamp(b.s0 + (b.dir * 230 * lt) / m.len, 0, 0.999);
      const fi = s * (m.path.length - 1), i0 = Math.floor(fi), fr = fi - i0;
      const p0 = m.path[i0], p1 = m.path[Math.min(i0 + 1, m.path.length - 1)], n = m.nrm[i0];
      const r = 5.5 * (1 + 0.28 * Math.sin(TAU * 3.2 * lt + b.ph));
      const x = lerp(p0[0], p1[0], fr) + n[0] * r * 0.35 - m.GX;
      const y = lerp(p0[1], p1[1], fr) + n[1] * r * 0.35 - m.GY;
      w.beginPath();
      w.arc(x, y, r, 0, TAU);
      w.fill();
    }
    g.filter = 'url(#s07-goo)';
    g.drawImage(m.work.c, m.GX, m.GY);
    g.filter = 'none';
  }

  // U — DATA: Ink stems and half-donut on Paper, a dashed Fog axis and 10% ticks
  function miniU(S, g, t) {
    const cx = cellCx(3), cy = CCY, x0 = cellX(3);
    const ro = 100, ri = 61.54, bw = ro - ri;
    g.strokeStyle = P.fog;
    g.lineWidth = 1;
    g.setLineDash([3, 2]);
    g.beginPath();
    g.moveTo(x0, cy + 0.5);
    g.lineTo(x0 + CW, cy + 0.5);
    g.stroke();
    g.setLineDash([]);
    g.beginPath();
    for (let k = 0; k <= 10; k++) {
      const a = Math.PI - (k * Math.PI) / 10;
      const c = Math.cos(a), s = Math.sin(a);
      g.moveTo(cx + c * (ro + 4), cy + s * (ro + 4));
      g.lineTo(cx + c * (ro + 9), cy + s * (ro + 9));
    }
    g.stroke();
    const lt = t - T_ROW;
    const h0 = 100 + 1.6 * Math.sin(TAU * lt / 0.9375), h1 = 100 + 1.6 * Math.sin(TAU * lt / 0.9375 + 2.2);
    g.fillStyle = P.ink;
    g.fillRect(cx - ro, cy - h0, bw, h0);
    g.fillRect(cx + ri, cy - h1, bw, h1);
    g.beginPath();
    g.moveTo(cx - ro, cy);
    g.arc(cx, cy, ro, Math.PI, 0, true);
    g.lineTo(cx + ri, cy);
    g.arc(cx, cy, ri, 0, Math.PI, false);
    g.closePath();
    g.fill();
  }

  // D — GLITCH: Paper D, Signal/Volt split ±6, 5 slices ±8 re-rolled every 4 frames, scanlines
  function miniD(S, g, t, f) {
    const m = S.mD, x0 = cellX(4);
    const roll = Math.floor(f / 4);
    for (let k = 0; k < 5; k++) {
      const y0 = m.sl[k], y1 = m.sl[k + 1], h = y1 - y0;
      const off = Math.round(glitchOff(R.hash(k, roll, 301), 8));
      const sy = y0 - CY0;
      g.globalCompositeOperation = 'source-over';
      g.drawImage(m.signal, 0, sy, CW, h, x0 + off - 6, y0, CW, h);
      g.globalCompositeOperation = 'screen';
      g.drawImage(m.volt, 0, sy, CW, h, x0 + off + 6, y0, CW, h);
      g.globalCompositeOperation = 'source-over';
      g.drawImage(m.paper, 0, sy, CW, h, x0 + off, y0, CW, h);
    }
    g.fillStyle = S.scan;
    g.fillRect(x0, CY0, CW, CH);
  }

  // E — SHAPE: the vignette's rectangles scaled 200/780 about the E box centre, centred on the cell
  function miniE(g) {
    g.fillStyle = P.ink;
    g.fillRect(1495, 440, 49, 200);
    g.fillRect(1543, 440, 126, 44);
    g.fillRect(1543, 518, 62, 44);
    g.fillRect(1543, 596, 126, 44);
  }

  // ------------------------------------------------------------------------------------------------------------
  // The protagonist (DOM disc) from the E cut onward
  // ------------------------------------------------------------------------------------------------------------
  function updateDot(S, t) {
    const el = S.dot;
    if (t < T_E) {
      if (el.style.display !== 'none') el.style.display = 'none';
      return;
    }
    if (el.style.display !== 'block') el.style.display = 'block';
    let d = 112, x = AX, y = AY, sx = 1, sy = 1, rot = 0, skew = 0, anchor = 'center';
    if (t < T_ROW) {
      // E: centre-locked, kissed by the middle arm
      sx = kissSquash(t);
      sy = 1 / sx;
    } else if (t < T_AU) {
      // anticipation at the anchor: squash 1.3 × 0.77 on its contact point, leaning into the leap
      const a = EZ.swift(R.seg(t, T_ROW, T_ROW + 4 / 60));
      sx = lerp(1, 1.3, a);
      sy = lerp(1, 0.77, a);
      skew = -7 * a;
      anchor = 'bottom';
      y = AY + 56;
    } else if (t < T_REV) {
      // the leap: x linear, y parabolic (apex ≈ 200), shrinking Ø112 → Ø56, stretched along its velocity
      const u = (t - T_AU) / LEAP_DUR;
      x = 960 + 790 * u;
      y = 540 + 142 * u - 4 * 407.9 * u * (1 - u);
      const vx = 790 / LEAP_DUR, vy = (142 - 4 * 407.9 * (1 - 2 * u)) / LEAP_DUR;
      d = lerp(112, 56, R.smoothstep(0, 1, u));
      const st = 1 + 0.3 * R.smoothstep(800, 5200, Math.hypot(vx, vy));
      sx = st;
      sy = 1 / st;
      rot = Math.atan2(vy, vx);
    } else {
      d = PERIOD.d;
      x = PERIOD.x;
      y = PERIOD.y;
      const tl = t - T_REV;
      if (t < T_SQ) {
        // landing: 2-frame squash 1.4 × 0.71 on the cell baseline, then a TIGHT settle
        if (tl < 2 / 60) { sx = 1.4; sy = 0.71; } else { sx = 1.4 - 0.4 * R.spring(tl - 2 / 60, TIGHT); sy = 1 / sx; }
        anchor = 'bottom';
        y = PERIOD.y + d / 2;
      } else {
        // squeeze (snap) and the rest pose
        const q = EZ.snap(R.seg(t, T_SQ, T_REST));
        x = lerp(PERIOD.x, FINAL.x, q);
        y = lerp(PERIOD.y, FINAL.y, q);
        d = lerp(PERIOD.d, FINAL.d, q);
        const tr = tremble(t, 1);
        x += tr[0];
        y += tr[1];
      }
    }
    if (d !== S.dotD) {
      el.style.width = d + 'px';
      el.style.height = d + 'px';
      S.dotD = d;
    }
    const oy = anchor === 'bottom' ? -d : -d / 2;
    let tf = `translate(${x}px,${y}px)`;
    if (rot) tf += ` rotate(${rot}rad)`;
    if (skew) tf += ` skewX(${skew}deg)`;
    if (sx !== 1 || sy !== 1) tf += ` scale(${sx},${sy})`;
    tf += ` translate(${-d / 2}px,${oy}px)`;
    el.style.transform = tf;
  }

  // ------------------------------------------------------------------------------------------------------------
  // Captions
  // ------------------------------------------------------------------------------------------------------------
  function updateCaptions(S, t, f) {
    // montage caption (x 72, baseline 976): types on at 3 chars/frame from each cut, HUD colour
    let txt = '', col = P.paper;
    if (t < T_E) {
      txt = 'D — GLITCH'.slice(0, 3 * (f - firstFrame(T_IN) + 1));
    } else if (t < T_ROW) {
      txt = 'E — SHAPE'.slice(0, 3 * (f - firstFrame(T_E) + 1));
      col = P.ink;
    }
    if (txt) {
      if (S.capM.textContent !== txt) S.capM.textContent = txt;
      S.capM.style.color = col;
      S.capM.style.display = 'block';
    } else if (S.capM.style.display !== 'none') S.capM.style.display = 'none';

    // row captions (baseline 744): 2 chars/frame, 1-frame stagger L→R from the reveal; wipe out right→left
    const k = f - firstFrame(T_REV);
    const wipe = EZ.inQuad(R.seg(t, T_FLAT, T_FLAT + 0.1));
    for (let i = 0; i < 6; i++) {
      const c = S.caps[i];
      const n = clamp(2 * (k - i + 1), 0, CAPTIONS[i].length);
      if (t < T_REV || n <= 0 || wipe >= 1) {
        if (c.style.display !== 'none') c.style.display = 'none';
        continue;
      }
      const s = CAPTIONS[i].slice(0, n);
      if (c.textContent !== s) c.textContent = s;
      c.style.clipPath = wipe > 0 ? `inset(0 ${(wipe * 100).toFixed(2)}% 0 0)` : 'none';
      c.style.display = 'block';
    }
  }

  // ------------------------------------------------------------------------------------------------------------
  // Plain glyphs (flatten), the squeeze into the canonical slots, and the rest-pose swap
  // ------------------------------------------------------------------------------------------------------------
  function updateGlyphs(S, t) {
    const showSpans = t >= T_FLAT && t < T_REST;
    const showCanon = t >= T_REST;
    const cd = showCanon ? 'block' : 'none';
    if (S.canon.style.display !== cd) S.canon.style.display = cd;
    for (let i = 0; i < 6; i++) {
      const s = S.spans[i];
      const dd = showSpans ? 'block' : 'none';
      if (s.style.display !== dd) s.style.display = dd;
    }
    if (!showSpans) return;
    const q = EZ.snap(R.seg(t, T_SQ, T_REST));
    const sc = lerp(PLAIN_SIZE / CANON_SIZE, 1, q);
    const stretch = lerp(100, 62, q);
    const base = lerp(PLAIN_BASE, CANON_BASE, q);
    const tr = tremble(t, 0);
    for (let i = 0; i < 6; i++) {
      const s = S.spans[i];
      const x = lerp(S.plainX0[i], S.canonX[i], q) + tr[0];
      const y = base - S.spanBase[i] + tr[1];
      s.style.fontStretch = stretch.toFixed(3) + '%';
      s.style.transform = `translate(${x}px,${y}px) scale(${sc})`;
    }
  }
})();
