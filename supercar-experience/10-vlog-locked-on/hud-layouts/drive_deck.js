/* drive_deck.js -- DRV, the drive plate for the SE driving HUD layouts: heading (with a compass strip and a gold caret)
 * and SIDE G (a level vial with a gold bead fed by the camera's own motion sensor, window.LAT at 30 fps, +-0.5 g full scale).
 * Built only from the vlog kit's own helpers (plate, stripe cap, Bebas + Michroma), so it reads as the same family.
 * p: {x, y, w, h, colW, vsize, heading, hdgKeys: [[t, deg], ...]}. Heading is an estimate until a clip carries GPS. */
SEK.driveDeck = function (cfg) {
  const H = SEK.helpers, GOLD = (window.THEME || {}).accent || '#FBD101', GLOW = (window.THEME || {}).glow || '251,209,1', E = KT.ease, P = KT.p, cl = KT.cl;
  const p = Object.assign({ x: 430, y: 292, w: 477, h: 196, heading: 206, colW: 236, vsize: 76, hdgKeys: null, compact: false }, cfg.p);
  const root = H.el('div', 'a', null);
  const pn = H.panel(root, p.x, p.y, p.w, p.h, { stripe: 5 });
  const colW = p.colW;
  // heading: label, Bebas value, a compass strip with a gold caret
  const l1 = H.line(pn.inner, 'Michroma', 14, 'HEADING', 26, 26, 'rgba(255,255,255,.72)', { ls: 0.16 });
  const val = H.line(pn.inner, 'Bebas', p.vsize, 'SW 206', 25, 52, '#fff', { split: false });
  const tapeW = colW - 44, tapeY = 52 + val.capH + 22;
  const tapeClip = H.el('div', 'a', pn.inner, `left:26px;top:${tapeY}px;width:${tapeW}px;height:30px;overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent,#000 22%,#000 78%,transparent)`);
  const tape = H.el('div', 'a', tapeClip, 'left:0;top:0;height:30px;width:4000px');
  const PPD = 3.2;
  for (let d = -180; d <= 540; d += 5) {
    const major = d % 30 === 0, mid = d % 10 === 0;
    H.el('div', 'a', tape, `left:${(d + 180) * PPD}px;top:0;width:${major ? 2 : 1.5}px;height:${major ? 14 : mid ? 9 : 5}px;background:rgba(255,255,255,${major ? .95 : .55})`);
  }
  H.el('div', 'a', pn.inner, `left:${26 + tapeW / 2 - 6}px;top:${tapeY + 18}px;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:9px solid ${GOLD}`);
  // divider
  H.el('div', 'a', pn.inner, `left:${colW}px;top:26px;width:1px;height:${p.h - 52}px;background:rgba(255,255,255,.18)`);
  // side G: label, a level vial, a gold bead from the camera's motion sensor
  const gx = colW + 26, gw = p.w - colW - 52;
  const l2 = H.line(pn.inner, 'Michroma', 14, 'SIDE G', gx, 26, 'rgba(255,255,255,.72)', { ls: 0.16 });
  const vy = 74;
  H.el('div', 'a', pn.inner, `left:${gx}px;top:${vy}px;width:${gw}px;height:28px;border:2px solid rgba(255,255,255,.85);border-radius:14px`);
  [-18, 18].forEach(o => H.el('div', 'a', pn.inner, `left:${gx + gw / 2 + o}px;top:${vy}px;width:2px;height:28px;background:rgba(255,255,255,.85)`));
  const bead = H.el('div', 'a', pn.inner, `left:${gx + gw / 2 - 10}px;top:${vy + 4}px;width:20px;height:20px;border-radius:50%;background:${GOLD};box-shadow:0 0 12px rgba(${GLOW},.7)`);
  const gv = H.line(pn.inner, 'Bebas', 44, '0.00 G', gx, vy + 50, '#fff', { split: false });
  H.line(pn.inner, 'Michroma', 12, 'L', gx, p.h - 38, 'rgba(255,255,255,.55)', { ls: 0.1, split: false });
  H.line(pn.inner, 'Michroma', 12, 'R', gx + gw - 12, p.h - 38, 'rgba(255,255,255,.55)', { ls: 0.1, split: false });
  if (p.compact) { tapeClip.style.display = 'none'; [...pn.inner.children].forEach(e => { if (/border-bottom:9px/.test(e.style.cssText) || /^[LR]$/.test(e.textContent)) e.style.display = 'none'; }); }
  const card = d => ['N','NE','E','SE','S','SW','W','NW'][Math.round((((d % 360) + 360) % 360) / 45) % 8];
  const LAT = window.LAT || [];
  return { code: cfg.code, render(t) {
    const on = t >= cfg.t0 && t < cfg.t1; H.show(root, on); if (!on) return;
    H.panelAt(pn, t, cfg.t0, null);
    KT.track(l1.g, t, { start: cfg.t0 + 0.2, dur: 0.34, spread: 1.6 });
    KT.track(l2.g, t, { start: cfg.t0 + 0.26, dur: 0.34, spread: 1.6 });
    let base = p.heading;
    if (p.hdgKeys) { const K = p.hdgKeys; base = K[0][1]; for (let j = 1; j < K.length; j++) { if (t >= K[j-1][0]) { const u = E.inOutCubic(P(t, K[j-1][0], K[j][0])); base = K[j-1][1] + (K[j][1] - K[j-1][1]) * u; } } }
    const hdg = base + 1.6 * Math.sin(t * 0.55) + 0.7 * Math.sin(t * 1.7), hr = Math.round(((hdg % 360) + 360) % 360) % 360;
    val.t.textContent = card(hr) + ' ' + String(hr).padStart(3, '0');
    tape.style.transform = `translateX(${(tapeW / 2 - (hdg + 180) * PPD).toFixed(2)}px)`;
    const i = Math.max(0, Math.min(LAT.length - 1, Math.round(t * 30)));
    const g = LAT.length ? LAT[i] : 0, v = Math.max(-1, Math.min(1, g / 0.5));
    const qb = E.outCubic(P(t, cfg.t0 + 0.3, cfg.t0 + 0.9));
    bead.style.transform = `translateX(${((gw / 2 - 14) * v * qb).toFixed(2)}px)`;
    gv.t.textContent = Math.abs(g * qb).toFixed(2) + ' G';
  } };
};
