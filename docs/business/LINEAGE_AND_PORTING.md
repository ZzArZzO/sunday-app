# Lineage & Porting — from `investment-ai` to Sunday

*Where Sunday came from, what's already been solved in the original, what to lift, and the one thing the original does that the SaaS legally cannot.*

> **The seed:** `Desktop/investment-ai` — a working, single-user personal investment analyst built on Claude Code: deterministic Python ETL writes weekly snapshots, custom + tradermonty skills drive analysis, a Next.js dashboard renders it, a Windows scheduled task runs it daily. Privacy-first, manual-holdings, no chain reads, dual EUR/USD, halt-on-partial.
>
> **The SaaS:** `Desktop/sunday-app` — the multi-tenant port of that idea. It inherited the *philosophy* faithfully (deterministic numbers + LLM narrative, EU-first, privacy-first, manual-first) but only a **subset of the features**. Several things the SaaS still has as placeholders are already **built and working** in the seed.

The seed's `product-onepager.md` is literally Sunday's product spec, and its `custom-skills/weekly-review/SKILL.md` is literally the Sunday-briefing spec (NAV + WoW, asset-class breakdown, top movers, macro context, cycle position, allocation drift, "1–2 things to watch", suggested history row). When in doubt about what a Sunday feature should output, **read the corresponding seed skill** — the design work is already done.

---

## 1. Capability reconciliation

| Capability | In the seed (`investment-ai`) | In Sunday today | Port priority | Compliance for SaaS |
|---|---|---|---|---|
| **Live prices + per-asset P&L** | ✅ `scripts/build_snapshot.py` + finance MCP (yfinance), dual EUR/USD | ❌ placeholder (`pnl.py` falls back to cost basis; FX hardcoded `1.08`) | **🔴 Sprint 0** | 🟢 fine |
| **Net-worth history / real WoW** | ✅ `portfolio-history.csv`, daily rows via scheduler | ❌ **WoW hardcoded to 0** | **🔴 Sprint 0** | 🟢 fine |
| **Sells / DCA / cost-basis maintenance** | ✅ `dca-tracker` (weighted-avg, atomic write) | ❌ CSV ingests `buy` rows only | **🔴 Sprint 0** | 🟢 fine |
| **"What changed this week" / news** | ✅ `scripts/build_news.py` → `news-*.json`, dashboard News tab | ❌ placeholder section | **🟠 Sprint 2** | 🟢 (describe, attribute) |
| **Crypto-cycle signal (BTC)** | ✅ `crypto-cycle-monitor` — Pi-Cycle, Puell, Mayer computed from BTC-USD; composite GREEN→EXTREME verdict, **no paid API** | ❌ "regime/crypto-cycle" is a placeholder string | **🟠 high-value** | 🟡 informational *only* (see §2) |
| **Economic calendar** | ✅ `economic-calendar` skill | ❌ briefing mentions it; not built | 🟠 | 🟢 fine |
| **Per-ticker deep-dive reports** | ✅ `analyze_ticker.py` → `data/reports/` + action/DCA syntheses | ❌ none | 🟡 (maps to AI_FEATURES #4) | 🟡 balanced/attributed |
| **Macro/regime narrative** | ✅ tradermonty `market-environment-analysis`, `macro-regime-detector`, `market-top-detector` | ❌ placeholder | 🟠 | 🟡 informational |
| **Richer asset model** (bonds, cash, leveraged/CFD, loan-DCA) | ✅ `manual-holdings.json` (crypto/bonds/bank_accounts/trading_accounts/loan_dca; equity-in-NAV vs notional-as-risk) | ⚠️ only stock/etf/crypto/cash | 🟡 V2 | 🟢 (tracking) |
| **Leveraged-account risk** (notional ≠ NAV, Bybit live read) | ✅ `bybit_client.py`, separate `leveraged_exposure_eur` | ❌ none | 🟡 V2/V3 | 🟡 (read-only data) |
| **PII firewall** | ✅ `tr-sanitizer` (strip name/IBAN/account-id) + `pii-tripwire` | ⚠️ lighter ("strips by not reading") | 🟠 (harden before launch) | 🟢 (GDPR) |
| **Daily automation** | ✅ Windows scheduled task → `daily_update.py` | ❌ Sunday cron is Phase 3 | 🟠 Sprint 3 | 🟢 fine |
| **EU tax engine** | partial (DE-flavoured, in CLAUDE.md profile) | ✅ **richer in Sunday** (`tax_summary.py`: DE/FR/ES/NL/IT/PT) | — (Sunday is ahead here) | 🟢 informational |
| **FIRE planner** | ❌ not in seed | ✅ **net-new in Sunday** | — | 🟢 |
| **AI chat assistant** | the whole tool *is* a Claude chat | ✅ **just built** (`services/llm/`) | — | 🟢 guardrailed |
| **Profit-taking ladder** (staged sell plan, armed/triggered, realized-pnl journal) | ✅ `profit-taking-ladder` skill | ❌ **explicitly DO-NOT-SHIP** (`docs/LEGAL.md`) | ⛔ **do not port as-is** | 🔴 **advice — see §2** |
| **Position sizing / breakout / VCP / "should I trim X?"** | ✅ tradermonty `position-sizer`, `breakout-trade-planner`, `vcp-screener`; power-prompts like "Should I trim RENDER?" | ❌ none | ⛔ keep out | 🔴 **advice** |

---

## 2. The regulatory delta (the most important lineage insight)

**The seed is allowed to do things the SaaS is not — because advising *yourself* is not being an investment adviser, but doing the same thing *for thousands of paying strangers* is.**

In `investment-ai`, you are the only user and the only "client." A profit-taking ladder that says *"sell 10% of BTC at $180k"*, a `position-sizer` that says *"add €500 to MSFT given your allocation"*, or a power-prompt *"Should I trim RENDER or SOL?"* are all fine — you're a person using a tool to reason about your own money. There is no adviser/client relationship.

The moment Sunday ships the **same features to paying users**, every one of those becomes a **personal recommendation to a specific person about a specific instrument, presented as suitable for them** — the exact MiFID II Art. 4(1)(4) definition of investment advice (`docs/LEGAL.md`). As a Publisher, Sunday must stay on the *information/education* side. So:

| Seed feature | Why it's fine for you | Why it's a landmine as a SaaS | Sunday's compliant version |
|---|---|---|---|
| **Profit-taking ladder** ("sell X% at $Y") | self-directed planning | staged **sell recommendation** per user | **User-set price alerts only.** "BTC reached the €X level you flagged." No sell %, no "execute this rung", no ACTION block. (`docs/LEGAL.md` already prescribes this.) |
| **Crypto-cycle → "execute first rung"** | you decide to act | a timing/sell signal | Ship the **verdict as information** ("BTC cycle indicators are in a historically elevated zone; here's what that has meant historically — heuristic, not predictive"). Never wire it to a per-user "now sell" action. |
| **`position-sizer` / `exposure-coach`** ("add €500 to MSFT") | personal calc | personalised allocation advice | Explain concentration/diversification **concepts**; show the user's own numbers. Never prescribe an amount or action. |
| **"Should I trim RENDER?"** power-prompt | you asking yourself | advice on demand | The chat already refuses this (guardrails) and re-frames to education. ✅ working as intended. |

**Bottom line:** port the seed's *analytical engine* (prices, snapshots, WoW, cycle indicators, news, per-ticker facts) — it's gold and mostly 🟢. Do **not** port the seed's *action layer* (ladders, sizing, trim/sell prompts) — that's the line. The crypto-cycle monitor is the sharpest example of both: the **indicator** is a strong informational differentiator to ship; the **"execute your ladder" action** it feeds is the thing to leave behind.

---

## 3. Already solved in the seed — lift directly (de-risks the sprints)

These are working implementations in `investment-ai/scripts/` and `custom-skills/` that map 1:1 onto Sunday's reordered plan (`REVIEW_AND_PLAN.md`). Porting is mostly translation from "Claude-skill + script writing JSON files" into "FastAPI service + Postgres", not net-new design:

- **Sprint 0 — live prices + FX:** lift `build_snapshot.py` + `finance_mcp_runner.py` (yfinance, dual EUR/USD, halt-on-partial). FMP fallback already anticipated.
- **Sprint 0 — real WoW:** the seed's `portfolio-history.csv` + daily append is exactly the historical-snapshot table Sunday needs. Copy the schema (date, stocks, crypto, bonds, cash, trading, total, rate).
- **Sprint 0 — sells/DCA:** `dca-tracker`'s weighted-average + atomic-write logic is the cost-basis maintenance Sunday's CSV ingestor is missing.
- **Sprint 2 — "what changed this week":** `build_news.py` is the holdings-tagged news feed; the `weekly-review` skill is the section-by-section briefing spec.
- **Crypto-cycle differentiator:** `custom-skills/crypto-cycle-monitor/scripts/cycle_fetch.py` computes Pi-Cycle/Puell/Mayer from BTC-USD with **no paid API** — a buildable, informational, EU-crypto-investor-relevant signal that Sunday's briefing already promises but hasn't built.
- **PII firewall:** `tr-sanitizer` + `pii-tripwire` are stronger than Sunday's current "strip by not reading"; port them as the GDPR ingestion guard.
- **Scheduler:** `daily_update.py` is the cron Sunday needs in Sprint 3 (re-platformed off Windows Task Scheduler onto the server job runner).

---

## 4. Keep out of the SaaS (or neuter to information)

- ⛔ Profit-taking ladders with sell %s and ACTION blocks → user-set price alerts only.
- ⛔ `position-sizer`, `breakout-trade-planner`, `vcp-screener`, `signal-postmortem` → these are trading-advice tools; out of scope for a Publisher.
- ⛔ Any "should I buy/sell/trim X" answer → already blocked by the chat guardrail; keep it that way.
- ⛔ Marketing the cycle verdict as a "sell signal" or "AI that times the top" → AI-washing risk (PortfolioPilot $175k SEC precedent). Frame as "heuristic, not predictive," exactly as the seed skill already self-describes.

---

## 5. Updated porting order (folds into REVIEW_AND_PLAN sprints)

1. **Sprint 0 (lift, don't invent):** port `build_snapshot` (prices+FX), `portfolio-history` (WoW), `dca-tracker` (sells/cost basis), `tr-sanitizer` (PII). The seed already proved all four.
2. **Sprint 1–2:** real AI briefing (the seed's `weekly-review` is the spec) + `build_news` "what changed this week."
3. **High-value informational differentiator:** port `crypto-cycle-monitor` as an **information** section (verdict + history + "heuristic" caveat). *Do not* port the ladder/action layer.
4. **V2:** richer asset model (bonds, cash, leveraged accounts with notional-as-risk) from `manual-holdings.json`; per-ticker deep-dives from `analyze_ticker.py` (balanced/attributed → AI_FEATURES #4).
5. **Always:** keep the action/advice layer out; keep the chat guardrail on; market the cycle signal as information.

---

## Cross-references
- `Sunday_App_Business_Blueprint.md` — market/strategy/financials (US-centric; this doc + the seed are the EU-grounded reality).
- `REVIEW_AND_PLAN.md` — the build-order review; this doc supplies the "it's already solved in the seed" shortcut for Sprints 0–2.
- `docs/AI_FEATURES.md` — AI feature menu; the seed is the source for #1 (what-changed), the cycle signal, and #4 (per-ticker deep-dive).
- `docs/LEGAL.md` — the MiFID II/MiCA bright line that §2 above operationalises against the seed's action layer.
- Seed: `investment-ai/product-onepager.md` (product spec), `custom-skills/weekly-review/SKILL.md` (briefing spec), `custom-skills/crypto-cycle-monitor` + `profit-taking-ladder` (the informational-vs-action split).
