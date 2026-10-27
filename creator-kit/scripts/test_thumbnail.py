#!/usr/bin/env python3
"""Check thumbnail.py against a made-up clip with known answers: 5 s blurred, 5 s sharp, 5 s black, 5 s soft.

usage: python3 creator-kit/scripts/test_thumbnail.py      (needs ffmpeg, Pillow, numpy; no network)
"""
import json, os, subprocess, sys, tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import thumbnail as t  # noqa: E402

fails = total = 0


def check(label, ok, extra=""):
    global fails, total
    total += 1
    fails += not ok
    print(("PASS" if ok else "FAIL"), label, "" if ok else extra)


tmp = tempfile.mkdtemp(prefix="thumbs-")
clip = os.path.join(tmp, "clip.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=540x960:r=25:d=20", "-vf",
                "split=4[a][b][c][d];[a]trim=0:5,setpts=PTS-STARTPTS,gblur=sigma=25[a1];"
                "[b]trim=5:10,setpts=PTS-STARTPTS[b1];[c]trim=10:15,setpts=PTS-STARTPTS,eq=brightness=-0.95[c1];"
                "[d]trim=15:20,setpts=PTS-STARTPTS,gblur=sigma=12[d1];[a1][b1][c1][d1]concat=n=4",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", clip], check=True)

# scoring
frames, times = t.sample(clip, t.probe_duration(clip), 40)
check("samples the asked number of frames", len(frames) == 40, len(frames))
scores, _ = t.score_frames(frames)
seg = lambda a, b: [s for s, x in zip(scores, times) if a <= x < b]
check("sharp section beats blurred", min(seg(5, 10)) > max(seg(0, 5)), (min(seg(5, 10)), max(seg(0, 5))))
check("black section scores lowest", max(seg(10, 15)) < min(seg(0, 5) + seg(15, 20)))
kept = t.pick(times, scores, frames, 4, 2.0)
check("best pick is from the sharp section", 5 <= times[max(kept, key=lambda i: scores[i])] < 10)
check("no black frame is ever picked", not any(10 <= times[i] < 15 for i in kept), [times[i] for i in kept])

# safe zones and contrast
check("centre-upper box is safe", t.safe_check((150, 500, 930, 900)) == [])
check("box in bottom third is flagged", "in the bottom third" in t.safe_check((150, 1200, 930, 1400)))
check("box in top-left is flagged", "in the top-left UI corner" in t.safe_check((100, 300, 600, 500)))
check("box above the grid crop is flagged", "outside the 3:4 grid crop" in t.safe_check((150, 100, 930, 400)))
check("white on black reads", t.contrast("#FFFFFF", np.zeros((10, 10, 3), np.uint8)) > 15)
check("FD red on red paint does not", t.contrast("#FE0F13", np.full((10, 10, 3), (230, 20, 20), np.uint8)) < 3)

# a very long headline still fits inside the grid and the margins
img = Image.new("RGB", (t.W, t.H), (120, 120, 120))
for b in t.BRANDS:
    _, box, _ = t.render_text(img, b, "the longest headline anyone would|ever put on a cover frame", "kicker")
    check(f"{b}: long headline stays safe", t.safe_check(box) == [] and box[0] >= 60 and box[2] <= t.W - 60, box)

# whole run per brand
for b in t.BRANDS:
    out = os.path.join(tmp, b)
    r = subprocess.run([sys.executable, os.path.join(HERE, "thumbnail.py"), clip, "--brand", b,
                        "--text", "Forged|fitment day", "--kicker", "the pickup", "--picks", "3", "--out", out],
                       capture_output=True, text=True, timeout=120)
    files = set(os.listdir(out)) if os.path.isdir(out) else set()
    rep = json.load(open(os.path.join(out, "covers.json"))) if "covers.json" in files else {"covers": []}
    ok = (r.returncode == 0 and {"sheet.png", "cover-01-clean.jpg", "cover-01-text.jpg", "grid-01.jpg"} <= files
          and all(c["safe"] for c in rep["covers"]))
    check(f"{b}: full run writes covers, grid checks and sheet", ok, r.stdout + r.stderr)
    if b == "fd":
        check("covers are 1080x1920", Image.open(os.path.join(out, "cover-01-text.jpg")).size == (1080, 1920))

r = subprocess.run([sys.executable, os.path.join(HERE, "thumbnail.py"), clip, "--brand", "se", "--at", "7.5",
                    "--out", os.path.join(tmp, "at")], capture_output=True, text=True, timeout=60)
rep = json.load(open(os.path.join(tmp, "at", "covers.json")))
check("--at uses your frame, no text gives clean only", r.returncode == 0 and [c["time"] for c in rep["covers"]] == [7.5]
      and not os.path.exists(os.path.join(tmp, "at", "cover-01-text.jpg")), r.stdout + r.stderr)

print(f"{total - fails}/{total} passed")
sys.exit(1 if fails else 0)
