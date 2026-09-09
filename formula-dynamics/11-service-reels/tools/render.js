// render.js <scene.html> <out.mp4> [fps] [w] [h]
// Captures the scene frame by frame from a single page instance, pipes the
// PNGs straight into ffmpeg, and writes a Meta-ready H.264 MP4.

const { chromium } = require('playwright-core');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const FFMPEG = require('child_process')
  .execSync("python3 -c \"import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())\"")
  .toString().trim();

(async () => {
  const [, , scene, out, fpsArg = '30', wArg = '1080', hArg = '1920'] = process.argv;
  const fps = +fpsArg, W = +wArg, H = +hArg;

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--font-render-hinting=none', '--force-color-profile=srgb',
           '--disable-lcd-text', '--allow-file-access-from-files'],
  });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });

  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });

  await page.goto('file://' + path.resolve(scene), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__ready === true, { timeout: 15000 });

  const duration = await page.evaluate(() => window.SCENE_DURATION);
  const total = Math.round(duration * fps);
  if (errs.length) { console.error('SCENE ERRORS:', errs.slice(0, 5).join(' | ')); }
  console.log(`${path.basename(scene)} -> ${duration}s, ${total} frames @${fps}fps`);

  const ff = spawn(FFMPEG, [
    '-y', '-f', 'image2pipe', '-vcodec', 'png', '-r', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2',
    '-movflags', '+faststart', '-r', String(fps), out,
  ], { stdio: ['pipe', 'ignore', 'pipe'] });
  let ffErr = '';
  ff.stderr.on('data', d => { ffErr += d.toString(); });

  const done = new Promise((res, rej) => {
    ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg ' + c + '\n' + ffErr.slice(-1500)))));
  });

  for (let i = 0; i < total; i++) {
    const t = i / fps;
    await page.evaluate(tt => window.seek(tt), t);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) process.stdout.write(`  ${i}/${total}\r`);
  }
  ff.stdin.end();
  await done;
  await browser.close();

  const mb = (fs.statSync(out).size / 1048576).toFixed(1);
  console.log(`  done -> ${out} (${mb} MB)`);
  if (errs.length) console.error('  NOTE: scene reported errors:', errs.slice(0, 3).join(' | '));
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
