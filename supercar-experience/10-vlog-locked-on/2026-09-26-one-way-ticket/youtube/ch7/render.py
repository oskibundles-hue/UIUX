#!/usr/bin/env python3
"""render.py -- Chapters 5-8 picture (one file, the same in ch5/ ch6/ ch7/ ch8/; copied from ../ch4/render.py: graph,
grade and blur code unchanged). edl.json shots from the mezzanines -> 16:9 cut from the open-gate square (or a 'zoom'
window), rotated where the camera was on its side, re-timed, ch4's locked grade, the dashboard blurs and the chapter
title (edl.json `title`, ch4's card: Anton white on #DE1A22, #FBD101 underline).

    python3 render.py raw       # 640x360, graded and cropped, NO blur or graphics -> WORK/raw_shots/sNN.mp4 (trackers)
    python3 render.py proxy     # 1280x720 from /home/user/owt/mezzB720 -> WORK/proxy_video.mp4 (silent; the 720p cut)
    python3 render.py sheets    # the pre-render frame gate on proxy_video.mp4: WORK/gate/shotNN_*.jpg (every 0.3 s,
                                #   640 px tiles, 4x3, stamped with timeline time and source clip:time)
    python3 render.py master    # 3840x2160 from the 4K mezzanines (VLOG_MEZZ_4K) -> WORK/chN_master.mp4 (+ _NOMUSIC);
                                #   kept for the later 4K pass, not run in the 720p job
WORK is /home/user/day-owt/<chN>work (from this folder's name). proxy_video.mp4 is H.264 High, yuv420p, 1280x720,
30000/1001, mp4 timescale 30000, bt709 tags, crf 20 preset fast, no audio, exactly edl.json `frames` frames: the four
chapters join with a stream copy. Each shot is a whole number of frames, cut on the rounded chapter clock (shot k spans
frames round(t_k * fps) .. round(t_k+1 * fps)), so the frame total equals edl `frames` and mix.py's wavs.

Per-shot framing lives in look.json: `rot` (cw/ccw/180; default edl.json `rotate` for the clip), the crop's vertical
centre `cy` (fraction of the square), or `zoom` [width fraction, centre x, centre y] (a smaller 16:9 window: the
windscreen cutaways in Ch7), and `blur` entries in output fractions (normalised, so they carry to 4K). Blur rule
(Omarie, 2026-10-09, overrides the brief: "only blur should be the dash"): the only blurs in Ch5-8 are the dashboard
(cluster, speedometer, centre screen) while the car is moving. No SE logo, HUD, strip, end card or SE colour.
"""
import glob, json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CHN = os.path.basename(HERE)                              # ch5 .. ch8
WORK = f'/home/user/day-owt/{CHN}work'
MEZZ = os.environ.get('VLOG_MEZZ', '/home/user/owt/mezzB720')
MEZZ_4K = os.environ.get('VLOG_MEZZ_4K', '/home/user/owt/mezzB')
_IIO = '/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
FF = os.environ.get('FFMPEG', _IIO if os.path.exists(_IIO) else 'ffmpeg')
FONT_T = glob.glob('/home/user/day-owt/fonts/fontsource-anton-*/files/anton-latin-400-normal.woff')[0]
FONT_P = glob.glob('/home/user/day-owt/fonts/fontsource-archivo-*/files/archivo-latin-800-normal.woff')[0]
RED, YEL = (0xDE, 0x1A, 0x22), (0xFB, 0xD1, 0x01)
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
FPS = '30000/1001'
FPSF = 30000 / 1001
NF = EDL['frames']
GRADE = 'eq=contrast=1.03:saturation=1.07,colorbalance=rs=0.015:bs=-0.02:rm=0.025:bm=-0.025:rh=0.01:bh=-0.015'   # ch4, locked
LOOK = json.load(open(os.path.join(HERE, 'look.json'))) if os.path.exists(os.path.join(HERE, 'look.json')) else {}
TITLE = EDL['title']          # nq-facts clears the title text
POPS = json.load(open(os.path.join(HERE, 'pops.json'))) if os.path.exists(os.path.join(HERE, 'pops.json')) else []


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f'failed: {" ".join(cmd[:8])} ...')
    return r


def mezz_for(src, a, b, mezz):
    best = None
    for p in glob.glob(f'{mezz}/{src}_*.mov'):
        m = re.match(rf'{src}_([\d.]+)-([\d.]+)\.mov$', os.path.basename(p))
        if m and float(m.group(1)) <= a + 1e-3 and b <= float(m.group(2)) + 1e-3:
            best = (p, float(m.group(1)))
    if not best:
        raise SystemExit(f'no mezzanine covers {src} {a}-{b} in {mezz}')
    return best


def shot_frames():
    """Frames per shot on the rounded chapter clock: the sum is edl `frames` exactly."""
    sh_ = EDL['shots']
    edges = [round(s['t'] * FPSF) for s in sh_] + [NF]
    return [edges[i + 1] - edges[i] for i in range(len(sh_))]


def shot_filter(i, s, W, H, noblur=False):
    lk = LOOK.get(str(i), {})
    f = []
    rot = lk.get('rot', EDL.get('rotate', {}).get(s['src']))
    if rot == 'cw':
        f.append('transpose=1')
    elif rot == 'ccw':
        f.append('transpose=2')
    elif rot == '180':
        f.append('transpose=1,transpose=1')
    if 'zoom' in lk:
        # a smaller 16:9 window: width z of the frame, centred on (cx, cy) as fractions, clamped inside the frame
        z, cx, czy = lk['zoom']
        f.append(f"crop=iw*{z}:iw*{z}*9/16:'max(0,min(iw-ow,iw*{cx}-ow/2))':'max(0,min(ih-oh,ih*{czy}-oh/2))'")
    else:
        cy = lk.get('cy', 0.5)
        if 'cy_keys' in lk:
            ks = lk['cy_keys']
            e = f'{ks[-1][1]}'
            for (ta, ca), (tb, cb) in reversed(list(zip(ks, ks[1:]))):
                u = f'((t-{ta})/{tb - ta:.4f})'
                e = f'if(lt(t,{tb}),{ca}+({cb - ca:.4f})*{u}*{u}*(3-2*{u}),{e})'
            cy = f'({e})'
        f.append(f"crop=iw:iw*9/16:0:'max(0,min(ih-iw*9/16,ih*{cy}-iw*9/32))'")
    if s['speed'] != 1.0:
        f.append(f"setpts=(PTS-STARTPTS)/{s['speed']}")
    else:
        f.append('setpts=PTS-STARTPTS')
    f.append(f'fps={FPS}')
    f.append(GRADE)
    f.append(f'scale={W}:{H}:flags=lanczos')
    chain = ','.join(f)
    blurs = [] if noblur else lk.get('blur', [])
    if not blurs:
        return f'[0:v]{chain},format=yuv420p[v]', []
    P = (H // 4) // 2 * 2
    g = f'[0:v]{chain},pad={W + 2 * P}:{H + 2 * P}:{P}:{P}:black[b0]'
    masks = []
    for k, bl in enumerate(blurs):
        if 'keys' in bl:
            ks = bl['keys']
            bw = max(2, int(max(q[3] for q in ks) * W) // 2 * 2); bh = max(2, int(max(q[4] for q in ks) * H) // 2 * 2)
            cxs = [(q[0], (q[1] + q[3] / 2) * W - bw / 2 + P, (q[2] + q[4] / 2) * H - bh / 2 + P) for q in ks]

            def lin(j):
                e = f'{cxs[-1][j]:.1f}'
                for (ta, *a), (tb, *b) in reversed(list(zip(cxs, cxs[1:]))):
                    e = f'if(lt(t,{tb}),{a[j - 1]:.1f}+({b[j - 1] - a[j - 1]:.1f})*(t-{ta})/{tb - ta:.4f},{e})'
                return e
            bxe = f'clip({lin(1)},0,{W + 2 * P - bw})'; bye = f'clip({lin(2)},0,{H + 2 * P - bh})'
            t0, t1 = round(ks[0][0] - 0.017, 3), round(ks[-1][0] + 0.017, 3)
            r = max(2, min(bw, bh) // 4)
            if bl.get('shape') == 'round':
                masks.append(mask_png(bw, bh))
                g += (f";[b{k}]split[m{k}][c{k}];[c{k}]crop={bw}:{bh}:'{bxe}':'{bye}',boxblur={r}:3,format=yuva420p[zc{k}];"
                      f"[{len(masks)}:v]format=gray[mk{k}];[zc{k}][mk{k}]alphamerge[z{k}];"
                      f"[m{k}][z{k}]overlay='{bxe}':'{bye}':enable='between(t,{t0},{t1})'[b{k + 1}]")
            else:
                g += (f";[b{k}]split[m{k}][c{k}];[c{k}]crop={bw}:{bh}:'{bxe}':'{bye}',boxblur={r}:3[z{k}];"
                      f"[m{k}][z{k}]overlay='{bxe}':'{bye}':enable='between(t,{t0},{t1})'[b{k + 1}]")
            continue
        x, y, w, h = bl['box']
        t0, t1 = bl.get('t', [0, 999])
        bx, by, bw, bh = int(x * W) // 2 * 2 + P, int(y * H) // 2 * 2 + P, max(2, int(w * W) // 2 * 2), max(2, int(h * H) // 2 * 2)
        r = max(2, min(bw, bh) // 4)
        if bl.get('shape') == 'round':
            masks.append(mask_png(bw, bh))
            g += (f";[b{k}]split[m{k}][c{k}];[c{k}]crop={bw}:{bh}:{bx}:{by},boxblur={r}:3,format=yuva420p[zc{k}];"
                  f"[{len(masks)}:v]format=gray[mk{k}];[zc{k}][mk{k}]alphamerge[z{k}];"
                  f"[m{k}][z{k}]overlay={bx}:{by}:enable='between(t,{t0},{t1})'[b{k + 1}]")
        else:
            g += (f';[b{k}]split[m{k}][c{k}];[c{k}]crop={bw}:{bh}:{bx}:{by},boxblur={r}:3[z{k}];'
                  f"[m{k}][z{k}]overlay={bx}:{by}:enable='between(t,{t0},{t1})'[b{k + 1}]")
    return g + f';[b{len(blurs)}]crop={W}:{H}:{P}:{P},format=yuv420p[v]', masks


def mask_png(bw, bh):
    path = f'{WORK}/masks/m{bw}x{bh}.png'
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        im = Image.new('L', (bw, bh))
        px = im.load()
        for yy in range(bh):
            for xx in range(bw):
                d = (abs(2 * xx / bw - 1) ** 4 + abs(2 * yy / bh - 1) ** 4) ** 0.25
                px[xx, yy] = int(255 * min(1, max(0, (1 - d) / 0.3)))
        im.save(path)
    return path


def render_shots(W, H, outdir, crf, preset, mezz, noblur=False, only=None):
    os.makedirs(outdir, exist_ok=True)
    parts = []
    nfs = shot_frames()
    for i, s in enumerate(EDL['shots']):
        nfr = nfs[i]
        src_len = nfr / FPSF * s['speed']
        p, t0 = mezz_for(s['src'], s['in'], s['in'] + src_len, mezz)
        out = f'{outdir}/s{i:02d}.mp4'
        parts.append(out)
        if only is not None and i not in only:
            continue
        graph, masks = shot_filter(i, s, W, H, noblur)
        sig = json.dumps(['pad+mask v3', p, s, nfr, {k: v for k, v in LOOK.get(str(i), {}).items() if not (noblur and k == 'blur')}, EDL.get('rotate', {}).get(s['src']), GRADE, W, crf])
        if os.path.exists(out) and os.path.exists(out + '.sig') and open(out + '.sig').read() == sig:
            continue
        mk = sum([['-loop', '1', '-framerate', FPS, '-i', m] for m in masks], [])
        sh([FF, '-v', 'error', '-y', '-ss', f"{s['in'] - t0:.4f}", '-t', f'{src_len + 0.3:.4f}', '-i', p, *mk,
            '-filter_complex', graph, '-map', '[v]', '-frames:v', str(nfr), '-an',
            '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-threads', '4', out])
        open(out + '.sig', 'w').write(sig)
        print(f'shot {i:02d} {s["src"]} {s["in"]} {nfr} fr', flush=True)
    return parts


# ---------------------------------------------------------------- graphics (PNG sequences with alpha)
def title_frames(W, H, n):
    ft = ImageFont.truetype(FONT_T, int(H * 0.052))
    txt = TITLE['text']
    tw = ft.getbbox(txt)[2]; th = ft.getbbox('INTO OREGON')[3]   # ch4's card height (cap height), so every card matches
    pad = int(H * 0.018)
    x0, y0 = int(W * 0.055), int(H * 0.80)
    frames = []
    for k in range(n):
        tt = k / 29.97
        dur = TITLE['t1'] - TITLE['t0']
        a = min(1, tt / 0.25, max(0, (dur - tt) / 0.3))
        dx = int((1 - min(1, tt / 0.3)) ** 3 * -W * 0.02)
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        sw = int(min(1, tt / 0.35) * (tw + 2 * pad))
        d.rectangle([x0 + dx, y0 - pad, x0 + dx + sw, y0 + th + pad], fill=RED + (int(235 * a),))
        d.rectangle([x0 + dx, y0 + th + pad, x0 + dx + int(sw * 0.35), y0 + th + pad + max(2, int(H * 0.006))], fill=YEL + (int(255 * a),))
        if tt > 0.12:
            d.text((x0 + dx + pad, y0 - int(H * 0.004)), txt, font=ft, fill=(255, 255, 255, int(255 * a)))
        frames.append(im)
    return frames


def pop_frames(W, H, text, n, side):
    frames = []
    for k in range(n):
        tt = k / 29.97
        s = 0.6 + 0.55 * min(1, tt / 0.12) - 0.15 * min(1, max(0, tt - 0.12) / 0.1)
        a = min(1, tt / 0.06, max(0, (n / 29.97 - tt) / 0.15))
        f = ImageFont.truetype(FONT_P, max(8, int(H * 0.11 * s)))
        bb = f.getbbox(text); tw, th = bb[2] - bb[0], bb[3] - bb[1]
        cx = int(W * (0.30 if side == 'l' else 0.70)); cy = int(H * 0.30)
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        st = max(2, int(H * 0.008 * s))
        d.text((cx - tw // 2 + int(H * 0.006), cy - th // 2 + int(H * 0.008)), text, font=f, fill=RED + (int(255 * a),))
        d.text((cx - tw // 2, cy - th // 2), text, font=f, fill=YEL + (int(255 * a),), stroke_width=st, stroke_fill=(0, 0, 0, int(255 * a)))
        frames.append(im.rotate(-4 if side == 'l' else 4, resample=Image.BICUBIC, center=(cx, cy)))
    return frames


def write_overlay(frames, path):
    W, H = frames[0].size
    p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', FPS, '-i', '-',
                          '-c:v', 'qtrle', path], stdin=subprocess.PIPE)
    for im in frames:
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()


def graphics(W, H, outdir):
    ov = []
    n = round((TITLE['t1'] - TITLE['t0']) * 29.97)
    path = f'{outdir}/title.mov'
    write_overlay(title_frames(W, H, n), path); ov.append((path, TITLE['t0']))
    for k, pp in enumerate(POPS):
        path = f'{outdir}/pop{k}.mov'
        write_overlay(pop_frames(W, H, pp['text'], round(pp['dur'] * 29.97), pp.get('side', 'r')), path)
        ov.append((path, pp['t']))
    return ov


def assemble(parts, ov, out, crf, preset):
    lst = out + '.txt'
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    cmd = [FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst]
    for p, t in ov:
        cmd += ['-itsoffset', f'{t:.4f}', '-i', p]
    g = f'[0:v]setpts=N/({FPS})/TB[v0]'
    for k in range(len(ov)):
        g += f';[v{k}][{k + 1}:v]overlay=0:0:eof_action=pass[v{k + 1}]'
    g += f';[v{len(ov)}]format=yuv420p[v]'
    cmd += ['-filter_complex', g, '-map', '[v]', '-frames:v', str(NF)]
    cmd += ['-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-r', FPS,
            '-video_track_timescale', '30000', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-color_range', 'tv', '-movflags', '+faststart', '-an', out]
    sh(cmd)


def mux(video, wav, out, br='320k'):
    sh([FF, '-v', 'error', '-y', '-i', video, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
        '-b:a', br, '-ar', '48000', '-shortest', '-movflags', '+faststart', out])


def raw():
    only = [int(a) for a in sys.argv[2:]] or None
    render_shots(640, 360, f'{WORK}/raw_shots', 16, 'veryfast', MEZZ, noblur=True, only=only)
    print('raw shots in', f'{WORK}/raw_shots')


def proxy():
    W, H = 1280, 720
    d = f'{WORK}/proxy_shots'
    parts = render_shots(W, H, d, 14, 'veryfast', MEZZ)
    ov = graphics(W, H, d)
    v = f'{WORK}/proxy_video.mp4'
    assemble(parts, ov, v, 20, 'fast')
    n = sh(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_packets',
            '-of', 'csv=p=0', v]).stdout.strip()
    print('proxy', v, 'frames', n, 'edl', NF)


def master():
    W, H = 3840, 2160
    d = f'{WORK}/master_shots'
    parts = render_shots(W, H, d, 14, 'veryfast', MEZZ_4K)
    ov = graphics(W, H, d)
    v = f'{WORK}/master_video.mp4'
    assemble(parts, ov, v, 18, 'fast')
    a, b = f'{WORK}/{CHN}_master.mp4', f'{WORK}/{CHN}_master_NOMUSIC.mp4'
    mux(v, f'{WORK}/mix.wav', a)
    mux(v, f'{WORK}/nomusic.wav', b)
    for p in (a, b):
        print(p, os.path.getsize(p))


def sheets():
    """The pre-render frame gate on proxy_video.mp4 (graded, cropped, blurred, titled as it renders): one frame every
    0.3 s, 640 px tiles, 12 a sheet, each tile stamped with timeline time and source clip:time."""
    tl = f'{WORK}/proxy_video.mp4'
    os.makedirs(f'{WORK}/gate', exist_ok=True)
    for i, s in enumerate(EDL['shots']):
        off = s['in'] - s['t']
        txt = (f"{CHN} s{i:02d}  T %{{pts\\:flt}}  {s['src']} %{{pts\\:flt\\:{off:.3f}}}")
        vf = (f"fps=10/3,scale=640:-2,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{txt}':x=8:y=8:fontsize=22:"
              f"fontcolor=white:box=1:boxcolor=black@0.6,tile=4x3")
        sh(['ffmpeg', '-v', 'error', '-y', '-copyts', '-ss', f"{s['t']:.3f}", '-to', f"{s['t'] + s['dur'] - 0.01:.3f}", '-i', tl,
            '-vf', vf, '-fps_mode', 'vfr', f'{WORK}/gate/shot{i:02d}_%02d.jpg'])
    print('sheets in', f'{WORK}/gate')


if __name__ == '__main__':
    {'raw': raw, 'proxy': proxy, 'master': master, 'sheets': sheets}[sys.argv[1]]()
