#!/usr/bin/env python3
"""build2.py -- the vlog kit's SET 2 (G3, B4, C4, C5, I4, I5, I6): prep, layer capture, compositing, reel, mockups, QA.

  python3 build2.py                  everything (prep, layer, reel, mocks, qa)
  python3 build2.py --stage prep     plates (mezzanine, 59.94 fps frames, 4K stills, inpainted backgrounds), contours,
                                     .work2/scene.js + tracks.js + kitdata.js for kit2.html
  python3 build2.py --stage layer    capture kit2.html for every reel frame, all passes (3 Chromium processes)
  python3 build2.py --stage reel     composite + audio -> exports/vlog-kit-set2-reel.mp4
  python3 build2.py --stage mocks    mockups/set2/*.jpg + mockups/set2/BOARD.jpg
  python3 build2.py --stage qa       safe-zone audit on every pass, probe, check stills -> exports/qa-set2/
  python3 build2.py --stills 1.5,6.2 composite single reel times -> .work2/stills/
  python3 build2.py --stage mattes   (macOS) re-cut the Vision mattes into lib/data/mattes2/ (lib/matte.swift)
  python3 build2.py --stage plane    (macOS or anywhere with the 59.94 frames) re-run the C5 planar track -> lib/data/plane.json

Set 1 (build.py, kit.html, the 22 variations) is untouched: set 2 has its own page, work folder and outputs, and only
reads set 1's code (sekit.js, compose.py, fx.py, accum.py) and its tracks (lib/data/tracks.json).
Machine paths: FFMPEG, ROOFTOP_RAW (DJI_0029 4K source), PW_MODULE / PW_EXEC (playwright + a Chromium binary).
"""
import argparse, json, math, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '.work2')
WORK1 = os.path.join(HERE, '.work')
LIB = os.path.join(HERE, 'lib')
sys.path.insert(0, LIB)
FPS = 30000 / 1001
CFG1 = json.load(open(os.path.join(HERE, 'config.json')))
CFG = json.load(open(os.path.join(HERE, 'config2.json')))
FF = os.environ.get('FFMPEG', CFG1['tools']['ffmpeg'])
RAW = os.environ.get('ROOFTOP_RAW', CFG1['tools']['rooftopRaw'])
NODE = shutil.which('node') or '/opt/node22/bin/node'
PY = sys.executable
rt = lambda r: r / FPS
NAMES = {'B4': 'NAME BEHIND', 'C4': 'CAR TRACE', 'C5': 'ORBIT BRACKETS', 'G3': 'DEPTH TITLE',
         'I4': 'LETTER WINDOW', 'I5': 'STRIPE SHUTTER', 'I6': 'FREEZE SWEEP'}


def run(cmd, **kw):
    print('  $', ' '.join(str(c) for c in cmd)[:200], flush=True)
    return subprocess.run(cmd, check=True, **kw)


# ============================================================================ scene
def build_scene():
    R = CFG['reel']
    shots, byid = [], {}

    def spec(p, r0, r1):
        if isinstance(p, str):
            return byid[p]['plate']
        sp = json.loads(json.dumps(p))
        span = sp.pop('span', [r0, r1])
        sp['t0'], sp['t1'] = rt(span[0]), rt(span[1])
        if sp['kind'] == 'clip':
            sp['c0'] = sp.pop('f0') / FPS
            sp['t0'] = rt(r0)
        if sp['kind'] == 'still' and sp['src'].startswith('rooftop:'):
            sp['frame'] = int(sp['src'].split(':')[1])
        return sp

    for s in R['shots']:
        o = {'id': s['id'], 'r0': s['r'][0], 'r1': s['r'][1], 't0': rt(s['r'][0]), 't1': rt(s['r'][1])}
        if 'plate' in s:
            o['plate'] = spec(s['plate'], *s['r'])
        byid[s['id']] = o; shots.append(o)
    for s, o in zip(R['shots'], shots):
        if s.get('fx') in ('switch', 'window'):
            o['fx'] = s['fx']
            o['a'] = spec(s['a'], *s['r']); o['b'] = spec(s['b'], *s['r'])
            if s['fx'] == 'switch':
                o['switchT'] = rt(s['switchAt'])
    end = R['shots'][-1]['r'][1]
    mattes = {k: v for k, v in CFG['mattes'].items() if not k.startswith('_')}
    comps, chip, mocks = scene_components(byid, rt(end))
    return dict(fps=FPS, dur=rt(end), reelEnd=rt(end), reelFrames=end, clipFrames=430, shots=shots, mattes=mattes,
                comps=comps + [chip], plan=motion_plan(byid), mocks=mocks)


def scene_components(S, reel_end):
    """the set-2 reel's choreography: which variation is on screen when (scene seconds)."""
    C = CFG['copy']; T0 = lambda i: S[i]['t0']; T1 = lambda i: S[i]['t1']
    host, car, chL, chD = C['host'], C['car'], C['chapters']['lineup'], C['chapters']['driveBack']
    comps = []
    add = lambda code, typ, t0, t1, **p: comps.append({'code': code, 'type': typ, 't0': round(t0, 4), 't1': round(t1, 4), 'p': p})
    # B4 on the host, I5 into the lineup still, G3 behind the lineup
    add('B4', 'nameBehind', 0, T1('host1'), track='face1', matte='host1', name=host['name'], handle=host['handle'], kicker=host['kicker'],
        acquire=0.2, exit=T1('host1') - 0.48)
    add('I5', 'stripeShutter', T0('shutter'), T1('shutter'))
    add('G3', 'depthTitle', T0('lineup'), T1('lineup'), tag=chL['tag'], pre=chL['pre'], title=chL['title'], y=688, matte='lineup252', maxW=770,
        push=[1.0, 1.055], anchor=[480, 1150], acquire=T0('lineup') + 0.06, exit=T1('lineup') - 0.62)
    # C5 on the slow-motion pass of the Urus, then C4 on the freeze, then the picture moves again
    add('C5', 'orbitLock', T0('urusSlow'), T1('urusSlow'), plane='urusSide', make=car['make'], model=car['model'],
        acquire=T0('urusSlow') + 0.12, exit=T1('urusSlow') - 0.4)
    add('C4', 'carTrace', T0('freeze'), T1('freeze'), contour='urus166', matte='urus166', make=car['make'], model=car['model'],
        trace=[0.16, 1.0], exit=T1('freeze') - 0.46)
    # I6 freezes the chapter's last shot; I4 flies through the next chapter's title into the host
    add('I6', 'freezeSweep', T0('suvFreeze'), T1('suvFreeze'), matte='suv128', tag=chL['end'], title=chL['full'], sweep=[0.12, 0.9],
        exit=T1('suvFreeze') - 0.3)
    add('I4', 'letterWindow', T0('window'), T1('window'), maxW=810, tag=chD['tag'], pre=chD['pre'], lines=chD['lines'], fill=[0.2, 0.26],
        zoom=[0.52, (T1('window') - T0('window')) - 0.52 - 0.02])
    rows = [[k, NAMES[k]] for k in ('B4', 'C4', 'C5', 'G3', 'I4', 'I5', 'I6')]
    add('IDX', 'indexCard', T0('index'), T1('index'), title=C['index']['title'], sub=C['index']['sub'], rows=rows)
    items = [(0, T0('shutter'), 'B4', 'NAME BEHIND'), (T0('shutter'), T1('shutter'), 'I5', 'STRIPE SHUTTER'),
             (T0('lineup'), T0('urusSlow'), 'G3', 'DEPTH TITLE'), (T0('urusSlow'), T0('freeze'), 'C5', 'ORBIT BRACKETS · 0.5X'),
             (T0('freeze'), T0('suv'), 'C4', 'CAR TRACE'), (T0('suv'), T0('window'), 'I6', 'FREEZE SWEEP'),
             (T0('window'), T1('window'), 'I4', 'LETTER WINDOW')]
    chip = {'code': 'CHIP', 'type': 'codeChip', 't0': 0, 't1': reel_end,
            'p': {'items': [{'t0': round(a, 4), 't1': round(b, 4), 'codes': c, 'name': n} for a, b, c, n in items]}}
    M = [('B4', 1.05), ('G3', T0('lineup') + 1.1), ('C5', T0('urusSlow') + 1.0), ('C4', T0('freeze') + 1.72)]
    mocks = [{'name': c, 't': round(t, 4), 'only': [c]} for c, t in M]
    mocks.append({'name': 'I5', 'only': ['I5'], 'band': [640, 1280], 'strip': [
        {'t': round(T0('shutter') + 0.07, 4), 'label': 'THE STRIPE DRAWS'}, {'t': round(T0('shutter') + 0.28, 4), 'label': 'OPEN · THE SHOT SWITCHES'},
        {'t': round(T0('shutter') + 0.495, 4), 'label': 'CLOSING ONTO THE NEXT SHOT'}]})
    mocks.append({'name': 'I6', 'only': ['I6'], 'band': [800, 1440], 'strip': [
        {'t': round(T0('suvFreeze') - 0.12, 4), 'label': 'THE LAST SHOT PLAYS'}, {'t': round(T0('suvFreeze') + 0.5, 4), 'label': 'FREEZE · THE LIGHT SWEEPS THE CAR'},
        {'t': round(T0('suvFreeze') + 1.18, 4), 'label': 'END OF CHAPTER · TAPE STOP'}]})
    mocks.append({'name': 'I4', 'only': ['I4'], 'band': [580, 1220], 'strip': [
        {'t': round(T0('window') + 0.18, 4), 'label': 'THE TITLE RISES'}, {'t': round(T0('window') + 0.5, 4), 'label': 'THE NEXT SHOT INSIDE THE LETTERS'},
        {'t': round(T0('window') + 0.98, 4), 'label': 'FLYING THROUGH THE B'}]})
    return comps, chip, mocks


def motion_plan(S):
    T0 = lambda i: S[i]['t0']; T1 = lambda i: S[i]['t1']
    sp = []
    A = lambda a, b, k, sh=200: sp.append({'a': round(a, 4), 'b': round(b, 4), 'k': k, 'shutter': sh})
    A(0.18, 0.95, 10, 220)                                 # B4 letters rise
    A(T1('host1') - 0.5, T1('host1'), 10, 220)             # B4 sink
    A(T0('shutter') - 0.01, T1('shutter') + 0.01, 14, 270) # I5
    A(T0('lineup'), T0('lineup') + 0.9, 10, 220)           # G3 rise
    A(T1('lineup') - 0.66, T1('lineup'), 10, 220)          # G3 sink
    A(T0('urusSlow'), T0('urusSlow') + 0.6, 12, 220)       # C5 acquire + bend
    A(T0('urusSlow') + 0.6, T1('urusSlow') - 0.42, 3)      # C5 riding the car
    A(T1('urusSlow') - 0.42, T1('urusSlow'), 12, 220)      # C5 release
    A(T0('freeze'), T0('freeze') + 1.9, 6)                 # C4 trace, tip, pulse
    A(T1('freeze') - 0.5, T1('freeze'), 10)                # C4 release
    A(T0('suvFreeze'), T0('suvFreeze') + 1.0, 8)           # I6 bars, marker
    A(T1('suvFreeze') - 0.45, T1('suvFreeze'), 8)
    A(T0('window'), T0('window') + 0.5, 10, 220)           # I4 rise + drain
    A(T0('window') + 0.5, T1('window'), 16, 270)           # I4 fly-through
    A(T0('index'), T0('index') + 0.8, 8)
    return {'k': 1, 'shutter': 180, 'spans': sp}


# ============================================================================ prep
def stage_prep():
    import numpy as np
    from PIL import Image
    os.makedirs(os.path.join(WORK, 'plates'), exist_ok=True)
    # mezzanine frames: shared with set 1 (.work/plates/rooftop); made here if set 1 has not been built on this machine
    mezz = os.path.join(WORK1, 'src', 'rooftop_mezz.mov')
    if not os.path.exists(mezz):
        os.makedirs(os.path.dirname(mezz), exist_ok=True)
        run([FF, '-v', 'error', '-y', '-i', RAW, '-map', '0:v:0', '-map', '0:a:0', '-vf',
             "select='not(mod(n\\,2))',setpts=N/(30000/1001)/TB,scale=1080:1920:flags=lanczos,format=yuv420p", '-r', '30000/1001',
             '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-tune', 'film', '-c:a', 'pcm_s16le', mezz])
    p1 = os.path.join(WORK1, 'plates', 'rooftop')
    if not os.path.exists(os.path.join(p1, '0429.jpg')):
        os.makedirs(p1, exist_ok=True)
        run([FF, '-v', 'error', '-y', '-i', mezz, '-q:v', '1', '-qmin', '1', '-start_number', '0', os.path.join(p1, '%04d.jpg')])
    link = os.path.join(WORK, 'plates', 'rooftop')
    if not os.path.exists(link):
        os.symlink(os.path.relpath(p1, os.path.dirname(link)), link)
    # 59.94 fps frames for the slow-motion plates (1080x1920, same scaling as the mezzanine)
    h = CFG['hfr']; d60 = os.path.join(WORK, 'plates', 'rooftop60')
    if not os.path.exists(os.path.join(d60, f"{h['to']:04d}.jpg")):
        os.makedirs(d60, exist_ok=True)
        run([FF, '-v', 'error', '-y', '-i', RAW, '-vf', f"select='between(n\\,{h['from']}\\,{h['to']})',scale=1080:1920:flags=lanczos",
             '-vsync', '0', '-q:v', '1', '-qmin', '1', '-start_number', str(h['from']), os.path.join(d60, '%04d.jpg')])
    scene = build_scene()
    # 4K stills (rooftop:N = frame 2N of the 59.94 fps source) and, for 2.5D plates, the background with the subject removed
    stills = {}
    def walk(sp):
        if isinstance(sp, dict):
            if sp.get('kind') == 'still':
                stills[sp['src']] = sp
            for k in ('a', 'b', 'plate'):
                walk(sp.get(k))
    for s in scene['shots']:
        walk(s)
    for src, sp in sorted(stills.items()):
        out = os.path.join(WORK, 'plates', 'still_' + src.replace(':', '_') + '.png')
        if not os.path.exists(out):
            run([FF, '-v', 'error', '-y', '-i', RAW, '-vf', f"select='eq(n\\,{2 * int(src.split(':')[1])})',format=rgb24", '-vsync', '0', '-frames:v', '1', out])
        if sp.get('fg'):
            bg = out[:-4] + '_bg.png'
            if not os.path.exists(bg):
                inpaint(out, os.path.join(HERE, scene['mattes'][sp['fg']['matte']]['file']), bg)
    clean_mattes(scene)
    json.dump(scene, open(os.path.join(WORK, 'scene.json'), 'w'))
    open(os.path.join(WORK, 'scene.js'), 'w').write('window.SCENE = ' + json.dumps(scene) + ';\n')
    open(os.path.join(WORK, 'tracks.js'), 'w').write('window.TRACKS = ' + open(os.path.join(LIB, 'data', 'tracks.json')).read() + ';\n' +
                                                      'window.PLANES = ' + open(os.path.join(LIB, 'data', 'plane.json')).read() + ';\n')
    import base64
    logos = {f: 'data:image/png;base64,' + base64.b64encode(open(os.path.join(HERE, '..', '..', '02-logos', 'png', f), 'rb').read()).decode()
             for f in ('sce-primary-horizontal--white.png', 'sce-icon-mark-only--white.png')}
    kd = {'logos': logos, 'contours': contours(scene)}
    open(os.path.join(WORK, 'kitdata.js'), 'w').write('window.KITDATA = ' + json.dumps(kd) + ';\n')
    print(f"scene: {len(scene['shots'])} shots, {len(scene['comps'])} components, reel {scene['reelEnd']:.2f} s ({scene['reelFrames']} frames), stills {sorted(stills)}")
    return scene


def clean_mattes(scene):
    """apply each matte's hand exclusions (config2.json mattes.<name>.exclude, polygons in source 1080x1920 units) into
    .work2/mattes/<name>.png and point the scene at the cleaned file."""
    import cv2, numpy as np
    d = os.path.join(WORK, 'mattes'); os.makedirs(d, exist_ok=True)
    for name, m in scene['mattes'].items():
        if m['kind'] != 'still' or not m.get('exclude'):
            continue
        im = cv2.imread(os.path.join(HERE, m['file']), cv2.IMREAD_GRAYSCALE); sc = im.shape[1] / 1080
        cut = np.zeros_like(im)
        for poly in m['exclude']:
            cv2.fillPoly(cut, [np.round(np.array(poly, np.float32) * sc).astype(np.int32)], 255)
        cut = cv2.GaussianBlur(cut, (0, 0), 2 * sc)
        out = os.path.join(d, name + '.png')
        cv2.imwrite(out, (im.astype(np.float32) * (1 - cut / 255.0)).astype(np.uint8))
        m['file'] = os.path.relpath(out, HERE)


def inpaint(still, matte, out):
    """the still with its subject removed (OpenCV Telea on a dilated matte, at half size, pasted back into the still),
    so a 2.5D push can move the subject off the background without exposing a hole."""
    import cv2, numpy as np
    im = cv2.imread(still); m = cv2.imread(matte, cv2.IMREAD_GRAYSCALE)
    m = cv2.dilate((m > 60).astype(np.uint8) * 255, np.ones((41, 41), np.uint8))
    sm, mm = cv2.resize(im, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), cv2.resize(m, None, fx=0.5, fy=0.5)
    fill = cv2.resize(cv2.inpaint(sm, mm, 12, cv2.INPAINT_TELEA), (im.shape[1], im.shape[0]), interpolation=cv2.INTER_CUBIC)
    a = cv2.GaussianBlur(m, (0, 0), 6).astype(np.float32)[..., None] / 255
    cv2.imwrite(out, (im * (1 - a) + fill * a).astype(np.uint8))
    print('  inpainted', os.path.basename(out))


def contours(scene):
    """car outlines for C4, from the still mattes: the largest outer contour, in source (1080x1920) units, starting at
    the front of the car and running over the roof first; plus a dilated outer line and the extreme points."""
    import cv2, numpy as np
    out = {}
    for name, c in CFG['contours'].items():
        m = cv2.imread(os.path.join(HERE, scene['mattes'][c['matte']]['file']), cv2.IMREAD_GRAYSCALE)
        sc = 1080 / m.shape[1]
        m = cv2.GaussianBlur(m, (0, 0), 2)
        b = cv2.morphologyEx((m > 127).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        def outline(bw):
            cs, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cc = max(cs, key=cv2.contourArea)
            cc = cv2.approxPolyDP(cc, 2.4, True)[:, 0, :].astype(np.float32) * sc
            i0 = int(np.argmin(cc[:, 0] - 0.15 * cc[:, 1]))           # the front of the car (leftmost, low)
            cc = np.roll(cc, -i0, axis=0)
            if cc[min(len(cc) - 1, 6), 1] > cc[0, 1]:                  # run over the top first (y decreasing)
                cc = np.concatenate([cc[:1], cc[1:][::-1]])
            return np.concatenate([cc, cc[:1]])
        pts = outline(b)
        dil = int(round(c.get('dilate', 18) / sc))
        opts = outline(cv2.dilate(b, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dil + 1, 2 * dil + 1))))
        ext = {'left': pts[np.argmin(pts[:, 0])].tolist(), 'right': pts[np.argmax(pts[:, 0])].tolist(), 'top': pts[np.argmin(pts[:, 1])].tolist()}
        out[name] = {'pts': np.round(pts, 1).tolist(), 'outer': np.round(opts, 1).tolist(), 'ext': ext}
        print(f"  contour {name}: {len(pts)} points, outer {len(opts)}")
    return out


# ============================================================================ mattes + plane (source tools)
def stage_mattes():
    """re-cut every matte with Apple Vision (macOS only): lib/matte.swift is compiled into .work2/matte."""
    if sys.platform != 'darwin':
        raise SystemExit('mattes need macOS (Apple Vision); the committed lib/data/mattes2/ are used elsewhere')
    exe = os.path.join(WORK, 'matte')
    if not os.path.exists(exe):
        run(['swiftc', '-O', os.path.join(LIB, 'matte.swift'), '-o', exe])
    import numpy as np
    from PIL import Image
    tmp = os.path.join(WORK, 'matte_tmp'); os.makedirs(tmp, exist_ok=True)
    for name, m in CFG['mattes'].items():
        if name.startswith('_'):
            continue
        if m['kind'] == 'still':
            n = int(m['src'].split(':')[1])
            src = os.path.join(WORK, 'plates', f'still_rooftop_{n}.png')
            if not os.path.exists(src):
                run([FF, '-v', 'error', '-y', '-i', RAW, '-vf', f"select='eq(n\\,{2 * n})',format=rgb24", '-vsync', '0', '-frames:v', '1', src])
            run([exe, m['mode'], tmp, src])
            js = json.load(open(os.path.join(tmp, f'still_rooftop_{n}.json')))
            # the largest instance is the subject (every instance is kept for the lineup, which is several cars and a guest)
            ims = [np.asarray(Image.open(os.path.join(tmp, i['file']))) for i in js['instances']]
            out = np.maximum.reduce(ims) if name.startswith('lineup') else max(ims, key=lambda a: (a > 127).sum())
            Image.fromarray(out).save(os.path.join(HERE, m['file']))
        else:
            d = os.path.join(HERE, m['dir']); os.makedirs(d, exist_ok=True)
            frames = [os.path.join(WORK, 'plates', 'rooftop', f'{f:04d}.jpg') for f in range(0, 73)]
            run([exe, 'person', tmp] + frames)
            for f in range(0, 73):
                shutil.move(os.path.join(tmp, f'{f:04d}_person.png'), os.path.join(d, f'{f:04d}.png'))
        print('  matte', name)


def stage_plane():
    """C5: the planar track of the Urus's side panel on the 59.94 fps frames (lib/plane_track.py)."""
    exe = os.path.join(WORK, 'matte'); tmp = os.path.join(WORK, 'matte60'); os.makedirs(tmp, exist_ok=True)
    frames = [os.path.join(WORK, 'plates', 'rooftop60', f'{f:04d}.jpg') for f in range(280, 335)]
    if sys.platform == 'darwin':
        if not os.path.exists(exe):
            run(['swiftc', '-O', os.path.join(LIB, 'matte.swift'), '-o', exe])
        run([exe, 'fg', tmp] + frames)
    run([PY, os.path.join(LIB, 'plane_track.py'), '--frames', os.path.join(WORK, 'plates', 'rooftop60'), '--mattes', tmp,
         '--f0', '280', '--f1', '334', '--anchor', '308', '--quad', '455,1062,690,1035,690,1190,455,1232',
         '--region', '430,1030,720,1000,720,1210,430,1260', '--out', os.path.join(LIB, 'data', 'plane.json'), '--name', 'urusSide',
         '--qa', os.path.join(WORK, 'plane_qa.jpg')])


# ============================================================================ layer capture
def stage_layer(scene, frames=None, out=None, workers=3):
    out = out or os.path.join(WORK, 'layer')
    os.makedirs(out, exist_ok=True)
    frames = list(range(scene['reelFrames'])) if frames is None else frames
    todo = [f for f in frames if not os.path.exists(os.path.join(out, f'{f:05d}.png'))]
    print(f'layer: {len(todo)} of {len(frames)} frames to capture')
    if not todo:
        return
    procs = []
    for i in range(workers):
        ch = todo[i::workers]
        if not ch:
            continue
        lst = os.path.join(WORK, f'frames_{i}.json'); json.dump(ch, open(lst, 'w'))
        procs.append(subprocess.Popen([NODE, os.path.join(LIB, 'kcapture2.js'), os.path.join(HERE, 'kit2.html'), out, 'list', '30000/1001', lst],
                                      stderr=open(os.path.join(WORK, f'capture_{i}.log'), 'w')))
    for p in procs:
        if p.wait() != 0:
            raise SystemExit('capture failed, see .work2/capture_*.log')


# ============================================================================ audio
def stage_audio(scene):
    import numpy as np, wave
    mezz = os.path.join(WORK1, 'src', 'rooftop_mezz.mov')
    raw = subprocess.run([FF, '-v', 'error', '-i', mezz, '-ac', '2', '-ar', '48000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    src = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
    SR = 48000; A = CFG['reel']['audio']
    n = int(round(scene['reelEnd'] * SR)); out = np.zeros((n, 2), np.float32)
    g = 10 ** (A['gainDb'] / 20); fade = int(A['fadeMs'] / 1000 * SR)
    def seg(c0, a, b, env=None):
        L = b - a; x = src[c0:c0 + L].copy(); L = len(x)
        e = np.ones(L, np.float32) if env is None else env[:L]
        f = min(fade, L // 2); e[:f] *= np.linspace(0, 1, f); e[L - f:] *= np.linspace(1, 0, f)
        out[a:a + L] += x * e[:, None] * g
    for s in scene['shots']:
        a, b = int(round(s['t0'] * SR)), int(round(s['t1'] * SR))
        sp = s.get('plate')
        if sp and sp['kind'] == 'clip' and sp.get('speed', 1) == 1:
            seg(int(round(sp['c0'] * SR)), a, b)
        if s.get('fx') == 'switch' and s['a'].get('kind') == 'clip':          # I5: the outgoing clip fades under the shutter
            seg(int(round(s['a']['c0'] * SR)), a, b, np.linspace(1, 0, b - a, dtype=np.float32) ** 1.5)
        if s.get('fx') == 'window' and s['b'].get('kind') == 'clip':          # I4: the next shot's sound comes up with the window
            seg(int(round(s['b']['c0'] * SR)), a, b, np.linspace(0, 1, b - a, dtype=np.float32) ** 0.7)
    # I6 tape stop: the SUV shot's own sound runs on from the freeze, slowing to a stop (pitch falls with it)
    fz = next(s for s in scene['shots'] if s['id'] == 'suvFreeze'); pv = next(s for s in scene['shots'] if s['id'] == 'suv')
    a = int(round(fz['t0'] * SR)); T = A['tapeStop']; L = int(T * SR)
    tau = np.arange(L) / SR; rate = (1 - tau / T) ** 1.6
    pos = pv['plate']['c0'] * SR + (fz['t0'] - pv['t0']) * SR + np.cumsum(rate)
    i0 = np.floor(pos).astype(int); fr = (pos - i0)[:, None]
    ts = src[i0] * (1 - fr) + src[i0 + 1] * fr
    ts *= (np.linspace(1, 0, L) ** 0.5)[:, None]
    out[a:a + L] += ts * g
    pk = np.abs(out).max()
    if pk > 0.7:
        out *= 0.7 / pk
    out[-int(0.05 * SR):] = 0
    p = os.path.join(WORK, 'reel_audio.wav')
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    return p


# ============================================================================ reel
def stage_reel(scene):
    from compose2 import Composer2
    C = Composer2(scene, WORK); N = scene['reelFrames']
    vid = os.path.join(WORK, 'reel_video.mov')
    p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30000/1001', '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', vid], stdin=subprocess.PIPE)
    t = time.time(); lay = os.path.join(WORK, 'layer')
    for i in range(N):
        p.stdin.write(C.frame(i, os.path.join(lay, f'{i:05d}.png'), os.path.join(lay, f'fx_{i:05d}.json')).tobytes())
        if i % 60 == 0:
            print(f'  compose {i}/{N} {time.time() - t:.0f}s', flush=True)
    p.stdin.close(); p.wait()
    aud = stage_audio(scene)
    os.makedirs(os.path.join(HERE, 'exports'), exist_ok=True)
    master = os.path.join(HERE, 'exports', 'vlog-kit-set2-reel.mp4')
    run([FF, '-v', 'error', '-y', '-i', vid, '-i', aud, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
         '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-profile:v', 'high',
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', master])
    print('master', master, f'{os.path.getsize(master) / 2**20:.1f} MiB')
    return master


# ============================================================================ mockups + board
def stage_mocks(scene, only=None):
    from compose2 import Composer2
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    mocks = [m for m in scene['mocks'] if not only or m['name'] in only]
    lay = os.path.join(WORK, 'mocklayer'); os.makedirs(lay, exist_ok=True)
    caps = []
    for m in mocks:
        caps += [{'name': f"{m['name']}_{k}", 't': s['t'], 'only': m['only']} for k, s in enumerate(m['strip'])] if 'strip' in m else [m]
    lst = os.path.join(WORK, 'mocks.json'); json.dump(caps, open(lst, 'w'))
    run([NODE, os.path.join(LIB, 'kcapture2.js'), os.path.join(HERE, 'kit2.html'), lay, 'mocks', lst])
    C = Composer2(scene, WORK)
    outd = os.path.join(HERE, 'mockups', 'set2'); os.makedirs(outd, exist_ok=True)
    fm = os.path.join(HERE, '..', '..', '07-fonts', 'Michroma-Regular.ttf')
    for m in mocks:
        if 'strip' in m:
            y0, y1 = m['band']; bh = y1 - y0
            img = Image.new('RGB', (1080, 1920), (0, 0, 0)); d = ImageDraw.Draw(img)
            for k, st in enumerate(m['strip']):
                fr = C.frame(int(round(st['t'] * FPS)), os.path.join(lay, f"{m['name']}_{k}.png"), os.path.join(lay, f"fx_{m['name']}_{k}.json"))
                img.paste(Image.fromarray(fr[y0:y1]), (0, k * bh)); yy = k * bh
                d.rectangle([0, yy, 1080, yy + 4], fill=(251, 209, 1)); d.rectangle([842, yy, 1080, yy + 4], fill=(255, 255, 255))
                tx = f"{k + 1}  ·  {st['label']}"
                d.rectangle([24, yy + 22, 24 + 22 + int(len(tx) * 15.5), yy + 64], fill=(0, 0, 0))
                d.text((36, yy + 32), tx, font=ImageFont.truetype(fm, 20), fill=(251, 209, 1))
            img = np.asarray(img)
        else:
            img = C.frame(int(round(m['t'] * FPS)), os.path.join(lay, m['name'] + '.png'), os.path.join(lay, f"fx_{m['name']}.json"))
        name = f"{m['name']}_{NAMES[m['name']].lower().replace(' ', '-')}.jpg"
        for old in [f for f in os.listdir(outd) if f.startswith(m['name'] + '_')]:
            os.remove(os.path.join(outd, old))
        Image.fromarray(img).save(os.path.join(outd, name), quality=92)
        print('  mock', name)
    board()


def board():
    from PIL import Image, ImageDraw, ImageFont
    outd = os.path.join(HERE, 'mockups', 'set2')
    order = ['G3', 'B4', 'C4', 'C5', 'I4', 'I5', 'I6']
    files = [f for c in order for f in sorted(os.listdir(outd)) if f.startswith(c + '_')]
    fb = os.path.join(HERE, '..', '..', '07-fonts', 'BebasNeue-Regular.ttf'); fm = os.path.join(HERE, '..', '..', '07-fonts', 'Michroma-Regular.ttf')
    cols, tw, th, head, lab, gap = 7, 320, 569, 190, 70, 18
    Wb = cols * tw + (cols + 1) * gap; Hb = head + th + lab + 2 * gap + 40
    B = Image.new('RGB', (Wb, Hb), (8, 8, 9)); d = ImageDraw.Draw(B)
    F = lambda f, s: ImageFont.truetype(f, s)
    d.rectangle([gap, 40, gap + 300, 48], fill=(251, 209, 1)); d.rectangle([gap + 234, 40, gap + 300, 48], fill=(255, 255, 255))
    d.text((gap, 60), 'SE VLOG KIT  ·  SET 2  ·  LOCKED-ON', font=F(fb, 84), fill=(255, 255, 255))
    d.text((gap + 2, 150), 'SEVEN MORE VARIATIONS OVER REAL FOOTAGE: RED ROCK CASINO GARAGE (DJI_0029, 22:49, SEP 15 2026).  SAY THE CODES.', font=F(fm, 15), fill=(251, 209, 1))
    for i, f in enumerate(files):
        x = gap + i * (tw + gap); y = head
        B.paste(Image.open(os.path.join(outd, f)).resize((tw, th), Image.LANCZOS), (x, y + lab))
        d.rectangle([x, y, x + tw, y + lab - 6], fill=(0, 0, 0))
        d.rectangle([x, y, x + int(tw * .78), y + 4], fill=(251, 209, 1)); d.rectangle([x + int(tw * .78), y, x + tw, y + 4], fill=(255, 255, 255))
        d.text((x + 12, y + 12), f[:2], font=F(fb, 50), fill=(251, 209, 1))
        d.text((x + 70, y + 30), NAMES[f[:2]], font=F(fm, 13), fill=(255, 255, 255))
    B.save(os.path.join(outd, 'BOARD.jpg'), quality=90)
    print('board', os.path.join(outd, 'BOARD.jpg'), B.size)


# ============================================================================ QA
def stage_qa(scene):
    import qa
    s = {'audit': qa.audit(scene, HERE, WORK, page='kit2.html', loose=('letterWindow',))}
    master = os.path.join(HERE, 'exports', 'vlog-kit-set2-reel.mp4')
    s['master'] = qa.probe(FF, master)
    qd = os.path.join(HERE, 'exports', 'qa-set2')
    if s['master']:
        s['check_stills'] = qa.stills(scene, HERE, FF, src=master, qd=qd)
    os.makedirs(qd, exist_ok=True)
    json.dump(s, open(os.path.join(qd, 'qa_summary.json'), 'w'), indent=1)
    a = s['audit']
    print(f"qa: {a['frames_checked']} times audited, {a['n_outside_safe']} text boxes outside the safe area "
          f"(+{a['n_transitional']} while a component slides, scales or flies through)")
    for b in a['outside_safe'][:12]:
        print('   ', b)
    print('qa:', json.dumps(s['master'], indent=1))


def stage_stills(scene, times):
    from compose2 import Composer2
    from PIL import Image
    out = os.path.join(WORK, 'stills'); os.makedirs(out, exist_ok=True)
    frames = sorted(set(int(round(t * FPS)) for t in times))
    stage_layer(scene, frames, os.path.join(WORK, 'layer'), workers=min(3, len(frames)))
    C = Composer2(scene, WORK)
    for f in frames:
        img = C.frame(f, os.path.join(WORK, 'layer', f'{f:05d}.png'), os.path.join(WORK, 'layer', f'fx_{f:05d}.json'))
        Image.fromarray(img).save(os.path.join(out, f'r{f:05d}_{f / FPS:06.2f}s.jpg'), quality=90)
        print('  still', f, f'{f / FPS:.2f}s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all'); ap.add_argument('--stills'); ap.add_argument('--mocks')
    a = ap.parse_args()
    if a.stage == 'mattes':
        stage_mattes(); return
    if a.stage == 'plane':
        stage_plane(); return
    scene = stage_prep()
    if a.stills:
        stage_stills(scene, [float(v) for v in a.stills.split(',')]); return
    st = a.stage
    if st in ('all', 'layer', 'reel'):
        stage_layer(scene)
    if st in ('all', 'reel'):
        stage_reel(scene)
    if st in ('all', 'mocks'):
        stage_mocks(scene, a.mocks.split(',') if a.mocks else None)
    if st == 'board':
        board()
    if st in ('all', 'qa'):
        stage_qa(scene)


if __name__ == '__main__':
    main()
