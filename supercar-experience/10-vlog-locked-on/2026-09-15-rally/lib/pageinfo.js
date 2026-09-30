// pageinfo.js -- load story.html headless and print its timing tables (WINDOWS, TIMES, KT_PLAN) as JSON.
//   node lib/pageinfo.js story.html > .work/page.json
//   node lib/pageinfo.js story.html --audit 4.9,16.5,...   (ink rects of visible text at those times)
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
(async () => {
  const [page, flag, arg] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('pageerror', e => { console.error('pageerror', e.message); process.exit(2); });
  await pg.goto('file://' + path.resolve(page));
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  let out;
  if (flag === '--audit') out = await pg.evaluate(ts => ts.map(t => ({ t, ink: window.inkAudit(t) })), arg.split(',').map(Number));
  else out = await pg.evaluate(() => ({ WINDOWS: window.WINDOWS, TIMES: window.TIMES, KT_PLAN: window.KT_PLAN }));
  process.stdout.write(JSON.stringify(out));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
