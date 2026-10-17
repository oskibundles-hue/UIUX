/* v2kit.js -- this vlog's own components, built with the vlog kit's helpers (lib/sekit.js, SEK.helpers) in the
 * same Locked-On language: black plates with the horizontal 78/22 stripe cap, gold #FF4F16 as the only accent,
 * Bebas + Michroma, glyph-level kinetic type, pure functions of t (no timers, no CSS animation, no randomness).
 *
 *   SEK.v2hook      frame-0 hook panel (eyebrow, big title, sub line, SE lockup), masked exit
 *   SEK.v2cta       CTA chip: TEXT OR DM TO BOOK + the text line
 *   SEK.v2slam      one-word kinetic slam (SAFELY.): scale-down slam, flash, stripe, glint, lift-out exit
 *   SEK.v2routeCard CH4 route card: three-stop schematic (VENETIAN -> BLUE DIAMOND -> RED ROCK), comet
 *   SEK.v2route     CH6 route panel: the kit's E1 with separate draw-in / first-stop times and "called" flashes
 *                   (the guide names a stop in the briefing; the stop ticks on its montage shot)
 *   SEK.v2place     place tag (TEAM DINNER / YARD HOUSE)
 *   SEK.v2wall      CH7 quote wall: header + words stacking as each guest says them
 *   SEK.v2lock      car lock-on: tracked brackets, ping, leader, kicker + name label
 *   SEK.v2end       the Locked-On end card (from the approved rally layer, 2026-09-15-rally/story.html)
 */
(function () {
  const H_ = SEK.helpers;
  const { ink, line, el, panel, panelAt, show, svgEl, svgRoot, glint, riseLine, bracketSet, bracketDraw, grow, lerpRect,
          padRect, pingSet, pingDraw, routeGeom, f2, px, GOLD, SAFE, fitSize, sigSvg, liveDot, liveDotAt } = H_;
  const E = KT.ease, P = KT.p, cl = KT.cl, lerp = KT.lerp;
  const FPS = 30000 / 1001;
  const LOGO = '../../../02-logos/png/';
  const centreX = (fam, size, text, cx, ls) => cx - ink(fam, size, text, ls).w / 2;
  let CTX = null;
  SEK.v2init = ctx => { CTX = ctx; };
  const stageEl = () => document.getElementById('stage');

  // ---------------------------------------------------------------- hook (complete on frame 0)
  SEK.v2hook = function (cfg) {
    const p = Object.assign({ x: 54, y: 360, w: 856, h: 470, exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stageEl());
    const clip = el('div', 'a', root, `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px;overflow:hidden`);
    el('div', 'a', clip, `width:${p.w}px;height:${p.h}px;background:#000`);
    const inner = el('div', 'a', clip, `width:${p.w}px;height:${p.h}px`);
    const stripe = el('div', 'a stripe', root, `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:8px`);
    const redge = el('div', 'a', root, `left:${p.x}px;top:0;width:${p.w}px;height:3px;background:${GOLD};box-shadow:0 0 14px 3px rgba(255,79,22,.55);opacity:0`);
    const sweep = el('div', 'a', root, `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:8px;overflow:hidden`);
    const sweepBar = el('div', 'a', sweep, 'width:120px;height:8px;background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,.95),rgba(255,255,255,0))');
    const X = 36;
    const eb = line(inner, 'Michroma', 21, p.eyebrow, X, 38, GOLD, { dots: '#fff' });
    eb.g.forEach(s => { if (s.dataset.ch === '×') s.style.color = '#fff'; });
    const s1 = fitSize(p.line1, p.w - 2 * X, 236);
    const l1 = line(inner, 'Bebas', s1, p.line1, X, 84, '#fff', { mask: true });
    const cap1 = ink('Bebas', s1, 'H').aA;
    const l2 = line(inner, 'Bebas', 76, p.line2, X, 84 + cap1 + 26, GOLD, { mask: true, dots: '#fff' });
    const cap2 = ink('Bebas', 76, 'H').aA;
    const lw = 250, lh = lw * 215 / 1527;
    const ly = 84 + cap1 + 26 + cap2 + 34;
    const logoW = el('div', 'a', inner, `left:${X}px;top:${ly}px;width:${lw}px;height:${lh.toFixed(2)}px`);
    const img = el('img', '', logoW, `width:${lw}px;display:block`); img.src = LOGO + 'sce-primary-horizontal--white.png';
    const H = Math.round(ly + lh + 36);
    clip.style.height = px(H); clip.firstChild.style.height = px(H); inner.style.height = px(H);
    return { code: cfg.code, H, render(t) {
      const on = t >= cfg.t0 && t < p.exit + 0.42; show(root, on); if (!on) return;
      const g1 = KT.glint(l1.g, t, { start: 0.28, dur: 0.5, base: '#FFFFFF', warm: '#FFD9C9', hot: GOLD, width: 0.2 * l1.g.W, angle: 106 });
      l1.w.style.filter = g1 > 0 ? `drop-shadow(0 0 ${(10 * g1).toFixed(2)}px rgba(255,79,22,${(.35 * g1).toFixed(3)}))` : 'none';
      glint(l2, t, 0.85, 0.45, { base: GOLD, warm: '#FFB08F', hot: '#FFFFFF', w: 0.18, glow: 8 });
      const qs = P(t, 1.0, 1.4), sw = qs > 0 && qs < 1;
      sweepBar.style.display = sw ? 'block' : 'none';
      sweepBar.style.transform = `translateX(${(-120 + (p.w + 240) * E.inOutCubic(qs)).toFixed(2)}px)`;
      const x0 = p.exit;
      const qp = E.inOutCubic(P(t, x0, x0 + 0.26));
      inner.style.transform = qp > 0 ? `translateY(${(-80 * qp).toFixed(2)}px)` : 'none';
      clip.style.clipPath = qp > 0 ? `inset(0 0 ${(100 * qp).toFixed(3)}% 0)` : 'none';
      redge.style.opacity = qp > 0 && qp < 1 ? Math.min(1, Math.sin(Math.PI * qp) * 2).toFixed(4) : 0;
      redge.style.transform = `translateY(${(p.y + H * (1 - qp) - 2).toFixed(2)}px)`;
      const qst = E.inExpo(P(t, x0 + 0.2, x0 + 0.38));
      stripe.style.transformOrigin = 'right center';
      stripe.style.transform = qst > 0 ? `scaleX(${(1 - qst).toFixed(5)})` : 'none';
      stripe.style.opacity = qst >= 1 ? 0 : 1;
    } };
  };

  // ---------------------------------------------------------------- CTA chip
  SEK.v2cta = function (cfg) {
    const p = Object.assign({ x: 54, y: 300, kicker: 'TEXT OR DM TO BOOK', line: '(725) 425-3583', sub: '', exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stageEl());
    const kw = ink('Michroma', 22, p.kicker).w, lw = ink('Bebas', 84, p.line).w, sw = p.sub ? ink('Michroma', 16, p.sub, 0.12).w : 0;
    const W = Math.ceil(Math.max(kw, lw, sw) + 64), capL = ink('Bebas', 84, 'H').aA;
    const Hh = Math.round(30 + 17 + 20 + capL + (p.sub ? 22 + 14 : 0) + 30);
    const pn = panel(root, p.x, p.y, W, Hh, { stripe: 6 });
    const dot = liveDot(pn.inner, 38, 40, 6);
    const kk = line(pn.inner, 'Michroma', 22, p.kicker, 58, 31, GOLD);
    const ln = line(pn.inner, 'Bebas', 84, p.line, 32, 30 + 17 + 20, '#fff', { mask: true });
    const sb = p.sub ? line(pn.inner, 'Michroma', 16, p.sub, 34, 30 + 17 + 20 + capL + 22, 'rgba(255,255,255,.78)', { ls: 0.12 }) : null;
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < p.exit + 0.4; show(root, on); if (!on) return;
      panelAt(pn, t, cfg.t0, p.exit);
      KT.track(kk.g, t, { start: cfg.t0 + 0.12, dur: 0.34, spread: 1.7 });
      riseLine(ln, t, cfg.t0 + 0.2, 0.34);
      if (sb) KT.track(sb.g, t, { start: cfg.t0 + 0.3, dur: 0.34, spread: 1.5 });
      liveDotAt(dot, t, cfg.t0 + 0.3, 1.1);
      glint(ln, t, cfg.t0 + 0.9, 0.55, { w: 0.2 });
      glint(ln, t, cfg.t0 + 4.6, 0.55, { w: 0.2 });
    } };
  };

  // ---------------------------------------------------------------- one-word slam
  SEK.v2slam = function (cfg) {
    const p = Object.assign({ word: 'SAFELY.', y: 700, maxS: 330, maxW: 820, exit: cfg.t1 - 0.3, color: '#fff' }, cfg.p);
    const root = el('div', 'a', stageEl(), 'width:1080px;height:1920px');
    const S = fitSize(p.word, p.maxW, p.maxS), cap = ink('Bebas', S, 'H').aA, tw = ink('Bebas', S, p.word).w;
    const cx = SAFE.x0 + (SAFE.x1 - SAFE.x0) / 2;
    const scrim = el('div', 'a', root, `left:0;top:${p.y - 240}px;width:1080px;height:${cap + 480}px;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,.45) 35%,rgba(0,0,0,.45) 65%,rgba(0,0,0,0) 100%)`);
    const holder = el('div', 'a', root, `width:1080px;height:1920px;transform-origin:${cx}px ${p.y + cap / 2}px`);
    const mask = el('div', 'a', holder, `left:0;top:${p.y - 40}px;width:1080px;height:${cap + 80}px;overflow:hidden`);
    const w = line(mask, 'Bebas', S, p.word, cx - tw / 2, 40, p.color);
    const stripe = el('div', 'a stripe', root, `left:${cx - tw / 2}px;top:${p.y + cap + 28}px;width:${tw}px;height:12px`);
    const flash = el('div', 'a', root, `left:${cx - tw / 2 - 60}px;top:${p.y - 60}px;width:${tw + 120}px;height:${cap + 120}px;background:radial-gradient(ellipse at center,rgba(255,224,210,.6) 0%,rgba(255,79,22,.2) 40%,rgba(255,79,22,0) 70%);opacity:0`);
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < p.exit + 0.3; show(root, on); if (!on) return;
      const t0 = cfg.t0, th = t0 + 0.12;
      const qs = E.outExpo(P(t, t0, th + 0.05));
      const qo = E.inCubic(P(t, p.exit, p.exit + 0.26));
      scrim.style.opacity = (E.outCubic(P(t, t0, t0 + 0.14)) * (1 - E.inCubic(P(t, p.exit + 0.08, p.exit + 0.3)))).toFixed(3);
      holder.style.transform = `scale(${lerp(1.7, 1, qs).toFixed(5)}) translateY(${(-cap * 0.35 * qo).toFixed(2)}px)`;
      holder.style.opacity = (1 - qo).toFixed(4);       // lifts a little and fades: never leaves the safe area
      w.w.style.opacity = cl(P(t, t0, t0 + 0.05)).toFixed(3);
      const hit = t >= th ? Math.exp(-(t - th) * 7) : 0;
      flash.style.opacity = (0.5 * hit).toFixed(3);
      const qst = E.outExpo(P(t, th, th + 0.3)), qsto = E.inExpo(P(t, p.exit, p.exit + 0.26));
      stripe.style.transformOrigin = qsto > 0 ? 'right center' : 'left center';
      stripe.style.transform = `scaleX(${(qsto > 0 ? 1 - qsto : qst).toFixed(5)})`;
      glint(w, t, th + 0.2, 0.5, { w: 0.22, glow: 14 });
    } };
  };

  // ---------------------------------------------------------------- route helpers (a copy of the kit's routeAt with
  // separate draw-in / first-stop times and "called" flashes on the labels)
  function routeAt2(RB, t, steps, o) {
    const g = RB.g;
    let s = 0, active = 0; const tArr = [];
    tArr[0] = o.firstAt;
    steps.forEach((st, j) => {
      const from = j === 0 ? RB.nodes[0].s : RB.nodes[steps[j - 1].k].s, to = RB.nodes[st.k].s;
      const dur = st.dur ?? o.dur;
      const q = E.inOutCubic(P(t, st.t - dur, st.t));
      if (t >= st.t - dur) s = lerp(from, to, q);
      if (t >= st.t) active = st.k;
      tArr[st.k] = st.t;
    });
    const qd = E.outCubic(P(t, o.drawIn, o.drawIn + 0.5));
    RB.done.setAttribute('stroke-dasharray', `${f2(t >= o.firstAt ? s : 0)} ${f2(g.total + 50)}`);
    RB.under.setAttribute('stroke-dasharray', `${f2(g.total * qd)} ${f2(g.total + 50)}`);
    RB.base.style.opacity = qd.toFixed(3);
    const tl = Math.min(s, 140);
    RB.trail.setAttribute('stroke-dasharray', `0 ${f2(Math.max(0, s - tl))} ${f2(tl)} ${f2(g.total + 400)}`);
    const moving = steps.some(st => t >= st.t - (st.dur ?? o.dur) && t < st.t);
    RB.trail.setAttribute('opacity', moving ? 0.9 : 0);
    const [cx, cy] = g.at(s);
    [RB.comet, RB.cometG].forEach(c => { c.setAttribute('cx', f2(cx)); c.setAttribute('cy', f2(cy)); c.setAttribute('opacity', moving ? 1 : 0); });
    RB.nodes.forEach((N, k) => {
      const tk = tArr[k] ?? 1e9;
      const reached = t >= tk;
      const q = E.outBack(P(t, tk, tk + 0.24), 2.2);
      N.core.setAttribute('opacity', reached ? 1 : 0);
      N.core.setAttribute('r', f2(o.nr * 0.55 * (reached ? q : 0)));
      N.ring.setAttribute('stroke', reached ? GOLD : 'rgba(255,255,255,.6)');
      N.ring.setAttribute('opacity', qd.toFixed(3));
      const isAct = k === active && reached;
      if (isAct) { const ph = ((t - tk) % 1.0) / 1.0; N.rip.setAttribute('r', f2(o.nr * (1 + 1.8 * E.outCubic(ph)))); N.rip.setAttribute('opacity', (0.9 * (1 - ph)).toFixed(3)); }
      else N.rip.setAttribute('opacity', 0);
      const L = RB.labels[k];
      const qa = P(t, (o.labelsIn ?? 0) + 0.05 * k, (o.labelsIn ?? 0) + 0.05 * k + 0.3);
      L.ln.t.style.transform = `translateY(${(108 * (1 - E.outExpo(qa))).toFixed(2)}%)`;
      L.ln.t.style.opacity = qa > 0 ? 1 : 0;
      // "called": the guide names the stop -> the label flashes gold and back, before it is reached
      let call = 0;
      (o.called || []).forEach(c => { if (c.k === k && t >= c.t) call = Math.max(call, Math.exp(-(t - c.t) * 2.2)); });
      const base = isAct ? 1 : reached ? 0.78 : 0.42 + 0.5 * call;
      const gold = call > 0.05 && !reached ? call : 0;
      L.ln.t.style.color = gold > 0 ? `rgba(${Math.round(255)},${Math.round(255 - 176 * gold)},${Math.round(255 - 233 * gold)},${base.toFixed(3)})` : `rgba(255,255,255,${base.toFixed(3)})`;
      L.ul.style.transform = `scaleX(${(isAct ? E.outExpo(P(t, tk, tk + 0.3)) : 0).toFixed(4)})`;
      glint(L.ln, t, tk < 1e8 ? tk + 0.1 : 1e9, 0.45, { w: 0.35 });
      (o.called || []).forEach(c => { if (c.k === k) glint(L.ln, t, c.t, 0.45, { w: 0.35 }); });
    });
    return { s, active };
  }

  // CH6 route panel (E1 geometry, 6 stops). p: {x, y, title, waypoints, drawIn, firstAt, called: [{k,t}], steps: [{t,k}]}
  SEK.v2route = function (cfg) {
    const p = Object.assign({ x: 54, y: 300, title: 'THE ROUTE', waypoints: [], steps: [], called: [], exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stageEl());
    const strip = p.layout === 'strip';
    const W = strip ? (p.w || 853) : 452, Hh = strip ? 244 : 470;
    const pn = panel(root, p.x, p.y, W, Hh, { stripe: 6, alpha: .88 });
    const hd = line(pn.inner, 'Michroma', 17, p.title, 28, 26, GOLD);
    const n = p.waypoints.length;
    const cnt = el('div', 'a', pn.inner, `left:${W - 118}px;top:22px;width:90px;height:22px;overflow:hidden`);
    const cstrip = el('div', '', cnt, 'display:flex;flex-direction:column');
    const p2 = v => String(v).padStart(2, '0');
    for (let k = 0; k <= n; k++) el('div', 'mic', cstrip, 'font-size:17px;height:22px;line-height:22px;color:#fff;letter-spacing:.08em;text-align:right', `${p2(k)} / ${p2(n)}`);
    const svg = svgRoot(pn.inner); svg.setAttribute('width', W); svg.setAttribute('height', Hh); svg.setAttribute('viewBox', `0 0 ${W} ${Hh}`);
    let RB;
    if (strip) {
      // horizontal schematic: the line runs left -> right with two 45-degree jogs, labels alternate below it
      const x0 = 62, x1 = W - 62, dx = (x1 - x0) / (n - 1), YA = 96, YB = 124, LS = 34;
      const ys = [YA, YA, YB, YB, YA, YA];
      const pts = [], nodeIdx = [];
      for (let k = 0; k < n; k++) {
        const x = x0 + k * dx, y = ys[k % ys.length];
        if (k > 0 && y !== ys[(k - 1) % ys.length]) { const py = ys[(k - 1) % ys.length]; pts.push([x - dx + 18, py]); pts.push([x - dx + 18 + Math.abs(y - py), y]); }
        nodeIdx.push(pts.length); pts.push([x, y]);
      }
      const capL = ink('Bebas', LS, 'H').aA;
      RB = H_.routeBuild(pn.inner, svg, { pts, nodes: p.waypoints.map((w, k) => ({ i: nodeIdx[k], label: w,
        lx: -Math.min(ink('Bebas', LS, w).w / 2, k === 0 ? 0 : 1e9) - (k === n - 1 ? Math.max(0, ink('Bebas', LS, w).w / 2 - 20) : 0),
        ly: (k % 2 ? 76 : 40) + (YB - ys[k % ys.length]) + capL / 2 })) }, { sw: 6, nr: 11, ls: LS, lx: 0, dur: 0.5 });
    } else {
      const X1 = 44, X2 = 88, Y = [96, 158, 220, 282, 344, 406];
      const pts = [[X1, Y[0]], [X1, Y[1]], [X1, Y[1] + 14], [X2, Y[1] + 58], [X2, Y[2]], [X2, Y[3]], [X2, Y[3] + 14], [X1, Y[3] + 58], [X1, Y[4]], [X1, Y[5]]];
      const nodeIdx = [0, 1, 4, 5, 8, 9];
      RB = H_.routeBuild(pn.inner, svg, { pts, nodes: p.waypoints.map((w, k) => ({ i: nodeIdx[k], label: w })) }, { sw: 6, nr: 11, ls: 40, lx: 30, dur: 0.5 });
    }
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < p.exit + 0.4; show(root, on); if (!on) return;
      panelAt(pn, t, cfg.t0, p.exit);
      KT.track(hd.g, t, { start: cfg.t0 + 0.1, dur: 0.34, spread: 1.8 });
      const r = routeAt2(RB, t, p.steps, { nr: 11, dur: 0.5, drawIn: p.drawIn ?? cfg.t0 + 0.12, labelsIn: cfg.t0 + 0.14, firstAt: p.firstAt, called: p.called });
      let qc = E.outExpo(P(t, p.firstAt, p.firstAt + 0.14)), prevK = 0;
      p.steps.forEach(st => { qc += (st.k - prevK) * E.outExpo(P(t, st.t, st.t + 0.14)); prevK = st.k; });
      cstrip.style.transform = `translateY(${(-22 * qc).toFixed(3)}px)`;
      svg.style.setProperty('--d', `"${r.s.toFixed(2)}"`);
    } };
  };

  // CH4 route card: three stops, big, vertical, in a panel. p: {x, y, w, title, sub, waypoints[3], firstAt, steps}
  SEK.v2routeCard = function (cfg) {
    const p = Object.assign({ x: 54, y: 820, w: 853, title: 'THE ROUTE', sub: '', waypoints: [], steps: [], exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stageEl());
    const n = p.waypoints.length, pitch = 150, top = 110, Hh = top + pitch * (n - 1) + 90;
    const pn = panel(root, p.x, p.y, p.w, Hh, { stripe: 8, alpha: .88 });
    const hd = line(pn.inner, 'Michroma', 20, p.title, 36, 34, GOLD, { ls: 0.2 });
    const sb = p.sub ? line(pn.inner, 'Michroma', 15, p.sub, 36 + ink('Michroma', 20, p.title, 0.2).adv + 26, 37, 'rgba(255,255,255,.7)', { ls: 0.16, dots: GOLD }) : null;
    const X = 76, pts = p.waypoints.map((w, k) => [X, top + k * pitch]);
    const svg = svgRoot(pn.inner); svg.setAttribute('width', p.w); svg.setAttribute('height', Hh); svg.setAttribute('viewBox', `0 0 ${p.w} ${Hh}`);
    const RB = H_.routeBuild(pn.inner, svg, { pts, nodes: p.waypoints.map((w, k) => ({ i: k, label: w })) }, { sw: 9, nr: 17, ls: 88, lx: 52, dur: 0.5 });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < p.exit + 0.4; show(root, on); if (!on) return;
      panelAt(pn, t, cfg.t0, p.exit, { din: 0.3 });
      KT.track(hd.g, t, { start: cfg.t0 + 0.1, dur: 0.34, spread: 1.8 });
      if (sb) KT.track(sb.g, t, { start: cfg.t0 + 0.18, dur: 0.34, spread: 1.6 });
      const r = routeAt2(RB, t, p.steps, { nr: 17, dur: 0.55, drawIn: cfg.t0 + 0.1, labelsIn: cfg.t0 + 0.12, firstAt: p.firstAt, called: [] });
      svg.style.setProperty('--d', `"${r.s.toFixed(2)}"`);
    } };
  };

  // ---------------------------------------------------------------- place tag
  SEK.v2place = function (cfg) {
    const p = Object.assign({ x: 54, y: 300, kicker: 'TEAM DINNER', name: 'YARD HOUSE', exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stageEl());
    const capN = ink('Bebas', 96, 'H').aA;
    const W = Math.ceil(Math.max(ink('Michroma', 20, p.kicker, 0.14).w + 30, ink('Bebas', 96, p.name).w) + 64), Hh = Math.round(28 + 16 + 22 + capN + 30);
    const pn = panel(root, p.x, p.y, W, Hh, { stripe: 6 });
    el('div', 'a', pn.inner, `left:32px;top:30px;width:12px;height:12px;background:${GOLD}`);
    const kk = line(pn.inner, 'Michroma', 20, p.kicker, 54, 28, '#fff', { ls: 0.14 });
    const nm = line(pn.inner, 'Bebas', 96, p.name, 30, 28 + 16 + 22, '#fff', { mask: true });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < p.exit + 0.4; show(root, on); if (!on) return;
      panelAt(pn, t, cfg.t0, p.exit);
      KT.track(kk.g, t, { start: cfg.t0 + 0.12, dur: 0.34, spread: 1.7 });
      riseLine(nm, t, cfg.t0 + 0.18, 0.34);
      glint(nm, t, cfg.t0 + 0.85, 0.55, { w: 0.22 });
    } };
  };

  // ---------------------------------------------------------------- quote wall
  // p: {header, x, y, items: [{w, t}], size, gap}
  SEK.v2wall = function (cfg) {
    const p = Object.assign({ header: 'EGNYTE ON THE DAY', x: 54, y: 300, w: 853, items: [], size: 104, gap: 16, flow: false, exit: cfg.t1 - 0.4 }, cfg.p);
    const root = el('div', 'a', stageEl());
    const cap = ink('Bebas', p.size, 'H').aA, rowH = cap + 44;
    const hW = Math.ceil(ink('Michroma', 19, p.header, 0.2).w + 60);
    const head = panel(root, p.x, p.y, hW, 62, { stripe: 6 });
    const hl = line(head.inner, 'Michroma', 19, p.header, 30, 26, GOLD, { ls: 0.2 });
    // chips flow left to right and wrap inside p.w (the wall stays in the top band, clear of faces)
    let cx0 = 0, cy0 = 0;
    const pos = p.items.map(it => {
      const W = Math.ceil(ink('Bebas', p.size, it.w).w + 58 + 56);
      if (p.flow && cx0 > 0 && cx0 + W > p.w) { cx0 = 0; cy0 += rowH + p.gap; }
      const q = p.flow ? { x: p.x + cx0, y: p.y + 62 + p.gap + cy0, W } : null;
      cx0 += W + p.gap;
      return q;
    });
    const rows = p.items.map((it, k) => {
      const y = p.flow ? pos[k].y : p.y + 62 + p.gap + k * (rowH + p.gap);
      const idx = String(k + 1).padStart(2, '0');
      const tw = ink('Bebas', p.size, it.w).w, W = Math.ceil(tw + 58 + 56);
      const x = p.flow ? pos[k].x : p.x;
      const wrap = el('div', 'a', root, `left:${x}px;top:${y}px;width:${W}px;height:${rowH}px;transform-origin:0 50%`);
      const bg = el('div', 'a', wrap, `width:${W}px;height:${rowH}px;background:rgba(0,0,0,.88);box-shadow:0 10px 30px rgba(0,0,0,.3)`);
      const bar = el('div', 'a', wrap, `left:0;top:0;width:6px;height:${rowH}px;background:${GOLD}`);
      const ix = line(wrap, 'Michroma', 16, idx, 22, (rowH - ink('Michroma', 16, 'H').aA) / 2, GOLD, { split: false });
      const tx = line(wrap, 'Bebas', p.size, it.w, 58, 22, '#fff');
      const fl = el('div', 'a', wrap, `width:${W}px;height:${rowH}px;background:linear-gradient(90deg,rgba(255,224,210,.75),rgba(255,79,22,.35) 40%,rgba(255,79,22,0));opacity:0`);
      return { wrap, bg, tx, fl, t: it.t, W };
    });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < p.exit + 0.4; show(root, on); if (!on) return;
      panelAt(head, t, cfg.t0, p.exit);
      KT.track(hl.g, t, { start: cfg.t0 + 0.1, dur: 0.34, spread: 1.8 });
      const qo = E.inCubic(P(t, p.exit + 0.05, p.exit + 0.35));
      rows.forEach((r, k) => {
        const vis = t >= r.t - 0.02;
        r.wrap.style.display = vis ? 'block' : 'none'; if (!vis) return;
        const q = E.outExpo(P(t, r.t - 0.02, r.t + 0.2));
        const later = rows.filter(o => o.t > r.t && t >= o.t).length;
        r.wrap.style.transform = `translateX(${(-140 * (1 - q) - 60 * qo * (1 + k * 0.3)).toFixed(2)}px) scale(${lerp(1.18, 1, q).toFixed(4)})`;
        r.wrap.style.opacity = (cl(q * 2.5) * (1 - qo) * (later ? 0.8 : 1)).toFixed(3);
        const hit = t >= r.t ? Math.exp(-(t - r.t) * 5) : 0;
        r.fl.style.opacity = (0.8 * hit).toFixed(3);
        r.tx.t.style.color = hit > 0.1 ? `rgb(255,${Math.round(255 - 46 * hit)},${Math.round(255 - 254 * hit)})` : '#fff';
        glint(r.tx, t, r.t + 0.35, 0.5, { w: 0.25, glow: 10 });
      });
    } };
  };

  // ---------------------------------------------------------------- car lock-on (kicker + name)
  // p: {track, kicker, name, acquire, exit, dx, gap, side: 'above'|'below', follow}
  SEK.v2lock = function (cfg) {
    const p = Object.assign({ track: '', kicker: '', name: '', acquire: cfg.t0, exit: cfg.t1 - 0.3, dx: -20, gap: 70, side: 'above', follow: 0.45, pad: 0.08 }, cfg.p);
    const root = el('div', 'a', stageEl(), 'width:1080px;height:1920px');
    const svg = svgRoot(root);
    const B = bracketSet(svg), pings = pingSet(svg);
    const lu = svgEl('path', { fill: 'none', stroke: 'rgba(0,0,0,.45)', 'stroke-width': 8 }, svg), lo = svgEl('path', { fill: 'none', stroke: GOLD, 'stroke-width': 3 }, svg);
    const dotU = svgEl('circle', { r: 10, fill: 'rgba(0,0,0,.45)' }, svg), dot = svgEl('circle', { r: 6.5, fill: GOLD }, svg);
    const ns = Math.min(66, 66 * 700 / ink('Bebas', 66, p.name).w);
    const kw = ink('Michroma', 20, p.kicker).w, nw = ink('Bebas', ns, p.name).w;
    const LW = Math.ceil(Math.max(kw, nw) + 64), capN = ink('Bebas', ns, 'H').aA, LH = Math.round(26 + 15 + 18 + capN + 26);
    const lab = el('div', 'a', root, `width:${LW}px;height:${LH}px`);
    el('div', 'a', lab, `width:${LW}px;height:${LH}px;background:rgba(0,0,0,.9);box-shadow:0 10px 30px rgba(0,0,0,.3)`);
    const stripe = el('div', 'a stripe', lab, `width:${LW}px;height:6px`);
    const kk = line(lab, 'Michroma', 20, p.kicker, 32, 26, GOLD, { mask: true });
    const nm = line(lab, 'Bebas', ns, p.name, 30, 26 + 15 + 18, '#fff', { mask: true });
    return { code: cfg.code, render(t) {
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const b = CTX.box(p.track, t); if (!b) { show(root, false); return; }
      const ta = p.acquire, tx = p.exit;
      const tgt = padRect(b, p.pad * Math.min(b.w, b.h) + 12);
      const qa = E.outExpo(cl((t - ta) * FPS / 8));
      let r = lerpRect(grow(tgt, 1.7), tgt, qa);
      const tl = ta + 0.26, pl = t >= tl ? Math.exp(-(t - tl) * 14) * Math.min(1, (t - tl) * FPS / 1.5) : 0;
      r = grow(r, (1 + 0.06 * pl) * (1 - 0.5 * E.inCubic(P(t, tx + 0.06, tx + 0.26))));
      const pp = bracketDraw(B, r, { maxL: 50 });
      B.bo.setAttribute('stroke', pl > 0.05 ? `rgb(255,${Math.round(79 + 176 * pl)},${Math.round(22 + 233 * pl)})` : GOLD);
      [B.tu, B.to].forEach(e => e.setAttribute('opacity', cl(qa * 1.4 - 0.4).toFixed(3)));
      pingDraw(pings, tgt, t, tl);
      svg.style.opacity = (cl(qa * 3) * (1 - E.inCubic(P(t, tx + 0.1, tx + 0.26)))).toFixed(4);
      const b0 = CTX.box(p.track, ta + 0.3) || b, t0r = padRect(b0, p.pad * Math.min(b0.w, b0.h) + 12);
      const above = p.side === 'above';
      const lx = cl(t0r.x + p.dx + p.follow * (tgt.x - t0r.x), SAFE.x0, SAFE.x1 - LW);
      const ly = cl((above ? t0r.y - p.gap - LH : t0r.y + t0r.h + p.gap) + p.follow * (tgt.y - t0r.y), SAFE.y0, SAFE.y1 - LH);
      lab.style.transform = `translate(${f2(lx)}px,${f2(ly)}px)`;
      const bx = r.x, by = above ? r.y : r.y + r.h, Ax = cl(bx, lx + 20, lx + LW - 20), Ay = above ? ly + LH : ly;
      const qL = E.inOutCubic(P(t, ta + 0.2, ta + 0.44)) * (1 - E.inCubic(P(t, tx, tx + 0.14)));
      const len = Math.hypot(Ax - bx, Ay - by), d = `M${f2(bx)},${f2(by)}L${f2(Ax)},${f2(Ay)}`;
      [lu, lo].forEach(e => { e.setAttribute('d', d); e.setAttribute('stroke-dasharray', `${f2(len * qL)} ${f2(len + 20)}`); });
      [dot, dotU].forEach(c => { c.setAttribute('cx', f2(bx)); c.setAttribute('cy', f2(by)); c.setAttribute('opacity', qL > 0 && qL < 1.01 && t < tx + 0.14 ? 1 : 0); });
      const tin = ta + 0.28, qp = E.outExpo(P(t, tin, tin + 0.3)), qpo = E.inCubic(P(t, tx, tx + 0.2));
      const right = qpo > 0 ? 100 * qpo : 100 * (1 - qp);
      lab.style.clipPath = right > 0.001 ? `inset(-40px ${right.toFixed(3)}% -40px 0)` : 'inset(-40px 0 -40px 0)';
      lab.style.display = qp > 0 && qpo < 1 ? 'block' : 'none';
      KT.drawStripe(stripe, t, { start: tin + 0.04, dur: 0.26 });
      riseLine(kk, t, tin + 0.08); riseLine(nm, t, tin + 0.12);
      glint(nm, t, tin + 0.7, 0.5);
      sigSvg(svg, pp.br + qL.toFixed(3));
    } };
  };

  // ---------------------------------------------------------------- end card (the approved rally layer's card)
  SEK.v2end = function (cfg) {
    const e = cfg.p, WIPE = 0.118;
    const root = el('div', 'a', stageEl(), 'width:1080px;height:1920px');
    const pnl = el('div', 'a', root, 'width:1080px;height:1920px;background:#000');
    const wipeStripe = el('div', 'a', root, 'width:1080px;height:160px;background:linear-gradient(180deg,rgba(255,79,22,.34) 0,rgba(255,79,22,.10) 30%,rgba(255,79,22,0) 100%);opacity:0');
    const body = el('div', 'a', root, 'width:1080px;height:1920px;transform-origin:540px 900px');
    const lw = 400, lh = lw * 683 / 1148;
    const logoW = el('div', 'a', body, `left:${540 - lw / 2}px;top:352px;width:${lw}px;height:${lh.toFixed(2)}px`);
    const logo = el('img', '', logoW, `width:${lw}px;display:block`); logo.src = LOGO + 'sce-stacked--white.png';
    const logoEdge = el('div', 'a edge', logoW, `height:${lh + 12}px;top:-6px;opacity:0`);
    const stripe = el('div', 'a stripe', body, 'left:360px;top:654px;width:360px;height:8px');
    const L = {};
    const C = (fam, size, txt, y, col, o) => line(body, fam, size, txt, centreX(fam, size, txt, 540), y, col, o);
    L.tag = C('Bebas', 104, e.tagline, 700, '#fff', { mask: true });
    L.cta = C('Michroma', 30, e.cta, 848, GOLD);
    L.phone = C('Bebas', 124, e.phone, 904, '#fff', { mask: true });
    L.url = C('Bebas', 72, e.url, 1044, '#fff');
    L.handle = C('Bebas', 72, e.handle, 1122, '#fff');
    L.loc = C('Michroma', 26, e.locations, 1232, '#fff', { dots: GOLD });
    L.req = C('Bebas', 44, e.requirement, 1290, '#fff', { dots: GOLD });
    const rule = el('div', 'a', body, 'left:470px;top:1374px;width:140px;height:2px;background:rgba(255,255,255,.35);transform-origin:50% 50%');
    L.credit = C('Michroma', 20, e.credit, 1406, '#fff');
    L.credit.t.style.opacity = 0.78;
    return { code: cfg.code, render(t) {
      const t0 = cfg.t0, on = t >= t0; show(root, on); if (!on) return;
      const qw = E.inOutCubic(P(t, t0, t0 + WIPE));
      const FE = 90, yb = (1920 + FE) * qw;
      if (qw >= 1) { pnl.style.webkitMaskImage = 'none'; pnl.style.maskImage = 'none'; }
      else { const m = `linear-gradient(0deg,#000 0px,#000 ${Math.max(0, yb - FE).toFixed(2)}px,rgba(0,0,0,0) ${yb.toFixed(2)}px)`; pnl.style.webkitMaskImage = m; pnl.style.maskImage = m; }
      pnl.style.display = qw > 0 ? 'block' : 'none';
      wipeStripe.style.opacity = Math.sin(Math.PI * P(t, t0 + WIPE - 0.02, t0 + WIPE + 0.30)).toFixed(4);
      const s0 = t0 + 0.06;
      KT.wipe(logo, t, { start: s0, dur: 0.24, dir: 'right', edge: logoEdge, ease: E.inOutCubic, pad: 2 });
      KT.drawStripe(stripe, t, { start: s0 + 0.06, dur: 0.22 });
      KT.rise(L.tag.g, t, { start: s0 + 0.08, stagger: 0.006, dur: 0.28, dy: 1.05, ease: E.outExpo });
      KT.track(L.cta.g, t, { start: s0 + 0.14, dur: 0.26, spread: 1.7, stagger: 0.004 });
      KT.rise(L.phone.g, t, { start: s0 + 0.16, stagger: 0.006, dur: 0.28, dy: 1.05, ease: E.outExpo });
      const fu = (ln, st) => { const q = E.outCubic(P(t, st, st + 0.22)); ln.w.style.opacity = q.toFixed(4); ln.w.style.transform = `translateY(${(14 * (1 - q)).toFixed(3)}px)`; };
      fu(L.url, s0 + 0.22); fu(L.handle, s0 + 0.26);
      KT.track(L.loc.g, t, { start: s0 + 0.24, dur: 0.24, spread: 1.6, stagger: 0.004 });
      fu(L.req, s0 + 0.28);
      rule.style.transform = `scaleX(${E.outExpo(P(t, s0 + 0.30, s0 + 0.52)).toFixed(5)})`;
      fu(L.credit, s0 + 0.32);
      const push = 1 + 0.018 * E.inOutCubic(P(t, t0 + 0.55, cfg.t1));
      body.style.transform = `scale(${push.toFixed(5)})`;
      glint(L.phone, t, t0 + 1.10, 0.55, { w: 0.2, glow: 12 });
      glint(L.tag, t, t0 + 2.05, 0.6, { w: 0.18, glow: 10 });
    } };
  };
})();
