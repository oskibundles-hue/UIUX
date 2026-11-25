#!/usr/bin/env python3
"""Save the review page as PDFs for people who won't open the artifact: page_pdf.py PAGE_DIR [--to DIR] [--out FILE] [--no-phone]

Writes two files into the delivery folder (the 00 sorts them to the top of a Drive folder):
  "00 <code> review page.pdf"          the page at full width (1360 px): slides beside the words, for a laptop
  "00 <code> review page - phone.pdf"  the page at phone width (430 px): one slide per row, one carousel per page
Page 1 is the header and the wall of covers, then one page per day (per carousel on the phone), then the footer.
Each page is as tall as what is on it, so nothing sits on a half-empty black page. The covers link to their carousel and every day links back to the
covers, inside the PDF too. Drive and phones open a PDF in their own viewer, where an HTML file would show as code.
Run build_page.py first."""
import re, sys, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import campaign as C
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("page_dir", help="the folder build_page.py wrote (index.html, fd-icon.png, s/)")
ap.add_argument("--to", help="delivery folder for this run (overrides campaign.json)")
ap.add_argument("--out", help="write the full-width PDF here instead; the phone one goes beside it")
ap.add_argument("--no-phone", action="store_true", help="skip the phone-width PDF")
a = ap.parse_args()
src = pathlib.Path(a.page_dir).resolve() / "index.html"
if not src.exists():
    sys.exit(f"{src} not found. Run build_page.py first.")
if a.out:                                     # --out needs no campaign.json, so it also works on an older campaign's page
    out = pathlib.Path(a.out).expanduser()
else:
    c = C.load()
    out = C.delivery_dir(c, a.to) / f"00 {c['code']} review page.pdf"
phone_out = out.with_name(out.stem + " - phone.pdf")

MAX_H = 19000        # a PDF page can't be taller than 200 inches (19200 px); a longer day flows onto a second page
PRINT_CSS = """
.copy,.days{display:none!important}                 /* a button and a sticky day row do nothing on paper */
main{padding-bottom:0!important}
.day{break-before:page}
footer{break-before:page}
.post{break-inside:avoid}
.tile,.tile:hover{transition:none;transform:none}
"""
PHONE_CSS = """
/* one slide per row, full width; the time and the idea sit above the slides, the prices and the caption below */
.post{grid-template-columns:minmax(0,1fr)!important;gap:12px!important}
.meta{display:contents}
.meta .when{order:-3}.meta h3{order:-2;margin:0}.strip{order:-1}
.strip{grid-auto-flow:row!important;grid-template-columns:minmax(0,1fr)!important;grid-auto-columns:auto!important;overflow:visible!important;gap:10px!important}
"""
# give the header, each day (or, on the phone, each carousel) and the footer a named page, and measure each one
NAME_BLOCKS = """(perPost) => {
  const out = []; let i = 0;
  const name = els => { const n = "p" + i++; els.forEach(e => { e.style.page = n; }); };
  const span = (a, b) => Math.ceil(b.getBoundingClientRect().bottom - a.getBoundingClientRect().top);
  const head = document.querySelector("header"); name([head]); out.push(span(head, head));
  for (const d of document.querySelectorAll(".day")) {
    const posts = [...d.querySelectorAll(".post")];
    if (!perPost || !posts.length) { name([d]); out.push(span(d, d)); continue; }
    const day = d.querySelector("h2").childNodes[0].textContent.trim();   // on its own page a carousel names its day
    posts.slice(1).forEach(p => { const w = p.querySelector(".when");
      if (w) w.insertAdjacentHTML("afterbegin", `<span style="color:var(--sub)">${day} · </span>`); });
    const groups = [];                           // a "not built yet" line rides on the page before it
    posts.forEach((p, k) => { if (!k || p.id) groups.push([p]); else groups[groups.length - 1].push(p); });
    groups.forEach((g, k) => {                   // the day's heading shares a page with its first carousel
      const last = g[g.length - 1];
      if (k) { name(g); out.push(span(g[0], last)); } else { name([d.querySelector("h2"), ...g]); out.push(span(d, last)); } });
  }
  const foot = document.querySelector("footer"); name([foot]); out.push(span(foot, foot));
  return out; }"""
WAIT = """async () => {
  const imgs = [...document.images];
  imgs.forEach(i => { i.loading = "eager"; });
  await Promise.race([
    Promise.all(imgs.map(i => (i.complete && i.naturalWidth) ? 0 : new Promise(r => { i.onload = i.onerror = r; }))),
    new Promise(r => setTimeout(r, 60000))]);
  await document.fonts.ready; }"""


def save(browser, width, pad, dest, extra_css="", per_post=False):
    pg = browser.new_page(viewport={"width": width, "height": 1000})
    pg.emulate_media(media="screen")
    pg.goto(src.as_uri(), wait_until="load")
    pg.add_style_tag(content=PRINT_CSS + extra_css)
    pg.evaluate(WAIT)
    bad = pg.evaluate("[...document.images].filter(i => !i.naturalWidth).map(i => i.getAttribute('src'))")
    if bad:
        sys.exit(f"{len(bad)} picture(s) didn't load, first: {bad[0]}. Nothing written.")
    fonts = pg.evaluate("['Bebas Neue','Barlow','IBM Plex Mono'].filter(f => !document.fonts.check('20px \"' + f + '\"'))")
    if fonts:
        print(f"warn: font(s) not loaded, a fallback was used: {', '.join(fonts)} (the page links Google Fonts: offline?)")
    heights = pg.evaluate(NAME_BLOCKS, per_post)
    sizes = [min(h + pad, MAX_H) for h in heights]
    pg.add_style_tag(content="".join(f"@page p{i}{{size:{width}px {h}px;margin:0}}" for i, h in enumerate(sizes)))
    dest.parent.mkdir(parents=True, exist_ok=True)
    # width and height here set the paper Chrome lays the page out on (without them it uses letter width and scales,
    # which reflows the page); the named @page rules then give each page its own height
    pg.pdf(path=str(dest), width=f"{width}px", height=f"{max(sizes)}px", prefer_css_page_size=True,
           print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    pg.close()
    # read the result back: one page per block, each the size it was given
    raw = dest.read_bytes()
    pages = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", raw))
    boxes = {tuple(round(float(v)) for v in m.split()[2:4]) for m in re.findall(rb"/MediaBox\s*\[([^\]]+)\]", raw)}
    long_days = sum(h + pad > MAX_H for h in heights)
    note = f", {long_days} block(s) too tall for one page ran onto a second" if long_days else ""
    if pages != len(sizes) + long_days:
        print(f"warn: {dest.name} has {pages} pages, expected {len(sizes) + long_days}: a block spilled onto an extra page")
    print(f"{dest.name}: {pages} pages ({len(heights) - 2} {'carousels' if per_post else 'days'}, the covers and the footer), {width} px wide, "
          f"{len(boxes)} page sizes{note}, {dest.stat().st_size / 1e6:.1f} MB")
    return pages


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
    save(b, 1360, 48, out)                          # the wrap is 1240 plus the side padding
    if not a.no_phone:
        save(b, 430, 32, phone_out, PHONE_CSS, per_post=True)   # a large phone's width, so the text needs no zoom;
                                                                # a page per carousel, since a phone viewer blurs very tall pages
    b.close()
print(f"in {out.parent}")
