#!/usr/bin/env python3
"""render.py -- the opening test's picture for edl_A.json / edl_B.json: shots from the 3840 open-gate square mezzanines
(/home/user/day-owt/mezz_open, cut by vlog.py fetch) -> 16:9 window from the square (rotated where the camera was on its
side), 59.94 -> 29.97, the approved test chapter's warm grade (GRADE and the crop/blur code are imported from
../test-ch3/render.py, so A and B match the chapter), plate/cluster blurs from look.json, NOTHING drawn on screen
(no title, no word pops, no captions), muxed with mix_<A|B>.wav.

look.json is keyed "<src>:<in>" (the same shot sits at different indexes in A and B): rot, cy (the crop's vertical centre
as a fraction of the square), blur boxes in output fractions (see ../test-ch3/README.md).

    python3 render.py gate A|B      # 1280x720 timeline (the picture as it will render) + gate sheets in opening-test/gate/
    python3 render.py preview A|B   # opening_<A|B>_preview_720p.mp4 (H.264 + AAC, well under 29 MiB)
    python3 render.py timeline B2   # the 1280x720 timeline only (WORK/timeline_B2.mp4), no gate sheets
    python3 render.py master B2     # 3840x2160 master (9 Oct): WORK/master_video.mp4 + the two muxed masters + 720p preview

4K master: every pixel value (blur boxes, feathers, blur sigma) is worked out on the 1280x720 design exactly as the
approved preview, then multiplied by ONE scale factor S = W / 1280 (3 at 3840x2160); the CH1 subject lift runs on the
720p design and is applied at full size (subject_lift.lift_pipe_hi). The final encode and the AAC mux are ../ch3/render.py's
own assemble() and mux() (H.264 High, crf 18 fast, 30000/1001, bt709 tags, AAC 320k), so the opening joins the
chapters with a stream copy. The source is /home/user/day-owt/mezz only (VLOG_MEZZ_LONG=3840 square mezzanines).
"""
import glob, importlib.util, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CH3 = os.path.join(HERE, '..', 'test-ch3')
_IIO = '/usr/local/lib/python3.13/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
if not os.path.exists(_IIO):
    os.environ.setdefault('FFMPEG', 'ffmpeg')   # test-ch3/render.py defaults to the imageio build; fall back to the system ffmpeg
spec = importlib.util.spec_from_file_location('ch3render', os.path.join(CH3, 'render.py'))
R = importlib.util.module_from_spec(spec)
_cwd = os.getcwd(); os.chdir(CH3); spec.loader.exec_module(R); os.chdir(_cwd)
FF, GRADE, FPS = R.FF, R.GRADE, R.FPS
WORK = '/home/user/day-owt/openwork'
MEZZ = ['/home/user/day-owt/mezz']   # 9 Oct: mezz_open / mezz_open2 are gone; every B2 shot is covered here
LOOK = json.load(open(os.path.join(HERE, 'look.json')))
LOOK2 = json.load(open(os.path.join(HERE, 'look_v2.json')))   # v2 (A2/B2): overrides look.json; v1 (A/B) never reads it
V2 = len(sys.argv) > 2 and sys.argv[2].endswith('2')
W, H = 1280, 720          # the design (gate, preview); master renders at 3840x2160 with S = 3
GFF = 'ffmpeg'   # the gate sheets need drawtext, which the imageio build lacks


def mezz_for(src, a, b):
    for d in MEZZ:
        for p in glob.glob(f'{d}/{src}_*.mov'):
            m = re.match(rf'{src}_([\d.]+)-([\d.]+)\.mov$', os.path.basename(p))
            if m and float(m.group(1)) <= a + 1e-3 and b <= float(m.group(2)) + 1e-3:
                return p, float(m.group(1))
    raise SystemExit(f'no mezzanine covers {src} {a}-{b}')


FILTER_VERSION = 'v2-feather-zoom-lift'


def _feather_alpha(bw, bh, f, edges):
    """alpha of a blur patch: 255 inside, a linear ramp over `f` px at every edge that is NOT the frame edge
    (edges = (left, right, top, bottom) True where the patch sits against the frame boundary: no ramp there)."""
    L, Rr, T, B = edges
    big = '1000'
    dl = big if L else f'(X+0.5)/{f}'
    dr = big if Rr else f'({bw}-X-0.5)/{f}'
    dt = big if T else f'(Y+0.5)/{f}'
    db = big if B else f'({bh}-Y-0.5)/{f}'
    return f"255*clip(min(min({dl},{dr}),min({dt},{db})),0,1)"


def _patch(g, k, W, H, x, y, w, h, enable=None, pos=None, S=1):
    """One soft blur: the region (x, y, w, h in 1280x720 DESIGN px) is hidden by a gaussian blur of its own pixels; the
    patch is grown by a feather band (a quarter of the short side, at least 6 px) whose alpha ramps to 0, so no hard edge
    shows. Everything is worked out on the design (W, H = 1280, 720), then scaled by S (the output is W*S x H*S).
    Returns the graph text; `pos` = (xexpr, yexpr) for a moving patch (size fixed)."""
    f = max(6, int(min(w, h) * 0.25))
    x0, y0 = max(0, x - f), max(0, y - f)
    x1, y1 = min(W, x + w + f), min(H, y + h + f)
    bw, bh = (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2
    edges = (x0 == 0, x1 >= W, y0 == 0, y1 >= H)
    sig = max(2.0, min(w, h) / 3.5)
    f, x0, y0, bw, bh, sig = f * S, x0 * S, y0 * S, bw * S, bh * S, sig * S
    alpha = _feather_alpha(bw, bh, f, edges)
    en = f":enable='{enable}'" if enable else ''
    return (f";[b{k}]split[m{k}][c{k}];[c{k}]crop={bw}:{bh}:{x0}:{y0},gblur=sigma={sig:.1f}:steps=3,"
            f"format=yuva444p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='{alpha}'[z{k}];"
            f"[m{k}][z{k}]overlay={x0}:{y0}{en}[b{k + 1}]")


def shot_filter(s, W, H, lk):
    """The test chapter's chain (rotate, 16:9 window, 29.97, grade, scale) plus, per look.json:
       zoom / cx / cy : window = full width / zoom, anchored at vertical centre cy (clamped to the top), centred on cx
       lift           : {t0, t1, gamma} a gentle gamma ramp on the shot, BEFORE the grade (exposure for a dark tail)
       blur           : [{box:[x,y,w,h]}] soft feathered blurs of the real pixels (fractions of the output frame)"""
    f = []
    rot = lk.get('rot')
    if rot == 'cw':
        f.append('transpose=1')
    elif rot == 'ccw':
        f.append('transpose=2')
    cy, z, cx = lk.get('cy', 0.5), lk.get('zoom', 1.0), lk.get('cx', 0.5)
    cw = f'iw/{z}'
    f.append(f"crop=w='{cw}':h='{cw}*9/16':x='(iw-{cw})*{cx}':y='max(0,min(ih-{cw}*9/16,ih*{cy}-{cw}*9/32))'")
    f.append('setpts=PTS-STARTPTS')
    f.append(f'fps={FPS}')
    if 'lift' in lk:
        L = lk['lift']
        f.append(f"eq=gamma='1+{L['gamma'] - 1:.3f}*clip((t-{L['t0']})/{L['t1'] - L['t0']},0,1)':eval=frame")
    f.append(GRADE)
    f.append(f'scale={W}:{H}:flags=lanczos')
    chain = ','.join(f)
    blurs = lk.get('blur', [])
    if not blurs:
        return f'[0:v]{chain},format=yuv420p[v]'
    g = f'[0:v]{chain}[b0]'
    S = W // 1280                           # the one scale factor: boxes, feathers and sigma come from the 720p design
    DW, DH = W // S, H // S
    for k, bl in enumerate(blurs):
        x, y, w, h = bl['box']
        en = f"gte(t,{bl['from']})" if 'from' in bl else None     # v2.1: a blur that starts part-way through the shot
        g += _patch(g, k, DW, DH, int(round(x * DW)), int(round(y * DH)), int(round(w * DW)), int(round(h * DH)), enable=en, S=S)
    return g + f';[b{len(blurs)}]format=yuv420p[v]'



def key(s):
    return f"{s['src']}:{s['in']:g}"


def look_of(s):
    k = key(s)
    if V2:
        if s['src'] == '0075' and s['in'] >= 80.5 - 1e-6:
            return LOOK2['0075:ch1']          # the CH1 tail, wherever B2's J-cut puts its in-point
        if k in LOOK2:
            return LOOK2[k]
    return LOOK.get(k, {})


def render_shots(edl, W=W, H=H, d=None):
    d = d or (f'{WORK}/shots2' if V2 else f'{WORK}/shots')
    os.makedirs(d, exist_ok=True)
    parts = []
    for s in edl['shots']:
        k = key(s)
        p, t0 = mezz_for(s['src'], s['in'], s['in'] + s['dur'])
        out = f"{d}/{k.replace(':', '_')}_{s['dur']:.3f}.mp4"
        parts.append(out)
        lk = look_of(s)
        sig = json.dumps([p, s['in'], s['dur'], lk, GRADE, FILTER_VERSION] + ([W, H] if W != 1280 else []))
        if os.path.exists(out + '.sig') and open(out + '.sig').read() == sig:
            continue
        nfr = round(s['dur'] * 30000 / 1001)
        if 'subject_lift' in lk:
            import subject_lift as SL
            g = shot_filter(s, W, H, lk).replace('format=yuv420p[v]', f"hqdn3d={lk['subject_lift'].get('denoise', '3:2:6:5')},format=yuv444p16le[v]")
            dec = [FF, '-v', 'error', '-ss', f"{s['in'] - t0:.4f}", '-t', f"{s['dur'] + 0.2:.4f}", '-i', p,
                   '-filter_complex', g, '-map', '[v]', '-frames:v', str(nfr), '-an', '-f', 'rawvideo', '-pix_fmt', 'yuv444p16le', '-']
            enc = [FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv444p16le', '-s', f'{W}x{H}', '-r', '30000/1001', '-i', '-',
                   '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-threads', '8', out]
            A = SL.lift_pipe(dec, enc, nfr, s['in']) if W == 1280 else SL.lift_pipe_hi(dec, enc, nfr, s['in'], W, H)
            open(out + '.lift.json', 'w').write(json.dumps([round(float(a), 3) for a in A]))
            open(out + '.sig', 'w').write(sig)
            print('shot', k, s['dur'], 'subject lift A max', round(float(max(A)), 2), flush=True)
            continue
        R.sh([FF, '-v', 'error', '-y', '-ss', f"{s['in'] - t0:.4f}", '-t', f"{s['dur'] + 0.2:.4f}", '-i', p,
              '-filter_complex', shot_filter(s, W, H, lk), '-map', '[v]', '-frames:v', str(nfr), '-an',
              '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-threads', '8', out])
        open(out + '.sig', 'w').write(sig)
        print('shot', k, s['dur'], flush=True)
    return parts


def timeline(name):
    edl = json.load(open(os.path.join(HERE, f'edl_{name}.json')))
    parts = render_shots(edl)
    tl = f'{WORK}/timeline_{name}.mp4'
    lst = tl + '.txt'
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    R.sh([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', tl])
    return edl, tl


def gate(name):
    edl, tl = timeline(name)
    g = os.path.join(HERE, 'gate'); os.makedirs(g, exist_ok=True)
    # 1) the lead's sheet: in / mid / out of every shot, one PNG (3 columns of 640 = 1920 px wide)
    tiles = []
    tl_dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', tl],
                                  capture_output=True, text=True).stdout)
    for i, s in enumerate(edl['shots']):
        for lab, tt in (('in', s['t'] + 0.05), ('mid', s['t'] + s['dur'] / 2), ('out', min(s['t'] + s['dur'] - 0.08, tl_dur - 0.12))):
            f = f'{WORK}/gt_{name}_{i:02d}_{lab}.png'
            src_t = s['in'] + (tt - s['t'])
            txt = f"{name}{i:02d} {s['kind']} {s['src']} {src_t:.2f} ({lab}) tl {tt:.2f}"
            R.sh([GFF, '-v', 'error', '-y', '-ss', f'{tt:.3f}', '-i', tl, '-frames:v', '1', '-vf',
                  f"scale=640:360,drawtext=text='{txt}':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.65", f])
            tiles.append(f)
    sheet = os.path.join(g, f'opening_{name}_shots_in_mid_out.png')
    ins = sum([['-i', t] for t in tiles], [])
    n = len(edl['shots'])
    R.sh([FF, '-v', 'error', '-y', *ins, '-filter_complex',
          ''.join(f'[{k}:v]' for k in range(len(tiles))) + f'xstack=inputs={len(tiles)}:layout=' +
          '|'.join(f'{c * 640}_{r * 360}' for r in range(n) for c in range(3)), '-frames:v', '1', sheet])
    # 2) the vlog frame gate: every 0.3 s, 640 px tiles, 12 a sheet, stamped with timeline time
    R.sh([GFF, '-v', 'error', '-y', '-i', tl, '-vf',
          "fps=10/3,scale=640:-2,drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6,tile=4x3",
          '-fps_mode', 'vfr', os.path.join(g, f'gate_{name}_%02d.jpg')])
    print('gate', sheet)


def preview(name):
    edl, tl = timeline(name)
    out = os.path.join(HERE, f'opening_{name}_preview_720p.mp4')
    R.sh([FF, '-v', 'error', '-y', '-i', tl, '-i', f'{WORK}/mix_{name}.wav', '-map', '0:v', '-map', '1:a',
          '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-maxrate', '5M', '-bufsize', '10M', '-profile:v', 'high',
          '-pix_fmt', 'yuv420p', '-r', FPS, '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
          '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', out])
    print(out, os.path.getsize(out))


def master(name):
    """3840x2160: the shots at S = 3 (crf 14 intermediates, as ../ch3), then ../ch3/render.py's assemble() (the chapters'
    final encode) -> WORK/master_video.mp4; its mux() with mix_<name>.wav and nomusic_<name>.wav (AAC 320k); a 720p
    preview from the music master (../ch3's preview encode). The per-shot intermediates are deleted once
    master_video.mp4 exists."""
    import shutil
    spec3 = importlib.util.spec_from_file_location('ch3master', os.path.join(HERE, '..', 'ch3', 'render.py'))
    C3 = importlib.util.module_from_spec(spec3); spec3.loader.exec_module(C3)
    edl = json.load(open(os.path.join(HERE, f'edl_{name}.json')))
    d = f'{WORK}/master_shots_{name}'
    v = f'{WORK}/master_video.mp4'
    if not os.path.exists(v + '.ok'):
        parts = render_shots(edl, 3840, 2160, d)
        C3.assemble(parts, [], v, 18, 'fast')
        open(v + '.ok', 'w').write('ok')
    shutil.rmtree(d, ignore_errors=True)
    a, b = f'{WORK}/opening_{name}_master.mp4', f'{WORK}/opening_{name}_master_NOMUSIC.mp4'
    C3.mux(v, f'{WORK}/mix_{name}.wav', a)
    C3.mux(v, f'{WORK}/nomusic_{name}.wav', b)
    pv = f'{WORK}/opening_{name}_master_preview_720p.mp4'
    R.sh([C3.FF, '-v', 'error', '-y', '-i', a, '-vf', 'scale=1280:720:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow',
          '-b:v', '1150k', '-maxrate', '1500k', '-bufsize', '3000k', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', pv])
    for p in (v, a, b, pv):
        print(p, os.path.getsize(p), flush=True)


if __name__ == '__main__':
    {'gate': gate, 'preview': preview, 'timeline': timeline, 'master': master}[sys.argv[1]](sys.argv[2])
