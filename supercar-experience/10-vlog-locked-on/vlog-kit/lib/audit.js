// audit.js -- load kit.html headless and return the ink rects of every visible text line at the given times.
//   node lib/audit.js kit.html times.json out.json
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path'); const fs = require('fs');
(async () => {
  const [page, tf, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('pageerror', e => { console.error('pageerror', e.message); process.exit(2); });
  await pg.goto('file://' + path.resolve(page));
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  const ts = JSON.parse(fs.readFileSync(tf, 'utf8'));
  const res = await pg.evaluate(ts => ts.map(t => ({ t, ink: window.inkAudit(t) })), ts);
  fs.writeFileSync(out, JSON.stringify(res));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
