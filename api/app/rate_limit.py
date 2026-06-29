"""Lightweight rate limiting as a FastAPI dependency.

Uses the `limits` library (a fixed-window in-memory limiter) wrapped in a
dependency factory. A dependency — rather than a route decorator — keeps the
endpoint signatures untouched, so FastAPI still resolves request bodies normally.

In-memory storage is per-process: good enough for a single API instance; swap the
storage for Redis (`limits.storage.RedisStorage`) if you scale to many instances.
Disabled wholesale when `rate_limit_enabled` is False (tests/benchmarks).
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException, Request, status
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

from app.config import get_settings

_storage = MemoryStorage()
_limiter = FixedWindowRateLimiter(_storage)


def rate_limit(limit_str: str, scope: str) -> Callable[[Request], None]:
    """Build a dependency enforcing `limit_str` (e.g. "5/minute") per client IP."""
    item = parse(limit_str)

    def _dependency(request: Request) -> None:
        if not get_settings().rate_limit_enabled:
            return
        client_ip = request.client.host if request.client else "anonymous"
        if not _limiter.hit(item, scope, client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a moment and try again.",
            )

    return _dependency
