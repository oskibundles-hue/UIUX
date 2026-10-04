"""Locked-On ABC lock-on tracks. Template tracks (lib/track.py) are run on plate sequences re-encoded to mp4 in
.work/L/trk (s27 fists, s32 hand, s38 blade hand, r29 trident). This script adds the s37 microfibre by colour (the
cloth deforms, so a template drifts; its yellow is unique in the frame) and writes tracks/locks.json (plate frame -> box).
   python3 lo_track.py"""
import json, os, cv2, numpy as np
T = os.path.dirname(os.path.abspath(__file__))
db = json.load(open(f"{T}/.work/L/trk/locks.json"))
out = {}
for k, v in db.items():
    out[k] = {"f0": v["f0"], "frames": [[f["x"], f["y"], f["w"], f["h"], f["conf"]] for f in v["frames"]]}
# s37: yellow cloth centroid, fixed-size box, zero-phase smoothing
cs, ws = [], []
for k in range(32, 88):
    im = cv2.imread(f"{T}/plates/F_s37/s37/{k:05d}.jpg")
    hsv = cv2.cvtColor(cv2.resize(im, (540, 960)), cv2.COLOR_BGR2HSV)
    m = (hsv[..., 0] >= 18) & (hsv[..., 0] <= 34) & (hsv[..., 1] > 110) & (hsv[..., 2] > 110)
    ys, xs = np.nonzero(m)
    cs.append([xs.mean() * 2, ys.mean() * 2]); ws.append(len(xs))
cs = np.array(cs); n = len(cs)
sm = np.array([cs[max(0, i - 4):i + 5].mean(0) for i in range(n)])
W, H = 300, 220
out["s37"] = {"f0": 32, "frames": [[round(float(x - W / 2), 2), round(float(y - H / 2), 2), W, H, round(min(1.0, w / 2000), 3)] for (x, y), w in zip(sm, ws)]}
json.dump(out, open(f"{T}/tracks/locks.json", "w"))
for k, v in out.items():
    c = [f[4] for f in v["frames"]]
    print(k, "frames", v["f0"], "-", v["f0"] + len(c) - 1, "conf min %.2f" % min(c))
