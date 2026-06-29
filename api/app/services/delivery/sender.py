"""Email sender — Resend when configured, dry-run otherwise.

No `RESEND_API_KEY` → dry-run: the email is rendered and logged but not sent, so
the whole delivery path is exercisable without an email provider. With a key set,
it POSTs to the Resend REST API (via httpx — already a dependency).
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"


@dataclass(frozen=True)
class SendResult:
    to: str
    ok: bool
    dry_run: bool = False
    message_id: str | None = None
    error: str | None = None


def send_email(
    to: str,
    subject: str,
    html: str,
    text: str | None = None,
    attachments: list[tuple[str, bytes]] | None = None,
) -> SendResult:
    """Send an email; `attachments` is a list of (filename, content_bytes)."""
    settings = get_settings()

    if not settings.resend_api_key:
        log.info(
            "[email dry-run] to=%s subject=%r attachments=%d (no RESEND_API_KEY)",
            to,
            subject,
            len(attachments or []),
        )
        return SendResult(to=to, ok=True, dry_run=True)

    payload: dict[str, object] = {
        "from": settings.email_from_validated,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    if attachments:
        payload["attachments"] = [
            {"filename": name, "content": base64.b64encode(content).decode("ascii")}
            for name, content in attachments
        ]

    try:
        resp = httpx.post(
            _RESEND_URL,
            json=payload,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            timeout=20.0,
        )
    except httpx.HTTPError as exc:
        return SendResult(to=to, ok=False, error=f"network error: {exc}")

    if resp.status_code >= 400:
        return SendResult(to=to, ok=False, error=f"HTTP {resp.status_code}: {resp.text[:300]}")

    try:
        message_id = resp.json().get("id")
    except ValueError:
        message_id = None
    return SendResult(to=to, ok=True, message_id=message_id)
