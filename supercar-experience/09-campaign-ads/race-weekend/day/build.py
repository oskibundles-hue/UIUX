"""build.py - SE "F1 weekend" ad, direction C COUNTDOWN. One command builds everything.

  .venv/bin/python build/build.py --post-date 2026-10-04            full build -> exports/
  .venv/bin/python build/build.py --post-date 2026-10-11 --only front,comp,encode   (new date: graphics + encode)

Stages (each resumable; markers in .work/<date>/):
  config  config.js: DAYS = days from --post-date to Thu Nov 19 2026 (the countdown's ONE parameter)
  plate   edl.json -> graded plate frames (raw, 360 x 1080x1920) via ffmpeg
  front   front.html -> RGBA frames with motion blur (capture.py)
  audio   original synthesised score + accents (audio.py) -> mastered WAV (-14 LUFS, TP <= -1.5 dBTP)
  comp    plate + punch-ins / whips / freeze push + front -> lossless intermediate
  encode  Instagram-ready H.264 High two-pass ~11.5 Mb/s, AAC 48 kHz, faststart
"""
import argparse, datetime as dt, json, os, subprocess, sys, shutil
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'src', 'day.mp4')
PY = os.path.join(ROOT, '.venv', 'bin', 'python')
FPS_S = '24000/1001'; FPS = 24000 / 1001
W, H = 1080, 1920
RACE_START = dt.date(2026, 11, 19)
GRADE_YUV = 'eq=contrast=1.05:saturation=1.07'                                  # one DAY grade, on the native video
GRADE_RGB = 'colorchannelmixer=rr=1.025:gg=1.0:bb=0.985'                   # slight warmth, in RGB (no vignette: it dimmed the sky ~12%)
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
B = EDL['beat']
NFR = round(EDL['beats_total'] * B * FPS)            # v2: 388 frames = 16.183 s


def fr(beat): return round(beat * B * FPS)


def run(cmd, **kw):
    print('+', ' '.join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    subprocess.run(cmd, check=True, **kw)


# ---------------------------------------------------------------- config
def stage_config(post):
    days = (RACE_START - post).days
    # v3: no countdown on screen; DAYS is unused
    last = EDL['shots'][-1]
    freeze = last['b'][0] * B + 0.9            # day: the end-card light sweep runs 0.9 s after the hit (no freeze)
    cfg = {'DAYS': days, 'POST_DATE': post.isoformat(), 'FREEZE': round(freeze, 4)}
    open(os.path.join(HERE, 'config.js'), 'w').write('window.CONFIG = ' + json.dumps(cfg) + ';\n')
    print('config', cfg)
    return cfg


# ---------------------------------------------------------------- plate
def stage_plate(work):
    out = os.path.join(work, 'plate.rgb')
    if os.path.exists(out + '.ok'): return out
    f = open(out + '.tmp', 'wb')
    for s in EDL['shots']:
        n = fr(s['b'][1]) - fr(s['b'][0])
        sp = s['speed']
        if s.get('freeze'):
            nmov = round((s['src_end'] - s['src']) / sp * FPS)
        elif 'src_end' in s:                      # shot ends before the beat: hold its last frame
            nmov = min(n, int((s['src_end'] - s['src']) / sp * FPS))
        else:
            nmov = n
        dur = nmov / FPS * sp + (0.2 if 'src_end' not in s else 0.0)
        vf = f'setpts=(PTS-STARTPTS)/{sp}' if sp != 1 else 'setpts=PTS-STARTPTS'
        if sp != 1:
            vf += f',minterpolate=fps={FPS_S}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'
        vf += f',fps={FPS_S},{GRADE_YUV},scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24,{GRADE_RGB},format=rgb24'
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f"{s['src']:.3f}", '-t', f'{dur:.3f}', '-i', SRC,
                              '-vf', vf, '-frames:v', str(nmov), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, check=True).stdout
        got = len(raw) // (W * H * 3)
        if got < nmov: print(f'  WARN shot b{s["b"]}: {got}/{nmov} frames, holding last')
        frames = [raw[i * W * H * 3:(i + 1) * W * H * 3] for i in range(got)]
        while len(frames) < n: frames.append(frames[-1])
        for fb in frames[:n]: f.write(fb)
        print(f'  shot b{s["b"]} src {s["src"]} x{sp}: {n} frames ({got} decoded)', flush=True)
    f.close(); os.replace(out + '.tmp', out); open(out + '.ok', 'w').write('ok')
    return out


# ---------------------------------------------------------------- front
def stage_front(work):
    d = os.path.join(work, 'front')
    if os.path.exists(d + '.ok'): return d
    run([PY, os.path.join(HERE, 'capture.py'), 'seq', d, str(NFR)])
    open(d + '.ok', 'w').write('ok')
    return d


# ---------------------------------------------------------------- comp
def _scale_about(img, s, cx=540, cy=960):
    if abs(s - 1) < 1e-4: return img
    w2, h2 = round(W * s), round(H * s)
    big = img.resize((w2, h2), Image.BICUBIC)
    x0, y0 = round(cx * s - cx), round(cy * s - cy)
    return big.crop((x0, y0, x0 + W, y0 + H))


def _shimmer(a, k, seed):
    """heat-shimmer: rows slide sideways on a moving sine plus a soft lift, strength k (0-1)."""
    if k <= 0: return a
    ys = np.arange(H)
    off = (k * (10 * np.sin(ys / 23.0 + seed * 1.7) + 6 * np.sin(ys / 9.0 - seed * 2.3))).astype(int)
    idx = np.clip(np.arange(W)[None, :] - off[:, None], 0, W - 1)   # clamp at the frame edges (no wrapped seam)
    out = np.take_along_axis(a, idx[:, :, None].repeat(3, 2), axis=1)
    return np.clip(out.astype(np.float32) * (1 + 0.10 * k) + 10 * k, 0, 255).astype(np.uint8)


def _hblur(a, px):
    if px < 2: return a
    n = 15; acc = np.zeros_like(a, dtype=np.float32)
    for k in range(n):
        acc += np.roll(a, int(round((k / (n - 1) - 0.5) * px)), axis=1)
    return (acc / n).astype(np.uint8)


def stage_comp(work, plate, front, cfg):
    out = os.path.join(work, 'comp.mkv')
    if os.path.exists(out + '.ok'): return out
    cuts = [fr(s['b'][0]) for s in EDL['shots']]
    shimmer = {fr(b) for b in (5.5, 6.5125, 12, 14, 15.5, 24, 27, 30, 32, 32.5125)}   # heat-shimmer cuts (b4, b8, b16, b20, b28, b36 are sun-flare wipes)
    starts = {fr(s['b'][0]): s for s in EDL['shots']}
    freeze_f = round(cfg['FREEZE'] * FPS)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', FPS_S, '-i', '-', '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'gbrp', out + '.tmp.mkv'],   # stays RGB: no matrix guess
                           stdin=subprocess.PIPE)
    pf = open(plate, 'rb')
    shot = None
    for i in range(NFR):
        if i in starts: shot = starts[i]; s0 = i
        a = np.frombuffer(pf.read(W * H * 3), np.uint8).reshape(H, W, 3)
        img = Image.fromarray(a)
        sy = shot.get('shift_y', 0)
        if sy:
            c = Image.new('RGB', (W, H)); c.paste(img, (0, sy)); img = c
        # punch-in on every cut: 1.07 -> 1.0 over 5 frames
        k = i - s0
        s = 1 + 0.07 * max(0, 1 - k / 5) ** 2
        # end card: freeze push 1.0 -> 1.045
        if shot.get('freeze') and i >= freeze_f:
            s *= 1 + 0.045 * (i - freeze_f) / max(1, NFR - freeze_f)
        img = _scale_about(img, s, 540, 1080)
        a = np.asarray(img)
        # whip blur: 2 frames either side of a whip cut
        for c in shimmer:
            d = i - c
            if -2 <= d <= 2:
                a = _shimmer(a, [0.35, 0.8, 1.0, 0.7, 0.3][d + 2], i); break
        # small shake on the end-card hit
        if 0 <= i - fr(36) < 5:
            dy = (-1) ** i * (5 - (i - fr(36))) * 3
            a = a[np.clip(np.arange(H) - dy, 0, H - 1)]   # shift with edge clamp, not wrap
        fg = np.asarray(Image.open(os.path.join(front, f'{i:05d}.png')).convert('RGBA'), dtype=np.float32)
        al = fg[..., 3:4] / 255.0
        o = a.astype(np.float32) * (1 - al) + fg[..., :3] * al
        enc.stdin.write(o.clip(0, 255).astype(np.uint8).tobytes())
        if i % 60 == 0: print('comp', i, '/', NFR, flush=True)
    enc.stdin.close(); enc.wait()
    os.replace(out + '.tmp.mkv', out); open(out + '.ok', 'w').write('ok')
    return out


# ---------------------------------------------------------------- encode
def stage_encode(work, comp, wav, cfg):
    exp = os.path.join(ROOT, 'exports'); os.makedirs(exp, exist_ok=True)
    name = 'SE_F1_Weekend_Day-Duo_v3_RENT_9x16_CARSCENES-MUSIC_organic-OK_paid-needs-licence.mp4'
    out = os.path.join(exp, name)
    plog = os.path.join(work, 'x264pass')
    common = ['-i', comp, '-vf', 'scale=in_range=pc:out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-b:v', '11500k', '-maxrate', '14000k',
              '-bufsize', '23000k', '-color_range', 'tv', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
              '-r', FPS_S, '-g', '48', '-passlogfile', plog]
    run(['ffmpeg', '-v', 'error', '-y'] + common + ['-pass', '1', '-an', '-f', 'mp4', '/dev/null'])
    run(['ffmpeg', '-v', 'error', '-y'] + common[:2] + ['-i', wav] + common[2:] +
        ['-pass', '2', '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
         '-metadata', 'comment=Music: Car Scenes original (from Day Time Duo 1). Organic posts OK; paid ads only after Car Scenes confirms the licence.',
         '-movflags', '+faststart', out])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--post-date', default='2026-10-04', help='v3 has no countdown; only names the work folder')
    ap.add_argument('--only', default='config,plate,front,audio,comp,encode')
    a = ap.parse_args()
    post = dt.date.fromisoformat(a.post_date)
    st = a.only.split(',')
    cfg = stage_config(post)
    work = os.path.join(ROOT, '.work_day3'); os.makedirs(work, exist_ok=True)
    dwork = os.path.join(work, cfg['POST_DATE']); os.makedirs(dwork, exist_ok=True)
    # a different date re-renders the graphics, comp and encode; plate and audio are date-free and shared
    plate = stage_plate(work) if 'plate' in st else os.path.join(work, 'plate.rgb')
    front = stage_front(dwork) if 'front' in st else os.path.join(dwork, 'front')
    wav = os.path.join(work, 'mix_master.wav')
    if 'audio' in st and not os.path.exists(wav + '.ok'):
        run([PY, os.path.join(HERE, 'audio_day.py'), wav]); open(wav + '.ok', 'w').write('ok')
    comp = stage_comp(dwork, plate, front, cfg) if 'comp' in st else os.path.join(dwork, 'comp.mkv')
    if 'encode' in st:
        print('wrote', stage_encode(dwork, comp, wav, cfg))


if __name__ == '__main__':
    main()
