#!/usr/bin/env python3
"""Fetch Kenney's CC0 audio packs.

Kenney releases everything under Creative Commons CC0 (public domain) — no
attribution required, commercial use fine, no restriction on advertising.
The licence is verified per pack before anything is downloaded, so a change
on their side surfaces as a skip rather than a silent bad grab.

The zip URL is not on the asset page as a plain link; it sits inside the
donation modal, under a different content hash from the preview audio, so
each page has to be scraped for it.
"""
import re
import subprocess
import pathlib
import sys

BASE = "https://kenney.nl"
PACKS = [
    "interface-sounds", "ui-audio", "impact-sounds", "digital-audio",
    "sci-fi-sounds", "music-jingles", "casino-audio", "rpg-audio",
    "voiceover-pack", "voiceover-pack-fighter",
]
OUT = pathlib.Path(__file__).parent / "assets" / "kenney"

# The zip href is absolute on some pages and root-relative on others.
ZIP_RE = re.compile(
    r"""href=['"]((?:https://kenney\.nl)?/media/pages/assets/[^'"]+?\.zip)['"]"""
)


def get(url, binary=False, timeout=120):
    r = subprocess.run(["curl", "-sSL", "-m", str(timeout), url],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    got, skipped = [], []
    for slug in PACKS:
        page = get(f"{BASE}/assets/{slug}")
        if not page:
            skipped.append((slug, "page unreachable"))
            continue

        # licence gate — only CC0 is taken
        if "CC0" not in page:
            skipped.append((slug, "not CC0"))
            continue

        # the link is absolute on some pages and root-relative on others
        m = re.search(ZIP_RE, page)
        if not m:
            skipped.append((slug, "no zip link found"))
            continue

        href = m.group(1)
        url = href if href.startswith("http") else BASE + href
        dest = OUT / f"{slug}.zip"
        blob = get(url, binary=True, timeout=300)
        if not blob or len(blob) < 10_000 or blob[:2] != b"PK":
            skipped.append((slug, f"bad download ({len(blob or b'')}b)"))
            continue
        dest.write_bytes(blob)
        got.append((slug, len(blob)))
        print(f"  ok   {slug:24s} {len(blob)/1048576:6.1f} MB")

    for slug, why in skipped:
        print(f"  skip {slug:24s} {why}")
    print(f"\n{len(got)} packs downloaded to {OUT}")
    return 0 if got else 1


if __name__ == "__main__":
    sys.exit(main())
