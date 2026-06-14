"""LLM layer for Sunday.

Everything that talks to Anthropic lives here so cost control and the MiFID II
output guardrails are enforced in one place (per docs/LEGAL.md). The rest of the
app stays deterministic — see services/briefing_composer.py.

Modules:
    client            — lazily-constructed Anthropic SDK client (EU endpoint aware)
    guardrails        — forbidden-phrase scan + re-prompt loop (no personal advice)
    portfolio_context — deterministic, compact portfolio summary fed to the model
    assistant         — the portfolio-grounded chat assistant
"""
