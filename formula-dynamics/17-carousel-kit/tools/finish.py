#!/usr/bin/env python3
"""Build the review pack from the delivery folder's exports: finish.py [--to DIR]
  <code> contact sheet.jpg  numbered, one row per day, every slide of every carousel
  <code> gallery.html       open in a browser (relative links into exports/)
  <code> review.pdf         a cover with the contact sheet, then one page per carousel: slides, caption, post time"""
import sys, csv, html, argparse, datetime, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import campaign as C
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser(); ap.add_argument("--to"); a = ap.parse_args()
c = C.load(); DEL = C.delivery_dir(c, a.to); CODE = c["code"]
FONTS = C.HERE / "assets" / "fonts"
rows = {}
lp = C.HERE / "ledger" / C.ledger_name(c)
if lp.exists():
    with open(lp, newline="") as f:
        for r in csv.DictReader(f): rows[(r["date"], r["slot"])] = r
days = sorted(p.name for p in (DEL / "exports").iterdir() if p.is_dir() and C.DATE_DIR.match(p.name))
posts, n = [], 0
for d in days:
    for s in c["slots"]:
        p = DEL / "exports" / d / s["id"]
        imgs = sorted(p.glob("[0-9][0-9].jpg"))
        if imgs:
            n += 1
            cap = (p / "Caption.txt").read_text().strip() if (p / "Caption.txt").exists() else ""
            posts.append(dict(n=n, date=d, slot=s["id"], role=s["role"], time=s.get("time", ""), imgs=imgs, cap=cap,
                              concept=rows.get((d, s["id"]), {}).get("concept", "")))
nslides = sum(len(p["imgs"]) for p in posts)
K = max((len(p["imgs"]) for p in posts), default=3)          # widest carousel sets the column width

# contact sheet
TW, TH, G, GAP = 216, 270, 10, 24
bebas = ImageFont.truetype(str(FONTS / "BebasNeue-Regular.ttf"), 34)
mono = ImageFont.truetype(str(FONTS / "IBMPlexMono-Bold.ttf"), 18)
colw = K * TW + (K - 1) * G
W = 160 + len(c["slots"]) * (colw + GAP) + 20
H = 60 + len(days) * (TH + 60) + 20
sheet = Image.new("RGB", (W, H), (8, 8, 10)); dr = ImageDraw.Draw(sheet)
dr.text((20, 14), f"{CODE} CONTACT SHEET  ·  {len(posts)} CAROUSELS  ·  {nslides} SLIDES", font=bebas, fill="white")
for i, d in enumerate(days):
    y = 60 + i * (TH + 60); dt = datetime.date.fromisoformat(d)
    dr.text((20, y + 4), dt.strftime("%a").upper(), font=mono, fill=(154, 154, 162))
    dr.text((20, y + 26), dt.strftime("%b %d").upper(), font=bebas, fill="white")
    for j, s in enumerate(c["slots"]):
        post = next((p for p in posts if p["date"] == d and p["slot"] == s["id"]), None)
        x0 = 160 + j * (colw + GAP)
        if not post:
            dr.rectangle((x0, y + 30, x0 + colw, y + 30 + TH), outline=(60, 60, 66)); continue
        dr.text((x0, y + 4), f"#{post['n']:02d}  {post['role'].upper()}", font=mono, fill=(254, 15, 19))
        for k, f in enumerate(post["imgs"]):
            sheet.paste(Image.open(f).convert("RGB").resize((TW, TH), Image.LANCZOS), (x0 + k * (TW + G), y + 30))
sheet.save(DEL / f"{CODE} contact sheet.jpg", quality=88)

def page(boss):
    font = (FONTS / "BebasNeue-Regular.ttf").as_uri() if boss else "editable%20source/assets/fonts/BebasNeue-Regular.ttf"
    cols = f"repeat({K},1fr) 1.1fr"
    css = f"""@font-face{{font-family:Bebas;src:url({font})}}
body{{margin:0;background:#08080A;color:#fff;font-family:-apple-system,Helvetica,Arial,sans-serif}}
h1,h2{{font-family:Bebas;font-weight:400;letter-spacing:.01em;margin:0}}
.wrap{{padding:32px 40px}} .day{{margin:40px 0 8px;border-top:3px solid #FE0F13;padding-top:12px}}
.post{{display:grid;grid-template-columns:{cols};gap:14px;margin:18px 0 30px;align-items:start}}
.post img{{width:100%;display:block;border-radius:2px}}
.meta{{font-size:15px;line-height:1.45;color:#C9C9D0}} .meta b{{color:#fff}} .tag{{color:#FE0F13;font:700 13px ui-monospace,Menlo,monospace;letter-spacing:.06em}}
.cap{{white-space:pre-wrap;margin-top:10px}}"""
    if boss:
        css += "@page{size:17in 9.6in;margin:0} .bp{page-break-after:always;height:9.6in;box-sizing:border-box;padding:.45in .55in} .post{margin:14px 0 0}"
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(CODE)}</title><style>{css}</style></head><body>"]
    src = (lambda f: f.as_uri()) if boss else (lambda f: f"exports/{f.parent.parent.name}/{f.parent.name}/{f.name}")
    head = (f"<h1 style='font-size:72px'>{html.escape(c.get('title', CODE))} · {C.pl(len(posts), 'carousel')}</h1>"
            f"<p class='meta'>{html.escape(c.get('date_label', ''))} · {C.pl(len(posts), 'carousel')}, {C.pl(nslides, 'slide')} at 1080×1350 · "
            f"times are Pacific · {html.escape(c.get('price_note', 'prices checked against the store listings on the build day'))}.</p>")
    out.append(f"<section class='bp'>{head}<img src='{(DEL / f'{CODE} contact sheet.jpg').as_uri()}' style='width:100%;margin-top:20px'></section>"
               if boss else f"<div class='wrap'>{head}")
    last = None
    for p in posts:
        dt = datetime.date.fromisoformat(p["date"]).strftime("%A %b %d").upper()
        block = (f"<div class='post'>" + "".join(f"<img src='{src(f)}'>" for f in p["imgs"]) +
                 "<span></span>" * (K - len(p["imgs"])) +
                 f"<div class='meta'><div class='tag'>#{p['n']:02d} · {html.escape(p['role'].upper())} · {html.escape(p['time'])}</div>"
                 f"<b>{html.escape(p['concept'])}</b><div class='cap'>{html.escape(p['cap'])}</div></div></div>")
        if boss:
            out.append(f"<section class='bp'><h2 style='font-size:44px'>{dt}</h2>{block}</section>")
        else:
            if p["date"] != last: out.append(f"<h2 class='day' style='font-size:44px'>{dt}</h2>"); last = p["date"]
            out.append(block)
    out.append("" if boss else "</div>")
    out.append("</body></html>")
    return "\n".join(out)

(DEL / f"{CODE} gallery.html").write_text(page(False))
tmp = C.HERE / "out" / "_review.html"; tmp.parent.mkdir(exist_ok=True); tmp.write_text(page(True))
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome"); pg = b.new_page()
    pg.goto(tmp.as_uri()); pg.wait_for_load_state("networkidle")
    pg.pdf(path=str(DEL / f"{CODE} review.pdf"), prefer_css_page_size=True, print_background=True)
    b.close()
print(f"{C.pl(len(posts), 'carousel')}, {C.pl(nslides, 'slide')}; contact sheet, gallery and review PDF in {DEL}")
