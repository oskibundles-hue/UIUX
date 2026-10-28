"""accum.py — motion-blur accumulator for kcapture.js (reads stdin, writes <outDir>/<name>.png).

Stream format per frame: uint32 nameLen, uint32 K, name bytes, then K x (uint32 len, PNG bytes).
Samples are straight-alpha RGBA screenshots. They are averaged in premultiplied space:
    A = mean(a);  RGB = sum(rgb * a) / sum(a)
which is the correct box-filter shutter for a layer that will later be alpha-composited over a plate.
K == 1 frames are written through untouched.
"""
import sys, io, os, struct
import numpy as np
from PIL import Image

out = sys.argv[1]
inp = sys.stdin.buffer

def rd(n):
    b = inp.read(n)
    if len(b) < n:
        raise EOFError
    return b

while True:
    try:
        nl, k = struct.unpack('<II', rd(8))
    except EOFError:
        break
    name = rd(nl).decode()
    bufs = [rd(struct.unpack('<I', rd(4))[0]) for _ in range(k)]
    dst = os.path.join(out, name + '.png')
    if k == 1:
        open(dst, 'wb').write(bufs[0]); continue
    acc = None; aacc = None
    for b in bufs:
        im = np.asarray(Image.open(io.BytesIO(b)).convert('RGBA'), dtype=np.float32)
        a = im[..., 3:4] / 255.0
        if acc is None:
            acc = im[..., :3] * a; aacc = a.copy()
        else:
            acc += im[..., :3] * a; aacc += a
    rgb = np.where(aacc > 1e-6, acc / np.maximum(aacc, 1e-6), 0)
    alpha = aacc / k * 255.0
    o = np.concatenate([rgb, alpha], axis=2)
    Image.fromarray(np.clip(o + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(dst, compress_level=1)
