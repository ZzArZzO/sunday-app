from pydantic import BaseModel


class NewsItemView(BaseModel):
    holding: str
    title: str
    summary: str
    publisher: str | None = None
    url: str | None = None
    published_at: str | None = None


class EarningsEventView(BaseModel):
    ticker: str
    date: str  # YYYY-MM-DD


class EventsResponse(BaseModel):
    as_of: str
    news: list[NewsItemView]
    earnings: list[EarningsEventView]
    notes: list[str]
