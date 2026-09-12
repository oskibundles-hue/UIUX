#!/usr/bin/env python3
"""
Supercar Experience - downloadable ZIP bundles.

Packages the kit into bundles you can download and unzip straight into a
CapCut media folder or a phone album, instead of pulling the whole repository.

Every archive is written deterministically (fixed timestamps, sorted entries),
so rebuilding without changing an asset produces a byte-identical file and the
repository doesn't accumulate a new copy on each run.

Run:  python3 99-toolkit/build_bundles.py
"""

import zipfile
from pathlib import Path

import sce_brand as B

OUT = B.KIT / "08-download-bundles"

# A fixed timestamp keeps archives reproducible. ZIP cannot store years < 1980.
FIXED_DATE = (1980, 1, 1, 0, 0, 0)


HOW_TO = """{brand}
{title}
================================================================

WHAT THIS IS
{blurb}

THE ONE RULE
Full-frame overlays are already the exact size of their canvas.
A file ending _9x16 is exactly 1080 x 1920 pixels.

Set your CapCut project ratio FIRST, then drag the overlay onto a
track above your video. Do NOT resize it. It is already in position.

If an overlay looks the wrong size, the project ratio does not match
the filename. Fix the ratio - do not scale the overlay.

READING THE FILENAMES
  9x16 = 1080 x 1920   TikTok / Reels / Shorts   <- your main format
  4x5  = 1080 x 1350   Instagram feed video
  1x1  = 1080 x 1080   Square feed posts
  16x9 = 1920 x 1080   YouTube / website

  white / dark  = for use on DARK footage
  black / light = for use on LIGHT footage

CONTENTS
{contents}

Every file in the kit: ASSET-INDEX.md
{website}
"""


def add(zf, path, arcname):
    """Add one file with a fixed timestamp so the archive stays reproducible."""
    info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, path.read_bytes())


def write_bundle(name, title, blurb, files):
    """files: list of (source Path, name inside the archive)."""
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"{name}.zip"

    files = sorted(files, key=lambda f: f[1])
    listing = "\n".join(f"  {arc}" for _, arc in files[:400])
    readme = HOW_TO.format(brand=B.BRAND_NAME, title=title, blurb=blurb,
                           contents=listing, website=B.WEBSITE)

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        info = zipfile.ZipInfo("HOW-TO-USE.txt", date_time=FIXED_DATE)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        zf.writestr(info, readme)
        for src, arc in files:
            add(zf, src, arc)

    return target, len(files)


def in_dir(folder, prefix=None):
    src = B.OVERLAYS / folder
    return [(p, f"{prefix or folder}/{p.name}")
            for p in src.iterdir() if p.is_file() and p.suffix == ".png"]


def in_tree(folder):
    """Like in_dir, but for a folder with sub-folders - keeps them in the zip."""
    src = B.OVERLAYS / folder
    return [(p, f"{folder}/{p.relative_to(src)}")
            for p in sorted(src.rglob("*.png")) if p.is_file()]


def build():
    results = []

    # 1. The vertical starter pack - everything needed for the main format.
    essentials = []
    for folder in ("corner-logo-bugs", "lower-thirds", "title-cards", "end-cards"):
        essentials += [(p, a) for p, a in in_dir(folder) if "9x16" in p.name]
    essentials += [(p, a) for p, a in in_dir("cta-captions") if "9x16" in p.name]
    essentials += in_dir("service-badges")
    essentials += [(p, a) for p, a in in_dir("accent-bars") if "1080w" in p.name]
    essentials.append((B.TEMPLATES / "safe-zone-guides" / "safe-zones_9x16.png",
                       "safe-zone-guide/safe-zones_9x16.png"))
    results.append(write_bundle(
        "SCE-00-VERTICAL-STARTER-PACK",
        "Vertical starter pack (9:16)",
        "Everything needed for TikTok, Reels and Shorts, and nothing else.\n"
        "If you only download one bundle, make it this one.",
        essentials))

    # 1b. Long-form / vlog furniture.
    results.append(write_bundle(
        "SCE-11-vlog-overlays",
        "Vlog and long-form overlays",
        "Furniture the ad overlays cannot stand in for: a name bar for\n"
        "whoever is on camera, numbered chapter markers, a place-and-date\n"
        "stamp, a track credit and a follow bug.\n"
        "\n"
        "The site is the only address on screen - no handles - so these do\n"
        "not go stale if an account name changes.\n"
        "\n"
        "For a name, chapter, stamp or track that is not in here, generate it:\n"
        "  python3 99-toolkit/build_vlog.py name --name \"OMARIE\" --role \"HOST\"\n"
        "  python3 99-toolkit/build_vlog.py chapter --index 02 --label \"WALKAROUND\"",
        in_tree("vlog")))

    # 2. One bundle per overlay type.
    per_type = [
        ("SCE-01-logo-bugs", "corner-logo-bugs", "Logo bugs",
         "Your logo, pre-positioned on a full transparent frame.\n"
         "Drop one on the timeline and it is already in place. Pick ONE\n"
         "position and use it on every video - that consistency is what\n"
         "makes a brand look established."),
        ("SCE-02-lower-thirds", "lower-thirds", "Lower thirds",
         "Name plates for services, partners and calls to action.\n"
         "Bring in around 1-2 s, hold 3-4 s, then out."),
        ("SCE-03-title-cards", "title-cards", "Title cards",
         "Two-line openers. White or black top line, gold beneath.\n"
         "Use 'dark' on dark footage, 'light' on bright footage."),
        ("SCE-04-end-cards", "end-cards", "End cards",
         "Full-frame closing cards with logo, tagline and contact details.\n"
         "These are NOT transparent - they are a finished last shot.\n"
         "Hold for 1.5-2.5 seconds."),
        ("SCE-05-cta-captions", "cta-captions", "CTA captions",
         "Sixteen calls to action in two styles.\n"
         "'bar' is the solid gold default. 'panel' is black with the key word\n"
         "in gold - use it when the shot is bright or yellow, because a gold\n"
         "bar on a sunlit wall or a gold car disappears.\n"
         "One CTA per video, held 2-3 seconds, on the payoff shot."),
        ("SCE-06-service-badges", "service-badges", "Service badges",
         "Gold-outlined chips for feature callouts, one per car,\n"
         "plus a ready-made strip of the four lead services."),
        ("SCE-07-accent-bars", "accent-bars", "Accent bars",
         "The two-tone accent stripe and solid gold bars.\n"
         "Underline a title, divide a split screen, or keyframe one across\n"
         "the frame over 6-10 frames as your house transition."),
    ]
    for name, folder, title, blurb in per_type:
        results.append(write_bundle(name, title, blurb, in_dir(folder)))

    # Rental overlays live in nested folders, so gather them recursively.
    rental_root = B.OVERLAYS / "rental"
    rental = [(p, f"rental/{p.relative_to(rental_root).as_posix()}")
              for p in sorted(rental_root.rglob("*.png"))]
    results.append(write_bundle(
        "SCE-10-rental-overlays", "Rental overlays",
        "Price stacks and pills for every listed car, requirements chip,\n"
        "location strip, promo chips, Tempesta spec ticker, Fall Rally plate.",
        rental))

    # 3. Everything, for archiving or a one-shot import.
    every = []
    every = list(every) + rental + in_tree("vlog")
    for folder in ("corner-logo-bugs", "lower-thirds", "title-cards",
                   "end-cards", "cta-captions", "service-badges", "accent-bars"):
        every += in_dir(folder)
    every += [(p, f"safe-zone-guides/{p.name}")
              for p in (B.TEMPLATES / "safe-zone-guides").iterdir()
              if p.suffix == ".png"]
    results.append(write_bundle(
        "SCE-08-ALL-OVERLAYS", "All overlays",
        "Every overlay in every format, plus the safe-zone guides.",
        every))

    # 4. Logos, since they are always wanted alongside the overlays.
    logos = [(p, f"png/{p.name}")
             for p in (B.LOGOS / "png").iterdir() if p.suffix == ".png"]
    logos += [(p, f"svg-vector/{p.name}")
              for p in (list((B.LOGOS / "svg-vector").iterdir()) if (B.LOGOS / "svg-vector").exists() else []) if p.suffix == ".svg"]
    results.append(write_bundle(
        "SCE-09-logos", "Logos",
        "Every logo lockup. SVG is true vector - use it anywhere that\n"
        "accepts SVG. CapCut does not, so use the PNGs there.\n"
        "PNGs come at 1000 / 2000 / 4000 px wide.",
        logos))

    return results


if __name__ == "__main__":
    bundles = build()
    for path, count in bundles:
        kb = path.stat().st_size / 1024
        size = f"{kb / 1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"
        print(f"  {path.name:<38} {count:>4} files  {size:>9}")
    print(f"\nDone. {len(bundles)} bundles in 08-download-bundles/.")
