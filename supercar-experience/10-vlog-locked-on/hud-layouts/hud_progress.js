/* hud_progress.js -- PRG, progress bar options for the SE driving HUD. Pair it with A2 p.rail: false, which hides the
 * banner's own rail. Omarie, 5 Oct: "change the progress bar".
 *   style 'underline': a slim scrubber along the bottom of another plate (p.anchor, default D1, the clock), inside
 *                      that plate, so it unrolls and exits with it
 *   style 'edge':      a hairline lap line across the top of the HUD row (p.x, p.y, p.w), with a glowing head
 *   style 'led':       a segmented, rev-counter style bar down the inner edge of the A2 banner (p.segs segments)
 * p.range: [t0, t1] the bar covers (the cut's length). Colours follow window.THEME like the rest of the kit.
 * List PRG after its anchor in the scene's comps: it attaches to the anchor's plate when first rendered. */
SEK.progressBar = function (cfg) {
  const H = SEK.helpers, TH = window.THEME || {}, ACC = TH.accent || '#FBD101', GLOW = TH.glow || '251,209,1';
  const E = KT.ease, P = KT.p;
  const p = Object.assign({ style: 'underline', anchor: 'D1', range: [0, cfg.t1], x: 54, y: 278, w: 853, segs: 22 }, cfg.p);
  const root = H.el('div', 'a', null);
  let parts = null;
  // the anchor's plate: its clip box (static left/top/width/height) and the element to draw into
  const plateOf = code => {
    const host = [...document.getElementById('stage').children].find(e => e.dataset.code === code);
    const pl = host && host.querySelector('.plate');
    if (!pl) return null;
    const box = pl.parentElement, cs = box.style;
    const n = v => parseFloat(v) || 0;
    return { box, x: n(cs.left) || n(pl.style.left), y: n(cs.top) || n(pl.style.top), w: n(pl.style.width), h: n(pl.style.height) };
  };
  function build() {
    if (p.style === 'underline') {
      const a = plateOf(p.anchor); if (!a) return null;
      // inside the plate's clip box, so coordinates are local to it
      // a slim scrubber under the date line, inset to the plate's text margin (clear of rounded glass corners)
      const L = 26, W = a.w - 52, T = a.h - 16;
      const track = H.el('div', 'a', a.box, `left:${L}px;top:${T}px;width:${W}px;height:4px;border-radius:2px;background:rgba(255,255,255,.22)`);
      const fill = H.el('div', 'a', a.box, `left:${L}px;top:${T}px;width:${W}px;height:4px;border-radius:2px;background:${ACC};transform-origin:0 50%;box-shadow:0 0 10px rgba(${GLOW},.55)`);
      return { len: W, track, fill };
    }
    if (p.style === 'led') {
      const a = plateOf('A2'); if (!a) return null;
      // A2 draws its plate straight into its sliding body, so a.box is that body and x/y are frame coordinates
      const y0 = a.y + 24 + 52 * 215 / 338 + 48, y1 = a.y + a.h - 18, pitch = (y1 - y0) / p.segs;
      const segs = [];
      for (let k = 0; k < p.segs; k++)
        segs.push(H.el('div', 'a', a.box, `left:${a.x + 7}px;top:${(y0 + k * pitch).toFixed(2)}px;width:5px;height:${(pitch * 0.62).toFixed(2)}px;background:rgba(255,255,255,.16)`));
      return { segs };
    }
    // edge: its own layer on the stage
    const track = H.el('div', 'a', root, `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:2px;background:rgba(255,255,255,.30)`);
    const fill = H.el('div', 'a', root, `left:${p.x}px;top:${p.y - 0.5}px;width:${p.w}px;height:3px;background:${ACC};transform-origin:0 50%;box-shadow:0 0 8px rgba(${GLOW},.6)`);
    const head = H.el('div', 'a', root, `left:${p.x - 5}px;top:${p.y - 4}px;width:10px;height:10px;border-radius:50%;background:#fff;box-shadow:0 0 0 3px ${ACC},0 0 14px 4px rgba(${GLOW},.7)`);
    [0.25, 0.5, 0.75].forEach(f => H.el('div', 'a', root, `left:${p.x + p.w * f}px;top:${p.y - 3}px;width:2px;height:8px;background:rgba(255,255,255,.45)`));
    return { len: p.w, track, fill, head };
  }
  return { code: cfg.code, render(t) {
    const on = t >= cfg.t0 && t < cfg.t1;
    if (!parts) parts = build();
    if (!parts) return;
    const all = [root, parts.track, parts.fill, parts.head, ...(parts.segs || [])].filter(Boolean);
    all.forEach(e => H.show(e, on)); if (!on) return;
    const pr = P(t, p.range[0], p.range[1]), qa = E.outCubic(P(t, cfg.t0, cfg.t0 + 0.5));
    if (parts.segs) {
      const lit = pr * parts.segs.length;
      parts.segs.forEach((s, k) => {
        const f = Math.max(0, Math.min(1, lit - k));
        s.style.background = f > 0 ? ACC : 'rgba(255,255,255,.16)';
        s.style.opacity = (f > 0 ? 0.35 + 0.65 * f : 1) * qa;
        s.style.boxShadow = f > 0 && k === Math.floor(lit) ? `0 0 10px rgba(${GLOW},.8)` : 'none';
      });
      return;
    }
    parts.fill.style.transform = `scaleX(${(pr * qa).toFixed(5)})`;
    parts.track.style.opacity = qa.toFixed(3);
    if (parts.head) parts.head.style.transform = `translateX(${(parts.len * pr * qa).toFixed(2)}px)`;
  } };
};
