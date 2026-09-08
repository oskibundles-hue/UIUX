// frames.js <scene.html> <out.png> <t1,t2,...>  — contact sheet of key frames
const { chromium } = require('playwright-core');
const path = require('path');
const { execSync } = require('child_process');

(async () => {
  const [, , scene, out, times] = process.argv;
  const ts = times.split(',').map(Number);
  const b = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--font-render-hinting=none', '--force-color-profile=srgb',
           '--allow-file-access-from-files'],
  });
  const page = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto('file://' + path.resolve(scene), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__ready === true, { timeout: 15000 });

  const tmp = path.resolve(__dirname, 'build/_kf');
  execSync(`mkdir -p ${tmp} && rm -f ${tmp}/*.png`);
  for (let i = 0; i < ts.length; i++) {
    await page.evaluate(t => window.seek(t), ts[i]);
    await page.screenshot({ path: `${tmp}/f${String(i).padStart(2, '0')}.png` });
  }
  await b.close();
  if (errs.length) console.error('SCENE ERRORS:', [...new Set(errs)].slice(0, 5).join(' | '));

  execSync(`python3 - <<'PY'
from PIL import Image, ImageDraw
import glob
fs=sorted(glob.glob("${tmp}/*.png")); ts=${JSON.stringify(ts)}
w=300; ims=[Image.open(f).resize((w,int(w*16/9)),Image.LANCZOS) for f in fs]
sheet=Image.new('RGB',(w*len(ims), ims[0].height+34),(18,20,26))
d=ImageDraw.Draw(sheet)
for i,im in enumerate(ims):
    sheet.paste(im,(i*w,34)); d.text((i*w+9,10), f"t={ts[i]}s", fill=(190,200,215))
sheet.save("${out}")
print("sheet", sheet.size)
PY`, { stdio: 'inherit' });
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
