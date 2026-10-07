"""accum2.py: motion-blur accumulator for kcap2.js (reads stdin, writes <outDir>/<name>.png atomically).

Stream per frame: 8 x uint32 (nameLen, K, x, y, w, h, OW, OH), name bytes, then K x (uint32 len, PNG bytes).
Samples are straight-alpha RGBA screenshots of the rect (x, y, w, h) inside an OW x OH frame; outside the rect the
frame is transparent. Averaged in premultiplied space exactly as accum.py does:
    A = mean(a);  RGB = sum(rgb * a) / sum(a)
so a clipped frame is pixel-identical to the same frame averaged full-size. K == 1 full-frame RGBA samples are
written through untouched. If any sample of a clipped frame has ink on the rect's border (where the rect is not at
the frame edge), the frame name is appended to <outDir>/_retry.txt and build.py captures it again unclipped.
Files are written to a temp name and renamed, so a hard-linked duplicate frame is never modified in place.
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


def save(dst, data=None, img=None):
    tmp = dst + f'.tmp{os.getpid()}'
    if data is not None:
        open(tmp, 'wb').write(data)
    else:
        img.save(tmp, format='PNG', compress_level=1)
    os.replace(tmp, dst)


while True:
    try:
        nl, k, x, y, w, h, OW, OH = struct.unpack('<8I', rd(32))
    except EOFError:
        break
    name = rd(nl).decode()
    bufs = [rd(struct.unpack('<I', rd(4))[0]) for _ in range(k)]
    dst = os.path.join(out, name + '.png')
    full = (x, y, w, h) == (0, 0, OW, OH)
    if k == 1 and full:
        if bufs[0][25] == 6:                       # IHDR colour type 6 = RGBA
            save(dst, data=bufs[0])
        else:
            save(dst, img=Image.open(io.BytesIO(bufs[0])).convert('RGBA'))
        continue
    ims = [np.asarray(Image.open(io.BytesIO(b)).convert('RGBA')) for b in bufs]
    # the float average runs only inside the union of the samples' ink (outside it every sample is transparent and
    # the average is 0 either way), which gives exactly the same pixels as averaging the whole rect
    anyink = np.zeros(ims[0].shape[:2], bool)
    for im in ims:
        anyink |= im[..., 3] > 0
    rows, cols = np.nonzero(anyink.any(1))[0], np.nonzero(anyink.any(0))[0]
    if len(rows) == 0:
        by0 = by1 = bx0 = bx1 = 0
    else:
        by0, by1, bx0, bx1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
    acc = None; aacc = None; border = False
    for im8 in ims:
        if not full:
            A = im8[..., 3]
            edges = []
            if y > 0: edges.append(A[0, :])
            if y + h < OH: edges.append(A[-1, :])
            if x > 0: edges.append(A[:, 0])
            if x + w < OW: edges.append(A[:, -1])
            if any(e.max() > 0 for e in edges):
                border = True
        im = im8[by0:by1, bx0:bx1].astype(np.float32)
        a = im[..., 3:4] / 255.0
        if acc is None:
            acc = im[..., :3] * a; aacc = a.copy()
        else:
            acc += im[..., :3] * a; aacc += a
    if border:
        with open(os.path.join(out, '_retry.txt'), 'a') as f:
            f.write(name + '\n')
        continue
    o = np.zeros((OH, OW, 4), np.uint8)
    if acc is not None and acc.size:
        rgb = np.where(aacc > 1e-6, acc / np.maximum(aacc, 1e-6), 0)
        alpha = aacc / k * 255.0
        o[y + by0:y + by1, x + bx0:x + bx1] = np.clip(np.concatenate([rgb, alpha], axis=2) + 0.5, 0, 255).astype(np.uint8)
    save(dst, img=Image.fromarray(o, 'RGBA'))
