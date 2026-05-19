# Roadmap

> Source of truth for *what's next*, not *what could exist*. For the long-tail feature inventory see `~/app-investment-ai/product-features-catalog.md`.

## Phase 1 — MVP slice (this session, ✅ in progress)

- [x] Repo structure (monorepo: `web/`, `api/`, `docs/`)
- [x] FastAPI scaffold (routes, services, models, schemas)
- [x] Postgres schema + Alembic migration
- [x] CSV ingest pipeline
- [x] Concentration + P&L deterministic services
- [x] Briefing composer (template-based, no LLM yet)
- [x] Next.js scaffold (App Router + Tailwind)
- [x] Upload / Dashboard / Briefing pages
- [x] Sample portfolio + seed script
- [x] Minimal pytest coverage
- [ ] Verified end-to-end with `docker compose up` (run-and-test step for the human)

## Phase 2 — AI + auth + delivery (target: ~6 weeks)

### Auth
- Magic-link sign-in via Resend
- Session cookies (httpOnly, rotating refresh)
- Email verification on first login
- Replace `demo_user_id` plumbing in `app/deps.py`

### AI pipeline
- Anthropic client setup with EU endpoint + DPA
- `services/llm/shared_market.py` — Sonnet 4.6 with prompt caching
- `services/llm/briefing_narrative.py` — Haiku 4.5 with cached shared layer as input
- `services/llm/guardrails.py` — forbidden-phrase regex + re-prompt loop
- `llm_call_log` table for cost tracking
- Per-user monthly budget cap with graceful degradation

### Real prices
- yfinance integration in `services/prices.py`
- Hourly price refresh job
- FMP fallback when yfinance fails
- `last_price_at` populated on every refresh

### Delivery
- Sunday cron via APScheduler or Temporal
- Email rendering (MJML templates)
- PDF rendering (Playwright server-side)
- User timezone-aware scheduling

### Tax flag engine
- Country rule tables for DE first (1-year crypto holding period)
- PT, FR, NL, ES in fast-follow

## Phase 3 — Billing + polish (target: ~10 weeks)

- Stripe subscription (Free + Pro €7/mo)
- VAT via Stripe Tax
- Sunday briefing email digest opt-in
- Ad-hoc Claude queries (Opus, credit-gated)
- Multi-portfolio support
- Custom alert rules
- Goal tracking
- PDF / CSV exports
- Position notes (field-level encrypted)

## Phase 4 — Launch readiness

- Legal review: DE BaFin + PT CMVM consultations
- Privacy policy + ToS + Cookie policy + DE Impressum
- DSAR workflow live
- GDPR DPIA documented
- AI Act transparency disclosures on every LLM-touched output
- Sentry + uptime monitoring + cost dashboards
- Migrate from in-memory placeholder FX to live yfinance + persisted snapshot
- Load test the Sunday batch (target: 1,000 concurrent briefings under 10 minutes)
- Pre-launch waitlist on /r/EuropeFIRE + finanzfluss + indie-hacker channels
- Soft launch (DE-only) → Pan-EU once stable

## Phase 5 — Expansion (post-launch)

See `~/app-investment-ai/product-features-catalog.md` for the Tier 2 + Tier 3 list. Most likely next: Scalable Capital + DEGIRO CSV ingestion, daily mini-briefing for Pro, IT/AT/BE country expansion.

## Explicit non-goals

See the catalog's "Out of scope" table. Keep this list reviewed quarterly — drift here is how products lose their wedge.
