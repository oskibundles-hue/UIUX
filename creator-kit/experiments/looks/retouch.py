#!/usr/bin/env python3
"""Paint out small marks on the skin (a patch, a speck) across the whole base, before the looks.

    python3 retouch.py --spec spec_sep03.json --work work

Runs after `build_looks.py base` and before `looks`. Each entry in the spec's "retouch" list
gives one mark: the time it is seeded at and its centre there, in pixels of the base's size.

The base is a row of jump cuts (one per keep range), so a mark is tracked one cut at a time and
nothing is carried across a cut. In each cut the frame whose saturation best matches the mark's
own patch, near where the face's five YuNet landmarks put it, anchors the track. From there the
track follows the skin around the mark frame to frame with pyramidal Lucas-Kanade optical flow
(the brows and skin texture move with the mark, and flow keeps up with a fast head turn where a
template search did not), and snaps to the mark's template when it is within a few pixels.
A grey patch on skin stands out by saturation, not brightness, because the ceiling lights make the
brightest spots on the face.

A frame is painted only when it shows his face at close to the seed frame's size with the track
inside it, and skin around the track: a wide shot, or the can held up over his brow, is left alone.
The mask is the pixels inside a disc at the track that are as grey and as dark as the mark itself
(eye whites are brighter, brow hair darker), filled with OpenCV's Telea inpainting, so a frame
where the mark is hidden gets little or no paint.

The untouched base is kept as base_src.mp4 (re-running starts from it), and the track goes to
retouch.json for the check pass.
"""
import argparse, json, math, os, shutil, subprocess, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
RADIUS, GROW, INPAINT = 24, 5, 9   # px at 2160 wide: mask disc, mask growth, inpaint radius
ANCHOR_R, LEASH = 80, 90           # anchor search around the face's prediction, and how far it may stray
SNAP, SNAP_SCORE = 12, 0.6         # template snap radius after each flow step, and the score it needs
FLOW_R, FB_ERR = 180, 1.0          # skin around the mark that flow follows; forward-back error, half px
MIN_FACE = 0.2                     # a face smaller than this share of the seed's is a wide shot
SURE = 0.8                         # a snap this good outranks the landmarks, which wander on close-ups


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


def flow(g0, g1, at):
    """Move at (full-res band px) from half-res grey frame g0 to g1 by the median LK motion of the
    skin around it, or None if too few points survive the forward-back check."""
    mask = np.zeros_like(g0)
    cv2.circle(mask, (int(at[0] / 2), int(at[1] / 2)), FLOW_R // 2, 255, -1)
    p0 = cv2.goodFeaturesToTrack(g0, 80, 0.01, 4, mask=mask)
    if p0 is None or len(p0) < 6:
        return None
    lk = dict(winSize=(21, 21), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, **lk)
    pb, st2, _ = cv2.calcOpticalFlowPyrLK(g1, g0, p1, None, **lk)
    good = (st[:, 0] == 1) & (st2[:, 0] == 1) & (np.linalg.norm((pb - p0)[:, 0], axis=1) < FB_ERR)
    if good.sum() < 6:
        return None
    return at + 2 * np.median((p1 - p0)[good, 0], axis=0)


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

    # one pass: hue, saturation and value on a band of rows around the marks (all 4K frames at
    # once would be ~8.6 GB), grey at half size for the flow, and the face at half size
    ys = [m["xy"][1] for m in marks]
    b0, b1 = max(min(ys) - 500, 0), min(max(ys) + 500, H)
    det = cv2.FaceDetectorYN.create(os.path.join(HERE, "face_detection_yunet_2023mar.onnx"), "",
                                    (W // 2, H // 2), 0.5)
    hues, sats, vals, greys, lms, boxes = [], [], [], [], [], []
    for f in decode(src, W, H):
        hsv = cv2.cvtColor(f[b0:b1], cv2.COLOR_BGR2HSV)
        hues.append(hsv[..., 0].copy())
        sats.append(hsv[..., 1].copy())
        vals.append(hsv[..., 2].copy())
        greys.append(cv2.cvtColor(cv2.resize(f[b0:b1], (W // 2, (b1 - b0) // 2)), cv2.COLOR_BGR2GRAY))
        _, faces = det.detect(cv2.resize(f, (W // 2, H // 2)))
        face = None if faces is None else max(faces, key=lambda r: r[2] * r[3])
        lms.append(None if face is None else face[4:14].reshape(5, 2) * 2)
        boxes.append(None if face is None else face[:4] * 2 - (0, b0, 0, 0))
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
        ring0 = (dist > 40) & (dist < 60)
        s_mark, s_skin = np.median(sats[i0][dist < 8]), np.median(sats[i0][ring0])
        h_skin = float(np.median(hues[i0][ring0]))
        sat_max = int(s_mark + 0.4 * (s_skin - s_mark))
        v_mark = float(np.median(vals[i0][dist < 8]))
        v_lo, v_hi = int(v_mark * 0.6), int(v_mark * 1.4)
        face0 = boxes[i0][2] * boxes[i0][3]

        pred = {}
        for i in range(n):
            if lms[i] is not None:
                A = cv2.estimateAffine2D(lms[i0], lms[i])[0]
                if A is not None:
                    pred[i] = A @ np.array([*m["xy"], 1.0]) - (0, b0)

        def unpaintable(i, c):
            """Why frame i can't be painted at c, or "" when it shows his face at about the seed's
            size, the track inside it, and skin around the track."""
            bx = boxes[i]
            if bx is None:
                return "no face"
            if bx[2] * bx[3] < MIN_FACE * face0:
                return f"face {bx[2] * bx[3] / face0:.2f} of seed"
            # YuNet's box is jittery up close and its top often sits on the brow line, right at the mark
            mx, my = 0.25 * bx[2], 0.5 * bx[3]
            if not sure.get(i) and not (bx[0] - mx <= c[0] <= bx[0] + bx[2] + mx
                                        and bx[1] - my <= c[1] <= bx[1] + bx[3]):
                return "off face"
            if not sure.get(i) and i in pred and np.hypot(*(c - pred[i])) > 3 * LEASH:
                return f"{np.hypot(*(c - pred[i])):.0f} px from landmarks"
            d = np.hypot(xx - c[0], yy - c[1])
            ring = (d > 40) & (d < 60)
            sr, hr = np.median(sats[i][ring]), float(np.median(hues[i][ring]))
            if abs(sr - s_skin) >= 0.3 * s_skin or abs(hr - h_skin) >= 8:
                return f"ring s{sr:.0f} h{hr:.0f} vs s{s_skin:.0f} h{h_skin:.0f}"
            return ""

        xy, how, skipped, sure = {}, {}, [], {}
        for c0, c1 in zip(bounds, bounds[1:]):
            # anchor: the frame in this cut that best matches near the face's prediction
            cands = []
            for i in range(c0, c1):
                if i in pred:
                    s, c = match(sats[i], tmpl, pred[i], ANCHOR_R)
                    if s >= SNAP_SCORE and np.hypot(*(c - pred[i])) <= LEASH and not unpaintable(i, c):
                        cands.append((s, i, c))
            if not cands:
                skipped += list(range(c0, c1))
                continue
            s, ia, c = max(cands, key=lambda t: t[0])
            xy[ia], how[ia], sure[ia] = c, f"anchor {s:.2f}", s >= SURE
            for order in (range(ia + 1, c1), range(ia - 1, c0 - 1, -1)):
                last, prev = c, ia
                for i in order:
                    p, kind = flow(greys[prev], greys[i], last), "flow"
                    if p is None:
                        p, kind = last, "held"
                    s, ps = match(sats[i], tmpl, p, SNAP)
                    if s >= SNAP_SCORE:
                        p, kind = ps, f"snap {s:.2f}"
                        sure[i] = s >= SURE
                    xy[i], how[i], last, prev = p, kind, p, i

        why = {i: unpaintable(i, c) for i, c in xy.items()}
        cut_of = {i: k for k, (c0, c1) in enumerate(zip(bounds, bounds[1:])) for i in range(c0, c1)}
        for i in xy:
            # the face box jitters on a smooth track: a short "off face" gap between painted frames
            # in the same cut is painted too, or the mark would blink back for a frame or two
            if why[i] == "off face":
                lo = next((j for j in range(i - 1, i - 4, -1) if j in why and not why[j]), None)
                hi = next((j for j in range(i + 1, i + 4) if j in why and not why[j]), None)
                if lo is not None and hi is not None and cut_of[lo] == cut_of[hi] == cut_of[i]:
                    why[i] = ""
                    how[i] += ", gap painted"
        painted = []
        for i, c in xy.items():
            if why[i]:
                skipped.append(i)
                how[i] += f", skipped: {why[i]}"
                continue
            inside = (xx - c[0]) ** 2 + (yy - c[1]) ** 2 < RADIUS ** 2
            masks[i] |= (inside & (sats[i] < sat_max) & (vals[i] > v_lo) & (vals[i] < v_hi)).astype(np.uint8) * 255
            painted.append(i)
        area = int((masks[i0] > 0).sum())
        log.append({"name": m["name"], "seed": m["xy"], "cuts": bounds, "area_px": area,
                    "sat_max": sat_max, "v_range": [v_lo, v_hi], "painted": len(painted),
                    "skipped": sorted(skipped),
                    "xy": {str(i): [round(float(c[0])), round(float(c[1])) + b0] for i, c in sorted(xy.items())},
                    "how": {str(i): how[i] for i in sorted(how)}})
        print(f"{m['name']}: painted {len(painted)}/{n} frames, cuts at {bounds[1:-1]}, area on the seed frame "
              f"{area} px, sat<{sat_max}, value {v_lo}-{v_hi}, skipped {sorted(skipped)}")
    del hues, sats, vals, greys

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
