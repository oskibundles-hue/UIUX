/*
 * s02-timing — "Timing — the dot learns to move"   1.875 → 3.75 s · bar 2 · z 20 · Ink
 *
 * The full stop born at the end of WIDE becomes a character. It crouches (anticipation), leaps a
 * long arc to "Timing", then bounces back along the sentence on a decaying grid rhythm
 * (3 16ths → 8th → 8th → 16th → 16th), stamping each word into existence, lands as the sentence's
 * hanging period, wobbles to rest, notices the camera and dives into it (exponential zoom) until
 * the frame is flat Signal — the rest pose s03 unfolds from.
 *
 * Layers (bottom → top): notation canvas (dashed arcs, onion skins, spacing chart, labels,
 * leaders) · world div (ground line + per-letter serif sentence; scaled/blurred in the dive) ·
 * dot canvas (the dot, impact ring, notice pulse, dive disc) · flat Signal 2D override.
 *
 * Everything is a pure function of t: hops are closed-form parabolas, onion skins are the same
 * pose function sampled at t − 2k/60, springs are analytic.
 */
(function () {
  'use strict';

  const PAL = R.pal;
  const FR = 1 / 60;
  const TAU = Math.PI * 2;
  const VOLT_LIGHT = '#718EF8';
  const FOG_RGB = R.col(PAL.fog);
  const PAPER_RGB = R.col(PAL.paper);

  // ---------------------------------------------------------------------------------------------
  // Timeline (global seconds, 128 BPM grid)
  // ---------------------------------------------------------------------------------------------
  const T_IN = 1.875; //             2.1.1  anticipation (groove in)
  const T_LEAP = 1.9921875; //       2.1.2  take-off
  const T_L = [2.34375, 2.578125, 2.8125, 2.9296875, 3.046875]; // Timing · is · everything · FULL STOP · micro-hop
  const T_NOTICE = 3.28125; //       2.4.1  notices the camera
  const T_DIVE = 3.515625; //        2.4.3  the dive
  const T_REST = 223 / 60; //        2D override: frames 223–224 are flat Signal
  const CONTACT = 2 / 60; //         ground-contact time of each landing (2-frame squash)
  const PATH_LEAD = 0.06; //         the dashed path is drawn this far ahead of the dot

  // ---------------------------------------------------------------------------------------------
  // Geometry
  // ---------------------------------------------------------------------------------------------
  const DOT_R = 44;
  const GROUND = 780; //             baseline of the sentence = ground line
  const REST_Y = GROUND - DOT_R; //  736: grounded dot centre
  const START = [1731, 656]; //      s01 handoff: Ø88 at (1731,656), bottom on WIDE's baseline (700)
  const START_FLOOR = 700;
  const SENT = 'Timing is everything';
  const SERIF = "italic 400 200px 'Instrument Serif'";
  const MONO = "500 14px 'JetBrains Mono'";
  const MONO_ADV = 8.4, MONO_TRACK = 1.68; // 0.6 em advance, 0.12 em tracking
  const WORLD_TOP = 560, WORLD_H = 320; // the (small) sentence layer: y 560 → 880

  // Springs
  const ERUPT = { stiffness: 700, damping: 30, velocity: 6 }; // POP character, tuned to peak at the storyboard's 1.12
  const TIGHT = { stiffness: 420, damping: 26 };
  const WOBBLE = { stiffness: 300, damping: 10 };

  // ---------------------------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------------------------
  const clamp = R.clamp, lerp = R.lerp, seg = R.seg;
  const E = R.ease;
  const rgba = (rgb, a) => `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;

  /** Parabolic hop: x linear in time, y(τ) = y0 + (y1−y0)τ − 4hτ(1−τ). */
  function makeHop(t0, t1, x0, y0, x1, y1, h) {
    const hop = { t0, t1, x0, y0, x1, y1, h, T: t1 - t0 };
    hop.at = (tau) => [x0 + (x1 - x0) * tau, y0 + (y1 - y0) * tau - 4 * h * tau * (1 - tau)];
    hop.vel = (tau) => [(x1 - x0) / hop.T, ((y1 - y0) - 4 * h * (1 - 2 * tau)) / hop.T];
    // arc-length table for trim-path drawing
    const N = 120, pts = [], cum = [0];
    for (let i = 0; i <= N; i++) pts.push(hop.at(i / N));
    for (let i = 1; i <= N; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    hop.pts = pts; hop.cum = cum; hop.len = cum[N]; hop.N = N;
    hop.sAt = (tau) => { // arc length at τ (linear within a sample)
      const f = clamp(tau) * N, i = Math.min(N - 1, Math.floor(f));
      return cum[i] + (cum[i + 1] - cum[i]) * (f - i);
    };
    return hop;
  }

  /** Point on a hop polyline at arc length s. */
  function pointAtS(hop, s) {
    const { cum, pts, N } = hop;
    s = clamp(s, 0, hop.len);
    let lo = 0, hi = N;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (cum[m] <= s) lo = m; else hi = m; }
    const d = cum[hi] - cum[lo], f = d > 0 ? (s - cum[lo]) / d : 0;
    return [pts[lo][0] + (pts[hi][0] - pts[lo][0]) * f, pts[lo][1] + (pts[hi][1] - pts[lo][1]) * f, lo, hi];
  }

  /** Trace the part of a hop between arc lengths s0 and s1 into the current path. */
  function traceHop(ctx, hop, s0, s1) {
    if (s1 - s0 < 0.5) return false;
    const a = pointAtS(hop, s0), b = pointAtS(hop, s1);
    ctx.moveTo(a[0], a[1]);
    for (let i = a[3]; i <= b[2]; i++) ctx.lineTo(hop.pts[i][0], hop.pts[i][1]);
    ctx.lineTo(b[0], b[1]);
    return true;
  }

  // Pose = ellipse: points = (cx,cy) + M·(r cosφ, r sinφ), M = [[a, c],[b, d]] (canvas setTransform order).
  const poseRound = (cx, cy, k = 1) => ({ cx, cy, a: k, b: 0, c: 0, d: k });
  /** Squash (sx, sy) anchored at a bottom contact point (ax, ay), leaning by skew angle k (rad, + = top left). */
  function poseSquash(ax, ay, sx, sy, k) {
    const tk = Math.tan(k);
    return { cx: ax - DOT_R * sy * tk, cy: ay - DOT_R * sy, a: sx, b: 0, c: tk * sy, d: sy };
  }
  /** Volume-preserving stretch s along direction θ, centred at (cx,cy). */
  function poseStretch(cx, cy, s, th) {
    const c = Math.cos(th), sn = Math.sin(th), is = 1 / s;
    const A = s * c * c + is * sn * sn, D = s * sn * sn + is * c * c, B = c * sn * (s - is);
    return { cx, cy, a: A, b: B, c: B, d: D };
  }
  function tracePose(ctx, ps, r = DOT_R) {
    ctx.setTransform(ps.a, ps.b, ps.c, ps.d, ps.cx, ps.cy);
    ctx.beginPath();
    ctx.arc(0, 0, r, 0, TAU);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  // ---------------------------------------------------------------------------------------------
  // Scene
  // ---------------------------------------------------------------------------------------------
  R.scene({
    id: 's02-timing',
    start: 1.875,
    end: 3.75,
    z: 20,
    bg: PAL.ink,

    async setup(root) {
      // ---- FX + sound (global, time-based) -------------------------------------------------
      R.cue(2.34375, 'shake', { amt: 4, dur: 0.12 }); // dot lands on "Timing"
      R.cue(2.8125, 'shake', { amt: 5, dur: 0.14 }); // dot lands on "everything"
      R.cue(3.515625, 'vignette', { amt: 0.45, dur: 0.234375, in: 0.2, out: 0.02 }); // tunnel vision in the dive

      R.sfx(1.875, 'blip', { pitch: 0.5 }); // anticipation stretch
      R.sfx(1.9921875, 'whoosh', { dur: 0.3515625, dir: 'up' }); // leap (lands 2.34375)
      R.sfx(2.34375, 'pop', { pitch: 1.0 }); // land 1, F4
      R.sfx(2.578125, 'pop', { pitch: 1.189 }); // land 2, Ab4
      R.sfx(2.8125, 'pop', { pitch: 1.498 }); // land 3, C5
      R.sfx(2.9296875, 'pop', { pitch: 2.0 }); // full stop, F5
      R.sfx(3.046875, 'tick', { pitch: 2.0 }); // micro-hop
      R.sfx(3.28125, 'click', { pitch: 1.2 }); // notices the camera
      R.sfx(3.515625, 'reverse', { dur: 0.234375 }); // dive, lands 3.75

      // ---- Measure the sentence (DOM pen positions keep kerning; canvas scan gives true ink) ----
      await document.fonts.load(SERIF, SENT);
      await document.fonts.load(MONO, 'ANTICIPATION');
      const probe = R.el('div', { text: SENT, style: { font: SERIF, lineHeight: '200px', whiteSpace: 'pre', visibility: 'hidden', left: '0px', top: '0px' } }, document.body);
      const node = probe.firstChild, rg = document.createRange();
      const pr = probe.getBoundingClientRect();
      const pen = [];
      for (let i = 0; i < SENT.length; i++) {
        rg.setStart(node, i); rg.setEnd(node, i + 1);
        pen.push(rg.getBoundingClientRect().left - pr.left);
      }
      const bl = R.el('span', { style: { position: 'static', display: 'inline-block', width: '0px', height: '0px', verticalAlign: 'baseline' } }, probe);
      const baseline = bl.getBoundingClientRect().top - pr.top; // 168 (0.84 em)
      probe.remove();

      const cv = document.createElement('canvas');
      cv.width = 420; cv.height = 380;
      const cx = cv.getContext('2d', { willReadFrequently: true });
      cx.font = SERIF;
      cx.fillStyle = '#fff';
      const letters = [];
      for (let i = 0; i < SENT.length; i++) {
        const ch = SENT[i];
        if (ch === ' ') continue;
        const fx = Math.floor(pen[i]);
        cx.clearRect(0, 0, cv.width, cv.height);
        cx.fillText(ch, 110 + (pen[i] - fx), 260);
        const img = cx.getImageData(0, 0, cv.width, cv.height).data;
        let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
        for (let y = 0; y < cv.height; y++) for (let x = 0; x < cv.width; x++) {
          if (img[(y * cv.width + x) * 4 + 3] >= 8) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
        }
        letters.push({ i, ch, pen: pen[i], ink: [x0 - 110 + fx, x1 + 1 - 110 + fx, y0 - 260, y1 + 1 - 260] });
      }
      // words by string index
      const wordRanges = [[0, 6], [7, 9], [10, 20]];
      const words = wordRanges.map(([a, b]) => {
        const ls = letters.filter((l) => l.i >= a && l.i < b);
        return { letters: ls, x0: Math.min(...ls.map((l) => l.ink[0])), x1: Math.max(...ls.map((l) => l.ink[1])) };
      });
      const originX = Math.round(200 - words[0].x0); // sentence ink starts at x = 200
      for (const l of letters) { l.x = originX + l.pen; l.ink = [l.ink[0] + originX, l.ink[1] + originX, l.ink[2] + GROUND, l.ink[3] + GROUND]; l.cx = (l.ink[0] + l.ink[1]) / 2; }
      for (const w of words) { w.x0 += originX; w.x1 += originX; w.cx = (w.x0 + w.x1) / 2; }
      this.meas = { originX, baseline, words: words.map((w) => [w.x0, w.x1]) };

      // Landing targets: ink centres of the words; the full stop hangs 60 px right of the ink (+16 px gap)
      const xT = Math.round(words[0].cx), xI = Math.round(words[1].cx), xE = Math.round(words[2].cx);
      const xS = Math.round(words[2].x1 + 60);
      this.xS = xS;
      this.words = words;

      // ---- Hops (flight windows start after each 2-frame ground contact) --------------------
      this.hops = [
        makeHop(T_LEAP, T_L[0], START[0], START[1], xT, REST_Y, 445.1), // LEAP: 3 16ths
        makeHop(T_L[0] + CONTACT, T_L[1], xT, REST_Y, xI, REST_Y, 266), // → "is": 8th
        makeHop(T_L[1] + CONTACT, T_L[2], xI, REST_Y, xE, REST_Y, 216), // → "everything": 8th
        makeHop(T_L[2] + CONTACT, T_L[3], xE, REST_Y, xS, REST_Y, 96), //  → full stop: 16th
        makeHop(T_L[3] + CONTACT, T_L[4], xS, REST_Y, xS, REST_Y, 36), //  micro-hop in place
      ];
      // Contacts: squash amounts per landing, momentum lean from the incoming horizontal velocity
      const SQ = [[1.5, 0.667], [1.4, 0.71], [1.35, 0.74], [1.3, 0.77]];
      this.contacts = SQ.map((sq, k) => {
        const vin = this.hops[k].vel(1)[0];
        return { t0: T_L[k], x: this.hops[k].x1, sx: sq[0], sy: sq[1], lean: -clamp(vin / 6000, -1, 1) * R.deg(8) };
      });
      // total trail length (for the trim-path retract)
      let acc = 0;
      this.trail = this.hops.slice(0, 4).map((h) => { const o = { hop: h, s0: acc }; acc += h.len; return o; });
      this.trailLen = acc;

      // ---- DOM ------------------------------------------------------------------------------
      const note = R.canvas(root);
      this.nctx = note.ctx; this.note = note.canvas;
      const volt = R.col(PAL.volt);
      this.pathGrad = note.ctx.createLinearGradient(0, 610, 0, 760);
      this.pathGrad.addColorStop(0, rgba(volt, 1));
      this.pathGrad.addColorStop(1, rgba(volt, 0.3));

      const world = R.el('div', { style: { top: WORLD_TOP + 'px', width: R.W + 'px', height: WORLD_H + 'px', transformOrigin: '0 0' } }, root);
      this.world = world;
      this.ground = R.el('div', { style: { top: GROUND - WORLD_TOP + 'px', height: '1.5px', width: '0px', background: rgba(FOG_RGB, 0.4) } }, world);
      this.letterEls = letters.map((l) => {
        const el = R.el('span', {
          text: l.ch,
          style: {
            left: l.x.toFixed(3) + 'px', top: GROUND - baseline - WORLD_TOP + 'px',
            font: SERIF, lineHeight: '200px', whiteSpace: 'pre', color: PAL.paper,
            transformOrigin: `50% ${baseline}px`, visibility: 'hidden',
          },
        }, world);
        return el;
      });
      // eruption schedule: each word erupts when the dot lands on it, rippling outward 1 frame per letter
      const eruptT = [T_L[0], T_L[1], T_L[2]], eruptX = [xT, xI, xE];
      this.letterSched = letters.map((l) => {
        const wi = words.findIndex((w) => w.letters.includes(l));
        const w = words[wi];
        const pitch = (w.x1 - w.x0) / w.letters.length;
        return { wi, t0: eruptT[wi] + (Math.abs(l.cx - eruptX[wi]) / pitch) * FR };
      });
      this.wordT = eruptT;

      const dot = R.canvas(root);
      this.dctx = dot.ctx; this.dot = dot.canvas;

      this.override = R.el('div', { style: { width: R.W + 'px', height: R.H + 'px', background: PAL.signal, display: 'none' } }, root);

      // ---- Notation labels -------------------------------------------------------------------
      // Positions follow the storyboard's intent (each label at its event) but are nudged so no
      // label is ever crossed by a dashed arc or by the dot itself (checked frame by frame).
      const self = this;
      const hop0 = this.hops[0], hop1 = this.hops[1];
      const apex0 = hop0.at(0.5 - (hop0.y1 - hop0.y0) / (8 * hop0.h)); // true apex: τ = ½ − (y1−y0)/8h
      const apex1 = hop1.at(0.5);
      const fadeAll = { tOut: T_L[3], fade: T_L[4] - T_L[3] };
      const ax = Math.round(apex0[0]), sx1 = Math.round(apex1[0] * 2) / 2;
      this.labels = [
        // stem tracks the top of the crouching dot, retracts when it leaves
        Object.assign({ text: 'ANTICIPATION', x: 1703, y: 560, align: 'left', tIn: T_IN - FR, rate: 2,
          stem: (t) => { const ps = self.pose(Math.min(t, T_LEAP - 1e-4)); return [ps.cx - DOT_R * ps.c, 567, ps.cy - DOT_R * ps.d - 5]; },
          stemOff: T_LEAP }, fadeAll),
        Object.assign({ text: 'ARCS', x: ax, y: 196, align: 'center', tIn: T_LEAP + 0.56 * hop0.T, rate: 1,
          stem: () => [ax, 203, apex0[1] - 7] }, fadeAll),
        Object.assign({ text: 'SQUASH & STRETCH', x: xT, y: 500, align: 'center', tIn: T_L[0], rate: 2,
          stem: () => [xT, 507, 662] }, fadeAll),
        Object.assign({ text: 'SLOW IN / SLOW OUT', x: sx1, y: 392, align: 'center', tIn: T_L[1], rate: 2,
          stem: () => [sx1, 399, apex1[1] - 14] }, fadeAll),
        { text: 'FOLLOW-THROUGH', x: xS, y: 640, align: 'center', tIn: T_L[3] + FR, rate: 2, tOut: 3.1640625, fade: 0.1171875 },
      ];
      for (const L of this.labels) {
        const w = L.text.length * MONO_ADV + (L.text.length - 1) * MONO_TRACK;
        L.x0 = Math.round(L.align === 'right' ? L.x - w : L.align === 'center' ? L.x - w / 2 : L.x); // static text on whole pixels
      }
      // spacing chart on the Timing → is hop: the dot's positions every 2 frames (τ = k/6)
      this.ticks = [];
      for (let k = 1; k <= 5; k++) {
        const tau = k / 6, p = hop1.at(tau), v = hop1.vel(tau), n = Math.hypot(v[0], v[1]);
        this.ticks.push({ t: hop1.t0 + tau * hop1.T, p, nx: -v[1] / n, ny: v[0] / n, len: k === 3 ? 20 : 13 });
      }
    },

    /** The dot's pose at global time t (also sampled at earlier times for onion skins). */
    pose(t) {
      const hops = this.hops, C = this.contacts;
      if (t < T_LEAP) { // anticipation crouch, bottom anchored on WIDE's (invisible) baseline
        const p = E.outCubic(clamp((t - T_IN) / 0.105));
        return poseSquash(START[0], START_FLOOR, lerp(1, 1.3, p), lerp(1, 0.77, p), R.deg(8) * p);
      }
      for (let k = 0; k < 4; k++) {
        const h = hops[k];
        if (t < h.t1) return this.flightPose(h, (t - h.t0) / h.T);
        const c = C[k];
        if (t < c.t0 + CONTACT) {
          const q = (t - c.t0) / CONTACT, e = 1 - q * q;
          return poseSquash(c.x, GROUND, 1 + (c.sx - 1) * e, 1 - (1 - c.sy) * e, c.lean * e);
        }
      }
      const mh = hops[4];
      if (t < mh.t1) return this.flightPose(mh, (t - mh.t0) / mh.T);
      const xS = this.xS;
      if (t < T_DIVE) {
        // settle wobble (WOBBLE), tapered to exact rest before the notice beat
        const w = (1 - R.spring(t - T_L[4], WOBBLE)) * (1 - R.smoothstep(T_L[4] + 0.12, T_NOTICE - FR, t));
        const k = lerp(1, 0.85, E.inOutSine(seg(t, T_NOTICE, T_NOTICE + R.E16)));
        const ps = poseSquash(xS, GROUND, 1 + 0.06 * w, 1 - 0.05 * w, 0);
        if (k === 1) return ps;
        return poseRound(xS, REST_Y, k); // notice: uniform scale about the centre
      }
      return null; // dive: drawn as a plain disc
    },

    flightPose(h, tau) {
      tau = clamp(tau);
      const p = h.at(tau), v = h.vel(tau), sp = Math.hypot(v[0], v[1]);
      const s = 1 + 0.25 * clamp(sp / 4200);
      return poseStretch(p[0], p[1], s, Math.atan2(v[1], v[0]));
    },

    update(lt, prog, t) {
      const rest = t >= T_REST - 1e-6;
      this.override.style.display = rest ? 'block' : 'none';
      this.note.style.display = rest ? 'none' : 'block';
      this.world.style.display = rest ? 'none' : 'block';
      this.dot.style.display = rest ? 'none' : 'block';
      if (rest) return;
      this.drawNotation(t);
      this.updateWorld(t);
      this.drawDot(t);
    },

    // -------------------------------------------------------------------------------------------
    updateWorld(t) {
      // ground line: draws outward from x = 1731 to both edges (swift)
      const g = E.swift(seg(t, T_IN, 2.109375));
      const gl = START[0] * (1 - g);
      this.ground.style.left = gl.toFixed(2) + 'px';
      this.ground.style.width = (R.W * g).toFixed(2) + 'px';

      // letters: stamped into existence (scaleY from the baseline) × the word taking the hit
      for (let i = 0; i < this.letterEls.length; i++) {
        const el = this.letterEls[i], sc = this.letterSched[i];
        const tw = this.wordT[sc.wi];
        let sy = 0;
        if (t >= sc.t0) {
          sy = R.spring(t - sc.t0, ERUPT);
          if (t - sc.t0 > 0.5) sy = 1;
        }
        if (t >= tw && t - tw < 0.5) sy *= 1 - 0.06 * (1 - R.spring(t - tw, TIGHT));
        if (sy <= 0.002) { el.style.visibility = 'hidden'; el.style.transform = 'none'; continue; }
        el.style.visibility = 'visible';
        el.style.transform = Math.abs(sy - 1) < 1e-4 ? 'none' : `scaleY(${sy.toFixed(4)})`;
      }

      // the dive: the sentence layer is pushed past the camera about the dot (inExpo) and defocuses
      if (t >= T_DIVE) {
        const q = E.inExpo(seg(t, T_DIVE, T_REST));
        const c = this.diveCentre(t);
        const s = 1 + 1.2 * q;
        const ox = c[0] * (1 - s), oy = (c[1] - WORLD_TOP) * (1 - s);
        this.world.style.transform = `matrix(${s.toFixed(5)},0,0,${s.toFixed(5)},${ox.toFixed(3)},${oy.toFixed(3)})`;
        this.world.style.filter = q > 0.002 ? `blur(${(6 * q).toFixed(3)}px)` : 'none';
      } else {
        this.world.style.transform = 'none';
        this.world.style.filter = 'none';
      }
    },

    diveCentre(t) {
      const u = t - T_DIVE, e = E.inOutCubic(Math.min(1, Math.max(0, u / 0.1875)));
      return [lerp(this.xS, 960, e), lerp(REST_Y, 540, e)];
    },

    // -------------------------------------------------------------------------------------------
    drawNotation(t) {
      const ctx = this.nctx;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, R.W, R.H);
      if (t >= T_NOTICE + 0.2) return;

      const outA = 1 - seg(t, T_L[3], T_L[4]); // notation fades as the full stop lands

      // ---- dashed motion paths (drawn PATH_LEAD ahead of the dot; trimmed away into the dot) ----
      const ret = this.trailLen * E.inQuad(seg(t, T_L[3], 3.1));
      ctx.save();
      ctx.strokeStyle = this.pathGrad; // dashes thin out where they pass behind the type
      ctx.lineWidth = 2;
      ctx.lineCap = 'butt';
      ctx.setLineDash([8, 10]);
      for (const tr of this.trail) {
        const h = tr.hop;
        const head = h.sAt((t + PATH_LEAD - h.t0) / h.T);
        const tail = clamp(ret - tr.s0, 0, h.len);
        if (head - tail < 0.5 || t + PATH_LEAD < h.t0) continue;
        ctx.beginPath();
        ctx.lineDashOffset = tail; // keep the dash phase anchored to the path
        if (traceHop(ctx, h, tail, head)) ctx.stroke();
      }
      ctx.restore();

      // ---- spacing chart (ticks dropped as the dot passes) ----
      if (outA > 0) {
        ctx.save();
        ctx.strokeStyle = VOLT_LIGHT;
        ctx.lineWidth = 1.5;
        for (const tk of this.ticks) {
          const a = seg(t, tk.t, tk.t + 2 * FR, 'outCubic');
          if (a <= 0) continue;
          const L = tk.len * a / 2;
          ctx.globalAlpha = outA;
          ctx.beginPath();
          ctx.moveTo(tk.p[0] - tk.nx * L, tk.p[1] - tk.ny * L);
          ctx.lineTo(tk.p[0] + tk.nx * L, tk.p[1] + tk.ny * L);
          ctx.stroke();
        }
        ctx.restore();
      }

      // ---- onion skins: the same pose sampled every 2 frames back (only once the dot has left) ----
      if (t >= T_LEAP && t < 3.1) {
        const skinA = 1 - seg(t, 3.0, 3.1);
        ctx.lineWidth = 1.5;
        // the crouch leaves ONE ghost (its key pose), not a stack of near-identical outlines
        const live = this.pose(t) || { cx: -1e4, cy: -1e4 };
        let kCrouch = 7;
        for (let k = 1; k <= 6; k++) if (t - 2 * k * FR < T_LEAP) { kCrouch = k; break; }
        for (let k = 6; k >= 1; k--) {
          let ts = t - (2 * k) * FR;
          if (ts < T_LEAP) { if (k !== kCrouch) continue; ts = T_LEAP - 1e-4; }
          const ps = this.pose(ts);
          if (!ps) continue;
          const near = R.smoothstep(30, 84, Math.hypot(ps.cx - live.cx, ps.cy - live.cy));
          const a = lerp(0.45, 0.08, (k - 1) / 5) * skinA * near;
          if (a <= 0.003) continue;
          ctx.strokeStyle = rgba(FOG_RGB, a.toFixed(3));
          tracePose(ctx, ps);
          ctx.stroke();
        }
      }

      // ---- labels + leaders ----
      ctx.font = MONO;
      ctx.letterSpacing = MONO_TRACK + 'px';
      ctx.textBaseline = 'alphabetic';
      ctx.textAlign = 'left';
      for (const L of this.labels) {
        if (t < L.tIn) continue;
        const a = 1 - seg(t, L.tOut, L.tOut + L.fade);
        if (a <= 0) continue;
        const n = Math.min(L.text.length, Math.floor((t - L.tIn) / FR * L.rate + 1e-6) + 1);
        ctx.globalAlpha = a;
        ctx.fillStyle = VOLT_LIGHT;
        ctx.fillText(L.text.slice(0, n), L.x0, L.y);
        if (L.stem) {
          // 1 px leader: grows from the subject up to the label; optionally retracts upward
          const [sx, yTop, yBot] = L.stem(t);
          const grow = seg(t, L.tIn, L.tIn + 4 * FR, 'swift');
          const off = L.stemOff != null ? seg(t, L.stemOff, L.stemOff + 3 * FR, 'outCubic') : 0;
          const yA = lerp(yBot, yTop, grow), yB = lerp(yBot, yTop, off);
          if (yB - yA > 0.5) {
            const px = Math.round(sx) + 0.5; // crisp 1 px line
            ctx.strokeStyle = PAL.volt;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(px, yA);
            ctx.lineTo(px, yB);
            ctx.stroke();
          }
        }
        ctx.globalAlpha = 1;
      }
      ctx.letterSpacing = '0px';
    },

    // -------------------------------------------------------------------------------------------
    drawDot(t) {
      const ctx = this.dctx;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, R.W, R.H);

      // impact ring on "Timing"
      const ir = seg(t, T_L[0], T_L[0] + 0.2);
      if (ir > 0 && ir < 1) {
        ctx.strokeStyle = rgba(PAPER_RGB, (1 - ir) * (1 - ir) * 0.9);
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(this.contacts[0].x, REST_Y, 44 + 96 * E.swift(ir), 0, TAU);
        ctx.stroke();
      }
      // the camera-notice pulse
      const pr = seg(t, T_NOTICE, T_NOTICE + 0.2);
      if (pr > 0 && pr < 1) {
        ctx.strokeStyle = rgba(PAPER_RGB, (1 - pr) * (1 - pr) * 0.9);
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(this.xS, REST_Y, 44 + 26 * E.swift(pr), 0, TAU);
        ctx.stroke();
      }

      ctx.fillStyle = PAL.signal;
      if (t < T_DIVE) {
        const ps = this.pose(t);
        tracePose(ctx, ps);
        ctx.fill();
        return;
      }
      // THE DIVE: exponential approach R = 37.4·e^(18u), centre eased to frame centre. While the
      // centre travels fast the disc keeps the reel's smear language (volume-preserving stretch
      // along its velocity, ≈ a 180° shutter); it is a perfect circle again before it fills the frame.
      const u = t - T_DIVE;
      const Rr = 37.4 * Math.exp(18 * u);
      const c = this.diveCentre(t), c2 = this.diveCentre(t + 1e-3);
      const vx = (c2[0] - c[0]) / 1e-3, vy = (c2[1] - c[1]) / 1e-3;
      const s = 1 + Math.min(0.3, Math.hypot(vx, vy) / 120 / (2 * Rr));
      tracePose(ctx, s > 1.001 ? poseStretch(c[0], c[1], s, Math.atan2(vy, vx)) : poseRound(c[0], c[1]), Rr);
      ctx.fill();
    },
  });
})();
