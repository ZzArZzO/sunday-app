"""Anthropic client factory.

Lazily constructs a single Anthropic SDK client from settings. Kept tiny and
separate so tests can monkeypatch `get_client` without importing the SDK, and so
EU data-residency configuration lives in exactly one place.

Set `ANTHROPIC_BASE_URL` to Anthropic's EU regional endpoint before launch (see
docs/LEGAL.md — EU endpoints + DPA only). When unset, the SDK default is used,
which is fine for local development against test keys.
"""

from __future__ import annotations

from functools import lru_cache

import anthropic

from app.config import get_settings


class LLMNotConfigured(RuntimeError):
    """Raised when an LLM call is attempted without an API key configured."""


@lru_cache
def get_client() -> anthropic.Anthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise LLMNotConfigured(
            "ANTHROPIC_API_KEY is not set. The AI assistant is unavailable until "
            "it is configured."
        )
    kwargs: dict[str, object] = {"api_key": settings.anthropic_api_key}
    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
    return anthropic.Anthropic(**kwargs)  # type: ignore[arg-type]
