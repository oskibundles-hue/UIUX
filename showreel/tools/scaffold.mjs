#!/usr/bin/env node
// Generate src/scenes/manifest.js from storyboard.json and create placeholder modules for scenes that
// don't exist yet, so the whole reel renders while scenes are still being built.
//
//   node tools/scaffold.mjs
import fs from 'node:fs';
import path from 'node:path';
import { ROOT } from './common.mjs';

const sb = JSON.parse(fs.readFileSync(path.join(ROOT, 'storyboard.json'), 'utf8'));
const scenes = [...sb.scenes].sort((a, b) => a.start - b.start);
const dir = path.join(ROOT, 'src', 'scenes');
fs.mkdirSync(dir, { recursive: true });

const files = scenes.map((s) => `src/scenes/${s.id}.js`);
fs.writeFileSync(path.join(dir, 'manifest.js'),
  `// Scene load order (generated from storyboard.json by tools/scaffold.mjs).\nwindow.SCENE_FILES = ${JSON.stringify(files, null, 2)};\n`);

scenes.forEach((s, i) => {
  const f = path.join(dir, `${s.id}.js`);
  if (fs.existsSync(f)) return;
  fs.writeFileSync(f, `// PLACEHOLDER — replaced by the scene build. ${s.name} (${s.start}s–${s.end}s)
R.scene({
  id: ${JSON.stringify(s.id)},
  start: ${s.start},
  end: ${s.end},
  z: ${s.z ?? (i + 1) * 10},${s.id.startsWith('s00') ? '' : '\n  bg: R.pal.graphite,'}
  setup(root) {
    this.label = R.el('div', { text: ${JSON.stringify(`${s.id} · ${s.name}`)}, style: { left: '120px', top: '470px', font: \`800 72px \${R.font.display}\`, color: R.pal.fog } }, root);
    this.bar = R.el('div', { style: { left: '120px', top: '590px', height: '6px', width: '0px', background: R.pal.fog } }, root);
  },
  update(lt, p) {
    this.bar.style.width = (p * 1680).toFixed(1) + 'px';
  },
});
`);
});
console.log(`manifest: ${files.length} scenes\n` + scenes.map((s) => `  ${s.id.padEnd(22)} ${String(s.start).padStart(7)} → ${String(s.end).padEnd(7)} ${s.name}`).join('\n'));
