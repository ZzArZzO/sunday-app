"""FIFO reconstruction of held lots from a token's transaction history.

A balance snapshot says *how much* a wallet holds now, not *when* it was
acquired, so the crypto tax holding-period clock (DE/PT 365-day rule) can't run
on it. Given a token's acquire/dispose events, `reconstruct_held_lots` replays
them FIFO — disposals consume the oldest acquisitions first, so what remains are
the most-recent acquisitions — then reconciles the result to the authoritative
current balance (trusting the chain balance for *quantity*, the history for
*dates*). Pure and deterministic; the vendor JSON mapping lives in the connector.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.services.connectors.base import KIND_BUY, CanonicalTransaction
from app.services.connectors.snapshot import TokenBalance

# Reconciliation tolerance. Quantities come from JSON floats (~15-16 sig figs),
# so for large-supply tokens (e.g. 1e9+ units) the absolute rounding error can
# exceed a fixed 1e-8; scale the epsilon with the balance so a float-noise
# residual doesn't spawn a phantom dust lot. Floor at the 8 dp the column stores.
_QTY_EPS = Decimal("0.00000001")
_QTY_REL_EPS = Decimal("1e-9")


def _qty_tolerance(quantity: Decimal) -> Decimal:
    return max(_QTY_EPS, abs(quantity) * _QTY_REL_EPS)


@dataclass(frozen=True)
class LedgerEvent:
    """One normalized transfer for a single token. `acquire` False = disposal."""

    date: datetime
    acquire: bool
    quantity: Decimal  # magnitude >= 0
    unit_price_eur: Decimal | None = None


@dataclass(frozen=True)
class HeldLot:
    date: datetime
    quantity: Decimal
    unit_price_eur: Decimal


def reconstruct_held_lots(
    events: list[LedgerEvent],
    *,
    current_qty: Decimal,
    now: datetime,
    fallback_price: Decimal = Decimal("0"),
) -> list[HeldLot]:
    """FIFO-reconstruct the lots that make up `current_qty`, dated by acquisition.

    Replays events oldest-first; disposals consume the oldest acquisitions, so the
    survivors are the most-recent buys (correct for a remaining-holding clock).
    The result is reconciled to `current_qty`: a surplus the ledger can't explain
    (airdrop / staking / untracked receive) becomes a `now`-dated lot — the
    conservative choice, since it starts the holding clock today rather than
    granting unearned age — and a ledger that overshoots is trimmed oldest-first.
    """
    if current_qty <= 0:
        return []

    queue: deque[list] = deque()  # each entry: [date, qty, price]
    for ev in sorted(events, key=lambda e: e.date):
        if ev.quantity <= 0:
            continue
        if ev.acquire:
            price = ev.unit_price_eur if ev.unit_price_eur is not None else fallback_price
            queue.append([ev.date, ev.quantity, price])
            continue
        # Disposal: consume oldest acquisitions first (FIFO).
        remaining = ev.quantity
        while remaining > 0 and queue:
            front = queue[0]
            if front[1] <= remaining:
                remaining -= front[1]
                queue.popleft()
            else:
                front[1] -= remaining
                remaining = Decimal("0")

    lots = [HeldLot(date=d, quantity=q, unit_price_eur=p) for d, q, p in queue if q > 0]
    total = sum((lot.quantity for lot in lots), Decimal("0"))
    diff = current_qty - total
    eps = _qty_tolerance(current_qty)

    if diff > eps:
        lots.append(HeldLot(date=now, quantity=diff, unit_price_eur=fallback_price))
    elif diff < -eps:
        excess = -diff
        trimmed: list[HeldLot] = []
        for lot in lots:  # oldest first
            if excess <= 0:
                trimmed.append(lot)
            elif lot.quantity <= excess:
                excess -= lot.quantity  # drop this lot entirely
            else:
                trimmed.append(HeldLot(lot.date, lot.quantity - excess, lot.unit_price_eur))
                excess = Decimal("0")
        lots = trimmed

    return lots


def balances_to_dated_transactions(
    balances: list[TokenBalance],
    history: dict[str, list[LedgerEvent]],
    *,
    now: datetime,
) -> list[CanonicalTransaction]:
    """Like `snapshot_to_transactions`, but each token is split into its real
    acquisition lots (FIFO-reconstructed from `history`) so the persisted lots
    carry true purchase dates. A token with no history collapses to one
    `now`-dated lot, i.e. the previous snapshot behaviour.
    """
    txns: list[CanonicalTransaction] = []
    for bal in balances:
        if bal.quantity <= 0:
            continue
        symbol = bal.symbol.upper()
        lots = reconstruct_held_lots(
            history.get(symbol, []),
            current_qty=bal.quantity,
            now=now,
            fallback_price=bal.price_eur or Decimal("0"),
        )
        for lot in lots:
            txns.append(
                CanonicalTransaction(
                    date=lot.date,
                    kind=KIND_BUY,
                    ticker=symbol,
                    isin=None,
                    asset_class="crypto",
                    quantity=lot.quantity,
                    unit_price_eur=lot.unit_price_eur,
                    fees_eur=Decimal("0"),
                )
            )
    return txns
