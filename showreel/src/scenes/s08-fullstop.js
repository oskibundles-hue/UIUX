// s08-fullstop — "Full Stop — the name card"  (13.125 → 15.0 s · bar 8 · z 80 · Ink)
//
// FINAL HIT: the canonical condensed "CLAUDE" handed over by s07 is released from width 62 to 125 on
// one 8th (swift), with a POP letter-spacing kick and a TIGHT scaleX overshoot as follow-through. The
// expanding E flings the protagonist dot up and over (smear frames, stretch along velocity); it lands on
// beat 2 as the hanging period with a baseline-anchored squash and two micro-bounces. The Swiss lockup
// sets in around it: hairlines drawn from the centre, registration crosses, the serif role rising through
// a mask, the mono year line typed behind a Signal block cursor, the masked tagline and the stroke-drawn
// "C." monogram. Beat 3 locks the card and starts a linear push-in; on beat 4 the monogram's dot clicks
// into its opening and the big period blinks. Everything is a pure function of t.
(function () {
  'use strict';

  const P = R.pal;
  const E = R.ease;
  const clamp = R.clamp, lerp = R.lerp;

  // ---- Timeline (global seconds, 128 BPM grid) -------------------------------------------------------
  const T_IN = 13.125;                                  // 8.1.1  FINAL HIT (audio)
  const T_F0 = Math.ceil(T_IN * R.FPS - 1e-6) / R.FPS;  // 13.1333: first rendered frame = the canonical rest pose
  const REL = R.E8;                                     // the release: one 8th, swift
  const T_HAIR = 13.2421875;                            // 8.1.2  hairlines draw outward
  const T_LAND = 13.59375;                              // 8.2.1  the period lands
  const T_UP1 = 13.625;                                 //        leaves the baseline after the 2-frame squash
  const T_B1 = 13.7109375;                              //        micro-bounce 1 lands (34 px hop)
  const T_UP2 = 13.7215;                                //        leaves again after 1 contact frame
  const T_B2 = 13.76953125;                             //        micro-bounce 2 lands (10 px hop)
  const T_REST = 13.83;                                 //        settled
  const T_TYPE = 13.828125;                             // 8.2.3  type-on, tagline, ring draw
  const T_LOCK = 14.0625;                               // 8.3.1  LOCK + push-in
  const T_TICK = 14.53125;                              // 8.4.1  THE FINAL TICK (the monogram dot lands ON the beat)
  const T_END = 15;

  // ---- Geometry (frame px) -----------------------------------------------------------------------------
  const W0 = { stretch: 62, size: 370, base: 670 };     // canonical condensed word (s07 rest pose)
  const W1 = { stretch: 125, base: 600, inkL: 200, inkR: 1720 };
  const DOT0 = { x: 1542, y: 638, d: 64 };              // s07 handoff disc
  const DOT1 = { x: 1764, y: 570, d: 60 };              // the hanging period (bottom on the baseline)
  const HAIR_Y = [370, 648];
  const RING = { cx: 236, cy: 980, r: 28, sw: 12 };      // "C." monogram, 60° opening at 3 o'clock
  const MDOT = { x: 264, y: 980, d: 16, y0: 940, dx: 48 }; // its dot (enters from (312, 940), lands in the opening)
  const YEAR = { text: 'SHOWREEL 2026', size: 30, ls: 0.24, x: 200, base: 336 };
  const TAG = { text: 'EVERY FRAME, ON PURPOSE.', size: 22, ls: 0.16, x: 1720, base: 752 };
  const ROLE = { text: 'Motion Designer', size: 96, x: 200, base: 752 };

  const C_HAIR = R.mixColor(P.ink, P.paper, 0.35);      // Paper @35% on Ink (opaque: overlaps stay uniform)
  const C_CROSS = R.mixColor(P.ink, P.paper, 0.6);      // Paper @60%
  const C_YEAR = R.mixColor(P.ink, P.paper, 0.85);      // Paper @85%

  // ---- Motion tuning -----------------------------------------------------------------------------------
  const LS_FROM = -0.03, LS_PEAK = 0.02;                // em: starts tight, POP kick swings it open, settles
  const LS_DELAY = 0.05;                                // the letters stay tight while the E shoves the dot
  const SX_AMP = 0.015, SX_DELAY = 0.083;               // extra scaleX overshoot (TIGHT impulse) once the dot has cleared the E
  const FOLLOW_END = 13.55;                             // letter-spacing and scaleX are exactly neutral from here
  const STRETCH_K = 0.3;                                // in-flight stretch per (displacement per frame / diameter)

  // ---- Small maths ------------------------------------------------------------------------------------
  // Damped oscillator (unit mass): displacement with x(0) = x0, x'(0) = v0, stiffness k, damping c.
  function osc(t, k, c, x0, v0) {
    const a = c / 2, wd = Math.sqrt(k - a * a);
    return Math.exp(-a * t) * (x0 * Math.cos(wd * t) + ((v0 + a * x0) / wd) * Math.sin(wd * t));
  }
  // Normalised impulse response of a spring (0 at t=0, peak 1, then the spring's own undershoot).
  function impulse(k, c) {
    const a = c / 2, wd = Math.sqrt(k - a * a), tp = Math.atan(wd / a) / wd;
    const pk = Math.exp(-a * tp) * Math.sin(wd * tp);
    return (t) => (t <= 0 ? 0 : (Math.exp(-a * t) * Math.sin(wd * t)) / pk);
  }
  const POP = { k: 380, c: 18 }, TIGHT = { k: 420, c: 26 };
  const sxImpulse = impulse(TIGHT.k, TIGHT.c);
  // POP kick velocity so the first overshoot of the letter-spacing reaches exactly LS_PEAK (bisection, once).
  const LS_V0 = (function () {
    const peak = (v0) => { let m = -1; for (let i = 1; i < 800; i++) m = Math.max(m, osc(i / 1000, POP.k, POP.c, LS_FROM, v0)); return m; };
    let lo = 0, hi = 20;
    for (let i = 0; i < 50; i++) { const mid = (lo + hi) / 2; if (peak(mid) < LS_PEAK) lo = mid; else hi = mid; }
    return (lo + hi) / 2;
  })();
  const followWin = (t) => 1 - R.smoothstep(FOLLOW_END - 0.08, FOLLOW_END, t);

  function lsEm(t) {                                   // letter-spacing in em at global t
    const tr = t - T_F0;
    if (tr <= 0) return 0;                             // canonical frame: exactly 0
    const u = tr - LS_DELAY;
    const x = u <= 0 ? LS_FROM : osc(u, POP.k, POP.c, LS_FROM, LS_V0);
    return x * followWin(t);
  }
  function scaleX(t) {
    const tr = t - T_F0;
    if (tr <= 0) return 1;
    return 1 + SX_AMP * sxImpulse(tr - SX_DELAY) * followWin(t);
  }
  const relEase = (t) => (t <= T_F0 ? 0 : E.swift(Math.min(1, (t - T_F0) / REL)));

  // Convex hull of two circles (head: centre h, radius a; tail: centre q, radius b) as an SVG path.
  function hullPath(hx, hy, a, qx, qy, b) {
    const dx = hx - qx, dy = hy - qy, c = Math.hypot(dx, dy) || 1e-6;
    const th = Math.atan2(dy, dx), al = Math.asin(clamp((a - b) / c, -0.99, 0.99));
    const pts = [], NH = 28, NT = 14;
    for (let k = 0; k <= NH; k++) {                        // front arc around the head
      const g = th + Math.PI / 2 + al - (k * (Math.PI + 2 * al)) / NH;
      pts.push([hx + a * Math.cos(g), hy + a * Math.sin(g)]);
    }
    for (let k = 0; k <= NT; k++) {                        // back arc around the tail
      const g = th - Math.PI / 2 - al - (k * (Math.PI - 2 * al)) / NT;
      pts.push([qx + b * Math.cos(g), qy + b * Math.sin(g)]);
    }
    return R.poly.toPath(pts, true);
  }

  // piecewise-linear lookup in a sorted [[x, y...], ...] table
  function lookup(tab, x, col) {
    if (x <= tab[0][0]) return tab[0][col];
    const n = tab.length - 1;
    if (x >= tab[n][0]) return tab[n][col];
    let i = 1;
    while (tab[i][0] < x) i++;
    const a = tab[i - 1], b = tab[i];
    return lerp(a[col], b[col], (x - a[0]) / (b[0] - a[0]));
  }

  // ---- Setup-time measurement (pipeline Chromium, bundled fonts) --------------------------------------
  function measure() {
    const host = R.el('div', { style: { width: R.W + 'px', height: R.H + 'px', visibility: 'hidden', pointerEvents: 'none' } }, document.body);
    const M = {};

    // Baseline offset below the line-box top (line-height 1) via a 0x0 inline-block marker.
    const baseOff = (style, text) => {
      const el = R.el('div', { style: Object.assign({ whiteSpace: 'nowrap', lineHeight: '1' }, style) }, host);
      el.appendChild(document.createTextNode(text));
      const mk = R.el('span', { style: { position: 'static', display: 'inline-block', width: '0px', height: '0px' } }, el);
      const off = mk.getBoundingClientRect().bottom - el.getBoundingClientRect().top;
      el.remove();
      return off;
    };
    // Ink box of rendered text relative to its origin/baseline: rasterise on a canvas, scan coverage.
    const scan = (font, text, size, o = {}) => {
      const cv = document.createElement('canvas');
      const ctx = cv.getContext('2d', { willReadFrequently: true });
      const setFont = () => {
        ctx.font = font;
        ctx.fontStretch = o.stretch || 'normal';
        ctx.letterSpacing = o.ls || '0px';
        ctx.fontKerning = 'normal';
      };
      setFont();
      const adv = ctx.measureText(text).width;
      const pad = Math.ceil(size * 0.6);
      cv.width = Math.ceil(adv + 2 * pad);
      cv.height = Math.ceil(size * 2);
      setFont();
      ctx.fillStyle = '#fff';
      ctx.textBaseline = 'alphabetic';
      const ox = pad, oy = Math.round(size * 1.35);
      ctx.fillText(text, ox, oy);
      const W = cv.width, H = cv.height, d = ctx.getImageData(0, 0, W, H).data;
      const cm = new Uint8Array(W), rm = new Uint8Array(H);
      for (let y = 0; y < H; y++) {
        for (let x = 0; x < W; x++) {
          const a = d[(y * W + x) * 4 + 3];
          if (a > cm[x]) cm[x] = a;
          if (a > rm[y]) rm[y] = a;
        }
      }
      let l = 0, r = W - 1, t = 0, b = H - 1;
      while (l < W - 1 && !cm[l]) l++;
      while (r > 0 && !cm[r]) r--;
      while (t < H - 1 && !rm[t]) t++;
      while (b > 0 && !rm[b]) b--;
      return {
        l: l + 1 - cm[l] / 255 - ox, r: r + cm[r] / 255 - ox,
        t: t + 1 - rm[t] / 255 - oy, b: b + rm[b] / 255 - oy, adv,
      };
    };

    // (1) the canonical start: baseline 670 exactly as s07 places it
    const canon = { fontFamily: R.font.display, fontWeight: '900', fontStretch: '62%', fontSize: '370px' };
    M.off0 = baseOff(canon, 'CLAUDE');
    M.top0 = W0.base - M.off0;

    // (2) Archivo 900 side bearings across the width axis (canvas knows keyword widths only)
    const REF = 284;
    const KW = [['extra-condensed', 62.5], ['condensed', 75], ['semi-condensed', 87.5], ['normal', 100], ['semi-expanded', 112.5], ['expanded', 125]];
    M.sb = KW.map(([kw, pct]) => {
      const s = scan(`900 ${REF}px ${R.font.display}`, 'CLAUDE', REF, { stretch: kw });
      return [pct, s.l / REF, (s.adv - s.r) / REF, (s.r - s.l) / REF];   // [%, lsb(C) em, rsb(E) em, ink width em]
    });
    // (3) final size: the ink of CLAUDE at width 125 spans exactly 1520 px (x 200 → 1720)
    M.size1 = (W1.inkR - W1.inkL) / M.sb[M.sb.length - 1][3];
    M.off1 = baseOff({ fontFamily: R.font.display, fontWeight: '900', fontStretch: '125%', fontSize: M.size1 + 'px' }, 'CLAUDE');
    M.top1 = W1.base - M.off1;

    // (4) release table: ink left (C) / ink right (E) of the centred word vs release progress e (ls 0, no transform)
    const word = R.el('div', {
      text: 'CLAUDE',
      style: Object.assign({}, canon, { lineHeight: '1', letterSpacing: '0px', fontKerning: 'normal', left: '0px', width: R.W + 'px', textAlign: 'center', whiteSpace: 'nowrap' }),
    }, host);
    const tn = word.firstChild, rg = document.createRange();
    const charRect = (i) => { rg.setStart(tn, i); rg.setEnd(tn, i + 1); return rg.getBoundingClientRect(); };
    M.tab = [];
    const NK = 40;
    for (let k = 0; k <= NK; k++) {
      const e = k / NK, st = lerp(W0.stretch, W1.stretch, e), sz = lerp(W0.size, M.size1, e);
      word.style.fontStretch = st + '%';
      word.style.fontSize = sz + 'px';
      const cL = charRect(0).left, eR = charRect(5).right;
      M.tab.push([e, cL + lookup(M.sb, st, 1) * sz, eR - lookup(M.sb, st, 2) * sz]);
    }
    word.remove();
    // horizontal trim so the final ink lands exactly on x 200 → 1720 (the E's right edge on a pixel boundary)
    M.dx1 = W1.inkR - M.tab[NK][2];

    // (5) mono + serif lines
    M.yearOff = baseOff({ fontFamily: R.font.mono, fontWeight: '500', fontSize: YEAR.size + 'px' }, YEAR.text);
    const ys = scan(`500 ${YEAR.size}px ${R.font.mono}`, YEAR.text, YEAR.size, { ls: YEAR.ls * YEAR.size + 'px' });
    M.yearX = YEAR.x - ys.l;
    M.yearPitch = ys.adv / YEAR.text.length;                  // advance + tracking per cell
    M.yearCap = -ys.t;                                        // cap height (block cursor height)
    M.tagOff = baseOff({ fontFamily: R.font.mono, fontWeight: '400', fontSize: TAG.size + 'px' }, TAG.text);
    const tg = scan(`400 ${TAG.size}px ${R.font.mono}`, TAG.text, TAG.size, { ls: TAG.ls * TAG.size + 'px' });
    M.tagX = TAG.x - tg.r;
    M.tagPitch = tg.adv / TAG.text.length;
    M.roleOff = baseOff({ fontFamily: R.font.serif, fontStyle: 'italic', fontWeight: '400', fontSize: ROLE.size + 'px' }, ROLE.text);
    const rs = scan(`italic 400 ${ROLE.size}px ${R.font.serif}`, ROLE.text, ROLE.size);
    M.roleX = ROLE.x - rs.l;
    M.roleInk = rs;
    // per-letter origins of the role (kerned positions from the unsplit run)
    const role = R.el('div', { text: ROLE.text, style: { fontFamily: R.font.serif, fontStyle: 'italic', fontWeight: '400', fontSize: ROLE.size + 'px', lineHeight: '1', whiteSpace: 'nowrap' } }, host);
    const rtn = role.firstChild, rx0 = role.getBoundingClientRect().left;
    M.roleChars = [];
    for (let i = 0; i < ROLE.text.length; i++) {
      rg.setStart(rtn, i); rg.setEnd(rtn, i + 1);
      M.roleChars.push({ ch: ROLE.text[i], x: rg.getBoundingClientRect().left - rx0 });
    }
    role.remove();
    host.remove();
    return M;
  }

  // ---- The scene ----------------------------------------------------------------------------------------
  R.scene({
    id: 's08-fullstop',
    start: 13.125,
    end: 15,
    z: 80,
    bg: P.ink,

    setup(root) {
      const M = (this.M = measure());

      // Global FX (storyboard, s08 rows)
      R.cue(13.125, 'chroma', { amt: 10, dur: 0.2 });                      // final hit
      R.cue(13.125, 'flash', { amt: 1.0, dur: 0.15, color: '#FFFFFF' });   // FINAL HIT (masks the s07→s08 handoff)
      R.cue(13.125, 'shake', { amt: 14, dur: 0.32 });                      // final hit (storyboard 0.35: the last 0.03 s is < 0.1 px and trips a compositor race, see report)
      R.cue(13.125, 'zoom', { amt: 0.06, dur: 0.3 });                      // final hit
      R.cue(13.59375, 'shake', { amt: 3, dur: 0.1 });                      // period lands
      R.cue(14.53125, 'zoom', { amt: 0.01, dur: 0.12 });                   // the final tick

      // Sound design (picture-locked)
      R.sfx(13.125, 'impact', { amt: 1.3, tone: 'huge' });                 // FINAL HIT
      R.sfx(13.125, 'subdrop', { amt: 1.0 });                              // final hit
      R.sfx(13.125, 'shimmer', { dur: 1.6, amt: 0.5 });                    // tail
      R.sfx(13.125, 'whoosh', { dur: 0.234375, dir: 'up' });               // dot flight
      R.sfx(13.59375, 'pop', { pitch: 2.0 });                              // period lands, F5
      R.sfx(13.7109375, 'tick', { pitch: 2.0 });                           // bounce
      R.sfx(13.76953125, 'tick', { pitch: 2.5 });                          // bounce
      R.sfx(13.828125, 'type', { count: 13, dur: 0.2167 });                // SHOWREEL 2026
      R.sfx(13.828125, 'shimmer', { dur: 0.5, amt: 0.3 });                 // reveal air
      R.sfx(14.53125, 'blip', { pitch: 4.0 });                             // THE FULL STOP, F6 sine
      R.sfx(14.53125, 'click', { pitch: 0.5 });                            // soft sub click

      // Everything of s08 lives on one wrapper so the end-card push-in never touches the HUD (s00).
      const wrap = (this.wrap = R.el('div', { style: { width: R.W + 'px', height: R.H + 'px', transformOrigin: '960px 540px' } }, root));

      // Hairlines + registration crosses: SVG rects (unsnapped geometry), so their rows can be pinned to whole
      // device pixels under the push-in (see update) and their drawn ends glide with sub-pixel AA.
      const rules = R.svgLayer(wrap);
      this.hair = HAIR_Y.map((y) => ({ y, el: R.svg('rect', { x: 960, y, width: 0, height: 1, fill: C_HAIR, display: 'none' }, rules) }));
      this.crosses = [];
      for (const y of HAIR_Y) {
        for (const x of [W1.inkL, W1.inkR - 1]) {
          this.crosses.push({
            x, y,
            h: R.svg('rect', { height: 1, fill: C_CROSS, display: 'none' }, rules),
            v: R.svg('rect', { x, width: 1, fill: C_CROSS, display: 'none' }, rules),
          });
        }
      }

      // The protagonist sits just beneath the word: its smear trails out from behind the E.
      this.dot = R.el('div', { style: { background: P.signal } }, wrap);
      const smearSvg = R.svgLayer(wrap);
      this.smear = R.svg('path', { fill: P.signal, d: 'M0 0' }, smearSvg);

      // THE canonical element (identical CSS to s07's rest pose; only restyled from here on)
      this.word = R.el('div', {
        text: 'CLAUDE',
        style: {
          fontFamily: R.font.display, fontWeight: '900', fontStretch: '62%', fontSize: '370px', lineHeight: '1',
          letterSpacing: '0px', fontKerning: 'normal', color: P.paper, left: '0px', width: R.W + 'px',
          textAlign: 'center', whiteSpace: 'nowrap', top: M.top0 + 'px', transformOrigin: '960px 0px',
        },
      }, wrap);

      // On the handoff frame the disc is rasterised exactly as s07 draws it (a canvas arc on the frame's pixel
      // grid, stacked above the word as in s07, so the word is not promoted to its own compositing layer):
      // s07's rest pose and s08's first frame match pixel for pixel, rim AA included.
      const hc = R.canvas(wrap, { w: 128, h: 128, style: { left: DOT0.x - 64 + 'px', top: DOT0.y - 64 + 'px' } });
      hc.ctx.fillStyle = P.signal;
      hc.ctx.beginPath();
      hc.ctx.arc(64, 64, DOT0.d / 2, 0, R.TAU);
      hc.ctx.fill();
      this.handoffDisc = hc.canvas;

      // Role: letters rise through a mask whose bottom sits just under the descenders
      const roleTop = ROLE.base - M.roleOff;
      const mTop = Math.floor(ROLE.base + M.roleInk.t) - 8, mBot = Math.ceil(ROLE.base + M.roleInk.b) + 6;
      this.maskH = mBot - mTop;
      this.roleMask = R.el('div', { style: { left: '0px', top: mTop + 'px', width: R.W + 'px', height: this.maskH + 'px', overflow: 'hidden' } }, wrap);
      this.roleWhole = R.el('div', {
        text: ROLE.text,
        style: { left: M.roleX + 'px', top: roleTop + 'px', fontFamily: R.font.serif, fontStyle: 'italic', fontWeight: '400', fontSize: ROLE.size + 'px', lineHeight: '1', whiteSpace: 'nowrap', color: P.paper },
      }, wrap);
      this.roleLetters = [];
      M.roleChars.forEach((c, i) => {
        if (c.ch === ' ') return;
        const el = R.el('div', {
          text: c.ch,
          style: { left: (M.roleX + c.x) + 'px', top: (roleTop - mTop) + 'px', fontFamily: R.font.serif, fontStyle: 'italic', fontWeight: '400', fontSize: ROLE.size + 'px', lineHeight: '1', whiteSpace: 'pre', color: P.paper },
        }, this.roleMask);
        this.roleLetters.push({ el, i });
      });

      // SHOWREEL 2026 (typed) + Signal block cursor
      this.year = R.el('div', {
        style: { left: M.yearX + 'px', top: (YEAR.base - M.yearOff) + 'px', fontFamily: R.font.mono, fontWeight: '500', fontSize: YEAR.size + 'px', lineHeight: '1', letterSpacing: (YEAR.ls * YEAR.size) + 'px', whiteSpace: 'pre', color: C_YEAR, fontVariantNumeric: 'tabular-nums' },
      }, wrap);
      this.cursorH = Math.round(Math.min(0.75 * YEAR.size, M.yearCap));   // block cursor = cap height (0.6 em × ≈0.75 em)
      this.cursor = R.el('div', { style: { width: Math.round(0.6 * YEAR.size) + 'px', height: this.cursorH + 'px', top: (YEAR.base - this.cursorH) + 'px', background: P.signal } }, wrap);

      // Tagline, revealed left→right 2 cells per frame
      this.tag = R.el('div', {
        text: TAG.text,
        style: { left: M.tagX + 'px', top: (TAG.base - M.tagOff) + 'px', fontFamily: R.font.mono, fontWeight: '400', fontSize: TAG.size + 'px', lineHeight: '1', letterSpacing: (TAG.ls * TAG.size) + 'px', whiteSpace: 'pre', color: P.fog },
      }, wrap);
      this.tagW = M.tagPitch * TAG.text.length;

      // Monogram "C.": gapped ring (stroke-drawn from 30° clockwise to 330°) + its dot
      const svg = R.svgLayer(wrap);
      const a0 = R.deg(30), a1 = R.deg(330);
      const p0 = [RING.cx + RING.r * Math.cos(a0), RING.cy + RING.r * Math.sin(a0)];
      const p1 = [RING.cx + RING.r * Math.cos(a1), RING.cy + RING.r * Math.sin(a1)];
      this.ring = R.svg('path', {
        d: `M${p0[0].toFixed(4)} ${p0[1].toFixed(4)}A${RING.r} ${RING.r} 0 1 1 ${p1[0].toFixed(4)} ${p1[1].toFixed(4)}`,
        fill: 'none', stroke: P.paper, 'stroke-width': RING.sw, 'stroke-linecap': 'butt',
      }, svg);
      R.drawStroke(this.ring, 0);   // caches the path length in setup
      this.mdot = R.el('div', { style: { background: P.signal, borderRadius: '50%' } }, wrap);

      // small-type lines whose baselines are held on whole device rows during the push-in (see update)
      const kLast = (this.kLast = +(1 + (0.012 * ((R.FPS * T_END - 1) / R.FPS - T_LOCK)) / (T_END - T_LOCK)).toFixed(6));
      this.pinned = [[this.year, YEAR.base], [this.tag, TAG.base], [this.roleWhole, ROLE.base]].map(([el, base]) => (
        { el, base, dEnd: Math.round(540 + (base - 540) * kLast) }));
    },

    // --- the word's state at global t ---
    wordAt(t) {
      const M = this.M, e = relEase(t);
      const stretch = lerp(W0.stretch, W1.stretch, e);
      const size = lerp(W0.size, M.size1, e);
      const base = lerp(W0.base, W1.base, e);
      const top = base - lerp(M.off0 / W0.size, M.off1 / M.size1, e) * size;
      const ls = lsEm(t) * size, sx = scaleX(t), dx = M.dx1 * e;
      // Blink adds tracking after every glyph (ink box grows by 5·ls and drifts by −ls/2): re-centre it.
      const tx = dx + 0.5 * ls * sx;
      const inkR0 = lookup(M.tab, e, 2) + dx;   // the E's ink edge before follow-through (what the dot rides)
      return { e, stretch, size, top, ls, sx, tx, inkR0 };
    },

    // --- the protagonist's flight (t < T_LAND): centre + along-velocity stretch ---
    flightPos(t) {
      const tau = clamp((t - T_F0) / (T_LAND - T_F0));
      const w = this.wordAt(t);
      // x rides the E's ink edge, 46 → 44 px right of it (on the release ease, so x never doubles back):
      // kicked up-right while the word expands, then a clean vertical pop and drop. y is the storyboard arc.
      const g0 = DOT0.x - this.M.tab[0][2], g1 = DOT1.x - W1.inkR;
      return {
        x: w.inkR0 + lerp(g0, g1, w.e),
        y: DOT0.y - 68 * tau - 4 * 403.3 * tau * (1 - tau),
        d: lerp(DOT0.d, DOT1.d, w.e),
      };
    },

    update(lt, p, t) {
      const M = this.M;

      // ---- push-in (linear, s08 content only) ----
      const push = t > T_LOCK ? +(1 + (0.012 * (t - T_LOCK)) / (T_END - T_LOCK)).toFixed(6) : 1;
      this.wrap.style.transform = push === 1 ? 'none' : `scale(${push})`;
      // Small type (mono year, serif role, mono tagline): Blink snaps text baselines to whole device pixels,
      // so under the push-in each line would hop 1 px at arbitrary frames (twice per line) while everything
      // else glides. Instead each line's baseline is held on its rest pixel row and moves to its final row
      // exactly on the beat-4 tick, where the tick's zoom punch moves the whole frame anyway. Horizontal
      // positions keep gliding (horizontal subpixel text is smooth). Deviation from the exact scale ≤ 1.3 px.
      for (const L of this.pinned) {
        const D = t >= T_TICK ? L.dEnd : L.base;          // target device row of the baseline
        const dy = push === 1 ? 0 : (D - 540) / push - (L.base - 540);
        L.el.style.transform = Math.abs(dy) < 1e-4 ? 'none' : `translateY(${dy.toFixed(4)}px)`;
      }

      // ---- RELEASE: restyle the canonical element ----
      const w = this.wordAt(t);
      const ws = this.word.style;
      ws.fontStretch = w.stretch.toFixed(4) + '%';
      ws.fontSize = w.size.toFixed(4) + 'px';
      ws.top = w.top.toFixed(4) + 'px';
      ws.letterSpacing = w.ls.toFixed(4) + 'px';
      ws.transform = w.tx === 0 && w.sx === 1 ? 'none' : w.sx === 1 ? `translateX(${w.tx.toFixed(4)}px)` : `translateX(${w.tx.toFixed(4)}px) scaleX(${w.sx.toFixed(5)})`;

      // ---- the protagonist ----
      this.drawDot(t);

      // ---- hairlines (drawn outward from x 960) + registration crosses ----
      const hq = E.swift(clamp((t - T_HAIR) / (T_LAND - T_HAIR)));
      const half = 760 * hq;
      // local y that puts a rule's row exactly on a whole device row: held on its rest row, moved to its
      // final row on the beat-4 tick together with the small type (the rows and the type stay locked).
      const rowY = (y) => {
        if (push === 1) return { y, h: 1 };
        const D = t >= T_TICK ? Math.round(540 + (y - 540) * this.kLast) : y;
        return { y: 540 + (D - 540) / push, h: 1 / push };
      };
      for (const h of this.hair) {
        const r = rowY(h.y);
        h.el.setAttribute('display', half > 0.01 ? 'inline' : 'none');
        h.el.setAttribute('x', (960 - half).toFixed(3));
        h.el.setAttribute('width', (2 * half).toFixed(3));
        h.el.setAttribute('y', r.y.toFixed(4));
        h.el.setAttribute('height', r.h.toFixed(6));
      }
      const cq = t < T_LAND ? 0 : E.punch(clamp((t - T_LAND) / 0.1));
      const arm = 6 * cq;
      for (const c of this.crosses) {
        const on = arm > 0.05, r = rowY(c.y), dy = r.y - c.y;
        c.h.setAttribute('display', on ? 'inline' : 'none');
        c.v.setAttribute('display', on ? 'inline' : 'none');
        c.h.setAttribute('x', (c.x - arm).toFixed(3));
        c.h.setAttribute('y', r.y.toFixed(4));
        c.h.setAttribute('width', (2 * arm + 1).toFixed(3));
        c.h.setAttribute('height', r.h.toFixed(6));
        c.v.setAttribute('y', (c.y - arm + dy).toFixed(4));
        c.v.setAttribute('height', (2 * arm + 1).toFixed(3));
      }

      // ---- role: letters rise through the mask (swift 0.234 s, stagger 1/120 s) ----
      const roleDone = t >= T_LAND + (ROLE.text.length - 1) / 120 + R.E8;
      this.roleWhole.style.display = roleDone ? 'block' : 'none';
      this.roleMask.style.display = roleDone || t < T_LAND ? 'none' : 'block';
      for (const L of this.roleLetters) {
        const u = clamp((t - (T_LAND + L.i / 120)) / R.E8);
        const y = this.maskH * (1 - E.swift(u));
        L.el.style.transform = y === 0 ? 'none' : `translateY(${y.toFixed(3)}px)`;
      }

      // ---- SHOWREEL 2026: 1 char/frame behind a Signal block cursor ----
      const k = Math.floor((t - T_TYPE) * R.FPS + 1e-6);
      const nYear = t < T_TYPE ? 0 : clamp(k + 1, 0, YEAR.text.length);
      this.year.textContent = YEAR.text.slice(0, nYear);
      const curOn = t >= T_TYPE - 1 / R.FPS && t < T_LOCK;
      this.cursor.style.display = curOn ? 'block' : 'none';
      this.cursor.style.left = Math.round(M.yearX + nYear * M.yearPitch) + 'px';

      // ---- tagline: 2 cells per frame, left → right ----
      const nTag = t < T_TYPE ? 0 : clamp(2 * (k + 1), 0, TAG.text.length);
      this.tag.style.display = nTag > 0 ? 'block' : 'none';
      this.tag.style.clipPath = nTag >= TAG.text.length ? 'none' : `inset(-8px ${(this.tagW - nTag * M.tagPitch).toFixed(3)}px -8px -8px)`;

      // ---- monogram ring: stroke-draw 30° → 330° clockwise ----
      const rq = E.swift(clamp((t - T_TYPE) / (T_LOCK - T_TYPE)));
      this.ring.style.display = rq > 0 ? 'inline' : 'none';
      R.drawStroke(this.ring, rq);

      // ---- monogram dot: drops into the opening and lands ON beat 4 ----
      this.drawMonoDot(t);
    },

    // Place a disc/ellipse element: centre (cx, cy), size w × h, rotated by `rot` radians.
    place(el, cx, cy, w, h, rot) {
      const s = el.style;
      s.width = w.toFixed(3) + 'px';
      s.height = h.toFixed(3) + 'px';
      s.borderRadius = '50%';
      const tx = cx - w / 2, ty = cy - h / 2;
      s.transform = `translate(${tx.toFixed(3)}px,${ty.toFixed(3)}px)` + (rot ? ` rotate(${rot.toFixed(5)}rad)` : '');
    },

    drawDot(t) {
      const el = this.dot;
      const handoff = t <= T_F0;                        // the canonical first frame
      this.handoffDisc.style.display = handoff ? 'block' : 'none';
      el.style.display = handoff ? 'none' : 'block';
      this.smear.style.display = 'none';
      if (handoff) return;
      if (t < T_LAND) {
        const tr = t - T_F0;
        const c = this.flightPos(t);
        // velocity from the frame-to-frame displacement (the smear direction)
        const prev = this.flightPos(Math.max(T_F0, t - 1 / R.FPS));
        let vx = c.x - prev.x, vy = c.y - prev.y;
        const dist = Math.hypot(vx, vy);
        if (dist < 1e-6) { vx = 0; vy = 1; } else { vx /= dist; vy /= dist; }
        // smear frames on the first two moving frames (2.2 then 1.4), then speed-proportional stretch
        const fr = tr * R.FPS;
        const smear = fr < 1 ? lerp(1, 2.2, fr) : fr < 2 ? lerp(2.2, 1.4, fr - 1) : fr < 3 ? lerp(1.4, 1, fr - 2) : 1;
        const s = Math.max(smear, Math.min(1.35, 1 + (STRETCH_K * dist) / c.d));
        if (s > 1.38) {
          // Smear frame: a tapered teardrop (full head, thin tail trailing back along the path) whose
          // leading edge sits where the round disc's leading edge would be.
          const Rr = c.d / 2, a = Rr * (1 - 0.065 * (s - 1)), b = Rr * Math.max(0.28, 1 - 0.6 * (s - 1));
          const hx = c.x + vx * (Rr - a), hy = c.y + vy * (Rr - a);
          const len = c.d * s - a - b;
          this.smear.setAttribute('d', hullPath(hx, hy, a, hx - vx * len, hy - vy * len, b));
          this.smear.style.display = 'inline';
          el.style.display = 'none';
          return;
        }
        const L = c.d * s, T = c.d / s;
        // keep the leading edge where the round disc's leading edge would be; the stretch trails behind
        const back = (L - c.d) / 2;
        this.place(el, c.x - vx * back, c.y - vy * back, L, T, Math.atan2(vy, vx));
        return;
      }
      // ---- touchdown, micro-bounces, settle ----
      const D = DOT1.d;
      let bottom = W1.base, sx = 1, sy = 1;
      if (t < T_UP1) {                                  // 2-frame squash 1.45 × 0.69 on the baseline
        const q = 1 - 0.1 * R.smoothstep(T_LAND, T_UP1, t);
        sy = 1 - 0.31 * q; sx = 1 / sy;
      } else if (t < T_B1) {                            // hop 1: 34 px
        const T = T_B1 - T_UP1, u = (t - T_UP1) / T;
        bottom -= 4 * 34 * u * (1 - u);
        sy = 1 + 0.00008 * Math.abs((4 * 34 * (1 - 2 * u)) / T); sx = 1 / sy;
      } else if (t < T_UP2) {                           // contact 2
        sy = 1 - 0.31 * 0.5; sx = 1 / sy;
      } else if (t < T_B2) {                            // hop 2: 10 px
        const T = T_B2 - T_UP2, u = (t - T_UP2) / T;
        bottom -= 4 * 10 * u * (1 - u);
        sy = 1 + 0.00008 * Math.abs((4 * 10 * (1 - 2 * u)) / T); sx = 1 / sy;
      } else if (t < T_REST) {                          // contact 3: quick TIGHT-character settle
        const q = 0.25 * osc(t - T_B2, 3780, 78, 1, 0) * (1 - R.smoothstep(T_REST - 0.03, T_REST, t));
        sy = 1 - 0.31 * q; sx = 1 / sy;
      }
      // the final-tick blink (anchored on the baseline)
      let b = 1;
      if (t >= T_TICK) b = R.kf(t, [[T_TICK, 1], [14.5703125, 1.14, 'outCubic'], [14.6484375, 1, 'inOutSine']]);
      const wd = D * sx * b, ht = D * sy * b;
      this.place(el, DOT1.x, bottom - ht / 2, wd, ht, 0);
    },

    drawMonoDot(t) {
      const el = this.mdot, D = MDOT.d;
      const tIn = T_TICK - 3 / R.FPS;                   // 3-frame inQuad drop, contact exactly on beat 4
      if (t < tIn) { el.style.display = 'none'; return; }
      el.style.display = 'block';
      if (t < T_TICK) {
        // A short arc into the mouth of the C: y is the storyboard's inQuad drop from 940; x slides in from
        // the right (linear in u) so the dot never crosses the ring's 330° tip (a straight drop at x 264
        // passes through it on the frame before contact). Stretch along velocity, leading edge held.
        const u = (t - tIn) / (T_TICK - tIn), dur = T_TICK - tIn;
        const x = MDOT.x + MDOT.dx * (1 - u);
        const y = MDOT.y0 + (MDOT.y - MDOT.y0) * u * u;
        const vx = -MDOT.dx / dur, vy = (2 * (MDOT.y - MDOT.y0) * u) / dur;   // px/s
        // it materialises small (Ø9.6) at the top of the arc and reaches full size a frame before contact
        const g = 0.6 + 0.4 * Math.min(1, 1.5 * u), d = D * g;
        const v = Math.hypot(vx, vy), s = Math.min(1.3, 1 + 0.00012 * v), back = (d * s - d) / 2;
        this.place(el, x - (vx / v) * back, y - (vy / v) * back, d * s, d / s, Math.atan2(vy, vx));
        return;
      }
      // 2-frame squash anchored at its lowest point, a one-frame rebound, then round
      const q = R.kf(t - T_TICK, [[0, 1], [0.02, 0.9], [0.036, 0.3], [0.053, -0.06], [0.07, 0.015], [0.09, 0]]);
      const sy = 1 - 0.18 * q, sx = 1 / sy;
      this.place(el, MDOT.x, MDOT.y + D / 2 - (D * sy) / 2, D * sx, D * sy, 0);
    },
  });
})();
