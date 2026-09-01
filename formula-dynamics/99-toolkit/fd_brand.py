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
    ("window-tint", "WINDOW TINT", "Ceramic window tint. Heat and UV rejection."),
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
    "window-tint": "CERAMIC WINDOW TINT",
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
# (slug, on-screen label, prose name, category)
# On-screen labels are uppercase because every graphic is set in Bebas Neue,
# which has no lowercase. Use the prose name in captions and written copy,
# where the brand's own styling matters: "iPE Exhaust", not "IPE EXHAUST".
PARTNERS = [
    ("nv-forged", "NV FORGED", "NV Forged", "Forged wheels"),
    ("ipe", "IPE EXHAUST", "iPE Exhaust", "Titanium / valvetronic exhaust"),
    ("ryft", "RYFT SPRINGS", "Ryft Springs",
     "Lowering springs, exhaust, blow-off valves"),
]

# --------------------------------------------------------------------------
# Call-to-action captions
# --------------------------------------------------------------------------
# (slug, lead, accent, group)
#
# The two halves matter: on the black "panel" style the accent half is set in
# brand red, so the line has one point of emphasis rather than shouting the
# whole way through. On the solid-red "bar" style the halves are simply joined
# and set in white - red type on a red bar would vanish.
#
# Grouped by what the viewer is ready to do, which is how they should be
# chosen. See 05-copy-library/cta-captions.md.
CTA_CAPTIONS = [
    # Ready to book - highest intent, lowest reach. Use on payoff content.
    ("book-now", "BOOK", "NOW", "booking"),
    ("schedule-appointment", "SCHEDULE AN", "APPOINTMENT", "booking"),
    ("book-your-build", "BOOK YOUR", "BUILD", "booking"),
    ("now-booking", "NOW", "BOOKING", "booking"),
    ("reserve-your-spot", "RESERVE YOUR", "SPOT", "booking"),

    # Still deciding - invites a low-commitment first step.
    ("see-what-fits", "SEE WHAT FITS", "YOUR CAR", "fitment"),
    ("find-your-fitment", "FIND YOUR", "FITMENT", "fitment"),
    ("built-for-your-car", "BUILT FOR", "YOUR CAR", "fitment"),

    # Wants a number.
    ("get-a-quote", "GET A", "QUOTE", "quote"),
    ("dm-your-model", "DM US", "YOUR MODEL", "quote"),
    ("dm-for-pricing", "DM FOR", "PRICING", "quote"),

    # Engagement - drives comments, which drives reach. Not a sales CTA.
    ("what-would-you-fit", "WHAT WOULD YOU", "FIT NEXT?", "engagement"),
    ("drop-your-model", "DROP YOUR MODEL", "BELOW", "engagement"),

    # Soft / top of funnel.
    ("link-in-bio", "LINK IN", "BIO", "soft"),
    ("follow-for-more", "FOLLOW FOR MORE", "BUILDS", "soft"),

    # Trust. Pairs with service and maintenance content.
    ("we-service-what-we-build", "WE SERVICE", "WHAT WE BUILD", "trust"),
]

CTA_GROUPS = {
    "booking": "Ready to book. Highest intent - use on reveals, dyno results "
               "and finished-car payoff shots.",
    "fitment": "Still deciding. A low-commitment first step for someone who "
               "likes the work but hasn't pictured it on their own car.",
    "quote": "Wants a number. Opens a direct conversation.",
    "engagement": "Drives comments, which drives reach. Not a sales CTA - "
                  "use it to widen the audience the sales CTAs land on.",
    "soft": "Top of funnel. Low friction, low intent.",
    "trust": "Pairs with service and maintenance content.",
}


# --------------------------------------------------------------------------
# Contact  (brand guide footer)
# --------------------------------------------------------------------------
WEBSITE = "formuladynamicsperformance.com"
INSTAGRAM = "@formuladynamicsperformance"
EMAIL = "info@formuladynamicsperformance.com"
BRAND_NAME = "FORMULA DYNAMICS"
BRAND_SUFFIX = "PERFORMANCE"
