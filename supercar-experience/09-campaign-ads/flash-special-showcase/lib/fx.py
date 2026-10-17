"""
fx.py -- reusable edit + compositing FX for SE vertical spots (numpy + Pillow + ffmpeg).

No OpenCV / scipy. Every function works on float32 RGB frames, shape (H, W, 3), values
0..1 (display-referred, gamma-encoded, i.e. what ffmpeg hands us). Values above 1 are
allowed mid-pipeline (flashes, streaks) and clipped only on write.

------------------------------------------------------------------------------------------
QUICK START
------------------------------------------------------------------------------------------
    import fx
    src = fx.Source(fx.FOOT + "/BlackSeries.mov", 8.03, 9.15,
                    dense=[(8.25, 0.75, 4)])          # optional minterpolate'd slow-mo span
    times = fx.ramp_times(src.t0, n_out=36,
                          keys=[(0, 1.6), (0.35, 0.3), (1, 0.3)])   # eased speed ramp
    frames = [src.sample(t, span) for t, span in times]              # blended / motion-blurred
    look   = fx.NightGrade.fit(src.frames)                           # per-clip normalise
    f = look(frames[0]); f = fx.streaks(f); f = fx.grain(f, 3); f = fx.vignette(f)
    with fx.Writer("out.mp4") as w: w.write(f)

------------------------------------------------------------------------------------------
API (all pure functions unless noted)
------------------------------------------------------------------------------------------
IO
  read_frames(path, t0, dur)            -> uint8 (N,H,W,3)  frame-accurate decode via ffmpeg
  minterp_frames(path, t0, dur, factor) -> uint8 (N*factor..)  optical-flow in-betweens
                                           (ffmpeg minterpolate mci/aobmc, cached on disk;
                                           ~85 s CPU per 1 s of source at 4x -- use sparingly)
  Writer(path, fps, crf, audio=None)     context manager; .write(float_frame)
  Source(path, t0, t1, dense=[(a, dur, factor)])
        .sample(t_src, span_s)          -> float frame. span_s = shutter span in source
                                           seconds. span > 1 src frame => motion-blur average;
                                           inside a dense span => optical-flow frames.

RETIME
  ramp_times(t_start, n_out, keys, shutter=0.5, fps=FPS)
        keys = [(u, speed), ...], u in 0..1 over the output shot, speed = source-sec per
        output-sec. Speed is eased (smootherstep) between keys and integrated per frame,
        so ramps are smooth, never stepped. Returns [(t_src, span_s), ...].

TRANSITIONS
  whip(a_tail, b_head, direction="left", dist=0.9, blur=1.0, bright=0.15)
        Whip-pan across the cut: A accelerates out, B decelerates in, directional blur
        proportional to the per-frame velocity, 1-frame mix at the seam. direction in
        left/right/up/down. a_tail and b_head are lists of frames (use 3+3 or 4+4).
  impact(frame, k, strength=1.0, seed=0)
        Frame k (0,1,2,...) after a hard cut/hit: 2-frame flash (k=0,1), zoom punch,
        decaying camera shake, RGB split, zoom blur on the first frames.

PER-FRAME FX
  shake_offsets(k, amp, freq, decay, seed) -> (dx, dy, rot_deg)
  transform(img, dx=0, dy=0, scale=1, rot=0)      affine about centre, edge-safe
  dir_blur(img, length_px, axis)                    O(1)/px box blur (cumsum), 3 passes
  zoom_blur(img, amount, center, n)
  chroma_split(img, amount_px, radial=True)         R out / B in, lateral CA
  flash(img, amount, color)
  streaks(img, thresh, length, gain, tint, core)    anamorphic: bright-pass -> wide H blur
  bloom(img, thresh, radius, gain)
  light_leak(img, t, strength, seed, palette)       generated drifting warm leak (screen)
  grain(img, idx, amount)                           luma-weighted, cached plates
  vignette(img, strength)
  NightGrade.fit(frames, **look)(img)               cohesive night grade (see class doc)

AUDIO (numpy -> wav, 48 kHz)
  sfx_whoosh(dur), sfx_hit(), mix_to_wav(events, total_dur, path)

Brand accent (light leaks default palette) = SE gold #FBD101.
"""
import os
import math
import hashlib
import subprocess
import wave

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.abspath(os.path.join(HERE, "..", ".."))
FFMPEG = os.environ.get("FFMPEG", os.path.join(SCRATCH, "ffmpeg"))
FOOT = os.path.join(SCRATCH, "footage")
CACHE = os.path.join(HERE, "cache")
FPS = 24000 / 1001
W, H = 1080, 1920
GOLD = (251 / 255, 209 / 255, 1 / 255)


# ------------------------------------------------------------------------------------ IO
def read_frames(path, t0, dur, w=W, h=H):
    """Decode [t0, t0+dur) to uint8 (N,h,w,3). -ss before -i is frame-accurate for .mov/.mp4."""
    cmd = [FFMPEG, "-loglevel", "error", "-ss", f"{t0:.4f}", "-i", path, "-t", f"{dur:.4f}",
           "-vf", f"scale={w}:{h}:flags=bicubic", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def minterp_frames(path, t0, dur, factor=4):
    """Optical-flow slow-mo source: `factor` x frame density over [t0, t0+dur). Cached."""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5(f"{path}|{t0:.4f}|{dur:.4f}|{factor}".encode()).hexdigest()[:12]
    out = os.path.join(CACHE, f"mi_{key}.mp4")
    if not os.path.exists(out):
        # pad the decode by 1 source frame each side so the first/last in-betweens exist
        vf = (f"minterpolate=fps={24000 * factor}/1001:mi_mode=mci:mc_mode=aobmc:"
              f"me_mode=bidir:vsbmc=1")
        subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-ss", f"{t0:.4f}", "-i", path,
                        "-t", f"{dur:.4f}", "-vf", vf, "-c:v", "libx264", "-crf", "10",
                        "-preset", "veryfast", "-pix_fmt", "yuv420p", out], check=True)
    return read_frames(out, 0, dur + 1)


class Writer:
    """Pipe float frames into libx264 (yuv420p, story-ready). Optional wav muxed on close."""

    def __init__(self, path, fps_str="24000/1001", crf=16, audio=None):
        self.path, self.audio = path, audio
        self.tmp = path if audio is None else path + ".v.mp4"
        self.p = subprocess.Popen(
            [FFMPEG, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", fps_str, "-i", "-", "-c:v", "libx264", "-preset", "medium",
             "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", self.tmp],
            stdin=subprocess.PIPE)
        self.n = 0

    def write(self, img):
        self.p.stdin.write(to_u8(img).tobytes())
        self.n += 1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.p.stdin.close()
        self.p.wait()
        if self.audio:
            subprocess.run([FFMPEG, "-loglevel", "error", "-y", "-i", self.tmp, "-i", self.audio,
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                            self.path], check=True)
            os.remove(self.tmp)


def to_f(u8):
    return u8.astype(np.float32) * (1 / 255)


def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


class Source:
    """A decoded source range with optional optical-flow dense sub-ranges for slow motion.

    dense = [(a, dur, factor)] : minterpolate [a, a+dur) at factor x density.
    """

    def __init__(self, path, t0, t1, dense=()):
        self.path, self.t0, self.t1 = path, t0, t1
        self.frames = read_frames(path, t0, t1 - t0)
        self.dense = []
        for a, dur, k in dense:
            self.dense.append((a, dur, k, minterp_frames(path, a, dur, k)))

    def _orig(self, t):
        x = (t - self.t0) * FPS
        n = len(self.frames) - 1
        x = min(max(x, 0.0), n)
        i = int(math.floor(x))
        f = x - i
        a = self.frames[i]
        if f < 1e-3 or i >= n:
            return to_f(a)
        return to_f(a) * (1 - f) + to_f(self.frames[i + 1]) * f

    def _at(self, t):
        for a, dur, k, fr in self.dense:
            if a <= t <= a + dur - 1 / FPS:
                x = min((t - a) * FPS * k, len(fr) - 1)
                i = int(math.floor(x))
                f = x - i
                if f < 0.15 or i + 1 >= len(fr):
                    return to_f(fr[i])
                if f > 0.85:
                    return to_f(fr[i + 1])
                return to_f(fr[i]) * (1 - f) + to_f(fr[i + 1]) * f
        return self._orig(t)

    def sample(self, t, span=0.0):
        """Frame at source time t. span (s) > one source frame => shutter-average (motion blur)."""
        nsub = int(math.ceil(span * FPS * 1.5))
        if nsub <= 1:
            return self._at(t)
        acc = None
        for j in range(nsub):
            tt = t - span / 2 + span * (j + 0.5) / nsub
            fr = self._at(tt)
            acc = fr if acc is None else acc + fr
        return acc / nsub


# ------------------------------------------------------------------------------ RETIME
def smootherstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (x * 6 - 15) + 10)


def speed_at(u, keys):
    if u <= keys[0][0]:
        return keys[0][1]
    for (u0, s0), (u1, s1) in zip(keys, keys[1:]):
        if u <= u1:
            return s0 + (s1 - s0) * smootherstep((u - u0) / max(u1 - u0, 1e-9))
    return keys[-1][1]


def ramp_times(t_start, n_out, keys, shutter=0.5, fps=FPS):
    """Eased speed ramp -> [(t_src, shutter_span_s)] for n_out output frames.

    Speed is integrated with 8 sub-steps per frame so the position curve is C1-smooth.
    shutter=0.5 is a 180-degree shutter; the span grows with speed (true motion blur).
    """
    out, t = [], t_start
    for i in range(n_out):
        u = i / max(n_out - 1, 1)
        s = speed_at(u, keys)
        out.append((t, s * shutter / fps))
        for j in range(8):
            uu = (i + (j + 0.5) / 8) / max(n_out - 1, 1)
            t += speed_at(uu, keys) / fps / 8
    return out


# ----------------------------------------------------------------------- CORE IMAGE OPS
def _box1d(img, r, axis):
    """Box blur of radius r (px) along axis, edge-clamped, via cumulative sum (O(1)/px)."""
    r = int(r)
    if r < 1:
        return img
    x = np.moveaxis(img, axis, 0)
    n = x.shape[0]
    p = np.concatenate([np.repeat(x[:1], r + 1, 0), x, np.repeat(x[-1:], r, 0)], 0)
    c = np.cumsum(p, axis=0, dtype=np.float32)
    out = (c[2 * r + 1:2 * r + 1 + n] - c[:n]) * np.float32(1.0 / (2 * r + 1))
    return np.ascontiguousarray(np.moveaxis(out, 0, axis))


def dir_blur(img, length_px, axis=1, passes=3):
    """Directional (motion) blur along axis 1 (horizontal) or 0 (vertical).
    length_px ~ visible smear length. 3 box passes approximate a gaussian."""
    if length_px < 1.5:
        return img
    r = max(1, int(length_px / (2 * math.sqrt(passes))))
    x = img if axis == 0 else np.ascontiguousarray(np.swapaxes(img, 0, 1))
    for _ in range(passes):
        x = _box1d(x, r, 0)
    return x if axis == 0 else np.ascontiguousarray(np.swapaxes(x, 0, 1))


def gauss(img, radius, passes=3):
    return dir_blur(dir_blur(img, radius, 1, passes), radius, 0, passes)


def down(img, k):
    h, w = img.shape[0] // k * k, img.shape[1] // k * k
    return img[:h, :w].reshape(h // k, k, w // k, k, -1).mean((1, 3))


def up(img, h=H, w=W):
    img = img.astype(np.float32, copy=False)  # PIL "F" needs float32 (NumPy 2 promotes to f64)
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(img[..., c]), "F")
                                .resize((w, h), Image.BILINEAR)) for c in range(img.shape[2])], -1)


def luma(img):
    return img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722


def transform(img, dx=0.0, dy=0.0, scale=1.0, rot=0.0, cx=None, cy=None):
    """Affine about (cx, cy): scale, rotate (deg), then translate by (dx, dy) px.
    Samples up to 96 px outside the frame come from a reflect pad (no black edges); pass
    scale >= ~1.03 when shaking so mirrored edges stay out of view."""
    if abs(dx) < 0.05 and abs(dy) < 0.05 and abs(scale - 1) < 1e-4 and abs(rot) < 1e-3:
        return img
    h, w = img.shape[:2]
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    a = math.radians(rot)
    ca, sa = math.cos(a) / scale, math.sin(a) / scale
    # inverse map: out(x,y) -> in(...)
    x0, y0 = -dx, -dy
    P = 96  # reflect pad so small overshoots sample mirrored picture, not black
    coeffs = (ca, sa, cx - ca * (cx + x0) - sa * (cy + y0) + P,
              -sa, ca, cy + sa * (cx + x0) - ca * (cy + y0) + P)
    pad = np.pad(img.astype(np.float32, copy=False), ((P, P), (P, P), (0, 0)), mode="reflect")
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(pad[..., c]), "F")
                                .transform((w, h), Image.AFFINE, coeffs, Image.BILINEAR))
                     for c in range(3)], -1)


def shift_wrap(img, dx=0, dy=0):
    """Integer translate with wrap-around (invisible under whip blur)."""
    return np.roll(img, (int(round(dy)), int(round(dx))), axis=(0, 1))


# ------------------------------------------------------------------------ PER-FRAME FX
def flash(img, amount, color=(1.0, 1.0, 1.0)):
    """Flash frame: overexpose + wash toward color. amount 0..1."""
    if amount <= 0:
        return img
    col = np.asarray(color, np.float32)
    hot = img * (1 + 5 * amount)          # overexpose first (keeps the picture's shapes)
    w = 0.55 * amount                     # then a partial wash, never a flat card
    return hot * (1 - w) + col * w


def chroma_split(img, amount_px, radial=True, angle=0.0):
    """RGB split. radial: R scaled out, B scaled in about centre (lens CA, strongest at the
    edges). Otherwise lateral: R/B shifted +-amount along angle (deg)."""
    if amount_px < 0.3:
        return img
    img = img.astype(np.float32, copy=False)
    h, w = img.shape[:2]
    out = img.copy()
    if radial:
        s = amount_px / (0.5 * math.hypot(w, h))
        for c, k in ((0, 1 + s), (2, 1 - s)):
            out[..., c] = np.asarray(Image.fromarray(np.ascontiguousarray(img[..., c]), "F")
                                     .transform((w, h), Image.AFFINE,
                                                (1 / k, 0, w / 2 * (1 - 1 / k), 0, 1 / k,
                                                 h / 2 * (1 - 1 / k)), Image.BILINEAR))
    else:
        a = math.radians(angle)
        dx, dy = amount_px * math.cos(a), amount_px * math.sin(a)
        out[..., 0] = np.roll(img[..., 0], (int(round(dy)), int(round(dx))), (0, 1))
        out[..., 2] = np.roll(img[..., 2], (-int(round(dy)), -int(round(dx))), (0, 1))
    return out


def zoom_blur(img, amount=0.04, n=6, cx=None, cy=None):
    """Radial zoom blur: average of n copies scaled 1..1+amount about (cx,cy)."""
    if amount < 0.002:
        return img
    acc = img.copy()
    for i in range(1, n):
        acc += transform(img, scale=1 + amount * i / (n - 1), cx=cx, cy=cy)
    return acc / n


def shake_offsets(k, amp=26.0, freq=11.0, decay=5.0, seed=0, rot_amp=0.6):
    """Decaying camera shake for frame k after the hit: sum of detuned sines * exp decay.
    Returns (dx, dy, rot_deg). Deterministic per seed."""
    t = k / FPS
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 2 * math.pi, 6)
    env = math.exp(-decay * t)
    dx = amp * env * (0.7 * math.sin(2 * math.pi * freq * t + ph[0]) +
                      0.3 * math.sin(2 * math.pi * freq * 1.9 * t + ph[1]))
    dy = amp * env * (0.7 * math.sin(2 * math.pi * freq * 1.13 * t + ph[2]) +
                      0.3 * math.sin(2 * math.pi * freq * 2.3 * t + ph[3]))
    rot = rot_amp * env * math.sin(2 * math.pi * freq * 0.8 * t + ph[4])
    return dx, dy, rot


def impact(img, k, strength=1.0, seed=0, flash_color=(1.0, 0.97, 0.9)):
    """Hit treatment for the k-th frame after an impact cut.
    k=0: flash 0.9, k=1: flash 0.15 (the '1-2 flash frames'), then clean.
    zoom punch 1.10 -> 1.0 (ease-out, ~8 fr), shake (~0.5 s), RGB split (~6 fr),
    zoom blur (~3 fr)."""
    s = strength
    punch = 1.0 + 0.10 * s * (1 - smootherstep(k / 8))
    dx, dy, rot = shake_offsets(k, amp=24 * s, seed=seed)
    out = transform(img, dx, dy, max(punch, 1.035) if k < 14 else punch, rot)
    if k < 3:
        out = zoom_blur(out, 0.05 * s * (1 - k / 3), n=6)
    ca = 22 * s * math.exp(-k / 2.2)
    out = chroma_split(out, ca, radial=True)
    if k < 2:
        out = chroma_split(out, 10 * s * (1 - k * 0.5), radial=False)
    fl = (0.9, 0.15)[k] * s if k < 2 else 0.0
    return flash(out, fl, flash_color)


def streaks(img, thresh=0.92, length=0.55, gain=0.9, tint=(0.55, 0.78, 1.0), core=0.08,
            ds=4, knee=0.06, point=0.18, point_radius=40):
    """Anamorphic light streaks: bright-pass (soft knee) at 1/ds res, restricted to POINT
    sources (lamps, headlights, LEDs) by a top-hat test -- a pixel must beat its local mean
    (box radius point_radius px) by `point` -- so white paint / bright walls do not streak.
    Then a very wide horizontal blur (length = fraction of frame width) + a short tight core
    -> tint -> add. The streak keeps half the lamp's own colour, half the cool anamorphic tint.
    Returns (img + streak). Call after the grade, before whips/impacts."""
    small = down(img, ds)
    l = small.max(-1, keepdims=True)
    local = gauss(l, point_radius / ds, passes=2)
    m = np.clip((l - thresh + knee) / (2 * knee), 0, 1) ** 2
    m *= np.clip((l - local - point) / point, 0, 1)
    bp = small * m
    wide = dir_blur(bp, length * small.shape[1], axis=1)
    tight = dir_blur(bp, core * small.shape[1], axis=1)
    st = wide * 2.2 + tight * 0.6
    t = np.asarray(tint, np.float32)
    lum = st.mean(-1, keepdims=True)
    st = 0.5 * st * t * 1.3 + 0.5 * lum * t
    return img + up(st * gain, img.shape[0], img.shape[1])


def bloom(img, thresh=0.7, radius=40, gain=0.35, ds=4):
    small = down(img, ds)
    m = np.clip((small.max(-1, keepdims=True) - thresh) / (1 - thresh + 1e-6), 0, 1)
    b = gauss(small * m, radius / ds)
    return img + up(b * gain, img.shape[0], img.shape[1])


# warm leak palette: gold-highlight -> amber -> ember. Pure #FBD101 reads olive when a screen
# blend keeps it dim, so the leak runs warmer and saves the brand gold for type/stripe.
_LEAK_PAL = [(1.0, 0.80, 0.38), (1.0, 0.56, 0.16), (0.95, 0.36, 0.12)]


def light_leak(img, t, strength=0.5, seed=3, palette=_LEAK_PAL, side="left"):
    """Generated light leak: 3-4 soft blobs drifting across a low-res field + a diagonal
    burn band, upscaled and SCREEN-blended. t in seconds (drives drift). Default palette is
    SE gold -> amber. strength 0..1 (animate it for leak 'bursts')."""
    if strength <= 0.003:
        return img
    rng = np.random.default_rng(seed)
    hh, ww = 96, 54
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    xx /= ww
    yy /= hh
    field = np.zeros((hh, ww, 3), np.float32)
    x_edge = 0.0 if side == "left" else 1.0
    for i in range(4):
        c = np.asarray(palette[i % len(palette)], np.float32)
        bx = x_edge + (0.25 if side == "left" else -0.25) * rng.uniform(-0.5, 1.5) \
            + 0.12 * math.sin(t * rng.uniform(0.6, 1.4) + rng.uniform(0, 6))
        by = rng.uniform(0.1, 0.9) + 0.15 * math.sin(t * rng.uniform(0.3, 0.9) + i) + 0.25 * t
        by = by % 1.3 - 0.15
        sx, sy = rng.uniform(0.18, 0.35), rng.uniform(0.18, 0.45)
        g = np.exp(-(((xx - bx) / sx) ** 2 + ((yy - by) / sy) ** 2))
        field += g[..., None] * c * rng.uniform(0.6, 1.0)
    # diagonal burn band sweeping with t
    band = np.exp(-(((xx * 0.6 + yy * 0.8) - (t * 0.55 % 1.8 - 0.3)) / 0.22) ** 2)
    field += band[..., None] * np.asarray(palette[0], np.float32) * 0.3
    field = np.clip(field * np.float32(strength), 0, 1).astype(np.float32)
    lk = up(field, img.shape[0], img.shape[1])
    return 1 - (1 - np.clip(img, 0, None)) * (1 - lk) + np.maximum(img - 1, 0)


_GRAIN = {}


def grain(img, idx, amount=0.045, size=2, n_plates=8, chroma=0.25):
    """Film grain: gaussian plates generated once at 1/size res (clump size ~size px),
    cycled per frame with random offsets. Weighted to mid-tones (less in blacks/highlights)."""
    h, w = img.shape[:2]
    key = (h, w, size)
    if key not in _GRAIN:
        rng = np.random.default_rng(7)
        plates = []
        for _ in range(n_plates):
            g = rng.standard_normal((h // size, w // size, 3)).astype(np.float32)
            g[..., 1:] = g[..., :1] * (1 - chroma) + g[..., 1:] * chroma
            g[..., 0] = g[..., 0]
            plates.append(up(g, h, w))
        _GRAIN[key] = plates
    plates = _GRAIN[key]
    g = plates[idx % len(plates)]
    rng = np.random.default_rng(idx)
    g = np.roll(g, (int(rng.integers(0, h)), int(rng.integers(0, w))), (0, 1))
    l = np.clip(luma(img), 0, 1)[..., None]
    wgt = 0.35 + 2.6 * l * (1 - l)
    return img + g * amount * wgt


_VIG = {}


def vignette(img, strength=0.45, roundness=1.0, softness=0.9):
    """Multiplicative oval vignette (cached mask). strength 0..1 at the corners."""
    h, w = img.shape[:2]
    key = (h, w, strength, roundness, softness)
    if key not in _VIG:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (xx / w - 0.5) * 2
        ny = (yy / h - 0.5) * 2 * roundness
        r = np.sqrt(nx * nx + ny * ny) / math.sqrt(2)
        m = 1 - strength * np.clip((r - (1 - softness)) / softness, 0, 1) ** 2
        _VIG[key] = m[..., None].astype(np.float32)
    return img * _VIG[key]


# ----------------------------------------------------------------------------- GRADE
class NightGrade:
    """Cohesive night grade so GT3 RS tunnel/warehouse and Black Series Strip footage sit in
    one world:
      1. per-clip normalise: clip's 0.5th / 99.7th luma percentiles -> black/white targets,
         and a gamma so the clip's median luma lands on `mid` (evens out bright grey tunnel vs
         dark Strip);
      2. filmic S-curve (contrast);
      3. split tone: teal-steel shadows, neutral-warm highlights;
      4. hue-aware saturation: reds/oranges (the cars, taillights) kept rich, everything
         else pulled down (sodium/neon noise tamed);
      5. soft highlight roll-off.
    Use:  g = NightGrade.fit(src.frames[::4]);  out = g(frame)
    """

    def __init__(self, lo, hi, gamma, contrast=0.6, black=0.012, white=0.97,
                 shadow_tint=(-0.012, 0.004, 0.018), hi_tint=(0.012, 0.004, -0.012),
                 sat=0.78, warm_sat=1.12):
        self.__dict__.update(locals())
        self.st = np.asarray(shadow_tint, np.float32)
        self.ht = np.asarray(hi_tint, np.float32)

    @classmethod
    def fit(cls, frames_u8, mid=0.13, **kw):
        sub = frames_u8[:: max(1, len(frames_u8) // 8), ::8, ::8].astype(np.float32) / 255
        l = luma(sub).ravel()
        lo, hi = np.percentile(l, 0.5), np.percentile(l, 99.7)
        med = np.clip((np.median(l) - lo) / max(hi - lo, 1e-3), 0.02, 0.98)
        gamma = math.log(mid) / math.log(med)
        gamma = min(max(gamma, 0.8), 1.5)
        return cls(lo, hi, gamma, **kw)

    def __call__(self, img):
        x = np.clip((img - self.lo) / max(self.hi - self.lo, 1e-3), 0, None)
        x = np.power(x, self.gamma, dtype=np.float32)
        # filmic S: blend toward smootherstep-like curve on [0,1], keep >1 headroom linear
        xc = np.clip(x, 0, 1)
        s = xc * xc * (3 - 2 * xc)
        x = np.where(x <= 1, xc + (s - xc) * self.contrast, x)
        l = luma(x)[..., None]
        # split tone
        x = x + self.st * (1 - l) ** 3 * 2.0 + self.ht * l ** 2
        # hue-aware saturation
        warm = np.clip((x[..., 0:1] - np.maximum(x[..., 1:2], x[..., 2:3])) * 4, 0, 1)
        satf = self.sat + (self.warm_sat - self.sat) * warm
        l = luma(x)[..., None]
        x = l + (x - l) * satf
        # black / white points + soft shoulder
        x = self.black + (self.white - self.black) * x
        sh = 0.85
        x = np.where(x > sh, sh + (1 - sh) * np.tanh((x - sh) / (1 - sh)), x)
        return x.astype(np.float32)


# ----------------------------------------------------------------------------- WHIP
def ease_io(x, p=4):
    x = min(max(x, 0.0), 1.0)
    return 0.5 * (2 * x) ** p if x < 0.5 else 1 - 0.5 * (2 - 2 * x) ** p


def whip(a_tail, b_head, direction="left", dist=0.9, blur=1.0, bright=0.15):
    """Whip-pan transition. Returns len(a_tail)+len(b_head) frames.
    The virtual camera travels `dist` frame-widths (or heights) along direction with an
    ease-in-out-quartic; A fills the first half, B the second. Each frame is wrapped-shifted
    by its position and smeared by a directional blur equal to that frame's travel (180deg
    shutter * blur). The two seam frames are 50/50 mixes; a small exposure lift sells the
    smear."""
    na, nb = len(a_tail), len(b_head)
    n = na + nb
    horiz = direction in ("left", "right")
    sgn = -1 if direction in ("left", "up") else 1
    size = W if horiz else H
    axis = 1 if horiz else 0
    out = []
    for i in range(n):
        p0, p1 = i / n, (i + 1) / n
        x = ease_io((p0 + p1) / 2)
        v = (ease_io(p1) - ease_io(p0)) * dist * size  # px travelled this frame
        if i < na:
            img, off = a_tail[i], sgn * x * dist * size
        else:
            img, off = b_head[i - na], -sgn * (1 - x) * dist * size
        f = shift_wrap(img, off if horiz else 0, 0 if horiz else off)
        if i in (na - 1, na):  # seam mix
            other = b_head[0] if i == na - 1 else a_tail[-1]
            o_off = (-sgn * (1 - x) if i == na - 1 else sgn * x) * dist * size
            f = 0.5 * f + 0.5 * shift_wrap(other, o_off if horiz else 0, 0 if horiz else o_off)
        f = dir_blur(f, v * blur * 1.6, axis=axis)
        f = f * (1 + bright * (v / (dist * size / n * 2)))
        out.append(f)
    return out


# ----------------------------------------------------------------------------- AUDIO
SR = 48000


def _noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def _onepole_lp(x, a):
    # vectorised-ish one-pole low-pass via cumulative filter (small loops OK at 48k * <1 s)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def sfx_whoosh(dur=0.35, seed=1, peak=0.6):
    """Filtered-noise whoosh: cutoff sweeps up to the peak then down; asymmetric envelope."""
    n = int(dur * SR)
    t = np.linspace(0, 1, n, dtype=np.float32)
    env = np.where(t < peak, (t / peak) ** 2.5, ((1 - t) / (1 - peak)) ** 1.5)
    fc = 300 + 5200 * env
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    x = _onepole_lp(_noise(n, seed), a)
    x = x - _onepole_lp(x, np.full(n, 1 - np.exp(-2 * np.pi * 150 / SR), np.float32))
    return x * env * 1.8


def sfx_hit(dur=0.9, seed=2):
    """Impact: pitched-down sine thump (90 -> 38 Hz) + noise crack, exp decay."""
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = 38 + 52 * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 4.5)
    crack = _noise(n, seed) * np.exp(-t * 45) * 0.5
    return (np.tanh(body * 1.8) * 0.9 + crack)


def sfx_riser(dur=1.0, seed=3):
    n = int(dur * SR)
    t = np.linspace(0, 1, n, dtype=np.float32)
    a = 1 - np.exp(-2 * np.pi * (400 + 6000 * t ** 2) / SR)
    return _onepole_lp(_noise(n, seed), a) * t ** 2 * 0.6


def mix_to_wav(events, total_dur, path, gain=0.9):
    """events = [(t_seconds, mono_array, level)] -> stereo 16-bit wav, peak-normalised."""
    n = int(total_dur * SR)
    buf = np.zeros(n, np.float32)
    for t0, sig, lvl in events:
        i = int(t0 * SR)
        j = min(n, i + len(sig))
        if j > i:
            buf[i:j] += sig[: j - i] * lvl
    fade = int(0.05 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf = buf / (np.abs(buf).max() + 1e-6) * gain
    st = (np.stack([buf, buf], -1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
