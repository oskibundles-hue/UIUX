#!/usr/bin/env node
// Export the reel's timeline (scene windows, FX cues, sound-design events) to audio/cues.json
// so the procedural soundtrack is generated from the same source of truth as the picture.
//
//   node tools/cues.mjs [--out audio/cues.json]
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, serve, launchBrowser, openReel, parseArgs } from './common.mjs';

const a = parseArgs();
const out = path.resolve(a.out || path.join(ROOT, 'audio', 'cues.json'));
const srv = await serve();
const browser = await launchBrowser();
try {
  const page = await openReel(browser, srv.url);
  const data = await page.evaluate(() => ({
    bpm: R.BPM, duration: R.DUR, fps: R.FPS,
    scenes: R.scenes.map((s) => ({ id: s.id, start: s.start, end: s.end })).sort((x, y) => x.start - y.start),
    fx: R.cues.map((c) => Object.assign({}, c)),
    sounds: R.sounds.map((s) => Object.assign({}, s)).sort((x, y) => x.t - y.t),
  }));
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(data, null, 2) + '\n');
  console.log(`wrote ${path.relative(process.cwd(), out)}: ${data.scenes.length} scenes, ${data.fx.length} fx cues, ${data.sounds.length} sound events`);
} finally {
  await browser.close();
  srv.close();
}
