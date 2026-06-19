const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 3 });
  await page.goto('file://' + path.join(__dirname, 'overlay.html'));
  // give web fonts a moment
  try { await page.evaluate(() => document.fonts.ready); } catch {}
  await page.waitForTimeout(500);

  const out = __dirname;

  // Full preview sheet (with checkerboard, for reference)
  await page.screenshot({ path: path.join(out, 'preview-sheet.png'), fullPage: true });

  // Each .row exported individually with a TRANSPARENT background
  const rows = await page.$$('.row');
  const names = ['hero-bar', 'handle-youtube', 'handle-twitch', 'handle-instagram', 'url-twitch', 'url-youtube'];
  for (let i = 0; i < rows.length; i++) {
    const label = names[i] || `element-${i}`;
    await rows[i].screenshot({ path: path.join(out, `${label}.png`), omitBackground: true });
  }

  await browser.close();
  console.log('rendered', rows.length, 'overlay elements + preview sheet');
})();
