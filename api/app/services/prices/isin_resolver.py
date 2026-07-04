"""Resolve ISIN → yfinance symbol via OpenFIGI, cached in the DB.

Holdings imported by ISIN only (DEGIRO, and any broker that omits a ticker) can't
be priced until the ISIN is mapped to a market symbol. OpenFIGI (Bloomberg's free
mapping API) does that; results — hits *and* misses — are cached in `isin_symbols`
so a given ISIN is asked at most once.

Layering (most trusted first): the curated `symbols.ISIN_TICKER_MAP`, then the DB
cache, then a live OpenFIGI call for the remainder. `resolve` never raises — a
provider outage just yields fewer mappings, and those positions fall back to
ticker-based pricing exactly as before.

OpenFIGI returns a Bloomberg `exchCode` per listing; `_EXCH_TO_YF_SUFFIX` maps it
to the yfinance venue suffix, and `_pick_symbol` prefers the EUR/home listing so a
EUR holding isn't matched to a foreign-currency venue.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import IsinSymbol
from app.services.prices import symbols

log = logging.getLogger(__name__)

OPENFIGI_BASE_URL = "https://api.openfigi.com/v3"

# Bloomberg composite exchange code → yfinance suffix. Empty string = US (bare).
_EXCH_TO_YF_SUFFIX: dict[str, str] = {
    "GR": ".DE",  # Xetra
    "GY": ".DE",  # Germany floor → Xetra (more reliable on yfinance)
    "GF": ".F",   # Frankfurt
    "NA": ".AS",  # Amsterdam
    "FP": ".PA",  # Paris
    "IM": ".MI",  # Milan
    "AV": ".VI",  # Vienna
    "SW": ".SW",  # SIX Swiss
    "VX": ".SW",
    "SE": ".SW",
    "LN": ".L",   # London
    "SM": ".MC",  # Madrid
    "PL": ".LS",  # Lisbon
    "BB": ".BR",  # Brussels
    "ID": ".IR",  # Dublin
    "FH": ".HE",  # Helsinki
    "US": "", "UN": "", "UW": "", "UQ": "", "UR": "", "UP": "", "UA": "",
    # Toronto Stock Exchange proper plus the ATS/alternative venues OpenFIGI
    # reports separately for the same security (Chi-X Canada, TSX Alpha,
    # Omega, etc.) — all resolve to the same yfinance ".TO" symbol.
    "CN": ".TO", "CT": ".TO", "CJ": ".TO", "TR": ".TO", "TX": ".TO",
    "TA": ".TO", "TG": ".TO", "TK": ".TO",
}

# Preferred yfinance suffix per ISIN country prefix (the holding's home venue).
# IE/LU (ETF domiciles) are intentionally absent — they list across EU venues, so
# the EUR-preference fallback decides.
_ISIN_COUNTRY_HOME: dict[str, str] = {
    "DE": ".DE", "NL": ".AS", "FR": ".PA", "IT": ".MI", "AT": ".VI",
    "CH": ".SW", "GB": ".L", "ES": ".MC", "PT": ".LS", "BE": ".BR",
    "FI": ".HE", "US": "", "CA": ".TO",
}

# EUR venues, in display/preference order (used when no country-home match).
_EUR_SUFFIX_ORDER = (".DE", ".AS", ".PA", ".MI", ".VI", ".MC", ".LS", ".BR", ".IR", ".HE")
_MIN_ISIN_LEN = 8


def _score(suffix: str, home: str | None) -> int:
    """Lower is better. Home venue wins, then EUR venues, then SW/L, then US bare."""
    if home is not None and suffix == home:
        return 0
    if suffix in _EUR_SUFFIX_ORDER:
        return 1 + _EUR_SUFFIX_ORDER.index(suffix)
    if suffix in (".SW", ".L"):
        return 50
    if suffix == "":
        return 100  # US bare — last, so EUR listings win for EU ISINs
    return 60


def _pick_symbol(isin: str, listings: list[dict]) -> str | None:
    """Choose the best yfinance symbol from OpenFIGI listings for one ISIN.

    OpenFIGI sometimes lists the same ISIN under genuinely different ticker
    symbols on different venues — not just "same ticker, different suffix"
    but a different symbol string entirely (a Jersey-domiciled silver ETC
    trades as PHAG on the LSE/Xetra-EUR venues but as VZLC on a smaller,
    delisted German venue, for the same underlying ISIN). Scoring every
    listing by venue alone, regardless of ticker, can pick a well-scored
    venue's ticker that isn't the security's actual primary/liquid symbol —
    that's exactly what picked VZLC.DE (delisted) over the correct PHAG.AS.
    So: first find the ticker used by the most listings (the primary one),
    then rank venues only within that ticker's own listings.
    """
    home = _ISIN_COUNTRY_HOME.get(isin[:2].upper())

    by_ticker: dict[str, list[dict]] = {}
    for listing in listings:
        ticker = str(listing.get("ticker", "")).strip().upper()
        exch = str(listing.get("exchCode", "")).strip().upper()
        if not ticker or exch not in _EXCH_TO_YF_SUFFIX:
            continue
        by_ticker.setdefault(ticker, []).append(listing)
    if not by_ticker:
        return None

    primary_ticker = max(by_ticker, key=lambda t: len(by_ticker[t]))

    best: tuple[int, str] | None = None
    for listing in by_ticker[primary_ticker]:
        exch = str(listing.get("exchCode", "")).strip().upper()
        suffix = _EXCH_TO_YF_SUFFIX[exch]
        candidate = (_score(suffix, home), f"{primary_ticker}{suffix}")
        if best is None or candidate[0] < best[0]:
            best = candidate
    return best[1] if best is not None else None


@runtime_checkable
class IsinMappingProvider(Protocol):
    """Maps ISINs to yfinance symbols.

    Returns ``(resolved, attempted)``: ``resolved`` is the {isin: symbol} it could
    map, ``attempted`` is every isin it actually got a provider answer for. The
    caller caches only ``attempted`` (as hit or miss), so ISINs left unanswered by
    a partial failure are retried rather than cached as permanent misses.
    """

    def map_isins(self, isins: list[str]) -> tuple[dict[str, str], list[str]]: ...


def _chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


class OpenFigiProvider:
    """Resolves ISINs via OpenFIGI's /mapping endpoint.

    Usable without a key (rate-limited); an `OPENFIGI_API_KEY` raises the limits
    and the per-request batch size. Network/HTTP errors propagate to `resolve`,
    which catches them so a refresh never fails on a mapping outage.
    """

    def __init__(self, api_key: str = "", base_url: str = OPENFIGI_BASE_URL) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._batch_size = 100 if api_key else 10

    def map_isins(self, isins: list[str]) -> tuple[dict[str, str], list[str]]:
        try:
            import httpx
        except ImportError:  # pragma: no cover - httpx is installed
            return {}, []

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["X-OPENFIGI-APIKEY"] = self._api_key

        out: dict[str, str] = {}
        attempted: list[str] = []
        for batch in _chunk(isins, self._batch_size):
            jobs = [{"idType": "ID_ISIN", "idValue": isin} for isin in batch]
            try:
                resp = httpx.post(
                    f"{self._base_url}/mapping", json=jobs, headers=headers, timeout=20.0
                )
                resp.raise_for_status()
                results = resp.json()
            except Exception:  # noqa: BLE001 - a failed batch stops here; earlier batches stand
                break
            attempted.extend(batch)
            for isin, result in zip(batch, results, strict=False):
                listings = result.get("data") if isinstance(result, dict) else None
                if not listings:
                    continue
                symbol = _pick_symbol(isin, listings)
                if symbol:
                    out[isin] = symbol
        return out, attempted


def get_provider() -> IsinMappingProvider:
    return OpenFigiProvider(api_key=get_settings().openfigi_api_key)


def resolve(
    db: Session, isins: list[str], *, provider: IsinMappingProvider | None = None
) -> dict[str, str]:
    """Return ``{isin: yfinance_symbol}`` for the given ISINs.

    Uses the curated map, then the DB cache, then OpenFIGI for the remainder
    (caching every result, hits and misses). Never raises.
    """
    wanted = {i.strip().upper() for i in isins if i and len(i.strip()) >= _MIN_ISIN_LEN}
    if not wanted:
        return {}

    result: dict[str, str] = {}
    # 1. Curated map wins (hand-verified).
    for isin in wanted:
        if isin in symbols.ISIN_TICKER_MAP:
            result[isin] = symbols.ISIN_TICKER_MAP[isin]

    # 2. DB cache (covers both prior hits and prior misses).
    to_check = wanted - set(result)
    cached_isins: set[str] = set()
    if to_check:
        for row in db.query(IsinSymbol).filter(IsinSymbol.isin.in_(to_check)).all():
            cached_isins.add(row.isin)
            if row.symbol:
                result.setdefault(row.isin, row.symbol)

    # 3. OpenFIGI for the truly unknown.
    misses = sorted(to_check - cached_isins)
    if not misses:
        return result

    prov = provider or get_provider()
    try:
        mapped, attempted = prov.map_isins(misses)
    except Exception as exc:  # noqa: BLE001 - any failure must not break pricing
        log.warning("OpenFIGI resolve failed for %d ISIN(s): %s", len(misses), exc)
        return result  # transient failure: don't cache, retry next refresh

    if not attempted:
        return result

    # Cache only the ISINs the provider actually answered (hit or miss); ones left
    # unanswered by a partial failure stay uncached and are retried next refresh.
    now = datetime.now(timezone.utc)
    for isin in attempted:
        symbol = mapped.get(isin)
        db.add(IsinSymbol(isin=isin, symbol=symbol, source="openfigi", resolved_at=now))
        if symbol:
            result[isin] = symbol
    try:
        db.commit()
    except IntegrityError:
        # A concurrent refresh cached these first; our resolved symbols (already in
        # `result`) still stand, so degrade quietly instead of 500-ing the refresh.
        db.rollback()
    return result
