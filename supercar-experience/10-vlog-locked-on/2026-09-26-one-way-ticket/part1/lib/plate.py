#!/usr/bin/env python3
"""
plate.py -- the picture edit of the rally vlog v2: EDL -> graded, reframed 1080x1920 29.97 plate.

Stages (called from build.py):
  shots   one file per EDL shot in .work/shots/NN.mov (x264 CRF 10, yuv444p). Per shot:
            * source frames from the mezzanine (native 59.94 / 29.97 fps, ffmpeg accurate seek, frame by
              frame; 59.94 drops every other frame at 1x; ramps pick and shutter-average source frames),
            * the grade: a per-shot 3D LUT (ffmpeg lut3d, tetrahedral) built from fx.NightGrade fitted
              on five sample frames of the shot's own crop window (normalises exposure per shot), in
              one of three looks (night / interior / day) of the same family,
            * the reframe: a 1080x1920 window (s = 1) or smaller (push-in, s > 1) moving from c0/s0 to
              c1/s1 (config.json `shots`), bicubic, eased,
            * extra post-roll frames when the next boundary has a gold light sweep (the old shot keeps
              playing on the right of the sweep line).
  join    all shots in order -> .work/plate.mov (x264 CRF 12), with the transitions:
            * whips (fx.whip, 3+3 frames) in the cold open and the CH6 montage,
            * the gold light sweep's plate switch at chapter changes (the layer draws the light band; the
              switch line here uses the same geometry as sekit.js SEK.sweep),
            * impacts (fx.impact, toned down) on the hard cut at 4.0 s and on the DROP,
            * the chapter-slam plate punch (same formula as SEK.chapterSlam's window.FX.punch),
            * the end card: the last shot runs on under the card's wipe, then black.
  sheet   QA stills: first / middle / last frame of every shot from the plate -> contact sheets.

Every shot's source range, including ramps, handles and post-roll, is checked against the forbidden
source moments (config.json `forbidden`) before anything renders.
"""
import hashlib, json, math, os, re, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fx  # noqa: E402

FPS = 30000 / 1001
W, H = 1080, 1920
WORK = os.path.join(ROOT, '.work')
from cfg import load_config  # noqa: E402
CFG = load_config()
P = CFG['paths']
FF = os.environ.get('FFMPEG', P['ffmpeg'])
EDL = json.load(open(P['edl']))
NF = int(round(EDL['duration'] * FPS))
SHOTS = EDL['shots']
for _k, _sl in CFG.get('slips', {}).items():      # per-shot source slips over the EDL (config "slips")
    if _k.startswith('_'):
        continue
    _s = SHOTS[int(_k)]
    _s['edl_in'], _s['edl_speed'] = _s['in'], _s['speed']
    _s['in'] = _sl.get('in', _s['in'])
    _s['speed'] = _sl.get('speed', _s['speed'])
    _s['out'] = round(_s['in'] + _s['dur'] * _s['speed'], 3)
RENDER_VERSION = 2


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ------------------------------------------------------------------------------------ timeline
def shot_frames():
    """[(k, f0, f1)] output frame ranges, contiguous, last shot to NF."""
    out = []
    for k, s in enumerate(SHOTS):
        f0 = int(round(s['t'] * FPS))
        f1 = int(round(SHOTS[k + 1]['t'] * FPS)) if k + 1 < len(SHOTS) else NF
        out.append((k, f0, f1))
    return out


FR = shot_frames()


def scfg(k):
    """per-shot config (reframe, look, ramp) merged over the defaults."""
    d = dict(CFG['shotDefaults'])
    d.update(CFG['shots'].get(str(k), {}))
    return d


def boundary(k):
    """transition INTO shot k (from k-1): dict or None."""
    for tr in CFG['transitions']:
        if tr['into'] == k:
            return tr
    return None


def post_frames(k):
    """post-roll frames shot k must render for a sweep into k+1."""
    tr = boundary(k + 1)
    if tr and tr['type'] == 'sweep':
        return int(math.ceil(tr['dur'] * FPS)) + 1
    if k + 1 < len(SHOTS) and SHOTS[k + 1]['src'] == 'card':
        return int(math.ceil(CFG['endCard']['plateRun'] * FPS)) + 1
    return 0


# ------------------------------------------------------------------------------------ mezzanine
_INFO = None


def mezz_info():
    global _INFO
    if _INFO is not None:
        return _INFO
    cache = os.path.join(WORK, 'mezz_info.json')
    info = json.load(open(cache)) if os.path.exists(cache) else {}
    dirs = [P['mezz'], os.path.join(WORK, 'mezz_extra')]
    changed = False
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            m = re.match(r'^(\w+?)_([\d.]+)-([\d.]+)\.mov$', fn) or re.match(r'^(0016)_(timelapse)\.mov$', fn)
            if not m:
                continue
            path = os.path.join(d, fn)
            st = os.stat(path)
            key = fn
            if key in info and info[key]['size'] == st.st_size:
                continue
            e = subprocess.run([FF, '-hide_banner', '-i', path], capture_output=True, text=True).stderr
            if 'moov atom not found' in e or 'Invalid data' in e:
                continue
            v = re.search(r'Video: .*?, (\d+)x(\d+).*?, ([\d.]+) fps', e)
            dur = re.search(r'Duration: (\d+):(\d+):([\d.]+)', e)
            d_s = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))
            fps = float(v.group(3))
            fps = 60000 / 1001 if abs(fps - 59.94) < 0.05 else 30000 / 1001 if abs(fps - 29.97) < 0.05 else fps
            tl = m.group(2) == 'timelapse'
            info[key] = dict(path=path, src=m.group(1), t0=0.0 if tl else float(m.group(2)),
                             t1=d_s if tl else float(m.group(3)), timelapse=tl, w=int(v.group(1)), h=int(v.group(2)),
                             fps=fps, dur=d_s, audio='Audio:' in e, size=st.st_size)
            changed = True
    if changed:
        json.dump(info, open(cache, 'w'), indent=1)
    _INFO = info
    return info


def find_mezz(src, a, b, timelapse=False):
    for fn, m in mezz_info().items():
        if m['src'] != src or m['timelapse'] != timelapse:
            continue
        if timelapse or (m['t0'] - 0.035 <= a and b <= m['t0'] + m['dur'] + 0.035):
            return m
    raise SystemExit(f'no mezzanine for {src} {a:.3f}-{b:.3f}')


# ------------------------------------------------------------------------------------ source time map
def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def src_times(k, n_extra=0):
    """source time (s) and speed for every output frame of shot k (+ post-roll frames)."""
    s = SHOTS[k]; c = scfg(k)
    _, f0, f1 = FR[k]
    n = f1 - f0 + n_extra
    dur = s['dur']
    out = []
    if s['speed'] == 'keyframes':                  # timelapse: keyframe index = source second
        v = (s['out'] - s['in']) / dur              # source seconds per output second
        for j in range(n):
            u = (f0 + j) / FPS - s['t']
            out.append((s['in'] + u * v, v))
        return out
    keys = c.get('ramp')
    if not keys:
        for j in range(n):
            u = (f0 + j) / FPS - s['t']
            out.append((s['in'] + u * s['speed'], s['speed']))
        return out
    # eased ramp: keys [[u01, speed], ...] over the shot's own duration, integrated in 16 sub-steps / frame;
    # the position is anchored at the shot's first frame time (so a ramp shot still starts on `in`)
    pos = s['in'] + ((f0 / FPS) - s['t']) * keys[0][1]
    for j in range(n):
        u01 = ((f0 + j) / FPS - s['t']) / dur
        sp = fx.speed_at(min(u01, 1.0), keys)
        out.append((pos, sp))
        for q in range(16):
            uu = ((f0 + j + (q + 0.5) / 16) / FPS - s['t']) / dur
            pos += fx.speed_at(min(uu, 1.0), keys) / FPS / 16
    return out


def check_forbidden():
    bad = []
    for k, s in enumerate(SHOTS):
        if s['src'] == 'card':
            continue
        ts = src_times(k, post_frames(k))
        a, b = min(t for t, _ in ts), max(t for t, _ in ts)
        if s['speed'] == 'keyframes':
            a, b = s['in'], s['out']
        for fb in CFG['forbidden']:
            if fb['src'] == s['src'] and a < fb['b'] and b > fb['a']:
                bad.append((k, s['src'], round(a, 2), round(b, 2), fb))
    return bad


# ------------------------------------------------------------------------------------ reframe
def windows(k, n):
    """per output frame: (cx, cy, s) of the source window (1080/s x 1920/s source px)."""
    c = scfg(k)
    m = shot_mezz(k)
    sw, sh = m['w'], m['h']
    c0 = c.get('c0') or [sw / 2, sh / 2]
    c1 = c.get('c1') or c0
    s0, s1 = c.get('s0', 1.0), c.get('s1', c.get('s0', 1.0))
    _, f0, f1 = FR[k]
    L = max(1, f1 - f0 - 1)
    keys = c.get('keys')          # [[u_seconds_into_shot, cx, cy, s], ...] (eased between keys)
    out = []
    for j in range(n):
        if keys:
            u = (f0 + j) / FPS - SHOTS[k]['t']
            if u <= keys[0][0]:
                _, cx, cy, s = keys[0]
            elif u >= keys[-1][0]:
                _, cx, cy, s = keys[-1]
            else:
                for a, b in zip(keys, keys[1:]):
                    if a[0] <= u <= b[0]:
                        e = ease_io((u - a[0]) / max(1e-6, b[0] - a[0]))
                        cx, cy, s = (a[1] + (b[1] - a[1]) * e, a[2] + (b[2] - a[2]) * e, a[3] + (b[3] - a[3]) * e)
                        break
        else:
            e = ease_io(j / L) if c.get('ease', 'io') == 'io' else min(1.0, j / L)
            s = s0 + (s1 - s0) * e
            cx = c0[0] + (c1[0] - c0[0]) * e
            cy = c0[1] + (c1[1] - c0[1]) * e
        ww, hh = W / s * (sh / H), H / s * (sh / H)
        cx = min(max(cx, ww / 2), sw - ww / 2)
        cy = min(max(cy, hh / 2), sh - hh / 2)
        out.append((cx, cy, s))
    return out


def shot_mezz(k):
    s = SHOTS[k]
    if s['speed'] == 'keyframes':
        return find_mezz(s['src'], 0, 0, timelapse=True)
    ts = src_times(k, post_frames(k))
    return find_mezz(s['src'], min(t for t, _ in ts), max(t for t, _ in ts))


# ------------------------------------------------------------------------------------ grade LUT
LOOKS = CFG['looks']


class Grade(fx.NightGrade):
    """NightGrade + a shadow white-balance: the mean chroma of the shot's darkest pixels (sensor noise, sodium
    spill, a magenta night cast) is removed, fading out towards the mid-tones, before the look is applied."""
    bias = np.zeros(3, np.float32)
    thr = 0.1

    def __call__(self, img):
        l = fx.luma(img)[..., None]
        w = np.clip(1 - l / (2 * self.thr), 0, 1) ** 2
        return super().__call__(np.clip(img - self.bias * w, 0, None))


def fit_grade(k, samples):
    c = scfg(k)
    look = dict(LOOKS[c['look']])
    look.update(c.get('grade', {}))
    mid = look.pop('mid')
    g = Grade.fit(np.stack(samples), mid=mid, **{kk: v for kk, v in look.items() if kk in (
        'contrast', 'black', 'white', 'shadow_tint', 'hi_tint', 'sat', 'warm_sat')})
    # shadow cast: chroma of the darkest 25 % of the shot's pixels
    px_ = np.stack(samples)[:, ::6, ::6].reshape(-1, 3).astype(np.float32) / 255
    lum = fx.luma(px_)
    q = np.percentile(lum, 25)
    dark = px_[lum <= q]
    g.thr = float(max(q, 0.02))
    g.bias = (dark.mean(0) - fx.luma(dark).mean()).astype(np.float32) * float(c.get('shadowWB', 0.9))
    # the showcase clamps gamma to 0.8-1.5; the vlog's darkest rooms need more lift
    sub = np.stack(samples)[:, ::8, ::8].astype(np.float32) / 255
    l = fx.luma(sub).ravel()
    med = np.clip((np.median(l) - g.lo) / max(g.hi - g.lo, 1e-3), 0.02, 0.98)
    g.gamma = float(min(max(math.log(mid) / math.log(med), look.get('gmin', 0.55)), 1.6))
    if 'expo' in c:
        g.hi = g.hi / (2 ** c['expo'])
    return g


def write_cube(g, path, n=33):
    v = np.linspace(0, 1, n, dtype=np.float32)
    b, gg, r = np.meshgrid(v, v, v, indexing='ij')           # r fastest in the file
    rgb = np.stack([r, gg, b], -1).reshape(-1, 1, 3)
    out = np.clip(g(rgb), 0, 1).reshape(-1, 3)
    with open(path, 'w') as f:
        f.write(f'TITLE "rally-v2"\nLUT_3D_SIZE {n}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        f.write('\n'.join(f'{a:.6f} {bb:.6f} {cc:.6f}' for a, bb, cc in out))
        f.write('\n')


# ------------------------------------------------------------------------------------ decode
class Reader:
    """Sequential RGB frames of a mezzanine from source frame index j0 (crop applied, optional LUT)."""

    def __init__(self, m, j0, count, crop, lut=None, rot=0):
        x, y, w, h = crop
        # part1: `rot` (config shots.N.rot, degrees clockwise) turns a camera that was mounted on its side / upside down
        # upright before the crop (square open-gate sources, so the frame size does not change)
        vf = {90: ['transpose=clock'], -90: ['transpose=cclock'], 270: ['transpose=cclock'], 180: ['hflip,vflip']}.get(rot, [])
        vf += [f'crop={w}:{h}:{x}:{y}', 'scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=bicubic', 'format=rgb48le']
        if lut:
            vf.append(f"lut3d=file='{lut}':interp=tetrahedral")
        vf.append('format=rgb24')
        ss = max(0.0, (j0 - 0.5) / m['fps'])
        self.w, self.h = w, h
        self.p = subprocess.Popen([FF, '-v', 'error', '-ss', f'{ss:.6f}', '-i', m['path'], '-map', '0:v:0', '-frames:v', str(count),
                                   '-vf', ','.join(vf), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=w * h * 3 * 4)
        self.j = j0
        self.buf = {}

    def get(self, j):
        """frame j (source index); frames are read forward and kept only while needed."""
        while self.j <= j:
            b = self.p.stdout.read(self.w * self.h * 3)
            if len(b) < self.w * self.h * 3:
                # past the end of the file: hold the last frame (flagged in the log)
                last = self.buf[max(self.buf)] if self.buf else None
                if last is None:
                    raise SystemExit('decode failed')
                self.buf[self.j] = last
                self.short = True
            else:
                self.buf[self.j] = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3)
            self.j += 1
        for q in [q for q in self.buf if q < j - 8]:
            del self.buf[q]
        return self.buf[j]

    def close(self):
        self.p.stdout.close(); self.p.kill(); self.p.wait()


def reframe(img, crop, win):
    """source crop image -> 1080x1920 output for window (cx, cy, s) given in full-source px."""
    cx, cy, s = win
    x0, y0 = crop[0], crop[1]
    a = 1.0 / s
    c = cx - x0 - (W / 2) * a
    f = cy - y0 - (H / 2) * a
    if abs(s - 1) < 1e-6 and abs(c - round(c)) < 1e-6 and abs(f - round(f)) < 1e-6:
        c, f = int(round(c)), int(round(f))
        return np.ascontiguousarray(img[f:f + H, c:c + W])
    im = Image.fromarray(img)
    return np.asarray(im.transform((W, H), Image.AFFINE, (a, 0, c, 0, a, f), resample=Image.BICUBIC))


def plan_shot(k):
    s = SHOTS[k]
    m = shot_mezz(k)
    n = FR[k][2] - FR[k][1] + post_frames(k)
    ts = src_times(k, post_frames(k))
    wins = windows(k, n)
    # union crop (even-aligned), in source px
    xs0 = min(cx - W / s_ / 2 * (m['h'] / H) for cx, cy, s_ in wins)
    xs1 = max(cx + W / s_ / 2 * (m['h'] / H) for cx, cy, s_ in wins)
    ys0 = min(cy - H / s_ / 2 * (m['h'] / H) for cx, cy, s_ in wins)
    ys1 = max(cy + H / s_ / 2 * (m['h'] / H) for cx, cy, s_ in wins)
    x0 = max(0, int(math.floor(xs0)) - 4) // 2 * 2
    y0 = max(0, int(math.floor(ys0)) - 4) // 2 * 2
    x1 = min(m['w'], int(math.ceil(xs1)) + 4)
    y1 = min(m['h'], int(math.ceil(ys1)) + 4)
    crop = (x0, y0, (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2)
    fps_s = m['fps']
    # source frame index + number of frames to average, per output frame
    picks = []
    for (t, sp) in ts:
        if m['timelapse']:
            jf = t                                     # keyframe index = source second
            adv = sp / FPS
            navg = max(1, int(round(adv * CFG['timelapseShutter'])))
        else:
            jf = (t - m['t0']) * fps_s
            adv = abs(sp) * fps_s / FPS
            navg = max(1, int(round(adv * 0.5))) if adv > 2.6 else 1
        picks.append((jf, navg))
    return dict(m=m, n=n, ts=ts, wins=wins, crop=crop, picks=picks)


def sample_frames(k, pl, count=5):
    m = pl['m']
    idx = [pl['picks'][int(round(q * (FR[k][2] - FR[k][1] - 1)))][0] for q in np.linspace(0, 1, count)]
    out = []
    for jf in idx:
        j = int(round(jf))
        r = Reader(m, j, 1, pl['crop'], rot=scfg(k).get('rot', 0))
        out.append(r.get(j).copy()); r.close()
    return out


def shot_sig(k):
    s = SHOTS[k]
    # RENDER_VERSION is bumped by hand when the shot renderer itself changes (so unrelated edits to this file
    # do not re-render 52 shots)
    blob = json.dumps([s, scfg(k), post_frames(k), CFG['looks'], CFG['timelapseShutter'], shot_mezz(k)['size'], RENDER_VERSION], sort_keys=True)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def render_shot(k, force=False):
    s = SHOTS[k]
    d = os.path.join(WORK, 'shots'); os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f'{k:02d}.mov')
    sigp = out + '.sig'
    if s['src'] == 'card':
        return None
    sig = shot_sig(k)
    if not force and os.path.exists(out) and os.path.exists(sigp) and open(sigp).read() == sig:
        return out
    t_0 = time.time()
    pl = plan_shot(k)
    m = pl['m']
    lut = os.path.join(d, f'{k:02d}.cube')
    g = fit_grade(k, sample_frames(k, pl))
    write_cube(g, lut)
    j_first = int(math.floor(min(jf - (na - 1) / 2 for jf, na in pl['picks'])))
    j_last = int(math.ceil(max(jf + (na - 1) / 2 for jf, na in pl['picks']))) + 1
    j_first = max(0, j_first)
    r = Reader(m, j_first, j_last - j_first + 1, pl['crop'], lut, rot=scfg(k).get('rot', 0))
    enc = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30000/1001', '-i', '-',
                            '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv444p', '-c:v', 'libx264', '-preset', 'veryfast',
                            '-crf', '10', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out],
                           stdin=subprocess.PIPE)
    r.short = False
    for i in range(pl['n']):
        jf, na = pl['picks'][i]
        if na == 1:
            j = int(round(jf))
            j = max(j, j_first)
            img = r.get(j)
            if not m['timelapse'] and abs(jf - round(jf)) > 0.25 and abs(pl['ts'][i][1]) < 0.9:
                # slow motion between two source frames: blend (no stutter)
                a = int(math.floor(jf)); fr_ = jf - a
                img = (r.get(max(a, j_first)).astype(np.float32) * (1 - fr_) + r.get(a + 1).astype(np.float32) * fr_ + 0.5).astype(np.uint8)
        else:
            js = [int(round(jf - (na - 1) / 2 + q)) for q in range(na)]
            acc = np.zeros((pl['crop'][3], pl['crop'][2], 3), np.float32)
            for j in js:
                acc += r.get(max(j, j_first))
            img = (acc / na + 0.5).astype(np.uint8)
        o = reframe(img, pl['crop'], pl['wins'][i])
        enc.stdin.write(o.tobytes())
    enc.stdin.close(); enc.wait(); r.close()
    if r.short:
        log(f'  shot {k}: WARNING ran past the end of {os.path.basename(m["path"])} (last frame held)')
    open(sigp, 'w').write(sig)
    json.dump(dict(k=k, src=s['src'], mezz=os.path.basename(m['path']), crop=pl['crop'], n=pl['n'], post=post_frames(k),
                   src_range=[round(pl['ts'][0][0], 3), round(pl['ts'][-1][0], 3)], lut=dict(lo=float(g.lo), hi=float(g.hi), gamma=g.gamma),
                   look=scfg(k)['look']), open(out + '.json', 'w'))
    log(f'  shot {k:02d} {s["src"]} {pl["n"]} fr ({post_frames(k)} post) in {time.time() - t_0:.0f}s gamma {g.gamma:.2f}')
    return out


# ------------------------------------------------------------------------------------ join
def read_all(path, n):
    p = subprocess.Popen([FF, '-v', 'error', '-i', path, '-vf', 'scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb24',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    for _ in range(n):
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            raise SystemExit(f'{path}: short read')
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.stdout.close(); p.wait()


def punch_at(t):
    """SEK.chapterSlam plate punch (impact th = t0 + 0.16): zoom 1 + 0.045 e^(-9 dt) and a decaying shake."""
    best = None
    for c in CFG['slams']:
        th = c['t'] + 0.16
        if th - 1e-6 <= t < th + 0.7:
            k = (t - th) * FPS
            amp = math.exp(-k / 2.2)
            best = (1 + 0.045 * math.exp(-(t - th) * 9), 9 * amp * math.sin(k * 2.1), 7 * amp * math.cos(k * 2.7))
    return best


def sweep_mask(t, tr):
    """1 where the NEW shot shows (left of the band's centre line), with a soft edge (SEK.sweep geometry)."""
    q = fx.smootherstep(0) if False else None
    u = min(max((t - tr['t0']) / tr['dur'], 0.0), 1.0)
    e = 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2      # KT.ease.inOutCubic
    xc = -420 + (1080 + 840) * e
    kk = math.tan(tr.get('angle', 16) * math.pi / 180)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    line = xc + kk * (yy - 960)
    return np.clip((line - xx) / 26 + 0.5, 0, 1)[..., None]


def join():
    out = os.path.join(WORK, 'plate.mov')
    enc = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30000/1001', '-i', '-',
                            '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'fast',
                            '-crf', '12', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out],
                           stdin=subprocess.PIPE)
    trans = {tr['into']: tr for tr in CFG['transitions']}
    written = 0
    pending = []                  # frames of the previous shot not yet written (kept for a whip)
    post_prev = []                # post-roll frames of the previous shot (for a sweep)
    t_start = time.time()

    # licence-plate blurs (config `blurs`): tracked boxes in output px (lib/data/tracks.json), blurred with a
    # feathered edge before anything else touches the frame
    tp = os.path.join(HERE, 'data', 'tracks.json')
    TRK = json.load(open(tp)) if os.path.exists(tp) else {}
    BL = {}
    for b in CFG.get('blurs', []):
        tr = TRK.get(b['track'])
        if not tr:
            log(f'  join: WARNING no track {b["track"]} for a plate blur'); continue
        for fr in tr['frames']:
            if b.get('f0', -1) <= fr['f'] <= b.get('f1', 10 ** 9):
                BL.setdefault(fr['f'], []).append((fr, b.get('pad', 10), b.get('radius', 14)))

    # part1: static boxes (config `speedo`: `box` [x,y,w,h] and a `shot`, or output frames f0-f1): the car's own
    # speedometer on the cabin-cam shots (no speed on screen). Licence plates are NOT blurred in this vlog (Omarie,
    # 6 Oct: "we dont need plate blur"), so config `blurs` stays empty.
    for b in CFG.get('blurs', []) + CFG.get('speedo', []):
        if 'box' not in b:
            continue
        if 'shot' in b:
            _, a_, b_ = FR[b['shot']]
            f0_, f1_ = a_, b_ - 1
        else:
            f0_, f1_ = b['f0'], b['f1']
        x_, y_, w_, h_ = b['box']
        for f in range(f0_, f1_ + 1):
            BL.setdefault(f, []).append((dict(x=x_, y=y_, w=w_, h=h_), b.get('pad', 10), b.get('radius', 14)))
    GL = glass_rects()

    def glass(img, i):
        """part1: the HUD strip's frosted glass (themes/glass-orange.json: backdrop-filter blur(22px) saturate(1.3)):
        the plate inside the strip panel's visible rect is blurred and saturated here; the layer draws the tint on top."""
        from PIL import ImageFilter
        if i not in GL:
            return img
        img = img.copy()
        for (x, y, w, h) in GL[i]:
            x0, y0, x1, y1 = int(round(x)), int(round(y)), int(round(x + w)), int(round(y + h))
            if x1 - x0 < 2 or y1 - y0 < 1:
                continue
            m = 66
            X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
            reg = Image.fromarray(img[Y0:Y1, X0:X1]).filter(ImageFilter.GaussianBlur(22))
            f = np.asarray(reg, np.float32)[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] / 255
            sat = 1.3                                   # CSS saturate() matrix
            M = np.array([[0.213 + 0.787 * sat, 0.715 - 0.715 * sat, 0.072 - 0.072 * sat],
                          [0.213 - 0.213 * sat, 0.715 + 0.285 * sat, 0.072 - 0.072 * sat],
                          [0.213 - 0.213 * sat, 0.715 - 0.715 * sat, 0.072 + 0.928 * sat]], np.float32)
            f = np.clip(f @ M.T, 0, 1)
            img[y0:y1, x0:x1] = (f * 255 + 0.5).astype(np.uint8)
        return img

    def blur_plates(img, i):
        from PIL import ImageFilter
        if i not in BL:
            return img
        img = img.copy()
        for fr, pad, rad in BL[i]:
            x0, y0 = int(max(0, fr['x'] - pad)), int(max(0, fr['y'] - pad))
            x1, y1 = int(min(W, fr['x'] + fr['w'] + pad)), int(min(H, fr['y'] + fr['h'] + pad))
            if x1 - x0 < 4 or y1 - y0 < 4:
                continue
            m = 2 * rad
            X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
            reg = Image.fromarray(img[Y0:Y1, X0:X1])
            bl = np.asarray(reg.filter(ImageFilter.GaussianBlur(rad)).filter(ImageFilter.BoxBlur(rad // 2)), np.float32)
            yy, xx = np.mgrid[Y0:Y1, X0:X1]
            dx = np.maximum(np.maximum(x0 - xx, xx - x1), 0); dy = np.maximum(np.maximum(y0 - yy, yy - y1), 0)
            a = np.clip(1 - np.hypot(dx, dy) / max(1, pad), 0, 1)[..., None]
            img[Y0:Y1, X0:X1] = (bl * a + img[Y0:Y1, X0:X1].astype(np.float32) * (1 - a) + 0.5).astype(np.uint8)
        return img

    def emit(img, i):
        nonlocal written
        assert i == written, (i, written)
        img = blur_plates(img, i)
        img = glass(img, i)
        t = i / FPS
        pk = punch_at(t)
        if pk:
            f = fx.to_f(img)
            f = fx.transform(f, pk[1], pk[2], pk[0])
            img = fx.to_u8(f)
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
        written += 1

    KW = 3                         # frames kept back at the end of every shot (a whip into the next one replaces them)
    for k, f0, f1 in FR:
        s = SHOTS[k]
        n_main = f1 - f0
        if s['src'] == 'card':
            # the previous shot runs on under the card's wipe (its post-roll), then black
            for i, img in pending:
                emit(img, i)
            pending = []
            run = post_prev[:n_main]
            for q, img in enumerate(run):
                emit(img, f0 + q)
            blank = np.zeros((H, W, 3), np.uint8)
            for i in range(f0 + len(run), f1):
                emit(blank, i)
            continue
        path = render_shot(k)
        n_post = post_frames(k)
        it = read_all(path, n_main + n_post)
        tr = trans.get(k)

        def treat(img, j):
            i = f0 + j
            if tr and tr['type'] == 'sweep':
                t = i / FPS
                if tr['t0'] <= t < tr['t0'] + tr['dur'] and j < len(post_prev):
                    m = sweep_mask(t, tr)
                    img = (img.astype(np.float32) * m + post_prev[j].astype(np.float32) * (1 - m) + 0.5).astype(np.uint8)
            if tr and tr['type'] == 'impact' and j < 14:
                img = fx.to_u8(fx.impact(fx.to_f(img), j, strength=tr.get('strength', 0.5), seed=k))
            return img
        head = [(f0 + j, treat(next(it), j)) for j in range(min(KW, n_main))]
        # whip into this shot: replace the last KW frames of the previous shot and the first KW of this one
        if tr and tr['type'] == 'whip':
            a_tail = [fx.to_f(img) for _, img in pending[-KW:]]
            b_head = [fx.to_f(img) for _, img in head[:KW]]
            wf = fx.whip(a_tail, b_head, direction=tr['dir'], dist=tr.get('dist', 0.9), blur=1.0, bright=0.12)
            for q in range(KW):
                pending[-KW + q] = (pending[-KW + q][0], fx.to_u8(wf[q]))
                head[q] = (head[q][0], fx.to_u8(wf[KW + q]))
        for i, img in pending:
            emit(img, i)
        buf = list(head)
        for j in range(len(head), n_main):
            buf.append((f0 + j, treat(next(it), j)))
            if len(buf) > KW:
                i, img = buf.pop(0)
                emit(img, i)
        pending = buf
        post_prev = [next(it) for _ in range(n_post)]
        if k % 6 == 0:
            log(f'  join: shot {k} at frame {written} ({time.time() - t_start:.0f}s)')
    for i, img in pending:
        emit(img, i)
    enc.stdin.close(); enc.wait()
    assert written == NF, (written, NF)
    log(f'join: {written} frames -> {out} in {time.time() - t_start:.0f}s')
    return out


def glass_rects():
    """{output frame: [(x, y, w, visible h)]} for every STRIP (driveStrip) in config layer.comps: the panel's clip-path
    as lib/sekit.js panelAt draws it (unroll: outExpo over ts+0.02..ts+0.34; retract: inOutCubic over tx..tx+0.245)."""
    def P(t, a, b):
        return min(max((t - a) / (b - a), 0.0), 1.0)
    def out_expo(x):
        return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
    def in_out_cubic(x):
        return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    out = {}
    for c in CFG['layer']['comps']:
        if c['type'] == 'seStrip':                    # part1 v2: the episode-long strip (lib/drive_strip.js seStrip)
            p = dict(x=54, y=292, w=853, hc=84, hx=140, exit=None, expand=[]); p.update(c['p'])
            ts, tx = c['t0'], p.get('exit')
            for f in range(int(math.floor(c['t0'] * FPS)), int(math.ceil(c['t1'] * FPS)) + 1):
                t = f / FPS
                if not (c['t0'] <= t < c['t1']):
                    continue
                ex = 0.0
                for w in p['expand']:
                    ex = max(ex, in_out_cubic(P(t, w['a'], w['a'] + 0.4)) * (1 - in_out_cubic(P(t, w['b'] - 0.4, w['b']))))
                h = p['hc'] + (p['hx'] - p['hc']) * ex
                qr = out_expo(P(t, ts + 0.02, ts + 0.26 + 0.08))
                qc = in_out_cubic(P(t, tx, tx + 0.34 * 0.72)) if tx is not None else 0.0
                bottom = qc if qc > 0 else 1 - qr
                vh = h * (1 - bottom)
                if vh > 0.5:
                    out.setdefault(f, []).append((p['x'], p['y'], p['w'], vh))
            continue
        if c['type'] != 'driveStrip':
            continue
        p = dict(x=54, y=292, w=853, h=140, exit=None); p.update(c['p'])
        ts, tx = c['t0'], p.get('exit')
        for f in range(int(math.floor(c['t0'] * FPS)), int(math.ceil(c['t1'] * FPS)) + 1):
            t = f / FPS
            if not (c['t0'] <= t < c['t1']):
                continue
            qr = out_expo(P(t, ts + 0.02, ts + 0.26 + 0.08))
            qc = in_out_cubic(P(t, tx, tx + 0.34 * 0.72)) if tx is not None else 0.0
            bottom = qc if qc > 0 else 1 - qr
            vh = p['h'] * (1 - bottom)
            if vh > 0.5:
                out.setdefault(f, []).append((p['x'], p['y'], p['w'], vh))
    return out


# ------------------------------------------------------------------------------------ QA sheet
def grab(video, idx):
    idx = sorted(set(idx))
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    raw = subprocess.run([FF, '-v', 'error', '-i', video, '-vf', f"select='{sel}',scale=in_color_matrix=bt709:in_range=tv:out_range=pc",
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    return dict(zip(idx, arr))


def sheet(video, out, cols=9, tw=200, only=None):
    idx, labels = [], []
    for k, f0, f1 in FR:
        if only is not None and k not in only:
            continue
        for q, nm in ((f0, 'in'), ((f0 + f1 - 1) // 2, 'mid'), (f1 - 1, 'out')):
            idx.append(q); labels.append((q, f'{k:02d} {SHOTS[k]["src"]} {nm}'))
    fr = grab(video, idx)
    th = int(tw * 16 / 9)
    rows = math.ceil(len(labels) / cols)
    sh = Image.new('RGB', (cols * tw, rows * (th + 14)), (20, 20, 20))
    d = ImageDraw.Draw(sh)
    for n, (q, lb) in enumerate(labels):
        x, y = (n % cols) * tw, (n // cols) * (th + 14)
        sh.paste(Image.fromarray(fr[q]).resize((tw, th), Image.BILINEAR), (x, y + 14))
        d.text((x + 2, y + 1), f'{lb} f{q}', fill=(255, 79, 22))
    sh.save(out, quality=85)
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['check', 'shots', 'join', 'sheet', 'plan'])
    ap.add_argument('--only', default=None)
    ap.add_argument('--force', action='store_true')
    A = ap.parse_args()
    only = [int(x) for x in A.only.split(',')] if A.only else None
    if A.cmd == 'check':
        bad = check_forbidden()
        print('forbidden overlaps:', bad or 'none')
        for k, f0, f1 in FR:
            print(k, SHOTS[k]['src'], f0, f1, f1 - f0, 'post', post_frames(k))
    elif A.cmd == 'plan':
        for k in (only or range(len(SHOTS))):
            if SHOTS[k]['src'] == 'card':
                continue
            pl = plan_shot(k)
            print(k, SHOTS[k]['src'], os.path.basename(pl['m']['path']), 'crop', pl['crop'], 'src', round(pl['ts'][0][0], 3), '->', round(pl['ts'][-1][0], 3))
    elif A.cmd == 'shots':
        bad = check_forbidden()
        assert not bad, bad
        for k in (only or range(len(SHOTS))):
            render_shot(k, force=A.force)
    elif A.cmd == 'join':
        join()
    elif A.cmd == 'sheet':
        print(sheet(os.path.join(WORK, 'plate.mov'), os.path.join(WORK, 'look', 'plate_sheet.jpg'), only=only))
