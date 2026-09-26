// s04-easing — "Easing — the graph editor" (5.15625s → 7.03125s, z 40)
//
// A live cubic-bezier editor. The dot hops from the corridor's vanishing point onto a preview track, a cursor
// drags the P2 handle out of the plot box (y2 1.00 → 1.50), and on the snare the dot is literally eased by that
// curve: spacing-chart ghosts, overshoot past the end, "EASE" stretching its width axis in lock-step. Then
// everything un-draws into the origin and the dot snaps back to centre for the lights-out match cut.
//
// Layers (bottom → top): base canvas (hairlines, plot, header, track, ghosts, readout) · EASE (DOM, variable
// font-stretch %, plus single-glyph copies at the kerned positions for the staggered mask rise / wipe) · top canvas (the dot, the cursor).
(() => {
  'use strict';

  const T0 = 5.15625, T1 = 7.03125, F = 1 / 60;
  const FR0 = Math.ceil(T0 * 60 - 1e-9) / 60; // first rendered frame (f310) — must equal the s03 rest pose
  const E = R.ease, seg = R.seg, clamp = R.clamp, lerp = R.lerp;
  const INK = R.pal.ink, PAPER = R.pal.paper, SIGNAL = R.pal.signal, VOLT = R.pal.volt, FOG = R.pal.fog;
  const TIGHT = { stiffness: 420, damping: 26 }, POP = { stiffness: 380, damping: 18 };
  const MONO = R.font.mono;

  // ---- Key times (global seconds) -------------------------------------------------------------------------
  const T = {
    hopLaunch: T0 + 3 * F, // 3 frames of crouch (anticipation), then launch
    hopLand: T0 + 10 * F, // 7-frame ballistic hop
    squashEnd: T0 + 12 * F, // 2-frame landing squash (1.25 × 0.8)
    type: 5.2, // header types on, 2 chars / frame
    easeIn: 5.2734375, easeInEnd: 5.44921875,
    curIn: 5.2734375, curArrive: 5.5078125,
    press: 5.625, release: 5.859375,
    curAway: 5.859375 + 2 * F, curParked: 6.09375, curGone: 6.2109375,
    play: 6.09375, playEnd: 6.5625,
    retract: 6.796875, home: 6.9979,
  };
  const PLAY_DUR = T.playEnd - T.play;

  // ---- Geometry ---------------------------------------------------------------------------------------------
  const PX = (u) => 240 + 480 * u, PY = (v) => 820 - 480 * v;
  const P0 = [240, 820], P1 = [576, 820], P3 = [720, 340];
  const P2X = 336, P2Y0 = 340, P2Y1 = 100;
  const TRACK_X0 = 1040, TRACK_X1 = 1680, TRACK_Y = 400;
  const DOT_R = 28;
  const TRACK_LABEL_BASE = 452; // storyboard says 432, but the resting Ø56 dot (bottom 428) would sit on the "0"
  const EASE_X = 1040, EASE_BASE = 700, EASE_SIZE = 200, EASE_DROP = 152;
  const HEADER = 'cubic-bezier(0.70, 0.00, 0.20, 1.00)';
  const HEAD_X = 240, HEAD_BASE = 900;
  const ODO_I = HEADER.lastIndexOf('1.00') + 2; // tenths digit of y2
  const Y2_I = HEADER.lastIndexOf('1.00');

  const valueFn = R.cubicBezier(0.7, 0, 0.2, 1.5); // the eased value — same solver as the engine
  const vAt = (t) => valueFn(clamp((t - T.play) / PLAY_DUR));

  // Handle drag: y2 1.00 → 1.50 (inOutCubic), P2 follows.
  const dragK = (t) => seg(t, T.press, T.release, 'inOutCubic');
  const p2y = (t) => lerp(P2Y0, P2Y1, dragK(t));

  // ---- Small helpers ----------------------------------------------------------------------------------------
  const qb = (a, c, b, s) => {
    const u = 1 - s;
    return [u * u * a[0] + 2 * u * s * c[0] + s * s * b[0], u * u * a[1] + 2 * u * s * c[1] + s * s * b[1]];
  };
  const mixPt = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
  const frameOf = (t) => Math.round(t * 60);
  // Tick pop envelope: 1 → peak → 1 over 4 frames.
  const popEnv = (t, t0, peak) => {
    const d = t - t0;
    if (d < 0 || d >= 4 * F) return 1;
    return d < 1.5 * F ? lerp(1, peak, E.outQuad(d / (1.5 * F))) : lerp(peak, 1, E.inOutQuad((d - 1.5 * F) / (2.5 * F)));
  };

  // ---- The dot's path (pure) --------------------------------------------------------------------------------
  const HOP_A = [960, 540], HOP_C = [1022, 262], HOP_B = [TRACK_X0, TRACK_Y];
  const RET_A = [TRACK_X1, TRACK_Y], RET_C = [1300, 262], RET_B = [960, 540];
  function dotPos(t) {
    if (t < T.hopLaunch) return HOP_A;
    if (t < T.hopLand) return qb(HOP_A, HOP_C, HOP_B, (t - T.hopLaunch) / (T.hopLand - T.hopLaunch)); // ballistic
    if (t < T.play) return HOP_B;
    if (t < T.retract) return [TRACK_X0 + 640 * vAt(t), TRACK_Y];
    if (t < T.home) return qb(RET_A, RET_C, RET_B, E.snap(seg(t, T.retract, T.home)));
    return RET_B;
  }
  // Shutter (in seconds) of the fake motion blur per phase.
  function shutter(t) {
    if (t >= T.hopLaunch && t < T.hopLand) return 0.55 * F;
    if (t >= T.play && t < T.retract) return 0.4 * F;
    if (t >= T.retract) return 0.7 * F;
    return 0;
  }
  // Squash / stretch that is not velocity-driven: crouch, landing squash, spring back.
  function dotSquash(t) {
    if (t > FR0 && t < T.hopLaunch) {
      const a = E.outQuad(seg(t, FR0, T.hopLaunch));
      const sy = 1 - 0.16 * a;
      return { sx: 1 / sy, sy, dy: DOT_R * (1 - sy) }; // anchored at the bottom: a crouch
    }
    if (t >= T.hopLand && t < T.squashEnd) return { sx: 1.25, sy: 0.8, dy: 0 };
    if (t >= T.squashEnd && t < T.squashEnd + 0.6) {
      const k = R.spring(t - T.squashEnd, TIGHT);
      const sx = 1.25 - 0.25 * k;
      return { sx, sy: 1 / sx, dy: 0 };
    }
    return { sx: 1, sy: 1, dy: 0 };
  }

  // ---- Cursor (pure) ----------------------------------------------------------------------------------------
  const CUR_A = [1500, 1140], CUR_C = [1180, 420], CUR_B = [P2X, P2Y0];
  const PARK_C = [690, 430], PARK = [760, 1000];
  function cursorState(t) {
    if (t < T.curIn || t >= T.curGone) return null;
    let p, s = 1, a = 1;
    if (t < T.curArrive) p = qb(CUR_A, CUR_C, CUR_B, E.glide(seg(t, T.curIn, T.curArrive)));
    else if (t < T.press) p = CUR_B;
    else if (t < T.release) p = [P2X, p2y(t)];
    else if (t < T.curAway) p = [P2X, P2Y1];
    else p = qb([P2X, P2Y1], PARK_C, PARK, E.glide(seg(t, T.curAway, T.curParked)));
    if (t >= T.press && t < T.press + 3 * F) s = 0.9;
    if (t >= T.release && t < T.release + 2 * F) s = 1.05;
    if (t >= T.curParked) a = 1 - E.inOutQuad(seg(t, T.curParked, T.curGone));
    return { x: p[0], y: p[1], s, a };
  }
  // Classic arrow, 34 px tall, hotspot at the tip (0,0).
  const ARROW = [[0, 0], [0, 30.2], [7.4, 23.4], [12.4, 34], [17.2, 31.8], [12.4, 21.6], [21.4, 21.6]];

  // ---- Bezier curve helpers (pixel space) -------------------------------------------------------------------
  function cubicPt(p0, p1, p2, p3, s) {
    const u = 1 - s;
    const a = u * u * u, b = 3 * u * u * s, c = 3 * u * s * s, d = s * s * s;
    return [a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]];
  }
  // Parameter s at arc-length fraction f (32-sample table).
  function sAtLen(p0, p1, p2, p3, f) {
    if (f >= 1) return 1;
    if (f <= 0) return 0;
    const N = 32, acc = [0];
    let prev = p0, L = 0;
    for (let i = 1; i <= N; i++) {
      const q = cubicPt(p0, p1, p2, p3, i / N);
      L += Math.hypot(q[0] - prev[0], q[1] - prev[1]);
      acc.push(L);
      prev = q;
    }
    const target = f * L;
    for (let i = 1; i <= N; i++) {
      if (acc[i] >= target) {
        const k = (target - acc[i - 1]) / Math.max(1e-9, acc[i] - acc[i - 1]);
        return (i - 1 + k) / N;
      }
    }
    return 1;
  }
  // First part [0, s] of a cubic (de Casteljau), returned as 4 points.
  function splitLeft(p0, p1, p2, p3, s) {
    const a = mixPt(p0, p1, s), b = mixPt(p1, p2, s), c = mixPt(p2, p3, s);
    const d = mixPt(a, b, s), e = mixPt(b, c, s);
    const f = mixPt(d, e, s);
    return [p0, a, d, f];
  }

  // ---- Swiss hairlines --------------------------------------------------------------------------------------
  const COLS = [];
  {
    const cw = (1920 - 2 * 96 - 11 * 16) / 12;
    for (let i = 0; i < 12; i++) {
      const l = 96 + i * (cw + 16);
      COLS.push(Math.round(l) + 0.5, Math.round(l + cw) - 0.5);
    }
  }
  const COL_RANK = COLS.map((x) => Math.floor(Math.abs(x - 960) / 80)); // centre-out stagger

  R.scene({
    id: 's04-easing',
    start: T0,
    end: T1,
    z: 40,
    bg: PAPER,

    setup(root) {
      // Global FX (storyboard cue list) ------------------------------------------------------------------
      R.cue(5.15625, 'flash', { amt: 0.35, dur: 0.1, color: '#FFFFFF' }); // arrival into the Paper UI
      R.cue(5.625, 'shake', { amt: 2, dur: 0.08 }); // cursor press

      // Canvases + EASE --------------------------------------------------------------------------------------
      this.base = R.canvas(root).ctx;
      this.easeMask = R.el('div', { style: { width: '1920px', height: EASE_BASE + 6 + 'px', overflow: 'hidden' } }, root);
      this.top = R.canvas(root).ctx;

      const easeFont = `800 ${EASE_SIZE}px ${R.font.display}`;
      const easeStyle = { font: easeFont, lineHeight: '1', whiteSpace: 'pre', color: INK, letterSpacing: '-0.01em', fontKerning: 'normal' };

      // Measurements (setup only). The scene root is display:none here, so measure in a hidden body probe.
      const probe = R.el('div', { style: Object.assign({ left: '-4000px', top: '0px', visibility: 'hidden' }, easeStyle) }, document.body);
      const tn = document.createTextNode('EASE');
      probe.appendChild(tn);
      const bl = document.createElement('span');
      Object.assign(bl.style, { display: 'inline-block', width: '0px', height: '0px' });
      probe.appendChild(bl);
      const rng = document.createRange();
      const letterBoxes = (stretch) => {
        probe.style.fontStretch = stretch + '%';
        const pr = probe.getBoundingClientRect();
        const xs = [];
        for (let i = 0; i < 4; i++) {
          rng.setStart(tn, i);
          rng.setEnd(tn, i + 1);
          const r = rng.getBoundingClientRect();
          xs.push([r.left - pr.left, r.right - pr.left]);
        }
        const wordW = (() => { rng.setStart(tn, 0); rng.setEnd(tn, 4); return rng.getBoundingClientRect().width; })();
        return { xs, boxW: pr.width, wordW, baseline: bl.getBoundingClientRect().top - pr.top };
      };
      this.lb62 = letterBoxes(62);
      this.lb125 = letterBoxes(125);
      probe.remove();
      this.easeTop = EASE_BASE - this.lb62.baseline;

      // Ink side bearing of "E" per width, scanned from pixels at 4× size (canvas takes keyword stretches only;
      // intermediate widths are interpolated). measureText's ink bounds are too coarse for pixel-exact alignment.
      const SC = 4, mcv = document.createElement('canvas');
      mcv.width = 1400; mcv.height = 1000;
      const mc = mcv.getContext('2d', { willReadFrequently: true });
      const kw = [[62.5, 'extra-condensed'], [75, 'condensed'], [87.5, 'semi-condensed'], [100, 'normal'], [112.5, 'semi-expanded'], [125, 'expanded']];
      this.lsb = kw.map(([pct, k]) => {
        mc.clearRect(0, 0, 1400, 1000);
        mc.font = `800 ${EASE_SIZE * SC}px ${R.font.display}`;
        mc.fontStretch = k;
        mc.fillStyle = '#000';
        mc.fillText('E', 100, 900);
        const row = mc.getImageData(0, 900 - 250, 1400, 1).data; // through the stem, below the middle arm
        let edge = null;
        for (let x = 0; x < 1400; x++) {
          const al = row[x * 4 + 3];
          if (al > 0) { edge = x + (1 - al / 255); break; }
        }
        mc.letterSpacing = -0.01 * EASE_SIZE * SC + 'px';
        const mW = mc.measureText('EASE');
        mc.letterSpacing = '0px';
        return { pct, lsb: (edge - 100) / SC, ink: (mW.actualBoundingBoxRight + mW.actualBoundingBoxLeft) / SC };
      });
      this.lsbAt = (pct) => {
        const L = this.lsb;
        if (pct <= L[0].pct) return L[0].lsb + (L[1].lsb - L[0].lsb) * (pct - L[0].pct) / (L[1].pct - L[0].pct);
        for (let i = 1; i < L.length; i++) if (pct <= L[i].pct) return lerp(L[i - 1].lsb, L[i].lsb, (pct - L[i - 1].pct) / (L[i].pct - L[i - 1].pct));
        return L[L.length - 1].lsb;
      };
      
      // EASE = one whole-word element (live width axis during PLAY) + four single-glyph elements placed at the
      // word's own shaped (kerned) advance positions for the staggered mask rise and wipe. Clipping copies of the
      // word per letter was rejected: the A's foot overhangs the S's advance box and got torn off mid-move.
      this.wordEl = R.el('div', { text: 'EASE', style: Object.assign({ display: 'none' }, easeStyle) }, this.easeMask);
      this.letterEls = 'EASE'.split('').map((ch) => R.el('div', { text: ch, style: Object.assign({ display: 'none' }, easeStyle) }, this.easeMask));
      this.easeState = { word: {}, letters: this.letterEls.map(() => ({})) };

      // Mono metrics.
      mc.font = `500 26px ${MONO}`;
      this.adv26 = mc.measureText('0').width;
      mc.font = `500 14px ${MONO}`;
      this.adv14 = mc.measureText('0').width;

      // Analytic spacing chart: ghost positions every 3 frames, and when the dot passes each 1/8 tick.
      this.ghosts = [];
      for (let k = 0; T.play + (3 * k) * F < T.playEnd - 1e-9; k++) {
        const tk = T.play + 3 * k * F;
        this.ghosts.push({ t: tk, x: TRACK_X0 + 640 * vAt(tk) });
      }
      this.tickPass = [];
      for (let k = 1; k <= 8; k++) {
        let lo = 0, hi = 0.8; // first crossing happens before the peak (x ≈ 0.73)
        for (let i = 0; i < 50; i++) { const m = (lo + hi) / 2; if (valueFn(m) < k / 8) lo = m; else hi = m; }
        this.tickPass.push(T.play + hi * PLAY_DUR);
      }
      // When the drawing track head reaches each tick (track draws with swift 5.2 → 5.42).
      this.trackHead = (t) => TRACK_X0 + 640 * E.swift(seg(t, 5.2, 5.42));
      this.tickAppear = [];
      for (let k = 0; k <= 8; k++) {
        let lo = 5.2, hi = 5.42;
        for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (this.trackHead(m) < TRACK_X0 + 80 * k - 0.5) lo = m; else hi = m; }
        this.tickAppear.push(hi);
      }

      // Sound (storyboard sfx list; tick times are the analytic crossings above).
      R.sfx(5.15625, 'blip', { pitch: 2.0 }); // arrival bloom
      R.sfx(5.2, 'type', { count: 18, dur: 0.3 }); // header typing (36 chars @ 2/frame)
      R.sfx(5.2734375, 'swish', { amt: 0.15 }); // faint air whoosh: the cursor enters
      R.sfx(5.625, 'click', { pitch: 1.0 }); // press
      R.sfx(5.625, 'tick', { pitch: 3.0 }); // tink
      R.sfx(5.625, 'swish', { amt: 0.25 }); // drag glide
      R.sfx(5.859375, 'pop', { pitch: 1.5 }); // release
      R.sfx(6.09375, 'whoosh', { dur: 0.46875, dir: 'up' }); // play swoop
      const pitches = [1.0, 1.06, 1.12, 1.19, 1.26, 1.33, 1.41, 1.5];
      this.tickPass.forEach((tp, i) => R.sfx(Math.round(tp * 1e4) / 1e4, 'tick', { pitch: pitches[i] }));
      R.sfx(6.5625, 'riser', { dur: 0.46875 }); // build into the tape-stop
      R.sfx(6.796875, 'reverse', { dur: 0.1875 }); // retract zip
    },

    update(lt, p, t) {
      this.drawBase(this.base, t);
      this.updateEase(t);
      this.drawTop(this.top, t);
    },

    // =======================================================================================================
    drawBase(ctx, t) {
      ctx.clearRect(0, 0, 1920, 1080);
      const fr = frameOf(t);
      const rt = seg(t, T.retract, T.retract + 0.17); // generic retract progress (linear)

      // ---- Swiss hairlines: draw out from y=540, centre-out; 20% on arrival, then 8%; fade out on retract.
      {
        let a = t < T.easeIn ? 0.2 : lerp(0.2, 0.08, E.outQuad(seg(t, T.easeIn, T.easeIn + 0.1)));
        a *= 1 - seg(t, T.retract, T.retract + 0.17, 'inQuad');
        if (a > 0.001) {
          ctx.strokeStyle = R.rgba(FOG, a);
          ctx.lineWidth = 1;
          ctx.beginPath();
          for (let i = 0; i < COLS.length; i++) {
            const d0 = FR0 + COL_RANK[i] * F;
            const h = 540 * E.swift(seg(t, d0, d0 + 0.3));
            if (h < 0.5) continue;
            ctx.moveTo(COLS[i], 540 - h);
            ctx.lineTo(COLS[i], 540 + h);
          }
          ctx.stroke();
        }
      }

      // ---- Plot grid (8×8, Fog 30%), drawn out of the axes with a 1-frame stagger.
      {
        const fade = 1 - seg(t, T.retract, T.retract + 0.1, 'inQuad');
        ctx.lineWidth = 1;
        for (let k = 1; k <= 8; k++) {
          const g = E.swift(seg(t, 5.22 + k * F, 5.22 + k * F + 0.28));
          if (g <= 0.001 || fade <= 0) continue;
          ctx.strokeStyle = R.rgba(FOG, 0.3 * Math.min(1, g * 1.6) * fade);
          const x = Math.round(PX(k / 8)) + 0.5, y = Math.round(PY(k / 8)) - 0.5;
          ctx.beginPath();
          ctx.moveTo(x, 820); ctx.lineTo(x, 820 - 480 * g);
          ctx.moveTo(240, y); ctx.lineTo(240 + 480 * g, y);
          ctx.stroke();
        }
      }

      // ---- Axes (Ink 2 px) from the origin outward; retract into the origin.
      {
        const a = E.swift(seg(t, T0 + F, T0 + F + 0.3)) * (1 - seg(t, T.retract + 0.02, T.retract + 0.17, 'inCubic'));
        if (a > 0.002) {
          ctx.strokeStyle = INK;
          ctx.lineWidth = 2;
          ctx.lineCap = 'square';
          ctx.beginPath();
          ctx.moveTo(240, 820); ctx.lineTo(240 + 480 * a, 820);
          ctx.moveTo(240, 820); ctx.lineTo(240, 820 - 480 * a);
          ctx.stroke();
          ctx.lineCap = 'butt';
        }
      }

      // ---- Axis labels (Fog mono 14, tracking 0.12em)
      {
        const a = seg(t, 5.3, 5.42, 'outQuad') * (1 - seg(t, T.retract, T.retract + 0.07));
        if (a > 0.002) {
          ctx.fillStyle = R.rgba(FOG, a);
          this.label(ctx, 'TIME', 480, 848, 'center');
          this.label(ctx, '0', 232, 848, 'right');
          this.label(ctx, '1', 720, 848, 'center');
          this.label(ctx, '1', 228, 345, 'right');
          ctx.save();
          ctx.translate(212, 580);
          ctx.rotate(-Math.PI / 2);
          this.label(ctx, 'VALUE', 0, 5, 'center');
          ctx.restore();
        }
      }

      // ---- Curve + handles
      const retr = E.inCubic(seg(t, T.retract, T.retract + 0.16)); // collapse into P0
      const p2 = [P2X, p2y(t)];
      const draw = t < T.retract ? E.swift(seg(t, 5.21, 5.45)) : 1 - retr;
      const sEnd = sAtLen(P0, P1, p2, P3, draw);
      const endPt = cubicPt(P0, P1, p2, P3, sEnd);
      const p1r = mixPt(P1, P0, retr), p2r = mixPt(p2, P0, retr);
      // Handle lines (Volt 2 px)
      const h1 = E.swift(seg(t, 5.3, 5.42)), h2 = E.swift(seg(t, 5.35, 5.45)); // out of their anchors
      ctx.strokeStyle = VOLT;
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      if (h1 > 0.002 && retr < 0.999) {
        const e1 = mixPt(P0, p1r, h1);
        ctx.beginPath(); ctx.moveTo(P0[0], P0[1]); ctx.lineTo(e1[0], e1[1]); ctx.stroke();
      }
      const p3Now = t < T.retract ? P3 : endPt;
      if (h2 > 0.002 && retr < 0.999) {
        const e2 = mixPt(p3Now, p2r, h2);
        ctx.beginPath(); ctx.moveTo(p3Now[0], p3Now[1]); ctx.lineTo(e2[0], e2[1]); ctx.stroke();
      }
      // Curve (Ink 5 px, round caps)
      if (sEnd > 0.001) {
        const c = splitLeft(P0, P1, p2, P3, sEnd);
        ctx.strokeStyle = INK;
        ctx.lineWidth = 5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        ctx.moveTo(c[0][0], c[0][1]);
        ctx.bezierCurveTo(c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1]);
        ctx.stroke();
      }
      ctx.lineCap = 'butt';

      // ---- Playhead + riding dot + value guide (PLAY → retract)
      if (t >= T.play) {
        const x = clamp((t - T.play) / PLAY_DUR), v = valueFn(x);
        const grow = E.swift(seg(t, T.play, T.play + 4 * F)) * (1 - seg(t, T.retract, T.retract + 0.07, 'inQuad')); // gone before the axis passes it
        const X = Math.round(PX(x));
        if (grow > 0.002) {
          ctx.fillStyle = SIGNAL;
          ctx.fillRect(X - 1, 820 - 544 * grow, 2, 544 * grow);
        }
        const rideA = 1 - seg(t, T.retract + 0.1, T.retract + 0.16);
        const ride = t < T.retract ? [PX(x), PY(v)] : endPt;
        // Value guide: dashed Fog line from the riding dot to the VALUE axis + a Signal tick on the axis.
        const gA = (1 - seg(t, T.retract, T.retract + 0.06)) * E.outQuad(seg(t, T.play, T.play + 4 * F));
        if (gA > 0.002) {
          const gy = Math.round(PY(v)) + 0.5;
          ctx.strokeStyle = R.rgba(FOG, 0.7 * gA);
          ctx.lineWidth = 1;
          ctx.setLineDash([3, 4]);
          ctx.beginPath(); ctx.moveTo(ride[0] - 8, gy); ctx.lineTo(248, gy); ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = R.rgba(SIGNAL, gA);
          ctx.fillRect(235, gy - 1.5, 10, 2); // value tick straddling the VALUE axis
        }
        this.ride = rideA > 0.002 ? [ride[0], ride[1], rideA] : null;
      } else this.ride = null;

      // ---- Anchor discs (Ink Ø12) and handle squares (Signal 18×18)
      {
        const s0 = R.spring(t - 5.22, TIGHT) * (1 - E.inCubic(seg(t, T.retract + 0.13, T.retract + 0.19)));
        if (s0 > 0.01) this.disc(ctx, P0[0], P0[1], 6 * s0, INK);
        const s3 = R.spring(t - 5.34, TIGHT) * (1 - E.inCubic(seg(t, T.retract + 0.1, T.retract + 0.16)));
        if (s3 > 0.01) this.disc(ctx, p3Now[0], p3Now[1], 6 * s3, INK);
        if (this.ride) this.disc(ctx, this.ride[0], this.ride[1], 5, R.rgba(SIGNAL, this.ride[2])); // rides above P3
        const shrink = 1 - 0.75 * E.inCubic(seg(t, T.retract + 0.06, T.retract + 0.16));
        const gone = t >= T.retract + 0.16;
        // P1
        const s1 = R.spring(t - 5.38, TIGHT) * shrink;
        if (s1 > 0.01 && !gone) this.square(ctx, p1r[0], p1r[1], 18 * s1, SIGNAL);
        // P2: pop in · hover 1→1.2 · press 1.2→0.9 then POP back to 1
        let s2 = R.spring(t - 5.41, TIGHT);
        if (t < T.press) s2 *= 1 + 0.2 * E.swift(seg(t, T.curArrive, T.press));
        else if (t < T.press + 3 * F) s2 = lerp(1.2, 0.9, E.outQuad(seg(t, T.press, T.press + 3 * F)));
        else s2 = 0.9 + 0.1 * R.spring(t - (T.press + 3 * F), POP);
        s2 *= shrink;
        // Hover halo
        if (t >= T.curArrive && t < T.press) {
          const h = E.swift(seg(t, T.curArrive, T.press));
          ctx.fillStyle = R.rgba(SIGNAL, 0.14 * h);
          ctx.beginPath(); ctx.arc(p2r[0], p2r[1], 11 + 11 * h, 0, R.TAU); ctx.fill();
        }
        if (s2 > 0.01 && !gone) this.square(ctx, p2r[0], p2r[1], 18 * s2, SIGNAL);
        // Press ripple (Signal 1.5 px, r 9 → 48, fades over 0.2 s)
        if (t >= T.press && t < T.press + 0.2) {
          const k = (t - T.press) / 0.2;
          const r = lerp(9, 48, E.outCubic(k));
          ctx.strokeStyle = R.rgba(SIGNAL, 1 - E.inQuad(k));
          ctx.lineWidth = 1.5;
          ctx.beginPath(); ctx.arc(P2X, p2y(t), r, 0, R.TAU); ctx.stroke();
        }
      }

      // ---- Header: cubic-bezier(…) types on, y2 rolls 1.00 → 1.50, deletes on retract.
      this.drawHeader(ctx, t, fr);

      // ---- Preview track
      this.drawTrack(ctx, t);

      // ---- Spacing chart ghosts (Fog 1.5 px outline Ø56); pulled into the dot like beads on retract.
      {
        const G = this.ghosts, n = G.length;
        ctx.lineWidth = 1.5;
        for (let k = 0; k < n; k++) {
          if (t < G[k].t) continue;
          let x = G[k].x, y = TRACK_Y, r = DOT_R, a = 1;
          if (t >= T.retract) {
            const j = n - 1 - k; // along the string: newest bead first
            const st = T.retract + j * 0.01;
            const q = E.inCubic(seg(t, st, st + 0.1));
            const d = dotPos(t);
            x = lerp(x, d[0], q); y = lerp(y, d[1], q);
            r = DOT_R * (1 - 0.3 * q);
            a = 1 - R.smoothstep(0.6, 1, q);
            if (a <= 0.002) continue;
          }
          // Stamp: lands Ink, settles to Fog over 6 frames.
          const age = t - G[k].t;
          ctx.strokeStyle = R.rgba(age < 6 * F ? R.mixColor(INK, FOG, E.outQuad(age / (6 * F))) : FOG, a);
          ctx.beginPath(); ctx.arc(x, y, r - 0.75, 0, R.TAU); ctx.stroke();
        }
      }

      // ---- Readout "v 0.00"
      {
        let txt = null, col = INK;
        if (fr >= 317) {
          const v = t >= T.play ? valueFn(clamp((t - T.play) / PLAY_DUR)) : 0;
          txt = 'v ' + v.toFixed(2);
          const n = fr < 323 ? fr - 316 : fr >= 408 ? Math.max(0, 6 - (fr - 407)) : 6;
          txt = txt.slice(0, n);
          if (fr >= 386 && fr <= 388) { txt = 'v 1.10'; col = SIGNAL; }
        }
        if (txt) {
          ctx.font = `500 26px ${MONO}`;
          ctx.letterSpacing = '0px';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'alphabetic';
          ctx.fillStyle = col;
          ctx.fillText(txt, 1040, 770);
        }
      }
    },

    drawHeader(ctx, t, fr) {
      let n = 0;
      if (fr >= 312) n = Math.min(HEADER.length, 2 * (fr - 311));
      if (fr >= 408) n = Math.max(0, HEADER.length - 3 * (fr - 407));
      if (n <= 0) return;
      const adv = this.adv26;
      ctx.font = `500 26px ${MONO}`;
      ctx.letterSpacing = '0px';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'alphabetic';
      const y2 = 1 + 0.5 * dragK(t - 2 * F); // odometer lags the handle by 2 frames
      const d = (y2 - 1) * 10; // tenths digit position 0..5
      for (let i = 0; i < n; i++) {
        const ch = HEADER[i];
        const x = HEAD_X + i * adv;
        const punct = ch === '(' || ch === ')' || ch === ',';
        ctx.fillStyle = punct ? FOG : INK;
        if (i === ODO_I && d > 0.0005) {
          const lo = Math.floor(d + 1e-6), fr2 = d - lo;
          const LH = 26; // digit pitch; the window is exactly one cap-height tall (+1 px AA each side)
          ctx.save();
          ctx.beginPath();
          ctx.rect(x - 1, HEAD_BASE - 21, adv + 2, 23);
          ctx.clip();
          ctx.fillText(String(lo % 10), x, HEAD_BASE - Math.round(fr2 * LH * 10) / 10);
          if (fr2 > 0.001) ctx.fillText(String((lo + 1) % 10), x, HEAD_BASE + LH - Math.round(fr2 * LH * 10) / 10);
          ctx.restore();
          continue;
        }
        ctx.fillText(ch, x, HEAD_BASE);
      }
      // Signal underline on the value being edited (press → release + 0.25)
      const u = E.swift(seg(t, T.press, T.press + 0.15)) * (1 - seg(t, T.release + 0.1, T.release + 0.3, 'inOutQuad'));
      if (u > 0.002) {
        ctx.fillStyle = SIGNAL;
        ctx.fillRect(HEAD_X + Y2_I * adv, HEAD_BASE + 7, 4 * adv * u, 2);
      }
      // Caret (2 px Ink) while typing / deleting
      const typing = fr >= 312 && fr <= 332;
      const deleting = fr >= 408;
      if (typing || deleting) {
        ctx.fillStyle = INK;
        ctx.fillRect(Math.round(HEAD_X + n * adv + 2), HEAD_BASE - 22, 2, 28);
      }
    },

    drawTrack(ctx, t) {
      const retract = E.inCubic(seg(t, T.retract, T.retract + 0.17));
      const head = t < T.retract ? this.trackHead(t) : lerp(TRACK_X1, TRACK_X0, retract);
      const vis = t >= 5.2 && !(t >= T.retract + 0.19);
      if (!vis) return;
      // line
      if (head > TRACK_X0 + 0.5) {
        ctx.fillStyle = INK;
        ctx.fillRect(TRACK_X0, TRACK_Y - 1, head - TRACK_X0, 2);
      }
      // 1/8 ticks (Fog 8 px), pop as the dot passes
      for (let k = 1; k <= 7; k++) {
        const x = TRACK_X0 + 80 * k;
        if (x > head + 0.5) continue;
        let s = R.spring(t - this.tickAppear[k], POP);
        s *= popEnv(t, this.tickPass[k - 1], 1.6);
        const hot = t >= this.tickPass[k - 1] && t < this.tickPass[k - 1] + 4 * F;
        const h = 8 * s;
        ctx.fillStyle = hot ? INK : FOG;
        ctx.fillRect(x - 1, TRACK_Y - h / 2, 2, h);
      }
      // end ticks (Ink 12 px)
      const endOut = 1 - E.inCubic(seg(t, T.retract + 0.12, T.retract + 0.19));
      const sL = R.spring(t - 5.2, POP) * endOut;
      ctx.fillStyle = INK;
      if (sL > 0.01) ctx.fillRect(TRACK_X0 - 1, TRACK_Y - 6 * sL, 2, 12 * sL);
      const sR = R.spring(t - this.tickAppear[8], POP) * popEnv(t, this.tickPass[7], 1.6) * endOut;
      const xR = t < T.retract ? TRACK_X1 : head;
      if (sR > 0.01 && (t >= T.retract || head >= TRACK_X1 - 0.5)) ctx.fillRect(xR - 1, TRACK_Y - 6 * sR, 2, 12 * sR);
      // "0" / "1" under the ends
      const a = seg(t, 5.3, 5.42, 'outQuad') * (1 - seg(t, T.retract, T.retract + 0.07));
      if (a > 0.002) {
        ctx.fillStyle = R.rgba(FOG, a);
        this.label(ctx, '0', TRACK_X0, TRACK_LABEL_BASE, 'center', 0);
        this.label(ctx, '1', TRACK_X1, TRACK_LABEL_BASE, 'center', 0);
      }
    },

    // Mono 14 px label with 0.12em tracking, aligned on its ink-free advance box (no trailing tracking).
    label(ctx, s, x, y, align, track = 0.12) {
      const sp = 14 * track;
      const w = s.length * this.adv14 + (s.length - 1) * sp;
      const x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
      ctx.font = `500 14px ${MONO}`;
      ctx.letterSpacing = sp + 'px';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'alphabetic';
      ctx.fillText(s, Math.round(x0), Math.round(y));
      ctx.letterSpacing = '0px';
    },
    disc(ctx, x, y, r, col) {
      ctx.fillStyle = col;
      ctx.beginPath(); ctx.arc(x, y, r, 0, R.TAU); ctx.fill();
    },
    square(ctx, x, y, s, col) {
      ctx.fillStyle = col;
      ctx.fillRect(x - s / 2, y - s / 2, s, s);
    },

    // =======================================================================================================
    updateEase(t) {
      // Phases: staggered rise at 62% (letters) · rest at 62% (letters) · live width axis (word) · staggered wipe
      // at 125% (letters). The letters→word switch happens on the first frame the width actually changes, and the
      // word→letters switch as the wipe starts, so any sub-pixel difference between the two renderings is in motion.
      const v = t >= T.play ? valueFn(clamp((t - T.play) / PLAY_DUR)) : 0;
      const live = t >= T.play && t < T.retract && v > 0.002;
      let stretch = 62, sx = 1, offs = null, lb = this.lb62;
      if (t < T.play || (t < T.retract && !live)) {
        offs = [0, 1, 2, 3].map((i) => EASE_DROP * (1 - R.stagger(t, i, 4, { start: T.easeIn, each: F, dur: T.easeInEnd - T.easeIn - 3 * F, ease: 'swift' })));
        if (t >= T.play) offs = [0, 0, 0, 0];
      } else if (live) {
        stretch = 62 + 63 * clamp(v);
        sx = v > 1 ? 1 + 0.5 * (v - 1) : 1;
      } else {
        stretch = 125;
        lb = this.lb125;
        offs = [0, 1, 2, 3].map((i) => EASE_DROP * R.stagger(t, i, 4, { start: T.retract, each: F, dur: 0.12, ease: 'whip' }));
      }
      const lsb = this.lsbAt(stretch);
      const left = EASE_X - lsb;
      const fs = stretch.toFixed(2) + '%';
      const set = (el, st, on, tf, org) => {
        const disp = on ? 'block' : 'none';
        if (st.disp !== disp) { el.style.display = disp; st.disp = disp; }
        if (!on) return;
        if (st.fs !== fs) { el.style.fontStretch = fs; st.fs = fs; }
        if (st.tf !== tf) { el.style.transform = tf; st.tf = tf; }
        if (org && st.org !== org) { el.style.transformOrigin = org; st.org = org; }
      };
      const S = this.easeState;
      set(this.wordEl, S.word, live, `translate(${left.toFixed(3)}px, ${this.easeTop.toFixed(3)}px) scale(${sx.toFixed(4)}, 1)`, `${lsb.toFixed(3)}px 0px`);
      for (let i = 0; i < 4; i++) {
        const on = !live && offs[i] < EASE_DROP - 0.01;
        const x = left + lb.xs[i][0];
        set(this.letterEls[i], S.letters[i], on, on ? `translate(${x.toFixed(3)}px, ${(this.easeTop + offs[i]).toFixed(3)}px)` : '', null);
      }
    },

    // =======================================================================================================
    drawTop(ctx, t) {
      ctx.clearRect(0, 0, 1920, 1080);
      // ---- The dot
      const p = dotPos(t);
      const sh = shutter(t);
      const q = sh > 0 ? dotPos(t - sh) : p;
      const L = Math.hypot(p[0] - q[0], p[1] - q[1]);
      ctx.fillStyle = SIGNAL;
      ctx.strokeStyle = SIGNAL;
      if (L > 1.5) {
        // Smear: a pill spanning the shutter interval, width shrunk so the area stays ≈ the disc's (floor 0.55 D).
        const D = 2 * DOT_R;
        const W = Math.max(D * 0.55, (-L + Math.sqrt(L * L + 4 * D * D)) / 2);
        ctx.lineWidth = W;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        // Straight stadium along the chord: clean at low speed (a curved sweep reads as a lumpy bean at the apex).
        ctx.beginPath();
        ctx.moveTo(q[0], q[1]);
        ctx.lineTo(p[0], p[1]);
        ctx.stroke();
      } else {
        const s = dotSquash(t);
        ctx.beginPath();
        ctx.ellipse(p[0], p[1] + s.dy, DOT_R * s.sx, DOT_R * s.sy, 0, 0, R.TAU);
        ctx.fill();
      }

      // ---- Cursor
      const c = cursorState(t);
      if (c && c.a > 0.002) {
        ctx.save();
        ctx.globalAlpha = c.a;
        ctx.translate(c.x, c.y);
        ctx.scale(c.s, c.s);
        ctx.beginPath();
        ARROW.forEach((pt, i) => (i ? ctx.lineTo(pt[0], pt[1]) : ctx.moveTo(pt[0], pt[1])));
        ctx.closePath();
        ctx.lineJoin = 'round';
        ctx.lineWidth = 4; // 2 px Paper outline outside the Ink fill
        ctx.strokeStyle = PAPER;
        ctx.stroke();
        ctx.fillStyle = INK;
        ctx.fill();
        ctx.restore();
      }
    },
  });
})();
