"""
Generate the Supercar Experience ad cues: five angles x three cars.

One table, fifteen cue.json files, same schema build_ad.py reads. Every line
on screen traces to supercarexp.vip (prices, specs, promos, requirements,
locations, the tagline, and the use-cases the site itself names). Nothing is
invented - see _source on each cue.

Angles (each a different reason to book, per the ad-creative brief):
  a-price       the number leads              -> book-now
  b-experience  the tagline / identity        -> reserve-your-ride
  c-occasion    weddings, race week, shoots   -> book-the-weekend
  d-offer       the listed promos             -> third-day-free
  e-engage      4 hours or 24? comments       -> which-one-first
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "99-toolkit"))
import sce_brand as B

HERE = Path(__file__).resolve().parent
SITE = "supercarexp.vip"
DEFAULT_T = 15.0   # plate length; build_ad.py overrides from the plate when present

CARS = {
    # layout is a measured choice, not taste: build the plate, read
    # source/zones.json, and take panel when the bands come back "range too wide".
    "porsche-gt3rs":       dict(name="PORSCHE 911 GT3 RS", year="2025", loc="LAS VEGAS · SCOTTSDALE · BOISE", specs=None,
                                layout="panel"),  # desert highway under open sky: bands swing 18-250
    "mclaren-750s-spider": dict(name="MCLAREN 750S SPIDER", year="2026", loc="LAS VEGAS · SCOTTSDALE",        specs=None,
                                layout="hud"),    # desert road, dark car: mid and CTA bands stay under 140
    "ferrari-tempesta":    dict(name="FERRARI TEMPESTA",    year="2025", loc="LAS VEGAS · SCOTTSDALE",
                                specs="750 HP · 2.7S 0-60 · 205 MPH",
                                layout="hud"),    # desert reel: mid/CTA/lower all under 120
    # Cut from Omarie's own masters, 9 Sept. Layouts set after measuring.
    "ferrari-f8-tributo":  dict(name="FERRARI F8 TRIBUTO",     year="2022", loc="LAS VEGAS · SCOTTSDALE", specs=None,
                                layout="hud"),
    "lamborghini-sto":     dict(name="LAMBORGHINI STO",        year="2023", loc="LAS VEGAS · SCOTTSDALE · BOISE", specs=None,
                                layout="hud"),
    "amg-gt-black-series": dict(name="AMG GT BLACK SERIES",    year="2021", loc="LAS VEGAS · SCOTTSDALE", specs=None,
                                layout="hud"),
    "novitec-urus":        dict(name="LAMBORGHINI NOVITEC URUS", year="2021", loc="LAS VEGAS · SCOTTSDALE", specs=None,
                                layout="hud"),
}

def money(n): return f"${n:,}"

def beats(T):
    # FD proportions from the 14.04s Aventador cue, expressed as offsets from T.
    hud_out = round(T - 5.74, 2)
    return {"title": [0.4, hud_out], "ticker": [0.9, hud_out], "hook": [1.3, 4.0],
            "build": [4.6, hud_out], "cta": [round(T - 4.14, 2), round(T - 2.69, 2)],
            "end": [round(T - 2.44, 2), T]}

def variants(slug):
    c = CARS[slug]; f = B.FLEET[slug]
    p4, p24 = money(f["hr4"]), money(f["hr24"])
    req = ["21+", "LICENSE · INSURANCE"]
    text = ["TO BOOK", f"TEXT {B.PHONE}"]
    spec_row = ["THE CAR", c["specs"]] if c["specs"] else ["THE CAR", f"{c['year']} {c['name']}"]
    return [
        dict(variant="a-price", cta="booking_book-now",
             angle="Price. The number leads; for the viewer who already wants the car and needs the figure.",
             build=f"FROM {p4} / 4 HRS", hook=[f"{p4}.", "FOUR HOURS."],
             heading="THE DEAL",
             rows=[["01", "4 HOURS", p4], ["02", "24 HOURS", p24], ["03", "LOCATION", c["loc"]], ["04", *text]],
             src="Prices, locations and phone from the car page and site footer."),
        dict(variant="b-experience", cta="booking_reserve-your-ride",
             angle="Experience. The site's own tagline; identity over arithmetic.",
             build="A RIDE OF A LIFETIME", hook=["A RIDE OF", "A LIFETIME."],
             heading="WHAT YOU GET",
             rows=[["01", *spec_row], ["02", "4 HRS / 24 HRS", f"{p4} / {p24}"], ["03", *req], ["04", "BOOK", SITE.upper()]],
             src="Tagline verbatim from the homepage; specs from the car page (Tempesta only); requirements from the booking section."),
        dict(variant="c-occasion", cta="booking_book-the-weekend",
             angle="Occasion. The use-cases the site names - weddings, race week, photoshoots.",
             build=c["loc"], hook=["VEGAS THIS WEEKEND?", "ARRIVE IN THIS."],
             heading="MADE FOR",
             rows=[["01", "WEDDINGS", "ARRIVE IN STYLE"], ["02", "RACE WEEK", "F1 WEEK RENTALS"],
                   ["03", "PHOTOSHOOTS", "EDITORIAL · AUTOMOTIVE"], ["04", "FROM", f"{p4} / 4 HRS"]],
             src="Weddings, F1 race week and photoshoot rentals are listed under Services and on the blog."),
        dict(variant="d-offer", cta="offer_third-day-free",
             angle="Offer. The promo exactly as the site prints it.",
             build="3RD DAY FREE", hook=["50% OFF DAY TWO.", "OR DAY THREE FREE."],
             heading="THE OFFER",
             rows=[["01", "DAY ONE", p24], ["02", "DAY TWO", "50% OFF"], ["03", "OR DAY THREE", "FREE"], ["04", "PRICE MATCH", "GUARANTEE"]],
             src='"50% Off 2nd Day or 3rd Day Free" and "Price Match Guarantee" appear on every fleet card.'),
        dict(variant="e-engage", cta="engagement_which-one-first",
             angle="Engagement. A question that earns comments, which earns reach. Not a sales CTA.",
             build="4 HOURS OR 24", hook=["4 HOURS", "OR 24?"],
             heading="YOU PICK",
             rows=[["01", "4 HOURS", p4], ["02", "24 HOURS", p24], ["03", "WHICH ONE?", "COMMENT BELOW"], ["04", *req]],
             src="Both durations and prices from the car page."),
    ]

def make(slug, v, T=DEFAULT_T):
    c = CARS[slug]
    cta = f"cta-captions/cta_9x16_{v['cta']}_bar.png"
    assert (B.OVERLAYS / cta).exists(), cta
    return {
        "_comment": f"Supercar Experience - {c['name']} - variant {v['variant']}. Generated by make_cues.py; edit the table there, not this file.",
        "_source": v["src"],
        "slug": slug,
        "canvas": "9x16", "width": 1080, "height": 1920, "fps": 30, "duration": T,
        "plate": "source/plate-1080x1920.mp4",
        "car": c["name"], "build": v["build"],
        "ticker": [B.BRAND_NAME, c["name"], "LAS VEGAS"],
        "hook": v["hook"],
        "buildHeading": v["heading"], "buildRows": v["rows"],
        "_buildRows_note": "Every line is on supercarexp.vip. No invented figures.",
        "ctaOverlay": cta, "endCard": "end-cards/endcard_9x16_dark.png",
        "beats": beats(T),
        "_beats_note": "HUD clears 1.6s before the ask; CTA never touches the end card; end card is a hard cut.",
        "layout": {"marginLeftFrac": 0.075, "marginRightFrac": 0.16, "bandTopFrac": 0.40},
        "layoutStyle": c["layout"],
        "_layoutStyle_note": "Chosen from source/zones.json, not by eye. panel = a solid card, for footage whose bands swing too far for type on its own.",
        "grade": "eq=contrast=1.04:saturation=0.96:gamma=1.0,vignette=angle=PI/5",
        "variant": v["variant"], "variantAngle": v["angle"],
    }

def main():
    n = 0
    for slug in CARS:
        d = HERE / slug / "variants"; d.mkdir(parents=True, exist_ok=True)
        for v in variants(slug):
            (d / f"cue-{v['variant']}.json").write_text(json.dumps(make(slug, v), indent=2, ensure_ascii=False) + "\n"); n += 1
        # the a-price variant is also the car's base cue.json
        (HERE / slug / "cue.json").write_text(json.dumps(make(slug, variants(slug)[0]), indent=2, ensure_ascii=False) + "\n")
    print(n, "variant cues +", len(CARS), "base cues")

if __name__ == "__main__":
    main()
