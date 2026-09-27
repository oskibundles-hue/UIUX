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
TIMES = {}


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
    comps = [json.loads(json.dumps(c)) for c in L['comps']]      # deep copy: the gates may adjust a component
    cp = dict(L['captions'])
    comps.append(dict(code='H1', type='captionsBox', t0=cp['t0'], t1=cp['t1'], p=dict(cp['p'], words=caption_words())))
    # lock-on gate: a lock whose car leaves the frame (or loses track) while it is shown is released automatically
    import gates as G
    tp = os.path.join(LIB, 'data', 'tracks.json')
    comps, rep = G.lock_gate(comps, json.load(open(tp)) if os.path.exists(tp) else {}, FPS)
    GATES[:] = [g for g in GATES if g.get('gate') != 'lock'] + [dict(g, gate='lock') for g in rep]
    # quote card words (Omarie, verbatim, timeline times from captions.json)
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
            cue('whooshRL', t0 + 0.1, "quote card (Omarie's pick) in", -6)
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
def _shot_sig(k):
    p = os.path.join(WORK, 'shots', f'{k:02d}.mov.sig')
    return open(p).read() if os.path.exists(p) else 'missing'


def _cached(name, sig, outputs):
    """True when stage `name` already ran on exactly these inputs and its outputs exist (.work/stage_<name>.sig)."""
    sp = os.path.join(WORK, f'stage_{name}.sig')
    return os.path.exists(sp) and open(sp).read() == sig and all(os.path.exists(o) for o in outputs)


def _done(name, sig):
    open(os.path.join(WORK, f'stage_{name}.sig'), 'w').write(sig)


def st_shots(A):
    sh([sys.executable, os.path.join(LIB, 'plate.py'), 'shots'])      # per-shot signatures inside plate.py


def join_sig():
    import plate as PL
    tp = os.path.join(LIB, 'data', 'tracks.json')
    T = json.load(open(tp)) if os.path.exists(tp) else {}
    bt = {b['track']: T.get(b['track'], {}).get('frames') for b in C.get('blurs', [])}
    blob = json.dumps([[_shot_sig(k) for k, _, _ in PL.FR if PL.SHOTS[k]['src'] != 'card'], C['transitions'], C.get('slams'), C['endCard'],
                       C.get('blurs', []), bt, EDL['duration'], [(s['src'], s['t'], s['dur']) for s in PL.SHOTS]], sort_keys=True)
    return _hash(os.path.join(LIB, 'plate.py'), os.path.join(LIB, 'fx.py'), extra=blob)


def st_join(A):
    sig = join_sig()
    if _cached('join', sig, [os.path.join(WORK, 'plate.mov')]):
        log('join: plate unchanged (cached)'); TIMES['join'] = dict(cached=True); return
    sh([sys.executable, os.path.join(LIB, 'plate.py'), 'join'])
    _done('join', sig)


def audio_sig():
    slot = os.path.join(ROOT, C['music']['file'])
    blob = json.dumps([C['audio'], C['music'], C['master'], C['sfx'], C['layer'].get('testimonial'), EDL['dialog'], EDL.get('audio_extra'),
                       os.environ.get('MUSIC', '1'), DUR], sort_keys=True)
    cues = os.path.join(WORK, 'sfx_cues.json')
    return _hash(os.path.join(LIB, 'mix.py'), os.path.join(LIB, 'synth.py'), os.path.join(LIB, 'music.py'), cues,
                 extra=blob + _files_sig([slot, C['paths']['mezz'], os.path.join(WORK, 'mezz_extra'), C['paths']['transcripts'],
                                          os.path.join(ROOT, C['paths']['sfx'])]))


def st_audio(A):
    sig = audio_sig()
    outs = [os.path.join(WORK, f) for f in ('mix.wav', 'mix_nomusic.wav', 'music_stem.wav', 'stem_dialog.wav', 'meter.json', 'mix.json')]
    if not _cached('audio', sig, outs):
        if not os.path.exists(os.path.join(ROOT, C['music']['file'])):
            mw = os.path.join(WORK, 'music_synth.wav')
            if not os.path.exists(mw) or os.path.getmtime(mw) < os.path.getmtime(os.path.join(LIB, 'music.py')):
                sh([sys.executable, os.path.join(LIB, 'music.py'), '--out', mw, '--sync', os.path.join(WORK, 'music_synth.json'), '--dur', f'{DUR:.4f}'])
        sh([sys.executable, os.path.join(LIB, 'mix.py')])
        _done('audio', sig)
    else:
        log('audio: mix unchanged (cached)'); TIMES['audio'] = dict(cached=True)
    mp = os.path.join(WORK, 'meter.json')
    ld = 'window.LAYERDATA=' + json.dumps({'meter': json.load(open(mp))}) + ';\n'
    lp = os.path.join(WORK, 'layerdata.js')
    if not os.path.exists(lp) or open(lp).read() != ld:
        open(lp, 'w').write(ld)


def st_track(A):
    plate = os.path.join(WORK, 'plate.mov')
    out = os.path.join(LIB, 'data', 'tracks.json')
    os.makedirs(os.path.join(LIB, 'data'), exist_ok=True)
    os.makedirs(QA, exist_ok=True)
    only = A.tracks.split(',') if A.tracks else None
    import plate as PL
    code = _hash(os.path.join(LIB, 'track_mid.py'), os.path.join(LIB, 'trackqa.py'))
    n_run = 0
    for name, t in C['tracks'].items():
        if name.startswith('_') or (only and name not in only):
            continue
        sig = hashlib.sha1(json.dumps([t, _shot_sig(t['shot']), PL.FR[t['shot']][1], code], sort_keys=True).encode()).hexdigest()[:16]
        db = json.load(open(out)) if os.path.exists(out) else {}
        if not only and db.get(name, {}).get('sig') == sig and os.path.exists(os.path.join(QA, f'track_{name}.jpg')):
            continue                                   # this track's inputs are unchanged
        n_run += 1
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
        r['sig'] = sig
        db = json.load(open(out)) if os.path.exists(out) else {}
        db[name] = r
        json.dump(db, open(out, 'w'), indent=1)
    if not n_run:
        log('track: all tracks unchanged (cached)')


# ================================================================================== gates
GATES = []


def st_gates(A):
    """automatic checks BEFORE the render (lib/gates.py). The lock-on gate already ran inside prep (build_scene), where it
    releases a lock whose car leaves the frame; here: the swap check, the shot scan, captions, loudness, quote cards.
    Errors stop a full render (unless --force); warnings and checks are listed for the reviewer."""
    import gates as G, plate as PL
    t0 = time.time()
    out = list(GATES)
    sc = os.path.join(WORK, 'swapcheck.json')
    sh([NODE, os.path.join(LIB, 'swapcheck.js'), os.path.join(ROOT, 'story.html'), sc], stdout=subprocess.DEVNULL)
    r = json.load(open(sc))
    for b in r['bad']:
        out.append(dict(level='error', what=f"swap check: frame {b['n']} ({b['t']} s) mixes two texts: {b['states'][:2]}"))
    sigs = {k: _shot_sig(k) for k, _, _ in PL.FR if PL.SHOTS[k]['src'] != 'card'}
    out += G.shot_scan(FF, os.path.join(WORK, 'shots'), PL.FR, PL.SHOTS, sigs, os.path.join(WORK, 'shotscan.json'))
    if os.path.exists(os.path.join(WORK, 'stem_dialog.wav')):
        out += G.caption_gate(caption_sync())
    mj = os.path.join(WORK, 'mix.json')
    if os.path.exists(mj):
        m = json.load(open(mj))['master']
        out += G.loud_gate('mix', m['lufs'], m['true_peak_db'], tp_max=-1.9)       # the limiter ceiling is -2.0 before AAC
        out += G.loud_gate('mix (no music)', m['nomusic_lufs'], m['nomusic_true_peak_db'], tp_max=-1.9)
    scene = json.loads(open(os.path.join(WORK, 'scene.js')).read()[len('window.SCENE='):-2])
    out += G.quote_gate(scene['comps'], CAPS)
    json.dump(out, open(os.path.join(WORK, 'gates.json'), 'w'), indent=1)
    os.makedirs(QA, exist_ok=True)
    lines = ['# Gates (build.py, before the render)\n', f'{time.strftime("%Y-%m-%d %H:%M")}; errors stop a full render, the rest is for the reviewer.\n']
    for lvl in ('error', 'auto', 'warn', 'check'):
        for g in out:
            if g['level'] == lvl:
                lines.append(f"- **{lvl}** {g.get('code', '')} {g['what']}")
    if len(lines) == 2:
        lines.append('- all clear')
    open(os.path.join(QA, 'gates.md'), 'w').write('\n'.join(lines) + '\n')
    n = {l: sum(g['level'] == l for g in out) for l in ('error', 'auto', 'warn', 'check')}
    log(f"gates: {n['error']} errors, {n['auto']} auto-fixes, {n['warn']} warnings, {n['check']} human checks ({time.time() - t0:.0f}s) -> exports/qa/gates.md")
    for g in out:
        if g['level'] in ('error', 'auto', 'warn'):
            log(f"  {g['level']}: {g.get('code', '')} {g['what']}")
    TIMES['gates'] = dict(n, s=round(time.time() - t0, 1))
    if n['error'] and not getattr(A, 'force', False):
        raise SystemExit('gates: errors (see exports/qa/gates.md); fix them or run with --force')


# ================================================================================== front
NPROC = int(os.environ.get('NPROC', '4'))            # capture / hash processes (4 cores)


def _files_sig(paths):
    h = hashlib.sha1()
    for p in paths:
        if os.path.isdir(p):
            for fn in sorted(os.listdir(p)):
                q = os.path.join(p, fn); st = os.stat(q); h.update(f'{fn}:{st.st_size}:{int(st.st_mtime)}|'.encode())
        elif os.path.exists(p):
            h.update(open(p, 'rb').read())
        h.update(b'#')
    return h.hexdigest()[:16]


def capture_salt():
    """what can change a layer frame's pixels without changing its DOM state: the capture code, the fonts, the logos."""
    return _files_sig([os.path.join(LIB, 'kcap2.js'), os.path.join(LIB, 'accum2.py'), os.path.join(ROOT, '..', '..', '07-fonts'),
                       os.path.join(ROOT, '..', '..', '02-logos', 'png')])


def _chunks(seq, n):
    """n interleaved chunks (the motion-blur frames cluster in time, interleaving balances the processes)."""
    return [c for c in (seq[k::n] for k in range(n)) if c]


def _run_kcap(args_per_proc, logname):
    procs = []
    for k, a in enumerate(args_per_proc):
        procs.append(subprocess.Popen(['nice', '-n', '5', NODE, os.path.join(LIB, 'kcap2.js')] + a,
                                      stderr=open(os.path.join(WORK, f'{logname}_{k}.log'), 'w')))
    for p in procs:
        p.wait()
        assert p.returncode == 0, f'kcap2 failed, see .work/{logname}_*.log'


def frame_hashes(frames=None, draft=False):
    """the layer state of every frame (all component DOM at every motion-blur sample) -> {frame: hash}."""
    frames = list(range(NF)) if frames is None else frames
    extra = ['--scale', '0.5', '--k1'] if draft else []
    parts = []
    args = []
    for k, ch in enumerate(_chunks(frames, NPROC)):
        lf = os.path.join(WORK, f'hash_in_{k}.json'); of = os.path.join(WORK, f'hash_out_{k}.json')
        json.dump(ch, open(lf, 'w')); parts.append(of)
        args.append([os.path.join(ROOT, 'story.html'), WORK, 'hash', '30000/1001', lf, of] + extra)
    _run_kcap(args, 'hash')
    salt = capture_salt()
    out = {}
    for of in parts:
        for n, h in json.load(open(of)).items():
            out[int(n)] = hashlib.sha1(f'{h}|{salt}'.encode()).hexdigest()[:20]
    return out


def capture(frames, outdir, draft=False):
    """capture these frames into outdir/NNNNN.png (kcap2: order-independent pixels, NPROC processes)."""
    os.makedirs(outdir, exist_ok=True)
    if not frames:
        return
    rt = os.path.join(outdir, '_retry.txt')
    if os.path.exists(rt):
        os.remove(rt)
    extra = ['--scale', '0.5', '--k1', '--noreset'] if draft else ['--noclip']      # drafts skip the compositor reset (speed)
    args = []
    for k, ch in enumerate(_chunks(sorted(frames), NPROC)):
        lf = os.path.join(WORK, f'frames_{k}.json'); json.dump(ch, open(lf, 'w'))
        args.append([os.path.join(ROOT, 'story.html'), outdir, 'list', '30000/1001', lf] + extra)
    _run_kcap(args, 'capture')
    if os.path.exists(rt):                          # clipped frames with ink on the clip border: again, full size
        again = sorted({int(x) for x in open(rt).read().split()}); os.remove(rt)
        lf = os.path.join(WORK, 'frames_retry.json'); json.dump(again, open(lf, 'w'))
        _run_kcap([[os.path.join(ROOT, 'story.html'), outdir, 'list', '30000/1001', lf, '--noclip']], 'capture_retry')


def st_front(A):
    """incremental layer capture: only frames whose layer-state hash changed since the last capture are rendered;
    frames with identical state are rendered once and hard-linked."""
    draft = getattr(A, 'draft', False)
    out = os.path.join(WORK, 'front_draft' if draft else 'front')
    idxp = os.path.join(out, 'index.json')
    t0 = time.time()
    hs = frame_hashes(draft=draft)
    th = time.time() - t0
    old = {} if A.force_front or not os.path.exists(idxp) else {int(k): v for k, v in json.load(open(idxp)).items()}
    have = {}                                        # hash -> an existing frame file with that state
    for n, h in old.items():
        if os.path.exists(os.path.join(out, f'{n:05d}.png')):
            have.setdefault(h, n)
    todo = [n for n in range(NF) if old.get(n) != hs[n] or not os.path.exists(os.path.join(out, f'{n:05d}.png'))]
    reps, links = {}, []
    for n in todo:
        h = hs[n]
        if h in have and old.get(have[h]) == h and have[h] not in todo:
            links.append((n, have[h]))
        elif h in reps:
            links.append((n, reps[h]))
        else:
            reps[h] = n
    os.makedirs(out, exist_ok=True)
    # the index is invalidated for the frames about to change (a crash mid-capture leaves them marked stale)
    for n in todo:
        old.pop(n, None)
    json.dump({str(k): v for k, v in sorted(old.items())}, open(idxp, 'w'))
    t1 = time.time()
    capture(sorted(reps.values()), out, draft=draft)
    for n, src in links:
        dst = os.path.join(out, f'{n:05d}.png')
        if os.path.exists(dst):
            os.remove(dst)
        os.link(os.path.join(out, f'{src:05d}.png'), dst)
    json.dump({str(n): hs[n] for n in range(NF)}, open(idxp, 'w'))
    log(f'front{" (draft)" if draft else ""}: {len(todo)} of {NF} frames changed -> {len(reps)} captured, {len(links)} linked '
        f'(hash {th:.0f}s, capture {time.time() - t1:.0f}s, {NPROC} processes)')
    TIMES['front'] = dict(changed=len(todo), captured=len(reps), hash_s=round(th, 1), capture_s=round(time.time() - t1, 1))


# ================================================================================== compose
# The master is encoded in SEG-frame segments (IDR at every segment start). Each segment's inputs are hashed (its layer
# frames' state hashes + the plate packets of the GOPs it decodes from + the encoder settings); only segments whose hash
# changed are re-encoded, then all segments are joined by stream copy and muxed with the audio (AAC encoded once per
# mix). The 720x1280 preview is encoded in the same ffmpeg process from the same composite (split), and the NO MUSIC
# master is the same video stream muxed with the no-music mix (no second video encode).
SEG = 120
GRAPH = ('[0:v]scale=in_color_matrix=bt709:in_range=tv,format=gbrp,vignette=angle=0.55:mode=forward:eval=init[b];'
         '[1:v]format=rgba[o];'
         '[b][o]overlay=format=gbrp:eof_action=pass:shortest=0,'
         'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]')
# vignette eval=init: the vignette has no time-varying parameter, so its gain map is computed once instead of per frame
# (identical pixels, checked by md5 of the composite)
VENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-maxrate', '16M', '-bufsize', '22M', '-profile:v', 'high',
        '-pix_fmt', 'yuv420p', '-x264-params', 'keyint=60:min-keyint=30', '-colorspace', 'bt709', '-color_primaries', 'bt709',
        '-color_trc', 'bt709', '-color_range', 'tv']
PENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '27', '-maxrate', '2M', '-bufsize', '3M', '-pix_fmt', 'yuv420p',
        '-x264-params', 'keyint=60:min-keyint=30', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
ENC_SIG = hashlib.sha1(json.dumps([SEG, GRAPH, VENC, PENC, 'v1']).encode()).hexdigest()[:12]


def build_sequence(front=None):
    seq = os.path.join(WORK, 'seq' if front is None else 'seq_draft')
    shutil.rmtree(seq, ignore_errors=True)
    os.makedirs(seq)
    front = front or os.path.join(WORK, 'front')
    for i in range(NF):
        src = os.path.join(front, f'{i:05d}.png')
        assert os.path.exists(src), f'missing layer frame {i}'
        os.link(src, os.path.join(seq, f'{i:05d}.png'))
    return seq


def mp4_sync_samples(path):
    """1-based decode-order numbers of the sync samples (stss) of the first video track of an MP4/MOV."""
    f = open(path, 'rb')
    size_all = os.path.getsize(path)
    def boxes(off, end):
        while off + 8 <= end:
            f.seek(off); sz, typ = struct.unpack('>I4s', f.read(8)); hl = 8
            if sz == 1:
                sz = struct.unpack('>Q', f.read(8))[0]; hl = 16
            elif sz == 0:
                sz = end - off
            yield typ, off + hl, off + sz
            off += sz
    for typ, a, b in boxes(0, size_all):
        if typ != b'moov':
            continue
        for t2, a2, b2 in boxes(a, b):
            if t2 != b'trak':
                continue
            vide, stss = False, None
            def walk(a, b):
                nonlocal vide, stss
                for t3, a3, b3 in boxes(a, b):
                    if t3 in (b'mdia', b'minf', b'stbl'):
                        walk(a3, b3)
                    elif t3 == b'hdlr':
                        f.seek(a3 + 8); vide = f.read(4) == b'vide'
                    elif t3 == b'stss':
                        f.seek(a3 + 4); n = struct.unpack('>I', f.read(4))[0]
                        stss = list(struct.unpack(f'>{n}I', f.read(4 * n)))
            walk(a2, b2)
            if vide:
                return stss            # None = every sample is a sync sample
    return None


def plate_frame_hashes():
    """{frame: packet md5} and the sorted keyframe indices of .work/plate.mov (cached on size + mtime)."""
    p = os.path.join(WORK, 'plate.mov')
    st = os.stat(p)
    key = f'{st.st_size}:{st.st_mtime_ns}'
    cp = os.path.join(WORK, 'plate_pkts.json')
    if os.path.exists(cp):
        c = json.load(open(cp))
        if c.get('key') == key:
            return {int(k): v for k, v in c['frames'].items()}, c['keys']
    out = subprocess.run([FF, '-v', 'error', '-i', p, '-map', '0:v', '-c', 'copy', '-f', 'framemd5', '-'], capture_output=True, text=True, check=True).stdout
    pk = []
    for ln in out.splitlines():
        if ln.startswith('#'):
            continue
        q = [x.strip() for x in ln.split(',')]
        pk.append((int(q[2]), q[5]))                      # pts, md5 (decode order)
    order = sorted(range(len(pk)), key=lambda i: pk[i][0])
    rank = {i: r for r, i in enumerate(order)}
    frames = {rank[i]: pk[i][1] for i in range(len(pk))}
    ss = mp4_sync_samples(p)
    keys = sorted(rank[s - 1] for s in ss) if ss else list(range(len(pk)))
    json.dump(dict(key=key, frames=frames, keys=keys), open(cp, 'w'))
    return frames, keys


def segment_hashes(layer_idx, plate_frames, keys):
    import bisect
    out = []
    for s in range(0, NF, SEG):
        e = min(NF, s + SEG)
        k0 = keys[bisect.bisect_right(keys, s) - 1] if keys and keys[0] <= s else 0
        j = bisect.bisect_left(keys, e)
        k1 = keys[j] if j < len(keys) else NF
        h = hashlib.sha1(ENC_SIG.encode())
        for n in range(s, e):
            h.update(str(layer_idx.get(str(n), 'x')).encode())
        for n in range(k0, k1):
            h.update(plate_frames.get(n, 'x').encode())
        out.append((s, e, h.hexdigest()[:20]))
    return out


def encode_run(s, e, seq, segdir, first_seg):
    """encode frames [s, e) (a run of whole segments) in one ffmpeg: master + preview segments of SEG frames each."""
    n = e - s
    cuts = ','.join(str(x) for x in range(SEG, n, SEG))
    seek = max(0.0, (s - 0.5) / FPS)
    fk = f'expr:eq(mod(n,{SEG}),0)'
    graph = GRAPH + f';[v]split=2[vm][vp0];[vp0]scale=720:1280:flags=lanczos[vp]'
    segargs = lambda pre: ['-flags', '+global_header', '-f', 'segment', '-segment_format', 'mp4', '-segment_start_number', str(first_seg),
                           *(['-segment_frames', cuts] if cuts else ['-segment_time', '100000']), '-reset_timestamps', '1',
                           os.path.join(segdir, pre + '_%03d.mp4')]
    sh([FF, '-v', 'error', '-y', '-ss', f'{seek:.6f}', '-i', os.path.join(WORK, 'plate.mov'), '-framerate', '30000/1001', '-start_number', str(s),
        '-i', os.path.join(seq, '%05d.png'), '-filter_complex_threads', '4', '-filter_complex', graph,
        '-map', '[vm]', '-frames:v', str(n), *VENC, '-force_key_frames', fk, '-an', *segargs('m'),
        '-map', '[vp]', '-frames:v', str(n), *PENC, '-force_key_frames', fk, '-an', *segargs('p')])


def aac(src, dst, br, af=None):
    """AAC once per mix (cached on the wav's content)."""
    h = hashlib.sha1(open(src, 'rb').read()).hexdigest()[:16] + f'|{br}|{af}'
    sp = dst + '.sig'
    if os.path.exists(dst) and os.path.exists(sp) and open(sp).read() == h:
        return dst
    sh([FF, '-v', 'error', '-y', '-i', src] + (['-af', af] if af else []) + ['-c:a', 'aac', '-b:a', br, '-ar', '48000', '-ac', '2', dst])
    open(sp, 'w').write(h)
    return dst


def concat_mux(parts, audio, out, title):
    lst = out + '.list.txt'
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    tmp = out + '.tmp.mp4'
    sh([FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-i', audio, '-map', '0:v', '-map', '1:a', '-c', 'copy',
        '-movflags', '+faststart', '-metadata', f'title={title}', tmp])
    os.replace(tmp, out); os.remove(lst)


def st_compose(A):
    if getattr(A, 'draft', False):
        return compose_draft(A)
    t0 = time.time()
    seq = build_sequence()
    os.makedirs(EXP, exist_ok=True)
    segdir = os.path.join(WORK, 'segs'); os.makedirs(segdir, exist_ok=True)
    idx = json.load(open(os.path.join(WORK, 'front', 'index.json')))
    pf, keys = plate_frame_hashes()
    segs = segment_hashes(idx, pf, keys)
    sp = os.path.join(segdir, 'index.json')
    old = json.load(open(sp)) if os.path.exists(sp) else {}
    stale = [i for i, (s, e, h) in enumerate(segs) if old.get(str(i)) != h or not os.path.exists(os.path.join(segdir, f'm_{i:03d}.mp4'))
             or not os.path.exists(os.path.join(segdir, f'p_{i:03d}.mp4'))]
    for i in stale:
        old.pop(str(i), None)
    json.dump(old, open(sp, 'w'))
    runs = []
    for i in stale:
        if runs and runs[-1][1] == i:
            runs[-1][1] = i + 1
        else:
            runs.append([i, i + 1])
    t1 = time.time()
    for a, b in runs:
        encode_run(segs[a][0], segs[b - 1][1], seq, segdir, a)
        for i in range(a, b):
            old[str(i)] = segs[i][2]
        json.dump(old, open(sp, 'w'))
    t_enc = time.time() - t1
    master = os.path.join(EXP, f'{NAME} - 1080x1920.mp4')
    nomus = os.path.join(EXP, f'{NAME} - NO MUSIC - 1080x1920.mp4')
    prev = os.path.join(EXP, f'{NAME} - PREVIEW 720x1280.mp4')
    mparts = [os.path.join(segdir, f'm_{i:03d}.mp4') for i in range(len(segs))]
    pparts = [os.path.join(segdir, f'p_{i:03d}.mp4') for i in range(len(segs))]
    a_m = aac(os.path.join(WORK, 'mix.wav'), os.path.join(WORK, 'aac_master.m4a'), '256k')
    a_n = aac(os.path.join(WORK, 'mix_nomusic.wav'), os.path.join(WORK, 'aac_nomusic.m4a'), '256k')
    # the preview's audio: the same mix 0.5 dB lower, so the 160k AAC still holds -1.5 dBTP
    a_p = aac(os.path.join(WORK, 'mix.wav'), os.path.join(WORK, 'aac_preview.m4a'), '160k', af='volume=-0.5dB')
    title = 'Rally day (Egnyte) - Supercar Experience vlog v2'
    concat_mux(mparts, a_m, master, title)
    concat_mux(mparts, a_n, nomus, title + ' (no music)')
    concat_mux(pparts, a_p, prev, title + ' (preview)')
    mbps = os.path.getsize(master) * 8 / DUR / 1e6
    deliv = os.path.join(EXP, f'{NAME} - 1080x1920_DELIVERY.mp4')
    if mbps > 11.5:
        log(f'compose: master {mbps:.2f} Mb/s > 11.5 -> _DELIVERY copy')
        plog = os.path.join(WORK, 'x264pass')
        sh([FF, '-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'slow', '-b:v', '11.2M', '-pass', '1', '-passlogfile', plog + 'd', '-an', '-f', 'null', '-'])
        sh([FF, '-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'slow', '-b:v', '11.2M', '-pass', '2', '-passlogfile', plog + 'd',
            '-c:a', 'copy', '-movflags', '+faststart', deliv])
    elif os.path.exists(deliv):
        os.remove(deliv)
    pmib = os.path.getsize(prev) / 2 ** 20
    if pmib >= 29.5:                                   # safety net: the preview must stay under 30 MiB
        log(f'compose: preview {pmib:.1f} MiB >= 29.5 -> two-pass 1.1 Mb/s from the master')
        plog = os.path.join(WORK, 'x264pass')
        pv = ['-vf', 'scale=720:1280:flags=lanczos', '-c:v', 'libx264', '-preset', 'medium', '-b:v', '1.1M', '-maxrate', '2M', '-bufsize', '3M',
              '-pix_fmt', 'yuv420p', '-passlogfile', plog + 'p']
        sh([FF, '-v', 'error', '-y', '-i', master] + pv + ['-pass', '1', '-an', '-f', 'null', '-'])
        sh([FF, '-v', 'error', '-y', '-i', master, '-i', a_p] + pv + ['-pass', '2', '-map', '0:v', '-map', '1:a', '-c:a', 'copy', '-movflags', '+faststart', prev])
    shutil.copyfile(os.path.join(WORK, 'music_stem.wav'), os.path.join(EXP, f'{NAME} - music-stem.wav'))
    log(f'compose: {len(stale)} of {len(segs)} segments encoded ({t_enc:.0f}s), muxed, {time.time() - t0:.0f}s in all '
        f'({mbps:.2f} Mb/s master, preview {os.path.getsize(prev) / 2 ** 20:.1f} MiB)')
    TIMES['compose'] = dict(segments_encoded=len(stale), segments=len(segs), encode_s=round(t_enc, 1), total_s=round(time.time() - t0, 1))


def compose_draft(A):
    """draft: plate scaled to 540x960 under the half-size layer, x264 veryfast, one pass, no segments."""
    t0 = time.time()
    seq = build_sequence(os.path.join(WORK, 'front_draft'))
    d = os.path.join(EXP, 'draft'); os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f'{NAME} - DRAFT 540x960.mp4')
    # a half-size copy of the plate, made once per plate (decoding the full plate would be half the draft's time)
    pd = os.path.join(WORK, 'plate_draft.mov'); pl = os.path.join(WORK, 'plate.mov')
    if not os.path.exists(pd) or os.path.getmtime(pd) < os.path.getmtime(pl):
        sh([FF, '-v', 'error', '-y', '-i', pl, '-vf', 'scale=540:960:flags=bilinear', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14',
            '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', pd + '.tmp.mov'])
        os.replace(pd + '.tmp.mov', pd)
    g = GRAPH
    sh([FF, '-v', 'error', '-y', '-i', pd, '-framerate', '30000/1001', '-i', os.path.join(seq, '%05d.png'),
        '-i', os.path.join(WORK, 'mix.wav'), '-filter_complex_threads', '4', '-filter_complex', g, '-map', '[v]', '-map', '2:a',
        '-frames:v', str(NF), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart', out])
    log(f'compose (draft): {out} in {time.time() - t0:.0f}s')
    TIMES['compose'] = dict(draft=True, total_s=round(time.time() - t0, 1))


# ================================================================================== QA
def decode_frames(path, idx):
    idx = sorted(set(idx))
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-vf', f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc",
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    assert len(arr) == len(idx), (len(arr), len(idx))
    return dict(zip(idx, arr))


def decode_stream(path, idx, fn):
    """decode only the frames idx of path (one pass) and hand each to fn(i, rgb array) as it arrives (low memory)."""
    idx = sorted(set(idx))
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    p = subprocess.Popen([FF, '-v', 'error', '-i', path, '-vf', f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc",
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3)
    for i in idx:
        b = p.stdout.read(W * H * 3)
        assert len(b) == W * H * 3, f'short decode at frame {i}'
        fn(i, np.frombuffer(b, np.uint8).reshape(H, W, 3))
    p.stdout.close(); p.wait()


def thumb(a, tw, th=None):
    th = th or int(tw * 16 / 9)
    return np.asarray(Image.fromarray(a).resize((tw, th), Image.LANCZOS))


def contact_sheet(frames, path, cols=8, tw=216, labels=None, th=None):
    th = th or int(tw * 16 / 9)
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
    cs = sorted(set(list(range(0, NF, 60)) + [NF - 1]))
    sidx, slab = [], {}
    for k, f0, f1 in PL.FR:
        for nm, i in (('in', f0 + 2), ('mid', (f0 + f1) // 2), ('out', f1 - 3)):
            i = min(max(i, f0), f1 - 1); sidx.append(i); slab[i] = f'{k:02d} {PL.SHOTS[k]["src"]} {nm}'
    # the swap check (lib/swapcheck.js): every frame's motion-blur samples agree on the caption page, the convoy label
    # text and the clock's HH:MM, and never two caption pages at once
    sc = os.path.join(QA, 'swapcheck.json')
    sh([NODE, os.path.join(LIB, 'swapcheck.js'), os.path.join(ROOT, 'story.html'), sc])
    r = json.load(open(sc))
    cidx = sorted(set(sum([[s_['n'] - 1, s_['n']] for s_ in r['swaps']], [])))
    # loudness of every export in background threads while the master is decoded ONCE for every still and sheet
    from concurrent.futures import ThreadPoolExecutor
    ex = ThreadPoolExecutor(3)
    mp4s = sorted(fn for fn in os.listdir(EXP) if fn.endswith('.mp4'))
    aq = {fn: ex.submit(audio_qa, os.path.join(EXP, fn)) for fn in mp4s}
    T_b, T_e, T_c, T_cap, T_s, LUM = {}, {}, {}, {}, {}, {}
    sset, cset, capset = set(sidx), set(cs), set(cidx)
    def take(i, a):
        if i in marks:
            nm = marks[i]; pre = 'beat_' if nm.startswith('beat') else ''
            Image.fromarray(a).save(os.path.join(QA, f'{pre}{nm}_f{i:05d}_{i / FPS:07.3f}s.jpg'), quality=80)
            (T_b if nm.startswith('beat') else T_e)[i] = thumb(a, 200 if nm.startswith('beat') else 216)
        if i == 0:
            Image.fromarray(a).save(os.path.join(EXP, 'poster.jpg'), quality=94)
        if i in cset:
            T_c[i] = thumb(a, 180)
        if i in capset:
            T_cap[i] = thumb(np.ascontiguousarray(a[900:1460]), 270, 140)
        if i in sset:
            T_s[i] = thumb(a, 150)
            q = a[300:1550:4, 60:1000:4].astype(np.float32) / 255
            y = 0.2126 * q[..., 0] + 0.7152 * q[..., 1] + 0.0722 * q[..., 2]
            LUM[i] = [round(float(y.mean()), 3), round(float(np.median(y)), 3), round(float((y < 0.02).mean()), 3), round(float((y > 0.98).mean()), 3)]
    decode_stream(master, list(marks) + cs + cidx + sidx + [0], take)
    beat_frames = sorted(i for i, nm in marks.items() if nm.startswith('beat'))
    contact_sheet([(i, T_b[i]) for i in beat_frames], os.path.join(QA, 'beats-sheet.jpg'), cols=9, tw=200,
                  labels={i: marks[i].replace('beat', 'b') for i in beat_frames})
    el_frames = sorted(i for i, nm in marks.items() if nm.startswith('el_'))
    contact_sheet([(i, T_e[i]) for i in el_frames], os.path.join(QA, 'elements-sheet.jpg'), cols=8, tw=216,
                  labels={i: marks[i][3:] + f' {i / FPS:.2f}' for i in el_frames})
    contact_sheet([(i, T_c[i]) for i in cs], os.path.join(EXP, 'contact-sheet.jpg'), cols=11, tw=180)
    # audio, container
    res = dict(file=os.path.basename(master), bytes=os.path.getsize(master), MB=round(os.path.getsize(master) / 1e6, 2),
               MiB=round(os.path.getsize(master) / 2 ** 20, 2), mbps=round(os.path.getsize(master) * 8 / DUR / 1e6, 3),
               frames=NF, picture_s=round(NF / FPS, 4), track_durations_s=mp4_track_durations(master), audio=aq[os.path.basename(master)].result())
    others = {}
    for fn in mp4s:
        if fn != os.path.basename(master):
            p = os.path.join(EXP, fn)
            others[fn] = dict(MiB=round(os.path.getsize(p) / 2 ** 20, 2), track_durations_s=mp4_track_durations(p), audio=aq[fn].result())
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
    res['hard_swaps'] = dict(caption_page_changes=[s_['n'] for s_ in r['swaps']], flagged=r['bad'])
    # the last frame of every caption page and the first frame of the next, from the delivered master (caption band)
    swn = {s_['n'] for s_ in r['swaps']}
    contact_sheet([(i, T_cap[i]) for i in cidx], os.path.join(QA, 'caption-swaps-sheet.jpg'), cols=12, tw=270,
                  labels={i: f'f{i}' + (' new page' if i in swn else '') for i in cidx}, th=140)
    # every shot's first / middle / last frame from the delivered file: sheet + luma (grade consistency)
    contact_sheet([(i, T_s[i]) for i in sorted(set(sidx))], os.path.join(QA, 'shots-sheet.jpg'), cols=12, tw=150, labels=slab)
    lum = {}
    for k, f0, f1 in PL.FR:
        vals = []
        for i in sorted(set(q for q in sidx if f0 <= q < f1)):
            vals.append(LUM[i])
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
    capture(idx, out)
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
    ap.add_argument('--stage', default='shots,track,join,prep,audio,gates,front,compose,qa')
    ap.add_argument('--draft', action='store_true', help='540x960 review cut in minutes: half-size layer, one sample per frame, '
                                                          'fast encode -> exports/draft/ (the full-size caches are not touched)')
    ap.add_argument('--force', action='store_true', help='render even when a gate reports an error')
    ap.add_argument('--stills')
    ap.add_argument('--tracks')
    ap.add_argument('--from-shots', action='store_true')
    ap.add_argument('--recapture', help='mark these frames (a-b,c-d) stale and re-capture them (normally not needed: the '
                                         'front stage finds changed frames by their layer-state hash)')
    ap.add_argument('--force-front', action='store_true')
    A = ap.parse_args()
    if A.stills:
        st_prep(A); stills(A, [int(x) for x in A.stills.split(',')]); return
    if A.recapture:
        ip = os.path.join(WORK, 'front', 'index.json')
        if os.path.exists(ip):
            idx = json.load(open(ip))
            for r in A.recapture.split(','):
                a, b = (int(v) for v in r.split('-'))
                for i in range(a, b + 1):
                    idx.pop(str(i), None)
            json.dump(idx, open(ip, 'w'))
        A.stage = 'prep,front'
    st = A.stage.split(',')
    if A.draft:
        st = [x for x in st if x not in ('qa',)]
    T0 = time.time()
    for name, fn in (('shots', st_shots), ('track', st_track), ('join', st_join), ('prep', st_prep), ('audio', st_audio),
                     ('gates', st_gates), ('front', st_front), ('compose', st_compose), ('qa', st_qa)):
        if name in st:
            import resource
            t = time.time(); r0 = resource.getrusage(resource.RUSAGE_CHILDREN); s0 = resource.getrusage(resource.RUSAGE_SELF)
            fn(A)
            r1 = resource.getrusage(resource.RUSAGE_CHILDREN); s1 = resource.getrusage(resource.RUSAGE_SELF)
            cpu = (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime) + (s1.ru_utime - s0.ru_utime) + (s1.ru_stime - s0.ru_stime)
            TIMES.setdefault(name, {}).update(s=round(time.time() - t, 1), cpu_s=round(cpu, 1), load=round(os.getloadavg()[0], 1))
    TIMES['total_s'] = round(time.time() - T0, 1)
    tp = os.path.join(WORK, 'timings_draft.json' if A.draft else 'timings.json')
    json.dump(dict(stages=st, when=time.strftime('%Y-%m-%d %H:%M:%S'), times=TIMES), open(tp, 'w'), indent=1)
    log('timings: ' + ', '.join(f'{k} {v["s"]:.0f}s' for k, v in TIMES.items() if isinstance(v, dict) and 's' in v) + f' | total {TIMES["total_s"]:.0f}s')


if __name__ == '__main__':
    main()
