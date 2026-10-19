#!/usr/bin/env python3
"""proof.py -- the 720p motion proof for the 4K rebuild (../PLAN.md, step 3): the approved cut (opening B2 v2.2 + Ch1-8,
18,951 frames, 10:32) rendered clean from the 720p working copies, with the 11 Oct motion picks (motion.py) on top.
The cut, its length and the sound are not changed: every piece comes from its own render.py `render_shots()` (grade,
crop, blurs; no old titles), its own music.py + mix.py, and ../hud/assemble.py's sample-exact sound join.

    python3 proof.py preflight   # every shot of the nine edit lists is covered by a working copy in VLOG_MEZZ
    python3 proof.py shots       # render_shots() at 1280x720 -> OUT/shots/<piece>/ + frame counts
    python3 proof.py audio       # music.py + mix.py per piece, then the join -> OUT/audio/mix_full.wav
    python3 proof.py overlays    # motion.clips(720) + Ch3's word pops (its own pop_frames, unchanged) -> OUT/ov/*.mov
    python3 proof.py encode      # ONE encode: concat + overlays + AAC -> OUT/one_way_ticket_proof_720p.mp4
    python3 proof.py sheet       # the one labelled contact sheet -> OUT/proof_sheet.jpg (+ sheet_tiles.json)
    python3 proof.py measure     # length, frame count, where the route cards sit -> OUT/measure.json
    python3 proof.py readme      # OUT/PROOF_README.md from sheet_tiles.json + measure.json
    python3 proof.py all         # everything above, in order; finished stages are skipped
    python3 proof.py nomusic     # 4K step 6: the same picture (copied) with nomusic_full.wav -> OUT/..._NO_MUSIC.mp4
    python3 proof.py chapters    # 4K step 6: OUT/chapters.txt (YouTube chapter lines at the route-card joins)

Env: VLOG_DAY (the day folder: sound, transcripts, fonts, work), VLOG_MEZZ (the 720p working copies),
PROOF_OUT (default: <VLOG_DAY>/../proof720). ffmpeg and ffprobe must be on PATH. Every stage is resumable.
PROOF_RES=2160 (PLAN_4K step 4): the same stages at 3840x2160, for the 4K masters from the 4K working copies (VLOG_MEZZ
= the 4K folder; default out <VLOG_DAY>/../master4k). `shots` then renders one piece at a time with a marker per piece
(OUT/shots/<piece>.ok), and before each piece waits for the Mac to be on its charger (a 4K piece is too long for battery).
Python needs Pillow and numpy; the `shots` stage also needs OpenCV (cv2), for the opening's subject lift
(../opening-test/subject_lift.py).
"""
import functools, importlib.util, json, math, os, re, subprocess, sys, threading, time

ARGS = sys.argv[1:]
HERE = os.path.dirname(os.path.abspath(__file__))
YT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import motion as M                                   # noqa: E402
from PIL import Image, ImageDraw                     # noqa: E402

DAY = os.environ.get('VLOG_DAY', '/home/user/day-owt')
MEZZ = os.environ.get('VLOG_MEZZ', f'{DAY}/mezz')
RES = os.environ.get('PROOF_RES', '720')
OUT = os.environ.get('PROOF_OUT', os.path.join(os.path.dirname(DAY.rstrip('/')), 'master4k' if RES == '2160' else 'proof720'))
FF = 'ffmpeg'
PY = sys.executable
FPS = 30000 / 1001
W, H = (3840, 2160) if RES == '2160' else (1280, 720)
PLAN = json.load(open(f'{YT}/hud/hud.json'))
PIECES = [(p['name'], p['frames']) for p in PLAN['pieces']]        # opening + ch1..ch8, the rough cut's frame counts
F0 = {p['name']: p['frame0'] for p in PLAN['pieces']}
TOTAL = sum(n for _, n in PIECES)
# music.py seconds, from each chapter's README. Ch4's README says 41, which cannot be right: the chapter is 72.56 s with
# the bed on throughout, and music.py stops with an error at 41 (the last two-bar chord is 0.02 s long). 76 covers the
# chapter; the bed over the chapter is the same whatever length is asked for (76 and 79 compared sample for sample).
BED = {'ch1': 60, 'ch2': 42, 'ch3': 165, 'ch4': 76, 'ch5': 59, 'ch6': 48, 'ch7': 73, 'ch8': 85}
NAME = f'{OUT}/one_way_ticket_master_2160p.mp4' if RES == '2160' else f'{OUT}/one_way_ticket_proof_720p.mp4'
RSS_LIMIT_GB = 9.0           # the encode is stopped if ffmpeg grows past this (24 GB Mac)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.stderr.write((r.stdout or '')[-1500:] + (r.stderr or '')[-3000:])
        raise SystemExit(f'FAILED: {" ".join(str(c) for c in cmd[:6])} ...')
    return r


def tc(frame):
    s = frame * 1001 / 30000
    return f'{int(s // 60)}:{s % 60:05.2f}'


def piece_of(frame):
    name = PIECES[0][0]
    for n, _ in PIECES:
        if frame >= F0[n]:
            name = n
    return name


def chap(name):
    return 'OPENING' if name == 'opening' else 'CH ' + name[2:]


# ---------------------------------------------------------------- one heavy job at a time
def busy():
    ff = subprocess.run(['pgrep', '-x', 'ffmpeg'], capture_output=True, text=True).stdout.split()
    ps = subprocess.run(['ps', '-axo', 'pid=,command='], capture_output=True, text=True).stdout.splitlines()
    other = [l.strip()[:110] for l in ps if re.search(r'remotion|chrome-headless-shell|--headless', l, re.I)]
    return ff, other


def wait_clear(stage, limit=1200):
    """Before a heavy stage: nothing else may be rendering (ffmpeg by exact name; Remotion or headless Chrome by command
    line). Re-checks every 30 s for up to 20 minutes, then stops."""
    t0 = time.time()
    while True:
        ff, other = busy()
        if not ff and not other:
            log(f'{stage}: no other render running')
            return
        if time.time() - t0 > limit:
            raise SystemExit(f'blocked by another render (before {stage}): ffmpeg pids {ff}; {other[:3]}')
        log(f'{stage}: waiting, another render is running (ffmpeg pids {ff}; {len(other)} other)')
        time.sleep(30)


def on_charger():
    return 'AC Power' in subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True).stdout


def wait_power(stage):
    """4K only: wait (checking every minute, with no time limit) until the Mac is on its charger."""
    if RES != '2160' or on_charger():
        return
    log(f'{stage}: waiting for the charger (the Mac is on battery)')
    while not on_charger():
        time.sleep(60)
    log(f'{stage}: on the charger')


# ---------------------------------------------------------------- the pieces' own code
@functools.lru_cache(maxsize=None)
def load(piece):
    """The piece's own render.py as a module (nothing in it runs at import beyond reading its edit list and look)."""
    d = f'{YT}/opening-test' if piece == 'opening' else f'{YT}/{piece}'
    if piece == 'opening':
        sys.argv = ['render.py', 'timeline', 'B2']       # the opening reads its variant from argv: B2 = v2.2
        if d not in sys.path:
            sys.path.insert(0, d)                        # subject_lift.py (the Ch1 tail shot)
    spec = importlib.util.spec_from_file_location(f'render_{piece}', f'{d}/render.py')
    m = importlib.util.module_from_spec(spec)
    cwd = os.getcwd(); spec.loader.exec_module(m); os.chdir(cwd)
    return m


def edl_of(piece):
    return json.load(open(f'{YT}/opening-test/edl_B2.json')) if piece == 'opening' else load(piece).EDL


def want_frames(piece):
    """Frames per shot, by the piece's own rule."""
    m = load(piece)
    if hasattr(m, 'shot_frames'):                        # ch5-8: the rounded chapter clock
        return m.shot_frames()
    return [round(s['dur'] * 30000 / 1001) for s in edl_of(piece)['shots']]


def spans(piece):
    """(src, in, out) of every shot, as the piece's render_shots() asks its working copy for it."""
    m = load(piece); e = edl_of(piece); nf = want_frames(piece)
    out = []
    for i, s in enumerate(e['shots']):
        if piece == 'opening':
            ln = s['dur']
        elif hasattr(m, 'shot_frames'):
            ln = nf[i] / FPS * s['speed']
        else:
            ln = s['dur'] * s['speed']
        out.append((s['src'], s['in'], s['in'] + ln))
    return out


def nframes(path):
    return int(run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries',
                    'stream=nb_read_packets', '-of', 'csv=p=0', path]).stdout.strip().strip(','))


def preflight():
    bad = []; n = 0
    names = sorted(os.listdir(MEZZ)) if os.path.isdir(MEZZ) else []
    for piece, _ in PIECES:
        for src, a, b in spans(piece):
            n += 1
            ok = False
            for f in names:
                m = re.match(rf'{src}_([\d.]+)-([\d.]+)\.mov$', f)
                if m and float(m.group(1)) <= a + 1e-3 and b <= float(m.group(2)) + 1e-3:
                    ok = True
            if not ok:
                bad.append(f'{piece} {src} {a:.3f}-{b:.3f}')
    log(f'preflight: {n - len(bad)} of {n} shots covered by a working copy in {MEZZ} ({len(names)} files)')
    for b in bad[:20]:
        log('  NOT COVERED:', b)
    if bad:
        raise SystemExit('preflight failed')


# ---------------------------------------------------------------- shots
def shots():
    d0 = f'{OUT}/shots'; os.makedirs(d0, exist_ok=True)
    if os.path.exists(f'{d0}/frames.json'):
        log('shots: already done'); return
    preflight()
    wait_clear('shots')
    rep = {}
    for piece, frames in PIECES:
        if os.path.exists(f'{d0}/{piece}.ok'):                    # finished in an earlier run (marker per piece)
            rep[piece] = json.load(open(f'{d0}/{piece}.json')); log(f'shots {piece}: already done'); continue
        wait_power(f'shots {piece}')
        wait_clear(f'shots {piece}')
        m = load(piece); d = f'{d0}/{piece}'
        os.makedirs(getattr(m, 'WORK'), exist_ok=True)
        t = time.time()
        if piece == 'opening':
            parts = m.render_shots(edl_of(piece), W, H, d)
        elif hasattr(m, 'shot_frames'):
            parts = m.render_shots(W, H, d, 14, 'veryfast', MEZZ)
        else:
            parts = m.render_shots(W, H, d, 14, 'veryfast')
        want = want_frames(piece); got = [nframes(p) for p in parts]
        short = [(os.path.basename(p), g, w) for p, g, w in zip(parts, got, want) if g != w]
        open(f'{d0}/{piece}.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
        rep[piece] = dict(shots=len(parts), frames=sum(got), piece_frames=frames, wrong=short)
        log(f'shots {piece}: {len(parts)} shots, {sum(got)} frames (the piece is {frames}), {time.time() - t:.0f}s'
            + (f' WRONG COUNT {short[:4]}' if short else ''))
        if short or sum(got) < frames:
            raise SystemExit(f'shots {piece}: frame count does not match the edit list')
        json.dump(rep[piece], open(f'{d0}/{piece}.json', 'w')); open(f'{d0}/{piece}.ok', 'w').write('ok')
    json.dump(rep, open(f'{d0}/frames.json', 'w'), indent=1)
    log('shots: done', sum(r['frames'] for r in rep.values()), 'frames rendered,', TOTAL, 'used')


# ---------------------------------------------------------------- sound
def audio():
    d = f'{OUT}/audio'; os.makedirs(d, exist_ok=True)
    if os.path.exists(f'{d}/mix_full.wav') and os.path.exists(f'{d}/audio.ok'):
        log('audio: already done'); return
    for c, secs in BED.items():
        wk = f'{DAY}/{c}work'; os.makedirs(wk, exist_ok=True)
        if os.path.exists(f'{wk}/mix.proof_ok'):
            continue
        t = time.time()
        run([PY, f'{YT}/{c}/music.py', f'{wk}/bed.wav', str(secs)], cwd=f'{YT}/{c}')
        r = run([PY, f'{YT}/{c}/mix.py', wk], cwd=f'{YT}/{c}')
        open(f'{wk}/mix.proof_ok', 'w').write('ok')
        log(f'audio {c}: mixed in {time.time() - t:.0f}s |', ' | '.join(r.stdout.strip().splitlines()[-2:])[:230])
    wk = f'{DAY}/openwork'; os.makedirs(wk, exist_ok=True)
    if not os.path.exists(f'{wk}/mix.proof_ok'):
        t = time.time()
        r = run([PY, f'{YT}/opening-test/mix.py', 'B2'], cwd=f'{YT}/opening-test')
        open(f'{wk}/mix.proof_ok', 'w').write('ok')
        log(f'audio opening: mixed in {time.time() - t:.0f}s |', ' | '.join(r.stdout.strip().splitlines()[-2:])[:230])
    spec = importlib.util.spec_from_file_location('hud_assemble', f'{YT}/hud/assemble.py')
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    assert [(p[0], p[4]) for p in A.PIECES] == PIECES, 'hud.json and assemble.py disagree on the pieces'
    A.D = DAY; A.OUT = d
    import contextlib, io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        A.audio()                                        # the rough cut's sample-exact join -> mix_full.wav, nomusic_full.wav
    rep = buf.getvalue().splitlines()
    log(f'audio join: {len(rep)} report lines; clicks flagged: {sum("CLICK?" in l for l in rep)}; report in {d}/audio_report.txt')
    open(f'{d}/audio.ok', 'w').write('ok')


# ---------------------------------------------------------------- overlays
def all_clips():
    """motion.clips(720) with the word pops slotted in above the HUD and under the titles (bottom to top)."""
    cl = M.clips(H)
    pops = []
    for piece, _ in PIECES[1:]:
        pj = f'{YT}/{piece}/pops.json'
        if not os.path.exists(pj):
            continue
        m = load(piece)
        for k, pp in enumerate(json.load(open(pj))):
            n = round(pp['dur'] * 29.97)                              # as the chapter's own graphics()
            f0 = F0[piece] + math.ceil(pp['t'] * FPS - 1e-6)          # where its `-itsoffset t` overlay landed
            pops.append(dict(name=f'pop_{piece}_{k}', kind='pop', piece=piece, f0=f0, n=n, x=0, y=0, w=W, h=H,
                             frames=functools.partial(m.pop_frames, W, H, pp['text'], n, pp.get('side', 'r')),
                             what=f'word pop A "{pp["text"]}" (unchanged)'))
    k = max(i for i, c in enumerate(cl) if c['kind'] == 'hud') + 1
    return cl[:k] + pops + cl[k:]


def overlays():
    d = f'{OUT}/ov'; os.makedirs(d, exist_ok=True)
    man = []; t0 = time.time(); made = 0
    for c in all_clips():
        path = f'{d}/{c["name"]}.mov'
        sig = json.dumps([c['f0'], c['n'], c['x'], c['y'], c['w'], c['h'], c['what'], os.path.getmtime(f'{HERE}/motion.py')])
        if not (os.path.exists(path) and os.path.exists(path + '.sig') and open(path + '.sig').read() == sig):
            k = M.write_clip(c['frames'](), path, c['w'], c['h'], FF)
            assert k == c['n'], (c['name'], k, c['n'])
            open(path + '.sig', 'w').write(sig); made += 1
        man.append({k: v for k, v in c.items() if k != 'frames'} | dict(path=path))
    json.dump(man, open(f'{d}/clips.json', 'w'), indent=1)
    kinds = {}
    for c in man:
        kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
    log(f'overlays: {len(man)} clips ({made} drawn now), {sum(c["n"] for c in man)} frames, {time.time() - t0:.0f}s | {kinds}')


# ---------------------------------------------------------------- the encode
OV_FMT = 'scale=out_color_matrix=bt709:out_range=tv,format=yuva420p'    # the brand colours go in as BT.709, like the picture


def encode():
    if os.path.exists(NAME) and os.path.exists(NAME + '.ok'):
        log('encode: already done'); return
    wait_power('encode')                                         # about 2.4 h at 4K: never start it on battery
    man = json.load(open(f'{OUT}/ov/clips.json'))
    fr = json.load(open(f'{OUT}/shots/frames.json'))
    assert all(fr[p]['frames'] >= n for p, n in PIECES)
    wait_clear('encode')
    cmd = [FF, '-v', 'error', '-nostats', '-y', '-progress', f'{OUT}/encode.progress']
    for p, _ in PIECES:
        cmd += ['-threads', '2', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/shots/{p}.txt']
    for c in man:
        cmd += ['-threads', '1', '-i', c['path']]
    cmd += ['-i', f'{OUT}/audio/mix_full.wav']
    n = len(PIECES)
    g = ''.join(f'[{i}:v]settb=1/30000,setpts=N*1001,trim=end_frame={fn},setsar=1,format=yuv420p[p{i}];' for i, (_, fn) in enumerate(PIECES))
    g += ''.join(f'[p{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0[c0]'
    for k, c in enumerate(man):
        g += (f";[{n + k}:v]settb=1/30000,setpts=N*1001+{c['f0'] * 1001},{OV_FMT}[o{k}]"
              f";[c{k}][o{k}]overlay={c['x']}:{c['y']}:eof_action=pass:format=yuv420[c{k + 1}]")
    g += f';[c{len(man)}]format=yuv420p[v]'
    open(f'{OUT}/encode.graph.txt', 'w').write(g.replace(';', ';\n'))
    cmd += ['-filter_complex', g, '-filter_complex_threads', '2', '-map', '[v]', '-map', f'{n + len(man)}:a', '-frames:v', str(TOTAL),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-threads', '3', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
            '-r', '30000/1001', '-video_track_timescale', '30000',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
            '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', NAME]
    t0 = time.time()
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=open(f'{OUT}/encode.err', 'w'))
    peak = [0.0]; killed = []

    def watch():
        while p.poll() is None:
            try:
                rss = int(subprocess.run(['ps', '-o', 'rss=', '-p', str(p.pid)], capture_output=True, text=True).stdout.strip() or 0) / 1048576
            except ValueError:
                rss = 0.0
            peak[0] = max(peak[0], rss)
            if rss > RSS_LIMIT_GB:
                killed.append(rss); p.kill()
            time.sleep(3)
    th = threading.Thread(target=watch, daemon=True); th.start()
    p.wait(); th.join(timeout=5)
    err = open(f'{OUT}/encode.err').read().strip().splitlines()
    if killed:
        raise SystemExit(f'encode stopped: ffmpeg grew to {killed[0]:.1f} GB (limit {RSS_LIMIT_GB} GB)')
    if p.returncode:
        raise SystemExit('encode FAILED:\n' + '\n'.join(err[-20:]))
    got = nframes(NAME)
    log(f'encode: {got} frames (want {TOTAL}) in {time.time() - t0:.0f}s, peak ffmpeg memory {peak[0]:.2f} GB, {len(man)} overlay clips, '
        f'{len(err)} stderr lines, {os.path.getsize(NAME) / 1048576:.1f} MiB')
    if got != TOTAL:
        raise SystemExit('encode: wrong frame count')
    open(NAME + '.ok', 'w').write('ok')


# ---------------------------------------------------------------- the one contact sheet
def grab(frame, w=W, h=H, pix='rgb24'):
    t = max(0.0, (frame - 0.5) * 1001 / 30000)
    r = subprocess.run([FF, '-v', 'error', '-ss', f'{t:.5f}', '-i', NAME, '-frames:v', '1', '-vf',
                        f'scale={w}:{h}:in_color_matrix=bt709:in_range=tv:flags=lanczos,format={pix}', '-f', 'rawvideo', '-'], capture_output=True)
    nb = w * h * (3 if pix == 'rgb24' else 1)
    assert len(r.stdout) == nb, (frame, len(r.stdout), r.stderr[-300:])
    return Image.frombytes('RGB' if pix == 'rgb24' else 'L', (w, h), r.stdout)


def tiles():
    c = {x['name']: x for x in json.load(open(f'{OUT}/ov/clips.json'))}
    J = lambda ch: c[f'join_{ch}']['join']
    f = lambda name, k: c[name]['f0'] + k
    pops = [x for x in c.values() if x['kind'] == 'pop']
    h4 = c['hud_03']; b8 = c['bar_ch8']
    both = max(b8['f0'] + 30, h4['f0'] + 24)
    assert both < b8['f0'] + b8['n'] - 12, 'the Ch8 bar and the last HUD run no longer overlap'
    t = [
        (f('host_tag', 70), 'host tag D: yellow brackets, leader, OMARIE / @NQ.YOUNG (once, first time on camera)'),
        (J('ch1') - 14, 'route card C fading in over the last frames of the opening'),
        (J('ch1') - 2, 'route card C "NEXT · 4:30 A.M." (before Seattle: no red on the route yet)'),
        (J('ch1') + 9, 'light band B wiping the card off into Ch1'),
        (f('title_ch1', 16), 'title D slot-reel clock: digits rolling'),
        (f('title_ch1', 60), 'title D landed: "4:30 A.M." + kicker under the digits'),
        (f('bar_ch1', 45), 'chapter bar (9 segments) + tab 01'),
        (f('title_ch2', 3), 'title B the slam: landing (scale + blur)'),
        (f('title_ch2', 20), 'title B settled, light sweep crossing, stripes'),
        (f('title_ch3', 50), 'title B "SEATTLE, WA"'),
    ]
    t += [(p['f0'] + 10, p['what']) for p in pops]
    t += [
        (f('hud_00', c['hud_00']['n'] // 2), 'HUD C: route rail + big place line (first drive run)'),
        (J('ch4') - 2, 'route card C "NEXT · OREGON": the red line snakes Seattle to Oregon'),
        (J('ch4') + 9, 'light band B wiping the card off into Ch4'),
        (f('title_ch4', 50), 'title B "INTO OREGON"'),
        (f('hud_01', 5), 'HUD C clipping in from the left (5 frames in), with chapter bar + tab 04 above it'),
        (f('title_ch5', 50), 'title B "NAMPA, IDAHO · NIGHT" (the longest title)'),
        (f('bar_ch5', 45), 'chapter bar + tab 05'),
        (f('title_ch6', 16), 'title D slot-reel clock: digits rolling'),
        (f('title_ch6', 60), 'title D landed: "1:29 A.M."'),
        (f('title_ch7', 50), 'title B "SUNRISE · NEVADA"'),
        (f('hud_02', c['hud_02']['n'] // 2), 'HUD C in Nevada (rail three stops down)'),
        (J('ch8') - 2, 'route card C "NEXT · LAS VEGAS"'),
        (f('title_ch8', 50), 'title B "LAS VEGAS"'),
        (both, 'chapter bar + tab 08 with HUD C under it'),
        (f('hud_03', h4['n'] - 20), 'HUD C at the last stop, Las Vegas'),
    ]
    return t


def sheet():
    import numpy as np
    T = tiles()
    cols = 4; tw, th, lh, pad, head = 640, 360, 46, 4, 56
    rows = math.ceil(len(T) / cols)
    S = Image.new('RGB', (cols * (tw + pad) + pad, head + rows * (th + lh + pad) + pad), (16, 16, 18))
    d = ImageDraw.Draw(S)
    fb, fs = M.archivo(700), M.archivo(500)
    d.text((pad + 6, 14), f'ONE-WAY TICKET · 720p MOTION PROOF · {len(T)} tiles · {TOTAL} frames = {tc(TOTAL)} · time and chapter on every tile',
           font=fb(24), fill=(251, 209, 1))
    rep = []
    for i, (fr, what) in enumerate(T):
        im = grab(fr).resize((tw, th), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad); y = head + (i // cols) * (th + lh + pad)
        S.paste(im, (x, y))
        pc = piece_of(fr)
        d.text((x + 4, y + th + 3), f'{i + 1:02d}   {tc(fr)}   frame {fr}   {chap(pc)}', font=fb(17), fill=(251, 209, 1))
        d.text((x + 4, y + th + 24), what[:88], font=fs(15), fill=(235, 235, 235))
        rep.append(dict(tile=i + 1, frame=fr, time=tc(fr), chapter=chap(pc), shows=what, mean=round(float(np.asarray(im.convert('L')).mean()), 1)))
    S.save(f'{OUT}/proof_sheet.jpg', quality=88)
    json.dump(rep, open(f'{OUT}/sheet_tiles.json', 'w'), indent=1, ensure_ascii=False)
    jpgs = [x for x in os.listdir(OUT) if x.lower().endswith(('.jpg', '.jpeg'))]
    log(f'sheet: {len(T)} tiles, {S.size[0]}x{S.size[1]}, {os.path.getsize(OUT + "/proof_sheet.jpg") / 1048576:.2f} MiB; JPGs in the proof folder: {jpgs}; '
        f'tile mean luma min {min(r["mean"] for r in rep)} max {max(r["mean"] for r in rep)}')


# ---------------------------------------------------------------- the measurements
def words_near(lo, hi):
    """Spoken words (small.en word times) that the mix places between global frames lo and hi: every dialog entry of
    every edit list, at its own timeline position."""
    out = []
    for piece, _ in PIECES:
        e = edl_of(piece)
        for dlg in e.get('dialog', []):
            try:
                tr = json.load(open(f'{DAY}/tr/{dlg["src"]}.json'))
            except FileNotFoundError:
                continue
            for seg in tr['segments']:
                for w0, w1, txt, *_ in seg['words']:
                    if dlg['in'] - 1e-6 <= w0 < dlg['out']:
                        a = F0[piece] + (dlg['t'] + w0 - dlg['in']) * FPS
                        b = F0[piece] + (dlg['t'] + min(w1, dlg['out']) - dlg['in']) * FPS
                        if a < hi and b > lo:
                            out.append((round(a, 1), round(b, 1), txt.strip(), piece))
    return sorted(set(out))


def shot_at(frame):
    piece = piece_of(frame); nf = want_frames(piece); e = edl_of(piece)
    f = F0[piece]
    for i, s in enumerate(e['shots']):
        if frame < f + nf[i] or i == len(nf) - 1:
            return dict(piece=piece, shot=i, src=s['src'], src_in=s['in'], kind=s.get('kind', ''), first=f, frames=nf[i])
        f += nf[i]


def measure():
    import numpy as np
    pr = json.loads(run(['ffprobe', '-v', 'error', '-count_packets', '-show_entries',
                         'stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_packets,duration,pix_fmt:format=duration,size',
                         '-of', 'json', NAME]).stdout)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]; a = [s for s in pr['streams'] if s['codec_type'] == 'audio'][0]
    nfr = int(v['nb_read_packets'])
    res = dict(file=NAME, frames=nfr, cut_frames=TOTAL, added_frames=nfr - TOTAL, video_s=float(v['duration']), audio_s=float(a['duration']),
               format_s=float(pr['format']['duration']), cut_s=round(TOTAL * 1001 / 30000, 3), size_mib=round(int(pr['format']['size']) / 1048576, 1),
               video=f"{v['codec_name']} {v['width']}x{v['height']} {v['pix_fmt']} {v['r_frame_rate']}", audio=a['codec_name'])
    # one decode of the finished proof at 160x90 grey: how dark is every frame (the route card is a black full-frame card)
    p = subprocess.Popen([FF, '-v', 'error', '-i', NAME, '-vf', 'scale=160:90:flags=area,format=gray', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    dark = []
    while True:
        b = p.stdout.read(14400)
        if len(b) < 14400:
            break
        dark.append(float((np.frombuffer(b, np.uint8) < 28).mean()))
    p.wait()
    res['decoded_frames'] = len(dark)
    man = {x['name']: x for x in json.load(open(f'{OUT}/ov/clips.json'))}
    joins = []
    for piece, _ in PIECES[1:]:
        c = man[f'join_{piece}']; J = c['join']
        # the card's own alpha, read back from the overlay clip: frames where it hides the whole picture, and the band's frames
        q = subprocess.Popen([FF, '-v', 'error', '-i', c['path'], '-vf', 'scale=160:90:flags=area,format=rgba', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
        raw = q.stdout.read(); q.wait()
        al = np.frombuffer(raw, np.uint8).reshape(-1, 90, 160, 4)[..., 3]
        full = [int(k) for k in range(len(al)) if al[k].min() >= 250]
        part = [int(k) for k in range(len(al)) if al[k].max() > 4 and al[k].min() < 250]
        lo, hi = c['f0'], c['f0'] + c['n']
        offs = [-16, -15, -13, -8, -2, 0, 4, 9, 14, 15]
        joins.append(dict(
            into=piece, join_frame=J, join_time=tc(J), card_first=lo, card_last=hi - 1, card_frames=c['n'], card_s=round(c['n'] * 1001 / 30000, 3),
            before_cut=J - lo, after_cut=hi - J, hides_all=[lo + full[0], lo + full[-1]] if full else None, hides_all_frames=len(full),
            partly_frames=len(part), dark_fraction={f'{o:+d}': round(dark[J + o], 2) for o in offs},
            outgoing=shot_at(J - 1), incoming=shot_at(J),
            words=[dict(word=w[2], from_frame=w[0], to_frame=w[1], rel_s=[round((w[0] - J) / FPS, 2), round((w[1] - J) / FPS, 2)]) for w in words_near(lo, hi)],
            clear_at=[next_start(man, piece)]))
    res['joins'] = joins
    k = len(joins); n = joins[0]['card_frames']
    res['if_inserted'] = dict(added_frames=k * n, added_s=round(k * n * 1001 / 30000, 3), total_frames=TOTAL + k * n,
                              total_s=round((TOTAL + k * n) * 1001 / 30000, 3), total=tc(TOTAL + k * n))
    # the brand red, read back from the finished file: the chapter tab's number block
    b = man.get('bar_ch5') or [c for c in man.values() if c['kind'] == 'bar'][0]
    im = np.asarray(grab(b['f0'] + 45)).astype(int)
    reg = im[40:76, W // 2:]
    red = reg[(reg[..., 0] > 170) & (reg[..., 1] < 80) & (reg[..., 2] < 90)]
    res['tab_red_rgb'] = [int(x) for x in np.median(red, 0)] if len(red) else None
    res['tab_red_pixels'] = int(len(red))
    json.dump(res, open(f'{OUT}/measure.json', 'w'), indent=1, ensure_ascii=False)
    log(f"measure: proof {res['frames']} frames (cut {TOTAL}, added {res['added_frames']}), video {res['video_s']:.3f}s audio {res['audio_s']:.3f}s "
        f"(cut {res['cut_s']}s); decoded {len(dark)}; tab red {res['tab_red_rgb']} from {res['tab_red_pixels']} px")
    for j in joins:
        log(f"  join into {j['into']} @ {j['join_time']} (frame {j['join_frame']}): card frames {j['card_first']}-{j['card_last']} "
            f"({j['before_cut']} before, {j['after_cut']} after), hides all {j['hides_all_frames']} fr, dark {j['dark_fraction']}, "
            f"words {[w['word'] for w in j['words']]}")
    log(f"  if inserted instead: +{res['if_inserted']['added_frames']} frames = +{res['if_inserted']['added_s']}s -> {res['if_inserted']['total']}")


def next_start(man, piece):
    """Frames from the join to the chapter title's first frame (the card must be gone by then)."""
    return man[f'title_{piece}']['f0'] - man[f'join_{piece}']['join']


# ---------------------------------------------------------------- the read-me
def readme():
    r = json.load(open(f'{OUT}/measure.json')); T = json.load(open(f'{OUT}/sheet_tiles.json'))
    man = json.load(open(f'{OUT}/ov/clips.json'))
    L = []
    A = L.append
    A('# One-way ticket: 720p motion proof\n')
    A(f'Written by `youtube/motion/proof.py readme` on {time.strftime("%d %b %Y, %-I:%M %p")} Pacific, from `measure.json` and `sheet_tiles.json` in this folder. '
      'Every number below was read back from the finished files. Nothing here is a 4K master.\n')
    A('## Files\n')
    A('| File | What it is | Length |\n|---|---|---|')
    A(f"| `{os.path.basename(NAME)}` | the proof: the approved cut with the motion picks, music mix | {r['frames']} frames, {r['video_s']:.3f} s = {tc(r['frames'])} ({r['video']}, {r['size_mib']} MiB) |")
    A(f'| `proof_sheet.jpg` | the one contact sheet, {len(T)} labelled tiles | still |')
    A('| `audio/mix_full.wav`, `audio/nomusic_full.wav` | the joined sound (music mix is on the proof) | same length as the picture |')
    A(f'| `ov/*.mov` | the {len(man)} overlay clips with alpha, listed in `ov/clips.json` | {sum(c["n"] for c in man)} frames in all |')
    A('| `shots/` | the clean 720p shots of each piece (no graphics) | see `shots/frames.json` |\n')
    A(f"The approved cut is {r['cut_frames']} frames = {r['cut_s']} s = {tc(r['cut_frames'])}. The proof is {r['frames']} frames, so it adds {r['added_frames']} frames. "
      f"Sound on the proof: {r['audio_s']:.3f} s.\n")
    A('## Does the route card sit over the cut, or add time?\n')
    j0 = r['joins'][0]; ins = r['if_inserted']
    A(f"**As built it sits over the cut and adds nothing.** Measured on the finished proof: {r['frames']} frames against the cut's {r['cut_frames']} "
      f"({r['added_frames']} added), {r['video_s']:.3f} s against {r['cut_s']} s. Each card is {j0['card_frames']} frames = {j0['card_s']} s, "
      f"{j0['before_cut']} frames before the join and {j0['after_cut']} after. It hides the whole picture for {j0['hides_all_frames']} of those frames "
      f"and part of it for {j0['partly_frames']} (the fade in and the light band wiping it off). The sound runs on underneath, unchanged.\n")
    A(f"**If the card were put in as its own second instead**, it would add {len(r['joins'])} x {j0['card_frames']} = {ins['added_frames']} frames = "
      f"{ins['added_s']} s, and the video would be {ins['total_frames']} frames = {ins['total_s']} s = {ins['total']} instead of {tc(r['cut_frames'])}. "
      'That would change the approved length, so it was not built.\n')
    A('What each card covers (frames are the proof\'s; "dark" is the share of the frame darker than a near-black level, measured on the proof):\n')
    A('| Into | Join at | Card frames | Picture fully hidden | Dark at -16 / -2 / +4 / +15 | Shot going out, shot coming in | Words spoken under the card |\n|---|---|---|---|---|---|---|')
    for j in r['joins']:
        d = j['dark_fraction']; o, i = j['outgoing'], j['incoming']
        w = ', '.join(f"{x['word']} ({x['rel_s'][0]:+.2f} to {x['rel_s'][1]:+.2f} s)" for x in j['words']) or 'none'
        A(f"| {chap(j['into'])} | {j['join_time']} (frame {j['join_frame']}) | {j['card_first']} to {j['card_last']} | "
          f"{j['hides_all'][0]} to {j['hides_all'][1]} | {d['-16']} / {d['-2']} / {d['+4']} / {d['+15']} | "
          f"{o['src']} {o['kind']} -> {i['src']} {i['kind']} | {w} |")
    A('\nThe word times come from the small.en transcripts placed by each edit list\'s dialog entries, so they are close, not exact.\n')
    A('## The contact sheet, tile by tile\n')
    A('| Tile | Time | Frame | Chapter | Shows |\n|---|---|---|---|---|')
    for t in T:
        A(f"| {t['tile']:02d} | {t['time']} | {t['frame']} | {t['chapter']} | {t['shows']} |")
    A('\n## Where each motion element is in the proof\n')
    A('| Element | Clip | First frame | Time | Frames |\n|---|---|---|---|---|')
    for c in man:
        A(f"| {c['what']} | `{c['name']}` | {c['f0']} | {tc(c['f0'])} | {c['n']} |")
    A('\n## Read this before judging it\n')
    A('- The look and timing follow the words of `youtube/PLAN.md` ("Motion picks for the 4K pass"). The mockup page those picks were made on is not on this Mac, so nothing here was matched against it.')
    A('- The host tag sits on his first on-camera shot, which is inside the opening hook. The older rule kept the hook free of text; it needs his call.')
    A('- The host tag leader ends in a ring beside the name; it is not tracked to his face.')
    A('- "NEXT" labels use the place words of each chapter\'s own title; the two time chapters show their time. Route positions are schematic.')
    A('- Ch1 uses the first 1,618 of its 1,620 rendered frames, as the rough cut did.')
    A(f"- The brand red read back from the proof (chapter tab): RGB {r['tab_red_rgb']} against #DE1A22 = [222, 26, 34].")
    A('- The picture comes from the 720p working copies (`mezz720`), each piece through its own `render_shots()`: grade, crop and blurs as approved, none of the old titles or the old corner HUD card.')
    A('- The sound was mixed again here from the same edit lists with each piece\'s own `music.py` and `mix.py`. Ch4\'s read-me asks for a 41 s music bed, which fails and is shorter than the 72.56 s chapter, so 76 s was used; the bed over the chapter is the same whatever length is asked for (76 and 79 s compared sample for sample).')
    A('- Word pops are the three in Ch3, drawn by Ch3\'s own `pop_frames()`, on the frames its master put them on.')
    A('- Not changed: the cut, the length, only the parts used, dash blur while the car is moving, the outro as filmed.')
    A('\n## Not checked\n')
    A('- The look against the mockup page (not on this Mac), and whether any of it is the look he wants: that is the checker\'s and his call.')
    A('- Facts on screen (place names, clock times, NEXT labels, route positions): not run through the facts check.')
    A('- Picture quality of the working copies beyond frame counts, sizes and a clean decode.')
    A('- The sound by ear. Loudness and peaks are in each `mix.json`; the joins are in `audio/audio_report.txt`.')
    A('- The proof against the old rough cut frame for frame: the rough cut files are not on this Mac.')
    open(f'{OUT}/PROOF_README.md', 'w').write('\n'.join(L) + '\n')
    log(f'readme: {len(L)} lines -> {OUT}/PROOF_README.md')


# ---------------------------------------------------------------- PLAN_4K step 6: the NO MUSIC master and the chapter list
NOMUSIC = NAME.replace('.mp4', '_NO_MUSIC.mp4')
# his own chapter names (../PLAN.md, "Chapters"); YouTube needs the first at 0:00
CHAPTER_NAMES = {'opening': 'Intro', 'ch1': '4:30 a.m.', 'ch2': 'Seattle · morning', 'ch3': 'Seattle, WA · noon', 'ch4': 'Into Oregon',
                 'ch5': 'Nampa, Idaho · night', 'ch6': '1:29 a.m.', 'ch7': 'Sunrise · Nevada', 'ch8': 'Las Vegas'}


def vmd5(path):
    return run([FF, '-v', 'error', '-i', path, '-map', '0:v:0', '-c', 'copy', '-f', 'md5', '-']).stdout.strip()


def nomusic():
    """The same picture (copied, not re-encoded) with the no-music sound (audio/nomusic_full.wav). No -shortest; the
    picture's frame count and stream md5 must match the music master, or the file is renamed .PICTURE_CHANGED.mp4."""
    if os.path.exists(NOMUSIC) and os.path.exists(NOMUSIC + '.ok'):
        log('nomusic: already done'); return
    assert os.path.exists(NAME + '.ok'), 'encode the music master first'
    wav = f'{OUT}/audio/nomusic_full.wav'
    t0 = time.time()
    run([FF, '-v', 'error', '-y', '-i', NAME, '-i', wav, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', NOMUSIC])
    a, b = nframes(NAME), nframes(NOMUSIC)
    ma, mb = vmd5(NAME), vmd5(NOMUSIC)
    log(f'nomusic: picture kept {b} of {a} frames, md5 {"identical" if ma == mb else "DIFFERENT"}, '
        f'{os.path.getsize(NOMUSIC) / 1048576:.1f} MiB, {time.time() - t0:.0f}s')
    if a != b or ma != mb or b != TOTAL:
        os.replace(NOMUSIC, NOMUSIC.replace('.mp4', '.PICTURE_CHANGED.mp4'))
        raise SystemExit('nomusic: picture changed')
    open(NOMUSIC + '.ok', 'w').write('ok')


def chapters():
    """OUT/chapters.txt for the YouTube description: one line per piece, at the cut into it (the route card's join
    frame), rounded down to the second."""
    man = {x['name']: x for x in json.load(open(f'{OUT}/ov/clips.json'))}
    L = []
    for piece, _ in PIECES:
        f = 0 if piece == 'opening' else man[f'join_{piece}']['join']
        s = int(f * 1001 / 30000)
        L.append((s, f'{s // 60}:{s % 60:02d} {CHAPTER_NAMES[piece]}'))
    gaps = [b[0] - a[0] for a, b in zip(L, L[1:])] + [int(TOTAL * 1001 / 30000) - L[-1][0]]
    assert min(gaps) >= 10, f'YouTube needs every chapter to be 10 s or longer: {gaps}'
    open(f'{OUT}/chapters.txt', 'w').write('\n'.join(t for _, t in L) + '\n')
    log(f'chapters: {len(L)} lines, shortest {min(gaps)} s -> {OUT}/chapters.txt')


STAGES = dict(preflight=preflight, shots=shots, audio=audio, overlays=overlays, encode=encode, sheet=sheet, measure=measure, readme=readme,
              nomusic=nomusic, chapters=chapters)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    todo = ARGS or ['all']
    if todo == ['all']:
        todo = ['shots', 'audio', 'overlays', 'encode', 'sheet', 'measure', 'readme']
    for s in todo:
        log(f'== {s}')
        STAGES[s]()
