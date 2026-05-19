from fastapi import APIRouter, Depends

from app.deps import get_default_portfolio
from app.models import Portfolio
from app.schemas import BriefingResponse
from app.services import briefing_composer

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("", response_model=BriefingResponse)
def get_briefing(portfolio: Portfolio = Depends(get_default_portfolio)) -> BriefingResponse:
    return briefing_composer.compose_briefing(portfolio)
