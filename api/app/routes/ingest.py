from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Connection, Portfolio, User
from app.schemas import IngestResult
from app.schemas.ingest_preview import (
    IngestPreviewResponse,
    PreviewColumnView,
    PreviewRowView,
)
from app.services import csv_ingestor
from app.services.billing import subscription

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

MAX_CSV_BYTES = 2 * 1024 * 1024  # 2 MB


def _get_or_create_csv_connection(
    db: Session, portfolio: Portfolio, broker: str | None
) -> Connection:
    """One csv-type Connection per broker label, so re-uploading the same broker's
    export updates that source rather than spawning duplicates."""
    label = (broker or "CSV import").strip()[:120] or "CSV import"
    conn = next(
        (c for c in portfolio.connections if c.kind == "csv" and c.label == label),
        None,
    )
    if conn is None:
        conn = Connection(portfolio_id=portfolio.id, kind="csv", label=label)
        db.add(conn)
        db.flush()
        portfolio.connections.append(conn)
    conn.last_synced_at = datetime.now(timezone.utc)
    return conn


async def _read_csv_text(file: UploadFile) -> str:
    raw = await file.read()
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CSV exceeds {MAX_CSV_BYTES} bytes",
        )
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is not valid UTF-8: {exc}",
        ) from exc


@router.post("/preview", response_model=IngestPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),  # noqa: ARG001 - auth gate only
) -> IngestPreviewResponse:
    """Parse-only review of a CSV before committing. No DB writes."""
    text = await _read_csv_text(file)
    result = csv_ingestor.preview_csv(text)
    return IngestPreviewResponse(
        detected_format=result.detected_format,
        columns=[PreviewColumnView(**vars(c)) for c in result.columns],
        unmapped_headers=result.unmapped_headers,
        rows=[PreviewRowView(**vars(r)) for r in result.rows],
        ok_count=result.ok_count,
        skipped_count=result.skipped_count,
        warnings=result.warnings,
    )


@router.post("", response_model=IngestResult)
async def upload_csv(
    file: UploadFile = File(...),
    broker: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngestResult:
    text = await _read_csv_text(file)

    portfolio = next(iter(user.portfolios), None)
    if portfolio is None:
        portfolio = Portfolio(user_id=user.id, name="Main")
        db.add(portfolio)
        db.flush()
        user.portfolios.append(portfolio)

    connection = _get_or_create_csv_connection(db, portfolio, broker)

    try:
        return csv_ingestor.ingest_csv(
            db,
            portfolio,
            text,
            max_holdings=subscription.holdings_limit(user),
            connection=connection,
        )
    except csv_ingestor.HoldingsLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Free plan is limited to {exc.limit} holdings; this import would "
                f"result in {exc.attempted}. Upgrade to Pro for unlimited holdings."
            ),
        ) from exc
