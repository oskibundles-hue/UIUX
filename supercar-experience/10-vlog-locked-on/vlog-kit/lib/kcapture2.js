/* kcapture2.js -- kcapture.js for kit2.html: true motion blur, plus PASSES.
 *
 * For every frame it first renders the frame-centre time to read window.FX, then captures the front layer and, when
 * the frame uses them, the back pass (FX.back: drawn under the subject) and the mask pass (FX.mask: a window onto the
 * B plate), each with the same sub-frame samples, into <name>.png, <name>_back.png and <name>_mask.png (accum.py
 * averages the samples in premultiplied alpha). window.FX goes to fx_<name>.json. Frames whose DOM state is identical
 * at shutter open / middle / close are captured once.
 *
 *   node kcapture2.js <kit2.html> <outDir> list  <fps> <frames.json>          (reel frames, named NNNNN)
 *   node kcapture2.js <kit2.html> <outDir> mocks <mocks.json>                 ([{name, t, only}], chip hidden)
 * Env: PW_MODULE (playwright), PW_EXEC (a Chromium / headless-shell binary) where /opt/node22 is not there.
 */
const { chromium } = require(process.env.PW_MODULE || '/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const path = require('path'); const fs = require('fs');

const argv = process.argv.slice(2);
const [page, outDir, mode, a1, a2] = argv;
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const acc = spawn('python3', [path.join(__dirname, 'accum.py'), outDir], { stdio: ['pipe', 'inherit', 'inherit'] });
  const b = await chromium.launch({ args: ['--disable-gpu-vsync', '--disable-lcd-text'], ...(process.env.PW_EXEC ? { executablePath: process.env.PW_EXEC } : {}) });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  pg.on('pageerror', e => { console.error('pageerror', e.message); process.exit(2); });
  await pg.goto('file://' + path.resolve(page) + (mode === 'mocks' ? '#chip=0' : ''));
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  const cdp = await pg.context().newCDPSession(pg);
  await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  const plan = await pg.evaluate(() => window.KT_PLAN || {});
  const planAt = t => { let k = plan.k || 1, sh = plan.shutter || 180; for (const s of plan.spans || []) if (t >= s.a && t <= s.b) { k = s.k || k; sh = s.shutter || sh; } return { k, sh }; };
  let items;
  if (mode === 'list') { const fps = a1.includes('/') ? a1.split('/')[0] / a1.split('/')[1] : +a1;
    items = JSON.parse(fs.readFileSync(a2, 'utf8')).map(i => ({ t: i / fps, name: String(i).padStart(5, '0'), fps })); }
  else items = JSON.parse(fs.readFileSync(a1, 'utf8')).map(m => Object.assign({ fps: 30000 / 1001 }, m));

  const shot = async () => Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64');
  const sig = async t => pg.evaluate(t => { window.renderAt(t); return KT.signature(); }, t);
  const T0 = Date.now(); let nShots = 0;
  for (let fi = 0; fi < items.length; fi++) {
    const it = items[fi];
    if (it.only) await pg.evaluate(o => window.setOnly(o), it.only);
    const fx = await pg.evaluate(t => { window.setPass('front'); window.renderAt(t); return window.FX || {}; }, it.t);
    const passes = [['front', '']].concat(fx.back ? [['back', '_back']] : [], fx.mask ? [['mask', '_mask']] : []);
    const { k, sh } = planAt(it.t), span = (sh / 360) / it.fps;
    for (const [pass, suf] of passes) {
      await pg.evaluate(p => window.setPass(p), pass);
      const ts = Array.from({ length: k }, (_, j) => it.t + ((j + .5) / k - .5) * span);
      if (k > 1) { const s0 = await sig(ts[0]), s1 = await sig(ts[k - 1]), sm = await sig(it.t); if (s0 === s1 && s0 === sm) { ts.length = 0; ts.push(it.t); } }
      const bufs = [];
      for (const ti of ts) { await pg.evaluate(([ti, sub]) => { window.__ktSub = sub; window.renderAt(ti); }, [ti, span / ts.length]); bufs.push(await shot()); nShots++; }
      const nb = Buffer.from(it.name + suf), hdr = Buffer.alloc(8); hdr.writeUInt32LE(nb.length, 0); hdr.writeUInt32LE(bufs.length, 4);
      const parts = [hdr, nb]; for (const bf of bufs) { const l = Buffer.alloc(4); l.writeUInt32LE(bf.length, 0); parts.push(l, bf); }
      if (!acc.stdin.write(Buffer.concat(parts))) await new Promise(r => acc.stdin.once('drain', r));
    }
    await pg.evaluate(() => window.setPass('front'));
    const fxPath = path.join(outDir, `fx_${it.name}.json`);
    if (Object.keys(fx).length) fs.writeFileSync(fxPath, JSON.stringify(fx)); else if (fs.existsSync(fxPath)) fs.unlinkSync(fxPath);
    if (fi % 24 === 0) process.stderr.write(`frame ${fi}/${items.length} t=${it.t.toFixed(2)} k=${k} passes=${passes.length} ${((Date.now() - T0) / 1000).toFixed(1)}s\n`);
  }
  await b.close();
  await new Promise(r => { acc.on('close', r); acc.stdin.end(); });
  process.stderr.write(`done: ${items.length} frames, ${nShots} samples, ${((Date.now() - T0) / 1000).toFixed(1)}s\n`);
})().catch(e => { console.error(e); process.exit(1); });
