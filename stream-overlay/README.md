# Stream Overlay — Youngomarie

Sticker-style social media overlay pack for streams/videos.

## Handles
| Platform  | Handle / URL |
|-----------|--------------|
| YouTube   | Youngomarie — `youtube.com/@Youngomarie` |
| Twitch    | Youngomarie — `twitch.tv/Youngomarie` |
| Instagram | nq.young |

## Exported PNGs (transparent background, 3× / ~4K wide)

| File | Use |
|------|-----|
| `hero-bar.png` | Big combined bar: all 3 icons + name (intro / banner) |
| `handle-youtube.png` | YouTube icon + Youngomarie |
| `handle-twitch.png` | Twitch icon + Youngomarie |
| `handle-instagram.png` | Instagram icon + nq.young |
| `url-twitch.png` | Twitch icon + twitch.tv/Youngomarie |
| `url-youtube.png` | YouTube icon + youtube.com/@Youngomarie |
| `preview-sheet.png` | Full reference sheet (all elements) |

All overlay PNGs (except the preview sheet) have a fully transparent
background, so they drop straight into OBS, StreamElements, CapCut,
Premiere, etc. as an image/logo source.

## Editing & re-rendering

The design is a single self-contained HTML file (`overlay.html`) using
inline SVG brand logos and two bundled display fonts (`fonts/`).

To change handles, colors, or sizes, edit `overlay.html`, then:

```bash
cd stream-overlay
npm install playwright          # first time only
npx playwright install chromium # first time only
node render.js                  # re-exports all PNGs
```

`render.js` screenshots each `.row` element individually with a
transparent background and writes the full `preview-sheet.png`.

## Fonts
- **Luckiest Guy** (Apache 2.0) — chunky outlined usernames
- **Anton** (OFL) — fallback display weight
