#!/usr/bin/env node
// Render still frames (and an optional labelled contact sheet) for visual QA.
//
//   node tools/stills.mjs --times 0.5,1.2,b3.1,f225          explicit times (s | fNNN frame | bBAR.BEAT.SIXTEENTH)
//   node tools/stills.mjs --scene s03-shapes --count 12        evenly sampled across a scene's window (+ its last frame)
//   node tools/stills.mjs --from 3.75 --to 5.625 --count 16    evenly sampled across a range
//   node tools/stills.mjs --from 3.75 --to 4.2 --every 1       every frame in a range (motion check)
//   options: --only s03-shapes[,s04-x]  isolate scenes     --out DIR (default .cache/stills/<name>)
//            --sheet  build contact sheet (sheet.png)      --cols 4      --label  bake debug timecode into stills
//            --name NAME  output folder name               --no-stills  only keep the sheet
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, FPS, W, H, serve, launchBrowser, openReel, parseArgs, parseTime } from './common.mjs';

const a = parseArgs();
const srv = await serve();
const browser = await launchBrowser();
let exitCode = 0;
try {
  const q = [];
  if (a.only) q.push('only=' + encodeURIComponent(a.only));
  if (a.label) q.push('debug');
  const page = await openReel(browser, srv.url, q.join('&'));
  const cdp = await page.context().newCDPSession(page);
  const windows = await page.evaluate(() => R.scenes.map((s) => ({ id: s.id, start: s.start, end: s.end })));

  let times = [];
  if (a.times) times = String(a.times).split(',').map(parseTime);
  else {
    let from = 0, to = 15;
    if (a.scene) {
      const sc = windows.find((w) => w.id === a.scene || w.id.startsWith(a.scene));
      if (!sc) throw new Error(`scene ${a.scene} not found. Known: ${windows.map((w) => w.id).join(', ')}`);
      from = sc.start; to = sc.end - 1 / FPS;
    }
    if (a.from !== undefined) from = parseTime(a.from);
    if (a.to !== undefined) to = parseTime(a.to);
    if (a.every) {
      const stepF = Number(a.every) || 1;
      for (let f = Math.ceil(from * FPS - 1e-6); f <= Math.floor(to * FPS + 1e-6); f += stepF) times.push(f / FPS);
    } else {
      const n = Number(a.count || 12);
      for (let i = 0; i < n; i++) times.push(from + ((to - from) * i) / Math.max(1, n - 1));
    }
  }
  // Snap to exact frames (what the final render will show)
  times = times.map((t) => Math.round(t * FPS) / FPS);

  const name = a.name || (a.scene ? `scene-${a.scene}` : a.only ? `only-${a.only}` : 'stills');
  const out = path.resolve(a.out || path.join(ROOT, '.cache', 'stills', name));
  fs.mkdirSync(out, { recursive: true });
  for (const f of fs.readdirSync(out)) if (f.endsWith('.png')) fs.unlinkSync(path.join(out, f));

  const files = [];
  let renderMs = 0;
  for (const t of times) {
    renderMs += await page.evaluate((tt) => { const t0 = performance.now(); R.render(tt); return performance.now() - t0; }, t);
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 } });
    const f = path.join(out, `t${t.toFixed(3).padStart(6, '0')}_f${String(Math.round(t * FPS)).padStart(3, '0')}.png`);
    fs.writeFileSync(f, Buffer.from(shot.data, 'base64'));
    files.push({ f, t });
  }

  if (a.sheet) {
    const cols = Number(a.cols || 4);
    const tileW = Math.floor(1920 / cols) - 12, tileH = Math.round((tileW * 9) / 16);
    const BEAT = 60 / 128;
    const cells = files.map(({ f, t }) => {
      const s = Math.floor(t / (BEAT / 4) + 1e-6);
      const mus = `${Math.floor(s / 16) + 1}.${(Math.floor(s / 4) % 4) + 1}.${(s % 4) + 1}`;
      const active = windows.filter((w) => t >= w.start && t < w.end).map((w) => w.id).join(' + ');
      const src = 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
      return `<figure><img src="${src}"><figcaption><b>${t.toFixed(3)}s</b> f${Math.round(t * FPS)} · ${mus} · ${active}</figcaption></figure>`;
    });
    const rows = Math.ceil(cells.length / cols);
    const sheetH = rows * (tileH + 40) + 16;
    const sp = await browser.newPage({ viewport: { width: 1920, height: sheetH }, deviceScaleFactor: 1 });
    await sp.setContent(`<!doctype html><style>
      body{margin:0;background:#111;font:500 15px/1.2 ui-monospace,monospace;color:#ddd}
      main{display:grid;grid-template-columns:repeat(${cols},${tileW}px);gap:12px 12px;padding:8px 6px;justify-content:center}
      figure{margin:0} img{width:${tileW}px;height:${tileH}px;display:block;outline:1px solid #333}
      figcaption{padding:5px 2px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis} b{color:#fff}
      </style><main>${cells.join('')}</main>`);
    await sp.waitForLoadState('load');
    const sheet = path.join(out, 'sheet.png');
    await sp.screenshot({ path: sheet, fullPage: true });
    console.log('sheet', sheet);
    if (a['no-stills']) for (const { f } of files) fs.unlinkSync(f);
  }
  if (!a['no-stills']) for (const { f } of files) console.log(f);
  console.log(`avg R.render: ${(renderMs / Math.max(1, times.length)).toFixed(1)} ms/frame over ${times.length} frames (JS only; excludes paint)`);
  if (page.__errors.length) {
    console.error(`\n${page.__errors.length} page error(s) — fix these first.`);
    exitCode = 2;
  }
} catch (e) {
  console.error(e && e.stack ? e.stack : e);
  exitCode = 1;
} finally {
  await browser.close();
  srv.close();
}
process.exit(exitCode);
