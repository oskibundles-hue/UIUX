// shot.js <url-or-file> <out.png> [w] [h] [dpr]
const { chromium } = require('playwright-core');
const path = require('path');

(async () => {
  const [, , src, out, w = '1080', h = '1920', dpr = '1'] = process.argv;
  const b = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--font-render-hinting=none', '--force-color-profile=srgb'],
  });
  const p = await b.newPage({
    viewport: { width: +w, height: +h },
    deviceScaleFactor: +dpr,
  });
  const url = src.startsWith('http') || src.startsWith('file:')
    ? src
    : 'file://' + path.resolve(src);
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts && document.fonts.ready);
  await p.screenshot({ path: out });
  await b.close();
  console.log('shot ->', out);
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
