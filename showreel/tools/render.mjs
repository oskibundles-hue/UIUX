#!/usr/bin/env node
// Render the reel frame-by-frame in headless Chromium and encode it with ffmpeg.
//
//   node tools/render.mjs                         full 1080p60 master -> dist/showreel.mp4 (muxes dist/soundtrack.wav if present)
//   node tools/render.mjs --preview               540p30 quick check  -> .cache/preview.mp4
//   options: --from S --to S   --workers N   --scale 0.5   --fps 60|30   --crf 16   --out FILE   --audio FILE|none
//            --only ids   --keep (keep PNG frames)   --reuse (skip frames already on disk)
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { ROOT, FPS, DUR, W, H, serve, launchBrowser, openReel, parseArgs, parseTime, findFfmpeg } from './common.mjs';

const a = parseArgs();
const preview = !!a.preview;
const scale = Number(a.scale || (preview ? 0.5 : 1));
const outFps = Number(a.fps || (preview ? 30 : FPS));
const step = FPS / outFps;
if (!Number.isInteger(step)) throw new Error('--fps must divide 60');
const from = a.from !== undefined ? parseTime(a.from) : 0;
const to = a.to !== undefined ? parseTime(a.to) : DUR;
const workers = Number(a.workers || Math.max(1, Math.min(4, os.cpus().length - 1)));
const out = path.resolve(a.out || (preview ? path.join(ROOT, '.cache', 'preview.mp4') : path.join(ROOT, 'dist', 'showreel.mp4')));
const framesDir = path.join(ROOT, '.cache', preview ? 'frames-preview' : 'frames');
const ffmpeg = findFfmpeg();

const frames = [];
for (let f = Math.round(from * FPS); f < Math.round(to * FPS); f += step) frames.push(f);
fs.mkdirSync(framesDir, { recursive: true });
if (!a.reuse) for (const f of fs.readdirSync(framesDir)) if (f.endsWith('.png')) fs.unlinkSync(path.join(framesDir, f));

const srv = await serve();
const browser = await launchBrowser();
const t0 = Date.now();
let done = 0, errors = 0;
try {
  // Contiguous chunks so cached simulations only ever step forward.
  const per = Math.ceil(frames.length / workers);
  const chunks = Array.from({ length: workers }, (_, i) => frames.slice(i * per, (i + 1) * per)).filter((c) => c.length);
  await Promise.all(chunks.map(async (chunk) => {
    const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: scale });
    page.on('pageerror', (e) => { errors++; console.error('[pageerror]', e && e.stack || e); });
    page.on('console', (m) => { if (m.type() === 'error') console.error('[console.error]', m.text()); });
    await page.goto(`${srv.url}/index.html?render${a.only ? '&only=' + encodeURIComponent(a.only) : ''}`);
    await page.evaluate(() => window.R.ready);
    const cdp = await page.context().newCDPSession(page);
    for (const f of chunk) {
      const idx = (f - frames[0]) / step;
      const file = path.join(framesDir, `${String(idx).padStart(5, '0')}.png`);
      if (a.reuse && fs.existsSync(file)) { done++; continue; }
      await page.evaluate((ff) => R.frame(ff), f);
      const shot = await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true });
      fs.writeFileSync(file, Buffer.from(shot.data, 'base64'));
      done++;
      if (done % 60 === 0 || done === frames.length) {
        const el = (Date.now() - t0) / 1000;
        process.stdout.write(`\r  ${done}/${frames.length} frames  ${el.toFixed(0)}s  (${(el / done * 1000).toFixed(0)} ms/frame)   `);
      }
    }
    await page.close();
  }));
  process.stdout.write('\n');
} finally {
  await browser.close();
  srv.close();
}
if (errors) console.error(`WARNING: ${errors} page errors during render`);

// Encode. Explicit BT.709 conversion so the locked palette survives RGB -> YUV intact.
let audio = a.audio === 'none' ? null : a.audio ? path.resolve(a.audio) : path.join(ROOT, 'dist', 'soundtrack.wav');
if (audio && !fs.existsSync(audio)) audio = null;
fs.mkdirSync(path.dirname(out), { recursive: true });
const args = ['-y', '-hide_banner', '-loglevel', 'error', '-framerate', String(outFps), '-i', path.join(framesDir, '%05d.png')];
if (audio) args.push('-ss', String(from), '-t', String(to - from), '-i', audio);
args.push(
  '-vf', 'scale=out_color_matrix=bt709:out_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p',
  '-c:v', 'libx264', '-preset', preview ? 'veryfast' : 'slow', '-crf', String(a.crf || (preview ? 23 : 16)),
  '-profile:v', 'high', '-g', String(outFps), '-bf', '2',
  '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
  '-movflags', '+faststart',
);
if (audio) args.push('-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest');
args.push(out);
const r = spawnSync(ffmpeg, args, { stdio: 'inherit' });
if (r.status !== 0) process.exit(r.status || 1);
if (!a.keep && !preview) for (const f of fs.readdirSync(framesDir)) if (f.endsWith('.png')) fs.unlinkSync(path.join(framesDir, f));
const mb = (fs.statSync(out).size / 1048576).toFixed(2);
console.log(`wrote ${path.relative(process.cwd(), out)}  ${mb} MB  ${frames.length} frames @ ${outFps}fps  ${audio ? '+ audio' : '(no audio)'}  in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
