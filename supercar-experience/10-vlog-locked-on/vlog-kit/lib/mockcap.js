// mockcap.js -- capture single frames of kit.html with only some codes shown (the mockup stills).
//   node lib/mockcap.js kit.html <outDir> <mocks.json>
// mocks.json: [{name, t, only: [codes]}]. Each still uses the page's motion-blur plan (window.KT_PLAN) at its
// time, so a mid-transition mockup is blurred like the reel frame. Writes <name>.png (+ fx_<name>.json).
const { chromium } = require(process.env.PW_MODULE || '/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const path = require('path'); const fs = require('fs');
const [page, outDir, list] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
(async () => {
  const acc = spawn('python3', [path.join(__dirname, 'accum.py'), outDir], { stdio: ['pipe', 'inherit', 'inherit'] });
  const b = await chromium.launch({ args: ['--disable-gpu-vsync', '--disable-lcd-text'], ...(process.env.PW_EXEC ? { executablePath: process.env.PW_EXEC } : {}) });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  pg.on('pageerror', e => { console.error('pageerror', e.message); process.exit(2); });
  await pg.goto('file://' + path.resolve(page) + '#chip=0');
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  const cdp = await pg.context().newCDPSession(pg);
  await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  const plan = await pg.evaluate(() => window.KT_PLAN || {});
  const fps = 30000 / 1001;
  const planAt = t => { let k = plan.k || 1, sh = plan.shutter || 180; for (const s of plan.spans || []) if (t >= s.a && t <= s.b) { k = s.k || k; sh = s.shutter || sh; } return { k, sh }; };
  const mocks = JSON.parse(fs.readFileSync(list, 'utf8'));
  for (const m of mocks) {
    await pg.evaluate(o => window.setOnly(o), m.only);
    const { k, sh } = planAt(m.t), span = (sh / 360) / fps;
    const ts = Array.from({ length: k }, (_, j) => m.t + ((j + .5) / k - .5) * span);
    const bufs = [];
    for (const ti of ts) {
      await pg.evaluate(([ti, sub]) => { window.__ktSub = sub; window.renderAt(ti); }, [ti, span / k]);
      bufs.push(Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png' })).data, 'base64'));
    }
    const fx = await pg.evaluate(t => { window.renderAt(t); return window.FX || {}; }, m.t);
    fs.writeFileSync(path.join(outDir, `fx_${m.name}.json`), JSON.stringify(fx));
    const nb = Buffer.from(m.name), hdr = Buffer.alloc(8); hdr.writeUInt32LE(nb.length, 0); hdr.writeUInt32LE(bufs.length, 4);
    const parts = [hdr, nb]; for (const bf of bufs) { const l = Buffer.alloc(4); l.writeUInt32LE(bf.length, 0); parts.push(l, bf); }
    acc.stdin.write(Buffer.concat(parts));
    process.stderr.write(`mock ${m.name} t=${m.t.toFixed(3)} k=${k}\n`);
  }
  await b.close();
  await new Promise(r => { acc.on('close', r); acc.stdin.end(); });
})().catch(e => { console.error(e); process.exit(1); });
