#!/usr/bin/env node
// FD x Asset Appeal VIP card: 5x7 in, two-sided, black tie.
// Reads card.json, writes out/: a print PDF with 0.125 in bleed (page 1 front, page 2 back),
// 300 dpi PNGs of each side, and a trimmed side-by-side preview.
// Usage: node build.js            (any [bracket] left in the copy marks the files DRAFT)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const DIR = __dirname;
const OUT = process.env.OUT || path.join(DIR, 'out');
const A = require('url').pathToFileURL(path.join(DIR, 'assets')).href + '/'; // asset base, so OUT can live anywhere
const spec = JSON.parse(fs.readFileSync(process.env.CARD || path.join(DIR, 'card.json'), 'utf8'));

// ---- page geometry (inches) ----
const TRIM_W = 5, TRIM_H = 7, BLEED = 0.125;
const PAGE_W = TRIM_W + 2 * BLEED, PAGE_H = TRIM_H + 2 * BLEED;
const DPI = 300, CSS_DPI = 96;

const esc0 = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// any [bracketed] copy is a placeholder: shown in red plain type so it can't pass for final copy
const esc = (s) => esc0(s).replace(/\[([^\]]*)\]/g, '<span class="ph">[$1]</span>');

// every string in the spec except _notes; a [bracket] means copy still to confirm
const strings = [];
(function walk(o, k) {
  if (typeof o === 'string') { if (!String(k).startsWith('_')) strings.push(o); return; }
  if (o && typeof o === 'object') for (const [kk, v] of Object.entries(o)) walk(v, kk);
})(spec, '');
const placeholders = strings.filter((s) => /\[[^\]]*\]/.test(s));
const DRAFT = placeholders.length > 0;

const partnerMark = spec.partner.logo
  ? `<img class="partner-logo" style="height:${spec.partner.logo_h || 0.42}in" src="${A}${esc0(spec.partner.logo)}" alt="${esc(spec.partner.name)}">`
  : `<div class="partner-type">${esc(spec.partner.name)}</div>`;
const stripe = (w) => `<div class="stripe" style="width:${w}in"><i style="flex:36.7;background:#FE0F13"></i><i style="flex:21.4;background:#000"></i><i style="flex:19.4;background:#FFF"></i><i style="flex:17;background:#1DB14B"></i><i style="flex:5.5;background:#FFDE00"></i></div>`;
const watermark = DRAFT ? '<div class="wm"><span>DRAFT \u00b7 NOT FOR PRINT</span></div>' : '';

const f = spec.front, b = spec.back;
const roman = ['I', 'II', 'III', 'IV', 'V'];

const html = `<!doctype html>
<html><head><meta charset="utf-8">
<style>
@font-face { font-family: 'Bebas Neue'; src: url('${A}BebasNeue-Regular.ttf'); }
@font-face { font-family: 'Cormorant'; font-weight: 500; font-style: normal; src: url('${A}cormorant-garamond-latin-500-normal.woff2'); }
@font-face { font-family: 'Cormorant'; font-weight: 500; font-style: italic; src: url('${A}cormorant-garamond-latin-500-italic.woff2'); }
@font-face { font-family: 'Cormorant'; font-weight: 600; font-style: normal; src: url('${A}cormorant-garamond-latin-600-normal.woff2'); }
@font-face { font-family: 'Cormorant'; font-weight: 600; font-style: italic; src: url('${A}cormorant-garamond-latin-600-italic.woff2'); }
@page { size: ${PAGE_W}in ${PAGE_H}in; margin: 0; }
:root { --red: #FE0F13; --white: #FFFFFF; --black: #000000; --b: ${BLEED}in; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: var(--black); }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { position: relative; width: ${PAGE_W}in; height: ${PAGE_H}in; background: var(--black);
  color: var(--white); overflow: hidden; page-break-after: always; break-after: page; }
.page:last-child { page-break-after: auto; break-after: auto; }

/* the formal double rule, 0.28 in inside the trim */
.frame { position: absolute; inset: calc(var(--b) + 0.34in); border: 0.75pt solid rgba(255,255,255,.75); }
.frame::after { content: ''; position: absolute; inset: 0.06in; border: 0.75pt solid rgba(255,255,255,.6); }

/* everything sits in a centred column inside the frame */
.col { position: absolute; left: calc(var(--b) + 0.6in); right: calc(var(--b) + 0.6in);
  top: calc(var(--b) + 0.8in); bottom: calc(var(--b) + 0.68in);
  display: flex; flex-direction: column; align-items: center; text-align: center; }
.col > * { flex-shrink: 0; }
.bebas { font-family: 'Bebas Neue', sans-serif; font-weight: 400; }
.serif { font-family: 'Cormorant', serif; }
.tracked { letter-spacing: .38em; padding-left: .38em; } /* pad so tracked caps stay optically centred */
.ph { font-family: 'Bebas Neue', sans-serif; font-style: normal; font-weight: 400; color: var(--red); letter-spacing: .06em; }
.wm { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; pointer-events: none; z-index: 5; }
.wm span { font-family: 'Bebas Neue', sans-serif; font-size: 34pt; letter-spacing: .08em; color: rgba(254,15,19,.42);
  border: 2pt solid rgba(254,15,19,.42); padding: .02in .16in 0; transform: rotate(-32deg); white-space: nowrap; }

/* ---- front ---- */
.fd-logo { width: 1.5in; display: block; }
.assoc { font-family: 'Cormorant', serif; font-style: italic; font-weight: 500; font-size: 10.5pt;
  opacity: .78; margin-top: .3in; letter-spacing: .02em; }
.partner-type { font-family: 'Cormorant', serif; font-weight: 600; font-size: 14.5pt;
  letter-spacing: .34em; padding-left: .34em; margin-top: .05in; }
.partner-logo { display: block; width: auto; margin-top: .1in; }
.kicker { font-size: 9.5pt; opacity: .8; margin-top: auto; }
.headline { margin-top: .12in; line-height: .86; }
.headline .big { font-size: 74pt; letter-spacing: .015em; display: block; white-space: nowrap; }
.headline .mid { font-family: 'Cormorant', serif; font-style: italic; font-weight: 500;
  font-size: 30pt; display: block; line-height: 1; margin: .02in 0 .05in; }
.dot { color: var(--red); }
.stripe { height: .034in; display: flex; }
.front .stripe { margin-top: .22in; }
.stripe i { display: block; height: 100%; }
.title { font-size: 15pt; margin-top: .18in; }
.sub { font-family: 'Cormorant', serif; font-style: italic; font-weight: 500; font-size: 12pt;
  opacity: .82; margin-top: .05in; }
.foot { font-size: 8.5pt; opacity: .7; margin-top: auto; }

/* ---- back ---- */
.fd-foot { width: 1.05in; display: block; margin-top: .27in; }
.b-title { font-size: 36pt; letter-spacing: .06em; padding-left: .06em; margin-top: .2in; line-height: 1; }
.b-sub { font-family: 'Cormorant', serif; font-style: italic; font-weight: 500; font-size: 15pt;
  margin-top: .04in; opacity: .9; }
.rule { width: .5in; height: 0; border-top: .5pt solid rgba(255,255,255,.45); margin: .2in 0 .04in; }
.offers { width: 100%; display: flex; flex-direction: column; align-items: center; }
.offer { padding: .085in 0 .075in; width: 100%; display: flex; flex-direction: column; align-items: center; }
.offer + .offer { border-top: .5pt solid rgba(255,255,255,.3); }
.num { font-family: 'Cormorant', serif; font-style: italic; font-weight: 600; font-size: 11.5pt; opacity: .7; }
.o-title { font-size: 21pt; letter-spacing: .07em; padding-left: .07em; line-height: 1.02; margin-top: .02in; }
.o-detail { font-family: 'Cormorant', serif; font-style: italic; font-weight: 500; font-size: 12.5pt;
  opacity: .85; margin-top: .03in; }
.terms { font-family: 'Cormorant', serif; font-style: italic; font-weight: 500; font-size: 10pt;
  opacity: .72; margin-top: auto; }
.contact { font-size: 8.3pt; letter-spacing: .14em; padding-left: .14em; opacity: .85; margin-top: .14in; line-height: 1.5; }
.pair { font-size: 8pt; opacity: .68; margin-top: .1in; }
</style></head><body>

<section class="page front">
  <div class="frame"></div>${watermark}
  <div class="col">
    <img class="fd-logo" src="${A}fd-primary-horizontal--white.svg" alt="Formula Dynamics Performance">
    <div class="assoc">in association with</div>
    ${partnerMark}
    <div class="kicker bebas tracked">${esc(f.kicker)}</div>
    <div class="headline bebas">
      <span class="big">${esc(f.line1)}</span>
      <span class="mid">${esc(f.line2)}</span>
      <span class="big">${esc(f.line3)}<span class="dot">.</span></span>
    </div>
    ${stripe(1.25)}
    <div class="title bebas tracked">${esc(f.title)}</div>
    <div class="sub">${esc(f.sub)}</div>
    <div class="foot bebas tracked">${esc(f.foot)}</div>
  </div>
</section>

<section class="page back">
  <div class="frame"></div>${watermark}
  <div class="col">
    ${stripe(1.0)}
    <div class="b-title bebas">${esc(b.title)}</div>
    <div class="b-sub">${esc(b.sub)}</div>
    <div class="rule"></div>
    <div class="offers">
      ${b.offers.map((o, i) => `<div class="offer"><div class="num">${roman[i] || i + 1}.</div><div class="o-title bebas">${esc(o.title)}</div><div class="o-detail">${esc(o.detail)}</div></div>`).join('\n      ')}
    </div>
    <div class="terms">${esc(b.terms)}</div>
    <div class="contact bebas">${esc(b.contact1)}<br>${esc(b.contact2)}</div>
    <img class="fd-foot" src="${A}fd-primary-horizontal--white.svg" alt="Formula Dynamics Performance">
  </div>
</section>
</body></html>`;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const htmlPath = path.join(OUT, 'card.html');
  fs.writeFileSync(htmlPath, html);
  const tag = DRAFT ? '_DRAFT' : '';
  const base = `FD-x-AssetAppeal_VIP-card_5x7`;

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: Math.round(PAGE_W * CSS_DPI), height: Math.round(PAGE_H * CSS_DPI) },
    deviceScaleFactor: DPI / CSS_DPI,
  });
  const page = await ctx.newPage();
  await page.goto('file://' + htmlPath);
  await page.evaluate(() => document.fonts.ready);
  // headline: the widest .big line fills 85% of the column; both lines share that size
  await page.evaluate(() => {
    const col = document.querySelector('.front .col').getBoundingClientRect().width;
    const bigs = [...document.querySelectorAll('.headline .big')];
    let pt = 90;
    const set = () => bigs.forEach((b) => (b.style.fontSize = pt + 'pt'));
    set();
    while (pt > 30 && Math.max(...bigs.map((b) => b.scrollWidth)) > col * 0.85) { pt -= 0.5; set(); }
    document.body.dataset.headlinePt = pt;
  });
  const headlinePt = await page.evaluate(() => document.body.dataset.headlinePt);
  const fontsOk = await page.evaluate(() => ['12px "Bebas Neue"', '600 12px "Cormorant"', 'italic 500 12px "Cormorant"', 'italic 600 12px "Cormorant"'].map((f) => [f, document.fonts.check(f)]));

  // overflow check: no line of copy may run outside the centred column
  const overflow = await page.evaluate(() => {
    const bad = [];
    document.querySelectorAll('.col').forEach((col, side) => {
      const c = col.getBoundingClientRect();
      col.querySelectorAll('*').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width && (r.left < c.left - 0.5 || r.right > c.right + 0.5 || r.bottom > c.bottom + 0.5))
          bad.push(`${side ? 'back' : 'front'}: ${el.className || el.tagName} "${(el.textContent || '').trim().slice(0, 30)}"`);
      });
      if (col.scrollHeight > col.clientHeight + 1) bad.push(`${side ? 'back' : 'front'}: column taller than the frame`);
    });
    return bad;
  });

  const pdfPath = path.join(OUT, `${base}_print-bleed${tag}.pdf`);
  await page.pdf({ path: pdfPath, width: `${PAGE_W}in`, height: `${PAGE_H}in`, printBackground: true, preferCSSPageSize: true });

  const b9 = BLEED * 72;
  const PY_BOXES = [
    'import sys, pypdf',
    'r = pypdf.PdfReader(sys.argv[1]); w = pypdf.PdfWriter()',
    'for pg in r.pages:',
    '    W, H = float(pg.mediabox.width), float(pg.mediabox.height)',
    `    pg.trimbox = pypdf.generic.RectangleObject([${b9}, ${b9}, W - ${b9}, H - ${b9}])`,
    '    pg.bleedbox = pypdf.generic.RectangleObject([0, 0, W, H])',
    '    w.add_page(pg)',
    'w.write(sys.argv[1])',
  ].join('\n');
  require('child_process').execFileSync('python3', ['-c', PY_BOXES, pdfPath]);

  const sides = await page.$$('section.page');
  const pngs = [];
  for (const [i, name] of ['front', 'back'].entries()) {
    const p = path.join(OUT, `${base}_${name}_300dpi${tag}.png`);
    await sides[i].screenshot({ path: p });
    pngs.push(p);
  }

  // the review preview leaves the DRAFT stamp off (placeholders stay red); the print files keep it
  await page.addStyleTag({ content: '.wm { display: none !important; }' });
  const clean = [];
  for (const [i, name] of ['front', 'back'].entries()) {
    const p = path.join(OUT, `.clean_${name}.png`);
    await sides[i].screenshot({ path: p });
    clean.push(p);
  }

  // trimmed side-by-side preview on a neutral grey, for review only
  const prev = await browser.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 2 });
  const img = (p) => 'data:image/png;base64,' + fs.readFileSync(p).toString('base64');
  const pct = (BLEED / PAGE_W) * 100, pctH = (BLEED / PAGE_H) * 100;
  await prev.setContent(`<body style="margin:0;background:#8d8d8d;display:flex;gap:60px;justify-content:center;align-items:center;height:900px">
    ${clean.map((p) => `<div style="width:500px;height:700px;overflow:hidden;position:relative;box-shadow:0 18px 40px rgba(0,0,0,.45)">
      <img src="${img(p)}" style="position:absolute;width:${100 / (TRIM_W / PAGE_W)}%;left:-${(pct / (TRIM_W / PAGE_W)).toFixed(4)}%;top:-${(pctH / (TRIM_H / PAGE_H)).toFixed(4)}%"></div>`).join('')}
  </body>`);
  await prev.waitForTimeout(150);
  const prevPath = path.join(OUT, `${base}_preview${tag}.png`);
  await prev.screenshot({ path: prevPath });
  clean.forEach((p) => fs.unlinkSync(p));
  await browser.close();
  const PY_DPI = ['import sys', 'from PIL import Image', 'for p in sys.argv[1:]:',
    '    im = Image.open(p); im.load(); im.save(p, dpi=(300, 300))'].join('\n');
  require('child_process').execFileSync('python3', ['-c', PY_DPI, ...pngs]);

  console.log('fonts:', JSON.stringify(fontsOk), '| headline', headlinePt + 'pt');
  console.log('overflow:', overflow.length ? overflow.join(' | ') : 'none');
  console.log(DRAFT ? `DRAFT: ${placeholders.length} line(s) still to confirm: ${placeholders.join(' | ')}` : 'FINAL: no placeholders left');
  for (const p of [pdfPath, ...pngs, prevPath]) console.log('wrote', path.relative(DIR, p));
})();
