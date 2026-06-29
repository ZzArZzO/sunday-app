from pydantic import BaseModel


class MagicLinkRequest(BaseModel):
    email: str


class MagicLinkResponse(BaseModel):
    sent: bool
    dry_run: bool
    # In dry-run (no email provider) we return the link so dev can sign in.
    dev_link: str | None = None


class MeResponse(BaseModel):
    authenticated: bool
    email: str | None = None
    country: str | None = None


class UpdateCountryRequest(BaseModel):
    """Set the signed-in user's tax-residence country (ISO-3166 alpha-2)."""

    country: str


class ExchangeRequest(BaseModel):
    """Mobile sign-in: trade a magic-link token for a session token (JSON, no cookie)."""

    magic_token: str


class ExchangeResponse(BaseModel):
    session_token: str
    email: str | None = None
    country: str | None = None
