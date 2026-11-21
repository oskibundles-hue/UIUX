#!/usr/bin/env python3
"""Build the private review page (a claude.ai artifact) from the delivery folder: build_page.py OUT_DIR [checks.txt] [--to DIR]
Writes OUT_DIR/index.html, OUT_DIR/fd-icon.png and OUT_DIR/s/<date>_<slot>_<n>.jpg (540 px wide, q82).
Publish OUT_DIR with the artifacts publish_files tool (index.html, fd-icon.png, every s/*.jpg). It starts private.
Words on the page come from campaign.json "page" (h1, lede, hot figure, warning); {carousels}, {slides} and {days} in
the h1 or lede become the real counts ("75 carousels"). checks.txt (keep it in the campaign folder) replaces the
"what was checked" line: say only what the review really did. tools/page_pdf.py turns the page into a PDF afterwards."""
import sys, csv, json, html, argparse, datetime, shutil, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import campaign as C
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("checks", nargs="?"); ap.add_argument("--to")
a = ap.parse_args()
c = C.load(); DEL = C.delivery_dir(c, a.to); OUT = pathlib.Path(a.out); P = c.get("page", {})
CHECKS = (pathlib.Path(a.checks).read_text().strip() if a.checks else
          "Every carousel passed the kit's rule check (safe margins, type sizes, overlaps, one FD mark, banned words) "
          "and was looked at phone size; every price was matched to the saved store listing named in the ledger.")
rows = {}
lp = C.HERE / "ledger" / C.ledger_name(c)
if lp.exists():
    with open(lp, newline="") as f:
        for r in csv.DictReader(f): rows[(r["date"], r["slot"])] = r
(OUT / "s").mkdir(parents=True, exist_ok=True)
shutil.copy(C.HERE / "assets" / "logos" / "fd-icon-white.png", OUT / "fd-icon.png")

data, n, nsl = [], 0, 0
for d in sorted(p.name for p in (DEL / "exports").iterdir() if p.is_dir() and C.DATE_DIR.match(p.name)):
    dt = datetime.date.fromisoformat(d)
    day = {"id": dt.strftime("%b-%d").lower(), "wd": dt.strftime("%a"), "wdl": dt.strftime("%A"), "md": dt.strftime("%b %-d"),
           "note": c["notes"].get(d, ""), "posts": []}
    for s in c["slots"]:
        p = DEL / "exports" / d / s["id"]
        files = sorted(p.glob("[0-9][0-9].jpg"))
        if not files:
            day["posts"].append(None); continue
        n += 1; nsl += len(files); imgs = []
        for k, f in enumerate(files, 1):
            name = f"{d}_{s['id']}_{k}.jpg"
            Image.open(f).convert("RGB").resize((540, 675), Image.LANCZOS).save(OUT / "s" / name, quality=82, optimize=True, progressive=True)
            imgs.append("s/" + name)
        r = rows.get((d, s["id"]), {})
        day["posts"].append({"n": n, "role": s["role"], "time": s.get("time", ""), "imgs": imgs,
                             "concept": r.get("concept", "").strip(), "prices": r.get("prices_shown", "").strip(),
                             "cap": (p / "Caption.txt").read_text().strip() if (p / "Caption.txt").exists() else ""})
    data.append(day)

drive = c.get("drive_link", "")
files_p = (f"The 1080 × 1350 exports, {'the caption' if n == 1 else f'the {n} captions'}, the editable source, the source and "
           f"fitment ledger, the contact sheet, the review PDF and PDFs of this page (one for a laptop, one for a phone) are in the " + (f'<a href="{html.escape(drive)}">delivery folder</a>' if drive else "delivery folder") +
           ". The pictures on this page are reduced previews.")
hot = P.get("hot_figure")
counts = {"{carousels}": C.pl(n, "carousel"), "{slides}": C.pl(nsl, "slide"), "{days}": C.pl(len(data), "day")}
def words(s):
    for k, v in counts.items(): s = s.replace(k, v)
    return s
page = (C.HERE / "tools" / "page_template.html").read_text()
for k, v in {
    "__DATA__": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
    "__ROLES__": json.dumps([[s["role"], s.get("time", "")] for s in c["slots"]]),
    "__PAGE_TITLE__": html.escape(P.get("title", c.get("title", c["code"]))),
    "__H1__": html.escape(words(P.get("h1", f"{c.get('title', c['code'])}: {{carousels}}"))),
    "__LEDE__": html.escape(words(P.get("lede", ""))),
    "__HOTFIG__": f'<li class="hot"><b>{html.escape(hot[0])}</b>{html.escape(hot[1])}</li>' if hot and hot[0] else "",
    "__TOTAL__": str(n), "__SLIDES__": str(nsl), "__DAYS__": str(len(data)),
    "__TOTAL_W__": "carousel" if n == 1 else "carousels", "__SLIDES_W__": "slide" if nsl == 1 else "slides",
    "__DAYS_W__": "day" if len(data) == 1 else "days",
    "__FILES__": files_p, "__CHECKS__": html.escape(CHECKS),
    "__WARN__": f'  <p class="warn">{html.escape(P["warning"])}</p>\n' if P.get("warning") else "",
}.items():
    page = page.replace(k, v)
assert "__" not in page.replace("__proto__", ""), "a placeholder was left in the page"
(OUT / "index.html").write_text(page)
print(f"{C.pl(n, 'carousel')}, {C.pl(nsl, 'slide')}, {C.pl(len(data), 'day')} -> {OUT}")
