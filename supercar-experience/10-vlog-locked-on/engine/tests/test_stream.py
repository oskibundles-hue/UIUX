#!/usr/bin/env python3
"""Streaming survey filter vs the full file, served from a local single-use Range server.

For every test clip: link 1 = tail Range request -> moov; link 2 = one plain GET streamed through
StreamFilter into a sparse file. Then checks
  1. the moov from the tail == the moov streamed == the moov in the original
  2. audio stream-copied from the sparse file is byte-identical to a stream copy of the full file
     (and its packet md5s match)
  3. every kept keyframe decoded from the sparse file is pixel-identical to the same picture as ffmpeg decodes
     it from the full file (framemd5 of the raw 10-bit planes)
  4. the sparse file really is small on disk
  5. each link was requested exactly once (206 for the tail, 200 for the stream)

usage: test_stream.py WORKDIR FILE [FILE...]
"""
import hashlib
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib import mp4, stream, thumbs  # noqa: E402
from lib.common import FF  # noqa: E402
from rangeserver import RangeServer  # noqa: E402


def plane_md5(fr):
    import numpy as np
    h = hashlib.md5()
    for i, p in enumerate(fr.planes):
        w = fr.width if i == 0 else (fr.width + 1) // 2
        ht = fr.height if i == 0 else (fr.height + 1) // 2
        bpp = 2 if '10' in fr.format.name or '16' in fr.format.name else 1
        a = np.frombuffer(bytes(p), dtype=np.uint8).reshape(-1, p.line_size)[:ht, :w * bpp]
        h.update(a.tobytes())
    return h.hexdigest()


def ffmpeg_keyframe_md5(path, pix_fmt):
    out = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-skip_frame', 'nokey', '-noautorotate', '-i', path,
                          '-map', '0:v:0', '-fps_mode', 'passthrough', '-pix_fmt', pix_fmt, '-f', 'framemd5', '-'],
                         capture_output=True, text=True).stdout
    res = {}
    tb = 1.0
    for line in out.splitlines():
        if line.startswith('#tb 0:'):
            a, b = line.split(':')[1].strip().split('/')
            tb = int(a) / int(b)
        if line.startswith('#') or not line.strip():
            continue
        parts = [x.strip() for x in line.split(',')]
        res[round(int(parts[2]) * tb * 1000)] = parts[5]   # keyed by milliseconds
    return res


def run(work, path, srv, kf_step=2.0):
    size = os.path.getsize(path)
    name = os.path.basename(path)
    rep = {'file': name, 'size': size}
    # link 1: the tail
    tail_len = min(size, max(16 << 20, size // 1000))
    t0 = time.time()
    tail = stream.http_range(srv.link(path), size - tail_len, size)
    found = mp4.find_moov_in_tail(tail, size)
    rep['tail_s'] = round(time.time() - t0, 3)
    movie = mp4.parse_moov(found[1]) if found else None
    rep['moov_in_tail'] = bool(found)
    # link 2: the stream
    sp_path = os.path.join(work, name + '.sparse')
    sp = stream.SparseFile(sp_path, size)
    filt = stream.StreamFilter(size, sp, lambda m: mp4.keep_ranges(m, kf_step), movie=movie)
    t0 = time.time()
    got, secs = stream.http_stream(srv.link(path), filt.feed, expect_size=size)
    res = filt.finish()
    sp.close()
    rep['stream_s'] = round(secs, 3)
    rep['MBps'] = round(size / secs / 1e6, 1)
    movie = filt.movie
    # 1. moov identity
    with open(path, 'rb') as f:
        mv_atom = [a for a in res['atoms'] if a[0] == 'moov'][0]
        f.seek(mv_atom[1])
        orig_moov = f.read(mv_atom[2])
    rep['moov_identical'] = filt.moov_bytes == orig_moov and (not found or found[1] == orig_moov)
    # 4. disk use
    st = os.stat(sp_path)
    rep['sparse_disk_MB'] = round(st.st_blocks * 512 / 1e6, 1)
    rep['kept_MB'] = round(res['kept_bytes'] / 1e6, 1)
    # 2. audio
    outs = []
    for src, tag in ((path, 'full'), (sp_path, 'sparse')):
        o = os.path.join(work, f'{name}.{tag}.m4a')
        subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-map', '0:a:0', '-c', 'copy',
                        '-f', 'ipod', o], check=True)
        md5s = subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-i', src, '-map', '0:a:0', '-c', 'copy',
                               '-f', 'framemd5', '-'], capture_output=True, text=True).stdout
        outs.append((open(o, 'rb').read(), md5s))
    rep['audio_bytes_identical'] = outs[0][0] == outs[1][0]
    rep['audio_packets_identical'] = outs[0][1] == outs[1][1] and outs[0][1].count('\n') > 10
    rep['audio_packets'] = sum(1 for x in outs[0][1].splitlines() if x and not x.startswith('#'))
    # 3. keyframes
    v = movie.video
    kept = filt.kept_sync
    fmt = None
    ours = {}
    t0 = time.time()
    for pts, fr in thumbs.decode_samples(sp_path, v, kept):
        fmt = fr.format.name
        ours[round(pts / v.timescale * 1000)] = plane_md5(fr)
    rep['kf_decode_s_per_frame'] = round((time.time() - t0) / max(1, len(kept)), 3)
    ref = ffmpeg_keyframe_md5(path, fmt)
    # framemd5 pts are in the stream time base = media timescale; ffmpeg shifts by the edit list like we do
    match = sum(1 for p, h in ours.items() if ref.get(p) == h)
    rep['keyframes_kept'] = len(kept)
    rep['keyframes_identical'] = match
    rep['keyframes_total_in_file'] = len(ref)
    # thumbnails as the ingest writes them
    tdir = os.path.join(work, name + '.kf')
    rep['thumbs'] = thumbs.thumbnails(sp_path, filt.moov_bytes, kept, tdir)
    os.unlink(sp_path)
    rep['ok'] = bool(rep['moov_identical'] and rep['audio_bytes_identical'] and rep['audio_packets_identical']
                     and match == len(kept) and len(kept) > 0)
    return rep


def main():
    work = sys.argv[1]
    files = sys.argv[2:]
    os.makedirs(work, exist_ok=True)
    srv = RangeServer()
    allok = True
    for f in files:
        rep = run(work, f, srv)
        allok &= rep['ok']
        print(rep)
    # 5. every link used once, with the expected status
    codes = [(x[0], x[2]) for x in srv.log]
    print('requests:', len(srv.log), 'ranges(206):', codes.count(('GET', 206)), 'streams(200):', codes.count(('GET', 200)),
          'tokens left unused:', len(srv.httpd.tokens))
    srv.stop()
    print('ALL OK' if allok else 'FAILED')
    sys.exit(0 if allok else 1)


if __name__ == '__main__':
    main()
