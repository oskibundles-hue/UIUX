#!/usr/bin/env python3
"""gate_sheets.py -- the pre-render frame gate (v2, 7 Oct): composited stills (plate + layer, exactly as the render
composes them: build.py --stills) of every driving / replacement / cabin shot, the food-break and talk-to-camera shots,
and the end card + HUD strip, as a few large labelled contact sheets in exports/qa/gate/ for nq-check.

    python3 tools/gate_sheets.py frames      # the output frame list (comma separated) for build.py --stills
    python3 build.py --stills $(python3 tools/gate_sheets.py frames)
    python3 tools/gate_sheets.py sheets      # .work/stills/cNNNNN.jpg -> exports/qa/gate/*.jpg

Each tile: programme time, output frame, shot, source clip and source time; config `speedo` boxes (box + pad, the
blurred area) outlined in orange on groups A and B."""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
os.chdir(ROOT)
from cfg import load_config  # noqa: E402
C = load_config()
E = json.load(open(C['paths']['edl']))
S = E['shots']
FPS = 30000 / 1001
NF = int(round(E['duration'] * FPS))
OUT = os.path.join(ROOT, 'exports', 'qa', 'gate')
STILLS = os.path.join(ROOT, '.work', 'stills')

# groups (shot indices into data/edl.json)
DRIVE = [0, 1, 2, 13, 14, 15, 16, 22, 23, 24, 25, 28, 29, 30, 36, 37, 38, 39, 40, 41, 42, 43]   # driving + replacement (cutaway) shots
CABIN = [11, 12, 17, 18, 19, 20, 31, 45]                       # other cabin-cam shots (speedo boxes or none needed: parked, cluster dark)
A = sorted(DRIVE + CABIN)
B = [5, 7, 26, 27, 35]                                       # food break, talk to camera, deck cam


def fr0(k):
    return int(round(S[k]['t'] * FPS))


def fr1(k):
    return int(round(S[k + 1]['t'] * FPS)) if k + 1 < len(S) else NF


def spread(k, n):
    a, b = fr0(k) + 3, fr1(k) - 4                            # off the cut frames
    return [int(round(a + (b - a) * i / (n - 1))) for i in range(n)]


def strip():
    return [c for c in C['layer']['comps'] if c['type'] == 'seStrip'][0]


def plan():
    """[(sheet name, title, cols, tile width, [(frame, shot or None, note)])]"""
    out = []
    ta = []
    for k in A:
        n = 4 if k == 31 else 3                              # 31: the one shot with speed digits under its box
        ta += [(f, k, '') for f in spread(k, n)]
    per = math.ceil(len(ta) / 3)                             # three A sheets
    for j in range(0, len(ta), per):
        out.append((f'gate_A{j // per + 1}_driving_cabin', 'A: driving, replacement and cabin shots (speedo blur = orange outline)', 6, 360, ta[j:j + per]))
    tb = []
    for k in B:
        n = 8 if S[k]['dur'] >= 8 and S[k]['src'] == '0116' else (4 if S[k]['src'] == '0121' else 6)
        tb += [(f, k, '') for f in spread(k, n)]
    out.append(('gate_B_food_talk', 'B: food break (0105 cut-in, 0107 eating), talk to camera (0116 x2), deck cam (0121)', 6, 360, tb))
    st = strip()
    end = [c for c in C['layer']['comps'] if c['type'] == 'v2end'][0]
    tc = []
    for t, note in ((5.0, 'HUD strip + scrubber'), (80.0, 'HUD strip + scrubber'), (115.0, 'HUD strip + scrubber')):
        tc.append((int(round(t * FPS)), None, note))
    for e in st['p']['expand']:
        tc.append((int(round((e['a'] + e['b']) / 2 * FPS)), None, 'strip expanded: ' + e['places'][0][1]))
    for t in (end['t0'] + 0.6, (end['t0'] + end['t1']) / 2, end['t1'] - 0.15):
        tc.append((min(NF - 1, int(round(t * FPS))), None, 'end card'))
    out.append(('gate_C_strip_endcard', 'C: HUD strip with its scrubber (3), each strip expand window (2), end card (3)', 4, 540, tc))
    return out


def shot_at(f):
    for k in range(len(S)):
        if fr0(k) <= f < fr1(k):
            return k


def font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def sheets():
    os.makedirs(OUT, exist_ok=True)
    SP = {}
    for b in C.get('speedo', []):
        SP.setdefault(b['shot'], []).append((b['box'], b.get('pad', 10)))
    written = []
    for name, title, cols, tw, tiles in plan():
        th = tw * 16 // 9
        sc = tw / 1080
        fl, ft = font(max(14, tw // 22)), font(30)
        rows = math.ceil(len(tiles) / cols)
        sh = Image.new('RGB', (cols * tw, 44 + rows * th), (24, 24, 24))
        ImageDraw.Draw(sh).text((10, 6), f'{title}  |  {len(tiles)} frames', fill=(255, 255, 255), font=ft)
        for i, (f, k, note) in enumerate(tiles):
            p = os.path.join(STILLS, f'c{f:05d}.jpg')
            im = Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS)
            d = ImageDraw.Draw(im)
            k = shot_at(f) if k is None else k
            s = S[k]
            if s['src'] != 'card' and name.startswith(('gate_A', 'gate_B')):
                for (x, y, w, h), pad in SP.get(k, []):
                    d.rectangle([(x - pad) * sc, (y - pad) * sc, (x + w + pad) * sc, (y + h + pad) * sc], outline=(255, 79, 22), width=2)
            t = f / FPS
            src = '' if s['src'] == 'card' else f"  {s['src']} @{s['in'] + (t - s['t']) * s['speed']:.2f}"
            lab = f"{int(t // 60)}:{t % 60:05.2f}  f{f}  #{k}{src}"
            d.rectangle([0, 0, tw, fl.size + 8], fill=(0, 0, 0))
            d.text((4, 3), lab, fill=(255, 200, 0), font=fl)
            if note:
                d.rectangle([0, th - fl.size - 8, tw, th], fill=(0, 0, 0))
                d.text((4, th - fl.size - 5), note, fill=(255, 255, 255), font=fl)
            sh.paste(im, ((i % cols) * tw, 44 + (i // cols) * th))
        q = os.path.join(OUT, name + '.jpg')
        sh.save(q, quality=88)
        written.append((q, len(tiles), sh.size))
    for q, n, sz in written:
        print(q, n, 'tiles', sz)


def render_sheet(mp4):
    """v2 gate round (7 Oct): gate_D_render_fixes.jpg from the FINAL mp4 (decoded frames, not stills): 1:38-1:52 (shots
    32-34, the MCLAREN 600LT lock) and shot 12's replacement every 10 frames (about 0.33 s), 1:02.8-1:03.6 every 2nd frame
    (the sweep into shot 23: clock and speedo blur held until it ends)."""
    import subprocess
    k12 = 12
    fs = [(f, 'shot 12 replacement (no phone)') for f in range(fr0(k12) + 2, fr1(k12), 10)]
    fs += [(f, 'sweep into 23: clock / speedo held') for f in range(int(62.8 * FPS), int(63.6 * FPS) + 1, 2)]
    fs += [(f, '') for f in range(int(98.0 * FPS), int(112.0 * FPS) + 1, 10)]
    idx = sorted({f for f, _ in fs})
    sel = '+'.join(f'eq(n\\,{i})' for i in idx)
    tw, cols = 360, 8
    th = tw * 16 // 9
    raw = subprocess.run([C['paths']['ffmpeg'], '-v', 'error', '-i', mp4, '-vf', f"select='{sel}',scale={tw}:{th}:flags=lanczos",
                          '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    n = len(raw) // (tw * th * 3)
    assert n == len(idx), (n, len(idx))
    ims = {f: Image.frombytes('RGB', (tw, th), raw[i * tw * th * 3:(i + 1) * tw * th * 3]) for i, f in enumerate(idx)}
    fl, ft = font(16), font(30)
    rows = math.ceil(len(fs) / cols)
    sh = Image.new('RGB', (cols * tw, 44 + rows * th), (24, 24, 24))
    ImageDraw.Draw(sh).text((10, 6), f'D: final render ({os.path.basename(mp4)})  |  {len(fs)} frames', fill=(255, 255, 255), font=ft)
    for i, (f, note) in enumerate(fs):
        im = ims[f].copy()
        d = ImageDraw.Draw(im)
        k = shot_at(f); s = S[k]; t = f / FPS
        src = '' if s['src'] == 'card' else f"  {s['src']} @{s['in'] + (t - s['t']) * s['speed']:.2f}"
        d.rectangle([0, 0, tw, fl.size + 8], fill=(0, 0, 0))
        d.text((4, 3), f"{int(t // 60)}:{t % 60:05.2f}  f{f}  #{k}{src}", fill=(255, 200, 0), font=fl)
        if note:
            d.rectangle([0, th - fl.size - 8, tw, th], fill=(0, 0, 0))
            d.text((4, th - fl.size - 5), note, fill=(255, 255, 255), font=fl)
        sh.paste(im, ((i % cols) * tw, 44 + (i // cols) * th))
    os.makedirs(OUT, exist_ok=True)
    q = os.path.join(OUT, 'gate_D_render_fixes.jpg')
    sh.save(q, quality=88)
    print(q, len(fs), 'tiles', sh.size)


if __name__ == '__main__':
    if sys.argv[1] == 'render':
        render_sheet(sys.argv[2])
    elif sys.argv[1] == 'frames':
        print(','.join(str(f) for f in sorted({f for _, _, _, _, t in plan() for f, _, _ in t})))
    else:
        sheets()
