// s03-space — Space: the corridor (3.75 → 5.15625 s, frames 225–309, bar 3 beats 1–3)
//
// A square type corridor seen through the storyboard's CSS-3D camera (perspective 1000px, origin 960/540;
// world = translateZ(D) rotateZ(roll); each wall = the floor hinged on its near edge by rotateX(θ), cloned at
// 90° steps round the corridor axis). Chromium's preserve-3d path mis-sorts intersecting planes, drops tiles
// near the camera and minifies wall textures without mipmaps (4 px depth rings break into dashes), so the
// same camera is evaluated here analytically and drawn on one Canvas 2D:
//   * walls are the four faces of a square frustum (a rigid hinged rectangle clipped where it passes behind
//     its neighbours), so no two faces ever overlap on screen and the draw order is exact at every fold angle;
//     during the >90° hinge overshoot the faces flare and still meet at the corners;
//   * depth shading is a perspective-correct gradient (stops solved in screen space);
//   * "SPACE" is vector type: glyph outlines traced from Archivo at setup, every vertex projected per frame,
//     so the letters stay razor sharp from 0.19× to 2.5×; rings and labels are projected quads / affine text.
// First frame (flat Signal) and the two rest frames (Paper + Ø56 dot) are drawn flat, so both handoffs are exact.
(() => {
  const P = R.pal;

  // ---- timing (global seconds) -------------------------------------------------------------------------
  const T0 = 3.75;
  const T_END = 5.15625;
  const T_ROLL1 = 4.21875; // snare: roll 1, words -> wght 100, dolly starts
  const T_ROLL2 = 4.6875; // beat 3: roll 2, words -> wght 900 / 62%, rush starts
  const T_REST = T_END - 2 / 60; // 5.1229: flat rest pose (frames 308-309)
  const T_RUSH_END = 308 / 60; // the rush lands exactly on the first rest frame
  const T_FADE0 = 3.8671875, T_FADE1 = 3.984375; // rings / labels / lettering fade in
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
  const NEAR_EXT = 320; // walls continue 320 px in front of the hinge line: invisible while unfolding, but
  //                        they keep the frame corners inside the corridor when it rolls before the dolly
  const RING_W = 4, RING_LIT_W = 10; // depth ring width; a lit (Paper) ring is drawn heavier so the chase reads
  const SHADE_MAX = 0.7;

  // Lettering: Archivo 440 px, tracking -0.01em, two instances per wall starting at depths 150 and 2250,
  // baseline along the depth axis reading near -> far, glyph tops to screen-left on the floor, cap band centred.
  const FS = 440;
  const CAP = 0.6875 * FS;
  const WORD_AT = [150, 2250];
  const STYLES = [
    { w: 900, kw: 'expanded' }, // 125%
    { w: 100, kw: 'expanded' }, // 125%, hairline (roll 1)
    { w: 900, kw: 'extra-condensed' }, // 62.5% (canvas keyword; DOM would be 62%)
  ];
  const X_BASE = CX + CAP / 2; // baseline x on the floor (tops point to -x)

  // Labels "03.1".."03.12": JetBrains Mono 500 20 px, 40 px in from each ring's left end, on the ring's near side.
  const LAB_FS = 20, LAB_CAP = 0.73 * LAB_FS, LAB_GAP = 8;

  const SIG = R.col(P.signal), INKC = R.col(P.ink);
  const shadeCol = (a) =>
    `rgb(${Math.round(SIG[0] + (INKC[0] - SIG[0]) * a)},${Math.round(SIG[1] + (INKC[1] - SIG[1]) * a)},${Math.round(SIG[2] + (INKC[2] - SIG[2]) * a)})`;

  const styleAt = (t) => (t < T_ROLL1 ? 0 : t < T_ROLL2 ? 1 : 2);
  const foldAngle = (t) => 90 * R.spring(t - T0, HINGE);
  const rollAngle = (t) => 90 * R.spring(t - T_ROLL1, ROLL) + 90 * R.spring(t - T_ROLL2, ROLL);
  function dolly(t) {
    if (t < T_ROLL1) return 0;
    if (t < T_ROLL2) return 1200 * R.ease.glide((t - T_ROLL1) / (T_ROLL2 - T_ROLL1));
    if (t < T_RUSH_END) return 1200 + 3000 * R.ease.whip((t - T_ROLL2) / (T_RUSH_END - T_ROLL2));
    return DEPTH;
  }

  // ---- glyph outline tracing (setup only) ---------------------------------------------------------------
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
    const kH = (x, y) => (y * W + x) * 2; // edge (x,y)-(x+1,y)
    const kV = (x, y) => (y * W + x) * 2 + 1; // edge (x,y)-(x,y+1)
    const ptH = (x, y) => {
      const k = kH(x, y);
      if (!pts.has(k)) {
        const a = A[y * W + x], b = A[y * W + x + 1];
        pts.set(k, [x + (T - a) / (b - a) + 0.5, y + 0.5]);
      }
      return k;
    };
    const ptV = (x, y) => {
      const k = kV(x, y);
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
          case 5: {
            if ((a + b + c + d) / 4 >= T) { link(lef(), top()); link(bot(), rig()); }
            else { link(top(), rig()); link(lef(), bot()); }
            break;
          }
          case 10: {
            if ((a + b + c + d) / 4 >= T) { link(top(), rig()); link(lef(), bot()); }
            else { link(lef(), top()); link(bot(), rig()); }
            break;
          }
          default: break;
        }
      }
    }
    // walk closed loops
    const seen = new Set();
    const loops = [];
    for (const start of adj.keys()) {
      if (seen.has(start)) continue;
      const loop = [];
      let prev = -1, cur = start;
      while (!seen.has(cur)) {
        seen.add(cur);
        loop.push(pts.get(cur));
        const nb = adj.get(cur);
        const next = nb[0] !== prev ? nb[0] : nb[1];
        prev = cur;
        cur = next;
        if (cur === undefined) break;
      }
      if (loop.length >= 3) loops.push(loop);
    }
    // to text space: u from the ink start along the baseline, v up from the baseline (1× px)
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
    return { contours: out, length: maxU - minU };
  }
  function simplifyClosed(p, eps) {
    // split at the point farthest from p[0], then Douglas-Peucker both halves
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
      const ax = p[i0][0], ay = p[i0][1], bx = p[i1][0], by = p[i1][1];
      const dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy) || 1e-9;
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

      // ---- vector lettering --------------------------------------------------------------------------
      this.words = STYLES.map((s) => traceWord('SPACE', s, 2));

      const { canvas, ctx } = R.canvas(root, { alpha: false });
      this.cv = canvas;
      this.ctx = ctx;
      this.labFont = `500 ${LAB_FS}px ${R.font.mono}`;
    },

    update(lt, p, t) {
      const ctx = this.ctx;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1;

      // ---- flat handoff frames -------------------------------------------------------------------------
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

      // ---- camera state ------------------------------------------------------------------------------
      const f = Math.round(t * 60);
      const th = foldAngle(t);
      const thR = (th * Math.PI) / 180;
      const cT = Math.cos(thR), sT = Math.sin(thR);
      const roll = (rollAngle(t) * Math.PI) / 180;
      const D = dolly(t);
      const shadeOp = R.clamp(th / 90);
      const fade = R.seg(t, T_FADE0, T_FADE1, 'inOutSine'); // lettering + labels (storyboard timing)
      const ringFade = R.seg(t, T0, T_FADE0, 'outCubic'); // rings from the first 3D frame: they ripple out of the centre as the box folds
      const word = this.words[styleAt(t)];

      // floor point (x across, d = depth from the hinge) -> screen, before the roll
      const proj = (x, d, out) => {
        const k = PERSP / (PERSP - (D - d * sT));
        out[0] = CX + (x - CX) * k;
        out[1] = CY + (HALF - d * cT) * k;
        return out;
      };
      const hw = (d) => HALF - d * cT; // frustum half-width at depth d
      const dNear = sT > 1e-6 ? Math.max(-NEAR_EXT, (D - Z_NEAR) / sT) : -NEAR_EXT;
      const dFar = cT > 1e-6 ? Math.min(DEPTH, HALF / cT) : DEPTH;
      const yAt = (d) => CY + (HALF - d * cT) * (PERSP / (PERSP - (D - d * sT)));

      // ---- background + far wall -----------------------------------------------------------------------
      ctx.fillStyle = P.ink;
      ctx.fillRect(0, 0, 1920, 1080);
      const kF = PERSP / (PERSP - (D - DEPTH));
      ctx.setTransform(Math.cos(roll), Math.sin(roll), -Math.sin(roll), Math.cos(roll), CX, CY);
      if (dFar >= DEPTH - 1e-6) {
        const h = (HALF + FAR_EXT) * kF;
        ctx.fillStyle = P.paper;
        ctx.fillRect(-h, -h, 2 * h, 2 * h);
        ctx.fillStyle = P.signal;
        ctx.beginPath();
        ctx.arc(0, 0, 28 * kF, 0, R.TAU);
        ctx.fill();
      }

      // ---- one wall, in unrolled screen space (drawn four times, rotated) ----------------------------------
      const q = [0, 0];
      const wall = new Path2D();
      const e = 1.0; // screen-px overlap along the corner edges (no AA seam between neighbouring faces)
      {
        const a = proj(CX - hw(dNear), dNear, [0, 0]);
        const b = proj(CX + hw(dNear), dNear, [0, 0]);
        const c = proj(CX + hw(dFar), dFar, [0, 0]);
        const d = proj(CX - hw(dFar), dFar, [0, 0]);
        // push the two side edges outwards by e px
        const off = (p0, p1, sgn) => {
          const dx = p1[0] - p0[0], dy = p1[1] - p0[1], L = Math.hypot(dx, dy) || 1;
          return [(-dy / L) * e * sgn, (dx / L) * e * sgn];
        };
        const oL = off(a, d, -1), oR = off(b, c, 1);
        wall.moveTo(a[0] + oL[0], a[1] + oL[1]);
        wall.lineTo(b[0] + oR[0], b[1] + oR[1]);
        wall.lineTo(c[0] + oR[0], c[1] + oR[1]);
        wall.lineTo(d[0] + oL[0], d[1] + oL[1]);
        wall.closePath();
      }
      // perspective-correct depth shading: stops placed uniformly in screen y, depth solved per stop
      const y0 = yAt(dNear), y1 = yAt(dFar);
      const grad = ctx.createLinearGradient(0, y0, 0, y1);
      const NS = 28;
      for (let i = 0; i <= NS; i++) {
        const y = y0 + ((y1 - y0) * i) / NS - CY;
        const d = R.clamp((HALF * PERSP - y * (PERSP - D)) / (y * sT + PERSP * cT), 0, DEPTH);
        grad.addColorStop(i / NS, shadeCol((SHADE_MAX * d * shadeOp) / DEPTH));
      }

      // depth rings: quads at d = 350 r (a lit ring is Paper and heavier)
      const lit = new Set();
      for (const tc of CHASE) {
        const i = f - Math.ceil(tc * 60 - 1e-6);
        if (i >= 0) { lit.add(11 - i); lit.add(12 - i); }
      }
      const ringsInk = new Path2D(), ringsLit = new Path2D();
      for (let r = 1; r <= 11; r++) {
        const on = lit.has(r);
        const d = SLAB * r, hwid = (on ? RING_LIT_W : RING_W) / 2;
        if (d - hwid < dNear || d + hwid > dFar) continue;
        const pth = on ? ringsLit : ringsInk;
        const d0 = d - hwid, d1 = d + hwid;
        const a = proj(CX - hw(d0) - 2, d0, [0, 0]), b = proj(CX + hw(d0) + 2, d0, [0, 0]);
        const c = proj(CX + hw(d1) + 2, d1, [0, 0]), dd = proj(CX - hw(d1) - 2, d1, [0, 0]);
        pth.moveTo(a[0], a[1]); pth.lineTo(b[0], b[1]); pth.lineTo(c[0], c[1]); pth.lineTo(dd[0], dd[1]); pth.closePath();
      }

      // lettering: every outline vertex projected; contours clipped at the near plane (d >= dNear)
      const text = new Path2D();
      for (const s0 of WORD_AT) {
        if (s0 + word.length < dNear) continue;
        for (const cn of word.contours) {
          const n = cn.length / 2;
          // fast path: whole contour in front of the near plane
          let allIn = true, anyIn = false;
          for (let i = 0; i < n; i++) {
            const dd = s0 + cn[i * 2];
            if (dd < dNear) allIn = false; else anyIn = true;
          }
          if (!anyIn) continue;
          if (allIn) {
            for (let i = 0; i < n; i++) {
              proj(X_BASE - cn[i * 2 + 1], s0 + cn[i * 2], q);
              if (i === 0) text.moveTo(q[0], q[1]); else text.lineTo(q[0], q[1]);
            }
            text.closePath();
          } else {
            // Sutherland-Hodgman against d >= dNear in the wall plane
            const poly = [];
            for (let i = 0; i < n; i++) {
              const ax = X_BASE - cn[i * 2 + 1], ad = s0 + cn[i * 2];
              const j = (i + 1) % n;
              const bx = X_BASE - cn[j * 2 + 1], bd = s0 + cn[j * 2];
              const ain = ad >= dNear, bin = bd >= dNear;
              if (ain) poly.push([ax, ad]);
              if (ain !== bin) {
                const k = (dNear - ad) / (bd - ad);
                poly.push([ax + (bx - ax) * k, dNear]);
              }
            }
            if (poly.length < 3) continue;
            for (let i = 0; i < poly.length; i++) {
              proj(poly[i][0], poly[i][1], q);
              if (i === 0) text.moveTo(q[0], q[1]); else text.lineTo(q[0], q[1]);
            }
            text.closePath();
          }
        }
      }

      // labels: affine frame per label (perspective change across a 70 px label is < 1%)
      const labels = [];
      for (let k = 1; k <= 12; k++) {
        const dTop = SLAB * k - 2 - LAB_GAP; // cap top, facing the ring
        const dBase = dTop - LAB_CAP;
        if (dBase < dNear + 4 || dTop > dFar) continue;
        const x0 = CX - hw(dBase) + 40;
        const o = proj(x0, dBase, [0, 0]);
        const ux = proj(x0 + 60, dBase, [0, 0]);
        const vy = proj(x0, dBase + LAB_CAP, [0, 0]);
        labels.push({ s: `03.${k}`, m: [(ux[0] - o[0]) / 60, (ux[1] - o[1]) / 60, -(vy[0] - o[0]) / LAB_CAP, -(vy[1] - o[1]) / LAB_CAP, o[0], o[1]] });
      }

      // ---- draw the four walls (the floor rotated by roll + w·90° about the centre) ----------------------
      const rot = (w) => {
        const a = roll + (w * Math.PI) / 2, ca = Math.cos(a), sa = Math.sin(a);
        ctx.setTransform(ca, sa, -sa, ca, CX - (ca * CX - sa * CY), CY - (sa * CX + ca * CY));
      };
      ctx.fillStyle = grad;
      for (let w = 0; w < 4; w++) {
        rot(w);
        ctx.fill(wall);
      }
      if (ringFade > 0) {
        ctx.font = this.labFont;
        ctx.letterSpacing = `${0.12 * LAB_FS}px`;
        ctx.textBaseline = 'alphabetic';
        for (let w = 0; w < 4; w++) {
          rot(w);
          ctx.save();
          ctx.clip(wall);
          ctx.globalAlpha = ringFade;
          ctx.fillStyle = P.ink;
          ctx.fill(ringsInk);
          ctx.fillStyle = P.paper;
          ctx.fill(ringsLit);
          if (fade > 0) {
            ctx.globalAlpha = fade;
            ctx.fillStyle = P.ink;
            ctx.fill(text, 'evenodd');
            for (const L of labels) {
              rot(w);
              const m = L.m;
              ctx.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
              ctx.fillText(L.s, 0, 0);
            }
          }
          ctx.restore();
        }
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1;
    },
  });
})();
