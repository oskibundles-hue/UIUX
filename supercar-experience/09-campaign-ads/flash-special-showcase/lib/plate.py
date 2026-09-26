"""
plate.py -- renders the picture plate (everything under the front HTML layer) for the showcase.

Per output frame (see edl.py for the beat table):
  source sample (frame-number exact, blended / shutter-averaged / optical-flow) -> NightGrade
  (fitted per shot) -> anamorphic streaks -> beat transform (push / punch / shake + RGB split)
  -> whip or impact across cuts -> light leak.  Warehouse frames (beats 17-19) come from
  warehouse.py (matte occlusion, behind-car type, 2.5D push) instead.

Writes uint8 RGB frames into a (432,1920,1080,3) .npy memmap; vignette + grain are applied later
on the composite (finish step in build.py) so they sit on top of the type as well.

Uses lib/fx.py (copied from scratchpad/showcase/rnd-fx/fx.py) for grade, streaks, whip, impact,
leak, transforms.
"""
import math
import os
import subprocess

import numpy as np

import edl
import fx

H, W = 1920, 1080


class Src:
    """Frame-number-addressed source (GT3RS_livery.mov decoded in order to a .npy)."""

    def __init__(self, npy, dense_npy=None):
        self.m = np.load(npy, mmap_mode='r')
        self.dense = {}
        if dense_npy:
            for bid, (path, fa, k) in dense_npy.items():
                self.dense[bid] = (np.load(path, mmap_mode='r'), fa, k)
        self._c = {}

    def f(self, n):
        n = int(n)
        if n not in self._c:
            if len(self._c) > 6:
                self._c.pop(next(iter(self._c)))
            self._c[n] = self.m[n].astype(np.float32) * (1 / 255)
        return self._c[n]

    def at(self, p, B):
        p = min(max(p, B['fa']), B['fb'])
        d = self.dense.get(B['id'])
        if d is not None:
            arr, fa, k = d
            x = (p - fa) * k
            if 0 <= x <= len(arr) - 1:
                i = int(math.floor(x))
                w = x - i
                if w < 0.15 or i + 1 >= len(arr):
                    return arr[i].astype(np.float32) * (1 / 255)
                if w > 0.85:
                    return arr[i + 1].astype(np.float32) * (1 / 255)
                return (arr[i].astype(np.float32) * (1 - w) + arr[i + 1].astype(np.float32) * w) * (1 / 255)
        i = int(math.floor(p + 1e-6))
        w = p - i
        if w < 1e-3 or i >= B['fb']:
            return self.f(i)
        return self.f(i) * (1 - w) + self.f(i + 1) * w

    def sample(self, p, span, B):
        nsub = int(math.ceil(span * 1.5 - 1e-6))
        if nsub <= 1:
            return self.at(p, B)
        acc = None
        for j in range(nsub):
            fr = self.at(p - span / 2 + span * (j + 0.5) / nsub, B)
            acc = fr.copy() if acc is None else acc + fr
        return acc / nsub


# ------------------------------------------------------------------------ build-time helpers
def plate_blur(npy, track_json, name='plate', f0=226, f1=246, pad=14, radius=8, feather=6, sigma=12):
    """Blur the Montana licence plate in place on source frames f0..f1 (tracked box `name`)."""
    import json
    from PIL import Image, ImageDraw
    import matte_lib as ml
    tr = json.load(open(track_json))[name]
    m = np.load(npy, mmap_mode='r+')
    for fr_ in tr['frames']:
        f = fr_['f']
        if not (f0 <= f <= f1):
            continue
        x0, y0 = fr_['x'] - pad, fr_['y'] - pad
        x1, y1 = fr_['x'] + fr_['w'] + pad, fr_['y'] + fr_['h'] + pad
        M = 60
        cx0, cy0 = int(x0) - M, int(y0) - M
        cx1, cy1 = min(int(math.ceil(x1)) + M, W), min(int(math.ceil(y1)) + M, H)
        cx0, cy0 = max(cx0, 0), max(cy0, 0)
        crop = m[f, cy0:cy1, cx0:cx1].astype(np.float32) / 255
        ss = 4
        im = Image.new('L', ((cx1 - cx0) * ss, (cy1 - cy0) * ss), 0)
        ImageDraw.Draw(im).rounded_rectangle([(x0 - cx0 - feather / 2) * ss, (y0 - cy0 - feather / 2) * ss,
                                              (x1 - cx0 + feather / 2) * ss, (y1 - cy0 + feather / 2) * ss],
                                             radius=radius * ss, fill=255)
        mask = np.asarray(im.resize((cx1 - cx0, cy1 - cy0), Image.BOX), np.float32) / 255
        mask = np.clip(ml.gauss_blur(mask, feather / 2.0) * 1.0, 0, 1)
        b = ml.gauss_blur(ml.gauss_blur(crop, sigma), sigma)
        out = crop * (1 - mask[..., None]) + b * mask[..., None]
        m[f, cy0:cy1, cx0:cx1] = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    m.flush()


def make_dense(ffmpeg, npy, fa, fb, k, out_npy):
    """Optical-flow in-betweens for source frames fa..fb (inclusive) at k x density, fed by frame
    number through a pipe (no seeking). Output index j <-> source position fa + j / k."""
    m = np.load(npy, mmap_mode='r')
    fps = f'{24000 * k}/1001'
    cmd = [ffmpeg, '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', '24000/1001', '-i', '-', '-threads', '2',
           '-vf', f'minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    tmp = out_npy + '.raw'
    with open(tmp, 'wb') as fo:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=fo)
        # the last input frame is repeated so minterpolate emits the full tail (it drops ~1 src frame)
        for n in list(range(fa, fb + 1)) + [fb, fb]:
            p.stdin.write(np.ascontiguousarray(m[n]).tobytes())
        p.stdin.close()
        p.wait()
    raw = np.fromfile(tmp, np.uint8).reshape(-1, H, W, 3)
    n = (fb - fa) * k + 1
    assert len(raw) >= n, (len(raw), n)
    np.save(out_npy, raw[:n])
    os.remove(tmp)
    return out_npy


# ------------------------------------------------------------------------ per-frame render
def ease_out_cubic(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


class Plate:
    def __init__(self, work, tl, ware=None):
        self.work = work
        self.tl = tl
        dn = {}
        for B in edl.BEATS:
            if 'dense' in B:
                fa, fb, k = B['dense']
                dn[B['id']] = (os.path.join(work, f'dense_b{B["id"]}_{fa}_{fb}_{k}.npy'), fa, k)
        self.src = Src(os.path.join(work, 'src_gt.npy'), dn)
        self.grades = {}
        self.ware = ware
        self.whip_at = {edl.fr(t): d for t, d in edl.WHIPS}

    def grade(self, B):
        if B['id'] not in self.grades:
            self.grades[B['id']] = fx.NightGrade.fit(np.asarray(self.src.m[B['fa']:B['fb'] + 1]))
        return self.grades[B['id']]

    def base(self, i):
        """Graded + streaked + transformed frame, before whip / impact / leak (float32)."""
        r = self.tl[i]
        B = edl.beat(r['beat'])
        if B.get('black'):
            return np.zeros((H, W, 3), np.float32)
        if B.get('ware'):
            return self.ware.render(i, r)
        f = self.src.sample(r['p'], r['span'], B)
        f = self.grade(B)(f)
        if 'streak' in B:
            f = fx.streaks(f, **B['streak'])
        if 'streak_split' in B:
            y, top, bot = B['streak_split']
            st_t = fx.streaks(f, **dict(top, gain=1.0)) - f
            st_b = fx.streaks(f, **dict(bot, gain=1.0)) - f
            yy = np.arange(H, dtype=np.float32)[:, None, None]
            wb = np.clip((yy - (y - 40)) / 80, 0, 1)
            f = f + st_t * top['gain'] * (1 - wb) + st_b * bot['gain'] * wb
        t = r['t']
        # beats 1-5: one continuous push 1.00 -> 1.03 (outCubic, 0 -> 3.25 s)
        if r['beat'] <= 5:
            a0, a1, s0, s1 = edl.PUSH_A
            sc = s0 + (s1 - s0) * ease_out_cubic((t - a0) / (a1 - a0))
            dx = dy = rot = 0.0
            if r['beat'] == 4:
                n = B['i1'] - B['i0']
                sc *= 1.0 + 0.04 * edl.smootherstep(r['j'] / (n - 1))
            kp = i - edl.fr(edl.PUNCH_T)
            if kp in (0, 1):
                sc *= (1.03, 1.015)[kp]
            if r['beat'] == 1 and 1 <= i <= 8:
                dx, dy, rot = fx.shake_offsets(i - 1, amp=6.0, freq=11.0, decay=5.0, seed=3, rot_amp=0.15)
            f = fx.transform(f, dx, dy, max(sc, 1.0), rot)
            if r['beat'] == 1 and 1 <= i <= 8:
                f = fx.chroma_split(f, 7.0 * math.exp(-(i - 1) / 2.4), radial=True)
        return f

    def post(self, i, f):
        """impact (beat 14) and light leaks, after whips."""
        k = i - edl.DROP_FRAME
        if 0 <= k < 16:
            f = fx.impact(f, k, strength=1.0, seed=edl.IMPACT_SEED)
        side, lk = 'left', 0.0
        best = 0
        for tc, peak, sd, sig in edl.LEAKS:
            v = peak * math.exp(-((i - tc * edl.FPS) / sig) ** 2)
            lk += v
            if v > best:
                best, side = v, sd
        if lk > 0.004:
            f = fx.light_leak(f, i / edl.FPS, strength=lk, seed=3, side=side)
        return f

    def units(self, frames):
        """Group requested frames into render units; whip windows render as one unit of 2k."""
        k = edl.WHIP_K
        want = set(frames)
        units, used = [], set()
        for b in sorted(self.whip_at):
            win = list(range(b - k, b + k))
            if want & set(win):
                units.append(('whip', b, win))
                used |= set(win)
        for i in sorted(want - used):
            units.append(('one', i, [i]))
        return units

    def render_unit(self, u):
        kind, b, win = u
        if kind == 'one':
            return {b: self.post(b, self.base(b))}
        k = edl.WHIP_K
        fr_ = [self.base(i) for i in win]
        out = fx.whip(fr_[:k], fr_[k:], direction=self.whip_at[b], dist=0.9)
        return {i: self.post(i, f) for i, f in zip(win, out)}
