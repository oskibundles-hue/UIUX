"""capture.py - render front.html's renderAt(t) to RGBA PNGs with sub-frame motion blur.

  python capture.py seq <outdir> <nframes>            all frames (K per frame from FAST spans)
  python capture.py at  <outdir> <t1,t2,...>          stills at given times, K=1

Samples straight-alpha screenshots across a 180-degree shutter and averages them in premultiplied
alpha (same maths as the Locked-On accum.py). Uses the installed Google Chrome through Playwright.
"""
import sys, io, os, json
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24000 / 1001
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
B = json.load(open(os.path.join(HERE, 'edl.json')))['beat']
# v2 fast-motion hits (ad beats): slams, wipes, whips, reels, snaps -> more samples around them
HITS = [4, 5.5, 6.5125, 8, 8.3, 9, 16, 16.5, 20, 20.5, 24, 24.4, 24.75, 27, 28, 30, 36, 37.5, 38]
REELS = []


def k_for(t):
    if any(a * B <= t <= b * B for a, b in REELS): return 10
    if any(abs(t - h * B) <= 0.2 for h in HITS): return 8
    return 1


def shoot(pg, t):
    pg.evaluate(f'window.renderAt({t:.6f})')
    return np.asarray(Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert('RGBA'), dtype=np.float32)


def frame(pg, t, k):
    if k == 1:
        return shoot(pg, t).astype(np.uint8)
    dt = 0.5 / FPS
    acc = None
    for j in range(k):
        im = shoot(pg, t - dt / 2 + dt * (j + 0.5) / k)
        a = im[..., 3:4] / 255.0
        if acc is None: acc, aa = im[..., :3] * a, a.copy()
        else: acc += im[..., :3] * a; aa += a
    rgb = np.where(aa > 1e-6, acc / np.maximum(aa, 1e-6), 0)
    return np.dstack([rgb, aa / k * 255.0]).clip(0, 255).astype(np.uint8)


def main():
    mode, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--disable-lcd-text', '--allow-file-access-from-files'])
        pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(HERE, 'front.html'))
        pg.wait_for_function('window.__ready === true', timeout=60000)
        if mode == 'at':
            for t in [float(x) for x in sys.argv[3].split(',')]:
                Image.fromarray(frame(pg, t, 1)).save(os.path.join(out, f't{t:07.3f}.png'))
        else:
            n = int(sys.argv[3])
            for i in range(n):
                dst = os.path.join(out, f'{i:05d}.png')
                if os.path.exists(dst): continue          # resumable
                Image.fromarray(frame(pg, i / FPS, k_for(i / FPS))).save(dst + '.tmp.png')
                os.replace(dst + '.tmp.png', dst)
                if i % 40 == 0: print('front', i, '/', n, flush=True)
        b.close()


if __name__ == '__main__':
    main()
