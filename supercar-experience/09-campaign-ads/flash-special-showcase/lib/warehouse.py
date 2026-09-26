"""
warehouse.py -- beats 17-19 (12.0-18.0 s): the GT3 RS in the warehouse with giant type BEHIND the car.

Refactored from scratchpad/showcase/rnd-matte/demo_occlusion.py (render_frame) to
  * read copy from ../config.json (giant word, price) -- no figures in this file,
  * follow the final cue's timeline (edl.py): 0.45x, tape stop to a freeze, resume 0.37x,
  * take source frames by FRAME NUMBER from the decoded source (.work/src_gt.npy; the matte track
    index k is source frame 290 + k -- verified pixel-identical against the R&D ware.npy),
  * add the cue's plate FX: NightGrade, overhead-lamp streaks, impact luma lifts, tape-stop grade,
    leak drift and the bottom scrim.
The front HTML layer (requirements, end-card copy) is NOT drawn here.

Layer stack per frame (back -> front), each with its own 2.5D push about the tyre contact point:
    BACKGROUND  plate, car diffused out, graded to 55 % above the car          s_bg
    TYPE        Bebas giant "GT3" / "$1,200" rising out of the floor line      s_type
                (per-glyph, 6-sample motion blur, lit from above), floor hairline
    CAR         plate x car matte (+ floor under the tyres)                    s_car
                + light wrap of the type onto the car's edge
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import edl
import fx
import matte_lib as ml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.abspath(os.path.join(ROOT, '..', '..', '07-fonts')) + '/'
BEBAS = FONTS + 'BebasNeue-Regular.ttf'
W, H = 1080, 1920
GOLD = np.array([251, 209, 1], np.float32) / 255
WHITE = np.ones(3, np.float32)
ANCHOR = (560.0, 1255.0)           # tyre contact (REF coords, frame f312)
FLOOR_Y = 1088                     # letters rise out of this line
# Giant words are sized so that at FULL 2.5D push (type layer x1.040 about x=560) the ink stays
# inside x 54..907: GT3 720 px at ink-left 64 (831 wide), $1,200 372 px at ink-left 76 (815 wide).
# (The cue's 730 / 384 px at x 58 would reach x ~912 at full push.)
HERO_PX, HERO_L = 720, 64
PRICE_PX, PRICE_L = 372, 76
PUSH1 = (1.012, 1.019, 1.024)      # bg / type / car at the end of beat 17
PUSH2 = (1.025, 1.040, 1.050)      # ... at 18.0 s


def cl(x):
    return max(0.0, min(1.0, x))


def out_expo(x):
    x = cl(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def in_cubic(x):
    return cl(x) ** 3


def out_cubic(x):
    return 1 - (1 - cl(x)) ** 3


def in_out_cubic(x):
    x = cl(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def out_back(x, s=1.2):
    x = cl(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def glyph_row(text, size):
    """Per-glyph alpha sprites on one baseline, advance-width spacing (no kerning pairs -- the
    HTML slot price places glyphs the same way, so the two $1,200s match), Bebas letter-spacing 0.
    Returns (glyphs [(sprite, x_off)], asc, ink_left_bearing)."""
    f = ImageFont.truetype(BEBAS, size)
    asc = f.getmetrics()[0]
    out, x = [], 0.0
    for ch in text:
        adv = f.getlength(ch)
        pad = int(size * 0.1)
        im = Image.new('L', (int(adv + 2 * pad), int(size * 1.25)), 0)
        ImageDraw.Draw(im).text((pad, 0), ch, font=f, fill=255)
        out.append((np.asarray(im, np.float32) / 255, x - pad))
        x += adv
    lb = f.getbbox(text[0])[0]
    return out, asc, lb


def paste(dst_rgb, dst_a, spr_rgb, spr_a, x, y, op=1.0):
    x, y = int(round(x)), int(round(y))
    h, w = spr_a.shape
    DH, DW = dst_a.shape
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, DW), min(y + h, DH)
    if x1 <= x0 or y1 <= y0 or op <= 0:
        return
    sa = spr_a[y0 - y:y1 - y, x0 - x:x1 - x] * op
    sr = spr_rgb[y0 - y:y1 - y, x0 - x:x1 - x] * op
    dst_rgb[y0:y1, x0:x1] = sr + dst_rgb[y0:y1, x0:x1] * (1 - sa[..., None])
    dst_a[y0:y1, x0:x1] = sa + dst_a[y0:y1, x0:x1] * (1 - sa)


class Warehouse:
    def __init__(self, work, config):
        C = json.load(open(config))
        self.C = C
        self.m = np.load(os.path.join(work, 'src_gt.npy'), mmap_mode='r')
        tr = json.load(open(os.path.join(HERE, 'data', 'ware_track.json')))
        self.dy, self.dx = np.array(tr['dy']), np.array(tr['dx'])
        self.ref = edl.WARE_F0 + tr['ref']                        # f312
        alpha = np.asarray(Image.open(os.path.join(HERE, 'data', 'matte_ref.png')), np.float32) / 255
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        contact = 1300 - (xx - 150) * (1300 - 1212) / (960 - 150)
        floor = np.clip((yy - contact + 10) / 70, 0, 1)
        self.fg = np.maximum(alpha, floor)
        self.hole = ml.dilate((alpha > 0.02).astype(np.float32), 9)
        self.look = fx.NightGrade.fit(np.asarray(self.m[edl.WARE_START:335]))
        ref = self.look(self.m[self.ref].astype(np.float32) / 255)
        self.fill = ml.inpaint_diffuse(ref, self.hole)
        self.bg_grade = (0.55 + 0.45 * np.clip((yy - 980) / 200, 0, 1))[..., None]
        self.hero = glyph_row(C['giant'], HERO_PX)
        self.price = glyph_row(C['price'], PRICE_PX)
        self._last = None

    # ---------------------------------------------------------------- timeline
    @staticmethod
    def push(t):
        """(s_bg, s_type, s_car) at output time t."""
        a = in_out_cubic((t - 12.0) / (edl.T_STOP0 - 12.0))
        s = [1 + (p - 1) * a for p in PUSH1]
        if t > edl.T_END:
            b = out_cubic((t - edl.T_END) / (18.0 - edl.T_END))
            s = [p1 + (p2 - p1) * b for p1, p2 in zip(PUSH1, PUSH2)]
        return s

    def hero_offsets(self, t):
        n = len(self.C['giant'])
        rise0 = [12.05 + 0.08 * k for k in range(n)]
        offs = []
        for k in range(n):
            rise = 1 - out_expo((t - rise0[k]) / 0.55)
            ks = n - 1 - k                                      # sink order: 3, T, G
            sink = in_cubic((t - edl.T_STOP0 - 0.05 * ks) / (14.15 - edl.T_STOP0 - 0.05 * (n - 1)))
            offs.append(640 * rise + 720 * sink)
        return offs

    @staticmethod
    def price_offset(t):
        return 470 * (1 - out_back((t - 15.189) / (edl.T_END - 15.189), 1.2)) if t < edl.T_END else 0.0

    # ---------------------------------------------------------------- type layer
    def _word(self, rgb, a, row, baseline, offs, color, ink_l):
        glyphs, asc, lb = row
        x0 = ink_l - lb
        for (spr, gx), oy in zip(glyphs, offs):
            if oy > 900:
                continue
            paste(rgb, a, spr[..., None] * color[None, None], spr, x0 + gx, baseline - asc + oy)

    def type_layer(self, t):
        acc_rgb = np.zeros((H, W, 3), np.float32)
        acc_a = np.zeros((H, W), np.float32)
        sh = 0.5 / edl.FPS
        def state(tt):
            return self.hero_offsets(tt), self.price_offset(tt)
        s0, s1 = state(t - sh / 2), state(t + sh / 2)
        moving = s0 != s1
        ts = [t + sh * (j / 5 - 0.5) for j in range(6)] if moving else [t]
        y0, y1 = 360, 1120
        for tt in ts:
            rgb = np.zeros((y1 - y0, W, 3), np.float32)
            a = np.zeros((y1 - y0, W), np.float32)
            ho, po = state(tt)
            self._word(rgb, a, self.hero, FLOOR_Y - y0, ho, WHITE, HERO_L)
            if tt >= 15.189:
                self._word(rgb, a, self.price, 968 - y0, [po] * len(self.C['price']), GOLD, PRICE_L)
            acc_rgb[y0:y1] += rgb
            acc_a[y0:y1] += a
        acc_rgb /= len(ts)
        acc_a /= len(ts)
        r, a = acc_rgb[y0:y1], acc_a[y0:y1]
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]
        clip = np.clip((FLOOR_Y + 2 - yy) / 4, 0, 1)
        r = r * clip[..., None]
        a = a * clip
        # glint on the price 16.29-16.75 (band tilted 18 deg, warm -> hot, painted into the letters)
        q = (t - 16.29) / (16.75 - 16.29)
        if 0 < q < 1:
            e = in_out_cubic(q)
            xx = np.arange(W, dtype=np.float32)[None, :]
            pos = -150 + 1250 * e
            d = (xx - (yy - 634) * math.tan(math.radians(18))) - pos
            band = np.exp(-(d / 70) ** 2)[..., None] * (a[..., None] > 0)
            warm = np.array([1.0, 0.965, 0.816], np.float32)
            is_gold = (r[..., 2:3] < 0.5 * np.maximum(r[..., 0:1], 1e-4)).astype(np.float32)
            tgt = warm * a[..., None]
            r = r + (tgt - r) * band * is_gold * 0.95
        # lit from the overhead lamp: brighter at the top; gold falls off less (stays #FBD101)
        fall = np.clip((yy - 480) / 600, 0, 1)
        gold_w = (r[..., 2:3] < 0.5 * r[..., 0:1]).astype(np.float32)
        light = 1.0 - fall[..., None] * (0.28 * (1 - gold_w) + 0.06 * gold_w)
        r = r * light
        # floor hairline 14.80-15.30, drawn L -> R, 2 px, behind the car
        hq = out_cubic((t - 14.80) / 0.50)
        if hq > 0:
            xe = HERO_L + (895 - HERO_L) * hq
            ry = FLOOR_Y - y0
            xs = np.arange(W, dtype=np.float32)
            cov = np.clip(xe - xs, 0, 1) * (xs >= HERO_L)
            for dy_ in (-1, 0):
                r[ry + dy_] = r[ry + dy_] * (1 - cov[:, None]) + GOLD[None] * cov[:, None]
                a[ry + dy_] = np.maximum(a[ry + dy_], cov)
        r = ml.gauss_blur(r, 0.55)
        a = ml.gauss_blur(a, 0.55)
        acc_rgb[:] = 0
        acc_a[:] = 0
        acc_rgb[y0:y1] = r
        acc_a[y0:y1] = a
        return acc_rgb * 0.96, acc_a * 0.96

    # ---------------------------------------------------------------- frame
    def plate_at(self, p):
        k = p - edl.WARE_F0
        i0 = int(math.floor(k + 1e-6))
        w = k - i0
        i1 = min(i0 + 1, 44)
        img = self.m[edl.WARE_F0 + i0].astype(np.float32)
        if w > 1e-3:
            img = img * (1 - w) + self.m[edl.WARE_F0 + i1].astype(np.float32) * w
        n = np.arange(len(self.dy))
        return img / 255, float(np.interp(k, n, self.dy)), float(np.interp(k, n, self.dx))

    def render(self, i, r):
        t = r['t']
        img, dy, dx = self.plate_at(r['p'])
        img = self.look(img)
        img = fx.streaks(img, thresh=0.85, point=0.12, point_radius=90, gain=0.8)
        sb, st, sc = self.push(t)
        cx, cy = ANCHOR[0] + dx, ANCHOR[1] + dy
        fg = ml.shift(self.fg, dy, dx)
        hole = ml.shift(self.hole, dy, dx)
        fill = ml.shift(self.fill, dy, dx)
        bg = img * (1 - hole[..., None]) + fill * hole[..., None]
        bg = bg * self.bg_grade
        bg = ml.scale_about(bg, sb, cx, cy)
        car = ml.scale_about(img * fg[..., None], sc, cx, cy)
        fga = ml.scale_about(fg, sc, cx, cy)
        trgb, ta = self.type_layer(t)
        trgb = ml.scale_about(trgb, st, ANCHOR[0], ANCHOR[1], dy, dx)
        ta = ml.scale_about(ta, st, ANCHOR[0], ANCHOR[1], dy, dx)
        out = trgb + bg * (1 - ta[..., None])
        b0, b1 = 840, 1140
        inner = np.clip(fga[b0:b1] - ml.gauss_blur(fga[b0:b1], 2.5), 0, 1) * 2.2
        wrap = np.zeros_like(car)
        wrap[b0:b1] = ml.gauss_blur(trgb[b0:b1], 4.0) * np.clip(inner, 0, 1)[..., None] * 0.55
        out = car + wrap + out * (1 - fga[..., None])
        out = np.clip((out - 0.5) * 1.05 + 0.5, 0, None)
        # impact_2: 1-frame 25 % luma lift + zoom 1.04 -> 1.0 ; impact_3: 1-frame 20 % lift
        k2 = i - edl.fr(12.0)
        if 0 <= k2 < 10:
            out = fx.transform(out, scale=1.0 + 0.04 * (1 - out_cubic(k2 / 9)))
        if k2 == 0:
            out = out * 1.25
        if i == edl.fr(15.429):
            out = out * 1.20
        # tape stop: -15 % luma, -20 % saturation (easeIn), recovers inOutCubic 14.571-15.429
        g = in_cubic((t - edl.T_STOP0) / (edl.T_STOP1 - edl.T_STOP0))
        if t > edl.T_SWELL:
            g *= 1 - in_out_cubic((t - edl.T_SWELL) / (edl.T_END - edl.T_SWELL))
        if g > 1e-4:
            l = fx.luma(out)[..., None]
            out = (l + (out - l) * (1 - 0.20 * g)) * (1 - 0.15 * g)
        # beat 19: warm leak drift + bottom scrim (0 -> 55 % black, y 1250-1920)
        if t > edl.T_END - 0.05:
            lk = 0.15 * out_cubic((t - edl.T_END) / 0.8)
            out = fx.light_leak(out, t, strength=lk, seed=11, side='right')
            sc_ = out_cubic((t - (edl.T_END - 0.05)) / 0.35)
            yy = np.arange(H, dtype=np.float32)[:, None, None]
            out = out * (1 - 0.55 * sc_ * np.clip((yy - 1250) / 670, 0, 1))
        return out.astype(np.float32)
