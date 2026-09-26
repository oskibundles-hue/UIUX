// s03-space — Space: the corridor (3.75 → 5.15625 s, frames 225–309, bar 3 beats 1–3)
//
// A square type corridor seen through the storyboard's CSS-3D camera: perspective 1000px, origin 960/540;
// world = translateZ(D) rotateZ(roll); each wall = the floor (plane y = 1500) hinged on its near edge by
// rotateX(θ) and cloned at 90° steps round the corridor axis. Chromium's preserve-3d path mis-sorts intersecting
// planes, drops tiles near the camera and minifies wall textures without mipmaps (the 4 px depth rings break
// into dashes), so this module evaluates the same camera analytically and draws it on one Canvas 2D:
//   * the walls are the four faces of a square frustum (a rigid hinged rectangle, clipped where it would pass
//     behind its neighbours), so no two faces overlap on screen and depth order is exact at every fold angle;
//     during the >90° hinge overshoot the faces flare and still meet at the corners;
//   * depth shading is a perspective-correct gradient (stops solved in screen space);
//   * "SPACE" is vector type: outlines traced from Archivo at setup, every vertex projected per frame, so the
//     letters stay razor sharp from 0.19× to 10×; rings are projected quads, labels are affine sprites;
//   * real motion blur: each frame averages N sub-frames across a 180° shutter, N adapted to the fastest
//     on-screen motion (discrete events — weight snaps, ring chase — stay locked to their frames); when the
//     24-sample cap is hit, each sub-frame also sweeps rings + lettering over its own slice of the shutter
//     (a nonzero union of copies), so fast streaks stay continuous instead of stepping into ghost copies.
// The rush is eased in log-scale space (see dolly) so the push-in builds continuously into the rest pose.
// The first frame (flat Signal) and the two rest frames (Paper + Ø56 dot) are drawn flat: exact handoffs.
(() => {
  const P = R.pal;

  // ---- timing (global seconds) -------------------------------------------------------------------------
  const T0 = 3.75;
  const T_END = 5.15625;
  const T_ROLL1 = 4.21875; // snare: roll 1, words -> wght 100, dolly starts
  const T_ROLL2 = 4.6875; // beat 3: roll 2, words -> wght 900 / 62%, rush starts
  const T_REST = T_END - 2 / 60; // 5.1229: flat rest pose (frames 308-309)
  const T_RUSH_END = 308 / 60; // the rush lands exactly on the first rest frame
  const T_FADE0 = 3.8671875, T_FADE1 = 3.984375; // lettering + labels fade in (storyboard)
  const CHASE = [4.6875, 4.8046875, 4.921875, 5.0390625]; // ring chase, one pulse per 16th

  const HINGE = { stiffness: 240, damping: 19 };
  const ROLL = { stiffness: 320, damping: 22 };

  // ---- world (px, storyboard units) -------------------------------------------------------------------------
  const PERSP = 1000;
  const CX = 960, CY = 540;
  const HALF = 960; // corridor cross-section 1920×1920 centred on (960,540)
  const DEPTH = 4200, SLAB = 350;
  const Z_NEAR = 900; // storyboard culling plane: nothing nearer than z = 900 is drawn (all of it is off-screen)
  const FAR_EXT = 640; // far wall overhang: only ever seen through the flare of the >90° hinge overshoot
  const NEAR_EXT = 320; // walls continue 320 px in front of the hinge line: invisible while unfolding, but they
  //                       keep the frame corners inside the corridor when it rolls before the dolly has moved
  const SHADE_MAX = 0.7;
  const RING_W = 4, RING_LIT_W = 10; // depth ring; a lit (Paper) ring is drawn heavier so the chase reads

  // Lettering: Archivo 440 px, tracking -0.01em, two instances per wall starting at depths 150 and 2250,
  // baseline along the depth axis reading near -> far, glyph tops to screen-left on the floor, cap band centred.
  const FS = 440;
  const CAP = 0.6875 * FS;
  const WORD_AT = [150, 2250];
  const STYLES = [
    { w: 900, kw: 'expanded' }, // 125%
    { w: 100, kw: 'expanded' }, // 125%, hairline (roll 1)
    { w: 900, kw: 'extra-condensed' }, // 62.5% (canvas keyword; the DOM minimum would be 62%)
  ];
  const X_BASE = CX + CAP / 2; // baseline x on the floor (tops point to -x)

  // Labels "03.1".."03.12": JetBrains Mono 500 20 px, tracking 0.12em, 40 px in from each ring's left end,
  // on the ring's near side with glyph tops facing the ring ("03.12" sits at the far end of the corridor).
  const LAB_FS = 20, LAB_CAP = 0.73 * LAB_FS, LAB_GAP = 8, LAB_SS = 3; // sprite supersampling

  // Motion blur
  const SHUTTER = 0.5 / 60; // 180°
  const BLUR_PX = 1; // target sub-frame spacing on screen: at 1 px even the 1 px depth rings fuse into a smear
  const BLUR_MIN_PX = 1.5; // below this much motion across the shutter, no blur
  const BLUR_MAX = R.isRender ? 24 : 6; // the interactive ?play preview uses a lighter shutter to stay real-time
  const COPY_PX = 2, COPY_MAX = R.isRender ? 8 : 2; // sweep copies of rings + lettering inside a sub-frame

  const SIG = R.col(P.signal), INKC = R.col(P.ink);
  const shadeCache = new Map();
  function shadeCol(a) {
    const key = Math.round(a * 1024);
    let s = shadeCache.get(key);
    if (!s) {
      const v = key / 1024;
      s = `rgb(${Math.round(SIG[0] + (INKC[0] - SIG[0]) * v)},${Math.round(SIG[1] + (INKC[1] - SIG[1]) * v)},${Math.round(SIG[2] + (INKC[2] - SIG[2]) * v)})`;
      shadeCache.set(key, s);
    }
    return s;
  }

  const styleAt = (t) => (t < T_ROLL1 ? 0 : t < T_ROLL2 ? 1 : 2);
  const foldAngle = (t) => 90 * R.spring(t - T0, HINGE);
  // Each 90° roll winds up first: a -4° counter-roll over the 4 frames before its beat (ease in-out, so it
  // arrives at rest), then the ROLL spring releases it from -4° to 90° on the beat (≈9% overshoot).
  const WIND = -4, WIND_T = 4 / 60;
  function rollStep(t, T) {
    if (t < T - WIND_T) return 0;
    if (t < T) return WIND * R.ease.inOutSine((t - (T - WIND_T)) / WIND_T);
    return WIND + (90 - WIND) * R.spring(t - T, ROLL);
  }
  const rollAngle = (t) => rollStep(t, T_ROLL1) + rollStep(t, T_ROLL2);
  // DOLLY (glide 0 -> 1200) then RUSH to D = 4200 (far wall at scale 1) on the first rest frame.
  // The camera "inhales" first: it eases back D_INHALE px over the same 4 frames as the roll-2 wind-up.
  // The rush is eased in LOG-SCALE space (far-wall scale s = P/(P + DEPTH - D), ln s -> 0 along u^RUSH_POW):
  // an ease applied to D itself compounds with the 1/z of perspective, so whip-on-D sat still for the first
  // 14 frames (far wall 480 -> 496 px) and then jumped ×1.65 on the cut. In log space the zoom accelerates
  // from rest on the beat, keeps building into the cut, and its last step onto the rest pose is ≈ ×1.14.
  const D_INHALE = 60, RUSH_POW = 2.5;
  const LN_S0 = Math.log(PERSP / (PERSP + DEPTH - (1200 - D_INHALE)));
  function dolly(t) {
    if (t < T_ROLL1) return 0;
    if (t < T_ROLL2) {
      const D = 1200 * R.ease.glide((t - T_ROLL1) / (T_ROLL2 - T_ROLL1));
      return t > T_ROLL2 - WIND_T ? D - D_INHALE * R.ease.inOutSine((t - (T_ROLL2 - WIND_T)) / WIND_T) : D;
    }
    if (t < T_RUSH_END) {
      const u = (t - T_ROLL2) / (T_RUSH_END - T_ROLL2);
      return PERSP + DEPTH - PERSP / Math.exp(LN_S0 * (1 - Math.pow(u, RUSH_POW)));
    }
    return DEPTH;
  }
  // ring chase: pulse k lights rings (11 - i) and (12 - i) on its i-th frame -> each ring Paper for 2 frames
  function litRings(f) {
    const lit = new Set();
    for (const tc of CHASE) {
      const i = f - Math.ceil(tc * 60 - 1e-6);
      if (i >= 0) {
        lit.add(11 - i);
        lit.add(12 - i);
      }
    }
    return lit;
  }

  // Camera state at time t (continuous quantities only).
  function camera(t) {
    const th = foldAngle(t);
    const thR = (th * Math.PI) / 180;
    const cT = Math.cos(thR), sT = Math.sin(thR);
    const D = dolly(t);
    return {
      th, cT, sT, D,
      roll: (rollAngle(t) * Math.PI) / 180,
      dNear: sT > 1e-6 ? Math.max(-NEAR_EXT, (D - Z_NEAR) / sT) : -NEAR_EXT,
      dFar: cT > 1e-6 ? Math.min(DEPTH, HALF / cT) : DEPTH,
    };
  }
  // Floor point (x across, d = depth from the hinge) -> screen, unrolled. Writes into out.
  function projC(c, x, d, out) {
    const k = PERSP / (PERSP - (c.D - d * c.sT));
    out[0] = CX + (x - CX) * k;
    out[1] = CY + (HALF - d * c.cT) * k;
    if (c.dr) {
      const x = out[0] - CX, y = out[1] - CY;
      out[0] = CX + x * c.cdr - y * c.sdr;
      out[1] = CY + x * c.sdr + y * c.cdr;
    }
    return out;
  }

  // Depth rings of one camera state appended to the Ink / lit paths: quads at d = 350 r (a lit ring is Paper
  // and heavier, and keeps at least ~2.5 px on screen so each pulse reads from its first frame at the far end).
  // Returns whether any lit ring was added.
  function addRings(c, lit, ink, lp, q) {
    const { cT, sT, D, dNear, dFar } = c;
    const yAt = (d) => (HALF - d * cT) * (PERSP / (PERSP - (D - d * sT)));
    let any = false;
    for (let r = 1; r <= 11; r++) {
      const on = lit.has(r);
      const d = SLAB * r;
      const hwid = on ? Math.max(RING_LIT_W, 2.5 / Math.max(1e-3, Math.abs(yAt(d + 1) - yAt(d)))) / 2 : RING_W / 2;
      const d0 = d - hwid, d1 = d + hwid;
      if (d0 < dNear || d1 > dFar) continue;
      const pth = on ? lp : ink;
      any = any || on;
      projC(c, CX - (HALF - d0 * cT) - 2, d0, q); pth.moveTo(q[0], q[1]);
      projC(c, CX + (HALF - d0 * cT) + 2, d0, q); pth.lineTo(q[0], q[1]);
      projC(c, CX + (HALF - d1 * cT) + 2, d1, q); pth.lineTo(q[0], q[1]);
      projC(c, CX - (HALF - d1 * cT) - 2, d1, q); pth.lineTo(q[0], q[1]);
      pth.closePath();
    }
    return any;
  }
  // Lettering of one camera state: every outline vertex projected; contours clipped at the near plane.
  function addText(c, word, text, q) {
    const { dNear, dFar } = c;
    for (const s0 of WORD_AT) {
      if (s0 + word.length < dNear || s0 > dFar) continue;
      for (const cn of word.contours) {
        const n = cn.length / 2;
        let allIn = true, anyIn = false;
        for (let i = 0; i < n; i++) {
          if (s0 + cn[i * 2] < dNear) allIn = false;
          else anyIn = true;
        }
        if (!anyIn) continue;
        if (allIn) {
          for (let i = 0; i < n; i++) {
            projC(c, X_BASE - cn[i * 2 + 1], s0 + cn[i * 2], q);
            if (i === 0) text.moveTo(q[0], q[1]);
            else text.lineTo(q[0], q[1]);
          }
          text.closePath();
          continue;
        }
        // Sutherland-Hodgman against d >= dNear in the wall plane (keeps the contour's winding)
        const poly = [];
        for (let i = 0; i < n; i++) {
          const j = (i + 1) % n;
          const ax = X_BASE - cn[i * 2 + 1], ad = s0 + cn[i * 2];
          const bx = X_BASE - cn[j * 2 + 1], bd = s0 + cn[j * 2];
          const ain = ad >= dNear, bin = bd >= dNear;
          if (ain) poly.push(ax, ad);
          if (ain !== bin) poly.push(ax + ((bx - ax) * (dNear - ad)) / (bd - ad), dNear);
        }
        if (poly.length < 6) continue;
        for (let i = 0; i < poly.length; i += 2) {
          projC(c, poly[i], poly[i + 1], q);
          if (i === 0) text.moveTo(q[0], q[1]);
          else text.lineTo(q[0], q[1]);
        }
        text.closePath();
      }
    }
  }

  // Orient contours for the nonzero rule: outlines one way, counters (odd nesting depth) the other.
  function orientContours(cs) {
    const area = (f) => {
      let a = 0;
      for (let i = 0, n = f.length / 2; i < n; i++) {
        const j = (i + 1) % n;
        a += f[i * 2] * f[j * 2 + 1] - f[j * 2] * f[i * 2 + 1];
      }
      return a / 2;
    };
    const inside = (x, y, f) => {
      let c = false;
      for (let i = 0, n = f.length / 2, j = n - 1; i < n; j = i++) {
        const xi = f[i * 2], yi = f[i * 2 + 1], xj = f[j * 2], yj = f[j * 2 + 1];
        if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
      }
      return c;
    };
    return cs.map((f, k) => {
      let depth = 0;
      for (let m = 0; m < cs.length; m++) if (m !== k && inside(f[0], f[1], cs[m])) depth++;
      const want = depth % 2 === 0 ? 1 : -1;
      if (Math.sign(area(f)) === want) return f;
      const r = new Float64Array(f.length);
      for (let i = 0, n = f.length / 2; i < n; i++) {
        r[i * 2] = f[(n - 1 - i) * 2];
        r[i * 2 + 1] = f[(n - 1 - i) * 2 + 1];
      }
      return r;
    });
  }

  // ---- glyph outline tracing (setup only)---------------------------------------------------------------
  // Rasterise the word at `scale`× and trace the 50% alpha iso-line with marching squares (linear edge
  // interpolation, saddles resolved by the cell centre), then simplify with Douglas-Peucker.
  function traceWord(text, style, scale) {
    const px = FS * scale;
    const cv = document.createElement('canvas');
    const ctx = cv.getContext('2d', { willReadFrequently: true });
    const font = () => {
      ctx.font = `${style.w} ${px}px Archivo`;
      ctx.fontStretch = style.kw;
      ctx.letterSpacing = `${-0.01 * px}px`;
    };
    font();
    const m = ctx.measureText(text);
    const pad = 6;
    const W = Math.ceil(m.actualBoundingBoxLeft + m.actualBoundingBoxRight) + 2 * pad + 4;
    const H = Math.ceil(m.actualBoundingBoxAscent + m.actualBoundingBoxDescent) + 2 * pad + 4;
    cv.width = W;
    cv.height = H;
    font();
    ctx.fillStyle = '#fff';
    const ox = pad + m.actualBoundingBoxLeft, oy = pad + m.actualBoundingBoxAscent;
    ctx.fillText(text, ox, oy);
    const data = ctx.getImageData(0, 0, W, H).data;
    const A = new Float32Array(W * H);
    for (let i = 0; i < W * H; i++) A[i] = data[i * 4 + 3];
    const T = 127.5;
    const pts = new Map(); // edge key -> [x, y]
    const adj = new Map(); // edge key -> [k1, k2]
    const ptH = (x, y) => {
      const k = (y * W + x) * 2; // edge (x,y)-(x+1,y)
      if (!pts.has(k)) {
        const a = A[y * W + x], b = A[y * W + x + 1];
        pts.set(k, [x + (T - a) / (b - a) + 0.5, y + 0.5]);
      }
      return k;
    };
    const ptV = (x, y) => {
      const k = (y * W + x) * 2 + 1; // edge (x,y)-(x,y+1)
      if (!pts.has(k)) {
        const a = A[y * W + x], b = A[(y + 1) * W + x];
        pts.set(k, [x + 0.5, y + (T - a) / (b - a) + 0.5]);
      }
      return k;
    };
    const link = (k1, k2) => {
      let l = adj.get(k1);
      if (!l) adj.set(k1, (l = []));
      l.push(k2);
      let l2 = adj.get(k2);
      if (!l2) adj.set(k2, (l2 = []));
      l2.push(k1);
    };
    for (let y = 0; y < H - 1; y++) {
      for (let x = 0; x < W - 1; x++) {
        const a = A[y * W + x], b = A[y * W + x + 1], c = A[(y + 1) * W + x + 1], d = A[(y + 1) * W + x];
        const idx = (a >= T ? 8 : 0) | (b >= T ? 4 : 0) | (c >= T ? 2 : 0) | (d >= T ? 1 : 0);
        if (idx === 0 || idx === 15) continue;
        const top = () => ptH(x, y), bot = () => ptH(x, y + 1), lef = () => ptV(x, y), rig = () => ptV(x + 1, y);
        switch (idx) {
          case 1: case 14: link(lef(), bot()); break;
          case 2: case 13: link(bot(), rig()); break;
          case 3: case 12: link(lef(), rig()); break;
          case 4: case 11: link(top(), rig()); break;
          case 6: case 9: link(top(), bot()); break;
          case 7: case 8: link(lef(), top()); break;
          case 5:
            if ((a + b + c + d) / 4 >= T) { link(lef(), top()); link(bot(), rig()); } else { link(top(), rig()); link(lef(), bot()); }
            break;
          case 10:
            if ((a + b + c + d) / 4 >= T) { link(top(), rig()); link(lef(), bot()); } else { link(lef(), top()); link(bot(), rig()); }
            break;
          default: break;
        }
      }
    }
    const seen = new Set();
    const loops = [];
    for (const start of adj.keys()) {
      if (seen.has(start)) continue;
      const loop = [];
      let prev = -1, cur = start;
      while (cur !== undefined && !seen.has(cur)) {
        seen.add(cur);
        loop.push(pts.get(cur));
        const nb = adj.get(cur);
        const next = nb[0] !== prev ? nb[0] : nb[1];
        prev = cur;
        cur = next;
      }
      if (loop.length >= 3) loops.push(loop);
    }
    // text space: u from the ink start along the baseline, v up from the baseline (1× px)
    let minU = Infinity, maxU = -Infinity;
    const out = loops.map((lp) => {
      const s = simplifyClosed(lp, 0.12 * scale);
      const f = new Float64Array(s.length * 2);
      for (let i = 0; i < s.length; i++) {
        const u = (s[i][0] - ox) / scale, v = (oy - s[i][1]) / scale;
        f[i * 2] = u;
        f[i * 2 + 1] = v;
        if (u < minU) minU = u;
        if (u > maxU) maxU = u;
      }
      return f;
    });
    for (const f of out) for (let i = 0; i < f.length; i += 2) f[i] -= minU;
    return { contours: orientContours(out), length: maxU - minU };
  }
  function simplifyClosed(p, eps) {
    let far = 0, best = -1;
    for (let i = 1; i < p.length; i++) {
      const d = (p[i][0] - p[0][0]) ** 2 + (p[i][1] - p[0][1]) ** 2;
      if (d > best) { best = d; far = i; }
    }
    const a = dp(p.slice(0, far + 1), eps), b = dp(p.slice(far).concat([p[0]]), eps);
    return a.slice(0, -1).concat(b.slice(0, -1));
  }
  function dp(p, eps) {
    if (p.length < 3) return p;
    const keep = new Uint8Array(p.length);
    keep[0] = keep[p.length - 1] = 1;
    const stack = [[0, p.length - 1]];
    while (stack.length) {
      const [i0, i1] = stack.pop();
      const ax = p[i0][0], ay = p[i0][1], dx = p[i1][0] - ax, dy = p[i1][1] - ay;
      const L = Math.hypot(dx, dy) || 1e-9;
      let md = -1, mi = -1;
      for (let i = i0 + 1; i < i1; i++) {
        const d = Math.abs((p[i][0] - ax) * dy - (p[i][1] - ay) * dx) / L;
        if (d > md) { md = d; mi = i; }
      }
      if (md > eps) {
        keep[mi] = 1;
        stack.push([i0, mi], [mi, i1]);
      }
    }
    const out = [];
    for (let i = 0; i < p.length; i++) if (keep[i]) out.push(p[i]);
    return out;
  }

  // Label sprite: the text rendered once at LAB_SS× with its baseline-left at (pad, pad + ascent).
  function labelSprite(s) {
    const c = document.createElement('canvas');
    const g = c.getContext('2d');
    const font = () => {
      g.font = `500 ${LAB_FS * LAB_SS}px ${R.font.mono}`;
      g.letterSpacing = `${0.12 * LAB_FS * LAB_SS}px`;
      g.textBaseline = 'alphabetic';
    };
    font();
    const m = g.measureText(s);
    const pad = 4 * LAB_SS;
    c.width = Math.ceil(m.width) + 2 * pad;
    c.height = Math.ceil(LAB_FS * LAB_SS * 1.0) + 2 * pad;
    font();
    g.fillStyle = P.ink;
    const oy = pad + Math.ceil(m.actualBoundingBoxAscent);
    g.fillText(s, pad, oy);
    return { c, ox: pad / LAB_SS, oy: oy / LAB_SS };
  }

  R.scene({
    id: 's03-space',
    start: T0,
    end: T_END,
    z: 30,
    bg: P.ink,

    setup(root) {
      // ---- global FX + sound (storyboard) --------------------------------------------------------------
      R.cue(3.75, 'chroma', { amt: 8, dur: 0.2 }); // through the dot into the corridor
      R.cue(3.75, 'zoom', { amt: 0.04, dur: 0.2 }); // box unfold starts
      R.cue(4.21875, 'chroma', { amt: 3, dur: 0.1 }); // roll 1
      R.cue(4.6875, 'chroma', { amt: 4, dur: 0.1 }); // roll 2 + rush
      R.cue(4.921875, 'chroma', { amt: 5, dur: 0.1171875, curve: 0 }); // rush ramp step 1 (held)
      R.cue(4.921875, 'vignette', { amt: 0.5, dur: 0.2008, in: 0.15, out: 0.02 }); // rush tunnel vision
      R.cue(5.0390625, 'chroma', { amt: 9, dur: 0.0838, curve: 0 }); // rush ramp step 2, off at 5.1229

      R.sfx(3.75, 'impact', { amt: 0.7, tone: 'sub' }); // box unfolds
      R.sfx(3.75, 'whoosh', { dur: 0.3515625, dir: 'down' }); // door
      R.sfx(4.21875, 'swish', { amt: 0.5 }); // roll 1
      R.sfx(4.21875, 'click', { pitch: 0.5 }); // roll 1 clunk
      R.sfx(4.6875, 'swish', { amt: 0.6 }); // roll 2
      R.sfx(4.6875, 'click', { pitch: 0.5 }); // roll 2 clunk
      R.sfx(4.6875, 'tick', { pitch: 1.0 }); // ring chase
      R.sfx(4.8046875, 'tick', { pitch: 1.12 });
      R.sfx(4.921875, 'tick', { pitch: 1.26 });
      R.sfx(5.0390625, 'tick', { pitch: 1.5 });
      R.sfx(4.6875, 'whoosh', { dur: 0.46875, dir: 'up' }); // rush, lands 5.15625

      // ---- assets built once ---------------------------------------------------------------------------
      this.words = STYLES.map((s) => traceWord('SPACE', s, 2));
      this.labels = [];
      for (let k = 1; k <= 12; k++) this.labels.push(labelSprite(`03.${k}`));

      // The shutter: a stack of canvases, one sub-frame each, composited by the browser with opacity 1/(i+1)
      // (a running average), so motion blur never forces a canvas read-back or a raster sync.
      this.stack = [];
      for (let i = 0; i < BLUR_MAX; i++) {
        const { canvas, ctx } = R.canvas(root, { alpha: false });
        canvas.style.display = i === 0 ? 'block' : 'none';
        this.stack.push({ canvas, ctx, on: i === 0 });
      }
      this.ctx = this.stack[0].ctx;
      this.q = [0, 0];
    },

    // Number of sub-frames: max on-screen displacement of probe points across the shutter / BLUR_PX.
    blurSamples(t) {
      const ca = camera(t - SHUTTER / 2), cb = camera(t + SHUTTER / 2);
      const pa = [0, 0], pb = [0, 0];
      let maxD = 0;
      const dLo = Math.max(ca.dNear, cb.dNear), dHi = Math.min(ca.dFar, cb.dFar);
      this.maxD = 0;
      if (!(dHi > dLo)) return 1;
      // probes spaced uniformly in on-screen scale k (uniform on screen), from the far wall out to k = 3
      // (well past the frame edge): the fastest on-screen motion is the lettering sweeping out of frame
      const kOf = (d) => PERSP / (PERSP - (ca.D - d * ca.sT));
      const kLo = kOf(dHi), kHi = Math.min(3, kOf(dLo));
      for (let i = 0; i <= 24; i++) {
        const kk = kLo + ((kHi - kLo) * i) / 24;
        const d = R.clamp((PERSP / kk - PERSP + ca.D) / Math.max(1e-6, ca.sT), dLo, dHi);
        for (const fx of [0, 0.5, 1]) {
          projC(ca, CX - (HALF - d * ca.cT) * fx, d, pa);
          projC(cb, CX - (HALF - d * cb.cT) * fx, d, pb);
          for (let w = 0; w < 4; w++) {
            const ra = ca.roll + (w * Math.PI) / 2, rb = cb.roll + (w * Math.PI) / 2;
            const ax = pa[0] - CX, ay = pa[1] - CY, bx = pb[0] - CX, by = pb[1] - CY;
            const Ax = CX + ax * Math.cos(ra) - ay * Math.sin(ra), Ay = CY + ax * Math.sin(ra) + ay * Math.cos(ra);
            const Bx = CX + bx * Math.cos(rb) - by * Math.sin(rb), By = CY + bx * Math.sin(rb) + by * Math.cos(rb);
            const onA = Ax > -60 && Ax < 1980 && Ay > -60 && Ay < 1140, onB = Bx > -60 && Bx < 1980 && By > -60 && By < 1140;
            if (!onA && !onB) continue;
            const dd = Math.hypot(Bx - Ax, By - Ay);
            if (dd > maxD) maxD = dd;
          }
        }
      }
      this.maxD = maxD;
      if (maxD < BLUR_MIN_PX) return 1;
      return Math.max(2, Math.min(BLUR_MAX, Math.ceil(maxD / BLUR_PX)));
    },

    // Draw the corridor at continuous time t with the frame's discrete state {word, lit}.
    draw(ctx, t, disc, dt = 0, k = 1) {
      const c = camera(t);
      const { cT, sT, D, dNear, dFar } = c;
      const q = this.q;
      const hw = (d) => HALF - d * cT; // frustum half-width at depth d
      const shadeOp = R.clamp(c.th / 90);
      const fade = R.seg(t, T_FADE0, T_FADE1, 'inOutSine'); // lettering + labels (storyboard timing)
      const ringFade = R.seg(t, T0, T_FADE0, 'outQuad'); // rings from the first 3D frame: they ripple out of the centre as the box folds

      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1;
      ctx.fillStyle = P.ink;
      ctx.fillRect(0, 0, 1920, 1080);

      // far wall + the dot
      const cr = Math.cos(c.roll), sr = Math.sin(c.roll);
      if (dFar >= DEPTH - 1e-6) {
        const kF = PERSP / (PERSP - (D - DEPTH));
        const h = (HALF + FAR_EXT) * kF, hp = HALF * kF;
        ctx.setTransform(cr, sr, -sr, cr, CX, CY);
        // the overhang (seen only through the flare of the hinge overshoot) continues the walls' far-end tone,
        // so the Paper portal stays exactly the storyboard's 1920 square: it opens and holds instead of
        // swelling to ≈590 px and shrinking back to 369 while the box settles
        ctx.fillStyle = shadeCol(SHADE_MAX);
        ctx.fillRect(-h, -h, 2 * h, 2 * h);
        ctx.fillStyle = P.paper;
        ctx.fillRect(-hp, -hp, 2 * hp, 2 * hp);
        ctx.fillStyle = P.signal;
        ctx.beginPath();
        ctx.arc(0, 0, 28 * kF, 0, R.TAU);
        ctx.fill();
      }

      // one wall (the floor) in unrolled screen space; drawn four times, rotated
      const wall = new Path2D();
      {
        const a = projC(c, CX - hw(dNear), dNear, [0, 0]);
        const b = projC(c, CX + hw(dNear), dNear, [0, 0]);
        const cc = projC(c, CX + hw(dFar), dFar, [0, 0]);
        const d = projC(c, CX - hw(dFar), dFar, [0, 0]);
        // push the two side edges outwards by 1 px so neighbouring faces overlap (no AA seam at the corners)
        const off = (p0, p1, sgn) => {
          const dx = p1[0] - p0[0], dy = p1[1] - p0[1], L = Math.hypot(dx, dy) || 1;
          return [(-dy / L) * sgn, (dx / L) * sgn];
        };
        const oL = off(a, d, -1), oR = off(b, cc, 1);
        wall.moveTo(a[0] + oL[0], a[1] + oL[1]);
        wall.lineTo(b[0] + oR[0], b[1] + oR[1]);
        wall.lineTo(cc[0] + oR[0], cc[1] + oR[1]);
        wall.lineTo(d[0] + oL[0], d[1] + oL[1]);
        wall.closePath();
      }
      // perspective-correct depth shading: the gradient runs from the visible near edge (clamped to the frame's
      // corner radius) to the far edge; 12 stops, denser towards the far end where the perspective curve bends;
      // the depth under each stop is solved exactly (max error vs the true curve ≈ 1 level of 255)
      const yAt = (d) => CY + (HALF - d * cT) * (PERSP / (PERSP - (D - d * sT)));
      const y0 = Math.min(yAt(dNear), CY + 1110), y1 = yAt(dFar);
      const grad = ctx.createLinearGradient(0, y0, 0, y1);
      const NS = 12;
      for (let i = 0; i <= NS; i++) {
        const u = 1 - (1 - i / NS) ** 2;
        const y = y0 + (y1 - y0) * u - CY;
        const d = R.clamp((HALF * PERSP - y * (PERSP - D)) / (y * sT + PERSP * cT), 0, DEPTH);
        grad.addColorStop(u, shadeCol((SHADE_MAX * d * shadeOp) / DEPTH));
      }

      // depth rings + lettering: the union of k copies spread across this sub-frame's slice of the shutter
      // (k > 1 only in the fastest frames), so the averaged sub-frames fuse into a continuous streak instead
      // of stepping into discrete ghost copies; nonzero fill makes overlapping copies a clean union
      const ringsInk = new Path2D(), ringsLit = new Path2D(), text = new Path2D();
      let anyLit = false;
      for (let j = 0; j < k; j++) {
        let cj = c;
        if (k > 1) {
          // a copy carries its own roll relative to the one the walls are painted with (rot below)
          cj = camera(t + dt * ((j + 0.5) / k - 0.5));
          cj.dr = cj.roll - c.roll;
          cj.cdr = Math.cos(cj.dr);
          cj.sdr = Math.sin(cj.dr);
        }
        if (addRings(cj, disc.lit, ringsInk, ringsLit, q)) anyLit = true;
        if (fade > 0) addText(cj, disc.word, text, q);
      }

      // labels: affine frame per label (perspective change across a 70 px label is < 1%)
      const labs = [];
      if (fade > 0) {
        for (let m = 1; m <= 12; m++) {
          const dBase = SLAB * m - RING_W / 2 - LAB_GAP - LAB_CAP; // cap top faces the ring
          if (dBase < dNear + 4 || dBase + LAB_CAP > dFar) continue;
          const x0 = CX - hw(dBase) + 40;
          const o = projC(c, x0, dBase, [0, 0]);
          const u = projC(c, x0 + 60, dBase, [0, 0]);
          const v = projC(c, x0, dBase + LAB_CAP, [0, 0]);
          labs.push([m - 1, (u[0] - o[0]) / 60, (u[1] - o[1]) / 60, -(v[0] - o[0]) / LAB_CAP, -(v[1] - o[1]) / LAB_CAP, o[0], o[1]]);
        }
      }

      // ---- paint the four walls (the floor rotated by roll + w·90° about the centre) ---------------------
      const rot = (w) => {
        const a = c.roll + (w * Math.PI) / 2, ca = Math.cos(a), sa = Math.sin(a);
        ctx.setTransform(ca, sa, -sa, ca, CX - (ca * CX - sa * CY), CY - (sa * CX + ca * CY));
      };
      ctx.fillStyle = grad;
      for (let w = 0; w < 4; w++) {
        rot(w);
        ctx.fill(wall);
      }
      if (ringFade <= 0) return;
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      for (let w = 0; w < 4; w++) {
        rot(w);
        ctx.save();
        ctx.clip(wall);
        ctx.globalAlpha = ringFade;
        ctx.fillStyle = P.ink;
        ctx.fill(ringsInk);
        if (anyLit) {
          ctx.fillStyle = P.paper;
          ctx.fill(ringsLit);
        }
        if (fade > 0) {
          ctx.globalAlpha = fade;
          ctx.fillStyle = P.ink;
          ctx.fill(text, 'nonzero');
          for (const L of labs) {
            const sp = this.labels[L[0]];
            rot(w);
            ctx.transform(L[1], L[2], L[3], L[4], L[5], L[6]);
            ctx.drawImage(sp.c, -sp.ox, -sp.oy, sp.c.width / LAB_SS, sp.c.height / LAB_SS);
          }
        }
        ctx.restore();
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1;
    },

    update(lt, p, t) {
      const ctx = this.ctx;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1;

      // ---- flat handoff frames -------------------------------------------------------------------------
      if (lt < 0.5 / 60 || t >= T_REST - 1e-6) {
        this.stack[0].canvas.style.opacity = '1';
        for (let i = 1; i < BLUR_MAX; i++) this.show(i, false);
      }
      if (lt < 0.5 / 60) {
        ctx.fillStyle = P.signal;
        ctx.fillRect(0, 0, 1920, 1080);
        return;
      }
      if (t >= T_REST - 1e-6) {
        ctx.fillStyle = P.paper;
        ctx.fillRect(0, 0, 1920, 1080);
        ctx.fillStyle = P.signal;
        ctx.beginPath();
        ctx.arc(CX, CY, 28, 0, R.TAU);
        ctx.fill();
        return;
      }

      // ---- the corridor, motion blurred ------------------------------------------------------------------
      const disc = { word: this.words[styleAt(t)], lit: litRings(Math.round(t * 60)) };
      const n = this.blurSamples(t);
      this.nSamples = n;
      // when the shutter is capped, each sub-frame also sweeps its own slice (copies ≤ COPY_PX apart)
      const k = n > 1 ? Math.max(1, Math.min(COPY_MAX, Math.ceil(this.maxD / n / COPY_PX))) : 1;
      this.nCopies = k;
      for (let i = 0; i < BLUR_MAX; i++) {
        const L = this.stack[i];
        if (i < n) {
          const ts = n === 1 ? t : t - SHUTTER / 2 + ((i + 0.5) * SHUTTER) / n;
          this.draw(L.ctx, ts, disc, SHUTTER / n, k);
          L.canvas.style.opacity = (1 / (i + 1)).toFixed(6);
        }
        this.show(i, i < n);
      }
    },

    show(i, on) {
      const L = this.stack[i];
      if (L.on !== on) {
        L.on = on;
        L.canvas.style.display = on ? 'block' : 'none';
      }
    },
  });
})();
