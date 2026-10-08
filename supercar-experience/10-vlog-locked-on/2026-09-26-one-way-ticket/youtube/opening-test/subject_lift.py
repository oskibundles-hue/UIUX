#!/usr/bin/env python3
"""subject_lift.py -- v2 fix 2 (Omarie, 8 Oct): brighten only HIM in the dark CH1 tail (0075 80.5-86.38), not the room.

  track   python3 subject_lift.py track
          CSRT-tracks his face through the shot from four hand-set anchors (720p px, read off a gridded sheet of the
          un-lifted graded shot) -> lift_track_0075_80.5.json (a face box per frame) + a check sheet in WORK.
  apply   used by render.py (look.json "subject_lift"): the shot's frames come in as 1280x720 yuv444p16le (after the
          grade, a mild hqdn3d and the scale), and each frame gets a GAMMA lift of a lightly smoothed luma, with the
          chroma scaled alongside (skin keeps its colour), weighted by  w = soft ellipse around the tracked face (gaussian falloff) x soft luma key (only
          pixels darker than 0.08-0.16 of the range on a blurred copy: his silhouette, never the lit ceiling around
          his head, so no halo). The gain is solved per frame so the face-core median reaches TARGET (the hook's face
          luma, 44-49 on the 0-255 scale), capped at GAMMA_MAX, then smoothed over 0.5 s; frames at or above TARGET get
          none.
  measure python3 subject_lift.py measure <video> <t0_in_video> [track.json]   face-box median luma every 0.5 s.
"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = '/home/user/day-owt/openwork/v2'
TRACK = os.path.join(HERE, 'lift_track_0075_80.5.json')
FPS = 30000 / 1001
TARGET = 47.0
GAMMA_MAX = 2.4            # beyond this the near-black face is mostly noise
CHROMA_MAX = 4.0
KEY_LO, KEY_HI = 0.08, 0.16
LIFT_END = (82.5, 83.0)
# (time in source s, face box x, y, w, h in 720p px) read off the gridded sheet of the un-lifted shot
ANCHORS = [(80.6, 610, 250, 150, 190), (82.5, 575, 250, 190, 210), (84.0, 680, 215, 200, 160), (85.5, 620, 190, 200, 160)]
SEGS = [(80.5, 81.6), (81.6, 83.3), (83.3, 84.8), (84.8, 86.4)]
IN = 80.5


def frames_of(path):
    import cv2
    cap = cv2.VideoCapture(path); fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(f)
    return fr


def track(src):
    import cv2
    fr = frames_of(src)
    br = [cv2.convertScaleAbs(f, alpha=2.5, beta=10) for f in fr]
    res = {}
    for (t, x, y, w, h), (ta, tb) in zip(ANCHORS, SEGS):
        i0 = round((t - IN) * FPS); ia = max(0, round((ta - IN) * FPS)); ib = min(len(fr) - 1, round((tb - IN) * FPS))
        res[i0] = (x, y, w, h)
        for rng in (range(i0 + 1, ib + 1), range(i0 - 1, ia - 1, -1)):
            tr = cv2.TrackerCSRT_create(); tr.init(br[i0], (x, y, w, h))
            for i in rng:
                ok, b = tr.update(br[i])
                if ok:
                    res[i] = tuple(int(v) for v in b)
    n = len(fr)
    keys = sorted(res)
    boxes = []
    for i in range(n):     # fill any gap by interpolation, then smooth the centre over 5 frames
        if i in res:
            boxes.append(res[i]); continue
        a = max([k for k in keys if k < i], default=keys[0]); b = min([k for k in keys if k > i], default=keys[-1])
        u = 0 if a == b else (i - a) / (b - a)
        boxes.append(tuple(int(res[a][j] + u * (res[b][j] - res[a][j])) for j in range(4)))
    B = np.array(boxes, float)
    k = 5; pad = np.pad(B, ((k // 2, k // 2), (0, 0)), mode='edge')
    B = np.array([pad[i:i + k].mean(0) for i in range(n)])
    json.dump({'fps': FPS, 'in': IN, 'size': [1280, 720], 'boxes': [[round(v, 1) for v in b] for b in B]}, open(TRACK, 'w'))
    tiles = []
    for i in range(0, n, 15):
        f = br[i].copy(); x, y, w, h = (int(v) for v in B[i])
        cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 255), 3)
        cv2.putText(f, f'{IN + i / FPS:.2f}', (20, 60), 0, 1.6, (255, 255, 255), 3)
        tiles.append(cv2.resize(f, (320, 180)))
    while len(tiles) % 4:
        tiles.append(np.zeros_like(tiles[0]))
    sheet = np.vstack([np.hstack(tiles[r:r + 4]) for r in range(0, len(tiles), 4)])
    cv2.imwrite(f'{WORK}/lift_track_check.jpg', sheet)
    print('track', n, 'frames ->', TRACK)


def face_core(Y, b):
    x, y, w, h = b
    x0, y0 = int(x + 0.2 * w), int(y + 0.2 * h); x1, y1 = int(x + 0.8 * w), int(y + 0.8 * h)
    return Y[max(0, y0):y1, max(0, x0):x1]


def to255(Yraw):   # limited-range 16-bit luma -> 0..255 display luma
    return np.clip((Yraw / 256.0 - 16) * 255 / 219, 0, 255)


class Lifter:
    def __init__(self, n_frames, off=0):
        T = json.load(open(TRACK))
        self.off = off            # the shot's first frame is track frame `off` (B2's CH1 starts later, under the J-cut)
        self.B = np.array(T['boxes'])
        self.n = n_frames
        self.W, self.H = T['size']
        yy, xx = np.mgrid[0:self.H, 0:self.W]
        self.xx, self.yy = xx.astype(np.float32), yy.astype(np.float32)
        self.A = None

    def box(self, i):
        return self.B[min(i + self.off, len(self.B) - 1)]

    def mask(self, i):
        x, y, w, h = self.box(i)
        cx, cy = x + w / 2, y + h * 0.55
        rx, ry = w * 0.62, h * 0.70
        d = np.sqrt(((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2)
        return np.clip(np.exp(-np.maximum(0, d - 1) ** 2 / (2 * 0.55 ** 2)), 0, 1)   # 1 inside, gaussian falloff outside

    def weight(self, i, v):
        """where the lift acts: the soft tracked ellipse x a soft luma key (only pixels darker than about 0.08-0.16 of
        the range, judged on a blurred copy), so the lit ceiling and walls around his head are never lifted (no halo)."""
        import cv2
        kv = cv2.GaussianBlur(v, (0, 0), 4)
        key = np.clip((KEY_HI - kv) / (KEY_HI - KEY_LO), 0, 1).astype(np.float32)
        # v4: close the key's holes (brighter skin, eyes, teeth) so the whole face gets one even weight (no blotches),
        # then erode so the soft edge sits INSIDE his silhouette and never reaches the wall (no rim halo)
        key = cv2.morphologyEx(key, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
        key = cv2.erode(key, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        key = cv2.GaussianBlur(key, (0, 0), 5)
        return self.mask(i) * key

    @staticmethod
    def lifted(v, g):
        """a power (gamma) lift of a lightly smoothed luma: it digs into near-black, where a plain gain only scales noise."""
        import cv2
        vs = cv2.GaussianBlur(v, (0, 0), 1.2)
        return np.power(np.maximum(vs, 0), 1.0 / g)

    def blend(self, v, w, g):
        return v + w * (self.lifted(v, g) - v)

    def solve_frame(self, i, v):
        w = self.weight(i, v)
        x, y, bw, bh = self.box(i)
        sl = (slice(max(0, int(y + 0.2 * bh)), int(y + 0.8 * bh)), slice(max(0, int(x + 0.2 * bw)), int(x + 0.8 * bw)))
        cv = v[sl]
        if float(np.median(cv)) * 255 >= TARGET:
            return 1.0
        # solve on the face crop only (with a margin for the blur)
        pad = 8
        sl2 = (slice(max(0, sl[0].start - pad), sl[0].stop + pad), slice(max(0, sl[1].start - pad), sl[1].stop + pad))
        vv, ww = v[sl2], w[sl2]
        inner = (slice(sl[0].start - sl2[0].start, sl[0].stop - sl2[0].start), slice(sl[1].start - sl2[1].start, sl[1].stop - sl2[1].start))
        med = lambda g: float(np.median(self.blend(vv, ww, g)[inner])) * 255
        lo, hi = 1.0, GAMMA_MAX
        if med(hi) < TARGET:
            return hi
        for _ in range(20):
            m = (lo + hi) / 2
            if med(m) < TARGET:
                lo = m
            else:
                hi = m
        return hi

    def solve(self, Ys):
        """per-frame gamma so the face-core median reaches TARGET (0..255), capped at GAMMA_MAX, then a 0.5 s moving average."""
        G = np.array([self.solve_frame(i, self.norm(Y)) for i, Y in enumerate(Ys)])
        k = int(round(0.5 * FPS)) | 1
        pad = np.pad(G, (k // 2, k // 2), mode='edge')
        self.A = np.array([pad[i:i + k].mean() for i in range(len(G))])
        # v5 (nq-check, 8 Oct): lift only up to source LIFT_END[1]; ease the gamma to 1 over LIFT_END, then none, so the
        # tail falls to his natural silhouette (no flat cutout, no wall glow)
        t = IN + (np.arange(len(G)) + self.off) / FPS
        r = np.clip((LIFT_END[1] - t) / (LIFT_END[1] - LIFT_END[0]), 0, 1)
        self.A = 1 + (self.A - 1) * r
        return self.A

    @staticmethod
    def norm(Yraw):
        return np.clip((Yraw.astype(np.float32) / 256.0 - 16) / 219, 0, 1)

    def apply(self, i, f):
        """f = (3, H, W) uint16 yuv444p16le. Chroma is scaled with the luma (capped at 4x), so his skin keeps its colour
        (a luma-only lift turns a dark face grey)."""
        if self.A[i] <= 1.0005:
            return f                     # no lift: the frame passes untouched
        v = self.norm(f[0])
        w = self.weight(i, v)
        out_v = self.blend(v, w, self.A[i])
        gm = np.clip(out_v / np.maximum(v, 0.004), 1, CHROMA_MAX)
        gm = 1 + (gm - 1) * w
        out = np.empty_like(f)
        out[0] = np.clip((out_v * 219 + 16) * 256, 0, 65535).astype(np.uint16)
        for c in (1, 2):
            out[c] = np.clip(32768 + (f[c].astype(np.float32) - 32768) * gm, 0, 65535).astype(np.uint16)
        return out


def lift_pipe(dec_cmd, enc_cmd, n_frames, t_in, W=1280, H=720):
    """decode (yuv444p16le raw on stdout) -> lift -> encode (raw on stdin). Two passes over the decode: measure, apply."""
    fs = W * H * 2 * 3
    raw = subprocess.run(dec_cmd, capture_output=True, check=True).stdout
    nf = min(n_frames, len(raw) // fs)
    frames = [np.frombuffer(raw, '<u2', count=W * H * 3, offset=i * fs).reshape(3, H, W) for i in range(nf)]
    L = Lifter(nf, int(round((t_in - IN) * FPS)))
    A = L.solve([f[0] for f in frames])
    p = subprocess.Popen(enc_cmd, stdin=subprocess.PIPE)
    for i, f in enumerate(frames):
        p.stdin.write(L.apply(i, f).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode:
        raise SystemExit('encode failed')
    return A


def measure(video, t0, step=0.5):
    import cv2
    T = json.load(open(TRACK)); B = T['boxes']
    fr = frames_of(video)
    out = []
    i0 = round(t0 * FPS)
    for k in range(0, len(B), int(round(step * FPS))):
        j = i0 + k
        if j >= len(fr):
            break
        g = cv2.cvtColor(fr[j], cv2.COLOR_BGR2YUV)[:, :, 0].astype(float)
        x, y, w, h = B[k]
        core = g[int(y + 0.2 * h):int(y + 0.8 * h), int(x + 0.2 * w):int(x + 0.8 * w)]
        ring = g[max(0, int(y - 0.6 * h)):int(y - 0.1 * h), int(x):int(x + w)]   # the ceiling just above his cap
        out.append((round(IN + k / FPS, 2), round(float(np.median(core)), 1), round(float(np.median(ring)), 1) if ring.size else None))
    return out


if __name__ == '__main__':
    if sys.argv[1] == 'track':
        track(sys.argv[2] if len(sys.argv) > 2 else f'{WORK}/ch1_nolift.mp4')
    elif sys.argv[1] == 'measure':
        for r in measure(sys.argv[2], float(sys.argv[3])):
            print(*r)
