"""Benchmark comparison: portfolio TWR vs a market index.

Portfolio return is an *approximate* time-weighted return (TWR) derived from the
net-worth snapshot history, treating each period's change in cost basis as the
cash flow in/out (the only flow signal available). It is labelled approximate
because a true TWR needs exact dated flows. The index series is the benchmark
ETF's own cumulative return over the same dates, indexed to the first snapshot.

All math is pure; market-data I/O is behind `HistoryProvider` so it tests with a
fake. Framed as orientation, never a verdict — staying on the information side.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class BenchmarkSpec:
    key: str
    name: str
    # EUR-listed ETF proxy, so its return is comparable to the EUR portfolio.
    symbol: str


BENCHMARKS: dict[str, BenchmarkSpec] = {
    "msci_world": BenchmarkSpec("msci_world", "MSCI World", "IWDA.AS"),
    "sp500": BenchmarkSpec("sp500", "S&P 500", "SXR8.DE"),
}
DEFAULT_BENCHMARK = "msci_world"


class HistoryProvider(Protocol):
    def get_closes(self, symbol: str, start: date, end: date) -> dict[date, Decimal]:
        """Daily closing prices within [start, end]. Empty dict if unavailable."""
        ...


@dataclass(frozen=True)
class TwrPoint:
    on: date
    twr_pct: Decimal


def twr_series(snaps: list) -> list[TwrPoint]:
    """Cumulative approximate TWR (%), first point anchored at 0. Empty if <2 snapshots."""
    rows = sorted(snaps, key=lambda s: s.captured_on)
    if len(rows) < 2:
        return []

    points = [TwrPoint(rows[0].captured_on, Decimal("0"))]
    cumulative = Decimal("1")
    for prev, cur in zip(rows, rows[1:]):
        v0 = Decimal(prev.total_value_eur)
        v1 = Decimal(cur.total_value_eur)
        cash_flow = Decimal(cur.total_cost_eur) - Decimal(prev.total_cost_eur)
        period_return = ((v1 - v0 - cash_flow) / v0) if v0 > 0 else Decimal("0")
        cumulative *= Decimal("1") + period_return
        points.append(
            TwrPoint(cur.captured_on, ((cumulative - Decimal("1")) * Decimal("100")).quantize(Decimal("0.01")))
        )
    return points


def _close_on_or_before(closes: dict[date, Decimal], d: date) -> Decimal | None:
    candidates = [cd for cd in closes if cd <= d]
    return closes[max(candidates)] if candidates else None


@dataclass(frozen=True)
class ComparisonPoint:
    on: date
    portfolio_twr_pct: Decimal
    index_twr_pct: Decimal | None


@dataclass(frozen=True)
class BenchmarkComparison:
    available: bool
    index_key: str
    index_name: str
    index_available: bool
    series: list[ComparisonPoint] = field(default_factory=list)
    portfolio_pct: Decimal | None = None
    index_pct: Decimal | None = None
    diff_pct: Decimal | None = None
    diff_eur: Decimal | None = None
    note: str | None = None


def build_comparison(snaps: list, index_key: str, history: HistoryProvider) -> BenchmarkComparison:
    spec = BENCHMARKS.get(index_key, BENCHMARKS[DEFAULT_BENCHMARK])
    pts = twr_series(snaps)
    if not pts:
        return BenchmarkComparison(
            available=False,
            index_key=spec.key,
            index_name=spec.name,
            index_available=False,
            note=(
                "Not enough history yet — benchmark comparison starts once a few days "
                "of net-worth snapshots accrue."
            ),
        )

    try:
        closes = history.get_closes(spec.symbol, pts[0].on, pts[-1].on)
    except Exception:  # noqa: BLE001 - market data must never break the page
        closes = {}

    base_close = _close_on_or_before(closes, pts[0].on)
    series: list[ComparisonPoint] = []
    index_final: Decimal | None = None
    for p in pts:
        idx_pct: Decimal | None = None
        if base_close and base_close > 0:
            c = _close_on_or_before(closes, p.on)
            if c is not None:
                idx_pct = ((c / base_close - Decimal("1")) * Decimal("100")).quantize(Decimal("0.01"))
                index_final = idx_pct
        series.append(ComparisonPoint(on=p.on, portfolio_twr_pct=p.twr_pct, index_twr_pct=idx_pct))

    port_final = pts[-1].twr_pct
    diff_pct = (port_final - index_final) if index_final is not None else None

    diff_eur: Decimal | None = None
    if diff_pct is not None:
        latest_value = Decimal(sorted(snaps, key=lambda s: s.captured_on)[-1].total_value_eur)
        diff_eur = (latest_value * diff_pct / Decimal("100")).quantize(Decimal("0.01"))

    return BenchmarkComparison(
        available=True,
        index_key=spec.key,
        index_name=spec.name,
        index_available=index_final is not None,
        series=series,
        portfolio_pct=port_final,
        index_pct=index_final,
        diff_pct=diff_pct,
        diff_eur=diff_eur,
    )
