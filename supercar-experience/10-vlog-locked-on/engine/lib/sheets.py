"""Contact sheets: keyframe tiles with the clip time (and camera clock) on each tile."""
import os

from PIL import Image, ImageDraw


def sheet(kfs, out, label, step=None, t0=0.0, t1=1e9, tile_w=150, cols=10, clock=None, max_tiles=120, quality=74):
    """kfs: [(t, path)] -> JPEG grid. step: min seconds between tiles (auto: fit max_tiles)."""
    sel = [(t, p) for t, p in kfs if t0 - 1e-6 <= t <= t1 + 1e-6]
    if not sel:
        return None
    if step is None:
        span = sel[-1][0] - sel[0][0]
        step = max(0.0, span / max_tiles)
    pick, nxt = [], -1e9
    for t, p in sel:
        if t >= nxt - 1e-6:
            pick.append((t, p))
            nxt = t + step
    first = Image.open(pick[0][1])
    w, h = first.size
    th = int(h * tile_w / w)
    cols = min(cols, len(pick))
    rows = (len(pick) + cols - 1) // cols
    img = Image.new('RGB', (cols * tile_w, rows * (th + 14)), (18, 18, 18))
    d = ImageDraw.Draw(img)
    for i, (t, p) in enumerate(pick):
        x = (i % cols) * tile_w
        y = (i // cols) * (th + 14)
        try:
            im = Image.open(p).convert('RGB').resize((tile_w, th))
        except OSError:
            continue
        img.paste(im, (x, y + 14))
        txt = f'{label} {int(t // 60)}:{t % 60:04.1f}'
        if clock is not None:
            c = int(clock + t)
            txt += f' {c // 3600 % 24:02d}:{c % 3600 // 60:02d}:{c % 60:02d}'
        d.text((x + 2, y + 1), txt, fill=(255, 210, 0))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, quality=quality)
    return out


def strip(kfs, out, label, a, b, n=6, tile_w=160, pad=1.0):
    """A one-row strip of up to n keyframes spread over [a-pad, b+pad] (moment previews)."""
    sel = [(t, p) for t, p in kfs if a - pad <= t <= b + pad]
    if not sel:
        near = sorted(kfs, key=lambda x: abs(x[0] - (a + b) / 2))[:1]
        sel = near
    if not sel:
        return None
    if len(sel) > n:
        k = len(sel) / n
        sel = [sel[int(i * k)] for i in range(n)]
    return sheet(sel, out, label, step=0, tile_w=tile_w, cols=len(sel))
