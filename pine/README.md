# Pine Script — Theme Package Selector

A reusable TradingView Pine Script v6 indicator skeleton with a single
**🎨 Theme Package** dropdown that re-colors the entire indicator from one
cohesive, hand-tuned palette.

## Themes

| Package | Mood | Bullish | Bearish | Accent | Background |
|---|---|---|---|---|---|
| **Obsidian Sniper** | Tactical dark / HUD | Neon green `#00E676` | Hot red `#FF3D3D` | Amber `#FFBF00` | Charcoal `#0D1113` |
| **Ice Blue** | Cool & clean | Glacier cyan `#26C6DA` | Slate indigo `#5C6BC0` | Soft sky `#81D4FA` | Frosted navy `#142130` |
| **Royal Gold** | Luxury | Royal gold `#D4AF37` | Deep crimson `#B22234` | Champagne `#F5DEB3` | Espresso `#110E0A` |

Each palette is a *coordinated set* — primary up/down plus accent, neutral
stroke, panel background, and foreground text — so swapping the dropdown
restyles candles, EMAs, volatility bands, cross signals, and the info table
together.

## Usage

1. Open [TradingView](https://www.tradingview.com/) → **Pine Editor**.
2. Paste the contents of [`theme-package-selector.pine`](./theme-package-selector.pine).
3. **Add to chart**, then pick a package under **Settings → 🎨 Style → Theme Package**.

## Extending

All theming flows through one `Theme` user-defined type. To add a package:

1. Add its name to the `themeMode` `options=[...]` list.
2. Write a `themeYourName()` constructor returning a `Theme.new(...)`.
3. Add a `case` for it in `activeTheme()`.

Everything downstream reads from the active theme `t`, so no other changes
are needed.
