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
