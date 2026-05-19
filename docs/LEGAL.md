# Legal positioning

> **This file is engineering-facing.** It captures the rules that shape the codebase: what the LLM is allowed to say, what guardrails exist, what default UX choices are non-negotiable. It is NOT legal advice. A licensed EU regulatory lawyer must review before launch.

## The four regimes that apply

| Regime | Citation | What it controls |
|---|---|---|
| MiFID II | Directive 2014/65/EU, Art. 4(1)(4) | Investment advice on financial instruments — requires authorization |
| MiCA | Regulation 2023/1114, Art. 3 | Same, for crypto-assets — requires CASP authorization |
| EU AI Act | Reg. 2024/1689 | Transparency obligations for AI systems |
| GDPR | Reg. 2016/679 | Portfolio data is sensitive personal data |

## The bright line (MiFID II Art. 4(1)(4))

> "Investment advice" = a **personal recommendation** to a **specific person** about a **specific instrument**, presented as **suitable** for them.

All four prongs must be met. Without a MiFID II / CASP licence, the product MUST stay on the "general information" side.

| Phrasing | Verdict |
|---|---|
| "S&P 500 is in a risk-on regime" | OK — general info |
| "Your portfolio is 31% NVDA" | OK — fact about user's data |
| "Concentration over 10% is generally considered elevated" | OK — generic education |
| "Your NVDA position is too large — consider trimming" | **CROSSES THE LINE** |
| "BTC is near a cycle top per market-top-detector" | Borderline (general if framed as market analysis; advice if framed as "you should sell") |
| "Your DE crypto crosses the 1-year mark on 2026-08-12 → tax-free in DE" | OK — informational tax flag |

## Engineering rules

### Thresholds are user-set, never platform-set
- Concentration warn / alert thresholds: collected in onboarding, stored on user row
- Defaults shown in `services/concentration.py` (`DEFAULT_WARN_PCT`, `DEFAULT_ALERT_PCT`) are *slice placeholders only*
- Production reads from `users.alert_settings`; the UI says "your warning threshold" not "our recommended threshold"

### LLM output guardrails (`services/llm/guardrails.py`, Phase 2)
- Forbidden-phrase regex applied to every LLM output before persistence/delivery
- Triggers re-prompt with stricter system message if hit
- Forbidden phrases (non-exhaustive): `you should`, `consider (trimming|selling|buying|rebalancing|rotating)`, `recommend`, `rebalance into`, `take profits`, `buy the dip`, `it's a good time to`
- Allowed: descriptive, observational, comparative, educational

### Required disclaimers (every screen)
- "Not investment advice. Information only." — persistent footer on dashboard, briefing, alerts
- "Generated with AI assistance." — every LLM-touched output (AI Act transparency)
- Component: `web/components/Disclaimer.tsx` — single source of truth

### Crypto take-profit framing (special care)
- JTBD #3 in the one-pager mentions "crypto near take-profit zones" — DO NOT ship that phrasing
- Replace with: "your average cost basis vs. current price" + user-set price alerts
- Never write "near take-profit zone" in product copy

### Tax flags vs. tax advice
- Flags are observational: "your DE 1-year mark is X"
- Never write: "you should hold until X to optimize tax"
- Country-specific rules live in deterministic Python (`services/tax_flags.py` in Phase 2), not LLM

### GDPR posture
- Portfolio data (quantities, cost basis) treated as sensitive — field-level encryption planned for Phase 2
- DSAR workflow: account-deletion endpoint cascades to all owned data
- Anthropic EU endpoints only — DPA must be in place before launch
- No third-party analytics with portfolio data in payload (Plausible or self-hosted only)

### AI Act
- Investment-recommendation AI may fall under Annex III high-risk — *informational* AI likely does not
- Transparency obligation: every LLM-touched output must disclose AI use (already enforced via `Disclaimer`)
- Logging: keep input + output tokens + model + timestamp per call (helps if regulator ever asks)

## DORA exposure

- DORA applies to "financial entities". An unlicensed information service does not become a financial entity by virtue of using AI.
- If the product ever obtains MiFID II authorization (or operates as a tied agent), DORA applies: incident reporting, ICT risk management framework, third-party register including Anthropic.

## Pre-launch legal checklist

- [ ] DE BaFin pre-launch consultation (free for fintech via FinTech-Kontakt)
- [ ] PT CMVM consultation
- [ ] Privacy policy + ToS + Cookie policy + DE Impressum drafted by licensed counsel
- [ ] DPIA documented
- [ ] Anthropic EU DPA executed
- [ ] Stripe DPA executed
- [ ] Marketing copy reviewed against MiFID II non-advice positioning ("robo-advisor" language is the trap)

## When in doubt

If a feature, copy line, or LLM output would feel weird if a regulator read it over your shoulder, change it. The cost of one round-trip with counsel is far less than the cost of an enforcement action.
