"""Net-worth snapshot history.

POST /api/snapshots/capture — record today's net worth (upsert by day).
GET  /api/snapshots         — the history, oldest first (powers week-over-week
                              and, later, a net-worth chart).

Snapshots are also captured automatically after a price refresh, so history
accumulates as the user uses the app. A future Sunday cron will call capture too.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas.snapshot import SnapshotListResponse, SnapshotView
from app.services import fx, snapshots

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


def _to_view(snap) -> SnapshotView:
    return SnapshotView(
        captured_on=snap.captured_on.isoformat(),
        as_of=snap.as_of.isoformat(),
        total_value=fx.dual(snap.total_value_eur, snap.eur_usd_rate),
        total_cost=fx.dual(snap.total_cost_eur, snap.eur_usd_rate),
        eur_usd_rate=snap.eur_usd_rate,
    )


@router.post("/capture", response_model=SnapshotView)
def capture_snapshot(
    db: Session = Depends(get_db),
    portfolio: Portfolio = Depends(get_default_portfolio),
) -> SnapshotView:
    snap = snapshots.capture(db, portfolio, now=datetime.now(timezone.utc))
    db.commit()
    db.refresh(snap)
    return _to_view(snap)


@router.get("", response_model=SnapshotListResponse)
def list_snapshots(
    portfolio: Portfolio = Depends(get_default_portfolio),
) -> SnapshotListResponse:
    views = [_to_view(s) for s in portfolio.snapshots]  # relationship is ordered by as_of
    return SnapshotListResponse(count=len(views), snapshots=views)
