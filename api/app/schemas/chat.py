from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

# Bound the conversation so a single request can't blow up token cost.
MAX_MESSAGES = 40
MAX_CONTENT_CHARS = 4000


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=MAX_CONTENT_CHARS)


class ChatRequest(BaseModel):
    """The full conversation so far. The last message must be from the user."""

    messages: list[ChatMessage] = Field(..., min_length=1, max_length=MAX_MESSAGES)


class ChatGroundingHolding(BaseModel):
    ticker: str
    weight_pct: Decimal


class ChatGrounding(BaseModel):
    """The deterministic facts the assistant was given — surfaced so the user
    can see (and trust) exactly what the answer was grounded in."""

    as_of: str | None = None
    holdings: list[ChatGroundingHolding] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    model: str
    # True when the MiFID II forbidden-phrase guardrail had to intervene.
    guardrail_triggered: bool = False
    grounding: ChatGrounding | None = None
    disclaimers: list[str] = Field(
        default_factory=lambda: [
            "Not investment advice. Information only.",
            "Generated with AI assistance.",
        ]
    )
