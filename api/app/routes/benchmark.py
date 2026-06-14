"""Benchmark comparison endpoint.

GET /api/benchmark?index=msci_world|sp500 — the portfolio's approximate TWR vs
the chosen index over the snapshot history, with a per-point series and a
headline difference. Honest empty state until enough history accrues.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas.benchmark import BenchmarkPoint, BenchmarkResponse
from app.services import benchmark, fx
from app.services.benchmark import BENCHMARKS, DEFAULT_BENCHMARK
from app.services.prices.yfinance_provider import YFinanceProvider

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


@router.get("", response_model=BenchmarkResponse)
def get_benchmark(
    index: str = Query(default=DEFAULT_BENCHMARK),
    portfolio: Portfolio = Depends(get_default_portfolio),
) -> BenchmarkResponse:
    key = index if index in BENCHMARKS else DEFAULT_BENCHMARK
    comparison = benchmark.build_comparison(list(portfolio.snapshots), key, YFinanceProvider())

    quote = fx.get_eur_usd()
    diff_money = fx.dual(comparison.diff_eur, quote.rate) if comparison.diff_eur is not None else None

    return BenchmarkResponse(
        available=comparison.available,
        index_key=comparison.index_key,
        index_name=comparison.index_name,
        index_available=comparison.index_available,
        series=[
            BenchmarkPoint(
                on=p.on.isoformat(),
                portfolio_twr_pct=p.portfolio_twr_pct,
                index_twr_pct=p.index_twr_pct,
            )
            for p in comparison.series
        ],
        portfolio_pct=comparison.portfolio_pct,
        index_pct=comparison.index_pct,
        diff_pct=comparison.diff_pct,
        diff=diff_money,
        note=comparison.note,
    )
