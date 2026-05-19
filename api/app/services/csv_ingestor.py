"""TR-style CSV ingestor.

Expected columns (subset of a Trade Republic export, normalised):
    date, type, ticker, isin, asset_class, quantity, unit_price_eur, fees_eur

`type` is "buy" or "sell". For the MVP slice only buy rows are honoured; sell
handling (FIFO lot consumption) is Phase 2.

The ingestor strips columns we don't want to persist (PII columns like
broker_account_id, iban, name, etc.) by simply not reading them.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from sqlalchemy.orm import Session

from app.models import Lot, Portfolio, Position
from app.schemas import IngestResult

ACCEPTED_TYPES = {"buy"}
ALLOWED_ASSET_CLASSES = {"stock", "etf", "crypto", "cash"}


@dataclass
class ParsedRow:
    date: datetime
    type_: str
    ticker: str
    isin: str | None
    asset_class: str
    quantity: Decimal
    unit_price_eur: Decimal
    fees_eur: Decimal


@dataclass
class IngestionContext:
    warnings: list[str] = field(default_factory=list)
    rows_read: int = 0
    positions_created: int = 0
    positions_updated: int = 0
    lots_created: int = 0


def _safe_decimal(raw: str, *, field_name: str, ctx: IngestionContext) -> Decimal | None:
    try:
        return Decimal(raw.replace(",", ".").strip())
    except (InvalidOperation, AttributeError):
        ctx.warnings.append(f"could not parse {field_name}={raw!r}; skipping row")
        return None


def _parse_row(row: dict[str, str], ctx: IngestionContext) -> ParsedRow | None:
    required = ("date", "type", "ticker", "asset_class", "quantity", "unit_price_eur")
    for key in required:
        if not row.get(key):
            ctx.warnings.append(f"missing column {key!r}; skipping row")
            return None

    type_ = row["type"].strip().lower()
    if type_ not in ACCEPTED_TYPES:
        ctx.warnings.append(f"row type {type_!r} not supported in MVP; skipping")
        return None

    asset_class = row["asset_class"].strip().lower()
    if asset_class not in ALLOWED_ASSET_CLASSES:
        ctx.warnings.append(f"unknown asset_class {asset_class!r}; skipping")
        return None

    try:
        date = datetime.fromisoformat(row["date"].strip())
    except ValueError:
        ctx.warnings.append(f"unparseable date {row['date']!r}; skipping")
        return None

    qty = _safe_decimal(row["quantity"], field_name="quantity", ctx=ctx)
    price = _safe_decimal(row["unit_price_eur"], field_name="unit_price_eur", ctx=ctx)
    fees = _safe_decimal(row.get("fees_eur") or "0", field_name="fees_eur", ctx=ctx) or Decimal("0")
    if qty is None or price is None:
        return None

    return ParsedRow(
        date=date,
        type_=type_,
        ticker=row["ticker"].strip().upper(),
        isin=(row.get("isin") or "").strip() or None,
        asset_class=asset_class,
        quantity=qty,
        unit_price_eur=price,
        fees_eur=fees,
    )


def _get_or_create_position(
    db: Session, portfolio: Portfolio, parsed: ParsedRow, ctx: IngestionContext
) -> Position:
    existing = next(
        (p for p in portfolio.positions if p.ticker == parsed.ticker),
        None,
    )
    if existing is not None:
        ctx.positions_updated += 1
        if parsed.isin and not existing.isin:
            existing.isin = parsed.isin
        return existing

    pos = Position(
        portfolio_id=portfolio.id,
        ticker=parsed.ticker,
        isin=parsed.isin,
        asset_class=parsed.asset_class,
        currency="EUR",
    )
    db.add(pos)
    db.flush()  # populate pos.id for lot FK
    portfolio.positions.append(pos)
    ctx.positions_created += 1
    return pos


def _recompute_weighted_avg(position: Position) -> None:
    total_qty = sum((lot.quantity for lot in position.lots), start=Decimal("0"))
    total_cost = sum(
        (lot.quantity * lot.unit_cost_eur + lot.fees_eur for lot in position.lots),
        start=Decimal("0"),
    )
    position.quantity = total_qty
    position.avg_cost_eur = (
        (total_cost / total_qty).quantize(Decimal("0.0001"))
        if total_qty > 0
        else Decimal("0")
    )


def ingest_csv(db: Session, portfolio: Portfolio, raw_csv: str) -> IngestResult:
    ctx = IngestionContext()
    reader = csv.DictReader(StringIO(raw_csv))

    for row in reader:
        ctx.rows_read += 1
        parsed = _parse_row(row, ctx)
        if parsed is None:
            continue

        pos = _get_or_create_position(db, portfolio, parsed, ctx)
        lot = Lot(
            position_id=pos.id,
            purchased_at=parsed.date,
            quantity=parsed.quantity,
            unit_cost_eur=parsed.unit_price_eur,
            fees_eur=parsed.fees_eur,
            source="tr_csv",
        )
        pos.lots.append(lot)
        db.add(lot)
        ctx.lots_created += 1
        _recompute_weighted_avg(pos)

    db.commit()
    return IngestResult(
        rows_read=ctx.rows_read,
        positions_created=ctx.positions_created,
        positions_updated=ctx.positions_updated,
        lots_created=ctx.lots_created,
        warnings=ctx.warnings,
    )
