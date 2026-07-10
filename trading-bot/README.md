# 1-5 Strategy Bot — TradingView + Claude AI Trade Filter

An AI-assisted trading bot built around a **1:5 risk/reward strategy** (10 pip stop
loss, 50 pip take profit) with entries from **adaptive support/resistance zone
rejections**.

> ⚠️ **Paper trading only.** This bot simulates fills and tracks pip P&L — it never
> places real orders. Trading forex involves substantial risk; nothing here is
> financial advice. Validate the strategy on paper before considering live execution.

## How it works

```
TradingView chart                         Your machine / server
┌─────────────────────────┐   webhook    ┌──────────────────────────────┐
│ Pine Script strategy    │  JSON alert  │ FastAPI bot (bot/main.py)    │
│ • adaptive S/R zones    ├─────────────►│ 1. verify shared secret      │
│ • zone-rejection entry  │              │ 2. Claude AI approves/vetoes │
│ • 10 pip SL / 50 pip TP │              │ 3. paper broker books trade  │
│ • fires entry+exit alerts│             │ 4. SQLite ledger + /stats    │
└─────────────────────────┘              └──────────────────────────────┘
```

- **`pinescript/one_five_sr_strategy.pine`** — Pine Script v6 strategy. Swing pivots
  are clustered into support/resistance zones whose width adapts to ATR and whose
  strength grows with each touch (an original implementation of the adaptive-zone
  concept — TradingView community indicators like BigBeluga's are proprietary and
  can't be redistributed, so this recreates the idea, not the code). A long fires
  when price wicks into a support zone and closes back above it (shorts mirrored at
  resistance), with an optional 200 EMA trend filter and entry cooldown. Every entry
  attaches a fixed 10-pip stop and 50-pip target.
- **`bot/`** — FastAPI webhook server. Each signal is sent to the Claude API, which
  returns `approve/veto + confidence + reason`; approved signals are booked by a
  SQLite paper broker. Exits are driven by the strategy's own exit alerts, so paper
  fills match TradingView's backtest engine.

## Setup

### 1. The Pine Script strategy

1. Open TradingView → Pine Editor → paste `pinescript/one_five_sr_strategy.pine` → **Add to chart**.
2. In the strategy settings, set **Shared secret** to a long random string.
3. Backtest first: use the Strategy Tester tab across your pairs/timeframes. A 1:5
   ratio only needs a ~17% win rate to break even — check the tester agrees before
   wiring up alerts.

### 2. The webhook bot

```bash
cd trading-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then edit: WEBHOOK_SECRET (same as step 1), ANTHROPIC_API_KEY
cd bot && uvicorn main:app --host 0.0.0.0 --port 8000
```

TradingView webhooks require a public HTTPS URL. For local testing, tunnel with
ngrok (`ngrok http 8000`) or deploy the bot to any small VPS.

### 3. The TradingView alert

1. On the chart with the strategy applied, create an **Alert**.
2. Condition: the strategy, **"Order fills only"**.
3. Message: exactly `{{strategy.order.alert_message}}` — the strategy builds the
   full JSON payload itself.
4. Webhook URL: `https://<your-tunnel-or-server>/webhook`.

One alert covers entries *and* exits: the strategy attaches an `exit` payload to its
SL/TP orders, so the paper broker closes positions at the same prices the backtester
fills them.

### 4. Watch it trade

| Endpoint | Purpose |
|---|---|
| `GET /positions` | Open paper positions |
| `GET /history` | Recent closed trades with pip P&L and the AI's reasoning |
| `GET /stats` | Win rate, total pips, open count |
| `GET /health` | Liveness + whether the AI filter is active |

## The Claude trade filter

Before booking any entry, the bot sends the signal context (direction, zone strength,
trend alignment, ATR in pips) to Claude, which replies with a JSON verdict. Trades
are skipped when Claude vetoes or confidence is below `MIN_CONFIDENCE`. Typical
vetoes: counter-trend entries, single-touch zones, or volatility so high a 10-pip
stop is likely to be noise-stopped.

- No `ANTHROPIC_API_KEY` → filter is bypassed (pure indicator bot).
- API errors → `FILTER_FAILURE_MODE` decides (`reject` by default: fail safe, miss
  the trade rather than take an unvetted one).
- Every verdict is stored on the trade row, so `/history` shows *why* each trade was
  taken.

## Tests

```bash
cd trading-bot && python3 -m pytest tests/ -q
```

## Extending to live execution

The paper broker is intentionally the only execution layer. When you're ready,
implement the same four methods (`open_position`, `close_position`, `positions`,
`stats`) against a broker API (e.g. OANDA practice account first) and swap it in
`bot/main.py`.
