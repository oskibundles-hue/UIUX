// hud_still.js <page.html> <t> <frame.png> <out.png> -- one frame of a HUD layer page drawn over a still of the footage,
// for theme mockups. The footage sits behind the page, so a glass theme's backdrop blur has something to blur.
const { chromium } = require(process.env.PW_MODULE || '/opt/node22/lib/node_modules/playwright');
const path = require('path');
(async () => {
  const [page, t, bg, out] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--disable-lcd-text'], ...(process.env.PW_EXEC ? { executablePath: process.env.PW_EXEC } : {}) });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto('file://' + path.resolve(page));
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  await pg.evaluate(async src => {
    const im = new Image(); im.src = src;
    im.style.cssText = 'position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:0';
    document.body.insertBefore(im, document.body.firstChild); await im.decode();
  }, 'file://' + path.resolve(bg));
  await pg.evaluate(t => window.renderAt(t), +t);
  await pg.waitForTimeout(120);
  await pg.screenshot({ path: out });
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
