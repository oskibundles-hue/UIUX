#!/usr/bin/env python3
"""
build.py -- ONE command for the Sep 15 rally vlog v2 (Egnyte rally day), rebuilt from the raw footage:
picture edit + grade (lib/plate.py), sound (lib/music.py, lib/mix.py), tracking (lib/track_mid.py), the
Locked-On motion layer (story.html + lib/sekit.js + lib/v2kit.js, captured by lib/kcapture.js), the
composite, the exports and QA.

    python3 build.py                        # everything
    python3 build.py --stage join           # stages: shots, track, join, prep, audio, front, compose, qa (comma list)
    python3 build.py --stills 0,776,4200    # composite single frames -> .work/stills/ (no mp4)

Stages (all cached in .work/):
  shots    lib/plate.py: every EDL shot -> .work/shots/NN.mov (graded, reframed, ramps)
  track    lib/track_mid.py on the rendered shots for every lock-on and licence plate in config.json `tracks`
           -> lib/data/tracks.json (boxes in OUTPUT pixels by OUTPUT frame), QA sheets -> exports/qa/track_*.jpg
  join     lib/plate.py: the shots in order with whips, sweeps, impacts, chapter punches and the plate blurs
           -> .work/plate.mov (5230 frames, 29.97 fps)
  prep     the layer scene (.work/scene.js), the camera clock of every frame (.work/clock.js), tracks.js,
           and the SFX cue list (.work/sfx_cues.json), all from config.json + the EDL + captions.json
  audio    lib/music.py (only when no audio/music.wav is supplied) + lib/mix.py -> .work/mix.wav and
           .work/mix_nomusic.wav (-14 LUFS), .work/meter.json -> .work/layerdata.js
  front    story.html captured frame by frame (RGBA PNG, sub-frame motion blur on fast moves, 3 Chromium processes)
  compose  ffmpeg: plate + vignette + layer overlay -> x264 High two-pass 11 Mb/s + AAC 256k (+faststart) master;
           the no-music master (same video stream, other mix); _DELIVERY copy only if the master is over
           11.5 Mb/s; the 720x1280 phone preview (< 30 MiB)
  qa       per-beat stills (first / mid / last), poster, contact sheet, lock-on stills, loudness, true peak,
           tail silence, safe-zone ink audit -> exports/qa/
"""
import argparse, hashlib, json, math, os, re, shutil, struct, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(ROOT, 'lib')
WORK = os.path.join(ROOT, '.work')
EXP = os.path.join(ROOT, 'exports')
QA = os.path.join(EXP, 'qa')
sys.path.insert(0, LIB)
C = json.load(open(os.path.join(ROOT, 'config.json')))
FF = os.environ.get('FFMPEG', C['paths']['ffmpeg'])
EDL = json.load(open(C['paths']['edl']))
CAPS = json.load(open(C['paths']['captions']))
FPS = 30000 / 1001
W, H = 1080, 1920
NF = int(round(EDL['duration'] * FPS))
DUR = NF / FPS
NAME = C['name']
NODE = shutil.which('node') or '/opt/node22/bin/node'


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def _hash(*paths, extra=''):
    h = hashlib.sha1(extra.encode())
    for p in paths:
        h.update(open(p, 'rb').read()); h.update(b'|')
    return h.hexdigest()[:16]


# ================================================================================== clock
def hms(s):
    s = s.split(':'); return int(s[0]) * 3600 + int(s[1]) * 60 + float(s[2])


def clock_table():
    """camera clock (seconds of the day, from the file names) and speed for every output frame; None on the card."""
    import plate as PL
    starts = {k: hms(v) for k, v in C['clockStarts'].items() if not k.startswith('_')}
    tab = [None] * NF
    for k, f0, f1 in PL.FR:
        s = PL.SHOTS[k]
        if s['src'] == 'card':
            continue
        ts = PL.src_times(k)
        for j in range(f1 - f0):
            t, sp = ts[j]
            tab[f0 + j] = [round(starts[s['src']] + t, 4), round(sp, 4)]
    return tab


def fmt_clock(sec):
    sec = int(sec); return f'{sec // 3600:02d}:{sec // 60 % 60:02d}'


# ================================================================================== scene
def caption_words():
    hide = C['captions']['hide']
    fix = C['captions'].get('fix', {})
    out = []
    for piece in CAPS + C['captions'].get('extra', []):
        for a, b, w in piece['words']:
            if any(h[0] <= a < h[1] for h in hide):
                continue
            for k, v in fix.items():
                w = re.sub(r'\b' + re.escape(k) + r'\b', v, w)
            out.append([round(a, 3), round(b, 3), w])
    return sorted(out)


def build_scene():
    L = C['layer']
    comps = [dict(c) for c in L['comps']]
    cp = dict(L['captions'])
    comps.append(dict(code='H1', type='captionsBox', t0=cp['t0'], t1=cp['t1'], p=dict(cp['p'], words=caption_words())))
    # testimonial card words (verbatim, timeline times from captions.json)
    for c in comps:
        if c['type'] == 'quoteCard' and 'wordsFrom' in c['p']:
            a, b = c['p'].pop('wordsFrom')
            ws = []
            for piece in CAPS:
                for w0, w1, w in piece['words']:
                    if a <= w0 < b:
                        ws.append({'w': w.upper(), 't': w0})
            for ins in c['p'].pop('insert', []):
                ws.append({'w': ins['w'], 't': ins['t']})
            ws.sort(key=lambda d: d['t'])
            for rp in c['p'].pop('replaceLast', []):
                ws[-1]['w'] = rp
            c['p']['words'] = ws
    # capture plan: 1 sample on holds, more on the fast moves
    spans = []
    def sp(a, b, k=10, sh=220):
        spans.append({'a': round(a, 3), 'b': round(b, 3), 'k': k, 'shutter': sh})
    for c in comps:
        t0, t1, ty, p = c['t0'], c['t1'], c['type'], c.get('p', {})
        if ty == 'v2hook':
            sp(p['exit'] - 0.02, p['exit'] + 0.42, 12)
        elif ty == 'bannerTab':
            sp(t0 - 0.02, t0 + 0.7, 10); sp(t1 - 0.36, t1 + 0.02, 10)
        elif ty == 'chapterSlam':
            sp(t0 - 0.02, t0 + 0.55, 14, 270); sp(t1 - 0.4, t1 + 0.02, 10)
        elif ty == 'sweep':
            sp(t0 - 0.02, t1 + 0.02, 12, 270)
        elif ty in ('v2lock', 'leadLock', 'personLock'):
            a = p.get('acquire', t0); sp(a - 0.02, a + 0.9, 10, 220); sp(p.get('exit', t1 - 0.3) - 0.02, p.get('exit', t1 - 0.3) + 0.3, 10)
        elif ty == 'convoyHop':
            for s in p['segs']:
                sp(s['t'] - 0.02, s['t'] + 0.9, 10, 220)
            sp(p['exit'] - 0.02, p['exit'] + 0.3, 10)
        elif ty == 'v2slam':
            sp(t0 - 0.02, t0 + 0.5, 14, 270); sp(p['exit'] - 0.02, p['exit'] + 0.3, 12, 270)
        elif ty in ('v2route', 'v2routeCard'):
            sp(t0 - 0.02, t0 + 0.7, 8)
            for s in p['steps']:
                sp(s['t'] - 0.55, s['t'] + 0.35, 8)
            sp(p.get('exit', t1 - 0.4) - 0.02, p.get('exit', t1 - 0.4) + 0.4, 8)
        elif ty == 'v2wall':
            sp(t0 - 0.02, t0 + 0.6, 8)
            for it in p['items']:
                sp(it['t'] - 0.04, it['t'] + 0.3, 10, 220)
            sp(p['exit'] - 0.02, p['exit'] + 0.4, 10)
        elif ty in ('v2cta', 'v2place', 'clockStamp', 'quoteCard'):
            sp(t0 - 0.02, t0 + 0.6, 8); sp(t1 - 0.45, t1 + 0.02, 8)
        elif ty == 'v2end':
            sp(t0 - 0.02, t0 + 0.16, 32, 270); sp(t0 + 0.16, t0 + 0.75, 10)
    scene = dict(dur=DUR, comps=comps, windows=[[0, DUR + 0.01]], plan={'k': 1, 'shutter': 180, 'spans': spans})
    open(os.path.join(WORK, 'scene.js'), 'w').write('window.SCENE=' + json.dumps(scene) + ';\n')
    return scene


def sfx_cues(scene):
    """the Locked-On accents, derived from the layer schedule and the plate transitions."""
    F = C['sfx']['files']
    cues = []
    def cue(key, t, why, db=0.0, align=None, dur=None):
        e = dict(file=F[key], t=round(t, 4), why=why, db=db)
        e['align'] = align if align is not None else C['sfx']['align'].get(key, 0.0)
        if dur:
            e['dur'] = dur
        cues.append(e)
    whoosh_i = 0
    for c in scene['comps']:
        t0, t1, ty, p = c['t0'], c['t1'], c['type'], c.get('p', {})
        if ty == 'v2hook':
            cue('hitOpen', 0.0, 'hook panel, frame 0', -1)
        elif ty == 'bannerTab':
            cue('whooshRL', t0 + 0.15, 'SE side banner slides in', -5)
        elif ty == 'chapterSlam':
            cue('hitDrop', t0 + 0.16, f'chapter slam {p.get("title")}', -3, dur=1.6)
        elif ty == 'sweep':
            cue('whooshLR', (t0 + t1) / 2, 'gold light sweep', -2)
        elif ty in ('v2lock', 'leadLock', 'personLock'):
            a = p.get('acquire', t0)
            cue('tickAcquire', a, f'lock acquire {c["code"]}', 0); cue('tickLock', a + 0.26, f'lock {c["code"]}', 0)
        elif ty == 'convoyHop':
            for i, s in enumerate(p['segs']):
                if i == 0:
                    cue('tickAcquire', s['t'], 'convoy lock acquire', 0); cue('tickLock', s['t'] + 0.26, 'convoy lock', 0)
                elif s.get('mode') == 'relock':        # lock lost as the car leaves frame: silent; the tick lands on the re-lock
                    cue('tickLock', s['t'] + s.get('lost', 0.36) + 9 / FPS, f'convoy re-lock {i + 1}', 0)
                else:
                    cue('tickLock', s['t'] + 9 / FPS, f'convoy hop {i + 1}', 0)
        elif ty == 'v2slam':
            cue('hitDrop', t0 + 0.12, 'SAFELY. slam', -2, dur=1.4)
        elif ty in ('v2route', 'v2routeCard'):
            cue('whooshLR', t0 + 0.1, 'route panel in', -6)
            if p.get('firstAt') is not None:
                cue('tickReel', p['firstAt'], 'route: first stop', 0, dur=0.1)
            for s in p['steps']:
                cue('tickReel', s['t'], f'route: stop {s["k"] + 1}', 0, dur=0.1)
            for s in p.get('called', []):
                cue('tickAcquire', s['t'], f'route: stop {s["k"] + 1} named', -3)
        elif ty == 'v2wall':
            for it in p['items']:
                cue('tickLock', it['t'], f'quote wall {it["w"]}', 0)
        elif ty in ('v2cta', 'v2place', 'clockStamp'):
            cue('tickLock', t0 + 0.2, f'{ty} in', -2)
        elif ty == 'quoteCard':
            cue('whooshRL', t0 + 0.1, 'testimonial card in', -6)
        elif ty == 'v2end':
            cue('hitEnd', t0, 'end card', 0)
    for tr in C['transitions']:
        import plate as PL
        t = PL.SHOTS[tr['into']]['t']
        if tr['type'] == 'whip':
            cue('whooshLR' if whoosh_i % 2 == 0 else 'whooshRL', t, f'whip into shot {tr["into"]}', -2); whoosh_i += 1
        elif tr['type'] == 'impact' and tr.get('sfx', True):
            cue('hitOpen', t, f'impact cut into shot {tr["into"]}', -4, dur=1.4)
    for e in C['sfx'].get('extra', []):
        cue(e['key'], e['t'], e['why'], e.get('db', 0.0))
    cues.sort(key=lambda e: e['t'])
    json.dump(cues, open(os.path.join(WORK, 'sfx_cues.json'), 'w'), indent=1)
    return cues


def st_prep(A):
    os.makedirs(WORK, exist_ok=True)
    scene = build_scene()
    sfx_cues(scene)
    open(os.path.join(WORK, 'clock.js'), 'w').write('window.CLOCK=' + json.dumps(clock_table()) + ';\n')
    tp = os.path.join(LIB, 'data', 'tracks.json')
    T = json.load(open(tp)) if os.path.exists(tp) else {}
    open(os.path.join(WORK, 'tracks.js'), 'w').write('window.TRACKS=' + json.dumps(T) + ';\n')
    mp = os.path.join(WORK, 'meter.json')
    ld = {'meter': json.load(open(mp))} if os.path.exists(mp) else {}
    open(os.path.join(WORK, 'layerdata.js'), 'w').write('window.LAYERDATA=' + json.dumps(ld) + ';\n')
    log(f'prep: {len(scene["comps"])} components, {len(scene["plan"]["spans"])} fast spans')


# ================================================================================== plate / audio / tracks
def st_shots(A):
    sh([sys.executable, os.path.join(LIB, 'plate.py'), 'shots'])


def st_join(A):
    sh([sys.executable, os.path.join(LIB, 'plate.py'), 'join'])


def st_audio(A):
    if not os.path.exists(os.path.join(ROOT, C['music']['file'])):
        mw = os.path.join(WORK, 'music_synth.wav')
        if not os.path.exists(mw) or os.path.getmtime(mw) < os.path.getmtime(os.path.join(LIB, 'music.py')):
            sh([sys.executable, os.path.join(LIB, 'music.py'), '--out', mw, '--sync', os.path.join(WORK, 'music_synth.json'), '--dur', f'{DUR:.4f}'])
    sh([sys.executable, os.path.join(LIB, 'mix.py')])
    mp = os.path.join(WORK, 'meter.json')
    open(os.path.join(WORK, 'layerdata.js'), 'w').write('window.LAYERDATA=' + json.dumps({'meter': json.load(open(mp))}) + ';\n')


def st_track(A):
    plate = os.path.join(WORK, 'plate.mov')
    out = os.path.join(LIB, 'data', 'tracks.json')
    os.makedirs(os.path.join(LIB, 'data'), exist_ok=True)
    os.makedirs(QA, exist_ok=True)
    only = A.tracks.split(',') if A.tracks else None
    import plate as PL
    for name, t in C['tracks'].items():
        if name.startswith('_') or (only and name not in only):
            continue
        # tracked on the rendered shot file (identical pixels to the plate inside the shot: transitions only touch
        # the first / last few frames), frame numbers shifted to OUTPUT frames afterwards
        k = t['shot']
        off = PL.FR[k][1]
        video = os.path.join(WORK, 'shots', f'{k:02d}.mov')
        tmp = os.path.join(WORK, f'track_{name}.json')
        if os.path.exists(tmp):
            os.remove(tmp)
        sh([sys.executable, os.path.join(LIB, 'track_mid.py'), '--video', video, '--ffmpeg', FF, '--name', name,
            '--f0', str(t['f0'] - off), '--f1', str(t['f1'] - off), '--anchor', str(t['anchor'] - off), '--box', ','.join(str(v) for v in t['box']),
            '--scale-pen', str(t.get('scalePen', 0.2)), '--out', tmp])
        sh([sys.executable, os.path.join(LIB, 'trackqa.py'), '--video', video, '--ffmpeg', FF, '--tracks', tmp, '--names', name,
            '--every', str(t.get('every', 6)), '--out', os.path.join(QA, f'track_{name}.jpg')])
        r = json.load(open(tmp))[name]
        r['f0'] += off; r['f1'] += off; r['anchor'] += off; r['shot'] = k; r['video'] = f'plate (shot {k}, output frames)'
        for fr in r['frames']:
            fr['f'] += off; fr['t'] = round(fr['f'] / FPS, 5)
        r['t0'], r['t1'] = round(r['f0'] / FPS, 5), round((r['f1'] + 1) / FPS, 5)
        db = json.load(open(out)) if os.path.exists(out) else {}
        db[name] = r
        json.dump(db, open(out, 'w'), indent=1)


# ================================================================================== front
def front_sig():
    return _hash(os.path.join(ROOT, 'story.html'), os.path.join(LIB, 'kinetic.js'), os.path.join(LIB, 'sekit.js'),
                 os.path.join(LIB, 'v2kit.js'), os.path.join(LIB, 'kcapture.js'), os.path.join(LIB, 'accum.py'),
                 os.path.join(WORK, 'scene.js'), os.path.join(WORK, 'tracks.js'), os.path.join(WORK, 'clock.js'),
                 os.path.join(WORK, 'layerdata.js'))


def capture(frames, outdir, nproc=3, page=None):
    os.makedirs(outdir, exist_ok=True)
    if not frames:
        return
    chunks = [frames[k::nproc] for k in range(nproc)]
    procs = []
    for k, ch in enumerate(chunks):
        if not ch:
            continue
        lf = os.path.join(WORK, f'frames_{k}.json')
        json.dump(ch, open(lf, 'w'))
        procs.append(subprocess.Popen(['nice', '-n', '5', NODE, os.path.join(LIB, 'kcapture.js'), page or os.path.join(ROOT, 'story.html'),
                                       outdir, 'list', '30000/1001', lf, '--workers', '1'],
                                      stderr=open(os.path.join(WORK, f'capture_{k}.log'), 'w')))
    for p in procs:
        p.wait()
        assert p.returncode == 0, 'kcapture failed, see .work/capture_*.log'


def st_front(A):
    out = os.path.join(WORK, 'front')
    sigp = os.path.join(WORK, 'front.sig')
    sig = front_sig()
    old = open(sigp).read().strip() if os.path.exists(sigp) else ''
    if old != sig or A.force_front:
        # keep frames whose time is outside every changed component? simpler: re-render all on a change
        shutil.rmtree(out, ignore_errors=True)
    todo = [i for i in range(NF) if not os.path.exists(os.path.join(out, f'{i:05d}.png'))]
    if todo:
        log(f'front: capturing {len(todo)} of {NF} layer frames (3 processes)')
        t0 = time.time()
        capture(todo, out)
        log(f'front: done in {time.time() - t0:.0f}s')
    open(sigp, 'w').write(sig)


# ================================================================================== compose
def build_sequence():
    seq = os.path.join(WORK, 'seq')
    shutil.rmtree(seq, ignore_errors=True)
    os.makedirs(seq)
    front = os.path.join(WORK, 'front')
    for i in range(NF):
        src = os.path.join(front, f'{i:05d}.png')
        assert os.path.exists(src), f'missing layer frame {i}'
        if Image.open(src).mode != 'RGBA':
            Image.open(src).convert('RGBA').save(src, compress_level=1)
        os.link(src, os.path.join(seq, f'{i:05d}.png'))
    return seq


GRAPH = ('[0:v]scale=in_color_matrix=bt709:in_range=tv,format=gbrp,vignette=angle=0.55:mode=forward[b];'
         '[1:v]format=rgba[o];'
         '[b][o]overlay=format=gbrp:eof_action=pass:shortest=0,'
         'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]')


def st_compose(A):
    seq = build_sequence()
    os.makedirs(EXP, exist_ok=True)
    master = os.path.join(EXP, f'{NAME} - 1080x1920.mp4')
    nomus = os.path.join(EXP, f'{NAME} - NO MUSIC - 1080x1920.mp4')
    plog = os.path.join(WORK, 'x264pass')
    common = [FF, '-v', 'error', '-y', '-i', os.path.join(WORK, 'plate.mov'), '-framerate', '30000/1001', '-i', os.path.join(seq, '%05d.png')]
    venc = ['-map', '[v]', '-frames:v', str(NF), '-r', '30000/1001', '-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high',
            '-pix_fmt', 'yuv420p', '-b:v', '10.7M', '-maxrate', '16M', '-bufsize', '22M', '-passlogfile', plog,
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
            '-x264-params', 'keyint=60:min-keyint=30']
    t0 = time.time()
    log('compose: pass 1 / 2')
    sh(common + ['-filter_complex', GRAPH] + venc + ['-pass', '1', '-an', '-f', 'null', '-'])
    log(f'compose: pass 2 / 2 ({time.time() - t0:.0f}s so far)')
    sh(common + ['-i', os.path.join(WORK, 'mix.wav'), '-filter_complex', GRAPH] + venc +
       ['-pass', '2', '-map', '2:a', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2',
        '-movflags', '+faststart', '-metadata', 'title=Rally day (Egnyte) - Supercar Experience vlog v2', master])
    log(f'compose: master in {time.time() - t0:.0f}s')
    sh([FF, '-v', 'error', '-y', '-i', master, '-i', os.path.join(WORK, 'mix_nomusic.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart',
        '-metadata', 'title=Rally day (Egnyte) - Supercar Experience vlog v2 (no music)', nomus])
    mbps = os.path.getsize(master) * 8 / DUR / 1e6
    deliv = os.path.join(EXP, f'{NAME} - 1080x1920_DELIVERY.mp4')
    if mbps > 11.5:
        log(f'compose: master {mbps:.2f} Mb/s > 11.5 -> _DELIVERY copy')
        sh([FF, '-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'slow', '-b:v', '11.2M', '-pass', '1', '-passlogfile', plog + 'd', '-an', '-f', 'null', '-'])
        sh([FF, '-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'slow', '-b:v', '11.2M', '-pass', '2', '-passlogfile', plog + 'd',
            '-c:a', 'copy', '-movflags', '+faststart', deliv])
    elif os.path.exists(deliv):
        os.remove(deliv)
    shutil.copyfile(os.path.join(WORK, 'music_stem.wav'), os.path.join(EXP, f'{NAME} - music-stem.wav'))
    prev = os.path.join(EXP, f'{NAME} - PREVIEW 720x1280.mp4')
    pv = ['-vf', 'scale=720:1280:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '1.15M', '-maxrate', '2M', '-bufsize', '3M',
          '-pix_fmt', 'yuv420p', '-passlogfile', plog + 'p']
    sh([FF, '-v', 'error', '-y', '-i', master] + pv + ['-pass', '1', '-an', '-f', 'null', '-'])
    # the preview's audio: the same mix 0.5 dB lower, so the 160k AAC still holds -1.5 dBTP
    sh([FF, '-v', 'error', '-y', '-i', master, '-i', os.path.join(WORK, 'mix.wav')] + pv +
       ['-pass', '2', '-map', '0:v', '-map', '1:a', '-af', 'volume=-0.5dB', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', prev])
    log(f'compose: done in {time.time() - t0:.0f}s ({mbps:.2f} Mb/s master)')


# ================================================================================== QA
def decode_frames(path, idx):
    idx = sorted(set(idx))
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-vf', f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc",
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    assert len(arr) == len(idx), (len(arr), len(idx))
    return dict(zip(idx, arr))


def contact_sheet(frames, path, cols=8, tw=216, labels=None):
    th = int(tw * 16 / 9)
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new('RGB', (cols * tw, rows * (th + 16)), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for k, (i, img) in enumerate(frames):
        x, y = (k % cols) * tw, (k // cols) * (th + 16)
        sheet.paste(Image.fromarray(img).resize((tw, th), Image.LANCZOS), (x, y + 16))
        d.text((x + 3, y + 2), (labels or {}).get(i, f'f{i} {i / FPS:.2f}s'), fill=(251, 209, 1))
    sheet.save(path, quality=86)


def mp4_track_durations(path):
    b = open(path, 'rb').read()
    out, mts = [], [1000]
    def walk(off, end):
        while off < end:
            sz, typ = struct.unpack('>I4s', b[off:off + 8]); hh = 8
            if sz == 1:
                sz, hh = struct.unpack('>Q', b[off + 8:off + 16])[0], 16
            typ = typ.decode('latin1')
            if typ in ('moov', 'trak', 'edts'):
                walk(off + hh, off + sz)
            elif typ == 'mvhd':
                mts[0] = struct.unpack('>I', b[off + 20:off + 24])[0]
            elif typ == 'elst':
                v = b[off + 8]
                sd = struct.unpack('>I' if v == 0 else '>Q', b[off + 16:off + (20 if v == 0 else 24)])[0]
                out.append(round(sd / mts[0], 4))
            off += sz
    walk(0, len(b))
    return out


def audio_qa(path):
    err = subprocess.run([FF, '-hide_banner', '-nostats', '-i', path, '-map', '0:a', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    ln = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', err, re.S).group(0))
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-map', '0:a', '-f', 'f32le', '-ac', '2', '-ar', '48000', '-'], capture_output=True, check=True).stdout
    au = np.frombuffer(raw, '<f4').reshape(-1, 2)
    nz = np.where(np.abs(au).max(1) > 1e-6)[0]
    return dict(I=float(ln['input_i']), TP=float(ln['input_tp']), LRA=float(ln['input_lra']),
                trailing_silence_ms=round(1000 * (len(au) - 1 - nz[-1]) / 48000, 1), last_50ms_peak=float(np.abs(au[-2400:]).max()),
                audio_s=round(len(au) / 48000, 4))


def ink_audit(times):
    js = os.path.join(WORK, 'audit.js')
    open(js, 'w').write("""
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
(async () => { const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto('file://' + process.argv[2]); await pg.waitForFunction(() => window.__ktReady === true, null, { timeout: 60000 });
  const ts = JSON.parse(process.argv[3]); const out = {};
  for (const t of ts) out[t] = await pg.evaluate(t => window.inkAudit(t), t);
  console.log(JSON.stringify(out)); await b.close(); })();
""")
    r = subprocess.run([NODE, js, os.path.join(ROOT, 'story.html'), json.dumps(times)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def caption_sync(n=10):
    """caption timing vs the audio actually in the mix. (1) per caption piece: the lag (-300..+300 ms) that best aligns the
    caption word mask with the speech-band energy of the dialog stem; (2) n spot words after a pause: speech-band level
    inside the word minus the 150 ms before it (positive = the word starts where the caption says)."""
    import synth as SY
    raw = subprocess.run([FF, '-v', 'error', '-i', os.path.join(WORK, 'stem_dialog.wav'), '-f', 'f32le', '-ac', '1', '-ar', '48000', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, '<f4').astype(np.float64)
    x = SY.fft_filter(x, lo=300, hi=3400, slope=3)
    hop = 480
    env = np.array([np.sqrt((x[k:k + hop] ** 2).mean()) for k in range(0, len(x) - hop, hop)])
    edb = 20 * np.log10(env + 1e-9)
    pieces = []
    for piece in CAPS + C['captions'].get('extra', []):
        ws = [w for w in piece['words']]
        if len(ws) < 3:
            continue
        a0, a1 = ws[0][0] - 0.4, ws[-1][1] + 0.4
        i0, i1 = int(a0 * 100), int(a1 * 100)
        m = np.zeros(i1 - i0)
        for w0, w1, _ in ws:
            m[max(0, int(w0 * 100) - i0):max(0, int(w1 * 100) - i0) + 1] = 1
        best = None
        for lag in range(-30, 31):
            seg = edb[i0 + lag:i1 + lag]
            if len(seg) != len(m):
                continue
            c = np.corrcoef(seg, m)[0, 1]
            if best is None or c > best[1]:
                best = (lag, c)
        pieces.append(dict(t=piece['t'], src=piece['src'], lag_ms=best[0] * 10, corr=round(float(best[1]), 2)))
    words = caption_words()
    cand = [w for p_, w in zip(words, words[1:]) if w[0] - p_[1] >= 0.3]
    pick = [cand[int(i)] for i in np.linspace(0, len(cand) - 1, min(n, len(cand)))]
    spots = []
    for a, b, w in pick:
        ins = edb[int(a * 100):int(max(b, a + 0.12) * 100)]
        pre = edb[int((a - 0.15) * 100):int(a * 100)]
        spots.append(dict(word=w, t=a, word_minus_pre_db=round(float(ins.mean() - pre.mean()), 1)))
    lags = [p['lag_ms'] for p in pieces]
    return dict(pieces=pieces, median_lag_ms=float(np.median(lags)), max_abs_lag_ms=int(max(abs(l) for l in lags)), spot_words=spots)


def write_cue():
    """cue.md: every transition, element, track, blur, sound cue and dialog piece, generated from the build's own data."""
    import plate as PL
    L = []
    w = L.append
    w('# Cue sheet: rally vlog v2 (generated by `build.py --stage qa`; edit config.json, not this file)\n')
    w(f'Timeline: {NF} frames at 30000/1001 fps = {DUR:.3f} s. Frame n is shown at n x 1001/30000 s.\n')
    w('## Picture: shots, reframe, look, transitions\n')
    w('| # | t (s) | frames | clip | source in-out | look | reframe | into it |')
    w('|---|---|---|---|---|---|---|---|')
    trans = {t['into']: t for t in C['transitions']}
    for k, f0, f1 in PL.FR:
        s = PL.SHOTS[k]; c = PL.scfg(k)
        if s['src'] == 'card':
            w(f'| {k} | {s["t"]:.2f} | {f0}-{f1 - 1} | end card | | | the last shot runs {C["endCard"]["plateRun"]} s under the card wipe, then black | |'); continue
        ts = PL.src_times(k)
        rf = 'keys ' + ' '.join(f'{q[0]:.1f}s:{q[1]:.0f}' for q in c['keys']) + f' (s {c["keys"][0][3]})' if c.get('keys') else f'c {c.get("c0", "centre")} s {c.get("s0", 1.0)}-{c.get("s1", c.get("s0", 1.0))}'
        tr = trans.get(k)
        trs = '' if not tr else f'{tr["type"]}' + (f' {tr.get("dir", "")}' if tr['type'] == 'whip' else '') + (f' {tr["dur"]} s' if tr['type'] == 'sweep' else '')
        sp = 'timelapse' if s['speed'] == 'keyframes' else ('ramp ' + ' '.join(f'{a:.2f}:{b}' for a, b in c['ramp'])) if c.get('ramp') else f'{s["speed"]:g}x'
        if 'edl_in' in s:
            sp += f', slipped from the EDL {s["edl_in"]:.2f} s at {s["edl_speed"]:g}x (config `slips`)'
        w(f'| {k} | {s["t"]:.2f} | {f0}-{f1 - 1} | {s["src"]} | {ts[0][0]:.2f}-{ts[-1][0]:.2f} ({sp}) | {c["look"]} | {rf} | {trs} |')
    w('\n## Layer elements\n')
    w('| code | type | in | out | what |')
    w('|---|---|---|---|---|')
    for c in C['layer']['comps']:
        p = c.get('p', {})
        what = p.get('title') or p.get('name') or p.get('word') or p.get('line1') or p.get('label') or p.get('header') or p.get('kicker') or ''
        extra = ''
        if c['type'] == 'convoyHop':
            extra = ' / '.join(f'{s["make"]} @{s["t"]}' for s in p['segs'])
        elif c['type'] in ('v2route', 'v2routeCard'):
            extra = ' → '.join(p['waypoints']) + ' | first ' + str(p.get('firstAt')) + ' | steps ' + ', '.join(f'{st["k"]}@{st["t"]}' for st in p['steps'])
        elif c['type'] == 'v2wall':
            extra = ', '.join(f'{it["w"]}@{it["t"]}' for it in p['items'])
        elif c['type'] in ('v2lock', 'leadLock', 'personLock'):
            extra = f'track {p.get("track")}, acquire {p.get("acquire")}, exit {p.get("exit")}'
        elif c['type'] == 'chapterSlam':
            extra = p.get('tag', '')
        w(f'| {c["code"]} | {c["type"]} | {c["t0"]:.2f} | {c["t1"]:.2f} | {what} {extra} |')
    cp = C['layer']['captions']
    w(f'| H1 | captionsBox | {cp["t0"]} | {cp["t1"]} | every caption word; hidden: ' + '; '.join(f'{h[0]}-{h[1]} ({h[2]})' for h in C['captions']['hide']) + ' |')
    tp = os.path.join(LIB, 'data', 'tracks.json')
    if os.path.exists(tp):
        T = json.load(open(tp))
        w('\n## Tracks (lib/track_mid.py from a sharp anchor frame, both ways; output frames, output px)\n')
        w('| name | shot | frames | anchor | box on the anchor | NCC min / mean |')
        w('|---|---|---|---|---|---|')
        for n, r in T.items():
            nc = [f.get('ncc', f['conf']) for f in r['frames']]
            b = C['tracks'].get(n, {}).get('box')
            w(f'| {n} | {r.get("shot")} | {r["f0"]}-{r["f1"]} | {r.get("anchor")} | {b} | {min(nc):.2f} / {sum(nc) / len(nc):.2f} |')
    if C.get('blurs'):
        w('\n## Licence-plate blurs\n')
        for b in C['blurs']:
            w(f'- `{b["track"]}` (pad {b.get("pad")} px, radius {b.get("radius")} px)')
    mj = os.path.join(WORK, 'mix.json')
    if os.path.exists(mj):
        M = json.load(open(mj))
        w('\n## Sound\n')
        w(f'Music: {M["music"]["source"]} ({M["music"].get("bpm")} BPM, first downbeat {M["music"].get("downbeat0")} s), enabled: {M.get("music_enabled")}. '
          f'Master {M["master"]["lufs"]} LUFS, true peak {M["master"]["true_peak_db"]} dBTP (numpy BS.1770 on the wav; the mp4 is measured in exports/qa/qa_summary.json).\n')
        w('| dialog piece | clip | source | at | loudness in | gain | music under it (duck, dialog over music) |')
        w('|---|---|---|---|---|---|---|')
        dc = {d['i']: d for d in M.get('duck_check', [])}
        for d in M['dialog']:
            k = dc.get(d['i'], {})
            w(f'| {d["i"]} | {d["src"]} | {d["a"]}-{d["b"]} | {d["t"]} | {d["lufs_in"]} LUFS | {d["gain_db"]:+.1f} dB | {k.get("duck_db", "")} dB, {k.get("dialog_over_music_db", "")} dB |')
        w('\n| nat | source | at | gain |')
        w('|---|---|---|---|')
        for d in M['nat']:
            w(f'| {d["src"]} | {d["a"]}-{d["b"]} | {d["t"]} | {d["gain_db"]:+.1f} dB |')
        w('\n| SFX | at | why | gain (incl. dialog duck) |')
        w('|---|---|---|---|')
        for d in M['sfx']:
            w(f'| {d["file"]} | {d["t"]} | {d["why"]} | {d["gain_db"]:+.1f} dB ({d["duck"]:+.1f}) |')
    open(os.path.join(ROOT, 'cue.md'), 'w').write('\n'.join(L) + '\n')


def st_qa(A):
    write_cue()
    import plate as PL
    master = os.path.join(EXP, f'{NAME} - 1080x1920.mp4')
    os.makedirs(QA, exist_ok=True)
    for f in os.listdir(QA):
        if f.startswith('beat_') or f.startswith('el_'):
            os.remove(os.path.join(QA, f))
    # per-beat first / mid / last
    marks = {}
    for b in EDL['beats']:
        f0, f1 = int(round(b['t0'] * FPS)), min(NF, int(round(b['t1'] * FPS)))
        for nm, i in (('first', f0), ('mid', (f0 + f1 - 1) // 2), ('last', f1 - 1)):
            marks[i] = f'beat{b["i"]:02d}_{b["ch"]}_{nm}'
    for c in C['layer']['comps']:
        if c['type'] in ('bannerTab', 'sweep'):
            continue
        t0, t1 = c['t0'], c['t1']
        a = c.get('p', {}).get('acquire', t0)
        for nm, t in (('in', a + min(0.6, (t1 - a) / 3)), ('mid', (a + t1) / 2), ('out', t1 - 0.2)):
            marks[int(round(t * FPS))] = f'el_{c["code"]}_{nm}'
    for nm, t in C['qa']['moments'].items():
        marks[int(round(t * FPS))] = 'el_' + nm
    fr = decode_frames(master, list(marks))
    for i, nm in marks.items():
        pre = 'beat_' if nm.startswith('beat') else ''
        Image.fromarray(fr[i]).save(os.path.join(QA, f'{pre}{nm}_f{i:05d}_{i / FPS:07.3f}s.jpg'), quality=80)
    Image.fromarray(fr[0] if 0 in fr else decode_frames(master, [0])[0]).save(os.path.join(EXP, 'poster.jpg'), quality=94)
    beat_frames = sorted(i for i, nm in marks.items() if nm.startswith('beat'))
    contact_sheet([(i, fr[i]) for i in beat_frames], os.path.join(QA, 'beats-sheet.jpg'), cols=9, tw=200,
                  labels={i: marks[i].replace('beat', 'b') for i in beat_frames})
    el_frames = sorted(i for i, nm in marks.items() if nm.startswith('el_'))
    contact_sheet([(i, fr[i]) for i in el_frames], os.path.join(QA, 'elements-sheet.jpg'), cols=8, tw=216,
                  labels={i: marks[i][3:] + f' {i / FPS:.2f}' for i in el_frames})
    cs = sorted(set(list(range(0, NF, 60)) + [NF - 1]))
    dec = decode_frames(master, cs)
    contact_sheet([(i, dec[i]) for i in cs], os.path.join(EXP, 'contact-sheet.jpg'), cols=11, tw=180)
    # audio, container
    res = dict(file=os.path.basename(master), bytes=os.path.getsize(master), MB=round(os.path.getsize(master) / 1e6, 2),
               MiB=round(os.path.getsize(master) / 2 ** 20, 2), mbps=round(os.path.getsize(master) * 8 / DUR / 1e6, 3),
               frames=NF, picture_s=round(NF / FPS, 4), track_durations_s=mp4_track_durations(master), audio=audio_qa(master))
    others = {}
    for fn in sorted(os.listdir(EXP)):
        if fn.endswith('.mp4') and fn != os.path.basename(master):
            p = os.path.join(EXP, fn)
            others[fn] = dict(MiB=round(os.path.getsize(p) / 2 ** 20, 2), track_durations_s=mp4_track_durations(p), audio=audio_qa(p))
    res['other_exports'] = others
    probe = subprocess.run([FF, '-hide_banner', '-i', master], capture_output=True, text=True).stderr
    res['stream_lines'] = [l.strip() for l in probe.splitlines() if 'Stream #' in l or 'Duration' in l]
    # safe-zone ink audit: every 0.5 s
    ts = [round(x, 3) for x in np.arange(0.02, DUR, 0.5)]
    aud = ink_audit(ts)
    SAFE = dict(x0=54, y0=269, x1=907, y1=1536)
    bad = []
    for t, items in aud.items():
        for it in items:
            if it['type'] in ('v2end',) or it['code'] in C['qa'].get('bannerCodes', []):
                continue
            if it['x0'] < SAFE['x0'] - 1 or it['x1'] > SAFE['x1'] + 1 or it['y0'] < SAFE['y0'] - 1 or it['y1'] > SAFE['y1'] + 1:
                bad.append(dict(t=t, text=it['text'][:40], code=it['code'], box=[round(it['x0']), round(it['y0']), round(it['x1']), round(it['y1'])]))
    res['safe_zone'] = dict(checked_times=len(ts), outside=bad[:40], n_outside=len(bad))
    res['caption_sync'] = caption_sync()
    # every shot's first / middle / last frame from the delivered file: sheet + luma (grade consistency)
    sidx, slab = [], {}
    for k, f0, f1 in PL.FR:
        for nm, i in (('in', f0 + 2), ('mid', (f0 + f1) // 2), ('out', f1 - 3)):
            i = min(max(i, f0), f1 - 1); sidx.append(i); slab[i] = f'{k:02d} {PL.SHOTS[k]["src"]} {nm}'
    sfr = decode_frames(master, sidx)
    contact_sheet([(i, sfr[i]) for i in sorted(set(sidx))], os.path.join(QA, 'shots-sheet.jpg'), cols=12, tw=150, labels=slab)
    lum = {}
    for k, f0, f1 in PL.FR:
        vals = []
        for i in sorted(set(q for q in sidx if f0 <= q < f1)):
            a = sfr[i][300:1550:4, 60:1000:4].astype(np.float32) / 255
            y = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
            vals.append([round(float(y.mean()), 3), round(float(np.median(y)), 3), round(float((y < 0.02).mean()), 3), round(float((y > 0.98).mean()), 3)])
        lum[f'{k:02d} {PL.SHOTS[k]["src"]} {PL.scfg(k)["look"] if PL.SHOTS[k]["src"] != "card" else "card"}'] = vals
    res['shot_luma_mean_median_crushed_clipped'] = lum
    json.dump(res, open(os.path.join(QA, 'qa_summary.json'), 'w'), indent=1)
    log(f"qa: {res['MB']} MB {res['mbps']} Mb/s, durations {res['track_durations_s']}, audio {res['audio']}, safe-zone outside {len(bad)}")


# ================================================================================== stills (dev)
def stills(A, idx):
    out = os.path.join(WORK, 'stills')
    os.makedirs(out, exist_ok=True)
    for i in idx:
        q = os.path.join(out, f'{i:05d}.png')
        if os.path.exists(q):
            os.remove(q)
    capture(idx, out, nproc=1)
    if os.path.exists(os.path.join(WORK, 'plate.mov')) and not A.from_shots:
        src = decode_frames(os.path.join(WORK, 'plate.mov'), idx)
    else:                                   # before the join: the rendered shot files (no transitions / blurs)
        import plate as PL
        src = {}
        for i in idx:
            k = [k for k, f0, f1 in PL.FR if f0 <= i < f1][0]
            f0 = PL.FR[k][1]
            p_ = os.path.join(WORK, 'shots', f'{k:02d}.mov')
            if PL.SHOTS[k]['src'] == 'card' or not os.path.exists(p_):
                src[i] = np.full((H, W, 3), 60, np.uint8); continue
            src[i] = decode_frames(p_, [i - f0])[i - f0]
    for i in idx:
        base = src[i].astype(np.float32) / 255
        o = np.asarray(Image.open(os.path.join(out, f'{i:05d}.png')).convert('RGBA'), np.float32) / 255
        a = o[..., 3:4]
        Image.fromarray((np.clip(o[..., :3] * a + base * (1 - a), 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(out, f'c{i:05d}.jpg'), quality=90)
    log('stills ->', out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stage', default='shots,track,join,prep,audio,front,compose,qa')
    ap.add_argument('--stills')
    ap.add_argument('--tracks')
    ap.add_argument('--from-shots', action='store_true')
    ap.add_argument('--recapture')
    ap.add_argument('--force-front', action='store_true')
    A = ap.parse_args()
    if A.stills:
        st_prep(A); stills(A, [int(x) for x in A.stills.split(',')]); return
    if A.recapture:
        # targeted re-capture after a change that only touches these frames (a..b inclusive, comma list of ranges);
        # the layer signature is then updated so the front stage keeps every other frame
        st_prep(A)
        fr = []
        for r in A.recapture.split(','):
            a, b = (int(v) for v in r.split('-'))
            fr += list(range(a, b + 1))
        out = os.path.join(WORK, 'front')
        for i in fr:
            q = os.path.join(out, f'{i:05d}.png')
            if os.path.exists(q):
                os.remove(q)
        capture(fr, out)
        open(os.path.join(WORK, 'front.sig'), 'w').write(front_sig())
        log(f'recaptured {len(fr)} frames'); return
    st = A.stage.split(',')
    for name, fn in (('shots', st_shots), ('track', st_track), ('join', st_join), ('prep', st_prep), ('audio', st_audio),
                     ('front', st_front), ('compose', st_compose), ('qa', st_qa)):
        if name in st:
            fn(A)


if __name__ == '__main__':
    main()
