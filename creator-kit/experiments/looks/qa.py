#!/usr/bin/env python3
"""Checks a looks build before nq-check sees it.

    python3 qa.py --spec spec_sep03.json --work work --transcript /path/to/words_large.json

1. words   every caption and hook on screen is a run of his words, in order, from the
           transcript inside the kept ranges (no invented copy).
2. safe    every caption and hook box sits inside the Instagram safe zone from theme.ts.
3. mouth   no caption or hook box covers his mouth, wherever the crop puts it.
4. files   the base's size (timeline.json; --size or the spec's "size" must match it),
           30 fps, same length as the base (one frame of slack).
5. loud    -14 LUFS +-1 integrated, true peak at or under -1 dBTP.
grid2x2.mp4 gets the file and loudness checks; its quadrants' text is reported (WARN),
since a quarter-size look can't keep the full frame's safe zone.
Exits 1 on any FAIL.
"""
import argparse, json, os, re, subprocess, sys

import build_looks as bl  # one source for W, H and SAFE


def norm(s):
    return [t for t in re.sub(r"[^a-z0-9' ]", " ", s.lower().replace("\u2019", "'")).split() if t]


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
                        "-show_entries", "stream=width,height,r_frame_rate,nb_read_packets",
                        "-of", "json", path], capture_output=True, text=True)
    return json.loads(r.stdout)["streams"][0]


def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-filter_complex",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rindex("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", tail).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail).group(1))
    return i, tp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--size", help="WxH; must match the base (default: spec \"size\")")
    a = ap.parse_args()
    spec = bl.load_spec(a.spec)
    bl.load_timeline(a, spec)  # exits if the base was built at another size
    W, H, SAFE = bl.W, bl.H, bl.SAFE
    man = json.load(open(os.path.join(a.work, "manifest.json")))
    base_n = int(probe(os.path.join(a.work, "base.mp4"))["nb_read_packets"])
    words = json.load(open(a.transcript))["words"]
    kept = [w for w in words
            if any(s - 0.7 <= w["start"] <= e for s, e in spec["keep"])]  # 0.7 s: whisper starts run early
    said = norm(" ".join(w["w"] for w in kept))
    fails = 0

    def report(ok, what):
        nonlocal fails
        fails += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {what}")

    def in_order(toks):
        n = len(toks)
        return any(said[i:i + n] == toks for i in range(len(said) - n + 1))

    for name, m in man.items():
        print(f"{name} ({m['title']}, {m['status']})")
        bad_words = [e["text"] for e in m["elements"] if not in_order(norm(e["text"]))]
        report(not bad_words, "words: all on-screen copy is his, in order" +
               (f" -- not found: {bad_words}" if bad_words else ""))
        out = [e for e in m["elements"]
               if e["box"][0] < SAFE[0] - 2 or e["box"][1] < SAFE[1] - 2
               or e["box"][2] > SAFE[2] + 2 or e["box"][3] > SAFE[3] + 2]
        report(not out, f"safe: {len(m['elements'])} boxes inside {SAFE}" +
               (f" -- outside: {[(e['text'], e['box']) for e in out]}" if out else ""))
        # mouth: a box that covers the mouth point, with a margin of a tenth of the face height
        mo, r = m.get("mouth"), m.get("face_h", 0) / 10
        on_mouth = [(e["text"], e["box"]) for e in m["elements"] if mo
                    and e["box"][0] <= mo["x"][1] + r and e["box"][2] >= mo["x"][0] - r
                    and e["box"][1] <= mo["y"][1] + r and e["box"][3] >= mo["y"][0] - r]
        report(bool(mo) and not on_mouth,
               (f"mouth: no text over the mouth (x {mo['x']}, y {mo['y']})" if mo else "mouth: not recorded") +
               (f" -- over it: {on_mouth}" if on_mouth else ""))
        p = probe(os.path.join(a.work, m["file"]))
        n = int(p["nb_read_packets"])
        ok = p["width"] == W and p["height"] == H and p["r_frame_rate"] == "30/1" and abs(n - base_n) <= 1
        report(ok, f"file: {p['width']}x{p['height']} {p['r_frame_rate']} {n} frames (base {base_n})")
        i, tp = loudness(os.path.join(a.work, m["file"]))
        report(abs(i + 14) <= 1 and tp <= -1.0, f"loud: {i} LUFS, true peak {tp} dBTP")
    for extra in ("cycle.mp4", "grid.mp4", "grid2x2.mp4"):
        path = os.path.join(a.work, extra)
        if os.path.exists(path):
            i, tp = loudness(path)
            print(extra)
            if extra == "grid2x2.mp4":
                p = probe(path)
                n = int(p["nb_read_packets"])
                report(p["width"] == W and p["height"] == H and p["r_frame_rate"] == "30/1"
                       and abs(n - base_n) <= 1,
                       f"file: {p['width']}x{p['height']} {p['r_frame_rate']} {n} frames (base {base_n})")
                for q, name in enumerate(spec.get("grid2x2", [])):
                    ox, oy = (q % 2) * W // 2, (q // 2) * H // 2
                    boxes = [[ox + b[0] / 2, oy + b[1] / 2, ox + b[2] / 2, oy + b[3] / 2]
                             for b in (e["box"] for e in man.get(name, {}).get("elements", []))]
                    out = sum(b[0] < SAFE[0] or b[1] < SAFE[1] or b[2] > SAFE[2] or b[3] > SAFE[3] for b in boxes)
                    print(f"  {'WARN' if out else 'PASS'}  safe: {name} quadrant, {out} of {len(boxes)} "
                          f"text boxes outside the full-frame safe zone")
            report(abs(i + 14) <= 1 and tp <= -1.0, f"loud: {i} LUFS, true peak {tp} dBTP")
    print("RESULT:", "PASS" if not fails else f"FAIL ({fails})")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
