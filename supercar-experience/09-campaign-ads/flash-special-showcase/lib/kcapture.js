/* kcapture.js — capture a deterministic renderAt(t) page with TRUE motion blur.
 *
 * For every output frame it renders K sub-frame samples spread across the shutter interval
 * (shutter angle, default 180 deg = half the frame period, centred on the frame time), screenshots each
 * with a transparent background, and streams them to accum.py which averages them in PREMULTIPLIED
 * alpha (so blurred edges composite correctly over the plate) and writes one RGBA PNG per frame.
 *
 *   node kcapture.js <page.html[#hash]> <outDir> seq  <fps> <dur> [--from s] [--to s]
 *   node kcapture.js <page.html[#hash]> <outDir> at   <t1,t2,...>            (stills, named by time)
 *   node kcapture.js <page.html[#hash]> <outDir> frames <fps> <i1,i2,...>    (frame indices, named NNNNN)
 *
 * Copied from scratchpad/showcase/rnd-type/kcapture.js for the SE flash-special showcase; changes:
 * the `frames` mode above, `fps` may be fractional (24000/1001), and the page is loaded once
 * with a longer ready timeout.
 *   options: --k 10 (default samples) --shutter 180 --workers 2 --scale 1
 *
 * The page may define window.KT_PLAN = {k, shutter, spans:[{a,b,k,shutter}]} (see kinetic.js) to
 * raise K only where motion is fast. Frames whose DOM style state (KT.signature) is identical at
 * shutter open / middle / close are captured once. Screenshots go through CDP captureScreenshot with
 * optimizeForSpeed (~40 ms at 1080x1920) instead of page.screenshot (~85 ms).
 */
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const path = require('path'); const fs = require('fs');

const argv = process.argv.slice(2);
const opt = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 ? argv[i + 1] : d; };
const [page, outDir, mode, a1, a2] = argv;
const K0 = +opt('k', 10), SH0 = +opt('shutter', 180), NW = +opt('workers', 2);
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const workers = Array.from({ length: NW }, () => spawn('python3', [path.join(__dirname, 'accum.py'), outDir], { stdio: ['pipe', 'inherit', 'inherit'] }));
  const b = await chromium.launch({ args: ['--disable-gpu-vsync', '--disable-lcd-text'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: +opt('scale', 1) });
  const url = page.startsWith('file:') || page.startsWith('http') ? page : 'file://' + path.resolve(page.split('#')[0]) + (page.includes('#') ? '#' + page.split('#')[1] : '');
  await pg.goto(url);
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  const cdp = await pg.context().newCDPSession(pg);
  await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  const plan = await pg.evaluate(() => window.KT_PLAN || {});
  const fps = mode === 'seq' || mode === 'frames' ? +a1 : 24;
  const planAt = t => { let k = plan.k || K0, sh = plan.shutter || SH0;
    for (const s of plan.spans || []) if (t >= s.a && t <= s.b) { k = s.k || k; sh = s.shutter || sh; }
    return { k, sh }; };

  let frames;
  if (mode === 'seq') { const from = +opt('from', 0), to = +opt('to', +a2); frames = [];
    for (let i = Math.round(from * fps); i < Math.round(to * fps); i++) frames.push({ t: i / fps, name: String(i).padStart(5, '0') }); }
  else if (mode === 'frames') frames = a2.split(',').map(Number).map(i => ({ t: i / fps, name: String(i).padStart(5, '0') }));
  else frames = a1.split(',').map(Number).map(t => ({ t, name: 't' + t.toFixed(3) }));

  const shot = async () => Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64');
  const sig = async t => pg.evaluate(t => { window.renderAt(t); return KT.signature(); }, t);
  const T0 = Date.now(); let nShots = 0;
  for (let fi = 0; fi < frames.length; fi++) {
    const { t, name } = frames[fi]; let { k, sh } = planAt(t);
    const span = (sh / 360) / fps;
    const ts = Array.from({ length: k }, (_, j) => t + ((j + .5) / k - .5) * span);
    if (k > 1) { const s0 = await sig(ts[0]), s1 = await sig(ts[k - 1]), sm = await sig(t);
      if (s0 === s1 && s0 === sm) { ts.length = 0; ts.push(t); } }
    const bufs = [];
    const sub = span / ts.length;
    for (const ti of ts) { await pg.evaluate(([ti, sub]) => { window.__ktSub = sub; window.renderAt(ti); }, [ti, sub]); bufs.push(await shot()); nShots++; }
    const w = workers[fi % NW].stdin;
    const nb = Buffer.from(name); const hdr = Buffer.alloc(8); hdr.writeUInt32LE(nb.length, 0); hdr.writeUInt32LE(bufs.length, 4);
    const parts = [hdr, nb]; for (const bf of bufs) { const l = Buffer.alloc(4); l.writeUInt32LE(bf.length, 0); parts.push(l, bf); }
    if (!w.write(Buffer.concat(parts))) await new Promise(r => w.once('drain', r));
    if (fi % 24 === 0) process.stderr.write(`frame ${fi}/${frames.length} t=${t.toFixed(2)} k=${bufs.length} ${((Date.now() - T0) / 1000).toFixed(1)}s\n`);
  }
  await b.close();
  await Promise.all(workers.map(w => new Promise(r => { w.on('close', r); w.stdin.end(); })));
  process.stderr.write(`done: ${frames.length} frames, ${nShots} samples, ${((Date.now() - T0) / 1000).toFixed(1)}s\n`);
})();
