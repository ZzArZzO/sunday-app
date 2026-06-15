"""AI assistant chat endpoint.

POST /api/chat — answer a portfolio question, grounded and guardrailed.

Kept as a sync handler (like the rest of the app); FastAPI runs it in a
threadpool, so the blocking Anthropic call doesn't stall the event loop.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, get_default_portfolio
from app.models import Portfolio, User
from app.schemas.chat import (
    ChatGrounding,
    ChatGroundingHolding,
    ChatRequest,
    ChatResponse,
)
from app.services.billing import budget
from app.services.llm import assistant
from app.services.llm.client import LLMNotConfigured

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _require_user_last(body: ChatRequest) -> None:
    if body.messages[-1].role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The last message must be from the user.",
        )


@router.post("", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    portfolio: Portfolio = Depends(get_default_portfolio),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    _require_user_last(body)

    if budget.is_exhausted(db, user):
        # Canned (not AI-generated) → drop the "Generated with AI assistance" line.
        return ChatResponse(
            reply=budget.ALLOWANCE_MESSAGE,
            model="",
            guardrail_triggered=False,
            grounding=None,
            disclaimers=["Not investment advice. Information only."],
        )

    try:
        result = assistant.answer(portfolio, body.messages)
    except LLMNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except anthropic.APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI assistant is temporarily unavailable. Please try again.",
        ) from exc

    grounding = ChatGrounding(
        as_of=result.grounding.as_of,
        holdings=[
            ChatGroundingHolding(ticker=h.ticker, weight_pct=h.weight_pct)
            for h in result.grounding.holdings
        ],
        facts=result.grounding.facts,
    )

    return ChatResponse(
        reply=result.reply,
        model=result.model,
        guardrail_triggered=result.guardrail_triggered,
        grounding=grounding,
    )


@router.post("/stream")
def post_chat_stream(
    body: ChatRequest,
    portfolio: Portfolio = Depends(get_default_portfolio),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Server-sent-events variant. Each event is one `data: {json}` line.

    The guardrail runs incrementally inside `answer_stream` (see its docstring):
    advice-shaped text is caught before it leaves the server.
    """
    _require_user_last(body)
    exhausted = budget.is_exhausted(db, user)

    def event_stream() -> Iterator[str]:
        if exhausted:
            yield f"data: {json.dumps({'type': 'delta', 'text': budget.ALLOWANCE_MESSAGE})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'guardrail_triggered': False, 'model': '', 'grounding': None})}\n\n"
            return
        try:
            for event in assistant.answer_stream(portfolio, body.messages):
                yield f"data: {json.dumps(event)}\n\n"
        except LLMNotConfigured as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
        except anthropic.APIError:
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "detail": "The AI assistant is temporarily unavailable. Please try again.",
                    }
                )
                + "\n\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
