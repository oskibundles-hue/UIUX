// s05-energy — Energy: breath, drop, chaos into RANGE.   7.03125 → 9.375 s (frames 422–562), z 50, root Ink.
//
// Everything is drawn into one opaque full-frame canvas as a pure function of t:
//   BREATH 7.03125–7.5     the Ø56 dot compresses to Ø26 (inCubic) with a growing 40 Hz tremble while a Signal
//                          ring implodes onto it (inQuart), trailed by three Fog echoes at 1-frame delays.
//   DROP   7.5–8.4375      12,000 particles detonate out of the Ø26 dot (R.sim, 120 Hz): radial launch with
//                          drag, curl-noise advection (R.noise3 potential sampled on a coarse grid) and two
//                          counter-rotating vortices; a +600 px/s radial impulse on beat 2; a Paper shockwave.
//   RANGE  8.4375–9.1406   particles are paired with a 5 px dot-matrix of "RANGE" by angle rank and spring onto
//                          it (SOFT shape, time-compressed) from their cached state, then settle over 4 frames
//                          into 3×3 Paper squares; the spare particles keep orbiting as a 0.3 haze.
//   WHIP   9.1406–9.375    the whole layer rides the shared whip P(t) (x = −P) with a horizontal smear.
(function () {
  'use strict';

  // ------------------------------------------------------------------ timing (global seconds)
  const T_IN = 7.03125; //        4.4.1  lights out
  const T_RING = 7.44140625; //   ring lands, one 32nd before the drop
  const T_DROP = 7.5; //          5.1.1
  const T_KICK = 7.96875; //      5.2.1  second impulse
  const T_SNAP = 8.4375; //       5.3.1  order from chaos
  const T_WHIP = 9.140625; //     5.4.3  and-of-4
  const T_OUT = 9.375; //         6.1.1
  const WHIP_DUR = T_OUT - T_WHIP;

  const W = R.W, H = R.H, CX = 960, CY = 540;
  const PAL = R.pal;

  // ------------------------------------------------------------------ breath
  const DOT_R0 = 28, DOT_R1 = 13; //  Ø56 → Ø26
  const RING_R0 = 700; //             Ø1400
  const ECHO_ALPHA = [0.5, 0.35, 0.2];

  // ------------------------------------------------------------------ tunables (dev: window.__S05 overrides)
  const C = Object.assign({
    V_MIN: 700, V_MAX: 2800, V_MEAN: 480, // truncated exponential launch speeds (px/s)
    SLOW_FRAC: 0.2, SLOW_MIN: 0, //         slow embers (0–700 px/s) so the core is hot, not hollow
    SWIRL: 0.12, DRAG: 2.2, KICK_V: 600,
    CURL_V: 220, CURL_SCALE: 0.0022, CURL_TIME: 0.35,
    VORTEX_V: 1000, VORTEX_FALL: 400, VORTEX_CORE: 56, VORTEX_SINK: 0.4, JET: 1,
    FIELD_RAMP: 0.22,
    A_SIGNAL: [0.72, 0.86, 1], A_PAPER: [0.3, 0.4, 0.55], A_VOLT: [0.4, 0.55, 0.7], A_ACID: [1, 1, 1],
    SIGNAL_TOP: 1, // Signal drawn over the additive sparks: the burst stays hot orange, not white
    STREAK_MAX: 110, STREAK_MAX_SNAP: 130,
    SPRING_K: 3.4, DELAY_MAX: 0.06, LAND_STEPS: 8,
    HAZE_ALPHA: 0.3, HAZE_FADE: 0.15, HAZE_SINK: 1.0, HAZE_DRAG: 4, HAZE_RANDOM: 0.2,
    LAND_MIX: [0.6, 0.85, 1, 1], LAND_W: 2,
    JITTER_T: 0.8, // |noise| above this shifts a square by 1 px
    SHUTTER: 0.5,
    SPEED_LV: [380, 1000], SPEED_A: [0.45, 0.72, 1], // speed thresholds (px/s) and brightness per level
    SELECT: 'near', SELECT_NOISE: 60,
    SNAP_SWIRL: 1.2, FLIGHT_A: [1, 0.85, 0.35, 0.35],
  }, (typeof window !== 'undefined' && window.__S05) || {});

  // ------------------------------------------------------------------ particles
  const N = 12000;
  const DT = 1 / 120;
  const DRAG_F = Math.exp(-C.DRAG * DT);
  const KICK_T = T_KICK - T_DROP;
  const SNAP_L = T_SNAP - T_DROP;
  const CURL_NORM = 3.64; // p90 of |grad noise3|, measured in this Chromium
  // JET +1: the left vortex turns clockwise on screen, the right one counter-clockwise, so the jet between
  // them runs downward and the cloud rolls up into two horns (the cross-section of a vortex ring).
  const VORTICES = [[640, 540, C.JET], [1280, 540, -C.JET]];

  // colour groups: 64% Signal, 22% Paper, 11% Volt, 3% Acid
  const G_SIGNAL = 0, G_PAPER = 1, G_VOLT = 2, G_ACID = 3;
  const GROUP_COUNT = [7680, 2640, 1320, 360];
  const WIDTHS = [1.5, 2.25, 3];

  // streaks: length |v|/60 × 1.5 (min 1.5 px)
  const STREAK_K = 1.5 / 60, STREAK_MIN = 1.5;

  // RANGE snap
  const ASSIGN_STEP = Math.floor((T_SNAP - T_DROP) / DT); // 112: the last sim step before the beat
  const LAND_STEPS = C.LAND_STEPS;
  const JITTER_HZ = 12;

  // whip: s05 content x = −P(t); the smear is a 180° shutter (|P'|/60 × 0.5, ≈205 px at the peak)
  const SHUTTER = C.SHUTTER;
  const whipU = (t) => R.clamp((t - T_WHIP) / WHIP_DUR);
  const whipP = (t) => 1920 * R.ease.inOutCubic(whipU(t));
  const whipV = (t) => {
    const u = whipU(t);
    if (u <= 0 || u >= 1) return 0;
    return (1920 * (u < 0.5 ? 12 * u * u : 3 * (2 - 2 * u) * (2 - 2 * u))) / WHIP_DUR;
  };

  // ------------------------------------------------------------------ curl-noise grid (pure function of the sim step)
  const GH = 48, GX0 = -960, GY0 = -1080, GNX = 81, GNY = 69; // x −960→2880, y −1080→2184
  const psi = new Float32Array(GNX * GNY);
  const gvx = new Float32Array(GNX * GNY);
  const gvy = new Float32Array(GNX * GNY);
  let gridStamp = -1;
  function updateCurlGrid(stepIdx) {
    const q = stepIdx >> 2; // refreshed at 30 Hz: the potential drifts slowly (time scale 0.35)
    if (q === gridStamp) return;
    gridStamp = q;
    const z = 11.7 + q * 4 * DT * C.CURL_TIME;
    for (let j = 0; j < GNY; j++) {
      const ny = (GY0 + j * GH) * C.CURL_SCALE;
      for (let i = 0; i < GNX; i++) psi[j * GNX + i] = R.noise3((GX0 + i * GH) * C.CURL_SCALE + 3.1, ny, z);
    }
    // v = (∂ψ/∂y, −∂ψ/∂x): divergence-free, so the particles swirl without clumping
    const k = C.CURL_V / CURL_NORM / (2 * GH * C.CURL_SCALE);
    for (let j = 0; j < GNY; j++) {
      const jm = j > 0 ? j - 1 : j, jp = j < GNY - 1 ? j + 1 : j;
      for (let i = 0; i < GNX; i++) {
        const im = i > 0 ? i - 1 : i, ip = i < GNX - 1 ? i + 1 : i;
        const o = j * GNX + i;
        gvx[o] = (k * (psi[jp * GNX + i] - psi[jm * GNX + i]) * 2) / (jp - jm);
        gvy[o] = (-k * (psi[j * GNX + ip] - psi[j * GNX + im]) * 2) / (ip - im);
      }
    }
  }

  // vortex speed / distance, tabulated every 2 px (Rankine-like core so the centre is calm)
  const VLUT_STEP = 2, VLUT_N = 1800;
  const VLUT = new Float32Array(VLUT_N + 1);
  for (let k = 0; k <= VLUT_N; k++) {
    const d = Math.max(k * VLUT_STEP, 1e-3);
    VLUT[k] = (C.VORTEX_V * Math.exp(-d / C.VORTEX_FALL) * (1 - Math.exp(-(d / C.VORTEX_CORE) * (d / C.VORTEX_CORE)))) / d;
  }

  // spring tables, indexed by sim steps since the particle's spring started
  const SP_N = 160;
  const SP_A = new Float64Array(SP_N), SP_B = new Float64Array(SP_N), SP_DA = new Float64Array(SP_N), SP_DB = new Float64Array(SP_N);
  const SP_C = new Float64Array(SP_N), SP_S = new Float64Array(SP_N); // swirl: the displacement turns by θ·(1 − A)
  const TRX = new Float64Array(4), TRY = new Float64Array(4); //         scratch trail points
  let LAND_AT = 0; // first step where the spring progress passes 0.95
  (function springTables() {
    const w0 = Math.sqrt(180) * C.SPRING_K;
    const zeta = 16 / (2 * Math.sqrt(180));
    const wd = w0 * Math.sqrt(1 - zeta * zeta), a = zeta * w0;
    for (let k = 0; k < SP_N; k++) {
      const tau = k * DT, e = Math.exp(-a * tau), c = Math.cos(wd * tau), s = Math.sin(wd * tau);
      SP_A[k] = e * (c + (a / wd) * s); //     displacement kept from x0
      SP_B[k] = (e * s) / wd; //               displacement from v0
      SP_DA[k] = (-e * (w0 * w0) * s) / wd; // d/dτ
      SP_DB[k] = e * (c - (a / wd) * s);
      if (!LAND_AT && 1 - SP_A[k] >= 0.95) LAND_AT = k;
      SP_C[k] = Math.cos(C.SNAP_SWIRL * (1 - SP_A[k]));
      SP_S[k] = Math.sin(C.SNAP_SWIRL * (1 - SP_A[k]));
    }
  })();

  const outCubic = R.ease.outCubic;

  R.scene({
    id: 's05-energy',
    start: T_IN,
    end: T_OUT,
    z: 50,
    bg: PAL.ink,

    setup(root) {
      // ---- global FX (engine) + picture-locked sound
      R.cue(7.03125, 'grain', { amt: 0.04, dur: 0.46875 }); //                                      breath texture
      R.cue(7.03125, 'letterbox', { amt: 110, dur: 0.46875, in: 0.1, out: 0.05 }); //               bars in on lights-out, gone at 7.5
      R.cue(7.03125, 'vignette', { amt: 0.6, dur: 0.46875, in: 0.1, out: 0.03 }); //                breath darkness
      R.cue(7.5, 'chroma', { amt: 12, dur: 0.3 }); //                                               drop
      R.cue(7.5, 'flash', { amt: 1.0, dur: 0.1, color: '#FFFFFF' }); //                             THE DROP (white)
      R.cue(7.5, 'shake', { amt: 18, dur: 0.45 }); //                                               drop
      R.cue(7.5, 'zoom', { amt: 0.08, dur: 0.3 }); //                                               drop
      R.cue(7.96875, 'shake', { amt: 5, dur: 0.15 }); //                                            second particle impulse
      R.cue(7.96875, 'zoom', { amt: 0.03, dur: 0.15 }); //                                          second particle impulse
      R.cue(8.4375, 'flash', { amt: 0.3, dur: 0.08, color: '#FF4A1C' }); //                         particles snap into RANGE
      R.cue(8.4375, 'shake', { amt: 6, dur: 0.15 }); //                                             RANGE snap
      R.cue(9.140625, 'chroma', { amt: 14, dur: 0.234375, angle: 0 }); //                           whip smear, horizontal split

      R.sfx(7.03125, 'tapestop', { dur: 0.18 }); //                  lights out
      R.sfx(7.03125, 'reverse', { dur: 0.46875 }); //                swell into the drop
      R.sfx(7.5, 'impact', { amt: 1.2, tone: 'huge' }); //           THE DROP
      R.sfx(7.5, 'subdrop', { amt: 1.0 }); //                        drop
      R.sfx(7.5, 'shimmer', { dur: 0.9375, amt: 0.6 }); //           particle glitter
      R.sfx(7.96875, 'impact', { amt: 0.5 }); //                     second impulse
      R.sfx(8.3203125, 'reverse', { dur: 0.1171875 }); //            zip into the snap
      R.sfx(8.4375, 'impact', { amt: 0.45 }); //                     RANGE snap
      R.sfx(8.4375, 'shimmer', { dur: 0.46875, amt: 0.4 }); //       snap sparkle
      R.sfx(9.140625, 'whoosh', { dur: 0.234375, dir: 'down' }); //  whip R→L

      const { ctx } = R.canvas(root, { alpha: false });
      this.ctx = ctx;

      // ---- RANGE dot-matrix targets (5 px cells, ink x 200→1720, cap centred on y 540)
      const T = sampleRange();
      this.TX = T.x; this.TY = T.y; this.NT = T.n; this.TSORT = T.sorted; this.JX = T.jx; this.JY = T.jy;

      // ---- per-particle constants (seeded)
      const rnd = R.rand(505);
      const grp = new Uint8Array(N);
      for (let g = 0, i = 0; g < 4; g++) for (let c = 0; c < GROUP_COUNT[g]; c++) grp[i++] = g;
      for (let i = N - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); const tmp = grp[i]; grp[i] = grp[j]; grp[j] = tmp; }
      const wb = new Uint8Array(N);
      const lx = new Float32Array(N), ly = new Float32Array(N), lvx = new Float32Array(N), lvy = new Float32Array(N);
      const vspan = 1 - Math.exp(-(C.V_MAX - C.V_MIN) / C.V_MEAN);
      for (let i = 0; i < N; i++) {
        wb[i] = Math.min(2, Math.floor(rnd() * 3));
        const a = rnd() * R.TAU, r = DOT_R1 * Math.sqrt(rnd());
        const u = rnd(), slow = rnd() < C.SLOW_FRAC;
        const sp = slow ? R.lerp(C.SLOW_MIN, C.V_MIN, u) : C.V_MIN - C.V_MEAN * Math.log(1 - u * vspan);
        const ca = Math.cos(a), sa = Math.sin(a);
        const sw = C.SWIRL * ca * -C.JET; // swirl sense follows the vortex on that side, zero at 12 and 6 o'clock
        lx[i] = CX + ca * r; ly[i] = CY + sa * r;
        lvx[i] = sp * (ca - sw * sa); lvy[i] = sp * (sa + sw * ca);
      }
      this.grp = grp; this.wb = wb;

      // Particles that become letters: every Paper and Acid one, then Signal ones. The spares
      // (remaining Signal + all Volt) stay behind as the haze.
      const list = [];
      for (const g of [G_PAPER, G_ACID, G_SIGNAL]) for (let i = 0; i < N && list.length < T.n; i++) if (grp[i] === g) list.push(i);
      const assignList = Int32Array.from(list);
      const NT = T.n, TX = T.x, TY = T.y, TSORT = T.sorted;

      const init = () => ({
        x: Float32Array.from(lx), y: Float32Array.from(ly),
        vx: Float32Array.from(lvx), vy: Float32Array.from(lvy),
        fx: Float32Array.from(lvx), fy: Float32Array.from(lvy),
        tgt: new Int32Array(N).fill(-1),
        sStep: new Int32Array(N).fill(-1),
        sx: new Float32Array(N), sy: new Float32Array(N), svx: new Float32Array(N), svy: new Float32Array(N),
        assigned: false,
      });

      const assign = (S) => {
        // Which particles become letters: the M closest to the word's band (plus a little seeded noise so the
        // selection has no hard contour); the rest stay behind as the haze. Then pair particles and targets by
        // angle rank around the centre, so the paths swirl coherently and never cross.
        let idx = assignList;
        if (C.SELECT === 'near') {
          const cost = new Float64Array(N);
          for (let i = 0; i < N; i++) {
            const dx = S.x[i] < 200 ? 200 - S.x[i] : S.x[i] > 1720 ? S.x[i] - 1720 : 0;
            const dy = S.y[i] < 428 ? 428 - S.y[i] : S.y[i] > 652 ? S.y[i] - 652 : 0;
            cost[i] = Math.sqrt(dx * dx + dy * dy) + R.hash(i, 404) * C.SELECT_NOISE + (R.hash(i, 405) < C.HAZE_RANDOM ? 1e6 : 0);
          }
          const all = Array.from({ length: N }, (_, i) => i).sort((a, b) => cost[a] - cost[b] || a - b);
          idx = Int32Array.from(all.slice(0, NT));
        }
        const M = idx.length;
        const ang = new Float64Array(M);
        for (let k = 0; k < M; k++) { const i = idx[k]; ang[k] = Math.atan2(S.y[i] - CY, S.x[i] - CX); }
        const order = Array.from({ length: M }, (_, k) => k).sort((a, b) => ang[a] - ang[b] || a - b);
        const dist = new Float64Array(M);
        for (let r = 0; r < M; r++) {
          const i = idx[order[r]], ti = TSORT[r];
          S.tgt[i] = ti;
          dist[r] = Math.hypot(TX[ti] - S.x[i], TY[ti] - S.y[i]);
        }
        const sorted = Float64Array.from(dist).sort();
        const dref = Math.max(1, sorted[Math.floor(0.9 * (M - 1))]);
        for (let r = 0; r < M; r++) {
          const i = idx[order[r]];
          S.sStep[i] = ASSIGN_STEP + Math.round((Math.min(1, dist[r] / dref) * C.DELAY_MAX) / DT);
        }
        S.assigned = true;
      };

      const step = (S, st, dt) => {
        const si = Math.round(st / dt);
        updateCurlGrid(si);
        if (si === ASSIGN_STEP && !S.assigned) assign(S);
        const kick = st < KICK_T - 1e-9 && st + dt >= KICK_T - 1e-9;
        const field = R.smoothstep(0, C.FIELD_RAMP, st);
        // after the snap the spares spiral in toward the two cores and settle into orbit behind the letters
        const post = R.smoothstep(SNAP_L, SNAP_L + 0.25, st);
        const sink = R.lerp(C.VORTEX_SINK, C.HAZE_SINK, post);
        const dragF = post > 0 ? Math.exp(-R.lerp(C.DRAG, C.HAZE_DRAG, post) * dt) : DRAG_F;
        const { x, y, vx, vy, fx, fy, sStep } = S;
        const v0x = VORTICES[0][0], v0y = VORTICES[0][1], v0s = VORTICES[0][2];
        const v1x = VORTICES[1][0], v1y = VORTICES[1][1], v1s = VORTICES[1][2];
        for (let i = 0; i < N; i++) {
          const ss = sStep[i];
          if (ss >= 0 && si >= ss) {
            if (si === ss) { S.sx[i] = x[i]; S.sy[i] = y[i]; S.svx[i] = fx[i]; S.svy[i] = fy[i]; }
            continue; // analytic spring from here on
          }
          const px = x[i], py = y[i];
          let bx = vx[i] * dragF, by = vy[i] * dragF;
          if (kick) {
            const dx = px - CX, dy = py - CY, d = Math.sqrt(dx * dx + dy * dy) || 1;
            bx += (C.KICK_V * dx) / d; by += (C.KICK_V * dy) / d;
          }
          vx[i] = bx; vy[i] = by;
          // curl noise (bilinear on the grid)
          let gx = (px - GX0) / GH, gy = (py - GY0) / GH;
          gx = gx < 0 ? 0 : gx > GNX - 1.001 ? GNX - 1.001 : gx;
          gy = gy < 0 ? 0 : gy > GNY - 1.001 ? GNY - 1.001 : gy;
          const ix = gx | 0, iy = gy | 0, ux = gx - ix, uy = gy - iy, o = iy * GNX + ix;
          const cx0 = gvx[o] + (gvx[o + 1] - gvx[o]) * ux, cx1 = gvx[o + GNX] + (gvx[o + GNX + 1] - gvx[o + GNX]) * ux;
          const cy0 = gvy[o] + (gvy[o + 1] - gvy[o]) * ux, cy1 = gvy[o + GNX] + (gvy[o + GNX + 1] - gvy[o + GNX]) * ux;
          let ax = cx0 + (cx1 - cx0) * uy, ay = cy0 + (cy1 - cy0) * uy;
          // two counter-rotating vortices
          let dx = px - v0x, dy = py - v0y, d = Math.sqrt(dx * dx + dy * dy), k = d * (1 / VLUT_STEP);
          let s = k < VLUT_N ? VLUT[k | 0] : 0;
          ax += (-dy * v0s - dx * sink) * s; ay += (dx * v0s - dy * sink) * s;
          dx = px - v1x; dy = py - v1y; d = Math.sqrt(dx * dx + dy * dy); k = d * (1 / VLUT_STEP);
          s = k < VLUT_N ? VLUT[k | 0] : 0;
          ax += (-dy * v1s - dx * sink) * s; ay += (dx * v1s - dy * sink) * s;
          const tvx = bx + ax * field, tvy = by + ay * field;
          fx[i] = tvx; fy[i] = tvy;
          x[i] = px + tvx * dt; y[i] = py + tvy * dt;
        }
      };

      this.sim = R.sim({ dt: DT, init, step });

      // ---- batch styles
      // free/spring streaks: group × width; thinner = dimmer (reads as depth). Paper & Volt are additive.
      const alphas = [C.A_SIGNAL, C.A_PAPER, C.A_VOLT, C.A_ACID];
      this.freeStyle = [];
      for (let g = 0; g < 4; g++) for (let w = 0; w < 3; w++) {
        const lighter = g === G_PAPER || g === G_VOLT;
        this.freeStyle.push({ g, w, lighter, a: alphas[g][w], col: [PAL.signal, PAL.paper, PAL.volt, PAL.acid][g] });
      }
      // landing: colour cools to Paper over 4 frames
      this.landCol = [];
      // (Volt and Acid heat through Signal: the letters form from fire, not from a pastel rainbow)
      for (let g = 0; g < 4; g++) for (let b = 0; b < 4; b++) this.landCol.push(R.mixColor(g === G_PAPER ? PAL.paper : PAL.signal, PAL.paper, C.LAND_MIX[b]));
    },

    update(lt, p, t) {
      const ctx = this.ctx;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalCompositeOperation = 'source-over';
      ctx.globalAlpha = 1;
      ctx.fillStyle = PAL.ink;
      ctx.fillRect(0, 0, W, H);
      if (t < T_DROP) this.drawBreath(ctx, t);
      else this.drawEnergy(ctx, t);
    },

    // ---------------------------------------------------------------- BREATH
    drawBreath(ctx, t) {
      const kIn = R.clamp((t - T_IN) / (T_RING - T_IN));
      // imploding ring + echoes (hidden once they land on the dot)
      const ringR = (tt) => RING_R0 + (DOT_R1 - RING_R0) * R.ease.inQuart(R.clamp((tt - T_IN) / (T_RING - T_IN)));
      ctx.lineCap = 'butt';
      for (let j = 3; j >= 1; j--) {
        const tt = t - j / 60;
        if (tt >= T_RING) continue;
        ctx.beginPath();
        ctx.arc(CX, CY, ringR(tt), 0, R.TAU);
        ctx.lineWidth = 1;
        ctx.strokeStyle = R.rgba(PAL.fog, ECHO_ALPHA[j - 1]);
        ctx.stroke();
      }
      if (t < T_RING) {
        ctx.beginPath();
        ctx.arc(CX, CY, ringR(t), 0, R.TAU);
        ctx.lineWidth = 2;
        ctx.strokeStyle = PAL.signal;
        ctx.stroke();
      }
      // the dot: compresses (inCubic) and trembles harder as the drop approaches
      const r = DOT_R0 + (DOT_R1 - DOT_R0) * R.ease.inCubic(kIn);
      const kb = R.clamp((t - T_IN) / (T_DROP - T_IN));
      const amp = t < T_RING ? 2.4 * kb * kb : 3;
      const ox = R.wiggle(t, 40, amp, 5), oy = R.wiggle(t, 40, amp, 9);
      ctx.beginPath();
      ctx.arc(CX + ox, CY + oy, r, 0, R.TAU);
      ctx.fillStyle = PAL.signal;
      ctx.fill();
    },

    // ---------------------------------------------------------------- DROP → RANGE → WHIP
    drawEnergy(ctx, t) {
      const S = this.sim(t - T_DROP);
      const cur = Math.round((t - T_DROP) / DT);
      const Pw = whipP(t);
      const smear = (whipV(t) * SHUTTER) / 60;
      ctx.setTransform(1, 0, 0, 1, -Pw, 0);

      const grp = this.grp, wb = this.wb, TX = this.TX, TY = this.TY;
      const { x, y, fx, fy, tgt, sStep, sx, sy, svx, svy } = S;
      const assigned = S.assigned;
      // visible window in layer coordinates (s06 covers everything right of 1920 − P on screen)
      const vx0 = Pw - 240, vx1 = W + 240, vy0 = -240, vy1 = H + 240;

      // batches: (group × width) × speed level; brightness follows speed, so energy reads where the motion is
      const free = [], spare = [], land = [];
      for (let b = 0; b < 36; b++) { free.push(new Path2D()); spare.push(new Path2D()); }
      const S1 = C.SPEED_LV[0] * C.SPEED_LV[0], S2 = C.SPEED_LV[1] * C.SPEED_LV[1];
      for (let b = 0; b < 16; b++) land.push(new Path2D());
      const flight = [];
      for (let b = 0; b < 12; b++) flight.push(new Path2D());
      const squares = new Path2D();
      let nSquares = 0;
      const jt = t * JITTER_HZ;
      const JX = this.JX, JY = this.JY;
      const maxLen = t >= T_SNAP ? C.STREAK_MAX_SNAP : C.STREAK_MAX;

      for (let i = 0; i < N; i++) {
        const ss = sStep[i];
        let hx, hy, dvx, dvy, path;
        if (ss < 0 || cur <= ss) {
          // free (at k = 0 the spring state equals the sim state; the snapshot is taken as the sim passes ss)
          hx = x[i]; hy = y[i]; dvx = fx[i]; dvy = fy[i];
          const v2 = dvx * dvx + dvy * dvy;
          path = (assigned && tgt[i] < 0 ? spare : free)[(grp[i] * 3 + wb[i]) * 3 + (v2 < S1 ? 0 : v2 < S2 ? 1 : 2)];
        } else {
          const ti = tgt[i], tx = TX[ti], ty = TY[ti];
          const k = cur - ss;
          if (k >= LAND_AT + LAND_STEPS) {
            // locked: a crisp 3×3 Paper square on the whole-pixel lattice, ±1 px live jitter
            const nx = R.noise2(JX[ti], jt), ny = R.noise2(JY[ti], jt);
            const jx = nx > C.JITTER_T ? 1 : nx < -C.JITTER_T ? -1 : 0, jy = ny > C.JITTER_T ? 1 : ny < -C.JITTER_T ? -1 : 0;
            squares.rect(tx - 1 + jx, ty - 1 + jy, 3 + smear, 3);
            nSquares++;
            continue;
          }
          // spring flight / landing: the displacement from the target shrinks on the spring while it turns in
          // the sense of that side's vortex, so the paths swirl into the letters; drawn as a curved trail
          // through the last 1.5 frames (3 sim steps) of the analytic path.
          const X0 = sx[i] - tx, Y0 = sy[i] - ty, V0x = svx[i], V0y = svy[i];
          const sg = tx < CX ? C.JET : -C.JET;
          const landing = k >= LAND_AT;
          const pa = landing ? land[grp[i] * 4 + Math.min(3, Math.floor(((k - LAND_AT) / LAND_STEPS) * 4))] : flight[grp[i] * 3 + wb[i]];
          let n = 0;
          for (let kk = k; kk >= k - 3 && kk >= 0; kk--) {
            const a = SP_A[kk], b = SP_B[kk], c = SP_C[kk], sn = SP_S[kk] * sg;
            let px = tx + (X0 * c - Y0 * sn) * a + V0x * b, py = ty + (X0 * sn + Y0 * c) * a + V0y * b;
            if (kk >= LAND_AT) { const e = outCubic(Math.min(1, (kk - LAND_AT) / LAND_STEPS)); px += (tx - px) * e; py += (ty - py) * e; }
            TRX[n] = px; TRY[n] = py; n++;
          }
          if (TRX[0] < vx0 && TRX[n - 1] < vx0) continue;
          // cap the trail length (from the head back), keep a 1.5 px minimum
          let len = 0, m = 1;
          for (; m < n; m++) {
            const dx = TRX[m] - TRX[m - 1], dy = TRY[m] - TRY[m - 1], d = Math.sqrt(dx * dx + dy * dy);
            if (len + d > C.STREAK_MAX_SNAP) { const f = (C.STREAK_MAX_SNAP - len) / d; TRX[m] = TRX[m - 1] + dx * f; TRY[m] = TRY[m - 1] + dy * f; len = C.STREAK_MAX_SNAP; m++; break; }
            len += d;
          }
          if (len < STREAK_MIN) {
            const dx = n > 1 ? TRX[0] - TRX[1] : 1, dy = n > 1 ? TRY[0] - TRY[1] : 0, d = Math.sqrt(dx * dx + dy * dy);
            const ux = d > 1e-4 ? dx / d : 1, uy = d > 1e-4 ? dy / d : 0;
            pa.moveTo(TRX[0] - ux * STREAK_MIN, TRY[0] - uy * STREAK_MIN);
            pa.lineTo(TRX[0], TRY[0]);
          } else {
            pa.moveTo(TRX[m - 1], TRY[m - 1]);
            for (let q = m - 2; q >= 0; q--) pa.lineTo(TRX[q], TRY[q]);
          }
          continue;
        }
        // velocity-aligned streak: head at the particle, tail along −v, plus the whip smear
        let ex = dvx * STREAK_K, ey = dvy * STREAK_K;
        let L = Math.sqrt(ex * ex + ey * ey);
        if (L > maxLen) { const s = maxLen / L; ex *= s; ey *= s; }
        else if (L < STREAK_MIN) {
          if (L > 1e-4) { const s = STREAK_MIN / L; ex *= s; ey *= s; } else { ex = STREAK_MIN; ey = 0; }
        }
        const tx0 = hx - ex + smear, ty0 = hy - ey;
        if ((hx < vx0 && tx0 < vx0) || (hx > vx1 && tx0 > vx1) || (hy < vy0 && ty0 < vy0) || (hy > vy1 && ty0 > vy1)) continue;
        path.moveTo(tx0, ty0);
        path.lineTo(hx, hy);
      }

      // haze fades to 0.3 after the snap
      const haze = R.seg(t, T_SNAP, T_SNAP + C.HAZE_FADE, 'outQuad');
      ctx.lineCap = 'round';
      // source-over groups first (Signal, Acid), then the additive ones (Paper, Volt)
      for (const pass of C.SIGNAL_TOP ? [true, false] : [false, true]) {
        ctx.globalCompositeOperation = pass ? 'lighter' : 'source-over';
        for (let b = 0; b < 36; b++) {
          const st = this.freeStyle[(b / 3) | 0];
          if (st.lighter !== pass) continue;
          const a = st.a * C.SPEED_A[b % 3];
          ctx.lineWidth = WIDTHS[st.w];
          ctx.strokeStyle = R.rgba(st.col, a);
          ctx.stroke(free[b]);
          ctx.strokeStyle = R.rgba(st.col, R.lerp(a, C.HAZE_ALPHA, haze));
          ctx.stroke(spare[b]);
        }
      }
      ctx.globalCompositeOperation = 'source-over';
      for (let b = 0; b < 12; b++) {
        const g = (b / 3) | 0;
        ctx.lineWidth = WIDTHS[b % 3];
        ctx.strokeStyle = R.rgba([PAL.signal, PAL.paper, PAL.volt, PAL.acid][g], C.FLIGHT_A[g]);
        ctx.stroke(flight[b]);
      }
      ctx.lineWidth = C.LAND_W;
      for (let b = 0; b < 16; b++) {
        ctx.strokeStyle = this.landCol[b];
        ctx.stroke(land[b]);
      }
      if (nSquares) {
        ctx.fillStyle = PAL.paper;
        ctx.fill(squares);
      }

      // Paper shockwave: r 0 → 1500 (outQuart, 0.35 s), alpha 1 → 0
      const ks = (t - T_DROP) / 0.35;
      if (ks > 0 && ks < 1) {
        ctx.beginPath();
        ctx.arc(CX, CY, 1500 * R.ease.outQuart(ks), 0, R.TAU);
        ctx.lineWidth = 3;
        ctx.strokeStyle = R.rgba(PAL.paper, 1 - ks);
        ctx.stroke();
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    },
  });

  // ------------------------------------------------------------------ RANGE target lattice
  // Archivo 900 at canvas width "expanded", size solved so the ink spans x 200→1720 (1520 px) with the flat
  // cap (0.6875 em) centred on y 540. Cells are 5×5 px anchored at x 200 / the cap top; a cell becomes a target
  // when the glyph covers ≥ 50% of it. Target = the cell's centre pixel, so a 3×3 square sits inside with a
  // 1 px margin on every side: a true dot-matrix on the whole-pixel lattice.
  function sampleRange() {
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    const g = c.getContext('2d', { willReadFrequently: true });
    const setFont = (px) => { g.font = `normal 900 ${px}px ${R.font.display}`; g.fontStretch = 'expanded'; };
    const inkBox = (px, x, base) => {
      g.clearRect(0, 0, W, H);
      setFont(px);
      g.textAlign = 'left'; g.textBaseline = 'alphabetic'; g.fillStyle = '#fff';
      g.fillText('RANGE', x, base);
      const d = g.getImageData(0, 0, W, H).data;
      let x0 = W, x1 = -1;
      for (let yy = 300; yy < 800; yy++) for (let xx = 0; xx < W; xx++) if (d[(yy * W + xx) * 4 + 3] > 127) { if (xx < x0) x0 = xx; if (xx > x1) x1 = xx; }
      return { x0, x1: x1 + 1, d };
    };
    let size = 326;
    for (let it = 0; it < 3; it++) {
      const b = inkBox(size, 100, 640);
      size *= 1520 / (b.x1 - b.x0);
    }
    const cap = 0.6875 * size;
    const base = CY + cap / 2;
    const probe = inkBox(size, 100, base);
    const x = 100 + (200 - probe.x0);
    const { d } = inkBox(size, x, base);
    const capTop = Math.round(base - cap);
    const X0 = 200, Y0 = capTop - 5;
    const cols = Math.ceil(1520 / 5) + 1, rows = Math.ceil((cap + 10) / 5) + 1;
    const xs = [], ys = [];
    for (let r = 0; r < rows; r++) {
      for (let q = 0; q < cols; q++) {
        let a = 0;
        const cx0 = X0 + q * 5, cy0 = Y0 + r * 5;
        for (let yy = cy0; yy < cy0 + 5; yy++) for (let xx = cx0; xx < cx0 + 5; xx++) a += d[(yy * W + xx) * 4 + 3];
        if (a >= 0.5 * 25 * 255) { xs.push(cx0 + 2); ys.push(cy0 + 2); }
      }
    }
    const n = xs.length;
    const tx = Float32Array.from(xs), ty = Float32Array.from(ys);
    const ang = new Float64Array(n);
    for (let i = 0; i < n; i++) ang[i] = Math.atan2(ty[i] - CY, tx[i] - CX);
    const sorted = Int32Array.from(Array.from({ length: n }, (_, i) => i).sort((a, b) => ang[a] - ang[b] || a - b));
    const jx = new Float32Array(n), jy = new Float32Array(n);
    for (let i = 0; i < n; i++) { jx[i] = 37.1 + R.hash(i, 11) * 900; jy[i] = 511.3 + R.hash(i, 23) * 900; }
    return { x: tx, y: ty, n, sorted, jx, jy, size, base, capTop };
  }
})();
