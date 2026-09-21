#!/usr/bin/env python3
"""
plan_reel.py - build an assemble_reel plan from ordered exports and their
transcripts, to a target length.

  plan_reel.py --target 90 --out plan.json "exports/01 x.mp4" "exports/02 y.mp4" ...

Transcripts are looked up as trial/aNN.json from the export's NN prefix.
If the clips fit the target they are used whole. Otherwise each clip gets a
time budget, and inside each clip the single contiguous window of that length
holding the most spoken words is kept, snapped to phrase edges. Order is never
changed.

Budget split (--weight, 0..1). Splitting purely by clip length gives a long,
near-silent take as much screen time as a talky one, and the reel then runs
with captions on a fraction of its length. Splitting purely by his-voice word
count fixes the captions but can starve the best-looking footage. The budget is
therefore dur**(1-weight) * words**weight, normalised, with a 12s floor:

    weight 0.0   by length only        (how MR1-MR8 were built)
    weight 0.7   default; captions win most of the argument, footage keeps a share
    weight 1.0   by his-voice words only

Measured on the MR series: weight makes no difference when the clips are evenly
talky (MR3 captured 161 of 221 of his words at every setting) and no difference
when the footage barely has him speaking (MR4 has 55 of his words in 86s of
footage; 48 at 0.0, 51 at 1.0 -- a caption problem no planner can solve). It
matters when one clip carries the talking: MR6 went 128 -> 143 of 200 at 0.7,
buying 15 more captioned words for 7s off its second chapter.
"""
import argparse, json, os, re, subprocess

def dur(p):
    e = subprocess.run(["ffmpeg", "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e); return int(m[1])*3600+int(m[2])*60+float(m[3])

def phrases(tpath, drop=None):
    """(start, end, words) per phrase; words inside dropped (other-voice) ranges count as 0."""
    out = []
    for s in json.load(open(tpath)):
        n = len(s.get("words", []))
        if drop and any(a - 0.05 <= s["start"] and s["end"] <= b + 0.05 for a, b in drop): n = 0
        out.append((s["start"], s["end"], n))
    return out

def best_window(ph, total, budget):
    if not ph or budget >= total: return 0.0, total
    best, bs = (0.0, min(total, budget)), -1
    starts = [0.0] + [p[0] for p in ph]
    for a in starts:
        if a + budget > total: a = max(0.0, total - budget)   # late speech: slide the window back, don't skip it
        b = min(total, a + budget)
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
    ap.add_argument("--drop-dir", default=None, help="dir with drop_NN.json (other-voice ranges) so those words don't attract the window")
    ap.add_argument("--weight", type=float, default=0.7, help="0 splits the budget by clip length, 1 by his-voice word count, between blends the two")
    a = ap.parse_args()
    items = []
    for c in a.clips:
        n = re.match(r"(\d{2})", os.path.basename(c))[1]
        t = os.path.join(a.tdir, f"a{n}.json")
        drop = None
        if a.drop_dir and os.path.exists(os.path.join(a.drop_dir, f"drop_{n}.json")):
            d = json.load(open(os.path.join(a.drop_dir, f"drop_{n}.json"))); drop = d if isinstance(d, list) else d.get(n, d.get("ranges", []))
        ph = phrases(t, drop) if os.path.exists(t) else []
        items.append({"clip": c, "words": t, "dur": dur(c), "ph": ph, "said": sum(n for _, _, n in ph)})
    total = sum(i["dur"] for i in items)
    segs = []
    if total <= a.target * 1.08:
        for i in items: segs.append({"clip": i["clip"], "words": i["words"], "in": 0.0, "out": round(i["dur"], 2)})
    else:
        w = min(1.0, max(0.0, a.weight))
        share = [i["dur"] ** (1 - w) * max(i["said"], 1) ** w for i in items]
        pool = sum(share)
        for i, sh in zip(items, share):
            budget = max(12.0, a.target * sh / pool)
            s, e = best_window(i["ph"], i["dur"], budget)
            segs.append({"clip": i["clip"], "words": i["words"], "in": s, "out": e})
    plan = {"fps": 29.97, "fix": json.loads(a.fix), "segments": segs}
    json.dump(plan, open(a.out, "w"), indent=1)
    print(f"{len(segs)} segments, {sum(s['out']-s['in'] for s in segs):.1f}s (source {total:.0f}s, target {a.target:.0f}s)")
    for s, i in zip(segs, items):
        kept = sum(n for st, e, n in i["ph"] if st >= s["in"] - 0.05 and e <= s["out"] + 0.05)
        print(f"  {os.path.basename(s['clip'])[:28]:<28} {s['in']:6.1f} -> {s['out']:6.1f}   his words {kept}/{i['said']}")

if __name__ == "__main__":
    main()
