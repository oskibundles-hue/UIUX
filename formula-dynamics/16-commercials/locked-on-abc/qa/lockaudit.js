// every lock invisible on every sub-frame sample outside its own shot (lo.html window.lockAudit)
const { chromium } = require(process.env.PW_MODULE); const path = require('path');
(async () => { const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto("file://" + path.resolve(process.argv[2] || 'lo.html')); await pg.waitForFunction(() => window.__ktReady === true);
  const r = await pg.evaluate(() => ({ bad: window.lockAudit(), locks: locks.map(L => [L.o.shot, L.o.g0, L.o.g1, +(L.o.ta * 29.97002997).toFixed(1), +((L.o.tx + 0.3) * 29.97002997).toFixed(1)]) }));
  console.log(JSON.stringify(r)); await b.close(); })();
