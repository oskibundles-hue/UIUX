#!/usr/bin/env python3
"""
Anderson Tai's three DaVinci Resolve effects, rebuilt as per-frame numpy
functions, each applied over a time window of a clip.

  flashbox          scene-to-scene transition: a white flash, or a box that
                    grows into a white frame and opens again as a box-shaped
                    window onto the next scene, over 4-6 frames around a cut.
  inverted_flicker  alternate inverted and normal frames over a window.
                    Resolve does this with Magic Mask on the subject; there is
                    no Magic Mask here, so --mode full inverts the whole frame
                    and --mode luma inverts only a luminance key (the bright
                    parts: paint highlights, sky, lights), soft-edged.
  difference_burn   composite a light-leak/burn overlay with Difference blend.
                    The overlay is procedural (animated value noise, a drifting
                    radial glow and an edge streak, tinted); no stock overlay.

The output is re-filled to 2160x3840 at 29.97 fps (the Fast Cut spec) unless
--res says otherwise; frames outside every window pass through untouched and
the source audio is carried over.

    python3 davinci_fx.py flashbox --in reel.mp4 --at 3.20 --frames 5 --mode box --out a.mp4
    python3 davinci_fx.py flicker  --in reel.mp4 --start 6.0 --end 6.8 --mode luma --out b.mp4
    python3 davinci_fx.py burn     --in reel.mp4 --start 0 --end 2.5 --out c.mp4
    python3 davinci_fx.py chain    --in reel.mp4 --spec fx.json --out d.mp4

fx.json for chain is a list of ops, applied in order on each frame:
    [{"fx": "flashbox", "at": 3.2, "frames": 5, "mode": "white"},
     {"fx": "flicker", "start": 6.0, "end": 6.8, "mode": "luma", "period": 1},
     {"fx": "burn", "start": 0, "end": 2.5, "opacity": 0.8, "seed": 3}]
Times are seconds on the input clip.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media as M  # noqa: E402


# ---------------------------------------------------------------- flashbox

def flashbox_frame(frame, k, before=2, after=3, mode="white"):
    """k = frame offset from the cut (0 = first frame of the incoming scene).
    Window covers k in [-before, after-1]; outside it the frame is returned."""
    if k < -before or k >= after:
        return frame
    h, w = frame.shape[:2]
    f = frame.astype(np.float32)
    if mode == "white":
        if k < 0:
            a = (k + before + 1) / (before + 1)            # ramps up into the cut
        elif k == 0:
            a = 1.0
        else:
            a = (1 - k / after) ** 1.5                     # decays off the cut
        return np.clip(f + (255 - f) * a, 0, 255).astype(np.uint8)
    # box: a white box grows from the centre to fill the frame by the cut, then
    # the incoming scene opens through a growing box-shaped hole.
    out = f.copy()
    if k < 0:
        s = (k + before + 1) / (before + 1)
        bw, bh = int(w * s), int(h * s)
        x0, y0 = (w - bw) // 2, (h - bh) // 2
        out[y0:y0 + bh, x0:x0 + bw] = 255
    elif k == 0:
        out[:] = 255
    else:
        s = min(1.0, (k / after) ** 0.8 + 0.15)
        bw, bh = int(w * s), int(h * s)
        x0, y0 = (w - bw) // 2, (h - bh) // 2
        mask = np.ones((h, w), bool)
        mask[y0:y0 + bh, x0:x0 + bw] = False
        out[mask] = 255
        edge = max(2, w // 270)                            # a thin white rule on the hole
        out[y0:y0 + edge, x0:x0 + bw] = 255; out[y0 + bh - edge:y0 + bh, x0:x0 + bw] = 255
        out[y0:y0 + bh, x0:x0 + edge] = 255; out[y0:y0 + bh, x0 + bw - edge:x0 + bw] = 255
    return out.astype(np.uint8)


# ---------------------------------------------------------------- inverted flicker

def luma(frame):
    f = frame.astype(np.float32) / 255
    return 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]


def inverted_flicker_frame(frame, i, period=1, mode="full", thresh=0.6, soft=0.1):
    """i = frame index inside the window. Inverted on even periods, normal on odd."""
    if (i // max(1, period)) % 2:
        return frame
    inv = 255 - frame
    if mode == "full":
        return inv
    y = luma(frame)
    key = np.clip((y - (thresh - soft)) / (2 * soft), 0, 1)
    key = (key * key * (3 - 2 * key))[..., None]          # smoothstep edge
    return (frame * (1 - key) + inv * key + 0.5).astype(np.uint8)


# ---------------------------------------------------------------- difference burn

class BurnOverlay:
    """Animated procedural light leak, deterministic for a seed.
    Value noise is keyed every `key_s` seconds on a coarse grid and cosine-
    interpolated between keys, then upsampled bicubic; a radial glow drifts
    across the frame and a streak sweeps in from one edge."""
    def __init__(self, w, h, seed=1, tint=(255, 150, 60), key_s=0.4, grid=(6, 10), scale=4):
        self.w, self.h, self.key_s, self.grid, self.sc = w, h, key_s, grid, scale
        self.seed = seed
        self.keys = {}
        self.tint = np.array(tint, np.float32) / 255
        r = np.random.default_rng(seed + 1000)
        self.p0 = r.uniform([0.1, 0.0], [0.9, 0.3])         # glow start (x, y fraction)
        self.p1 = r.uniform([0.1, 0.6], [0.9, 1.0])         # glow end
        self.side = int(r.integers(0, 2))

    def _key(self, n):
        if n not in self.keys:
            g = np.random.default_rng([self.seed, n])
            self.keys[n] = g.random(self.grid[::-1]).astype(np.float32)
        return self.keys[n]

    def __call__(self, t, u):
        """t = seconds into the window, u = 0..1 progress through it. RGB float32 0..1."""
        lw, lh = max(8, self.w // self.sc), max(8, self.h // self.sc)
        n = int(t // self.key_s); fr = (t / self.key_s) - n
        fr = 0.5 - 0.5 * math.cos(math.pi * fr)
        g = self._key(n) * (1 - fr) + self._key(n + 1) * fr
        # Bicubic from a 6x10 grid leaves the cell edges visible, and the Difference
        # blend shows them as soft squares; a blur of about half a cell hides the grid.
        noise = np.asarray(Image.fromarray(g).resize((lw, lh), Image.BICUBIC), np.float32)
        noise = np.clip(noise, 0, 1)
        img = Image.fromarray((noise * 255).astype(np.uint8))
        noise = np.asarray(img.filter(ImageFilter.GaussianBlur(lw / self.grid[0] / 2)), np.float32) / 255
        lo, hi = noise.min(), noise.max()
        noise = ((noise - lo) / max(hi - lo, 1e-3)) ** 1.6
        yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
        xx /= lw; yy /= lh
        p = self.p0 + (self.p1 - self.p0) * u
        glow = np.exp(-(((xx - p[0]) * 1.0) ** 2 + ((yy - p[1]) * 0.56) ** 2) / 0.06)
        edge = xx if self.side else 1 - xx
        streak = np.clip(1 - edge / (0.25 + 0.2 * math.sin(u * math.pi)), 0, 1) ** 2
        v = np.clip(0.55 * noise + 0.8 * glow + 0.5 * streak, 0, 1)
        img = Image.fromarray((v * 255).astype(np.uint8)).resize((self.w, self.h), Image.BICUBIC)
        v = np.asarray(img, np.float32)[..., None] / 255
        return v * self.tint + (v ** 3) * (1 - self.tint)    # hot core goes toward white


def difference_burn_frame(frame, overlay, opacity=0.8):
    """Difference blend: |base - overlay|, mixed in at `opacity`."""
    f = frame.astype(np.float32) / 255
    d = np.abs(f - overlay)
    return np.clip((f * (1 - opacity) + d * opacity) * 255 + 0.5, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- runner

def window_env(t, start, end, fade):
    if t < start or t >= end:
        return 0.0
    if fade <= 0:
        return 1.0
    return min(1.0, (t - start) / fade, (end - t) / fade)


def make_ops(ops, w, h):
    """Turn op dicts into per-frame callables f(frame, i, t) -> frame."""
    out = []
    for op in ops:
        fx = op["fx"]
        if fx == "flashbox":
            nfr = int(op.get("frames", 5))
            if not 4 <= nfr <= 6:
                raise SystemExit("flashbox --frames must be 4-6")
            before = int(op.get("before", nfr // 2)); after = nfr - before
            cut_i = int(round(op["at"] * M.FPS))
            mode = op.get("mode", "white")
            out.append(lambda fr, i, t, c=cut_i, b=before, a=after, m=mode:
                       flashbox_frame(fr, i - c, b, a, m))
        elif fx == "flicker":
            s_i, e_i = int(round(op["start"] * M.FPS)), int(round(op["end"] * M.FPS))
            kw = dict(period=int(op.get("period", 1)), mode=op.get("mode", "full"),
                      thresh=float(op.get("thresh", 0.6)), soft=float(op.get("soft", 0.1)))
            out.append(lambda fr, i, t, s=s_i, e=e_i, kw=kw:
                       inverted_flicker_frame(fr, i - s, **kw) if s <= i < e else fr)
        elif fx == "burn":
            tint = op.get("tint", "FF963C").lstrip("#")
            ov = BurnOverlay(w, h, seed=int(op.get("seed", 1)),
                             tint=tuple(int(tint[j:j + 2], 16) for j in (0, 2, 4)))
            st, en = float(op["start"]), float(op["end"])
            op_, fade = float(op.get("opacity", 0.8)), float(op.get("fade", 0.25))

            def f(fr, i, t, ov=ov, st=st, en=en, o=op_, fd=fade):
                e = window_env(t, st, en, fd)
                if e <= 0:
                    return fr
                return difference_burn_frame(fr, ov(t - st, (t - st) / max(1e-6, en - st)), o * e)
            out.append(f)
        else:
            raise SystemExit(f"unknown fx {fx}")
    return out


def apply(src, out, ops, res=(M.W, M.H), crf=16):
    w, h = res
    fns = make_ops(ops, w, h)
    tmp = os.path.splitext(out)[0] + "_v.mp4"
    wr = M.FrameWriter(tmp, w, h, w, h, crf=crf)
    for i, fr in enumerate(M.FrameReader(src, w, h)):
        t = i / M.FPS
        for fn in fns:
            fr = fn(fr, i, t)
        wr.write(fr)
    wr.close()
    M.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", src, "-map", "0:v", "-map", "1:a?",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", str(M.SR), "-shortest",
           "-movflags", "+faststart", out])
    os.remove(tmp)
    return wr.n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--in", dest="src", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--res", default=f"{M.W}x{M.H}")
        p.add_argument("--crf", type=int, default=16)

    p = sub.add_parser("flashbox"); common(p)
    p.add_argument("--at", type=float, required=True, help="cut time (s): first frame of the incoming scene")
    p.add_argument("--frames", type=int, default=5, help="4-6")
    p.add_argument("--before", type=int, help="frames before the cut (default frames//2)")
    p.add_argument("--mode", choices=["white", "box"], default="white")

    p = sub.add_parser("flicker"); common(p)
    p.add_argument("--start", type=float, required=True); p.add_argument("--end", type=float, required=True)
    p.add_argument("--period", type=int, default=1, help="frames per state (1 = every other frame)")
    p.add_argument("--mode", choices=["full", "luma"], default="full")
    p.add_argument("--thresh", type=float, default=0.6, help="luma key centre, 0-1")
    p.add_argument("--soft", type=float, default=0.1)

    p = sub.add_parser("burn"); common(p)
    p.add_argument("--start", type=float, required=True); p.add_argument("--end", type=float, required=True)
    p.add_argument("--opacity", type=float, default=0.8)
    p.add_argument("--fade", type=float, default=0.25)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--tint", default="FF963C", help="leak colour hex (default warm amber)")

    p = sub.add_parser("chain"); common(p)
    p.add_argument("--spec", required=True)

    a = ap.parse_args()
    if a.cmd == "chain":
        ops = json.load(open(a.spec))
    else:
        d = {k: v for k, v in vars(a).items() if k not in ("cmd", "src", "out", "res", "crf") and v is not None}
        d["fx"] = a.cmd
        ops = [d]
    res = tuple(map(int, a.res.lower().split("x")))
    n = apply(a.src, a.out, ops, res, a.crf)
    print(f"{a.out}: {n} frames, ops {[o['fx'] for o in ops]}")


if __name__ == "__main__":
    main()
