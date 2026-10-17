"""Keyframes -> survey thumbnails, decoded straight from the sample tables (no demuxing of the holes).

decode_samples() builds one decoder from the track's hvcC/avcC and feeds it only the kept sync samples, read
from the sparse file at their own offsets. Sync samples are intra pictures, so each decodes on its own and the
pixels are identical to the same picture decoded out of the full file (tests/test_stream.py checks this).

Per thumbnail we also keep a few picture statistics (kf/<id>/stats.json) for the quality notes: mean / spread of
luma, share of near-black pixels, sharpness (Laplacian variance), and where the light comes from (top vs sides).
"""
import json
import os
import time

import av
import numpy as np
from PIL import Image

from . import mp4

THUMB_W = 270


def _rotate(img, rot):
    if rot == 90:
        return img.transpose(Image.Transpose.ROTATE_270)   # 90 degrees clockwise
    if rot == 270:
        return img.transpose(Image.Transpose.ROTATE_90)
    if rot == 180:
        return img.transpose(Image.Transpose.ROTATE_180)
    return img


def frame_stats(img):
    """Statistics of a small RGB PIL image."""
    g = np.asarray(img.convert('L').resize((96, 96), Image.Resampling.BILINEAR), dtype=np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    gy = np.abs(np.diff(g, axis=0)).mean()
    gx = np.abs(np.diff(g, axis=1)).mean()
    q = 32
    L = lap[:92, :92].reshape(4, 23, 4, 23).transpose(0, 2, 1, 3).reshape(16, -1)
    smooth = float((L.var(axis=1) < 25).mean())
    return {
        'mean': round(float(g.mean()), 1), 'std': round(float(g.std()), 1),
        'black': round(float((g < 18).mean()), 3), 'white': round(float((g > 245).mean()), 3),
        'sharp': round(float(lap.var()), 1),
        'top': round(float(g[:q].mean()), 1), 'bottom': round(float(g[-q:].mean()), 1),
        'left': round(float(g[:, :q].mean()), 1), 'right': round(float(g[:, -q:].mean()), 1),
        'gx': round(float(gx), 2), 'gy': round(float(gy), 2), 'smooth': round(smooth, 3),
    }


def make_decoder(track, threads=1):
    name = 'hevc' if track.codec in ('hvc1', 'hev1') else 'h264' if track.codec in ('avc1', 'avc3') else track.codec
    ctx = av.CodecContext.create(name, 'r')
    ctx.extradata = track.extradata
    ctx.thread_type = 'NONE' if threads <= 1 else 'FRAME'
    ctx.thread_count = max(1, threads)
    return ctx


def decode_samples(path, track, indices, raw=False, threads=1):
    """Yield (sample_index, frame) decoding only `indices` (sync samples) read from `path` at their offsets."""
    ctx = make_decoder(track, threads)
    order = []
    with open(path, 'rb') as f:
        for si in indices:
            f.seek(int(track.offsets[si]))
            data = f.read(int(track.sizes[si]))
            pkt = av.Packet(data)
            pkt.pts = int(track.pts[si])
            pkt.dts = int(track.dts[si])
            order.append(si)
            for fr in ctx.decode(pkt):
                yield fr.pts, fr
        for fr in ctx.decode(None):
            yield fr.pts, fr


def thumbnails(sparse_path, moov_bytes, indices, out_dir, width=THUMB_W, quality=82):
    """Decode the kept sync samples to out_dir/<ms>.jpg (display-rotated, `width` px wide) + stats.json."""
    t0 = time.time()
    movie = mp4.parse_moov(moov_bytes)
    v = movie.video
    os.makedirs(out_dir, exist_ok=True)
    by_pts = {int(v.pts[i]): i for i in indices}
    stats = {}
    n = 0
    rot = v.rotation
    for pts, fr in decode_samples(sparse_path, v, indices):
        si = by_pts.get(pts)
        t = (pts if si is None else int(v.pts[si])) / float(v.timescale)
        w, h = fr.width, fr.height
        if rot in (90, 270):
            w, h = h, w
        tw = width
        th = max(2, int(round(h * tw / w / 2)) * 2)
        sw, sh = (th, tw) if rot in (90, 270) else (tw, th)
        img = fr.reformat(width=sw, height=sh, format='rgb24', interpolation='AREA').to_image()
        img = _rotate(img, rot)
        name = f'{int(round(t * 1000)):08d}.jpg'
        img.save(os.path.join(out_dir, name), quality=quality)
        stats[name] = frame_stats(img)
        n += 1
    with open(os.path.join(out_dir, 'stats.json'), 'w') as f:
        json.dump({'rotation': rot, 'size': [v.width, v.height], 'frames': stats}, f)
    return {'n': n, 'secs': round(time.time() - t0, 2)}


def worker_thumbnails(args):
    """Process-pool entry point."""
    sparse_path, moov_path, indices, out_dir = args
    with open(moov_path, 'rb') as f:
        moov = f.read()
    return thumbnails(sparse_path, moov, indices, out_dir)


def list_keyframes(day_root, cid):
    """[(t_seconds, path)] for a clip: kf/<id>/<ms>.jpg (this engine) or kf/<id>_<n>.jpg (Sep 15 layout: the
    n-th file is the n-th sync sample of the saved moov)."""
    d = os.path.join(day_root, 'kf', cid)
    if os.path.isdir(d):
        return sorted((int(f[:-4]) / 1000.0, os.path.join(d, f)) for f in os.listdir(d) if f.endswith('.jpg'))
    import glob
    fs = sorted(glob.glob(os.path.join(day_root, 'kf', f'{cid}_*.jpg')))
    if not fs:
        return []
    moov = os.path.join(day_root, 'idx', cid + '.moov')
    if os.path.exists(moov):
        v = mp4.parse_moov(open(moov, 'rb').read()).video
        sy = v.sync_indices()
        if len(sy) == len(fs):
            return [(float(v.pts[i]) / v.timescale, f) for i, f in zip(sy, fs)]
    return [(int(os.path.basename(f).split('_')[-1][:-4]) * 1001 / 60000.0, f) for f in fs]
