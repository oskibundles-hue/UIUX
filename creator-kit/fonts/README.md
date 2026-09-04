# Fonts

**SpaceGrotesk.ttf** — [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk),
licensed SIL Open Font License 1.1, which permits redistribution. Vendored so
`build_se_overlays.py` reproduces byte-identical output without a network fetch.

It stands in for the licensed grotesk on supercarexp.vip. If the real face is
ever licensed, drop it in and pass `--font` — the geometry is driven by measured
bounding boxes, not by this specific font, so the pack rebuilds cleanly.

A caution learned the hard way: **woff2 does not work in the headless Chromium
used here.** `@font-face` is accepted, `document.fonts` reports success, and the
text paints in the fallback face with no error anywhere. Use TTF, and verify by
rendering the same string with and without the `@font-face` — if the two PNGs
are byte-identical, the font did not load.
