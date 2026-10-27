#!/usr/bin/env python3
"""Paint out small marks on the skin (a patch, a speck) across the whole base, before the looks.

    python3 retouch.py --spec spec_sep03.json --work work

Runs after `build_looks.py base` and before `looks`. Each entry in the spec's "retouch" list
gives one mark: the time it is seeded at and its centre there, in pixels of the base's size.
The mark is followed frame by frame by matching its own saturation patch from the seed frame:
a grey patch on skin stands out by saturation, not brightness, because the ceiling lights make
the brightest spots on the face. The mask is the low-saturation pixels in a disc at each match,
grown a little and filled with OpenCV's Telea inpainting. A frame lost between two tracked ones
takes the midpoint of its neighbours; any other lost frame is left untouched and listed, so a miss
shows up in the log rather than as a smudge in the wrong place.

The untouched base is kept as base_src.mp4 (re-running starts from it), and the track goes to
retouch.json for the check pass.
"""
import argparse, json, os, shutil, subprocess, sys
import cv2
import numpy as np

SEARCH, RADIUS, GROW, INPAINT = 150, 26, 5, 9   # px at 2160 wide
MIN_SCORE = 0.6                                  # template match below this counts as lost


def find(sat, tmpl, pred, search, sat_max):
    """Best match of the mark's saturation template near pred, as (centre, mask), or None."""
    H, W = sat.shape
    h, w = tmpl.shape
    x0, y0 = max(int(pred[0]) - search, 0), max(int(pred[1]) - search, 0)
    x1, y1 = min(int(pred[0]) + search, W), min(int(pred[1]) + search, H)
    res = cv2.matchTemplate(sat[y0:y1, x0:x1], tmpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    if score < MIN_SCORE:
        return None
    c = np.array([x0 + loc[0] + w / 2, y0 + loc[1] + h / 2])
    return c, disc_mask(sat, c, sat_max)


def disc_mask(sat, c, sat_max):
    """The mark's own pixels: low saturation, inside a disc at c."""
    yy, xx = np.ogrid[:sat.shape[0], :sat.shape[1]]
    disc = (xx - c[0]) ** 2 + (yy - c[1]) ** 2 < RADIUS ** 2
    return ((sat < sat_max) & disc).astype(np.uint8) * 255


def decode(path, W, H):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    while len(b := p.stdout.read(W * H * 3)) == W * H * 3:
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--work", required=True)
    a = ap.parse_args()
    marks = json.load(open(a.spec)).get("retouch", [])
    tl = json.load(open(os.path.join(a.work, "timeline.json")))
    W, H = tl["size"]
    base, src = os.path.join(a.work, "base.mp4"), os.path.join(a.work, "base_src.mp4")
    if not marks:
        sys.exit("spec has no retouch entries")
    if not os.path.exists(src):
        shutil.copy(base, src)

    # track on a band of rows around the marks (all 4K frames at once would be ~8.6 GB), then
    # stream the base a second time to paint
    ys = [m["xy"][1] for m in marks]
    b0, b1 = max(min(ys) - 500, 0), min(max(ys) + 500, H)
    frames = []
    for f in decode(src, W, H):
        frames.append(f[b0:b1].copy())
    log = []
    masks = [np.zeros((b1 - b0, W), np.uint8) for _ in frames]
    for m in marks:
        i0 = round(m["t"] * 30)
        seed = np.array(m["xy"], float) - (0, b0)
        # threshold halfway between the mark's own saturation and the skin in a ring around it
        sat = cv2.cvtColor(frames[i0], cv2.COLOR_BGR2HSV)[..., 1]
        yy, xx = np.mgrid[:sat.shape[0], :sat.shape[1]]
        d = np.hypot(xx - seed[0], yy - seed[1])
        sat_max = int((np.median(sat[d < 8]) + np.median(sat[(d > 40) & (d < 60)])) / 2)
        sats = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[..., 1] for f in frames]
        cx, cy = int(seed[0]), int(seed[1])
        tmpl = sats[i0][cy - RADIUS:cy + RADIUS, cx - RADIUS:cx + RADIUS].copy()
        track_xy, lost = {}, []
        for order in (range(i0, len(frames)), range(i0 - 1, -1, -1)):   # forward, then back from the seed
            pos, search = seed, SEARCH
            for i in order:
                h = find(sats[i], tmpl, pos, search, sat_max)
                if h is None:
                    lost.append(i)
                    search = min(search * 2, 600)   # look wider until it comes back
                    continue
                pos, search = h[0], SEARCH
                track_xy[i] = [round(float(pos[0])), round(float(pos[1])) + b0]
                masks[i] |= h[1]
        # a frame lost between two tracked ones takes the midpoint of its neighbours
        for i in list(lost):
            if i - 1 in track_xy and i + 1 in track_xy:
                c = (np.array(track_xy[i - 1]) + np.array(track_xy[i + 1])) / 2
                track_xy[i] = [round(float(c[0])), round(float(c[1]))]
                masks[i] |= disc_mask(sats[i], c - (0, b0), sat_max)
                lost.remove(i)
        area = int((masks[i0] > 0).sum())
        log.append({"name": m["name"], "seed": m["xy"], "area_px": area, "sat_max": sat_max,
                    "tracked": len(track_xy), "lost": sorted(lost), "xy": track_xy})
        print(f"{m['name']}: {len(track_xy)}/{len(frames)} frames, area on the seed frame {area} px, sat<{sat_max}, "
              f"lost {sorted(lost)[:12]}{' ...' if len(lost) > 12 else ''}")

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * GROW + 1, 2 * GROW + 1))
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-c:v", "libx264", "-crf", "12",
                            "-preset", "medium", "-pix_fmt", "yuv420p", "-colorspace", "bt709",
                            "-color_primaries", "bt709", "-color_trc", "bt709", base], stdin=subprocess.PIPE)
    del frames
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
