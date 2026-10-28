#!/usr/bin/env python3
"""splice_v3.py -- One-way ticket Part 2 v3: a new picture for shot 10 spliced into the delivered v2 pair, nothing else touched.

Why: v2's shot 10 (0111 54.5-57.05, 27.4-29.95 s) showed the store ceiling upside down under "I was like, that's not a
Corvette." (FAIL card 20261027-cb071403-09b521, row "Frame gate"). Omarie picked SPLICE INTO v2. v2's .work/ is gone, so the
whole piece is NOT re-rendered: only the picture of shot 10 is rebuilt with this build's own code and spliced in.

New shot 10 (data/edl.json, tools/make_edl.py): 0111 147.6-150.15, the McLaren parked at the pump at night (the same stop,
after the store), graded "night" by lib/plate.py like its neighbours. config.json shots.10.clockAs {0111, 54.5} keeps the
strip clock exactly as v2 (20:08:29 at the shot's first frame), so the layer (strip + caption) is v2's layer.

Steps (all under .work/v3/):
  plate    lib/plate.py render_shot(10) from the mezzanine (paths.mezz: 0111_146.0-152.0.mov, made like engine/lib/fetch.py:
           long side 1920 lanczos, native 59.94, x264 High 10 CRF 13), then join()'s per-frame treatment for frames
           821-897: the strip glass (plate.strip_glass on plate.glass_rects()); asserts there is no plate blur, speedo box,
           punch or transition there. Encoded like plate.mov (x264 fast CRF 12 yuv420p).
  layer    build.py st_prep (scene, clock, tracks) and build.capture() of frames 821-897 (story.html, lib/kcap2.js).
  master   build.GRAPH (plate + vignette + layer) -> build.VENC (the master CRF 17.3 generation, as v2's master).
  gop      v2's GOP that holds shot 10 is frames 821-987 (IDR 821 .. IDR 988, closed GOP, one slice). It is re-encoded from
           the new shot 10 (821-897) + v2's own decoded frames 898-987 (shot 11, same pictures), with v2's encoder settings
           (x264 core 164, preset slow, High, VBV 14M / 22M, keyint 250) at CRF 16 (see GOPENC) so shot 11 stays as close to v2 as the
           re-encode allows. Its avcC (SPS / PPS) must equal v2's, or the splice stops.
  splice   v2 packets 0-820 (stream copy) + the new GOP + v2 packets 988-end (stream copy), concat demuxer, then each v2
           file's AUDIO stream copied untouched -> the two v3 masters.
  proof    framemd5 (packets and decoded frames) v2 vs v3, audio packet md5, ffprobe summaries, PSNR on 898-987.

    python3 tools/splice_v3.py --v2 <v2_main.mp4> --v2n <v2_nomusic.mp4> --out <dir>
"""
import argparse, hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, ROOT)
os.chdir(ROOT)
import numpy as np  # noqa: E402
import plate as PL  # noqa: E402
import build as B  # noqa: E402

K = 10
W, H = 1080, 1920
V3 = os.path.join(B.WORK, 'v3')
FF = B.FF
NAME = '2026-09-26 One-way ticket Part 2 v3 - SE LOCKED-ON vlog - 1080x1920'
# v2 delivery video settings (x264 SEI of v2: preset slow, ref 5, bframes 3, b_pyramid 2, keyint 250, VBV 14000/22000)
GOPENC = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-maxrate', '14M', '-bufsize', '22M', '-profile:v', 'high',
          '-pix_fmt', 'yuv420p',
          '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
# CRF 16: in CRF mode x264 writes the CRF as the PPS pic_init_qp; v2's PPS has pic_init_qp 16 (pic_init_qp_minus26 -10), so
# CRF 16 is the one value whose PPS equals v2's avcC byte for byte (CRF 12 and stitchable=1 both gave a different PPS)


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def keyframes(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries', 'packet=pts,flags', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout.split()
    pts = sorted((int(l.split(',')[0]), 'K' in l.split(',')[1]) for l in out)
    return [i for i, (_, k) in enumerate(pts) if k], len(pts)


def avcc(path):
    """the avcC box payload of the video track (SPS / PPS the decoder uses for every sample)."""
    d = open(path, 'rb').read()
    i = d.find(b'avcC')
    n = int.from_bytes(d[i - 4:i], 'big')
    return d[i + 4:i - 4 + n]


def step_plate(f0, f1):
    PL.render_shot(K)
    n = f1 - f0
    GL = PL.glass_rects()
    bad = [b for b in PL.CFG.get('blurs', []) + PL.CFG.get('speedo', []) if b.get('shot') == K or
           ('f0' in b and b['f0'] <= f1 - 1 and b.get('f1', 10 ** 9) >= f0)]
    assert not bad, f'plate boxes on the window: {bad}'
    assert not any(PL.punch_at(i / PL.FPS) for i in range(f0, f1)), 'a slam punch in the window'
    assert not [t for t in PL.CFG['transitions'] if t['into'] in (K, K + 1)], 'a transition at the window edge'
    out = os.path.join(V3, 'plate_w.mov')
    enc = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30000/1001', '-i', '-',
                            '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'fast',
                            '-crf', '12', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
    for j, img in enumerate(PL.read_all(os.path.join(B.WORK, 'shots', f'{K:02d}.mov'), n)):
        i = f0 + j
        if i in GL:
            img = PL.strip_glass(img, GL[i])
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
    enc.stdin.close(); assert enc.wait() == 0
    return out


def step_layer(f0, f1):
    B.st_prep(argparse.Namespace(draft=False))
    d = os.path.join(V3, 'front')
    B.capture(list(range(f0, f1)), d)
    for i in range(f0, f1):
        assert os.path.exists(os.path.join(d, f'{i:05d}.png')), i
    return d


def step_master(plate_w, front, f0, f1):
    out = os.path.join(V3, 'master_w.mp4')
    sh([FF, '-v', 'error', '-y', '-i', plate_w, '-framerate', '30000/1001', '-start_number', str(f0), '-i', os.path.join(front, '%05d.png'),
        '-filter_complex_threads', '4', '-filter_complex', B.GRAPH, '-map', '[v]', '-frames:v', str(f1 - f0), *B.VENC, '-an', out])
    return out


def raw_frames(path, a=None, b=None):
    vf = ['-vf', f'select=between(n\\,{a}\\,{b})'] if a is not None else []
    return subprocess.run([FF, '-v', 'error', '-i', path, *vf, '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'],
                          capture_output=True, check=True).stdout


def step_gop(master_w, v2, g0, g1, f1):
    fs = W * H * 3 // 2
    new = raw_frames(master_w)
    old = raw_frames(v2, f1, g1 - 1)
    assert len(new) == fs * (f1 - g0) and len(old) == fs * (g1 - f1), (len(new) / fs, len(old) / fs)
    out = os.path.join(V3, 'gop.mp4')
    p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}', '-r', '30000/1001', '-i', '-',
                          *GOPENC, '-video_track_timescale', '30000', '-an', out], stdin=subprocess.PIPE)
    p.stdin.write(new); p.stdin.write(old); p.stdin.close(); assert p.wait() == 0
    assert avcc(out) == avcc(v2), 'the new GOP\'s SPS / PPS differ from v2: the splice would not decode'
    return out


def step_splice(v2, gop, g0, g1, audio_srcs):
    a = os.path.join(V3, 'a.mp4'); c = os.path.join(V3, 'c.mp4')
    # decode order: closed GOPs, so the first g0 packets are display frames 0..g0-1; from IDR g1 to the end by seek
    sh([FF, '-v', 'error', '-y', '-i', v2, '-map', '0:v', '-c', 'copy', '-frames:v', str(g0), a])
    kt = g1 * 1001 / 30000
    sh([FF, '-v', 'error', '-y', '-ss', f'{kt:.6f}', '-i', v2, '-map', '0:v', '-c', 'copy', c])
    lst = os.path.join(V3, 'concat.txt')
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in (a, gop, c)))
    vid = os.path.join(V3, 'video_v3.mp4')
    # -auto_convert 0: the concat demuxer would otherwise run h264_mp4toannexb and every IDR packet would carry an in-band SPS / PPS
    # (+42 bytes) that v2's packets do not have
    sh([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-auto_convert', '0', '-i', lst, '-map', '0:v', '-c', 'copy', '-video_track_timescale', '30000', vid])
    outs = []
    for src, out, title in audio_srcs:
        sh([FF, '-v', 'error', '-y', '-i', vid, '-i', src, '-map', '0:v', '-map', '1:a', '-c', 'copy', '-movflags', '+faststart',
            '-metadata', f'title={title}', out])
        outs.append(out)
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--v2', required=True); ap.add_argument('--v2n', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--steps', default='plate,layer,master,gop,splice')
    A = ap.parse_args()
    os.makedirs(V3, exist_ok=True); os.makedirs(A.out, exist_ok=True)
    _, f0, f1 = PL.FR[K]
    keys, nf = keyframes(A.v2)
    assert nf == PL.NF, (nf, PL.NF)
    g0 = max(k for k in keys if k <= f0); g1 = min(k for k in keys if k >= f1)
    print(f'shot {K}: frames {f0}-{f1 - 1}; v2 GOP {g0}-{g1 - 1} (IDR {g0}, next IDR {g1})', flush=True)
    st = A.steps.split(',')
    plate_w = step_plate(f0, f1) if 'plate' in st else os.path.join(V3, 'plate_w.mov')
    front = step_layer(f0, f1) if 'layer' in st else os.path.join(V3, 'front')
    master_w = step_master(plate_w, front, f0, f1) if 'master' in st else os.path.join(V3, 'master_w.mp4')
    gop = step_gop(master_w, A.v2, g0, g1, f1) if 'gop' in st else os.path.join(V3, 'gop.mp4')
    if 'splice' in st:
        title = 'One-way ticket, Part 2 - Supercar Experience vlog'
        outs = step_splice(A.v2, gop, g0, g1, [(A.v2, os.path.join(A.out, NAME + '.mp4'), title),
                                               (A.v2n, os.path.join(A.out, NAME + ' - NO MUSIC.mp4'), title + ' (no music)')])
        for o in outs:
            print(hashlib.sha256(open(o, 'rb').read()).hexdigest(), o)
    json.dump(dict(shot=K, f0=f0, f1=f1, gop=[g0, g1], src=PL.SHOTS[K], cfg=PL.scfg(K)), open(os.path.join(V3, 'splice.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
