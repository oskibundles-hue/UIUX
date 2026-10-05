#!/usr/bin/env python3
"""track_csrt.py -- OpenCV CSRT tracker for a car ahead (the kit's numpy tracker lost the purple car at night).
  Edit the clip and the start box below; needs `pip install opencv-contrib-python-headless`. Writes tracks32.json."""
import cv2, json, sys
cap = cv2.VideoCapture('raw32.mov'); ok, fr = cap.read()
box = (390, 930, 160, 105)
mk = getattr(cv2, 'TrackerCSRT_create', None) or cv2.legacy.TrackerCSRT_create
tr = mk(); tr.init(fr, box)
frames = [{'f': 0, 'x': box[0], 'y': box[1], 'w': box[2], 'h': box[3], 'conf': 1.0}]
i = 0
while True:
    ok, fr = cap.read()
    if not ok: break
    i += 1
    good, b = tr.update(fr)
    frames.append({'f': i, 'x': float(b[0]), 'y': float(b[1]), 'w': float(b[2]), 'h': float(b[3]), 'conf': 1.0 if good else 0.2})
# light smoothing (centered moving average, 5 frames) on centre and size
def sm(k):
    v = [f[k] for f in frames]; n = len(v); out = []
    for j in range(n):
        s = v[max(0, j-2):min(n, j+3)]; out.append(sum(s)/len(s))
    return out
for k in ('x', 'y', 'w', 'h'):
    s = sm(k)
    for j, f in enumerate(frames): f[k] = round(s[j], 2)
json.dump({'car': {'f0': 0, 'fps': 30000/1001, 'frames': frames}}, open('tracks32.json', 'w'))
print('frames', len(frames), 'lost', sum(1 for f in frames if f['conf'] < 1))
for j in (0, 60, 120, 150, 180, 240, 300, len(frames)-1): f = frames[j]; print(j, round(f['x']), round(f['y']), round(f['w']), round(f['h']))
