import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))

from paper_broker import PaperBroker  # noqa: E402


def pip_size(symbol: str) -> float:
    return 0.01 if "JPY" in symbol else 0.0001


def make_broker():
    return PaperBroker(":memory:", pip_size)


def test_win_hits_50_pip_take_profit():
    b = make_broker()
    assert b.open_position("EURUSD", "long", 1.1000, sl=1.0990, tp=1.1050)["ok"]
    result = b.close_position("EURUSD", 1.1050)
    assert result["ok"] and result["pnl_pips"] == 50.0


def test_loss_hits_10_pip_stop():
    b = make_broker()
    b.open_position("EURUSD", "long", 1.1000, sl=1.0990, tp=1.1050)
    assert b.close_position("EURUSD", 1.0990)["pnl_pips"] == -10.0


def test_short_direction_and_jpy_pip():
    b = make_broker()
    b.open_position("USDJPY", "short", 150.00, sl=150.10, tp=149.50)
    assert b.close_position("USDJPY", 149.50)["pnl_pips"] == 50.0


def test_rejects_duplicate_position_and_unknown_exit():
    b = make_broker()
    assert b.open_position("EURUSD", "long", 1.1, 1.099, 1.105)["ok"]
    assert not b.open_position("EURUSD", "long", 1.1, 1.099, 1.105)["ok"]
    assert not b.close_position("GBPUSD", 1.25)["ok"]


def test_stats():
    b = make_broker()
    b.open_position("EURUSD", "long", 1.1000, 1.0990, 1.1050)
    b.close_position("EURUSD", 1.1050)
    b.open_position("GBPUSD", "long", 1.2500, 1.2490, 1.2550)
    b.close_position("GBPUSD", 1.2490)
    s = b.stats()
    assert s["closed_trades"] == 2
    assert s["wins"] == 1 and s["losses"] == 1
    assert s["win_rate_pct"] == 50.0
    assert s["total_pnl_pips"] == 40.0
