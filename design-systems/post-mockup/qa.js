// qa.js <page.html> : the check every post mockup gets before it is published.
// For each version at 390 px, 360 px and 1280 px: no sideways scroll, nothing clipped or off screen outside the
// carousel track, one posting-order row per item, the counter and the next button working, a caption, and no script
// errors. Unless POST.demo is on, every file the page points at must sit next to it ({version id}/{f}, the avatar).
// Screenshots land next to the page as qa-<size>-<version>.png. Needs Node with Playwright.
const { chromium } = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'template.html');
const dir = path.dirname(file);
const wrapped = file.replace(/\.html$/, '.qa-wrapped.html');
// the artifact host wraps a published page in this skeleton; test it the same way
fs.writeFileSync(wrapped, `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}body{margin:0}[hidden]{display:none!important}</style></head><body>${fs.readFileSync(file, 'utf8')}</body></html>`);
const media = /\.(mp4|jpe?g|png|webm)\b|net::|ERR_FILE_NOT_FOUND|Failed to load resource/;
(async () => {
  const b = await chromium.launch({ executablePath: fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined })
    .catch(() => chromium.launch());
  let bad = 0, checkedFiles = false;
  for (const [w, h, tag] of [[390, 844, 'phone'], [360, 780, 'small'], [1280, 900, 'desktop']]) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: w < 500 ? 2 : 1 });
    const p = await ctx.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    p.on('console', m => { if (m.type() === 'error' && !media.test(m.text())) errs.push(m.text()); });
    await p.goto('file://' + wrapped); await p.waitForTimeout(400);
    const post = await p.evaluate(() => JSON.parse(JSON.stringify(POST)));
    if (!checkedFiles) {
      checkedFiles = true;
      if (!post.demo) {
        const want = post.variants.flatMap(v => post.items.map(it => path.join(v.id, it.f)));
        if (post.avatar) want.push(post.avatar);
        const missing = want.filter(f => !fs.existsSync(path.join(dir, f)));
        if (missing.length) { bad++; console.log('MISSING FILES next to the page: ' + missing.join(', ')); }
      }
    }
    for (let k = 0; k < post.variants.length; k++) {
      const v = post.variants[k];
      if (post.variants.length > 1) { await p.click(`#seg button[data-k="${k}"]`); await p.waitForTimeout(150); }
      const problems = [];
      const r = await p.evaluate(() => {
        const vis = el => { const s = getComputedStyle(el); return s.display !== 'none' && s.visibility !== 'hidden' && el.getClientRects().length; };
        const out = { hscroll: document.documentElement.scrollWidth - document.documentElement.clientWidth, problems: [],
          rows: document.querySelectorAll('#order li').length, count: document.getElementById('count').textContent,
          cap: document.getElementById('captxt').textContent.trim().length };
        for (const el of document.querySelectorAll('.wrap *')) {
          if (!vis(el) || el.closest('.track')) continue;
          const cs = getComputedStyle(el), rc = el.getBoundingClientRect();
          if (el.scrollWidth > el.clientWidth + 1 && !['visible', 'auto', 'scroll'].includes(cs.overflowX)) out.problems.push('clipped: ' + el.className + ' ' + el.textContent.slice(0, 40));
          if (rc.right > innerWidth + 0.5 || rc.left < -0.5) out.problems.push('off screen: ' + el.className + ' ' + el.textContent.slice(0, 40));
        }
        return out;
      });
      if (r.hscroll > 0) problems.push(`page scrolls sideways by ${r.hscroll}px`);
      if (r.rows !== post.items.length) problems.push(`posting order shows ${r.rows} rows for ${post.items.length} items`);
      if (r.cap === 0) problems.push('empty caption');
      problems.push(...r.problems);
      if (post.items.length > 1) {
        if (r.count !== `1/${post.items.length}`) problems.push(`counter reads "${r.count}" on the first slide`);
        await p.click('#next'); await p.waitForTimeout(500);
        const c2 = await p.textContent('#count');
        if (c2 !== `2/${post.items.length}`) problems.push(`counter reads "${c2}" after Next`);
        await p.click('#order li:first-child button[data-i]'); await p.waitForTimeout(500);
      }
      await p.screenshot({ path: path.join(dir, `qa-${tag}-${v.id}.png`), fullPage: true });
      if (problems.length) { bad++; console.log(`${tag} ${w}px ${v.id}: ` + [...new Set(problems)].join(' | ')); }
      else console.log(`${tag} ${w}px ${v.id}: ok`);
    }
    if (errs.length) { bad++; console.log(`${tag}: script errors: ` + errs.join(' | ')); }
    await ctx.close();
  }
  await b.close();
  fs.unlinkSync(wrapped);
  console.log(bad ? `${bad} problem(s)` : 'all clear');
  process.exit(bad ? 1 : 0);
})();
