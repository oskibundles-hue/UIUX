/* swapcheck.js: QA for hard state swaps in the layer (no Playwright install; uses the preinstalled module).
 * For every output frame it evaluates the page at each motion-blur sample time exactly as kcapture.js does
 * (KT_PLAN spans, samples centred on the frame time) and reads the discrete text state of:
 *   H1 captions (which page(s) are on screen), C1 convoy label (which make / LOCK LOST is shown), D1 clock (HH:MM).
 * A frame fails if two caption pages are visible at once, or if its samples show two different non-empty texts for
 * any of these (an element fading in or out inside a frame is not a swap).
 * Usage: node lib/swapcheck.js story.html out.json [nframes]
 */
const { chromium } = require('./playwright');  // resolves Playwright on this machine (lib/playwright.js)
const path = require('path'); const fs = require('fs');
(async () => {
  const [page, out, nfArg] = process.argv.slice(2);
  const FPS = 30000 / 1001;
  const b = await chromium.launch({ args: ['--disable-gpu-vsync'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('pageerror', e => { console.error('pageerror', e.message); process.exit(2); });
  await pg.goto('file://' + path.resolve(page));
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  const res = await pg.evaluate(([FPS, nfArg]) => {
    const plan = window.KT_PLAN || {}, NF = nfArg ? +nfArg : Math.round(window.SCENE.dur * FPS);
    const planAt = t => { let k = plan.k || 10, sh = plan.shutter || 180;
      for (const s of plan.spans || []) if (t >= s.a && t <= s.b) { k = s.k || k; sh = s.shutter || sh; } return { k, sh }; };
    const host = code => [...document.getElementById('stage').children].filter(e => e.dataset.code === code);
    const vis = e => { for (let m = e; m && m.id !== 'stage'; m = m.parentElement) if (m.style.display === 'none') return false; return true; };
    const H1 = host('H1')[0], C1 = host('C1'), D1 = [...document.getElementById('stage').children].filter(e => e.dataset.type === 'clockStamp');
    const state = () => {
      const pages = H1 ? [...H1.children].filter(vis).map(e => e.textContent) : [];
      // C1 label: the visible text rows of the label box (makes / LOCK LOST), not the counter strip
      let lab = '';
      C1.forEach(r => r.querySelectorAll('.beb').forEach(n => { if (vis(n) && n.closest('[style*="clip-path"]')) lab += n.textContent + '|'; }));
      let clk = '';
      D1.forEach(r => { if (vis(r)) r.querySelectorAll('.beb').forEach(n => { if (vis(n)) clk += n.textContent; }); });
      return { pages, lab, clk: clk.slice(0, 5) };
    };
    const bad = [], swaps = [];
    let prevPages = null;
    for (let n = 0; n < NF; n++) {
      const t = n / FPS, { k, sh } = planAt(t), span = (sh / 360) / FPS;
      const ts = k > 1 ? Array.from({ length: k }, (_, j) => t + ((j + .5) / k - .5) * span) : [t];
      const st = ts.map(ti => { window.renderAt(ti); return state(); });
      const key = s => JSON.stringify(s);
      const two = st.some(s => s.pages.length > 1);
      // a swap = two different non-empty texts among one frame's samples (an element fading in or out is not a swap)
      const multi = f => new Set(st.map(s => JSON.stringify(s[f])).filter(v => v !== '""' && v !== '[]')).size > 1;
      const disagree = multi('pages') || multi('lab') || multi('clk');
      window.renderAt(t); const s0 = state();
      if (prevPages !== null && JSON.stringify(s0.pages) !== prevPages) swaps.push({ n, t: +t.toFixed(3), k: ts.length, pages: s0.pages.map(x => x.slice(0, 40)) });
      prevPages = JSON.stringify(s0.pages);
      if (two || disagree) bad.push({ n, t: +t.toFixed(3), k: ts.length, two, states: [...new Set(st.map(key))].slice(0, 3) });
    }
    return { NF, bad, swaps };
  }, [FPS, nfArg]);
  fs.writeFileSync(out, JSON.stringify(res, null, 1));
  console.log(`frames ${res.NF}  caption page changes ${res.swaps.length}  bad frames ${res.bad.length}`);
  await b.close();
})();
