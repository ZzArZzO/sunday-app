import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.routes import (
    auth,
    benchmark,
    billing,
    briefing,
    chat,
    connections,
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

log = logging.getLogger(__name__)
settings = get_settings()

# Error tracking — dormant unless SENTRY_DSN is set (like the other integrations).
if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

app = FastAPI(
    title="Sunday API",
    description=(
        "Portfolio briefings for EU retail investors. Not investment advice. "
        "Information only."
    ),
    version="0.1.0",
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Conservative security response headers on every response."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Lock the origin whitelist down in production; warn loudly if it's missing.
if settings.auth_required and not settings.cors_origins_list:
    log.warning(
        "AUTH_REQUIRED is on but API_CORS_ORIGINS is empty — the browser app "
        "will be unable to call the API. Set it to your web origin."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
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
app.include_router(connections.router)


@app.on_event("startup")
def _start_weekly_scheduler() -> None:
    # No-op unless ENABLE_SCHEDULER is set; starts the Sunday briefing cron.
    # Never let a scheduler hiccup take down the whole API.
    from app.services.delivery import scheduler

    try:
        scheduler.start()
    except Exception:  # noqa: BLE001 — best-effort; the API must still boot
        log.exception("weekly scheduler failed to start")
