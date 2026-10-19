#!/usr/bin/env python3
"""track_print.py -- the moving blur for the "SUPERCAR EXPERIENCE" print on Omarie's hoodie (personal brand only: the
lead's Ch1 brief overrides test-ch3's "unblurred wardrobe" note). Same OpenCV CSRT tracker as ../test-ch3/track_plate.py.

The SE print is a small patch directly under the "Hidden Hills" script on the right chest, too small and low-contrast to
track by itself, so the tracker follows an ANCHOR (the "Hidden Hills" script, kind 'hh', or the pink "HR" logo in the
dark 0076 kerb shot, kind 'hr') and the blur box is set relative to it (REL, measured on the gate frames: the patch sits
0.0-0.4 anchor-widths right of the script's left edge and 1.0-1.4 heights below its top). Boxes are generous because
the blur uses render.py's feathered 'round' shape.

Each anchor [t, x, y, w, h, kind] is a box in the 640x360 raw gate shot (WORK/raw_shots/sNN.mp4, graded and cropped,
no blur); it is tracked forward to the midpoint before the next anchor and back to the midpoint after the previous one.
Where CSRT loses the anchor, the run stops and the gap is printed; every gap is checked on the gate sheets.
Output: look.json blur entries {"shape": "round", "keys": [[t, x, y, w, h], ...]} (fractions of the frame), one per
contiguous tracked run.
    PYTHONPATH=/home/user/day-owt/pycv python3 track_print.py   # -> updates look.json
(CSRT lives in opencv-contrib; the installed opencv-python-headless 5.0 lacks it, so contrib is installed beside it:
    pip install --target /home/user/day-owt/pycv opencv-contrib-python-headless)
"""
import cv2, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = '/home/user/day-owt/ch1work/raw_shots'
# v2 (2026-10-08 gate check): the v1 boxes stopped above the bottom line of the print ("EXPERIENCE" showed under the
# patch in 0076 92.6-93.4, 113-116 and 0080); measured on a full-res 0076 93.2 frame, the SE logo spans 1.36-1.9
# Hidden-Hills-with-CLUB heights below the script top (about 2.5 script-only anchor heights), so the box now runs to 3.2
REL = {'hh': (-0.6, 0.5, 2.7, 2.7), 'hr': (0.7, -1.1, 1.9, 2.9)}
# anchors per shot (gate shot index from edl.json), measured on gate frames 2026-10-08
ANCHORS = {
    1: [[0.2, 291, 284, 87, 36, 'hr'], [0.5, 284, 287, 58, 29, 'hr'], [1.1, 298, 262, 66, 36, 'hr'], [1.7, 349, 287, 87, 37, 'hr'],
        [4.4, 318, 288, 35, 40, 'hh'], [8.9, 365, 270, 45, 30, 'hh']],
    3: [[2.06, 310, 307, 65, 33, 'hh']],
    4: [[0.96, 285, 300, 50, 27, 'hh'], [6.96, 287, 300, 40, 30, 'hh'], [9.96, 315, 307, 45, 23, 'hh']],
    5: [[1.26, 320, 305, 40, 25, 'hh']],
    6: [[0.56, 330, 300, 60, 32, 'hh'], [2.66, 360, 325, 52, 30, 'hh']],
    7: [[0.45, 247, 323, 62, 36, 'hh'], [0.75, 291, 323, 62, 36, 'hh'], [1.2, 276, 320, 80, 36, 'hh'], [1.8, 258, 320, 77, 36, 'hh']],
    9: [[0.0, 356, 309, 51, 47, 'hh'], [1.1, 310, 300, 32, 30, 'hh']],
    10: [[3.0, 290, 292, 62, 33, 'hh'], [4.2, 290, 295, 60, 30, 'hh']],
}
# stop tracking here (s): from 4.4 s the bagel covers the patch and CSRT drifts onto the bagel
UNTIL = {10: 4.35}


def frames_of(path):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS); fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(f)
    return fr, fps


def track(i, anchors, dbg):
    fr, fps = frames_of(f'{RAW}/s{i:02d}.mp4')
    H, W = fr[0].shape[:2]
    n = len(fr)
    idx = [round(a[0] * fps) for a in anchors]
    res = {}
    gaps = []
    for k, (t, x, y, w, h, kind) in enumerate(anchors):
        i0 = idx[k]
        lo = 0 if k == 0 else (idx[k - 1] + i0) // 2 + 1
        hi = n - 1 if k == len(anchors) - 1 else (i0 + idx[k + 1]) // 2
        res[i0] = (x, y, w, h, kind)
        for rng in (range(i0 + 1, hi + 1), range(i0 - 1, lo - 1, -1)):
            tr = cv2.TrackerCSRT_create(); tr.init(fr[i0], (x, y, w, h))
            for j in rng:
                ok, b = tr.update(fr[j])
                if not ok:
                    gaps.append((round(j / fps, 2), 'lost'))
                    break
                res[j] = (*[int(v) for v in b], kind)
    if i in UNTIL:
        for j in [j for j in res if j / fps > UNTIL[i]]:
            res.pop(j)
    # blur box per tracked frame
    bl = {}
    for j, (x, y, w, h, kind) in res.items():
        dx, dy, rw, rh = REL[kind]
        bl[j] = (x + dx * w, y + dy * h, rw * w, rh * h)
    # bridge short tracking losses (<= 1.1 s) by interpolating the blur box, because the print can
    # still show in a dark or blurred frame the tracker dropped (s01 2.37-3.34 at the night kerb)
    ks = sorted(bl)
    for a, b in zip(ks, ks[1:]):
        if 1 < b - a <= round(1.1 * fps):
            for j in range(a + 1, b):
                u = (j - a) / (b - a)
                bl[j] = tuple(bl[a][k] + u * (bl[b][k] - bl[a][k]) for k in range(4))
    # split into contiguous runs
    runs, cur = [], []
    for j in range(n):
        if j in bl:
            cur.append((j, *bl[j]))
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    out = []
    for r in runs:
        keys = [[round(j / fps, 3), round(bx / W, 4), round(by / H, 4), round(bw / W, 4), round(bh / H, 4)]
                for (j, bx, by, bw, bh) in r if j % 3 == 0 or j in (r[0][0], r[-1][0])]
        why = 'SE hoodie print, tracked from the ' + ('Hidden Hills script' if r[0][0] in res and res[r[0][0]][4] == 'hh' else 'HR logo')
        # at most 40 keys per entry (sharing the boundary key), because render.py turns the keys into
        # nested if() expressions and ffmpeg's expression parser fails past about 100 levels
        for c in range(0, max(len(keys) - 1, 1), 39):
            out.append(dict(shape='round', why=why, keys=keys[c:c + 40]))
    # debug sheet frames
    os.makedirs(dbg, exist_ok=True)
    for j in range(0, n, 9):
        f = fr[j].copy()
        if j in res:
            x, y, w, h, kind = res[j]; dx, dy, rw, rh = REL[kind]
            cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 0), 1)
            cv2.rectangle(f, (int(x + dx * w), int(y + dy * h)), (int(x + dx * w + rw * w), int(y + dy * h + rh * h)), (0, 255, 255), 2)
        cv2.putText(f, f's{i:02d} {j / fps:.2f}', (8, 24), 0, 0.7, (255, 255, 255), 2)
        cv2.imwrite(f'{dbg}/s{i:02d}_{j:04d}.jpg', f)
    covered = len(res) / n
    return out, gaps, covered, n


if __name__ == '__main__':
    lp = os.path.join(HERE, 'look.json')
    look = json.load(open(lp)) if os.path.exists(lp) else {}
    for i, an in ANCHORS.items():
        out, gaps, cov, n = track(i, an, '/home/user/day-owt/ch1work/track_dbg')
        look.setdefault(str(i), {})['blur'] = out
        print(f'shot {i:02d}: {len(out)} run(s), tracked {cov:.0%} of {n} frames, runs ' +
              ', '.join(f"{b['keys'][0][0]}-{b['keys'][-1][0]}" for b in out) + (f'  lost at {gaps}' if gaps else ''))
    json.dump(look, open(lp, 'w'), indent=1)
