"""Stage 1: graded, retimed plates for one ad -> plates/<ad>/<shot>/NNNNN.jpg + plates/<ad>/srcmap.json

  python3 plates.py mc20 [shot ...]
Decodes only each shot's source range (select by frame number, never -ss), R2 grade at the native 59.94 fps
(temporal denoise sees consecutive frames), retimes with fx.ramp_times (eased speed, 180-degree shutter:
spans longer than one source frame are averaged = motion blur), then the slow push (kb) about the centre.
srcmap.json: per shot, the source frame (float, absolute) behind every output frame, and the push -- kit.html
uses it to put the tracked lock-on boxes on screen.
"""
import json, math, os, subprocess, sys
import numpy as np
import cv2

T = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{T}/lib")
import fx  # noqa: E402
import importlib; _m = importlib.import_module(os.environ.get("ADS_MOD", "ads")); ADS, OFPS, timeline = _m.ADS, _m.OFPS, _m.timeline  # noqa: E402

V = os.path.expanduser("~/.local/vlogtools")
FF = f"{V}/bin/ffmpeg"
SFPS = 60000 / 1001
GRADE = f"lut3d={V}/gR2.cube,hqdn3d=2:1.5:3:3,unsharp=5:5:0.45:5:5:0,unsharp=13:13:0.3:13:13:0"
W, H = 1080, 1920


def decode(path, a, b):
    vf = f"select='between(n\\,{a}\\,{b})',{GRADE}"
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-vf", vf, "-vsync", "0", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    assert len(fr) == b - a + 1, (path, a, b, len(fr))
    return fr


def push(img, s):
    if abs(s - 1) < 1e-4:
        return img
    M = np.float32([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def zoom_to(img, cx, cy, tx, ty, s):
    M = np.float32([[s, 0, tx - s * cx], [0, s, ty - s * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def build_shot(ad, s, out_dir):
    keys = s.get("keys") or [(0, s.get("speed", 1.0)), (1, s.get("speed", 1.0))]
    times = fx.ramp_times(s["a"], s["n"], keys, shutter=0.5, fps=OFPS)
    xs = [(t * SFPS, span * SFPS) for t, span in times]
    lo = max(0, int(math.floor(min(x - sp / 2 for x, sp in xs))) - 1)
    hi = int(math.ceil(max(x + sp / 2 for x, sp in xs))) + 1
    src = decode(f"{T}/{ad['src']}/{s['clip']}", lo, hi)
    hi = lo + len(src) - 1
    os.makedirs(out_dir, exist_ok=True)
    kb = s.get("kb", (1.0, 1.0))
    smap = []
    for i, (x, sp) in enumerate(xs):
        nsub = max(1, int(round(sp)))
        acc = np.zeros((H, W, 3), np.float32)
        for j in range(nsub):
            xx = x - sp / 2 + sp * (j + 0.5) / nsub if nsub > 1 else x
            k = min(max(xx - lo, 0), hi - lo)
            i0 = int(math.floor(k)); fr = k - i0
            f0 = src[i0].astype(np.float32)
            if fr > 1e-3 and i0 + 1 <= hi - lo:
                f0 = f0 * (1 - fr) + src[i0 + 1].astype(np.float32) * fr
            acc += f0
        img = acc / nsub
        u = fx.smootherstep(i / max(s["n"] - 1, 1))
        sc = kb[0] + (kb[1] - kb[0]) * u
        if s.get("zoom"):
            cx, cy, tx, ty, z0, z1 = s["zoom"]
            img = zoom_to(img, cx, cy, tx, ty, z0 + (z1 - z0) * u)
        img = push(img, sc)
        cv2.imwrite(f"{out_dir}/{i:05d}.jpg", np.clip(img + 0.5, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
        smap.append([round(x, 3), round(sc, 5)])
    return smap


def main():
    key = sys.argv[1]
    only = set(sys.argv[2:])
    ad = ADS[key]
    shots, nf = timeline(ad)
    root = f"{T}/plates/{key}"
    os.makedirs(root, exist_ok=True)
    mp = f"{root}/srcmap.json"
    smap = json.load(open(mp)) if os.path.exists(mp) else {}
    for s in shots:
        if not s["clip"] or (only and s["id"] not in only):
            continue
        smap[s["id"]] = build_shot(ad, s, f"{root}/{s['id']}")
        print(key, s["id"], s["clip"], s["n"], "frames", flush=True)
    json.dump(smap, open(mp, "w"))
    print("total", nf, "frames", round(nf / OFPS, 3), "s")


if __name__ == "__main__":
    main()
