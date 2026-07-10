"""Environment-driven configuration for the 1-5 trading bot."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Must match the "Shared secret" input in the Pine Script strategy.
    webhook_secret: str = field(default_factory=lambda: os.environ.get("WEBHOOK_SECRET", ""))

    # Claude trade-filter. Leave ANTHROPIC_API_KEY unset to skip the AI filter
    # and trade on raw indicator signals.
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    claude_model: str = field(
        default_factory=lambda: os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    )
    # Minimum confidence (0-100) Claude must report for a trade to pass.
    min_confidence: int = field(default_factory=lambda: int(os.environ.get("MIN_CONFIDENCE", "60")))
    # If the Claude API call fails: "reject" (safe default) or "approve".
    filter_failure_mode: str = field(
        default_factory=lambda: os.environ.get("FILTER_FAILURE_MODE", "reject")
    )

    # Paper-trading ledger.
    db_path: str = field(default_factory=lambda: os.environ.get("DB_PATH", "paper_trades.db"))

    # Pip size per symbol; JPY pairs use 0.01, everything else defaults to 0.0001.
    default_pip: float = 0.0001
    jpy_pip: float = 0.01

    def pip_size(self, symbol: str) -> float:
        return self.jpy_pip if "JPY" in symbol.upper() else self.default_pip


settings = Settings()
