"""CSV ingestor with auto-detected broker format.

Supported formats:

  1. Sunday's normalised columns (legacy):
        date, type, ticker, isin, asset_class, quantity, unit_price_eur, fees_eur

  2. Trade Republic export (auto-detected):
        Date, Type, Asset, ISIN, Shares, Price per share, Total, Fee, Tax, ...
        — German variants ("Datum", "Typ", "Stück", "Preis pro Anteil") also recognised.

Transaction types handled (EU average-cost method):
  - BUY      → weighted-average cost update, creates an audit Lot.
  - SELL     → reduces quantity; avg cost is UNCHANGED (EU Durchschnittsmethode).
  - SPLIT    → scales quantity by the ratio, inverse-scales avg cost (basis preserved).
               If no ratio is available it's flagged for review, not guessed.
  - DIVIDEND → does not affect holdings (cash event); counted, not stored.

Per-position state is derived by replaying that ticker's transactions in date
order over a (quantity, total_cost) pool, then writing quantity + avg_cost_eur.
For buys-only this reproduces the previous weighted-average exactly.

The ingestor strips PII columns (broker_account_id, iban, name, etc.) by simply
not reading them. Asset class is inferred from ISIN prefix + symbol when not
explicitly provided (TR exports don't include it).
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

KIND_BUY = "buy"
KIND_SELL = "sell"
KIND_DIVIDEND = "dividend"
KIND_SPLIT = "split"
_HOLDING_KINDS = {KIND_BUY, KIND_SELL}

ALLOWED_ASSET_CLASSES = {"stock", "etf", "crypto", "cash"}

# Header aliases. Lowercased + stripped before matching.
HEADER_ALIASES: dict[str, set[str]] = {
    "date": {"date", "datum", "executed at", "transaction date", "trade date"},
    "type": {"type", "typ", "transaction type", "action"},
    "ticker": {"ticker", "symbol", "asset", "instrument", "name"},
    "isin": {"isin", "instrument id"},
    "asset_class": {"asset_class", "asset class", "class", "category"},
    "quantity": {"quantity", "shares", "stück", "qty", "units", "amount"},
    "unit_price_eur": {
        "unit_price_eur",
        "price per share",
        "preis pro anteil",
        "share price",
        "unit price",
        "price",
    },
    "fees_eur": {"fees_eur", "fee", "fees", "gebühr", "commission"},
    "split_ratio": {"split_ratio", "split ratio", "ratio"},
}


# Heuristics to classify when the CSV doesn't tell us.
CRYPTO_SYMBOLS = {"BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "XRP", "DOGE", "LINK"}
ETF_ISIN_PREFIXES = ("IE", "LU")  # Most UCITS ETFs are Irish or Luxembourg domiciled


@dataclass
class ParsedRow:
    date: datetime
    kind: str
    ticker: str
    isin: str | None
    asset_class: str
    quantity: Decimal  # magnitude (>= 0); 0 when not applicable (e.g. dividend)
    unit_price_eur: Decimal
    fees_eur: Decimal
    split_ratio: Decimal | None


@dataclass
class IngestionContext:
    warnings: list[str] = field(default_factory=list)
    rows_read: int = 0
    positions_created: int = 0
    positions_updated: int = 0
    lots_created: int = 0
    sells_applied: int = 0
    dividends_seen: int = 0
    splits_applied: int = 0
    detected_format: str = "unknown"


@dataclass
class _Pool:
    """A position's average-cost pool: total quantity and total cost basis."""

    qty: Decimal
    total_cost: Decimal


def _normalise_header(raw: str) -> str:
    return raw.strip().lower().replace("﻿", "")


def _alias_to_canonical(header: str) -> str | None:
    h = _normalise_header(header)
    for canonical, aliases in HEADER_ALIASES.items():
        if h in aliases:
            return canonical
    return None


def _build_column_map(fieldnames: list[str]) -> dict[str, str]:
    """Map raw CSV headers → canonical column names we understand."""
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        canonical = _alias_to_canonical(raw)
        if canonical is not None and canonical not in mapping.values():
            mapping[raw] = canonical
    return mapping


def _detect_format(fieldnames: list[str]) -> str:
    normalised = {_normalise_header(h) for h in fieldnames}
    if {"date", "type", "ticker", "asset_class"}.issubset(normalised):
        return "sunday_native"
    if {"isin"}.issubset(normalised) and (
        "shares" in normalised or "stück" in normalised
    ):
        return "trade_republic"
    return "generic"


def _classify_kind(raw_type: str) -> str | None:
    """Map a broker transaction type to a Sunday kind (None = unsupported)."""
    t = raw_type.strip().lower()
    if not t:
        return None
    # Order matters: check split/dividend before sell/buy.
    if "split" in t:
        return KIND_SPLIT
    if any(k in t for k in ("dividend", "dividende", "distribution", "ausschüttung", "ausschuttung")):
        return KIND_DIVIDEND
    if any(k in t for k in ("sell", "verkauf", "sale", "sold")):
        return KIND_SELL
    if any(k in t for k in ("buy", "kauf", "purchase", "sparplan", "saveback", "savings", "reinvest")):
        return KIND_BUY
    return None


def _safe_decimal(raw: str, *, field_name: str, ctx: IngestionContext) -> Decimal | None:
    if raw is None:
        return None
    cleaned = raw.strip().replace("€", "").replace(" ", "").replace("\xa0", "")
    if not cleaned:
        return None
    # Handle European decimals: 1.234,56 → 1234.56
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, AttributeError):
        ctx.warnings.append(f"could not parse {field_name}={raw!r}; skipping row")
        return None


def _parse_date(raw: str) -> datetime | None:
    raw = raw.strip()
    formats = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _infer_asset_class(ticker: str, isin: str | None) -> str:
    if ticker.upper() in CRYPTO_SYMBOLS:
        return "crypto"
    if isin and isin[:2] in ETF_ISIN_PREFIXES:
        return "etf"
    return "stock"


def _row_get(row: dict[str, str], column_map: dict[str, str], canonical: str) -> str | None:
    for raw, mapped in column_map.items():
        if mapped == canonical:
            return row.get(raw)
    return None


def _parse_row(
    row: dict[str, str], column_map: dict[str, str], ctx: IngestionContext
) -> ParsedRow | None:
    date_raw = _row_get(row, column_map, "date")
    type_raw = _row_get(row, column_map, "type")
    ticker_raw = _row_get(row, column_map, "ticker")

    for label, value in (("date", date_raw), ("type", type_raw), ("ticker", ticker_raw)):
        if not value:
            ctx.warnings.append(f"missing column {label!r}; skipping row")
            return None

    kind = _classify_kind(type_raw)
    if kind is None:
        ctx.warnings.append(f"unsupported type {type_raw!r}; skipping row")
        return None

    date = _parse_date(date_raw)
    if date is None:
        ctx.warnings.append(f"unparseable date {date_raw!r}; skipping")
        return None

    qty = _safe_decimal(_row_get(row, column_map, "quantity") or "", field_name="quantity", ctx=ctx)
    price = _safe_decimal(
        _row_get(row, column_map, "unit_price_eur") or "", field_name="unit_price_eur", ctx=ctx
    )
    fees = _safe_decimal(_row_get(row, column_map, "fees_eur") or "0", field_name="fees_eur", ctx=ctx) or Decimal("0")
    ratio = _safe_decimal(
        _row_get(row, column_map, "split_ratio") or "", field_name="split_ratio", ctx=ctx
    )

    # Per-kind requirements.
    if kind in _HOLDING_KINDS:
        if qty is None or qty == 0:
            ctx.warnings.append(f"{kind} row for {ticker_raw!r} has no quantity; skipping")
            return None
        qty = abs(qty)  # direction comes from `kind`, not the sign
    if kind == KIND_BUY and price is None:
        ctx.warnings.append(f"buy row for {ticker_raw!r} has no price; skipping")
        return None

    isin = _row_get(row, column_map, "isin")
    isin = isin.strip() if isin else None
    if isin == "":
        isin = None

    asset_class_raw = _row_get(row, column_map, "asset_class")
    if asset_class_raw:
        asset_class = asset_class_raw.strip().lower()
        if asset_class not in ALLOWED_ASSET_CLASSES:
            ctx.warnings.append(f"unknown asset_class {asset_class!r}; inferring")
            asset_class = _infer_asset_class(ticker_raw, isin)
    else:
        asset_class = _infer_asset_class(ticker_raw, isin)

    return ParsedRow(
        date=date,
        kind=kind,
        ticker=ticker_raw.strip().upper(),
        isin=isin,
        asset_class=asset_class,
        quantity=qty or Decimal("0"),
        unit_price_eur=price or Decimal("0"),
        fees_eur=fees,
        split_ratio=ratio,
    )


def _build_position_index(portfolio: Portfolio) -> dict[str, Position]:
    return {p.ticker: p for p in portfolio.positions}


def _get_or_create_position(
    db: Session,
    portfolio: Portfolio,
    rows: list[ParsedRow],
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


def _apply(pool: _Pool, row: ParsedRow, ctx: IngestionContext) -> None:
    if row.kind == KIND_BUY:
        pool.qty += row.quantity
        pool.total_cost += row.quantity * row.unit_price_eur + row.fees_eur
        return

    if row.kind == KIND_SELL:
        if pool.qty <= 0:
            ctx.warnings.append(
                f"SELL_IGNORED: {row.ticker} — sell of {row.quantity} but no holdings"
            )
            return
        sell_qty = min(row.quantity, pool.qty)
        avg = pool.total_cost / pool.qty
        pool.total_cost -= sell_qty * avg  # remove at avg → avg unchanged (EU method)
        pool.qty -= sell_qty
        ctx.sells_applied += 1
        if row.quantity > sell_qty:
            ctx.warnings.append(
                f"SELL_CLAMPED: {row.ticker} — sold {row.quantity} but only {sell_qty} held"
            )
        return

    if row.kind == KIND_SPLIT:
        if row.split_ratio and row.split_ratio > 0:
            pool.qty *= row.split_ratio  # total_cost unchanged → avg /= ratio
            ctx.splits_applied += 1
        else:
            ctx.warnings.append(
                f"SPLIT_FLAGGED: {row.ticker} — split detected but no ratio; review holdings"
            )
        return

    if row.kind == KIND_DIVIDEND:
        ctx.dividends_seen += 1  # cash event; does not affect holdings


def _finalize_position(position: Position, pool: _Pool) -> None:
    position.quantity = pool.qty.quantize(Decimal("0.00000001"))
    if pool.qty > 0:
        position.avg_cost_eur = (pool.total_cost / pool.qty).quantize(Decimal("0.0001"))
    # On a fully-closed position, keep the last avg cost for reference; qty 0
    # makes its value zero in pnl.


def _summary_warning(ctx: IngestionContext) -> str | None:
    parts = []
    if ctx.sells_applied:
        parts.append(f"{ctx.sells_applied} sell(s) applied")
    if ctx.dividends_seen:
        parts.append(f"{ctx.dividends_seen} dividend row(s) recorded (no holdings change)")
    if ctx.splits_applied:
        parts.append(f"{ctx.splits_applied} split(s) applied")
    return "; ".join(parts) if parts else None


@dataclass
class PreviewColumn:
    source: str  # raw CSV header
    mapped_to: str  # canonical column we understood it as
    confidence: str  # "high" (alias-matched)
    sample: str | None


@dataclass
class PreviewRow:
    line: int  # 1-based line in the file (2 = first data row)
    status: str  # "ok" | "skipped"
    reason: str | None
    date: str | None = None
    kind: str | None = None
    ticker: str | None = None
    quantity: str | None = None
    unit_price_eur: str | None = None


@dataclass
class PreviewResult:
    detected_format: str
    columns: list[PreviewColumn]
    unmapped_headers: list[str]
    rows: list[PreviewRow]
    ok_count: int
    skipped_count: int
    warnings: list[str]


_PREVIEW_ROW_CAP = 200


def preview_csv(raw_csv: str) -> PreviewResult:
    """Parse a CSV WITHOUT touching the DB — powers the import wizard's review step.

    Reuses the same detection + per-row parsing as `ingest_csv`, but reports each
    row's status (ok / skipped + reason) and the detected column mapping instead
    of committing anything.
    """
    ctx = IngestionContext()
    reader = csv.DictReader(StringIO(raw_csv))
    fieldnames = list(reader.fieldnames or [])
    if not fieldnames:
        return PreviewResult("unknown", [], [], [], 0, 0, ["CSV has no header row"])

    detected = _detect_format(fieldnames)
    column_map = _build_column_map(fieldnames)
    data_rows = list(reader)
    first = data_rows[0] if data_rows else {}

    columns = [
        PreviewColumn(source=raw, mapped_to=canonical, confidence="high", sample=(first.get(raw) or None))
        for raw, canonical in column_map.items()
    ]
    mapped_sources = set(column_map.keys())
    unmapped = [h for h in fieldnames if h not in mapped_sources]

    rows: list[PreviewRow] = []
    ok = skipped = 0
    for line, row in enumerate(data_rows[:_PREVIEW_ROW_CAP], start=2):
        before = len(ctx.warnings)
        parsed = _parse_row(row, column_map, ctx)
        if parsed is None:
            skipped += 1
            reason = ctx.warnings[-1] if len(ctx.warnings) > before else "skipped"
            rows.append(PreviewRow(line=line, status="skipped", reason=reason))
        else:
            ok += 1
            rows.append(
                PreviewRow(
                    line=line,
                    status="ok",
                    reason=None,
                    date=parsed.date.date().isoformat(),
                    kind=parsed.kind,
                    ticker=parsed.ticker,
                    quantity=str(parsed.quantity),
                    unit_price_eur=str(parsed.unit_price_eur),
                )
            )

    warnings: list[str] = []
    if not column_map:
        warnings.append(f"No recognised columns found. Headers: {fieldnames}")
    if len(data_rows) > _PREVIEW_ROW_CAP:
        warnings.append(f"Showing the first {_PREVIEW_ROW_CAP} of {len(data_rows)} rows.")

    return PreviewResult(detected, columns, unmapped, rows, ok, skipped, warnings)


def ingest_csv(db: Session, portfolio: Portfolio, raw_csv: str) -> IngestResult:
    ctx = IngestionContext()
    reader = csv.DictReader(StringIO(raw_csv))
    fieldnames = list(reader.fieldnames or [])
    if not fieldnames:
        return IngestResult(
            rows_read=0,
            positions_created=0,
            positions_updated=0,
            lots_created=0,
            warnings=["CSV has no header row"],
        )

    ctx.detected_format = _detect_format(fieldnames)
    column_map = _build_column_map(fieldnames)
    if not column_map:
        return IngestResult(
            rows_read=0,
            positions_created=0,
            positions_updated=0,
            lots_created=0,
            warnings=[
                f"No recognised columns found. Detected format: {ctx.detected_format}. "
                f"Headers: {fieldnames}"
            ],
        )

    # Parse every row first, grouping by ticker (preserve first-seen order).
    groups: dict[str, list[ParsedRow]] = {}
    for row in reader:
        ctx.rows_read += 1
        parsed = _parse_row(row, column_map, ctx)
        if parsed is None:
            continue
        groups.setdefault(parsed.ticker, []).append(parsed)

    index = _build_position_index(portfolio)

    for ticker, rows in groups.items():
        existing = index.get(ticker)
        has_holding = any(r.kind in _HOLDING_KINDS for r in rows)
        if existing is None and not has_holding:
            kinds = ", ".join(sorted({r.kind for r in rows}))
            ctx.warnings.append(
                f"SKIPPED: {ticker} — {kinds} with no buy/holding to attach to"
            )
            continue

        pos, created = _get_or_create_position(db, portfolio, rows, index)

        holding_rows = [r for r in rows if r.kind in _HOLDING_KINDS]
        if created:
            ctx.positions_created += 1
            ctx.positions_updated += max(len(holding_rows) - 1, 0)
        else:
            ctx.positions_updated += len(holding_rows)

        pool = _seed_pool(pos)
        for r in sorted(rows, key=lambda x: x.date):
            if r.kind == KIND_BUY:
                lot = Lot(
                    position_id=pos.id,
                    purchased_at=r.date,
                    quantity=r.quantity,
                    unit_cost_eur=r.unit_price_eur,
                    fees_eur=r.fees_eur,
                    source=ctx.detected_format,
                )
                pos.lots.append(lot)
                db.add(lot)
                ctx.lots_created += 1
            _apply(pool, r, ctx)

        _finalize_position(pos, pool)

    db.commit()

    warnings = ctx.warnings
    summary = _summary_warning(ctx)
    if summary:
        warnings = [summary, *warnings]
    if ctx.detected_format != "sunday_native":
        warnings = [f"Detected format: {ctx.detected_format}", *warnings]

    return IngestResult(
        rows_read=ctx.rows_read,
        positions_created=ctx.positions_created,
        positions_updated=ctx.positions_updated,
        lots_created=ctx.lots_created,
        warnings=warnings,
    )
