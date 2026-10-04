// visible text boxes per frame vs the safe text zone (x 54-907, y 285-1536); prints the worst extents per direction
const { chromium } = require(process.env.PW_MODULE); const path = require('path');
(async () => {
  const b = await chromium.launch();
  for (const d of (process.env.PAGES || 'A,B,C').split(',')) {
    const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
    await pg.goto("file://" + path.resolve(d.endsWith(".html") ? d : `dir${d}.html`)); await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
    const r = await pg.evaluate(() => {
      const ext = { x0: 1e9, x1: -1e9, y0: 1e9, y1: -1e9 }, bad = [];
      const NFR = window.SCENE && window.SCENE.nf ? window.SCENE.nf : 90; for (let i = 0; i < NFR; i += 0.5) {
        window.renderAt(i * 1001 / 30000);
        const nodes = [...document.querySelectorAll('.beb,.mono,.ex,.kk')].filter(n => n.textContent.trim());
        for (const n of nodes) {
          let op = 1, m = n; while (m && m !== document.body) { const cs = getComputedStyle(m); op *= +cs.opacity; if (cs.display === 'none') op = 0; m = m.parentElement; }
          if (op < 0.05) continue;
          const q = n.getBoundingClientRect(); if (q.width < 1) continue;
          ext.x0 = Math.min(ext.x0, q.left); ext.x1 = Math.max(ext.x1, q.right); ext.y0 = Math.min(ext.y0, q.top); ext.y1 = Math.max(ext.y1, q.bottom);
          if (q.left < 54 || q.right > 907 || q.top < 285 || q.bottom > 1536) bad.push([i, n.textContent.slice(0, 18), Math.round(q.left), Math.round(q.right), Math.round(q.top), Math.round(q.bottom), +op.toFixed(2)]);
        }
      }
      const uniq = {}; for (const b of bad) { const k = b[1]; if (!uniq[k]) uniq[k] = []; uniq[k].push(b[0]); } return { ext, nbad: bad.length, frames: uniq, worst: bad.slice(0, 6) };
    });
    console.log(d, JSON.stringify(r)); await pg.close();
  }
  await b.close();
})();
