/* audit.js -- loads front.html, prints ink rects of visible text lines at the given times (QA: safe zone). */
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  const errs = []; pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto('file://' + path.resolve(process.argv[2]));
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 30000 }).catch(e => errs.push('not ready'));
  const ts = process.argv[3].split(',').map(Number); const res = {};
  for (const t of ts) res[t] = await pg.evaluate(t => window.inkAudit(t), t);
  console.log(JSON.stringify({ errs, res }));
  await b.close();
})();
