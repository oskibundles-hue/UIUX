/* fdc.js -- Formula Dynamics commercial components (Locked-On language, FD brand), built on the kit's helpers
 * (sekit.js SEK.helpers, kinetic.js KT). Pure functions of t; no timers, no CSS animation, no randomness.
 *
 *   SEK.stepCard   numbered chapter card, bottom-left: tag (STEP 01 / 06), slammed title, FD stripe, sub line and
 *                  a segment tracker (done white, current red, to-do dim). Plate punch through window.FX.punch.
 *   SEK.cardFD     the APPROVED FD end card (v4 no-grid, 24 Sept) animated in the Locked-On way: black wipe up,
 *                  then its own bands (logo, tagline, BOOK YOUR BUILD, stripe, site, handle) come in one by one,
 *                  slow push, one light sweep across BOOK YOUR BUILD. The bands are crops of the approved card,
 *                  so the settled frame is the approved card pixel for pixel.
 */
(function () {
  const { ink, line, el, show, glint, riseLine, px } = SEK.helpers;
  const E = KT.ease, P = KT.p, cl = KT.cl, lerp = KT.lerp;
  const FPS = 30000 / 1001;
  const RED = '#FE0F13', SUB = '#C9C9D0';
  const fitSize = (text, maxW, maxS) => Math.min(maxS, maxS * maxW / ink('Bebas', maxS, text).w);
  const stageEl = () => document.getElementById('stage');

  SEK.stepCard = function (cfg) {
    const p = Object.assign({ n: 1, total: 6, label: 'STEP', title: '', sub: '', x: 54, bottom: 1500, exitDur: 0.2, last: true, count: true, chip: false }, cfg.p);
    const root = el('div', 'a', stageEl(), 'width:1080px;height:1920px');
    const scrim = el('div', 'a', root, 'left:0;top:1020px;width:1080px;height:900px;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,.5) 45%,rgba(0,0,0,.62) 100%)');
    const S = fitSize(p.title, 800, 176), cap = ink('Bebas', S, 'H').aA, tw = ink('Bebas', S, p.title).w;
    const tagTxt = p.count ? `${p.label} ${String(p.n).padStart(2, '0')} / ${String(p.total).padStart(2, '0')}` : p.label;
    const subS = p.sub ? fitSize(p.sub, 800, 50) : 0, capS = p.sub ? ink('Bebas', subS, 'H').aA : 0;
    // stack from the bottom up: segments, sub, stripe, title, tag
    const segY = p.count ? p.bottom - 8 : p.bottom + 4;
    const subY = p.sub ? segY - 26 - capS : segY;
    const stY = subY - 24 - 10;
    const tiY = stY - 22 - cap;
    const tagY = tiY - 24 - 28;
    let chipEl = null;
    if (p.chip) { const cw = ink('Michroma', 30, tagTxt, 0.3).w; chipEl = el('div', 'a', root, `left:${p.x - 12}px;top:${tagY - 10}px;width:${(cw + 30).toFixed(1)}px;height:${30 + 20}px;background:rgba(0,0,0,.88);transform-origin:left center`); }
    const tag = line(root, 'Michroma', 30, tagTxt, p.x, tagY, RED, { ls: 0.3 });
    const holder = el('div', 'a', root, `width:1080px;height:1920px;transform-origin:${p.x}px ${tiY + cap}px`);
    const mask = el('div', 'a', holder, `left:0;top:${tiY - 30}px;width:1080px;height:${cap + 60}px;overflow:hidden`);
    const ti = line(mask, 'Bebas', S, p.title, p.x, 30, '#fff');
    const stripe = el('div', 'a stripe', root, `left:${p.x}px;top:${stY}px;width:${tw.toFixed(1)}px;height:10px`);
    const edge = el('div', 'a edge', root, `left:${p.x}px;top:${stY - 11}px;height:32px;opacity:0`);
    const sb = p.sub ? line(root, 'Bebas', subS, p.sub, p.x, subY, SUB, { mask: true }) : null;
    const segs = [];
    const SW = 58, SG = 10;
    if (p.count) for (let i = 0; i < p.total; i++) segs.push(el('div', 'a', root, `left:${p.x + i * (SW + SG)}px;top:${segY}px;width:${SW}px;height:8px;background:${i < p.n - 1 ? '#fff' : i === p.n - 1 ? RED : 'rgba(255,255,255,.22)'};transform-origin:left center`));
    const flash = el('div', 'a', root, `left:${p.x - 60}px;top:${tiY - 50}px;width:${tw + 160}px;height:${cap + 100}px;background:radial-gradient(ellipse at 30% 50%,rgba(255,240,235,.55) 0%,rgba(254,15,19,.2) 40%,rgba(254,15,19,0) 70%);opacity:0`);
    return { code: cfg.code, render(t) {
      const x0 = cfg.t1 - p.exitDur;
      const on = t >= cfg.t0 && t < cfg.t1; show(root, on); if (!on) return;
      const t0 = cfg.t0, th = t0 + 0.12;
      const qs = E.outExpo(P(t, t0, th + 0.06));
      const qo = p.last ? E.inCubic(P(t, x0, cfg.t1)) : 0;
      scrim.style.opacity = (E.outCubic(P(t, t0, t0 + 0.2)) * (1 - qo)).toFixed(3);
      holder.style.transform = `scale(${lerp(1.45, 1, qs).toFixed(5)}) translateY(${(-cap * 0.3 * qo).toFixed(2)}px)`;
      holder.style.opacity = (1 - qo).toFixed(4);
      ti.w.style.opacity = cl(P(t, t0, t0 + 0.05)).toFixed(3);
      const hit = t >= th ? Math.exp(-(t - th) * 7) : 0;
      flash.style.opacity = (0.5 * hit * (1 - qo)).toFixed(3);
      const qst = E.outExpo(P(t, th, th + 0.34));
      stripe.style.transform = `scaleX(${qst.toFixed(5)})`; stripe.style.transformOrigin = 'left center';
      stripe.style.opacity = (1 - qo).toFixed(3);
      edge.style.opacity = (qst > 0 && qst < 1 ? Math.sin(Math.PI * qst) : 0).toFixed(3);
      edge.style.transform = `translateX(${(tw * qst).toFixed(2)}px)`;
      KT.track(tag.g, t, { start: th, dur: 0.34, spread: 2.0 });
      tag.w.style.opacity = (1 - qo).toFixed(3);
      if (chipEl) { chipEl.style.transform = `scaleX(${E.outExpo(P(t, th - 0.04, th + 0.24)).toFixed(4)})`; chipEl.style.opacity = (1 - qo).toFixed(3); }
      if (sb) { riseLine(sb, t, th + 0.1, 0.32); sb.w.style.opacity = (1 - qo).toFixed(3); }
      segs.forEach((s, i) => {
        const q = i === p.n - 1 ? E.outExpo(P(t, th + 0.16, th + 0.46)) : E.outCubic(P(t, th + 0.1 + 0.025 * i, th + 0.3 + 0.025 * i));
        s.style.transform = `scaleX(${q.toFixed(4)})`; s.style.opacity = (1 - qo).toFixed(3);
      });
      glint(ti, t, th + 0.5, 0.5, { w: 0.2, glow: 10 });
      if (t >= th - 0.001) {
        const k = (t - th) * FPS, amp = Math.exp(-k / 2.2);
        if (k < 12) window.FX.punch = { s: 1 + 0.045 * Math.exp(-(t - th) * 9), dx: 9 * amp * Math.sin(k * 2.1), dy: 7 * amp * Math.cos(k * 2.7) };
      }
    } };
  };

  SEK.cardFD = function (cfg) {
    const B = (window.KITDATA || {}).card;               // {full, bands:[{name,y0,y1,src}]}
    const root = el('div', 'a', stageEl(), 'width:1080px;height:1920px');
    const pnl = el('div', 'a', root, 'width:1080px;height:1920px;background:#08080A');
    const glow = el('div', 'a', root, 'width:1080px;height:160px;background:linear-gradient(180deg,rgba(254,15,19,.34) 0,rgba(254,15,19,.1) 30%,rgba(254,15,19,0) 100%);opacity:0');
    const body = el('div', 'a', root, 'width:1080px;height:1920px;transform-origin:540px 900px');
    const parts = {};
    for (const b of B.bands) {
      const w = el('div', 'a', body, `left:0;top:${b.y0}px;width:1080px;height:${b.y1 - b.y0}px;overflow:hidden`);
      const im = el('img', 'a', w, `width:1080px;height:${b.y1 - b.y0}px;display:block`); im.src = b.src;
      parts[b.name] = { w, im, h: b.y1 - b.y0 };
    }
    const cta = parts.cta;
    // light sweep: a brand-red band MULTIPLIED over the settled card -- white letters x #FE0F13 = exact FD red, the
    // near-black ground stays black. (v1 used a url() mask, which a file:// page cannot load: it drew a box.)
    const sweep = el('div', 'a', cta.w, `left:322px;width:436px;height:${cta.h}px;display:none;mix-blend-mode:multiply`);  // ink x 322-758
    const edge = el('div', 'a edge', root, 'height:0;opacity:0');
    const WIPE = 0.12;
    return { code: cfg.code, render(t) {
      const t0 = cfg.t0, on = t >= t0; show(root, on); if (!on) return;
      const qw = E.inOutCubic(P(t, t0, t0 + WIPE)), FE = 90, yb = (1920 + FE) * qw;
      if (qw >= 1) { pnl.style.webkitMaskImage = 'none'; pnl.style.maskImage = 'none'; }
      else { const m = `linear-gradient(0deg,#000 0px,#000 ${Math.max(0, yb - FE).toFixed(2)}px,rgba(0,0,0,0) ${yb.toFixed(2)}px)`; pnl.style.webkitMaskImage = m; pnl.style.maskImage = m; }
      glow.style.opacity = Math.sin(Math.PI * P(t, t0 + WIPE - 0.02, t0 + WIPE + 0.3)).toFixed(4);
      const s0 = t0 + 0.06;
      // logo: masked wipe left -> right with a light edge
      const ql = E.inOutCubic(P(t, s0, s0 + 0.26));
      parts.logo.w.style.clipPath = `inset(0 ${(100 * (1 - ql)).toFixed(3)}% 0 0)`;
      const lb = B.bands.find(b => b.name === 'logo');
      edge.style.cssText = `left:${(300 + 480 * ql).toFixed(2)}px;top:${lb.y0 - 6}px;height:${lb.y1 - lb.y0 + 12}px;opacity:${ql > 0 && ql < 1 ? 1 : 0}`;
      edge.className = 'a edge';
      // tagline: fade + small rise
      const fu = (pp, st, d = 0.24, dy = 14) => { const q = E.outCubic(P(t, st, st + d)); pp.im.style.opacity = q.toFixed(4); pp.im.style.transform = `translateY(${(dy * (1 - q)).toFixed(3)}px)`; };
      fu(parts.tag, s0 + 0.14);
      // BOOK YOUR BUILD: masked rise
      const qc = E.outExpo(P(t, s0 + 0.18, s0 + 0.5));
      cta.im.style.transform = `translateY(${(105 * (1 - qc)).toFixed(3)}%)`;
      // stripe: draw from the left
      const qs = E.outExpo(P(t, s0 + 0.28, s0 + 0.6));
      parts.stripe.w.style.clipPath = `inset(0 ${(100 * (1 - qs)).toFixed(3)}% 0 0)`;
      fu(parts.site, s0 + 0.34); fu(parts.handle, s0 + 0.4);
      body.style.transform = `scale(${(1 + 0.018 * E.inOutCubic(P(t, t0 + 0.6, cfg.t1))).toFixed(5)})`;
      // one light sweep through the CTA letters
      const qg = P(t, t0 + 1.1, t0 + 1.65);
      if (qg > 0 && qg < 1) {
        const x = -80 + 600 * E.inOutCubic(qg);         // band centre, in the sweep's own x (ink starts at 0)
        sweep.style.display = 'block';
        sweep.style.background = `linear-gradient(106deg,rgba(254,15,19,0) ${(x - 150).toFixed(1)}px,#FE0F13 ${(x - 30).toFixed(1)}px,#FE0F13 ${(x + 30).toFixed(1)}px,rgba(254,15,19,0) ${(x + 150).toFixed(1)}px)`;
      } else sweep.style.display = 'none';
    } };
  };
})();
