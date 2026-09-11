"""
Build the two download trees: one for us, one to forward to the client.

Export filenames are built for the render pipeline, not for a phone's Files
app - "...-15s-9x16-c-occasion.mp4" tells you nothing at a glance. These
trees rename every ad to <brand>_<car>_<n>-<angle>_<len>-<ratio> and sort
the cars into numbered folders so they hold their order on any device.

EXPVIP is the client copy and carries only what has been approved. The
rally set is held back, so it appears in our tree alone, under a folder
whose name says so.
"""
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "_deliverables"
BRAND = "SCE"

# (slug, folder name, filename stem, price, seconds)  -- flagship first
CARS = [
    ("porsche-gt3rs",       "Porsche 911 GT3 RS",      "Porsche-911-GT3-RS",          "$1,299 / 4 hrs   -   $1,799 / full day", 15),
    ("mclaren-750s-spider", "McLaren 750S Spider",     "McLaren-750S-Spider",         "$1,299 / 4 hrs   -   $1,799 / full day", 15),
    ("ferrari-f8-tributo",  "Ferrari F8 Tributo",      "Ferrari-F8-Tributo",          "$999 / 4 hrs   -   $1,599 / full day",   15),
    ("lamborghini-sto",     "Lamborghini Huracan STO", "Lamborghini-Huracan-STO",     "$999 / 4 hrs   -   $1,599 / full day",   15),
    ("amg-gt-black-series", "AMG GT Black Series",     "Mercedes-AMG-GT-Black-Series","$899 / 4 hrs   -   $1,299 / full day",   15),
    ("ferrari-tempesta",    "Ferrari Tempesta",        "Ferrari-Tempesta",            "$849 / 4 hrs   -   $1,199 / full day",   15),
    ("novitec-urus",        "Lamborghini Novitec Urus","Lamborghini-Novitec-Urus",    "$699 / 4 hrs   -   $949 / full day",     15),
]
HELD = [("fall-rally", "Fall Rally 2026", "Fall-Rally-2026", "$2,999 per car   -   Nov 13-16", 18)]

# export suffix -> (sort number, plain-English name, what the cut leads with)
ANGLES = [
    ("",             1, "Price",      "Leads on the rate card. For someone who already wants the car and needs the figure."),
    ("-b-experience",2, "Experience", "Leads on the tagline. Identity over arithmetic."),
    ("-c-occasion",  3, "Occasion",   "Weddings, race week, photoshoots - the uses the site names."),
    ("-d-offer",     4, "Offer",      "Leads on the promo, worded exactly as the site prints it."),
    ("-e-engage",    5, "Question",   "Ends on a question that earns comments rather than a hard CTA."),
]

HEAD = """SUPERCAR EXPERIENCE - RENTAL ADS
{n} vertical ads   -   {c} cars   -   five angles each
1080x1920, 15 seconds, sound on.   Built for Reels, TikTok and Shorts.

Every price, promo and spec on screen is read off supercarexp.vip.
Phone on every cut: (888) 678-6079.   Location: Scottsdale.

THE FIVE ANGLES
Each car has the same five cuts, numbered 1 to 5 in its folder:
"""


def readme(cars, n, note=""):
    L = [HEAD.format(n=n, c=len(cars))]
    for _, num, name, desc in ANGLES:
        L.append(f"  {num}. {name:<11} {desc}")
    L += ["", "THE FLEET", ""]
    for i, (_, folder, _, price, _) in enumerate(cars, 1):
        L.append(f"  {i:02d}. {folder:<26} {price}")
    if note:
        L += ["", note]
    L += ["", "FILENAMES", "",
          "  SCE_<car>_<n>-<angle>_15s-9x16.mp4",
          "  e.g. SCE_Ferrari-F8-Tributo_3-Occasion_15s-9x16.mp4", ""]
    return "\n".join(L) + "\n"


def build(root, cars, held=(), note=""):
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    n = 0
    for i, (slug, folder, stem, _, secs) in enumerate(list(cars) + list(held), 1):
        holding = slug in {h[0] for h in held}
        name = f"{i:02d} {folder}" if not holding else f"HOLD - {folder} (not approved)"
        d = root / name
        d.mkdir()
        for suffix, num, angle, _ in ANGLES:
            src = HERE / slug / "exports" / f"supercar-experience-{slug}-{secs}s-9x16{suffix}.mp4"
            if not src.exists():
                raise SystemExit(f"missing render: {src}")
            # hardlink: same bytes, no second copy on disk until it is zipped
            (d / f"{BRAND}_{stem}_{num}-{angle}_{secs}s-9x16.mp4").hardlink_to(src)
            n += 1
    (root / "README.txt").write_text(readme(cars, len(cars) * len(ANGLES), note))
    return n


approved = build(OUT / "Supercar Experience Ads", CARS, HELD,
                 "HOLD FOLDER\n\n  The Fall Rally set is cut but not approved - it is still in\n"
                 "  revision. It is in here for reference only. Do not send it on.")
client = build(OUT / "EXPVIP", CARS)
print(f"our set:  {approved} files")
print(f"EXPVIP:   {client} files")
