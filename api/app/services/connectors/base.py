"""Connector core: a provider-agnostic transaction model + the shared
average-cost replay that turns transactions into Positions and Lots.

Every import method (CSV, manual, on-chain address, exchange API) implements
`ImportSource` by producing `CanonicalTransaction`s; `apply_transactions`
persists them identically. `csv_ingestor` was the first such source and now
delegates its replay/persist step here.

Quantities are magnitudes (>= 0); direction comes from `kind`, never the sign.
EU average-cost (Durchschnittsmethode): buys update the weighted average, sells
leave it unchanged, splits scale quantity and inverse-scale the average.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from sqlalchemy.orm import Session

from app.models import Lot, Portfolio, Position

if TYPE_CHECKING:
    from app.models import Connection

KIND_BUY = "buy"
KIND_SELL = "sell"
KIND_DIVIDEND = "dividend"
KIND_SPLIT = "split"
_HOLDING_KINDS = {KIND_BUY, KIND_SELL}

ALLOWED_ASSET_CLASSES = {"stock", "etf", "crypto", "cash"}


@dataclass
class CanonicalTransaction:
    """One provider-agnostic transaction. Quantity is a magnitude (>= 0)."""

    date: datetime
    kind: str
    ticker: str
    isin: str | None
    asset_class: str
    quantity: Decimal
    unit_price_eur: Decimal
    fees_eur: Decimal
    split_ratio: Decimal | None = None


@runtime_checkable
class ImportSource(Protocol):
    """A portfolio import method.

    Implementations read from a file, an API, or a chain and return canonical
    transactions; `apply_transactions` persists them. `kind` is one of
    manual | csv | address | exchange and matches `Connection.kind`.
    """

    kind: str

    def fetch(self) -> list[CanonicalTransaction]: ...


class HoldingsLimitExceeded(Exception):  # noqa: N818 - public name kept; callers import it
    """Raised when applying transactions would push a free portfolio past its cap."""

    def __init__(self, limit: int, attempted: int) -> None:
        self.limit = limit
        self.attempted = attempted
        super().__init__(
            f"Free plan allows {limit} holdings; this import would result in {attempted}."
        )


class ConnectorNotConfigured(Exception):  # noqa: N818 - mirrors billing's BillingNotConfigured
    """Raised when a live connector's provider/credentials aren't configured.

    Routes translate this to a 503, like billing/LLM/email without their keys.
    """


@dataclass
class ApplyResult:
    """Counts + warnings from a single apply pass (provider-agnostic)."""

    positions_created: int = 0
    positions_updated: int = 0
    lots_created: int = 0
    sells_applied: int = 0
    dividends_seen: int = 0
    splits_applied: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class _Pool:
    """A position's average-cost pool: total quantity and total cost basis."""

    qty: Decimal
    total_cost: Decimal


def _build_position_index(portfolio: Portfolio) -> dict[str, Position]:
    return {p.ticker: p for p in portfolio.positions}


def _get_or_create_position(
    db: Session,
    portfolio: Portfolio,
    rows: list[CanonicalTransaction],
    index: dict[str, Position],
) -> tuple[Position, bool]:
    ticker = rows[0].ticker
    existing = index.get(ticker)
    if existing is not None:
        # Backfill ISIN if we now know it.
        for r in rows:
            if r.isin and not existing.isin:
                existing.isin = r.isin
                break
        return existing, False

    first = rows[0]
    pos = Position(
        portfolio_id=portfolio.id,
        ticker=ticker,
        isin=next((r.isin for r in rows if r.isin), None),
        asset_class=first.asset_class,
        currency="EUR",
    )
    db.add(pos)
    db.flush()  # populate pos.id for lot FK
    portfolio.positions.append(pos)
    index[ticker] = pos
    return pos, True


def _seed_pool(position: Position) -> _Pool:
    qty = position.quantity or Decimal("0")
    avg = position.avg_cost_eur or Decimal("0")
    return _Pool(qty=qty, total_cost=qty * avg)


def _apply(pool: _Pool, row: CanonicalTransaction, result: ApplyResult) -> None:
    if row.kind == KIND_BUY:
        pool.qty += row.quantity
        pool.total_cost += row.quantity * row.unit_price_eur + row.fees_eur
        return

    if row.kind == KIND_SELL:
        if pool.qty <= 0:
            result.warnings.append(
                f"SELL_IGNORED: {row.ticker} — sell of {row.quantity} but no holdings"
            )
            return
        sell_qty = min(row.quantity, pool.qty)
        avg = pool.total_cost / pool.qty
        pool.total_cost -= sell_qty * avg  # remove at avg → avg unchanged (EU method)
        pool.qty -= sell_qty
        result.sells_applied += 1
        if row.quantity > sell_qty:
            result.warnings.append(
                f"SELL_CLAMPED: {row.ticker} — sold {row.quantity} but only {sell_qty} held"
            )
        return

    if row.kind == KIND_SPLIT:
        if row.split_ratio and row.split_ratio > 0:
            pool.qty *= row.split_ratio  # total_cost unchanged → avg /= ratio
            result.splits_applied += 1
        else:
            result.warnings.append(
                f"SPLIT_FLAGGED: {row.ticker} — split detected but no ratio; review holdings"
            )
        return

    if row.kind == KIND_DIVIDEND:
        result.dividends_seen += 1  # cash event; does not affect holdings


def _finalize_position(position: Position, pool: _Pool) -> None:
    position.quantity = pool.qty.quantize(Decimal("0.00000001"))
    if pool.qty > 0:
        position.avg_cost_eur = (pool.total_cost / pool.qty).quantize(Decimal("0.0001"))
    # On a fully-closed position, keep the last avg cost for reference; qty 0
    # makes its value zero in pnl.


def apply_transactions(
    db: Session,
    portfolio: Portfolio,
    txns: list[CanonicalTransaction],
    *,
    source_label: str = "manual",
    connection: Connection | None = None,
    max_holdings: int | None = None,
) -> ApplyResult:
    """Replay canonical transactions into the portfolio's Positions and Lots.

    Groups by ticker (first-seen order), replays each group's transactions in
    date order over a (quantity, total_cost) pool, and writes back quantity +
    avg_cost. Buys also create an audit `Lot` tagged with `source_label` and the
    originating `connection`. Commits on success; rolls back and raises
    `HoldingsLimitExceeded` if the free-tier cap would be exceeded.
    """
    result = ApplyResult()

    groups: dict[str, list[CanonicalTransaction]] = {}
    for t in txns:
        groups.setdefault(t.ticker, []).append(t)

    index = _build_position_index(portfolio)
    connection_id = connection.id if connection is not None else None

    for ticker, rows in groups.items():
        existing = index.get(ticker)
        has_holding = any(r.kind in _HOLDING_KINDS for r in rows)
        if existing is None and not has_holding:
            kinds = ", ".join(sorted({r.kind for r in rows}))
            result.warnings.append(
                f"SKIPPED: {ticker} — {kinds} with no buy/holding to attach to"
            )
            continue

        pos, created = _get_or_create_position(db, portfolio, rows, index)

        holding_rows = [r for r in rows if r.kind in _HOLDING_KINDS]
        if created:
            result.positions_created += 1
            result.positions_updated += max(len(holding_rows) - 1, 0)
        else:
            result.positions_updated += len(holding_rows)

        pool = _seed_pool(pos)
        for r in sorted(rows, key=lambda x: x.date):
            if r.kind == KIND_BUY:
                lot = Lot(
                    position_id=pos.id,
                    purchased_at=r.date,
                    quantity=r.quantity,
                    unit_cost_eur=r.unit_price_eur,
                    fees_eur=r.fees_eur,
                    source=source_label,
                    connection_id=connection_id,
                )
                pos.lots.append(lot)
                db.add(lot)
                result.lots_created += 1
            _apply(pool, r, result)

        _finalize_position(pos, pool)

    # Enforce the holdings cap before persisting, so a free user never lands a
    # partial import. `index` holds every position touched plus pre-existing ones.
    if max_holdings is not None:
        held = sum(1 for p in index.values() if p.quantity is not None and p.quantity > 0)
        if held > max_holdings:
            db.rollback()
            raise HoldingsLimitExceeded(max_holdings, held)

    db.commit()
    return result


def replace_connection_lots(
    db: Session,
    portfolio: Portfolio,
    connection: Connection,
    txns: list[CanonicalTransaction],
    *,
    max_holdings: int | None = None,
) -> ApplyResult:
    """Re-sync a *live* source: drop this connection's existing lots, then apply
    the freshly-fetched transactions and recompute affected positions.

    Live connectors (address / exchange) report *current* balances, not a full
    transaction history, so each asset is one buy-like lot and replacing is safe.
    Do NOT use this for CSV/manual sources, which carry sell/split history that
    isn't persisted as lots and would be lost on recompute.
    """
    stale = db.query(Lot).filter(Lot.connection_id == connection.id).all()
    touched_position_ids = {lot.position_id for lot in stale}
    for lot in stale:
        db.delete(lot)
    db.flush()

    # Recompute positions that lost lots, from whatever lots remain (any source).
    index = _build_position_index(portfolio)
    for pos in index.values():
        if pos.id not in touched_position_ids:
            continue
        _recompute_position_from_lots(db, pos)

    return apply_transactions(
        db,
        portfolio,
        txns,
        source_label=f"conn:{connection.id}",
        connection=connection,
        max_holdings=max_holdings,
    )


def replace_csv_import(
    db: Session,
    portfolio: Portfolio,
    connection: Connection,
    detected_format: str,
    txns: list[CanonicalTransaction],
    *,
    max_holdings: int | None = None,
) -> ApplyResult:
    """Re-importing the same (or an updated) CSV export should replace what a
    prior import through this connection created, not double it. A CSV has no
    natural idempotency key of its own (Trade Republic includes a
    transaction_id we don't currently track) -- without this, a second import
    of an unchanged file silently reapplies every buy/sell and inflates every
    quantity, which is exactly what happened importing the same 854-row file
    twice: every position ended up at roughly double its real size.

    `_get_or_create_csv_connection` (routes/ingest.py) already gives every CSV
    upload a persistent Connection keyed by broker label, specifically so
    re-uploads of the same broker update that source rather than spawning
    duplicates -- this is the same connection-scoping `replace_connection_lots`
    uses for live sync, just without its recompute-from-remaining-lots step,
    which would be wrong here: CSV history includes sells/splits that aren't
    persisted as lots, so recomputing from remaining buy lots alone would
    silently lose that history. Deleting the whole position and replaying the
    fresh file's full history avoids that.

    Deletes positions where EVERY lot came from this connection (never a
    different broker's connection, and never a manually-entered or
    differently-sourced lot for the same ticker -- that mixed case is left
    untouched rather than guessed at).
    """
    stale = [
        p
        for p in portfolio.positions
        if p.lots and all(lot.connection_id == connection.id for lot in p.lots)
    ]
    for pos in stale:
        # Both sides: db.delete() alone leaves the now-stale ORM instance in
        # portfolio.positions' already-loaded collection, which the
        # apply_transactions call below also reads via _build_position_index.
        portfolio.positions.remove(pos)
        db.delete(pos)
    db.flush()

    return apply_transactions(
        db,
        portfolio,
        txns,
        source_label=detected_format,
        connection=connection,
        max_holdings=max_holdings,
    )


def _recompute_position_from_lots(db: Session, position: Position) -> None:
    """Rebuild a position's quantity + avg cost from its remaining buy lots.

    Buy-only weighted average — correct for live snapshot sources, which is the
    only path that calls this (see `replace_connection_lots`).
    """
    remaining = db.query(Lot).filter(Lot.position_id == position.id).all()
    total_qty = sum((lot.quantity for lot in remaining), Decimal("0"))
    total_cost = sum(
        (lot.quantity * lot.unit_cost_eur + lot.fees_eur for lot in remaining),
        Decimal("0"),
    )
    position.quantity = total_qty.quantize(Decimal("0.00000001"))
    if total_qty > 0:
        position.avg_cost_eur = (total_cost / total_qty).quantize(Decimal("0.0001"))
