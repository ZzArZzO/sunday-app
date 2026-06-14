from pydantic import BaseModel


class DeliveryResultView(BaseModel):
    email: str
    ok: bool
    dry_run: bool = False
    subject: str | None = None
    message_id: str | None = None
    error: str | None = None


class WeeklyDeliverySummary(BaseModel):
    total: int
    sent: int
    failed: int
    dry_run: bool
    results: list[DeliveryResultView]
