#!/usr/bin/env python3
"""Paint out small marks on the skin (a patch, a speck) across the whole base, before the looks.

    python3 retouch.py --spec spec_sep03.json --work work

Runs after `build_looks.py base` and before `looks`. Each entry in the spec's "retouch" list
gives one mark: the time it is seeded at and its centre there, in pixels of the base's size.

The base is a row of jump cuts (one per keep range), so a mark is tracked one cut at a time and
nothing is carried across a cut. In every frame the face's five YuNet landmarks, mapped from the
seed frame by an affine fit, predict where the mark should be. Within each cut, the frame whose
saturation best matches the mark's own patch near that prediction anchors the track; the track
then runs frame to frame from there with a small search, and a match is refused if it jumps, or
strays from the face's prediction (that is how the first version ended up on the nose and an eye).
A grey patch on skin stands out by saturation, not brightness, because the ceiling lights make the
brightest spots on the face. The mask is the pixels inside a disc at the match that are as grey
and as dark as the mark itself (eye whites are brighter, brow hair darker), filled with OpenCV's
Telea inpainting. A short gap inside a cut is filled from its neighbours in that cut; any other
miss is left untouched and listed.

The untouched base is kept as base_src.mp4 (re-running starts from it), and the track goes to
retouch.json for the check pass.
"""
import argparse, json, math, os, shutil, subprocess, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
RADIUS, GROW, INPAINT = 24, 5, 9   # px at 2160 wide: mask disc, mask growth, inpaint radius
ANCHOR_R, STEP_R = 80, 30          # search radius around the face's prediction / the last match
MAX_JUMP, LEASH = 40, 90           # refuse a match this far from the last one / from the prediction
MIN_SCORE, MAX_GAP = 0.45, 3       # template score to accept; longest gap filled from neighbours
SURE, SURE_LEASH = 0.8, 150        # a match this good may stray further from the landmark prediction
HOLD = 2                           # frames at a cut's edge that keep the nearest tracked position


def decode(path, W, H):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    while len(b := p.stdout.read(W * H * 3)) == W * H * 3:
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()


def cuts(spec, n):
    """First frame of each keep range in the base (the fps filter rounds each one up), plus n."""
    starts, i = [], 0
    for s, e in spec["keep"]:
        starts.append(i)
        i += math.ceil(round((e - s) * FPS, 6))
    if i != n:
        sys.exit(f"keep ranges give {i} frames, base has {n}: rebuild base")
    return starts + [n]


def match(sat, tmpl, at, r):
    """Best template match within r of at, as (score, centre)."""
    h, w = tmpl.shape
    x0, y0 = max(int(at[0]) - r - w // 2, 0), max(int(at[1]) - r - h // 2, 0)
    x1, y1 = min(int(at[0]) + r + w // 2, sat.shape[1]), min(int(at[1]) + r + h // 2, sat.shape[0])
    if x1 - x0 < w or y1 - y0 < h:
        return -1.0, np.array(at, float)
    res = cv2.matchTemplate(sat[y0:y1, x0:x1], tmpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    return score, np.array([x0 + loc[0] + w / 2, y0 + loc[1] + h / 2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--work", required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    marks = spec.get("retouch", [])
    if not marks:
        sys.exit("spec has no retouch entries")
    tl = json.load(open(os.path.join(a.work, "timeline.json")))
    W, H = tl["size"]
    base, src = os.path.join(a.work, "base.mp4"), os.path.join(a.work, "base_src.mp4")
    if not os.path.exists(src):
        shutil.copy(base, src)

    # one pass: saturation and value on a band of rows around the marks (all 4K frames at once
    # would be ~8.6 GB), and the face's landmarks at half size
    ys = [m["xy"][1] for m in marks]
    b0, b1 = max(min(ys) - 500, 0), min(max(ys) + 500, H)
    det = cv2.FaceDetectorYN.create(os.path.join(HERE, "face_detection_yunet_2023mar.onnx"), "",
                                    (W // 2, H // 2), 0.5)
    sats, vals, lms = [], [], []
    for f in decode(src, W, H):
        hsv = cv2.cvtColor(f[b0:b1], cv2.COLOR_BGR2HSV)
        sats.append(hsv[..., 1].copy())
        vals.append(hsv[..., 2].copy())
        _, faces = det.detect(cv2.resize(f, (W // 2, H // 2)))
        lms.append(None if faces is None else max(faces, key=lambda r: r[2] * r[3])[4:14].reshape(5, 2) * 2)
    n = len(sats)
    bounds = cuts(spec, n)
    yy, xx = np.ogrid[:b1 - b0, :W]

    log = []
    masks = [np.zeros((b1 - b0, W), np.uint8) for _ in range(n)]
    for m in marks:
        i0 = round(m["t"] * FPS)
        if lms[i0] is None:
            sys.exit(f"{m['name']}: no face on the seed frame {i0}")
        cx, cy = m["xy"][0], m["xy"][1] - b0
        tmpl = sats[i0][cy - RADIUS:cy + RADIUS, cx - RADIUS:cx + RADIUS].copy()
        # thresholds from the mark itself: its saturation against the skin in a ring around it, its value
        dist = np.hypot(xx - cx, yy - cy)
        s_mark, s_skin = np.median(sats[i0][dist < 8]), np.median(sats[i0][(dist > 40) & (dist < 60)])
        sat_max = int(s_mark + 0.4 * (s_skin - s_mark))
        v_mark = float(np.median(vals[i0][dist < 8]))
        v_lo, v_hi = int(v_mark * 0.6), int(v_mark * 1.4)

        pred = {}
        for i in range(n):
            if lms[i] is not None:
                A = cv2.estimateAffine2D(lms[i0], lms[i])[0]
                if A is not None:
                    pred[i] = A @ np.array([*m["xy"], 1.0]) - (0, b0)

        def ok(i, score, c, last):
            leash = SURE_LEASH if score >= SURE else LEASH
            return (score >= MIN_SCORE and (last is None or np.hypot(*(c - last)) <= MAX_JUMP)
                    and (i not in pred or np.hypot(*(c - pred[i])) <= leash))

        xy, lost, scores = {}, [], {}
        for c0, c1 in zip(bounds, bounds[1:]):
            # anchor: the frame in this cut that best matches near the face's prediction
            cands = [(match(sats[i], tmpl, pred[i], ANCHOR_R), i) for i in range(c0, c1) if i in pred]
            cands = [((s, c), i) for (s, c), i in cands if ok(i, s, c, None)]
            if not cands:
                lost += list(range(c0, c1))
                continue
            (_, c), ia = max(cands, key=lambda t: t[0][0])
            xy[ia] = c
            for order in (range(ia + 1, c1), range(ia - 1, c0 - 1, -1)):
                last = c
                for i in order:
                    score, ci = match(sats[i], tmpl, last, STEP_R)
                    if not ok(i, score, ci, last) and i in pred:
                        # a fast head move outruns the small search: look again around the face's
                        # prediction, still refusing anything far from it
                        score, ci = match(sats[i], tmpl, pred[i], ANCHOR_R)
                        if not ok(i, score, ci, None):
                            scores[i] = round(float(score), 2)
                            continue
                    elif not ok(i, score, ci, last):
                        scores[i] = round(float(score), 2)
                        continue
                    xy[i] = last = ci
            # a short gap between two tracked frames in this cut is interpolated
            for i in range(c0, c1):
                if i in xy:
                    continue
                lo = max((j for j in xy if c0 <= j < i), default=None)
                hi = min((j for j in xy if i < j < c1), default=None)
                if lo is not None and hi is not None and hi - lo - 1 <= MAX_GAP:
                    xy[i] = xy[lo] + (xy[hi] - xy[lo]) * (i - lo) / (hi - lo)
                elif (lo is None) != (hi is None) and min(abs(i - (lo if hi is None else hi)), 99) <= HOLD:
                    xy[i] = xy[lo if hi is None else hi]
                else:
                    lost.append(i)

        for i, c in xy.items():
            inside = (xx - c[0]) ** 2 + (yy - c[1]) ** 2 < RADIUS ** 2
            masks[i] |= (inside & (sats[i] < sat_max) & (vals[i] > v_lo) & (vals[i] < v_hi)).astype(np.uint8) * 255
        area = int((masks[i0] > 0).sum())
        log.append({"name": m["name"], "seed": m["xy"], "cuts": bounds, "area_px": area,
                    "sat_max": sat_max, "v_range": [v_lo, v_hi], "tracked": len(xy), "lost": sorted(lost),
                    "lost_scores": {str(i): scores.get(i) for i in sorted(lost)},
                    "xy": {str(i): [round(float(c[0])), round(float(c[1])) + b0] for i, c in sorted(xy.items())}})
        print(f"{m['name']}: {len(xy)}/{n} frames, cuts at {bounds[1:-1]}, area on the seed frame {area} px, "
              f"sat<{sat_max}, value {v_lo}-{v_hi}, lost {sorted(lost)[:12]}{' ...' if len(lost) > 12 else ''}")
    del sats, vals

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * GROW + 1, 2 * GROW + 1))
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "12",
                            "-preset", "medium", "-pix_fmt", "yuv420p", "-colorspace", "bt709",
                            "-color_primaries", "bt709", "-color_trc", "bt709", base], stdin=subprocess.PIPE)
    for f, mk in zip(decode(src, W, H), masks):
        if mk.any():
            ys, xs = np.nonzero(mk)
            y0, y1 = max(ys.min() - 40, 0), min(ys.max() + 40, mk.shape[0])
            x0, x1 = max(xs.min() - 40, 0), min(xs.max() + 40, W)
            f = f.copy()
            f[b0 + y0:b0 + y1, x0:x1] = cv2.inpaint(f[b0 + y0:b0 + y1, x0:x1], cv2.dilate(mk[y0:y1, x0:x1], k),
                                                    INPAINT, cv2.INPAINT_TELEA)
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    if enc.wait():
        sys.exit("encode failed")
    json.dump(log, open(os.path.join(a.work, "retouch.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
