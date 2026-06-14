from __future__ import annotations

from pydantic import BaseModel, Field


class PreviewColumnView(BaseModel):
    source: str
    mapped_to: str
    confidence: str
    sample: str | None = None


class PreviewRowView(BaseModel):
    line: int
    status: str  # "ok" | "skipped"
    reason: str | None = None
    date: str | None = None
    kind: str | None = None
    ticker: str | None = None
    quantity: str | None = None
    unit_price_eur: str | None = None


class IngestPreviewResponse(BaseModel):
    detected_format: str
    columns: list[PreviewColumnView] = Field(default_factory=list)
    unmapped_headers: list[str] = Field(default_factory=list)
    rows: list[PreviewRowView] = Field(default_factory=list)
    ok_count: int
    skipped_count: int
    warnings: list[str] = Field(default_factory=list)
