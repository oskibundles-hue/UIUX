/* sekit2.js -- the SE vlog Locked-On kit, set 2: seven more variations (G3, B4, C4, C5, I4, I5, I6).
 *
 * Same contract as lib/sekit.js: every component is a factory SEK.<type>(cfg) -> { code, render(t) }, render(t) is a
 * PURE function of t, and the look is the same (gold #FBD101 the only accent, black plates, white type, the 78/22
 * stripe always horizontal, Bebas + Michroma, text inside x 54-907 / y 269-1536). What is new is DEPTH: set 2 draws
 * some elements BEHIND the people and cars in the footage, cuts windows into the picture, and lights the car itself.
 *
 * Passes. A component can put elements on three layers, each its own root under the stage:
 *   front (default)   composited over everything, like set 1
 *   .pass-back        composited over the plate and then UNDER the subject: the compositor re-lays the subject on top
 *                     through its matte (window.FX.depth = {matte}), so type sits between the background and the car
 *   .pass-mask        white shapes whose alpha is a window: inside it the compositor shows the shot's B plate
 * lib/kcapture2.js captures each pass that is in use at a frame (window.FX.back / window.FX.mask) as its own PNG.
 *
 * Compositor instructions (window.FX, per frame, read by lib/compose2.py):
 *   depth {matte}                  re-lay the subject over the back pass
 *   pop {matte, amt}               the picture outside the car darkens and desaturates, the car lifts (C4)
 *   sweep {x, k, w, gain, glob, matte}   a slanted light band lights the car body (I6); centre line x + k * (y - 960)
 *   grade {sat, con}               saturation / contrast on the plate (I6 freeze)
 *   flash {a}                      warm white flash on the plate (freeze frames)
 *
 * Context adds (kit2.html): CTX.pt(x, y, t) maps a point on the SOURCE frame (1080x1920 units) to the screen through the
 * shot's Ken Burns; CTX.plane(name, t) -> the tracked quad [TL, TR, BR, BL] on screen or null (lib/data/plane.json,
 * 59.94 fps source frames); CTX.data('contours') -> car outlines traced from the Vision mattes (build2.py prep).
 */
(function () {
  const SEK = window.SEK, H = SEK.helpers;
  const E = KT.ease, P = KT.p, cl = KT.cl, lerp = KT.lerp;
  const FPS = 30000 / 1001, GOLD = '#FBD101', SAFE = SEK.SAFE;
  const f2 = v => v.toFixed(2);
  let stage = null, CTX = null;
  const init0 = SEK.init;
  SEK.init = (st, ctx) => { init0(st, ctx); stage = st; CTX = ctx; };

  const root = (pass, css = '') => H.el('div', 'a' + (pass ? ' pass-' + pass : ''), stage, 'width:1080px;height:1920px;' + css);
  const flag = k => { window.FX[k] = 1; };
  // per-glyph masked rise in, and the mirrored sink out (RELEASE: each glyph leaves the way it came, last in first out)
  function riseSink(g, t, tin, tout, o = {}) {
    const sg = o.stagger ?? 0.045, d = o.dur ?? 0.5, dy = o.dy ?? 1.15, so = o.outStagger ?? 0.03, dout = o.outDur ?? 0.3, n = g.length;
    g.forEach((s, i) => {
      const qi = E.outExpo(P(t, tin + i * sg, tin + i * sg + d));
      const qo = tout == null ? 0 : E.inExpo(P(t, tout + (n - 1 - i) * so, tout + (n - 1 - i) * so + dout));
      s.style.transform = `translateY(${f2((1 - qi + qo) * dy * (s._h || 100))}px)`;
      s.style.opacity = qi > 0 && qo < 1 ? 1 : 0;
    });
  }
  // stripe: draws L->R on the way in, retracts to the right on the way out
  function stripeIO(st, t, tin, tout, din = 0.4, dout = 0.26) {
    const qi = E.outExpo(P(t, tin, tin + din)), qo = tout == null ? 0 : E.inExpo(P(t, tout, tout + dout));
    st.style.transformOrigin = qo > 0 ? 'right center' : 'left center';
    st.style.transform = `scaleX(${(qo > 0 ? 1 - qo : qi).toFixed(5)})`;
    st.style.opacity = qi > 0 && qo < 1 ? 1 : 0;
  }
  const fadeIO = (t, tin, din, tout, dout) => cl(P(t, tin, tin + din)) * (tout == null ? 1 : 1 - E.inCubic(P(t, tout, tout + dout)));

  // ------------------------------------------------------------------ geometry for the plane lock
  // square -> quad homography: (u, v) in the unit square maps to the quad [TL(0,0), TR(1,0), BR(1,1), BL(0,1)]
  function sq2quad(q) {
    const [x0, y0] = q[0], [x1, y1] = q[1], [x2, y2] = q[2], [x3, y3] = q[3];
    const dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2, sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
    let g = 0, h = 0;
    if (Math.abs(sx) > 1e-9 || Math.abs(sy) > 1e-9) { const det = dx1 * dy2 - dx2 * dy1; g = (sx * dy2 - dx2 * sy) / det; h = (dx1 * sy - sx * dy1) / det; }
    return { a: x1 - x0 + g * x1, b: x3 - x0 + h * x3, c: x0, d: y1 - y0 + g * y1, e: y3 - y0 + h * y3, f: y0, g, h };
  }
  const hmap = (M, u, v) => { const w = M.g * u + M.h * v + 1; return [(M.a * u + M.b * v + M.c) / w, (M.d * u + M.e * v + M.f) / w]; };
  const lerpP = (a, b, q) => [lerp(a[0], b[0], q), lerp(a[1], b[1], q)];
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const toward = (a, b, L) => { const d = dist(a, b) || 1; return [a[0] + (b[0] - a[0]) * L / d, a[1] + (b[1] - a[1]) * L / d]; };
  const pathOf = (pts, close) => 'M' + pts.map(p => f2(p[0]) + ',' + f2(p[1])).join('L') + (close ? 'Z' : '');
  // a polyline's cumulative lengths; point + prefix at a length (for the live tip and partial dashed paths)
  function polyLen(pts) { const c = [0]; for (let i = 1; i < pts.length; i++) c.push(c[i - 1] + dist(pts[i - 1], pts[i])); return c; }
  function pointAt(pts, cum, L) {
    L = cl(L / cum[cum.length - 1]) * cum[cum.length - 1];
    let i = 1; while (i < cum.length - 1 && cum[i] < L) i++;
    const k = (L - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]);
    return { p: lerpP(pts[i - 1], pts[i], cl(k)), i };
  }
  function prefix(pts, cum, L) { if (L <= 0) return []; const a = pointAt(pts, cum, L); return pts.slice(0, a.i).concat([a.p]); }
  function underOver(svg, wU, wO, colO = GOLD) {
    const u = H.svgEl('path', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': wU, 'stroke-linecap': 'square', 'stroke-linejoin': 'round' }, svg);
    const o = H.svgEl('path', { fill: 'none', stroke: colO, 'stroke-width': wO, 'stroke-linecap': 'square', 'stroke-linejoin': 'round' }, svg);
    return { u, o, set(d, extra = {}) { [u, o].forEach(e => { e.setAttribute('d', d); for (const k in extra) e.setAttribute(k, extra[k]); }); } };
  }
  function glowDefs(svg, id) {
    const defs = H.svgEl('defs', {}, svg);
    const g = H.svgEl('radialGradient', { id }, defs);
    H.svgEl('stop', { offset: '0%', 'stop-color': '#FFFFFF', 'stop-opacity': 1 }, g);
    H.svgEl('stop', { offset: '28%', 'stop-color': '#FFF2B0', 'stop-opacity': .9 }, g);
    H.svgEl('stop', { offset: '60%', 'stop-color': GOLD, 'stop-opacity': .35 }, g);
    H.svgEl('stop', { offset: '100%', 'stop-color': GOLD, 'stop-opacity': 0 }, g);
  }

  // ================================================================== B4 NAME BEHIND
  // The host's name, huge, set BEHIND him: the letters rise from their baseline just above his head and his hair and
  // shoulders cover their lower edge (person matte, per frame). HOST + handle ride in front. The name drifts with the
  // face at a fraction of its motion, so it reads as part of the scene rather than stuck to him.
  // p: {track, matte, name, handle, kicker, maxW, maxS, lift (baseline above the face box), fx, fy, acquire, exit, cx}
  SEK.nameBehind = function (cfg) {
    const p = Object.assign({ track: 'face1', matte: 'host1', name: 'OMARIE', handle: '@NQ.YOUNG', kicker: 'HOST', maxW: 800, maxS: 420,
      lift: 58, fx: 0.3, fy: 0.6, cx: 480, acquire: cfg.t0 + 0.2, exit: cfg.t1 - 0.45 }, cfg.p);
    p.maxW = Math.min(p.maxW, 740);                  // room to drift with the face and stay inside x 54-907
    const back = root('back'), front = root();
    const S = H.fitSize(p.name, p.maxW, p.maxS), cap = H.ink('Bebas', S, 'H').aA, tw = H.ink('Bebas', S, p.name).w;
    const hb = H.el('div', 'a', back, 'width:1080px;height:1920px');
    // the mask's bottom edge is the letters' baseline: they rise out of it (and out from behind him)
    const mask = H.el('div', 'a', hb, `left:0;top:0;width:1080px;height:${Math.round(cap + 24)}px;overflow:hidden`);
    const ti = H.line(mask, 'Bebas', S, p.name, p.cx - tw / 2, 20, '#fff');
    ti.t.style.textShadow = '0 8px 30px rgba(0,0,0,.35)';
    const st = H.el('div', 'a stripe', hb, `left:${f2(p.cx - tw / 2)}px;top:${f2(20 + cap + 18)}px;width:${f2(tw)}px;height:10px`);
    const hf = H.el('div', 'a', front, 'width:1080px;height:1920px');
    const kw = H.ink('Michroma', 20, p.kicker, 0.3).w;
    const kk = H.line(hf, 'Michroma', 20, p.kicker, p.cx - tw / 2 + 4, -44, GOLD, { ls: 0.3 });
    const hd = H.line(hf, 'Michroma', 24, p.handle, p.cx - tw / 2 + 4 + kw + 38, -46, '#fff', { ls: 0.12 });
    const dotU = H.el('div', 'a', hf, `left:${f2(p.cx - tw / 2 + 4 + kw + 17)}px;top:-38px;width:6px;height:6px;background:${GOLD};border-radius:50%`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; H.show(back, on); H.show(front, on); if (!on) return;
      const b = CTX.box(p.track, t), b0 = CTX.box(p.track, p.acquire) || b;
      if (!b) { H.show(back, false); H.show(front, false); return; }
      const top0 = cl(b0.y - p.lift - cap - 20, SAFE.y0 + 50, 1300);
      // drift with the face, clamped so the name's box never leaves the safe area (x 54-907)
      const x = cl(p.fx * ((b.x + b.w / 2) - (b0.x + b0.w / 2)), SAFE.x0 + 6 - (p.cx - tw / 2), SAFE.x1 - 6 - (p.cx + tw / 2)), y = top0 + p.fy * (b.y - b0.y);
      hb.style.transform = hf.style.transform = `translate(${f2(x)}px,${f2(y)}px)`;
      riseSink(ti.g, t, p.acquire, p.exit, { stagger: 0.05, dur: 0.52 });
      stripeIO(st, t, p.acquire + 0.32, p.exit + 0.1);
      H.glint(ti, t, p.acquire + 1.0, 0.55, { w: 0.2, glow: 12 });
      KT.track(kk.g, t, { start: p.acquire + 0.42, dur: 0.36, spread: 1.8 }); KT.track(hd.g, t, { start: p.acquire + 0.5, dur: 0.36, spread: 1.6 });
      const fo = fadeIO(t, p.acquire + 0.42, 0.12, p.exit, 0.22);
      kk.w.style.opacity = hd.w.style.opacity = fo.toFixed(3); dotU.style.opacity = fo.toFixed(3);
      flag('back'); window.FX.depth = { matte: p.matte };
    } };
  };

  // ================================================================== G3 DEPTH TITLE
  // The chapter title stands BETWEEN the background and the cars: the letters rise from behind the lineup (the cars and
  // the people in front of them cover their lower edge through the still's matte), the stripe and the tag sit in front.
  // The plate is a still with a 2.5D push: the background, the title and the cars scale at three rates (build2.py sets
  // the plate's bg / fg push, this sets the title's), so the title visibly sits between them.
  // p: {tag, pre, title, y (cap top), cx, maxW, maxS, push [s0, s1], anchor [x, y], matte, acquire, exit}
  SEK.depthTitle = function (cfg) {
    const p = Object.assign({ tag: 'CH 04', pre: 'THE', title: 'LINEUP', y: 720, cx: 480, maxW: 853, maxS: 460, push: [1, 1.05], anchor: [480, 980],
      matte: 'lineup', acquire: cfg.t0 + 0.1, exit: cfg.t1 - 0.5 }, cfg.p);
    const back = root('back'), front = root();
    const S = H.fitSize(p.title, p.maxW, p.maxS), cap = H.ink('Bebas', S, 'H').aA, tw = H.ink('Bebas', S, p.title).w, x0 = p.cx - tw / 2;
    const org = `transform-origin:${p.anchor[0]}px ${p.anchor[1]}px`;
    const hb = H.el('div', 'a', back, 'width:1080px;height:1920px;' + org);
    const mask = H.el('div', 'a', hb, `left:0;top:${f2(p.y - 30)}px;width:1080px;height:${f2(cap + 30 + 14)}px;overflow:hidden`);
    const ti = H.line(mask, 'Bebas', S, p.title, x0, 30, '#fff');
    ti.t.style.textShadow = '0 10px 40px rgba(0,0,0,.4)';
    const hf = H.el('div', 'a', front, 'width:1080px;height:1920px;' + org);
    const preS = Math.round(S * 0.3), preCap = H.ink('Bebas', preS, 'H').aA;
    const preM = H.el('div', 'a', hf, `left:0;top:${f2(p.y - 26 - preCap - 12)}px;width:1080px;height:${f2(preCap + 24)}px;overflow:hidden`);
    const pre = H.line(preM, 'Bebas', preS, p.pre, x0 + 2, 12, '#fff');
    const tgw = H.ink('Michroma', 22, p.tag, 0.3).w;
    const tag = H.line(hf, 'Michroma', 22, p.tag, x0 + tw - tgw, p.y - 26 - H.ink('Michroma', 22, 'H').aA - 14, GOLD, { ls: 0.3, dots: '#fff' });
    const st = H.el('div', 'a stripe', hf, `left:${f2(x0)}px;top:${f2(p.y - 18)}px;width:${f2(tw)}px;height:8px`);
    const edge = H.el('div', 'a edge', hf, `left:${f2(x0)}px;top:${f2(p.y - 26)}px;height:24px;opacity:0`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; H.show(back, on); H.show(front, on); if (!on) return;
      const u = 0.5 - 0.5 * Math.cos(Math.PI * cl((t - cfg.t0) / (cfg.t1 - cfg.t0)));
      const s = lerp(p.push[0], p.push[1], u);
      hb.style.transform = hf.style.transform = `scale(${s.toFixed(5)})`;
      riseSink(ti.g, t, p.acquire, p.exit, { stagger: 0.045, dur: 0.6, dy: 1.1 });
      const qi = E.outExpo(P(t, p.acquire + 0.14, p.acquire + 0.54));
      stripeIO(st, t, p.acquire + 0.14, p.exit + 0.12);
      edge.style.opacity = (qi > 0 && qi < 1 ? Math.sin(Math.PI * qi) : 0).toFixed(3); edge.style.transform = `translateX(${f2(tw * qi)}px)`;
      riseSink(pre.g, t, p.acquire + 0.26, p.exit + 0.05, { stagger: 0.04, dur: 0.4 });
      KT.track(tag.g, t, { start: p.acquire + 0.34, dur: 0.4, spread: 2 });
      tag.w.style.opacity = fadeIO(t, p.acquire + 0.34, 0.1, p.exit, 0.24).toFixed(3);
      H.glint(ti, t, p.acquire + 1.3, 0.6, { w: 0.2, glow: 14 });
      flag('back'); window.FX.depth = { matte: p.matte };
    } };
  };

  // ================================================================== C5 ORBIT BRACKETS (surface lock)
  // The lock is pinned to a SURFACE of the car (a planar track: a homography per source frame, lib/plane_track.py), so
  // the brackets skew and turn with the car as the camera moves round it, where C1-C3 only follow position and scale.
  // ACQUIRE: a flat screen-aligned box closes onto the car and BENDS onto the surface; DRAW: a perspective grid and a
  // scan line sweep the panel, a ruler runs along the sill; READ: the tag; RELEASE: the brackets straighten back into a
  // flat box and collapse. p: {plane, make, model, acquire, exit, pad [u, v], grid [nu, nv], follow}
  SEK.orbitLock = function (cfg) {
    const p = Object.assign({ plane: 'urusSide', make: 'LAMBORGHINI', model: 'URUS', acquire: cfg.t0 + 0.1, exit: cfg.t1 - 0.4,
      pad: [0.42, 0.24, 0.3, 0.2], grid: [9, 4], follow: 0.5 }, cfg.p);
    const R = root(), svg = H.svgRoot(R);
    const gridG = H.svgEl('g', { fill: 'none', stroke: GOLD, 'stroke-width': 1.4 }, svg);
    const gl = []; for (let k = 0; k < p.grid[0] - 1 + p.grid[1] - 1; k++) gl.push(H.svgEl('path', {}, gridG));
    const scanU = H.svgEl('path', { fill: 'none', stroke: 'rgba(255,242,176,.25)', 'stroke-width': 14 }, svg);
    const scan = H.svgEl('path', { fill: 'none', stroke: '#FFF7D6', 'stroke-width': 3 }, svg);
    const ruler = underOver(svg, 6, 2);
    const edgesU = H.svgEl('path', { fill: 'none', stroke: 'rgba(251,209,1,.35)', 'stroke-width': 1.5 }, svg);
    const br = underOver(svg, 11, 5);
    const ping = H.svgEl('path', { fill: 'none', stroke: GOLD, 'stroke-width': 2 }, svg);
    const lead = underOver(svg, 8, 3);
    const dot = H.svgEl('circle', { r: 6.5, fill: GOLD }, svg);
    const T = H.nameTag(R, p.make, p.model);
    const quadAt = t => CTX.plane(p.plane, t);
    const bbox = q => { const xs = q.map(v => v[0]), ys = q.map(v => v[1]); return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) }; };
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; H.show(R, on); if (!on) return;
      const q = quadAt(t); if (!q) { H.show(R, false); return; }
      const M0q = sq2quad(q), [pf, pt, pr, pb] = p.pad;
      // the lock's own panel: the tracked quad padded out along the car's side (front / top / rear / bottom, in panel units)
      const pq = [hmap(M0q, -pf, -pt), hmap(M0q, 1 + pr, -pt), hmap(M0q, 1 + pr, 1 + pb), hmap(M0q, -pf, 1 + pb)];
      const M = sq2quad(pq), pu = 0, pv = 0;
      const bb = bbox(pq), c = [bb.x + bb.w / 2, bb.y + bb.h / 2];
      // ACQUIRE: flat box 1.6x -> the surface quad (9 frames, out-expo); RELEASE: back to the flat box, then collapse
      const qa = E.outExpo(cl((t - p.acquire) * FPS / 9)), qr = E.inCubic(P(t, p.exit, p.exit + 0.16)), qx = E.inCubic(P(t, p.exit + 0.12, p.exit + 0.3));
      const flat = s => [[c[0] - bb.w / 2 * s, c[1] - bb.h / 2 * s], [c[0] + bb.w / 2 * s, c[1] - bb.h / 2 * s], [c[0] + bb.w / 2 * s, c[1] + bb.h / 2 * s], [c[0] - bb.w / 2 * s, c[1] + bb.h / 2 * s]];
      const Fin = flat(1.6), Fout = flat(1 - 0.5 * qx);
      const bend = qa * (1 - qr);
      const tl = p.acquire + 0.3, pl = t >= tl ? Math.exp(-(t - tl) * 14) * Math.min(1, (t - tl) * FPS / 1.5) : 0;
      let Q = pq.map((v, i) => lerpP(qr > 0 ? Fout[i] : Fin[i], v, bend));
      Q = Q.map(v => lerpP(c, v, 1 + 0.05 * pl));
      // corner brackets along the (perspective) edges
      let d = '';
      for (let i = 0; i < 4; i++) {
        const a = Q[i], nx = Q[(i + 1) % 4], pr = Q[(i + 3) % 4];
        const L1 = Math.min(74, 0.24 * dist(a, nx)), L2 = Math.min(74, 0.3 * dist(a, pr));
        const e1 = toward(a, nx, L1), e2 = toward(a, pr, L2);
        d += `M${f2(e1[0])},${f2(e1[1])}L${f2(a[0])},${f2(a[1])}L${f2(e2[0])},${f2(e2[1])}`;
      }
      br.set(d);
      br.o.setAttribute('stroke', pl > 0.05 ? `rgb(255,${Math.round(209 + 46 * pl)},${Math.round(1 + 200 * pl)})` : GOLD);
      const vis = cl(qa * 3) * (1 - qx);
      svg.style.opacity = vis.toFixed(4);
      edgesU.setAttribute('d', pathOf(Q, true)); edgesU.setAttribute('opacity', (0.9 * bend).toFixed(3));
      // ping: the quad outline expanding about its centre
      const qp = P(t, tl, tl + 0.42);
      ping.setAttribute('d', qp > 0 && qp < 1 ? pathOf(Q.map(v => lerpP(c, v, 1 + 0.3 * E.outCubic(qp))), true) : '');
      ping.setAttribute('opacity', (0.8 * (1 - qp)).toFixed(3));
      // DRAW: a perspective grid on the panel (inside the unit square), each line drawing across; then it settles faint
      const gIn = p.acquire + 0.34, gOut = p.exit - 0.02;
      let k = 0; const [nu, nv] = p.grid;
      for (let i = 1; i < nu; i++, k++) {
        const qd = E.outCubic(P(t, gIn + 0.03 * i, gIn + 0.03 * i + 0.3)), qo = E.inCubic(P(t, gOut, gOut + 0.14));
        const a = hmap(M, i / nu, 0), b = hmap(M, i / nu, 1), e = lerpP(a, b, qd * (1 - qo));
        gl[k].setAttribute('d', qd > 0 ? `M${f2(a[0])},${f2(a[1])}L${f2(e[0])},${f2(e[1])}` : '');
      }
      for (let j = 1; j < nv; j++, k++) {
        const qd = E.outCubic(P(t, gIn + 0.1 + 0.05 * j, gIn + 0.1 + 0.05 * j + 0.34)), qo = E.inCubic(P(t, gOut, gOut + 0.14));
        const a = hmap(M, 0, j / nv), b = hmap(M, 1, j / nv), e = lerpP(a, b, qd * (1 - qo));
        gl[k].setAttribute('d', qd > 0 ? `M${f2(a[0])},${f2(a[1])}L${f2(e[0])},${f2(e[1])}` : '');
      }
      const gq = P(t, gIn, gIn + 0.9);
      gridG.setAttribute('opacity', (bend * (gq < 1 ? 0.55 - 0.3 * E.inOutCubic(gq) : 0.25)).toFixed(3));
      // scan line: one pass front -> back across the panel
      const sq = E.inOutCubic(P(t, gIn + 0.05, gIn + 0.6));
      const sa = hmap(M, sq, -0.04), sb = hmap(M, sq, 1.04);
      const sOn = sq > 0 && sq < 1 ? Math.sin(Math.PI * sq) * bend : 0;
      [scan, scanU].forEach(e => { e.setAttribute('d', `M${f2(sa[0])},${f2(sa[1])}L${f2(sb[0])},${f2(sb[1])}`); e.setAttribute('opacity', sOn.toFixed(3)); });
      // ruler along the sill (just outside the panel), ticks every 1/20, long ones every 5
      const rq = E.outCubic(P(t, gIn + 0.2, gIn + 0.6)) * (1 - E.inCubic(P(t, gOut, gOut + 0.14)));
      let rd = '';
      if (rq > 0) {
        const v0 = 1.06, a0 = hmap(M, 0, v0), a1 = hmap(M, rq, v0);
        rd = `M${f2(a0[0])},${f2(a0[1])}L${f2(a1[0])},${f2(a1[1])}`;
        for (let i = 0; i <= 20 * rq; i++) {
          const u = i / 20, A = hmap(M, u, v0), B = hmap(M, u, v0 + (i % 5 === 0 ? 0.07 : 0.035));
          rd += `M${f2(A[0])},${f2(A[1])}L${f2(B[0])},${f2(B[1])}`;
        }
      }
      ruler.set(rd); ruler.o.setAttribute('opacity', bend.toFixed(3)); ruler.u.setAttribute('opacity', bend.toFixed(3));
      // READ: flat tag above the panel, following it at p.follow; leader from the panel's top-front corner
      const q0 = quadAt(p.acquire + 0.3) || q, M0 = sq2quad(q0), tl0 = hmap(M0, -pf, -pt), tlN = pq[0];
      const lx = cl(tl0[0] - 30 + p.follow * (tlN[0] - tl0[0]), SAFE.x0, SAFE.x1 - T.w);
      const ly = cl(Math.min(tl0[1], hmap(M0, 1 + pr, -pt)[1]) - 70 - T.h + p.follow * (tlN[1] - tl0[1]), SAFE.y0, SAFE.y1 - T.h);
      T.lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      const A = Q[0], Bx = cl(A[0], lx + 22, lx + T.w - 22), By = ly + T.h;
      const qL = E.inOutCubic(P(t, p.acquire + 0.22, p.acquire + 0.46)) * (1 - E.inCubic(P(t, p.exit, p.exit + 0.14)));
      const len = Math.hypot(Bx - A[0], By - A[1]);
      lead.set(`M${f2(A[0])},${f2(A[1])}L${f2(Bx)},${f2(By)}`, { 'stroke-dasharray': `${f2(len * qL)} ${f2(len + 20)}` });
      dot.setAttribute('cx', f2(A[0])); dot.setAttribute('cy', f2(A[1])); dot.setAttribute('opacity', qL > 0 ? 1 : 0);
      H.nameTagAt(T, t, p.acquire + 0.3, p.exit);
      H.sigSvg(svg, d.length + ':' + f2(t));
    } };
  };

  // ================================================================== C4 CAR TRACE (freeze)
  // The picture freezes with a flash, the world outside the car drops back (darker, desaturated) and a gold line
  // TRACES THE CAR'S OUTLINE with a live tip, a dashed offset line following it; ticks mark the car's extremes, a light
  // pulse runs the finished outline and the make locks in above the roof. RELEASE: the line un-draws back to where it
  // started, the world comes back, and the picture moves again. The outline is the Vision matte's contour of the frozen
  // frame (build2.py prep), mapped through the still's Ken Burns every frame.
  // p: {contour, matte, make, model, trace [start offset, dur], exit}
  SEK.carTrace = function (cfg) {
    const p = Object.assign({ contour: 'urus166', matte: 'urus166', make: 'LAMBORGHINI', model: 'URUS', trace: [0.16, 1.0], exit: cfg.t1 - 0.45 }, cfg.p);
    const C = (CTX.data('contours') || {})[p.contour];
    if (!C) throw new Error('carTrace: no contour ' + p.contour);
    const R = root(), svg = H.svgRoot(R);
    glowDefs(svg, 'tipglow-' + cfg.code);
    const outer = H.svgEl('path', { fill: 'none', stroke: 'rgba(255,255,255,.75)', 'stroke-width': 1.6, 'stroke-dasharray': '3 9' }, svg);
    const main = underOver(svg, 8, 3.5);
    const pulse = H.svgEl('path', { fill: 'none', stroke: '#FFF9E0', 'stroke-width': 5, 'stroke-linecap': 'round' }, svg);
    const ticks = underOver(svg, 8, 3);
    const lead = underOver(svg, 8, 3);
    const halo = H.svgEl('circle', { r: 26, fill: `url(#tipglow-${cfg.code})` }, svg);
    const tip = H.svgEl('circle', { r: 6, fill: '#FFFFFF' }, svg);
    const T = H.nameTag(R, p.make, p.model);
    const ts = cfg.t0 + p.trace[0], td = p.trace[1];
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; H.show(R, on); if (!on) return;
      const pts = C.pts.map(v => CTX.pt(v[0], v[1], t)), cum = polyLen(pts), L = cum[cum.length - 1];
      const opts = C.outer.map(v => CTX.pt(v[0], v[1], t)), ocum = polyLen(opts), OL = ocum[ocum.length - 1];
      const qi = E.inOutCubic(P(t, ts, ts + td)), qo = E.inExpo(P(t, p.exit, p.exit + 0.3));
      const q = qi * (1 - qo);
      main.set(pathOf(pts, false), { 'stroke-dasharray': `${f2(L * q)} ${f2(L + 40)}` });
      const qoi = E.inOutCubic(P(t, ts + 0.14, ts + td + 0.14)) * (1 - E.inExpo(P(t, p.exit - 0.04, p.exit + 0.24)));
      outer.setAttribute('d', qoi > 0 ? pathOf(prefix(opts, ocum, OL * qoi), false) : '');
      // live tip rides the drawing (and the un-drawing) end of the line
      const moving = (qi > 0 && qi < 1) || (qo > 0 && qo < 1);
      const tp = pointAt(pts, cum, L * q).p;
      [tip, halo].forEach(e => { e.setAttribute('cx', f2(tp[0])); e.setAttribute('cy', f2(tp[1])); e.setAttribute('opacity', moving ? 1 : 0); });
      // light pulse once round the closed outline
      const pq = P(t, ts + td + 0.1, ts + td + 0.75);
      pulse.setAttribute('d', pq > 0 && pq < 1 ? pathOf(pts, false) : '');
      pulse.setAttribute('stroke-dasharray', `140 ${f2(L)}`); pulse.setAttribute('stroke-dashoffset', f2(-L * E.inOutCubic(pq) + 70));
      pulse.setAttribute('opacity', (Math.sin(Math.PI * pq) * 0.9).toFixed(3));
      // extreme ticks (front, rear, roof): short brackets that snap on once the outline has closed
      const kq = E.outBack(P(t, ts + td, ts + td + 0.22), 1.6) * (1 - E.inCubic(P(t, p.exit, p.exit + 0.16)));
      let kd = '';
      if (kq > 0) for (const key of ['left', 'right', 'top']) {
        const [x, y] = CTX.pt(C.ext[key][0], C.ext[key][1], t), s = 22 * kq, o = 14;
        const dx = key === 'left' ? -o : key === 'right' ? o : 0, dy = key === 'top' ? -o : 0;
        if (key === 'top') kd += `M${f2(x - s)},${f2(y + dy)}H${f2(x + s)}M${f2(x)},${f2(y + dy)}v${f2(-s * 0.6)}`;
        else kd += `M${f2(x + dx)},${f2(y - s)}V${f2(y + s)}M${f2(x + dx)},${f2(y)}h${f2(dx * 0.9)}`;
      }
      ticks.set(kd);
      // READ: the tag above the roof, leader down to the roof's top point
      const top = CTX.pt(C.ext.top[0], C.ext.top[1], t);
      const lx = cl(top[0] - T.w * 0.35, SAFE.x0, SAFE.x1 - T.w), ly = cl(top[1] - 120 - T.h, SAFE.y0, SAFE.y1 - T.h);
      T.lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      const tin = ts + td - 0.1;
      const qL = E.inOutCubic(P(t, tin - 0.06, tin + 0.2)) * (1 - E.inCubic(P(t, p.exit, p.exit + 0.14)));
      const Ax = cl(top[0], lx + 22, lx + T.w - 22), Ay = ly + T.h, ll = Math.hypot(Ax - top[0], Ay - top[1] + 14);
      lead.set(`M${f2(top[0])},${f2(top[1] - 14)}L${f2(Ax)},${f2(Ay)}`, { 'stroke-dasharray': `${f2(ll * qL)} ${f2(ll + 20)}` });
      H.nameTagAt(T, t, tin, p.exit);
      // the freeze: flash, then the world drops back behind the car
      if (t >= cfg.t0) window.FX.flash = { a: 0.5 * Math.exp(-(t - cfg.t0) * 13) };
      const pop = E.outCubic(P(t, cfg.t0 + 0.04, cfg.t0 + 0.34)) * (1 - E.inOutCubic(P(t, p.exit + 0.05, p.exit + 0.4)));
      if (pop > 0) window.FX.pop = { matte: p.matte, amt: pop };
      H.sigSvg(svg, f2(q) + f2(qoi) + f2(pq) + f2(kq));
    } };
  };

  // ================================================================== I5 STRIPE SHUTTER
  // The 78/22 stripe draws across the middle of the frame, then OPENS to fill it: for three frames the whole picture is
  // the SE stripe (gold, white on the right) with the mark knocked out in black; the plate switches underneath; the
  // stripe closes back into its line (the frame opening from the top and bottom edges) and the line wipes off.
  // p: {y, h (the line), mark}
  SEK.stripeShutter = function (cfg) {
    const p = Object.assign({ y: 960, h: 12, mark: 250 }, cfg.p);
    const R = root('', 'overflow:hidden');
    const band = H.el('div', 'a', R, 'left:0;top:0;width:1080px;height:1920px;background:linear-gradient(90deg,#FBD101 0 78%,#FFFFFF 78% 100%);transform-origin:left center');
    const eT = H.el('div', 'a', R, 'left:0;width:1080px;height:3px;background:#fff;box-shadow:0 0 24px 8px rgba(255,255,255,.5)');
    const eB = H.el('div', 'a', R, 'left:0;width:1080px;height:3px;background:#fff;box-shadow:0 0 24px 8px rgba(255,255,255,.5)');
    const tip = H.el('div', 'a edge', R, `top:${p.y - 14}px;height:${p.h + 28}px;opacity:0`);
    const mw = p.mark, mh = mw * 0.62;
    const mark = H.el('div', 'a', R, `left:${540 - mw / 2}px;top:${960 - mh / 2}px;width:${mw}px;height:${mh}px;background:#000;` +
      `-webkit-mask:url(${H.maskUrl('sce-icon-mark-only--white.png')}) center/contain no-repeat;mask:url(${H.maskUrl('sce-icon-mark-only--white.png')}) center/contain no-repeat`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; H.show(R, on); if (!on) return;
      const t0 = cfg.t0;
      const qd = E.outExpo(P(t, t0, t0 + 0.13));                         // line draws L -> R
      const qo = E.outExpo(P(t, t0 + 0.1, t0 + 0.25));                   // opens to full frame
      const qc = E.inExpo(P(t, t0 + 0.33, t0 + 0.5));                    // closes back into the line
      const qw = E.inExpo(P(t, t0 + 0.47, t0 + 0.585));                  // line wipes off to the right
      const h = qc > 0 ? lerp(1920, p.h, qc) : lerp(p.h, 1920, qo);
      const top = p.y - h / 2 * (h >= 1920 ? 1 : 1);
      band.style.top = f2(Math.max(0, p.y - h / 2)) + 'px'; band.style.height = f2(Math.min(1920, h)) + 'px';
      band.style.transformOrigin = qw > 0 ? 'right center' : 'left center';
      band.style.transform = `scaleX(${(qw > 0 ? 1 - qw : qd).toFixed(5)})`;
      const moving = (qo > 0 && qo < 1) || (qc > 0 && qc < 1);
      eT.style.top = f2(Math.max(-4, top - 1.5)) + 'px'; eB.style.top = f2(Math.min(1924, p.y + h / 2 - 1.5)) + 'px';
      eT.style.opacity = eB.style.opacity = (moving ? 0.9 : 0).toFixed(3);
      const tq = qd > 0 && qd < 1 ? Math.sin(Math.PI * qd) : 0;
      tip.style.opacity = tq.toFixed(3); tip.style.transform = `translateX(${f2(1080 * qd)}px)`;
      const mq = E.outBack(P(t, t0 + 0.22, t0 + 0.32), 1.8), mo = E.inCubic(P(t, t0 + 0.33, t0 + 0.37));
      mark.style.opacity = (cl(mq * 2) * (1 - mo)).toFixed(3);
      mark.style.transform = `scale(${(1.25 - 0.25 * mq).toFixed(4)})`;
    } };
  };

  // ================================================================== I6 FREEZE SWEEP (chapter out)
  // The chapter's last shot freezes with a flash and cools (a little less colour, a little more contrast), letterbox
  // bars close into the phone's own UI bands, and a slanted studio light SWEEPS ACROSS THE CAR'S BODY (the compositor
  // lights the car through its matte, the rest of the frame only faintly); END OF CH 04 sets in the corner. The clip's
  // own sound tape-stops under it (build2.py audio). p: {matte, tag, title, sweep [start offset, dur], angle, exit}
  SEK.freezeSweep = function (cfg) {
    const p = Object.assign({ matte: 'suv128', tag: 'END OF CH 04', title: 'THE LINEUP', sweep: [0.14, 0.9], from: 220, to: 1160, w: 120, gain: 1.2, angle: 20, exit: cfg.t1 - 0.3,
      x: 72, y: 1290 }, cfg.p);
    const R = root();
    const barT = H.el('div', 'a', R, 'left:0;top:0;width:1080px;height:269px;background:rgba(0,0,0,.94);transform-origin:top center');
    const barB = H.el('div', 'a', R, 'left:0;top:1536px;width:1080px;height:384px;background:rgba(0,0,0,.94);transform-origin:bottom center');
    const sT = H.el('div', 'a stripe', R, 'left:0;top:265px;width:1080px;height:4px');
    const sB = H.el('div', 'a stripe', R, 'left:0;top:1536px;width:1080px;height:4px');
    const tg = H.line(R, 'Michroma', 20, p.tag, p.x + 2, p.y, GOLD, { ls: 0.3 });
    const tiM = H.el('div', 'a', R, `left:0;top:${p.y + 44 - 6}px;width:1080px;height:${Math.round(H.ink('Bebas', 110, 'H').aA + 16)}px;overflow:hidden`);
    const ti = H.line(tiM, 'Bebas', 110, p.title, p.x, 6, '#fff');
    const st = H.el('div', 'a stripe', R, `left:${p.x}px;top:${p.y + 44 + H.ink('Bebas', 110, 'H').aA + 22}px;width:${H.ink('Bebas', 110, p.title).w}px;height:6px`);
    const k = Math.tan(p.angle * Math.PI / 180);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; H.show(R, on); if (!on) return;
      const t0 = cfg.t0;
      window.FX.flash = { a: 0.42 * Math.exp(-(t - t0) * 14) };
      const gq = E.outCubic(P(t, t0, t0 + 0.3));
      window.FX.grade = { sat: 1 - 0.38 * gq, con: 1 + 0.1 * gq };
      const sq = P(t, t0 + p.sweep[0], t0 + p.sweep[0] + p.sweep[1]);
      // near-constant speed across the car (eased only at the ends), so the light takes about a third of a second to cross it
      const sx = sq * sq * (3 - 2 * sq) * 0.35 + sq * 0.65, fade = Math.min(1, sq * 6, (1 - sq) * 6);
      if (sq > 0 && sq < 1) window.FX.sweep = { x: lerp(p.from, p.to, sx), k, w: p.w, gain: p.gain * fade, glob: 0.06 * fade, matte: p.matte };
      // letterbox bars close into the top 14 % / bottom 20 % and open again at the end
      const bi = E.outExpo(P(t, t0 + 0.05, t0 + 0.35)), bo = E.inExpo(P(t, p.exit + 0.02, cfg.t1 - 0.02));
      const bq = bi * (1 - bo);
      barT.style.transform = `scaleY(${bq.toFixed(5)})`; barB.style.transform = `scaleY(${bq.toFixed(5)})`;
      sT.style.transform = `translateY(${f2(-269 * (1 - bq))}px)`; sB.style.transform = `translateY(${f2(384 * (1 - bq))}px)`;
      sT.style.opacity = sB.style.opacity = bq > 0 ? 1 : 0;
      KT.track(tg.g, t, { start: t0 + 0.34, dur: 0.4, spread: 1.8 });
      tg.w.style.opacity = fadeIO(t, t0 + 0.34, 0.1, p.exit - 0.1, 0.2).toFixed(3);
      riseSink(ti.g, t, t0 + 0.4, p.exit - 0.12, { stagger: 0.03, dur: 0.42, outStagger: 0.015, outDur: 0.2 });
      stripeIO(st, t, t0 + 0.5, p.exit - 0.05, 0.36, 0.2);
    } };
  };

  // ================================================================== I4 LETTER WINDOW
  // The next chapter's title rises as solid white letters over the frozen frame; the white drains out of them from the
  // bottom up and the NEXT SHOT is inside the letters (mask pass: the compositor shows plate B through them), with a
  // gold outline; then the camera flies INTO one letter until the next shot fills the frame.
  // p: {tag, pre, lines, cx, y, maxW, maxS, gap, fill [start offset, dur], zoom [start offset, dur], zoomTo 60}
  SEK.letterWindow = function (cfg) {
    const p = Object.assign({ tag: 'CH 05', pre: 'THE', lines: ['DRIVE', 'BACK'], cx: 480, y: 640, maxW: 853, maxS: 560, gap: 40,
      fill: [0.2, 0.26], zoom: [0.52, 0.76], zoomTo: 60 }, cfg.p);
    const S = Math.min(...p.lines.map(l => H.fitSize(l, p.maxW, p.maxS))), cap = H.ink('Bebas', S, 'H').aA;
    const rowsY = p.lines.map((_, i) => p.y + i * (cap + p.gap));
    // zoom target: the middle of the thickest vertical stroke of the last line's first letter (found on a canvas)
    const zl = p.lines[p.lines.length - 1], zx0 = p.cx - H.ink('Bebas', S, zl).w / 2;
    const cv = document.createElement('canvas'); cv.width = Math.ceil(S * 1.2); cv.height = Math.ceil(S * 1.4);
    const cx2 = cv.getContext('2d'); cx2.font = `${S}px Bebas`; cx2.fillStyle = '#fff'; cx2.textBaseline = 'alphabetic';
    const m0 = cx2.measureText(zl[0]); cx2.fillText(zl[0], m0.actualBoundingBoxLeft, S);
    const img = cx2.getImageData(0, 0, cv.width, cv.height).data, midRow = Math.round(S - cap / 2);
    let best = -1, bestX = 0, run = 0, runStart = 0;
    for (let x = 0; x < cv.width; x++) {
      const inside = img[(midRow * cv.width + x) * 4 + 3] > 128;
      if (inside) { if (!run) runStart = x; run++; if (run > best) { best = run; bestX = runStart + run / 2; } } else run = 0;
    }
    const ZX = zx0 + bestX, ZY = rowsY[rowsY.length - 1] + cap / 2;
    const org = `transform-origin:${f2(ZX)}px ${f2(ZY)}px`;
    const build = (parent, mode) => {
      const z = H.el('div', 'a', parent, 'width:1080px;height:1920px;' + org);
      const rows = p.lines.map((l, i) => {
        const w = H.ink('Bebas', S, l).w;
        const mk = H.el('div', 'a', z, `left:0;top:${f2(rowsY[i] - 20)}px;width:1080px;height:${f2(cap + 36)}px;overflow:hidden`);
        const ln = H.line(mk, 'Bebas', S, l, p.cx - w / 2, 20, mode === 'outline' ? 'transparent' : '#fff', { split: false });
        if (mode === 'outline') { ln.t.style.webkitTextStroke = `3px ${GOLD}`; ln.t.style.filter = 'drop-shadow(0 0 6px rgba(0,0,0,.5))'; }
        return ln;
      });
      return { z, rows };
    };
    const MR = root('mask'), FR = root();
    const mk = build(MR, 'mask');
    const full = H.el('div', 'a', MR, 'left:0;top:0;width:1080px;height:1920px;background:#fff;opacity:0');
    const fl = build(FR, 'fill'), ol = build(FR, 'outline');
    const tagW = H.ink('Michroma', 22, p.tag, 0.3).w;
    const tg = H.line(fl.z, 'Michroma', 22, p.tag, p.cx + H.ink('Bebas', S, p.lines[0]).w / 2 - tagW, p.y - 60, GOLD, { ls: 0.3 });
    const pre = H.line(fl.z, 'Bebas', Math.round(S * 0.22), p.pre, p.cx - H.ink('Bebas', S, p.lines[0]).w / 2 + 2, p.y - 36 - H.ink('Bebas', Math.round(S * 0.22), 'H').aA, '#fff');
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; H.show(MR, on); H.show(FR, on); if (!on) return;
      const t0 = cfg.t0;
      const rise = i => E.outExpo(P(t, t0 + 0.02 + 0.07 * i, t0 + 0.3 + 0.07 * i));
      [mk, fl, ol].forEach(c => c.rows.forEach((ln, i) => { const q = rise(i); ln.t.style.transform = `translateY(${f2((1 - q) * 108)}%)`; ln.t.style.opacity = q > 0 ? 1 : 0; }));
      // the white drains out of the letters from the bottom up
      const qf = E.inOutCubic(P(t, t0 + p.fill[0], t0 + p.fill[0] + p.fill[1]));
      fl.rows.forEach(ln => { ln.w.style.clipPath = qf > 0 ? `inset(-10px 0 ${(100 * qf).toFixed(3)}% 0)` : 'none'; });
      // the fly-in: exponential zoom into the stroke (constant speed in log space, accelerating)
      const qz = P(t, t0 + p.zoom[0], t0 + p.zoom[0] + p.zoom[1]);
      const z = Math.pow(p.zoomTo, E.inCubic(qz));
      [mk, fl, ol].forEach(c => { c.z.style.transform = `scale(${z.toFixed(5)})`; });
      ol.z.style.opacity = (1 - E.inCubic(P(qz, 0.35, 0.85))).toFixed(3);
      full.style.opacity = qz >= 0.999 ? 1 : 0;
      KT.track(tg.g, t, { start: t0 + 0.12, dur: 0.36, spread: 2 });
      tg.w.style.opacity = pre.w.style.opacity = (cl(P(t, t0 + 0.12, t0 + 0.22)) * (1 - E.inCubic(P(qz, 0, 0.3)))).toFixed(3);
      KT.rise(pre.g, t, { start: t0 + 0.06, stagger: 0.03, dur: 0.3, dy: 0.4 });
      flag('mask');
    } };
  };

  window.SEK = SEK;
})();
