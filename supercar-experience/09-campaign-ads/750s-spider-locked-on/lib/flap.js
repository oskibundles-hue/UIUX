/* flap.js -- a split-flap (departure board) engine for the "NOW BOARDING" look.
 *
 * Same contract as kinetic.js: the DOM is built once, every schedule is computed at build time from a seeded
 * RNG, and Flap.render(row, t) is a PURE function of t, so lib/kcapture.js can sample any sub-frame time and
 * average true motion blur. Every change goes through inline styles, which KT.signature() hashes.
 *
 * A cell is four half-tiles: the static top shows the NEW character's top half, the static bottom the OLD
 * character's bottom half; the upper flap (old top half) falls from 0 to -90 deg, then the lower flap (new bottom
 * half) falls from +90 to 0 deg and bounces once. A flip takes Flap.D seconds.
 *
 *   const r = Flap.row(parent, 'SPIDER', { x, y, cw, ch, gap, fs, color })
 *   Flap.set(r, '')                              // the character every cell starts on ('' = blank tile)
 *   Flap.cascade(r, t0, { stagger, cycle, rng, pool, text })   // flip in (optionally via n random pre-flips)
 *   Flap.all(r, t0, text)                        // every cell flips at once (figures arrive and leave whole)
 *   Flap.render(r, t)
 */
(function () {
  const Flap = {};
  const D = Flap.D = 0.075;                       // one flip, about 1.8 frames at 23.976 fps
  const BOUNCE = 0.07;                            // the lower flap's single bounce after it lands
  // letters a price cell may show while it cycles: nothing that reads as a digit (no O S B I Z G L D C Q)
  Flap.SAFE_LETTERS = 'AEFHJKMNPRTUVWXY';
  Flap.LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';

  const ink = (() => { const c = document.createElement('canvas').getContext('2d'); return (fs, s) => {
    c.font = `${fs}px Bebas`; return c.measureText(s); }; })();

  function half(cls, w, h, top, r, fs, dy, color) {
    const d = document.createElement('div');
    d.className = 'fh ' + cls;
    const bgTop = 'linear-gradient(180deg,#2c2c2c 0%,#1d1d1d 100%)', bgBot = 'linear-gradient(180deg,#181818 0%,#0e0e0e 100%)';
    d.style.cssText = `position:absolute;left:0;top:${top ? 0 : h / 2}px;width:${w}px;height:${h / 2}px;overflow:hidden;` +
      `background:${top ? bgTop : bgBot};border-radius:${top ? `${r}px ${r}px 0 0` : `0 0 ${r}px ${r}px`};` +
      `transform-origin:50% ${top ? '100%' : '0%'};backface-visibility:hidden;` +
      (top ? 'box-shadow:inset 0 1px 0 rgba(255,255,255,.10)' : '');
    const s = document.createElement('span');
    s.style.cssText = `position:absolute;left:0;top:${top ? 0 : -h / 2}px;width:${w}px;height:${h}px;line-height:${h}px;` +
      `text-align:center;font-family:Bebas;font-size:${fs}px;color:${color};transform:translateY(${dy.toFixed(2)}px);white-space:pre`;
    d.appendChild(s);
    return d;
  }

  Flap.row = function (parent, text, o) {
    const chars = [...text], cells = [];
    const { cw, ch, gap = 4, fs = Math.round(ch * 1.0), r = Math.max(2, Math.round(cw * 0.07)) } = o;
    // centre the capitals on the hinge: baseline = h/2 + capH/2
    const m = ink(fs, 'H'), capH = m.actualBoundingBoxAscent, fA = m.fontBoundingBoxAscent, fD = m.fontBoundingBoxDescent;
    const dy = (ch / 2 + capH / 2) - ((ch - (fA + fD)) / 2 + fA);
    chars.forEach((c, i) => {
      const color = (o.colors && o.colors[i]) || o.color || '#FFFFFF';
      const el = document.createElement('div');
      el.className = 'fc';
      el.style.cssText = `position:absolute;left:${o.x + i * (cw + gap)}px;top:${o.y}px;width:${cw}px;height:${ch}px;` +
        `perspective:${Math.round(ch * 4)}px`;
      const sT = half('st', cw, ch, true, r, fs, dy, color), sB = half('sb', cw, ch, false, r, fs, dy, color);
      const fT = half('ft', cw, ch, true, r, fs, dy, color), fB = half('fb', cw, ch, false, r, fs, dy, color);
      const hinge = document.createElement('div');
      hinge.style.cssText = `position:absolute;left:0;top:${ch / 2 - 1}px;width:${cw}px;height:2px;background:#000;` +
        `box-shadow:0 1px 0 rgba(255,255,255,.07)`;
      const pinL = document.createElement('div'), pinR = document.createElement('div');
      for (const [p, x] of [[pinL, 1], [pinR, cw - 4]])
        p.style.cssText = `position:absolute;left:${x}px;top:${ch / 2 - 3}px;width:3px;height:6px;background:#3a3a3a;border-radius:1px`;
      el.append(sT, sB, fT, fB, hinge, pinL, pinR);
      parent.appendChild(el);
      cells.push({ el, sT, sB, fT, fB, final: c, ch0: c, ev: [], color, last: null });
    });
    return { cells, text, o };
  };

  Flap.set = (row, c) => { row.cells.forEach(k => { k.ch0 = c; }); return row; };
  const push = (k, t, c) => { k.ev.push({ t, c }); k.ev.sort((a, b) => a.t - b.t); };

  // flip every cell to its character (text[i], default the row's text) starting at t0 + i * stagger, after
  // `cycle` random pre-flips drawn from `pool` (one every `step` seconds)
  Flap.cascade = function (row, t0, o = {}) {
    const { stagger = 0.03, cycle = 0, step = 0.083, pool = Flap.LETTERS, rng = Math.random, order = 'ltr' } = o;
    const text = o.text !== undefined ? [...o.text] : row.cells.map(k => k.final);
    const n = row.cells.length;
    row.cells.forEach((k, i) => {
      const j = order === 'rtl' ? n - 1 - i : i, target = text[i] ?? '';
      let t = t0 + j * stagger;
      const ncy = typeof cycle === 'function' ? cycle(i) : cycle;
      if (target.trim() && ncy > 0) for (let c = 0; c < ncy; c++) { push(k, t, pool[Math.floor(rng() * pool.length)]); t += step; }
      push(k, t, target);
    });
    return row;
  };
  // every cell at once (a figure appears or leaves whole, never as a partial number)
  Flap.all = function (row, t0, text) {
    const tx = text !== undefined ? [...text] : row.cells.map(k => k.final);
    row.cells.forEach((k, i) => push(k, t0, tx[i] ?? ''));
    return row;
  };
  // one cell: cycle `pool` letters from t0 every `step` until it lands on its character at tLand
  Flap.reel = function (cell, t0, tLand, o = {}) {
    const { step = 0.083, pool = Flap.SAFE_LETTERS, rng = Math.random } = o;
    for (let t = t0; t < tLand - step * 0.5; t += step) push(cell, t, pool[Math.floor(rng() * pool.length)]);
    push(cell, tLand, cell.final);
  };

  // the state of one cell at time t: { a: old char, b: new char, u: flip progress (null = at rest), since }
  function stateAt(k, t) {
    let cur = k.ch0, prev = k.ch0, tk = -1e9;
    for (const e of k.ev) { if (e.t > t) break; prev = cur; cur = e.c; tk = e.t; }
    const u = (t - tk) / D;
    return u < 1 ? { a: prev, b: cur, u } : { a: cur, b: cur, u: null, since: t - tk - D };
  }

  const setTxt = (h, c) => { const s = h.firstChild; if (s.textContent !== c) s.textContent = c; };
  const on = c => !!(c && c.trim());
  // no half character ever reads on its own (a top half of 9 over a blank bottom read as $1,200): the new top half
  // stays in the falling flap's shadow until the lower flap has nearly covered the old bottom half, and an old
  // bottom half darkens as the new lower flap falls over it
  const shadeTop = (S) => (on(S.b) && S.a !== S.b) ? 0.16 + 0.84 * Math.min(1, Math.max(0, (S.u - 0.62) / 0.38)) : 1;
  const shadeBot = (S) => (on(S.a) && S.a !== S.b) ? 1 - 0.84 * Math.min(1, Math.max(0, (S.u - 0.12) / 0.5)) : 1;
  Flap.render = function (row, t, o = {}) {
    for (const k of row.cells) {
      const S = stateAt(k, t);
      if (S.u === null) {
        setTxt(k.sT, S.b); setTxt(k.sB, S.b);
        k.sT.style.filter = 'none'; k.sB.style.filter = 'none';
        // the single bounce of the lower flap just after it lands
        const q = S.since / BOUNCE;
        if (q >= 0 && q < 1) {
          setTxt(k.fB, S.b); k.fB.style.display = 'block';
          k.fB.style.transform = `rotateX(${(-9 * Math.sin(Math.PI * q) * (1 - q)).toFixed(3)}deg)`;
          k.fB.style.filter = 'none';
        } else k.fB.style.display = 'none';
        k.fT.style.display = 'none';
      } else {
        setTxt(k.sT, S.b); setTxt(k.sB, S.a); setTxt(k.fT, S.a); setTxt(k.fB, S.b);
        const st = shadeTop(S), sb = shadeBot(S);
        k.sT.style.filter = st < 1 ? `brightness(${st.toFixed(3)})` : 'none';
        k.sB.style.filter = sb < 1 ? `brightness(${sb.toFixed(3)})` : 'none';
        if (S.u < 0.5) {                          // the old top half falls to edge-on, darkening as it goes
          const v = S.u / 0.5;
          k.fT.style.display = 'block';
          k.fT.style.transform = `rotateX(${(-90 * v * v).toFixed(3)}deg)`;
          k.fT.style.filter = `brightness(${(1 - 0.55 * v).toFixed(3)})`;
          k.fB.style.display = 'none';
        } else {                                  // the new bottom half falls from edge-on into place
          const v = (S.u - 0.5) / 0.5;
          k.fT.style.display = 'none';
          k.fB.style.display = 'block';
          k.fB.style.transform = `rotateX(${(90 * (1 - v) * (1 - v)).toFixed(3)}deg)`;
          k.fB.style.filter = `brightness(${(1.35 - 0.35 * v).toFixed(3)})`;
        }
      }
      if (o.flash) {                              // a landing flash on the cell (price reels)
        const f = o.flash(k, t);
        k.el.style.filter = f > 0 ? `brightness(${(1 + 0.6 * f).toFixed(3)}) drop-shadow(0 0 ${(14 * f).toFixed(1)}px rgba(251,209,1,${(0.5 * f).toFixed(3)}))` : 'none';
      }
    }
  };
  // the cells' ink box (for inkAudit)
  Flap.box = row => { const a = row.cells[0].el.getBoundingClientRect(), b = row.cells[row.cells.length - 1].el.getBoundingClientRect();
    return { x0: a.left, x1: b.right, y0: Math.min(a.top, b.top), y1: Math.max(a.bottom, b.bottom) }; };
  // is anything showing (any cell not blank, or mid-flip)?
  Flap.visible = (row, t) => row.cells.some(k => { const S = stateAt(k, t); return S.u !== null || (S.b && S.b.trim()); });
  Flap.landTime = k => { const e = k.ev.filter(e => e.c === k.final); return e.length ? e[e.length - 1].t + D : null; };
  window.Flap = Flap;
})();
