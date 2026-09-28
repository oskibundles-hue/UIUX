"""plate_find.py -- locate the licence plate in the rear chase shot S17 (source f348-368). The white temporary
tag ("NZ-303-..." / a date) is readable at full res, so it is blurred in the plate stage.

Method: hand-read keyframe boxes (from gridded full-res crops, KEYS below) give a predicted box per frame;
inside a +-40 px window around it the tag's white ink is found and its bounding box snaps the prediction;
the result is smoothed (3-frame median on the centre, the median size). Writes lib/data/plate_track.json
{"<f>": [x, y, w, h]} in 1080x1920 px.

    python3 lib/plate_find.py
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
F0, F1 = 348, 368
KEYS = {348: (874, 976, 100, 44), 352: (844, 980, 100, 46), 356: (796, 984, 100, 46), 358: (766, 986, 104, 48),
        361: (726, 992, 104, 44), 364: (686, 996, 108, 48), 366: (660, 1000, 110, 48), 368: (640, 1000, 110, 56)}


def predict(f):
    ks = sorted(KEYS)
    for a, b in zip(ks, ks[1:]):
        if a <= f <= b:
            u = (f - a) / (b - a)
            return [KEYS[a][k] + (KEYS[b][k] - KEYS[a][k]) * u for k in range(4)]
    return list(KEYS[ks[0]] if f < ks[0] else KEYS[ks[-1]])


def main():
    src = np.load(os.path.join(HERE, '..', '.work', 'src.npy'), mmap_mode='r')
    raw = {}
    for f in range(F0, F1 + 1):
        px, py, pw, ph = predict(f)
        x0, y0 = int(px - 40), int(py - 40)
        x1, y1 = int(px + pw + 40), int(py + ph + 40)
        im = src[f, y0:y1, x0:x1].astype(np.float32) / 255
        white = (im.min(2) > 0.5) & ((im.max(2) - im.min(2)) < 0.25)
        ys, xs = np.nonzero(white)
        box = [px, py, pw, ph]
        if len(xs) > 40:
            bx0, bx1 = np.percentile(xs, 2) + x0, np.percentile(xs, 98) + x0
            by0, by1 = np.percentile(ys, 2) + y0, np.percentile(ys, 98) + y0
            if 70 <= bx1 - bx0 <= 140 and 28 <= by1 - by0 <= 70:
                box = [bx0, by0, bx1 - bx0, by1 - by0]
        raw[f] = box
    fs = sorted(raw)
    arr = np.array([raw[f] for f in fs])
    c = np.stack([arr[:, 0] + arr[:, 2] / 2, arr[:, 1] + arr[:, 3] / 2], 1)
    cs = np.array([np.median(c[max(0, i - 1):i + 2], 0) for i in range(len(c))])
    w, h = np.percentile(arr[:, 2], 80), np.percentile(arr[:, 3], 80)
    out = {str(f): [round(float(cs[i, 0] - w / 2), 1), round(float(cs[i, 1] - h / 2), 1), round(float(w), 1),
                    round(float(h), 1)] for i, f in enumerate(fs)}
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, 'data', 'plate_track.json'), 'w'), indent=1)
    for f in fs:
        print(f, [round(v) for v in raw[f]], out[str(f)])


if __name__ == '__main__':
    main()
