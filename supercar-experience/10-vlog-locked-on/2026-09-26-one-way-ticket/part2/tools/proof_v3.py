#!/usr/bin/env python3
"""proof_v3.py -- v2 vs v3 proof for the shot-10 splice (tools/splice_v3.py): stream summaries, per-packet and per-decoded-frame
md5 (framemd5), audio stream hashes, PSNR on the re-encoded frames, a clean full decode, sha256 of each file.

    python3 tools/proof_v3.py --pair <v2.mp4> <v3.mp4> [--pair ...] --window 821 897 --gop 821 987 > PROOF part
"""
import argparse, hashlib, re, subprocess

FF, FP = 'ffmpeg', 'ffprobe'


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def summary(p):
    keys = ('codec_name', 'profile', 'level', 'width', 'height', 'pix_fmt', 'color_range', 'color_space', 'color_transfer',
            'color_primaries', 'r_frame_rate', 'avg_frame_rate', 'time_base', 'start_time', 'duration', 'nb_frames', 'has_b_frames',
            'sample_rate', 'channels', 'channel_layout', 'bit_rate')
    out = run([FP, '-v', 'error', '-show_entries', 'stream=' + ','.join(keys) + ':format=duration,size,bit_rate:format_tags=title',
               '-of', 'default=nw=1', p]).stdout
    return out.strip().splitlines()


def framemd5(p, stream, copy):
    cmd = [FF, '-v', 'error', '-i', p, '-map', f'0:{stream}'] + (['-c', 'copy'] if copy else []) + ['-f', 'framemd5', '-']
    rows = []
    for ln in run(cmd).stdout.splitlines():
        if ln.startswith('#'):
            continue
        q = [x.strip() for x in ln.split(',')]
        rows.append(tuple(q[1:]))                      # dts, pts, duration, size, md5
    return rows


def ranges(ix):
    out = []
    for i in ix:
        if out and out[-1][1] == i - 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return ', '.join(f'{a}-{b}' if a != b else f'{a}' for a, b in out) or 'none'


def psnr(a, b, f0, f1):
    sel = f'select=between(n\\,{f0}\\,{f1})'
    e = subprocess.run([FF, '-v', 'info', '-i', a, '-i', b, '-filter_complex', f'[0:v]{sel}[x];[1:v]{sel}[y];[x][y]psnr',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = re.search(r'PSNR y:([\d.inf]+) u:([\d.inf]+) v:([\d.inf]+) average:([\d.inf]+) min:([\d.inf]+) max:([\d.inf]+)', e)
    return m.group(0) if m else 'n/a'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pair', nargs=2, action='append', required=True)
    ap.add_argument('--window', nargs=2, type=int, required=True)
    ap.add_argument('--gop', nargs=2, type=int, required=True)
    A = ap.parse_args()
    w0, w1 = A.window; g0, g1 = A.gop
    for v2, v3 in A.pair:
        print('=' * 100)
        print(f'v2: {v2}\n    sha256 {sha256(v2)}\nv3: {v3}\n    sha256 {sha256(v3)}')
        s2, s3 = summary(v2), summary(v3)
        print('\n-- ffprobe stream summary (v2 | v3; * = differs)')
        for a, b in zip(s2, s3):
            print(f'  {"*" if a != b else " "} {a:<52} | {b}')
        # video packets (decode order, stream copy): dts, pts, duration, size, md5
        p2, p3 = framemd5(v2, 'v', True), framemd5(v3, 'v', True)
        print(f'\n-- video packets: v2 {len(p2)}, v3 {len(p3)}')
        diff = [i for i, (a, b) in enumerate(zip(p2, p3)) if a != b]
        ts_diff = [i for i, (a, b) in enumerate(zip(p2, p3)) if a[:3] != b[:3]]
        print(f'   packets that differ (decode-order index): {ranges(diff)}')
        print(f'   packets whose dts / pts / duration differ: {ranges(ts_diff)}')
        # decoded frames (display order)
        d2, d3 = framemd5(v2, 'v', False), framemd5(v3, 'v', False)
        dd = [i for i, (a, b) in enumerate(zip(d2, d3)) if a[4] != b[4]]
        out_win = [i for i in dd if not (g0 <= i <= g1)]
        print(f'\n-- decoded frames: v2 {len(d2)}, v3 {len(d3)}')
        print(f'   frames whose decoded md5 differs: {ranges(dd)}  ({len(dd)} frames)')
        print(f'   of those outside the re-encoded GOP {g0}-{g1}: {ranges(out_win)}')
        print(f'   new picture (shot 10): frames {w0}-{w1} = {w0 * 1001 / 30000:.3f}-{(w1 + 1) * 1001 / 30000:.3f} s')
        print(f'   re-encoded, same picture (shot 11, from v2\'s own decoded frames): {w1 + 1}-{g1} = '
              f'{(w1 + 1) * 1001 / 30000:.3f}-{(g1 + 1) * 1001 / 30000:.3f} s')
        print(f'   PSNR v3 vs v2, frames {w1 + 1}-{g1}: {psnr(v2, v3, w1 + 1, g1)}')
        same_ts = all(a[:3] == b[:3] for a, b in zip(d2, d3)) and len(d2) == len(d3)
        print(f'   decoded frame timestamps identical: {same_ts}')
        # audio
        a2, a3 = framemd5(v2, 'a', True), framemd5(v3, 'a', True)
        ah2 = run([FF, '-v', 'error', '-i', v2, '-map', '0:a', '-c', 'copy', '-f', 'md5', '-']).stdout.strip()
        ah3 = run([FF, '-v', 'error', '-i', v3, '-map', '0:a', '-c', 'copy', '-f', 'md5', '-']).stdout.strip()
        print(f'\n-- audio stream (packets, stream copy): v2 {len(a2)} packets {ah2}; v3 {len(a3)} packets {ah3}; '
              f'identical: {a2 == a3 and ah2 == ah3}')
        err = subprocess.run([FF, '-v', 'error', '-i', v3, '-f', 'null', '-'], capture_output=True, text=True).stderr.strip()
        print(f'\n-- full decode of v3: {"clean (no decoder errors)" if not err else err[:500]}')


if __name__ == '__main__':
    main()
