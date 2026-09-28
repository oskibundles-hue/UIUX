// Shared helpers for the capture tools: static server, Playwright loader, ffmpeg lookup, arg parsing.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync, spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const FPS = 60;
export const DUR = 15;
export const W = 1920;
export const H = 1080;

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2', '.woff': 'font/woff', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.wav': 'audio/wav', '.mp4': 'video/mp4', '.m4a': 'audio/mp4',
};

/** Serve ROOT over http on a random localhost port. Returns {url, close}. */
export function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      const p = path.join(ROOT, u === '/' ? 'index.html' : u);
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) {
        res.writeHead(404); res.end('not found'); return;
      }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      fs.createReadStream(p).pipe(res);
    });
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({ url: `http://127.0.0.1:${port}`, close: () => server.close() });
    });
  });
}

/** Import playwright from the local project, else from the global npm root. */
export async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch {
    const globalRoot = execSync('npm root -g').toString().trim();
    const req = createRequire(path.join(globalRoot, 'noop.js'));
    return req('playwright');
  }
}

export async function launchBrowser() {
  const { chromium } = await loadPlaywright();
  const opts = {
    args: ['--force-color-profile=srgb', '--font-render-hinting=none', '--disable-lcd-text', '--hide-scrollbars', '--mute-audio'],
  };
  if (process.env.CHROMIUM_PATH) opts.executablePath = process.env.CHROMIUM_PATH;
  return chromium.launch(opts);
}

/** Open the reel page in render mode and wait for boot. Forwards page errors to stderr. */
export async function openReel(browser, base, query = '') {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => { errors.push(String(e && e.stack || e)); console.error('[pageerror]', e && e.stack || e); });
  page.on('console', (m) => {
    if (m.type() === 'error' || m.type() === 'warning') console.error(`[console.${m.type()}]`, m.text());
    if (m.type() === 'error') errors.push(m.text());
  });
  await page.goto(`${base}/index.html?render${query ? '&' + query : ''}`);
  await page.evaluate(() => window.R.ready);
  page.__errors = errors;
  return page;
}

/** Locate an ffmpeg with libx264: $FFMPEG, PATH, or the imageio-ffmpeg wheel. */
export function findFfmpeg() {
  const cands = [process.env.FFMPEG, 'ffmpeg'].filter(Boolean);
  for (const c of cands) {
    const r = spawnSync(c, ['-hide_banner', '-encoders'], { encoding: 'utf8' });
    if (r.status === 0 && r.stdout.includes('libx264')) return c;
  }
  const r = spawnSync('python3', ['-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'], { encoding: 'utf8' });
  if (r.status === 0 && r.stdout.trim()) return r.stdout.trim();
  throw new Error('ffmpeg with libx264 not found. Install one, set $FFMPEG, or `pip install imageio-ffmpeg`.');
}

/** Minimal --flag value / --flag parser. */
export function parseArgs(argv = process.argv.slice(2)) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const k = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith('--')) { out[k] = next; i++; } else out[k] = true;
    } else out._.push(a);
  }
  return out;
}

/** Parse a time expression: seconds ("3.75"), frames ("f225") or musical "b3.2.0" (bar.beat.sixteenth). */
export function parseTime(s) {
  s = String(s).trim();
  if (s.startsWith('f')) return Number(s.slice(1)) / FPS;
  if (s.startsWith('b')) {
    const [bar, beat = 1, six = 0] = s.slice(1).split('.').map(Number);
    const BEAT = 60 / 128;
    return (bar - 1) * BEAT * 4 + (beat - 1) * BEAT + six * BEAT / 4;
  }
  return Number(s);
}
