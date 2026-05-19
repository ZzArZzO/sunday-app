# Architecture

## System diagram (text)

```
┌────────────────┐        ┌────────────────┐        ┌─────────────────┐
│  Next.js web   │ ─────► │  FastAPI API   │ ─────► │  Postgres 16    │
│  (App Router)  │  HTTPS │  (deterministic│ SQLA   │  positions,     │
│  Tailwind UI   │        │   services +   │        │  lots, briefings│
│                │ ◄───── │   Claude orch.)│ ◄───── │                 │
└────────────────┘  JSON  └───────┬────────┘        └─────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │ Anthropic API  │
                          │ (EU endpoint)  │
                          │ Sonnet / Haiku │
                          │ / Opus on-dem. │
                          └────────────────┘
```

## Layers

### `web/` — Next.js App Router
- Server Components fetch from the FastAPI backend via `lib/api.ts`
- No client-side LLM calls — all model invocation lives in the API for cost control + guardrail enforcement
- Tailwind for layout, design tokens in `tailwind.config.ts`
- Auth (Phase 2) lives in middleware + `lib/session.ts`

### `api/` — FastAPI
- **Routes** (`app/routes/`) — thin HTTP handlers, validate via Pydantic, delegate
- **Services** (`app/services/`) — pure Python business logic, no I/O coupling, fully unit-testable
- **Models** (`app/models/`) — SQLAlchemy ORM, one file per aggregate
- **Schemas** (`app/schemas/`) — Pydantic DTOs, mirror to `web/lib/types.ts` until OpenAPI codegen lands

### Deterministic vs. LLM split (load-bearing)
The hybrid pipeline keeps numbers auditable and shrinks the hallucination surface:

| Layer | Implementation | Why |
|---|---|---|
| Numbers (concentration %, P&L, FX) | Pure Python | Exact, auditable for MiFID II, cheap |
| Market regime / cycle / rotation | Claude Sonnet 4.6 (Phase 2) | Inherently fuzzy/interpretive — LLM strength. One shared run per week, cached across users |
| Per-portfolio narrative wrapper | Claude Haiku 4.5 (Phase 2) | Cheap; consumes the cached shared layer as input |
| Ad-hoc deep research | Claude Opus 4.7 (Phase 2, paid tier) | Highest quality, credit-gated |
| Output guardrail | Regex + re-prompt (Haiku) | Enforces MiFID II "no personal recommendation" line |

### Model selection rules
- Shared market context is identical across all users on a given Sunday — caches perfectly with Anthropic prompt caching (~90% discount on cached input)
- Per-user input is small (portfolio state + cached shared layer reference) — Haiku is sufficient
- Opus is reserved for queries where the user explicitly asks for depth and pays for it

## Data flow — Sunday briefing pipeline (Phase 2 target)

1. **Sunday 17:00 UTC** — scheduler kicks off `compute_shared_market_layer()`
   - Sonnet 4.6 with prompt caching enabled
   - Produces structured JSON: regime tag, cycle position, sector rotation, crypto-cycle signal, macro-week-ahead
   - Stored in `market_snapshots` table, cached for the next 7 days
2. **For each active user** (parallel) — `compose_user_briefing(user_id)`
   - Deterministic Python computes numbers from latest portfolio state
   - Haiku 4.5 receives: (a) cached shared market layer (b) user's portfolio summary
   - Haiku writes only `body_markdown` for each `BriefingSection`
   - Output passes `narrative_guardrails` filter — re-prompt if forbidden phrases trip
3. **Delivery** — web view + email (Resend) + PDF (server-side rendering)

## Persistence

- Postgres 16, single instance for v1
- Row-level security per `user_id` once auth lands
- Field-level encryption for `Lot.unit_cost_eur` and `Position.quantity` (Phase 2)
- Daily backups, 30-day retention

## Observability (Phase 2)

- Sentry for errors (PII-scrubbed)
- Per-user LLM cost ledger (`llm_call_log` table) — feeds the cost guardrail
- Briefing generation traces — input tokens, cached tokens, output tokens, model, latency

## Why FastAPI + Next.js, not Next.js full-stack
- Reuses the Python skills ecosystem from the personal investment-ai project
- Lets the AI backend scale independently from the web frontend
- Server-side jobs (Sunday cron, email send, PDF render) live naturally in Python
- Type-safe contract via schemas mirrored to `lib/types.ts`
