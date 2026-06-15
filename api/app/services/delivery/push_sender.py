"""Push sender — Firebase Cloud Messaging (HTTP v1) when configured, dry-run otherwise.

No FCM credentials → dry-run: the notification is logged but not sent, so the
whole push path (register → deliver) is exercisable without a Firebase project —
mirroring how `sender.py` runs email without a Resend key.

With `FCM_PROJECT_ID` + `FCM_CREDENTIALS_JSON` (a service-account key file) set,
it mints an OAuth2 access token and POSTs to the FCM v1 endpoint. iOS is routed
through FCM too (the standard Capacitor setup: APNs key uploaded to Firebase),
so this single path covers both platforms. `google-auth` is imported lazily —
like apscheduler in `scheduler.py` — so it isn't a hard dependency for dry-run.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_FCM_V1 = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"


@dataclass(frozen=True)
class PushResult:
    token: str
    ok: bool
    dry_run: bool = False
    message_id: str | None = None
    error: str | None = None


def _access_token(credentials_path: str) -> str:
    """Mint a short-lived FCM access token from a service-account key file."""
    from google.auth.transport.requests import Request  # type: ignore
    from google.oauth2 import service_account  # type: ignore

    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=[_FCM_SCOPE]
    )
    creds.refresh(Request())
    return creds.token


def send_push(
    token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> PushResult:
    """Send a single notification to one device token."""
    settings = get_settings()

    if not settings.fcm_project_id or not settings.fcm_credentials_json:
        # Don't log the token (it's a routing credential) — title is enough.
        log.info("[push dry-run] title=%r (no FCM_PROJECT_ID/FCM_CREDENTIALS_JSON)", title)
        return PushResult(token=token, ok=True, dry_run=True)

    try:
        access_token = _access_token(settings.fcm_credentials_json)
    except ImportError:
        return PushResult(
            token=token,
            ok=False,
            error="google-auth not installed (pip install google-auth) — cannot send FCM push",
        )
    except (OSError, ValueError) as exc:
        return PushResult(token=token, ok=False, error=f"FCM credentials error: {exc}")

    inner: dict[str, object] = {
        "token": token,
        "notification": {"title": title, "body": body},
    }
    if data:
        # FCM data values must be strings.
        inner["data"] = {k: str(v) for k, v in data.items()}

    url = _FCM_V1.format(project_id=settings.fcm_project_id)
    try:
        resp = httpx.post(
            url,
            content=json.dumps({"message": inner}),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=20.0,
        )
    except httpx.HTTPError as exc:
        return PushResult(token=token, ok=False, error=f"network error: {exc}")

    if resp.status_code >= 400:
        return PushResult(
            token=token, ok=False, error=f"HTTP {resp.status_code}: {resp.text[:300]}"
        )

    try:
        message_id = resp.json().get("name")
    except ValueError:
        message_id = None
    return PushResult(token=token, ok=True, message_id=message_id)
