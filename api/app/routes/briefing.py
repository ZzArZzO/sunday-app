from fastapi import APIRouter, Depends, Response

from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas import BriefingResponse
from app.services import briefing_build
from app.services.delivery import pdf_render

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("", response_model=BriefingResponse)
def get_briefing(portfolio: Portfolio = Depends(get_default_portfolio)) -> BriefingResponse:
    return briefing_build.build_briefing(portfolio)


@router.get("/pdf")
def get_briefing_pdf(portfolio: Portfolio = Depends(get_default_portfolio)) -> Response:
    """Download this week's briefing as a calm one-page PDF."""
    briefing = briefing_build.build_briefing(portfolio)
    pdf = pdf_render.render_briefing_pdf(briefing)
    filename = f"sunday-briefing-{briefing.week_of}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
