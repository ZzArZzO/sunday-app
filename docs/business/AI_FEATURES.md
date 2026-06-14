# AI Features — Research & Roadmap

*What AI can do for Sunday beyond the chat assistant and the weekly briefing — ranked, costed, and filtered through the MiFID II / MiCA "information, not advice" line (docs/LEGAL.md).*

> Companion to `REVIEW_AND_PLAN.md`. The AI chat assistant is **built** (`api/app/services/llm/`, `web/app/assistant`). This doc is the menu of what comes next.

---

## Guiding constraints (read first)

Every AI feature below is scored against three Sunday-specific filters:

1. **The advice line.** Anything that produces a *personal recommendation* (buy/sell/hold/allocate tailored to the user) crosses into MiFID II / MiCA territory and is **out of scope** as a Publisher. Features that *generate, summarise, explain, or contextualise information* are in scope. Several otherwise-attractive ideas (auto-rebalancing, "optimal portfolio", trade signals) are deliberately down-ranked or reframed for this reason. ([SEC AI-washing precedent](https://www.sec.gov/news/press-release/2024-36))
2. **Cost discipline.** Reuse the two-tier split already in the architecture: **Haiku 4.5** for high-volume summarise/classify/extract, **Sonnet 4.6** for user-facing synthesis, **Opus 4.8** only for paid, credit-gated deep work. Cache the shared market layer across all users (one run/week, ~90% cached-input discount).
3. **Grounding over generation.** Finance is YMYL and hallucination is a UDAAP-style liability. Prefer **RAG** — feed the model real, dated, cited facts (prices, filings, news) and have it *reason over them*, never invent them. This is exactly what `portfolio_context.py` already does for the chat. ([AI-in-fintech 2026 / RAG](https://www.brilworks.com/blog/ai-in-fintech/))

---

## The ranked feature menu

Scoring: **Value** (user pull × differentiation), **Effort** (eng weeks, solo), **Compliance** (🟢 clearly information · 🟡 needs careful framing · 🔴 advice-line risk).

| # | Feature | Value | Effort | Compliance | Tier |
|---|---|---|---|---|---|
| 1 | **"What changed this week" engine** (news/earnings/macro for held tickers) | ★★★★★ | Med | 🟢 | Haiku→Sonnet |
| 2 | **Earnings-call & filing summaries** (per held company) | ★★★★ | Med | 🟢 | Haiku |
| 3 | **News sentiment & narrative tagging** (per holding) | ★★★★ | Med | 🟡 | Haiku |
| 4 | **AI stock deep-dive** (balanced bull/bear research note) | ★★★★ | Med | 🟡 | Sonnet/Opus |
| 5 | **Jargon & concept explainer** (inline "what's CPI?") | ★★★ | Low | 🟢 | Haiku |
| 6 | **Portfolio risk *explanation*** (concentration, factor, correlation, in plain English) | ★★★★ | Med | 🟡 | Sonnet |
| 7 | **Scenario / "what-if" sandbox** (educational, not advisory) | ★★★ | High | 🟡 | Sonnet |
| 8 | **Proactive mid-week alerts** (AI-triaged "something happened to X") | ★★★★ | Med | 🟡 | Haiku |
| 9 | **Behavioural / decision-journal coach** (reflect, not direct) | ★★★ | Med | 🟡 | Sonnet |
| 10 | **Voice / multimodal briefing** (audio "Sunday read", chart-image Q&A) | ★★ | High | 🟢 | Sonnet+TTS |
| 11 | **Document drop-in** (paste a broker PDF / annual report → summary) | ★★★ | Med | 🟢 | Sonnet (PDF) |
| 12 | **Anonymised "what retail holds/asks" insights** (data-moat content) | ★★★ | High | 🟢 | Haiku (batch) |
| ✗ | ~~Auto-rebalancing / optimal allocation / trade signals~~ | — | — | 🔴 **avoid** | — |

---

## Detail on the high-value features

### 1. "What changed this week" engine  🟢  ★★★★★
The emotional core of the briefing and the chat's best fuel. Pipeline: pull news + earnings + macro for **held tickers only** → cheap Haiku/Flash summaries into a per-week `market_snapshot` (shared layer, cached) → Sonnet weaves the personalised "here's what moved your holdings and why". Already the #1 item in `REVIEW_AND_PLAN.md` Sprint 2 — it doubles as context for the chat (`portfolio_context.py` can append "this week's events"). Framing stays descriptive ("NVDA fell 6% after earnings; the miss was in data-center guidance"), never directive. ([earnings/news summarisation](https://officechai.com/learn/ai-tools-for-stock-analysis/))

### 2. Earnings-call & filing summaries  🟢  ★★★★
For each held company, a Haiku pass over the latest transcript / report → 5-bullet "what management said, what changed, what analysts flag." High value, low hallucination risk (grounded in the actual document), cheap. The single most-cited AI capability in 2026 stock-research tools. Gate depth behind Pro. ([earnings call analysis](https://www.tradingkey.com/analysis/stocks/us-stocks/261576043-ai-tools-stock-analysis-investment))

### 3. News sentiment & narrative tagging  🟡  ★★★★
Classify each holding's news flow (positive/negative/neutral + theme tags: "regulatory", "earnings", "guidance"). Drives a calm "sentiment this week" chip and feeds alerts. 🟡 because aggregated sentiment can *read* as a signal — frame as "news tone", show the underlying headlines, never "bullish, buy". ([sentiment analysis](https://officechai.com/learn/ai-tools-for-stock-analysis/))

### 4. AI stock deep-dive  🟡  ★★★★
On-demand, Pro/credit-gated research note on any ticker: business model, recent results, **balanced bull *and* bear cases (attributed)**, key risks, glossary. This is the Fiscal.ai head-to-head — win on *grounded + balanced + EU-tax-aware*. 🟡: must present both sides and attribute opinions; never a verdict. Sonnet default, Opus for "go deep" (credit-gated, protects margin).

### 6. Portfolio risk *explanation*  🟡  ★★★★
Turn the deterministic risk numbers (concentration, asset-class drift, single-name weight, crypto share, rough correlation/factor tilt) into plain-English *understanding*: "64% of your book is large-cap US tech; historically that cluster moves together, so a tech drawdown hits ~two-thirds of your portfolio at once." The numbers stay in Python (auditable); the model only explains. 🟡: explain risk, never prescribe the fix.

### 8. Proactive mid-week alerts  🟡  ★★★★
The retention lever. A scheduled Haiku triage of held-ticker events decides "is this worth a push?" and writes a one-line, neutral notification ("Your holding ASML reports earnings tomorrow" / "CPI prints Wednesday, which historically moves rate-sensitive names you hold"). Strong habit hook between Sunday reads. 🟡: informational triggers only — no "act now."

---

## Cross-cutting AI infrastructure to build alongside

- **RAG retrieval layer** — a thin service that, given a question or a ticker, fetches the relevant grounded facts (portfolio snapshot, this-week events, latest filing/news) and assembles the context. `portfolio_context.py` is the first brick; generalise it. This is what keeps every feature above honest and cheap. ([RAG grounding](https://www.brilworks.com/blog/ai-in-fintech/))
- **Shared market layer + prompt caching** — one weekly Sonnet run produces the regime/macro/sector/crypto-cycle JSON every user's briefing *and* chat references. ~90% cached-input discount; this is the margin lever.
- **Eval harness** — a small golden-set of prompts + expected guardrail behaviour (extend `tests/test_guardrails.py`). Run before every prompt/model change so compliance and quality don't regress silently. Adversarial "try to make it give advice" tests belong here.
- **LLM cost ledger** (`llm_call_log`) — per-user token + model + cached-token accounting, feeding a per-user monthly budget cap with graceful degradation. Already specced in `docs/ROADMAP.md`.

---

## Deliberately out of scope (the advice line)  🔴

These are technically easy and tempting, and they are how this product gets an enforcement action as a Publisher:

- **Auto-rebalancing / "optimal portfolio" / target-weight prescriptions** tailored to the user → personal recommendation → MiFID II / MiCA authorisation required.
- **Buy/sell/hold signals, price targets, "take profits" zones** → market-timing advice.
- **"AI that beats the market" / "expert AI forecasts" marketing** → AI-washing (the PortfolioPilot $175k SEC fine). Describe AI capabilities *accurately*.
- **Agentic AI that executes or recommends trades** → both an advice and an execution problem. Sunday reads data; it does not act on accounts.

If Sunday ever wants these, it's a deliberate move to **register as an adviser** (MiFID II / a CASP for crypto), with the full compliance program — a strategic V3+ decision, not a feature toggle. ([Lowe v. SEC publisher line](https://supreme.justia.com/cases/federal/us/472/181/) · [EU AI Act chatbot disclosure, Aug 2026](https://www.insideprivacy.com/artificial-intelligence/digital-fairness-act-series-topic-2-transparency-and-disclosure-obligations-for-ai-chatbots-in-consumer-interactions/))

---

## Suggested build order (layered on REVIEW_AND_PLAN sprints)

1. **Now (chat shipped):** generalise `portfolio_context.py` into the RAG layer; add the eval harness; wire the shared market layer + cost ledger.
2. **Next:** #1 *What changed this week* (also powers the briefing) → #5 inline explainer in the chat → #2 earnings/filing summaries.
3. **Then:** #3 sentiment chips + #8 mid-week alerts (retention) → #6 risk explanation → #4 Pro stock deep-dive (monetised).
4. **Later / moat:** #11 document drop-in, #9 decision journal, #12 anonymised retail-behaviour insights (data-moat content), #10 voice briefing.

---

## Sources
[AI investing copilots & NL interfaces](https://monday.com/blog/ai-agents/best-ai-for-investing/) · [Earnings/sentiment/risk AI features](https://officechai.com/learn/ai-tools-for-stock-analysis/) · [AI stock analysis 2026](https://www.tradingkey.com/analysis/stocks/us-stocks/261576043-ai-tools-stock-analysis-investment) · [Agentic AI + RAG guardrails in fintech](https://www.brilworks.com/blog/ai-in-fintech/) · [LLM portfolio research](https://dl.acm.org/doi/10.1145/3768292.3770376) · [SEC AI-washing](https://www.sec.gov/news/press-release/2024-36) · [EU AI Act chatbot disclosure](https://www.insideprivacy.com/artificial-intelligence/digital-fairness-act-series-topic-2-transparency-and-disclosure-obligations-for-ai-chatbots-in-consumer-interactions/) · [Lowe v. SEC](https://supreme.justia.com/cases/federal/us/472/181/)
