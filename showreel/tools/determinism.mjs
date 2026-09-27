#!/usr/bin/env node
// Verify a scene is a pure function of time: render its frames in order in one page and in a
// shuffled order (with backward seeks) in a fresh page, then compare the pixels frame by frame.
//
//   node tools/determinism.mjs --scene s03 [--count 24]
import { FPS, W, H, serve, launchBrowser, openReel, parseArgs } from './common.mjs';
import crypto from 'node:crypto';

const a = parseArgs();
if (!a.scene) { console.error('usage: node tools/determinism.mjs --scene <id> [--count 24]'); process.exit(1); }
const srv = await serve();
const browser = await launchBrowser();
let code = 0;
try {
  const probe = await openReel(browser, srv.url, 'only=' + encodeURIComponent(a.scene));
  const win = await probe.evaluate((id) => R.scenes.filter((s) => s.id === id || s.id.startsWith(id)).map((s) => [s.start, s.end])[0], a.scene);
  await probe.close();
  if (!win) throw new Error('scene not found: ' + a.scene);
  const n = Number(a.count || 24);
  const f0 = Math.ceil(win[0] * FPS), f1 = Math.ceil(win[1] * FPS) - 1;
  const frames = Array.from({ length: n }, (_, i) => Math.round(f0 + ((f1 - f0) * i) / Math.max(1, n - 1)));
  const shuffled = frames.map((f, i) => [((i * 7919) % 104729) / 104729, f]).sort((x, y) => x[0] - y[0]).map((x) => x[1]);
  async function pass(order) {
    const page = await openReel(browser, srv.url, 'only=' + encodeURIComponent(a.scene));
    const cdp = await page.context().newCDPSession(page);
    const out = new Map();
    for (const f of order) {
      await page.evaluate((ff) => R.frame(ff), f);
      const s = await cdp.send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 } });
      out.set(f, crypto.createHash('sha1').update(s.data).digest('hex'));
    }
    await page.close();
    return out;
  }
  const A = await pass(frames);
  const B = await pass(shuffled);
  const bad = frames.filter((f) => A.get(f) !== B.get(f));
  if (bad.length) {
    code = 2;
    console.log(`NOT DETERMINISTIC: ${bad.length}/${frames.length} frames differ between in-order and shuffled rendering: ` + bad.map((f) => `f${f} (${(f / FPS).toFixed(3)}s)`).join(', '));
    console.log('Look for state carried between update() calls, sims without R.sim, or properties not set every frame.');
  } else console.log(`deterministic: ${frames.length} frames identical in-order vs shuffled (${a.scene})`);
} catch (e) {
  console.error(e && e.stack || e); code = 1;
} finally {
  await browser.close(); srv.close();
}
process.exit(code);
