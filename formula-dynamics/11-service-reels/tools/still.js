// still.js <scene.html[?query]> <out.jpg|png> [w] [h]
// Seeks the scene to window.STILL_T (or 0) and writes one frame: the carousel
// slides are stills cut from the same scene the video renders from.

const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const [, , scene, out, wArg = '1080', hArg = '1350'] = process.argv;
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--font-render-hinting=none', '--force-color-profile=srgb',
           '--disable-lcd-text', '--allow-file-access-from-files'],
  });
  const page = await browser.newPage({ viewport: { width: +wArg, height: +hArg }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });

  const [file, query] = scene.split('?');
  await page.goto('file://' + path.resolve(file) + (query ? '?' + query : ''), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__ready === true, { timeout: 15000 });
  await page.evaluate(() => window.seek(window.STILL_T || 0));
  const jpg = /\.jpe?g$/i.test(out);
  await page.screenshot({ path: out, type: jpg ? 'jpeg' : 'png', ...(jpg ? { quality: 95 } : {}) });
  await browser.close();
  if (errs.length) { console.error('SCENE ERRORS:', errs.slice(0, 5).join(' | ')); process.exit(1); }
  console.log('ok', out);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
