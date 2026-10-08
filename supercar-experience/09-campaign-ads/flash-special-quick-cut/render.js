const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => {
  const [,, mode, outDir, fpsOrTimes] = process.argv;
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await pg.goto('file://' + __dirname + '/' + (process.env.PAGE||'story.html'));
  await pg.evaluate(() => document.fonts.ready);
  await pg.waitForTimeout(300);
  const times = mode === 'seq' ? Array.from({ length: Math.round(15 * +fpsOrTimes) }, (_, i) => i / +fpsOrTimes) : fpsOrTimes.split(',').map(Number);
  for (let i = 0; i < times.length; i++) {
    await pg.evaluate(t => window.renderAt(t), times[i]);
    await pg.screenshot({ path: `${outDir}/${mode === 'seq' ? String(i).padStart(5, '0') : times[i].toFixed(2)}.png`, omitBackground: true });
  }
  await b.close();
})();
