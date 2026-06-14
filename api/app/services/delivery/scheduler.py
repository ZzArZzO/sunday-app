"""Weekly Sunday-briefing cron (opt-in via ENABLE_SCHEDULER).

APScheduler is imported lazily inside `start()` so the app and tests don't depend
on it unless the scheduler is actually enabled. Fires Sunday 17:00 UTC and sends
the briefing to every user. (Per-user-timezone scheduling is a refinement; for
now one weekly run covers the EU beachhead well enough.)
"""

from __future__ import annotations

import logging

from app.config import get_settings

log = logging.getLogger(__name__)

_scheduler = None


def _run_weekly() -> None:
    from app.db import SessionLocal
    from app.services.delivery import briefing_delivery

    db = SessionLocal()
    try:
        summary = briefing_delivery.deliver_weekly(db)
        log.info(
            "weekly briefing run: %s/%s sent, %s failed (dry_run=%s)",
            summary.sent,
            summary.total,
            summary.failed,
            summary.dry_run,
        )
    finally:
        db.close()


def start():
    """Start the weekly scheduler if ENABLE_SCHEDULER is set. Idempotent."""
    global _scheduler
    if not get_settings().enable_scheduler:
        return None
    if _scheduler is not None:
        return _scheduler

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        log.warning(
            "ENABLE_SCHEDULER is set but apscheduler is not installed — "
            "weekly briefing cron disabled. Install: pip install apscheduler"
        )
        return None

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _run_weekly,
        CronTrigger(day_of_week="sun", hour=17, minute=0),
        id="weekly_briefing",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    log.info("weekly briefing scheduler started (Sun 17:00 UTC)")
    return scheduler


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
