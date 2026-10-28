#!/usr/bin/env python3
"""proof_v3.py -- v2 vs v3 proof for the shot-10 splice (tools/splice_v3.py): stream summaries, per-packet and per-decoded-frame
md5 (framemd5), audio stream hashes, PSNR on the re-encoded frames, a clean full decode, sha256 of each file.

    python3 tools/proof_v3.py --pair <v2.mp4> <v3.mp4> [--pair ...] --gop 821 987 --gop 3256 3505 \
        --new 821 897 --cap 898 902 --cap 3362 3447 > PROOF part
  --gop: re-encoded GOPs; --new: frames with a new picture; --cap: frames whose caption changed (PSNR outside the caption band);
  every other frame in a GOP is v2's picture re-encoded (full-frame PSNR).
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


BAND = (1150, 1420)   # tools/caption_patch_v3.py BAND


def psnr(a, b, spans, crop=None):
    """PSNR v2 vs v3 over the frames in spans [(f0, f1) inclusive]; crop 'out' = outside the caption band only."""
    sel = 'select=' + '+'.join(f'between(n\\,{f0}\\,{f1})' for f0, f1 in spans)
    if crop == 'out':
        y0, y1 = BAND
        g = (f'[0:v]{sel},split[a0][a1];[1:v]{sel},split[b0][b1];[a0]crop=iw:{y0}:0:0[at];[a1]crop=iw:ih-{y1}:0:{y1}[ab];'
             f'[b0]crop=iw:{y0}:0:0[bt];[b1]crop=iw:ih-{y1}:0:{y1}[bb];[at][ab]vstack[x];[bt][bb]vstack[y];[x][y]psnr')
    else:
        g = f'[0:v]{sel}[x];[1:v]{sel}[y];[x][y]psnr'
    e = subprocess.run([FF, '-v', 'info', '-i', a, '-i', b, '-filter_complex', g, '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = re.search(r'PSNR y:([\d.inf]+) u:([\d.inf]+) v:([\d.inf]+) average:([\d.inf]+) min:([\d.inf]+) max:([\d.inf]+)', e)
    return m.group(0) if m else 'n/a'


def spans_minus(g0, g1, cut):
    """[g0, g1] minus the cut spans, as inclusive spans."""
    keep = [i for i in range(g0, g1 + 1) if not any(a <= i <= b for a, b in cut)]
    out = []
    for i in keep:
        if out and out[-1][1] == i - 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return [tuple(x) for x in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pair', nargs=2, action='append', required=True)
    ap.add_argument('--gop', nargs=2, type=int, action='append', required=True)
    ap.add_argument('--new', nargs=2, type=int, action='append', default=[])
    ap.add_argument('--cap', nargs=2, type=int, action='append', default=[])
    A = ap.parse_args()
    t = lambda f: f * 1001 / 30000
    for v2, v3 in A.pair:
        print('=' * 100)
        print(f'v2: {v2}\n    sha256 {sha256(v2)}\nv3: {v3}\n    sha256 {sha256(v3)}')
        s2, s3 = summary(v2), summary(v3)
        print('\n-- ffprobe stream summary (v2 | v3; * = differs)')
        for a, b in zip(s2, s3):
            print(f'  {"*" if a != b else " "} {a:<52} | {b}')
        p2, p3 = framemd5(v2, 'v', True), framemd5(v3, 'v', True)
        print(f'\n-- video packets: v2 {len(p2)}, v3 {len(p3)}')
        diff = [i for i, (a, b) in enumerate(zip(p2, p3)) if a != b]
        ts_diff = [i for i, (a, b) in enumerate(zip(p2, p3)) if a[:3] != b[:3]]
        print(f'   packets that differ (decode-order index): {ranges(diff)}')
        print(f'   packets whose dts / pts / duration differ: {ranges(ts_diff)}')
        d2, d3 = framemd5(v2, 'v', False), framemd5(v3, 'v', False)
        dd = [i for i, (a, b) in enumerate(zip(d2, d3)) if a[4] != b[4]]
        out_win = [i for i in dd if not any(g0 <= i <= g1 for g0, g1 in A.gop)]
        print(f'\n-- decoded frames: v2 {len(d2)}, v3 {len(d3)}')
        print(f'   frames whose decoded md5 differs: {ranges(dd)}  ({len(dd)} frames)')
        print(f'   of those outside the re-encoded GOPs {", ".join(f"{a}-{b}" for a, b in A.gop)}: {ranges(out_win)}')
        for a, b in A.new:
            print(f'   new picture: frames {a}-{b} = {t(a):.3f}-{t(b + 1):.3f} s')
        for a, b in A.cap:
            print(f'   caption changed, v2 picture elsewhere: frames {a}-{b} = {t(a):.3f}-{t(b + 1):.3f} s; '
                  f'PSNR outside the caption band (rows {BAND[0]}-{BAND[1] - 1}): {psnr(v2, v3, [(a, b)], "out")}')
        for g0, g1 in A.gop:
            rest = spans_minus(g0, g1, A.new + A.cap)
            print(f'   GOP {g0}-{g1}: frames with v2\'s picture and caption, re-encoded only because they share the GOP: '
                  f'{", ".join(f"{a}-{b}" for a, b in rest)}; PSNR vs v2: {psnr(v2, v3, rest)}')
        same_ts = all(a[:3] == b[:3] for a, b in zip(d2, d3)) and len(d2) == len(d3)
        print(f'   decoded frame timestamps identical: {same_ts}')
        a2, a3 = framemd5(v2, 'a', True), framemd5(v3, 'a', True)
        ah2 = run([FF, '-v', 'error', '-i', v2, '-map', '0:a', '-c', 'copy', '-f', 'md5', '-']).stdout.strip()
        ah3 = run([FF, '-v', 'error', '-i', v3, '-map', '0:a', '-c', 'copy', '-f', 'md5', '-']).stdout.strip()
        print(f'\n-- audio stream (packets, stream copy): v2 {len(a2)} packets {ah2}; v3 {len(a3)} packets {ah3}; '
              f'identical: {a2 == a3 and ah2 == ah3}')
        err = subprocess.run([FF, '-v', 'error', '-i', v3, '-f', 'null', '-'], capture_output=True, text=True).stderr.strip()
        print(f'\n-- full decode of v3: {"clean (no decoder errors)" if not err else err[:500]}')


if __name__ == '__main__':
    main()
