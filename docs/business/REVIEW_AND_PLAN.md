# Sunday App — Code & Product Review + Development & Go-to-Market Plan

*A walkthrough of the actual application as built, measured against the market research, with a concrete plan to ship, launch, and start selling.*

**Reviewer hats:** founder · fintech analyst · product manager · growth · VC
**Date:** June 2026
**Scope:** Read-only review of `Desktop/sunday-app` (no code changed). Compared against `Sunday_App_Business_Blueprint.md` (the prior market research) and fresh EU-market research.
**Method:** Read README, `docs/{ARCHITECTURE,ROADMAP,LEGAL}.md`, all `api/app/services/*`, models, routes, the Next.js pages/components, env, and deps.

---

## 0. TL;DR — the one thing that matters

**You have built an excellent *deterministic portfolio-analytics engine* with a genuinely strong legal posture — but you have NOT yet built the thing the product is named after: the AI briefing.** The "Sunday briefing" today is **template strings**, the headline "week-over-week" number is **hardcoded to 0**, and P&L uses **cost basis as a stand-in for live price** (so every position shows ~0% gain). The AI chat assistant from the original concept has been **dropped entirely**.

The architecture, code quality, and compliance thinking are **top 10% for a pre-launch indie fintech**. The problem is not *how* it's built — it's *what's been prioritized*. You've built the auditable-numbers layer (the easy-to-defend, commodity part) and deferred the AI-narrative layer (the actual wedge, the only reason to exist next to Parqet and getquin).

**Verdict:** Strong foundation, wrong build order for a product whose entire differentiation is the AI weekly narrative. The plan in Part 6 reorders the work to make the promise real before you spend a euro on marketing.

---

## 1. What the app actually is (vs. the generic concept)

The repo is a **deliberate, well-reasoned pivot** away from the broad "Sunday App" concept in the business blueprint. Key divergences:

| Dimension | Blueprint concept (generic) | What's actually built | My take |
|---|---|---|---|
| **Geography** | US-first, global | **EU-first (DE → PT/FR/NL/ES/IT)** | ✅ Smart — less red-ocean than US; founder is in PT/EU |
| **Data in** | Broker sync (SnapTrade/Plaid) primary | **Manual CSV only, privacy-first, "no wallet-connect"** | ⚖️ Defensible but high-friction (see §4) |
| **Assets** | Stocks | **Stocks + crypto (declared, not chain-read)** | ✅ Differentiator vs equity-only tools |
| **AI briefing** | Hero feature | **Template strings; LLM not wired** | ❌ The wedge is unbuilt |
| **AI chat assistant** | Core differentiator | **Does not exist** | ❌ Dropped — see §3, §5 |
| **Tax/FIRE/dividend** | V2/V3 | **Already built (deterministic)** | ✅ Impressive depth; real EU-tax angle |
| **Pricing** | $12 / $29 | **Free + Pro €7/mo (roadmap)** | ⚖️ Possibly underpriced (see §7) |
| **Legal** | Publisher exclusion (US, Lowe v. SEC) | **MiFID II/MiCA non-advice bright line + guardrails** | ✅✅ Excellent, ahead of peers |

**Net:** the team traded the blueprint's *breadth + AI-first* for *EU-depth + compliance-first*. The compliance and analytics work is excellent. The risk is that **the parts that make it "Sunday" (AI narrative + the weekly ritual delivery) are exactly the parts not yet built**, while the parts that are built (tracking, tax, dividends, FIRE) are precisely where incumbents are strongest.

---

## 2. Comparison to the research — where it aligns and diverges

### ✅ Strong alignment (the team independently reached the report's conclusions)
- **Non-advice "publisher/information" posture.** `docs/LEGAL.md`'s MiFID II Art. 4(1)(4) bright line is the EU analog of the *Lowe v. SEC* publisher exclusion in the blueprint. The forbidden-phrase guardrail + "information only" framing is exactly right. **This is the single best thing in the repo.**
- **Two-tier model + prompt caching.** `docs/ARCHITECTURE.md`'s "Sonnet shared layer cached across users + Haiku per-user" is precisely the margin strategy the blueprint's Part 7 recommended (amortize one market summary across all reports). Good instinct, even un-built.
- **The "Sunday ritual" wedge.** The landing copy ("a quiet portfolio briefing, every Sunday … not another dashboard you forget to open") nails the blueprint's #1 differentiation: *scheduled, calm synthesis* vs. a firehose.
- **Privacy/trust as positioning.** "No wallet-connect, no broker permissions" matches the blueprint's "advice-neutral, conflict-free, trust" moat.
- **Deterministic numbers / LLM narrative split.** Matches the report's "keep numbers auditable, shrink hallucination surface."

### ⚠️ Divergences that change the strategy
1. **EU, not US → totally different competitive set.** The blueprint benchmarked Morningstar/Seeking Alpha/Fiscal.ai. The *real* competitors here are **Parqet (~350k users, free + €11.99/mo), getquin (~300k users, largest EU investor community), and Finanzfluss Copilot** (backed by Germany's biggest personal-finance YouTube channel). ([Parqet](https://etf.capital/parqet-app/), [getquin](https://www.matchmybroker.com/tools/getquin-review)) These are *consolidated, well-funded, community-rich incumbents in your exact lane.*
2. **The AI chat was dropped.** The blueprint rated the portfolio-grounded co-pilot as a **co-hero** and a top differentiator. Removing it is legally simpler — but it also removes the one feature Parqet/getquin/Finanzfluss don't have. **You can't out-track the trackers; you can only out-*reason* them. Reasoning (AI briefing + chat) is the differentiation, and it's the unbuilt part.**
3. **Manual-only vs sync.** The blueprint suggested manual-first then add sync. The EU reality *validates manual-first* (Trade Republic/Scalable have **no official API**; even big trackers rely on CSV/PDF import/scraping). But "sync issues are users' biggest frustration" (Finary 2026) cuts both ways — manual is reliable but adds onboarding friction you must design around. ([trefolio EU trackers](https://trefolio.com/blog/best-portfolio-trackers-europe-2026), [neobroker importer](https://github.com/roboes/neobroker-portfolio-importer))
4. **Differentiation is already partly occupied.** Tools like **trefolio** ("EU Tax Reports & AI Insights") and **Capitally/Tukhe** (privacy-first, manual, no aggregator) are *already* selling the exact "EU tax + privacy + AI" position. Sunday is not first to this idea — so execution on the *weekly AI narrative ritual* (not tax/privacy alone) has to be the wedge.

---

## 3. Deep dive: features users want that are missing or fake

Ranked by how much they undermine the core promise.

### 🔴 Credibility-breaking (fix before showing anyone)
1. **Week-over-week is hardcoded to 0.** `briefing_composer.py:168` sets `wow_delta_eur = 0`, `wow_pct = 0`. The hero section is literally titled "The one number that matters" and it's **always zero**. There are no historical net-worth snapshots, so WoW *can't* be computed yet. This is the most-promised, least-delivered number in the app.
2. **P&L is fake.** `pnl.py:16` falls back to `avg_cost_eur` when `last_price_eur` is null — and `last_price_eur` is *never populated* (no price fetcher). So market value = cost basis → **every portfolio shows 0% gain/loss.** FX is also a hardcoded `1.08` placeholder (`fx.py:14`).
3. **The "AI briefing" has no AI.** `_build_regime_section`, `_build_what_changed_placeholder` are explicit placeholders. "What changed this week" — the *emotional core* of a Sunday briefing — is a stub. The product promises narrative; it delivers `f"Net worth: {x}. Week over week: {y}."`

### 🟠 Core-feature gaps (needed for a sellable v1)
4. **No delivery mechanism.** No auth, no email (Resend stubbed), no PDF, no scheduler. The product is "a briefing **every Sunday**" but there is **no way to send a Sunday email**. The promise is undeliverable today.
5. **No AI chat assistant.** Dropped from concept. It's the highest-differentiation feature vs EU incumbents (§5).
6. **CSV ingests only "buy" rows.** `csv_ingestor.py:30` `ACCEPTED_TYPES = {"buy","kauf","purchase"}`. **Sells, dividends, splits, transfers are silently skipped.** Over time, cost basis and quantities drift wrong — fatal for a tax/FIRE tool. Trade Republic's CSV export includes sells; you're dropping them.
7. **No benchmark comparison.** "Am I beating MSCI World / S&P 500?" is the single most-requested feature in EU tracker reviews. Absent.
8. **Dividend & tax data are hardcoded.** `dividend_projector.py` uses static per-ticker yields; real ex-div dates/amounts and DE Teilfreistellung-per-holding aren't tracked. Fine for a preview, wrong for a paid tax product.

### 🟡 Friction & polish
9. **Onboarding is CSV-or-nothing.** No PDF import (EU brokers export PDF), no "paste from Trade Republic" wizard, no sample-to-yours flow. In a market where Parqet has buttery import UX, this is a conversion risk.
10. **Positions forced to EUR.** `csv_ingestor.py:254` hardcodes `currency="EUR"`; multi-currency holdings (USD stocks) aren't modeled correctly beyond a single EUR/USD rate.
11. **No mobile/PWA notification story.** Push is a top retention lever in this category; not addressed.
12. **No "regime/cycle" data source.** The regime section needs a real market-data + macro feed; none is wired.

---

## 4. What's genuinely good (keep and lean into)

| Strength | Evidence | Why it matters |
|---|---|---|
| **Compliance posture** | `docs/LEGAL.md` bright-line table + `guardrails` design + user-set (not platform-set) thresholds + per-screen disclaimers | This is where most fintech founders get fined or shut down. You're ahead. It's also *marketable* trust. |
| **Clean architecture** | Deterministic services, pure functions, DTO/ORM separation, `compose_briefing` orchestration | Numbers are auditable (MiFID II), testable, cheap; LLM only writes prose. Exactly right. |
| **Code quality** | Type hints, frozen dataclasses, immutability, small cohesive files, real pytest coverage (concentration/csv/dividend/fire/rebalance/tax) | Maintainable; you can move fast without breaking the math. |
| **EU-specific tax engine** | `tax_summary.py` — DE Abgeltungsteuer + Soli + Teilfreistellung, FR PFU, ES brackets, NL Box 3, IT, PT | A *real* differentiator US tools can't easily copy; aligns with the trefolio/Capitally lane but with the Sunday ritual on top. |
| **FIRE calculator** | `fire_calculator.py` — full/coast/lean/fat, years-to-FIRE solver, timeline | Perfect fit for the r/EuropeFIRE beachhead audience. |
| **EU-aware CSV ingest** | Trade Republic + German headers, EU decimal parsing (`1.234,56`), ISIN→asset-class inference, PII stripping | Pragmatic for a market with no broker APIs; the right call. |
| **Brand & tone** | "A quiet portfolio briefing, every Sunday" + calm Geist/dark-mode UI | The name *is* an asset (own "Sunday" like Morning Brew owns the AM). Distinctive in a noisy category. |

---

## 5. The central strategic problem (read this twice)

**You are entering a consolidated EU market where three incumbents (Parqet ~350k, getquin ~300k + community, Finanzfluss + YouTube distribution) already own tracking, dividends, social, and import UX — and you are currently competing on *their* turf (tracking/tax/dividend/FIRE) while leaving your *only* structural advantage (AI weekly narrative + chat) unbuilt.**

- You **cannot win on tracking breadth** — getquin tracks 800k+ assets, Parqet is years ahead on import.
- You **cannot win on community** — getquin *is* the community.
- You **cannot win on distribution** — Finanzfluss has the largest German finance audience; you have a waitlist.
- You **can** win on: **a genuinely good AI-written, personalized, calm Sunday narrative that explains *what happened to my money and why*, with an AI chat to go deeper — wrapped in a privacy-first, EU-tax-aware, advice-neutral package.** None of the big three does the AI narrative well.

So the AI layer isn't "Phase 2 polish." **It is the product.** Everything else is table stakes you're over-investing in. The plan below fixes the build order accordingly.

> ⚠️ **AI-washing caution (from the research):** the SEC fined PortfolioPilot $175k for overstating AI; the EU AI Act (Art. 50, from Aug 2 2026) requires you to disclose AI use. **Do not market "AI briefing" until the AI is real.** Right now the marketing would describe a feature that doesn't exist. Build it, then say it.

---

## 6. Development plan (reordered for the wedge)

> Principle: **make the promise true before you make it loud.** Fix the lies → build the wedge → make it deliverable → charge for it. Each sprint ends with something demoable.

### Sprint 0 — "Stop lying" (1–2 weeks) — *make the numbers real*
- **Live prices:** wire `services/prices.py` (yfinance primary, FMP fallback per roadmap); populate `last_price_eur`; hourly refresh. *Kills the fake-P&L problem.*
- **Live FX:** replace the `1.08` placeholder with a fetched + cached EUR/USD (and per-currency support).
- **Historical net-worth snapshots:** daily/weekly `portfolio_snapshot` rows so **week-over-week actually computes**. *Kills the hardcoded-0 problem — the single most important fix.*
- **Handle sells/dividends/splits in CSV ingest:** expand `ACCEPTED_TYPES`; net quantities and cost basis correctly. *Without this the tax/FIRE math is wrong.*
- *Exit criteria:* a real portfolio shows true value, true WoW, true P&L.

### Sprint 1 — "Build the wedge" (2–3 weeks) — *the actual AI briefing*
- `services/llm/shared_market.py` — Sonnet 4.6, prompt caching, weekly batch → structured regime/cycle/rotation/crypto-cycle/macro-week-ahead JSON in a `market_snapshots` table.
- `services/llm/briefing_narrative.py` — Haiku 4.5 consumes (cached shared layer + user portfolio facts) → writes only `body_markdown` per section.
- `services/llm/guardrails.py` — implement the forbidden-phrase regex + re-prompt loop already specced in `docs/LEGAL.md`.
- `llm_call_log` + per-user monthly budget cap (cost discipline).
- *Exit criteria:* a generated briefing reads like a human wrote it, passes guardrails, costs < €0.10/user/week.

### Sprint 2 — "What changed this week" (1–2 weeks) — *the heart of the briefing*
- News/earnings/macro feed for **held tickers only** (Marketaux/Tiingo/FMP); summarize cheaply (Haiku/Flash) into the shared layer.
- Economic calendar (CPI/ECB/jobs/earnings dates) filtered to the user's holdings.
- *Exit criteria:* the "This week" section names 3–5 real, relevant events per portfolio.

### Sprint 3 — "Deliver it" (1–2 weeks) — *make Sunday real*
- **Auth:** magic-link via Resend; sessions; replace `demo_user_id` in `deps.py`.
- **Sunday scheduler** (APScheduler/Temporal), timezone-aware.
- **Email** (MJML) + **PDF** (server render). The briefing lands in the inbox Sunday evening.
- *Exit criteria:* you receive your own portfolio's briefing by email on a Sunday.

### Sprint 4 — "Charge for it" (1–2 weeks)
- **Stripe** subscription + **Stripe Tax** (EU VAT/MOSS), free vs Pro gating, AI message/credit caps.
- Annual plan with ~2 months free.
- *Exit criteria:* a stranger can pay you.

### Sprint 5 — "The differentiator returns" (2–3 weeks)
- **Re-add the AI chat assistant** (portfolio-grounded, same guardrails). This is the feature the big three lack — it's worth the legal care.
- **Benchmark comparison** (vs MSCI World/S&P) — the most-requested missing feature.
- PDF import + more broker formats (Scalable, DEGIRO); onboarding wizard.

### Parallel, always-on
- Privacy/ToS/Impressum + Anthropic EU DPA + DPIA (per `docs/LEGAL.md` checklist) **before** public launch.
- Sentry, uptime, cost dashboards.
- Load-test the Sunday batch (target: 1,000 briefings < 10 min).

**Total to a sellable, true-to-promise v1: ~8–13 weeks solo.** Note this is *re-sequencing*, not new scope — most of it is already in your Phase 2/3 roadmap; I'm just moving "real numbers + real AI" ahead of everything else and pulling the chat back in.

---

## 7. Pricing & packaging recommendation

Your roadmap says **Free + Pro €7/mo**. I'd adjust:

| Tier | Price | Limits | Rationale |
|---|---|---|---|
| **Free** | €0 | 1 portfolio, ≤15 holdings, monthly briefing + 1 weekly preview, 5 AI chats/mo, basic tax/FIRE | Funnel + the free newsletter feeds it |
| **Pro** | **€9/mo or €79/yr** | Unlimited holdings, full weekly briefing + email/PDF, 150 AI chats/mo, full tax/FIRE/dividend, benchmark, alerts | €9 anchors below Parqet's €11.99 but isn't bargain-bin; annual = €6.6/mo crushes churn |
| **Pro+ / AI** (later) | €19/mo | Higher AI limits, Opus deep-dives, multi-portfolio, daily mini-briefing | Captures power users; protects AI margin |

**Why €9 not €7:** €7 signals "cheap tracker" in a market anchored at Parqet €11.99 / getquin. You're selling *intelligence*, not tracking — don't underprice the wedge. Keep the AI-cost caps tight (the message limits are both monetization and COGS control). The blueprint's benchmarks hold: target 80% gross margin via prompt caching + caps; expect 3–5% freemium conversion (8%+ if the briefing is genuinely loved).

---

## 8. Go-to-market & selling plan

**Beachhead (be narrow):** **German + Portuguese self-directed FIRE/dividend investors who hold stocks + crypto on Trade Republic/Scalable.** DE first (largest neobroker base + your tax engine's deepest country), PT second (founder proximity), then FR/NL/ES/IT as the tax tables fill in. The roadmap already names this — commit to it.

### Pre-launch (now → first AI briefing works)
- **Waitlist + free weekly newsletter** — a *de-personalized* "EU Markets: Your Sunday Read." This is your #1 growth engine and doubles as proof the AI narrative is good. Start it **this week**, before the app is done.
- **Build-in-public** on X/LinkedIn (DE + EN): show the briefing evolving, the privacy/no-login stance, the EU-tax angle. FinTwit + finanzfluss-adjacent audiences.
- **Seed value, don't spam:** r/EuropeFIRE, r/Finanzen, r/mauerstrassenwetten (carefully), r/dividends, getquin-refugee threads. Answer real questions; invite to beta.

### First 100 customers (design partners)
- Hand-onboard from the waitlist; generate a stunning real briefing for each. Extract testimonials. Fix the aha-moment (the first briefing must land in <2 min from CSV upload).
- Product Hunt + a "Show HN" once the AI briefing + email delivery work.

### First 1,000
- **Referral** ("give a month, get a month" + newsletter milestone rewards — the Morning Brew engine, ~€0.25 effective CAC).
- **Comparison-page SEO** (DE + EN): "Sunday vs Parqet," "Sunday vs getquin," "best EU portfolio tracker with AI briefing," "Trade Republic Steuer-Übersicht." YMYL-careful, cited, author-attributed.
- **One distribution partnership:** a mid-tier German/PT finance YouTuber or newsletter (NOT Finanzfluss — they're a competitor now; find the tier below). Disclosed, compliant.
- **Pan-EU expansion** as tax tables land.

### KPIs (north star = weekly briefing open rate)
- Weekly briefing **open rate > 50%** sustained = ritual is sticking (your PMF proxy).
- Free→Pro **≥ 4%**; monthly churn **< 5%** (push annual to suppress it).
- CAC **< €40** (organic-led); LTV:CAC **≥ 3–5x**.
- Aha-rate: % of signups who upload a portfolio AND view a full briefing within 24h.

### Positioning line to test
> *"Every Sunday, one calm read on your money — stocks and crypto, written by AI that actually knows what you own, EU-tax-aware, and never tells you what to do. No broker login. No noise."*

That sentence does the work: ritual + AI + EU-tax + privacy + advice-neutral, all at once.

---

## 9. Honest risk assessment (VC lens)

| Risk | Severity | Mitigation |
|---|---|---|
| **Wedge unbuilt while marketing implies it exists** | 🔴 High | Sprint 1–2 *before* any paid push; don't say "AI" until it's real (AI-washing/AI Act) |
| **Consolidated EU incumbents (Parqet/getquin/Finanzfluss)** | 🔴 High | Don't fight on tracking; win on AI narrative + ritual + privacy + EU-tax; narrow beachhead |
| **Solo-founder distribution in a YouTuber-dominated market** | 🟠 Med-High | Newsletter + referral + SEO + sub-Finanzfluss partnerships; be patient, compound |
| **Manual-CSV onboarding friction** | 🟠 Med | Killer import wizard, PDF import, "paste TR export" flow; frame privacy as the *reason* |
| **Numbers currently wrong (WoW=0, fake P&L)** | 🟠 Med | Sprint 0 fixes; never demo until fixed |
| **Low EU willingness-to-pay + churn** | 🟠 Med | Annual plans, the ritual, the newsletter as a second monetizable asset |
| **Regulatory drift into "advice"** | 🟡 Low (well-managed) | Keep the guardrails; counsel review; the posture is already strong |

**Probability read (unchanged from blueprint, sharpened):**
- Ramen-profitable EU indie SaaS (€100–400k ARR): **~45–55%** *if* the AI briefing is genuinely good and you nail the DE/PT beachhead.
- €1M+ ARR: **~12–18%** — requires beating the incumbents on the one axis you can (intelligence) and winning distribution.
- The build-order mistake is the biggest *self-inflicted* risk. Fix it and the odds improve materially.

---

## 10. The 10 things to do next (in order)

1. **Fix week-over-week** (historical snapshots) — your headline number can't be 0.
2. **Wire live prices + FX** — stop showing fake P&L.
3. **Handle sells/dividends/splits in CSV** — your tax/FIRE math depends on it.
4. **Build the real AI briefing** (shared Sonnet layer + Haiku narrative + guardrails) — *this is the product.*
5. **Build "what changed this week"** (news/earnings/macro for held tickers).
6. **Ship auth + Sunday email/PDF delivery** — make the promise deliverable.
7. **Start the free weekly newsletter + waitlist now** — growth compounds slowly; begin today.
8. **Add Stripe + EU VAT, price Pro at €9/yr-discounted** — let people pay.
9. **Re-add the AI chat assistant + benchmark comparison** — your two biggest differentiators vs the big three.
10. **Legal pre-launch checklist** (DPA/DPIA/ToS/Impressum) + **don't market "AI" until step 4 ships.**

---

## Appendix — Sources (this review)
**EU competitors/market:** [Parqet](https://etf.capital/parqet-app/) · [getquin review](https://www.matchmybroker.com/tools/getquin-review) · [EU trackers 2026 (trefolio)](https://trefolio.com/blog/best-portfolio-trackers-europe-2026) · [getquin alternatives / no-login](https://www.donkycapital.com/en/compare/best-getquin-alternatives-portfolio-tracker-2026) · [neobroker CSV importer](https://github.com/roboes/neobroker-portfolio-importer)
**Cross-refs:** `Sunday_App_Business_Blueprint.md` (prior research: competitors, pricing, SaaS/churn/CAC benchmarks, AI API pricing, Lowe v. SEC publisher exclusion, PortfolioPilot/SEC AI-washing, EU AI Act).
**Code reviewed (no changes made):** `api/app/services/{briefing_composer,concentration,csv_ingestor,fx,pnl,fire_calculator,dividend_projector,rebalancer,tax_summary}.py`, `api/app/models/user.py`, `web/app/page.tsx`, `web/components/BriefingView.tsx`, `docs/{ARCHITECTURE,ROADMAP,LEGAL}.md`.

*End of review.*
