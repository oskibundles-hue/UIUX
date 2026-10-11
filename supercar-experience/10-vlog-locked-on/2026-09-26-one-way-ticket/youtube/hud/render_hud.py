#!/usr/bin/env python3
"""Draw the personal driving HUD from hud.json at any frame height.

    python3 render_hud.py OUTDIR [HEIGHT=720] [--stills]

Writes one qtrle RGBA clip per run (OUTDIR/run_NN.mov, only the panel's box, not the full frame) and OUTDIR/runs.json
with each clip's global start frame and x, y placement for assemble.py. Everything is sized from H (W = 16/9 H), drawn
at SS x and downsampled, so the same code makes the 720p rough-cut HUD and the 4K one.

Look (personal brand, @nq.young): lower-left at the chapter titles' x (5.5 % in), above the bottom safe area; a soft
dark backing; the place in Anton (white), the camera-clock time in Archivo 600 (white); a schematic route line
Seattle -> Oregon -> Idaho -> Nevada -> Las Vegas (white 40 % ahead, #DE1A22 travelled, a #FBD101 dot with a slow pulse
ring), and a thin progress bar under it (#DE1A22 fill, #FBD101 cap). No numbers but the clock.
"""
import glob, json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30000 / 1001
RED, YEL, WHT = (0xDE, 0x1A, 0x22), (0xFB, 0xD1, 0x01), (255, 255, 255)
FONTS = '/home/user/day-owt/fonts'
F_PLACE = glob.glob(f'{FONTS}/fontsource-anton-*/files/anton-latin-400-normal.woff')[0]
F_CLOCK = glob.glob(f'{FONTS}/fontsource-archivo-*/files/archivo-latin-600-normal.woff')[0]
SS = 3          # supersampling
SCALE = 0.85    # overall size; 1.0 = a 30 px place name at 720p
# schematic node shape (x, y in 0..1 of the route box): NW to SE, a stylised zig-zag, not a map
SHAPE = [(0.0, 0.0), (0.27, 0.62), (0.52, 0.28), (0.76, 0.82), (1.0, 1.0)]


def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def point_at(p):
    n = len(SHAPE) - 1
    q = max(0.0, min(1.0, p)) * n
    i = min(int(q), n - 1); f = q - i
    (x0, y0), (x1, y1) = SHAPE[i], SHAPE[i + 1]
    return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f


def clock_str(sec):
    sec = int(sec) % 86400
    h, m = sec // 3600, (sec % 3600) // 60
    return f'{(h % 12) or 12}:{m:02d} {"AM" if h < 12 else "PM"}'


class Hud:
    def __init__(self, H):
        self.H = H; self.W = round(H * 16 / 9)
        u = H / 720.0 * SCALE
        self.u = u
        self.fp = ImageFont.truetype(F_PLACE, round(30 * u * SS))
        self.fc = ImageFont.truetype(F_CLOCK, round(17 * u * SS))
        self.pad = 12 * u
        self.route_w, self.route_h = 196 * u, 24 * u
        self.bar_h = 3.5 * u
        self.slide = 0.018 * self.W
        # panel box (in frame px): x0 = title x (5.5 %), bottom at 92 % of H
        self.box_w = round(self.route_w + 2 * self.pad + 70 * u)   # room for the widest place + clock
        self.box_h = round(self.pad * 2 + 34 * u + 10 * u + self.route_h + 10 * u + self.bar_h)
        self.x = round(0.055 * self.W - self.pad)
        self.y = round(0.92 * H - self.box_h)
        self.cw = self.box_w + round(self.slide) + 4     # clip canvas: room for the slide
        self.cx = self.x - round(self.slide) - 4

    def frame(self, place, place_prev, xfade, clock, p_disp, a, slide_k, pulse):
        S = SS; u = self.u * S
        im = Image.new('RGBA', (self.cw * S, self.box_h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ox = (round(self.slide) + 4 - self.slide * (1 - slide_k)) * S
        # backing: the place line sets the width
        tw = d.textlength(place, font=self.fp)
        assert tw + 12 * u + d.textlength(clock, font=self.fc) + 2 * self.pad * S <= self.box_w * S, place
        cw = d.textlength(clock, font=self.fc)
        top_w = tw + 12 * u + cw
        bw = max(top_w, self.route_w * S) + 2 * self.pad * S
        d.rounded_rectangle([ox, 0, ox + bw, self.box_h * S - 1], radius=8 * u, fill=(0, 0, 0, round(0.42 * 255 * a)))
        # place (Anton) with a quick crossfade at a change
        px, py = ox + self.pad * S, self.pad * S - 6 * u
        if place_prev and xfade < 1:
            d.text((px, py), place_prev, font=self.fp, fill=WHT + (round(255 * a * (1 - xfade)),))
        d.text((px, py), place, font=self.fp, fill=WHT + (round(255 * a * (xfade if place_prev else 1)),))
        # small yellow divider, then the clock (Archivo 600), bottoms aligned with Anton's cap line
        tx = px + tw + 6 * u
        asc_p = self.fp.getbbox('H')[3]; asc_c = self.fc.getbbox('H')[3]
        d.rectangle([tx - 1 * u, py + asc_p - asc_c + 2 * u, tx + 1 * u, py + asc_p], fill=YEL + (round(255 * a),))
        d.text((tx + 6 * u, py + asc_p - asc_c), clock, font=self.fc, fill=WHT + (round(240 * a),))
        # route line
        rx, ry = ox + self.pad * S + 4 * u, self.pad * S + 44 * u
        rw, rh = self.route_w * S - 8 * u, self.route_h * S
        pts = [(rx + x * rw, ry + y * rh) for x, y in SHAPE]
        d.line(pts, fill=WHT + (round(105 * a),), width=max(1, round(1.6 * u)), joint='curve')
        n = len(SHAPE) - 1
        trav = [pts[0]]
        for i in range(1, n + 1):
            if p_disp * n >= i:
                trav.append(pts[i])
        cx, cy = point_at(p_disp); cpt = (rx + cx * rw, ry + cy * rh)
        trav.append(cpt)
        if len(trav) > 1:
            d.line(trav, fill=RED + (round(255 * a),), width=max(1, round(3.0 * u)), joint='curve')
        for i, q in enumerate(pts):
            r = 2.4 * u
            col = RED if p_disp * n >= i - 1e-6 else WHT
            d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col + (round((255 if col == RED else 150) * a),))
        # pulse ring + dot
        if pulse is not None:
            rr = (4.5 + 9 * pulse) * u
            d.ellipse([cpt[0] - rr, cpt[1] - rr, cpt[0] + rr, cpt[1] + rr], outline=YEL + (round(200 * a * (1 - pulse)),),
                      width=max(1, round(1.5 * u)))
        r = 4.6 * u
        d.ellipse([cpt[0] - r - 1.2 * u, cpt[1] - r - 1.2 * u, cpt[0] + r + 1.2 * u, cpt[1] + r + 1.2 * u], fill=(0, 0, 0, round(150 * a)))
        d.ellipse([cpt[0] - r, cpt[1] - r, cpt[0] + r, cpt[1] + r], fill=YEL + (round(255 * a),))
        # progress bar
        by = ry + rh + 12 * u
        bx0, bx1 = ox + self.pad * S, ox + self.pad * S + self.route_w * S
        bh = self.bar_h * S
        d.rounded_rectangle([bx0, by, bx1, by + bh], radius=bh / 2, fill=WHT + (round(64 * a),))
        fx = bx0 + (bx1 - bx0) * p_disp
        if fx > bx0 + bh:
            d.rounded_rectangle([bx0, by, fx, by + bh], radius=bh / 2, fill=RED + (round(255 * a),))
        d.rectangle([fx - 1.2 * u, by - 2 * u, fx + 1.2 * u, by + bh + 2 * u], fill=YEL + (round(255 * a),))
        return im.resize((self.cw, self.box_h), Image.LANCZOS)


def run_frames(hud, run, fade):
    n = run['f1'] - run['f0']
    shots = run['shots']
    piece_f0 = run['f0'] - round(run['t0'] * FPS)
    p_first = shots[0]['p0']
    p_from = max(0.0, p_first - 0.07)       # the travelled line draws in to here when the run starts
    prev_p, prev_place, change_t = p_from, None, run['t0']
    cur = None
    for k in range(n):
        t = (run['f0'] + k - piece_f0) / FPS      # chapter time of this frame
        s = next((s for s in shots if s['t'] <= t + 1e-6 < s['t'] + s['dur']), shots[-1])
        if cur is None or s is not cur:
            if cur is not None:
                prev_place = cur['place'] if s['place'] != cur['place'] else None
                prev_p = p_now
                change_t = t
            cur = s
        clk = s['clock_hold'] if 'clock_hold' in s else s['clock0'] + max(0.0, t - s['t']) * s['speed']
        p_target = s['p0'] + (s['p1'] - s['p0']) * max(0.0, min(1.0, (t - s['t']) / s['dur']))
        glide = 0.9 if change_t == run['t0'] else 0.5
        p_now = prev_p + (p_target - prev_p) * ease((t - change_t) / glide)
        xfade = min(1.0, (t - change_t) / 0.2) if prev_place else 1.0
        tr = (k + 0.5) / FPS; tl = (n - k - 0.5) / FPS
        a = min(1.0, tr / fade, tl / fade)
        slide_k = ease(min(1.0, tr / fade)) if tr < tl else ease(min(1.0, tl / fade))
        ph = ((t - run['t0']) - 0.6) % 1.8
        pulse = ph / 1.1 if (t - run['t0']) > 0.6 and ph < 1.1 else None
        yield hud.frame(s['place'], prev_place, xfade, clock_str(clk), p_now, a, slide_k, pulse)


def write_clip(frames, path, w, h):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}',
                          '-r', '30000/1001', '-i', '-', '-c:v', 'qtrle', path], stdin=subprocess.PIPE)
    k = 0
    for im in frames:
        p.stdin.write(im.tobytes()); k += 1
    p.stdin.close(); p.wait()
    assert p.returncode == 0, path
    return k


def main():
    out = sys.argv[1]; H = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 720
    os.makedirs(out, exist_ok=True)
    plan = json.load(open(f'{HERE}/hud.json'))
    hud = Hud(H)
    meta = dict(H=H, W=hud.W, x=hud.cx, y=hud.y, w=hud.cw, h=hud.box_h, runs=[])
    for i, r in enumerate(plan['runs']):
        path = f'{out}/run_{i:02d}.mov'
        k = write_clip(run_frames(hud, r, plan['fade']), path, hud.cw, hud.box_h)
        assert k == r['f1'] - r['f0']
        meta['runs'].append(dict(path=path, f0=r['f0'], f1=r['f1'], frames=k))
        print(f'run {i:02d} frames {r["f0"]}-{r["f1"]} ({k})')
    json.dump(meta, open(f'{out}/runs.json', 'w'), indent=1)
    if '--stills' in sys.argv:   # a design sheet: a few frames of each run on grey
        tiles = []
        for i, r in enumerate(plan['runs']):
            fr = list(run_frames(hud, r, plan['fade']))
            for k in (4, len(fr) // 2):
                bg = Image.new('RGBA', fr[k].size, (90, 110, 120, 255)); bg.alpha_composite(fr[k]); tiles.append(bg)
        W2, H2 = tiles[0].size
        sh = Image.new('RGB', (W2 * 4, H2 * math.ceil(len(tiles) / 4)), (40, 40, 40))
        for j, im in enumerate(tiles):
            sh.paste(im.convert('RGB'), ((j % 4) * W2, (j // 4) * H2))
        sh.save(f'{out}/design_sheet.png')


if __name__ == '__main__':
    main()
