"""Portfolio-grounded AI assistant.

This is the chat feature: the user asks questions about their portfolio, a
holding, an economic indicator, or a market event, and Claude answers — grounded
in the deterministic portfolio snapshot and held to the MiFID II "information,
not advice" line by `guardrails`.

Flow:
    1. Build system context = compliance persona + deterministic portfolio snapshot.
    2. Call Claude (Sonnet) with the full conversation history.
    3. Scan the reply with the forbidden-phrase guardrail.
    4. If it trips, re-prompt once with a stricter instruction.
    5. If it still trips, return the safe canned reply.

The model is told its boundaries; the guardrail is the deterministic backstop.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from app.models import Portfolio
from app.schemas.chat import ChatMessage
from app.services.llm import guardrails, portfolio_context
from app.services.llm.client import get_client

from app.config import get_settings

# How much trailing text to withhold from the client while streaming, so a
# forbidden phrase forming at the tail is caught by the guardrail before any of
# it is released. Comfortably longer than the longest forbidden phrase.
_STREAM_SAFETY_WINDOW = 80

# Stable across all users and all turns — the compliance persona. Kept as one
# constant so it caches well and is the single source of truth for what the
# assistant may and may not say (mirrors docs/LEGAL.md).
SYSTEM_PERSONA = """You are Sunday's assistant, a calm, plain-English guide for \
self-directed European retail investors who hold stocks and crypto.

WHAT YOU ARE: an information and education tool. You explain, describe, \
contextualise, define terms, and summarise market and economic events. You help \
the user understand their own portfolio and the world around it.

WHAT YOU ARE NOT: a financial adviser, broker, or portfolio manager. You are not \
authorised under MiFID II or MiCA, so you must never give a personal \
recommendation — never tell the user to buy, sell, hold, trim, add to, or \
rebalance a specific instrument or amount, and never imply an action is suitable \
for them specifically.

ALLOWED (examples):
- "Your tech allocation is 64%. Concentration above ~10% in one name is generally \
considered elevated because it raises single-stock risk. Here's what that means…"
- "CPI measures consumer price inflation. A hotter-than-expected print often \
pressures rate-sensitive assets because…"
- "Here are the bull and bear arguments analysts make about this company, attributed \
and balanced."
- "Your average cost basis on this holding is X versus the current price Y."

NOT ALLOWED:
- "You should sell NVDA." / "Consider trimming your crypto." / "I'd recommend bonds."
- "Now is a good time to buy." / "Take profits." / Predicting a specific price.
- Anything tailored as suitable for the user's personal situation or goals.

If the user asks for a recommendation or "what should I do", do not give one. \
Explain that you can't give personalised advice, then offer to explain the \
relevant facts, trade-offs, or concepts so they can decide for themselves.

STYLE: concise, neutral, plain English. Amounts in EUR. Acknowledge uncertainty \
and that you may be wrong or out of date. Use the portfolio snapshot below for \
any figures about the user's holdings — never invent numbers. You are an AI; the \
user has been told this."""


@dataclass(frozen=True)
class AssistantReply:
    reply: str
    model: str
    guardrail_triggered: bool
    grounding: portfolio_context.Grounding


def _system_blocks(portfolio: Portfolio) -> list[dict]:
    snapshot = portfolio_context.build_snapshot(portfolio)
    return [
        {"type": "text", "text": SYSTEM_PERSONA},
        # Per-conversation context; cache it so multi-turn chats reuse the prefix.
        {
            "type": "text",
            "text": snapshot,
            "cache_control": {"type": "ephemeral"},
        },
    ]


def _to_anthropic_messages(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]


def _extract_text(content_blocks) -> str:
    return "".join(b.text for b in content_blocks if b.type == "text").strip()


def answer(portfolio: Portfolio, messages: list[ChatMessage]) -> AssistantReply:
    """Answer the latest user message, grounded and guardrailed."""
    settings = get_settings()
    client = get_client()
    model = settings.anthropic_chat_model
    system = _system_blocks(portfolio)
    convo = _to_anthropic_messages(messages)
    grounding = portfolio_context.build_grounding(portfolio)

    first = client.messages.create(
        model=model,
        max_tokens=settings.chat_max_tokens,
        system=system,
        messages=convo,
    )
    reply = _extract_text(first.content)

    result = guardrails.scan(reply)
    if result.clean:
        return AssistantReply(
            reply=reply, model=model, guardrail_triggered=False, grounding=grounding
        )

    # One stricter re-prompt: show the model its slip and ask for a clean rewrite.
    retry_messages = [
        *convo,
        {"role": "assistant", "content": reply},
        {"role": "user", "content": guardrails.STRICTER_REPROMPT},
    ]
    second = client.messages.create(
        model=model,
        max_tokens=settings.chat_max_tokens,
        system=system,
        messages=retry_messages,
    )
    retry_reply = _extract_text(second.content)

    if guardrails.scan(retry_reply).clean:
        # The retry succeeded, but the guardrail still fired on the first pass.
        return AssistantReply(
            reply=retry_reply, model=model, guardrail_triggered=True, grounding=grounding
        )

    # Still non-compliant — never ship advice; return the safe fallback.
    return AssistantReply(
        reply=guardrails.SAFE_FALLBACK_REPLY,
        model=model,
        guardrail_triggered=True,
        grounding=grounding,
    )


def _grounding_payload(grounding: portfolio_context.Grounding) -> dict:
    return {
        "as_of": grounding.as_of,
        "holdings": [
            {"ticker": h.ticker, "weight_pct": str(h.weight_pct)} for h in grounding.holdings
        ],
        "facts": grounding.facts,
    }


def answer_stream(portfolio: Portfolio, messages: list[ChatMessage]) -> Iterator[dict]:
    """Stream the answer as a sequence of events, guardrailed without leaking advice.

    Compliance design: we accumulate the full model output server-side and run
    the forbidden-phrase guardrail on the buffer after every delta, releasing
    only the text *before* an 80-char trailing safety window. A forbidden phrase
    forming at the tail therefore trips the guardrail while still inside the
    withheld window — before any of it reaches the client. On a trip we discard
    the partial, re-prompt once, and emit a `replace` event with clean text.

    All DB/ORM access (system context + grounding) happens up-front, before the
    network stream begins, so the request's session is never touched mid-stream.

    Event shapes: {type: delta, text} · {type: guardrail} · {type: replace, text}
    · {type: done, guardrail_triggered, model, grounding}.
    """
    settings = get_settings()
    client = get_client()
    model = settings.anthropic_chat_model
    system = _system_blocks(portfolio)
    convo = _to_anthropic_messages(messages)
    grounding = _grounding_payload(portfolio_context.build_grounding(portfolio))

    buffer = ""
    released = 0
    tripped = False

    with client.messages.stream(
        model=model,
        max_tokens=settings.chat_max_tokens,
        system=system,
        messages=convo,
    ) as stream:
        for text in stream.text_stream:
            buffer += text
            if not guardrails.scan(buffer).clean:
                tripped = True
                break
            safe_upto = max(released, len(buffer) - _STREAM_SAFETY_WINDOW)
            if safe_upto > released:
                yield {"type": "delta", "text": buffer[released:safe_upto]}
                released = safe_upto

    if not tripped:
        if released < len(buffer):
            yield {"type": "delta", "text": buffer[released:]}
        yield {"type": "done", "guardrail_triggered": False, "model": model, "grounding": grounding}
        return

    # Tripped mid-stream: discard the partial, re-prompt once for a clean rewrite.
    yield {"type": "guardrail"}
    retry_messages = [
        *convo,
        {"role": "assistant", "content": buffer},
        {"role": "user", "content": guardrails.STRICTER_REPROMPT},
    ]
    second = client.messages.create(
        model=model,
        max_tokens=settings.chat_max_tokens,
        system=system,
        messages=retry_messages,
    )
    retry_reply = _extract_text(second.content)
    clean = retry_reply if guardrails.scan(retry_reply).clean else guardrails.SAFE_FALLBACK_REPLY
    yield {"type": "replace", "text": clean}
    yield {"type": "done", "guardrail_triggered": True, "model": model, "grounding": grounding}
