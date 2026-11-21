#!/usr/bin/env python3
"""Check carousels against the house rules before anyone looks at them.

Usage: lint.py source/<date>/<slot> [more carousel folders]   or   lint.py --all [--dates d1,d2]
Exit 1 if any FAIL. WARN lines are for a human to look at; they don't block delivery.

Measured in the real browser at 1080x1350, per slide:
  FAIL  ink outside the safe area (72 px sides, 64 px top and bottom), measured on the glyphs, not the text box.
        Exempt: pins and markers on the part (.pin or data-free) and 1-2 character graphic glyphs 200 px and up
  FAIL  text smaller than 21 px
  FAIL  text cut off by a box that hides overflow
  FAIL  the ink of two different text elements overlapping
  FAIL  a broken image, the kit's placeholder photo, or leftover [[placeholder]] text
  FAIL  more than one FD mark (anything from assets/logos/), WARN for none
  FAIL  a font file that didn't load
  FAIL  the running counter (01 / 03) not matching the slide's place in the carousel
  FAIL  a never_print word from campaign.json (on a slide or in the caption)
  WARN  a photo blown up more than 1.25x (it will look soft)
Per carousel: Caption.txt missing or still holding [[placeholder]] text (FAIL), outside 40-90 words, hashtags or emoji (WARN); every $ figure on the
slides and in the caption is matched against the saved store listings (ref/store/*.json, Shopify products.json):
a figure that is no listing's price, compare-at price or saving is listed as WARN to check by hand (sums are fine,
but someone has to add them up)."""
import sys, re, json, glob, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import campaign as C

JS = r"""
(cfg) => {
  const F = [], Wn = [];
  const SX = 72, SY = 64, W = 1080, H = 1350;
  const runs = [];
  // Ink, not the text box: a font's box runs well above the capitals and below the baseline, so measure the real
  // glyph extents with canvas (same loaded fonts) and check those. Falls back to the box when the two disagree.
  const cv = document.createElement('canvas').getContext('2d');
  const tf = {uppercase: x => x.toUpperCase(), lowercase: x => x.toLowerCase(), capitalize: x => x.replace(/\b\w/g, c => c.toUpperCase())};
  const inkOf = (el, cs, raw, rects) => {
    cv.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    cv.letterSpacing = cs.letterSpacing === 'normal' ? '0px' : cs.letterSpacing;
    const txt = (tf[cs.textTransform] || (x => x))(raw);
    const m = cv.measureText(txt), fa = m.fontBoundingBoxAscent, fd = m.fontBoundingBoxDescent;
    return rects.map(q => {
      const k = (q.bottom - q.top) / (fa + fd || 1);                  // box taller than the font says: scale
      const one = rects.length === 1 && Math.abs((q.right - q.left) - m.width) < 2;
      return {left: one ? q.left - m.actualBoundingBoxLeft : q.left, right: one ? q.left + m.actualBoundingBoxRight : q.right,
              top: q.top + (fa - m.actualBoundingBoxAscent) * k, bottom: q.top + (fa + m.actualBoundingBoxDescent) * k};
    });
  };
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (tw.nextNode()) {
    const t = tw.currentNode, s = t.textContent.replace(/\s+/g, ' ').trim();
    if (!s) continue;
    const el = t.parentElement, cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    let op = 1; for (let a = el; a; a = a.parentElement) op *= +getComputedStyle(a).opacity;
    if (op < 0.05) continue;
    const r = document.createRange(); r.selectNodeContents(t);
    const rects = [...r.getClientRects()].filter(q => q.width > .5 && q.height > .5);
    if (!rects.length) continue;
    const fs = parseFloat(cs.fontSize);
    // free: a pin or marker sitting on the part in the photo (.pin, or anything marked data-free), or a one- or
    // two-character graphic glyph 200 px and up. These may cross the margin on purpose; everything else may not.
    const free = !!el.closest('.pin, [data-free]') || (s.length <= 2 && fs >= 200);
    runs.push({el, s: s.slice(0, 40), rects, ink: inkOf(el, cs, s, rects), fs, fam: cs.fontFamily, free});
  }
  for (const u of runs) {
    if (u.fs < 20.5) F.push(`text ${u.fs}px, under 21px: "${u.s}"`);
    if (!u.free) for (const q of u.ink) {
      const over = [SX - q.left, q.right - (W - SX), SY - q.top, q.bottom - (H - SY)].map(v => Math.round(v));
      if (Math.max(...over) > 1) F.push(`ink outside the safe area by ${Math.max(...over)}px: "${u.s}"`);
    }
    for (let a = u.el; a && a !== document.body && !u.free; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.overflow === 'visible' && cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
      const b = a.getBoundingClientRect();
      if (u.ink.some(q => q.left < b.left - 1 || q.right > b.right + 1 || q.top < b.top - 1 || q.bottom > b.bottom + 1))
        { F.push(`cut off by its box: "${u.s}"`); break; }
    }
  }
  for (let i = 0; i < runs.length; i++) for (let j = i + 1; j < runs.length; j++) {
    const a = runs[i], b = runs[j];
    if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
    for (const p of a.ink) for (const q of b.ink) {
      const w = Math.min(p.right, q.right) - Math.max(p.left, q.left), h = Math.min(p.bottom, q.bottom) - Math.max(p.top, q.top);
      if (w > 1 && h > 1) { F.push(`text overlaps: "${a.s}" / "${b.s}"`); break; }
    }
  }
  const imgs = [...document.images];
  let marks = 0;
  for (const im of imgs) {
    const src = im.getAttribute('src') || '';
    if (/\/logos\//.test(src)) { marks++; }
    if (!im.complete || !im.naturalWidth) { F.push(`broken image: ${src}`); continue; }
    if (/_placeholder/.test(src)) F.push(`kit placeholder photo still in place: ${src}`);
    if (/\/logos\//.test(src)) continue;
    const r = im.getBoundingClientRect();
    const k = Math.max(r.width / im.naturalWidth, r.height / im.naturalHeight);
    if (k > 1.25) Wn.push(`photo blown up ${k.toFixed(2)}x, may look soft: ${src.split('/').pop()}`);
  }
  if (marks > 1) F.push(`${marks} FD marks on one slide (one only)`);
  if (marks === 0) Wn.push('no FD mark on this slide');
  const txt = document.body.innerText;
  if (/\[\[/.test(txt)) F.push('placeholder [[...]] text left in');
  for (const w of cfg.never) {
    const re = new RegExp('(^|[^A-Za-z0-9])' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '($|[^A-Za-z0-9])', 'i');
    if (re.test(txt)) F.push(`never-print word on slide: "${w}"`);
  }
  const fams = new Set(runs.map(u => u.fam.split(',')[0].replace(/["']/g, '').trim()));
  for (const fam of fams) {
    const faces = [...document.fonts].filter(f => f.family.replace(/["']/g, '') === fam);
    if (faces.length && faces.every(f => f.status === 'error')) F.push(`font file failed to load: ${fam}`);
  }
  const cnt = document.querySelector('.run .count, .count');
  const m = cnt && cnt.innerText.match(/(\d+)\s*\/\s*(\d+)/);
  if (cfg.idx && !m) Wn.push('no running counter (0N / 0M) found');
  if (m && (+m[1] !== cfg.idx || +m[2] !== cfg.total)) F.push(`counter says ${m[1]} / ${m[2]}, slide is ${cfg.idx} of ${cfg.total}`);
  return {F, Wn, money: txt.match(/\$\s?\d[\d,]*(\.\d{2})?/g) || []};
}
"""


def store_amounts(c):
    """Every listing price, compare-at price and saving in the saved store files, in cents."""
    known = set()
    for fp in glob.glob(str(C.HERE / c.get("store_json", "ref/store/*.json"))):
        try:
            data = json.load(open(fp))
        except Exception:
            continue
        for p in data.get("products", []):
            for v in p.get("variants", []):
                pr = round(float(v.get("price") or 0) * 100)
                ca = round(float(v.get("compare_at_price") or 0) * 100)
                known.update(x for x in (pr, ca, ca - pr if ca > pr else 0) if x > 0)
    return known


def cents(s):
    s = s.replace("$", "").replace(",", "").strip()
    return round(float(s) * 100), "." in s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carousels", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dates", default="")
    a = ap.parse_args()
    c = C.load()
    dirs = ([pathlib.Path(x).resolve() for x in a.carousels] if a.carousels else
            C.carousels(c, set(filter(None, a.dates.split(",")))) if a.all else [])
    if not dirs:
        ap.error("name carousel folders, or --all")
    known = store_amounts(c)
    never = [w for w in c["never_print"] if w]
    from playwright.sync_api import sync_playwright
    nfail = nwarn = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for d in dirs:
            key = f"{d.parent.name}/{d.name}"
            fails, warns, money = [], [], []
            slides = C.slides_of(d)
            for i, f in enumerate(slides, 1):
                pg.goto(f.as_uri()); pg.wait_for_load_state("networkidle"); pg.evaluate("document.fonts.ready")
                r = pg.evaluate(JS, {"idx": i, "total": len(slides), "never": never})
                fails += [f"slide {i:02d}: {x}" for x in dict.fromkeys(r["F"])]
                warns += [f"slide {i:02d}: {x}" for x in dict.fromkeys(r["Wn"])]
                money += r["money"]
            cap = d / "Caption.txt"
            if not cap.exists():
                fails.append("Caption.txt missing")
            else:
                t = cap.read_text()
                if "[[" in t or "]]" in t:
                    fails.append("caption still has [[placeholder]] text")
                n = len(t.split())
                if not 40 <= n <= 90: warns.append(f"caption is {n} words (house range 40-90)")
                if "#" in t: warns.append("caption has a hashtag")
                if re.search("[\U0001F300-\U0001FAFF☀-➿]", t): warns.append("caption has an emoji")
                for w in never:
                    if re.search(r"(^|[^A-Za-z0-9])" + re.escape(w) + r"($|[^A-Za-z0-9])", t, re.I):
                        fails.append(f"never-print word in caption: \"{w}\"")
                money += re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", t)
            if known:
                odd = []
                for s in dict.fromkeys(money):
                    v, has_cents = cents(s)
                    if v in known or (not has_cents and any(abs(k - v) < 100 for k in known)): continue
                    odd.append(s)
                if odd: warns.append("$ figures that are no listing price, was-price or saving (check the sum by hand): " + ", ".join(odd))
            elif money:
                warns.append("no saved store listings (ref/store/*.json), so prices were not matched")
            nfail += len(fails); nwarn += len(warns)
            print(f"{'FAIL' if fails else 'ok  '} {key}  ({len(slides)} slides)")
            for x in fails: print("   FAIL", x)
            for x in warns: print("   warn", x)
        b.close()
    print(f"{len(dirs)} carousel(s): {nfail} fail, {nwarn} warn")
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
