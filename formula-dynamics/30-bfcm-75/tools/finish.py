#!/usr/bin/env python3
"""Build the review pack from the Drive delivery folder's exports:
  - FD-BFCM-75 contact sheet.jpg  (numbered, one row per day, 5 carousels x 3 slides)
  - FD-BFCM-75 gallery.html       (open in a browser; relative links to exports/)
  - FD-BFCM-75 boss review.pdf    (cover + one page per carousel: 3 slides, caption, schedule)
Usage: finish.py DELIVERY_DIR"""
import sys, csv, html, pathlib, datetime
from PIL import Image, ImageDraw, ImageFont

DEL = pathlib.Path(sys.argv[1])
HERE = pathlib.Path(__file__).resolve().parent.parent
FONTS = HERE / "assets" / "fonts"
SLOTS = [("1_products", "Product spotlight", "9:00 AM"), ("2_sale", "Sale guide", "11:00 AM"),
         ("3_cars", "Car with product", "1:00 PM"), ("4_education", "Education", "4:00 PM"),
         ("5_reminder", "Sale reminder", "7:00 PM")]
rows = {}
with open(HERE / "ledger" / "FD-BFCM-75 source and fitment ledger.csv") as f:
    for r in csv.DictReader(f): rows[(r["date"], r["slot"])] = r
days = sorted(p.name for p in (DEL / "exports").iterdir() if p.is_dir())
posts = []
n = 0
for d in days:
    for s, role, t in SLOTS:
        p = DEL / "exports" / d / s
        if (p / "03.jpg").exists():
            n += 1
            cap = (p / "Caption.txt").read_text().strip() if (p / "Caption.txt").exists() else ""
            posts.append(dict(n=n, date=d, slot=s, role=role, time=t, dir=p, cap=cap,
                              concept=rows.get((d, s), {}).get("concept", "")))

# contact sheet
TW, TH, G = 216, 270, 10
bebas = ImageFont.truetype(str(FONTS / "BebasNeue-Regular.ttf"), 34)
mono = ImageFont.truetype(str(FONTS / "IBMPlexMono-Bold.ttf"), 18)
cols = 5 * 3
W = 160 + cols * TW + (cols - 1) * G + 4 * 24 + 40
H = 60 + len(days) * (TH + 60) + 20
sheet = Image.new("RGB", (W, H), (8, 8, 10)); dr = ImageDraw.Draw(sheet)
dr.text((20, 14), f"FD-BFCM-75 CONTACT SHEET  ·  {len(posts)} CAROUSELS  ·  {3*len(posts)} SLIDES", font=bebas, fill="white")
for i, d in enumerate(days):
    y = 60 + i * (TH + 60)
    dt = datetime.date.fromisoformat(d)
    dr.text((20, y + 4), dt.strftime("%a").upper(), font=mono, fill=(154, 154, 162))
    dr.text((20, y + 26), dt.strftime("%b %d").upper(), font=bebas, fill="white")
    for j, (s, role, _) in enumerate(SLOTS):
        post = next((p for p in posts if p["date"] == d and p["slot"] == s), None)
        x0 = 160 + j * (3 * TW + 2 * G + 24)
        if not post:
            dr.rectangle((x0, y + 30, x0 + 3 * TW + 2 * G, y + 30 + TH), outline=(60, 60, 66)); continue
        dr.text((x0, y + 4), f"#{post['n']:02d}  {role.upper()}", font=mono, fill=(254, 15, 19))
        for k in range(3):
            im = Image.open(post["dir"] / f"0{k+1}.jpg").convert("RGB").resize((TW, TH), Image.LANCZOS)
            sheet.paste(im, (x0 + k * (TW + G), y + 30))
sheet.save(DEL / "FD-BFCM-75 contact sheet.jpg", quality=88)

# gallery + boss pages share one HTML builder
def page(boss: bool) -> str:
    font = (FONTS / "BebasNeue-Regular.ttf").as_uri() if boss else ""
    css = f"""
@font-face{{font-family:Bebas;src:url({font or 'editable%20source/assets/fonts/BebasNeue-Regular.ttf'})}}
body{{margin:0;background:#08080A;color:#fff;font-family:-apple-system,Helvetica,Arial,sans-serif}}
h1,h2{{font-family:Bebas;font-weight:400;letter-spacing:.01em;margin:0}}
.wrap{{padding:32px 40px}} .day{{margin:40px 0 8px;border-top:3px solid #FE0F13;padding-top:12px}}
.post{{display:grid;grid-template-columns:repeat(3,1fr) 1.1fr;gap:14px;margin:18px 0 30px;align-items:start}}
.post img{{width:100%;display:block;border-radius:2px}}
.meta{{font-size:15px;line-height:1.45;color:#C9C9D0}} .meta b{{color:#fff}} .tag{{color:#FE0F13;font:700 13px ui-monospace,Menlo,monospace;letter-spacing:.06em}}
.cap{{white-space:pre-wrap;margin-top:10px}}
"""
    if boss:
        css += "@page{size:17in 9.6in;margin:0} .bp{page-break-after:always;height:9.6in;box-sizing:border-box;padding:.45in .55in} .post{margin:14px 0 0}"
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>FD-BFCM-75</title><style>{css}</style></head><body>"]
    src = (lambda p, k: (p['dir'] / f'0{k}.jpg').as_uri()) if boss else (lambda p, k: f"exports/{p['date']}/{p['slot']}/0{k}.jpg")
    head = (f"<h1 style='font-size:72px'>Formula Dynamics Black Friday · 75 carousels</h1>"
            f"<p class='meta'>Nov 20 – Dec 4, 2026 · {len(posts)} carousels, {3*len(posts)} slides at 1080×1350 · "
            f"times are Pacific · prices checked against the formuladynamics.com listings on the build day.</p>")
    if boss:
        out.append(f"<section class='bp'>{head}<img src='{(DEL / 'FD-BFCM-75 contact sheet.jpg').as_uri()}' style='width:100%;margin-top:20px'></section>")
    else:
        out.append(f"<div class='wrap'>{head}")
    last = None
    for p in posts:
        dt = datetime.date.fromisoformat(p["date"]).strftime("%A %b %d").upper()
        block = (f"<div class='post'>" + "".join(f"<img src='{src(p, k)}'>" for k in (1, 2, 3)) +
                 f"<div class='meta'><div class='tag'>#{p['n']:02d} · {p['role'].upper()} · {p['time']}</div>"
                 f"<b>{html.escape(p['concept'])}</b><div class='cap'>{html.escape(p['cap'])}</div></div></div>")
        if boss:
            out.append(f"<section class='bp'><h2 style='font-size:44px'>{dt}</h2>{block}</section>")
        else:
            if p["date"] != last: out.append(f"<h2 class='day' style='font-size:44px'>{dt}</h2>"); last = p["date"]
            out.append(block)
    out.append("" if boss else "</div>")
    out.append("</body></html>")
    return "\n".join(out)

(DEL / "FD-BFCM-75 gallery.html").write_text(page(False))
tmp = HERE / "out" / "_boss.html"; tmp.parent.mkdir(exist_ok=True); tmp.write_text(page(True))
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome"); pg = b.new_page()
    pg.goto(tmp.as_uri()); pg.wait_for_load_state("networkidle")
    pg.pdf(path=str(DEL / "FD-BFCM-75 boss review.pdf"), prefer_css_page_size=True, print_background=True)
    b.close()
print(f"{len(posts)} carousels, {3*len(posts)} slides; contact sheet, gallery, boss PDF written")
