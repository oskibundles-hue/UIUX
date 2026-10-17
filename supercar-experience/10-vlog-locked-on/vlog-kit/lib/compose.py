#!/usr/bin/env python3
"""compose.py -- lay the kit's motion layer over the footage, frame by frame (numpy + Pillow + ffmpeg).

Reads the scene that build.py wrote (.work/scene.json: shots with their plate specs), the layer PNGs that
lib/kcapture.js / lib/mockcap.js rendered from kit.html, and each frame's compositor sidecar (fx_<name>.json:
G2 glass panels, the I1 sweep line, the G1 plate punch). The plate mapping mirrors kit.html exactly (same
Ken Burns ease, same clip-frame mapping), so tracked brackets stay on their targets.

Plate specs:
  {kind:'clip', c0, t0, speed}      rooftop mezzanine frame (c0 + (t - t0) * speed) * fps; fractional frames
                                    (speed < 1) are a blend of the two neighbours
  {kind:'still', src, frame?, kb, t0, t1}   one image (a 4K rooftop still or a rally-cut frame), Ken Burns kb
  {kind:'split', seam, top, bottom} two specs, top above the seam, bottom below
  {kind:'black'}
Shot fx: 'whip' (lib/fx.py whip between aTail and bHead clip frames), 'sweep' (A right of the light band's
centre line, B left of it, soft edge), 'switch' (A until switchAt, B after).

Library use:  C = Composer(scene, work); img = C.frame(i, layer_png, fx_json)  -> uint8 HxWx3
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fx as FXL  # noqa: E402  (the showcase's fx.py: whip, blur helpers)

W, H = 1080, 1920
FPS = 30000 / 1001


def kb_ease(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


class Composer:
    def __init__(self, scene, work):
        self.S, self.work = scene, work
        self.cache = {}
        self.whips = {}

    # ------------------------------------------------------------------ sources
    def clip_frame(self, n):
        n = int(max(0, min(self.S['clipFrames'] - 1, n)))
        k = ('clip', n)
        if k not in self.cache:
            if len(self.cache) > 48:
                for kk in [kk for kk in self.cache if kk[0] == 'clip'][:24]:
                    del self.cache[kk]
            self.cache[k] = np.asarray(Image.open(os.path.join(self.work, 'plates', 'rooftop', f'{n:04d}.jpg')).convert('RGB'))
        return self.cache[k]

    def still(self, src):
        k = ('still', src)
        if k not in self.cache:
            self.cache[k] = Image.open(os.path.join(self.work, 'plates', 'still_' + src.replace(':', '_') + '.png')).convert('RGB')
        return self.cache[k]

    @staticmethod
    def kb_at(sp, t):
        k = sp.get('kb')
        if not k:
            return 1.0, 0.0, 0.0, 540.0, 960.0
        u = kb_ease((t - sp['t0']) / max(1e-6, sp['t1'] - sp['t0']))
        s = k['s0'] + (k['s1'] - k['s0']) * u
        dx = k.get('dx0', 0) + (k.get('dx1', 0) - k.get('dx0', 0)) * u
        dy = k.get('dy0', 0) + (k.get('dy1', 0) - k.get('dy0', 0)) * u
        return s, dx, dy, k.get('ax', 540), k.get('ay', 960)

    def render_spec(self, sp, t, punch=None):
        kind = sp['kind']
        if kind == 'black':
            return np.zeros((H, W, 3), np.uint8)
        if kind == 'split':
            top = self.render_spec(sp['top'], t, punch)
            bot = self.render_spec(sp['bottom'], t, punch)
            out = bot.copy(); out[:sp['seam']] = top[:sp['seam']]
            return out
        if kind == 'clip':
            fp = (sp['c0'] + (t - sp['t0']) * sp.get('speed', 1)) * FPS
            f0 = math.floor(fp + 1e-6); a = fp - f0
            img = self.clip_frame(f0)
            if a > 0.02:
                img = (img.astype(np.float32) * (1 - a) + self.clip_frame(f0 + 1).astype(np.float32) * a + 0.5).astype(np.uint8)
            if punch:
                img = np.asarray(self.affine(Image.fromarray(img), 1.0, 0, 0, 540, 960, 1.0, punch))
            return img
        if kind == 'still':
            im = self.still(sp['src'])
            s, dx, dy, ax, ay = self.kb_at(sp, t)
            return np.asarray(self.affine(im, s, dx, dy, ax, ay, im.width / W, punch))
        raise ValueError(kind)

    @staticmethod
    def affine(im, s, dx, dy, ax, ay, res, punch=None):
        """output (X, Y) shows source point ((X - ax - dx)/s + ax, (Y - ay - dy)/s + ay) in 1080x1920 units;
        res = source px per unit. An optional punch {s, dx, dy} scales/shifts the result about the centre."""
        a, c = 1 / s, ax - (ax + dx) / s
        e, f = 1 / s, ay - (ay + dy) / s
        if punch:
            ps, pdx, pdy = punch.get('s', 1), punch.get('dx', 0), punch.get('dy', 0)
            # X_final = 540 + ps (X - 540) + pdx  ->  X = (X_final - 540 - pdx)/ps + 540
            pa, pc = 1 / ps, 540 - (540 + pdx) / ps
            pe, pf = 1 / ps, 960 - (960 + pdy) / ps
            c = a * pc + c; a = a * pa
            f = e * pf + f; e = e * pe
        coeffs = (a * res, 0, c * res, 0, e * res, f * res)
        return im.transform((W, H), Image.AFFINE, coeffs, Image.BICUBIC)

    def whip_frames(self, shot):
        if shot['id'] not in self.whips:
            a = [self.clip_frame(n).astype(np.float32) / 255 for n in shot['aTail']]
            b = [self.clip_frame(n).astype(np.float32) / 255 for n in shot['bHead']]
            fr = FXL.whip(a, b, direction=shot.get('dir', 'left'), dist=shot.get('dist', 0.9))
            self.whips[shot['id']] = [np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8) for f in fr]
        return self.whips[shot['id']]

    # ------------------------------------------------------------------ frame
    def shot_at(self, t):
        for s in self.S['shots']:
            if s['t0'] - 1e-6 <= t < s['t1'] - 1e-6:
                return s
        return self.S['shots'][-1]

    def plate(self, i, fxd):
        t = i / FPS
        s = self.shot_at(t)
        punch = fxd.get('punch')
        fxk = s.get('fx')
        if fxk == 'whip':
            k = int(round((t - s['t0']) * FPS))
            fr = self.whip_frames(s)
            return fr[max(0, min(len(fr) - 1, k))]
        if fxk == 'switch':
            return self.render_spec(s['a'] if t < s['switchT'] - 1e-6 else s['b'], t, punch)
        if fxk == 'sweep':
            A = self.render_spec(s['a'], t, punch).astype(np.float32)
            B = self.render_spec(s['b'], t, punch).astype(np.float32)
            wp = fxd.get('wipe')
            if not wp:
                return (B if t >= (s['t0'] + s['t1']) / 2 else A).astype(np.uint8)
            Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
            xl = wp['x'] + wp['k'] * (Y - 960)          # band centre line (new plate on the left)
            m = np.clip((xl - X) / wp.get('soft', 24) * 0.5 + 0.5, 0, 1)[..., None]
            return (B * m + A * (1 - m) + 0.5).astype(np.uint8)
        return self.render_spec(s['plate'], t, punch)

    def frame(self, i, layer_path, fx_path=None):
        fxd = json.load(open(fx_path)) if fx_path and os.path.exists(fx_path) else {}
        base = self.plate(i, fxd).astype(np.float32)
        for g in fxd.get('glass', []):
            x0, y0 = int(round(g['x'])), int(round(g['y']))
            x1, y1 = int(round(g['x'] + g['w'])), int(round(g['y'] + g['h']))
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            if x1 - x0 < 4 or y1 - y0 < 4:
                continue
            pad = 60
            X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
            reg = base[Y0:Y1, X0:X1] / 255.0
            small = FXL.down(reg[: (Y1 - Y0) // 4 * 4, : (X1 - X0) // 4 * 4], 4)
            small = FXL.gauss(small, g.get('blur', 26) / 4)
            up = np.asarray(Image.fromarray(np.clip(small * 255, 0, 255).astype(np.uint8)).resize((X1 - X0, Y1 - Y0), Image.BICUBIC)).astype(np.float32)
            sub = up[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] * (1 - g.get('dim', 0.4))
            op = g.get('op', 1)
            base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - op) + sub * op
        if layer_path and os.path.exists(layer_path):
            L = np.asarray(Image.open(layer_path).convert('RGBA')).astype(np.float32)
            a = L[..., 3:4] / 255.0
            base = base * (1 - a) + L[..., :3] * a
        return np.clip(base + 0.5, 0, 255).astype(np.uint8)
