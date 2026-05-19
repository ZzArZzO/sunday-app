# Sunday — Portfolio briefings for EU retail investors

> Working name. A Sunday-evening portfolio briefing for self-directed EU retail investors who hold stocks **and** crypto — privacy-first, no wallet-connect required.

## Status

MVP scaffold. Working slice: CSV upload → concentration analysis → briefing view with sample data. No auth, no real LLM calls, no payments yet. See `docs/ROADMAP.md` for what's next.

## Stack

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind
- **Backend:** FastAPI + SQLAlchemy + Alembic + Pydantic v2
- **Database:** Postgres 16
- **AI (planned):** Anthropic SDK with prompt caching, two-tier model split (Sonnet shared + Haiku per-user, Opus on-demand)
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
│   │   ├── models/           SQLAlchemy ORM
│   │   ├── schemas/          Pydantic DTOs
│   │   ├── routes/           HTTP routes
│   │   ├── services/         Business logic (deterministic)
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

### 4. Try the working slice

1. Go to `/upload` → upload `api/app/seeds/sample-tr.csv` (or any TR-style CSV)
2. Go to `/dashboard` → see positions + concentration analysis
3. Go to `/briefing` → see the structured Sunday-briefing view (currently template-based; AI narrative wrapper comes next)

## What's intentionally NOT here yet

| Missing | Will be in | Why deferred |
|---|---|---|
| Auth (magic-link + passkey) | Phase 2 | Slice doesn't need it; hardcoded `demo_user_id=1` placeholder |
| Real LLM calls | Phase 2 | Validate the data pipeline first; LLM cost discipline needs measurement |
| Stripe billing | Phase 3 | No paid features yet |
| Background scheduler | Phase 3 | Sunday cron needs auth + delivery infra |
| Email + PDF delivery | Phase 3 | Briefing view in-app is enough for the slice |
| Tax flag engine for all 5 countries | Phase 2 | DE-only scaffolded; PT/FR/NL/ES rules tables to follow |
| FX live fetch | Phase 2 | Hardcoded EUR/USD = 1.08 placeholder; `services/fx.py` has the interface |

## Documentation

- `docs/ARCHITECTURE.md` — system design, data flow, model selection
- `docs/ROADMAP.md` — phased build plan
- `docs/LEGAL.md` — MiFID II / MiCA / AI Act / GDPR notes; LLM output guardrails

## Sister docs (in the personal-tool repo)

- `~/app-investment-ai/product-onepager.md` — product hypothesis
- `~/app-investment-ai/product-features-catalog.md` — full feature inventory
- `~/app-investment-ai/investment-ai-mvp-plan.md` — personal-tool plan (the seed for this SaaS)
