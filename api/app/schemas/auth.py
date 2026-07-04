from pydantic import BaseModel


class MeResponse(BaseModel):
    authenticated: bool
    email: str | None = None
    country: str | None = None


class UpdateCountryRequest(BaseModel):
    """Set the signed-in user's tax-residence country (ISO-3166 alpha-2)."""

    country: str
