/*
 * Showreel engine — a tiny, deterministic motion-graphics runtime.
 *
 * Everything on screen is a pure function of time `t` (seconds). The renderer seeks
 * to t = frame / FPS, calls R.render(t) and screenshots the page, so scenes must never
 * read the wall clock (Date.now, performance.now) or Math.random — use R.rand / R.hash /
 * R.noise and R.sim for anything stochastic or simulated.
 *
 * Scene modules register themselves with R.scene({...}) — see README.md for the contract.
 */
(function () {
  'use strict';

  const R = (window.R = {});

  // ---------------------------------------------------------------------------
  // Timing + musical grid (128 BPM, 4/4, 8 bars = 15 s)
  // ---------------------------------------------------------------------------
  R.W = 1920;
  R.H = 1080;
  R.FPS = 60;
  R.DUR = 15;
  R.FRAMES = R.FPS * R.DUR;
  R.BPM = 128;
  R.BEAT = 60 / R.BPM; // 0.46875
  R.BAR = R.BEAT * 4; // 1.875
  R.E8 = R.BEAT / 2; // 0.234375
  R.E16 = R.BEAT / 4; // 0.1171875

  /** Global beat index (0-based) -> seconds. R.beat(4) === start of bar 2. */
  R.beat = (n) => n * R.BEAT;
  /** Bar number (1-based) -> seconds. R.bar(2) === 1.875. */
  R.bar = (n) => (n - 1) * R.BAR;
  /** Musical position -> seconds. R.pos(bar 1-based, beat 1-based, sixteenth 0-based). */
  R.pos = (bar, beat = 1, sixteenth = 0) => (bar - 1) * R.BAR + (beat - 1) * R.BEAT + sixteenth * R.E16;
  /** Seconds -> {bar, beat, sixteenth} (1-based bar/beat, 0-based sixteenth). */
  R.musical = (t) => {
    const s = Math.floor(t / R.E16 + 1e-6);
    return { bar: Math.floor(s / 16) + 1, beat: (Math.floor(s / 4) % 4) + 1, sixteenth: s % 4 };
  };
  /** Quantize a time down to the nearest grid step (default: 16th). */
  R.quantize = (t, step = R.E16) => Math.floor(t / step + 1e-6) * step;
  /** Time since the most recent grid step (e.g. beat pulse envelopes). */
  R.since = (t, step = R.BEAT) => t - R.quantize(t, step);

  // ---------------------------------------------------------------------------
  // Art direction tokens (locked)
  // ---------------------------------------------------------------------------
  R.pal = {
    ink: '#0B0B0F',
    paper: '#F3F0EA',
    signal: '#FF4A1C',
    volt: '#2B59FF',
    acid: '#D7FF3A',
    graphite: '#1C1C22',
    fog: '#8A8A93',
  };
  R.font = {
    display: "'Archivo', sans-serif", // variable: wght 100–900, wdth 62–125 (CSS font-stretch 62%–125%)
    serif: "'Instrument Serif', serif", // 400 normal + italic
    mono: "'JetBrains Mono', monospace", // variable: wght 100–800
  };

  // ---------------------------------------------------------------------------
  // Math
  // ---------------------------------------------------------------------------
  R.TAU = Math.PI * 2;
  R.clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
  R.lerp = (a, b, t) => a + (b - a) * t;
  R.invLerp = (a, b, v) => (b === a ? 0 : (v - a) / (b - a));
  R.fract = (v) => v - Math.floor(v);
  R.mod = (a, n) => ((a % n) + n) % n;
  R.deg = (d) => (d * Math.PI) / 180;
  R.smoothstep = (a, b, v) => {
    const x = R.clamp((v - a) / (b - a));
    return x * x * (3 - 2 * x);
  };
  /** Eased 0..1 progress of t through the window [t0, t1]. */
  R.seg = (t, t0, t1, ease) => {
    const p = R.clamp((t - t0) / (t1 - t0));
    return ease ? R.easeFn(ease)(p) : p;
  };
  /** Map v from [a,b] to [c,d], clamped, optionally eased. */
  R.remap = (v, a, b, c, d, ease) => R.lerp(c, d, R.seg(v, a, b, ease));
  /** Quantize time to a lower frame rate for a stylised "on twos" look: R.stepped(t, 12). */
  R.stepped = (t, fps) => Math.floor(t * fps + 1e-6) / fps;

  // ---------------------------------------------------------------------------
  // Easing
  // ---------------------------------------------------------------------------
  function cubicBezier(x1, y1, x2, y2) {
    const ax = 3 * x1 - 3 * x2 + 1, bx = 3 * x2 - 6 * x1, cx = 3 * x1;
    const ay = 3 * y1 - 3 * y2 + 1, by = 3 * y2 - 6 * y1, cy = 3 * y1;
    const sx = (u) => ((ax * u + bx) * u + cx) * u;
    const sy = (u) => ((ay * u + by) * u + cy) * u;
    const dsx = (u) => (3 * ax * u + 2 * bx) * u + cx;
    return function (x) {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      let u = x;
      for (let i = 0; i < 8; i++) {
        const e = sx(u) - x;
        if (Math.abs(e) < 1e-6) return sy(u);
        const d = dsx(u);
        if (Math.abs(d) < 1e-6) break;
        u -= e / d;
      }
      let lo = 0, hi = 1;
      u = x;
      for (let i = 0; i < 30; i++) {
        const v = sx(u);
        if (Math.abs(v - x) < 1e-6) break;
        if (v < x) lo = u; else hi = u;
        u = (lo + hi) / 2;
      }
      return sy(u);
    };
  }
  R.cubicBezier = cubicBezier;

  const E = {};
  E.linear = (x) => x;
  E.inQuad = (x) => x * x;
  E.outQuad = (x) => 1 - (1 - x) * (1 - x);
  E.inOutQuad = (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
  E.inCubic = (x) => x * x * x;
  E.outCubic = (x) => 1 - Math.pow(1 - x, 3);
  E.inOutCubic = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  E.inQuart = (x) => x * x * x * x;
  E.outQuart = (x) => 1 - Math.pow(1 - x, 4);
  E.inOutQuart = (x) => (x < 0.5 ? 8 * x * x * x * x : 1 - Math.pow(-2 * x + 2, 4) / 2);
  E.inQuint = (x) => x * x * x * x * x;
  E.outQuint = (x) => 1 - Math.pow(1 - x, 5);
  E.inOutQuint = (x) => (x < 0.5 ? 16 * x * x * x * x * x : 1 - Math.pow(-2 * x + 2, 5) / 2);
  E.inExpo = (x) => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10));
  E.outExpo = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
  E.inOutExpo = (x) =>
    x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2;
  E.inCirc = (x) => 1 - Math.sqrt(1 - x * x);
  E.outCirc = (x) => Math.sqrt(1 - Math.pow(x - 1, 2));
  E.inOutCirc = (x) =>
    x < 0.5 ? (1 - Math.sqrt(1 - Math.pow(2 * x, 2))) / 2 : (Math.sqrt(1 - Math.pow(-2 * x + 2, 2)) + 1) / 2;
  E.inSine = (x) => 1 - Math.cos((x * Math.PI) / 2);
  E.outSine = (x) => Math.sin((x * Math.PI) / 2);
  E.inOutSine = (x) => -(Math.cos(Math.PI * x) - 1) / 2;
  const c1 = 1.70158, c2 = c1 * 1.525, c3 = c1 + 1;
  E.inBack = (x) => c3 * x * x * x - c1 * x * x;
  E.outBack = (x) => 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
  E.inOutBack = (x) =>
    x < 0.5
      ? (Math.pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2
      : (Math.pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2;
  E.outElastic = (x) =>
    x <= 0 ? 0 : x >= 1 ? 1 : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1;
  E.inElastic = (x) =>
    x <= 0 ? 0 : x >= 1 ? 1 : -Math.pow(2, 10 * x - 10) * Math.sin((x * 10 - 10.75) * ((2 * Math.PI) / 3));
  E.outBounce = (x) => {
    const n1 = 7.5625, d1 = 2.75;
    if (x < 1 / d1) return n1 * x * x;
    if (x < 2 / d1) return n1 * (x -= 1.5 / d1) * x + 0.75;
    if (x < 2.5 / d1) return n1 * (x -= 2.25 / d1) * x + 0.9375;
    return n1 * (x -= 2.625 / d1) * x + 0.984375;
  };
  E.inBounce = (x) => 1 - E.outBounce(1 - x);
  // House curves — the reel's shared easing language.
  E.snap = cubicBezier(0.85, 0, 0.15, 1); // aggressive in-out: hard accelerate, silky settle
  E.swift = cubicBezier(0.16, 1, 0.3, 1); // out-expo-like: fast launch, long glide
  E.whip = cubicBezier(0.7, 0, 0.84, 0); // in-expo-like: builds into a cut
  E.glide = cubicBezier(0.45, 0, 0.1, 1); // gentle in, long settle
  E.punch = cubicBezier(0.2, 1.6, 0.4, 1); // overshoot out (settles past 1 then back)
  E.anticipate = cubicBezier(0.6, -0.4, 0.4, 1); // dips below 0 first, then goes
  R.ease = E;
  /** Resolve an ease given as a function, a name ('outExpo') or a bezier array [x1,y1,x2,y2]. */
  R.easeFn = (e) => {
    if (!e) return E.linear;
    if (typeof e === 'function') return e;
    if (Array.isArray(e)) return cubicBezier(e[0], e[1], e[2], e[3]);
    const f = E[e];
    if (!f) throw new Error('Unknown ease: ' + e);
    return f;
  };

  /**
   * Analytic damped spring from 0 -> 1, starting at local time t = 0 (t in seconds).
   * stiffness/damping/mass as in popmotion/framer (170/26/1 = snappy, 120/14 = bouncy).
   */
  R.spring = (t, opts = {}) => {
    if (t <= 0) return 0;
    const k = opts.stiffness ?? 170, c = opts.damping ?? 26, m = opts.mass ?? 1;
    const v0 = -(opts.velocity ?? 0);
    const w0 = Math.sqrt(k / m);
    const zeta = c / (2 * Math.sqrt(k * m));
    const x0 = 1; // displacement from target
    if (zeta < 1) {
      const wd = w0 * Math.sqrt(1 - zeta * zeta);
      const env = Math.exp(-zeta * w0 * t);
      return 1 - env * (x0 * Math.cos(wd * t) + ((zeta * w0 * x0 + v0) / wd) * Math.sin(wd * t));
    }
    if (zeta === 1) {
      return 1 - Math.exp(-w0 * t) * (x0 + (v0 + w0 * x0) * t);
    }
    const s = Math.sqrt(zeta * zeta - 1);
    const r1 = -w0 * (zeta - s), r2 = -w0 * (zeta + s);
    const A = (v0 - r2 * x0) / (r1 - r2), B = x0 - A;
    return 1 - (A * Math.exp(r1 * t) + B * Math.exp(r2 * t));
  };

  /**
   * Keyframe interpolation, After Effects style.
   *   R.kf(t, [[0, 0], [0.5, 100, 'outExpo'], [1, [10, 20]], ...])
   * Each key is [time, value, ease?]; the ease on a key shapes the motion INTO that key.
   * Values may be numbers, arrays of numbers, or '#rrggbb' colors (returns 'rgb(...)').
   */
  R.kf = (t, keys) => {
    if (t <= keys[0][0]) return fmtKf(keys[0][1]);
    const last = keys[keys.length - 1];
    if (t >= last[0]) return fmtKf(last[1]);
    for (let i = 0; i < keys.length - 1; i++) {
      const a = keys[i], b = keys[i + 1];
      if (t >= a[0] && t < b[0]) {
        const p = R.easeFn(b[2])((t - a[0]) / (b[0] - a[0]));
        return mixAny(a[1], b[1], p);
      }
    }
    return fmtKf(last[1]);
  };
  function fmtKf(v) {
    return typeof v === 'string' ? R.mixColor(v, v, 0) : v;
  }
  function mixAny(a, b, p) {
    if (typeof a === 'number') return a + (b - a) * p;
    if (typeof a === 'string') return R.mixColor(a, b, p);
    return a.map((v, i) => v + (b[i] - v) * p);
  }

  /**
   * Stagger helper: eased 0..1 progress of item i of n.
   *   R.stagger(t, i, n, {start: 0, each: 0.03, dur: 0.4, ease: 'outExpo', from: 'start'|'end'|'center'|'edges'|'random', seed})
   */
  R.stagger = (t, i, n, o = {}) => {
    const each = o.each ?? 0.03, dur = o.dur ?? 0.4, start = o.start ?? 0;
    let k = i;
    switch (o.from) {
      case 'end': k = n - 1 - i; break;
      case 'center': k = Math.abs(i - (n - 1) / 2); break;
      case 'edges': k = (n - 1) / 2 - Math.abs(i - (n - 1) / 2); break;
      case 'random': k = R.hash(i, o.seed ?? 7) * (n - 1); break;
      default: break;
    }
    return R.seg(t, start + k * each, start + k * each + dur, o.ease ?? 'outExpo');
  };

  // ---------------------------------------------------------------------------
  // Deterministic randomness + noise
  // ---------------------------------------------------------------------------
  /** Seeded PRNG (mulberry32). const rnd = R.rand(42); rnd() -> [0,1). */
  R.rand = (seed = 1) => {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  /** Stateless hash of up to 3 integers -> [0,1). */
  R.hash = (x, y = 0, z = 0) => {
    let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(z | 0, 2147483647);
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
  R.randRange = (rnd, a, b) => a + (b - a) * rnd();

  // Simplex noise (Gustavson), seeded permutation.
  const grad3 = [
    [1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0], [1, 0, 1], [-1, 0, 1],
    [1, 0, -1], [-1, 0, -1], [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1],
  ];
  const perm = new Uint8Array(512), permMod12 = new Uint8Array(512);
  (function seedNoise(seed) {
    const p = new Uint8Array(256);
    for (let i = 0; i < 256; i++) p[i] = i;
    const rnd = R.rand(seed);
    for (let i = 255; i > 0; i--) {
      const j = Math.floor(rnd() * (i + 1));
      const tmp = p[i]; p[i] = p[j]; p[j] = tmp;
    }
    for (let i = 0; i < 512; i++) {
      perm[i] = p[i & 255];
      permMod12[i] = perm[i] % 12;
    }
  })(1337);
  const F2 = 0.5 * (Math.sqrt(3) - 1), G2 = (3 - Math.sqrt(3)) / 6;
  /** 2D simplex noise in [-1, 1]. */
  R.noise2 = (xin, yin) => {
    let n0 = 0, n1 = 0, n2 = 0;
    const s = (xin + yin) * F2;
    const i = Math.floor(xin + s), j = Math.floor(yin + s);
    const t = (i + j) * G2;
    const x0 = xin - (i - t), y0 = yin - (j - t);
    const i1 = x0 > y0 ? 1 : 0, j1 = x0 > y0 ? 0 : 1;
    const x1 = x0 - i1 + G2, y1 = y0 - j1 + G2;
    const x2 = x0 - 1 + 2 * G2, y2 = y0 - 1 + 2 * G2;
    const ii = i & 255, jj = j & 255;
    let t0 = 0.5 - x0 * x0 - y0 * y0;
    if (t0 >= 0) { const g = grad3[permMod12[ii + perm[jj]]]; t0 *= t0; n0 = t0 * t0 * (g[0] * x0 + g[1] * y0); }
    let t1 = 0.5 - x1 * x1 - y1 * y1;
    if (t1 >= 0) { const g = grad3[permMod12[ii + i1 + perm[jj + j1]]]; t1 *= t1; n1 = t1 * t1 * (g[0] * x1 + g[1] * y1); }
    let t2 = 0.5 - x2 * x2 - y2 * y2;
    if (t2 >= 0) { const g = grad3[permMod12[ii + 1 + perm[jj + 1]]]; t2 *= t2; n2 = t2 * t2 * (g[0] * x2 + g[1] * y2); }
    return 70 * (n0 + n1 + n2);
  };
  const F3 = 1 / 3, G3 = 1 / 6;
  /** 3D simplex noise in [-1, 1]. Use the 3rd axis for time: R.noise3(x, y, t). */
  R.noise3 = (xin, yin, zin) => {
    let n0 = 0, n1 = 0, n2 = 0, n3 = 0;
    const s = (xin + yin + zin) * F3;
    const i = Math.floor(xin + s), j = Math.floor(yin + s), k = Math.floor(zin + s);
    const t = (i + j + k) * G3;
    const x0 = xin - (i - t), y0 = yin - (j - t), z0 = zin - (k - t);
    let i1, j1, k1, i2, j2, k2;
    if (x0 >= y0) {
      if (y0 >= z0) { i1 = 1; j1 = 0; k1 = 0; i2 = 1; j2 = 1; k2 = 0; }
      else if (x0 >= z0) { i1 = 1; j1 = 0; k1 = 0; i2 = 1; j2 = 0; k2 = 1; }
      else { i1 = 0; j1 = 0; k1 = 1; i2 = 1; j2 = 0; k2 = 1; }
    } else {
      if (y0 < z0) { i1 = 0; j1 = 0; k1 = 1; i2 = 0; j2 = 1; k2 = 1; }
      else if (x0 < z0) { i1 = 0; j1 = 1; k1 = 0; i2 = 0; j2 = 1; k2 = 1; }
      else { i1 = 0; j1 = 1; k1 = 0; i2 = 1; j2 = 1; k2 = 0; }
    }
    const x1 = x0 - i1 + G3, y1 = y0 - j1 + G3, z1 = z0 - k1 + G3;
    const x2 = x0 - i2 + 2 * G3, y2 = y0 - j2 + 2 * G3, z2 = z0 - k2 + 2 * G3;
    const x3 = x0 - 1 + 3 * G3, y3 = y0 - 1 + 3 * G3, z3 = z0 - 1 + 3 * G3;
    const ii = i & 255, jj = j & 255, kk = k & 255;
    let t0 = 0.6 - x0 * x0 - y0 * y0 - z0 * z0;
    if (t0 >= 0) { const g = grad3[permMod12[ii + perm[jj + perm[kk]]]]; t0 *= t0; n0 = t0 * t0 * (g[0] * x0 + g[1] * y0 + g[2] * z0); }
    let t1 = 0.6 - x1 * x1 - y1 * y1 - z1 * z1;
    if (t1 >= 0) { const g = grad3[permMod12[ii + i1 + perm[jj + j1 + perm[kk + k1]]]]; t1 *= t1; n1 = t1 * t1 * (g[0] * x1 + g[1] * y1 + g[2] * z1); }
    let t2 = 0.6 - x2 * x2 - y2 * y2 - z2 * z2;
    if (t2 >= 0) { const g = grad3[permMod12[ii + i2 + perm[jj + j2 + perm[kk + k2]]]]; t2 *= t2; n2 = t2 * t2 * (g[0] * x2 + g[1] * y2 + g[2] * z2); }
    let t3 = 0.6 - x3 * x3 - y3 * y3 - z3 * z3;
    if (t3 >= 0) { const g = grad3[permMod12[ii + 1 + perm[jj + 1 + perm[kk + 1]]]]; t3 *= t3; n3 = t3 * t3 * (g[0] * x3 + g[1] * y3 + g[2] * z3); }
    return 32 * (n0 + n1 + n2 + n3);
  };
  /** Fractal (fBm) 3D noise, roughly [-1, 1]. */
  R.fbm = (x, y, z = 0, octaves = 4) => {
    let v = 0, amp = 0.5, f = 1, norm = 0;
    for (let o = 0; o < octaves; o++) {
      v += amp * R.noise3(x * f, y * f, z * f);
      norm += amp; amp *= 0.5; f *= 2;
    }
    return v / norm;
  };
  /** AE-style wiggle(freq, amp): smooth noise offset at time t. Different seeds decorrelate channels. */
  R.wiggle = (t, freq = 2, amp = 10, seed = 0) => R.noise2(t * freq, seed * 17.13 + 3.7) * amp;

  // ---------------------------------------------------------------------------
  // Color
  // ---------------------------------------------------------------------------
  const colCache = new Map();
  /** '#rrggbb' | 'rgb(r,g,b)' -> [r, g, b] (0..255). */
  R.col = (c) => {
    if (Array.isArray(c)) return c;
    let v = colCache.get(c);
    if (v) return v;
    if (c[0] === '#') {
      let h = c.slice(1);
      if (h.length === 3) h = h.split('').map((x) => x + x).join('');
      v = [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    } else {
      const m = c.match(/-?[\d.]+/g).map(Number);
      v = [m[0], m[1], m[2]];
    }
    colCache.set(c, v);
    return v;
  };
  R.rgba = (c, a = 1) => {
    const [r, g, b] = R.col(c);
    return `rgba(${r},${g},${b},${a})`;
  };
  R.mixColor = (a, b, t) => {
    const x = R.col(a), y = R.col(b);
    return `rgb(${Math.round(x[0] + (y[0] - x[0]) * t)},${Math.round(x[1] + (y[1] - x[1]) * t)},${Math.round(x[2] + (y[2] - x[2]) * t)})`;
  };

  // ---------------------------------------------------------------------------
  // DOM helpers
  // ---------------------------------------------------------------------------
  /**
   * R.el('div', {style: {...}, text: 'hi', html: '...', class: 'x', attrs: {...}}, parent)
   * Elements are absolutely positioned at 0,0 by default unless style.position is given.
   */
  R.el = (tag, o = {}, parent) => {
    const e = document.createElement(tag);
    if (o.class) e.className = o.class;
    if (o.text != null) e.textContent = o.text;
    if (o.html != null) e.innerHTML = o.html;
    if (o.attrs) for (const k in o.attrs) e.setAttribute(k, o.attrs[k]);
    e.style.position = 'absolute';
    e.style.left = '0px';
    e.style.top = '0px';
    if (o.style) Object.assign(e.style, o.style);
    if (parent) parent.appendChild(e);
    return e;
  };
  const SVGNS = 'http://www.w3.org/2000/svg';
  /** R.svg('path', {d: 'M0 0L10 10', fill: 'none'}, parent) — attributes set verbatim. */
  R.svg = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(SVGNS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  /** Full-frame <svg> layer with a 1920x1080 viewBox. */
  R.svgLayer = (parent, attrs = {}) =>
    R.svg('svg', Object.assign({ width: R.W, height: R.H, viewBox: `0 0 ${R.W} ${R.H}`, style: 'position:absolute;left:0;top:0;overflow:visible' }, attrs), parent);
  /** Full-frame (or sized) canvas. Returns {canvas, ctx}. */
  R.canvas = (parent, o = {}) => {
    const w = o.w ?? R.W, h = o.h ?? R.H;
    const c = R.el('canvas', { attrs: { width: w, height: h }, style: Object.assign({ width: w + 'px', height: h + 'px' }, o.style || {}) }, parent);
    const ctx = c.getContext('2d', { alpha: o.alpha ?? true });
    return { canvas: c, ctx };
  };
  /**
   * Transform string builder. Units: px / deg. Order: translate -> rotate -> skew -> scale.
   * R.tf({x, y, z, r, rx, ry, rz, s, sx, sy, skx, sky, p: perspective px})
   */
  R.tf = (o) => {
    let s = '';
    if (o.p) s += `perspective(${o.p}px) `;
    if (o.x || o.y || o.z) s += `translate3d(${o.x || 0}px,${o.y || 0}px,${o.z || 0}px) `;
    if (o.rx) s += `rotateX(${o.rx}deg) `;
    if (o.ry) s += `rotateY(${o.ry}deg) `;
    if (o.r || o.rz) s += `rotate(${o.r || o.rz}deg) `;
    if (o.skx || o.sky) s += `skew(${o.skx || 0}deg,${o.sky || 0}deg) `;
    const sx = (o.s ?? 1) * (o.sx ?? 1), sy = (o.s ?? 1) * (o.sy ?? 1);
    if (sx !== 1 || sy !== 1) s += `scale(${sx},${sy})`;
    return s || 'none';
  };
  /**
   * Split text into per-character (and per-word) inline-block spans for kinetic type.
   * Returns {chars, words}. Spaces become fixed-width spans so layout stays stable.
   */
  R.split = (el, text, o = {}) => {
    el.textContent = '';
    const chars = [], words = [];
    const parts = text.split(/(\s+)/);
    for (const part of parts) {
      if (!part) continue;
      if (/^\s+$/.test(part)) {
        const sp = document.createElement('span');
        sp.textContent = part.replace(/ /g, ' ');
        sp.style.whiteSpace = 'pre';
        el.appendChild(sp);
        continue;
      }
      const w = document.createElement('span');
      w.style.display = 'inline-block';
      w.style.whiteSpace = 'pre';
      if (o.wordClass) w.className = o.wordClass;
      for (const ch of part) {
        const c = document.createElement('span');
        c.textContent = ch;
        c.style.display = 'inline-block';
        if (o.charClass) c.className = o.charClass;
        w.appendChild(c);
        chars.push(c);
      }
      el.appendChild(w);
      words.push(w);
    }
    return { chars, words };
  };
  /** Stroke-draw an SVG path/line: p in [0,1] reveals that fraction. Optional `from` for trim-start. */
  R.drawStroke = (pathEl, p, from = 0) => {
    let L = pathEl.__len;
    if (L == null) L = pathEl.__len = pathEl.getTotalLength();
    const a = R.clamp(from) * L, b = R.clamp(p) * L;
    pathEl.style.strokeDasharray = `${Math.max(0, b - a)} ${L + 1}`;
    pathEl.style.strokeDashoffset = `${-a}`;
  };

  // ---------------------------------------------------------------------------
  // Geometry: point sets for morphs / particles
  // ---------------------------------------------------------------------------
  R.shapes = {
    /** n points on a circle, starting at 12 o'clock, clockwise. */
    circle(cx, cy, r, n = 128) {
      const pts = [];
      for (let i = 0; i < n; i++) {
        const a = -Math.PI / 2 + (i / n) * R.TAU;
        pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
      }
      return pts;
    },
    /** Regular polygon (sides) resampled to n points, first vertex at 12 o'clock. */
    polygon(cx, cy, r, sides, n = 128, rot = 0) {
      const verts = [];
      for (let i = 0; i < sides; i++) {
        const a = -Math.PI / 2 + rot + (i / sides) * R.TAU;
        verts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
      }
      return R.poly.resample(verts, n, true);
    },
    /** Axis-aligned rect (w x h) centered at cx,cy, resampled to n points starting top-center. */
    rect(cx, cy, w, h, n = 128) {
      const x0 = cx - w / 2, y0 = cy - h / 2, x1 = cx + w / 2, y1 = cy + h / 2;
      return R.poly.resample([[cx, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]], n, true);
    },
    star(cx, cy, r1, r2, spikes = 5, n = 128) {
      const v = [];
      for (let i = 0; i < spikes * 2; i++) {
        const a = -Math.PI / 2 + (i / (spikes * 2)) * R.TAU, r = i % 2 ? r2 : r1;
        v.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
      }
      return R.poly.resample(v, n, true);
    },
  };
  R.poly = {
    /** Resample a polyline/polygon to n evenly spaced points (by arc length). */
    resample(pts, n, closed = true) {
      const P = closed ? pts.concat([pts[0]]) : pts;
      const seg = [];
      let total = 0;
      for (let i = 0; i < P.length - 1; i++) {
        const d = Math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]);
        seg.push(d);
        total += d;
      }
      const out = [];
      const step = total / (closed ? n : n - 1);
      let si = 0, acc = 0;
      for (let k = 0; k < n; k++) {
        const target = k * step;
        while (si < seg.length - 1 && acc + seg[si] < target) { acc += seg[si]; si++; }
        const f = seg[si] ? (target - acc) / seg[si] : 0;
        out.push([P[si][0] + (P[si + 1][0] - P[si][0]) * f, P[si][1] + (P[si + 1][1] - P[si][1]) * f]);
      }
      return out;
    },
    /** Point-wise lerp between two equal-length point arrays. */
    lerp(a, b, t) {
      const out = new Array(a.length);
      for (let i = 0; i < a.length; i++) out[i] = [a[i][0] + (b[i][0] - a[i][0]) * t, a[i][1] + (b[i][1] - a[i][1]) * t];
      return out;
    },
    /** Trace points into the current canvas path (does not fill/stroke). */
    trace(ctx, pts, closed = true) {
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      if (closed) ctx.closePath();
    },
    /** Points -> SVG path 'd'. */
    toPath(pts, closed = true) {
      let d = `M${pts[0][0].toFixed(2)} ${pts[0][1].toFixed(2)}`;
      for (let i = 1; i < pts.length; i++) d += `L${pts[i][0].toFixed(2)} ${pts[i][1].toFixed(2)}`;
      return closed ? d + 'Z' : d;
    },
  };
  const ptsCache = new Map();
  /**
   * Sample points inside rendered text (for particles that assemble into type).
   * R.textPoints('CLAUDE', {font: R.font.display, weight: 900, size: 300, x: 960, y: 540, step: 6, stretch: 'normal'})
   * Returns [[x, y], ...] in frame coordinates (text centered on x,y). Cached by options.
   */
  R.textPoints = (text, o = {}) => {
    const key = 'T' + text + JSON.stringify(o);
    if (ptsCache.has(key)) return ptsCache.get(key);
    const size = o.size ?? 200, step = o.step ?? 6;
    const c = document.createElement('canvas');
    c.width = R.W; c.height = R.H;
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.font = `${o.style ?? 'normal'} ${o.weight ?? 800} ${size}px ${o.font ?? R.font.display}`;
    if (o.stretch) ctx.fontStretch = o.stretch;
    if (o.letterSpacing) ctx.letterSpacing = o.letterSpacing;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#fff';
    ctx.fillText(text, o.x ?? R.W / 2, o.y ?? R.H / 2);
    const img = ctx.getImageData(0, 0, R.W, R.H).data;
    const pts = [];
    for (let y = 0; y < R.H; y += step)
      for (let x = 0; x < R.W; x += step) if (img[(y * R.W + x) * 4 + 3] > 128) pts.push([x, y]);
    ptsCache.set(key, pts);
    return pts;
  };
  /** n evenly spaced points along an SVG path 'd' string (frame coordinates). Cached. */
  R.pathPoints = (d, n = 200) => {
    const key = 'P' + n + d;
    if (ptsCache.has(key)) return ptsCache.get(key);
    const tmp = R.svg('svg', { width: 0, height: 0, style: 'position:absolute' }, document.body);
    const p = R.svg('path', { d }, tmp);
    const L = p.getTotalLength();
    const pts = [];
    for (let i = 0; i < n; i++) {
      const q = p.getPointAtLength((i / n) * L);
      pts.push([q.x, q.y]);
    }
    tmp.remove();
    ptsCache.set(key, pts);
    return pts;
  };

  // ---------------------------------------------------------------------------
  // Pseudo-3D
  // ---------------------------------------------------------------------------
  R.v3 = {
    rotX: (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c]; },
    rotY: (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c]; },
    rotZ: (p, a) => { const c = Math.cos(a), s = Math.sin(a); return [p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]]; },
    /** Perspective project a camera-space point. Camera at z = -dist looking +z. Returns [sx, sy, scale, depth] or null if behind. */
    project: (p, o = {}) => {
      const fov = o.fov ?? 900, dist = o.dist ?? 900, cx = o.cx ?? R.W / 2, cy = o.cy ?? R.H / 2;
      const z = p[2] + dist;
      if (z <= 1) return null;
      const k = fov / z;
      return [cx + p[0] * k, cy + p[1] * k, k, z];
    },
    /** n points evenly on a unit sphere (Fibonacci lattice). */
    fibSphere: (n) => {
      const pts = [], ga = Math.PI * (3 - Math.sqrt(5));
      for (let i = 0; i < n; i++) {
        const y = 1 - (i / (n - 1)) * 2, r = Math.sqrt(1 - y * y), th = ga * i;
        pts.push([Math.cos(th) * r, y, Math.sin(th) * r]);
      }
      return pts;
    },
    /** Torus point grid (u x v), major radius R0, minor r0. */
    torus: (R0, r0, nu = 48, nv = 24) => {
      const pts = [];
      for (let i = 0; i < nu; i++)
        for (let j = 0; j < nv; j++) {
          const u = (i / nu) * R.TAU, v = (j / nv) * R.TAU;
          pts.push([(R0 + r0 * Math.cos(v)) * Math.cos(u), r0 * Math.sin(v), (R0 + r0 * Math.cos(v)) * Math.sin(u)]);
        }
      return pts;
    },
  };

  // ---------------------------------------------------------------------------
  // Deterministic simulation cache
  // ---------------------------------------------------------------------------
  /**
   * const get = R.sim({dt: 1/120, init: () => state, step: (state, t, dt) => {...}});
   * get(localT) returns the state advanced to localT (fixed timestep; re-inits when seeking backwards).
   */
  R.sim = ({ dt = 1 / 120, init, step }) => {
    let state = null, simT = 0;
    return function (t) {
      if (state === null || t < simT - 1e-9) { state = init(); simT = 0; }
      while (simT + dt <= t + 1e-9) { step(state, simT, dt); simT += dt; }
      return state;
    };
  };

  // ---------------------------------------------------------------------------
  // Scenes
  // ---------------------------------------------------------------------------
  R.scenes = [];
  /**
   * Register a scene:
   * R.scene({
   *   id: 's03-shapes', start: 3.75, end: 5.625,   // global seconds, window is [start, end)
   *   z: 30,                                        // stacking order (higher = on top), defaults to registration order
   *   bg: R.pal.ink,                                // optional root background
   *   setup(root) {...},                            // build DOM once. root = 1920x1080 div, overflow hidden
   *   update(lt, p, t) {...},                       // every visible frame: local seconds, 0..1 progress, global seconds
   * })
   */
  R.scene = (def) => {
    if (!def.id) throw new Error('scene needs an id');
    if (!(def.end > def.start)) throw new Error(`scene ${def.id}: end must be > start`);
    def.z = def.z ?? R.scenes.length * 10;
    R.scenes.push(def);
    return def;
  };

  // ---------------------------------------------------------------------------
  // Global FX cues
  // ---------------------------------------------------------------------------
  R.cues = [];
  /**
   * Register a global post-FX cue (call at module load or in setup):
   *   R.cue(t, 'flash',  {amt: 1, dur: 0.12, color: '#fff'})     // additive overlay flash, decays
   *   R.cue(t, 'shake',  {amt: 14, dur: 0.3, freq: 28})          // px, decaying noise shake
   *   R.cue(t, 'chroma', {amt: 10, dur: 0.2, angle: 0})          // RGB split in px, decays
   *   R.cue(t, 'zoom',   {amt: 0.05, dur: 0.3})                  // camera scale punch, decays
   *   R.cue(t, 'invert', {dur: 0.06})                            // hard invert for dur
   *   R.cue(t, 'letterbox', {amt: 120, dur: 1.2, in: 0.2, out: 0.2}) // bars of amt px, eased in/out
   *   R.cue(t, 'grain',  {amt: 0.12, dur: 1})                    // extra grain on top of the base
   *   R.cue(t, 'vignette', {amt: 0.5, dur: 0.47, in: 0.1, out: 0.03}) // vignette opacity from base 0.22 to amt, eased in/out
   * Envelopes: flash/shake/chroma/zoom decay as (1 - k)^curve (curve default 2).
   */
  R.cue = (t, type, o = {}) => {
    const c = Object.assign({ t, type }, o);
    R.cues.push(c);
    return c;
  };
  R.config = { grain: 0.045, vignette: 0.22 };

  /**
   * Declare a sound-design event so the procedural soundtrack locks to picture.
   * tools/cues.mjs exports these to audio/cues.json for audio/synth.py.
   *   R.sfx(t, 'impact', {amt: 1})              big hit (kick + noise burst + sub)
   *   R.sfx(t, 'whoosh', {dur: 0.3, dir: 'up'}) air movement ending at t + dur ('up' | 'down' pitch sweep)
   *   R.sfx(t, 'swish',  {amt: 0.6})            short fast whoosh (whip pans, quick slides)
   *   R.sfx(t, 'click' | 'tick' | 'pop' | 'blip', {pitch: 1})   UI / micro-interaction sounds
   *   R.sfx(t, 'glitch', {dur: 0.2})            digital stutter burst
   *   R.sfx(t, 'riser',  {dur: 1.875})          tension build ending at t + dur
   *   R.sfx(t, 'reverse', {dur: 0.47})          reverse swell that lands at t + dur
   *   R.sfx(t, 'subdrop', {amt: 1})             808-style sub drop
   *   R.sfx(t, 'shimmer', {dur: 0.9})           airy sparkle (particles, reveals)
   *   R.sfx(t, 'type',    {count: 6, dur: 0.3}) typewriter / letter-by-letter ticks
   *   R.sfx(t, 'tapestop', {dur: 0.3})          pitch-down stop
   */
  R.sounds = [];
  R.sfx = (t, type, o = {}) => {
    const s = Object.assign({ t, type }, o);
    R.sounds.push(s);
    return s;
  };

  function decay(t, c, defDur) {
    const dur = c.dur ?? defDur;
    const k = (t - c.t) / dur;
    if (k < 0 || k >= 1) return 0;
    return Math.pow(1 - k, c.curve ?? 2);
  }
  /** Evaluate all FX at global time t (pure). */
  R.fxAt = (t) => {
    const fx = { flash: 0, flashColor: '#ffffff', shakeX: 0, shakeY: 0, chroma: 0, chromaAngle: 0, zoom: 0, invert: false, letterbox: 0, grain: R.config.grain, vignette: R.config.vignette };
    let flashBest = 0;
    for (const c of R.cues) {
      if (t < c.t) continue;
      switch (c.type) {
        case 'flash': {
          const v = (c.amt ?? 1) * decay(t, c, 0.12);
          if (v > flashBest) { flashBest = v; fx.flashColor = c.color ?? '#ffffff'; }
          break;
        }
        case 'shake': {
          const v = (c.amt ?? 12) * decay(t, c, 0.3);
          if (v > 0) {
            const f = c.freq ?? 28, lt = t - c.t;
            fx.shakeX += R.noise2(lt * f, c.t * 13.1) * v;
            fx.shakeY += R.noise2(lt * f + 91.7, c.t * 7.7) * v;
          }
          break;
        }
        case 'chroma': {
          const v = (c.amt ?? 8) * decay(t, c, 0.2);
          if (v > fx.chroma) { fx.chroma = v; fx.chromaAngle = c.angle ?? 0; }
          break;
        }
        case 'zoom': fx.zoom += (c.amt ?? 0.04) * decay(t, c, 0.3); break;
        case 'invert': if (t - c.t < (c.dur ?? 0.05)) fx.invert = !fx.invert; break;
        case 'letterbox': {
          const dur = c.dur ?? 1, i = c.in ?? 0.2, o = c.out ?? 0.2, lt = t - c.t;
          if (lt < dur) {
            const v = lt < i ? E.snap(lt / i) : lt > dur - o ? 1 - E.snap((lt - (dur - o)) / o) : 1;
            fx.letterbox = Math.max(fx.letterbox, (c.amt ?? 110) * v);
          }
          break;
        }
        case 'grain': if (t - c.t < (c.dur ?? 1)) fx.grain += c.amt ?? 0.08; break;
        case 'vignette': {
          // Eases from the base vignette to amt over `in` (snap), holds, returns over `out`.
          const dur = c.dur ?? 0.5, i = c.in ?? 0.1, o = c.out ?? 0.05, lt = t - c.t;
          if (lt < dur) {
            const v = lt < i ? E.snap(lt / i) : lt > dur - o ? 1 - E.snap((lt - (dur - o)) / o) : 1;
            fx.vignette = Math.max(fx.vignette, R.lerp(R.config.vignette, c.amt ?? 0.5, v));
          }
          break;
        }
        default: break;
      }
    }
    fx.flash = flashBest;
    return fx;
  };

  // ---------------------------------------------------------------------------
  // Stage + render loop
  // ---------------------------------------------------------------------------
  const params = new URLSearchParams(location.search);
  R.params = params;
  R.isRender = params.has('render');
  R.only = params.get('only'); // comma-separated scene ids to isolate
  R.debug = params.has('debug');
  R.t = 0;
  R.frameIndex = 0;

  let viewport, camera, stage, flashEl, lbTop, lbBot, vignetteEl, grainCanvas, grainCtx, debugEl, chromaR, chromaB, grainTiles;

  function buildStage() {
    document.body.style.margin = '0';
    document.body.style.background = '#000';
    document.body.style.overflow = 'hidden';
    viewport = R.el('div', { attrs: { id: 'viewport' }, style: { width: R.W + 'px', height: R.H + 'px', overflow: 'hidden', background: R.pal.ink, transformOrigin: '0 0' } }, document.body);
    camera = R.el('div', { attrs: { id: 'camera' }, style: { width: R.W + 'px', height: R.H + 'px', transformOrigin: '50% 50%' } }, viewport);
    stage = R.el('div', { attrs: { id: 'stage' }, style: { width: R.W + 'px', height: R.H + 'px', overflow: 'hidden', background: R.pal.ink } }, camera);
    flashEl = R.el('div', { style: { width: R.W + 'px', height: R.H + 'px', opacity: 0, pointerEvents: 'none', mixBlendMode: 'screen' } }, viewport);
    vignetteEl = R.el('div', { style: { width: R.W + 'px', height: R.H + 'px', pointerEvents: 'none', background: `radial-gradient(ellipse 75% 75% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,1) 140%)`, opacity: R.config.vignette } }, viewport);
    const gc = R.canvas(viewport, { style: { pointerEvents: 'none', mixBlendMode: 'overlay' } });
    grainCanvas = gc.canvas; grainCtx = gc.ctx;
    lbTop = R.el('div', { style: { width: R.W + 'px', height: '0px', background: '#000' } }, viewport);
    lbBot = R.el('div', { style: { width: R.W + 'px', height: '0px', top: 'auto', bottom: '0px', background: '#000' } }, viewport);
    if (R.debug) {
      debugEl = R.el('div', { style: { left: '16px', top: '14px', padding: '6px 10px', font: `600 18px ${R.font.mono}`, color: '#fff', background: 'rgba(0,0,0,.72)', borderRadius: '4px', zIndex: 99, whiteSpace: 'pre' } }, viewport);
    }
    // RGB split filter (applied to #camera only while a chroma cue is active)
    const defs = R.svg('svg', { width: 0, height: 0, style: 'position:absolute;left:0;top:0' }, document.body);
    const f = R.svg('filter', { id: 'fx-chroma', x: '0', y: '0', width: '100%', height: '100%', 'color-interpolation-filters': 'sRGB' }, defs);
    R.svg('feColorMatrix', { in: 'SourceGraphic', type: 'matrix', values: '1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0', result: 'r' }, f);
    chromaR = R.svg('feOffset', { in: 'r', dx: 0, dy: 0, result: 'r2' }, f);
    R.svg('feColorMatrix', { in: 'SourceGraphic', type: 'matrix', values: '0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0', result: 'g' }, f);
    R.svg('feColorMatrix', { in: 'SourceGraphic', type: 'matrix', values: '0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0', result: 'b' }, f);
    chromaB = R.svg('feOffset', { in: 'b', dx: 0, dy: 0, result: 'b2' }, f);
    R.svg('feBlend', { in: 'r2', in2: 'g', mode: 'screen', result: 'rg' }, f);
    R.svg('feBlend', { in: 'rg', in2: 'b2', mode: 'screen' }, f);
    // Pre-baked grain tiles (deterministic)
    grainTiles = [];
    for (let k = 0; k < 6; k++) {
      const c = document.createElement('canvas');
      c.width = c.height = 256;
      const g = c.getContext('2d');
      const img = g.createImageData(256, 256);
      const rnd = R.rand(9001 + k);
      for (let i = 0; i < img.data.length; i += 4) {
        const v = Math.floor(rnd() * 255);
        img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
        img.data[i + 3] = 255;
      }
      g.putImageData(img, 0, 0);
      grainTiles.push(c);
    }
  }

  function fitToWindow() {
    if (R.isRender) return;
    const k = Math.min(window.innerWidth / R.W, window.innerHeight / R.H);
    viewport.style.transform = `scale(${k})`;
    viewport.style.left = (window.innerWidth - R.W * k) / 2 + 'px';
    viewport.style.top = (window.innerHeight - R.H * k) / 2 + 'px';
  }

  function applyFx(t) {
    const fx = R.fxAt(t);
    const s = 1 + fx.zoom;
    camera.style.transform = `translate3d(${fx.shakeX.toFixed(2)}px,${fx.shakeY.toFixed(2)}px,0) scale(${s.toFixed(4)})`;
    if (fx.chroma > 0.25) {
      const dx = Math.cos(fx.chromaAngle) * fx.chroma, dy = Math.sin(fx.chromaAngle) * fx.chroma;
      chromaR.setAttribute('dx', dx.toFixed(2)); chromaR.setAttribute('dy', dy.toFixed(2));
      chromaB.setAttribute('dx', (-dx).toFixed(2)); chromaB.setAttribute('dy', (-dy).toFixed(2));
      camera.style.filter = fx.invert ? 'url(#fx-chroma) invert(1)' : 'url(#fx-chroma)';
    } else {
      camera.style.filter = fx.invert ? 'invert(1)' : 'none';
    }
    vignetteEl.style.opacity = fx.vignette.toFixed(3);
    flashEl.style.opacity = fx.flash.toFixed(3);
    flashEl.style.background = fx.flashColor;
    lbTop.style.height = fx.letterbox.toFixed(1) + 'px';
    lbBot.style.height = fx.letterbox.toFixed(1) + 'px';
    // Grain: new pattern every 2 frames (30 fps grain reads filmic and is kinder to the encoder)
    const gi = Math.floor(R.frameIndex / 2);
    grainCtx.clearRect(0, 0, R.W, R.H);
    if (fx.grain > 0) {
      grainCtx.globalAlpha = R.clamp(fx.grain * 2.2);
      const tile = grainTiles[gi % grainTiles.length];
      const ox = Math.floor(R.hash(gi, 1) * 256), oy = Math.floor(R.hash(gi, 2) * 256);
      for (let y = -oy; y < R.H; y += 256) for (let x = -ox; x < R.W; x += 256) grainCtx.drawImage(tile, x, y);
      grainCtx.globalAlpha = 1;
    }
  }

  /** Render global time t (seconds). Synchronous; the capture tool screenshots right after. */
  R.render = (t) => {
    R.t = t;
    R.frameIndex = Math.round(t * R.FPS);
    let label = '';
    for (const sc of R.scenes) {
      const visible = t >= sc.start && t < sc.end && isSelected(sc.id);
      if (visible !== sc.__visible) {
        sc.__root.style.display = visible ? 'block' : 'none';
        sc.__visible = visible;
      }
      if (visible && !sc.__broken) {
        const lt = t - sc.start;
        try {
          sc.update && sc.update(lt, lt / (sc.end - sc.start), t);
        } catch (e) {
          sceneFailed(sc, 'update', e, t);
        }
        label += (label ? ' + ' : '') + sc.id;
      }
    }
    applyFx(t);
    if (debugEl) {
      const m = R.musical(t);
      debugEl.textContent = `${t.toFixed(3)}s  F${String(R.frameIndex).padStart(3, '0')}  ${m.bar}.${m.beat}.${m.sixteenth + 1}  ${label || '—'}`;
    }
  };
  R.frame = (i) => R.render(i / R.FPS);

  function isSelected(id) {
    if (!R.only) return true;
    return R.only.split(',').some((o) => o && (id === o || id.startsWith(o)));
  }
  // A failing scene logs once and renders a loud error card instead of taking the whole reel down.
  function sceneFailed(sc, phase, e, t) {
    sc.__broken = true;
    console.error(`[scene ${sc.id}] ${phase} failed at t=${t.toFixed(3)}: ${e && e.stack ? e.stack : e}`);
    const root = sc.__root;
    if (!root) return;
    root.innerHTML = '';
    root.style.background = '#400';
    R.el('div', { text: `SCENE ERROR ${sc.id} (${phase}): ${e && e.message}`, style: { left: '60px', top: '60px', width: '1800px', font: `700 36px ${R.font.mono}`, color: '#fff', whiteSpace: 'pre-wrap' } }, root);
  }

  function loadScript(src) {
    return new Promise((res, rej) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = res;
      s.onerror = () => rej(new Error('failed to load ' + src));
      document.head.appendChild(s);
    });
  }

  async function loadFonts() {
    const faces = [
      [`900 100px Archivo`, 'normal'], [`100 100px Archivo`, 'normal'], [`italic 900 100px Archivo`, 'italic'],
      [`400 100px 'Instrument Serif'`], [`italic 400 100px 'Instrument Serif'`],
      [`400 100px 'JetBrains Mono'`], [`800 100px 'JetBrains Mono'`],
    ];
    await Promise.all(faces.map((f) => document.fonts.load(f[0], 'AaZz09')));
    await document.fonts.ready;
  }

  /** Boot: fonts -> scene modules (from manifest) -> setups. Resolves R.ready. */
  R.ready = (async () => {
    await new Promise((r) => (document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', r) : r()));
    buildStage();
    fitToWindow();
    window.addEventListener('resize', fitToWindow);
    await loadFonts();
    // With ?only=ids, load just those modules so a half-built neighbour can't break an isolated preview.
    const list = (window.SCENE_FILES || []).filter((f) => isSelected(f.split('/').pop().replace(/\.js$/, '')));
    for (const f of list) {
      try {
        await loadScript(f);
      } catch (e) {
        console.error('[engine] ' + e.message);
      }
    }
    R.scenes.sort((a, b) => a.z - b.z);
    for (const sc of R.scenes) {
      const root = R.el('div', { attrs: { 'data-scene': sc.id }, style: { width: R.W + 'px', height: R.H + 'px', overflow: 'hidden', display: 'none', contain: 'strict' } }, stage);
      if (sc.bg) root.style.background = sc.bg;
      sc.__root = root;
      sc.__visible = false;
      try {
        if (sc.setup) await sc.setup(root);
      } catch (e) {
        sceneFailed(sc, 'setup', e, 0);
      }
    }
    R.cues.sort((a, b) => a.t - b.t);
    const t0 = parseFloat(params.get('t') || '0');
    R.render(isFinite(t0) ? t0 : 0);
    return true;
  })().catch((e) => {
    console.error('[engine] boot failed:', e && e.stack ? e.stack : e);
    throw e;
  });
})();
