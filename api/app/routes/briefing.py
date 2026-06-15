from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, get_default_portfolio
from app.models import Portfolio, User
from app.schemas import BriefingResponse
from app.services import briefing_build
from app.services.billing import budget
from app.services.delivery import pdf_render

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("", response_model=BriefingResponse)
def get_briefing(
    portfolio: Portfolio = Depends(get_default_portfolio),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BriefingResponse:
    # Skip the AI narrative (keep the deterministic briefing) once over budget.
    ai_enabled = not budget.is_exhausted(db, user)
    return briefing_build.build_briefing(portfolio, ai_enabled=ai_enabled)


@router.get("/pdf")
def get_briefing_pdf(
    portfolio: Portfolio = Depends(get_default_portfolio),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Download this week's briefing as a calm one-page PDF."""
    briefing = briefing_build.build_briefing(
        portfolio, ai_enabled=not budget.is_exhausted(db, user)
    )
    pdf = pdf_render.render_briefing_pdf(briefing)
    filename = f"sunday-briefing-{briefing.week_of}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
