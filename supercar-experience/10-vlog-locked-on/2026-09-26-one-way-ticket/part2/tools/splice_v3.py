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

Round 2 (28 Oct, nq-facts block, Omarie by click): two caption changes in the data (build.py caption_words sorts on the
start time only; 0111 54.70 "that's" dropped by the two-model rule), redrawn in two GOP windows of the same single splice:
  window 1 = GOP 821-987: shot 10 (821-897) as round 1 with the new layer; the "NOT A CORVETTE." page stays on to frame 902,
           so frames 898-902 (shot 11, 0112) get shot 11's plate rebuilt (lib/plate.py render_shot(11) + join's speedo box
           and strip glass), the new layer, build.GRAPH, build.VENC; that rebuilt picture is used ONLY at the caption change
           mask (tools/caption_patch_v3.change_mask), every other pixel is v2's decoded frame.
  window 2 = GOP 3256-3505 (0121 28.66 "you guys"): v2's decoded frames, the caption redrawn over v2's own picture where the
           layer changes (tools/caption_patch_v3.patch_rgb; the boxes do not change there).
  Shot 11's mezzanine: 0112_16.3083-20.9.mov in paths.mezz = the engine's recipe (fetch.py cut_range: -ss 16.3 -t 4.6, the
           range fetch.make_plan gives 0112 with 0.8 s handles), named with t0 16.3083 (16.3 + half a 59.94 source frame): with
           t0 16.3 render_shot picks the other source frame of each pair and frames 899-902 match v2 at only 27-34 dB (his arm
           moves fast); with 16.3083 all five match v2 at 43.5 dB (measured 28 Oct), i.e. v2's own frame picks.
  The old layer (v2's captions: captions.json at V2_REV, the old sort) and the new layer are both captured with build.capture.
    python3 tools/splice_v3.py --v2 <v2_main.mp4> --v2n <v2_nomusic.mp4> --out <dir>
"""
import argparse, hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, ROOT)
os.chdir(ROOT)
import numpy as np  # noqa: E402
import plate as PL  # noqa: E402
import build as B  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import caption_patch_v3 as CP  # noqa: E402

K = 10
W, H = 1080, 1920
V3 = os.path.join(B.WORK, 'v3')
FF = B.FF
V2_REV = 'b2530ee'          # round 1 commit: data/captions.json as v2 shows it
W2 = (3256, 3506)           # window 2: v2's GOP holding the 0121 28.66 caption page (IDR 3256 .. IDR 3506)
T11 = (898, 903)            # shot 11 frames under the new 0111 54.70 page (its last page ends at frame 902)
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


def speedo_boxes(k):
    """join()'s static boxes for shot k (config speedo / blurs with a `shot`): [(x, y, w, h, pad, radius)]."""
    out = []
    for b in PL.CFG.get('blurs', []) + PL.CFG.get('speedo', []):
        if 'box' in b and b.get('shot') == k:
            assert not [t for t in PL.CFG['transitions'] if t['into'] == k and t['type'] == 'sweep'], 'a sweep into the shot'
            out.append((*b['box'], b.get('pad', 10), b.get('radius', 14)))
    return out


def blur_box(img, box):
    """join()'s blur_plates for one box, unchanged (lib/plate.py join)."""
    from PIL import Image, ImageFilter
    x, y, w, h, pad, rad = box
    img = img.copy()
    x0, y0 = int(max(0, x - pad)), int(max(0, y - pad))
    x1, y1 = int(min(W, x + w + pad)), int(min(H, y + h + pad))
    m = 2 * rad
    X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
    reg = Image.fromarray(img[Y0:Y1, X0:X1])
    bl = np.asarray(reg.filter(ImageFilter.GaussianBlur(rad)).filter(ImageFilter.BoxBlur(rad // 2)), np.float32)
    yy, xx = np.mgrid[Y0:Y1, X0:X1]
    dx = np.maximum(np.maximum(x0 - xx, xx - x1), 0); dy = np.maximum(np.maximum(y0 - yy, yy - y1), 0)
    a = np.clip(1 - np.hypot(dx, dy) / max(1, pad), 0, 1)[..., None]
    img[Y0:Y1, X0:X1] = (bl * a + img[Y0:Y1, X0:X1].astype(np.float32) * (1 - a) + 0.5).astype(np.uint8)
    return img


def step_plate(k, f0, f1, name):
    """shot k's plate for frames f0..f1-1 (render_shot + join's per-frame treatment: speedo boxes, strip glass)."""
    PL.render_shot(k)
    _, s0, s1 = PL.FR[k]
    assert s0 <= f0 and f1 <= s1, (k, f0, f1, s0, s1)
    GL = PL.glass_rects()
    bad = [b for b in PL.CFG.get('blurs', []) + PL.CFG.get('speedo', []) if 'box' not in b and
           b.get('f0', -1) <= f1 - 1 and b.get('f1', 10 ** 9) >= f0]
    assert not bad, f'tracked plate boxes on the window: {bad}'
    assert not any(PL.punch_at(i / PL.FPS) for i in range(f0, f1)), 'a slam punch in the window'
    assert not [t for t in PL.CFG['transitions'] if t['into'] in (k, k + 1)], 'a transition at the shot edge'
    boxes = speedo_boxes(k)
    out = os.path.join(V3, name)
    enc = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30000/1001', '-i', '-',
                            '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'fast',
                            '-crf', '12', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
    for j, img in enumerate(PL.read_all(os.path.join(B.WORK, 'shots', f'{k:02d}.mov'), f1 - s0)):
        i = s0 + j
        if i < f0:
            continue
        for b in boxes:
            img = blur_box(img, b)
        if i in GL:
            img = PL.strip_glass(img, GL[i])
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
    enc.stdin.close(); assert enc.wait() == 0
    return out


def v2_caption_words():
    """build.caption_words() as v2 ran it: v2's captions.json and the old sort (ties broken on the word)."""
    caps = json.loads(subprocess.run(['git', 'show', f'{V2_REV}:./data/captions.json'], capture_output=True, text=True, check=True,
                                     cwd=ROOT).stdout)
    hide = B.C['captions']['hide']; fix = B.C['captions'].get('fix', {})
    out = []
    for piece in caps + B.C['captions'].get('extra', []):
        for j, (a, b, w) in enumerate(piece['words']):
            if any(h[0] <= a < h[1] for h in hide):
                continue
            for k, v in fix.items():
                w = re.sub(r'\b' + re.escape(k) + r'\b', v, w)
            out.append([round(a, 3), round(b, 3), ('⁣' + w) if j == 0 else w])
    return sorted(out)


def step_layer(frames, d, old=False):
    """build.py st_prep + build.capture() of these frames (old=True: v2's captions)."""
    keep = B.caption_words
    if old:
        B.caption_words = v2_caption_words
    try:
        B.st_prep(argparse.Namespace(draft=False))
        B.capture(list(frames), d)
    finally:
        B.caption_words = keep
        if old:
            B.st_prep(argparse.Namespace(draft=False))
    for i in frames:
        assert os.path.exists(os.path.join(d, f'{i:05d}.png')), i
    return d


def step_master(plate_w, front, f0, f1, name):
    out = os.path.join(V3, name)
    sh([FF, '-v', 'error', '-y', '-i', plate_w, '-framerate', '30000/1001', '-start_number', str(f0), '-i', os.path.join(front, '%05d.png'),
        '-filter_complex_threads', '4', '-filter_complex', B.GRAPH, '-map', '[v]', '-frames:v', str(f1 - f0), *B.VENC, '-an', out])
    return out


def raw_frames(path, a=None, b=None, fmt='yuv420p', vf=None):
    f = [f'select=between(n\\,{a}\\,{b})'] if a is not None else []
    f += [vf] if vf else []
    vfa = ['-vf', ','.join(f)] if f else []
    return subprocess.run([FF, '-v', 'error', '-i', path, *vfa, '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', fmt, '-'],
                          capture_output=True, check=True).stdout


FS = W * H * 3 // 2
TO_RGB = 'scale=in_color_matrix=bt709:in_range=tv'          # v2's yuv -> the GRAPH's RGB (its overlay works in gbrp)


def to_yuv(rgb_frames):
    """RGB frames -> yuv420p the way build.GRAPH ends (scale=out_color_matrix=bt709:out_range=tv,format=yuv420p)."""
    p = subprocess.run([FF, '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-i', '-', '-vf',
                        'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'],
                       input=b''.join(rgb_frames), capture_output=True, check=True)
    return [p.stdout[k * FS:(k + 1) * FS] for k in range(len(rgb_frames))]


def band_outside_equal(a, b):
    """True when two yuv420p frames are identical outside CP.BAND (luma rows and the chroma rows under them)."""
    y0, y1 = CP.BAND
    A = np.frombuffer(a, np.uint8); Bq = np.frombuffer(b, np.uint8)
    ys = W * H; Y = A[:ys].reshape(H, W) != Bq[:ys].reshape(H, W)
    C = (A[ys:] != Bq[ys:]).reshape(2, H // 2, W // 2)
    return not (Y[:y0].any() or Y[y1:].any() or C[:, :y0 // 2].any() or C[:, y1 // 2:].any())


def gop_encode(frames, v2, name):
    out = os.path.join(V3, name)
    p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{W}x{H}', '-r', '30000/1001', '-i', '-',
                          *GOPENC, '-video_track_timescale', '30000', '-an', out], stdin=subprocess.PIPE)
    for f in frames:
        assert len(f) == FS
        p.stdin.write(f)
    p.stdin.close(); assert p.wait() == 0
    assert avcc(out) == avcc(v2), f'{name}: SPS / PPS differ from v2: the splice would not decode'
    return out


def split(buf):
    assert len(buf) % FS == 0
    return [buf[k * FS:(k + 1) * FS] for k in range(len(buf) // FS)]


def step_gop1(master_w, master11, v2, g0, g1, f1, old, new, rep):
    """GOP 821-987: new shot 10 + shot 11 frames 898-902 (v2 + rebuilt picture at the caption mask) + v2 903-987."""
    new10 = split(raw_frames(master_w)); assert len(new10) == f1 - g0
    t0, t1 = T11
    v2f = split(raw_frames(v2, f1, g1 - 1)); assert len(v2f) == g1 - f1
    m11 = split(raw_frames(master11)); assert len(m11) == t1 - t0
    out = list(v2f)
    for j, i in enumerate(range(t0, t1)):
        M = CP.change_mask(os.path.join(old, f'{i:05d}.png'), os.path.join(new, f'{i:05d}.png'))
        out[i - f1], Mc = CP.paste_yuv(v2f[i - f1], m11[j], M)
        assert band_outside_equal(out[i - f1], v2f[i - f1])
        rep['w1_tail'].append(dict(frame=i, mask_px=int(M.sum()), chroma_px=int(Mc.sum()), outside_band_identical=True,
                                   psnr_rebuilt_vs_v2_outside_band=psnr_outside(m11[j], v2f[i - f1])))
    for i in range(t1, g1):
        assert out[i - f1] == v2f[i - f1]
    return gop_encode(new10 + out, v2, 'gop1.mp4')


def psnr_outside(a, b):
    """luma PSNR of two yuv420p frames outside CP.BAND."""
    y0, y1 = CP.BAND
    A = np.frombuffer(a, np.uint8)[:W * H].reshape(H, W).astype(np.float64); Bq = np.frombuffer(b, np.uint8)[:W * H].reshape(H, W).astype(np.float64)
    m = np.ones((H, W), bool); m[y0:y1] = False
    mse = ((A - Bq)[m] ** 2).mean()
    return round(10 * np.log10(255 ** 2 / mse), 2) if mse else float('inf')


def step_gop2(v2, old, new, rep):
    """GOP 3256-3505: v2's decoded frames, the caption redrawn over v2's own picture where the layer changes."""
    g0, g1 = W2
    v2f = split(raw_frames(v2, g0, g1 - 1)); assert len(v2f) == g1 - g0
    rgb = raw_frames(v2, g0, g1 - 1, fmt='rgb24', vf=TO_RGB)
    out = list(v2f)
    todo = []
    for i in range(g0, g1):
        F = np.frombuffer(rgb[(i - g0) * W * H * 3:(i - g0 + 1) * W * H * 3], np.uint8).reshape(H, W, 3).astype(np.float32)
        N, M, err = CP.patch_rgb(F, os.path.join(old, f'{i:05d}.png'), os.path.join(new, f'{i:05d}.png'))
        if M.any():
            todo.append((i, (N + 0.5).clip(0, 255).astype(np.uint8), M, err))
    yuv = to_yuv([np.ascontiguousarray(n).tobytes() for _, n, _, _ in todo])
    for (i, _, M, err), y in zip(todo, yuv):
        out[i - g0], Mc = CP.paste_yuv(v2f[i - g0], y, M)
        assert band_outside_equal(out[i - g0], v2f[i - g0])
        rep['w2'].append(dict(frame=i, mask_px=int(M.sum()), chroma_px=int(Mc.sum()), ink_err=round(err, 2) if err is not None else None,
                              outside_band_identical=True))
    return gop_encode(out, v2, 'gop2.mp4')


def step_splice(v2, gops, audio_srcs, nf):
    """v2's packets, with each [(g0, g1, gop.mp4)] GOP replaced (closed GOPs: g1 is the next IDR)."""
    parts, cur, k = [], 0, 0
    for g0, g1, gop in sorted(gops):
        part = os.path.join(V3, f'copy_{k}.mp4'); k += 1
        ss = ['-ss', f'{cur * 1001 / 30000:.6f}'] if cur else []
        sh([FF, '-v', 'error', '-y', *ss, '-i', v2, '-map', '0:v', '-c', 'copy', '-frames:v', str(g0 - cur), part])
        parts += [part, gop]; cur = g1
    part = os.path.join(V3, f'copy_{k}.mp4')
    sh([FF, '-v', 'error', '-y', '-ss', f'{cur * 1001 / 30000:.6f}', '-i', v2, '-map', '0:v', '-c', 'copy', part])
    parts.append(part)
    lst = os.path.join(V3, 'concat.txt')
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    vid = os.path.join(V3, 'video_v3.mp4')
    # -auto_convert 0: the concat demuxer would otherwise run h264_mp4toannexb and every IDR packet would carry an in-band SPS / PPS
    # (+42 bytes) that v2's packets do not have
    sh([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-auto_convert', '0', '-i', lst, '-map', '0:v', '-c', 'copy', '-video_track_timescale', '30000', vid])
    assert keyframes(vid)[1] == nf
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
    assert g1 >= T11[1] and W2[0] in keys and W2[1] in keys and not [k for k in keys if W2[0] < k < W2[1]]
    print(f'shot {K}: frames {f0}-{f1 - 1}; v2 GOP {g0}-{g1 - 1}; shot 11 tail {T11[0]}-{T11[1] - 1}; window 2 GOP {W2[0]}-{W2[1] - 1}', flush=True)
    st = A.steps.split(',')
    old, new = os.path.join(V3, 'layer_v2'), os.path.join(V3, 'front')
    if 'plate' in st:
        step_plate(K, f0, f1, 'plate_w.mov'); step_plate(K + 1, *T11, 'plate11_w.mov')
    if 'layer' in st:
        step_layer(list(range(T11[0], T11[1])) + list(range(*W2)), old, old=True)
        step_layer(list(range(f0, T11[1])) + list(range(*W2)), new)
    if 'master' in st:
        step_master(os.path.join(V3, 'plate_w.mov'), new, f0, f1, 'master_w.mp4')
        step_master(os.path.join(V3, 'plate11_w.mov'), new, *T11, 'master11_w.mp4')
    rep = dict(w1_tail=[], w2=[])
    if 'gop' in st:
        step_gop1(os.path.join(V3, 'master_w.mp4'), os.path.join(V3, 'master11_w.mp4'), A.v2, g0, g1, f1, old, new, rep)
        step_gop2(A.v2, old, new, rep)
        json.dump(rep, open(os.path.join(V3, 'mask_report.json'), 'w'), indent=1)
    if 'splice' in st:
        title = 'One-way ticket, Part 2 - Supercar Experience vlog'
        gops = [(g0, g1, os.path.join(V3, 'gop1.mp4')), (W2[0], W2[1], os.path.join(V3, 'gop2.mp4'))]
        outs = step_splice(A.v2, gops, [(A.v2, os.path.join(A.out, NAME + '.mp4'), title),
                                        (A.v2n, os.path.join(A.out, NAME + ' - NO MUSIC.mp4'), title + ' (no music)')], nf)
        for o in outs:
            print(hashlib.sha256(open(o, 'rb').read()).hexdigest(), o)
    json.dump(dict(shot=K, f0=f0, f1=f1, gop=[g0, g1], shot11_tail=list(T11), window2=list(W2), src=PL.SHOTS[K], cfg=PL.scfg(K)),
              open(os.path.join(V3, 'splice.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
