"""LLM cost ledger — record true token usage + cost for every Anthropic call.

Writes one `llm_call_log` row per call so per-user COGS can be read from live
traffic. Pricing is computed at write time from the model + token counts (cache
reads at 0.1x input, cache writes at 1.25x input), so historical rows stay
correct if list prices change later.

Recording uses its own short-lived session and never raises — observability must
never break the feature it observes (same posture as the AI itself degrading
gracefully). Shared calls (e.g. the weekly market layer) log with user_id=None.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import LlmCallLog

log = logging.getLogger(__name__)

_MILLION = Decimal(1_000_000)
_CACHE_READ_MULT = Decimal("0.1")
_CACHE_WRITE_MULT = Decimal("1.25")

# USD per 1M tokens (input, output). Matched by substring on the model id.
_PRICES: dict[str, tuple[Decimal, Decimal]] = {
    "haiku": (Decimal("1"), Decimal("5")),
    "sonnet": (Decimal("3"), Decimal("15")),
    "opus": (Decimal("5"), Decimal("25")),
    "fable": (Decimal("10"), Decimal("50")),
}


def _tier(model: str) -> str:
    m = (model or "").lower()
    for tier in _PRICES:
        if tier in m:
            return tier
    return "sonnet"  # safe (more expensive) default if the id is unrecognised


def cost_usd(
    model: str, input_tokens: int, output_tokens: int, cache_write: int, cache_read: int
) -> Decimal:
    """Cost of one call in USD, from token counts and the model's list price."""
    price_in, price_out = _PRICES[_tier(model)]
    total = (
        Decimal(input_tokens) * price_in
        + Decimal(cache_read) * price_in * _CACHE_READ_MULT
        + Decimal(cache_write) * price_in * _CACHE_WRITE_MULT
        + Decimal(output_tokens) * price_out
    ) / _MILLION
    return total.quantize(Decimal("0.000001"))


def _tokens(usage: object) -> tuple[int, int, int, int]:
    def g(name: str) -> int:
        val = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, 0)
        return int(val or 0)

    return (
        g("input_tokens"),
        g("output_tokens"),
        g("cache_creation_input_tokens"),
        g("cache_read_input_tokens"),
    )


def record(
    *,
    feature: str,
    model: str,
    usage: object,
    user_id: int | None = None,
    portfolio_id: int | None = None,
) -> None:
    """Persist one call's usage + cost. Never raises."""
    if not model:
        return  # nothing meaningful to log (e.g. a stubbed response in tests)
    try:
        in_tok, out_tok, cw_tok, cr_tok = _tokens(usage)
        db = SessionLocal()
        try:
            db.add(
                LlmCallLog(
                    feature=feature,
                    model=model or "",
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    cache_write_tokens=cw_tok,
                    cache_read_tokens=cr_tok,
                    cost_usd=cost_usd(model, in_tok, out_tok, cw_tok, cr_tok),
                )
            )
            db.commit()
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001 - the ledger must never break the caller
        log.warning("llm cost ledger write failed (%s): %s", feature, exc)


def record_response(
    feature: str, response: object, *, user_id: int | None = None, portfolio_id: int | None = None
) -> None:
    """Convenience: pull model + usage off an Anthropic response and record it."""
    record(
        feature=feature,
        model=getattr(response, "model", "") or "",
        usage=getattr(response, "usage", None),
        user_id=user_id,
        portfolio_id=portfolio_id,
    )


def summary(db: Session, *, days: int = 30) -> dict:
    """Aggregate spend over the last `days`: total, per-feature, and per-user."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    base = select(
        func.coalesce(func.sum(LlmCallLog.cost_usd), 0),
        func.count(LlmCallLog.id),
    ).where(LlmCallLog.created_at >= since)
    total_cost, total_calls = db.execute(base).one()

    by_feature = [
        {"feature": f, "calls": int(n), "cost_usd": str(c)}
        for f, c, n in db.execute(
            select(
                LlmCallLog.feature,
                func.coalesce(func.sum(LlmCallLog.cost_usd), 0),
                func.count(LlmCallLog.id),
            )
            .where(LlmCallLog.created_at >= since)
            .group_by(LlmCallLog.feature)
            .order_by(func.sum(LlmCallLog.cost_usd).desc())
        ).all()
    ]

    by_user = [
        {"user_id": uid, "calls": int(n), "cost_usd": str(c)}
        for uid, c, n in db.execute(
            select(
                LlmCallLog.user_id,
                func.coalesce(func.sum(LlmCallLog.cost_usd), 0),
                func.count(LlmCallLog.id),
            )
            .where(LlmCallLog.created_at >= since)
            .group_by(LlmCallLog.user_id)
            .order_by(func.sum(LlmCallLog.cost_usd).desc())
        ).all()
    ]

    return {
        "days": days,
        "total_cost_usd": str(total_cost),
        "total_calls": int(total_calls),
        "by_feature": by_feature,
        "by_user": by_user,
    }
