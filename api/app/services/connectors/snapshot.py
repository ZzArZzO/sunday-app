"""Shared 'current balances' snapshot model for live connectors.

Both the crypto-address and exchange connectors report *current* balances rather
than a transaction history, so they share one representation (`TokenBalance`) and
one translation to canonical buy-like transactions. A snapshot has no cost-basis
history, so each asset is a single lot at the current price (value is right today;
cost-basis-from-source is a later refinement).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from app.services.connectors.base import KIND_BUY, CanonicalTransaction


@dataclass(frozen=True)
class TokenBalance:
    symbol: str
    quantity: Decimal
    price_eur: Decimal | None = None


def snapshot_to_transactions(
    balances: list[TokenBalance], *, asset_class: str = "crypto"
) -> list[CanonicalTransaction]:
    now = datetime.now(timezone.utc)
    txns: list[CanonicalTransaction] = []
    for bal in balances:
        if bal.quantity <= 0:
            continue
        txns.append(
            CanonicalTransaction(
                date=now,
                kind=KIND_BUY,
                ticker=bal.symbol.upper(),
                isin=None,
                asset_class=asset_class,
                quantity=bal.quantity,
                unit_price_eur=bal.price_eur or Decimal("0"),
                fees_eur=Decimal("0"),
            )
        )
    return txns


def to_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
