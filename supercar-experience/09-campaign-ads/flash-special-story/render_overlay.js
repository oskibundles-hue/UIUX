// Render the motion-graphics layer of story.html to transparent PNGs.
//   node render_overlay.js [outDir=.work/overlay] [fps=24] [frames=372] [workers=4]
//   node render_overlay.js --times 0,1,2.5 outDir     (named by time, for spot checks)
// Each frame: renderAt(i / fps), then a screenshot with omitBackground so only the graphics carry alpha.
const path = require('path');
const fs = require('fs');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
process.env.PLAYWRIGHT_BROWSERS_PATH = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';

(async () => {
  const args = process.argv.slice(2);
  let jobs;                                    // [{t, file}]
  let outDir;
  if (args[0] === '--times') {
    outDir = path.resolve(args[2] || path.join(__dirname, '.work/overlay-stills'));
    jobs = args[1].split(',').map(Number).map(t => ({ t, file: path.join(outDir, `t${t.toFixed(3)}.png`) }));
  } else {
    outDir = path.resolve(args[0] || path.join(__dirname, '.work/overlay'));
    const fps = +(args[1] || 24), n = +(args[2] || 372);
    jobs = Array.from({ length: n }, (_, i) => ({ t: i / fps, file: path.join(outDir, String(i).padStart(5, '0') + '.png') }));
  }
  fs.mkdirSync(outDir, { recursive: true });
  const workers = Math.max(1, Math.min(+(args[3] || 4), jobs.length));
  const browser = await chromium.launch();
  const url = 'file://' + path.join(__dirname, 'story.html');
  const t0 = Date.now();
  await Promise.all(Array.from({ length: workers }, async (_, w) => {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    page.on('pageerror', e => { console.error('pageerror', e.message); process.exitCode = 1; });
    await page.goto(url);
    await page.evaluate(() => window.storyReady);
    await page.evaluate(() => document.fonts.ready);
    for (let i = w; i < jobs.length; i += workers) {
      await page.evaluate(t => window.renderAt(t), jobs[i].t);
      await page.screenshot({ path: jobs[i].file, omitBackground: true });
    }
    await page.close();
  }));
  await browser.close();
  console.log(`overlay: ${jobs.length} frames -> ${outDir} in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
})().catch(e => { console.error(e); process.exit(1); });
