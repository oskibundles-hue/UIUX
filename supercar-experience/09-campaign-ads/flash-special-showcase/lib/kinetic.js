/* kinetic.js — deterministic kinetic-typography primitives for SE motion layers.
 *
 * Contract: every function here is a PURE function of time `t` (seconds). A page builds its DOM once,
 * then defines window.renderAt(t) which calls these primitives; kcapture.js calls renderAt at K
 * sub-frame times per output frame and averages the screenshots (true motion blur). Nothing reads the
 * clock, nothing uses CSS transitions/animations, randomness is seeded — so any t can be rendered in
 * any order and sub-frame samples are exact.
 *
 * Build-time helpers (call once, after fonts load — see KT.ready()):
 *   KT.split(el, {perspective})      -> glyph <span>s (inline-block, 3D-ready), measured offsets
 *   KT.slot(el, text, {seed})        -> slot-reel price; digits become reels, other chars stay static
 *   KT.stripe(el)                    -> turns a div into the SE 78/22 gold/white accent stripe
 *
 * Per-frame animators (call inside renderAt(t)):
 *   KT.flip(glyphs,t,{start,stagger,dur,from,axis,origin,z,ease,dy})   per-glyph 3D perspective flip-in
 *   KT.rise(glyphs,t,{start,stagger,dur,dy,rot,ease})                  per-glyph masked rise (use in a KT.mask wrapper)
 *   KT.track(glyphs,t,{start,stagger,dur,spread})                      tracking collapse + per-glyph fade
 *   KT.wipe(el,t,{start,dur,dir,edge,ease})                            masked wipe (clip-path) + optional light edge el
 *   KT.glint(glyphs,t,{start,dur,base,hot,width,angle})                light sweep painted INTO the letters
 *   KT.slotAt(slot,t,{lands,v,ease})                                   spins reels, lands on the true digits
 *   KT.drawStripe(el,t,{start,dur})                                    scaleX draw-on
 *   KT.whip(el,t,{start,dur,dx,dy})                                    fast exit; pair with a high-K capture plan
 *   KT.env(t,a,b,rise,fall) / KT.p / KT.ease.*                         timing helpers
 *
 * Capture plan: a page may set window.KT_PLAN = {k:10, shutter:180, spans:[{a,b,k,shutter}]} so the
 * capture step spends more samples only where motion is fast (whips, reels). Frames whose DOM state is
 * identical across the shutter interval are detected by KT.signature() and captured once.
 */
(function () {
  const KT = {};
  const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const p = (t, a, b) => (b === a ? (t >= b ? 1 : 0) : cl((t - a) / (b - a)));
  KT.cl = cl; KT.p = p;
  KT.lerp = (a, b, x) => a + (b - a) * x;

  // ---- easing ------------------------------------------------------------------------------------
  const E = {
    lin: x => x,
    outCubic: x => 1 - Math.pow(1 - x, 3),
    inCubic: x => x * x * x,
    inOutCubic: x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    outQuint: x => 1 - Math.pow(1 - x, 5),
    outExpo: x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
    inExpo: x => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10)),
    inOutExpo: x => (x <= 0 ? 0 : x >= 1 ? 1 : x < .5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2),
    outBack: (x, s = 1.7) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2),
    // damped spring 0->1 (overshoot), settles by x=1
    spring: (x, w = 11, z = .42) => { if (x >= 1) return 1; const T = x * 1.0; const wd = w * Math.sqrt(1 - z * z);
      return 1 - Math.exp(-z * w * T) * (Math.cos(wd * T) + (z * w / wd) * Math.sin(wd * T)); },
  };
  KT.ease = E;
  // in/out envelope: 0 before a, rises over `rise`, holds, falls over `fall` ending at b
  KT.env = (t, a, b, rise = .25, fall = .2) => Math.min(E.outExpo(p(t, a, a + rise)), 1 - E.inExpo(p(t, b - fall, b)));

  // ---- seeded RNG --------------------------------------------------------------------------------
  KT.rng = seed => { let s = seed % 2147483647 || 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; };

  // ---- build: split text into glyph spans ---------------------------------------------------------
  // Each glyph is inline-block so it can take 3D transforms. Spaces keep their width.
  KT.split = function (el, o = {}) {
    const text = o.text != null ? o.text : el.textContent;
    el.textContent = '';
    el.style.whiteSpace = 'pre';
    if (o.perspective !== 0) { el.style.perspective = (o.perspective || 900) + 'px'; el.style.transformStyle = 'preserve-3d'; }
    const g = [];
    for (const ch of text) {
      const s = document.createElement('span');
      s.textContent = ch;
      s.style.display = 'inline-block';
      s.style.backfaceVisibility = 'hidden';
      s.style.willChange = 'transform,opacity';
      s.dataset.ch = ch;
      el.appendChild(s);
      if (ch !== ' ') g.push(s);
    }
    g.host = el;
    return g;
  };
  // Measure glyph offsets relative to host (call after fonts are ready, with transforms cleared)
  KT.measure = function (glyphs) {
    const host = glyphs.host; const hr = host.getBoundingClientRect();
    glyphs.W = hr.width; glyphs.H = hr.height;
    glyphs.forEach(s => { const r = s.getBoundingClientRect(); s._ox = r.left - hr.left; s._oy = r.top - hr.top; s._w = r.width; s._h = r.height; });
    return glyphs;
  };

  // ---- per-glyph 3D flip-in -----------------------------------------------------------------------
  // from: start angle (deg); axis 'X' flips like a board swinging up off the baseline, 'Y' like a door.
  KT.flip = function (glyphs, t, o = {}) {
    const st = o.start || 0, sg = o.stagger ?? .04, d = o.dur ?? .45, from = o.from ?? -96, ax = o.axis || 'X';
    const ease = o.ease || (x => E.outBack(x, 1.25)), z = o.z ?? 0, dy = o.dy ?? 0, order = o.order || 'lr';
    const n = glyphs.length;
    glyphs.forEach((s, i) => {
      const k = order === 'rl' ? n - 1 - i : order === 'center' ? Math.abs(i - (n - 1) / 2) : i;
      const q = p(t, st + k * sg, st + k * sg + d), e = ease(q);
      s.style.transformOrigin = o.origin || '50% 88%';
      s.style.opacity = q <= 0 ? 0 : Math.min(1, q * 3.5);
      s.style.transform = `translate3d(0,${(1 - e) * dy}px,${(1 - e) * z}px) rotate${ax}(${(1 - e) * from}deg)`;
    });
  };

  // ---- per-glyph rise (put the host inside an overflow:hidden / KT.mask wrapper for a masked rise) --
  KT.rise = function (glyphs, t, o = {}) {
    const st = o.start || 0, sg = o.stagger ?? .035, d = o.dur ?? .4, dy = o.dy ?? 1.1, rot = o.rot ?? 0;
    const ease = o.ease || E.outExpo;
    glyphs.forEach((s, i) => {
      const q = p(t, st + i * sg, st + i * sg + d), e = ease(q);
      const h = s._h || 100;
      s.style.opacity = q <= 0 ? 0 : 1;
      s.style.transform = `translateY(${(1 - e) * dy * h}px) rotate(${(1 - e) * rot}deg)`;
    });
  };

  // ---- tracking collapse: glyphs converge from a wide spread onto their set positions --------------
  KT.track = function (glyphs, t, o = {}) {
    const st = o.start || 0, d = o.dur ?? .6, spread = o.spread ?? 2.2, sg = o.stagger ?? .012;
    const n = glyphs.length, mid = (n - 1) / 2, ease = o.ease || E.outExpo;
    glyphs.forEach((s, i) => {
      const q = p(t, st + Math.abs(i - mid) * sg, st + Math.abs(i - mid) * sg + d), e = ease(q);
      const cx = (s._ox || 0) + (s._w || 0) / 2, hx = (glyphs.W || 0) / 2;
      s.style.opacity = cl(q * 2.2);
      s.style.transform = `translateX(${(1 - e) * (cx - hx) * (spread - 1)}px)`;
    });
  };

  // ---- masked wipe: clip-path reveal with optional light edge riding the boundary ----------------
  // dir: 'right' (reveal L->R), 'left', 'up' (reveal bottom->top), 'down'. edge: element positioned by us.
  KT.wipe = function (el, t, o = {}) {
    const q = (o.ease || E.inOutExpo)(p(t, o.start || 0, (o.start || 0) + (o.dur ?? .5)));
    const r = (1 - q) * 100, pad = o.pad ?? 12; // pad lets descenders/glow escape the clip box
    const ins = { right: `-${pad}% ${r}% -${pad}% -${pad}%`, left: `-${pad}% -${pad}% -${pad}% ${r}%`,
      up: `${r}% -${pad}% -${pad}% -${pad}%`, down: `-${pad}% -${pad}% ${r}% -${pad}%` }[o.dir || 'right'];
    el.style.clipPath = q >= 1 ? 'none' : `inset(${ins})`;
    el.style.opacity = q <= 0 ? 0 : 1;
    if (o.edge) {
      const w = el.offsetWidth, h = el.offsetHeight, x = el.offsetLeft, y = el.offsetTop;
      const vis = q > 0 && q < 1 ? Math.sin(Math.PI * q) : 0;
      o.edge.style.opacity = vis;
      if (o.dir === 'up' || o.dir === 'down') o.edge.style.transform = `translate(${x}px,${y + h * (o.dir === 'up' ? 1 - q : q)}px)`;
      else o.edge.style.transform = `translate(${x + w * (o.dir === 'left' ? 1 - q : q)}px,${y}px)`;
    }
    return q;
  };

  // ---- glint: a hot band painted into the glyphs (background-clip:text), continuous across glyphs --
  // Uses each glyph's measured offset so one band crosses the whole word. base = letter colour.
  KT.glint = function (glyphs, t, o = {}) {
    const st = o.start || 0, d = o.dur ?? .6, base = o.base || '#FBD101', hot = o.hot || '#FFFFFF';
    const bw = o.width ?? 90, ang = o.angle ?? 104, W = glyphs.W || 800, H = glyphs.H || 300;
    const q = p(t, st, st + d); const x = -bw * 2 + (W + bw * 4) * (o.ease || E.inOutCubic)(q);
    const on = q > 0 && q < 1;
    const warm = o.warm || base;
    glyphs.forEach(s => {
      if (!on) { s.style.backgroundImage = 'none'; s.style.webkitTextFillColor = ''; return; }
      const gx = x - (s._ox || 0);
      s.style.backgroundImage = `linear-gradient(${ang}deg, ${base} 0px, ${base} ${gx - bw}px, ${warm} ${gx - bw * .45}px, ${hot} ${gx}px, ${warm} ${gx + bw * .45}px, ${base} ${gx + bw}px, ${base} ${W + 400}px)`;
      s.style.backgroundSize = `${W + 400}px ${H}px`;
      s.style.backgroundPosition = `0 ${-(s._oy || 0)}px`;
      s.style.webkitBackgroundClip = 'text'; s.style.backgroundClip = 'text';
      s.style.webkitTextFillColor = 'transparent';
    });
    return on ? Math.sin(Math.PI * q) : 0; // strength, e.g. to drive a bloom
  };

  // ---- stripe ------------------------------------------------------------------------------------
  KT.stripe = el => { el.style.background = 'linear-gradient(90deg,#FBD101 0 78%,#fff 78% 100%)'; el.style.transformOrigin = 'left center'; return el; };
  KT.drawStripe = (el, t, o = {}) => { const q = (o.ease || E.outExpo)(p(t, o.start || 0, (o.start || 0) + (o.dur ?? .45))); el.style.transform = `scaleX(${q})`; el.style.opacity = q > 0 ? 1 : 0; return q; };

  // ---- whip exit ---------------------------------------------------------------------------------
  KT.whip = (el, t, o = {}) => { const q = (o.ease || E.inExpo)(p(t, o.start || 0, (o.start || 0) + (o.dur ?? .25)));
    el.style.transform = `translate(${q * (o.dx ?? -1400)}px,${q * (o.dy ?? 0)}px)`; el.style.opacity = q >= 1 ? 0 : 1; return q; };

  // ---- slot-reel price ---------------------------------------------------------------------------
  // Every digit becomes a reel: a strip whose row 0 is the TRUE digit, rows 1..10 a seeded cycle of
  // other digits, rows 11..12 repeat rows 1..2 so the strip wraps seamlessly. Nothing sits above row 0,
  // so the landing overshoot reveals blank space, never a wrong digit. Reels only ever move fast
  // (>= ~26 rows/s) while a non-true digit is in the window, so every intermediate is a blur.
  KT.slot = function (el, text, o = {}) {
    const rnd = KT.rng(o.seed || 11);
    el.textContent = ''; el.style.whiteSpace = 'pre'; el.style.display = 'inline-flex'; el.style.alignItems = 'flex-start';
    const reels = [], statics = [], all = [];
    const probe = document.createElement('span'); probe.style.cssText = 'position:absolute;visibility:hidden;white-space:pre';
    el.appendChild(probe);
    for (const ch of text) {
      probe.textContent = ch; const w = probe.getBoundingClientRect().width;
      if (/[0-9]/.test(ch)) {
        const win = document.createElement('span');
        win.style.cssText = `display:inline-block;position:relative;width:${w}px;height:1em;overflow:hidden;` +
          `-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 16%,#000 84%,transparent 100%);mask-image:linear-gradient(180deg,transparent 0,#000 16%,#000 84%,transparent 100%)`;
        win.style.isolation = 'isolate';
        const cyc = []; let prev = ch;
        for (let i = 0; i < 10; i++) { let d; do { d = String(Math.floor(rnd() * 10)); } while (d === prev || d === ch && i === 0); cyc.push(d); prev = d; }
        const rows = [ch, ...cyc, cyc[0], cyc[1]];
        // G identical strips: strip 0 is the "real" one; the others are in-DOM motion-blur ghosts that are
        // spread across the capture sub-interval and summed with plus-lighter (exact premultiplied average).
        const strips = [];
        for (let gI = 0; gI < (o.ghosts ?? 16); gI++) {
          const strip = document.createElement('span');
          strip.style.cssText = 'position:absolute;left:0;top:0;width:100%;display:flex;flex-direction:column;align-items:center;will-change:transform,opacity;mix-blend-mode:plus-lighter';
          rows.forEach((d, i) => { const r = document.createElement('span'); r.textContent = d; r.style.cssText = 'display:block;height:1em;line-height:1em'; if (i === 0 && gI === 0) r.dataset.true = '1'; strip.appendChild(r); });
          win.appendChild(strip); strips.push(strip);
        }
        el.appendChild(win);
        const reel = { win, strip: strips[0], strips, ch, top: strips[0].firstChild }; reels.push(reel); all.push(win);
      } else {
        const s = document.createElement('span'); s.textContent = ch; s.style.cssText = `display:inline-block;height:1em;line-height:1em;width:${w}px;text-align:center`;
        el.appendChild(s); statics.push(s); all.push(s);
      }
    }
    probe.remove();
    return { el, reels, statics, all };
  };
  // Reel position in rows (0 = true digit centred). Phases: cruise at v, brake to v2 over the last
  // wrong rows, then an underdamped spring from P0 (overshoot ~-0.09 rows into the blank area above).
  KT.reelPos = function (t, tl, o = {}) {
    const v = o.v ?? 60, v2 = o.v2 ?? 35, Pd = o.Pd ?? 2.5, P0 = o.P0 ?? .8, w = o.w ?? 45, z = o.z ?? .7;
    const a = (v * v - v2 * v2) / (2 * (Pd - P0)), TB = (v - v2) / a; // brake phase duration
    if (t >= tl) { const T = t - tl, wd = w * Math.sqrt(1 - z * z), B = (-v2 + z * w * P0) / wd;
      return Math.exp(-z * w * T) * (P0 * Math.cos(wd * T) + B * Math.sin(wd * T)); }
    const tb = tl - TB;
    if (t >= tb) { const T = t - tb; return Pd - (v * T - a * T * T / 2); }
    return Pd + v * (tb - t);
  };
  // lands: absolute landing time per reel. Returns per-reel {pos, landed, justLanded (0..1 pulse)}.
  KT.slotAt = function (slot, t, o = {}) {
    const H = slot.reels.length ? slot.reels[0].win.offsetHeight : 100;
    // Sub-interval each capture sample stands for (set by kcapture.js as window.__ktSub; 0 in previews).
    // Ghost strips spread across it turn K capture samples into K*G samples for the reels only.
    const sub = window.__ktSub || 0;
    const wrap = q => (q >= 1 ? 1 + ((q - 1) % 10) : q); // wrap on the repeated cycle
    return slot.reels.map((r, i) => {
      const tl = o.lands[i]; const pos = wrap(KT.reelPos(t, tl, o)); const G = r.strips.length;
      const ps = r.strips.map((_, j) => wrap(KT.reelPos(t + ((j + .5) / G - .5) * sub, tl, o)));
      const moving = sub > 0 && Math.max(...ps.map(x => Math.abs(x - ps[0]))) > 1e-3;
      r.strips.forEach((s, j) => {
        if (!moving) { s.style.opacity = j === 0 ? 1 : 0; s.style.transform = `translateY(${-pos * H}px)`; }
        else { s.style.opacity = 1 / G; s.style.transform = `translateY(${-ps[j] * H}px)`; }
      });
      const hit = t >= tl ? Math.exp(-(t - tl - .03) * 9) * (t - tl < .03 ? (t - tl) / .03 : 1) : 0;
      return { pos, landed: t >= tl + .25, hit };
    });
  };

  // ---- fit: shrink an element's font-size until it is no wider than maxW (build time) ------------
  KT.fit = function (el, maxW) {
    let fs = parseFloat(getComputedStyle(el).fontSize);
    el.style.whiteSpace = 'pre'; el.style.display = 'inline-block';
    while (el.getBoundingClientRect().width > maxW && fs > 10) { fs -= 2; el.style.fontSize = fs + 'px'; }
    return fs;
  };

  // ---- capture support ---------------------------------------------------------------------------
  // Cheap DOM-state hash: if identical at shutter open/mid/close the frame is static => 1 sample.
  KT.signature = function () {
    let s = '';
    const els = document.body.getElementsByTagName('*');
    for (let i = 0; i < els.length; i++) { const c = els[i].style.cssText; if (c) s += c + '|'; }
    let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
    return h + ':' + s.length;
  };
  KT.ready = async () => { await document.fonts.ready; await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); };

  window.KT = KT;
})();
