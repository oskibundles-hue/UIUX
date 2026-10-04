/* fdkit.js -- the Formula Dynamics end card for the Locked-On vlog (built from v2kit.js SEK.v2end, same motion:
 * bottom-up wipe to black, logo wipe, stripe draw, glyph rise / tracking, a slow push, glints). FD copy is
 * FD.copy in creator-kit/remotion/src/brand/tokens.ts: BOOK YOUR BUILD, always with the site and the handle.
 *   SEK.fdEnd  p: {cta, how, site, handle, credit}
 */
(function () {
  const { el, show, line, ink, glint } = SEK.helpers;
  const E = KT.ease, P = KT.p;
  const RED = '#FE0F13', WIPE = 0.118;
  const centreX = (fam, size, text, cx, ls) => cx - ink(fam, size, text, ls).w / 2;
  SEK.fdEnd = function (cfg) {
    const e = Object.assign({ cta: 'BOOK YOUR BUILD', how: 'DM US YOUR MODEL', site: 'FORMULADYNAMICSPERFORMANCE.COM',
                              handle: '@FORMULADYNAMICSPERFORMANCE', credit: 'FILMED BY @NQ.YOUNG' }, cfg.p);
    const root = el('div', 'a', document.getElementById('stage'), 'width:1080px;height:1920px');
    const pnl = el('div', 'a', root, 'width:1080px;height:1920px;background:#000');
    const wipeStripe = el('div', 'a', root, 'width:1080px;height:160px;background:linear-gradient(180deg,rgba(254,15,19,.34) 0,rgba(254,15,19,.10) 30%,rgba(254,15,19,0) 100%);opacity:0');
    const body = el('div', 'a', root, 'width:1080px;height:1920px;transform-origin:540px 900px');
    const lw = 330, lh = lw * 4102 / 4000;
    const logoW = el('div', 'a', body, `left:${540 - lw / 2}px;top:330px;width:${lw}px;height:${lh.toFixed(2)}px`);
    const logo = el('img', '', logoW, `width:${lw}px;display:block`); logo.src = 'logos/fd-stacked--white.png';
    const logoEdge = el('div', 'a edge', logoW, `height:${lh + 12}px;top:-6px;opacity:0`);
    const stripe = el('div', 'a stripe', body, `left:360px;top:${Math.round(330 + lh + 34)}px;width:360px;height:8px`);
    const Y = Math.round(330 + lh + 80);
    const C = (fam, size, txt, y, col, o) => line(body, fam, size, txt, centreX(fam, size, txt, 540, o && o.ls), y, col, o);
    const L = {};
    L.cta = C('Bebas', 150, e.cta, Y, '#fff', { mask: true });
    L.how = C('Michroma', 30, e.how, Y + 176, RED);
    L.site = C('Bebas', 64, e.site, Y + 240, '#fff');
    L.handle = C('Bebas', 64, e.handle, Y + 314, 'rgba(255,255,255,.72)');
    const rule = el('div', 'a', body, `left:470px;top:${Y + 420}px;width:140px;height:2px;background:rgba(255,255,255,.35);transform-origin:50% 50%`);
    L.credit = C('Michroma', 22, e.credit, Y + 452, '#fff');
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
      KT.rise(L.cta.g, t, { start: s0 + 0.08, stagger: 0.006, dur: 0.28, dy: 1.05, ease: E.outExpo });
      KT.track(L.how.g, t, { start: s0 + 0.16, dur: 0.26, spread: 1.7, stagger: 0.004 });
      const fu = (ln, st) => { const q = E.outCubic(P(t, st, st + 0.22)); ln.w.style.opacity = q.toFixed(4); ln.w.style.transform = `translateY(${(14 * (1 - q)).toFixed(3)}px)`; };
      fu(L.site, s0 + 0.22); fu(L.handle, s0 + 0.26);
      rule.style.transform = `scaleX(${E.outExpo(P(t, s0 + 0.30, s0 + 0.52)).toFixed(5)})`;
      fu(L.credit, s0 + 0.32);
      const push = 1 + 0.018 * E.inOutCubic(P(t, t0 + 0.55, cfg.t1));
      body.style.transform = `scale(${push.toFixed(5)})`;
      glint(L.cta, t, t0 + 1.10, 0.55, { w: 0.2, glow: 12 });
    } };
  };
})();
