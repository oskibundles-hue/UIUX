#!/usr/bin/env python3
"""
Formula Dynamics Performance - rebuild the whole asset kit.

Run this after changing anything in fd_brand.py (colours, services, partners,
contact details) and every generated file is regenerated consistently.

    cd 99-toolkit && python3 build_all.py

Requires: Python 3, Pillow, numpy, potracer, cairosvg, reportlab
    pip install Pillow numpy potracer cairosvg reportlab
"""

import build_bundles
import build_index
# import build_logos  # not part of the SCE kit
import build_overlays
import build_rental
# import build_pdf  # not part of the SCE kit
import build_tokens

if __name__ == "__main__":
    print("[1/6] Logos")
    n = 0  # logos are shipped as PNGs, see 02-logos/png
    print(f"      {n} logo variants\n")

    print("[2/6] Overlays and templates")
    total = 0
    for label, fn in [
        ("colour swatches", build_overlays.build_swatches),
        ("accent bars", build_overlays.build_accent_bars),
        ("logo bugs", build_overlays.build_logo_bugs),
        ("lower thirds", build_overlays.build_lower_thirds),
        ("service badges", build_overlays.build_badges),
        ("CTA captions", build_overlays.build_cta_captions),
        ("title cards", build_overlays.build_title_cards),
        ("end cards", build_overlays.build_end_cards),
        ("safe-zone guides", build_overlays.build_safe_zones),
    ]:
        count = fn()
        total += count
        print(f"      {label:<20} {count:>4}")
    print()
    print("[2b/6] Rental overlays")
    print(f"      {build_rental.build()} files\n")
    print("[3/6] Brand tokens")
    print(f"      {build_tokens.build()} token files\n")

    print("[4/6] Printable guide (PDF)")
    print("      skipped for the SCE kit\n")

    print("[5/6] Download bundles")
    for path, count in build_bundles.build():
        print(f"      {path.name:<38} {count:>4} files")
    print()

    print("[6/6] Asset index")
    print(f"      {build_index.main()} files indexed\n")

    print("Done. Kit rebuilt.")
