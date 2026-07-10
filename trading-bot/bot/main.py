"""FastAPI webhook server for the 1-5 TradingView strategy.

Endpoints:
    POST /webhook    - TradingView alert sink (buy / sell / exit)
    GET  /positions  - open paper positions
    GET  /history    - recent closed trades
    GET  /stats      - win rate and pip P&L
    GET  /health     - liveness probe

Run:  uvicorn main:app --host 0.0.0.0 --port 8000
"""

import hmac
import logging

from fastapi import FastAPI, HTTPException, Request

import claude_filter
from config import settings
from paper_broker import PaperBroker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("one-five-bot")

app = FastAPI(title="1-5 Strategy Bot", version="1.0.0")
broker = PaperBroker(settings.db_path, settings.pip_size)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        signal = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="body must be JSON (use {{strategy.order.alert_message}} as the alert message)")

    if not settings.webhook_secret or not hmac.compare_digest(
        str(signal.get("secret", "")), settings.webhook_secret
    ):
        raise HTTPException(status_code=403, detail="bad or missing secret")

    action = str(signal.get("action", "")).lower()
    symbol = str(signal.get("symbol", "")).upper()
    try:
        price = float(signal["price"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="missing/invalid price")
    if not symbol:
        raise HTTPException(status_code=400, detail="missing symbol")

    if action == "exit":
        result = broker.close_position(symbol, price)
        log.info("EXIT %s @ %s -> %s", symbol, price, result)
        return result

    if action not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail=f"unknown action {action!r}")

    try:
        sl, tp = float(signal["sl"]), float(signal["tp"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="missing/invalid sl/tp")

    verdict = claude_filter.evaluate_signal(signal)
    log.info("SIGNAL %s %s @ %s | AI approve=%s conf=%s (%s)",
             action, symbol, price, verdict.approve, verdict.confidence, verdict.reason)

    if not verdict.approve or verdict.confidence < settings.min_confidence:
        return {"ok": True, "executed": False, "vetoed": True,
                "confidence": verdict.confidence, "reason": verdict.reason}

    direction = "long" if action == "buy" else "short"
    result = broker.open_position(symbol, direction, price, sl, tp,
                                  ai_confidence=verdict.confidence, ai_reason=verdict.reason)
    return {**result, "executed": result.get("ok", False),
            "confidence": verdict.confidence, "reason": verdict.reason}


@app.get("/positions")
def positions():
    return broker.positions()


@app.get("/history")
def history(limit: int = 50):
    return broker.history(limit=limit)


@app.get("/stats")
def stats():
    return broker.stats()


@app.get("/health")
def health():
    return {"ok": True, "ai_filter": bool(settings.anthropic_api_key)}
