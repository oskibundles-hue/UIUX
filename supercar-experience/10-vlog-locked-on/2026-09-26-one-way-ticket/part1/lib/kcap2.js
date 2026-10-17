/* kcap2.js: layer capture for the rally-v2 build (replaces lib/kcapture.js here; the kit copy is left as it was).
 *
 * Same sampling as kcapture.js (KT_PLAN spans, K samples across the shutter centred on the frame time, a frame whose
 * KT.signature is the same at shutter open / middle / close is captured once, premultiplied-alpha average), plus:
 *
 *  - order-independent pixels. The kit's split glyphs carry `will-change: transform`, and Chromium keeps a composited
 *    layer's raster state from the frames it rendered before, so the same frame came out slightly different (text
 *    edges, up to 105/255) depending on which frames a process had rendered first. Before every frame the page is
 *    hidden and one frame is committed (renderAt(-1e9) + rAF), so every frame starts from the same compositor state.
 *    This is what makes a per-frame cache sound: a frame re-captured alone equals the same frame from a full run.
 *  - `hash` mode: a hash of each frame's complete layer state (every visible component's DOM: styles, text, SVG
 *    attributes, for every motion-blur sample) plus the page's CSS and the capture settings. build.py re-captures
 *    only frames whose hash changed, and captures identical frames once.
 *  - multi-sample frames are screenshotted inside their dirty rect (the union of every visible element's box over the
 *    frame's samples, + 96 px for shadows and glows). The rect's border must be transparent in every sample, else the
 *    frame is captured again full-size, so clipping can never cut anything off.
 *  - --scale 0.5 --k1: draft capture (540x960, one sample per frame).
 *
 *   node kcap2.js <page.html> <outDir> list <fps> <frames.json> [--workers 1] [--scale 1] [--k1] [--noclip] [--noreset]
 *   node kcap2.js <page.html> <outDir> hash <fps> <frames.json|all> <out.json> [--scale 1] [--k1]
 */
const { chromium } = require('./playwright');  // resolves Playwright on this machine (lib/playwright.js)
const { spawn } = require('child_process');
const path = require('path'); const fs = require('fs');

const argv = process.argv.slice(2);
const opt = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 ? argv[i + 1] : d; };
const flag = n => argv.includes('--' + n);
const [page, outDir, mode, fpsArg, listArg, outJson] = argv;
const FPS = fpsArg.includes('/') ? fpsArg.split('/')[0] / fpsArg.split('/')[1] : +fpsArg;
const SCALE = +opt('scale', 1), K1 = flag('k1'), CLIP = !flag('noclip'), RESET = !flag('noreset'), NW = +opt('workers', 1);
const VERSION = 'kcap2-1';
const W = 1080, H = 1920;

(async () => {
  const b = await chromium.launch({ args: ['--disable-gpu-vsync', '--disable-lcd-text'] });
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  pg.on('pageerror', e => { console.error('pageerror', e.message); process.exit(2); });
  await pg.goto('file://' + path.resolve(page));
  await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  const cdp = await pg.context().newCDPSession(pg);
  await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  // page-side helpers (the page itself is not modified)
  await pg.evaluate(([K1, FPS]) => {
    const plan = window.KT_PLAN || {};
    const stage = document.getElementById('stage');
    const cyrb = (str, seed = 0) => { let h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
      for (let i = 0; i < str.length; i++) { const c = str.charCodeAt(i); h1 = Math.imul(h1 ^ c, 2654435761); h2 = Math.imul(h2 ^ c, 1597334677); }
      h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
      h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
      return (h2 >>> 0).toString(16).padStart(8, '0') + (h1 >>> 0).toString(16).padStart(8, '0'); };
    let css = '';
    for (const s of document.styleSheets) { try { for (const r of s.cssRules) css += r.cssText; } catch (e) { css += 'x'; } }
    const salt = cyrb(css + '|' + navigator.userAgent);
    // exactly kcapture.js's plan + sample times + static-frame collapse (K0 = 10, SH0 = 180 defaults)
    const samples = t => {
      let k = plan.k || 10, sh = plan.shutter || 180;
      for (const s of plan.spans || []) if (t >= s.a && t <= s.b) { k = s.k || k; sh = s.shutter || sh; }
      if (K1) k = 1;
      const span = (sh / 360) / FPS;
      let ts = Array.from({ length: k }, (_, j) => t + ((j + .5) / k - .5) * span);
      if (k > 1) { window.__ktSub = span / k; const sig = x => { window.renderAt(x); return KT.signature(); };
        const s0 = sig(ts[0]), s1 = sig(ts[k - 1]), sm = sig(t); if (s0 === s1 && s0 === sm) ts = [t]; }
      return { k, sh, ts, sub: span / ts.length };
    };
    const vis = e => e.style.display !== 'none';
    const state = () => { let s = ''; for (const r of stage.children) s += vis(r) ? r.outerHTML.length + ':' + cyrb(r.outerHTML) + ';' : '-;'; return s; };
    const dirty = () => { let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const r of stage.children) { if (!vis(r)) continue;
        for (const e of r.querySelectorAll('*')) { const bb = e.getBoundingClientRect(); if (bb.width <= 0 || bb.height <= 0) continue;
          if (bb.width >= 1070 && bb.height >= 1900) continue;   // full-frame containers (component roots, svg canvases): their content counts
          x0 = Math.min(x0, bb.left); y0 = Math.min(y0, bb.top); x1 = Math.max(x1, bb.right); y1 = Math.max(y1, bb.bottom); } }
      return [x0, y0, x1, y1]; };
    window.__kc = { samples, state, dirty, salt, cyrb };
  }, [K1, FPS]);

  let frames;
  if (listArg === 'all') { const nf = Math.round((await pg.evaluate(() => window.SCENE.dur)) * FPS); frames = Array.from({ length: nf }, (_, i) => i); }
  else frames = JSON.parse(fs.readFileSync(listArg, 'utf8'));

  if (mode === 'hash') {
    const res = await pg.evaluate(([frames, FPS, VERSION, SCALE, K1]) => {
      const out = {};
      for (const n of frames) {
        const t = n / FPS, s = window.__kc.samples(t);
        let st = '';
        for (const ti of s.ts) { window.__ktSub = s.sub; window.renderAt(ti); st += window.__kc.state() + '#'; }
        out[n] = window.__kc.cyrb([VERSION, SCALE, K1 ? 1 : 0, s.k, s.sh, s.ts.length, window.__kc.salt, st].join('|'));
      }
      return out;
    }, [frames, FPS, VERSION, SCALE, K1]);
    fs.writeFileSync(outJson, JSON.stringify(res));
    await b.close(); return;
  }

  fs.mkdirSync(outDir, { recursive: true });
  const workers = Array.from({ length: NW }, () => spawn('python3', [path.join(__dirname, 'accum2.py'), outDir], { stdio: ['pipe', 'inherit', 'inherit'] }));
  const OW = Math.round(W * SCALE), OH = Math.round(H * SCALE);
  const shot = async clip => Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true,
    clip: clip ? { x: clip[0], y: clip[1], width: clip[2], height: clip[3], scale: SCALE } : { x: 0, y: 0, width: W, height: H, scale: SCALE } })).data, 'base64');
  const T0 = Date.now(); let nShots = 0, nClip = 0, nRetry = 0;
  for (let fi = 0; fi < frames.length; fi++) {
    const n = frames[fi], t = n / FPS;
    if (RESET) {
      await pg.evaluate(() => window.renderAt(-1e9));
      await pg.evaluate(() => new Promise(r => requestAnimationFrame(() => setTimeout(r, 0))));
    }
    const s = await pg.evaluate(t => { const s = window.__kc.samples(t); return { k: s.k, ts: s.ts, sub: s.sub }; }, t);
    let clip = null;
    if (CLIP && s.ts.length > 1 && SCALE === 1) {
      const d = await pg.evaluate(([ts, sub]) => { let u = [1e9, 1e9, -1e9, -1e9];
        for (const ti of ts) { window.__ktSub = sub; window.renderAt(ti); const q = window.__kc.dirty();
          u = [Math.min(u[0], q[0]), Math.min(u[1], q[1]), Math.max(u[2], q[2]), Math.max(u[3], q[3])]; }
        return u; }, [s.ts, s.sub]);
      if (d[2] > d[0]) {
        const x0 = Math.max(0, Math.floor((d[0] - 96) / 2) * 2), y0 = Math.max(0, Math.floor((d[1] - 96) / 2) * 2);
        const x1 = Math.min(W, Math.ceil((d[2] + 96) / 2) * 2), y1 = Math.min(H, Math.ceil((d[3] + 96) / 2) * 2);
        if ((x1 - x0) * (y1 - y0) < 0.85 * W * H) clip = [x0, y0, x1 - x0, y1 - y0];
      }
    }
    const bufs = [];
    for (const ti of s.ts) { await pg.evaluate(([ti, sub]) => { window.__ktSub = sub; window.renderAt(ti); }, [ti, s.sub]); bufs.push(await shot(clip)); nShots++; }
    if (clip) nClip++;
    const rect = clip ? clip.map(v => Math.round(v * SCALE)) : [0, 0, OW, OH];
    const w = workers[fi % NW].stdin;
    const nb = Buffer.from(String(n).padStart(5, '0')); const hdr = Buffer.alloc(32);
    hdr.writeUInt32LE(nb.length, 0); hdr.writeUInt32LE(bufs.length, 4);
    [rect[0], rect[1], rect[2], rect[3], OW, OH].forEach((v, i) => hdr.writeUInt32LE(v, 8 + 4 * i));
    const parts = [hdr, nb]; for (const bf of bufs) { const l = Buffer.alloc(4); l.writeUInt32LE(bf.length, 0); parts.push(l, bf); }
    if (!w.write(Buffer.concat(parts))) await new Promise(r => w.once('drain', r));
    if (fi % 48 === 0) process.stderr.write(`frame ${fi}/${frames.length} n=${n} k=${bufs.length}${clip ? ' clip ' + clip.join(',') : ''} ${((Date.now() - T0) / 1000).toFixed(1)}s\n`);
  }
  await b.close();
  await Promise.all(workers.map(w => new Promise(r => { w.on('close', r); w.stdin.end(); })));
  process.stderr.write(`done: ${frames.length} frames, ${nShots} samples, ${nClip} clipped, ${((Date.now() - T0) / 1000).toFixed(1)}s\n`);
})();
