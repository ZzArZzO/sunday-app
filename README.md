# Sunday — Portfolio briefings for EU retail investors

> Working name. A Sunday-evening portfolio briefing for self-directed EU retail investors who hold stocks **and** crypto — privacy-first, no wallet-connect required.

## Status

Working product, pre-billing. The full loop runs end to end:

**CSV import → live prices + FX → concentration & week-over-week → AI Sunday briefing (+ chat) → email + PDF delivery**, behind **magic-link auth** with per-user portfolios.

What's live today:

- **Live market data** — yfinance prices for stocks + crypto, EU listings resolved via ISIN, EUR/USD/GBP/CHF cross-rates. No broker login.
- **Week-over-week** — real deltas from a portfolio snapshot history (not a placeholder).
- **AI briefing + chat** — Anthropic SDK with structured outputs and prompt caching. Deterministic numbers, LLM narrative; MiFID II / MiCA non-advice guardrails (forbidden-phrase filter) on every generated string. Disabled gracefully when no API key is set.
- **"What changed this week"** — real news / earnings pulled per holding.
- **Magic-link auth** — passwordless sign-in, SHA-256-hashed tokens, httpOnly session cookies; each user gets their own portfolio.
- **Delivery** — calm HTML email + a one-page PDF, plus an opt-in weekly Sunday scheduler.

Still to come: Stripe billing, passkeys, the tax-flag engine for all five countries. See `docs/ROADMAP.md`.

## Stack

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind
- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2
- **Database:** Postgres 16
- **Market data:** yfinance (Chrome-impersonated via curl_cffi to avoid WAF 429s)
- **AI:** Anthropic SDK — structured outputs + prompt caching, two-tier model split (Sonnet for chat, Haiku for the guardrail tier; configurable, Opus on-demand)
- **Email / PDF:** Resend (dry-run without a key) + fpdf2 (pure-Python, no headless browser)
- **Hosting (planned):** Vercel (web) + Railway/Fly.io (api) + Neon (db) — all EU regions

## Repository layout

```
sunday-app/
├── api/                      FastAPI backend
│   ├── app/
│   │   ├── main.py           Entrypoint
│   │   ├── config.py         Settings
│   │   ├── db.py             SQLAlchemy session
│   │   ├── deps.py           FastAPI dependencies
│   │   ├── models/           SQLAlchemy ORM (portfolio, snapshots, auth)
│   │   ├── schemas/          Pydantic DTOs
│   │   ├── routes/           HTTP routes
│   │   ├── services/         Business logic
│   │   │   ├── prices/       Live prices + FX (yfinance)
│   │   │   ├── events/       Per-holding news / earnings
│   │   │   ├── llm/          AI briefing + chat + guardrails
│   │   │   ├── delivery/     Email + PDF render + weekly scheduler
│   │   │   └── auth/         Magic-link tokens + sessions
│   │   └── seeds/            Sample portfolio data
│   ├── alembic/              DB migrations
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
├── web/                      Next.js frontend
│   ├── app/                  App Router pages
│   ├── components/           React components
│   ├── lib/                  API client + utilities
│   └── package.json
├── docs/                     Architecture & roadmap
├── docker-compose.yml        Postgres (+ Redis later)
├── .env.example
└── README.md
```

## Quick start

### Prerequisites

- Docker + Docker Compose
- Python 3.12+
- Node.js 20+
- pnpm or npm

### 1. Start Postgres

```bash
cp .env.example .env
docker compose up -d
```

Everything runs without external keys (AI is disabled, email goes to dry-run). To enable the AI briefing + chat, set `ANTHROPIC_API_KEY` in `.env`. To actually send email, set `RESEND_API_KEY` (+ a verified `EMAIL_FROM` domain); otherwise delivery renders and logs but doesn't send.

### 2. Run the API

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seeds.load_sample        # seeds a sample portfolio
uvicorn app.main:app --reload --port 8000
```

API docs at http://localhost:8000/docs

### 3. Run the web app

```bash
cd web
npm install
npm run dev
```

Open http://localhost:3000

> If you change the web port, set `APP_BASE_URL` in `.env` to match — magic-link sign-in redirects there after verifying.

### 4. Try the full loop

1. **Sign in** at `/signin` → enter any email. Without a Resend key it's dry-run, so the response includes a dev sign-in link — open it to set your session cookie and get your own (empty) portfolio.
2. **Import** at `/upload` → upload `api/app/seeds/sample-tr.csv` (or any TR-style CSV: buys, sells, dividends, splits).
3. **Dashboard** at `/dashboard` → positions priced live, allocation, concentration, and week-over-week once history builds.
4. **Briefing** at `/briefing` → the AI Sunday briefing (deterministic numbers + LLM narrative). Download it as a PDF from `GET /api/briefing/pdf`.
5. **Assistant** at `/assistant` → chat about your portfolio; stays informational (non-advice guardrails).

> Auth is opt-in for local dev: `AUTH_REQUIRED=false` (default) falls back to a demo portfolio so the app works before you sign in. Set `AUTH_REQUIRED=true` to require a session.

## What's intentionally NOT here yet

| Missing | Will be in | Why deferred |
|---|---|---|
| Stripe billing | Phase 4 | No paid tier wired yet |
| Passkeys | Phase 4 | Magic-link covers auth for now |
| Tax flag engine for all 5 countries | Later | DE scaffolded; PT/FR/NL/ES rules tables to follow |
| Briefing persistence (history of past briefings) | Later | Generated fresh on demand today |
| Production email | — | Needs a verified Resend domain; dry-run until then |

## Documentation

**Engineering**

- `docs/ARCHITECTURE.md` — system design, data flow, model selection
- `docs/ROADMAP.md` — phased build plan
- `docs/LEGAL.md` — MiFID II / MiCA / AI Act / GDPR notes; LLM output guardrails
- `docs/FRONTEND_IMPLEMENTATION_PLAN.md` — web build plan

**Business & research** (`docs/business/`)

- `Sunday_App_Business_Blueprint.md` — the 10-part deep-research blueprint
- `REVIEW_AND_PLAN.md` — app review vs. research + path to launch
- `AI_FEATURES.md` — AI feature catalogue
- `FRONTEND_UX_RESEARCH.md` · `DEPLOYMENT_AND_MARKETING.md` · `DEPLOYMENT_TOOLS_RESEARCH.md`
- `LINEAGE_AND_PORTING.md` — relationship to the `investment-ai` seed project
