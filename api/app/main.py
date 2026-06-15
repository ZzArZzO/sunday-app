from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import (
    auth,
    benchmark,
    billing,
    briefing,
    chat,
    delivery,
    dividend,
    events,
    fire,
    health,
    ingest,
    portfolio,
    prices,
    push,
    rebalance,
    snapshots,
    tax,
)

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
app.include_router(fire.router)
app.include_router(dividend.router)
app.include_router(tax.router)
app.include_router(rebalance.router)
app.include_router(chat.router)
app.include_router(prices.router)
app.include_router(snapshots.router)
app.include_router(events.router)
app.include_router(benchmark.router)
app.include_router(delivery.router)
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(push.router)


@app.on_event("startup")
def _start_weekly_scheduler() -> None:
    # No-op unless ENABLE_SCHEDULER is set; starts the Sunday briefing cron.
    from app.services.delivery import scheduler

    scheduler.start()
