#!/usr/bin/env python3
"""
Formula Dynamics Performance - rebuild the whole asset kit.

Run this after changing anything in fd_brand.py (colours, services, partners,
contact details) and every generated file is regenerated consistently.

    cd 99-toolkit && python3 build_all.py

Requires: Python 3, Pillow, numpy, potracer, cairosvg
    pip install Pillow numpy potracer cairosvg
"""

import build_index
import build_logos
import build_overlays
import build_tokens

if __name__ == "__main__":
    print("[1/4] Logos")
    n = build_logos.build()
    print(f"      {n} logo variants\n")

    print("[2/4] Overlays and templates")
    total = 0
    for label, fn in [
        ("colour swatches", build_overlays.build_swatches),
        ("accent bars", build_overlays.build_accent_bars),
        ("logo bugs", build_overlays.build_logo_bugs),
        ("lower thirds", build_overlays.build_lower_thirds),
        ("service badges", build_overlays.build_badges),
        ("title cards", build_overlays.build_title_cards),
        ("end cards", build_overlays.build_end_cards),
        ("safe-zone guides", build_overlays.build_safe_zones),
    ]:
        count = fn()
        total += count
        print(f"      {label:<20} {count:>4}")
    print()
    print("[3/4] Brand tokens")
    print(f"      {build_tokens.build()} token files\n")

    print("[4/4] Asset index")
    print(f"      {build_index.main()} files indexed\n")

    print("Done. Kit rebuilt.")
