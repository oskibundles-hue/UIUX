/* drive_strip.js -- STRIP, the decluttered driving HUD: one slim plate across the top in place of the A2 banner, D1
 * clock, DRV drive plate and PRG bar. Omarie, 6 Oct: "i feel like its too clutteres can we fix that plz".
 *   [SE mark] [10:00:08 + place] | [HEADING S 180] | [SIDE G 0.10 G + bead]   with a progress scrubber along the bottom
 * p: {x, y, w, h, start, place, heading, hdgKeys, range, route: {waypoints, steps}} -- route adds one slim line under
 * the strip (the stop you're on in the accent, the next one in white). Side G from window.LAT, as DRV.
 * Colours follow window.THEME; the plate is a kit panel, so a glass theme frosts it. */
SEK.driveStrip = function (cfg) {
  const H = SEK.helpers, TH = window.THEME || {}, ACC = TH.accent || '#FBD101', GLOW = TH.glow || '251,209,1';
  const E = KT.ease, P = KT.p, cl = KT.cl;
  const p = Object.assign({ x: 54, y: 292, w: 853, h: 140, start: '10:00:00', place: '', heading: 0, hdgKeys: null,
    range: [0, cfg.t1], route: null }, cfg.p);
  const root = H.el('div', 'a', null);
  const pn = H.panel(root, p.x, p.y, p.w, p.h, { stripe: 5 });
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
  const c3 = c2 + (p.w - c2) * 0.48;
  [c2, c3].forEach(x => H.el('div', 'a', IN, `left:${x - 16}px;top:22px;width:1px;height:${p.h - 44}px;background:rgba(255,255,255,.18)`));
  H.line(IN, 'Michroma', 14, 'HEADING', c2, 24, dim, { ls: 0.16, split: false });
  const hv = H.line(IN, 'Bebas', 62, 'S 180', c2, 50, '#fff', { split: false });
  H.line(IN, 'Michroma', 14, 'SIDE G', c3, 24, dim, { ls: 0.16, split: false });
  const gv = H.line(IN, 'Bebas', 62, '0.00 G', c3, 50, '#fff', { split: false });
  const vx = c3 + H.ink('Bebas', 62, '0.00 G').adv + 16, vw = Math.max(40, p.w - 24 - vx), vy = 50 + hv.capH / 2 - 9;
  H.el('div', 'a', IN, `left:${vx}px;top:${vy}px;width:${vw}px;height:18px;border:1.5px solid rgba(255,255,255,.7);border-radius:9px`);
  H.el('div', 'a', IN, `left:${vx + vw / 2 - 1}px;top:${vy}px;width:2px;height:18px;background:rgba(255,255,255,.7)`);
  const bead = H.el('div', 'a', IN, `left:${vx + vw / 2 - 6}px;top:${vy + 3}px;width:12px;height:12px;border-radius:50%;background:${ACC};box-shadow:0 0 10px rgba(${GLOW},.7)`);
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
  const LAT = window.LAT || [];
  return { code: cfg.code, render(t) {
    const on = t >= cfg.t0 && t < cfg.t1; H.show(root, on); if (!on) return;
    H.panelAt(pn, t, cfg.t0, null);
    // clock: the camera's own time, from the clip position
    const sec = Math.floor(s0 + ((typeof CTX !== 'undefined' && CTX.clip(t)) ?? t));
    hm.t.textContent = p2(Math.floor(sec / 3600) % 24) + ':' + p2(Math.floor(sec / 60) % 60);
    ss.t.textContent = ':' + p2(sec % 60);
    // heading (estimate) and side G (camera sensor)
    let base = p.heading;
    if (p.hdgKeys) { const K = p.hdgKeys; base = K[0][1]; for (let j = 1; j < K.length; j++) { if (t >= K[j - 1][0]) { const u = E.inOutCubic(P(t, K[j - 1][0], K[j][0])); base = K[j - 1][1] + (K[j][1] - K[j - 1][1]) * u; } } }
    const hd = base + 1.6 * Math.sin(t * 0.55) + 0.7 * Math.sin(t * 1.7), hr = Math.round(((hd % 360) + 360) % 360);
    hv.t.textContent = card(hr) + ' ' + String(hr).padStart(3, '0');
    const g = LAT.length ? LAT[Math.max(0, Math.min(LAT.length - 1, Math.round(t * 30)))] : 0;
    gv.t.textContent = Math.abs(g).toFixed(2) + ' G';
    const qb = E.outCubic(P(t, cfg.t0 + 0.3, cfg.t0 + 0.9));
    bead.style.transform = `translateX(${((vw / 2 - 9) * Math.max(-1, Math.min(1, g / 0.5)) * qb).toFixed(2)}px)`;
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
