import cv2, json, sys
# segs = [[anchor_t, x, y, w, h, t_from, t_to], ...] px in the 640x360 gate shot; tracks both ways from the anchor.
# Writes keyframes every 0.1 s as fractions (x, y, w, h), padded 35 %, for render.py's moving blur.
src, segs, out = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
H, W = frames[0].shape[:2]
res = {}
for (t, x, y, w, h, ta, tb) in segs:
    i0 = round(t * fps); ia = max(0, round(ta * fps)); ib = min(len(frames) - 1, round(tb * fps))
    res[i0] = (x, y, w, h)
    for rng in (range(i0 + 1, ib + 1), range(i0 - 1, ia - 1, -1)):
        tr = cv2.TrackerCSRT_create(); tr.init(frames[i0], (x, y, w, h))
        for i in rng:
            ok, b = tr.update(frames[i])
            if ok: res[i] = tuple(int(v) for v in b)
keys = []
for i, b in sorted(res.items()):
    if i % 3 and i not in (min(res), max(res)): continue
    x, y, w, h = b; p = 0.35
    keys.append([round(i / fps, 3), round((x - w * p) / W, 4), round((y - h * p) / H, 4), round(w * (1 + 2 * p) / W, 4), round(h * (1 + 2 * p) / H, 4)])
json.dump({'fps': fps, 'keys': keys}, open(out, 'w'))
for i, b in sorted(res.items()):
    if i % 3: continue
    f = frames[i].copy(); x, y, w, h = b; p = 0.35
    cv2.rectangle(f, (int(x - w * p), int(y - h * p)), (int(x + w * (1 + p)), int(y + h * (1 + p))), (0, 255, 255), 2)
    cv2.putText(f, f'{i / fps:.2f}', (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.imwrite(out.replace('.json', f'_{i:04d}.jpg'), f)
