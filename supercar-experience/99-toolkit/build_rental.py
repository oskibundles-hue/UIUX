"""
Supercar Experience - rental-specific overlays.

Everything the base kit does not know about: prices as the headline,
booking requirements, the listed promos, the one car with published specs,
the three locations, and the Fall Rally. Every number comes from sce_brand,
which was read off the site. Reuses the shared renderer and the base
builders' chip / lower-third / title styles so it all matches.
"""

from PIL import Image, ImageDraw

import sce_brand as B
import fd_render as R
import build_overlays as O
import fd_hud as H

OUT = B.OVERLAYS / "rental"
LABEL = {slug: label for slug, label, _ in B.SERVICES}
GREY = "#C9C9D0"


def _zones(canvas):
    return B.SAFE_ZONES_9X16 if canvas == "9x16" else {
        "top": 0.05, "bottom": 0.09, "left": 0.05, "right": 0.05}


def _rows(slug):
    f = B.FLEET[slug]
    rows = []
    if f["hr4"]:
        rows.append(("4 HRS", B.price(f["hr4"])))
    rows.append(("24 HRS", B.price(f["hr24"])))
    return rows


# --------------------------------------------------------------------------
# 1. Price stack - the hero. Car name, then the prices large in gold.
# --------------------------------------------------------------------------
def price_stack(canvas, slug):
    fw, fh = B.CANVASES[canvas]
    s = fw / 1080.0
    im = R.frame(canvas)

    kick = R.text(B.BRAND_NAME, round(26 * s), B.GOLD, tracking=0.18)
    title = R.fit_text(LABEL[slug], round(fw * 0.60), round(72 * s),
                       color=B.WHITE, tracking=0.03)
    rows = [(R.text(lab, round(30 * s), GREY, tracking=0.14),
             R.text(val, round(104 * s), B.GOLD, tracking=0.01))
            for lab, val in _rows(slug)]

    pad, bar, gap, lgap = round(36 * s), round(22 * s), round(10 * s), round(18 * s)
    text_w = max([kick.width, title.width] + [v.width + lgap + l.width for l, v in rows])
    panel_w = bar + pad + text_w + pad
    rows_h = sum(max(l.height, v.height) for l, v in rows) + gap * (len(rows) - 1)
    panel_h = pad + kick.height + gap + title.height + round(22 * s) + rows_h + pad

    panel = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 224))
    ImageDraw.Draw(panel).rectangle([0, 0, bar, panel_h], fill=B.rgb(B.GOLD) + (255,))
    x, y = bar + pad, pad
    R.paste(panel, kick, x, y); y += kick.height + gap
    R.paste(panel, title, x, y); y += title.height + round(22 * s)
    for l, v in rows:
        h = max(l.height, v.height)
        R.paste(panel, v, x, y + h, anchor="lb")
        R.paste(panel, l, x + v.width + lgap, y + h - round(10 * s), anchor="lb")
        y += h + gap

    z = _zones(canvas)
    px = round(fw * 0.06)
    py = fh - round(fh * z["bottom"]) - panel_h - round(fh * 0.05)
    R.paste(im, panel, px, py)
    R.paste(im, R.accent_stripe(panel_w, round(9 * s)), px, py + panel_h)
    return im


# --------------------------------------------------------------------------
# 2. Price pills - compact, centred, for over moving footage.
# --------------------------------------------------------------------------
def price_pills(canvas, slug, y_frac=0.66):
    fw, fh = B.CANVASES[canvas]
    s = fw / 1080.0
    im = R.frame(canvas)
    pills = []
    for lab, val in _rows(slug):
        t = R.text(f"{val}   {lab}", round(54 * s), B.BLACK, tracking=0.06)
        pw, ph = t.width + round(60 * s), t.height + round(36 * s)
        p = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        ImageDraw.Draw(p).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=ph // 2,
                                            fill=B.rgb(B.GOLD) + (255,))
        R.paste(p, t, pw // 2, ph // 2, anchor="cm")
        pills.append(R.with_shadow(p))
    gap = round(18 * s)
    total = sum(p.width for p in pills) + gap * (len(pills) - 1)
    x = (fw - total) // 2
    y = round(fh * y_frac)
    for p in pills:
        R.paste(im, p, x, y); x += p.width + gap
    return im


# --------------------------------------------------------------------------
# 3. Requirements chip - sits just above the bottom keep-out.
# --------------------------------------------------------------------------
def requirements(canvas):
    fw, fh = B.CANVASES[canvas]
    s = fw / 1080.0
    im = R.frame(canvas)
    t = R.text("   ·   ".join(B.REQUIREMENTS), round(28 * s), B.WHITE, tracking=0.12)
    pw, ph = t.width + round(48 * s), t.height + round(26 * s)
    p = Image.new("RGBA", (pw, ph), (0, 0, 0, 200))
    ImageDraw.Draw(p).rectangle([0, 0, round(6 * s), ph], fill=B.rgb(B.GOLD) + (255,))
    R.paste(p, t, pw // 2, ph // 2, anchor="cm")
    z = _zones(canvas)
    R.paste(im, p, fw // 2, fh - round(fh * z["bottom"]) - round(fh * 0.02), anchor="cb")
    return im


# --------------------------------------------------------------------------
# 4. Location strip
# --------------------------------------------------------------------------
def locations(canvas):
    fw, fh = B.CANVASES[canvas]
    s = fw / 1080.0
    im = R.frame(canvas)
    t = R.with_shadow(R.text("   ·   ".join(B.LOCATIONS), round(38 * s), B.WHITE, tracking=0.22))
    stripe = R.accent_stripe(round(fw * 0.34), round(8 * s))
    z = _zones(canvas)
    base = fh - round(fh * z["bottom"]) - round(fh * 0.04)
    R.paste(im, stripe, fw // 2, base, anchor="cb")
    R.paste(im, t, fw // 2, base - stripe.height - round(16 * s), anchor="cb")
    return im


# --------------------------------------------------------------------------
# 5. Build
# --------------------------------------------------------------------------
def build():
    n = 0
    # Price stacks: every fleet car on 9x16; the three priority cars on all canvases.
    for slug in B.FLEET:
        canvases = B.CANVASES if slug in B.PRIORITY_SERVICES else ["9x16"]
        for c in canvases:
            R.save(price_stack(c, slug), OUT / "price-stack" / f"price_{c}_{slug}.png"); n += 1
            R.save(price_pills(c, slug), OUT / "price-pills" / f"pills_{c}_{slug}.png"); n += 1

    for c in B.CANVASES:
        R.save(requirements(c), OUT / "requirements" / f"req_{c}.png"); n += 1
        R.save(locations(c), OUT / "locations" / f"loc_{c}.png"); n += 1

    # Promo chips, drop-anywhere, both tones.
    for slug, lead, accent in B.PROMOS:
        for tone in ("dark", "light"):
            R.save(O.badge(f"{lead}  {accent}", tone), OUT / "promo-chips" / f"promo_{slug}-{tone}.png"); n += 1

    # Specs: only the car whose page publishes them.
    f = B.FLEET["ferrari-tempesta"]
    segs = [f"{f['hp']} HP", f"0-60 IN {f['zero60']}S", f"{f['top']} MPH"]
    for c in ("9x16", "16x9"):
        try:
            R.save(H.ticker(c, segs), OUT / "specs" / f"ticker_{c}_ferrari-tempesta.png"); n += 1
        except Exception as e:
            print("  ticker skipped:", e)
    for seg in segs:
        for tone in ("dark", "light"):
            R.save(O.badge(seg, tone), OUT / "specs" / f"chip_{seg.replace(' ', '-').lower()}-{tone}.png"); n += 1

    # Fall Rally plate.
    for c in ("9x16", "16x9"):
        R.save(O.lower_third(c, B.RALLY["name"],
                             f"{B.RALLY['dates']}   ·   CODE {B.RALLY['code']}   ·   ${B.RALLY['off']} OFF",
                             "2027 SUPERCAR EXPERIENCE"),
               OUT / "rally" / f"rally_{c}.png"); n += 1
    return n


if __name__ == "__main__":
    print(build(), "rental overlays")
