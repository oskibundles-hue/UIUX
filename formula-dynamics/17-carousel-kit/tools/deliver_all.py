#!/usr/bin/env python3
"""Re-render every carousel (or --dates d1,d2) into the delivery folder in one browser, then verify all of it.
Usage: deliver_all.py [--dates 2026-11-20,2026-11-21] [--verify-only] [--to DIR]

Verify: each carousel's export has exactly as many NN.jpg as source has slides, all 1080x1350, a Caption.txt
identical to source, and no slide identical to another carousel's (md5). Writes out/delivery-manifest.json
(source hash and export md5s per carousel) so a later run can tell what changed. Exit 1 on any problem."""
import sys, json, shutil, hashlib, argparse, subprocess, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import campaign as C
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--dates", default=""); ap.add_argument("--verify-only", action="store_true"); ap.add_argument("--to")
a = ap.parse_args()
c = C.load(); DEL = C.delivery_dir(c, a.to)
want = set(filter(None, a.dates.split(",")))
if not a.verify_only:
    from playwright.sync_api import sync_playwright
    import render as R
    with sync_playwright() as pw:
        b, pg = R.open_browser(pw)
        for p in C.carousels(c, want):
            out = DEL / "exports" / p.parent.name / p.name
            R.render(pg, C.slides_of(p), out, phone=False)
            shutil.copy(p / "Caption.txt", out / "Caption.txt")
            print("delivered", p.parent.name, p.name, flush=True)
        b.close()
    C.sync_editable(DEL)
    subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "progress.py")] + (["--to", a.to] if a.to else []),
                   check=True, stdout=subprocess.DEVNULL)

seen, problems, manifest = {}, [], {}
for p in C.carousels(c):
    key = f"{p.parent.name}/{p.name}"
    out = DEL / "exports" / key
    n = len(C.slides_of(p))
    h = hashlib.md5()
    for f in C.slides_of(p) + [p / "Caption.txt"]:
        if f.exists(): h.update(f.read_bytes())
    have = sorted(out.glob("[0-9][0-9].jpg"))
    if len(have) != n: problems.append(f"{key}: {len(have)} exported slides, source has {n}")
    md5s = []
    for f in have:
        if Image.open(f).size != (1080, 1350): problems.append(f"{key}: {f.name} wrong size")
        m = hashlib.md5(f.read_bytes()).hexdigest(); md5s.append(m)
        if m in seen and seen[m] != key: problems.append(f"{key}: {f.name} identical to a slide of {seen[m]}")
        seen[m] = key
    cap = out / "Caption.txt"
    if not cap.exists() or cap.read_bytes() != (p / "Caption.txt").read_bytes(): problems.append(f"{key}: caption differs from source")
    manifest[key] = {"source": h.hexdigest(), "exports": md5s}
(C.HERE / "out").mkdir(exist_ok=True)
(C.HERE / "out" / "delivery-manifest.json").write_text(json.dumps(manifest, indent=1))
print(f"verified {C.pl(len(manifest), 'carousel')}, {C.pl(sum(len(v['exports']) for v in manifest.values()), 'slide')}; {len(problems)} problem(s)")
for x in problems: print("  PROBLEM", x)
sys.exit(1 if problems else 0)
