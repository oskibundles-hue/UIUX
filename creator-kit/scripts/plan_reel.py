#!/usr/bin/env python3
"""
plan_reel.py - build an assemble_reel plan from ordered exports and their
transcripts, to a target length.

  plan_reel.py --target 90 --out plan.json "exports/01 x.mp4" "exports/02 y.mp4" ...

Transcripts are looked up as trial/aNN.json from the export's NN prefix.
If the clips fit the target they are used whole. Otherwise each clip gets a
time budget in proportion to its length (floor 12s), and inside each clip the
single contiguous window of that length holding the most spoken words is
kept, snapped to phrase edges. Order is never changed.
"""
import argparse, json, os, re, subprocess

def dur(p):
    e = subprocess.run(["ffmpeg", "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e); return int(m[1])*3600+int(m[2])*60+float(m[3])

def phrases(tpath):
    return [(s["start"], s["end"], len(s.get("words", []))) for s in json.load(open(tpath))]

def best_window(ph, total, budget):
    if not ph or budget >= total: return 0.0, total
    best, bs = (0.0, min(total, budget)), -1
    starts = [0.0] + [p[0] for p in ph]
    for a in starts:
        b = min(total, a + budget)
        if b - a < budget * 0.8 and a > 0: continue
        w = sum(n for s, e, n in ph if s >= a - 0.05 and e <= b + 0.05)
        if w > bs: bs, best = w, (a, b)
    a, b = best
    # snap the end to the last phrase that fits
    ends = [e for s, e, n in ph if e <= b + 0.05 and e > a]
    if ends: b = min(total, max(ends) + 0.15)
    return round(a, 2), round(b, 2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+"); ap.add_argument("--target", type=float, default=90)
    ap.add_argument("--out", required=True); ap.add_argument("--tdir", default="trial")
    ap.add_argument("--fix", default="{}")
    a = ap.parse_args()
    items = []
    for c in a.clips:
        n = re.match(r"(\d{2})", os.path.basename(c))[1]
        t = os.path.join(a.tdir, f"a{n}.json")
        items.append({"clip": c, "words": t, "dur": dur(c), "ph": phrases(t) if os.path.exists(t) else []})
    total = sum(i["dur"] for i in items)
    segs = []
    if total <= a.target * 1.08:
        for i in items: segs.append({"clip": i["clip"], "words": i["words"], "in": 0.0, "out": round(i["dur"], 2)})
    else:
        for i in items:
            budget = max(12.0, a.target * i["dur"] / total)
            s, e = best_window(i["ph"], i["dur"], budget)
            segs.append({"clip": i["clip"], "words": i["words"], "in": s, "out": e})
    plan = {"fps": 29.97, "fix": json.loads(a.fix), "segments": segs}
    json.dump(plan, open(a.out, "w"), indent=1)
    print(f"{len(segs)} segments, {sum(s['out']-s['in'] for s in segs):.1f}s (source {total:.0f}s, target {a.target:.0f}s)")
    for s in segs: print(f"  {os.path.basename(s['clip'])[:28]:<28} {s['in']:6.1f} -> {s['out']:6.1f}")

if __name__ == "__main__":
    main()
