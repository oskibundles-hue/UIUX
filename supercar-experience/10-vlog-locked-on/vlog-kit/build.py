#!/usr/bin/env python3
"""build.py -- the SE vlog Locked-On kit: prep, layer capture, compositing, reel export, mockups, board, QA.

  python3 build.py                  everything (prep, layer, audio, reel, deliver, mocks, qa)
  python3 build.py --stage prep     footage plates, 4K stills, tracks/scene/data JS for kit.html
  python3 build.py --stage layer    capture kit.html for every reel frame (3 Chromium processes)
  python3 build.py --stage reel     composite + audio -> exports/vlog-kit-reel.mp4 (master, CRF)
  python3 build.py --stage deliver  two-pass copy under 30 MiB -> exports/vlog-kit-reel_DELIVERY.mp4 (if needed)
  python3 build.py --stage mocks    mockups/*.jpg + mockups/BOARD.jpg
  python3 build.py --stage qa       exports/qa/ (check stills per component, safe-zone audit)
  python3 build.py --stills 1.2,5.9 composite single reel times -> .work/stills/

The scene (what is on screen when) is built here from config.json: shots come from config.json reel.shots,
the component schedule is SCENE_COMPONENTS below (codes A1..I3). kit.html reads it as .work/scene.js.
"""
import argparse, json, math, os, shutil, subprocess, sys, time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, '.work')
LIB = os.path.join(HERE, 'lib')
sys.path.insert(0, LIB)
FPS = 30000 / 1001
CFG = json.load(open(os.path.join(HERE, 'config.json')))
FF = os.environ.get('FFMPEG', CFG['tools']['ffmpeg'])
NODE = shutil.which('node') or '/opt/node22/bin/node'
rt = lambda r: r / FPS


def run(cmd, **kw):
    print('  $', ' '.join(str(c) for c in cmd)[:200], flush=True)
    return subprocess.run(cmd, check=True, **kw)


# ============================================================================ scene
def build_scene():
    R = CFG['reel']
    shots, byid = [], {}

    def spec(p, r0, r1):
        """plate spec in scene seconds (t0/t1 = its Ken Burns span)."""
        if isinstance(p, str):
            return byid[p]['plate']
        sp = dict(p)
        span = sp.pop('span', [r0, r1])
        sp['t0'], sp['t1'] = rt(span[0]), rt(span[1])
        if sp['kind'] == 'clip':
            sp['c0'] = sp.pop('f0') / FPS
            sp['t0'] = rt(r0)
        if sp['kind'] == 'still':
            src = sp['src']
            if src.startswith('rooftop:'):
                sp['frame'] = int(src.split(':')[1])
        if sp['kind'] == 'split':
            sp['top'] = spec(sp['top'], r0, r1); sp['bottom'] = spec(sp['bottom'], r0, r1)
        return sp

    allshots = R['shots'] + []
    r_end = R['shots'][-1]['r'][1]
    r = r_end
    for a in CFG['appendix']['shots']:
        allshots.append(dict(a, r=[r, r + a['len']])); r += a['len']
    # first pass: plain plates (so fx shots can reference them by id)
    for s in allshots:
        o = {'id': s['id'], 'r0': s['r'][0], 'r1': s['r'][1], 't0': rt(s['r'][0]), 't1': rt(s['r'][1])}
        if 'plate' in s:
            o['plate'] = spec(s['plate'], *s['r'])
        byid[s['id']] = o; shots.append(o)
    for s, o in zip(allshots, shots):
        if s.get('fx') == 'whip':
            o.update(fx='whip', dir=s.get('dir', 'left'), aTail=s['aTail'], bHead=s['bHead'],
                     a={'kind': 'clip', 'c0': s['aTail'][0] / FPS, 't0': o['t0']},
                     b={'kind': 'clip', 'c0': s['bHead'][0] / FPS, 't0': rt(o['r0'] + len(s['aTail']))})
        elif s.get('fx') in ('sweep', 'switch'):
            o['fx'] = s['fx']
            o['a'] = spec(s['a'], *s['r']) if not isinstance(s['a'], str) else byid[s['a']]['plate']
            o['b'] = spec(s['b'], *s['r']) if not isinstance(s['b'], str) else byid[s['b']]['plate']
            if s['fx'] == 'switch':
                o['switchT'] = rt(s['switchAt'])
    reel_end = rt(r_end)
    comps, chip, mocks = scene_components(byid, reel_end)
    plan = motion_plan(byid)
    dur = shots[-1]['t1']
    return dict(fps=FPS, dur=dur, reelEnd=reel_end, reelFrames=r_end, clipFrames=430, shots=shots,
                comps=comps + [chip], plan=plan, mocks=mocks)


def words_for(seg_idx, clip_to_reel, t_max=None):
    tr = json.load(open(os.path.join(LIB, 'data', 'transcript_0029.json')))
    out = []
    for i in seg_idx:
        for a, b, w in tr['segments'][i]['words']:
            ra, rb = clip_to_reel(a), clip_to_reel(b)
            if t_max is not None and ra >= t_max:
                continue
            out.append([round(ra, 4), round(rb, 4), w])
    return out


def scene_components(S, reel_end):
    """The reel's choreography: which variation (code) is on screen when. Times are scene seconds."""
    C = CFG['copy']
    T0 = lambda i: S[i]['t0']; T1 = lambda i: S[i]['t1']
    host, ch = C['host'], C['chapters']
    comps = []
    add = lambda code, typ, t0, t1, **p: comps.append({'code': code, 'type': typ, 't0': round(t0, 4), 't1': round(t1, 4), 'p': p})
    whip = {'t0': T0('whip1'), 't1': T1('whip1'), 'dir': 'left', 'dist': 0.9}
    # --- opener on the host (clip 0-2.1 s): A1 bug, D1 clock, B1 name lock, H1 captions
    add('A1', 'bannerBug', 0, T0('lineup'), label=C['banner']['status'], built=True)
    add('D1', 'clockStamp', 0, T0('whip1'), start=C['clock']['start'], place=C['clock']['place'], date=C['clock']['date'], built=True)
    add('B1', 'personLock', 0, (T0('whip1') + T1('whip1')) / 2, track='face1', name=host['name'], handle=host['handle'],
        acquire=0.25, exit=99, whip=whip, maxBottom=1282)
    add('H1', 'captionsBox', 0, T0('whip1'), words=words_for([0], lambda c: c, T0('whip1')), maxLines=1, yBottom=1370)
    # --- the lineup: G1 slam, C1 hop, I2 relock across the cut, B3 guest, C2 scan
    add('G1', 'chapterSlam', T0('convoy') + 0.13, T0('convoy') + 1.62, tag=ch['lineup']['tag'], title=ch['lineup']['title'], y=700)
    cars = C['cars']
    add('C1', 'convoyHop', 4.10, 6.72, total=3, exit=6.40, segs=[
        {'track': 'urusG', 't': 4.10, 'make': cars['urusGrey']['make'], 'placeholder': cars['urusGrey']['placeholder'], 'mode': 'acquire'},
        {'track': 'conv', 't': 4.95, 'make': cars['convertible']['make'], 'placeholder': cars['convertible']['placeholder'], 'mode': 'hop'},
        {'track': 'urusR', 't': T0('lineup'), 'make': cars['urusRed']['make'], 'placeholder': cars['urusRed']['placeholder'], 'mode': 'relock', 'lost': 0.40}])
    add('B3', 'guestLock', 6.62, T1('lineup'), track='guest', name=C['guest'], kicker='LOCKED ON', acquire=6.62, exit=T1('lineup') - 0.32)
    add('A2', 'bannerTab', T0('lineup'), T1('sweep1'), name=C['banner']['name'], label=C['banner']['statusLong'], enter='slide',
        progress=[T0('lineup'), T0('sweep1')])
    add('C2', 'convoyScan', T0('far') + 0.03, T1('far'), targets=[{'track': f'far{k}'} for k in range(1, 6)], ts=T0('far') + 0.03,
        sweep=0.62, exit=T1('far') - 0.38, py=640)
    # --- host again: B2 reticle + H2 speaker strip
    c2r = lambda c: T0('host2') + (c - 326 / FPS)
    add('H2', 'captionsStrip', 9.70, T1('sweep1'), words=words_for([3, 4], c2r), speaker=host['name'], y=1200)
    add('B2', 'personReticle', 10.13, T1('host2'), track='face2', name=host['name'], handle=host['handle'], acquire=10.13, exit=T1('host2') - 0.30)
    # --- stills: I1 sweep, G2 glass, E1 compact route + A3 breathing, E2 full route, F1, F2, D2 -> D1
    add('I1', 'sweep', T0('sweep1'), T1('sweep1'))
    add('I1', 'sweep', T0('sweep2'), T1('sweep2'))
    fs0 = T0('routeFull')
    add('A3', 'bannerBreathe', T0('sweep1'), T0('jump'), enter='slide', chapters=[
        {'t': T0('glass') + 0.10, 'tag': ch['driveBack']['tag'], 'title': ch['driveBack']['title'], 'hold': 1.9},
        {'t': fs0 + 3.0, 'tag': ch['level9']['tag'], 'title': ch['level9']['title'], 'hold': 1.9}])
    add('G2', 'chapterGlass', T0('glass') + 0.05, T1('glass'), tag=ch['driveBack']['tag'], title=ch['driveBack']['title'], y=720)
    rs = T0('route1') + 0.02
    add('E1', 'routeCompact', rs, T1('route1'), title=C['route']['title'], waypoints=C['route']['waypoints'],
        steps=[{'t': rs + 0.75, 'k': 1}, {'t': rs + 1.25, 'k': 2}, {'t': rs + 1.75, 'k': 3}], exit=T1('route1') - 0.40)
    add('E2', 'routeFull', fs0, T1('routeFull'), title=C['route']['title'], sub=C['route']['sub'], waypoints=C['route']['waypoints'],
        steps=[{'t': fs0 + 0.95 + 0.5 * k, 'k': k + 1} for k in range(5)], exit=T1('routeFull') - 0.45)
    add('F1', 'quoteCard', T0('quote'), T1('quote'), label=C['guest'], quote=C['quote'], start=T0('quote') + 0.55, wordGap=0.2,
        footer=C['footer'], exit=T1('quote') - 0.40)
    add('F2', 'quoteSplit', T0('split'), T1('split'), q=C['question'], host=host['name'], handle=host['handle'], a=C['answer'],
        label=C['guest'], qt=T0('split') + 0.45, at=T0('split') + 1.75, wordGap=0.22, exit=T1('split') - 0.40)
    add('D2', 'clockJump', T0('jump'), T1('jump'), **{'from': C['clock']['jumpFrom']}, to=C['clock']['start'][:5], place=C['clock']['place'],
        date=C['clock']['date'], handoff={'x': 80, 'y': 1296, 'size': 104})
    add('D1', 'clockStamp', T1('jump') - 0.34, T1('post'), start=C['clock']['start'], place=C['clock']['place'], date=C['clock']['date'],
        built=False, handoff=T1('jump') - 0.12, y=1270)
    cu = cars['cullinan']
    add('C3', 'leadLock', T1('jump') - 0.05, T1('post'), track='cullinan', kicker=cu['kicker'], name=cu['make'], quote=cu['quote'],
        quoteBy=cu['quoteBy'], acquire=T1('jump') + 0.05, exit=T1('post') - 0.36, side='below')
    add('A1', 'bannerBug', T1('jump') - 0.10, T1('post'), label=C['banner']['status'], built=False)
    rows = [['A1', 'CORNER BUG'], ['A2', 'EDGE TAB'], ['A3', 'BREATHING BANNER'], ['B1', 'NAME LOCK'], ['B2', 'RETICLE'],
            ['B3', 'GUEST LOCK'], ['C1', 'CONVOY HOP'], ['C2', 'LINEUP SCAN'], ['D1', 'CLOCK STAMP'], ['D2', 'TIME JUMP'],
            ['E1', 'ROUTE, CORNER'], ['E2', 'ROUTE, FULL FRAME'], ['F1', 'TESTIMONIAL CARD'], ['F2', 'Q&A SPLIT'],
            ['G1', 'CHAPTER SLAM'], ['G2', 'GLASS SLAM'], ['H1', 'BOXED CAPTIONS'], ['H2', 'SPEAKER STRIP'],
            ['I1', 'GOLD LIGHT SWEEP'], ['I2', 'LOCK LOST / RE-ACQUIRE'], ['I3', 'WHIP-PAN HELPER']]
    add('IDX', 'indexCard', T0('index'), T1('index'), title=C['index']['title'], sub=C['index']['sub'], rows=rows)
    # --- appendix (mockup-only shots)
    add('A1', 'bannerBug', T0('mockA1'), T1('mockA1'), label=C['banner']['status'], built=True)
    a0 = T0('mockH1') + 0.1
    add('H1', 'captionsBox', T0('mockH1'), T1('mockH1'), words=words_for([4], lambda c: a0 + (c - 12.32)), maxLines=2, yBottom=1370)
    # --- reel code chip (annotation, top band)
    items = [(0, T0('whip1'), 'A1 · B1 · D1 · H1', 'BUG · NAME LOCK · CLOCK · CAPTIONS'),
             (T0('whip1'), T1('whip1'), 'I3', 'WHIP-PAN HELPER'),
             (T1('whip1'), 4.10, 'G1 · A1', 'CHAPTER SLAM'),
             (4.10, T0('lineup'), 'C1', 'CONVOY HOP'),
             (T0('lineup'), 6.62, 'I2 · C1 · A2', 'LOCK LOST / RE-ACQUIRE · EDGE TAB'),
             (6.62, T0('far'), 'B3 · A2', 'GUEST LOCK'),
             (T0('far'), 9.70, 'C2 · A2', 'LINEUP SCAN'),
             (9.70, T0('sweep1'), 'B2 · H2 · A2', 'RETICLE · SPEAKER STRIP'),
             (T0('sweep1'), T1('sweep1'), 'I1', 'GOLD LIGHT SWEEP'),
             (T0('glass'), T0('route1'), 'G2 · A3', 'GLASS SLAM · BANNER BREATHES'),
             (T0('route1'), T0('sweep2'), 'E1 · A3', 'ROUTE, CORNER'),
             (T0('sweep2'), T1('sweep2'), 'I1', 'GOLD LIGHT SWEEP'),
             (T0('routeFull'), fs0 + 3.0, 'E2 · A3', 'ROUTE, FULL FRAME'),
             (fs0 + 3.0, T0('quote'), 'E2 · A3', 'ROUTE ARRIVES · BANNER BREATHES'),
             (T0('quote'), T0('split'), 'F1 · A3', 'TESTIMONIAL CARD'),
             (T0('split'), T0('jump'), 'F2 · A3', 'Q&A SPLIT'),
             (T0('jump'), T1('jump') - 0.3, 'D2', 'TIME JUMP'),
             (T1('jump') - 0.3, T1('post'), 'D1 · C3 · A1', 'STAMP HAND-OFF · LEAD-CAR LOCK')]
    chip = {'code': 'CHIP', 'type': 'codeChip', 't0': 0, 't1': reel_end,
            'p': {'items': [{'t0': round(a, 4), 't1': round(b, 4), 'codes': c, 'name': n} for a, b, c, n in items]}}
    # --- mockups: one still per code (a reel frame, or an appendix shot), only that code rendered
    M = [('A1', T0('mockA1') + 0.5, ['A1']), ('A2', 11.35, ['A2']), ('A3', fs0 + 3.9, ['A3']),
         ('B1', 1.50, ['B1']), ('B2', 11.62, ['B2']), ('B3', 7.28, ['B3']),
         ('C1', 4.75, ['C1']), ('C2', 8.95, ['C2']), ('C3', T1('post') - 0.6, ['C3']),
         ('D1', 1.20, ['D1']), ('D2', T0('jump') + 2.05, ['D2']),
         ('E1', T0('route1') + 2.6, ['E1']), ('E2', T0('routeFull') + 3.3, ['E2']),
         ('F1', T0('quote') + 2.75, ['F1']), ('F2', T0('split') + 3.4, ['F2']),
         ('G1', T0('convoy') + 1.0, ['G1']), ('G2', T0('glass') + 1.7, ['G2']),
         ('H1', a0 + (13.34 - 12.32) + 0.05, ['H1']), ('H2', 12.40, ['H2']),
         ('I1', T0('sweep1') + 0.24, ['I1'])]
    mocks = [{'name': c, 't': round(t, 4), 'only': o} for c, t, o in M]
    # transitions read better as a three-frame strip (bands of the frame stacked in one 1080x1920 still)
    lk = T0('lineup')
    mocks.append({'name': 'I2', 'only': ['C1'], 'band': [760, 1400],
                  'strip': [{'t': round(5.5, 4), 'label': 'LOCKED  ·  CAR 02'}, {'t': round(lk + 0.28, 4), 'label': 'CUT  ·  LOCK LOST'},
                            {'t': round(lk + 0.75, 4), 'label': 'RE-ACQUIRED  ·  CAR 03'}]})
    mocks.append({'name': 'I3', 'only': ['B1'], 'band': [560, 1200],
                  'strip': [{'t': round(T0('whip1') - 0.3, 4), 'label': 'SHOT A'}, {'t': round(T0('whip1') + 3.5 / FPS, 4), 'label': 'WHIP  ·  LIB/FX.PY WHIP()'},
                            {'t': round(T1('whip1') + 0.25, 4), 'label': 'SHOT B'}]})
    return comps, chip, mocks


def motion_plan(S):
    """Samples per frame (true motion blur): 1 on holds, more on fast moves; 270-degree shutter on whips/slams."""
    T0 = lambda i: S[i]['t0']; T1 = lambda i: S[i]['t1']
    sp = []
    A = lambda a, b, k, sh=200: sp.append({'a': round(a, 4), 'b': round(b, 4), 'k': k, 'shutter': sh})
    A(0, T0('whip1'), 3)                                  # D1 seconds roll, H1 box glide
    A(0.22, 0.62, 12, 220)                                # B1 acquire
    A(T0('whip1') - 0.02, T1('whip1') + 0.02, 16, 270)    # whip (B1 rides it)
    A(T0('convoy') + 0.1, T0('convoy') + 0.45, 16, 270)   # G1 slam
    A(T0('convoy') + 1.2, T0('convoy') + 1.65, 10)        # G1 exit
    for a in (4.08, 4.93, T0('lineup') + 0.38):
        A(a, a + 0.38, 12, 220)                           # C1 acquire / hops / re-acquire
    A(T0('lineup'), T0('lineup') + 0.45, 10)              # A2 slide-in, lock lost
    A(6.38, 6.72, 10); A(6.6, 7.0, 12, 220)               # C1 exit, B3 acquire
    A(T1('lineup') - 0.34, T1('lineup'), 10)
    A(T0('far'), T1('far'), 6)                            # C2 scan
    A(9.68, T1('host2'), 4)                               # H2 pops
    A(10.1, 10.8, 10)                                     # B2 acquire
    A(T1('host2') - 0.4, T1('host2'), 10)
    A(T0('sweep1') - 0.02, T1('sweep1') + 0.1, 12, 220)   # I1 + A3 slide
    A(T0('glass'), T0('glass') + 0.7, 8); A(T1('glass') - 0.45, T1('glass'), 8)
    A(T0('route1'), T0('route1') + 2.3, 6)                # E1 comet, A3 breath
    A(T1('route1') - 0.45, T1('route1'), 8)
    A(T0('sweep2') - 0.02, T1('sweep2') + 0.02, 12, 220)
    A(T0('routeFull'), T1('routeFull'), 6)
    A(T0('quote'), T0('quote') + 2.9, 6); A(T1('quote') - 0.45, T1('quote'), 8)
    A(T0('split'), T0('split') + 3.3, 6); A(T1('split') - 0.45, T1('split'), 8)
    A(T0('jump'), T0('jump') + 0.4, 16, 270)              # card wipe
    A(T0('jump') + 0.4, T0('jump') + 2.1, 16, 270)        # reels
    A(T1('jump') - 0.7, T1('jump') + 0.45, 12, 220)       # hand-off to D1, A1 build, C3 acquire
    A(T1('post') - 0.45, T1('post'), 8)
    A(T0('index'), T0('index') + 0.8, 8)
    return {'k': 1, 'shutter': 180, 'spans': sp}


# ============================================================================ prep
def stage_prep():
    os.makedirs(os.path.join(WORK, 'plates', 'rooftop'), exist_ok=True)
    mezz = os.path.join(WORK, 'src', 'rooftop_mezz.mov')
    if not os.path.exists(mezz):
        os.makedirs(os.path.dirname(mezz), exist_ok=True)
        run([FF, '-v', 'error', '-y', '-i', CFG['tools']['rooftopRaw'], '-map', '0:v:0', '-map', '0:a:0', '-vf',
             "select='not(mod(n\\,2))',setpts=N/(30000/1001)/TB,scale=1080:1920:flags=lanczos,format=yuv420p", '-r', '30000/1001',
             '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-tune', 'film', '-color_primaries', 'bt709', '-color_trc', 'bt709',
             '-colorspace', 'bt709', '-c:a', 'pcm_s16le', mezz])
    if not os.path.exists(os.path.join(WORK, 'plates', 'rooftop', '0429.jpg')):
        run([FF, '-v', 'error', '-y', '-i', mezz, '-q:v', '1', '-qmin', '1', '-start_number', '0', os.path.join(WORK, 'plates', 'rooftop', '%04d.jpg')])
    scene = build_scene()
    # stills: rooftop:N from the 4K source (frame 2N of the 59.94 fps file), rally:N from the rally cut
    srcs = set()
    def walk(sp):
        if not isinstance(sp, dict):
            return
        if sp.get('kind') == 'still':
            srcs.add(sp['src'])
        for k in ('top', 'bottom', 'plate', 'a', 'b'):
            walk(sp.get(k))
    for s in scene['shots']:
        walk(s)
    for src in sorted(srcs):
        out = os.path.join(WORK, 'plates', 'still_' + src.replace(':', '_') + '.png')
        if os.path.exists(out):
            continue
        kind, n = src.split(':'); n = int(n)
        if kind == 'rooftop':
            run([FF, '-v', 'error', '-y', '-i', CFG['tools']['rooftopRaw'], '-vf', f"select='eq(n\\,{2 * n})',format=rgb24", '-vsync', '0', '-frames:v', '1', out])
        else:
            run([FF, '-v', 'error', '-y', '-i', CFG['tools']['rallyCut'], '-vf', f"select='eq(n\\,{n})'", '-vsync', '0', '-frames:v', '1', out])
    check_kb(scene)
    json.dump(scene, open(os.path.join(WORK, 'scene.json'), 'w'))
    open(os.path.join(WORK, 'scene.js'), 'w').write('window.SCENE = ' + json.dumps(scene) + ';\n')
    open(os.path.join(WORK, 'tracks.js'), 'w').write('window.TRACKS = ' + open(os.path.join(LIB, 'data', 'tracks.json')).read() + ';\n')
    meter = os.path.join(LIB, 'data', 'meter.json')
    if not os.path.exists(meter):
        make_meter(mezz, meter)
    import base64
    logos = {f: 'data:image/png;base64,' + base64.b64encode(open(os.path.join(HERE, '..', '..', '02-logos', 'png', f), 'rb').read()).decode()
             for f in ('sce-primary-horizontal--white.png', 'sce-icon-mark-only--white.png')}
    open(os.path.join(WORK, 'kitdata.js'), 'w').write('window.KITDATA = {"meter": ' + open(meter).read() + ', "logos": ' + json.dumps(logos) + '};\n')
    print(f"scene: {len(scene['shots'])} shots, {len(scene['comps'])} components, reel {scene['reelEnd']:.2f} s ({scene['reelFrames']} frames), "
          f"stills {sorted(srcs)}")
    return scene


def check_kb(scene):
    """every Ken Burns move must stay inside its picture (no exposed edges)."""
    def chk(sp, name):
        if not isinstance(sp, dict) or sp.get('kind') != 'still' or not sp.get('kb'):
            return
        k = sp['kb']
        for s, dx, dy in ((k['s0'], k.get('dx0', 0), k.get('dy0', 0)), (k['s1'], k.get('dx1', 0), k.get('dy1', 0))):
            ax, ay = k.get('ax', 540), k.get('ay', 960)
            x0, x1 = (0 - ax - dx) / s + ax, (1080 - ax - dx) / s + ax
            y0, y1 = (0 - ay - dy) / s + ay, (1920 - ay - dy) / s + ay
            if sp.get('_region'):
                y0 = (sp['_region'][0] - ay - dy) / s + ay; y1 = (sp['_region'][1] - ay - dy) / s + ay
            assert x0 >= -0.5 and x1 <= 1080.5 and y0 >= -0.5 and y1 <= 1920.5, (name, s, x0, x1, y0, y1)
            if sp['src'].startswith('rally:'):
                assert y0 >= 340, (name, 'the rally frame\'s burned-in bug (y 296-338) would show', y0)
    for s in scene['shots']:
        for k in ('plate', 'a', 'b'):
            sp = s.get(k)
            if isinstance(sp, dict) and sp.get('kind') == 'split':
                sp['top']['_region'] = [0, sp['seam']]; sp['bottom']['_region'] = [sp['seam'], 1920]
                chk(sp['top'], s['id'] + '.top'); chk(sp['bottom'], s['id'] + '.bottom')
            else:
                chk(sp, s['id'])


def make_meter(mezz, out, t0=7.0, t1=10.6, bands=14):
    """a 14-band level envelope (29.97 fps) from the rooftop clip's own speech, used as demo data for the meters."""
    import numpy as np
    raw = subprocess.run([FF, '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', mezz, '-ac', '1', '-ar', '48000', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = 48000 / FPS; n = int(len(x) / hop) - 1
    edges = np.geomspace(120, 7000, bands + 1)
    rows = []
    for i in range(n):
        a = int(i * hop); seg = x[a:a + 2048]
        if len(seg) < 2048:
            seg = np.pad(seg, (0, 2048 - len(seg)))
        sp = np.abs(np.fft.rfft(seg * np.hanning(2048)))
        fr = np.fft.rfftfreq(2048, 1 / 48000)
        v = [20 * np.log10(sp[(fr >= edges[k]) & (fr < edges[k + 1])].mean() + 1e-6) for k in range(bands)]
        rows.append(v)
    A = np.array(rows)
    A = (A - np.percentile(A, 8)) / (np.percentile(A, 99.5) - np.percentile(A, 8))
    A = np.clip(A, 0, 1) ** 1.3
    # interleave low/high bands so the bar row reads as a meter, not a slope
    order = [0, 7, 2, 9, 4, 11, 6, 13, 1, 8, 3, 10, 5, 12]
    A = A[:, order]
    json.dump({'fps': FPS, 'src': f'DJI_0029 audio {t0}-{t1} s (demo data)', 'bands': [[round(float(v), 3) for v in r] for r in A]}, open(out, 'w'))


# ============================================================================ layer capture
def stage_layer(scene, frames=None, out=None, workers=3):
    out = out or os.path.join(WORK, 'layer')
    os.makedirs(out, exist_ok=True)
    if frames is None:
        frames = list(range(scene['reelFrames']))
    todo = [f for f in frames if not os.path.exists(os.path.join(out, f'{f:05d}.png'))]
    print(f'layer: {len(todo)} of {len(frames)} frames to capture')
    if not todo:
        return
    chunks = [todo[i::workers] for i in range(workers)]
    procs = []
    for i, ch in enumerate(chunks):
        if not ch:
            continue
        lst = os.path.join(WORK, f'frames_{i}.json'); json.dump(ch, open(lst, 'w'))
        procs.append(subprocess.Popen([NODE, os.path.join(LIB, 'kcapture.js'), os.path.join(HERE, 'kit.html'), out, 'list', '30000/1001', lst, '--workers', '1'],
                                      stderr=open(os.path.join(WORK, f'capture_{i}.log'), 'w')))
    for p in procs:
        if p.wait() != 0:
            raise SystemExit('capture failed, see .work/capture_*.log')


# ============================================================================ audio
def stage_audio(scene):
    """the clip's own sound at low level, only where the rooftop clip plays at 1x; 60 ms fades; silence elsewhere."""
    import numpy as np, wave
    mezz = os.path.join(WORK, 'src', 'rooftop_mezz.mov')
    raw = subprocess.run([FF, '-v', 'error', '-i', mezz, '-ac', '2', '-ar', '48000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    src = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
    SR = 48000
    n = int(round(scene['reelEnd'] * SR))
    out = np.zeros((n, 2), np.float32)
    g = 10 ** (CFG['reel']['audio']['gainDb'] / 20); fade = int(CFG['reel']['audio']['fadeMs'] / 1000 * SR)
    for s in scene['shots']:
        if s['t0'] >= scene['reelEnd'] - 1e-6:
            continue
        sp = s.get('plate')
        if sp and sp['kind'] == 'clip' and sp.get('speed', 1) == 1:
            a, b = int(round(s['t0'] * SR)), int(round(s['t1'] * SR))
            c = int(round(sp['c0'] * SR))
            seg = src[c:c + (b - a)].copy()
            L = len(seg)
            env = np.ones(L, np.float32); f = min(fade, L // 2)
            env[:f] = np.linspace(0, 1, f); env[L - f:] = np.linspace(1, 0, f)
            out[a:a + L] += seg * env[:, None] * g
        if s.get('fx') == 'sweep' and s['a'].get('kind') == 'clip':   # the clip's sound fades out under the sweep
            a, b = int(round(s['t0'] * SR)), int(round(s['t1'] * SR)); c = int(round(s['a']['c0'] * SR))
            seg = src[c:c + (b - a)].copy(); L = len(seg)
            out[a:a + L] += seg * np.linspace(1, 0, L, dtype=np.float32)[:, None] ** 1.5 * g
        if s.get('fx') == 'whip':                         # carry the sound across the whip with a crossfade
            a, b = int(round(s['t0'] * SR)), int(round(s['t1'] * SR)); L = b - a
            ca, cb = int(round(s['a']['c0'] * SR)), int(round(s['b']['c0'] * SR))
            x = np.linspace(0, 1, L, dtype=np.float32)[:, None]
            out[a:b] += (src[ca:ca + L] * np.cos(x * np.pi / 2) + src[cb:cb + L] * np.sin(x * np.pi / 2)) * g
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
    import numpy as np
    from compose import Composer
    C = Composer(scene, WORK)
    N = scene['reelFrames']
    vid = os.path.join(WORK, 'reel_video.mov')
    p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30000/1001', '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', vid], stdin=subprocess.PIPE)
    t = time.time()
    lay = os.path.join(WORK, 'layer')
    for i in range(N):
        img = C.frame(i, os.path.join(lay, f'{i:05d}.png'), os.path.join(lay, f'fx_{i:05d}.json'))
        p.stdin.write(img.tobytes())
        if i % 100 == 0:
            print(f'  compose {i}/{N} {time.time() - t:.0f}s', flush=True)
    p.stdin.close(); p.wait()
    aud = stage_audio(scene)
    os.makedirs(os.path.join(HERE, 'exports'), exist_ok=True)
    master = os.path.join(HERE, 'exports', 'vlog-kit-reel.mp4')
    run([FF, '-v', 'error', '-y', '-i', vid, '-i', aud, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
         '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-profile:v', 'high',
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', '-movflags', '+faststart', master])
    print('master', master, f'{os.path.getsize(master) / 2**20:.1f} MiB')
    return master


def stage_deliver():
    master = os.path.join(HERE, 'exports', 'vlog-kit-reel.mp4')
    size = os.path.getsize(master)
    deliv = os.path.join(HERE, 'exports', 'vlog-kit-reel_DELIVERY.mp4')
    if size <= 29.5 * 2**20:
        print(f'master is {size / 2**20:.1f} MiB (under 30 MiB): no delivery copy needed')
        if os.path.exists(deliv):
            os.remove(deliv)
        return master
    dur = float(subprocess.run([FF, '-i', master], capture_output=True, text=True).stderr.split('Duration: ')[1].split(',')[0].split(':')[2]) + 0
    kbps = int((28.0 * 2**20 * 8 / dur - 160e3) / 1000)
    log = os.path.join(WORK, 'x264pass')
    common = ['-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{kbps}k', '-maxrate', f'{int(kbps * 1.6)}k', '-bufsize', f'{kbps * 2}k',
              '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-profile:v', 'high', '-passlogfile', log]
    run([FF, '-v', 'error', '-y', '-i', master, *common, '-pass', '1', '-an', '-f', 'mp4', '/dev/null'])
    run([FF, '-v', 'error', '-y', '-i', master, *common, '-pass', '2', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', deliv])
    print('delivery', deliv, f'{os.path.getsize(deliv) / 2**20:.2f} MiB at {kbps} kb/s')
    return deliv


# ============================================================================ mockups + board
NAMES = {'A1': 'CORNER BUG', 'A2': 'EDGE TAB', 'A3': 'BREATHING BANNER', 'B1': 'NAME LOCK', 'B2': 'RETICLE', 'B3': 'GUEST LOCK',
         'C1': 'CONVOY HOP', 'C2': 'LINEUP SCAN', 'C3': 'LEAD-CAR LOCK', 'D1': 'CLOCK STAMP', 'D2': 'TIME JUMP', 'E1': 'ROUTE, CORNER', 'E2': 'ROUTE, FULL FRAME',
         'F1': 'TESTIMONIAL CARD', 'F2': 'Q&A SPLIT', 'G1': 'CHAPTER SLAM', 'G2': 'GLASS SLAM', 'H1': 'BOXED CAPTIONS',
         'H2': 'SPEAKER STRIP', 'I1': 'GOLD LIGHT SWEEP', 'I2': 'LOCK LOST / RE-ACQUIRE', 'I3': 'WHIP-PAN HELPER'}


def stage_mocks(scene, only=None):
    from compose import Composer
    from PIL import Image
    from PIL import ImageDraw, ImageFont
    import numpy as np
    mocks = [m for m in scene['mocks'] if not only or m['name'] in only]
    lay = os.path.join(WORK, 'mocklayer'); os.makedirs(lay, exist_ok=True)
    caps = []
    for m in mocks:
        if 'strip' in m:
            caps += [{'name': f"{m['name']}_{k}", 't': s['t'], 'only': m['only']} for k, s in enumerate(m['strip'])]
        else:
            caps.append(m)
    lst = os.path.join(WORK, 'mocks.json'); json.dump(caps, open(lst, 'w'))
    run([NODE, os.path.join(LIB, 'mockcap.js'), os.path.join(HERE, 'kit.html'), lay, lst])
    C = Composer(scene, WORK)
    outd = os.path.join(HERE, 'mockups'); os.makedirs(outd, exist_ok=True)
    fm = os.path.join(HERE, '..', '..', '07-fonts', 'Michroma-Regular.ttf')
    for m in mocks:
        if 'strip' in m:                                  # three bands of the frame, stacked, each labelled
            y0, y1 = m['band']; bh = y1 - y0
            img = Image.new('RGB', (1080, 1920), (0, 0, 0)); d = ImageDraw.Draw(img)
            for k, st in enumerate(m['strip']):
                fr = C.frame(st['t'] * FPS, os.path.join(lay, f"{m['name']}_{k}.png"), os.path.join(lay, f"fx_{m['name']}_{k}.json"))
                img.paste(Image.fromarray(fr[y0:y1]), (0, k * bh))
                yy = k * bh
                d.rectangle([0, yy, 1080, yy + 4], fill=(251, 209, 1)); d.rectangle([842, yy, 1080, yy + 4], fill=(255, 255, 255))
                tx = f"{k + 1}  ·  {st['label']}"
                d.rectangle([24, yy + 22, 24 + 22 + int(len(tx) * 15.5), yy + 64], fill=(0, 0, 0))
                d.text((36, yy + 32), tx, font=ImageFont.truetype(fm, 20), fill=(251, 209, 1))
            img = np.asarray(img)
        else:
            img = C.frame(m['t'] * FPS, os.path.join(lay, m['name'] + '.png'), os.path.join(lay, f"fx_{m['name']}.json"))
        name = f"{m['name']}_{NAMES[m['name']].lower().replace(', ', '-').replace(' / ', '-').replace(' ', '-').replace('&', 'and')}.jpg"
        for old in [f for f in os.listdir(outd) if f.startswith(m['name'] + '_')]:
            os.remove(os.path.join(outd, old))
        Image.fromarray(img).save(os.path.join(outd, name), quality=92)
        print('  mock', name)
    board()


def board():
    from PIL import Image, ImageDraw, ImageFont
    outd = os.path.join(HERE, 'mockups')
    files = sorted(f for f in os.listdir(outd) if f[:2] in NAMES and f.endswith('.jpg'))
    fb = os.path.join(HERE, '..', '..', '07-fonts', 'BebasNeue-Regular.ttf'); fm = os.path.join(HERE, '..', '..', '07-fonts', 'Michroma-Regular.ttf')
    cols, tw, th = 8, 320, 569
    rows = math.ceil(len(files) / cols)
    head, lab, gap = 190, 70, 18
    Wb = cols * tw + (cols + 1) * gap; Hb = head + rows * (th + lab + gap) + gap + 40
    B = Image.new('RGB', (Wb, Hb), (8, 8, 9)); d = ImageDraw.Draw(B)
    F = lambda f, s: ImageFont.truetype(f, s)
    d.rectangle([gap, 40, gap + 300, 48], fill=(251, 209, 1)); d.rectangle([gap + 234, 40, gap + 300, 48], fill=(255, 255, 255))
    d.text((gap, 60), 'SE VLOG KIT  ·  LOCKED-ON', font=F(fb, 84), fill=(255, 255, 255))
    d.text((gap + 2, 150), 'ONE STILL PER VARIATION OVER REAL FOOTAGE: RED ROCK CASINO GARAGE (DJI_0029, 22:49, SEP 15 2026) AND THE APPROVED RALLY CUT.  SAY THE CODES.',
           font=F(fm, 15), fill=(251, 209, 1))
    for i, f in enumerate(files):
        c, r = i % cols, i // cols
        x = gap + c * (tw + gap); y = head + r * (th + lab + gap)
        im = Image.open(os.path.join(outd, f)).resize((tw, th), Image.LANCZOS)
        B.paste(im, (x, y + lab))
        code = f[:2]
        d.rectangle([x, y, x + tw, y + lab - 6], fill=(0, 0, 0))
        d.rectangle([x, y, x + int(tw * .78), y + 4], fill=(251, 209, 1)); d.rectangle([x + int(tw * .78), y, x + tw, y + 4], fill=(255, 255, 255))
        d.text((x + 12, y + 12), code, font=F(fb, 50), fill=(251, 209, 1))
        d.text((x + 70, y + 30), NAMES[code], font=F(fm, 13), fill=(255, 255, 255))
    B.save(os.path.join(outd, 'BOARD.jpg'), quality=90)
    print('board', os.path.join(outd, 'BOARD.jpg'), B.size)


# ============================================================================ stills (single reel times)
def stage_stills(scene, times):
    from compose import Composer
    from PIL import Image
    out = os.path.join(WORK, 'stills'); os.makedirs(out, exist_ok=True)
    frames = sorted(set(int(round(t * FPS)) for t in times))
    stage_layer(scene, frames, os.path.join(WORK, 'layer'), workers=min(3, len(frames)))
    C = Composer(scene, WORK)
    for f in frames:
        img = C.frame(f, os.path.join(WORK, 'layer', f'{f:05d}.png'), os.path.join(WORK, 'layer', f'fx_{f:05d}.json'))
        Image.fromarray(img).save(os.path.join(out, f'r{f:05d}_{f / FPS:06.2f}s.jpg'), quality=90)
        print('  still', f, f'{f / FPS:.2f}s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all')
    ap.add_argument('--stills'); ap.add_argument('--mocks')
    a = ap.parse_args()
    scene = stage_prep()
    if a.stills:
        stage_stills(scene, [float(v) for v in a.stills.split(',')]); return
    st = a.stage
    if st in ('all', 'layer', 'reel'):
        stage_layer(scene)
    if st in ('all', 'reel'):
        stage_reel(scene)
    if st in ('all', 'deliver'):
        stage_deliver()
    if st in ('all', 'mocks'):
        stage_mocks(scene, a.mocks.split(',') if a.mocks else None)
    if st == 'board':
        board()
    if st in ('all', 'qa'):
        import qa
        qa.run(scene, HERE, WORK, FF)


if __name__ == '__main__':
    main()
