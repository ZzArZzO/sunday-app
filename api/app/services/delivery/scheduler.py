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
# Held-open connection carrying the Postgres advisory lock (None until acquired).
_lock_conn = None
# Arbitrary stable key (year+month of the feature) shared across all instances.
_ADVISORY_LOCK_KEY = 202607


def _acquire_singleton_lock() -> bool:
    """Ensure only one instance runs the scheduler.

    On Postgres, take a session-level advisory lock on a held-open connection;
    the lock lives as long as that connection stays open (the process lifetime).
    On non-Postgres (sqlite dev/tests) there's only ever one process, so allow it.
    """
    global _lock_conn
    from app.db import engine

    if engine.dialect.name != "postgresql":
        return True

    from sqlalchemy import text

    conn = engine.connect()
    got = conn.execute(
        text("SELECT pg_try_advisory_lock(:k)"), {"k": _ADVISORY_LOCK_KEY}
    ).scalar()
    if not got:
        conn.close()
        return False
    _lock_conn = conn  # keep open so the lock is held for this process
    return True


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

    if not _acquire_singleton_lock():
        log.info("scheduler lock held by another instance — not starting here")
        return None

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
    global _scheduler, _lock_conn
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    if _lock_conn is not None:
        try:
            from sqlalchemy import text

            _lock_conn.execute(
                text("SELECT pg_advisory_unlock(:k)"), {"k": _ADVISORY_LOCK_KEY}
            )
        finally:
            _lock_conn.close()
            _lock_conn = None
