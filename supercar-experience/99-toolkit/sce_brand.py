"""
Supercar Experience - single source of truth.

Sibling of formula-dynamics/99-toolkit/fd_brand.py, kept to the same constant
names so the shared toolkit runs unmodified. Change values HERE and re-run
build_all.py - never edit a generated file.

Every price, spec, location and requirement below was read off
supercarexp.vip on 2026-09-09. Only put on screen what the site substantiates.
"""

from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
BRAND_CORE = KIT / "01-brand-core"
LOGOS = KIT / "02-logos"
# Logo stems, so a layout never hard-codes another brand's filename.
MARK_WHITE = "sce-icon-mark-only--white"
MARK_BLACK = "sce-icon-mark-only--black"
MARK_GOLD = "sce-icon-mark-only--gold"
LOCKUP_WHITE = "sce-primary-horizontal--white"
OVERLAYS = KIT / "03-overlays"
TEMPLATES = KIT / "04-templates"
FONTS = KIT / "07-fonts"

# Display face. The toolkit's sizes are tuned for a condensed font; the wide
# look comes from the wordmark itself. Michroma (OFL) is bundled as the accent
# face for a later pass. Name kept for toolkit compatibility.
FONT_BEBAS = FONTS / "BebasNeue-Regular.ttf"
FONT_ACCENT = FONTS / "Michroma-Regular.ttf"

# --------------------------------------------------------------------------
# Colour
# --------------------------------------------------------------------------
# The brand is black and white. The one accent is the gold Omarie already
# uses for highlights in his approved reel recipe (#FBD101), so it stays
# consistent across his content rather than inventing a second colour.
# The toolkit reads the accent as B.RED - the name is historical.
GOLD = "#FBD101"
RED = GOLD
ACCENT = GOLD
WHITE = "#FFFFFF"
BLACK = "#000000"
GREEN = "#FFFFFF"     # guide/stripe slot in the toolkit; SCE has no green
YELLOW = GOLD

PALETTE = [
    # name,   hex,   role
    ("gold", GOLD, "Single accent. Prices, CTAs, key words, rules, the stripe."),
    ("white", WHITE, "Primary logo + headline colour on dark footage."),
    ("black", BLACK, "Primary background. Logo colour on light footage."),
]

HEX = {n: h for n, h, _ in PALETTE}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# Accent rule under lower thirds and on the end card. Two segments so it
# reads as a designed stripe rather than a plain bar; shares must sum to 1.0.
ACCENT_STRIPE = [
    (GOLD, 0.78),
    (WHITE, 0.22),
]
assert abs(sum(s for _, s in ACCENT_STRIPE) - 1.0) < 1e-6

# --------------------------------------------------------------------------
# Type
# --------------------------------------------------------------------------
TYPE_PRIMARY = "Bebas Neue"      # headlines - bundled, OFL
TYPE_ACCENT = "Michroma"         # accent / kickers - bundled, OFL

# --------------------------------------------------------------------------
# Canvases and platform keep-out zones
# --------------------------------------------------------------------------
CANVASES = {
    "9x16": (1080, 1920),   # TikTok / Reels / Shorts - primary
    "4x5":  (1080, 1350),
    "1x1":  (1080, 1080),
    "16x9": (1920, 1080),
}

SAFE_ZONES_9X16 = {
    "top": 0.11,
    "bottom": 0.20,
    "right": 0.16,
    "left": 0.05,
}

# --------------------------------------------------------------------------
# Fleet  (the toolkit calls these SERVICES; here a "service" is a car)
# --------------------------------------------------------------------------
# The first three are the cars with footage in Dropbox, named as the site
# lists them. Everything else is the listed fleet with listed prices, so a
# lower third exists for any car Omarie films next. Diacritics dropped for
# the bundled font.
#
# (slug, LABEL, description)
SERVICES = [
    ("porsche-gt3rs", "PORSCHE 911 GT3 RS", "2025 - Exotic - Las Vegas, Scottsdale, Boise"),
    ("mclaren-750s-spider", "MCLAREN 750S SPIDER", "2026 - Exotic - Las Vegas, Scottsdale"),
    ("ferrari-tempesta", "FERRARI TEMPESTA", "2025 - Exotic - Las Vegas, Scottsdale - 750 hp, 0-60 in 2.7s"),
    ("lamborghini-sto", "LAMBORGHINI HURACAN STO", "2023 - Exotic - Las Vegas"),
    ("ferrari-f8-tributo", "FERRARI F8 TRIBUTO", "2022 - Exotic - Las Vegas"),
    ("mansory-urus", "LAMBORGHINI MANSORY URUS", "2025 - Wide body - Las Vegas"),
    ("amg-gt-black-series", "MERCEDES-AMG GT BLACK SERIES", "2021 - Exotic - Las Vegas"),
    ("huracan-evo-spyder-2021", "LAMBORGHINI HURACAN EVO SPYDER", "2021 - Exotic - Las Vegas"),
    ("huracan-evo-spyder-2020", "LAMBORGHINI HURACAN EVO SPYDER", "2020 - Exotic - Las Vegas"),
    ("sce-rally", "SUPERCAR EXPERIENCE RALLY", "2027 - Fall Rally Nov 13-16, 2026"),
    ("rolls-royce-cullinan", "ROLLS-ROYCE CULLINAN", "2024 - Luxury - Las Vegas"),
    ("cullinan-black-badge", "ROLLS-ROYCE CULLINAN BLACK BADGE", "2024 - Luxury - Las Vegas"),
    ("novitec-urus", "LAMBORGHINI NOVITEC URUS", "2021 - Wide body - Las Vegas"),
    ("porsche-911-pure-800", "PORSCHE 911 PURE 800", "2024 - Luxury - Las Vegas"),
    ("lamborghini-urus", "LAMBORGHINI URUS", "2022 - Luxury - Las Vegas"),
    ("g63-4x4-squared", "MERCEDES G63 4X4 SQUARED", "2023 - Luxury - Las Vegas"),
    ("brabus-g63", "BRABUS G63", "2025 - Luxury - Las Vegas"),
    ("gls600-maybach", "MERCEDES GLS600 MAYBACH", "2024 - Luxury - Las Vegas"),
]

# Numeric prices, for the rental builders and the ad cue files.
# hr4 None = the site lists a day rate only.
FLEET = {
    "porsche-gt3rs":          dict(year=2025, cat="EXOTIC", hr4=1299, hr24=1799, hp=None,
                                   url="/cars/2025-porsche-gt3rs-las-vegas"),
    "mclaren-750s-spider":    dict(year=2026, cat="EXOTIC", hr4=1299, hr24=1799, hp=None,
                                   url="/cars/2026-mclaren-750s-spider-las-vegas"),
    "ferrari-tempesta":       dict(year=2025, cat="EXOTIC", hr4=849,  hr24=1199, hp=750,
                                   zero60="2.7", top="205", engine="3.0L TWIN-TURBO V6 HYBRID",
                                   url="/cars/2023-ferrari-tempesta-las-vegas"),
    "lamborghini-sto":        dict(year=2023, cat="EXOTIC", hr4=999,  hr24=1599),
    "ferrari-f8-tributo":     dict(year=2022, cat="EXOTIC", hr4=999,  hr24=1599),
    "mansory-urus":           dict(year=2025, cat="EXOTIC", hr4=999,  hr24=1399),
    "amg-gt-black-series":    dict(year=2021, cat="EXOTIC", hr4=899,  hr24=1299),
    "huracan-evo-spyder-2021": dict(year=2021, cat="EXOTIC", hr4=899, hr24=1299),
    "huracan-evo-spyder-2020": dict(year=2020, cat="EXOTIC", hr4=899, hr24=1299),
    "sce-rally":              dict(year=2027, cat="EXOTIC", hr4=None, hr24=2999),
    "rolls-royce-cullinan":   dict(year=2024, cat="LUXURY", hr4=899,  hr24=1199),
    "cullinan-black-badge":   dict(year=2024, cat="LUXURY", hr4=899,  hr24=1199),
    "novitec-urus":           dict(year=2021, cat="LUXURY", hr4=699,  hr24=949),
    "porsche-911-pure-800":   dict(year=2024, cat="LUXURY", hr4=599,  hr24=849),
    "lamborghini-urus":       dict(year=2022, cat="LUXURY", hr4=599,  hr24=849),
    "g63-4x4-squared":        dict(year=2023, cat="LUXURY", hr4=599,  hr24=799),
    "brabus-g63":             dict(year=2025, cat="LUXURY", hr4=499,  hr24=699),
    "gls600-maybach":         dict(year=2024, cat="LUXURY", hr4=449,  hr24=649),
}


def price(n):
    return f"${n:,}"


def price_line(slug):
    """'$1,299 / 4 HRS  -  $1,799 / 24 HRS', or the day rate alone."""
    f = FLEET[slug]
    if f["hr4"] is None:
        return f"{price(f['hr24'])} / 24 HRS"
    return f"{price(f['hr4'])} / 4 HRS   -   {price(f['hr24'])} / 24 HRS"


# Subline under each car's lower third = its listed price.
SERVICE_SUBLINE = {slug: price_line(slug) for slug in FLEET}

# Badges are built for these. The three with footage.
PRIORITY_SERVICES = ["porsche-gt3rs", "mclaren-750s-spider", "ferrari-tempesta"]

# --------------------------------------------------------------------------
# Locations  (the toolkit calls these PARTNERS; they get a plate lower third)
# --------------------------------------------------------------------------
# (slug, LABEL, prose, category)
PARTNERS = [
    ("las-vegas", "LAS VEGAS", "Las Vegas, Nevada", "NEVADA"),
    ("scottsdale", "SCOTTSDALE", "Scottsdale, Arizona", "ARIZONA"),
    ("boise", "BOISE", "Boise, Idaho", "IDAHO"),
]
LOCATIONS = [p[1] for p in PARTNERS]

# --------------------------------------------------------------------------
# Booking facts  (all from the site)
# --------------------------------------------------------------------------
REQUIREMENTS = ["21+", "VALID DRIVER'S LICENSE", "MATCHING INSURANCE"]
PROMOS = [
    ("second-day-half", "50% OFF", "2ND DAY"),
    ("third-day-free", "3RD DAY", "FREE"),
    ("two-exotic-two-luxury", "2 EXOTIC DAYS", "2 LUXURY DAYS FREE"),
    ("price-match", "PRICE MATCH", "GUARANTEE"),
    ("rally500", "CODE RALLY500", "$500 OFF THE RALLY"),
]
# Fall Rally - every figure read off supercarexp.vip/rally on 2026-09-09.
RALLY = dict(
    name="FALL RALLY", year="2026",
    dates="NOV 13-16, 2026",
    route=["LAS VEGAS", "SAN DIEGO", "SANTA BARBARA", "LAS VEGAS"],
    route_short="LAS VEGAS · SAN DIEGO · SANTA BARBARA",
    price=2999, unit="PER CAR",
    code="RALLY500", off=500,
    # The site's own tagline. It says three days while the dates span four;
    # printed here as written rather than corrected.
    tagline="THREE ICONIC DESTINATIONS.",
    includes=["HOTELS EVERY NIGHT", "CO-PILOT INCLUDED",
              "CHECKPOINTS · SUPPORT CARS", "SWAG · AWARDS"],
    spots="LIMITED SPOTS AVAILABLE",
    start_venue="SUPERCAR EXPERIENCE LV",
)

# --------------------------------------------------------------------------
# Call-to-action captions   (slug, lead, accent, group)
# --------------------------------------------------------------------------
# On the black "panel" style the accent half is set in gold; on the solid-
# gold "bar" style the halves are joined in black.
CTA_CAPTIONS = [
    # Ready to book - highest intent.
    ("book-now", "BOOK", "NOW", "booking"),
    ("reserve-your-ride", "RESERVE YOUR", "RIDE", "booking"),
    ("book-the-weekend", "BOOK THE", "WEEKEND", "booking"),
    ("text-to-book", "TEXT TO", "BOOK", "booking"),

    # Still deciding - a low-commitment first step.
    ("pick-your-car", "PICK YOUR", "CAR", "choose"),
    ("4-hours-or-24", "4 HOURS", "OR 24", "choose"),
    ("see-the-fleet", "SEE THE", "FLEET", "choose"),

    # Wants dates / a number.
    ("dm-for-dates", "DM FOR", "DATES", "quote"),
    ("text-us", "TEXT", "(725) 425-3583", "quote"),

    # Engagement - drives comments, which drives reach.
    ("which-one-first", "WHICH ONE", "FIRST?", "engagement"),
    ("tag-your-copilot", "TAG YOUR", "CO-PILOT", "engagement"),
    ("drop-your-dream-car", "DROP YOUR", "DREAM CAR", "engagement"),

    # Soft / top of funnel.
    ("link-in-bio", "LINK IN", "BIO", "soft"),
    ("follow-for-the-fleet", "FOLLOW FOR", "THE FLEET", "soft"),

    # Offer / trust.
    ("third-day-free", "3RD DAY", "FREE", "offer"),
    ("price-match", "PRICE MATCH", "GUARANTEE", "offer"),
]

CTA_GROUPS = {
    "booking": "Ready to book. Highest intent - use on the payoff shot.",
    "choose": "Still deciding. A first step for someone who likes the car but "
              "hasn't pictured the weekend yet.",
    "quote": "Wants dates or a number. Opens a direct conversation by text.",
    "engagement": "Drives comments, which drives reach. Not a sales CTA.",
    "soft": "Top of funnel. Low friction, low intent.",
    "offer": "The listed promos. Pairs with a price on screen.",
}

# --------------------------------------------------------------------------
# Contact  (site footer)
# --------------------------------------------------------------------------
WEBSITE = "supercarexp.vip"
INSTAGRAM = "@supercar_experience_"
PHONE = "(725) 425-3583"
EMAIL = PHONE                 # the site books by text; any EMAIL slot shows the number
BRAND_NAME = "SUPERCAR EXPERIENCE"
BRAND_SUFFIX = "LAS VEGAS - SCOTTSDALE - BOISE"
TAGLINE = "A RIDE OF A LIFETIME. WAITING FOR YOU."
