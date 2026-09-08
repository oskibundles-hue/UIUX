// Exports each overlay twice: a transparent PNG for compositing over footage,
// and a "on plate" PNG so the look can be judged.
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const PARTS = ['ov-bug', 'ov-handle', 'ov-lower', 'ov-spec', 'ov-end'];
const OUT = path.resolve(__dirname, 'out/overlays');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--font-render-hinting=none', '--force-color-profile=srgb',
           '--allow-file-access-from-files'],
  });
  // 2x for a 2160x3840 master, matching the 4K reels already in the library
  const page = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(__dirname, 'overlays.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);

  for (const id of PARTS) {
    const el = page.locator('#' + id);
    await el.screenshot({ path: `${OUT}/${id}-plate.png` });
    await page.evaluate(i => document.getElementById(i).setAttribute('data-alpha', '1'), id);
    await el.screenshot({ path: `${OUT}/${id}-alpha.png`, omitBackground: true });
    console.log('  ', id);
  }

  // contact sheet for review
  await page.setViewportSize({ width: 1080 * 5, height: 1920 });
  await page.evaluate(() => { document.querySelector('.sheet').style.flexWrap = 'nowrap'; });
  await page.screenshot({ path: `${OUT}/_contact-sheet.png`, fullPage: true, scale: 'css' });
  await b.close();
  console.log('overlays ->', OUT);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
