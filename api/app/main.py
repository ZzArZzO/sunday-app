from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import briefing, health, ingest, portfolio

settings = get_settings()

app = FastAPI(
    title="Sunday API",
    description=(
        "Portfolio briefings for EU retail investors. Not investment advice. "
        "Information only."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(portfolio.router)
app.include_router(briefing.router)
