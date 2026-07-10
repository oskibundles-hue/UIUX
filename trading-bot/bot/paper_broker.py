"""SQLite-backed paper-trading ledger.

Opens a position when a buy/sell signal is approved and closes it when the
strategy's exit alert arrives (TradingView's strategy engine simulates the
10-pip SL / 50-pip TP fills, so the exit alert carries the close price).
P&L is tracked in pips.
"""

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,           -- 'long' | 'short'
    entry_price REAL NOT NULL,
    sl REAL NOT NULL,
    tp REAL NOT NULL,
    exit_price REAL,
    pnl_pips REAL,
    status TEXT NOT NULL DEFAULT 'open',  -- 'open' | 'closed'
    ai_confidence INTEGER,
    ai_reason TEXT,
    opened_at TEXT NOT NULL,
    closed_at TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class PaperBroker:
    def __init__(self, db_path: str, pip_size_fn):
        self._pip_size = pip_size_fn
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def open_position(self, symbol: str, direction: str, price: float, sl: float,
                      tp: float, ai_confidence: Optional[int] = None,
                      ai_reason: Optional[str] = None) -> dict[str, Any]:
        with self._lock:
            existing = self._open_row(symbol)
            if existing:
                return {"ok": False, "error": f"position already open on {symbol} (id={existing['id']})"}
            cur = self._conn.execute(
                "INSERT INTO trades (symbol, direction, entry_price, sl, tp, ai_confidence, ai_reason, opened_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (symbol, direction, price, sl, tp, ai_confidence, ai_reason, _now()),
            )
            self._conn.commit()
            return {"ok": True, "trade_id": cur.lastrowid}

    def close_position(self, symbol: str, price: float) -> dict[str, Any]:
        with self._lock:
            row = self._open_row(symbol)
            if not row:
                return {"ok": False, "error": f"no open position on {symbol}"}
            pip = self._pip_size(symbol)
            sign = 1 if row["direction"] == "long" else -1
            pnl = sign * (price - row["entry_price"]) / pip
            self._conn.execute(
                "UPDATE trades SET exit_price = ?, pnl_pips = ?, status = 'closed', closed_at = ? WHERE id = ?",
                (price, round(pnl, 1), _now(), row["id"]),
            )
            self._conn.commit()
            return {"ok": True, "trade_id": row["id"], "pnl_pips": round(pnl, 1)}

    def positions(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM trades WHERE status = 'open' ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM trades WHERE status = 'closed' ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(pnl_pips), 0) AS total,"
            " SUM(CASE WHEN pnl_pips > 0 THEN 1 ELSE 0 END) AS wins"
            " FROM trades WHERE status = 'closed'"
        ).fetchone()
        n, wins = row["n"], row["wins"] or 0
        return {
            "closed_trades": n,
            "wins": wins,
            "losses": n - wins,
            "win_rate_pct": round(100 * wins / n, 1) if n else None,
            "total_pnl_pips": round(row["total"], 1),
            "open_positions": len(self.positions()),
        }

    def _open_row(self, symbol: str):
        return self._conn.execute(
            "SELECT * FROM trades WHERE symbol = ? AND status = 'open' ORDER BY id DESC LIMIT 1",
            (symbol,),
        ).fetchone()
