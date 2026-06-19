# Pine Script — IFVG Sniper Entry Engine

[`ifvg-sniper-entry-engine.pine`](./ifvg-sniper-entry-engine.pine) — a
TradingView **Pine Script v6** indicator that detects Inverse Fair Value Gaps
(IFVGs), filters them by quality, and draws a single active trade model
(entry / SL / TP boxes + levels) with a live dashboard.

## How it works

1. **Hidden FVG memory** — every 3-bar fair value gap is stored internally
   (capped by *Hidden FVG Memory*, expired by *Max Hidden FVG Age*) along with
   its gap/ATR, body ratio, and range/ATR metrics.
2. **IFVG inversion** — when price closes through a stored gap (plus an optional
   clean-break ATR buffer), the gap inverts into an IFVG and a line/label is
   drawn (`IFVG+` / `IFVG-`).
3. **Quality filter** — `Off / Loose / Balanced / Strict / Custom` gate which
   inversions are allowed to produce a trade model.
4. **Trade model** — one active trade at a time: ENTRY/SL/TP lines, TP & SL
   boxes, and an RR-based take-profit. SL is counted first if both are touched
   in the same candle (conservative). Closed models are removed; only the
   active one stays on the chart.

## 🎨 Theme Packages

The **Theme Package** dropdown (Visual Style group) recolors IFVG lines, trade
levels, trade boxes, and the dashboard from one cohesive palette. Disable
*Use Theme Package Colors* to fall back to the individual custom color inputs.

| Package | Bull IFVG | Bear IFVG | TP | SL | Dashboard BG |
|---|---|---|---|---|---|
| **Obsidian Sniper** | `#0078FF` | `#FF3C46` | `#00BE6E` | `#DC3232` | `#0C0C10` |
| **Ice Blue** | `#00B4FF` | `#FF5078` | `#00DCFF` | `#FF4673` | `#081420` |
| **Royal Gold** | `#D4AF37` | `#D22D41` | `#D4AF37` | `#D22D41` | `#140F08` |

## Usage

1. Open [TradingView](https://www.tradingview.com/) → **Pine Editor**.
2. Paste the contents of `ifvg-sniper-entry-engine.pine`.
3. **Add to chart**, then tune inputs under groups 01–05. Pick a look under
   **🎨 04. Visual Style → Theme Package**.

> Note: this is a visual/analytical indicator (no `strategy()` orders); the
> Trades / W / L counters are based on visual TP/SL touches, not broker fills.
