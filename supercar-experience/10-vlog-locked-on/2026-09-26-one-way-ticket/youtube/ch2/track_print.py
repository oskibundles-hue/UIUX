#!/usr/bin/env python3
"""track_print.py -- the moving blur for the "SUPERCAR EXPERIENCE" print on Omarie's hoodie (personal brand only: the
lead's Ch1/Ch2 briefs overrides test-ch3's "unblurred wardrobe" note). Same OpenCV CSRT tracker as ../test-ch3/track_plate.py.

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
RAW = '/home/user/day-owt/ch2work/raw_shots'
# v2 (2026-10-08 gate check): the v1 boxes stopped above the bottom line of the print ("EXPERIENCE" showed under the
# patch in 0076 92.6-93.4, 113-116 and 0080); measured on a full-res 0076 93.2 frame, the SE logo spans 1.36-1.9
# Hidden-Hills-with-CLUB heights below the script top (about 2.5 script-only anchor heights), so the box now runs to 3.2
# Ch2 (2026-10-08): the anchors are measured on the Ch2 raw gate shots. Three kinds, because the print is seen at very
# different sizes: 'se' tracks the SE print itself where it is large enough (shots 2, 3, 5: 0084 close-ups, the 0085 selfie,
# the 0086 selfie) and the blur box is that box plus a margin; 'chest' tracks the whole front print block (RYFT to HIDDEN HILLS
# CLUB) in the far full-length fit check (shot 4), where the SE patch sits 0.3-0.75 across and 0.2-0.47 down it; 'helm' tracks
# the green helmet on the back of the hoodie (shot 4), where a second, smaller SE logo sits in the row under the helmet
# (0.4-1.1 helmet-widths across, 1.15-1.35 heights down).
REL = {'se': (-0.2, -0.3, 1.4, 1.6), 'chest': (0.25, 0.05, 0.55, 0.55), 'helm': (0.25, 0.95, 1.0, 0.6)}
# anchors per shot (gate shot index from edl.json), measured on the raw gate frames 2026-10-08
ANCHORS = {
    2: [[11.6, 245, 105, 245, 95, 'se'], [11.9, 145, 258, 230, 60, 'se'], [12.3, 360, 318, 220, 42, 'se'], [12.6, 330, 262, 225, 68, 'se']],
    3: [[0.8, 238, 198, 68, 26, 'se'], [1.5, 228, 203, 64, 24, 'se'], [2.0, 260, 233, 68, 30, 'se'], [2.4, 263, 238, 70, 30, 'se'],
        [2.75, 288, 262, 66, 30, 'se']],
    4: [[0.1, 288, 165, 100, 70, 'chest'], [0.8, 268, 128, 95, 75, 'chest'], [1.5, 292, 98, 100, 80, 'chest'],
        [2.6, 285, 105, 70, 75, 'helm'], [3.5, 350, 120, 75, 75, 'helm'], [4.4, 315, 120, 75, 75, 'helm'], [5.2, 335, 120, 60, 70, 'helm'],
        [5.8, 358, 128, 90, 75, 'chest'], [6.5, 295, 135, 100, 75, 'chest'], [7.3, 280, 125, 100, 75, 'chest'], [7.8, 345, 58, 90, 80, 'chest']],
    # 0.55 at the bottom edge; 2.3/2.5 re-measured on the gate (the old 2.5 anchor sat 55 px right of the print)
    5: [[0.55, 356, 336, 42, 22, 'se'], [0.9, 362, 312, 60, 22, 'se'], [1.3, 403, 318, 60, 28, 'se'], [1.8, 398, 342, 55, 18, 'se'],
        [2.3, 448, 309, 44, 22, 'se'], [2.5, 493, 309, 42, 24, 'se']],
}
# track only inside [FROM, UNTIL] (s): shot 2's print enters at 11.45 (before it the camera is on his face and the walls);
# shot 2's leaves the bottom of the frame at 12.82; shot 4's front print leaves the top of the frame at ~8.2 as the window tilts down to the shoes; shot 5's enters at ~0.7
FROM = {2: 11.4, 5: 0.45}
UNTIL = {2: 12.82, 4: 8.2}


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
    for j in [j for j in res if j / fps > UNTIL.get(i, 1e9) or j / fps < FROM.get(i, -1)]:
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
        kind = res[r[0][0]][4] if r[0][0] in res else 'se'
        why = 'SE hoodie print, tracked ' + {'se': 'on the print itself', 'chest': 'on the front print block', 'helm': 'on the back helmet (second SE logo under it)'}[kind]
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
        out, gaps, cov, n = track(i, an, '/home/user/day-owt/ch2work/track_dbg')
        # keep the other blurs (plates) already in look.json; replace only the print runs
        keep = [b for b in look.get(str(i), {}).get('blur', []) if not b.get('why', '').startswith('SE hoodie print')]
        look.setdefault(str(i), {})['blur'] = out + keep
        print(f'shot {i:02d}: {len(out)} run(s), tracked {cov:.0%} of {n} frames, runs ' +
              ', '.join(f"{b['keys'][0][0]}-{b['keys'][-1][0]}" for b in out) + (f'  lost at {gaps}' if gaps else ''))
    json.dump(look, open(lp, 'w'), indent=1)
