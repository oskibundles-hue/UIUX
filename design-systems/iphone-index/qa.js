// qa.js <page.html> : the layout check every page in this layout gets before it is published.
// For each tab at 390 px light and dark, 360 px and 1280 px, with every row opened: no sideways scroll, no clipped
// text, no overlapping siblings in a row, nothing off screen, the footer clear of the tab bar, and no script errors.
// Screenshots of each tab land next to the page as qa-<size>-<tab>.png. Needs Node with Playwright.
const { chromium } = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'example.html');
const wrapped = file.replace(/\.html$/, '.qa-wrapped.html');
// the artifact host wraps a published page in this skeleton; test it the same way
fs.writeFileSync(wrapped, `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0}[hidden]{display:none!important}</style></head><body>${fs.readFileSync(file, 'utf8')}</body></html>`);
(async () => {
  const b = await chromium.launch(); let bad = 0;
  for (const [w, h, scheme, tag] of [[390, 844, 'light', 'phone'], [390, 844, 'dark', 'phone-dark'], [360, 780, 'light', 'small'], [1280, 900, 'light', 'desktop']]) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: scheme, deviceScaleFactor: w < 500 ? 2 : 1 });
    const p = await ctx.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.goto('file://' + wrapped); await p.waitForTimeout(300);
    for (const tab of await p.$$eval('.tab[data-tab]', ts => ts.map(t => t.dataset.tab))) {
      await p.click(`.tab[data-tab="${tab}"]`); await p.waitForTimeout(120);
      const r = await p.evaluate(() => {
        const vis = el => { const s = getComputedStyle(el); return s.display !== 'none' && s.visibility !== 'hidden' && el.getClientRects().length; };
        const ds = [...document.querySelectorAll('.panel:not([hidden]) details')]; ds.forEach(d => { d.open = true; });
        const out = { hscroll: document.documentElement.scrollWidth - document.documentElement.clientWidth, problems: [] };
        for (const el of document.querySelectorAll('.panel:not([hidden]) *')) {
          if (!vis(el) || el.closest('.chips') || el.classList.contains('dz-pv') || el.closest('.rowlink')) continue;
          const cs = getComputedStyle(el), rc = el.getBoundingClientRect();
          if (el.scrollWidth > el.clientWidth + 1 && cs.overflowX !== 'visible' && cs.overflowX !== 'auto') out.problems.push('clipped: ' + el.textContent.slice(0, 40));
          if (rc.right > innerWidth + 0.5 || rc.left < -0.5) out.problems.push('off screen: ' + el.textContent.slice(0, 40));
        }
        for (const row of document.querySelectorAll('.panel:not([hidden]) :is(.cell, .row-main, summary, .row-top, .dz-title, .gh)')) {
          if (!vis(row)) continue;
          const k = [...row.children].filter(vis).map(c => c.getBoundingClientRect());
          for (let i = 0; i < k.length; i++) for (let j = i + 1; j < k.length; j++) {
            const ox = Math.min(k[i].right, k[j].right) - Math.max(k[i].left, k[j].left);
            const oy = Math.min(k[i].bottom, k[j].bottom) - Math.max(k[i].top, k[j].top);
            if (ox > 1 && oy > 1) out.problems.push('overlap in: ' + row.textContent.slice(0, 40));
          }
        }
        ds.forEach(d => { d.open = false; });
        scrollTo(0, document.body.scrollHeight);
        const last = [...document.querySelectorAll('.foot > *')].filter(vis).pop();
        if (last && last.getBoundingClientRect().bottom > document.querySelector('.tabbar').getBoundingClientRect().top) out.problems.push('footer under the tab bar');
        scrollTo(0, 0);
        return out;
      });
      const n = r.problems.length + (r.hscroll > 0 ? 1 : 0); bad += n;
      const why = (r.hscroll > 0 ? `sideways scroll ${r.hscroll}px; ` : '') + [...new Set(r.problems)].slice(0, 4).join('; ');
      console.log(`${tag.padEnd(11)} ${tab.padEnd(7)} ${n ? 'FAIL ' + why : 'ok'}`);
      await p.screenshot({ path: path.join(path.dirname(file), `qa-${tag}-${tab}.png`) });
    }
    if (errs.length) { bad += errs.length; console.log(`${tag}: script errors: ${errs.join('; ')}`); }
    await ctx.close();
  }
  fs.unlinkSync(wrapped); await b.close();
  console.log(bad ? `${bad} problem(s)` : 'all clear'); process.exit(bad ? 1 : 0);
})();
