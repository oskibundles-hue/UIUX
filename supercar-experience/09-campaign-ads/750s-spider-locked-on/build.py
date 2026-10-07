#!/usr/bin/env python3
"""
build.py -- one-command build of "ROOF DOWN" (McLaren 750S Spider, LOCKED ON standard), 18.018 s 9:16.

    python3 build.py                     # every stage, cached (only what changed re-renders)
    python3 build.py --stage prep,front  # named stages only
    python3 build.py --frames 0,113,335  # stills of those output frames -> .work/stills/ (plate+mid+front)
    python3 build.py --qa                # QA stage only, on the delivered files
    python3 build.py --format 4x5        # a placement version: 4x5 (1080x1350) or 1x1 (1080x1080); see lib/formats.py

Stages
  source  decode SCE_McLaren-750S_no-branding.mov in frame order (never -ss) -> .work/src.npy (1080x1920)
  dense   4x optical-flow in-betweens of every shot played at a non-integer speed (lib/dense.py) -> .work/dense_*.npy
  prep    .work/config.js, timeline.js, tracks.js for the HTML layers
  plate   lib/plate.py -> .work/plate/*.png (+ .work/matte/*.png on the roof shot)
  front   front.html via lib/kcapture.js (sub-frame motion blur) -> .work/front/*.png
  mid     mid.html (behind-the-car type) -> .work/mid/*.png, roof shot only
  audio   audio/bed.py -> audio/bed.wav (the clip's own music + accents, -14 LUFS)
  finish  plate, vignette, mid x sky matte, the crash punch, front, grain -> x264: one Instagram-ready file per edit,
          exports/*.mp4 (two-pass ~11.5 Mb/s, H.264 High 4.2, AAC 48 kHz, fast start), with the bed muxed as-is.
          Omarie, 28 Sept 2026: "I just need Instagram ready reels... I don't need 2 videos per video", so no
          separate master is written
  qa      stills at the check frames, contact sheet, loudness, probe, safe-zone ink audit -> exports/qa/

Placement versions (--format 4x5 | 1x1) reuse every cached stage. They crop the plate, sky matte and layers to a
per-shot window (lib/formats.py), then vignette, crash punch and grain on the new frame, and encode
exports/*-<fmt>.mp4 with the same bed. 4x5 uses the approved 9:16 layers as they are; 1x1 renders its
own front layer (front_1x1.html: the square's hook and end card) into .work/front_1x1/ for those frames only and
composites the approved 9:16 layer everywhere else. QA goes to exports/qa_<fmt>/. The finish stage will not re-encode
over an approved render (SHA-256 in lib/formats.py APPROVED) unless --force is given.

Looks (--look NAME): the same edit, plate, sky matte, tracks, timing, copy and sound under a completely different
graphics package: front_<look>.html and mid_<look>.html (+ lib/<look>.js) render into .work/front_<look>/ and
.work/mid_<look>/, composite into .work/final_<look>/ and encode exports/SCE_750S-Spider_Roof-Down_<Name>_18s-9x16.mp4,
QA in exports/qa_<look>/. 9:16 only. The default look, locked-on, is the approved ad and its caches are untouched.

Needs Python 3 + numpy + Pillow, ffmpeg with libx264, Node 22 + Playwright (/opt/node22/lib/node_modules).
"""
import argparse
import functools
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))
import edl  # noqa: E402
import formats  # noqa: E402
import fx  # noqa: E402

WORK = os.path.join(HERE, '.work')
EXP = os.path.join(HERE, 'exports')
NAME = 'SCE_750S-Spider_Roof-Down_Locked-On_18s-9x16'
FMT = '9x16'                                          # set by --format (module level so the Pool workers see it)
LOOK = 'locked-on'                                    # set by --look (passed to Pool workers explicitly, like the format)
# graphics packages over the same edit: name (in the file name), pages, extra libraries in their cache signature
LOOKS = {
    'locked-on': dict(name='Locked-On', front='front.html', mid='mid.html', libs=[]),
    'now-boarding': dict(name='Now-Boarding', front='front_now-boarding.html', mid='mid_now-boarding.html',
                         libs=['lib/flap.js']),
    'paste-up': dict(name='Paste-Up', front='front_paste-up.html', mid='mid_paste-up.html', libs=['lib/paper.js']),
}


def lsub(look=None):
    """'' for the approved look, '_<look>' for the others (cache, final and QA folder suffix)"""
    look = look or LOOK
    return '' if look == 'locked-on' else '_' + look


CLIP = 'SCE_McLaren-750S_no-branding.mov'
FPS_STR = '24000/1001'
FF = os.environ.get('FFMPEG', shutil.which('ffmpeg') or 'ffmpeg')
NODE = shutil.which('node') or 'node'
ROOF0 = edl.beat(16)['i0']


def run(cmd, **kw):
    print('  $', ' '.join(str(c) for c in cmd)[:200], flush=True)
    return subprocess.run(cmd, check=True, **kw)


def sig_of(paths, extra=''):
    h = hashlib.sha1(extra.encode())
    for p in paths:
        h.update(open(p, 'rb').read())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------ stages
def st_source(a):
    dst = os.path.join(WORK, 'src.npy')
    if os.path.exists(dst):
        return
    src = os.path.join(a.footage, CLIP)
    n = 584
    mm = np.lib.format.open_memmap(dst + '.tmp', mode='w+', dtype=np.uint8, shape=(n, 1920, 1080, 3))
    p = subprocess.Popen([FF, '-v', 'error', '-i', src, '-map', '0:v', '-vf',
                          'scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix=bt709:in_range=tv,format=rgb24',
                          '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    fb = 1920 * 1080 * 3
    for i in range(n):
        mm[i] = np.frombuffer(p.stdout.read(fb), np.uint8).reshape(1920, 1080, 3)
    p.wait()
    mm.flush()
    del mm
    os.replace(dst + '.tmp', dst)


def st_dense(a):
    import dense
    if not all(os.path.exists(dense.path(*r)) for r in dense.RANGES):
        run([sys.executable, os.path.join(HERE, 'lib', 'dense.py'), '--ffmpeg', FF])


def st_prep(a):
    C = json.load(open(os.path.join(HERE, 'config.json')))
    open(os.path.join(WORK, 'config.js'), 'w').write('window.CONFIG = ' + json.dumps(C) + ';\n')
    tl = edl.build()
    shake = {}
    for f0, strength, seed, n in edl.IMPACTS[:1]:
        for k in range(2):
            dx, dy, _ = fx.shake_offsets(k, amp=24 * strength, seed=seed)
            shake[f0 + k] = [round(dx, 2), round(dy, 2)]
    T = dict(fps=edl.FPS, nf=edl.NF, g0=edl.G0, beat=edl.BEAT, tEnd=edl.T_END, tDrop=edl.T_DROP,
             tCrash=edl.T_CRASH, tStop=edl.T_STOP0, beats={B['id']: [B['i0'], B['i1']] for B in edl.BEATS},
             p=[None if r['p'] is None else round(r['p'], 4) for r in tl], shake=shake)
    open(os.path.join(WORK, 'timeline.js'), 'w').write('window.TL = ' + json.dumps(T) + ';\n')
    tr = json.load(open(os.path.join(HERE, 'lib', 'data', 'tracks.json')))
    open(os.path.join(WORK, 'tracks.js'), 'w').write('window.TRACKS = ' + json.dumps(tr) + ';\n')


def st_plate(a):
    cmd = [sys.executable, os.path.join(HERE, 'lib', 'plate.py'), '--workers', str(a.workers)]
    if a.frames:
        cmd += ['--frames', a.frames]
    run(cmd)


def capture(page, outdir, frames, jobs=3):
    """kcapture.js in `frames` mode, split over `jobs` browsers (contiguous chunks)"""
    os.makedirs(outdir, exist_ok=True)
    if not frames:
        return
    per = (len(frames) + jobs - 1) // jobs
    chunks = [frames[k:k + per] for k in range(0, len(frames), per)]
    fps = f'{24000 / 1001:.10f}'

    def one(ch):
        return subprocess.run([NODE, os.path.join(HERE, 'lib', 'kcapture.js'), page, outdir, 'frames', fps,
                               ','.join(map(str, ch)), '--workers', '1'], check=True, cwd=HERE)
    with ThreadPoolExecutor(len(chunks)) as ex:
        list(ex.map(one, chunks))


def layer_stage(a, page, sub, frames, extra=()):
    out = os.path.join(WORK, sub)
    base = (page.split('#')[0], 'lib/kinetic.js', 'lib/lock.js', 'lib/kcapture.js', 'lib/accum.py', '.work/config.js',
            '.work/timeline.js', '.work/tracks.js')
    libs = [os.path.join(HERE, p) for p in (*base, *extra)]
    s = sig_of(libs, page.split('#', 1)[1] if '#' in page else '')
    sp = os.path.join(WORK, sub + '.sig')
    if a.frames:
        frames = [f for f in map(int, a.frames.split(',')) if f in frames]
    elif os.path.exists(sp) and open(sp).read() == s and all(os.path.exists(os.path.join(out, f'{i:05d}.png')) for i in frames):
        print(f'  {sub}: up to date')
        return
    capture(page, out, frames)
    if not a.frames:
        open(sp, 'w').write(s)


def st_front(a):
    if LOOK != 'locked-on':
        L = LOOKS[LOOK]
        layer_stage(a, L['front'], 'front' + lsub(), list(range(edl.NF)), L['libs'])
        return
    lay = formats.FORMATS[FMT]['front']
    if lay == '9x16':
        layer_stage(a, 'front.html', 'front', list(range(edl.NF)))
    else:                                             # the format's own layout, only where it differs (formats.py)
        layer_stage(a, f'front_{lay}.html', 'front_' + lay, [i for i in range(edl.NF) if formats.own_front(FMT, i)])


def st_mid(a):
    L = LOOKS[LOOK]
    layer_stage(a, L['mid'], 'mid' + lsub(), list(range(ROOF0, edl.NF)), L['libs'])


def st_audio(a):
    out = os.path.join(HERE, 'audio', 'bed.wav')
    src = [os.path.join(HERE, 'audio', 'bed.py'), os.path.join(HERE, 'audio', 'synth.py'), os.path.join(HERE, 'lib', 'edl.py')]
    if os.path.exists(out) and os.path.getmtime(out) > max(os.path.getmtime(p) for p in src):
        print('  audio: up to date')
        return
    run([sys.executable, os.path.join(HERE, 'audio', 'bed.py'), '--footage', a.footage, '--ffmpeg', FF])


# ------------------------------------------------------------------------------------------ finish
def over(base, layer_png, matte_png=None, rows=None):
    if not os.path.exists(layer_png):
        return base
    L = np.asarray(Image.open(layer_png).convert('RGBA'), np.float32) / 255
    al = L[..., 3:4]
    if matte_png is not None:
        al = al * (np.asarray(Image.open(matte_png), np.float32)[..., None] / 255)
    if rows is not None:                              # placement versions: the crop window of a plate-sized layer
        L, al = L[rows], al[rows]
    return base * (1 - al) + L[..., :3] * al


def composite(i, fmt=None, look=None):
    fmt, look = fmt or FMT, look or LOOK              # explicit in Pool workers (spawn start method on macOS)
    F = formats.FORMATS[fmt]
    gy, py = formats.y0(fmt, i), formats.plate_y0(fmt, i)
    rows, prows = slice(gy, gy + F['h']), slice(py, py + F['h'])  # graphics / picture windows (lib/formats.py)
    base = np.asarray(Image.open(os.path.join(WORK, 'plate', f'{i:05d}.png')).convert('RGB'), np.float32)[prows] / 255
    # the vignette goes on the picture only, so the brand gold (front and behind-car type) arrives exact
    base = fx.vignette(base, 0.36)
    if i >= ROOF0:
        base = over(base, os.path.join(WORK, 'mid' + lsub(look), f'{i:05d}.png'), os.path.join(WORK, 'matte', f'{i:05d}.png'),
                    prows)
    k = i - edl.CRASH_F
    if 0 <= k < edl.CRASH_N:
        # the crash hit on plate + matted type together, so the type stays locked behind the car (review r1)
        u = min(k / (edl.CRASH_N - 1), 1.0)
        base = fx.transform(base, scale=1 + edl.CRASH_PUNCH * (1 - (1 - (1 - u) ** 3)))
        if k == 0:
            base = base * (1 + edl.CRASH_LIFT)
    fdir = formats.front_dir(fmt, i) if look == 'locked-on' else 'front' + lsub(look)
    base = over(base, os.path.join(WORK, fdir, f'{i:05d}.png'), rows=rows)
    base = fx.grain(base, i, amount=0.02)
    return fx.to_u8(base)


def final_dir(fmt=None, look=None):
    fmt = fmt or FMT
    return os.path.join(WORK, ('final' if fmt == '9x16' else 'final_' + fmt) + lsub(look))


def exp_dir(look=None):
    """exports/ holds the approved look; proposed looks go to exports/proposed/ so nothing that picks up every mp4
    in exports/ can take an unapproved one"""
    return EXP if (look or LOOK) == 'locked-on' else os.path.join(EXP, 'proposed')


def out_name(fmt=None, look=None):
    fmt, look = fmt or FMT, look or LOOK
    n = NAME.replace('Locked-On', LOOKS[look]['name'])
    return n if fmt == '9x16' else n.replace('-9x16', '-' + fmt)


def _comp_to(i, fmt, look):
    im = composite(i, fmt, look)
    Image.fromarray(im).save(os.path.join(final_dir(fmt, look), f'{i:05d}.png'), compress_level=1)
    return i


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def approved_intact(fmt):
    """True when exports/ holds this format's approved files, byte for byte (lib/formats.py APPROVED)"""
    ap = formats.APPROVED.get(fmt)
    if not ap:
        return False
    f = os.path.join(EXP, out_name(fmt) + '.mp4')        # the Instagram-ready file (ap[1], the retired master, is kept
    return os.path.exists(f) and sha256(f) == ap[0]      # in APPROVED as a record only)


def st_finish(a):
    if LOOK == 'locked-on' and approved_intact(FMT) and not a.force:
        print(f'  {FMT}: exports/ holds the approved render (SHA-256 as in lib/formats.py APPROVED); not re-encoding it.'
              ' Pass --force to rebuild (the result then needs approving again).')
        return
    os.makedirs(exp_dir(), exist_ok=True)
    os.makedirs(final_dir(), exist_ok=True)
    with Pool(a.workers) as pool:
        for k, _ in enumerate(pool.imap(functools.partial(_comp_to, fmt=FMT, look=LOOK), range(edl.NF), chunksize=4)):
            if k % 48 == 0:
                print(f'  composite {k}/{edl.NF}', flush=True)
    bed = os.path.join(HERE, 'audio', 'bed.wav')
    seq = os.path.join(final_dir(), '%05d.png')
    vf = 'scale=out_color_matrix=bt709:out_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p'
    tags = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
    aud = ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000']
    deliv = os.path.join(exp_dir(), out_name() + '.mp4')
    plog = os.path.join(WORK, ('x264pass' if FMT == '9x16' else 'x264pass_' + FMT) + lsub())
    b, mx, buf = formats.FORMATS[FMT]['rate']
    common = ['-framerate', FPS_STR, '-i', seq, '-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{b}k',
              '-maxrate', f'{mx}k', '-bufsize', f'{buf}k', '-profile:v', 'high', '-level', '4.2', '-g', '24', '-bf', '2',
              *tags]
    run([FF, '-y', '-v', 'error', *common, '-pass', '1', '-passlogfile', plog, '-an', '-f', 'mp4', os.devnull])
    run([FF, '-y', '-v', 'error', *common[:4], '-i', bed, '-map', '0:v', '-map', '1:a', *common[4:], '-pass', '2',
         '-passlogfile', plog, *aud, '-shortest', '-movflags', '+faststart', deliv])
    print(f'  wrote {os.path.relpath(deliv, HERE)}  {os.path.getsize(deliv) / 1e6:.1f} MB')


# ------------------------------------------------------------------------------------------ qa
# every hold, cut and hit, plus every whip-exit frame (review r1: a vertical whip turned $1,299 into a readable
# $1,200 on frames the QA stills did not cover) and the end-card price rise
QA_FRAMES = [0, 5, 7, 12, 24, 25, 46, 47, 66, 67, 68, 69, 76, 90, 108, 109, 110, 111, 112, 113, 114, 115, 124, 127, 128,
             135, 136, 150, 158, 163, 168, 169, 180, 187, 188, 189, 190, 191, 196, 202, 210, 223, 224, 235, 246, 253,
             254, 255, 256, 257, 262, 268, 273, 277, 281, 290, 293, 299, 300, 318, 324, 332, 334, 335, 336, 337, 338,
             339, 340, 341, 345, 360, 400, 431]


AUDIT_FRAMES = [0, 24, 46, 60, 95, 105, 140, 150, 175, 186, 200, 215, 230, 244, 300, 318, 345, 360, 400, 431]
# PASTE-UP pieces are slapped again on beat hits (one drawing, two frames), and a hit is a held piece, so those
# frames are audited too (the review of 28 Sept found paper 7-9 px past x 54 on them that the list above missed)
LOOK_AUDIT = {'paste-up': [124, 125, 130, 131, 136, 137, 138, 139, 158, 159, 290, 291]}


def st_qa(a):
    F = formats.FORMATS[FMT]
    sfx = ('' if FMT == '9x16' else '-' + FMT) + lsub().replace('_', '-')
    qa = os.path.join(exp_dir(), ('qa' if FMT == '9x16' else 'qa_' + FMT) + lsub())
    os.makedirs(qa, exist_ok=True)
    for f in os.listdir(qa):                          # no stale stills from an earlier render
        if f.endswith('.jpg'):
            os.remove(os.path.join(qa, f))
    deliv = os.path.join(exp_dir(), out_name() + '.mp4')
    raw = subprocess.run([FF, '-v', 'error', '-i', deliv, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, F['h'], F['w'], 3)
    n = len(frames)
    for i in QA_FRAMES:
        if i < n:
            Image.fromarray(frames[i]).save(os.path.join(qa, f'f{i:03d}_{i / edl.FPS:06.3f}s.jpg'), quality=90)
    Image.fromarray(frames[0]).save(os.path.join(exp_dir(), f'poster{sfx}.jpg'), quality=92)
    Image.fromarray(frames[n - 1]).save(os.path.join(exp_dir(), f'poster-endcard{sfx}.jpg'), quality=92)
    # contact sheet: every 6th frame
    cols, w, h = 12, 180, 180 * F['h'] // F['w']
    sel = list(range(0, n, 6))
    sheet = Image.new('RGB', (cols * w, ((len(sel) + cols - 1) // cols) * h))
    d = ImageDraw.Draw(sheet)
    for k, i in enumerate(sel):
        x, y = (k % cols) * w, (k // cols) * h
        sheet.paste(Image.fromarray(frames[i]).resize((w, h)), (x, y))
        d.rectangle([x, y, x + 64, y + 14], fill='black')
        d.text((x + 2, y + 2), f'{i} {i / edl.FPS:.2f}s', fill=(251, 209, 1))
    sheet.save(os.path.join(exp_dir(), f'contact-sheet{sfx}.jpg'), quality=86)
    # loudness + probe + tail silence
    r = subprocess.run([FF, '-hide_banner', '-nostats', '-i', deliv, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True)
    loud = json.loads(re.findall(r'\{[^{}]+\}', r.stderr)[-1])
    pr = subprocess.run([FF, '-hide_banner', '-i', deliv], capture_output=True, text=True).stderr
    au = subprocess.run([FF, '-v', 'error', '-i', deliv, '-map', '0:a', '-f', 'f32le', '-ac', '2', '-ar', '48000', '-'],
                        capture_output=True, check=True).stdout
    A = np.frombuffer(au, '<f4').reshape(-1, 2)
    summary = dict(frames=n, video_seconds=n / edl.FPS, audio_seconds=len(A) / 48000,
                   loudness=dict(I=loud['input_i'], TP=loud['input_tp'], LRA=loud['input_lra']),
                   last_50ms_peak=float(np.abs(A[-2400:]).max()),
                   streams=[l.strip() for l in pr.splitlines() if 'Stream #' in l],
                   sizes_mb={f: round(os.path.getsize(os.path.join(exp_dir(), f)) / 1e6, 2) for f in os.listdir(exp_dir())
                             if f.endswith('.mp4') and f.startswith(out_name())})
    # safe-zone ink audit, on pixels: the bright opaque ink (white / gold) of the front and mid layers at every
    # held frame (whip exits and fly-ins are in motion by design and are skipped) must stay inside the format's
    # safe box (lib/formats.py SAFE; 9:16 is the SE story safe zone x 54..907, y 269..1536), measured in output
    # pixels after the crop. Mid-layer ink is counted only where the sky matte shows it.
    Z = formats.SAFE[FMT]
    viol = []
    for i in AUDIT_FRAMES + LOOK_AUDIT.get(LOOK, []):
        for layer in (formats.front_dir(FMT, i) if LOOK == 'locked-on' else 'front' + lsub(), 'mid' + lsub()):
            y0 = formats.plate_y0(FMT, i) if layer.startswith('mid') else formats.y0(FMT, i)
            p = os.path.join(WORK, layer, f'{i:05d}.png')
            if not os.path.exists(p):
                continue
            L = np.asarray(Image.open(p).convert('RGBA'), np.float32) / 255
            al = L[..., 3]
            mp = os.path.join(WORK, 'matte', f'{i:05d}.png')
            if layer.startswith('mid') and os.path.exists(mp):
                al = al * np.asarray(Image.open(mp), np.float32) / 255
            L, al = L[y0:y0 + F['h']], al[y0:y0 + F['h']]
            ys, xs = np.nonzero((al > 0.5) & (L[..., :3].max(-1) > 0.55))
            if len(xs) and (xs.min() < Z['x0'] or xs.max() > Z['x1'] or ys.min() < Z['y0'] or ys.max() > Z['y1']):
                viol.append(dict(frame=i, layer=layer, x=[int(xs.min()), int(xs.max())], y=[int(ys.min()), int(ys.max())]))
    summary['safe_zone_violations'] = viol
    json.dump(summary, open(os.path.join(qa, 'qa_summary.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != 'streams'}, indent=1))


def st_stills(a):
    """--frames: composite just those frames (plate / mid / front must exist) -> .work/stills/"""
    os.makedirs(os.path.join(WORK, 'stills'), exist_ok=True)
    sfx = ('' if FMT == '9x16' else '_' + FMT) + lsub()
    for i in map(int, a.frames.split(',')):
        Image.fromarray(composite(i)).save(os.path.join(WORK, 'stills', f'f{i:03d}{sfx}.jpg'), quality=92)
    print('  stills ->', os.path.relpath(os.path.join(WORK, 'stills'), HERE))


STAGES = dict(source=st_source, dense=st_dense, prep=st_prep, plate=st_plate, front=st_front, mid=st_mid,
              audio=st_audio, finish=st_finish, qa=st_qa)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='')
    ap.add_argument('--frames', default='')
    ap.add_argument('--qa', action='store_true')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--format', default='9x16', choices=sorted(formats.FORMATS))
    ap.add_argument('--look', default='locked-on', choices=sorted(LOOKS), help='graphics package (see LOOKS)')
    ap.add_argument('--force', action='store_true', help='re-encode even over an approved render')
    ap.add_argument('--footage', default=os.environ.get('FOOTAGE', os.path.join(HERE, '.work', 'footage')))
    a = ap.parse_args()
    global FMT, LOOK
    FMT, LOOK = a.format, a.look
    if LOOK != 'locked-on' and FMT != '9x16':
        ap.error('--look renders the 9:16 only')
    os.makedirs(WORK, exist_ok=True)
    if a.qa:
        names = ['qa']
    elif a.stage:
        names = a.stage.split(',')
    elif a.frames:
        names = ['source', 'dense', 'prep', 'plate', 'front', 'mid']
    else:
        names = list(STAGES)
    for nme in names:
        print(f'== {nme}', flush=True)
        STAGES[nme](a)
    if a.frames and not a.stage:
        st_stills(a)


if __name__ == '__main__':
    main()
