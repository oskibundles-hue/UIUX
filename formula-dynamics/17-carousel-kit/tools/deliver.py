#!/usr/bin/env python3
"""Deliver one finished carousel: deliver.py DATE SLOT [--to DIR] [--force]

1. Stops if the carousel has no ledger row (ledger/rows/DATE_SLOT.csv): the row is the record that the photos,
   fitment and prices were checked. Then runs lint.py and stops on any FAIL (--force skips both, say why in the
   ledger notes).
2. Renders it into <delivery>/exports/DATE/SLOT/01.jpg ... + Caption.txt.
3. Copies the editable source (source, assets, tools, campaign.json, BRIEF.md, ledger) into <delivery>/editable source/.
4. Rebuilds the merged ledger and PROGRESS.md (progress.py).
The delivery folder is campaign.json "delivery_dir" unless --to names another."""
import sys, shutil, argparse, subprocess, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import campaign as C

ap = argparse.ArgumentParser()
ap.add_argument("date"); ap.add_argument("slot")
ap.add_argument("--to"); ap.add_argument("--force", action="store_true")
a = ap.parse_args()
c = C.load()
DEL = C.delivery_dir(c, a.to)
src = C.HERE / "source" / a.date / a.slot
assert a.slot in C.slot_ids(c), f"{a.slot} is not a slot in campaign.json"
slides = C.slides_of(src)
assert slides, f"no slide-NN.html in {src}"
assert (src / "Caption.txt").exists(), f"no Caption.txt in {src}"
tools = pathlib.Path(__file__).resolve().parent
row = C.HERE / "ledger" / "rows" / f"{a.date}_{a.slot}.csv"
if not a.force and (not row.exists() or len([l for l in row.read_text().splitlines() if l.strip()]) < 2):
    sys.exit(f"no ledger row in {row.relative_to(C.HERE)} (header from ledger/HEADER.csv, then one row saying how the "
             "photos, fitment and prices were checked). Nothing delivered.")
if not a.force:
    r = subprocess.run([sys.executable, str(tools / "lint.py"), str(src)])
    if r.returncode:
        sys.exit("lint found FAIL items: fix them (or --force and note why in the ledger). Nothing delivered.")
from playwright.sync_api import sync_playwright
import render as R
out = DEL / "exports" / a.date / a.slot
with sync_playwright() as pw:
    b, pg = R.open_browser(pw)
    n = R.render(pg, slides, out, phone=False)
    b.close()
shutil.copy(src / "Caption.txt", out / "Caption.txt")
C.sync_editable(DEL)
subprocess.run([sys.executable, str(tools / "progress.py")] + (["--to", a.to] if a.to else []), check=True)
print(f"delivered {a.date}/{a.slot}: {n} slides -> {out}")
