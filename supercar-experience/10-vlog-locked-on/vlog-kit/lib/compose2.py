#!/usr/bin/env python3
"""compose2.py -- the set-2 compositor: lib/compose.py plus depth, windows and light.

Adds to Composer (the plate mapping stays identical to kit2.html, so tracked graphics stay on their targets):
  plate {kind:'clip', hfr:true}   frames from the 59.94 fps source (.work2/plates/rooftop60/NNNN.jpg, NNNN = 2 x the
                                  mezzanine frame): speed 0.5 is a true slow-motion, one source frame per reel frame
  plate {kind:'still', fg:{kb, matte}}   2.5D push: the background is the still with the subject inpainted out
                                  (still_<src>_bg.png) on the plate's own Ken Burns, the subject is laid back on top
                                  through its matte on a faster Ken Burns (fg.kb), so it moves forward off the background
  plate {kind:'still', matte}     a still whose subject matte is known (for depth / pop / sweep on a plain still)
  shot fx 'window'                A outside, B inside the mask pass (<name>_mask.png alpha)
Per-frame compositor instructions (fx_<name>.json, from kit2.html's window.FX):
  back (flag)  + depth {matte}     back pass over the plate, then the subject re-laid on top through its matte
  pop {matte, amt}                 outside the matte: darker and desaturated; inside: a small lift (C4 freeze)
  sweep {x, k, w, gain, glob, matte}   slanted light band, centre x + k (y - 960): strong on the matte, faint elsewhere
  grade {sat, con}                 saturation / contrast on the plate
  flash {a}                        warm white flash on the plate
Mattes (scene['mattes'][name]): {kind:'still', file} aligned with that still's source image (any size), or
{kind:'seq', dir} with one PNG per mezzanine frame (NNNN.png).
"""
import json, math, os
import numpy as np
from PIL import Image
from compose import Composer, W, H, FPS, kb_ease

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Composer2(Composer):
    def __init__(self, scene, work):
        super().__init__(scene, work)
        self.mc = {}

    # ------------------------------------------------------------------ sources
    def clip60(self, n):
        k = ('c60', n)
        if k not in self.cache:
            if len(self.cache) > 48:
                for kk in [kk for kk in self.cache if kk[0] in ('clip', 'c60')][:24]:
                    del self.cache[kk]
            self.cache[k] = np.asarray(Image.open(os.path.join(self.work, 'plates', 'rooftop60', f'{n:04d}.jpg')).convert('RGB'))
        return self.cache[k]

    def image(self, path, mode='RGB'):
        k = ('img', path, mode)
        if k not in self.cache:
            self.cache[k] = Image.open(path).convert(mode)
        return self.cache[k]

    def matte_img(self, name, sp=None, t=None):
        """the named matte as a PIL 'L' image in its own source geometry (a still's matte), or for a clip sequence at
        the plate's current frame."""
        m = self.S['mattes'][name]
        path = m['file'] if m['kind'] == 'still' else None
        if m['kind'] == 'seq':
            fp = (sp['c0'] + (t - sp['t0']) * sp.get('speed', 1)) * FPS
            path = os.path.join(m['dir'], f'{int(round(fp)):04d}.png')
        if not os.path.isabs(path):
            path = os.path.join(KIT, path)
        return self.image(path, 'L')

    def _kb(self, sp, kb, t):
        u = kb_ease((t - sp['t0']) / max(1e-6, sp['t1'] - sp['t0']))
        return (kb['s0'] + (kb['s1'] - kb['s0']) * u, kb.get('dx0', 0) + (kb.get('dx1', 0) - kb.get('dx0', 0)) * u,
                kb.get('dy0', 0) + (kb.get('dy1', 0) - kb.get('dy0', 0)) * u, kb.get('ax', 540), kb.get('ay', 960))

    def matte_on_screen(self, name, sp, t, kb=None):
        """the matte mapped to the screen exactly like its plate (float HxWx1, 0..1)."""
        im = self.matte_img(name, sp, t)
        if sp['kind'] == 'still':
            s, dx, dy, ax, ay = self._kb(sp, kb, t) if kb else self.kb_at(sp, t)
            im = self.affine(im, s, dx, dy, ax, ay, im.width / W)
        elif im.size != (W, H):
            im = im.resize((W, H), Image.BILINEAR)
        return (np.asarray(im).astype(np.float32) / 255.0)[..., None]

    # ------------------------------------------------------------------ plates
    def render_spec(self, sp, t, punch=None):
        if sp['kind'] == 'clip' and sp.get('hfr'):
            fp = (sp['c0'] + (t - sp['t0']) * sp.get('speed', 1)) * FPS
            return self.clip60(int(round(fp * 2)))
        if sp['kind'] == 'still' and sp.get('fg'):
            bg = self.image(os.path.join(self.work, 'plates', 'still_' + sp['src'].replace(':', '_') + '_bg.png'))
            s, dx, dy, ax, ay = self.kb_at(sp, t)
            base = np.asarray(self.affine(bg, s, dx, dy, ax, ay, bg.width / W, punch)).astype(np.float32)
            S, m = self.subject(sp, t)
            return (base * (1 - m) + S * m + 0.5).astype(np.uint8)
        return super().render_spec(sp, t, punch)

    def subject(self, sp, t):
        """(subject pixels, matte) on screen for a plate whose subject is matted: the fg of a 2.5D still, a still with a
        matte, or a clip with a per-frame matte sequence."""
        if sp['kind'] == 'still' and sp.get('fg'):
            fg = sp['fg']; im = self.still(sp['src'])
            s, dx, dy, ax, ay = self._kb(sp, fg['kb'], t)
            S = np.asarray(self.affine(im, s, dx, dy, ax, ay, im.width / W)).astype(np.float32)
            return S, self.matte_on_screen(fg['matte'], sp, t, fg['kb'])
        return None, None

    def spec_on_screen(self, s, t):
        if s.get('fx') == 'switch':
            return s['a'] if t < s['switchT'] - 1e-6 else s['b']
        if s.get('fx') == 'window':
            return s['b']
        return s.get('plate')

    # ------------------------------------------------------------------ frame
    def frame(self, i, layer_path, fx_path=None):
        fxd = json.load(open(fx_path)) if fx_path and os.path.exists(fx_path) else {}
        t = i / FPS
        s = self.shot_at(t)
        side = lambda suf: layer_path[:-4] + suf + '.png'
        if s.get('fx') == 'window':
            A = self.render_spec(s['a'], t).astype(np.float32)
            B = self.render_spec(s['b'], t).astype(np.float32)
            if fxd.get('mask') and os.path.exists(side('_mask')):
                M = np.asarray(Image.open(side('_mask')).convert('RGBA'))[..., 3:4].astype(np.float32) / 255.0
                base = A * (1 - M) + B * M
            else:
                base = A
        else:
            base = self.plate(i, fxd).astype(np.float32)
        sp = self.spec_on_screen(s, t)
        g = fxd.get('grade')
        if g:
            lum = (base @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
            base = lum + g.get('sat', 1) * (base - lum)
            base = (base - 118) * g.get('con', 1) + 118
        pop = fxd.get('pop')
        if pop and sp:
            m = self.matte_on_screen(pop['matte'], sp, t); a = pop['amt']
            lum = (base @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
            out = (base + (lum - base) * 0.72 * a) * (1 - 0.5 * a)
            inn = base * (1 + 0.1 * a) + 6 * a
            base = out * (1 - m) + inn * m
        sw = fxd.get('sweep')
        if sw and sp:
            m = self.matte_on_screen(sw['matte'], sp, t)
            Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
            d = (X - (sw['x'] + sw['k'] * (Y - 960))) / math.sqrt(1 + sw['k'] ** 2)
            band = np.exp(-(d / sw['w']) ** 2)[..., None]; core = np.exp(-(d / (sw['w'] * 0.28)) ** 2)[..., None]
            # the light catches what is already bright on the body (paint highlights, trim) more than the tyres and glass
            lum = np.clip((base @ np.array([0.2126, 0.7152, 0.0722], np.float32)) / 255.0, 0, 1)[..., None]
            amt = m * sw['gain'] * (0.22 + 1.1 * lum ** 1.3) + (1 - m) * sw['glob']
            L = np.clip(band * amt * np.array([1.0, 0.93, 0.7], np.float32) + core * amt * 0.8, 0, 1)
            base = 255 - (255 - np.clip(base, 0, 255)) * (1 - L)
        if fxd.get('back') and os.path.exists(side('_back')):
            Lb = np.asarray(Image.open(side('_back')).convert('RGBA')).astype(np.float32)
            a = Lb[..., 3:4] / 255.0
            plate_now = base.copy()
            base = base * (1 - a) + Lb[..., :3] * a
            dp = fxd.get('depth') or {}
            S, m = self.subject(sp, t) if sp else (None, None)
            if S is None and dp.get('matte'):
                S, m = plate_now, self.matte_on_screen(dp['matte'], sp, t)
            elif S is not None:
                S = plate_now          # the subject as already graded on the plate
            if S is not None:
                base = base * (1 - m) + S * m
        for gl in fxd.get('glass', []):
            x0, y0 = int(round(gl['x'])), int(round(gl['y'])); x1, y1 = int(round(gl['x'] + gl['w'])), int(round(gl['y'] + gl['h']))
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            if x1 - x0 >= 4 and y1 - y0 >= 4:
                from fx import down, gauss
                reg = base[y0:y1, x0:x1] / 255.0
                sm = gauss(down(reg[: (y1 - y0) // 4 * 4, : (x1 - x0) // 4 * 4], 4), gl.get('blur', 26) / 4)
                up = np.asarray(Image.fromarray(np.clip(sm * 255, 0, 255).astype(np.uint8)).resize((x1 - x0, y1 - y0), Image.BICUBIC)).astype(np.float32)
                base[y0:y1, x0:x1] = up * (1 - gl.get('dim', 0.4))
        fl = fxd.get('flash')
        if fl and fl.get('a', 0) > 0.003:
            base = base + (np.array([255, 250, 232], np.float32) - base) * fl['a']
        if layer_path and os.path.exists(layer_path):
            L = np.asarray(Image.open(layer_path).convert('RGBA')).astype(np.float32)
            a = L[..., 3:4] / 255.0
            base = base * (1 - a) + L[..., :3] * a
        return np.clip(base + 0.5, 0, 255).astype(np.uint8)
