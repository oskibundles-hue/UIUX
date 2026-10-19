#!/usr/bin/env python3
"""motion.py -- Omarie's 11 Oct 2026 motion picks (../PLAN.md, "Motion picks for the 4K pass"), drawn with PIL at any
frame height. Personal brand only: Anton, #DE1A22, #FBD101, white; Archivo for small type. No speed, no figures, no SE
marks.

    HUD C      route rail + big place line, on the drive runs of ../hud/hud.json (replaces the corner card)
    titles B   the slam: yellow "CHAPTER 0n" kicker, big Anton title (scale + blur), one light sweep, red and yellow
               stripe wipe; centre-left, in each title's own t0-t1 slot (replaces the red box)
    titles D   the slot-reel clock on the two time chapters (Ch1 "4:30 A.M.", Ch6 "1:29 A.M."), kicker under the digits
    joins      C the route card (about 1 s, black, the route snakes on, "NEXT · <chapter place>") and B the red, yellow
               and white slanted light band (about 0.33 s), one of each on every chapter join
    host tag D yellow brackets, a leader, OMARIE over @NQ.YOUNG, once, the first time he is on camera, about 4 s
    bar + tab E nine top segments (opening + 8 chapters) and a right-edge tab with the chapter number and name, for a
               few seconds after each title
Word pops (A) are unchanged: they stay in ../ch3/render.py (pop_frames).

Everything is sized from H (u = H / 720), drawn as single-colour masks at SS x and flattened to straight-alpha RGBA, so
the same code makes the 720p proof and the 4K overlays. `clips(H)` is the whole schedule: every overlay clip with its
global start frame, length and x, y. The mockup page's HTML/CSS was not on disk when this was written (13 Oct 2026), so
the look and timing follow PLAN.md's words, not the page's exact CSS.
"""
import functools, glob, json, math, os, re, subprocess
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
YT = os.path.dirname(HERE)
DAY = os.environ.get('VLOG_DAY', '/home/user/day-owt')   # the day folder (fonts); set VLOG_DAY to build outside the cloud container
FPS = 30000 / 1001
RED, YEL, WHT, BLK = (0xDE, 0x1A, 0x22), (0xFB, 0xD1, 0x01), (255, 255, 255), (0, 0, 0)
SS = 2                      # supersampling
CHAPTERS = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'ch7', 'ch8']
STOPS = ['SEATTLE', 'OREGON', 'IDAHO', 'NEVADA', 'LAS VEGAS']     # the rail's five stops = hud.json `nodes`
SHAPE = [(0.0, 0.0), (0.27, 0.62), (0.52, 0.28), (0.76, 0.82), (1.0, 1.0)]   # ../hud/render_hud.py's schematic zig-zag
# The route card's "NEXT · <chapter place>": the place words of the next chapter's own title. The two time chapters
# have no place in their title, so their card shows the title's time. Ch2 and Ch3 are both Seattle, so their cards
# carry the time of day from his chapter names in ../PLAN.md ("Seattle · morning", "Seattle, WA · noon"; 18 Oct
# proof check: two cards in a row said only Seattle). (For nq-facts.)
NEXT = {'ch1': '4:30 A.M.', 'ch2': 'SEATTLE · MORNING', 'ch3': 'SEATTLE · NOON', 'ch4': 'OREGON', 'ch5': 'NAMPA, IDAHO',
        'ch6': '1:29 A.M.', 'ch7': 'NEVADA', 'ch8': 'LAS VEGAS'}
REEL = ('ch1', 'ch6')       # titles D: the slot-reel clock
JOIN_N, JOIN_PRE, BAND_N = 30, 15, 10     # route card: 30 frames, 15 before the join; the light band is its last 10
TAG_T, TAG_N = 0.2, 120     # host tag: starts 0.2 s into his first on-camera shot, 120 frames (4.0 s)
BAR_N, BAR_LAP = 96, 4      # chapter bar + tab: 96 frames (3.2 s), starting 4 frames before the title ends


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_io(x):
    x = clamp(x); return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- fonts
def _font(*pats):
    for p in pats:
        g = sorted(glob.glob(p))
        if g:
            return g[0]
    raise SystemExit(f'font not found: {pats}')


@functools.lru_cache(maxsize=None)
def anton(px):
    return ImageFont.truetype(_font(f'{DAY}/fonts/fontsource-anton-*/files/anton-latin-400-normal.woff', f'{DAY}/fonts/Anton-Regular.ttf'), max(4, int(round(px))))


@functools.lru_cache(maxsize=None)
def _archivo(px, wght):
    g = glob.glob(f'{DAY}/fonts/fontsource-archivo-*/files/archivo-latin-{wght}-normal.woff')
    if g:
        return ImageFont.truetype(g[0], px)
    f = ImageFont.truetype(_font(f'{DAY}/fonts/Archivo.ttf'), px)   # the variable font (weight, width)
    f.set_variation_by_axes([wght, 100])
    return f


def archivo(wght):
    return lambda px: _archivo(max(4, int(round(px))), wght)


def tlen(font, s, track=0.0):
    return sum(font.getlength(c) for c in s) + track * (len(s) - 1) if track else font.getlength(s)


def text_mask(font, txt, pad):
    """L mask of `txt` with `pad` px around it -> (mask, origin x, baseline y in the mask, advance width)."""
    l, t, r, b = font.getbbox(txt, anchor='ls')
    m = Image.new('L', (int(math.ceil(r)) + 2 * pad, int(math.ceil(b - t)) + 2 * pad), 0)
    ImageDraw.Draw(m).text((pad, pad - t), txt, font=font, fill=255, anchor='ls')
    return m, pad, pad - t, r


# ---------------------------------------------------------------- drawing: colour masks -> straight-alpha RGBA
class Ink:
    """Shapes and text are drawn into one L mask per colour at SS x (coordinates are output px, floats welcome), then
    flattened in draw order. Straight alpha: no dark fringe on text over video."""

    def __init__(self, w, h, ss=SS):
        self.w, self.h, self.ss = int(w), int(h), ss
        self.layers = []

    def _layer(self, col):
        if not self.layers or self.layers[-1][0] != col:
            self.layers.append([col, Image.new('L', (self.w * self.ss, self.h * self.ss), 0)])
        return self.layers[-1]

    def _d(self, col):
        return ImageDraw.Draw(self._layer(col)[1])

    def rect(self, col, x0, y0, x1, y1, a=1.0):
        s = self.ss
        if x1 * s - 1 >= x0 * s and y1 * s - 1 >= y0 * s and a > 0:
            self._d(col).rectangle([x0 * s, y0 * s, x1 * s - 1, y1 * s - 1], fill=round(255 * a))

    def poly(self, col, pts, a=1.0):
        s = self.ss
        if a > 0:
            self._d(col).polygon([(x * s, y * s) for x, y in pts], fill=round(255 * a))

    def line(self, col, pts, width, a=1.0):
        s = self.ss
        if a > 0 and len(pts) > 1:
            self._d(col).line([(x * s, y * s) for x, y in pts], fill=round(255 * a), width=max(1, round(width * s)), joint='curve')

    def dot(self, col, cx, cy, r, a=1.0):
        s = self.ss
        if a > 0 and r > 0:
            self._d(col).ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=round(255 * a))

    def ring(self, col, cx, cy, r, width, a=1.0):
        s = self.ss
        if a > 0 and r > 0:
            self._d(col).ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], outline=round(255 * a), width=max(1, round(width * s)))

    def text(self, col, x, y, txt, font, size, a=1.0, track=0.0, anchor='ls'):
        """`font` is anton or archivo(weight); (x, y) is the left end of the baseline unless `anchor` says otherwise."""
        s = self.ss
        if a <= 0:
            return
        f = font(size * s); d = self._d(col)
        if track:
            cx = x * s
            for c in txt:
                d.text((cx, y * s), c, font=f, fill=round(255 * a), anchor=anchor)
                cx += f.getlength(c) + track * s
        else:
            d.text((x * s, y * s), txt, font=f, fill=round(255 * a), anchor=anchor)

    def width(self, txt, font, size, track=0.0):
        return tlen(font(size * self.ss), txt, track * self.ss) / self.ss

    def mask(self, col, m, x, y, a=1.0):
        """Add an SS-scale L mask with its top-left at output (x, y); keeps the brighter value where it overlaps."""
        if a <= 0:
            return
        lay = self._layer(col)
        if a < 1:
            m = m.point(lambda v: int(v * a))
        tmp = Image.new('L', lay[1].size, 0)
        tmp.paste(m, (int(round(x * self.ss)), int(round(y * self.ss))))
        lay[1] = ImageChops.lighter(lay[1], tmp)

    def flat(self, alpha=1.0, shadow=0.0, sblur=5.0, blur=None):
        """`blur` = (rx, ry) box-blurs every colour's mask (not the colours), so a blurred edge keeps its colour."""
        out = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        for col, m in self.layers:
            if self.ss > 1:
                m = m.reduce(self.ss)
            if blur:
                m = m.filter(ImageFilter.BoxBlur(blur))
            lay = Image.new('RGBA', (self.w, self.h), col + (255,)); lay.putalpha(m)
            out = Image.alpha_composite(out, lay)
        if shadow > 0:
            sa = out.getchannel('A').filter(ImageFilter.GaussianBlur(sblur)).point(lambda v: min(255, int(v * shadow)))
            sh = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 255)); sh.putalpha(sa)
            out = Image.alpha_composite(sh, out)
        if alpha < 1:
            out.putalpha(out.getchannel('A').point(lambda v: int(v * alpha)))
        return out


def clip_right(im, x):
    """Keep only what is left of x (a hard left-to-right clip)."""
    x = int(round(x))
    if x >= im.width:
        return im
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    if x > 0:
        out.paste(im.crop((0, 0, x, im.height)), (0, 0))
    return out


def even(v):
    return int(round(v)) // 2 * 2


def soft_patch(w, h, x1, y0, y1, soft, x0=None):
    """For white type over a bright picture: an L mask that is full from x0 (None = the left edge of the frame) to x1,
    between y0 and y1 (y0 None = from the top edge), and falls away over about 2 x `soft` px beyond them."""
    far = -6 * soft
    m = Image.new('L', (int(w), int(h)), 0)
    ImageDraw.Draw(m).rectangle([far if x0 is None else x0, far if y0 is None else y0, x1, y1], fill=255)
    return m.filter(ImageFilter.GaussianBlur(soft))


def on_patch(im, patch, a):
    """`im` over black at `patch` x a (a soft dark backing; nothing changes when a is 0)."""
    if a <= 0:
        return im
    bk = Image.new('RGBA', im.size, (0, 0, 0, 255)); bk.putalpha(patch.point(lambda v: int(v * a)))
    return Image.alpha_composite(bk, im)


# ---------------------------------------------------------------- HUD C: route rail + big place line
def clock_str(sec):
    sec = int(sec) % 86400
    h, m = sec // 3600, (sec % 3600) // 60
    return f'{(h % 12) or 12}:{m:02d} {"AM" if h < 12 else "PM"}'


class HudC:
    """Top-left: the place (Anton), under it a short yellow rule then the camera clock (Archivo 600). Left edge: a
    vertical rail with the five stops; passed stops red, the current stop yellow with a pulse ring, the red line filled
    to the trip progress. The clip is the left strip of the frame (x = y = 0)."""

    def __init__(self, H):
        self.H = H; self.W = even(H * 16 / 9); u = self.u = H / 720.0
        self.w, self.h = even(0.42 * self.W), H
        self.x = self.y = 0
        self.px = 44 * u                       # left edge of the place line and of the stop dots' column
        self.rx = 51 * u                       # the rail's centre line
        self.ry0, self.ry1 = 0.31 * H, 0.79 * H
        self.patches = {}
        # the stop labels (RAIL_LABEL) and the soft dark column behind the rail on every run (RAIL_BACKING)
        lx = self.rx + 16 * u
        lw = max(Ink(8, 8).width(s, archivo(700), RAIL_LABEL['size'] * u, RAIL_LABEL['track'] * u) for s in STOPS)
        self.rail_patch = soft_patch(self.w, self.h, lx + lw + 14 * u, self.ry0 - 22 * u, self.ry1 + 18 * u, 16 * u)

    def stop_y(self, i):
        return self.ry0 + (self.ry1 - self.ry0) * i / (len(STOPS) - 1)

    def frame(self, place, place_prev, xfade, clock, p, alpha, reveal, pulse, backing=0.0):
        u = self.u; k = Ink(self.w, self.h); lab = Ink(self.w, self.h)
        n = len(STOPS) - 1
        p = clamp(p)
        cur = min(n, int(p * n + 1e-6))        # the last stop reached
        yp = self.ry0 + (self.ry1 - self.ry0) * p
        # rail: the whole line ahead in white, the travelled part in red
        k.line(WHT, [(self.rx, self.ry0), (self.rx, self.ry1)], 2 * u, 0.42)
        ls = RAIL_LABEL['size'] * u
        capl = -archivo(700)(ls * SS).getbbox('H', anchor='ls')[1] / SS
        for i, name in enumerate(STOPS):
            a = 0.78 if i < cur else 1.0 if i == cur else 0.58
            lab.text(WHT, self.rx + 16 * u, self.stop_y(i) + capl / 2, name, archivo(700), ls, a, track=RAIL_LABEL['track'] * u)
            if i > cur:
                k.dot(WHT, self.rx, self.stop_y(i), 3.6 * u, 0.7)
        # place (Anton) with a quick crossfade at a change; the yellow rule and the clock under it
        cap = -anton(46 * u * SS).getbbox('H', anchor='ls')[1] / SS
        base = 0.075 * self.H + cap
        if place_prev and xfade < 1:
            k.text(WHT, self.px, base, place_prev, anton, 46 * u, 1 - xfade)
        k.text(WHT, self.px, base, place, anton, 46 * u, xfade if place_prev else 1.0)
        capc = -archivo(600)(18 * u * SS).getbbox('H', anchor='ls')[1] / SS
        base2 = base + 13 * u + capc
        k.text(WHT, self.px + 26 * u + 9 * u, base2, clock, archivo(600), 18 * u, 0.96)
        if yp > self.ry0 + 0.5 * u:
            k.line(RED, [(self.rx, self.ry0), (self.rx, yp)], 4 * u)
        for i in range(cur):
            k.dot(RED, self.rx, self.stop_y(i), 5 * u)
        k.rect(YEL, self.px, base2 - capc / 2 - 1.5 * u, self.px + 26 * u, base2 - capc / 2 + 1.5 * u)
        if abs(yp - self.stop_y(cur)) > 7 * u:     # the head of the red line, when it is clear of the current stop
            k.rect(YEL, self.rx - 6 * u, yp - 1.5 * u, self.rx + 6 * u, yp + 1.5 * u)
        if pulse is not None:
            k.ring(YEL, self.rx, self.stop_y(cur), (6 + 11 * pulse) * u, 1.6 * u, 0.85 * (1 - pulse))
        k.dot(YEL, self.rx, self.stop_y(cur), 5.6 * u)
        im = Image.alpha_composite(lab.flat(alpha, shadow=RAIL_LABEL['shadow'], sblur=4 * u), k.flat(alpha, shadow=0.6, sblur=4 * u))
        if reveal < 1:                          # the clip-in runs over what is drawn, not over the empty strip
            bb = im.getbbox()
            im = clip_right(im, reveal * (bb[2] + 4 * u) if bb else 0)
        im = on_patch(im, self.rail_patch, RAIL_BACKING * min(alpha, reveal))
        if backing > 0:                         # a bright sky behind the place line: a soft dark corner under it
            wp = max(k.width(q, anton, 46 * u) for q in (place, place_prev) if q)
            key = round(wp)
            if key not in self.patches:
                self.patches[key] = soft_patch(self.w, self.h, self.px + wp + 26 * u, None, base2 + 26 * u, 22 * u)
            im = on_patch(im, self.patches[key], backing * min(alpha, reveal))
        return im


def hud_frames(H, run, fade, backing=0.0):
    """One drive run of hud.json. The shot lookup, the camera clock and the progress glide are ../hud/render_hud.py's
    run_frames; only the drawing differs. It clips in left to right over `fade` and fades out over `fade`."""
    hud = HudC(H)
    n = run['f1'] - run['f0']
    shots = run['shots']
    piece_f0 = run['f0'] - round(run['t0'] * FPS)
    prev_p, prev_place, change_t = max(0.0, shots[0]['p0'] - 0.07), None, run['t0']
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
        p_target = s['p0'] + (s['p1'] - s['p0']) * clamp((t - s['t']) / s['dur'])
        glide = 0.9 if change_t == run['t0'] else 0.5
        p_now = prev_p + (p_target - prev_p) * ease_out((t - change_t) / glide)
        xfade = min(1.0, (t - change_t) / 0.2) if prev_place else 1.0
        tr = (k + 0.5) / FPS; tl = (n - k - 0.5) / FPS
        ph = ((t - run['t0']) - 0.6) % 1.8
        pulse = ph / 1.1 if (t - run['t0']) > 0.6 and ph < 1.1 else None
        yield hud.frame(s['place'], prev_place, xfade, clock_str(clk), p_now, min(1.0, tl / fade), ease_out(tr / fade), pulse, backing)


# ---------------------------------------------------------------- titles B (the slam) and D (the slot-reel clock)
TITLE_X = 0.055           # the chapter titles' left edge, as the old red box
# Per-clip changes from the 13 Oct proof check. A chapter or run not listed keeps the standard look.
#   ch5  At the standard size and place "NAMPA, IDAHO · NIGHT" ran across his cap and forehead. He moves through the
#        middle and right of the frame for the whole title (two handheld shots); the top-left is the only part he
#        never enters, and only about its left 600 px at 720p. So the title sits there at 62 instead of 90, with
#        its kicker's top where the HUD place line's top is (0.075 H). The kicker and the stripes keep their size.
#        Measured on the clean 720p shots: 58 px or more from his head (clip-on mic included) on all 99 frames.
#   ch8  "LAS VEGAS" and the HUD's "LAS VEGAS, NV" are white type on a white overcast sky: a soft dark patch behind
#        the title block (kicker included), and the same in the corner behind the HUD's place line and clock on the
#        arrival run. 0.6 puts the white type at about 4.5 to 1 against a white sky.
# Second round, from the 18 Oct check of the approved proof (Omarie: approve, but fix the small notes first):
#   ch7  "SUNRISE · NEVADA" at the standard size and place lay across his neck and chest. The top band of both
#        shots is the dark headliner (then the dark visor over the desert), so the title goes there the ch5 way: 62,
#        centre line 0.12 H (0.14 still came within 6-15 px of his head on several frames). Measured on the clean 720p
#        shots, YuNet face box widened to a head box (0.6 face heights up for hair, 0.25 to each side): no overlap on
#        the 72 frames with his face found, closest 9 px in the 1.85x landing (frames 3-5), 21 px once landed, median
#        41 px. The last 27 frames (from 14425) found no face, so they are not measured.
#   ch6  "1:29 A.M." reached his face as he leans left (7:13-7:15): the reel at 0.78 (digits 128 -> 100, A.M. 56 -> 44),
#        same left edge, so A.M. ends near 0.26 W.
#   all  the yellow CHAPTER kicker was lost on an orange wall (ch3) and an orange seat (ch4): 17 instead of 15, a
#        stronger shadow of its own and a small soft dark patch behind it (KICKER).
#   HUD  the rail's stop labels were too small and lost on sky and the Rio billboard (ch8): 14 instead of 11.5, a
#        stronger shadow and a soft dark column behind the rail on every run (RAIL_LABEL, RAIL_BACKING). hud.json's
#        run 3 (NEVADA after the "NEXT · LAS VEGAS" card) is dropped, so the arrival run is now run 3.
SLAM_FIX = {'ch5': dict(size=62, yc=0.1427), 'ch7': dict(size=62, yc=0.12), 'ch8': dict(backing=0.6)}   # slam_frames() keywords, by chapter
REEL_FIX = {'ch6': dict(scale=0.78)}                     # reel_frames() keywords, by chapter
HUD_BACKING = {3: 0.6}       # hud.json run index -> strength of the patch behind the place line (3 = LAS VEGAS, NV)
KICKER = dict(size=17, shadow=0.85, backing=0.5)         # the CHAPTER kicker on every title
RAIL_LABEL = dict(size=14, track=1.8, shadow=0.85)       # the HUD rail's stop labels
RAIL_BACKING = 0.55          # the soft dark column behind the rail, every run
TAB_NAME = 16                # the chapter tab's name (was 13.5; too small on a phone)


def kicker_patch(W, H, kicker, x, baseline, u):
    """The small soft dark patch behind a CHAPTER kicker whose baseline starts at (x, baseline)."""
    kw = Ink(8, 8).width(kicker, archivo(800), KICKER['size'] * u, 3.2 * u)
    capk = -archivo(800)(KICKER['size'] * u * SS).getbbox('H', anchor='ls')[1] / SS
    return soft_patch(W, H, x + kw + 10 * u, baseline - capk - 6 * u, baseline + 5 * u, 7 * u, x0=x - 10 * u)


def slam_frames(H, text, kicker, n, size=90, yc=0.5, backing=0.0):
    """Titles B. Kicker (yellow, small) slides in; the title lands from 1.85x with blur and a small squash; one light
    sweep crosses it; a red stripe and a shorter yellow one wipe in under it. Out: 0.3 s fade with a small slide.
    `size` (the title's px at 720p), `yc` (the block's centre line as a share of H) and `backing` (strength of a soft
    dark patch behind the block) are the per-title changes in SLAM_FIX; the defaults are the standard look."""
    W = even(H * 16 / 9); u = H / 720.0
    dur = n / FPS
    size = size * u
    f = anton(size * SS)
    pad = int(40 * u * SS)
    tm, ox, oy, adv = text_mask(f, text, pad)
    l, t, r, b = f.getbbox(text, anchor='ls')
    cap = -f.getbbox('H', anchor='ls')[1] / SS
    tw = adv / SS
    x0 = TITLE_X * W
    base = yc * H + cap / 2 + 4 * u                       # the block (kicker, title, stripes) sits on the centre line
    cx, cy = x0 + tw / 2, base + (t + b) / 2 / SS         # the title's centre: it scales about this point
    glow = tm.filter(ImageFilter.GaussianBlur(7 * u * SS))
    patch = soft_patch(W, H, x0 + tw + 26 * u, base - cap - 27 * u - 26 * u, base + 29 * u + 26 * u, 22 * u) if backing > 0 else None
    kb = base - cap - 16 * u                              # the kicker's baseline
    kpatch = kicker_patch(W, H, kicker, x0 + 2 * u, kb, u)
    for k in range(n):
        tt = k / FPS
        out = clamp((dur - tt) / 0.3)
        dx = -18 * u * (1 - out) ** 2
        ink = Ink(W, H)
        # the title: 0.08 s after the kicker
        ts = tt - 0.08
        if ts >= 0:
            if ts < 0.2:
                sc = 1.85 - 0.85 * (ts / 0.2) ** 2
            elif ts < 0.34:
                sc = 1 - 0.035 * math.sin(math.pi * (ts - 0.2) / 0.14)
            else:
                sc = 1.0
            a = min(1.0, (ts + 0.5 / FPS) / 0.07)
            m = tm
            if sc != 1.0:
                m = tm.resize((max(2, round(tm.width * sc)), max(2, round(tm.height * sc))), Image.BILINEAR)
                br = 9 * u * SS * (sc - 1) / 0.85
                if br > 0.3:
                    m = m.filter(ImageFilter.GaussianBlur(br))
            mx, my = cx + dx - m.width / 2 / SS, cy - m.height / 2 / SS
            sw = (ts - 0.42) / 0.56                       # the light sweep: 0.42 -> 0.98 s after the title lands
            band = None
            if 0 < sw < 1 and sc == 1.0:
                bw = max(44 * u, 0.09 * tw) * SS; sl = 0.36 * tm.height
                bx = (-0.12 + 1.24 * sw) * tm.width
                band = Image.new('L', tm.size, 0)
                ImageDraw.Draw(band).polygon([(bx - bw / 2 + sl / 2, 0), (bx + bw / 2 + sl / 2, 0), (bx + bw / 2 - sl / 2, tm.height), (bx - bw / 2 - sl / 2, tm.height)], fill=255)
                band = band.filter(ImageFilter.GaussianBlur(9 * u * SS))
                ink.mask(WHT, ImageChops.multiply(glow, band), mx, my, 0.55)   # the light spills a little past the letters
            ink.mask((232, 232, 232), m, mx, my, a)
            if band is not None:
                ink.mask(WHT, ImageChops.multiply(tm, band), mx, my)
        # stripes under the title
        sy = base + 15 * u
        w1 = ease_out((tt - 0.30) / 0.30) * tw
        w2 = ease_out((tt - 0.40) / 0.30) * tw * 0.42
        ink.rect(RED, x0 + dx, sy, x0 + dx + w1, sy + 7 * u)
        ink.rect(YEL, x0 + dx, sy + 11 * u, x0 + dx + w2, sy + 14 * u)
        # kicker: its own ink, for its own (stronger) shadow, over a small soft dark patch
        ka = min(1.0, (tt + 0.5 / FPS) / 0.15)
        kx = x0 + dx - 14 * u * (1 - ease_out(tt / 0.25))
        ki = Ink(W, H)
        ki.text(YEL, kx + 2 * u, kb, kicker, archivo(800), KICKER['size'] * u, ka, track=3.2 * u)
        im = Image.alpha_composite(ink.flat(out, shadow=0.55, sblur=6 * u), ki.flat(out, shadow=KICKER['shadow'], sblur=5 * u))
        im = on_patch(im, kpatch, KICKER['backing'] * ka * out)
        yield on_patch(im, patch, backing * ka * out) if patch is not None else im


def reel_frames(H, text, kicker, n, scale=1.0):
    """Titles D, for a time title like "4:30 A.M.": each digit is a reel that rolls up and lands in turn; the colon
    holds; A.M. slides in; a short red rule and the yellow kicker come in under the digits when the last reel lands.
    `scale` (REEL_FIX) shrinks the digits, A.M. and their spacing about the same left edge; the kicker keeps its size."""
    W = even(H * 16 / 9); u = H / 720.0
    dur = n / FPS
    time_s, _, suffix = text.partition(' ')
    v = u * scale
    size, ssz = 128 * v, 56 * v
    f = anton(size * SS)
    cap = -f.getbbox('H', anchor='ls')[1] / SS
    dw = max(f.getlength(str(d)) for d in range(10)) / SS            # one cell for every digit, so nothing shifts
    x0 = TITLE_X * W
    base = 0.5 * H + cap / 2 - 10 * v
    padc = 6 * v
    pitch = cap + 2 * padc + 10 * v                                   # distance between two digits on a reel
    cells = []; x = x0; di = 0
    for c in time_s:
        if c.isdigit():
            cells.append((c, x, di)); x += dw; di += 1
        else:
            cells.append((c, x, None)); x += f.getlength(c) / SS
    xs = x + 14 * v                                                   # A.M. starts here
    nd = di
    stop = [0.72 + 0.2 * i for i in range(nd)]                        # when each reel lands
    steps = [14 + 5 * i for i in range(nd)]
    cw_, ch_ = int(math.ceil(dw * SS)), int(math.ceil((cap + 2 * padc) * SS))
    kb = base + 34 * v                                                # the kicker's baseline, once it has landed
    kpatch = kicker_patch(W, H, kicker, x0 + 40 * u, kb, u)
    for k in range(n):
        tt = k / FPS
        out = clamp((dur - tt) / 0.3)
        dx = -18 * u * (1 - out) ** 2
        ain = min(1.0, (tt + 0.5 / FPS) / 0.1)
        ink = Ink(W, H)
        for c, x, i in cells:
            if i is None:
                ink.text(WHT, x + dx, base, c, anton, size, ain)
                continue
            pos = steps[i] * ease_out(tt / stop[i])                   # in digit steps; lands on steps[i]
            vel = steps[i] * (ease_out((tt + 0.5 / FPS) / stop[i]) - ease_out((tt - 0.5 / FPS) / stop[i]))   # steps per frame
            cell = Image.new('L', (cw_, ch_), 0); d = ImageDraw.Draw(cell)
            k0 = int(math.floor(pos))
            for kk in (k0, k0 + 1):
                if kk > steps[i]:
                    continue
                dg = (int(c) - (steps[i] - kk)) % 10
                gw = f.getlength(str(dg))
                d.text(((cw_ - gw) / 2, (padc + cap) * SS + (kk - pos) * pitch * SS), str(dg), font=f, fill=255, anchor='ls')
            vb = abs(vel) * pitch * SS * 0.35
            if vb > 1:
                cell = cell.filter(ImageFilter.BoxBlur((0, min(vb, ch_ / 3))))
            ink.mask(WHT, cell, x + dx, base - cap - padc, ain)
        sa = clamp((tt - 0.35) / 0.25)
        ink.text(WHT, xs + dx + 10 * v * (1 - ease_out((tt - 0.35) / 0.25)), base, suffix, anton, ssz, sa)
        ka = clamp((tt - stop[-1]) / 0.25)
        ky = kb + 6 * u * (1 - ease_out((tt - stop[-1]) / 0.25))
        ink.rect(RED, x0 + dx, ky - 9 * u, x0 + dx + 30 * u * ka, ky - 5 * u)
        ki = Ink(W, H)
        ki.text(YEL, x0 + dx + 40 * u, ky, kicker, archivo(800), KICKER['size'] * u, ka, track=3.2 * u)
        im = Image.alpha_composite(ink.flat(out, shadow=0.55, sblur=6 * u), ki.flat(out, shadow=KICKER['shadow'], sblur=5 * u))
        yield on_patch(im, kpatch, KICKER['backing'] * ka * out)


# ---------------------------------------------------------------- joins: C the route card + B the light band
def point_at(p, box):
    x0, y0, w, h = box
    n = len(SHAPE) - 1
    q = clamp(p) * n
    i = min(int(q), n - 1); fr = q - i
    (ax, ay), (bx, by) = SHAPE[i], SHAPE[i + 1]
    return x0 + (ax + (bx - ax) * fr) * w, y0 + (ay + (by - ay) * fr) * h


def path_to(p, box):
    """The route polyline from the first stop to progress p."""
    n = len(SHAPE) - 1
    pts = [point_at(i / n, box) for i in range(n + 1) if i / n < p - 1e-9]
    return pts + [point_at(p, box)]


def band_poly(xl, xr, H, slant):
    """A slanted stripe: its left and right edges at mid-height are xl and xr; the top leans right by `slant`."""
    return [(xl + slant / 2, 0), (xr + slant / 2, 0), (xr - slant / 2, H), (xl - slant / 2, H)]


def join_frames(H, p_from, p_to, label):
    """One chapter join, JOIN_N frames, full frame. The black card fades in over 3 frames; the schematic route draws on,
    the red line snakes from p_from to p_to (None = the trip has not started) and the stop ahead pulses; under it
    "NEXT · <label>". Its last BAND_N frames are the light band: three slanted stripes (red, yellow, white) cross
    left to right and wipe the card away, so the new chapter is under the band."""
    W = even(H * 16 / 9); u = H / 720.0
    box = (0.19 * W, 0.31 * H, 0.62 * W, 0.15 * H)
    n = len(SHAPE) - 1
    slant = 0.34 * H
    wr, wy, ww = 0.085 * W, 0.055 * W, 0.03 * W            # red, yellow, white stripe widths (white leads)
    travel = W + slant + wr + wy + ww
    for k in range(JOIN_N):
        ca = min(1.0, (k + 1) / 3)
        ink = Ink(W, H)
        ink.rect(BLK, 0, 0, W, H, ca)
        g = ease_out((k - 0.5) / 8)                         # the route line draws on
        if g > 0:
            ink.line(WHT, path_to(g, box), 3 * u, 0.36 * ca)
        p = None
        if p_to is not None:
            p = p_to if p_from is None else p_from + (p_to - p_from) * ease_io((k - 6) / 13)
        target = None if p_to is None else min(n, int(math.ceil(p_to * n - 1e-6)))    # the stop this chapter is heading for
        for i, name in enumerate(STOPS):
            x, y = point_at(i / n, box)
            show = clamp((g * n - i + 0.6) / 0.6)
            passed = p is not None and p * n >= i - 1e-6
            lw = ink.width(name, archivo(700), 12 * u, 1.8 * u)
            ink.text(WHT, x - lw / 2, y + 30 * u, name, archivo(700), 12 * u, (0.95 if passed or i == target else 0.6) * show * ca, track=1.8 * u)
            if not passed:
                ink.dot(WHT, x, y, 4.5 * u, 0.75 * show * ca)
        if p is not None:
            if p > 1e-6:
                ink.line(RED, path_to(p, box), 5.5 * u, ca)
            for i in range(n + 1):
                if p * n >= i - 1e-6:
                    ink.dot(RED, *point_at(i / n, box), 6 * u, ca)
            hx, hy = point_at(p, box)
            pop = ease_out((k - 5) / 5) if p_from is None else 1.0
            pu = ((k - 8) % 14) / 14
            if k >= 8:
                tx, ty = point_at(target / n, box)
                ink.ring(YEL, tx, ty, (8 + 14 * pu) * u, 2 * u, 0.9 * (1 - pu) * ca)
            ink.dot(YEL, hx, hy, 7.5 * u * pop, ca)
        # NEXT · <label>, centred
        la = clamp((k - 1) / 6) * ca
        ly = 0.72 * H + 10 * u * (1 - ease_out((k - 1) / 7))
        w1 = ink.width('NEXT', archivo(800), 19 * u, 5 * u); w2 = ink.width(label, anton, 56 * u)
        gap = 20 * u
        lx = (W - (w1 + 2 * gap + 8 * u + w2)) / 2
        ink.text(YEL, lx, ly, 'NEXT', archivo(800), 19 * u, la, track=5 * u)
        ink.dot(RED, lx + w1 + gap + 4 * u, ly - 8 * u, 4 * u, la)
        ink.text(WHT, lx + w1 + 2 * gap + 8 * u, ly, label, anton, 56 * u, la)
        im = ink.flat()
        b0 = JOIN_N - BAND_N
        if k >= b0:
            e = (k - b0 + 0.5) / BAND_N
            xt = -slant / 2 - (wr + wy + ww) + e * travel      # the band's trailing edge at mid-height
            # wipe: everything left of the trailing edge is the new chapter
            keep = Image.new('L', (W * SS, H * SS), 0)
            ImageDraw.Draw(keep).polygon([(x * SS, y * SS) for x, y in band_poly(xt, W + slant, H, slant)], fill=255)
            keep = keep.reduce(SS)
            im.putalpha(ImageChops.multiply(im.getchannel('A'), keep))
            bi = Ink(W, H)
            bi.poly(RED, band_poly(xt, xt + wr, H, slant))
            bi.poly(YEL, band_poly(xt + wr, xt + wr + wy, H, slant))
            bi.poly(WHT, band_poly(xt + wr + wy, xt + wr + wy + ww, H, slant))
            im = Image.alpha_composite(im, bi.flat(blur=(10 * u, 0)))     # a light streak, not hard bars
        yield im


# ---------------------------------------------------------------- D the host tag
class HostTag:
    """Lower-left: yellow square brackets around OMARIE (Anton) over @NQ.YOUNG (Archivo 700), and a leader (a thin
    white elbow line ending in a yellow ring) running up and right from the tag. The clip is the lower-left quarter."""

    def __init__(self, H):
        self.H = H; self.W = even(H * 16 / 9)
        self.x, self.y = 0, even(0.46 * H)
        self.w, self.h = even(0.5 * self.W), even(0.5 * H)

    def frames(self, n=TAG_N):
        H, W = self.H, self.W; u = H / 720.0
        dur = n / FPS
        x0 = TITLE_X * W
        name, handle = 'OMARIE', '@NQ.YOUNG'
        probe = Ink(self.w, self.h)
        nw = probe.width(name, anton, 46 * u); hw = probe.width(handle, archivo(700), 15 * u, 2.6 * u)
        cap = -anton(46 * u * SS).getbbox('H', anchor='ls')[1] / SS
        bw = max(nw, hw)
        tx = x0 + 18 * u                                   # text left edge
        nb = 0.80 * H - self.y                             # OMARIE baseline (in the clip)
        hb = nb + 26 * u                                   # handle baseline
        top, bot = nb - cap - 12 * u, hb + 12 * u
        xl, xr = x0, tx + bw + 18 * u                      # bracket spines
        arm, th = 13 * u, 3.2 * u
        mid = (xl + xr) / 2
        ex, ey = xr + 44 * u, top - 34 * u                 # the leader's elbow
        fx = ex + 46 * u                                   # ... and its end
        for k in range(n):
            tt = k / FPS
            out = clamp((dur - tt) / 0.3)
            ink = Ink(self.w, self.h)
            op = ease_out(tt / 0.3)                        # brackets open from the middle
            a = min(1.0, (tt + 0.5 / FPS) / 0.1)
            for sx, sgn in ((mid + (xl - mid) * op, 1), (mid + (xr - mid) * op, -1)):
                ink.rect(YEL, sx - th / 2, top, sx + th / 2, bot, a)
                ink.rect(YEL, min(sx, sx + sgn * arm), top, max(sx, sx + sgn * arm), top + th, a)
                ink.rect(YEL, min(sx, sx + sgn * arm), bot - th, max(sx, sx + sgn * arm), bot, a)
            ld = ease_io((tt - 0.3) / 0.35)                # the leader draws out from the right bracket's top corner
            if ld > 0:
                seg1 = math.hypot(ex - xr, ey - top); seg2 = fx - ex
                d = ld * (seg1 + seg2)
                pts = [(xr, top)]
                if d <= seg1:
                    pts.append((xr + (ex - xr) * d / seg1, top + (ey - top) * d / seg1))
                else:
                    pts += [(ex, ey), (ex + (d - seg1), ey)]
                ink.line(WHT, pts, 2 * u, 0.95)
            wipe = ease_out((tt - 0.2) / 0.3)
            im_t = Ink(self.w, self.h)
            im_t.text(WHT, tx, nb, name, anton, 46 * u)
            ha = clamp((tt - 0.4) / 0.25)
            if ld >= 1:
                ink.ring(YEL, fx + 5 * u, ey, 5 * u, 2.2 * u, clamp((tt - 0.65) / 0.1))
            lower = ink.flat(shadow=0.55, sblur=5 * u)
            name_im = clip_right(im_t.flat(shadow=0.55, sblur=5 * u), tx + wipe * (nw + 8 * u)) if wipe < 1 else im_t.flat(shadow=0.55, sblur=5 * u)
            hk = Ink(self.w, self.h)
            hk.text(WHT, tx + 1 * u, hb, handle, archivo(700), 15 * u, ha, track=2.6 * u)
            im = Image.alpha_composite(Image.alpha_composite(lower, name_im), hk.flat(shadow=0.55, sblur=4 * u))
            if out < 1:
                im.putalpha(im.getchannel('A').point(lambda v: int(v * out)))
            yield im


# ---------------------------------------------------------------- E the chapter bar + tab
def bar_frames(H, index, number, name, frac0, frac1, n=BAR_N):
    """Nine equal segments along the top (opening + 8 chapters): passed ones red, the current one yellow up to how far
    the chapter has run (frac0 at the first frame, frac1 at the last), the rest white at a third. A tab on the right
    edge under the bar: the chapter number on red (Anton), the name on a dark backing (Archivo 700). The segments wipe
    in one after the other and the tab slides in from the right; both fade and slide out."""
    W = even(H * 16 / 9); u = H / 720.0
    dur = n / FPS
    bx0, bx1, by, bh, gap = 44 * u, W - 44 * u, 20 * u, 4.5 * u, 6 * u
    seg = (bx1 - bx0 - 8 * gap) / 9
    probe = Ink(8, 8)
    nmw = probe.width(name, archivo(700), TAB_NAME * u, 1.8 * u)
    numw = 44 * u
    tw = numw + 14 * u + nmw + 18 * u
    ty0, ty1 = 40 * u, 76 * u
    capn = -anton(23 * u * SS).getbbox('H', anchor='ls')[1] / SS
    capm = -archivo(700)(TAB_NAME * u * SS).getbbox('H', anchor='ls')[1] / SS
    for k in range(n):
        tt = k / FPS
        out = clamp((dur - tt) / 0.3)
        ink = Ink(W, H)
        frac = frac0 + (frac1 - frac0) * k / max(1, n - 1)
        for i in range(9):
            g = ease_out((tt - 0.03 * i) / 0.22)
            x = bx0 + i * (seg + gap)
            ink.rect(WHT, x, by, x + seg * g, by + bh, 0.34)
        for i in range(index):
            g = ease_out((tt - 0.03 * i) / 0.22)
            x = bx0 + i * (seg + gap)
            ink.rect(RED, x, by, x + seg * g, by + bh)
        g = ease_out((tt - 0.03 * index) / 0.22)
        x = bx0 + index * (seg + gap)
        ink.rect(YEL, x, by, x + seg * g, by + bh, 0.5)
        ink.rect(YEL, x, by, x + seg * min(g, clamp(frac)), by + bh)
        bar = ink.flat(shadow=0.5, sblur=3 * u)
        # the tab: slides in from the right edge after 0.15 s
        sl = ease_out((tt - 0.15) / 0.3) * out ** 0.5
        tx = W - tw * sl
        tab = Ink(W, H)
        tab.rect(BLK, tx + numw, ty0, W, ty1, 0.66)
        tab.rect(RED, tx, ty0, tx + numw, ty1)
        nw_ = tab.width(number, anton, 23 * u)
        tab.text(WHT, tx + (numw - nw_) / 2, (ty0 + ty1) / 2 + capn / 2, number, anton, 23 * u)
        tab.text(WHT, tx + numw + 14 * u, (ty0 + ty1) / 2 + capm / 2, name, archivo(700), TAB_NAME * u, track=1.8 * u)
        im = Image.alpha_composite(bar, tab.flat())
        if out < 1:
            im.putalpha(im.getchannel('A').point(lambda v: int(v * out)))
        yield im


# ---------------------------------------------------------------- the schedule
def _clock_min(s):
    m = re.match(r'(\d+):(\d+)\s*([AP])\.?M', s.upper())
    return (int(m.group(1)) % 12 + (12 if m.group(3) == 'P' else 0)) * 60 + int(m.group(2))


def titles():
    """{chapter: (text, t0, t1)}: Ch1-4 keep the title in render.py (TITLE = dict(...)), Ch5-8 in edl.json `title`."""
    out = {}
    for c in CHAPTERS:
        e = json.load(open(f'{YT}/{c}/edl.json'))
        if 'title' in e:
            out[c] = (e['title']['text'], e['title']['t0'], e['title']['t1'])
        else:
            m = re.search(r"^TITLE = dict\(text='([^']+)', t0=([\d.]+), t1=([\d.]+)\)", open(f'{YT}/{c}/render.py').read(), re.M)
            assert m, f'{c}: no TITLE in render.py'
            out[c] = (m.group(1), float(m.group(2)), float(m.group(3)))
    return out


def route_progress(plan, ttl):
    """Trip progress (0-1 along the five stops) when each chapter starts, for the route cards. Schematic, on hud.json's
    own rule (the camera clock between the stop moments): None before Seattle; Ch2 and Ch3 at Seattle; Ch4 heads for
    Oregon, Ch5 for Idaho, Ch7 for Nevada, Ch8 for Las Vegas; Ch6 ("1:29 A.M.") sits between Idaho (7:44 PM) and
    Nevada (6:24 AM) by its title's clock."""
    nodes = {n['name']: _clock_min(n['clock']) for n in plan['nodes']}
    a, b, t = nodes['Idaho'], nodes['Nevada'] + 1440, _clock_min(ttl['ch6'][0]) + 1440
    return {'opening': None, 'ch1': None, 'ch2': 0.0, 'ch3': 0.0, 'ch4': 0.25, 'ch5': 0.5,
            'ch6': round(0.5 + 0.25 * (t - a) / (b - a), 4), 'ch7': 0.75, 'ch8': 1.0}


def first_on_camera():
    """(global frame, frames in the shot) of the first shot with him on camera: the opening's first 'talk' shot."""
    e = json.load(open(f'{YT}/opening-test/edl_B2.json'))
    f = 0
    for s in e['shots']:
        nf = round(s['dur'] * FPS)
        if s['kind'] == 'talk':
            return f, nf, s
        f += nf
    raise SystemExit('no talk shot in the opening')


def clips(H):
    """Every overlay clip, bottom to top: dicts with name, kind, f0 (global frame), n (frames), x, y, w, h, frames
    (a generator of RGBA images) and what it shows. Word pops are added by the caller from ../ch3/render.py."""
    W = even(H * 16 / 9)
    plan = json.load(open(f'{YT}/hud/hud.json'))
    piece = {p['name']: p for p in plan['pieces']}
    ttl = titles()
    prog = route_progress(plan, ttl)
    out = []
    hud = HudC(H)
    for i, r in enumerate(plan['runs']):
        out.append(dict(name=f'hud_{i:02d}', kind='hud', piece=r['piece'], f0=r['f0'], n=r['f1'] - r['f0'], x=hud.x, y=hud.y, w=hud.w, h=hud.h,
                        frames=functools.partial(hud_frames, H, r, plan['fade'], HUD_BACKING.get(i, 0.0)), what=f'HUD C run {i} ({r["shots"][0]["place"]})'))
    for j, c in enumerate(CHAPTERS):
        text, t0, t1 = ttl[c]
        n = round((t1 - t0) * 29.97)                       # as the old graphics()
        f0 = piece[c]['frame0'] + math.ceil(t0 * FPS - 1e-6)   # the first frame at or after t0: where the old `-itsoffset t0` title landed
        kick = f'CHAPTER {j + 1:02d}'
        mk = reel_frames if c in REEL else slam_frames
        out.append(dict(name=f'title_{c}', kind='title_reel' if c in REEL else 'title_slam', piece=c, f0=f0, n=n, x=0, y=0, w=W, h=H,
                        frames=functools.partial(mk, H, text, kick, n, **(REEL_FIX if c in REEL else SLAM_FIX).get(c, {})), what=f'title {"D slot reel" if c in REEL else "B slam"} "{text}"'))
        fb = f0 + n - BAR_LAP
        fr = lambda f: (f - piece[c]['frame0']) / piece[c]['frames']
        out.append(dict(name=f'bar_{c}', kind='bar', piece=c, f0=fb, n=BAR_N, x=0, y=0, w=W, h=H,
                        frames=functools.partial(bar_frames, H, j + 1, f'{j + 1:02d}', text, fr(fb), fr(fb + BAR_N)), what=f'chapter bar + tab {j + 1:02d} {text}'))
    tf, tn, ts = first_on_camera()
    tag = HostTag(H)
    assert round(TAG_T * FPS) + TAG_N <= tn, 'the host tag runs past his first shot'
    out.append(dict(name='host_tag', kind='tag', piece='opening', f0=tf + round(TAG_T * FPS), n=TAG_N, x=tag.x, y=tag.y, w=tag.w, h=tag.h,
                    frames=tag.frames, what=f'host tag (first talk shot: {ts["src"]} {ts["in"]})'))
    prev = 'opening'
    for c in CHAPTERS:
        J = piece[c]['frame0']
        out.append(dict(name=f'join_{c}', kind='join', piece=c, f0=J - JOIN_PRE, n=JOIN_N, x=0, y=0, w=W, h=H, join=J,
                        frames=functools.partial(join_frames, H, prog[prev], prog[c], NEXT[c]), what=f'route card "NEXT · {NEXT[c]}" + light band, {prev} -> {c}'))
        prev = c
    return out


def write_clip(frames, path, w, h, ff='ffmpeg'):
    """RGBA frames -> a qtrle .mov (alpha kept). Returns the frame count."""
    p = subprocess.Popen([ff, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-r', '30000/1001', '-i', '-',
                          '-c:v', 'qtrle', path], stdin=subprocess.PIPE)
    k = 0
    for im in frames:
        assert im.size == (w, h), (im.size, w, h)
        p.stdin.write(im.tobytes()); k += 1
    p.stdin.close(); p.wait()
    assert p.returncode == 0, path
    return k
