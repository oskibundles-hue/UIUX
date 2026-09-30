#!/usr/bin/env python3
"""capscan.py -- measure the burned-in word-highlight captions of the approved cut, per frame.

The T7 captions are an opaque dark box (26,25,30 -> 16,15,20) in y ~1280-1450 with white spoken words,
grey upcoming words and a WHITE BOX behind the word being spoken. A frame counts as "word spoken" when a
white run of at least 24 px (full res) sits in the caption rows. That is the speech-activity signal the
audio accents duck under (lib/mix.py) and the caption-clear check in QA (build.py --stage qa).

    python3 lib/capscan.py --video V.mp4 --ffmpeg FF --out lib/data/captions.json
JSON: {"fps":29.97, "n":3866, "rect":[x0,y0,x1,y1], "word":[0/1 per frame], "hl":[[x0,y0,x1,y1] or null]}
"""
import argparse, json, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--video', required=True); ap.add_argument('--ffmpeg', required=True); ap.add_argument('--out', required=True)
A = ap.parse_args()
X0, Y0, W, H = 60, 1260, 780, 220            # caption box area, full res; analysed at half res
w, h = W // 2, H // 2
p = subprocess.Popen([A.ffmpeg, '-v', 'error', '-i', A.video, '-vf', f'crop={W}:{H}:{X0}:{Y0},scale={w}:{h}:flags=area',
                      '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
word, hls = [], []
while True:
    b = p.stdout.read(w * h * 3)
    if len(b) < w * h * 3:
        break
    f = np.frombuffer(b, np.uint8).reshape(h, w, 3)
    white = f.min(-1) >= 200
    cs = np.cumsum(np.pad(white, ((0, 0), (1, 0))), 1)
    win = (cs[:, 12:] - cs[:, :-12]) == 12
    # a highlight box is a solid white block: >= 12 rows (24 px) of long runs
    rows = np.where(win.sum(1) > 0)[0]
    ok = len(rows) >= 12
    if ok:
        hy, hx = np.where(win)
        hls.append([int(hx.min()) * 2 + X0, int(hy.min()) * 2 + Y0, int(hx.max() + 12) * 2 + X0, int(hy.max()) * 2 + Y0])
    else:
        hls.append(None)
    word.append(int(ok))
p.wait()
json.dump(dict(fps=30000 / 1001, n=len(word), rect=[X0, Y0, X0 + W, Y0 + H], word=word, hl=hls), open(A.out, 'w'))
print(f'{len(word)} frames, word-highlight on {sum(word)} ({100 * sum(word) / len(word):.1f} %)')
