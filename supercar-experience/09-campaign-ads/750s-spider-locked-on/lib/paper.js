/* paper.js -- a cut-paper collage kit for the "PASTE-UP" look.
 *
 * A paste-up is the pre-digital way a layout was made: type set on paper, cut out and pasted onto the board.
 * Here strips of torn paper, gold tape and hand-drawn marker are pasted over the footage.
 *
 * Motion grammar: everything moves ON TWOS (12 drawings a second on the 23.976 fps timeline) and BOILS (each
 * drawing sits a hair off the last one), the opposite of the approved cut's sub-frame motion blur. Time is
 * quantised to the OUTPUT frame first, so every sub-frame sample inside one frame renders the same drawing and
 * lib/kcapture.js captures each frame once. Every function is pure in t; schedules are seeded.
 */
(function () {
  const Paper = {};
  let FPS = 24000 / 1001;
  Paper.fps = f => { FPS = f; };
  // the drawing index (12 per second) and the time it stands for
  Paper.step = t => Math.floor(Math.round(t * FPS) / 2);
  Paper.qt = t => Paper.step(t) * 2 / FPS;
  const STEP = () => 2 / FPS;
  const rngOf = seed => { let s = (seed * 2654435761) % 2147483647 || 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; };
  const hash = (a, b) => { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
  Paper.rng = rngOf;

  // ---------------------------------------------------------------- textures (built once)
  function noiseURL(rgb, maxA, seed, size = 160) {
    const c = document.createElement('canvas'); c.width = c.height = size;
    const x = c.getContext('2d'), im = x.createImageData(size, size), r = rngOf(seed);
    for (let i = 0; i < size * size; i++) {
      const a = r() ** 2.2 * maxA;
      im.data[i * 4] = rgb[0]; im.data[i * 4 + 1] = rgb[1]; im.data[i * 4 + 2] = rgb[2]; im.data[i * 4 + 3] = a;
    }
    // a few fibres
    x.putImageData(im, 0, 0);
    x.strokeStyle = `rgba(${rgb.join(',')},${(maxA / 255 * 0.5).toFixed(3)})`; x.lineWidth = 0.6;
    for (let k = 0; k < 26; k++) { x.beginPath(); const px = r() * size, py = r() * size; x.moveTo(px, py);
      x.quadraticCurveTo(px + (r() - .5) * 30, py + (r() - .5) * 30, px + (r() - .5) * 50, py + (r() - .5) * 50); x.stroke(); }
    return c.toDataURL();
  }
  let TEX = null;
  function tex() {
    if (TEX) return TEX;
    TEX = { white: noiseURL([60, 50, 40], 34, 11), black: noiseURL([255, 255, 255], 20, 12), gold: noiseURL([90, 60, 0], 40, 13) };
    return TEX;
  }
  // paper fill: base colour + grain; gold paper also carries a halftone of darker gold dots
  Paper.fill = function (kind) {
    const T = tex();
    if (kind === 'white') return `background:url(${T.white}),#FFFFFF`;
    if (kind === 'black') return `background:url(${T.black}),#0B0B0B`;
    if (kind === 'gold') return `background:url(${T.gold}),radial-gradient(circle,rgba(120,80,0,.16) 30%,transparent 33%) 0 0/13px 13px,#FBD101`;
    if (kind === 'tape') return `background:url(${T.gold}),linear-gradient(90deg,rgba(251,209,1,.9),rgba(255,226,90,.86) 50%,rgba(251,209,1,.9))`;
    return kind;
  };

  // ---------------------------------------------------------------- torn edges
  // a deckled polygon: every side is walked in small steps with a perpendicular jitter; `sides` picks which are torn
  Paper.torn = function (w, h, seed, o = {}) {
    const { amp = 3.2, step = 9, sides = 'tblr', inset = 4 } = o, r = rngOf(seed), pts = [];
    const j = s => (sides.includes(s) ? (r() - 0.5) * 2 * amp : 0);
    const walk = (x0, y0, x1, y1, side, nx, ny) => {
      const n = Math.max(2, Math.round(Math.hypot(x1 - x0, y1 - y0) / step));
      for (let i = 0; i < n; i++) { const u = i / n, d = j(side) + (sides.includes(side) ? inset * 0.5 : 0);
        pts.push([x0 + (x1 - x0) * u + nx * d, y0 + (y1 - y0) * u + ny * d]); }
    };
    walk(0, 0, w, 0, 't', 0, 1); walk(w, 0, w, h, 'r', -1, 0); walk(w, h, 0, h, 'b', 0, -1); walk(0, h, 0, 0, 'l', 1, 0);
    return 'polygon(' + pts.map(p => `${p[0].toFixed(1)}px ${p[1].toFixed(1)}px`).join(',') + ')';
  };
  // a rough disc (a sticker cut with scissors)
  Paper.disc = function (d, seed, n = 46) {
    const r = rngOf(seed), pts = [];
    for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, rr = d / 2 * (0.965 + r() * 0.035);
      pts.push([d / 2 + Math.cos(a) * rr, d / 2 + Math.sin(a) * rr]); }
    return 'polygon(' + pts.map(p => `${p[0].toFixed(1)}px ${p[1].toFixed(1)}px`).join(',') + ')';
  };

  // ---------------------------------------------------------------- pieces
  // a piece = an outer wrapper (position, rotation, boil, shadow) around a clipped paper face.
  // o: { x, y, w, h, rot, kind, seed, sides, shape: 'strip'|'disc', shadow }
  Paper.piece = function (parent, o) {
    const w = document.createElement('div');
    w.style.cssText = `position:absolute;left:${o.x}px;top:${o.y}px;width:${o.w}px;height:${o.h}px;` +
      `transform-origin:50% 50%;filter:drop-shadow(0 ${o.lift ?? 7}px ${o.blur ?? 9}px rgba(0,0,0,${o.shadow ?? 0.38}))`;
    const face = document.createElement('div');
    face.style.cssText = `position:absolute;left:0;top:0;width:${o.w}px;height:${o.h}px;${Paper.fill(o.kind || 'white')};` +
      `clip-path:${o.shape === 'disc' ? Paper.disc(o.w, o.seed || 1) : Paper.torn(o.w, o.h, o.seed || 1, { sides: o.sides ?? 'tblr', amp: o.amp ?? 3.2 })}`;
    w.appendChild(face); parent.appendChild(w);
    return { w, face, o, rot: o.rot || 0, id: (o.seed || 1) };
  };
  // text on a piece (ink box centred, or at pad from the left)
  Paper.text = function (piece, text, o) {
    const s = document.createElement('div');
    s.style.cssText = `position:absolute;left:0;top:0;width:${piece.o.w}px;height:${piece.o.h}px;display:flex;align-items:center;` +
      `justify-content:${o.align === 'left' ? 'flex-start' : 'center'};padding-left:${o.pad || 0}px;font-family:${o.font || 'Bebas'};` +
      `font-size:${o.size}px;color:${o.color};line-height:1;white-space:pre;letter-spacing:${o.ls || 0};` +
      `transform:translateY(${o.dy || 0}px)`;
    s.innerHTML = text; piece.face.appendChild(s); return s;
  };
  // gold tape across a point (cx, cy) of the parent
  Paper.tape = function (parent, cx, cy, w, rot, seed) {
    const p = Paper.piece(parent, { x: cx - w / 2, y: cy - 19, w, h: 38, rot, kind: 'tape', seed, sides: 'lr', amp: 4,
                                    shadow: 0.14, lift: 2, blur: 3 });
    p.w.style.opacity = '0.93'; return p;
  };

  // ---------------------------------------------------------------- stepped motion
  // where the piece is at drawing time: a slap-on (appears big and turned, overshoots, settles over 3 drawings),
  // a boil (a small per-drawing jitter), and an optional rip-off (flies out over 2 drawings)
  Paper.pose = function (pc, t, o = {}) {
    const q = Paper.qt(t), S = STEP(), k = Paper.step(t);
    const { t0 = -1e9, t1 = 1e9, dx = 0, dy = -900, spin = 16, boil = 1, pop = 1, hits = [], dyIn = 0, hitPop = 1 } = o;
    if (q < t0 - 1e-6 || q >= t1 + 2 * S - 1e-6) { pc.w.style.display = 'none'; return false; }
    pc.w.style.display = 'block';
    let sc = 1, rot = pc.rot, tx = 0, ty = 0;
    const s = Math.round((q - t0) / S);
    if (s === 0) { sc = 1 + 0.16 * pop; rot += 4 * pop; ty += dyIn; } else if (s === 1) { sc = 1 - 0.03 * pop; rot -= 1.2 * pop; ty -= dyIn * 0.12; }
    for (const h of hits) { const e = Math.round((q - h) / S);            // a beat hit: the piece is slapped again
      if (e === 0) { sc *= 1 + 0.09 * hitPop; rot += 2.2 * hitPop; } else if (e === 1) { sc *= 1 - 0.015 * hitPop; rot -= 0.6 * hitPop; } }
    const e = Math.round((q - t1) / S);
    if (q >= t1 - 1e-6) { const f = e === 0 ? 0.22 : 1; tx += dx * f; ty += dy * f; rot += spin * (e === 0 ? 0.35 : 1); }
    const bx = (hash(k, pc.id) - 0.5) * 2.4 * boil, by = (hash(k + 99, pc.id) - 0.5) * 2.4 * boil, br = (hash(k + 7, pc.id) - 0.5) * 0.7 * boil;
    pc.w.style.transform = `translate(${(tx + bx).toFixed(2)}px,${(ty + by).toFixed(2)}px) rotate(${(rot + br).toFixed(3)}deg) scale(${sc.toFixed(4)})`;
    return true;
  };

  // ---------------------------------------------------------------- marker
  // a smooth path through points (Catmull-Rom as cubic Beziers)
  function smooth(P) {
    if (P.length < 2) return '';
    let d = `M${P[0][0].toFixed(1)},${P[0][1].toFixed(1)}`;
    for (let i = 0; i < P.length - 1; i++) {
      const p0 = P[i - 1] || P[i], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2] || p2;
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6], c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += `C${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${c2[0].toFixed(1)},${c2[1].toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
    }
    return d;
  }
  const jit = (P, r, a) => P.map(p => [p[0] + (r() - .5) * 2 * a, p[1] + (r() - .5) * 2 * a]);
  // shapes, in local coordinates; each returns point lists (one list per stroke)
  Paper.shapes = {
    loop: (rx, ry, turns = 1.3, start = -2.2) => { const P = []; const n = Math.round(28 * turns);
      for (let i = 0; i <= n; i++) { const a = start + i / n * turns * Math.PI * 2, g = 1 + 0.07 * Math.sin(i * 0.9);
        P.push([Math.cos(a) * rx * g, Math.sin(a) * ry * g]); } return [P]; },
    line: (x0, y0, x1, y1, bow = 0) => { const P = []; for (let i = 0; i <= 8; i++) { const u = i / 8;
      P.push([x0 + (x1 - x0) * u - (y1 - y0) * bow * Math.sin(Math.PI * u), y0 + (y1 - y0) * u + (x1 - x0) * bow * Math.sin(Math.PI * u)]); } return [P]; },
    arrow: (x0, y0, x1, y1, bow = 0.12, head = 34) => { const L = Paper.shapes.line(x0, y0, x1, y1, bow)[0];
      const a = Math.atan2(y1 - L[7][1], x1 - L[7][0]);
      const h1 = [[x1 + Math.cos(a + 2.6) * head, y1 + Math.sin(a + 2.6) * head], [x1, y1], [x1 + Math.cos(a - 2.6) * head, y1 + Math.sin(a - 2.6) * head]];
      return [L, h1]; },
    tick: s => [[[-0.45 * s, 0], [-0.1 * s, 0.38 * s], [0.55 * s, -0.5 * s]]],
    wave: (w, amp = 6, n = 7) => { const P = []; for (let i = 0; i <= n * 2; i++) P.push([i / (n * 2) * w, (i % 2 ? -amp : amp)]); return [P]; },
    star: (r) => { const P = []; for (let i = 0; i <= 10; i++) { const a = -Math.PI / 2 + i * Math.PI * 4 / 5; P.push([Math.cos(a) * r, Math.sin(a) * r]); } return [P]; },
  };
  // a marker mark: an <svg> in stage coordinates with `boil` (3) jittered versions of every stroke; it draws on over
  // `draw` seconds (stepped) from t0 and disappears at t1 (erased over 2 drawings)
  Paper.mark = function (parent, strokes, o) {
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', 1080); svg.setAttribute('height', 1920); svg.setAttribute('viewBox', '0 0 1080 1920');
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const g = document.createElementNS(NS, 'g'); svg.appendChild(g); parent.appendChild(svg);
    const r = rngOf(o.seed || 5), variants = [];
    for (let v = 0; v < 3; v++) {
      const paths = strokes.map(P => { const p = document.createElementNS(NS, 'path');
        p.setAttribute('d', smooth(jit(P, r, o.jitter ?? 2.2))); p.setAttribute('fill', 'none');
        p.setAttribute('stroke', o.color || '#FBD101'); p.setAttribute('stroke-width', o.width || 9);
        p.setAttribute('stroke-linecap', 'round'); p.setAttribute('stroke-linejoin', 'round');
        if (o.opacity) p.setAttribute('stroke-opacity', o.opacity);
        g.appendChild(p); return p; });
      variants.push(paths);
    }
    const lens = variants.map(ps => ps.map(p => p.getTotalLength()));
    return { svg, g, variants, lens, o };
  };
  // o: { t0, draw, t1, x, y, rot } (x, y, rot place the mark; may be updated per frame for tracked marks)
  Paper.markAt = function (m, t, place) {
    const q = Paper.qt(t), k = Paper.step(t), S = STEP();
    const { t0, draw = 0.33, t1 = 1e9 } = m.o;
    const on = q >= t0 - 1e-6 && q < t1 + S - 1e-6;
    m.svg.style.display = on ? 'block' : 'none';
    if (!on) return;
    const pl = place || m.o;
    m.g.setAttribute('transform', `translate(${(pl.x || 0).toFixed(2)},${(pl.y || 0).toFixed(2)}) rotate(${(pl.rot || 0).toFixed(2)})`);
    const v = k % 3, fade = q >= t1 - 1e-6 ? 0.45 : 1;
    const prog = Math.min(1, (Math.round((q - t0) / S) + 1) / Math.max(1, Math.round(draw / S)));
    m.variants.forEach((ps, vi) => ps.forEach((p, si) => {
      const L = m.lens[vi][si], tot = m.lens[vi].reduce((a, b) => a + b, 0);
      const before = m.lens[vi].slice(0, si).reduce((a, b) => a + b, 0), shown = Math.max(0, Math.min(L, prog * tot - before));
      p.style.display = vi === v && shown > 0.5 ? 'inline' : 'none';
      p.style.strokeDasharray = `${L.toFixed(1)} ${L.toFixed(1)}`;
      p.style.strokeDashoffset = (L - shown).toFixed(1);
      p.style.opacity = fade;
    }));
    m.svg.style.setProperty('--k', `"${k},${(pl.x || 0).toFixed(1)},${(pl.y || 0).toFixed(1)}"`);
  };
  window.Paper = Paper;
})();
