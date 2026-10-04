"""Per-frame homography (ref frame -> frame i) for a plate by masked ECC (intensity alignment), chained outward from the
reference frame (each frame starts from its neighbour's estimate). Mask = rigid body regions only (no glare, no hands).
   python3 track30.py c20 60 x0,y0,x1,y1 ...   -> tracks/<key>.json (list of 3x3, ref -> frame)"""
import json, sys, numpy as np, cv2
import os
key, ref = sys.argv[1], int(sys.argv[2]); boxes = [tuple(map(int, b.split(','))) for b in sys.argv[3:]]
PD = os.environ.get("PLATE_DIR", f"plates/{key}/{key}"); N = len([f for f in os.listdir(PD) if f.endswith(".jpg")])
S = 0.5
def load(i):
    g = cv2.cvtColor(cv2.imread(f"{PD}/{i:05d}.jpg"), cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.resize(g, None, fx=S, fy=S, interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(g, (0, 0), 1.2)
fr = [load(i) for i in range(N)]
mask = np.zeros(fr[0].shape, np.uint8)
for x0, y0, x1, y1 in boxes: mask[int(y0 * S):int(y1 * S), int(x0 * S):int(x1 * S)] = 255
Sm = np.diag([S, S, 1.0]); Si = np.linalg.inv(Sm)
H = {ref: np.eye(3)}
crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
for step in (1, -1):
    W = np.eye(3, dtype=np.float32); i = ref + step
    while 0 <= i < N:
        # warp maps template(ref) coords -> input(frame) coords with WARP_INVERSE_MAP semantics: findTransformECC(template, input)
        MOT = os.environ.get("MOTION", "homography")
        try:
            if MOT == "affine":
                W2 = W[:2].copy() if W.shape[0] == 3 else W
                cc, W2 = cv2.findTransformECC(fr[ref], fr[i], W2, cv2.MOTION_AFFINE, crit, mask, 5)
                W = np.vstack([W2, [0, 0, 1]]).astype(np.float32)
            else:
                cc, W = cv2.findTransformECC(fr[ref], fr[i], W, cv2.MOTION_HOMOGRAPHY, crit, mask, 5)
        except cv2.error:
            cc = -1; print(i, "ECC failed: keeping the neighbour's estimate", flush=True)
        H[i] = Si @ W.astype(np.float64) @ Sm
        print(i, "cc %.4f" % cc, flush=True) if i % 10 == 0 else None
        i += step
if os.environ.get("CHAIN"):                          # chained: each frame aligned to its neighbour (mask carried by the track)
    H = {ref: np.eye(3)}
    for step in (1, -1):
        i = ref + step
        while 0 <= i < N:
            j = i - step; Hj = H[j]; Wl = np.eye(3, dtype=np.float32)
            mj = cv2.warpPerspective(mask, (Sm @ Hj @ Si).astype(np.float64), mask.shape[::-1], flags=cv2.INTER_NEAREST)
            try:
                if os.environ.get("MOTION", "homography") == "affine":
                    cc, W2 = cv2.findTransformECC(fr[j], fr[i], np.eye(2, 3, dtype=np.float32), cv2.MOTION_AFFINE, crit, mj, 5)
                    Wl = np.vstack([W2, [0, 0, 1]])
                else:
                    cc, Wl = cv2.findTransformECC(fr[j], fr[i], Wl, cv2.MOTION_HOMOGRAPHY, crit, mj, 5)
            except cv2.error:
                cc = -1
            H[i] = (Si @ Wl.astype(np.float64) @ Sm) @ Hj
            if i % 10 == 0: print("chain", i, "cc %.4f" % cc, flush=True)
            i += step
json.dump([H[i].tolist() for i in range(N)], open(f"tracks/{key}.json", "w"))
