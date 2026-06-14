"""MiFID II / MiCA output guardrails for LLM-generated text.

The bright line (docs/LEGAL.md): the product must stay on the *general
information* side and never produce a **personal recommendation** to buy, sell,
hold, or rebalance a specific instrument. This module is the deterministic
backstop that runs on every model output before it reaches the user.

Design:
    - `scan()` returns the list of forbidden phrases a text trips (empty == clean).
    - The assistant service uses this to (a) re-prompt once with a stricter system
      message, then (b) fall back to a safe canned reply if it still trips.

The patterns target *advice-shaped* phrasing ("you should sell", "I'd recommend
trimming") rather than the bare word "recommend", so the model's own compliant
disclaimer ("I can't give personal recommendations") does not false-positive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Each entry: (human-readable label, compiled case-insensitive pattern).
# Keep these conservative and advice-shaped — see module docstring.
_FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("directive 'you should'", re.compile(r"\byou\s+should\b", re.IGNORECASE)),
    ("directive 'you ought to'", re.compile(r"\byou\s+ought\s+to\b", re.IGNORECASE)),
    ("directive 'you need to (buy|sell)'", re.compile(r"\byou\s+need\s+to\s+(buy|sell|trim|rebalance)\b", re.IGNORECASE)),
    ("personal recommendation", re.compile(r"\b(i|we)\s*(would|'?d|'?ll)?\s*(recommend|suggest|advise)\b", re.IGNORECASE)),
    ("'my recommendation'", re.compile(r"\bmy\s+recommendation\b", re.IGNORECASE)),
    ("'consider <action>'", re.compile(r"\bconsider\s+(trimming|selling|buying|rebalancing|rotating|adding|reducing|increasing|decreasing|cutting)\b", re.IGNORECASE)),
    ("'rebalance into'", re.compile(r"\brebalance\s+into\b", re.IGNORECASE)),
    ("'take profits'", re.compile(r"\btake\s+profits?\b", re.IGNORECASE)),
    ("'buy the dip'", re.compile(r"\bbuy\s+the\s+dip\b", re.IGNORECASE)),
    ("market-timing 'good time to buy/sell'", re.compile(r"\bgood\s+time\s+to\s+(buy|sell)\b", re.IGNORECASE)),
    ("directive 'buy/sell now'", re.compile(r"\b(buy|sell)\s+now\b", re.IGNORECASE)),
]

# What we return when even a re-prompt cannot produce a compliant answer.
SAFE_FALLBACK_REPLY = (
    "I can't give personalised buy, sell, or rebalancing advice — Sunday is an "
    "information and education tool, not a financial adviser. I can instead "
    "explain what's happening with your holdings, define any terms, or walk "
    "through how something like concentration or a macro event generally works. "
    "Want me to do that?"
)


@dataclass(frozen=True)
class GuardrailResult:
    clean: bool
    violations: list[str]


def scan(text: str) -> GuardrailResult:
    """Return which forbidden patterns (if any) the text trips."""
    violations = [label for label, pattern in _FORBIDDEN_PATTERNS if pattern.search(text)]
    return GuardrailResult(clean=not violations, violations=violations)


STRICTER_REPROMPT = (
    "Your previous answer contained language that reads as a personal "
    "recommendation, which is not allowed. Rewrite it as purely descriptive, "
    "educational, and neutral information. Do NOT tell the user what to do, do "
    "NOT use phrases like 'you should', 'consider selling/trimming', 'I "
    "recommend', 'take profits', or 'good time to buy'. Explain and contextualise "
    "only; the user decides for themselves."
)
