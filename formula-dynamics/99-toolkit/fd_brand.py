"""
Formula Dynamics Performance - shared brand constants.

Single source of truth for every generated asset. Values come from the
official brand guide (01-brand-core/brand-guide-master.png). If the brand
guide changes, change it HERE and re-run build_all.py.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
KIT = Path(__file__).resolve().parent.parent
BRAND_CORE = KIT / "01-brand-core"
LOGOS = KIT / "02-logos"
OVERLAYS = KIT / "03-overlays"
TEMPLATES = KIT / "04-templates"
FONTS = KIT / "07-fonts"

BRAND_GUIDE = BRAND_CORE / "brand-guide-master.png"
POSTERS = TEMPLATES / "reference-posters"

FONT_BEBAS = FONTS / "BebasNeue-Regular.ttf"

# --------------------------------------------------------------------------
# Colour palette  (brand guide section 4)
# --------------------------------------------------------------------------
RED = "#FE0F13"
WHITE = "#FFFFFF"
BLACK = "#000000"
GREEN = "#1DB14B"
YELLOW = "#FFDE00"

PALETTE = [
    # name,        hex,     role
    ("red", RED, "Primary accent. CTAs, key words, underlines, highlights."),
    ("white", WHITE, "Primary logo + headline colour on dark footage."),
    ("black", BLACK, "Primary background. Logo colour on light footage."),
    ("green", GREEN, "Racing stripe only. Never a background or body colour."),
    ("yellow", YELLOW, "Racing stripe only. Never a background or body colour."),
]

HEX = {n: h for n, h, _ in PALETTE}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# Colours that can appear in the logo artwork (black excluded: it is the
# background of the extraction source, not an ink).
INK_COLORS = [RED, WHITE, GREEN, YELLOW]

# The four-colour racing stripe, left to right, as it appears under the
# wordmark. Widths are proportional, not absolute.
ACCENT_STRIPE = [
    (RED, 0.42),
    (WHITE, 0.24),
    (GREEN, 0.20),
    (YELLOW, 0.14),
]

# --------------------------------------------------------------------------
# Typography  (brand guide section 5)
# --------------------------------------------------------------------------
TYPE_PRIMARY = "Bebas Neue"          # headlines - bundled, OFL licensed
TYPE_ACCENT = "Neuropol X"           # performance/accent - COMMERCIAL, not bundled

# --------------------------------------------------------------------------
# Video canvases
# --------------------------------------------------------------------------
CANVASES = {
    "9x16": (1080, 1920),   # TikTok / Reels / Shorts  - primary format
    "4x5":  (1080, 1350),   # Instagram feed video
    "1x1":  (1080, 1080),   # Square feed
    "16x9": (1920, 1080),   # YouTube / web / landing hero
}

# Platform UI keep-out zones for 9:16, as fractions of frame height/width.
# Nothing important should live inside these bands.
SAFE_ZONES_9X16 = {
    "top": 0.11,      # status bar + platform chrome
    "bottom": 0.20,   # caption, handle, CTA button
    "right": 0.16,    # like / comment / share rail
    "left": 0.05,
}

# --------------------------------------------------------------------------
# Services  (badges + copy library are generated from this list)
# --------------------------------------------------------------------------
SERVICES = [
    ("tuning", "TUNING", "ECU / TCU calibration, custom maps, dyno-verified gains."),
    ("exhaust", "EXHAUST", "Valvetronic, catback, downpipes, titanium systems."),
    ("wheels", "WHEELS", "Forged, monoblock and multi-piece fitment."),
    ("body-kits", "BODY KITS", "Aero, carbon fibre, widebody, full conversions."),
    ("ppf", "PPF", "Paint protection film. Full front, track pack, full body."),
    ("ceramic-coating", "CERAMIC COATING", "Multi-year paint, wheel and glass protection."),
    ("paint-correction", "PAINT CORRECTION", "Multi-stage machine polish and gloss restoration."),
    ("detailing", "DETAILING", "Interior and exterior maintenance detailing."),
    ("suspension", "SUSPENSION", "Coilovers, lowering springs, air, lift kits."),
    ("service", "SERVICE", "Scheduled maintenance, fluids, brakes, diagnostics."),
]

# Short sublines for on-screen name plates. The longer SERVICES blurbs above
# are written for captions and scripts; they are too long to set as a subline.
SERVICE_SUBLINE = {
    "tuning": "ECU & TCU CALIBRATION",
    "exhaust": "VALVETRONIC & CATBACK SYSTEMS",
    "wheels": "FORGED WHEEL FITMENT",
    "body-kits": "AERO & CARBON FIBRE",
    "ppf": "PAINT PROTECTION FILM",
    "ceramic-coating": "MULTI-YEAR PAINT PROTECTION",
    "paint-correction": "MULTI-STAGE MACHINE POLISH",
    "detailing": "INTERIOR & EXTERIOR DETAIL",
    "suspension": "COILOVERS, SPRINGS & AIR",
    "service": "MAINTENANCE & DIAGNOSTICS",
}

# The four services the current video push leads with.
PRIORITY_SERVICES = ["body-kits", "exhaust", "wheels", "tuning"]

# --------------------------------------------------------------------------
# Partners
# NOTE: names only. Partner LOGOS are their intellectual property and are not
# generated here - drop official files into 03-overlays/partner-logos/.
# --------------------------------------------------------------------------
PARTNERS = [
    ("nv-forged", "NV FORGED", "Forged wheels"),
    ("ipe", "IPE EXHAUST", "Titanium / valvetronic exhaust"),
    ("rift", "RIFT", "Exhaust, blow-off valves, performance hardware"),
    ("luring", "LURING", "Lowering springs / suspension"),
]

# --------------------------------------------------------------------------
# Contact  (brand guide footer)
# --------------------------------------------------------------------------
WEBSITE = "formuladynamicsperformance.com"
INSTAGRAM = "@formuladynamicsperformance"
EMAIL = "info@formuladynamicsperformance.com"
BRAND_NAME = "FORMULA DYNAMICS"
BRAND_SUFFIX = "PERFORMANCE"
