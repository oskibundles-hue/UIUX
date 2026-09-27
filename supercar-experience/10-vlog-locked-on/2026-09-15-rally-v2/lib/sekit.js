/* sekit.js -- the SE vlog Locked-On component kit (window.SEK).
 *
 * Every component is a factory SEK.<type>(cfg) -> { code, render(t) }. cfg = { code, t0, t1, p: {params} }.
 * render(t) is a PURE function of t (seconds on the scene timeline): no timers, no CSS animation, no clock,
 * no randomness. kit.html calls every component's render(t) from window.renderAt(t); lib/kcapture.js samples it
 * several times per frame for true motion blur.
 *
 * Components can publish compositor instructions for the frame into window.FX (reset by kit.html every
 * renderAt): FX.glass = [{x,y,w,h,blur,dim,op}] (frosted panel behind G2), FX.wipe = {x,k,soft} (I1 sweep line:
 * the new plate is left of x + k*(y-960)), FX.punch = {s,dx,dy} (G1 impact on the plate). kcapture writes them to
 * a per-frame sidecar that lib/compose.py reads.
 *
 * Context (set by kit.html through SEK.init): CTX.box(track, t) -> tracked box in SCREEN px for the plate on screen
 * at t (clip mapping + Ken Burns applied) or null; CTX.clip(t) -> source clip seconds (or null on a non-clip plate);
 * CTX.data(name) -> a data table (meter envelopes); CTX.dur -> scene length.
 *
 * Look: gold #FBD101 is the only accent; black plates, white type; the 78/22 gold/white stripe is ALWAYS
 * horizontal; Bebas (display) + Michroma (labels). Text stays inside the 9:16 safe area
 * (x 54-907, y 269-1536) except the SE banner, which lives on the right edge between y 269 and 1056.
 */
(function () {
  const SEK = {};
  const E = KT.ease, P = KT.p, cl = KT.cl, lerp = KT.lerp;
  const FPS = 30000 / 1001;
  const GOLD = '#FBD101';
  const SAFE = { x0: 54, y0: 269, x1: 907, y1: 1536 };
  const BANNER = { y0: 269, y1: 1056 };
  const LOGO = '../../02-logos/png/';
  // CSS masks need CORS, which file:// pages do not have: build.py passes the two logo PNGs as data URIs
  const maskUrl = f => ((window.KITDATA || {}).logos || {})[f] || (LOGO + f);
  let stage = null, CTX = null;
  SEK.SAFE = SAFE; SEK.BANNER = BANNER;
  SEK.init = (st, ctx) => { stage = st; CTX = ctx; };

  // ------------------------------------------------------------------ text + DOM helpers
  const cv = document.createElement('canvas').getContext('2d');
  const LS = { Michroma: 0.08, Bebas: 0 };
  function ink(fam, size, text, ls) {
    const l = ls ?? LS[fam];
    cv.font = `${size}px ${fam}`; cv.letterSpacing = (l * size) + 'px';
    const m = cv.measureText(text);
    return { aA: m.actualBoundingBoxAscent, aD: m.actualBoundingBoxDescent, fA: m.fontBoundingBoxAscent,
             fD: m.fontBoundingBoxDescent, left: m.actualBoundingBoxLeft,
             w: m.actualBoundingBoxLeft + m.actualBoundingBoxRight - l * size, adv: m.width - l * size };
  }
  const px = v => v.toFixed(2) + 'px';
  // place wrapper w so the INK of its text starts at (x, y) (cap top-left) in the wrapper's parent
  function place(w, fam, size, text, x, y, ls) {
    const m = ink(fam, size, text, ls), hl = (size - (m.fA + m.fD)) / 2;
    w.style.left = px(x + m.left); w.style.top = px(y - (hl + m.fA - m.aA));
    return m;
  }
  function el(tag, cls, parent, css, text) {
    const e = document.createElement(tag); if (cls) e.className = cls; if (css) e.style.cssText = css;
    if (text != null) e.textContent = text; (parent || stage).appendChild(e); return e;
  }
  // text line: wrapper > (mask) > text; returns {w, t, m, g, host}
  function line(parent, fam, size, text, x, y, color, o = {}) {
    const w = el('div', 'a', parent);
    let host = w;
    if (o.mask) host = el('div', 'mask', w);
    const ls = o.ls ?? LS[fam];
    const t = el('div', fam === 'Bebas' ? 'beb' : 'mic', host, `font-size:${size}px;color:${color || '#fff'};letter-spacing:${ls}em`);
    t.textContent = text;
    const m = place(w, fam, size, text, x, y, ls);
    let g = null;
    if (o.split !== false) {
      g = KT.measure(KT.split(t, { perspective: 0 }));
      if (o.dots) g.forEach(s => { if (s.dataset.ch === '·') s.style.color = o.dots; });
    }
    return { w, t, m, g, host, x, y, size, fam, text, capH: m.aA };
  }
  const show = (e, on) => { e.style.display = on ? 'block' : 'none'; };
  const NS = 'http://www.w3.org/2000/svg';
  function svgEl(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  function svgRoot(parent) {
    const s = svgEl('svg', { width: 1080, height: 1920, viewBox: '0 0 1080 1920' }, parent);
    s.style.cssText = 'position:absolute;left:0;top:0;overflow:visible'; return s;
  }
  const f2 = v => v.toFixed(2);
  // gold glint painted into glyphs + a warm bloom (strength returned)
  function glint(ln, t, start, dur = 0.5, o = {}) {
    if (!ln.g) return 0;
    const g = KT.glint(ln.g, t, { start, dur, base: o.base || '#FFFFFF', warm: o.warm || '#FFF2B0', hot: o.hot || GOLD,
      width: (o.w || 0.22) * ln.g.W, angle: 106 });
    ln.w.style.filter = g > 0 ? `drop-shadow(0 0 ${(o.glow || 9) * g}px rgba(251,209,1,${(.32 * g).toFixed(3)}))` : 'none';
    return g;
  }
  // mask-rise a whole line (the text slides up inside its mask)
  function riseLine(ln, t, st, dur = 0.32, out = null) {
    const q = E.outExpo(P(t, st, st + dur));
    let y = 108 * (1 - q);
    if (out != null) { const qo = E.inCubic(P(t, out, out + 0.22)); y -= 108 * qo; }
    ln.t.style.transform = `translateY(${y.toFixed(3)}%)`;
    ln.t.style.opacity = q > 0 ? 1 : 0;
  }
  // periodic helper: phase in [0,1) of a repeating event with period T starting at t0
  const phase = (t, t0, T) => (t < t0 ? -1 : ((t - t0) % T) / T);

  // ------------------------------------------------------------------ building blocks
  // black plate with the horizontal 78/22 stripe cap on top. Reveal: stripe draws L->R (or R->L with
  // p.fromRight) with a light edge, plate unrolls down from it. Exit: content lifts, plate retracts up into
  // the stripe (gold edge on the boundary), stripe wipes off.
  function panel(parent, x, y, w, h, o = {}) {
    const root = el('div', 'a', parent);
    const shadow = el('div', 'a', root, `left:${x}px;top:${y}px;width:${w}px;height:${h}px;box-shadow:0 10px 34px rgba(0,0,0,${o.shadow ?? .30})`);
    const clip = el('div', 'a', root, `left:${x}px;top:${y}px;width:${w}px;height:${h}px;overflow:hidden`);
    const bg = el('div', 'a', clip, `width:${w}px;height:${h}px;background:rgba(0,0,0,${o.alpha ?? .9})`);
    const inner = el('div', 'a', clip, `width:${w}px;height:${h}px`);
    const sh = o.stripe ?? 6;
    const stripe = el('div', 'a stripe', root, `left:${x}px;top:${y}px;width:${w}px;height:${sh}px`);
    const edge = el('div', 'a edge', root, `left:${x}px;top:${y - 7}px;height:${sh + 14}px;opacity:0`);
    const redge = el('div', 'a', root, `left:${x}px;top:0;width:${w}px;height:3px;background:${GOLD};box-shadow:0 0 12px 3px rgba(251,209,1,.5);opacity:0`);
    return { root, shadow, clip, bg, inner, stripe, edge, redge, x, y, w, h, fromRight: !!o.fromRight };
  }
  function panelAt(pn, t, ts, tx, o = {}) {
    const din = o.din ?? 0.26, dout = o.dout ?? 0.34;
    const qs = ts == null ? 1 : E.outExpo(P(t, ts, ts + din));
    const qo = tx == null ? 0 : E.inExpo(P(t, tx + dout * 0.55, tx + dout));
    const org = pn.fromRight ? 'right center' : 'left center', orgOut = pn.fromRight ? 'left center' : 'right center';
    if (qo > 0) { pn.stripe.style.transformOrigin = orgOut; pn.stripe.style.transform = `scaleX(${(1 - qo).toFixed(5)})`; }
    else { pn.stripe.style.transformOrigin = org; pn.stripe.style.transform = qs < 1 ? `scaleX(${qs.toFixed(5)})` : 'none'; }
    pn.stripe.style.opacity = qo >= 1 || qs <= 0 ? 0 : 1;
    const ev = qs > 0 && qs < 1 ? Math.sin(Math.PI * qs) : 0;
    pn.edge.style.opacity = ev.toFixed(4);
    pn.edge.style.transform = `translateX(${(pn.fromRight ? pn.w * (1 - qs) : pn.w * qs).toFixed(2)}px)`;
    const qr = ts == null ? 1 : E.outExpo(P(t, ts + 0.02, ts + din + 0.08));
    const qc = tx == null ? 0 : E.inOutCubic(P(t, tx, tx + dout * 0.72));
    const bottom = qc > 0 ? 100 * qc : 100 * (1 - qr);
    pn.clip.style.clipPath = bottom > 0.001 ? `inset(0 0 ${bottom.toFixed(3)}% 0)` : 'none';
    pn.shadow.style.opacity = (1 - bottom / 100).toFixed(3);
    pn.inner.style.transform = qc > 0 ? `translateY(${(-0.35 * pn.h * qc).toFixed(2)}px)` : 'none';
    pn.redge.style.opacity = qc > 0 && qc < 1 ? Math.min(1, Math.sin(Math.PI * qc) * 2).toFixed(4) : 0;
    pn.redge.style.transform = `translateY(${(pn.y + pn.h * (1 - qc) - 2).toFixed(2)}px)`;
    return { qs, qr, qc, qo };
  }
  // pulsing live dot with a ripple ring (period T)
  function liveDot(parent, cx, cy, r = 6) {
    const ring = el('div', 'a', parent, `left:${cx - r}px;top:${cy - r}px;width:${2 * r}px;height:${2 * r}px;border-radius:50%;border:2px solid ${GOLD};box-sizing:border-box`);
    const dot = el('div', 'a', parent, `left:${cx - r}px;top:${cy - r}px;width:${2 * r}px;height:${2 * r}px;border-radius:50%;background:${GOLD};box-shadow:0 0 8px rgba(251,209,1,.7)`);
    return { ring, dot };
  }
  function liveDotAt(d, t, t0, T = 1.2, amp = 1) {
    const ph = phase(t, t0, T);
    if (ph < 0) { d.ring.style.opacity = 0; d.dot.style.opacity = 1; return; }
    const q = E.outCubic(ph);
    d.ring.style.transform = `scale(${(1 + 1.8 * q * amp).toFixed(4)})`;
    d.ring.style.opacity = (0.85 * (1 - ph)).toFixed(4);
    d.dot.style.opacity = (0.72 + 0.28 * Math.cos(2 * Math.PI * ph)).toFixed(4);
  }
  // corner brackets + edge ticks paths for a rect
  function bracketPaths(r, o = {}) {
    const m = Math.min(r.w, r.h);
    const L = o.L ?? Math.max(18, Math.min(o.maxL ?? 52, 0.22 * m)), Tk = o.tick ?? Math.min(16, 0.08 * m);
    const x0 = r.x, y0 = r.y, x1 = r.x + r.w, y1 = r.y + r.h, mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
    const br = `M${f2(x0)},${f2(y0 + L)}V${f2(y0)}H${f2(x0 + L)}M${f2(x1 - L)},${f2(y0)}H${f2(x1)}V${f2(y0 + L)}` +
               `M${f2(x1)},${f2(y1 - L)}V${f2(y1)}H${f2(x1 - L)}M${f2(x0 + L)},${f2(y1)}H${f2(x0)}V${f2(y1 - L)}`;
    const tk = `M${f2(mx)},${f2(y0)}v${f2(Tk)}M${f2(mx)},${f2(y1)}v${f2(-Tk)}M${f2(x0)},${f2(my)}h${f2(Tk)}M${f2(x1)},${f2(my)}h${f2(-Tk)}`;
    return { br, tk };
  }
  function bracketSet(svg, o = {}) {
    const U = svgEl('g', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': o.under ?? 11, 'stroke-linecap': 'square' }, svg);
    const O = svgEl('g', { fill: 'none', stroke: GOLD, 'stroke-width': o.over ?? 5, 'stroke-linecap': 'square' }, svg);
    return { U, O, bu: svgEl('path', {}, U), bo: svgEl('path', {}, O), tu: svgEl('path', {}, U), to: svgEl('path', {}, O) };
  }
  function bracketDraw(b, r, o = {}) {
    const p = bracketPaths(r, o);
    b.bu.setAttribute('d', p.br); b.bo.setAttribute('d', p.br); b.tu.setAttribute('d', p.tk); b.to.setAttribute('d', p.tk);
    return p;
  }
  // grow a box about its centre
  const grow = (r, s) => ({ x: r.x + r.w / 2 * (1 - s), y: r.y + r.h / 2 * (1 - s), w: r.w * s, h: r.h * s });
  const lerpRect = (a, b, q) => ({ x: lerp(a.x, b.x, q), y: lerp(a.y, b.y, q), w: lerp(a.w, b.w, q), h: lerp(a.h, b.h, q) });
  const padRect = (b, pad) => ({ x: b.x - pad, y: b.y - pad, w: b.w + 2 * pad, h: b.h + 2 * pad });
  // lock "ping": two hairline rects expanding from the lock rect
  function pingSet(svg) { return [0, 1].map(() => svgEl('rect', { fill: 'none', stroke: GOLD, 'stroke-width': 2, opacity: 0 }, svg)); }
  function pingDraw(pings, r, t, tl) {
    pings.forEach((e, i) => {
      const q = P(t, tl + i * 0.07, tl + i * 0.07 + 0.42);
      if (q <= 0 || q >= 1) { e.setAttribute('opacity', 0); return; }
      const g = grow(r, 1 + 0.32 * E.outCubic(q));
      e.setAttribute('x', f2(g.x)); e.setAttribute('y', f2(g.y)); e.setAttribute('width', f2(g.w)); e.setAttribute('height', f2(g.h));
      e.setAttribute('opacity', (0.75 * (1 - q)).toFixed(3));
    });
  }
  // whip offset shared with lib/fx.py whip (ease_io p=4 over the whip window, A leaves in the first half)
  function whipX(t, w) {
    if (!w) return 0;
    const u = P(t, w.t0, w.t1); if (u <= 0) return 0;
    const e = u < .5 ? 0.5 * Math.pow(2 * u, 4) : 1 - 0.5 * Math.pow(2 - 2 * u, 4);
    return (w.dir === 'right' ? 1 : -1) * e * (w.dist ?? 0.9) * 1080;
  }
  const sigSvg = (svg, s) => svg.style.setProperty('--d', `"${s}"`);   // lets KT.signature see SVG changes

  // ------------------------------------------------------------------ A. SE SIDE BANNER
  // A1 bug: the approved top-right bug, refined. Black plate, stripe cap, white lockup with a periodic gold
  //     glint, a live dot and a status label. p: {x1, y, label, built, glintAt, glintEvery, morphOut}
  SEK.bannerBug = function (cfg) {
    const p = Object.assign({ x1: 1040, y: 292, label: 'RALLY DAY', built: true, glintAt: 1.4, glintEvery: 5.5, morphOut: false, tile: 96 }, cfg.p);
    const root = el('div', 'a', stage);
    const lw = 244, lh = lw * 215 / 1527;
    const w = lw + 40, h = 98, x = p.x1 - w, y = p.y;
    const pn = panel(root, x, y, w, h, { stripe: 5, fromRight: true, alpha: .9 });
    const logoW = el('div', 'a', pn.inner, `left:20px;top:19px;width:${lw}px;height:${lh.toFixed(2)}px`);
    const logo = el('img', '', logoW, `width:${lw}px;display:block`); logo.src = LOGO + 'sce-primary-horizontal--white.png';
    const gl = el('div', 'a', logoW, `width:${lw}px;height:${lh.toFixed(2)}px;-webkit-mask-image:url(${maskUrl('sce-primary-horizontal--white.png')});-webkit-mask-size:100% 100%;mask-image:url(${maskUrl('sce-primary-horizontal--white.png')});mask-size:100% 100%;opacity:0`);
    const dot = liveDot(pn.inner, 26, 75, 5);
    const lab = line(pn.inner, 'Michroma', 17, p.label, 42, 69, '#fff', { dots: GOLD });
    const tile = el('div', 'a', root, `left:${p.x1 - p.tile}px;top:${y}px;width:${p.tile}px;height:${p.tile}px;background:rgba(0,0,0,.9);opacity:0`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const ts = p.built ? null : cfg.t0;
      // morph out: the plate narrows to the A3 tile anchored at the right, content wipes out right->left
      if (p.morphOut) {
        const qm = E.inOutCubic(P(t, cfg.t1 - 0.36, cfg.t1));
        const ww = lerp(w, p.tile, qm), hh = lerp(h, p.tile, qm);
        [pn.clip, pn.shadow].forEach(e => { e.style.left = px(p.x1 - ww); e.style.width = px(ww); e.style.height = px(hh); });
        pn.bg.style.width = px(ww); pn.bg.style.height = px(hh);
        pn.stripe.style.left = px(p.x1 - ww); pn.stripe.style.width = px(ww);
        pn.inner.style.opacity = (1 - E.outCubic(P(t, cfg.t1 - 0.36, cfg.t1 - 0.16))).toFixed(4);
        pn.inner.style.transform = qm > 0 ? `translateX(${(-(w - ww)).toFixed(2)}px)` : 'none';
        panelAt(pn, t, ts, null);
      } else panelAt(pn, t, ts, cfg.t1 - 0.4);
      if (ts != null) {
        KT.wipe(logo, t, { start: ts + 0.12, dur: 0.3, dir: 'right', ease: E.inOutCubic, pad: 3 });
        KT.track(lab.g, t, { start: ts + 0.2, dur: 0.3, spread: 1.6 });
      } else { logo.style.clipPath = 'none'; logo.style.opacity = 1; }
      // idle life: gold glint through the lockup every glintEvery s, live dot pulse
      const ph = phase(t, cfg.t0 + p.glintAt, p.glintEvery);
      const gq = ph >= 0 ? P(ph * p.glintEvery, 0, 0.62) : 0;
      if (gq > 0 && gq < 1) {
        const gx = -60 + (lw + 120) * E.inOutCubic(gq);
        gl.style.opacity = 1;
        gl.style.background = `linear-gradient(106deg, rgba(251,209,1,0) ${gx - 46}px, rgba(255,242,176,.95) ${gx - 12}px, #FFFFFF ${gx}px, rgba(251,209,1,.95) ${gx + 14}px, rgba(251,209,1,0) ${gx + 48}px)`;
      } else gl.style.opacity = 0;
      liveDotAt(dot, t, cfg.t0 + 0.2, 1.2);
      tile.style.opacity = 0;
    } };
  };

  // A2 edge tab: a slim vertical tab flush with the right edge. Horizontal stripe cap on top, the SE mark,
  //     a live dot, SUPERCAR EXPERIENCE + the live status set vertically, and a progress rail that fills with
  //     the video. p: {w, y, h, name, label, enter: 'built'|'slide', progress: [t0, t1]}
  SEK.bannerTab = function (cfg) {
    const p = Object.assign({ w: 88, y: 300, h: 600, name: 'SUPERCAR EXPERIENCE', label: 'RALLY DAY · LAS VEGAS', enter: 'slide', progress: null }, cfg.p);
    const x = 1080 - p.w;
    const root = el('div', 'a', stage);
    const body = el('div', 'a', root, `width:1080px;height:1920px`);
    const sh = el('div', 'a', body, `left:${x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px;box-shadow:-10px 0 34px rgba(0,0,0,.30)`);
    const bg = el('div', 'a', body, `left:${x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px;background:rgba(0,0,0,.9)`);
    const inner = el('div', 'a', body, `left:${x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px`);
    const stripe = el('div', 'a stripe', body, `left:${x}px;top:${p.y}px;width:${p.w}px;height:6px;transform-origin:right center`);
    const iw = 52, ih = iw * 215 / 338;
    const icon = el('img', 'a', inner, `left:${(p.w - iw) / 2}px;top:24px;width:${iw}px`); icon.src = LOGO + 'sce-icon-mark-only--white.png';
    const dot = liveDot(inner, p.w / 2, 24 + ih + 22, 5);
    // vertical text, reading top -> bottom (rotate 90deg), glyph tops toward the frame edge
    const vt = el('div', 'a', inner, `left:${p.w - 20}px;top:${24 + ih + 48}px;width:${p.h}px;height:${p.w}px;transform-origin:0 0;transform:rotate(90deg)`);
    const nm = line(vt, 'Michroma', 18, p.name, 0, 4, '#fff', { ls: 0.14 });
    const lb = line(vt, 'Michroma', 14, p.label, 0, 34, GOLD, { ls: 0.16, dots: '#fff' });
    // progress rail on the inner (left) edge
    const r0 = 24 + ih + 48, r1 = p.h - 18;
    const rail = el('div', 'a', inner, `left:12px;top:${r0}px;width:2px;height:${r1 - r0}px;background:rgba(255,255,255,.22)`);
    const fill = el('div', 'a', inner, `left:12px;top:${r0}px;width:2px;height:${r1 - r0}px;background:${GOLD};transform-origin:50% 0;box-shadow:0 0 6px rgba(251,209,1,.6)`);
    const ticks = [];
    for (let yy = r0; yy <= r1; yy += 40) ticks.push(el('div', 'a', inner, `left:14px;top:${yy}px;width:6px;height:2px;background:rgba(255,255,255,.35)`));
    const head = el('div', 'a', inner, `left:9px;top:${r0 - 4}px;width:8px;height:8px;background:${GOLD};box-shadow:0 0 10px rgba(251,209,1,.8)`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const slide = p.enter === 'slide';
      const qi = slide ? E.outExpo(P(t, cfg.t0, cfg.t0 + 0.42)) : 1;
      const qo = p.exit === false ? 0 : E.inExpo(P(t, cfg.t1 - 0.34, cfg.t1));
      const dx = (p.w + 30) * (1 - qi) + (p.w + 30) * qo;
      body.style.transform = dx > 0.01 ? `translateX(${dx.toFixed(2)}px)` : 'none';
      const qs = slide ? E.outExpo(P(t, cfg.t0 + 0.08, cfg.t0 + 0.36)) : 1;
      stripe.style.transform = qs < 1 ? `scaleX(${qs.toFixed(5)})` : 'none';
      if (slide) { KT.track(nm.g, t, { start: cfg.t0 + 0.18, dur: 0.34, spread: 1.5 }); KT.track(lb.g, t, { start: cfg.t0 + 0.26, dur: 0.34, spread: 1.5 }); }
      liveDotAt(dot, t, cfg.t0 + 0.3, 1.2);
      const pr = p.progress ? P(t, p.progress[0], p.progress[1]) : P(t, cfg.t0, cfg.t1);
      const qa = slide ? E.outCubic(P(t, cfg.t0 + 0.2, cfg.t0 + 0.7)) : 1;
      fill.style.transform = `scaleY(${(pr * qa).toFixed(5)})`;
      head.style.transform = `translateY(${((r1 - r0) * pr * qa).toFixed(2)}px)`;
      rail.style.opacity = qa.toFixed(3);
      // a gold glint along the name every 4.8 s
      glint(nm, t, cfg.t0 + 1.0 + Math.floor(Math.max(0, t - cfg.t0 - 1.0) / 4.8) * 4.8, 0.7, { w: 0.2, glow: 6 });
    } };
  };

  // A3 breathing banner: rests as a square tile with the SE mark; at each chapter change it inhales (expands
  //     left with the chapter tag + name), holds, and exhales back to the mark.
  //     p: {x1, y, size, chapters: [{t, tag, title, hold}], enter: 'built'|'slide'}
  SEK.bannerBreathe = function (cfg) {
    const p = Object.assign({ x1: 1040, y: 292, size: 96, chapters: [], enter: 'built' }, cfg.p);
    const S = p.size;
    const root = el('div', 'a', stage);
    const body = el('div', 'a', root, 'width:1080px;height:1920px');
    const sh = el('div', 'a', body, `top:${p.y}px;height:${S}px;box-shadow:0 10px 34px rgba(0,0,0,.30)`);
    const clip = el('div', 'a', body, `top:${p.y}px;height:${S}px;overflow:hidden`);
    const bg = el('div', 'a', clip, `left:0;top:0;width:1080px;height:${S}px;background:rgba(0,0,0,.9)`);
    const stripe = el('div', 'a stripe', body, `top:${p.y}px;height:5px`);
    const iw = 60, ih = iw * 215 / 338;
    const iconW = el('div', 'a', body, `left:${p.x1 - S / 2 - iw / 2}px;top:${p.y + (S - ih) / 2 + 2}px;width:${iw}px;height:${ih}px`);
    const icon = el('img', '', iconW, `width:${iw}px;display:block`); icon.src = LOGO + 'sce-icon-mark-only--white.png';
    const igl = el('div', 'a', iconW, `width:${iw}px;height:${ih}px;-webkit-mask-image:url(${maskUrl('sce-icon-mark-only--white.png')});-webkit-mask-size:100% 100%;mask-image:url(${maskUrl('sce-icon-mark-only--white.png')});mask-size:100% 100%;opacity:0`);
    const ring = el('div', 'a', body, `left:${p.x1 - S}px;top:${p.y}px;width:${S}px;height:${S}px;border:2px solid ${GOLD};box-sizing:border-box;opacity:0`);
    const chs = p.chapters.map(c => {
      const tw = ink('Bebas', 54, c.title).w, gw = ink('Michroma', 16, c.tag).w;
      const tx = Math.max(tw, gw);
      const W = S + tx + 44;
      const holder = el('div', 'a', clip, `width:1080px;height:${S}px`);
      const tg = line(holder, 'Michroma', 16, c.tag, p.x1 - S - 10 - gw, 20, GOLD, { mask: true });
      const ti = line(holder, 'Bebas', 54, c.title, p.x1 - S - 10 - tw, 44, '#fff', { mask: true });
      return Object.assign({ W, holder, tg, ti, hold: c.hold ?? 1.9 }, c);
    });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      let W = S, act = null, breath = 0;
      for (const c of chs) {
        const qe = E.outBack(P(t, c.t, c.t + 0.40), 1.1), qx = E.inOutCubic(P(t, c.t + c.hold, c.t + c.hold + 0.34));
        const k = qe * (1 - qx);
        if (t >= c.t && t < c.t + c.hold + 0.34) { W = lerp(S, c.W, k); act = c; }
        show(c.holder, t >= c.t && t < c.t + c.hold + 0.34);
        riseLine(c.tg, t, c.t + 0.14, 0.3, c.t + c.hold - 0.02);
        riseLine(c.ti, t, c.t + 0.18, 0.34, c.t + c.hold);
        if (t >= c.t && t < c.t + 0.6) breath = Math.sin(Math.PI * P(t, c.t, c.t + 0.6));
        glint(c.ti, t, c.t + 0.75, 0.5, { w: 0.25, glow: 7 });
      }
      const slide = p.enter === 'slide';
      const qi = slide ? E.outExpo(P(t, cfg.t0, cfg.t0 + 0.42)) : 1;
      const qo = p.exit === false ? 0 : E.inExpo(P(t, cfg.t1 - 0.34, cfg.t1));
      const dx = (S + 60) * (1 - qi) + (S + 60) * qo;
      body.style.transform = dx > 0.01 ? `translateX(${dx.toFixed(2)}px)` : 'none';
      const x = p.x1 - W;
      [sh, clip, stripe].forEach(e => { e.style.left = px(x); e.style.width = px(W); });
      bg.style.left = px(-x);
      chs.forEach(c => { c.holder.style.left = px(-x); });
      iconW.style.transform = breath > 0 ? `scale(${(1 + 0.14 * breath).toFixed(4)})` : 'none';
      ring.style.opacity = breath > 0 ? (0.8 * (1 - P(t, act.t, act.t + 0.6))).toFixed(3) : 0;
      ring.style.transform = breath > 0 ? `scale(${(1 + 0.5 * E.outCubic(P(t, act.t, act.t + 0.6))).toFixed(4)})` : 'none';
      // idle: gold glint across the mark every 4.5 s
      const ph = phase(t, cfg.t0 + 0.9, 4.5), gq = ph >= 0 ? P(ph * 4.5, 0, 0.55) : 0;
      if (gq > 0 && gq < 1) { const gx = -30 + (iw + 60) * E.inOutCubic(gq); igl.style.opacity = 1;
        igl.style.background = `linear-gradient(106deg, rgba(251,209,1,0) ${gx - 26}px, #FFF2B0 ${gx - 8}px, #FFFFFF ${gx}px, ${GOLD} ${gx + 8}px, rgba(251,209,1,0) ${gx + 28}px)`; }
      else igl.style.opacity = 0;
    } };
  };

  // ------------------------------------------------------------------ B. PERSON LOCK-ON
  // shared tag: black plate, stripe cap, big name (Bebas) + small line (Michroma)
  function nameTag(parent, big, small, o = {}) {
    const bs = o.bigSize ?? 78, ss = o.smallSize ?? 22, pad = o.pad ?? 30;
    const bw = ink('Bebas', bs, big).w, sw = ink('Michroma', ss, small, o.smallLs).w;
    const bigCap = ink('Bebas', bs, 'H').aA, smCap = ink('Michroma', ss, 'H').aA;
    const top = o.kicker ? 22 : 24;
    const w = Math.ceil(Math.max(bw, sw) + 2 * pad + 4), h = Math.round(top + bigCap + 16 + smCap + 22);
    const lab = el('div', 'a', parent, `width:${w}px;height:${h}px`);
    el('div', 'a', lab, `width:${w}px;height:${h}px;background:rgba(0,0,0,.9);box-shadow:0 10px 30px rgba(0,0,0,.3)`);
    const stripe = el('div', 'a stripe', lab, `width:${w}px;height:6px`);
    const bl = line(lab, 'Bebas', bs, big, pad, top, '#fff', { mask: true });
    const sl = line(lab, 'Michroma', ss, small, pad + 2, top + bigCap + 16, o.smallColor || GOLD, { mask: true, ls: o.smallLs, dots: '#fff' });
    return { lab, stripe, bl, sl, w, h };
  }
  function nameTagAt(T, t, tin, tout) {
    const qp = E.outExpo(P(t, tin, tin + 0.30)), qpo = tout == null ? 0 : E.inCubic(P(t, tout, tout + 0.2));
    const right = qpo > 0 ? 100 * qpo : 100 * (1 - qp);
    T.lab.style.clipPath = right > 0.001 ? `inset(-40px ${right.toFixed(3)}% -40px 0)` : 'inset(-40px 0 -40px 0)';
    T.lab.style.display = qp > 0 && qpo < 1 ? 'block' : 'none';
    KT.drawStripe(T.stripe, t, { start: tin + 0.04, dur: 0.26 });
    riseLine(T.bl, t, tin + 0.10); riseLine(T.sl, t, tin + 0.16);
    glint(T.bl, t, tin + 0.75, 0.5);
  }

  // B1 name lock: tracked corner brackets on the face, a lock ping, and a leader up into the name tag.
  //     p: {track, name, handle, acquire, exit, maxBottom, whip, tagDx}
  SEK.personLock = function (cfg) {
    const p = Object.assign({ track: 'face1', name: 'OMARIE', handle: '@NQ.YOUNG', acquire: cfg.t0, exit: cfg.t1 - 0.3, maxBottom: 1536, whip: null, tagDx: -24, gap: 40, follow: 0.4 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const svg = svgRoot(root);
    const B = bracketSet(svg), pings = pingSet(svg);
    const lu = svgEl('path', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 8 }, svg), lo = svgEl('path', { fill: 'none', stroke: GOLD, 'stroke-width': 3 }, svg);
    const dotU = svgEl('circle', { r: 10, fill: 'rgba(0,0,0,.45)' }, svg), dot = svgEl('circle', { r: 6.5, fill: GOLD }, svg);
    const T = nameTag(root, p.name, p.handle);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const b = CTX.box(p.track, t); if (!b) { show(root, false); return; }
      const ta = p.acquire, tx = p.exit;
      let tgt = padRect(b, 0.08 * Math.min(b.w, b.h) + 14);
      if (tgt.y + tgt.h > p.maxBottom) tgt.h = p.maxBottom - tgt.y;
      const qa = E.outExpo(cl((t - ta) * FPS / 8));
      const src = grow(tgt, 1.8);
      let r = lerpRect(src, tgt, qa);
      const tl = ta + 0.26, pl = t >= tl ? Math.exp(-(t - tl) * 14) * Math.min(1, (t - tl) * FPS / 1.5) : 0;
      r = grow(r, 1 + 0.06 * pl);
      const qx = p.whip ? 0 : E.inCubic(P(t, tx + 0.06, tx + 0.26));
      r = grow(r, 1 - 0.5 * qx);
      const pp = bracketDraw(B, r);
      B.bo.setAttribute('stroke', pl > 0.05 ? `rgb(255,${Math.round(209 + 46 * pl)},${Math.round(1 + 200 * pl)})` : GOLD);
      [B.tu, B.to].forEach(e => e.setAttribute('opacity', cl(qa * 1.4 - 0.4).toFixed(3)));
      pingDraw(pings, tgt, t, tl);
      svg.style.opacity = (cl(qa * 3) * (1 - E.inCubic(P(t, tx + 0.1, tx + 0.26)) * (p.whip ? 0 : 1))).toFixed(4);
      // tag above the brackets; it follows the face at p.follow of its motion (calm, readable type) and the
      // leader stretches between the bracket corner and the tag
      const b0 = CTX.box(p.track, ta + 0.3) || b, t0r = padRect(b0, 0.08 * Math.min(b0.w, b0.h) + 14);
      const lx = cl(t0r.x + p.tagDx + p.follow * (tgt.x - t0r.x), SAFE.x0, SAFE.x1 - T.w);
      const ly = cl(t0r.y - p.gap - T.h + p.follow * (tgt.y - t0r.y), SAFE.y0, 1400);
      T.lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      const bx = tgt.x, by = tgt.y, Ax = cl(bx, lx + 22, lx + T.w - 22), Ay = ly + T.h;
      const qL = E.inOutCubic(P(t, ta + 0.22, ta + 0.46)), qLo = p.whip ? 0 : E.inCubic(P(t, tx, tx + 0.14));
      const len = Math.max(0, Math.hypot(Ax - bx, Ay - by)), drawn = len * qL * (1 - qLo);
      const d = `M${f2(bx)},${f2(by)}L${f2(Ax)},${f2(Ay)}`;
      [lu, lo].forEach(e => { e.setAttribute('d', d); e.setAttribute('stroke-dasharray', `${f2(drawn)} ${f2(len + 20)}`); });
      [dot, dotU].forEach(c => { c.setAttribute('cx', f2(bx)); c.setAttribute('cy', f2(by)); c.setAttribute('opacity', qL > 0 && qLo < 1 ? 1 : 0); });
      nameTagAt(T, t, ta + 0.30, p.whip ? null : tx);
      const wx = whipX(t, p.whip);
      root.style.transform = wx ? `translateX(${wx.toFixed(2)}px)` : 'none';
      sigSvg(svg, pp.br + drawn.toFixed(1));
    } };
  };

  // B2 reticle: a circular HUD reticle (drawn-on ring, counter-rotating tick crowns, crosshair gaps) with a
  //     compact tag hung off the ring at 10 o'clock. p: {track, name, handle, acquire, exit}
  SEK.personReticle = function (cfg) {
    const p = Object.assign({ track: 'face2', name: 'OMARIE', handle: '@NQ.YOUNG', acquire: cfg.t0, exit: cfg.t1 - 0.3, status: 'HOST', follow: 0.45 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const svg = svgRoot(root);
    const gU = svgEl('g', { fill: 'none', stroke: 'rgba(0,0,0,.42)', 'stroke-width': 9 }, svg);
    const gO = svgEl('g', { fill: 'none', stroke: GOLD, 'stroke-width': 3.5 }, svg);
    const ringU = svgEl('circle', {}, gU), ring = svgEl('circle', {}, gO);
    const arcsU = svgEl('path', { 'stroke-width': 12 }, gU), arcs = svgEl('path', { 'stroke-width': 6 }, gO);
    const crown = svgEl('path', { stroke: 'rgba(255,255,255,.85)', 'stroke-width': 2 }, svg);
    const crossU = svgEl('path', { 'stroke-width': 8 }, gU), cross = svgEl('path', { 'stroke-width': 3.5 }, gO);
    const lu = svgEl('path', { 'stroke-width': 8 }, gU), lo = svgEl('path', { 'stroke-width': 3 }, gO);
    const T = nameTag(root, p.name, p.handle, { bigSize: 56, smallSize: 17, pad: 24 });
    const st = el('div', 'a', root);
    const stl = line(st, 'Michroma', 14, 'LOCKED · ' + p.status, 0, 0, GOLD, { dots: '#fff' });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const b = CTX.box(p.track, t); if (!b) { show(root, false); return; }
      const ta = p.acquire, tx = p.exit;
      const cx = b.x + b.w / 2, cy = b.y + b.h * 0.52, R0 = 0.62 * Math.max(b.w, b.h) + 10;
      const qa = E.outExpo(P(t, ta, ta + 0.42)), qx = E.inCubic(P(t, tx, tx + 0.28));
      const R = R0 * (1 + 0.45 * (1 - qa)) * (1 - 0.35 * qx);
      const C = 2 * Math.PI * R;
      [ring, ringU].forEach(c => { c.setAttribute('cx', f2(cx)); c.setAttribute('cy', f2(cy)); c.setAttribute('r', f2(R));
        c.setAttribute('stroke-dasharray', `${f2(C * qa)} ${f2(C)}`); c.setAttribute('transform', `rotate(${(-90 + 180 * (1 - qa)).toFixed(2)} ${f2(cx)} ${f2(cy)})`); });
      // four heavy arc segments, spinning in and settling; slow drift afterwards
      const spin = 220 * (1 - E.outCubic(P(t, ta, ta + 0.7))) + 14 * (t - ta);
      let d = '';
      for (let k = 0; k < 4; k++) {
        const a0 = (k * 90 + 20 + spin) * Math.PI / 180, a1 = a0 + 50 * Math.PI / 180, rr = R + 12;
        d += `M${f2(cx + rr * Math.cos(a0))},${f2(cy + rr * Math.sin(a0))}A${f2(rr)},${f2(rr)} 0 0 1 ${f2(cx + rr * Math.cos(a1))},${f2(cy + rr * Math.sin(a1))}`;
      }
      [arcs, arcsU].forEach(e => e.setAttribute('d', d));
      // tick crown, counter-rotating
      let c2 = '';
      const cr = -0.8 * spin;
      for (let k = 0; k < 36; k++) { const a = (k * 10 + cr) * Math.PI / 180, r1 = R + 24, r2 = R + (k % 3 === 0 ? 36 : 30);
        c2 += `M${f2(cx + r1 * Math.cos(a))},${f2(cy + r1 * Math.sin(a))}L${f2(cx + r2 * Math.cos(a))},${f2(cy + r2 * Math.sin(a))}`; }
      crown.setAttribute('d', c2); crown.setAttribute('opacity', (0.55 * E.outCubic(P(t, ta + 0.15, ta + 0.5)) * (1 - qx)).toFixed(3));
      const g = 16, L = 20;
      const cd = `M${f2(cx - R)},${f2(cy)}h${L}M${f2(cx + R)},${f2(cy)}h${-L}M${f2(cx)},${f2(cy - R)}v${L}M${f2(cx)},${f2(cy + R)}v${-L}`;
      [cross, crossU].forEach(e => { e.setAttribute('d', cd); e.setAttribute('opacity', cl(qa * 1.5 - 0.5).toFixed(3)); });
      // tag at 10 o'clock: 45-degree leader out of the ring, then horizontal into the tag's right edge
      const a = 225 * Math.PI / 180, Px = cx + (R + 12) * Math.cos(a), Py = cy + (R + 12) * Math.sin(a);
      const b0 = CTX.box(p.track, ta + 0.4) || b, c0x = b0.x + b0.w / 2, c0y = b0.y + b0.h * 0.52, R00 = 0.62 * Math.max(b0.w, b0.h) + 10;
      const E0x = c0x + (R00 + 12) * Math.cos(a) - 46, E0y = c0y + (R00 + 12) * Math.sin(a) - 46;
      const Ex = E0x + p.follow * (Px - 46 - E0x), Ey = E0y + p.follow * (Py - 46 - E0y);
      const lx = cl(Ex - 20 - T.w, SAFE.x0, SAFE.x1 - T.w), ly = cl(Ey - T.h / 2, SAFE.y0, 1400);
      const Ax = lx + T.w, Ay = cl(Ey, ly + 10, ly + T.h - 10);
      const ld = `M${f2(Px)},${f2(Py)}L${f2(Ax + 20)},${f2(Ay)}H${f2(Ax)}`, len = Math.hypot(Px - Ax - 20, Py - Ay) + 22;
      const qL = E.inOutCubic(P(t, ta + 0.25, ta + 0.5)) * (1 - E.inCubic(P(t, tx, tx + 0.14)));
      [lu, lo].forEach(e => { e.setAttribute('d', ld); e.setAttribute('stroke-dasharray', `${f2(len * qL)} ${f2(len + 20)}`); });
      T.lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      nameTagAt(T, t, ta + 0.36, tx);
      // status under the ring
      const sw = stl.m.w;
      st.style.transform = `translate(${f2(cx - sw / 2)}px,${f2(cy + R + 50)}px)`;
      KT.track(stl.g, t, { start: ta + 0.45, dur: 0.3, spread: 1.8 });
      st.style.opacity = (1 - qx).toFixed(3);
      svg.style.opacity = (cl(qa * 2.5) * (1 - E.inCubic(P(t, tx + 0.1, tx + 0.28)))).toFixed(4);
      sigSvg(svg, d.length + ':' + R.toFixed(2) + ':' + qL.toFixed(3));
    } };
  };

  // B3 guest lock: full-body brackets from an upper-body track, a scan line on acquire, tag above the head.
  //     p: {track, kicker, name, acquire, exit, legs (body height / tracked height)}
  SEK.guestLock = function (cfg) {
    const p = Object.assign({ track: 'guest', kicker: 'LOCKED ON', name: 'RALLY GUEST', acquire: cfg.t0, exit: cfg.t1 - 0.3, legs: 1.8, head: 0.1, follow: 0.45 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const svg = svgRoot(root);
    const B = bracketSet(svg), pings = pingSet(svg);
    const scanU = svgEl('path', { stroke: 'rgba(251,209,1,.25)', 'stroke-width': 18, fill: 'none' }, svg), scan = svgEl('path', { stroke: '#FFF6C8', 'stroke-width': 2.5, fill: 'none' }, svg);
    const lu = svgEl('path', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 8 }, svg), lo = svgEl('path', { fill: 'none', stroke: GOLD, 'stroke-width': 3 }, svg);
    const T = nameTag(root, p.name, p.kicker, { bigSize: 64, smallSize: 17, pad: 26 });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const b = CTX.box(p.track, t); if (!b) { show(root, false); return; }
      const ta = p.acquire, tx = p.exit;
      const body = { x: b.x - 0.16 * b.w, y: b.y - p.head * b.h, w: b.w * 1.32, h: b.h * (p.legs + p.head) };
      const tgt = padRect(body, 10);
      const qa = E.outExpo(cl((t - ta) * FPS / 8));
      let r = lerpRect(grow(tgt, 1.7), tgt, qa);
      const tl = ta + 0.26, pl = t >= tl ? Math.exp(-(t - tl) * 14) * Math.min(1, (t - tl) * FPS / 1.5) : 0;
      r = grow(r, (1 + 0.05 * pl) * (1 - 0.5 * E.inCubic(P(t, tx + 0.06, tx + 0.26))));
      const pp = bracketDraw(B, r, { maxL: 40 });
      B.bo.setAttribute('stroke', pl > 0.05 ? `rgb(255,${Math.round(209 + 46 * pl)},${Math.round(1 + 200 * pl)})` : GOLD);
      [B.tu, B.to].forEach(e => e.setAttribute('opacity', cl(qa * 1.4 - 0.4).toFixed(3)));
      pingDraw(pings, tgt, t, tl);
      // scan line sweeps down the body once, right after the snap
      const qs = P(t, ta + 0.12, ta + 0.62);
      if (qs > 0 && qs < 1) { const yy = tgt.y + tgt.h * E.inOutCubic(qs), d = `M${f2(tgt.x + 4)},${f2(yy)}H${f2(tgt.x + tgt.w - 4)}`;
        [scan, scanU].forEach(e => { e.setAttribute('d', d); e.setAttribute('opacity', Math.sin(Math.PI * qs).toFixed(3)); }); }
      else [scan, scanU].forEach(e => e.setAttribute('opacity', 0));
      svg.style.opacity = (cl(qa * 3) * (1 - E.inCubic(P(t, tx + 0.1, tx + 0.26)))).toFixed(4);
      const b0 = CTX.box(p.track, ta + 0.3) || b;
      const x0 = b0.x - 0.16 * b0.w + b0.w * 0.66, y0 = b0.y - p.head * b0.h - 10;       // top centre at lock time
      const cxN = tgt.x + tgt.w / 2;
      const lx = cl(x0 - T.w / 2 + p.follow * (cxN - x0), SAFE.x0, SAFE.x1 - T.w), ly = cl(y0 - 44 - T.h + p.follow * (tgt.y - y0), SAFE.y0, 1400);
      T.lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      const Ax = cl(cxN, lx + 22, lx + T.w - 22), Ay = ly + T.h, cy = tgt.y;
      const qL = E.inOutCubic(P(t, ta + 0.22, ta + 0.44)) * (1 - E.inCubic(P(t, tx, tx + 0.14)));
      const len = Math.max(0, Math.hypot(Ax - cxN, cy - Ay)), d = `M${f2(cxN)},${f2(cy)}L${f2(Ax)},${f2(Ay)}`;
      [lu, lo].forEach(e => { e.setAttribute('d', d); e.setAttribute('stroke-dasharray', `${f2(len * qL)} ${f2(len + 20)}`); });
      nameTagAt(T, t, ta + 0.30, tx);
      sigSvg(svg, pp.br + qs.toFixed(3) + qL.toFixed(3));
    } };
  };

  // ------------------------------------------------------------------ C. CONVOY LOCK-ON
  // C1 hop (+ I2 lock-lost / re-acquire): one bracket set hops from car to car with a counter and a make
  //     label; a hop across a cut goes through a calm LOCK LOST state and snaps onto the new target.
  //     p: {segs: [{track, t, make, placeholder, mode: 'acquire'|'hop'|'relock', lost}], total, exit}
  SEK.convoyHop = function (cfg) {
    const p = Object.assign({ segs: [], total: 3, exit: cfg.t1 - 0.3, label: 'CAR', follow: 0.45 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const svg = svgRoot(root);
    const ghost = svgEl('path', { fill: 'none', stroke: 'rgba(255,255,255,.55)', 'stroke-width': 2, 'stroke-dasharray': '10 8' }, svg);
    const B = bracketSet(svg), pings = pingSet(svg);
    const lu = svgEl('path', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 8 }, svg), lo = svgEl('path', { fill: 'none', stroke: GOLD, 'stroke-width': 3 }, svg);
    const dot = svgEl('circle', { r: 6, fill: GOLD }, svg);
    // label: "CAR 0N / 0T" (rolling digits) over the make
    const n2 = n => String(n).padStart(2, '0');
    const makeW = Math.max(...p.segs.map(s => ink('Bebas', 58, s.make).w), ink('Bebas', 58, 'LOCK LOST').w);
    const LW = Math.ceil(Math.max(makeW + 64, 300)), LH = 120;
    const lab = el('div', 'a', root, `width:${LW}px;height:${LH}px`);
    el('div', 'a', lab, `width:${LW}px;height:${LH}px;background:rgba(0,0,0,.9);box-shadow:0 10px 30px rgba(0,0,0,.3)`);
    const stripe = el('div', 'a stripe', lab, `width:${LW}px;height:6px`);
    const head = el('div', 'a', lab, 'left:30px;top:22px');
    const hl = line(head, 'Michroma', 18, p.label + ' ', 0, 0, GOLD, { split: false });
    const hx = hl.m.adv + 4;
    const dcol = el('div', 'a', head, `left:${hx}px;top:${hl.w.style.top};height:18px;overflow:hidden;width:60px`);
    const dstrip = el('div', '', dcol, 'display:flex;flex-direction:column');
    for (let k = 0; k <= p.segs.length; k++) el('div', 'mic', dstrip, 'font-size:18px;height:18px;line-height:18px;color:#fff;letter-spacing:.08em', n2(k));
    const tot = line(head, 'Michroma', 18, '/ ' + n2(p.total), hx + ink('Michroma', 18, '00').adv + 12, 0, 'rgba(255,255,255,.6)', { split: false });
    const makes = p.segs.map(s => {
      const w = el('div', 'a', lab, `left:0;top:0;width:${LW}px;height:${LH}px`);
      const ln = line(w, 'Bebas', 58, s.make, 30, 56, s.placeholder ? 'rgba(255,255,255,.55)' : '#fff', { mask: true });
      if (s.placeholder) el('div', 'a', w, `left:24px;top:48px;width:${Math.ceil(ln.m.w + 14)}px;height:60px;border:1.5px dashed rgba(255,255,255,.45)`);
      return { w, ln };
    });
    const lostW = el('div', 'a', lab, `left:0;top:0;width:${LW}px;height:${LH}px`);
    const lost = line(lostW, 'Bebas', 58, 'LOCK LOST', 30, 56, 'rgba(255,255,255,.7)', { mask: true });
    let prevBox = null;
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const S = p.segs;
      let i = -1; for (let k = 0; k < S.length; k++) if (t >= S[k].t) i = k;
      if (i < 0) { show(root, false); return; }
      const s = S[i];
      const boxOf = (k, tt) => { const b = CTX.box(S[k].track, tt); return b ? padRect(b, 0.08 * Math.min(b.w, b.h) + 12) : null; };
      // last valid box of the previous target (frozen once its track is gone)
      const lastOf = (k, tt) => { for (let d = 0; d < 40; d++) { const b = boxOf(k, tt - d / FPS); if (b) return b; } return null; };
      let tgt = boxOf(i, t) || lastOf(i, t);
      if (!tgt) { show(root, false); return; }
      let r = tgt, lostK = 0, pl = 0, lostRect = null;
      // a lost target's rect, pulled inside the frame (a track can end half off-screen)
      const fitIn = q => { const w = Math.min(q.w, 560), h = Math.min(q.h, 380), cx = cl(q.x + q.w / 2, 60 + w / 2, 1020 - w / 2), cy = cl(q.y + q.h / 2, 400 + h / 2, 1450 - h / 2);
        return { x: cx - w / 2, y: cy - h / 2, w, h }; };
      const lostAt = tt => { const sr = grow(fitIn(lastOf(i - 1, s.t)), 1.25), tsn0 = s.t + (s.lost ?? 0.36);
        const qd = E.inOutCubic(P(tt, s.t, tsn0)), cxs = lerp(sr.x + sr.w / 2, 480, 0.5 * qd), cys = lerp(sr.y + sr.h / 2, 1020, 0.5 * qd);
        return { x: cxs - sr.w / 2, y: cys - sr.h / 2, w: sr.w, h: sr.h }; };
      const hopD = 9 / FPS;
      ghost.setAttribute('opacity', 0);
      if (s.mode === 'acquire' || i === 0) {
        const qa = E.outExpo(cl((t - s.t) * FPS / 8)); r = lerpRect(grow(tgt, 1.8), tgt, qa);
        svg.style.opacity = cl(qa * 3).toFixed(3);
      } else {
        const prev = lastOf(i - 1, s.t);
        const tsnap = s.mode === 'relock' ? s.t + (s.lost ?? 0.36) : s.t;
        if (s.mode === 'relock' && t < tsnap) {                 // LOCK LOST: open up, turn white, breathe calmly
          lostK = E.outCubic(P(t, s.t, s.t + 0.22));
          const L1 = lostAt(t), g0 = fitIn(prev);
          r = lerpRect(g0, L1, lostK);
          r = grow(r, 1 + 0.025 * Math.sin((t - s.t) * 2 * Math.PI * 2.2) * lostK);
          lostRect = r;
        } else {
          const q = E.outExpo(cl((t - tsnap) * FPS / 9));
          const from = s.mode === 'relock' ? lostAt(tsnap) : prev;
          r = lerpRect(from, tgt, q);
          const arc = Math.sin(Math.PI * q) * Math.min(90, 0.25 * Math.hypot(tgt.x - from.x, tgt.y - from.y));
          r = { x: r.x, y: r.y - arc, w: r.w, h: r.h };
          // ghost of the previous lock fades out
          const gq = P(t, tsnap, tsnap + 0.3);
          if (gq < 1) { ghost.setAttribute('d', `M${f2(from.x)},${f2(from.y)}h${f2(from.w)}v${f2(from.h)}h${f2(-from.w)}Z`); ghost.setAttribute('opacity', (0.6 * (1 - gq)).toFixed(3)); }
          else ghost.setAttribute('opacity', 0);
        }
        svg.style.opacity = 1;
      }
      const tsn = s.mode === 'relock' ? s.t + (s.lost ?? 0.36) : s.t;
      const tl = tsn + (i === 0 || s.mode === 'acquire' ? 0.26 : hopD);
      pl = t >= tl ? Math.exp(-(t - tl) * 14) * Math.min(1, (t - tl) * FPS / 1.5) : 0;
      const qx = E.inCubic(P(t, p.exit + 0.06, p.exit + 0.26));
      r = grow(r, (1 + 0.06 * pl) * (1 - 0.5 * qx));
      const pp = bracketDraw(B, r, { maxL: 46 });
      const lostNow = s.mode === 'relock' && t < tsn;
      B.bo.setAttribute('stroke', lostNow ? `rgba(251,209,1,${(1 - 0.3 * lostK).toFixed(3)})` : pl > 0.05 ? `rgb(255,${Math.round(209 + 46 * pl)},${Math.round(1 + 200 * pl)})` : GOLD);
      B.tu.setAttribute('opacity', lostNow ? 0 : 1); B.to.setAttribute('opacity', lostNow ? 0 : 1);
      if (!lostNow) pingDraw(pings, tgt, t, tl); else pingDraw(pings, tgt, -1, 0);
      svg.style.opacity = (parseFloat(svg.style.opacity || 1) * (1 - E.inCubic(P(t, p.exit + 0.1, p.exit + 0.26)))).toFixed(4);
      // label: wipes out with the old target, reappears on the new one (no type flying across the frame); while a
      // target is held it follows at p.follow of the target's motion so the type stays calm and readable
      const snapT = k => S[k].mode === 'relock' ? S[k].t + (S[k].lost ?? 0.36) : S[k].t;
      const t0 = S[0].t;
      const tinOf = k => k === 0 ? t0 + 0.36 : snapT(k) + 0.16;
      const segRect = (k, tt) => boxOf(k, tt) || lastOf(k, tt);
      const labRectFor = (k, tt) => { const a = segRect(k, tinOf(k)), c = segRect(k, Math.max(tt, tinOf(k))); return a && c ? lerpRect(a, c, p.follow) : (c || a || r); };
      let LR, vis, showK = i, lostTxt = false, tin = tinOf(i);
      if (i === 0) { LR = labRectFor(0, t); vis = E.outExpo(P(t, t0 + 0.28, t0 + 0.58)); }
      else {
        const ts = snapT(i), oS = s.mode === 'relock' ? ts - 0.16 : s.t - 0.02;
        if (t < ts + 0.14) {
          LR = labRectFor(i - 1, Math.min(t, s.t - 0.5 / FPS)); vis = 1 - E.inCubic(P(t, oS, oS + 0.14));
          showK = i - 1; lostTxt = s.mode === 'relock' && t >= s.t;
        } else { LR = labRectFor(i, t); vis = E.outExpo(P(t, ts + 0.14, ts + 0.44)); }
      }
      vis *= 1 - E.inCubic(P(t, p.exit, p.exit + 0.2));
      const lx = cl(LR.x - 10, SAFE.x0, SAFE.x1 - LW), ly = cl(LR.y - 36 - LH, SAFE.y0, 1400);
      lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      const right = 100 * (1 - vis);
      lab.style.clipPath = right > 0.001 ? `inset(-40px ${right.toFixed(3)}% -40px 0)` : 'inset(-40px 0 -40px 0)';
      lab.style.display = vis > 0.001 ? 'block' : 'none';
      KT.drawStripe(stripe, t, { start: t0 + 0.32, dur: 0.26 });
      // counter: rolls to the new index as the label comes back
      // the digits change only while the label is wiped out (never a new number beside the old make)
      let pos = 0; S.forEach((sg, k) => { const tt = k === 0 ? t0 + 0.3 : sg.mode === 'relock' ? snapT(k) - 0.01 : snapT(k) + 0.122, d = k === 0 || sg.mode === 'relock' ? 0.12 : 0.012; pos += E.outExpo(P(t, tt, tt + d)); });
      dstrip.style.transform = `translateY(${(-18 * pos).toFixed(3)}px)`;
      makes.forEach((mk, k) => {
        const on2 = k === showK && !lostTxt;
        mk.w.style.display = on2 ? 'block' : 'none';
        if (on2) riseLine(mk.ln, t, k === i ? tin : -1e9, 0.3);
        const tk = tinOf(k);
        glint(mk.ln, t, tk + 0.5, 0.5, S[k].placeholder ? { base: 'rgba(255,255,255,.55)' } : {});
      });
      lostW.style.display = lostTxt ? 'block' : 'none';
      if (lostTxt) riseLine(lost, t, s.t + 0.02, 0.22);
      const cxL = cl(LR.x, lx + 20, lx + LW - 20), Ay = ly + LH, len = Math.max(0, Math.hypot(cxL - r.x, r.y - Ay));
      const qL = E.inOutCubic(P(t, t0 + 0.22, t0 + 0.46)) * (i === 0 ? 1 : vis) * (1 - E.inCubic(P(t, p.exit, p.exit + 0.14)));
      const d = `M${f2(r.x)},${f2(r.y)}L${f2(cxL)},${f2(Ay)}`;
      [lu, lo].forEach(e => { e.setAttribute('d', d); e.setAttribute('stroke-dasharray', `${f2(len * qL)} ${f2(len + 20)}`); });
      dot.setAttribute('cx', f2(r.x)); dot.setAttribute('cy', f2(r.y)); dot.setAttribute('opacity', qL > 0.01 ? 1 : 0);
      sigSvg(svg, pp.br + pos.toFixed(3) + lostK.toFixed(3));
    } };
  };

  // C3 lead-car lock: brackets on the lead car, gold "lead" chevrons climbing above it, and a label with the
  //     host's own line. p: {track, kicker, name, quote, quoteBy, acquire, exit, side: 'below'|'above', follow}
  SEK.leadLock = function (cfg) {
    const p = Object.assign({ track: 'cullinan', kicker: 'LEAD CAR', name: 'ROLLS-ROYCE CULLINAN', quote: '', quoteBy: '', acquire: cfg.t0,
      exit: cfg.t1 - 0.3, side: 'below', follow: 0.5, maxW: 640 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const svg = svgRoot(root);
    const B = bracketSet(svg), pings = pingSet(svg);
    const chevU = [0, 1, 2].map(() => svgEl('path', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 10, 'stroke-linejoin': 'miter' }, svg));
    const chev = [0, 1, 2].map(() => svgEl('path', { fill: 'none', stroke: GOLD, 'stroke-width': 5, 'stroke-linejoin': 'miter' }, svg));
    const lu = svgEl('path', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 8 }, svg), lo = svgEl('path', { fill: 'none', stroke: GOLD, 'stroke-width': 3 }, svg);
    const dot = svgEl('circle', { r: 6, fill: GOLD }, svg);
    const ns = Math.min(64, 64 * (p.maxW - 64) / ink('Bebas', 64, p.name).w);
    const q = p.quote ? `“${p.quote}”` : '';
    const qw = q ? ink('Michroma', 15, q, 0.1).adv + 16 + ink('Michroma', 15, '— ' + p.quoteBy, 0.1).w : 0;
    const W = Math.ceil(Math.max(ink('Bebas', ns, p.name).w, qw, ink('Michroma', 18, p.kicker).w) + 64);
    const nCap = ink('Bebas', ns, 'H').aA, H = Math.round(24 + 14 + 16 + nCap + (q ? 20 + 12 : 0) + 24);
    const lab = el('div', 'a', root, `width:${W}px;height:${H}px`);
    el('div', 'a', lab, `width:${W}px;height:${H}px;background:rgba(0,0,0,.9);box-shadow:0 10px 30px rgba(0,0,0,.3)`);
    const stripe = el('div', 'a stripe', lab, `width:${W}px;height:6px`);
    const kk = line(lab, 'Michroma', 18, p.kicker, 32, 24, GOLD, { mask: true });
    const nm = line(lab, 'Bebas', ns, p.name, 30, 24 + 14 + 16, '#fff', { mask: true });
    let ql = null, qb = null;
    if (q) {
      ql = line(lab, 'Michroma', 15, q, 32, 24 + 30 + nCap + 20, '#fff', { ls: 0.1 });
      qb = line(lab, 'Michroma', 15, '— ' + p.quoteBy, 32 + ink('Michroma', 15, q, 0.1).adv + 16, 24 + 30 + nCap + 20, GOLD, { ls: 0.1 });
    }
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const b = CTX.box(p.track, t); if (!b) { show(root, false); return; }
      const ta = p.acquire, tx = p.exit;
      const tgt = padRect(b, 0.06 * Math.min(b.w, b.h) + 12);
      const qa = E.outExpo(cl((t - ta) * FPS / 8));
      let r = lerpRect(grow(tgt, 1.7), tgt, qa);
      const tl = ta + 0.26, pl = t >= tl ? Math.exp(-(t - tl) * 14) * Math.min(1, (t - tl) * FPS / 1.5) : 0;
      r = grow(r, (1 + 0.05 * pl) * (1 - 0.5 * E.inCubic(P(t, tx + 0.06, tx + 0.26))));
      const pp = bracketDraw(B, r, { maxL: 56 });
      B.bo.setAttribute('stroke', pl > 0.05 ? `rgb(255,${Math.round(209 + 46 * pl)},${Math.round(1 + 200 * pl)})` : GOLD);
      [B.tu, B.to].forEach(e => e.setAttribute('opacity', cl(qa * 1.4 - 0.4).toFixed(3)));
      pingDraw(pings, tgt, t, tl);
      // lead chevrons: three carets above the brackets, lighting up bottom -> top on a 0.9 s loop
      const cx = r.x + r.w / 2, cy0 = r.y - 18, cw = 22;
      const qc = E.outCubic(P(t, ta + 0.35, ta + 0.6)) * (1 - E.inCubic(P(t, tx, tx + 0.2)));
      [0, 1, 2].forEach(k => {
        const y = cy0 - k * 20, d = `M${f2(cx - cw)},${f2(y)}L${f2(cx)},${f2(y - 14)}L${f2(cx + cw)},${f2(y)}`;
        const ph = ((t - ta) / 0.9 - k * 0.18 + 10) % 1, a = 0.35 + 0.65 * Math.pow(Math.max(0, Math.cos(ph * 2 * Math.PI)), 2);
        [chev[k], chevU[k]].forEach(e => { e.setAttribute('d', d); e.setAttribute('opacity', (qc * (e === chev[k] ? a : 1)).toFixed(3)); });
      });
      svg.style.opacity = (cl(qa * 3) * (1 - E.inCubic(P(t, tx + 0.1, tx + 0.26)))).toFixed(4);
      const b0 = CTX.box(p.track, ta + 0.3) || b, t0r = padRect(b0, 0.06 * Math.min(b0.w, b0.h) + 12);
      const below = p.side === 'below';
      const lx = cl(t0r.x + p.follow * (tgt.x - t0r.x), SAFE.x0, SAFE.x1 - W);
      const ly0 = below ? t0r.y + t0r.h + 40 : t0r.y - 60 - H;
      const ly = cl(ly0 + p.follow * (tgt.y - t0r.y), SAFE.y0, SAFE.y1 - H);
      lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      const bx = r.x, by = below ? r.y + r.h : r.y, Ax = cl(bx, lx + 20, lx + W - 20), Ay = below ? ly : ly + H;
      const qL = E.inOutCubic(P(t, ta + 0.22, ta + 0.46)) * (1 - E.inCubic(P(t, tx, tx + 0.14)));
      const len = Math.hypot(Ax - bx, Ay - by), d = `M${f2(bx)},${f2(by)}L${f2(Ax)},${f2(Ay)}`;
      [lu, lo].forEach(e => { e.setAttribute('d', d); e.setAttribute('stroke-dasharray', `${f2(len * qL)} ${f2(len + 20)}`); });
      dot.setAttribute('cx', f2(bx)); dot.setAttribute('cy', f2(by)); dot.setAttribute('opacity', qL > 0 ? 1 : 0);
      const tin = ta + 0.3, qp = E.outExpo(P(t, tin, tin + 0.3)), qpo = E.inCubic(P(t, tx, tx + 0.2));
      const right = qpo > 0 ? 100 * qpo : 100 * (1 - qp);
      lab.style.clipPath = right > 0.001 ? `inset(-40px ${right.toFixed(3)}% -40px 0)` : 'inset(-40px 0 -40px 0)';
      lab.style.display = qp > 0 && qpo < 1 ? 'block' : 'none';
      KT.drawStripe(stripe, t, { start: tin + 0.04, dur: 0.26 });
      riseLine(kk, t, tin + 0.08); riseLine(nm, t, tin + 0.12);
      if (ql) { KT.track(ql.g, t, { start: tin + 0.3, dur: 0.4, spread: 1.4, stagger: 0.006 }); KT.track(qb.g, t, { start: tin + 0.42, dur: 0.34, spread: 1.4 }); }
      glint(nm, t, tin + 0.9, 0.55);
      sigSvg(svg, pp.br + ((t - ta) / 0.9 % 1).toFixed(3) + qL.toFixed(3));
    } };
  };

  // C2 lineup scan: a vertical scan beam sweeps across the lineup; each car it passes gets small brackets and
  //     an index chip; a HUD panel counts them in. p: {targets: [{track}], ts, sweep, panel: {x, y}, title, x0, x1}
  SEK.convoyScan = function (cfg) {
    const p = Object.assign({ targets: [], ts: cfg.t0, sweep: 0.7, x0: 60, x1: 900, title: 'LINEUP SCAN', px: 54, py: 640, exit: cfg.t1 - 0.3 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const svg = svgRoot(root);
    const beamG = svgEl('rect', { fill: 'rgba(251,209,1,.18)', width: 60, height: 1 }, svg), beam = svgEl('rect', { fill: '#FFF3B8', width: 3, height: 1 }, svg);
    const tg = p.targets.map(() => ({ B: bracketSet(svg, { under: 7, over: 3 }), chip: null }));
    const n2 = n => String(n).padStart(2, '0');
    tg.forEach((g, k) => {
      const c = el('div', 'a', root, 'height:26px');
      el('div', 'a', c, `width:40px;height:26px;background:${GOLD}`);
      line(c, 'Michroma', 14, n2(k + 1), 7, 6, '#000', { split: false });
      g.chip = c;
    });
    // HUD panel: title + big rolling count
    const PW = 330, PH = 150;
    const pn = panel(root, p.px, p.py, PW, PH, { stripe: 6 });
    line(pn.inner, 'Michroma', 17, p.title, 26, 24, GOLD, { split: false });
    const cntW = el('div', 'a', pn.inner, 'left:26px;top:58px;width:120px;height:72px;overflow:hidden');
    const cstrip = el('div', '', cntW, 'display:flex;flex-direction:column');
    for (let k = 0; k <= p.targets.length; k++) el('div', 'beb', cstrip, 'font-size:84px;height:72px;line-height:78px;color:#fff', n2(k));
    line(pn.inner, 'Michroma', 16, 'LOCKED', 136, 88, '#fff', { split: false });
    const bar = el('div', 'a', pn.inner, `left:136px;top:116px;width:160px;height:4px;background:rgba(255,255,255,.2)`);
    const barF = el('div', 'a', pn.inner, `left:136px;top:116px;width:160px;height:4px;background:${GOLD};transform-origin:0 50%`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      panelAt(pn, t, cfg.t0, p.exit);
      const ts = p.ts + 0.2, qb = P(t, ts, ts + p.sweep);
      const bx = lerp(p.x0, p.x1, E.inOutCubic(qb));
      const boxes = p.targets.map(g => CTX.box(g.track, t));
      const ys = boxes.filter(Boolean).map(b => [b.y, b.y + b.h]);
      const by0 = ys.length ? Math.min(...ys.map(v => v[0])) - 90 : 900, by1 = ys.length ? Math.max(...ys.map(v => v[1])) + 70 : 1300;
      const bon = qb > 0 && qb < 1 ? Math.sin(Math.PI * qb) : 0;
      [beam, beamG].forEach(e => { e.setAttribute('y', f2(by0)); e.setAttribute('height', f2(by1 - by0)); e.setAttribute('opacity', bon.toFixed(3)); });
      beam.setAttribute('x', f2(bx - 1.5)); beamG.setAttribute('x', f2(bx - 60));
      let count = 0, sig = '';
      const qx = E.inCubic(P(t, p.exit, p.exit + 0.24));
      p.targets.forEach((g, k) => {
        const b = boxes[k], G = tg[k];
        if (!b) { G.B.U.style.display = G.B.O.style.display = 'none'; G.chip.style.display = 'none'; return; }
        const r0 = padRect(b, 6), cx = r0.x + r0.w / 2;
        // the beam reaches this car at tk (time the beam passes its centre)
        const u = cl((cx - p.x0) / (p.x1 - p.x0)); let lo2 = 0, hi2 = 1; for (let it = 0; it < 30; it++) { const m = (lo2 + hi2) / 2; if (E.inOutCubic(m) < u) lo2 = m; else hi2 = m; }
        const tk = ts + p.sweep * lo2;
        const q = E.outBack(P(t, tk, tk + 0.16), 1.6);
        const vis = t >= tk;
        G.B.U.style.display = G.B.O.style.display = vis ? 'block' : 'none';
        G.chip.style.display = vis ? 'block' : 'none';
        if (!vis) return;
        count += E.outExpo(P(t, tk, tk + 0.12));
        const r = grow(r0, (1.5 - 0.5 * q) * (1 - 0.4 * qx));
        const pp = bracketDraw(G.B, r, { L: Math.max(10, Math.min(20, 0.3 * Math.min(r.w, r.h))), tick: 0 });
        G.B.O.setAttribute('opacity', (cl(q * 2) * (1 - qx)).toFixed(3)); G.B.U.setAttribute('opacity', (cl(q * 2) * (1 - qx)).toFixed(3));
        G.chip.style.transform = `translate(${f2(cl(r.x, SAFE.x0, SAFE.x1 - 40))}px,${f2(r.y - 34)}px)`;
        G.chip.style.opacity = (cl(q * 2) * (1 - qx)).toFixed(3);
        sig += pp.br.length + r.x.toFixed(1);
      });
      cstrip.style.transform = `translateY(${(-72 * count).toFixed(3)}px)`;
      barF.style.transform = `scaleX(${(count / Math.max(1, p.targets.length)).toFixed(4)})`;
      sigSvg(svg, sig + bx.toFixed(1) + count.toFixed(3));
    } };
  };

  // ------------------------------------------------------------------ D. CLOCK + PLACE
  const hms = s => { s = ((s % 86400) + 86400) % 86400; return [Math.floor(s / 3600), Math.floor(s / 60) % 60, Math.floor(s % 60)]; };
  const parseT = str => { const a = str.split(':').map(Number); return a[0] * 3600 + a[1] * 60 + (a[2] || 0); };
  const p2 = n => String(n).padStart(2, '0');
  // D1 stamp: HH:MM in Bebas, ticking seconds (each second rolls in), place + date. The seconds run from
  //     the file's clock: clock = start + clip seconds of the plate on screen. p: {x, y, start, place, date, built, fixed}
  SEK.clockStamp = function (cfg) {
    const p = Object.assign({ x: 54, y: 292, start: '22:49:05', place: 'VENETIAN ROOFTOP', date: 'SEP 15 2026', built: true, fixed: null, exit: true }, cfg.p);
    const root = el('div', 'a', stage);
    const s0 = parseT(p.start);
    const hmW = ink('Bebas', 104, '22:49').w, colW = ink('Bebas', 56, ':').adv, dW = ink('Bebas', 56, '0').adv + 1;
    const plW = ink('Michroma', 19, p.place, 0.1).w, dtW = ink('Michroma', 15, p.date, 0.14).w;
    const W = Math.ceil(Math.max(hmW + 14 + colW + 2 * dW + 10, plW + 8, dtW + 30) + 52), H = 196;
    const pn = panel(root, p.x, p.y, W, H, { stripe: 5 });
    const hm = line(pn.inner, 'Bebas', 104, '22:49', 26, 26, '#fff');
    const capH = hm.capH, sCap = ink('Bebas', 56, '0').aA;
    const sx = 26 + hmW + 12, sy = 26 + capH - sCap;
    line(pn.inner, 'Bebas', 56, ':', sx, sy, GOLD, { split: false });
    const cols = [0, 1].map(k => {
      const w = el('div', 'a', pn.inner, `left:${sx + colW + 2 + k * dW}px;top:${sy - 8}px;width:${dW}px;height:${sCap + 16}px;overflow:hidden`);
      const inner = el('div', 'a', w, 'left:0;top:0');
      const a = line(inner, 'Bebas', 56, '0', 0, 8, GOLD, { split: false }), b = line(inner, 'Bebas', 56, '0', 0, 8 + sCap + 16, GOLD, { split: false });
      return { w, inner, a, b, H: sCap + 16 };
    });
    const tick = el('div', 'a', pn.inner, `left:${sx + colW + 2 + 2 * dW + 8}px;top:${sy + 2}px;width:8px;height:8px;border-radius:50%;background:${GOLD}`);
    const pl = line(pn.inner, 'Michroma', 19, p.place, 27, 26 + capH + 26, '#fff', { ls: 0.1 });
    const dt = line(pn.inner, 'Michroma', 15, p.date, 44, 26 + capH + 62, 'rgba(255,255,255,.72)', { ls: 0.14 });
    el('div', 'a', pn.inner, `left:27px;top:${26 + capH + 64}px;width:9px;height:9px;background:${GOLD}`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const ts = p.built ? null : cfg.t0;
      panelAt(pn, t, ts, p.exit ? cfg.t1 - 0.4 : null);
      const c = p.fixed != null ? p.fixed : (CTX.clip(t) ?? 0);
      const sec = s0 + c, [H, M, S] = hms(Math.floor(sec)), fr = sec - Math.floor(sec);
      hm.g.forEach((g, i) => { g.textContent = (p2(H) + ':' + p2(M))[i] ?? g.textContent; });
      const next = hms(Math.floor(sec) + 1)[2];
      // the true second is shown for the whole second; the digits roll to the next one over its last 0.16 s
      const q = p.fixed != null || CTX.clip(t) == null ? 0 : E.inOutCubic(P(fr, 0.84, 1.0));
      [0, 1].forEach(k => {
        const cur = p2(S)[k], nx = p2(next)[k], C = cols[k];
        C.a.t.textContent = cur; C.b.t.textContent = nx;
        const move = cur !== nx ? q : 0;
        C.inner.style.transform = move > 0 ? `translateY(${(-C.H * move).toFixed(3)}px)` : 'none';
      });
      if (p.handoff != null) { const qh = t >= p.handoff ? 1 : 0; hm.w.style.opacity = qh; }
      tick.style.opacity = fr < 0.5 ? 1 : 0.25;
      if (ts != null) {
        if (p.handoff == null) KT.flip(hm.g, t, { start: ts + 0.08, stagger: 0.03, dur: 0.36, from: -90 });
        KT.track(pl.g, t, { start: ts + 0.2, dur: 0.34, spread: 1.6 }); KT.track(dt.g, t, { start: ts + 0.26, dur: 0.34, spread: 1.6 });
      }
      glint(hm, t, cfg.t0 + (p.built ? 1.0 : 0.9), 0.55, { w: 0.3 });
    } };
  };

  // D2 time jump: a black time card wipes in, HH:MM slot reels roll from the last clip's clock to the next
  //     clip's clock (blurred while fast, landing on the true digits), the delta rolls in, then the card lifts
  //     and the clock flies up into the D1 stamp position. p: {from, to, place, date, ts, handoff: {x, y}}
  SEK.clockJump = function (cfg) {
    const p = Object.assign({ from: '20:24', to: '22:49', place: 'VENETIAN ROOFTOP', date: 'SEP 15 2026', handoff: { x: 80, y: 318, size: 104 } }, cfg.p);
    const T0 = cfg.t0, T1 = cfg.t1;
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const card = el('div', 'a', root, 'width:1080px;height:1920px;background:#000');
    const body = el('div', 'a', root, 'width:1080px;height:1920px;transform-origin:0 0');
    const SZ = 300, cap = ink('Bebas', SZ, '0').aA, dW = ink('Bebas', SZ, '0').adv + 6, cW = ink('Bebas', SZ, ':').adv + 8;
    const totalW = 4 * dW + cW, X0 = 540 - totalW / 2, Y0 = 690;
    const toD = p.to.replace(':', ''), fromD = p.from.replace(':', '');
    const H = cap + 40;
    const reels = [0, 1, 2, 3].map(k => {
      const x = X0 + k * dW + (k >= 2 ? cW : 0);
      const w = el('div', 'a', body, `left:${x}px;top:${Y0 - 20}px;width:${dW}px;height:${H}px;overflow:hidden;-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 14%,#000 86%,transparent 100%)`);
      const from = +fromD[k], to = +toD[k];
      const n = ((to - from + 10) % 10) + 10 * (k === 3 ? 2 : 1);        // at least one full turn
      const strip = el('div', 'a', w, 'left:0;top:0');
      // rows top->bottom: blank, to, to-1, ..., from (so moving up the strip counts forward in time)
      const rows = ['']; for (let i = 0; i <= n; i++) rows.push(String((to - i + 100) % 10));
      rows.forEach((d, i) => { if (d !== '') line(strip, 'Bebas', SZ, d, (dW - 6 - ink('Bebas', SZ, d).w) / 2, 20 + i * H, i === 1 ? GOLD : '#fff', { split: false }); });
      return { w, strip, n, x };
    });
    const colon = line(body, 'Bebas', SZ, ':', X0 + 2 * dW + 2, Y0, GOLD, { split: false });
    const lands = p.lands || [T0 + 1.05, T0 + 1.2, T0 + 1.35, T0 + 1.52];
    const spinStart = T0 + 0.42;
    const delta = parseT(p.to) - parseT(p.from), dh = Math.floor(delta / 3600), dm = Math.floor(delta / 60) % 60;
    const dl = line(body, 'Michroma', 22, `+${dh} H ${p2(dm)} MIN`, 0, Y0 - 70, GOLD, { ls: 0.18 });
    dl.w.style.left = px(540 - dl.m.w / 2 + dl.m.left);
    const pl = line(body, 'Michroma', 26, p.place, 0, Y0 + cap + 64, '#fff', { ls: 0.12 });
    pl.w.style.left = px(540 - pl.m.w / 2 + pl.m.left);
    const dt = line(body, 'Michroma', 17, p.date, 0, Y0 + cap + 112, 'rgba(255,255,255,.7)', { ls: 0.16 });
    dt.w.style.left = px(540 - dt.m.w / 2 + dt.m.left);
    const stripe = el('div', 'a stripe', body, `left:${540 - 180}px;top:${Y0 + cap + 38}px;width:360px;height:8px`);
    return { code: cfg.code, render(t) {
      const on = t >= T0 && t < T1; show(root, on); if (!on) return;
      // card in: feathered wipe up from the bottom (0.3 s); out: wipe up off the top at the end
      const qi = E.inOutCubic(P(t, T0, T0 + 0.32)), qo = E.inOutCubic(P(t, T1 - 0.62, T1 - 0.2));
      const FE = 120;
      let m;
      if (qo > 0) { const yt = (1920 + FE) * qo - FE; m = `linear-gradient(180deg,rgba(0,0,0,0) ${f2(yt)}px,#000 ${f2(yt + FE)}px)`; }
      else { const yb = (1920 + FE) * qi; m = `linear-gradient(0deg,#000 0px,#000 ${f2(Math.max(0, yb - FE))}px,rgba(0,0,0,0) ${f2(yb)}px)`; }
      card.style.webkitMaskImage = m; card.style.maskImage = m;
      let sig = '';
      reels.forEach((r, k) => {
        let pos;                                             // rows from 'to' (0 = landed); starts at n (= from)
        if (t < spinStart + k * 0.05) pos = r.n;
        else { const rp = KT.reelPos(t, lands[k], { v: 46, v2: 30, Pd: 2.2, P0: 0.7, w: 44, z: 0.64 }); pos = Math.min(r.n, rp); }
        r.strip.style.transform = `translateY(${(-(1 + pos) * H).toFixed(3)}px)`;
        sig += pos.toFixed(3);
      });
      const landed = t >= lands[3] + 0.15;
      const hit = lands.reduce((a, tl) => a + (t >= tl ? Math.exp(-(t - tl - 0.03) * 10) * (t - tl < 0.03 ? (t - tl) / 0.03 : 1) : 0), 0);
      body.style.filter = hit > 0.02 ? `drop-shadow(0 0 ${(18 * Math.min(1, hit)).toFixed(2)}px rgba(251,209,1,${(0.4 * Math.min(1, hit)).toFixed(3)}))` : 'none';
      KT.track(dl.g, t, { start: lands[3] + 0.05, dur: 0.32, spread: 1.8 });
      KT.track(pl.g, t, { start: lands[3] + 0.12, dur: 0.34, spread: 1.7 });
      KT.track(dt.g, t, { start: lands[3] + 0.2, dur: 0.34, spread: 1.7 });
      KT.drawStripe(stripe, t, { start: lands[3] + 0.08, dur: 0.3 });
      // hand-off: the clock shrinks and flies to the D1 stamp position as the card lifts
      const qh = E.inOutCubic(P(t, T1 - 0.62, T1 - 0.12)), s = lerp(1, p.handoff.size / SZ, qh);
      const hx = lerp(0, p.handoff.x - X0 * s, qh), hy = lerp(0, p.handoff.y - Y0 * s, qh);
      body.style.transform = qh > 0 ? `translate(${f2(hx)}px,${f2(hy)}px) scale(${s.toFixed(5)})` : 'none';
      [dl, pl, dt].forEach(l => { l.w.style.opacity = (1 - E.outCubic(P(t, T1 - 0.66, T1 - 0.46))).toFixed(3); });
      stripe.style.opacity = (1 - E.outCubic(P(t, T1 - 0.66, T1 - 0.46))).toFixed(3) * (t >= lands[3] + 0.08 ? 1 : 0);
      body.style.opacity = (1 - P(t, T1 - 0.16, T1)).toFixed(3);
      body.style.setProperty('--s', `"${sig}${landed}"`);
    } };
  };

  // ------------------------------------------------------------------ E. ROUTE LINE
  // metro-style schematic: polyline through the waypoints (with 45-degree jogs); completed segments gold,
  // upcoming dashed; a comet travels to the next node on each step; the active node pulses.
  function routeGeom(pts) {             // cumulative lengths along the polyline
    const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const at = s => { s = cl(s, 0, L[L.length - 1]); let i = 1; while (i < L.length - 1 && L[i] < s) i++;
      const k = (s - L[i - 1]) / Math.max(1e-6, L[i] - L[i - 1]); return [lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)]; };
    return { L, at, total: L[L.length - 1] };
  }
  function routeBuild(parent, svg, R, o) {
    // R: {pts: [[x,y]...], nodes: [{i (index into pts), label, lx, ly}]}
    const g = routeGeom(R.pts);
    const d = 'M' + R.pts.map(q => `${f2(q[0])},${f2(q[1])}`).join('L');
    const base = svgEl('path', { d, fill: 'none', stroke: 'rgba(255,255,255,.34)', 'stroke-width': o.sw * 0.5, 'stroke-dasharray': `${o.sw * 1.2} ${o.sw * 1.1}` }, svg);
    const under = svgEl('path', { d, fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': o.sw + 6, 'stroke-linejoin': 'round' }, svg);
    const done = svgEl('path', { d, fill: 'none', stroke: GOLD, 'stroke-width': o.sw, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
    const trail = svgEl('path', { d, fill: 'none', stroke: '#FFF6C8', 'stroke-width': o.sw * 0.7, 'stroke-linecap': 'round' }, svg);
    const nodes = R.nodes.map(n => {
      const [x, y] = R.pts[n.i];
      return { n, x, y, s: g.L[n.i],
        rip: svgEl('circle', { cx: x, cy: y, r: o.nr, fill: 'none', stroke: GOLD, 'stroke-width': 2.5, opacity: 0 }, svg),
        ring: svgEl('circle', { cx: x, cy: y, r: o.nr, fill: '#000', stroke: 'rgba(255,255,255,.6)', 'stroke-width': 3 }, svg),
        core: svgEl('circle', { cx: x, cy: y, r: o.nr * 0.55, fill: GOLD, opacity: 0 }, svg) };
    });
    const comet = svgEl('circle', { r: o.nr * 0.6, fill: '#FFFFFF', opacity: 0 }, svg);
    const cometG = svgEl('circle', { r: o.nr * 1.6, fill: 'rgba(251,209,1,.35)', opacity: 0 }, svg);
    const labels = nodes.map(N => {
      const ln = line(parent, 'Bebas', o.ls, N.n.label, N.x + (N.n.lx ?? o.lx), N.y + (N.n.ly ?? 0) - ink('Bebas', o.ls, 'H').aA / 2, '#fff', { mask: true });
      const ul = el('div', 'a', parent, `left:${N.x + (N.n.lx ?? o.lx)}px;top:${N.y + (N.n.ly ?? 0) + ink('Bebas', o.ls, 'H').aA / 2 + 8}px;width:${ln.m.w}px;height:3px;background:${GOLD};transform-origin:0 50%;transform:scaleX(0)`);
      return { ln, ul };
    });
    return { g, base, under, done, trail, nodes, comet, cometG, labels };
  }
  // steps: [{t, k}] -> the comet reaches node k at t (travels over dur before it)
  function routeAt(RB, t, steps, o) {
    const g = RB.g;
    // distance drawn: interpolate between node distances along the step schedule
    let s = 0, active = 0, tArr = [];
    steps.forEach((st, j) => {
      const from = j === 0 ? RB.nodes[0].s : RB.nodes[steps[j - 1].k].s, to = RB.nodes[st.k].s;
      const dur = st.dur ?? o.dur;
      const q = E.inOutCubic(P(t, st.t - dur, st.t));
      if (t >= st.t - dur) s = lerp(from, to, q);
      if (t >= st.t) active = st.k;
      tArr[st.k] = st.t;
    });
    const qd = o.drawIn != null ? E.outCubic(P(t, o.drawIn, o.drawIn + 0.5)) : 1;
    RB.done.setAttribute('stroke-dasharray', `${f2(s)} ${f2(g.total + 50)}`);
    RB.under.setAttribute('stroke-dasharray', `${f2(g.total * qd)} ${f2(g.total + 50)}`);
    RB.base.style.opacity = qd.toFixed(3);
    const tl = Math.min(s, 140);
    RB.trail.setAttribute('stroke-dasharray', `0 ${f2(Math.max(0, s - tl))} ${f2(tl)} ${f2(g.total + 400)}`);
    const moving = steps.some(st => t >= st.t - (st.dur ?? o.dur) && t < st.t);
    RB.trail.setAttribute('opacity', moving ? 0.9 : 0);
    const [cx, cy] = g.at(s);
    [RB.comet, RB.cometG].forEach(c => { c.setAttribute('cx', f2(cx)); c.setAttribute('cy', f2(cy)); c.setAttribute('opacity', moving ? 1 : 0); });
    RB.nodes.forEach((N, k) => {
      const reached = s >= N.s - 0.5 && (k === 0 ? t >= (o.drawIn ?? -1) + 0.2 : true);
      const tk = tArr[k] ?? (k === 0 ? (o.drawIn ?? 0) + 0.2 : 1e9);
      const q = E.outBack(P(t, tk, tk + 0.24), 2.2);
      N.core.setAttribute('opacity', reached ? 1 : 0);
      N.core.setAttribute('r', f2(o.nr * 0.55 * (reached ? q : 0)));
      N.ring.setAttribute('stroke', reached ? GOLD : 'rgba(255,255,255,.6)');
      N.ring.setAttribute('opacity', qd.toFixed(3));
      // active node: ripple every 1 s
      if (k === active && t >= tk) { const ph = ((t - tk) % 1.0) / 1.0; N.rip.setAttribute('r', f2(o.nr * (1 + 1.8 * E.outCubic(ph)))); N.rip.setAttribute('opacity', (0.9 * (1 - ph)).toFixed(3)); }
      else N.rip.setAttribute('opacity', 0);
      const L = RB.labels[k];
      const qa = P(t, (o.labelsIn ?? 0) + 0.05 * k, (o.labelsIn ?? 0) + 0.05 * k + 0.3);
      L.ln.t.style.transform = `translateY(${(108 * (1 - E.outExpo(qa))).toFixed(2)}%)`;
      L.ln.t.style.opacity = qa > 0 ? 1 : 0;
      L.ln.t.style.color = k === active && t >= tk ? '#FFFFFF' : reached ? 'rgba(255,255,255,.78)' : 'rgba(255,255,255,.42)';
      L.ul.style.transform = `scaleX(${(k === active && t >= tk ? E.outExpo(P(t, tk, tk + 0.3)) : 0).toFixed(4)})`;
      glint(L.ln, t, tk < 1e8 ? tk + 0.1 : 1e9, 0.45, { w: 0.35 });
    });
    return { s, active };
  }
  // E1 compact corner route (top-left panel). p: {x, y, title, waypoints, steps: [{t, k}], exit}
  SEK.routeCompact = function (cfg) {
    const p = Object.assign({ x: 54, y: 300, title: 'THE ROUTE', waypoints: [], steps: [], exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stage);
    const W = 452, H = 470;
    const pn = panel(root, p.x, p.y, W, H, { stripe: 6, alpha: .88 });
    const hd = line(pn.inner, 'Michroma', 17, p.title, 28, 26, GOLD);
    const n = p.waypoints.length;
    const cnt = el('div', 'a', pn.inner, `left:${W - 118}px;top:22px;width:90px;height:22px;overflow:hidden`);
    const cstrip = el('div', '', cnt, 'display:flex;flex-direction:column');
    for (let k = 0; k <= n; k++) el('div', 'mic', cstrip, 'font-size:17px;height:22px;line-height:22px;color:#fff;letter-spacing:.08em;text-align:right', `${p2(k)} / ${p2(n)}`);
    // schematic: vertical spine with two 45-degree jogs
    const X1 = 44, X2 = 88, Y = [96, 158, 220, 282, 344, 406];
    const pts = [[X1, Y[0]], [X1, Y[1]], [X1, Y[1] + 14], [X2, Y[1] + 58], [X2, Y[2] + 4], [X2, Y[3]], [X2, Y[3] + 14], [X1, Y[3] + 58], [X1, Y[4] + 4], [X1, Y[5]]];
    // node positions on the path
    const nodeIdx = [0, 1, 4, 5, 8, 9];
    pts[4] = [X2, Y[2]]; pts[8] = [X1, Y[4]];
    const svg = svgRoot(pn.inner); svg.setAttribute('width', W); svg.setAttribute('height', H); svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const RB = routeBuild(pn.inner, svg, { pts, nodes: p.waypoints.map((w, k) => ({ i: nodeIdx[k], label: w })) }, { sw: 6, nr: 11, ls: 40, lx: 30, dur: 0.5 });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      panelAt(pn, t, cfg.t0, p.exit);
      KT.track(hd.g, t, { start: cfg.t0 + 0.1, dur: 0.34, spread: 1.8 });
      const r = routeAt(RB, t, p.steps, { nr: 11, dur: 0.5, drawIn: cfg.t0 + 0.12, labelsIn: cfg.t0 + 0.14 });
      // counter = waypoints reached: the first one as the line draws in, then one per step
      let qc = E.outExpo(P(t, cfg.t0 + 0.32, cfg.t0 + 0.46)), prevK = 0;
      p.steps.forEach(st => { qc += (st.k - prevK) * E.outExpo(P(t, st.t, st.t + 0.14)); prevK = st.k; });
      cstrip.style.transform = `translateY(${(-22 * qc).toFixed(3)}px)`;
      svg.style.setProperty('--d', `"${r.s.toFixed(2)}"`);
    } };
  };
  // E2 full-frame route: a big schematic snaking down the frame over a scrim, the comet travels the whole
  //     drive, each waypoint lands with a ripple and its label; the last one blooms. p: {title, waypoints, steps}
  SEK.routeFull = function (cfg) {
    const p = Object.assign({ title: 'THE ROUTE', sub: 'IN THE GUIDE\'S WORDS', waypoints: [], steps: [], scrim: .62, exit: cfg.t1 - 0.45 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const scrim = el('div', 'a', root, `width:1080px;height:1920px;background:radial-gradient(ellipse 90% 70% at 50% 52%, rgba(0,0,0,${p.scrim}) 0%, rgba(0,0,0,${Math.min(.92, p.scrim + .22)}) 100%)`);
    const body = el('div', 'a', root, 'width:1080px;height:1920px;transform-origin:300px 900px');
    const hd = line(body, 'Michroma', 22, p.title, 110, 318, GOLD, { ls: 0.2 });
    const sb = line(body, 'Michroma', 15, p.sub, 110, 356, 'rgba(255,255,255,.7)', { ls: 0.16 });
    const hs = el('div', 'a stripe', body, 'left:110px;top:296px;width:220px;height:6px');
    // path: spine down the left third with two wide 45-degree swings to the right
    const pts = [[150, 470], [150, 640], [150, 660], [340, 850], [340, 880], [340, 1040], [340, 1060], [150, 1250], [150, 1270], [150, 1440]];
    const nodeIdx = [0, 1, 4, 5, 8, 9];
    pts[4] = [340, 850]; pts[8] = [150, 1250];
    const svg = svgRoot(body);
    const RB = routeBuild(body, svg, { pts, nodes: p.waypoints.map((w, k) => ({ i: nodeIdx[k], label: w })) }, { sw: 10, nr: 20, ls: 76, lx: 50, dur: 0.5 });
    const last = RB.nodes[RB.nodes.length - 1];
    const bloom = svgEl('circle', { cx: last.x, cy: last.y, r: 20, fill: 'none', stroke: GOLD, 'stroke-width': 4, opacity: 0 }, svg);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const qi = E.outCubic(P(t, cfg.t0, cfg.t0 + 0.4)), qo = E.inCubic(P(t, p.exit, p.exit + 0.4));
      scrim.style.opacity = (qi * (1 - qo)).toFixed(3);
      body.style.opacity = (1 - qo).toFixed(3);
      body.style.transform = `scale(${(1 + 0.035 * E.inOutCubic(P(t, cfg.t0, cfg.t1))).toFixed(5)})`;
      KT.track(hd.g, t, { start: cfg.t0 + 0.15, dur: 0.4, spread: 1.8 }); KT.track(sb.g, t, { start: cfg.t0 + 0.25, dur: 0.4, spread: 1.6 });
      KT.drawStripe(hs, t, { start: cfg.t0 + 0.1, dur: 0.35 });
      const r = routeAt(RB, t, p.steps, { nr: 20, dur: 0.5, drawIn: cfg.t0 + 0.2, labelsIn: cfg.t0 + 0.3 });
      const tl = p.steps.length ? p.steps[p.steps.length - 1].t : 1e9, qb = P(t, tl, tl + 0.8);
      bloom.setAttribute('r', f2(20 + 90 * E.outCubic(qb))); bloom.setAttribute('opacity', qb > 0 && qb < 1 ? (0.9 * (1 - qb)).toFixed(3) : 0);
      svg.style.setProperty('--d', `"${r.s.toFixed(2)}:${qb.toFixed(3)}"`);
    } };
  };

  // ------------------------------------------------------------------ F. GUEST TESTIMONIAL
  // live audio meter: N bars from an envelope table (CTX.data(name) = {fps, bands: [[..]...]})
  function meter(parent, x, y, n = 14, bw = 7, gap = 4, hmax = 34) {
    const bars = []; for (let k = 0; k < n; k++) bars.push(el('div', 'a', parent, `left:${x + k * (bw + gap)}px;top:${y}px;width:${bw}px;height:${hmax}px;background:${GOLD};transform-origin:50% 100%`));
    const peaks = []; for (let k = 0; k < n; k++) peaks.push(el('div', 'a', parent, `left:${x + k * (bw + gap)}px;top:${y}px;width:${bw}px;height:3px;background:#fff`));
    return { bars, peaks, n, hmax, y };
  }
  function meterAt(M, t, data, t0, on) {
    const d = data; if (!d) return;
    const fi = Math.max(0, (t - t0) * d.fps);
    const i = Math.floor(fi) % d.bands.length, j = (i + 1) % d.bands.length, k = fi - Math.floor(fi);
    M.bars.forEach((b, n) => {
      const v = on * lerp(d.bands[i][n % d.bands[i].length], d.bands[j][n % d.bands[j].length], k);
      const h = Math.max(0.08, v);
      b.style.transform = `scaleY(${h.toFixed(4)})`;
      // peak cap: max over the last 0.35 s
      let pk = 0; for (let q = 0; q < 10; q++) { const ii = Math.max(0, Math.floor(fi) - q) % d.bands.length; pk = Math.max(pk, d.bands[ii][n % d.bands[ii].length] * (1 - q * 0.05)); }
      M.peaks[n].style.transform = `translateY(${(M.hmax * (1 - Math.max(0.08, on * pk)) - 5).toFixed(2)}px)`;
      M.peaks[n].style.opacity = on;
    });
  }
  // word-by-word quote: words laid out in lines inside width W; each word rises in on its time and flashes gold
  function quoteBuild(parent, words, x, y, W, size, lh) {
    const out = []; let cx = 0, cy = 0; const sp = ink('Bebas', size, ' ').adv;
    words.forEach(wd => {
      const w = ink('Bebas', size, wd.w).adv;
      if (cx > 0 && cx + w > W) { cx = 0; cy += lh; }
      const wrap = el('div', 'a', parent, `left:${x + cx}px;top:${y + cy}px;overflow:hidden;padding:0 6px 0 0;height:${size + 6}px`);
      const t = el('div', 'beb', wrap, `font-size:${size}px;color:${wd.ph ? 'rgba(255,255,255,.62)' : '#fff'}`, wd.w);
      out.push({ wrap, t, x: cx, y: cy, wd }); cx += w + sp;
    });
    return { words: out, height: cy + lh };
  }
  function quoteAt(Q, t, tout) {
    Q.words.forEach(o => {
      const t0 = o.wd.t, q = E.outExpo(P(t, t0, t0 + 0.26));
      o.t.style.transform = `translateY(${(100 * (1 - q)).toFixed(2)}%)`;
      o.t.style.opacity = t >= t0 ? 1 : 0;
      const hot = t >= t0 ? Math.exp(-(t - t0) * 3.2) : 0;
      o.t.style.color = o.wd.ph ? 'rgba(255,255,255,.62)' : hot > 0.05 ? `rgb(${Math.round(255 - 4 * hot)},${Math.round(255 - 46 * hot)},${Math.round(255 - 254 * hot)})` : '#fff';
      if (tout != null) o.wrap.style.opacity = (1 - E.inCubic(P(t, tout, tout + 0.2))).toFixed(3);
    });
  }
  function wordsFrom(text, t0, gap, ph) {
    return text.split(' ').map((w, i) => ({ w, t: t0 + i * gap, ph }));
  }
  // F1 testimonial card. p: {label, quote, wordGap, words (optional [{w,t}]), footer, meter, y}
  SEK.quoteCard = function (cfg) {
    const p = Object.assign({ label: 'RALLY GUEST', quote: '[GUEST QUOTE]', wordGap: 0.22, start: cfg.t0 + 0.55, footer: 'RALLY DAY · SEP 15 2026', meter: 'meter', y: 1010, placeholder: true, exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stage);
    const X = 54, W = 853;
    const words = p.words || wordsFrom(p.quote, p.start, p.wordGap, p.placeholder);
    // measure quote height first
    const probe = el('div', 'a', root, 'visibility:hidden');
    const qh = quoteBuild(probe, words, 0, 0, W - 110, 68, 74).height; probe.remove();
    const H = Math.round(92 + qh + 70);
    const pn = panel(root, X, p.y, W, H, { stripe: 7 });
    const qm = line(root, 'Bebas', 190, '“', X + 22, p.y - 50, GOLD, { split: false });
    const dot = liveDot(pn.inner, 118, 44, 6);
    const lb = line(pn.inner, 'Michroma', 19, p.label, 136, 37, GOLD);
    const M = meter(pn.inner, W - 40 - 14 * 11 + 4, 26, 14, 7, 4, 34);
    const Q = quoteBuild(pn.inner, words, 54, 92, W - 110, 68, 74);
    const ft = line(pn.inner, 'Michroma', 14, p.footer, 54, H - 38, 'rgba(255,255,255,.62)', { ls: 0.14, dots: GOLD });
    const lastT = words[words.length - 1].t;
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      panelAt(pn, t, cfg.t0, p.exit, { din: 0.3 });
      const qq = E.outBack(P(t, cfg.t0 + 0.18, cfg.t0 + 0.5), 1.8), qqo = E.inCubic(P(t, p.exit, p.exit + 0.2));
      qm.w.style.opacity = (cl(qq) * (1 - qqo)).toFixed(3);
      qm.w.style.transform = `translateY(${(30 * (1 - qq)).toFixed(2)}px) scale(${(0.6 + 0.4 * qq).toFixed(4)})`;
      KT.track(lb.g, t, { start: cfg.t0 + 0.2, dur: 0.34, spread: 1.7 });
      liveDotAt(dot, t, cfg.t0 + 0.3, 1.0);
      const speaking = t >= p.start - 0.1 && t < lastT + 0.5 ? 1 : 0.15;
      meterAt(M, t, CTX.data(p.meter), cfg.t0, E.outCubic(P(t, cfg.t0 + 0.3, cfg.t0 + 0.6)) * speaking * (1 - qqo));
      quoteAt(Q, t);
      KT.track(ft.g, t, { start: cfg.t0 + 0.4, dur: 0.34, spread: 1.5 });
      root.style.setProperty('--m', `"${Math.floor(t * FPS)}"`);
    } };
  };
  // F2 Q&A split: host question on the top half, guest answer on the bottom half, a horizontal stripe seam.
  //     p: {q, host, handle, a, label, qt, at, meter}
  SEK.quoteSplit = function (cfg) {
    const p = Object.assign({ q: 'HOW WAS IT?', host: 'OMARIE', handle: '@NQ.YOUNG', a: '[GUEST ANSWER]', label: 'RALLY GUEST', qt: cfg.t0 + 0.4, at: cfg.t0 + 1.7, wordGap: 0.2, meter: 'meter', seam: 960, exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const seam = el('div', 'a stripe', root, `left:0;top:${p.seam - 5}px;width:1080px;height:10px`);
    const seamGlow = el('div', 'a', root, `left:0;top:${p.seam - 1}px;width:1080px;height:2px;box-shadow:0 0 22px 6px rgba(251,209,1,.45)`);
    // top: host tag + question
    const T = nameTag(root, p.host, p.handle, { bigSize: 52, smallSize: 16, pad: 22 });
    const qTag = line(root, 'Michroma', 16, 'Q', 60, 0, '#000', { split: false });
    const qW = Math.min(800, ink('Bebas', 150, p.q).w);
    const qs = Math.min(150, 150 * 800 / ink('Bebas', 150, p.q).w);
    const qCap = ink('Bebas', qs, 'H').aA;
    const qy = p.seam - 60 - qCap;
    const qchip = el('div', 'a', root, `left:60px;top:${qy - 64}px;width:36px;height:36px;background:${GOLD}`);
    qTag.w.style.transform = `translate(${10}px,${qy - 64 + 10}px)`;
    const Ql = line(root, 'Bebas', qs, p.q, 60, qy, '#fff', { mask: true });
    // bottom: guest label + meter + answer
    const bY = p.seam + 60;
    const achip = el('div', 'a', root, `left:60px;top:${bY}px;width:36px;height:36px;background:${GOLD}`);
    const aTag = line(root, 'Michroma', 16, 'A', 70, bY + 10, '#000', { split: false });
    const lb = line(root, 'Michroma', 19, p.label, 114, bY + 9, GOLD);
    const M = meter(root, 114 + ink('Michroma', 19, p.label).w + 30, bY + 1, 12, 7, 4, 34);
    const words = wordsFrom(p.a, p.at, p.wordGap, true);
    const Q = quoteBuild(root, words, 60, bY + 70, 820, 110, 112);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const qs0 = E.outExpo(P(t, cfg.t0, cfg.t0 + 0.4)), qo = E.inExpo(P(t, p.exit, p.exit + 0.35));
      seam.style.transformOrigin = qo > 0 ? 'right center' : 'left center';
      seam.style.transform = `scaleX(${(qo > 0 ? 1 - qo : qs0).toFixed(5)})`;
      seamGlow.style.opacity = (Math.sin(Math.PI * P(t, cfg.t0, cfg.t0 + 0.6)) * 0.9).toFixed(3);
      T.lab.style.transform = `translate(60px,${f2(qy - 64 - 30 - T.h)}px)`;
      T.lab.style.transform = `translate(60px,${f2(300)}px)`;
      nameTagAt(T, t, cfg.t0 + 0.15, p.exit);
      const qc = E.outBack(P(t, p.qt - 0.1, p.qt + 0.12), 2);
      [qchip, qTag.w].forEach(e => e.style.opacity = (cl(qc) * (1 - qo)).toFixed(3));
      qchip.style.transform = `scale(${qc.toFixed(4)})`;
      // question slams in: glyphs rise in fast, then a glint
      KT.rise(Ql.g, t, { start: p.qt, stagger: 0.03, dur: 0.3, dy: 1.05 });
      glint(Ql, t, p.qt + 0.6, 0.5);
      Ql.w.style.opacity = (1 - qo).toFixed(3);
      const ac = E.outBack(P(t, p.at - 0.35, p.at - 0.13), 2);
      [achip, aTag.w].forEach(e => e.style.opacity = (cl(ac) * (1 - qo)).toFixed(3));
      achip.style.transform = `scale(${ac.toFixed(4)})`;
      KT.track(lb.g, t, { start: p.at - 0.35, dur: 0.34, spread: 1.7 });
      lb.w.style.opacity = (1 - qo).toFixed(3);
      const lastT = words[words.length - 1].t;
      meterAt(M, t, CTX.data(p.meter), cfg.t0, E.outCubic(P(t, p.at - 0.3, p.at)) * (t < lastT + 0.6 ? 1 : 0.15) * (1 - qo));
      quoteAt(Q, t, p.exit);
      root.style.setProperty('--m', `"${Math.floor(t * FPS)}"`);
    } };
  };

  // ------------------------------------------------------------------ G. CHAPTER SLAM
  function fitSize(text, maxW, maxS) { return Math.min(maxS, maxS * maxW / ink('Bebas', maxS, text).w); }
  // G1 slam: huge Bebas title slams down onto the frame (scale 1.5 -> 1 with a plate punch), the gold stripe
  //     wipes under it, the chapter tag tracks in above; exit lifts through the mask. p: {tag, title, y, maxW, maxS}
  SEK.chapterSlam = function (cfg) {
    const p = Object.assign({ tag: 'CH 01', title: 'TITLE', y: 760, maxW: 800, maxS: 250, exit: cfg.t1 - 0.36, punch: true }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const S = fitSize(p.title, p.maxW, p.maxS), cap = ink('Bebas', S, 'H').aA, tw = ink('Bebas', S, p.title).w;
    const scrim = el('div', 'a', root, `left:0;top:${p.y - 260}px;width:1080px;height:${cap + 520}px;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,.42) 35%,rgba(0,0,0,.42) 65%,rgba(0,0,0,0) 100%)`);
    const tl = line(root, 'Michroma', 24, p.tag, 540 - ink('Michroma', 24, p.tag, 0.3).w / 2, p.y - 58, GOLD, { ls: 0.3 });
    const holder = el('div', 'a', root, `width:1080px;height:1920px;transform-origin:540px ${p.y + cap / 2}px`);
    const mask = el('div', 'a', holder, `left:0;top:${p.y - 30}px;width:1080px;height:${cap + 60}px;overflow:hidden`);
    const ti = line(mask, 'Bebas', S, p.title, 540 - tw / 2, 30, '#fff');
    const stripe = el('div', 'a stripe', root, `left:${540 - tw / 2}px;top:${p.y + cap + 26}px;width:${tw}px;height:12px`);
    const edge = el('div', 'a edge', root, `left:${540 - tw / 2}px;top:${p.y + cap + 16}px;height:32px;opacity:0`);
    const flash = el('div', 'a', root, `left:${540 - tw / 2 - 40}px;top:${p.y - 40}px;width:${tw + 80}px;height:${cap + 80}px;background:radial-gradient(ellipse at center,rgba(255,246,200,.55) 0%,rgba(251,209,1,.18) 40%,rgba(251,209,1,0) 70%);opacity:0`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const t0 = cfg.t0, th = t0 + 0.16;           // impact time
      const qs = E.outExpo(P(t, t0, th + 0.06));
      const qo = E.inCubic(P(t, p.exit, p.exit + 0.3));
      scrim.style.opacity = (E.outCubic(P(t, t0, t0 + 0.2)) * (1 - E.inCubic(P(t, p.exit + 0.1, p.exit + 0.36)))).toFixed(3);
      const s = lerp(1.55, 1, qs);
      holder.style.transform = `scale(${s.toFixed(5)}) translateY(${(-cap * 1.2 * qo).toFixed(2)}px)`;
      ti.w.style.opacity = cl(P(t, t0, t0 + 0.06)).toFixed(3);
      const hit = t >= th ? Math.exp(-(t - th) * 7) : 0;
      flash.style.opacity = (0.45 * hit).toFixed(3);
      ti.t.style.textShadow = hit > 0.03 ? `0 0 ${(12 * hit).toFixed(1)}px rgba(255,236,150,${(0.4 * hit).toFixed(3)})` : 'none';
      const qst = E.outExpo(P(t, th, th + 0.34)), qsto = E.inExpo(P(t, p.exit, p.exit + 0.3));
      stripe.style.transformOrigin = qsto > 0 ? 'right center' : 'left center';
      stripe.style.transform = `scaleX(${(qsto > 0 ? 1 - qsto : qst).toFixed(5)})`;
      edge.style.opacity = (qst > 0 && qst < 1 ? Math.sin(Math.PI * qst) : 0).toFixed(3);
      edge.style.transform = `translateX(${(tw * qst).toFixed(2)}px)`;
      KT.track(tl.g, t, { start: th + 0.02, dur: 0.36, spread: 2.2 });
      tl.w.style.opacity = (1 - qo).toFixed(3);
      glint(ti, t, th + 0.55, 0.55, { w: 0.2, glow: 12 });
      if (p.punch && t >= th - 0.001) {                  // plate impact: zoom punch + a short decaying shake
        const k = (t - th) * FPS, amp = Math.exp(-k / 2.2);
        window.FX.punch = { s: 1 + 0.045 * Math.exp(-(t - th) * 9), dx: 9 * amp * Math.sin(k * 2.1), dy: 7 * amp * Math.cos(k * 2.7) };
      }
    } };
  };
  // G2 glass: the title sits on a frosted glass panel (the compositor blurs and dims the plate inside it) for
  //     busy shots. The glass unrolls down from its stripe cap. p: {tag, title, y, w, h}
  SEK.chapterGlass = function (cfg) {
    const p = Object.assign({ tag: 'CH 01', title: 'TITLE', y: 700, x: 72, w: 836, maxS: 170, exit: cfg.t1 - 0.4, sub: null }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const S = fitSize(p.title, p.w - 110, p.maxS), cap = ink('Bebas', S, 'H').aA, tw = ink('Bebas', S, p.title).w;
    const H = Math.round(cap + 190);
    const clip = el('div', 'a', root, `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${H}px;overflow:hidden`);
    const tint = el('div', 'a', clip, `width:${p.w}px;height:${H}px;background:linear-gradient(160deg,rgba(255,255,255,.14) 0%,rgba(255,255,255,.04) 40%,rgba(0,0,0,.18) 100%);border:1.5px solid rgba(255,255,255,.28);box-sizing:border-box`);
    const sheen = el('div', 'a', clip, `left:0;top:0;width:260px;height:${H}px;background:linear-gradient(100deg,rgba(255,255,255,0),rgba(255,255,255,.16),rgba(255,255,255,0));opacity:0`);
    const inner = el('div', 'a', clip, `width:${p.w}px;height:${H}px`);
    const stripe = el('div', 'a stripe', root, `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:8px`);
    const edge = el('div', 'a edge', root, `left:${p.x}px;top:${p.y - 7}px;height:22px;opacity:0`);
    const tg = line(inner, 'Michroma', 22, p.tag, (p.w - ink('Michroma', 22, p.tag, 0.28).w) / 2, 44, GOLD, { ls: 0.28 });
    const ti = line(inner, 'Bebas', S, p.title, (p.w - tw) / 2, 92, '#fff', { mask: true });
    const rule = el('div', 'a', inner, `left:${p.w / 2 - 60}px;top:${92 + cap + 36}px;width:120px;height:3px;background:${GOLD};transform-origin:50% 50%`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const t0 = cfg.t0;
      const qs = E.outExpo(P(t, t0, t0 + 0.3)), qo = E.inExpo(P(t, p.exit + 0.2, p.exit + 0.4));
      stripe.style.transformOrigin = qo > 0 ? 'right center' : 'left center';
      stripe.style.transform = `scaleX(${(qo > 0 ? 1 - qo : qs).toFixed(5)})`;
      edge.style.opacity = (qs > 0 && qs < 1 ? Math.sin(Math.PI * qs) : 0).toFixed(3); edge.style.transform = `translateX(${(p.w * qs).toFixed(2)}px)`;
      const qr = E.outExpo(P(t, t0 + 0.06, t0 + 0.46)), qc = E.inOutCubic(P(t, p.exit, p.exit + 0.3));
      const vis = qc > 0 ? 1 - qc : qr;
      clip.style.clipPath = vis < 0.999 ? `inset(0 0 ${(100 * (1 - vis)).toFixed(3)}% 0)` : 'none';
      inner.style.transform = qc > 0 ? `translateY(${(-50 * qc).toFixed(2)}px)` : 'none';
      KT.track(tg.g, t, { start: t0 + 0.2, dur: 0.38, spread: 2 });
      KT.rise(ti.g, t, { start: t0 + 0.22, stagger: 0.022, dur: 0.4, dy: 1.05 });
      rule.style.transform = `scaleX(${E.outExpo(P(t, t0 + 0.5, t0 + 0.9)).toFixed(4)})`;
      glint(ti, t, t0 + 0.95, 0.55, { w: 0.22 });
      const sq = P(t, t0 + 0.5, t0 + 1.3);
      sheen.style.opacity = sq > 0 && sq < 1 ? Math.sin(Math.PI * sq).toFixed(3) : 0;
      sheen.style.transform = `translateX(${(-260 + (p.w + 260) * E.inOutCubic(sq)).toFixed(2)}px)`;
      // the compositor frosts the plate inside the visible part of the panel
      window.FX.glass = (window.FX.glass || []).concat([{ x: p.x, y: p.y, w: p.w, h: H * vis, blur: 26, dim: 0.42, op: 1 }]);
    } };
  };

  // ------------------------------------------------------------------ H. CAPTIONS
  // words: [[t0, t1, word] ...] on the scene clock. Pages: consecutive words that fit maxLines x maxW.
  function capPages(words, size, maxW, maxLines) {
    const pages = []; let cur = null;
    words.forEach(([a, b, w]) => {
      const W = ink('Bebas', size, w.toUpperCase()).adv;
      if (!cur) cur = { lines: [[]], widths: [0] };
      let L = cur.lines.length - 1, sp = cur.lines[L].length ? ink('Bebas', size, ' ').adv : 0;
      if (cur.widths[L] + sp + W > maxW) {
        if (cur.lines.length >= maxLines) { pages.push(cur); cur = { lines: [[]], widths: [0] }; }
        else { cur.lines.push([]); cur.widths.push(0); }
        L = cur.lines.length - 1; sp = 0;
      }
      cur.lines[L].push({ a, b, w: w.toUpperCase(), W }); cur.widths[L] += sp + W;
      // sentence end closes the page
      if (/[.?!]$/.test(w)) { pages.push(cur); cur = null; }
    });
    if (cur) pages.push(cur);
    pages.forEach(pg => { const all = pg.lines.flat(); pg.a = all[0].a; pg.b = all[all.length - 1].b; });
    for (let i = 0; i < pages.length; i++) pages[i].end = i + 1 < pages.length ? Math.min(pages[i + 1].a, pages[i].b + 0.6) : pages[i].b + 0.6;
    return pages;
  }
  // H1 boxed karaoke: per-line black plates, every word of the page shown, spoken words white, upcoming words
  //     dim, the active word on a gold box that glides from word to word. p: {words, size, yBottom, maxLines}
  SEK.captionsBox = function (cfg) {
    const p = Object.assign({ words: [], size: 72, yBottom: 1370, maxLines: 2, maxW: 700, cx: 480 }, cfg.p);
    const root = el('div', 'a', stage);
    const pages = capPages(p.words, p.size, p.maxW, p.maxLines);
    const cap = ink('Bebas', p.size, 'H').aA, padX = 18, padY = 16, lh = cap + 2 * padY + 8;
    const sp = ink('Bebas', p.size, ' ').adv;
    pages.forEach(pg => {
      pg.root = el('div', 'a', root);
      const n = pg.lines.length;
      pg.lines.forEach((ln, li) => {
        const y = p.yBottom - (n - li) * lh + 8, W = pg.widths[li], x = p.cx - W / 2;
        el('div', 'a', pg.root, `left:${x - padX}px;top:${y}px;width:${W + 2 * padX}px;height:${cap + 2 * padY}px;background:rgba(0,0,0,.86)`);
      });
      pg.gold = el('div', 'a', pg.root, `height:${cap + 2 * padY - 8}px;background:${GOLD}`);
      pg.lines.forEach((ln, li) => {
        const y = p.yBottom - (n - li) * lh + 8, W = pg.widths[li], x = p.cx - W / 2;
        let cx = x;
        ln.forEach(w => { w.x = cx; w.y = y; w.el = line(pg.root, 'Bebas', p.size, w.w, cx, y + padY, '#fff', { split: false }); cx += w.W + sp; });
      });
      pg.gold.style.top = px(p.yBottom - n * lh + 8 + 4);
    });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      pages.forEach((pg, i) => {
        const vis = t >= pg.a - (i === 0 && pg.a <= cfg.t0 + 0.01 ? 1 : 0.06) && t < pg.end;
        show(pg.root, vis); if (!vis) return;
        const all = pg.lines.flat();
        const qi = i === 0 && pg.a <= cfg.t0 + 0.01 ? 1 : E.outExpo(P(t, pg.a - 0.06, pg.a + 0.14));
        pg.root.style.transform = `translateY(${(14 * (1 - qi)).toFixed(2)}px)`; pg.root.style.opacity = cl(qi * 1.4).toFixed(3);
        let k = -1; all.forEach((w, j) => { if (t >= w.a) k = j; });
        all.forEach((w, j) => { w.el.t.style.color = j === k ? '#000' : j < k ? '#fff' : 'rgba(255,255,255,.5)'; });
        if (k < 0) { pg.gold.style.opacity = 0; return; }
        const w = all[k], pw = k > 0 ? all[k - 1] : w;
        const q = E.outCubic(P(t, w.a, w.a + 0.09)), sameRow = pw.y === w.y;
        const gx = sameRow ? lerp(pw.x, w.x, q) : w.x, gw = sameRow ? lerp(pw.W, w.W, q) : w.W;
        pg.gold.style.opacity = 1;
        pg.gold.style.left = px(gx - 8); pg.gold.style.width = px(gw + 16); pg.gold.style.top = px(w.y + 4);
        const pop = 1 + 0.06 * Math.exp(-(t - w.a) * 16);
        pg.gold.style.transform = `scale(${pop.toFixed(4)})`;
      });
    } };
  };
  // H2 speaker strip: one line, words pop on as spoken (scale + rise), the latest word in gold, a gold speaker
  //     tab on the left; the line pages when full. p: {words, speaker, size, y}
  SEK.captionsStrip = function (cfg) {
    const p = Object.assign({ words: [], speaker: 'OMARIE', size: 80, y: 1170, maxW: 560, cx: 480 }, cfg.p);
    const root = el('div', 'a', stage);
    const pages = capPages(p.words, p.size, p.maxW, 1);
    const cap = ink('Bebas', p.size, 'H').aA, sp = ink('Bebas', p.size, ' ').adv;
    const tabW = Math.ceil(ink('Michroma', 15, p.speaker, 0.14).w + 30), H = cap + 40;
    const maxPW = Math.max(...pages.map(pg => pg.widths[0]));
    const X = Math.round(p.cx - (tabW + 26 + maxPW + 30) / 2);
    const bar = el('div', 'a', root, `left:${X}px;top:${p.y}px;height:${H}px;background:rgba(0,0,0,.86);transform-origin:0 50%`);
    const tab = el('div', 'a', root, `left:${X}px;top:${p.y}px;width:${tabW}px;height:${H}px;background:${GOLD}`);
    const tl = line(tab, 'Michroma', 15, p.speaker, 15, (H - ink('Michroma', 15, 'H').aA) / 2, '#000', { ls: 0.14, split: false });
    pages.forEach(pg => {
      pg.root = el('div', 'a', root);
      let cx = X + tabW + 26;
      pg.lines[0].forEach(w => {
        const wrap = el('div', 'a', pg.root, `left:0;top:0;transform-origin:50% 80%`);
        w.el = line(wrap, 'Bebas', p.size, w.w, cx, p.y + 20, '#fff', { split: false }); w.wrap = wrap; w.x = cx;
        wrap.style.transformOrigin = `${cx + w.W / 2}px ${p.y + 20 + cap}px`;
        cx += w.W + sp;
      });
      pg.W = cx - sp - (X + tabW + 26);
    });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const qi = pages.length && pages[0].a <= cfg.t0 + 0.01 ? 1 : E.outExpo(P(t, cfg.t0, cfg.t0 + 0.3));
      let bw = 0;
      pages.forEach((pg, i) => {
        const vis = t >= pg.a - 0.02 && t < pg.end; show(pg.root, vis); if (!vis) return;
        let k = -1; pg.lines[0].forEach((w, j) => { if (t >= w.a) k = j; });
        pg.lines[0].forEach((w, j) => {
          const q = P(t, w.a, w.a + 0.16), e = E.outBack(q, 2.2);
          w.wrap.style.opacity = t >= w.a ? cl(q * 3).toFixed(3) : 0;
          w.wrap.style.transform = t >= w.a ? `translateY(${(18 * (1 - E.outExpo(q))).toFixed(2)}px) scale(${(0.7 + 0.3 * e).toFixed(4)})` : 'none';
          w.el.t.style.color = j === k ? GOLD : '#fff';
        });
        const last = pg.lines[0][Math.max(0, k)];
        bw = Math.max(bw, k >= 0 ? last.x + last.W - X + 30 : tabW + 60);
      });
      const qo = E.inCubic(P(t, cfg.t1 - 0.3, cfg.t1));
      bar.style.width = px(Math.max(tabW + 60, bw)); bar.style.transform = `scaleX(${(qi * (1 - qo)).toFixed(4)})`;
      tab.style.opacity = (qi * (1 - qo)).toFixed(3);
      root.style.opacity = (1 - qo).toFixed(3);
    } };
  };

  // ------------------------------------------------------------------ I. TRANSITIONS
  // I1 gold light sweep: a slanted light band crosses the frame; the compositor switches plates along its
  //     centre line (new plate on the left). p: {dur, angle (deg from vertical), width}
  SEK.sweep = function (cfg) {
    const p = Object.assign({ angle: 16, width: 360 }, cfg.p);
    const root = el('div', 'a', stage, 'width:1080px;height:1920px;overflow:hidden');
    const k = Math.tan(p.angle * Math.PI / 180);
    const band = el('div', 'a', root, `left:0;top:-200px;width:${p.width * 2}px;height:2320px;transform-origin:0 0`);
    const W = p.width;
    band.style.background = `linear-gradient(90deg, rgba(251,209,1,0) 0px, rgba(251,209,1,.06) ${W - 240}px, rgba(251,209,1,.18) ${W - 120}px, rgba(251,209,1,.52) ${W - 36}px, rgba(255,248,214,.95) ${W - 8}px, #FFFFFF ${W}px, rgba(255,248,214,.9) ${W + 8}px, rgba(251,209,1,.42) ${W + 30}px, rgba(251,209,1,.12) ${W + 90}px, rgba(251,209,1,0) ${W + 170}px)`;
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const q = E.inOutCubic(P(t, cfg.t0, cfg.t1));
      const xc = lerp(-420, 1080 + 420, q);                    // band centre at y = 960 (enters on frame 1)
      band.style.transform = `translate(${f2(xc - W)}px,960px) skewX(${-p.angle}deg) translateY(-1160px)`;
      window.FX.wipe = { x: xc, k: k, soft: 26 };
    } };
  };

  // ------------------------------------------------------------------ reel annotation (not part of the kit)
  // code chip in the top band so Omarie can say "use B2, C1". p: {items: [{t0, t1, codes, name}]}
  SEK.codeChip = function (cfg) {
    const root = el('div', 'a', stage);
    const items = cfg.p.items.map(it => {
      const w = el('div', 'a', root, 'left:40px;top:74px');
      const cw = ink('Michroma', 20, it.codes, 0.1).w, nw = ink('Michroma', 13, it.name, 0.14).w;
      const W = Math.ceil(Math.max(cw, nw) + 88);
      el('div', 'a', w, `width:${W}px;height:74px;background:rgba(0,0,0,.62);border:1px solid rgba(255,255,255,.35);box-sizing:border-box`);
      el('div', 'a', w, `left:12px;top:12px;width:34px;height:50px;border:1.5px dashed rgba(251,209,1,.9);box-sizing:border-box`);
      line(w, 'Michroma', 11, 'KIT', 17, 31, GOLD, { split: false, ls: 0.1 });
      line(w, 'Michroma', 20, it.codes, 60, 16, '#fff', { split: false, ls: 0.1 });
      line(w, 'Michroma', 13, it.name, 61, 48, 'rgba(255,255,255,.72)', { split: false, ls: 0.14 });
      return Object.assign({ w }, it);
    });
    return { code: 'CHIP', chip: true, render(t) {
      let any = false;
      items.forEach(it => {
        const on = t >= it.t0 && t < it.t1; it.w.style.display = on ? 'block' : 'none'; if (!on) return; any = true;
        const q = E.outExpo(P(t, it.t0, it.t0 + 0.2));
        it.w.style.opacity = (it.t0 < 0.01 ? 1 : q).toFixed(3);
        it.w.style.transform = `translateY(${(it.t0 < 0.01 ? 0 : -10 * (1 - q)).toFixed(2)}px)`;
      });
      root.style.display = any ? 'block' : 'none';
    } };
  };
  // kit index card (reel end): every code with its name
  SEK.indexCard = function (cfg) {
    const p = cfg.p;
    const root = el('div', 'a', stage, 'width:1080px;height:1920px');
    const bg = el('div', 'a', root, 'width:1080px;height:1920px;background:#000');
    const lw = 300, lh = lw * 683 / 1148;
    const logo = el('img', 'a', root, `left:${540 - lw / 2}px;top:300px;width:${lw}px`); logo.src = LOGO + 'sce-stacked--white.png';
    const st = el('div', 'a stripe', root, `left:${540 - 150}px;top:${300 + lh + 34}px;width:300px;height:8px`);
    const ti = line(root, 'Bebas', 92, p.title, 540 - ink('Bebas', 92, p.title).w / 2, 300 + lh + 70, '#fff');
    const sb = line(root, 'Michroma', 17, p.sub, 540 - ink('Michroma', 17, p.sub, 0.16).w / 2, 300 + lh + 186, GOLD, { ls: 0.16 });
    const rows = [];
    const y0 = 300 + lh + 250, colX = [90, 520], rh = 44;
    p.rows.forEach((r, i) => {
      const col = i < Math.ceil(p.rows.length / 2) ? 0 : 1, ri = col ? i - Math.ceil(p.rows.length / 2) : i;
      const w = el('div', 'a', root);
      line(w, 'Michroma', 17, r[0], colX[col], y0 + ri * rh, GOLD, { split: false, ls: 0.1 });
      line(w, 'Michroma', 15, r[1], colX[col] + 58, y0 + ri * rh + 2, '#fff', { split: false, ls: 0.1 });
      rows.push(w);
    });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const q = E.inOutCubic(P(t, cfg.t0, cfg.t0 + 0.25));
      bg.style.clipPath = q < 1 ? `inset(${(100 * (1 - q)).toFixed(3)}% 0 0 0)` : 'none';
      KT.wipe(logo, t, { start: cfg.t0 + 0.12, dur: 0.3, dir: 'right', ease: E.inOutCubic, pad: 2 });
      KT.drawStripe(st, t, { start: cfg.t0 + 0.2, dur: 0.3 });
      KT.rise(ti.g, t, { start: cfg.t0 + 0.22, stagger: 0.01, dur: 0.3 });
      ti.w.style.overflow = 'visible';
      KT.track(sb.g, t, { start: cfg.t0 + 0.3, dur: 0.34, spread: 1.6 });
      rows.forEach((w, i) => { const qq = E.outCubic(P(t, cfg.t0 + 0.35 + 0.02 * i, cfg.t0 + 0.55 + 0.02 * i)); w.style.opacity = qq.toFixed(3); w.style.transform = `translateY(${(10 * (1 - qq)).toFixed(2)}px)`; });
      glint(ti, t, cfg.t0 + 1.0, 0.6);
    } };
  };

  // rally-v2 copy: the one change to the kit file -- more of the internal helpers are exported, so
  // lib/v2kit.js can build this vlog's own components in the same language (no kit behaviour changes)
  SEK.helpers = { ink, line, el, panel, panelAt, place, show, svgEl, svgRoot, glint, riseLine, phase, liveDot, liveDotAt,
    bracketPaths, bracketSet, bracketDraw, grow, lerpRect, padRect, pingSet, pingDraw, routeGeom, routeBuild, routeAt,
    meter, meterAt, quoteBuild, quoteAt, nameTag, nameTagAt, capPages, fitSize, sigSvg, f2, px, GOLD, SAFE };
  window.SEK = SEK;
})();
