"""Claude trade-filter: second opinion on every indicator signal.

The Pine strategy generates the raw signal; before the paper broker books it,
the signal context is sent to the Claude API, which returns approve/veto plus
a confidence score. If no API key is configured the filter passes everything
through. If the API call fails, FILTER_FAILURE_MODE decides (default: reject).
"""

import json
from dataclasses import dataclass
from typing import Any

from config import settings

_SYSTEM_PROMPT = """You are a disciplined forex trade-risk filter for a strategy with a fixed
10-pip stop loss and 50-pip take profit (1:5 risk/reward, ~17% breakeven win rate).
Entries come from adaptive support/resistance zone rejections.

Evaluate the signal you are given and respond with ONLY a JSON object:
{"approve": true|false, "confidence": 0-100, "reason": "<one sentence>"}

Veto (approve=false) when:
- The trade fights the stated trend direction.
- The zone is weak (fewer than 2 touches).
- ATR is so high that a 10-pip stop is likely noise-stopped (atr_pips much
  greater than 10), or so low that 50 pips of profit is unrealistic for the
  session (atr_pips far below 5).
Otherwise approve, with confidence scaled to zone strength and trend alignment."""


@dataclass
class Verdict:
    approve: bool
    confidence: int
    reason: str


def evaluate_signal(signal: dict[str, Any]) -> Verdict:
    if not settings.anthropic_api_key:
        return Verdict(True, 100, "AI filter disabled (no ANTHROPIC_API_KEY set)")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        context = {k: signal.get(k) for k in
                   ("action", "symbol", "price", "sl", "tp", "zone", "zone_touches", "trend", "atr_pips", "time")}
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=200,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Signal: {json.dumps(context)}"}],
        )
        return _parse(response.content[0].text)
    except Exception as exc:  # noqa: BLE001 - any API failure falls back to policy
        approve = settings.filter_failure_mode == "approve"
        return Verdict(approve, 0, f"AI filter error ({exc.__class__.__name__}); failure mode = {settings.filter_failure_mode}")


def _parse(text: str) -> Verdict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON in Claude response: {text!r}")
    data = json.loads(text[start:end + 1])
    return Verdict(
        approve=bool(data["approve"]),
        confidence=int(data.get("confidence", 0)),
        reason=str(data.get("reason", ""))[:500],
    )
