# Sunday App — Status / Handoff

> Living "where we left off" doc. Last updated: **2026-06-29**.
> Point a new chat at this file to pick up exactly where we stopped.
> The git log is the source of truth; this doc summarises it.

## TL;DR

Working product with billing, mobile, and cost-control rails in place. The core loop runs end to end:
**CSV import → live prices + FX → concentration & week-over-week → AI Sunday briefing (+ chat) → email + PDF delivery**, behind **magic-link auth** with per-user portfolios.

Since the last big checkpoint we landed: **Stripe billing** (rails + env wired), an **LLM cost ledger** + **per-user monthly AI budget cap**, and **mobile Builds 1–5** (responsive shell → Capacitor iOS/Android → native push → biometric lock).

**Where we left off (in flight):** a **multi-source import / connector abstraction** — generalising CSV-only import into pluggable sources (CSV + crypto wallet address + read-only exchange API). It is **code-complete, tested, and on its own branch**, but the live connectors are dormant until a vendor + keys are chosen.

**Test health:** backend **180 passing**; web `tsc` clean.

---

## ✅ Done

### Core loop (Sprints 0–3)
- **Live market data** — yfinance prices for stocks + crypto, EU listings via ISIN, EUR/USD/GBP/CHF cross-rates. `services/prices/`.
- **Week-over-week** — real deltas from a portfolio snapshot history. `services/snapshots.py`, migration `0003`.
- **CSV ingest** — buy/sell/dividend/split, EU average-cost. `services/csv_ingestor.py`.
- **AI briefing + chat** — Anthropic SDK, structured outputs + prompt caching, deterministic numbers + LLM narrative, MiFID II / MiCA non-advice guardrails. `services/llm/`.
- **"What changed this week"** — real news / earnings per holding. `services/events/`.
- **Delivery** — email render (HTML + text) + Resend sender with dry-run fallback, PDF render (fpdf2), opt-in weekly scheduler (APScheduler). `services/delivery/`, `routes/delivery.py`. Per-user `weekly_opt_in` (migration `0005`); weekly send only goes to opted-in users.
- **Magic-link auth + multi-user** — `models/auth.py` (SHA-256 hashes only), migration `0004`, `services/auth/`, `routes/auth.py`. Live round-trip verified against the Docker stack (request → verify → per-user isolated portfolio → logout). Cookie **and** Bearer-token paths (the Bearer path is what mobile uses).

### Sprint 4 — Stripe billing (CODE COMPLETE; live round-trip pending keys)
- **Billing rails** (test-mode-safe; 503 without keys): `services/billing/` (`client`, `subscription`, `checkout`, `portal`, `webhooks`), `routes/billing.py` (`GET /subscription`, `POST /checkout`, `POST /portal`, signature-verified `POST /webhook`). Stripe state on `User` (migration `0006`). Config `STRIPE_API_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRICE_PRO`; env now passed to the api container (commit `dbef16d`). `current_period_end` read from subscription items (`6842891`).
- **Pro gates:** `subscription.is_pro(user)` / `subscription.holdings_limit(user)`. Benchmark, weekly-email toggle, and holdings cap are gated. `/billing` page + nav entry exist.
- **To go live (needs a Stripe account):** restricted key → `STRIPE_API_KEY`; create €9/mo Price → `STRIPE_PRICE_PRO`; `stripe listen --forward-to localhost:8000/api/billing/webhook` → `STRIPE_WEBHOOK_SECRET`; test card `4242…`. The live Checkout→webhook round-trip has **not** been executed yet.

### Cost control (margin protection)
- **LLM cost ledger** (`bc53b47`) — `services/llm/cost_ledger.py`, `models/llm_call_log.py`, migration `0007`. Measures real per-call token usage + COGS on every AI call.
- **Monthly per-user AI budget cap** (`3f785ef`) — `services/billing/budget.py`, config `ai_monthly_budget_free_usd` (0.25) / `ai_monthly_budget_pro_usd` (5.0). Once a user crosses the cap, AI features degrade gracefully until the 1st. Enforced from the ledger.

### Mobile — Builds 1–5
- **Build 1** — mobile shell: bottom tab bar + responsive holdings + Plan hub with bottom-sheet holding detail (`3f948a9`, `b9c0bc8`, `7ae86b9`).
- **Build 2** — Bearer-token frontend path + client-side data fetch for dashboard/briefing/plan/fire; env-gated dual output (standalone web / static export for Capacitor) (`e6ba70b`, `c5c34b1`, `eb45327`, `23aba21`, `de5a23e`).
- **Build 3** — Capacitor iOS + Android app projects (`3893008`); `.github/workflows/mobile.yml`.
- **Build 4** — native push for the weekly briefing via FCM HTTP v1 (`bbfca86`); migration `0008_push_tokens`, `routes/push.py`, config `fcm_*`. See `docs/MOBILE_PUSH_SETUP.md`.
- **Build 5** — biometric app-lock + Keychain-backed session (`9073b41`).

---

## 🚧 In flight — Multi-source import (connector abstraction)

**Status: code-complete, fully tested, NOT yet on master.** Generalises CSV-only import into a pluggable connector model so users can mix sources per portfolio (CSV + wallet + exchange at once).

- **Backend:** `services/connectors/` — `base.py` (`CanonicalTransaction`, `ImportSource` protocol, shared `apply_transactions` / `replace_connection_lots` replay core), `crypto_address.py`, `exchange.py`, `secrets.py`, `snapshot.py`. `csv_ingestor` delegates to the shared core. `Connection` model + migrations `0009_connections` / `0010_connection_secret`; `Lot.connection_id` records provenance so a source can be re-synced or disconnected cleanly. `routes/connections.py` wired into `main.py`: list / connect-address / connect-exchange / `{id}/sync` / disconnect.
- **Frontend:** `/sources` page + `SourcesManager`, `BrokerPicker`, `ImportWizard` components, `lib/brokers.ts`, broker-picker upload wizard. Nav entry added.
- **Tests:** `test_connectors*.py` (14 tests) green; full suite 180 green; web `tsc` clean.
- **Strategy (why):** EU has no consumer brokerage APIs, so stocks stay CSV-first (broker-picker wizard is the fix). Crypto is where automation is feasible: address paste (read-only public ledger) + exchange read-only API keys. Both live connectors are Pro-gated (402) and read-only (no custody), and stay **dormant (503)** until configured — same graceful-degradation pattern as Stripe/LLM/email.
- **Snapshot connectors** report current balances only (no cost-basis history): each asset is one lot at current price, and re-sync replaces holdings. Cost-basis-from-source is a later refinement.

**To make the live connectors real:**
- **Crypto address:** pick an indexer vendor (Zerion / Covalent / Alchemy), adapt the request + response mapping in `crypto_address.py` to its schema, set `CRYPTO_INDEXER_API_KEY` + `CRYPTO_INDEXER_BASE_URL`.
- **Exchange:** generate a Fernet key for `CONNECTION_SECRET_KEY` (encrypts stored exchange API secrets at rest). `cryptography` + `ccxt` are already in `requirements.txt`.

---

## 🔜 Not started / open

- **Stripe live round-trip** — live keys + real Pro Price + a real Checkout→webhook test (rails are done).
- **Launch-safety (partly done on a branch):** the `(user_id, iso_week)` idempotency guard on `deliver_weekly` + the seed-script sequence resync are **committed on branch `feat/weekly-idempotency-seed-fix`** (commit `72b896a`) but not yet merged. Still open: pin the scheduler to a single always-on instance before any cloud weekly send.
- Passkeys (magic-link covers auth for now).
- Tax-flag engine for all 5 countries (DE scaffolded; PT/FR/NL/ES to follow). Note: founder is NL-based — see memory `founder-context`; legal/tax docs still say PT in places.
- Briefing persistence (history of past briefings — generated fresh on demand today).
- Production email (needs a verified Resend domain; dry-run until then).
- AI features #2–12 (`docs/business/AI_FEATURES.md`), eval harness, monitoring, ToS/Privacy/DPA.

---

## 🌿 Branch state (read this before reconciling)

- **`master`** — base; behind the feature work below.
- **`feat/frontend-ux-phase-a-track-2`** (current) — carries the committed billing / cost-ledger / budget-cap / mobile-Builds-1–5 history, and the multi-source import feature (being committed onto its own branch).
- **`feat/weekly-idempotency-seed-fix`** — same base + one commit (`72b896a`) with the launch-safety idempotency + seed-resync fix. Does **not** contain the connector work.
- These have diverged from `master` and from each other; reconcile deliberately (likely: land features onto `master`, then fold in the idempotency fix).

---

## ⚠️ Notes for the next chat

- **Secrets:** never print `ANTHROPIC_API_KEY` / Stripe keys; `.env` is gitignored; auth tokens store SHA-256 hashes only; exchange API secrets are Fernet-encrypted at rest.
- **Env:** Windows + PowerShell; `api/.venv` is uv-managed. Web default port 3000; auth `app_base_url` defaults to 3002.
- **Local deploy gotchas:** stale API image → alembic "can't locate revision" crash loop (fix: `docker compose up -d --build`); Postgres sequence desync from seed data blocks new sign-ups (fixed by the seed-resync on `feat/weekly-idempotency-seed-fix`). See memory `local-deploy-gotchas`.

## Recommended next step

Reconcile branches (features → `master`, then the idempotency fix), then either (a) run the **live Stripe round-trip**, or (b) pick a **crypto indexer vendor** to switch the multi-source connectors from dormant to live. Before any *cloud* weekly send, land the scheduler single-instance pin.
