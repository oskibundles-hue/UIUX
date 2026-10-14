#!/usr/bin/env python3
"""
build.py -- ONE command for the Locked-On layer of the 2026-09-15 rally vlog (reel cut, 1080x1920, 29.97 fps).

    python3 build.py                  # everything -> exports/*.mp4 + poster + contact sheet + QA
    python3 build.py --stage qa       # re-run only the QA on the existing export
    python3 build.py --stills 0,142,3850   # composite single frames -> .work/stills/ (no mp4)
    options: --ffmpeg PATH  --video PATH  --stage prep,front,audio,compose,qa  --force-front

Stages (cached in .work/):
  prep     config.json -> .work/config.js, lib/data/tracks.json -> .work/tracks.js, story.html timing tables
           (WINDOWS / TIMES / KT_PLAN) -> .work/page.json via lib/pageinfo.js
  front    story.html captured by lib/kcapture.js (sub-frame motion blur, transparent) -> .work/front/NNNNN.png,
           only for frames whose shutter touches an on-screen window; 3 capture processes in parallel.
           Re-rendered when story.html, kinetic.js, config.json or the tracks change (.work/front.sig).
  audio    lib/mix.py -> .work/mix.wav (the vlog's own audio untouched + quiet accents + tail, -14 LUFS)
  compose  ffmpeg: source (tpad +48 black frames) -> RGB, overlay the PNG layer (straight alpha), -> bt709
           yuv420p, x264 High two-pass 11 Mb/s, AAC 256k 48 kHz, +faststart -> exports/<NAME>
  qa       stills from the delivered mp4, poster.jpg (frame 0), contact sheet, coverage checks on the layer's
           alpha (old title, pills, SE bug, captions, end card), loudness (loudnorm print), true peak,
           trailing silence, A/V durations -> exports/qa/
The source is the approved T7 cut (captions, labels, plate blurs are already burned in); nothing in it is
re-edited. Measured anchors live in config.json; how they were measured is in cue.md.
"""
import argparse, hashlib, json, math, os, re, shutil, struct, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(ROOT, 'lib')
WORK = os.path.join(ROOT, '.work')
EXP = os.path.join(ROOT, 'exports')
QA = os.path.join(EXP, 'qa')
C = json.load(open(os.path.join(ROOT, 'config.json')))
FPS = 30000 / 1001
W, H = 1080, 1920
NSRC = C['source']['frames']
NF = NSRC + C['source']['extendFrames']
NAME = '01 2026-09-15 the rally, dinner and the drive back (reel cut) SE LOCKED-ON - INSTAGRAM 1080x1920.mp4'
AN = C['anchors']


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def _hash(*paths):
    h = hashlib.sha1()
    for p in paths:
        h.update(open(p, 'rb').read()); h.update(b'|')
    return h.hexdigest()[:16]


# ------------------------------------------------------------------------------------ prep
def st_prep(A):
    os.makedirs(WORK, exist_ok=True)
    open(os.path.join(WORK, 'config.js'), 'w').write('window.CONFIG=' + json.dumps(C) + ';\n')
    T = json.load(open(os.path.join(LIB, 'data', 'tracks.json')))
    open(os.path.join(WORK, 'tracks.js'), 'w').write('window.TRACKS=' + json.dumps(T) + ';\n')
    out = subprocess.run(['node', os.path.join(LIB, 'pageinfo.js'), os.path.join(ROOT, 'story.html')],
                         capture_output=True, text=True, check=True).stdout
    pj = os.path.join(WORK, 'page.json')
    if not os.path.exists(pj) or open(pj).read() != out:     # rewrite only on change (the audio stage keys on its mtime)
        open(pj, 'w').write(out)
        log('prep: page timing tables changed -> .work/page.json')
    else:
        log('prep: page timing tables unchanged')


def page():
    return json.load(open(os.path.join(WORK, 'page.json')))


def active_frames(pg):
    """Frames whose (widest, 270-degree) shutter touches an on-screen window."""
    half = 0.40 / FPS
    fs = []
    for i in range(NF):
        t = i / FPS
        if any(t + half >= a and t - half <= b for a, b in pg['WINDOWS']):
            fs.append(i)
    return fs


# ------------------------------------------------------------------------------------ front
def front_sig():
    return _hash(os.path.join(ROOT, 'story.html'), os.path.join(LIB, 'kinetic.js'), os.path.join(LIB, 'kcapture.js'),
                 os.path.join(LIB, 'accum.py'), os.path.join(WORK, 'config.js'), os.path.join(WORK, 'tracks.js'))


def capture(frames, outdir, nproc=3):
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
        procs.append(subprocess.Popen(['nice', '-n', '5', 'node', os.path.join(LIB, 'kcapture.js'), os.path.join(ROOT, 'story.html'),
                                       outdir, 'list', '30000/1001', lf, '--workers', '1'],
                                      stderr=open(os.path.join(WORK, f'capture_{k}.log'), 'w')))
    for p in procs:
        p.wait()
        assert p.returncode == 0, 'kcapture failed, see .work/capture_*.log'


def st_front(A):
    pg = page()
    fs = active_frames(pg)
    out = os.path.join(WORK, 'front')
    sigp = os.path.join(WORK, 'front.sig')
    sig = front_sig()
    old = open(sigp).read().strip() if os.path.exists(sigp) else ''
    if old != sig or A.force_front:
        shutil.rmtree(out, ignore_errors=True)
    todo = [i for i in fs if not os.path.exists(os.path.join(out, f'{i:05d}.png'))]
    if todo:
        log(f'front: capturing {len(todo)} of {len(fs)} layer frames (3 processes)')
        t0 = time.time()
        capture(todo, out)
        log(f'front: done in {time.time() - t0:.0f}s')
    open(sigp, 'w').write(sig)
    json.dump(fs, open(os.path.join(WORK, 'front_frames.json'), 'w'))


# ------------------------------------------------------------------------------------ audio
def st_audio(A):
    out = os.path.join(WORK, 'mix.wav')
    deps = [os.path.join(LIB, 'mix.py'), os.path.join(LIB, 'synth.py'), os.path.join(WORK, 'page.json'),
            os.path.join(LIB, 'data', 'captions.json')]
    if os.path.exists(out) and all(os.path.getmtime(out) >= os.path.getmtime(d) for d in deps) and not A.force_audio:
        return
    log('audio: mixing')
    sh([sys.executable, os.path.join(LIB, 'mix.py'), '--video', A.video, '--ffmpeg', A.ffmpeg,
        '--times', os.path.join(WORK, 'page.json'), '--captions', os.path.join(LIB, 'data', 'captions.json'),
        '--out', out, '--report', os.path.join(WORK, 'mix.json'), '--dump-bus', os.path.join(WORK, 'accents.wav')])


# ------------------------------------------------------------------------------------ compose
def build_sequence():
    """.work/seq/NNNNN.png for every output frame: the captured layer frame, or a hard link to one blank."""
    seq = os.path.join(WORK, 'seq')
    shutil.rmtree(seq, ignore_errors=True)
    os.makedirs(seq)
    blank = os.path.join(WORK, 'blank.png')
    Image.new('RGBA', (W, H), (0, 0, 0, 0)).save(blank)
    front = os.path.join(WORK, 'front')
    for i in range(NF):
        src = os.path.join(front, f'{i:05d}.png')
        if os.path.exists(src) and Image.open(src).mode != 'RGBA':      # one pixel format for the whole sequence
            Image.open(src).convert('RGBA').save(src, compress_level=1)
        os.link(src if os.path.exists(src) else blank, os.path.join(seq, f'{i:05d}.png'))
    return seq


def ff_graph():
    ext = C['source']['extendFrames']
    return (f'[0:v]tpad=stop_mode=add:stop={ext}:color=black,'
            'scale=in_color_matrix=bt709:in_range=tv,format=gbrp[b];'
            '[1:v]format=rgba[o];'
            '[b][o]overlay=format=gbrp:eof_action=pass:shortest=0,'
            'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[v]')


def st_compose(A):
    seq = build_sequence()
    os.makedirs(EXP, exist_ok=True)
    out = os.path.join(EXP, NAME)
    plog = os.path.join(WORK, 'x264pass')
    common = [A.ffmpeg, '-v', 'error', '-y', '-i', A.video, '-framerate', '30000/1001', '-i', os.path.join(seq, '%05d.png')]
    venc = ['-map', '[v]', '-frames:v', str(NF), '-r', '30000/1001', '-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high',
            '-pix_fmt', 'yuv420p', '-b:v', '11M', '-maxrate', '16M', '-bufsize', '22M', '-passlogfile', plog,
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
            '-x264-params', 'keyint=60:min-keyint=30']
    t0 = time.time()
    log('compose: pass 1 / 2')
    sh(common + ['-filter_complex', ff_graph()] + venc + ['-pass', '1', '-an', '-f', 'null', '-'])
    log(f'compose: pass 2 / 2 ({time.time() - t0:.0f}s so far)')
    sh(common + ['-i', os.path.join(WORK, 'mix.wav'), '-filter_complex', ff_graph()] + venc +
       ['-pass', '2', '-map', '2:a', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2',
        '-movflags', '+faststart', '-metadata', 'title=The rally, dinner & the drive back (SE Locked-On)', out])
    log(f'compose: {out} in {time.time() - t0:.0f}s')
    return out


# ------------------------------------------------------------------------------------ QA
def decode_frames(path, idx, ff):
    """Decode the given frame indices from an mp4 (frame-accurate: select by n)."""
    idx = sorted(set(idx))
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    raw = subprocess.run([ff, '-v', 'error', '-i', path, '-vf', f"select='{sel}'", '-fps_mode', 'passthrough',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    assert len(arr) == len(idx), (len(arr), len(idx))
    return dict(zip(idx, arr))


def mp4_track_durations(path):
    """Presentation duration of each track (edit list / movie timescale), as players see it."""
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


def alpha(i):
    p = os.path.join(WORK, 'front', f'{i:05d}.png')
    if not os.path.exists(p):
        return None
    im = Image.open(p)
    assert im.mode == 'RGBA', f'{p} is {im.mode}, not RGBA'
    return np.asarray(im)[..., 3]


def composite_check(mp4, ff):
    """End to end: wherever the layer is fully opaque, the delivered frame must show the layer. Streams the
    whole mp4 once and compares every layer frame (catches a lost or shifted overlay frame)."""
    fl = sorted(json.load(open(os.path.join(WORK, 'front_frames.json'))))
    want = set(fl)
    p = subprocess.Popen([ff, '-v', 'error', '-i', mp4, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    fsz = W * H * 3; i = 0; worst = (0.0, -1); bad = []; n = 0
    while True:
        b = p.stdout.read(fsz)
        if len(b) < fsz:
            break
        if i in want:
            im = np.asarray(Image.open(os.path.join(WORK, 'front', f'{i:05d}.png')))
            m = im[..., 3] == 255
            # compare the interior of opaque areas only (2 px erosion): x264 legitimately softens thin edges
            # (5 px brackets, glyph outlines); a lost or shifted layer frame differs by 30+ levels everywhere
            for _ in range(2):
                m = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
            if m.sum() > 2000:
                f = np.frombuffer(b, np.uint8).reshape(H, W, 3)
                d = float(np.abs(f[m].astype(np.int16) - im[..., :3][m].astype(np.int16)).mean())
                n += 1
                if d > worst[0]:
                    worst = (d, i)
                if d > 10:
                    bad.append((i, round(d, 1)))
        i += 1
    p.wait()
    return dict(frames_decoded=i, layer_frames_compared=n, worst_mean_abs_diff=round(worst[0], 2), worst_frame=worst[1],
                frames_over_10=bad[:30], n_bad=len(bad), ok=(len(bad) == 0 and i == NF))


def coverage_checks(pg):
    """Numeric checks on the captured layer's alpha channel (255 = our opaque panel)."""
    res = {}
    T = pg['TIMES']
    fr = lambda t: int(math.floor(t * FPS + 1e-6))

    def cover(name, frames, box, need=250):
        x0, y0, x1, y1 = box
        worst = 255
        for i in frames:
            a = alpha(i)
            m = 0 if a is None else int(a[y0:y1 + 1, x0:x1 + 1].min())
            worst = min(worst, m)
        res[name] = dict(frames=[frames[0], frames[-1]], box=box, min_alpha=worst, ok=worst >= need)

    def clear(name, frames, box):
        x0, y0, x1, y1 = box
        worst = 0; bad = []
        for i in frames:
            a = alpha(i)
            m = 0 if a is None else int(a[y0:y1 + 1, x0:x1 + 1].max())
            if m > 0:
                bad.append(i)
            worst = max(worst, m)
        res[name] = dict(frames=[frames[0], frames[-1]], box=box, max_alpha=worst, frames_touching=bad[:20],
                         n_touching=len(bad), ok=worst == 0)

    tb = AN['titleBox']
    cover('hook_covers_old_title_f0_to_f77', list(range(0, AN['titleLast'] + 1)), [tb[0] - 6, tb[1] - 6, tb[2] + 6, tb[3] + 6])
    for k, key in ((1, 'pill1'), (2, 'pill2')):
        p = AN[key]; bx = p['box']
        cx, cy, hw, hh = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2, (bx[2] - bx[0]) / 2 * 1.05, (bx[3] - bx[1]) / 2 * 1.05
        box = [int(cx - hw) - 4, int(cy - hh) - 4, int(cx + hw) + 4, int(cy + hh) + 4]
        cover(f'ch0{k}_covers_pill{k}', list(range(p['first'] - 1, p['last'] + 1)), box)
    # SE bug: nothing of ours on it, ever, before the end card
    bb = AN['bugBox']
    clear('se_bug_clear', list(range(0, AN['endCardFirst'])), [bb[0] - 20, bb[1] - 14, bb[2] + 20, bb[3] + 14])
    # follow card (34-38 s, top-left): no layer frames at all in that span
    fl = [i for i in range(fr(33.5), fr(38.5))]
    clear('follow_card_clear', fl, [0, 300, 1080, 700])
    # captions: the layer never touches the caption box area while a caption is on screen
    cap = json.load(open(os.path.join(LIB, 'data', 'captions.json')))
    word = np.array(cap['word'], bool)
    on = np.zeros(NSRC, bool)
    for i in np.where(word)[0]:            # a caption page stays up around its highlighted words
        on[max(0, i - 20):min(NSRC, i + 21)] = True
    on[AN['endCardFirst']:] = False        # the old end card: captions are gone from f3810 (measured)
    cb = AN['captionBand']
    clear('captions_clear', [i for i in range(NSRC) if on[i]], [40, cb[0], 1040, cb[1]])
    # end card: full frame, opaque from f3814 to the last frame
    e0 = fr(T['end'] + T['END_WIPE']) + 1           # first frame whose whole shutter is after the wipe landed
    cover('end_card_full_frame', list(range(e0, NF)), [0, 0, W - 1, H - 1], need=255)
    res['end_card_first_opaque_frame'] = e0
    built = T['end'] + 0.60                           # the last end-card line (the credit) settles at t0 + 0.60 s
    res['end_card_fully_built_s'] = round(built, 3)
    res['end_card_readable_s'] = round(NF / FPS - built, 3)     # from fully built to the end of the last frame
    # route ticks: no gold in the tick box on the frame before the word, gold fill on the word frame
    ticks = []
    for k, rt in enumerate(AN['routeTicks']):
        x0, y0, x1, y1 = [int(round(v)) for v in T['routeBoxes'][k]]
        def gold(i):
            im = np.asarray(Image.open(os.path.join(WORK, 'front', f'{i:05d}.png')).convert('RGBA')).astype(int)
            c = im[y0 + 4:y1 - 4, x0 + 4:x1 - 4]
            g = (c[..., 0] > 200) & (c[..., 1] > 160) & (c[..., 2] < 90) & (c[..., 3] > 200)
            return round(float(g.mean()), 3)
        f = rt['frame']
        ticks.append(dict(word=rt['word'], frame=f, gold_before=gold(f - 1), gold_on_word=gold(f), ok=gold(f - 1) == 0 and gold(f) > 0.5))
    res['route_ticks_on_word_frame'] = dict(ticks=ticks, ok=all(x['ok'] for x in ticks))
    return res


def st_qa(A, mp4=None):
    mp4 = mp4 or os.path.join(EXP, NAME)
    os.makedirs(QA, exist_ok=True)
    for f in os.listdir(QA):
        if f.endswith('.jpg'):
            os.remove(os.path.join(QA, f))
    pg = page(); T = pg['TIMES']
    fr = lambda t: int(round(t * FPS))
    # stills: every element at entry / middle / exit (+ frame edges of the covering checks)
    marks = {'hook_f000': 0, 'hook_mid': fr(1.3), 'hook_f077_last_title_frame': 77, 'hook_f078': 78, 'hook_exit': fr(T['hookExit'] + 0.15)}
    for k, c in enumerate(T['ch']):
        marks[f'ch{k + 1}_in'] = fr(c['ts'] + 0.12); marks[f'ch{k + 1}_mid'] = fr((c['ts'] + c['tx']) / 2)
        marks[f'ch{k + 1}_out'] = fr(c['tx'] + 0.12)
    for key in ('pill1', 'pill2'):
        p = AN[key]; marks[f'{key}_first_f{p["first"]}'] = p['first']; marks[f'{key}_last_f{p["last"]}'] = p['last']
    marks['route_in'] = fr(T['routeIn'] + 0.4); marks['route_out'] = fr(T['routeOut'] + 0.15)
    for k, tk in enumerate(T['ticks']):
        f = AN['routeTicks'][k]['frame']
        marks[f'route_tick{k + 1}_f{f - 1}_before'] = f - 1; marks[f'route_tick{k + 1}_f{f}_word'] = f
        marks[f'route_tick{k + 1}_f{f + 4}'] = f + 4
    for key in ('soe', 'urus'):
        L = T[key]
        marks[f'{key}_acquire'] = fr(L['a'] + 0.1); marks[f'{key}_mid'] = fr((L['a'] + L['x']) / 2); marks[f'{key}_exit'] = fr(L['x'] + 0.12)
    marks['urus_start_f3222'] = 3222; marks['urus_late_f3380'] = 3380
    e = fr(T['end'])
    for d in (-1, 0, 1, 2, 3, 4, 5, 7, 10, 20):
        marks[f'end_f{e + d}'] = e + d
    marks['end_last_frame'] = NF - 1
    frames = decode_frames(mp4, list(marks.values()), A.ffmpeg)
    for nm, i in sorted(marks.items(), key=lambda kv: kv[1]):
        Image.fromarray(frames[i]).save(os.path.join(QA, f'f{i:05d}_{i / FPS:07.3f}s_{nm}.jpg'), quality=90)
    Image.fromarray(frames[0]).save(os.path.join(EXP, 'poster.jpg'), quality=94)
    # contact sheet: one frame per 2 s of the delivered file + every element's middle
    cs = sorted(set(list(range(0, NF, 60)) + [NF - 1]))
    dec = decode_frames(mp4, cs, A.ffmpeg)
    contact_sheet([(i, dec[i]) for i in cs], os.path.join(EXP, 'contact-sheet.jpg'), cols=11, tw=180)
    contact_sheet(sorted([(i, frames[i]) for i in set(marks.values())]), os.path.join(QA, 'element-sheet.jpg'), cols=10, tw=200)
    # audio + container
    err = subprocess.run([A.ffmpeg, '-hide_banner', '-nostats', '-i', mp4, '-map', '0:a', '-af',
                          'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    ln = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', err, re.S).group(0))
    raw = subprocess.run([A.ffmpeg, '-v', 'error', '-i', mp4, '-map', '0:a', '-f', 'f32le', '-ac', '2', '-ar', '48000', '-'],
                         capture_output=True, check=True).stdout
    au = np.frombuffer(raw, '<f4').reshape(-1, 2)
    nz = np.where(np.abs(au).max(1) > 1e-6)[0]
    tail_ms = 1000 * (len(au) - 1 - nz[-1]) / 48000
    last50 = float(np.abs(au[-2400:]).max())
    probe = subprocess.run([A.ffmpeg, '-hide_banner', '-i', mp4], capture_output=True, text=True).stderr
    durs = mp4_track_durations(mp4)
    size = os.path.getsize(mp4)
    cov = coverage_checks(pg)
    cov['mp4_shows_layer_on_every_opaque_pixel'] = composite_check(mp4, A.ffmpeg)
    summ = dict(file=os.path.basename(mp4), bytes=size, MB=round(size / 1e6, 2), track_durations_s=durs,
                frames=NF, picture_s=round(NF / FPS, 4), audio_decoded_s=round(len(au) / 48000, 4),
                loudnorm=dict(I=float(ln['input_i']), TP=float(ln['input_tp']), LRA=float(ln['input_lra'])),
                trailing_silence_ms=round(tail_ms, 1), last_50ms_peak=last50,
                stream_lines=[l.strip() for l in probe.splitlines() if 'Stream #' in l or 'Duration' in l],
                coverage=cov)
    json.dump(summ, open(os.path.join(QA, 'qa_summary.json'), 'w'), indent=1)
    log(f"qa: {summ['MB']} MB, durations {durs}, I {summ['loudnorm']['I']} LUFS, TP {summ['loudnorm']['TP']} dBTP, "
        f"tail {tail_ms:.0f} ms silent")
    for k, v in cov.items():
        log('   ', k, v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk in ('ok', 'min_alpha', 'max_alpha', 'n_touching', 'frames_touching')})


def contact_sheet(frames, path, cols=8, tw=216):
    th = int(tw * 16 / 9)
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new('RGB', (cols * tw, rows * (th + 16)), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for k, (i, img) in enumerate(frames):
        x, y = (k % cols) * tw, (k // cols) * (th + 16)
        sheet.paste(Image.fromarray(img).resize((tw, th), Image.LANCZOS), (x, y + 16))
        d.text((x + 3, y + 2), f'f{i} {i / FPS:.2f}s', fill=(251, 209, 1))
    sheet.save(path, quality=86)


# ------------------------------------------------------------------------------------ stills (dev)
def stills(A, idx):
    out = os.path.join(WORK, 'stills')
    os.makedirs(out, exist_ok=True)
    capture(idx, out, nproc=1)
    src = decode_frames(A.video, [min(i, NSRC - 1) for i in idx], A.ffmpeg)
    for i in idx:
        base = src[min(i, NSRC - 1)].astype(np.float32) / 255 if i < NSRC else np.zeros((H, W, 3), np.float32)
        o = np.asarray(Image.open(os.path.join(out, f'{i:05d}.png')).convert('RGBA'), np.float32) / 255
        a = o[..., 3:4]
        Image.fromarray((np.clip(o[..., :3] * a + base * (1 - a), 0, 1) * 255 + .5).astype(np.uint8)).save(os.path.join(out, f'c{i:05d}.png'))
    log('stills ->', out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', C['source']['ffmpeg']))
    ap.add_argument('--video', default=os.environ.get('VIDEO', C['source']['video']))
    ap.add_argument('--stage', default='prep,front,audio,compose,qa')
    ap.add_argument('--stills')
    ap.add_argument('--force-front', action='store_true'); ap.add_argument('--force-audio', action='store_true')
    A = ap.parse_args()
    st = A.stage.split(',')
    if A.stills:
        st_prep(A); stills(A, [int(x) for x in A.stills.split(',')]); return
    if 'prep' in st: st_prep(A)
    if 'front' in st: st_front(A)
    if 'audio' in st: st_audio(A)
    mp4 = st_compose(A) if 'compose' in st else None
    if 'qa' in st: st_qa(A, mp4)


if __name__ == '__main__':
    main()
