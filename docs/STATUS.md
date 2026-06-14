# Sunday App — Status / Handoff

> Living "where we left off" doc. Last updated: **2026-06-14**.
> Point a new chat at this file to pick up exactly where we stopped.

## TL;DR

Working product, pre-billing. The full loop runs end to end:
**CSV import → live prices + FX → concentration & week-over-week → AI Sunday briefing (+ chat) → email + PDF delivery**, behind **magic-link auth** with per-user portfolios.

**Loose thread RESOLVED (2026-06-14):** Phase B (auth) live HTTP round-trip is now verified against the running Docker stack — request → verify (303, cookie set) → `me` authenticated → new user gets their own isolated empty portfolio (id=2) → logout clears session. Two latent bugs were fixed to get there: a stale API image (alembic couldn't find rev `0004`) and a Postgres sequence desync that made every new sign-up collide on `id=1`. The Sprint 3 delivery surface now also has a frontend (Download PDF, Email me, weekly opt-in). **Next: Sprint 4 — Stripe billing.**

---

## ✅ Done

### Sprints 0–2
- **Live market data** — yfinance prices for stocks + crypto, EU listings via ISIN, EUR/USD/GBP/CHF cross-rates. `services/prices/`.
- **Week-over-week** — real deltas from a portfolio snapshot history. `services/snapshots.py`, migration `0003`.
- **CSV ingest** — buy/sell/dividend/split, EU average-cost. `services/csv_ingestor.py`.
- **AI briefing + chat** — Anthropic SDK, structured outputs + prompt caching, deterministic numbers + LLM narrative, MiFID II / MiCA non-advice guardrails. `services/llm/`. Live and verified with the API key (chat correctly refused "should I sell SOL and buy BTC").
- **"What changed this week"** — real news / earnings per holding. `services/events/`.
- Testing mode: `ANTHROPIC_CHAT_MODEL=claude-haiku-4-5` in `.env`.

### Sprint 3 Phase A — delivery
- Email render (HTML + text) + Resend sender with dry-run fallback + opt-in weekly scheduler (APScheduler, lazy-imported). `services/delivery/`, `routes/delivery.py`.

### Sprint 3 Phase B — magic-link auth + multi-user (CODE COMPLETE)
- Backend: `models/auth.py` (`MagicToken`, `UserSession` — store SHA-256 hashes only), migration `0004` (applied), `services/auth/` (single-use 15-min tokens, 30-day sessions, get-or-create user + default portfolio), `routes/auth.py` (`/request`, `/verify`, `/me`, `/logout`), `deps.get_current_user` rewired to session cookie with gated demo fallback (`AUTH_REQUIRED`).
- Frontend: `web/lib/auth.ts`, `web/app/signin/page.tsx`, `web/components/AuthStatus.tsx` (in NavBar), and `web/lib/api.ts` `http()` forwards the session cookie through Next SSR + sends `credentials:include` in the browser.
- **Verified:** 114 backend tests pass (11 auth), frontend typechecks clean, routes live in OpenAPI, `/api/auth/me` returned `authenticated:false` correctly.

### Sprint 3 — PDF render (DONE)
- `services/delivery/pdf_render.py` (fpdf2, pure-Python, Unicode→latin-1 sanitized), `GET /api/briefing/pdf` download endpoint, PDF **attached to the weekly delivery email**. `fpdf2` added to `requirements.txt`. Sample at `C:\Users\Costa\Desktop\sunday-briefing-sample.pdf`.

### Sprint 3 — delivery UI + weekly opt-in (DONE, 2026-06-14)
- **Frontend delivery surface** on `/briefing`: `components/BriefingActions.tsx` (Download PDF via a credentialed blob fetch + Email-me-this-briefing, honest dry-run labelling) and `components/WeeklyOptInToggle.tsx`. Web client gained `sendMyBriefing`, `fetchBriefingPdf`, `fetch/updateDeliveryPreferences` in `lib/api.ts` + `DeliveryResult`/`DeliveryPreferences` in `lib/types.ts`.
- **Per-user weekly opt-in:** `User.weekly_opt_in` (default off), migration `0005_weekly_opt_in` (applied), `GET`/`PUT /api/delivery/preferences`, and `deliver_weekly` now sends **only to opted-in users** (no unsolicited briefings — also a launch-safety fix). 2 new tests.
- **Verified end-to-end** on the running stack: opt-in default false → PUT true persists → `/weekly` total 1 → opt-out → total 0; PDF endpoint returns valid `%PDF-`; email-me dry-run scoped to the signed-in user. Full backend suite **116 passing**, web `tsc` clean.

### Docs
- `README.md` rewritten to match current reality.

---

## ✅ The loose thread — Phase B LIVE verification (RESOLVED 2026-06-14)

Done. The full magic-link round-trip ran green against the Docker stack (see TL;DR). Root cause of the "Docker/Postgres kept crashing" symptom turned out to be a **stale API image** (entrypoint `alembic upgrade head` couldn't locate rev `0004` because the image predated the auth migration) — fixed by `docker compose up -d --build`. A separate **Postgres sequence desync** (seed inserts explicit ids without advancing sequences) made every new sign-up collide on `users_id_seq=1` → 500; fixed by resyncing all sequences to `max(id)+1`. **Patch the seed script to advance sequences so this can't recur on a fresh DB.**

<details><summary>Original repro steps (kept for reference)</summary>

1. Bring Postgres up: `docker compose up -d postgres` (from repo root). Confirm reachable.
2. Start one clean API on :8000: from `api/`, `uvicorn app.main:app --port 8000` (venv: `api/.venv`, uv-managed — use `uv pip ...`, there's no `pip` in it).
3. Run the end-to-end flow (proves cookie round-trip + per-user data isolation):
   ```python
   import httpx
   c = httpx.Client(base_url="http://localhost:8000", follow_redirects=True, timeout=15)
   r = c.post("/api/auth/request", json={"email": "newuser@test.com"}).json()
   c.get(r["dev_link"])                       # sets session cookie
   print(c.get("/api/auth/me").json())        # authenticated:true + email
   p = c.get("/api/portfolio").json()
   print(p["portfolio_id"], len(p["positions"]))  # NEW user's empty portfolio, not demo's 7
   c.post("/api/auth/logout")
   print(c.get("/api/auth/me").json())        # authenticated:false
   ```
4. Restart web on :3002 (or set `APP_BASE_URL` to match its port) and confirm `/signin` + AuthStatus render and the dashboard becomes per-user.

</details>

---

## 🔜 Not started

- **Sprint 4 — Stripe / payments** (no paid tier wired).
- Passkeys (magic-link covers auth for now).
- Tax-flag engine for all 5 countries (DE scaffolded; PT/FR/NL/ES to follow).
- Briefing persistence (history of past briefings — generated fresh on demand today).
- Production email (needs a verified Resend domain; dry-run until then).
- AI features #2–12 (`docs/business/AI_FEATURES.md`), seed ports (crypto-cycle, richer asset model, PII firewall), LLM cost ledger, eval harness, monitoring, ToS/Privacy/DPA.

---

## ⚠️ Notes for the next chat

- **Parallel edits:** a teammate also edits some files — don't revert their work in `chat.py`, `assistant.py`, `portfolio_context.py`, `schemas/chat.py`, `schemas/briefing.py`, `main.py` (benchmark route), `csv_ingestor.py`, `yfinance_provider.py`, `web/lib/api.ts`, `web/lib/types.ts`, `briefing_composer.py`, `ChatPanel.tsx`, `BriefingView.tsx`, `dashboard/page.tsx`.
- **Secrets:** never print `ANTHROPIC_API_KEY`; `.env` is gitignored; auth tokens store SHA-256 hashes only.
- **Env:** Windows + PowerShell; `api/.venv` is uv-managed (no `pip` — use `uv pip install`). Python 3.14. Web default port 3000, but auth `app_base_url` defaults to 3002.

## Recommended next step

**Sprint 4 — Stripe billing** (Free + Pro €9/mo per the blueprint). Phase B is verified and the Sprint 3 delivery surface is shipped. Before any *cloud* weekly send, also land the two launch-safety items: `(user_id, iso_week)` idempotency guard on `deliver_weekly` and pin the scheduler to a single always-on instance. And patch the seed script to advance Postgres sequences (see resolved loose thread).
