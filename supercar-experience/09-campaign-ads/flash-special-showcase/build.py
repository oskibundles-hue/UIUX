#!/usr/bin/env python3
"""
build.py -- ONE command for the SE flash-special showcase ("LOCKED ON", Porsche 911 GT3 RS, 18 s 9:16).

    python3 build.py                      # full render -> exports/*.mp4 + poster + QA stills + contact sheet
    python3 build.py --qa                 # QA gate: only the cue's check frames -> exports/qa/ (no mp4)
    python3 build.py --frames 0,206,370   # just these frames -> .work/stills/
    options: --ffmpeg PATH  --footage DIR  --workers 2  --stage source,dense,plate,front,finish,qa

Stages (each is cached in .work/ and skipped when its output exists; delete the file to redo):
  source   decode GT3RS_livery.mov IN FRAME ORDER (never -ss) -> .work/src_gt.npy, then blur the
           licence plate in place on source frames 226-246 (tracked box, lib/data/plate_track.json)
  dense    optical-flow in-betweens (ffmpeg minterpolate, fed by frame number) for beat 14's slow-mo
  timeline per-frame source map (lib/edl.py) -> .work/timeline.js; config.json -> .work/config.js;
           lib/data/tracks.json -> .work/tracks.js  (the front page loads all three)
  plate    lib/plate.py + lib/warehouse.py -> .work/plate.npy  (uint8, 432 x 1920 x 1080 x 3)
  front    front.html captured by lib/kcapture.js with sub-frame motion blur -> .work/front/NNNNN.png
  finish   plate + front (alpha over) -> vignette 0.42 -> grain 0.035 (last) -> x264 + the bed (as-is)
  qa       QA stills, contact sheet, loudness print, ffprobe summary

Everything that is a figure or a claim lives in config.json. Nothing else needs editing to change the
price, hours or end time: re-run `python3 build.py` (the front layer and the behind-car type both
re-render; the cached source/dense stages are reused).
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from multiprocessing import get_context

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(ROOT, 'lib')
sys.path.insert(0, LIB)
import edl  # noqa: E402

WORK = os.path.join(ROOT, '.work')
EXP = os.path.join(ROOT, 'exports')
SCRATCH = '/tmp/claude-0/-home-user-UIUX/2e2fc1bb-c45d-5ce1-ba97-afbf7647f193/scratchpad'
H, W = 1920, 1080
NAME = 'SCE_Flash-Special-Showcase_GT3RS-Locked-On_18s-9x16.mp4'
AUDIO = os.path.join(ROOT, 'audio', 'bed_hero.wav')
QA_TIMES = [0, 0.47, 0.70, 2.30, 3.30, 4.00, 5.90, 6.38, 6.50, 6.90, 7.90, 8.40, 8.62, 8.84, 9.43, 9.90,
            10.50, 11.00, 11.20, 12.70, 13.30, 14.00, 14.15, 14.25, 14.40, 14.60, 15.30, 16.40, 17.99]


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ------------------------------------------------------------------------------------ stages
def st_source(A):
    npy = os.path.join(WORK, 'src_gt.npy')
    ok = os.path.join(WORK, 'src_gt.ok')
    if os.path.exists(ok):
        return
    src = os.path.join(A.footage, 'GT3RS_livery.mov')
    log('source: decoding', src, 'in frame order')
    p = subprocess.Popen([A.ffmpeg, '-v', 'error', '-threads', '2', '-i', src, '-map', '0:v:0',
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
    frames = []
    fs = W * H * 3
    tmp = os.path.join(WORK, 'src_gt.raw')
    n = 0
    with open(tmp, 'wb') as fo:
        while True:
            b = p.stdout.read(fs)
            if len(b) < fs:
                break
            fo.write(b)
            n += 1
    p.wait()
    assert n == 335, n
    mm = np.lib.format.open_memmap(npy, mode='w+', dtype=np.uint8, shape=(n, H, W, 3))
    mm[:] = np.fromfile(tmp, np.uint8).reshape(n, H, W, 3)
    mm.flush()
    del mm
    os.remove(tmp)
    import plate
    log('source: blurring the licence plate on f226-246 (drive-away) and f9-22 (corner under the wing)')
    plate.plate_blur(npy, os.path.join(LIB, 'data', 'plate_track.json'), 'plate', 226, 246)
    plate.plate_blur(npy, os.path.join(LIB, 'data', 'plate2_track.json'), 'plate2', 9, 22)
    open(ok, 'w').write('decoded %d frames; plate blurred f226-246 and f9-22\n' % n)


def st_source_plate3(A):
    """fix r1: beat 15 now uses the rear tracking shot f206-224, where the Montana plate is readable.
    Tracked with lib/track.py (box 262,943,118,59 on f206 -> lib/data/plate3_track.json) and blurred in
    place like the other two. Separate marker so an existing decoded cache is upgraded, not re-decoded."""
    ok = os.path.join(WORK, 'src_gt.plate3.ok')
    if os.path.exists(ok):
        return
    import plate
    log('source: blurring the licence plate on f206-224 (rear tracking, beat 15)')
    plate.plate_blur(os.path.join(WORK, 'src_gt.npy'), os.path.join(LIB, 'data', 'plate3_track.json'),
                     'plate3', 206, 224)
    open(ok, 'w').write('plate blurred f206-224\n')


def st_dense(A):
    import plate
    for B in edl.BEATS:
        if 'dense' in B:
            fa, fb, k = B['dense']
            out = os.path.join(WORK, f'dense_b{B["id"]}_{fa}_{fb}_{k}.npy')
            if not os.path.exists(out):
                log(f'dense: minterpolate f{fa}-f{fb} x{k} (beat {B["id"]})')
                plate.make_dense(A.ffmpeg, os.path.join(WORK, 'src_gt.npy'), fa, fb, k, out)


def st_timeline(A):
    import fx
    tl, meta = edl.build()
    json.dump(dict(tl=tl, meta=meta), open(os.path.join(WORK, 'timeline.json'), 'w'))
    # plate shake at the drop (fx.impact k=2,3) so the offer panel can shake with it
    shake = {}
    for k in range(0, 6):
        dx, dy, rot = fx.shake_offsets(k, amp=24 * 1.0, seed=edl.IMPACT_SEED)
        shake[edl.DROP_FRAME + k] = [round(dx, 2), round(dy, 2)]
    js = dict(fps=edl.FPS, nf=edl.NF, p=[None if r['p'] is None else round(r['p'], 4) for r in tl],
              beat=[r['beat'] for r in tl], shake=shake,
              beats={B['id']: [B['i0'], B['i1']] for B in edl.BEATS}, tEnd=edl.snap(edl.T_END))
    open(os.path.join(WORK, 'timeline.js'), 'w').write('window.TL=' + json.dumps(js) + ';\n')
    C = json.load(open(os.path.join(ROOT, 'config.json')))
    open(os.path.join(WORK, 'config.js'), 'w').write('window.CONFIG=' + json.dumps(C) + ';\n')
    T = json.load(open(os.path.join(LIB, 'data', 'tracks.json')))
    open(os.path.join(WORK, 'tracks.js'), 'w').write('window.TRACKS=' + json.dumps(T) + ';\n')


_P = None


def _init_worker():
    global _P
    os.nice(10)
    import plate
    import warehouse
    tl = json.load(open(os.path.join(WORK, 'timeline.json')))['tl']
    wh = warehouse.Warehouse(WORK, os.path.join(ROOT, 'config.json'))
    _P = plate.Plate(WORK, tl, wh)


def _do_unit(u):
    t0 = time.time()
    res = _P.render_unit(u)
    mm = np.load(os.path.join(WORK, 'plate.npy'), mmap_mode='r+')
    for i, f in res.items():
        mm[i] = (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)
    mm.flush()
    return list(res), time.time() - t0


def st_plate(A, frames):
    npy = os.path.join(WORK, 'plate.npy')
    if not os.path.exists(npy):
        np.lib.format.open_memmap(npy, mode='w+', dtype=np.uint8, shape=(edl.NF, H, W, 3)).flush()
    done_p = os.path.join(WORK, 'plate.done.json')
    done = set(json.load(open(done_p))) if os.path.exists(done_p) else set()
    if A.force_plate:
        done -= set(frames)
    todo = [i for i in frames if i not in done]
    if not todo:
        return
    import plate
    tl = json.load(open(os.path.join(WORK, 'timeline.json')))['tl']
    units = plate.Plate.__new__(plate.Plate)
    units.whip_at = {edl.fr(t): d for t, d in edl.WHIPS}
    us = plate.Plate.units(units, todo)
    # heavy warehouse frames first so the pool drains evenly
    us.sort(key=lambda u: -(u[1] >= 288) * 3 - len(u[2]))
    log(f'plate: {len(todo)} frames in {len(us)} units, {A.workers} workers')
    t0 = time.time()
    with get_context('fork').Pool(A.workers, initializer=_init_worker) as pool:
        for n, (fs, dt) in enumerate(pool.imap_unordered(_do_unit, us)):
            done |= set(fs)
            if n % 20 == 0:
                log(f'  plate unit {n + 1}/{len(us)} frames {fs[0]}.. {dt:.1f}s')
                json.dump(sorted(done), open(done_p, 'w'))
    json.dump(sorted(done), open(done_p, 'w'))
    log(f'plate: done in {time.time() - t0:.0f}s')


def st_front(A, frames=None, outdir=None):
    outdir = outdir or os.path.join(WORK, 'front')
    os.makedirs(outdir, exist_ok=True)
    cmd = ['nice', '-n', '10', 'node', os.path.join(LIB, 'kcapture.js'), os.path.join(ROOT, 'front.html'), outdir]
    if frames is None:
        cmd += ['seq', repr(edl.FPS), repr(edl.DUR), '--workers', '2']
    else:
        todo = [i for i in frames if A.force_front or not os.path.exists(os.path.join(outdir, f'{i:05d}.png'))]
        if not todo:
            return
        cmd += ['frames', repr(edl.FPS), ','.join(map(str, todo)), '--workers', '2']
    log('front:', ' '.join(cmd[3:]))
    subprocess.run(cmd, check=True)


def finish_frame(i, plate_mm=None):
    import fx
    mm = plate_mm if plate_mm is not None else np.load(os.path.join(WORK, 'plate.npy'), mmap_mode='r')
    base = mm[i].astype(np.float32) * (1 / 255)
    fp = os.path.join(WORK, 'front', f'{i:05d}.png')
    if os.path.exists(fp):
        fr_ = np.asarray(Image.open(fp).convert('RGBA'), np.float32) * (1 / 255)
        a = fr_[..., 3:4]
        base = fr_[..., :3] * a + base * (1 - a)
    base = fx.vignette(base, 0.42)
    base = fx.grain(base, i, amount=0.035)
    return (np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)


def _fin(i):
    return i, finish_frame(i).tobytes()


def _fin_init():
    os.nice(10)


def st_finish(A):
    out = os.path.join(EXP, NAME)
    log('finish: composite + vignette + grain -> x264 crf16 slow + AAC 192k (bed as-is)')
    cmd = ['nice', '-n', '10', A.ffmpeg, '-v', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '24000/1001', '-i', '-',
           '-i', AUDIO, '-map', '0:v', '-map', '1:a',
           '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-profile:v', 'high', '-threads', '2',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', '18.0180',
           '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with get_context('fork').Pool(A.workers, initializer=_fin_init) as pool:
        for i, b in pool.imap(_fin, range(edl.NF), chunksize=4):
            p.stdin.write(b)
            if i % 48 == 0:
                log(f'  finish frame {i}')
    p.stdin.close()
    p.wait()
    assert p.returncode == 0
    log(f'finish: {out} in {time.time() - t0:.0f}s')
    return out


# ------------------------------------------------------------------------------------ QA
def qa_frames():
    fs = {edl.fr(t) if t < 17.99 else edl.NF - 1 for t in QA_TIMES}
    fs |= set(range(edl.fr(8.62), edl.fr(9.45) + 1))          # every reel frame
    fs |= set(range(edl.fr(5.571), edl.fr(6.429) + 1))        # plate check
    return sorted(fs)


def save_still(i, path, img=None):
    img = finish_frame(i) if img is None else img
    Image.fromarray(img).save(path, quality=92)


def contact_sheet(frames, path, cols=8, tw=216):
    th = int(tw * 16 / 9)
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new('RGB', (cols * tw, rows * (th + 18)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for k, (i, img) in enumerate(frames):
        x, y = (k % cols) * tw, (k // cols) * (th + 18)
        sheet.paste(Image.fromarray(img).resize((tw, th), Image.LANCZOS), (x, y + 18))
        d.text((x + 4, y + 3), f'f{i}  {i / edl.FPS:.3f}s', fill=(251, 209, 1))
    sheet.save(path, quality=88)


def run_qa_gate(A):
    fs = qa_frames()
    st_plate(A, sorted(set(fs) | set(u for f in fs for u in whip_window(f))))
    st_front(A, fs)
    qd = os.path.join(EXP, 'qa')
    os.makedirs(qd, exist_ok=True)
    imgs = []
    for i in fs:
        img = finish_frame(i)
        Image.fromarray(img).save(os.path.join(qd, f'gate_f{i:03d}_{i / edl.FPS:06.3f}s.jpg'), quality=92)
        imgs.append((i, img))
    contact_sheet(imgs, os.path.join(qd, 'gate_contact.jpg'))
    log('QA gate stills ->', qd)


def whip_window(i):
    for t, _ in edl.WHIPS:
        b = edl.fr(t)
        if b - edl.WHIP_K <= i < b + edl.WHIP_K:
            return range(b - edl.WHIP_K, b + edl.WHIP_K)
    return [i]


def st_qa(A, mp4):
    qd = os.path.join(EXP, 'qa')
    os.makedirs(qd, exist_ok=True)
    # decode the delivered mp4 (not the intermediates) for the stills
    fs = sorted({edl.fr(t) if t < 17.99 else edl.NF - 1 for t in QA_TIMES})
    for old in os.listdir(qd):                                  # stale stills from earlier renders
        if old.startswith('final_f'):
            os.remove(os.path.join(qd, old))
    raw = subprocess.run([A.ffmpeg, '-v', 'error', '-i', mp4, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    allf = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    log('qa: decoded', len(allf), 'frames from the mp4')
    imgs = []
    for i in fs:
        Image.fromarray(allf[i]).save(os.path.join(qd, f'final_f{i:03d}_{i / edl.FPS:06.3f}s.jpg'), quality=92)
        imgs.append((i, allf[i]))
    contact_sheet(imgs, os.path.join(EXP, 'contact-sheet.jpg'), cols=7, tw=240)
    # poster = frame 0 (complete hook: FLASH SPECIAL / TODAY ONLY / ENDS {endTime} + SCE lockup);
    # poster-endcard.jpg = the held last frame (logo, car name, price, offer, contact) as an alternate cover
    Image.fromarray(allf[0]).save(os.path.join(EXP, 'poster.jpg'), quality=94)
    Image.fromarray(allf[-1]).save(os.path.join(EXP, 'poster-endcard.jpg'), quality=94)
    every = [(i, allf[i]) for i in range(0, len(allf), 6)]
    contact_sheet(every, os.path.join(qd, 'every6_contact.jpg'), cols=12, tw=150)
    # loudness + probe
    ln = subprocess.run([A.ffmpeg, '-hide_banner', '-nostats', '-i', mp4, '-af', 'loudnorm=print_format=json',
                         '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(ln[ln.rindex('{'):ln.rindex('}') + 1])
    probe = subprocess.run([A.ffmpeg, '-hide_banner', '-i', mp4], capture_output=True, text=True).stderr
    summ = dict(loudness=dict(I=j['input_i'], TP=j['input_tp'], LRA=j['input_lra']),
                probe=[l.strip() for l in probe.splitlines() if 'Stream' in l or 'Duration' in l],
                frames=len(allf))
    json.dump(summ, open(os.path.join(qd, 'qa_summary.json'), 'w'), indent=1)
    log('qa:', json.dumps(summ))
    return summ


# ------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', os.path.join(SCRATCH, 'ffmpeg')))
    ap.add_argument('--footage', default=os.path.join(SCRATCH, 'footage'))
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--qa', action='store_true')
    ap.add_argument('--frames', default=None)
    ap.add_argument('--stage', default='source,dense,timeline,plate,front,finish,qa')
    ap.add_argument('--force-plate', action='store_true')
    ap.add_argument('--force-front', action='store_true')
    A = ap.parse_args()
    os.environ['FFMPEG'] = A.ffmpeg
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(EXP, exist_ok=True)
    stages = A.stage.split(',')
    if 'source' in stages:
        st_source(A)
        st_source_plate3(A)
    if 'dense' in stages:
        st_dense(A)
    if 'timeline' in stages:
        st_timeline(A)
    if A.qa:
        run_qa_gate(A)
        return
    if A.frames:
        fs = [int(x) for x in A.frames.split(',')]
        st_plate(A, sorted(set(fs) | set(u for f in fs for u in whip_window(f))))
        st_front(A, fs)
        sd = os.path.join(WORK, 'stills')
        os.makedirs(sd, exist_ok=True)
        for i in fs:
            save_still(i, os.path.join(sd, f'f{i:03d}.jpg'))
        log('stills ->', sd)
        return
    if 'plate' in stages:
        st_plate(A, list(range(edl.NF)))
    if 'front' in stages:
        if A.force_front or not os.path.exists(os.path.join(WORK, 'front', f'{edl.NF - 1:05d}.png')):
            st_front(A)
    mp4 = os.path.join(EXP, NAME)
    if 'finish' in stages:
        mp4 = st_finish(A)
    if 'qa' in stages:
        st_qa(A, mp4)


if __name__ == '__main__':
    main()
