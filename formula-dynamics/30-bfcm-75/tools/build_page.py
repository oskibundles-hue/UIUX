#!/usr/bin/env python3
"""Build the private review page (claude.ai artifact) for FD-BFCM-75 from the Drive delivery folder.
Writes OUT/index.html, OUT/fd-icon.png and OUT/s/<date>_<slot>_<n>.jpg (540 px wide, q82).
Usage: build_page.py DELIVERY_DIR OUT_DIR"""
import sys, csv, json, html, pathlib, datetime, shutil
from PIL import Image

DEL, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
HERE = pathlib.Path(__file__).resolve().parent.parent
SLOTS = [("1_products", "Product spotlight", "9 AM"), ("2_sale", "Sale guide", "11 AM"),
         ("3_cars", "Car with product", "1 PM"), ("4_education", "Education", "4 PM"),
         ("5_reminder", "Sale reminder", "7 PM")]
NOTES = {"2026-11-26": "Thanksgiving", "2026-11-27": "Black Friday", "2026-11-28": "Small Business Saturday",
         "2026-11-30": "Cyber Monday", "2026-12-04": "Last day of the sale"}
DRIVE = "https://drive.google.com/drive/folders/1thkwBipnUR0XABz6mdxJmZlc8y-afVv-"
# What was checked: only state what the review runs actually did. Optional third argument: a text file to use instead.
CHECKS = (pathlib.Path(sys.argv[3]).read_text().strip() if len(sys.argv) > 3 else
          "Every carousel was reviewed at phone size (390 px wide) for margins, clipping and readable type, "
          "its prices against the formuladynamics.com listing, its car and parts against the source photo, "
          "and every readable number plate was blurred.")

rows = {}
with open(HERE / "ledger" / "FD-BFCM-75 source and fitment ledger.csv") as f:
    for r in csv.DictReader(f): rows[(r["date"], r["slot"])] = r
(OUT / "s").mkdir(parents=True, exist_ok=True)
shutil.copy(HERE / "assets" / "logos" / "fd-icon-white.png", OUT / "fd-icon.png")

days = sorted(p.name for p in (DEL / "exports").iterdir() if p.is_dir())
data, n = [], 0
for d in days:
    dt = datetime.date.fromisoformat(d)
    day = {"id": dt.strftime("%b-%d").lower(), "wd": dt.strftime("%a"), "wdl": dt.strftime("%A"), "md": dt.strftime("%b %-d"),
           "note": NOTES.get(d, ""), "posts": []}
    for s, role, t in SLOTS:
        p = DEL / "exports" / d / s
        if not (p / "03.jpg").exists():
            day["posts"].append(None); continue
        n += 1
        imgs = []
        for k in (1, 2, 3):
            name = f"{d}_{s}_{k}.jpg"
            im = Image.open(p / f"0{k}.jpg").convert("RGB")
            im.resize((540, 675), Image.LANCZOS).save(OUT / "s" / name, quality=82, optimize=True, progressive=True)
            imgs.append("s/" + name)
        r = rows.get((d, s), {})
        day["posts"].append({"n": n, "role": role, "time": t, "imgs": imgs,
                             "concept": r.get("concept", "").strip(),
                             "prices": r.get("prices_shown", "").strip(),
                             "cap": (p / "Caption.txt").read_text().strip() if (p / "Caption.txt").exists() else ""})
    data.append(day)

total = sum(1 for d in data for p in d["posts"] if p)
page = (HERE / "tools" / "page_template.html").read_text()
page = (page.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__TOTAL__", str(total)).replace("__SLIDES__", str(3 * total))
            .replace("__DAYS__", str(len(data))).replace("__DRIVE__", html.escape(DRIVE))
            .replace("__CHECKS__", html.escape(CHECKS)))
(OUT / "index.html").write_text(page)
print(f"{total} carousels, {3*total} slides, {len(data)} days -> {OUT}")
