/* one-way-ticket part1 copy (changes marked 'part1 copy'): the glass is the plate's job here (the layer is captured
 * transparent, so a CSS backdrop-filter has nothing to blur): the panel is the glass-orange tint rgba(8,8,10,.58) with
 * its 1px inset edge, and build.py blurs (22 px) and saturates (1.3) the plate inside the panel's visible rect
 * (glass_rects in build.py repeats panelAt's unroll / retract maths). The strip can retract (p.exit).
 * drive_strip.js -- STRIP, the decluttered driving HUD: one slim plate across the top in place of the A2 banner, D1
 * clock, DRV drive plate and PRG bar. Omarie, 6 Oct: "i feel like its too clutteres can we fix that plz".
 *   [SE mark] [10:00:08 + place] | [HEADING S 180, or ROUTE SEATTLE → VEGAS with p.route_text] | [SIDE G 0.10 G + bead]   with a progress scrubber along the bottom
 * p: {x, y, w, h, start, place, heading, hdgKeys, range, route: {waypoints, steps}} -- route adds one slim line under
 * the strip (the stop you're on in the accent, the next one in white). Side G from window.LAT, as DRV.
 * Colours follow window.THEME; the plate is a kit panel, so a glass theme frosts it. */
SEK.driveStrip = function (cfg) {
  const H = SEK.helpers, TH = window.THEME || {}, ACC = TH.accent || '#FF4F16', GLOW = TH.glow || '255,79,22';
  const E = KT.ease, P = KT.p, cl = KT.cl;
  const p = Object.assign({ x: 54, y: 292, w: 853, h: 140, start: '10:00:00', place: '', heading: 0, hdgKeys: null,
    range: [0, cfg.t1], route: null }, cfg.p);
  const root = H.el('div', 'a', null);
  const pn = H.panel(root, p.x, p.y, p.w, p.h, { stripe: 5, shadow: 0.24 });
  // part1 copy: the glass-orange theme's tint and edge (themes/glass-orange.json), drawn by the layer
  pn.bg.style.background = 'rgba(8,8,10,.58)';
  H.el('div', 'a', pn.clip, `width:${p.w}px;height:${p.h}px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.16)`);
  const IN = pn.inner, dim = 'rgba(255,255,255,.66)';
  // SE mark
  const mk = H.el('img', 'a', IN, `left:24px;top:${(p.h - 36) / 2}px;width:54px`); mk.src = H.maskUrl('sce-icon-mark-only--white.png');
  // clock + place
  const cx = 100;
  const hm = H.line(IN, 'Bebas', 78, '10:00', cx, 20, '#fff', { split: false });
  const ss = H.line(IN, 'Bebas', 46, ':00', cx + H.ink('Bebas', 78, '10:00').adv + 4, 20 + hm.capH - H.ink('Bebas', 46, '0').aA, ACC, { split: false });
  const pl = H.line(IN, 'Michroma', 15, p.place, cx + 1, 20 + hm.capH + 18, dim, { ls: 0.12 });
  // heading and side G columns, divided by hairlines
  const c2 = Math.max(cx + H.ink('Bebas', 78, '10:00').adv + H.ink('Bebas', 46, ':00').adv + 34, cx + H.ink('Michroma', 15, p.place, 0.12).w + 34);
  // part1 copy: p.hide_g drops the SIDE G column (7 Oct: an unsourced accelerometer figure); ROUTE then takes the whole right side
  const c3 = p.hide_g ? p.w - 24 + 16 : c2 + (p.w - c2) * 0.48;
  (p.hide_g ? [c2] : [c2, c3]).forEach(x => H.el('div', 'a', IN, `left:${x - 16}px;top:22px;width:1px;height:${p.h - 44}px;background:rgba(255,255,255,.18)`));
  // part1 copy: p.route_text ('SEATTLE → VEGAS') replaces the heading column with a static ROUTE label and the text,
  // fitted to the column (the arrow is drawn: the display face has no arrow glyph). No heading is computed then.
  let hv;
  if (p.route_text) {
    H.line(IN, 'Michroma', 14, p.route_label || 'ROUTE', c2, 24, dim, { ls: 0.16, split: false });
    const [ra, rb] = String(p.route_text).split(/\s*(?:→|->|>)\s*/), colW = c3 - c2 - 20, gap = 12, arW = 0.5;   // arrow length = 0.5 em
    const rs = Math.min(62, 62 * (colW - 2 * gap) / (H.ink('Bebas', 62, ra).adv + H.ink('Bebas', 62, rb).adv + 62 * arW));
    const CAP62 = H.ink('Bebas', 62, 'H').aA, rcap = H.ink('Bebas', rs, 'H').aA, aw = rs * arW, ay = 50 + rcap / 2;
    hv = H.line(IN, 'Bebas', rs, ra, c2, 50 + (CAP62 - rcap) / 2, '#fff', { split: false });
    const ax = c2 + H.ink('Bebas', rs, ra).adv + gap;
    H.el('div', 'a', IN, `left:${ax}px;top:${50 + (CAP62) / 2 - 1.25}px;width:${aw}px;height:2.5px;background:${ACC}`);
    H.el('div', 'a', IN, `left:${ax + aw - 9}px;top:${50 + (CAP62) / 2 - 6}px;width:12px;height:12px;border-top:2.5px solid ${ACC};border-right:2.5px solid ${ACC};transform:rotate(45deg) scale(.9);transform-origin:50% 50%`);
    H.line(IN, 'Bebas', rs, rb, ax + aw + gap, 50 + (CAP62 - rcap) / 2, '#fff', { split: false });
  } else {
    H.line(IN, 'Michroma', 14, 'HEADING', c2, 24, dim, { ls: 0.16, split: false });
    hv = H.line(IN, 'Bebas', 62, 'S 180', c2, 50, '#fff', { split: false });
  }
  let gv = null, vx = 0, vw = 0, vy = 0, bead = null;
  if (!p.hide_g) {
  H.line(IN, 'Michroma', 14, 'SIDE G', c3, 24, dim, { ls: 0.16, split: false });
  gv = H.line(IN, 'Bebas', 62, '0.00 G', c3, 50, '#fff', { split: false });
  vx = c3 + H.ink('Bebas', 62, '0.00 G').adv + 16; vw = Math.max(40, p.w - 24 - vx); vy = 50 + gv.capH / 2 - 9;
  H.el('div', 'a', IN, `left:${vx}px;top:${vy}px;width:${vw}px;height:18px;border:1.5px solid rgba(255,255,255,.7);border-radius:9px`);
  // part1 copy: p.g_mag = magnitude only (the side-G sign was never calibrated against a turn, so nothing may imply left or
  // right): no centre tick, and the bar fills from the left end by |g| instead of a bead swinging about the centre
  if (!p.g_mag) H.el('div', 'a', IN, `left:${vx + vw / 2 - 1}px;top:${vy}px;width:2px;height:18px;background:rgba(255,255,255,.7)`);
  bead = p.g_mag
    ? H.el('div', 'a', IN, `left:${vx + 3}px;top:${vy + 3}px;width:${vw - 6}px;height:12px;border-radius:6px;background:${ACC};transform-origin:0 50%;box-shadow:0 0 10px rgba(${GLOW},.6)`)
    : H.el('div', 'a', IN, `left:${vx + vw / 2 - 6}px;top:${vy + 3}px;width:12px;height:12px;border-radius:50%;background:${ACC};box-shadow:0 0 10px rgba(${GLOW},.7)`);
  }
  // scrubber along the bottom of the plate
  const sL = 24, sW = p.w - 48, sT = p.h - 10;
  H.el('div', 'a', IN, `left:${sL}px;top:${sT}px;width:${sW}px;height:3px;border-radius:2px;background:rgba(255,255,255,.2)`);
  const fill = H.el('div', 'a', IN, `left:${sL}px;top:${sT}px;width:${sW}px;height:3px;border-radius:2px;background:${ACC};transform-origin:0 50%;box-shadow:0 0 8px rgba(${GLOW},.55)`);
  // route: one slim line under the strip
  let rt = null;
  if (p.route && p.route.waypoints && p.route.waypoints.length) {
    const rw = p.w, rh = 60, ry = p.y + p.h + 12, cap = H.ink('Bebas', 32, 'H').aA;
    const rp = H.panel(root, p.x, ry, rw, rh, { stripe: 0 });
    const dot = H.el('div', 'a', rp.inner, `left:26px;top:${rh / 2 - 6}px;width:12px;height:12px;border-radius:50%;background:${ACC};box-shadow:0 0 10px rgba(${GLOW},.8)`);
    const cur = H.line(rp.inner, 'Bebas', 32, 'HH', 52, (rh - cap) / 2, '#fff', { split: false });
    const lab = H.line(rp.inner, 'Michroma', 13, 'NEXT', 52, rh / 2 - 7, ACC, { ls: 0.18, split: false });
    const nxt = H.line(rp.inner, 'Bebas', 32, 'HH', 52, (rh - cap) / 2, 'rgba(255,255,255,.62)', { split: false });
    rt = { rp, dot, cur, lab, nxt };
  }
  const parseT = s => { const [a, b, c] = s.split(':').map(Number); return a * 3600 + b * 60 + (c || 0); };
  const s0 = parseT(p.start), p2 = n => String(n).padStart(2, '0');
  const card = d => ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.round((((d % 360) + 360) % 360) / 45) % 8];
  const LAT = (window.LAYERDATA || {})['lat_' + cfg.code] || window.LAT || [];   // part1 copy: side G per strip, from build.py
  return { code: cfg.code, render(t) {
    const on = t >= cfg.t0 && t < cfg.t1; H.show(root, on); if (!on) return;
    H.panelAt(pn, t, cfg.t0, p.exit ?? null);      // part1 copy: optional retract
    // clock: the camera's own time, from the clip position
    const sec = Math.floor(s0 + (CTX.clip(t) ?? t));       // part1 copy: the build's camera clock
    hm.t.textContent = p2(Math.floor(sec / 3600) % 24) + ':' + p2(Math.floor(sec / 60) % 60);
    ss.t.textContent = ':' + p2(sec % 60);
    // heading (estimate) and side G (camera sensor)
    let base = p.heading;
    if (p.hdgKeys) { const K = p.hdgKeys; base = K[0][1]; for (let j = 1; j < K.length; j++) { if (t >= K[j - 1][0]) { const u = E.inOutCubic(P(t, K[j - 1][0], K[j][0])); base = K[j - 1][1] + (K[j][1] - K[j - 1][1]) * u; } } }
    const hd = base + 1.6 * Math.sin(t * 0.55) + 0.7 * Math.sin(t * 1.7), hr = Math.round(((hd % 360) + 360) % 360) % 360;
    if (!p.route_text) hv.t.textContent = card(hr) + ' ' + String(hr).padStart(3, '0');
    const g = LAT.length ? LAT[Math.max(0, Math.min(LAT.length - 1, Math.round(t * 30)))] : 0;
    const qb = E.outCubic(P(t, cfg.t0 + 0.3, cfg.t0 + 0.9));
    if (gv) gv.t.textContent = Math.abs(g).toFixed(2) + ' G';
    if (!bead) { /* hide_g: no side-G readout */ }
    else if (p.g_mag) bead.style.transform = `scaleX(${(Math.max(0.04, Math.min(1, Math.abs(g) / 0.5)) * qb).toFixed(4)})`;
    else bead.style.transform = `translateX(${((vw / 2 - 9) * Math.max(-1, Math.min(1, g / 0.5)) * qb).toFixed(2)}px)`;
    fill.style.transform = `scaleX(${(P(t, p.range[0], p.range[1]) * qb).toFixed(5)})`;
    if (rt) {
      H.panelAt(rt.rp, t, cfg.t0 + 0.25, null);
      let k = 0; for (const st of p.route.steps || []) if (t >= st.t) k = st.k;
      const W = p.route.waypoints, c = W[Math.min(k, W.length - 1)], n = W[k + 1];
      rt.cur.t.textContent = c; rt.nxt.t.textContent = n || '';
      const xl = H.ink('Bebas', 32, c).adv + 26, xn = xl + H.ink('Michroma', 13, 'NEXT', 0.18).adv + 14;
      rt.lab.w.style.transform = `translateX(${xl}px)`; rt.nxt.w.style.transform = `translateX(${xn}px)`;
      rt.lab.w.style.opacity = rt.nxt.w.style.opacity = n ? 1 : 0;
    }
  } };
};

/* part1 v2 (Omarie, 6 Oct: "i dont like the sidebar on both episodes ... made a new progress bar"): SEK.seStrip, the ONE
 * progress element of the episode. The A2 side banner and its rail are gone; this dark-glass strip runs from just after
 * the hook to the end card. Compact (hc px tall) it carries the SE mark, the camera clock (from p.clockFrom on; the
 * hook is a flash-forward of later shots, so no clock there) and the series label; over the two HUD-1 cabin shots
 * (p.expand windows) it grows to the full HUD-1 strip (hx px: clock + place | ROUTE). The scrubber along its bottom
 * edge fills over p.progress the whole way. No speeds, prices or distances.
 * p: {x, y, w, hc, hx, progress: [t0, t1], label, clockFrom, exit, route_text,
 *     expand: [{a, b, places: [[t, 'PLACE'], ...]}]}
 * Geometry is mirrored in lib/plate.py glass_rects (stripH / vis): keep the two in step. */
SEK.stripH = function (p, t) {
  const E = KT.ease, P = KT.p;
  let ex = 0;
  for (const w of p.expand || []) ex = Math.max(ex, E.inOutCubic(P(t, w.a, w.a + 0.4)) * (1 - E.inOutCubic(P(t, w.b - 0.4, w.b))));
  return { ex, h: p.hc + (p.hx - p.hc) * ex };
};
SEK.seStrip = function (cfg) {
  const H = SEK.helpers, TH = window.THEME || {}, ACC = TH.accent || '#FF4F16', GLOW = TH.glow || '255,79,22';
  const E = KT.ease, P = KT.p;
  const p = Object.assign({ x: 54, y: 292, w: 853, hc: 84, hx: 140, progress: [cfg.t0, cfg.t1], label: '', clockFrom: cfg.t0,
    exit: null, route_text: '', expand: [] }, cfg.p);
  const root = H.el('div', 'a', null);
  const pn = H.panel(root, p.x, p.y, p.w, p.hx, { stripe: 5, shadow: 0.24 });
  pn.bg.style.background = 'rgba(8,8,10,.68)';                        // the glass-orange tint; the frost is in the plate (7 Oct: .58 -> .68, dark over foliage and sky)
  // 7 Oct (nq-check): the cap stripe is one solid SE orange the full panel width, not the house 78/22 orange/white, which
  // read as a second, frozen progress bar; the scrubber along the bottom is the only progress element
  pn.stripe.style.background = ACC;
  const edgeLine = H.el('div', 'a', pn.clip, `width:${p.w}px;height:${p.hc}px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.16)`);
  const IN = pn.inner, dim = 'rgba(255,255,255,.66)';
  const mk = H.el('img', 'a', IN, `left:24px;top:0;width:54px`); mk.src = H.maskUrl('sce-icon-mark-only--white.png');
  const MKH = 54 * 215 / 338;
  const cx = 100;
  // compact: HH:MM :SS | LABEL
  const gC = H.el('div', 'a', IN, `width:${p.w}px;height:${p.hx}px`);
  const CS = 52, cyC = (p.hc - 4 - H.ink('Bebas', CS, 'H').aA) / 2;
  const hmC = H.line(gC, 'Bebas', CS, '10:00', cx, cyC, '#fff', { split: false });
  const ssC = H.line(gC, 'Bebas', 32, ':00', cx + H.ink('Bebas', CS, '10:00').adv + 3, cyC + hmC.capH - H.ink('Bebas', 32, '0').aA, ACC, { split: false });
  const c2C = cx + H.ink('Bebas', CS, '10:00').adv + H.ink('Bebas', 32, ':00').adv + 30;
  const hairC = H.el('div', 'a', gC, `left:${c2C - 15}px;top:${(p.hc - 4) / 2 - 18}px;width:1px;height:36px;background:rgba(255,255,255,.18)`);
  const LS_ = 14, lyC = (p.hc - 4 - H.ink('Michroma', LS_, 'H', 0.16).aA) / 2;
  const lab = H.line(gC, 'Michroma', LS_, p.label, c2C, lyC, dim, { ls: 0.16, split: false, dots: ACC });
  // expanded: the HUD-1 strip (clock + place | ROUTE)
  const gX = H.el('div', 'a', IN, `width:${p.w}px;height:${p.hx}px`);
  const hmX = H.line(gX, 'Bebas', 78, '10:00', cx, 20, '#fff', { split: false });
  const ssX = H.line(gX, 'Bebas', 46, ':00', cx + H.ink('Bebas', 78, '10:00').adv + 4, 20 + hmX.capH - H.ink('Bebas', 46, '0').aA, ACC, { split: false });
  const places = [...new Set((p.expand || []).flatMap(w => (w.places || []).map(q => q[1])))];
  const plEls = {};
  for (const s of places) plEls[s] = H.line(gX, 'Michroma', 15, s, cx + 1, 20 + hmX.capH + 18, dim, { ls: 0.12 });
  const wPl = Math.max(0, ...places.map(s => H.ink('Michroma', 15, s, 0.12).w));
  const c2 = Math.max(cx + H.ink('Bebas', 78, '10:00').adv + H.ink('Bebas', 46, ':00').adv + 34, cx + wPl + 34), c3 = p.w - 8;
  H.el('div', 'a', gX, `left:${c2 - 16}px;top:22px;width:1px;height:${p.hx - 44}px;background:rgba(255,255,255,.18)`);
  if (p.route_text) {
    H.line(gX, 'Michroma', 14, 'ROUTE', c2, 24, dim, { ls: 0.16, split: false });
    const [ra, rb] = String(p.route_text).split(/\s*(?:→|->|>)\s*/), colW = c3 - c2 - 20, gap = 12, arW = 0.5;
    const rs = Math.min(62, 62 * (colW - 2 * gap) / (H.ink('Bebas', 62, ra).adv + H.ink('Bebas', 62, rb).adv + 62 * arW));
    const CAP62 = H.ink('Bebas', 62, 'H').aA, rcap = H.ink('Bebas', rs, 'H').aA, aw = rs * arW;
    H.line(gX, 'Bebas', rs, ra, c2, 50 + (CAP62 - rcap) / 2, '#fff', { split: false });
    const ax = c2 + H.ink('Bebas', rs, ra).adv + gap;
    H.el('div', 'a', gX, `left:${ax}px;top:${50 + CAP62 / 2 - 1.25}px;width:${aw}px;height:2.5px;background:${ACC}`);
    H.el('div', 'a', gX, `left:${ax + aw - 9}px;top:${50 + CAP62 / 2 - 6}px;width:12px;height:12px;border-top:2.5px solid ${ACC};border-right:2.5px solid ${ACC};transform:rotate(45deg) scale(.9);transform-origin:50% 50%`);
    H.line(gX, 'Bebas', rs, rb, ax + aw + gap, 50 + (CAP62 - rcap) / 2, '#fff', { split: false });
  }
  // the scrubber: the episode's one progress element
  const sL = 24, sW = p.w - 48;
  const rail = H.el('div', 'a', IN, `left:${sL}px;top:0;width:${sW}px;height:3px;border-radius:2px;background:rgba(255,255,255,.2)`);
  const fill = H.el('div', 'a', IN, `left:${sL}px;top:0;width:${sW}px;height:3px;border-radius:2px;background:${ACC};transform-origin:0 50%;box-shadow:0 0 8px rgba(${GLOW},.55)`);
  const p2 = n => String(n).padStart(2, '0');
  return { code: cfg.code, render(t) {
    const on = t >= cfg.t0 && t < cfg.t1; H.show(root, on); if (!on) return;
    const { ex, h } = SEK.stripH(p, t);
    pn.h = h;                                                          // panelAt's retract edge follows the current height
    const st = H.panelAt(pn, t, cfg.t0, p.exit ?? null);
    const bottomFrac = st.qc > 0 ? st.qc : 1 - st.qr;
    const vis = h * (1 - bottomFrac);
    pn.clip.style.clipPath = `inset(0 0 ${(p.hx - vis).toFixed(3)}px 0)`;
    pn.shadow.style.height = h.toFixed(2) + 'px';
    edgeLine.style.height = h.toFixed(2) + 'px';
    mk.style.top = ((h - 4 - MKH) / 2).toFixed(2) + 'px';
    gC.style.opacity = (1 - ex).toFixed(4); gX.style.opacity = ex.toFixed(4);
    gC.style.display = ex >= 0.999 ? 'none' : 'block'; gX.style.display = ex <= 0.001 ? 'none' : 'block';
    const c = CTX.clip(t), clockOn = c != null && t >= p.clockFrom;
    const sec = clockOn ? Math.floor(c) : 0, hm = p2(Math.floor(sec / 3600) % 24) + ':' + p2(Math.floor(sec / 60) % 60), ss = ':' + p2(sec % 60);
    hmC.t.textContent = hmX.t.textContent = hm; ssC.t.textContent = ssX.t.textContent = ss;
    hmC.w.style.opacity = ssC.w.style.opacity = hairC.style.opacity = clockOn ? 1 : 0;
    lab.w.style.transform = clockOn ? 'none' : `translateX(${(cx - c2C).toFixed(2)}px)`;
    let cur = null;
    for (const w of p.expand || []) if (t >= w.a - 0.5 && t < w.b + 0.5) for (const q of w.places || []) if (t >= q[0] || cur == null) cur = q[1];
    for (const s of places) plEls[s].w.style.opacity = s === cur ? 1 : 0;
    const qb = E.outCubic(P(t, cfg.t0 + 0.3, cfg.t0 + 0.9));
    rail.style.top = fill.style.top = (h - 10).toFixed(2) + 'px';
    fill.style.transform = `scaleX(${(P(t, p.progress[0], p.progress[1]) * qb).toFixed(5)})`;
  } };
};
