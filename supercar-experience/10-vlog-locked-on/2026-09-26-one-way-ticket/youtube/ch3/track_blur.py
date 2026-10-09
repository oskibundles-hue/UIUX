#!/usr/bin/env python3
"""track_blur.py -- Chapter 4's moving blurs, found automatically on the 640x360 raw gate shots (WORK/raw_shots/sNN.mp4:
graded and cropped as they render, no blur) and written into look.json as render.py 'round' blur keys (fractions).

Ch4 is mostly driving from a camera behind his left shoulder that shakes and swings with the car, so the dash moves a lot
inside every shot. Hand-keyed boxes (test-ch3's cluster patch) would miss; this tracks them on every frame instead:

  * 'tft' and 'cluster' (every rear-camera shot): multi-scale template match (OpenCV TM_CCOEFF_NORMED on the grey frame,
    scales 0.75-1.3) of two templates cut from a reference frame (s07 at 1.05 s: the centre TFT with its bezel, and the
    driver's cluster seen through the wheel). The cluster is searched only near where the TFT match puts it (the two sit
    on one dash), at the same scale. Boxes are padded (TFT 30 %, cluster 60 %: the wheel rim crosses it) and a frame
    whose match score is low holds the last good box. Every speed/gear readout and the TFT (nav, media) are covered.
  * 'print' (the 0093 side-camera shots): the "SUPERCAR EXPERIENCE" print sits on his left chest between the HR logo and
    the "22", mostly under the seat belt from this side. It is too small to track, so the anchor is the green sleeve
    badge beside it (the only saturated green blob on his torso; found by colour, HSV, inside the torso window), and the
    blur box sits up and to the left of it, generous (REL below), covering the belt, the "Hidden Hills" script, the SE
    print and "BASED".
Keys every 0.1 s, box size the largest over the run (render.py), so a run never shrinks.
    PYTHONPATH=/home/user/day-owt/pycv python3 track_blur.py      # -> look.json (keeps cy and any other blur entries)
"""
import cv2, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = '/home/user/day-owt/ch4work/raw_shots'
DBG = '/home/user/day-owt/ch4work/track_dbg'
# reference frames for the dash templates: (shot, time, TFT box, cluster box), x, y, w, h in the 640x360 frame. The
# 0100 camera sits elsewhere (lower, more behind him), so its shots get their own templates.
REFS = {'a': (7, 1.05, (328, 226, 46, 80), (236, 200, 66, 28)),
        'b': (18, 1.5, (354, 220, 48, 80), (262, 198, 72, 30))}
REAR = {i: 'a' for i in range(3, 15)} | {18: 'b', 19: 'b'}   # rear-camera shots; 2 and 15-17 (scenery crop) show no TFT
                                                              # or cluster (the dash is below the frame), so none there
SIDE = [0, 1]                           # 0093 side camera
REL = (-1.9, -1.6, 2.4, 2.4)            # print box from the badge box (x, y offsets and w, h, in badge sizes)
PAD = {'tft': 0.40, 'cluster': 0.60}


def frames(i):
    cap = cv2.VideoCapture(f'{RAW}/s{i:02d}.mp4'); fps = cap.get(cv2.CAP_PROP_FPS); out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(f)
    return out, fps


def best(gray, tpl, scales, region=None):
    bs = (-1, None, None)
    x0, y0 = 0, 0
    if region:
        x0, y0, x1, y1 = [int(v) for v in region]
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(gray.shape[1], x1), min(gray.shape[0], y1)
        gray = gray[y0:y1, x0:x1]
    for s in scales:
        t = cv2.resize(tpl, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        if t.shape[0] >= gray.shape[0] or t.shape[1] >= gray.shape[1]:
            continue
        r = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
        _, v, _, loc = cv2.minMaxLoc(r)
        if v > bs[0]:
            bs = (v, (loc[0] + x0, loc[1] + y0, t.shape[1], t.shape[0]), s)
    return bs


def pad(b, p):
    x, y, w, h = b
    return (x - w * p, y - h * p, w * (1 + 2 * p), h * (1 + 2 * p))


def keys_of(boxes, fps, W=640, H=360):
    # every 3rd frame, or wider on long shots so a run never passes 90 keys: render.py nests one if() per key and
    # ffmpeg's expression parser stops near 100 levels (s01's 129 keys failed the crop, 2026-10-08)
    ks = []
    n = len(boxes); step = max(3, -(-n // 90))
    for k, b in enumerate(boxes):
        if k % step and k != n - 1:
            continue
        x, y, w, h = b
        ks.append([round(k / fps, 3), round(x / W, 4), round(y / H, 4), round(w / W, 4), round(h / H, 4)])
    return ks


def main():
    os.makedirs(DBG, exist_ok=True)
    look = json.load(open(os.path.join(HERE, 'look.json')))
    tpl = {}
    for key, (ri, rt, T_TFT, T_CLU) in REFS.items():
        rf, _ = frames(ri); ref = cv2.cvtColor(rf[round(rt * 29.97)], cv2.COLOR_BGR2GRAY)
        tpl[key] = (ref[T_TFT[1]:T_TFT[1] + T_TFT[3], T_TFT[0]:T_TFT[0] + T_TFT[2]],
                    ref[T_CLU[1]:T_CLU[1] + T_CLU[3], T_CLU[0]:T_CLU[0] + T_CLU[2]],
                    (T_CLU[0] - T_TFT[0], T_CLU[1] - T_TFT[1]), T_CLU)
    report = []
    for i in list(REAR) + SIDE:
        fr, fps = frames(i)
        lk = look.setdefault(str(i), {})
        lk['blur'] = [b for b in lk.get('blur', []) if b.get('auto') not in ('tft', 'cluster', 'print')]   # keeps the CSRT plate entries
        if i in REAR:
            tt, tc, off, T_CLU = tpl[REAR[i]]
            G = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
            # seed: the best full-frame match over every 5th frame; then follow it frame by frame both ways inside a
            # +-50 px window at the seed scale (the camera is fixed to the car, so the dash never changes size; a drifting
            # scale shrank s19's boxes, 2026-10-08), so a passing car or the mirror cannot steal the match (s18 frame 0 did)
            seeds = [(best(G[k], tt, np.arange(0.75, 1.31, 0.05), (0, 100, 640, 360)), k) for k in range(0, len(G), 5)]
            (v0, b0, s0), k0 = max(seeds, key=lambda q: q[0][0])
            res = {k0: (v0, b0, s0)}
            for rng in (range(k0 + 1, len(G)), range(k0 - 1, -1, -1)):
                lb, ls = b0, s0
                for k in rng:
                    v, b, s = best(G[k], tt, [s0 * 0.97, s0, s0 * 1.03], (lb[0] - 50, lb[1] - 50, lb[0] + lb[2] + 50, lb[1] + lb[3] + 50))
                    if b is None or v < 0.35:
                        v, b, s = -1, lb, ls
                    res[k] = (v, b, s); lb, ls = b, s
            tft, clu, st, sc, lastc = [], [], [], [], None
            for k, g in enumerate(G):
                v, b, s = res[k]
                ex, ey = b[0] + off[0] * s, b[1] + off[1] * s
                vc, bc, _ = best(g, tc, [s * 0.9, s, s * 1.1], (ex - 45 * s, ey - 30 * s, ex + 45 * s + T_CLU[2] * s, ey + 30 * s + T_CLU[3] * s))
                if bc is None or vc < 0.25:
                    bc = lastc if lastc else (ex, ey, T_CLU[2] * s, T_CLU[3] * s)
                lastc = bc
                tft.append(pad(b, PAD['tft'])); clu.append(pad(bc, PAD['cluster'])); st.append(v); sc.append(vc)
            lk['blur'] += [dict(shape='round', auto='tft', why='centre TFT (nav/media), template-tracked', keys=keys_of(tft, fps)),
                           dict(shape='round', auto='cluster', why='driver cluster (speed/gear), template-tracked', keys=keys_of(clu, fps))]
            report.append(f's{i:02d}: TFT score min {min(st):.2f} median {np.median(st):.2f}; cluster min {min(sc):.2f} median {np.median(sc):.2f}')
            dbg = [(tft, (0, 255, 255)), (clu, (255, 0, 255))]
        else:
            boxes, last, miss = [], None, 0
            for f in fr:
                hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
                m = cv2.inRange(hsv, (40, 90, 60), (85, 255, 255))
                m[:180, :] = 0; m[290:, :] = 0; m[:, :250] = 0; m[:, 430:] = 0
                n, lab, stats, cen = cv2.connectedComponentsWithStats(m)
                cand = [stats[k] for k in range(1, n) if 25 <= stats[k][4] <= 900]
                if cand:
                    x, y, w, h, a = max(cand, key=lambda q: q[4])
                    w, h = max(w, 16), max(h, 16)
                    last = (x + REL[0] * w, y + REL[1] * h, REL[2] * w + w, REL[3] * h)
                else:
                    miss += 1
                boxes.append(last)
            first = next(b for b in boxes if b)
            boxes = [b if b else first for b in boxes]
            lk['blur'] += [dict(shape='round', auto='print', why='SE hoodie print (left chest, under the belt), anchored on the green sleeve badge', keys=keys_of(boxes, fps))]
            report.append(f's{i:02d}: badge found on {len(fr) - miss}/{len(fr)} frames')
            dbg = [(boxes, (0, 255, 255))]
        for k in range(0, len(fr), 15):
            f = fr[k].copy()
            for bx, col in dbg:
                x, y, w, h = [int(v) for v in bx[k]]
                cv2.rectangle(f, (x, y), (x + w, y + h), col, 2)
            cv2.imwrite(f'{DBG}/s{i:02d}_{k:04d}.jpg', f)
    json.dump(look, open(os.path.join(HERE, 'look.json'), 'w'), indent=1)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
