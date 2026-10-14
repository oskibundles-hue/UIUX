/*
 * lock.js -- consume tracks.json from track.py and draw a locked-on callout
 * (corner brackets + centre ticks + leader line + label) in an HTML/SVG
 * motion layer that is rendered frame-by-frame with window.renderAt(t).
 * No dependencies.  Deterministic: every call depends only on (track, t).
 *
 * ---------------------------------------------------------------- DATA
 *   tracks.json -> { name: { fps, f0, f1, t0, t1, frames:[{f,t,x,y,w,h,conf,...}] } }
 *   Boxes are full-res source px (1080x1920).  Frame f is on screen for
 *   [f/fps, (f+1)/fps).  To stay frame-accurate, render the overlay at the
 *   source fps and ask for t = f/fps (or use TrackLock.atFrame(track, f)).
 *
 * ---------------------------------------------------------------- API
 *   TrackLock.at(track, t)            -> {x,y,w,h,cx,cy,conf,inside}  (linear interp.)
 *   TrackLock.atFrame(track, f)       -> same, exact frame (no interpolation)
 *   TrackLock.follow(track, t, base, gain, stiff)
 *        spring-lagged label position: base + gain * (object displacement since
 *        shot start), critically damped (stiff = omega, rad/s).  Deterministic.
 *   TrackLock.clampSafe({x,y,w,h})    -> keeps a label rect inside the SE story safe
 *        zone (top 14 %, bottom 20 %, left 5 %, right 16 % excluded).
 *   const c = TrackLock.callout(parentEl, {lines:[{text,cls}...], corner:'tl'|'tr'|'bl'|'br'})
 *   c.update({box, label:{x,y}, acquire, leader, reveal, from, opacity})
 *        box      {x,y,w,h} object box (use TrackLock.at)
 *        from     optional {x,y,w,h}: brackets fly from here while acquire < 1
 *                 (use the previous shot's last box for a re-lock across a cut)
 *        acquire  0..1 bracket snap-in    leader 0..1 line draw-on
 *        reveal   0..1 label wipe-in      opacity 0..1 whole callout
 *   c.el  -> root element (remove to dispose)
 *
 * ---------------------------------------------------------------- LOOK
 *   Gold #FBD101 brackets and leader over a 45 % black under-stroke (reads on
 *   white paint), label on a 74 % black panel (its own scrim) with the gold/white
 *   78/22 stripe laid HORIZONTALLY on top.  Fonts are whatever the page loads as
 *   'Bebas' and 'Michroma'.
 */
(function (g) {
  const W = 1080, H = 1920;
  const SAFE = { x0: 0.05 * W, y0: 0.14 * H, x1: (1 - 0.16) * W, y1: (1 - 0.20) * H };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const ease = {
    outExpo: k => (k >= 1 ? 1 : 1 - Math.pow(2, -10 * k)),
    outCubic: k => 1 - Math.pow(1 - clamp(k, 0, 1), 3),
    inOutCubic: k => (k = clamp(k, 0, 1), k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  };

  function box(fr) {
    return { x: fr.x, y: fr.y, w: fr.w, h: fr.h, cx: fr.x + fr.w / 2, cy: fr.y + fr.h / 2, conf: fr.conf };
  }
  function atFrame(tr, f) {
    const i = clamp(Math.round(f) - tr.f0, 0, tr.frames.length - 1);
    const b = box(tr.frames[i]); b.inside = f >= tr.f0 && f <= tr.f1; return b;
  }
  function at(tr, t) {
    const fp = t * tr.fps - tr.f0, n = tr.frames.length;
    const i = clamp(Math.floor(fp), 0, n - 1), j = Math.min(i + 1, n - 1), k = clamp(fp - i, 0, 1);
    const a = tr.frames[i], b = tr.frames[j];
    const r = box({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), w: lerp(a.w, b.w, k), h: lerp(a.h, b.h, k),
                    conf: Math.min(a.conf, b.conf) });
    r.inside = fp >= -1e-6 && fp <= n - 1 + 1e-6; return r;
  }
  // critically-damped spring, integrated per source frame from the shot start
  function follow(tr, t, base, gain = { x: 0.2, y: 0.2 }, stiff = 9) {
    const dt = 1 / tr.fps, c0 = box(tr.frames[0]);
    let px = base.x, py = base.y, vx = 0, vy = 0;
    const steps = clamp(Math.round(t * tr.fps - tr.f0), 0, tr.frames.length - 1);
    for (let s = 0; s <= steps; s++) {
      const b = box(tr.frames[s]);
      const tx = base.x + gain.x * (b.cx - c0.cx), ty = base.y + gain.y * (b.cy - c0.cy);
      for (let k = 0; k < 4; k++) {                        // 4 sub-steps for stability
        const h = dt / 4, ax = stiff * stiff * (tx - px) - 2 * stiff * vx, ay = stiff * stiff * (ty - py) - 2 * stiff * vy;
        vx += ax * h; vy += ay * h; px += vx * h; py += vy * h;
      }
    }
    return { x: px, y: py };
  }
  function clampSafe(r) {
    return { x: clamp(r.x, SAFE.x0, SAFE.x1 - r.w), y: clamp(r.y, SAFE.y0, SAFE.y1 - r.h), w: r.w, h: r.h };
  }

  const NS = 'http://www.w3.org/2000/svg';
  function svgEl(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    parent && parent.appendChild(e); return e;
  }

  function callout(parent, opt) {
    const root = document.createElement('div');
    root.style.cssText = 'position:absolute;left:0;top:0;width:1080px;height:1920px;pointer-events:none';
    parent.appendChild(root);
    const svg = svgEl('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}` });
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    root.appendChild(svg);
    const under = svgEl('g', { stroke: 'rgba(0,0,0,.45)', 'stroke-width': 12, fill: 'none', 'stroke-linecap': 'square' }, svg);
    const over = svgEl('g', { stroke: '#FBD101', 'stroke-width': 6, fill: 'none', 'stroke-linecap': 'square' }, svg);
    const paths = { br: [svgEl('path', {}, under), svgEl('path', {}, over)],
                    tk: [svgEl('path', {}, under), svgEl('path', {}, over)],
                    ld: [svgEl('path', { 'stroke-width': 9 }, under), svgEl('path', { 'stroke-width': 4 }, over)] };
    const dotU = svgEl('circle', { r: 11, fill: 'rgba(0,0,0,.45)', stroke: 'none' }, under);
    const dot = svgEl('circle', { r: 7, fill: '#FBD101', stroke: 'none' }, over);
    // label
    const lab = document.createElement('div');
    lab.style.cssText = 'position:absolute;left:0;top:0;background:rgba(0,0,0,.74);padding:34px 36px 26px 36px;white-space:nowrap';
    const stripe = document.createElement('div');
    stripe.style.cssText = 'position:absolute;left:0;top:0;right:0;height:10px;background:linear-gradient(90deg,#FBD101 0 78%,#fff 78% 100%)';
    lab.appendChild(stripe);
    const lines = opt.lines.map(l => {
      const wrap = document.createElement('div'); wrap.style.cssText = 'overflow:hidden';
      const d = document.createElement('div'); d.className = l.cls || ''; d.textContent = l.text; d.style.cssText = l.style || '';
      wrap.appendChild(d); lab.appendChild(wrap); return d;
    });
    root.appendChild(lab);
    const corner = opt.corner || 'tl';

    function update(s) {
      const a = ease.outExpo(clamp(s.acquire ?? 1, 0, 1));
      const b0 = s.box;
      const pad = 0.12 * Math.min(b0.w, b0.h) + 10;
      let tgt = { x: b0.x - pad, y: b0.y - pad, w: b0.w + 2 * pad, h: b0.h + 2 * pad };
      let src = s.from ? { x: s.from.x - pad, y: s.from.y - pad, w: s.from.w + 2 * pad, h: s.from.h + 2 * pad }
                       : { x: tgt.x - tgt.w * 0.35, y: tgt.y - tgt.h * 0.35, w: tgt.w * 1.7, h: tgt.h * 1.7 };
      const r = { x: lerp(src.x, tgt.x, a), y: lerp(src.y, tgt.y, a), w: lerp(src.w, tgt.w, a), h: lerp(src.h, tgt.h, a) };
      const L = clamp(0.24 * Math.min(r.w, r.h), 26, 80);
      const x0 = r.x, y0 = r.y, x1 = r.x + r.w, y1 = r.y + r.h;
      const br = `M${x0},${y0 + L}V${y0}H${x0 + L} M${x1 - L},${y0}H${x1}V${y0 + L} M${x1},${y1 - L}V${y1}H${x1 - L} M${x0 + L},${y1}H${x0}V${y1 - L}`;
      const T = clamp(0.08 * Math.min(r.w, r.h), 10, 24), mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
      const tk = `M${mx},${y0}v${T} M${mx},${y1}v${-T} M${x0},${my}h${T} M${x1},${my}h${-T}`;
      paths.br.forEach(p => p.setAttribute('d', br));
      paths.tk.forEach(p => { p.setAttribute('d', tk); p.setAttribute('opacity', clamp(a * 1.4 - 0.4, 0, 1)); });
      svg.style.opacity = (s.opacity ?? 1) * (s.from ? 1 : clamp(a * 3, 0, 1));   // re-lock: visible from frame 0
      // label geometry (measured)
      const lw = lab.offsetWidth, lh = lab.offsetHeight;
      const lr = clampSafe({ x: s.label.x, y: s.label.y, w: lw, h: lh });
      lab.style.transform = `translate(${lr.x}px,${lr.y}px)`;
      const rv = ease.outCubic(s.reveal ?? 1);
      lab.style.clipPath = `inset(0 ${100 - 100 * rv}% 0 0)`;
      lab.style.opacity = s.opacity ?? 1;
      lines.forEach((d, i) => {
        const k = ease.outCubic(clamp(((s.reveal ?? 1) - 0.15 - 0.12 * i) / 0.5, 0, 1));
        d.style.transform = `translateY(${(1 - k) * 105}%)`;
      });
      // leader: bracket corner P -> 45deg run -> vertical into label edge A
      const P = { x: corner[1] === 'l' ? x0 : x1, y: corner[0] === 't' ? y0 : y1 };
      const above = lr.y + lh <= P.y;
      const Ay = above ? lr.y + lh : lr.y;
      const Ax = clamp(P.x, lr.x + 40, lr.x + lw - 40);
      const dx = Ax - P.x, dy = Ay - P.y, run = Math.min(Math.abs(dx), Math.abs(dy) * 0.8);
      const E = { x: P.x + Math.sign(dx) * run, y: P.y + Math.sign(dy) * run };
      const pts = [P, E, { x: Ax, y: Ay }];
      if (Math.abs(dx) > run + 0.5) pts.splice(2, 0, { x: Ax, y: E.y });   // extra horizontal leg
      let len = 0; for (let i = 1; i < pts.length; i++) len += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
      const d = 'M' + pts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join('L');
      const ld = ease.inOutCubic(s.leader ?? 1);
      paths.ld.forEach(p => { p.setAttribute('d', d); p.setAttribute('stroke-dasharray', `${len * ld} ${len + 10}`); });
      [dot, dotU].forEach(c => { c.setAttribute('cx', P.x); c.setAttribute('cy', P.y); c.setAttribute('opacity', ld > 0 ? 1 : 0); });
    }
    return { el: root, update };
  }

  g.TrackLock = { at, atFrame, follow, clampSafe, callout, ease, SAFE };
})(window);
