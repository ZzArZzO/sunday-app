"""CSV ingestor with auto-detected broker format.

The CSV-specific concern here is *parsing*: detect the broker layout, map raw
headers to canonical columns, and turn each row into a `CanonicalTransaction`.
The provider-agnostic *replay/persist* step (average-cost pool → Positions +
Lots, holdings-cap enforcement) lives in `services/connectors/base.py` and is
shared with the live connectors. CSV is simply the first `ImportSource`.

Supported formats:

  1. Sunday's normalised columns (legacy):
        date, type, ticker, isin, asset_class, quantity, unit_price_eur, fees_eur

  2. Trade Republic export, older layout (auto-detected):
        Date, Type, Asset, ISIN, Shares, Price per share, Total, Fee, Tax, ...
        — German variants ("Datum", "Typ", "Stück", "Preis pro Anteil") also recognised.

  3. Trade Republic "Transaction export", current layout (auto-detected as
     trade_republic_v2): datetime, date, account_type, category, type,
     asset_class, name, symbol, shares, price, amount, fee, tax, currency, ...
     — no column literally called "isin"; it lives inside `symbol`, and `name`
     carries the human-readable instrument name instead of a ticker. Needs its
     own column map (TRADE_REPUBLIC_V2_HEADER_ALIASES) rather than the generic
     alias table: `name` and `symbol` would otherwise both match the generic
     "ticker" alias, and whichever loses that race has its ISIN silently
     dropped for every position.

Transaction types handled (EU average-cost method):
  - BUY      → weighted-average cost update, creates an audit Lot.
  - SELL     → reduces quantity; avg cost is UNCHANGED (EU Durchschnittsmethode).
  - SPLIT    → scales quantity by the ratio, inverse-scales avg cost (basis preserved).
               If no ratio is available it's flagged for review, not guessed.
  - DIVIDEND → does not affect holdings (cash event); counted, not stored.

The ingestor strips PII columns (broker_account_id, iban, name, etc.) by simply
not reading them. Asset class is inferred from ISIN prefix + symbol when not
explicitly provided (TR exports don't include it).
"""

from __future__ import annotations

import csv
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models import Portfolio
from app.schemas import IngestResult

if TYPE_CHECKING:
    from app.models import Connection
from app.services.connectors.base import (
    _HOLDING_KINDS,
    ALLOWED_ASSET_CLASSES,
    KIND_BUY,
    KIND_DIVIDEND,
    KIND_SELL,
    KIND_SPLIT,
    ApplyResult,
    CanonicalTransaction,
    HoldingsLimitExceeded,
    apply_transactions,
)

# Re-exported so existing callers (routes/ingest.py, tests) keep working.
__all__ = ["HoldingsLimitExceeded", "ingest_csv", "preview_csv"]

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


# Modern Trade Republic "Transaction export" (their current downloadable CSV,
# distinct from the older Date/Type/Asset/ISIN/Shares layout HEADER_ALIASES
# above already handles). Critically, there is no column literally called
# "isin" — the ISIN lives in `symbol`, and `name` carries the human-readable
# instrument name. Both `name` and `symbol` would otherwise collide on the
# generic "ticker" alias (which lists "symbol" as an alias), silently
# dropping the ISIN entirely — hence a dedicated, unambiguous map instead of
# extending HEADER_ALIASES.
TRADE_REPUBLIC_V2_HEADER_ALIASES: dict[str, set[str]] = {
    "date": {"date"},
    "type": {"type"},
    "ticker": {"name"},
    "isin": {"symbol"},
    "asset_class": {"asset_class"},
    "quantity": {"shares"},
    "unit_price_eur": {"price"},
    "fees_eur": {"fee"},
}

# Trade Republic's own asset-class vocabulary ("FUND" for ETFs) normalised to
# Sunday's — applied in addition to a direct match against ALLOWED_ASSET_CLASSES.
_ASSET_CLASS_ALIASES = {"fund": "etf"}

# Heuristics to classify when the CSV doesn't tell us.
CRYPTO_SYMBOLS = {"BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "XRP", "DOGE", "LINK"}
ETF_ISIN_PREFIXES = ("IE", "LU")  # Most UCITS ETFs are Irish or Luxembourg domiciled


@dataclass
class IngestionContext:
    """Parse-time state: warnings, rows seen, and the detected broker format.

    Replay/persist counts (sells/splits/etc.) now come from `ApplyResult`.
    """

    warnings: list[str] = field(default_factory=list)
    rows_read: int = 0
    detected_format: str = "unknown"


def _normalise_header(raw: str) -> str:
    return raw.strip().lower().replace("﻿", "")


def _delimiter_for(raw_csv: str) -> str:
    """Pick the column delimiter. DEGIRO (and some EU exports) use semicolons;
    most others use commas. Decided from the header line so a comma inside a
    quoted field doesn't flip the choice."""
    header = raw_csv.lstrip("﻿").split("\n", 1)[0]
    return ";" if header.count(";") > header.count(",") else ","


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


# DEGIRO transactions export. No "Type" column: direction is the sign of
# Quantity (+buy / -sell). No symbol either, so the Product name is the label and
# the ISIN is the stable identifier. Price is in the instrument currency; Value
# is in the account currency (EUR), so it gives the cleaner EUR unit cost.
DEGIRO_HEADER_ALIASES: dict[str, set[str]] = {
    "date": {"date", "datum"},
    "ticker": {"product"},
    "isin": {"isin"},
    "quantity": {"quantity", "aantal"},  # SIGNED
    "unit_price_eur": {"price", "koers"},  # instrument currency (fallback only)
    "value_eur": {"value", "waarde"},  # account currency (EUR), signed
    "fees_eur": {
        "transaction and/or third party costs",
        "transactiekosten en/of kosten derden",
        "transaction costs",
        "costs",
    },
}


def _build_degiro_column_map(fieldnames: list[str]) -> dict[str, str]:
    """Map raw DEGIRO headers → the canonical names `_parse_degiro_row` reads.

    DEGIRO interleaves unnamed per-amount currency columns; those collapse to an
    empty header and simply don't match any alias, so they're ignored.
    """
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        h = _normalise_header(raw)
        for canonical, aliases in DEGIRO_HEADER_ALIASES.items():
            if h in aliases and canonical not in mapping.values():
                mapping[raw] = canonical
                break
    return mapping


def _build_trade_republic_v2_column_map(fieldnames: list[str]) -> dict[str, str]:
    """Map the modern Trade Republic export's headers, unambiguously — see
    TRADE_REPUBLIC_V2_HEADER_ALIASES for why this can't reuse the generic
    alias table (name/symbol would collide on the shared "ticker" alias)."""
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        h = _normalise_header(raw)
        for canonical, aliases in TRADE_REPUBLIC_V2_HEADER_ALIASES.items():
            if h in aliases and canonical not in mapping.values():
                mapping[raw] = canonical
                break
    return mapping


def _detect_format(fieldnames: list[str]) -> str:
    normalised = {_normalise_header(h) for h in fieldnames}
    if {"date", "type", "ticker", "asset_class"}.issubset(normalised):
        return "sunday_native"
    # DEGIRO: a "Product" column + ISIN, no "Type" (direction is the Quantity sign).
    if {"product", "isin"}.issubset(normalised) and (
        "quantity" in normalised or "aantal" in normalised
    ):
        return "degiro"
    # Trade Republic's current "Transaction export" download: no literal "isin"
    # column (it's inside "symbol"), separate "name" and "category" columns.
    if {"symbol", "shares", "name", "category", "asset_class"}.issubset(normalised):
        return "trade_republic_v2"
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
        "%d-%m-%Y",  # DEGIRO
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
) -> CanonicalTransaction | None:
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
        asset_class = _ASSET_CLASS_ALIASES.get(asset_class, asset_class)
        if asset_class not in ALLOWED_ASSET_CLASSES:
            ctx.warnings.append(f"unknown asset_class {asset_class!r}; inferring")
            asset_class = _infer_asset_class(ticker_raw, isin)
    else:
        asset_class = _infer_asset_class(ticker_raw, isin)

    # Trade Republic's crypto rows invert the usual convention: `symbol`
    # (mapped to isin) holds the actual short trading symbol ("ADA"), and
    # `name` (mapped to ticker) holds the full name ("Cardano") -- unusable
    # for pricing ("CARDANO-EUR" doesn't exist). Crypto has no ISIN, so
    # anything shorter than a real 12-character ISIN here is really the
    # symbol misfiled by the column map.
    if asset_class == "crypto" and isin and len(isin) != 12:
        ticker_raw = isin
        isin = None

    return CanonicalTransaction(
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


def _parse_degiro_row(
    row: dict[str, str], column_map: dict[str, str], ctx: IngestionContext
) -> CanonicalTransaction | None:
    """Parse one DEGIRO transactions row. Direction is the sign of Quantity."""
    date_raw = _row_get(row, column_map, "date")
    product_raw = _row_get(row, column_map, "ticker")
    if not date_raw or not product_raw:
        ctx.warnings.append("DEGIRO row missing date/product; skipping")
        return None

    qty_signed = _safe_decimal(
        _row_get(row, column_map, "quantity") or "", field_name="quantity", ctx=ctx
    )
    if qty_signed is None or qty_signed == 0:
        # Cash movements / currency conversions carry no quantity.
        ctx.warnings.append(f"DEGIRO row for {product_raw!r} has no quantity; skipping")
        return None
    kind = KIND_BUY if qty_signed > 0 else KIND_SELL

    date = _parse_date(date_raw)
    if date is None:
        ctx.warnings.append(f"unparseable date {date_raw!r}; skipping")
        return None

    isin = _row_get(row, column_map, "isin")
    isin = isin.strip() if isin else None
    if not isin:
        isin = None

    qty = abs(qty_signed)
    # Prefer the EUR account-currency Value for unit cost; fall back to the
    # instrument-currency Price (flagged) when Value is absent.
    value_eur = _safe_decimal(
        _row_get(row, column_map, "value_eur") or "", field_name="value", ctx=ctx
    )
    if value_eur is not None:
        unit_price: Decimal | None = abs(value_eur) / qty
    else:
        price = _safe_decimal(
            _row_get(row, column_map, "unit_price_eur") or "", field_name="price", ctx=ctx
        )
        unit_price = abs(price) if price is not None else None
        if unit_price is not None:
            ctx.warnings.append(
                f"DEGIRO {product_raw!r}: no EUR value column, used Price (may be non-EUR)"
            )

    if kind == KIND_BUY and unit_price is None:
        ctx.warnings.append(f"DEGIRO buy for {product_raw!r} has no price; skipping")
        return None

    fees = _safe_decimal(
        _row_get(row, column_map, "fees_eur") or "0", field_name="fees", ctx=ctx
    ) or Decimal("0")

    return CanonicalTransaction(
        date=date,
        kind=kind,
        ticker=product_raw.strip().upper(),
        isin=isin,
        asset_class=_infer_asset_class(product_raw, isin),
        quantity=qty,
        unit_price_eur=unit_price or Decimal("0"),
        fees_eur=abs(fees),
    )


def _summary_warning(applied: ApplyResult) -> str | None:
    parts = []
    if applied.sells_applied:
        parts.append(f"{applied.sells_applied} sell(s) applied")
    if applied.dividends_seen:
        parts.append(f"{applied.dividends_seen} dividend row(s) recorded (no holdings change)")
    if applied.splits_applied:
        parts.append(f"{applied.splits_applied} split(s) applied")
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

# A row parser: (row, column_map, ctx) → CanonicalTransaction | None.
RowParser = Callable[[dict[str, str], dict[str, str], IngestionContext], "CanonicalTransaction | None"]


def _mapper_and_parser(detected: str, fieldnames: list[str]) -> tuple[dict[str, str], RowParser]:
    """Pick the column map + row parser for a detected format. DEGIRO has no type
    column (sign-based direction), so it uses a dedicated parser; the modern
    Trade Republic export has an unambiguous dedicated column map (see
    TRADE_REPUBLIC_V2_HEADER_ALIASES) but still uses `_parse_row` since it does
    have a type column; everything else shares the alias-driven `_parse_row`."""
    if detected == "degiro":
        return _build_degiro_column_map(fieldnames), _parse_degiro_row
    if detected == "trade_republic_v2":
        return _build_trade_republic_v2_column_map(fieldnames), _parse_row
    return _build_column_map(fieldnames), _parse_row


def preview_csv(raw_csv: str) -> PreviewResult:
    """Parse a CSV WITHOUT touching the DB — powers the import wizard's review step.

    Reuses the same detection + per-row parsing as `ingest_csv`, but reports each
    row's status (ok / skipped + reason) and the detected column mapping instead
    of committing anything.
    """
    ctx = IngestionContext()
    reader = csv.DictReader(StringIO(raw_csv), delimiter=_delimiter_for(raw_csv))
    fieldnames = list(reader.fieldnames or [])
    if not fieldnames:
        return PreviewResult("unknown", [], [], [], 0, 0, ["CSV has no header row"])

    detected = _detect_format(fieldnames)
    column_map, parse = _mapper_and_parser(detected, fieldnames)
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
        parsed = parse(row, column_map, ctx)
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


def ingest_csv(
    db: Session,
    portfolio: Portfolio,
    raw_csv: str,
    max_holdings: int | None = None,
    connection: Connection | None = None,
) -> IngestResult:
    ctx = IngestionContext()
    reader = csv.DictReader(StringIO(raw_csv), delimiter=_delimiter_for(raw_csv))
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
    column_map, parse = _mapper_and_parser(ctx.detected_format, fieldnames)
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

    # Parse every row into canonical transactions (parse warnings collect in ctx).
    txns: list[CanonicalTransaction] = []
    for row in reader:
        ctx.rows_read += 1
        parsed = parse(row, column_map, ctx)
        if parsed is None:
            continue
        txns.append(parsed)

    # Shared replay/persist (raises HoldingsLimitExceeded + rolls back on cap).
    applied = apply_transactions(
        db,
        portfolio,
        txns,
        source_label=ctx.detected_format,
        connection=connection,
        max_holdings=max_holdings,
    )

    # Warning order matches the previous single-pass build: parse warnings, then
    # apply warnings, with the summary and detected-format banner prepended.
    warnings = [*ctx.warnings, *applied.warnings]
    summary = _summary_warning(applied)
    if summary:
        warnings = [summary, *warnings]
    if ctx.detected_format != "sunday_native":
        warnings = [f"Detected format: {ctx.detected_format}", *warnings]

    return IngestResult(
        rows_read=ctx.rows_read,
        positions_created=applied.positions_created,
        positions_updated=applied.positions_updated,
        lots_created=applied.lots_created,
        warnings=warnings,
    )
