from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Portfolio, User
from app.schemas import IngestResult
from app.services import csv_ingestor

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

MAX_CSV_BYTES = 2 * 1024 * 1024  # 2 MB


@router.post("", response_model=IngestResult)
async def upload_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngestResult:
    raw = await file.read()
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"CSV exceeds {MAX_CSV_BYTES} bytes",
        )

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is not valid UTF-8: {exc}",
        ) from exc

    portfolio = next(iter(user.portfolios), None)
    if portfolio is None:
        portfolio = Portfolio(user_id=user.id, name="Main")
        db.add(portfolio)
        db.flush()
        user.portfolios.append(portfolio)

    return csv_ingestor.ingest_csv(db, portfolio, text)
