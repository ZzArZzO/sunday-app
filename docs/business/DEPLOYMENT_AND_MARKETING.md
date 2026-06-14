# Sunday App — Deployment & Marketing Deep Dive

*How to ship this to production (EU-safe, low-ops, cheap) and how to get the first 10,000 users without a marketing budget.*

**Date:** June 2026
**Method:** Read the actual codebase (`api/`, `web/`, `docker-compose.yml`, Dockerfiles, `config.py`, services) and the four `docs/business/*` strategy docs + `docs/{ARCHITECTURE,ROADMAP,LEGAL}.md`. Deployment guidance is grounded in what is *actually wired today*, not the stale README/ROADMAP.
**Status:** Operational playbook. Market figures and benchmarks are inherited from `Sunday_App_Business_Blueprint.md` / `REVIEW_AND_PLAN.md` (cited there); this doc does not re-cite — it operationalizes.

---

## 0. Reality check — what is actually built (this changes everything)

The README says *"No auth, no real LLM calls, no payments yet."* **That is out of date.** Reading `api/app/main.py` and the service tree, the app is dramatically further along than every doc claims:

| Capability | Docs say | Code actually has | Evidence |
|---|---|---|---|
| Auth | Phase 2, not built | ✅ Magic-link tokens + sessions, hashed-at-rest, single-use, TTLs | `services/auth/tokens.py`, `routes/auth.py`, `0004_auth.py` migration |
| AI chat assistant | "Dropped entirely" | ✅ Wired | `routes/chat.py` in `main.py` |
| AI briefing narrative | "Template strings, no AI" | ✅ `briefing_ai.enhance()` with deterministic fallback | `services/briefing_build.py`, `services/llm/briefing_ai.py` |
| Live prices | Placeholder | ✅ yfinance + FMP fallback | `routes/prices.py`, requirements |
| Week-over-week | "Hardcoded to 0" | ✅ Snapshots route | `routes/snapshots.py` |
| "What changed this week" | Stub | ✅ Events feed + summary | `services/events/`, `EventsCard.tsx` |
| Benchmark vs index | Missing | ✅ Wired | `routes/benchmark.py` |
| Email + Sunday cron | Phase 3 | ✅ Render + send (Resend) + APScheduler weekly cron | `services/delivery/*`, `routes/delivery.py` |
| Tax / FIRE / dividend / rebalance | Mixed | ✅ All wired | respective routes |
| **Stripe billing** | Phase 3 | ❌ **Not built** (env vars stubbed only) | no `routes/billing.py`, no webhook handler |
| **Production deploy config** | — | ❌ **None** (no vercel.json / fly.toml / railway / render / CI) | repo root |

**Implication:** The build-order problem flagged in `REVIEW_AND_PLAN.md` has been largely *fixed*. The two things standing between you and a paid launch are now (1) **monetization** (Stripe) and (2) **production deployment + the legal gates that must precede a public fintech launch**. This doc covers both, plus the marketing engine to fill the funnel.

> ⚠️ **First action, unrelated to deploy/marketing:** the README and ROADMAP describe a product that no longer exists. Update them, or a contributor (or you, in 3 months) will make decisions on false premises. 30-minute fix.

---

# PART A — DEPLOYMENT

## A.1 Design constraints that dictate the architecture

Four properties of *this specific app* drive every hosting decision:

1. **The product is an email.** The Sunday briefing is delivered to the inbox. **Deliverability is not a feature, it is the product.** This makes the email provider + domain auth (SPF/DKIM/DMARC) a P0, not a nicety.
2. **There is a stateful weekly cron.** `services/delivery/scheduler.py` uses an **in-process** `BackgroundScheduler` (APScheduler) gated by `ENABLE_SCHEDULER`. This means the API **cannot be deployed to a scale-to-zero / multi-replica serverless platform without changes** — if it sleeps, Sunday never fires; if it runs 3 replicas, every user gets 3 emails. → The API needs **one always-on instance**, or the cron must be externalized (see A.6).
3. **EU data residency is a legal requirement, not a preference.** `docs/LEGAL.md`: Anthropic EU endpoints only, GDPR-sensitive portfolio data, DPA before launch. → **Every component must sit in an EU region** (Frankfurt/Dublin/Paris). This rules out US-default project regions.
4. **It's a two-service app + Postgres.** FastAPI (Python, stateful cron, long-running) + Next.js 14 (App Router, SSR, standalone output) + Postgres 16. The Dockerfiles already exist and `docker compose up` works.

## A.2 Recommended target architecture (solo-founder, EU, low-ops)

The README's instinct (Vercel web + Railway/Fly api + Neon db) is right. Refined and made concrete:

```
┌────────────────────────┐     ┌─────────────────────────┐     ┌──────────────────────┐
│  Vercel (web)          │ ──► │  Fly.io (api)           │ ──► │  Neon Postgres       │
│  Next.js 14 SSR/PWA    │HTTPS│  FastAPI, 1 always-on   │ SQLA│  EU (Frankfurt)      │
│  region: fra1 (EU)     │ ◄── │  machine, EU (fra/ams)  │ ◄── │  branching + backups │
└────────────────────────┘     └──────────┬──────────────┘     └──────────────────────┘
                                           │
                          ┌────────────────┼────────────────┬─────────────────┐
                          ▼                ▼                ▼                 ▼
                   Anthropic EU      Resend (email)    Stripe (billing)   Sentry + Plausible
                   (Sonnet/Haiku)    DKIM/SPF/DMARC    EU VAT via Tax     (EU, PII-scrubbed)
```

**Provider choices and the *why* (each defensible for a solo founder):**

| Layer | Pick | Why this, not the alternative |
|---|---|---|
| **Web** | **Vercel** (region `fra1`) | Next.js is theirs; SSR + edge + zero-config; free tier covers launch. Pin the function region to Frankfurt for GDPR. |
| **API** | **Fly.io** (region `fra`/`ams`), 1 `shared-cpu-1x` machine, `min_machines_running=1` | **Critical:** Fly can run a *persistent* process, which the in-process APScheduler cron needs. Railway works too but Fly's EU regions + persistent machines + cheap always-on are the cleanest fit. Render is the third option. **Do NOT use Vercel/Lambda for the API** — serverless kills the in-process scheduler. |
| **DB** | **Neon** (EU Frankfurt) | Serverless Postgres, branching (a staging DB per PR is free), generous free tier, scales to paid. Supabase is the alternative if you later want their Auth — but you already built auth, so Neon's pure-Postgres simplicity wins. |
| **Email** | **Resend** (already coded) | `services/delivery/sender.py` already targets it. Keep it. Set up a **dedicated sending subdomain** (`mail.sundayapp.eu`) so marketing/newsletter sends never poison transactional deliverability. |
| **Newsletter** | **Beehiiv** or **Buttondown** (separate from Resend) | The *free* growth newsletter (Part B) should NOT go through Resend transactional infra — different reputation profile, and you want referral/SparkLoop tooling. Beehiiv has the referral engine built in. |
| **AI** | **Anthropic, EU region** (`ANTHROPIC_REGION=eu`, set `ANTHROPIC_BASE_URL`) | Already configured in `config.py`. **DPA must be executed before launch** (`LEGAL.md`). |
| **Payments** | **Stripe** + **Stripe Tax** | EU VAT/MOSS handled for you. Not yet built — see A.9. |
| **Errors** | **Sentry** (EU data region, PII scrubbing on) | `ARCHITECTURE.md` already plans it. |
| **Product analytics** | **Plausible** (EU, cookieless) or **PostHog EU** | `LEGAL.md` mandates "no third-party analytics with portfolio data in payload — Plausible or self-hosted only." Plausible is the compliant default; PostHog EU if you need funnels/flags. |
| **DNS/CDN/WAF** | **Cloudflare** | Free WAF, DNS, rate-limiting at the edge, bot protection on `/auth` endpoints. |
| **Secrets** | Fly secrets + Vercel env vars | No secrets manager needed at this scale. |

**Why not "all on one box with docker-compose"?** You *could* (a single Hetzner CX22 in Nuremberg, ~€4/mo, runs the whole compose file — and Hetzner is EU-native, which is a real GDPR plus). That's the cheapest path and genuinely viable for a solo founder. The tradeoff: you own OS patching, backups, TLS renewal, and uptime. **Recommendation:** Use the managed stack (Vercel+Fly+Neon) for launch to minimize ops; keep the Hetzner-single-box option in your pocket as a cost-cutting move if infra ever dominates costs. The Dockerfiles make either path one decision, not a rewrite.

## A.3 The scheduler problem (read before you deploy the API)

This is the single most important deployment detail and it's invisible until Sunday doesn't fire.

`scheduler.py` runs `BackgroundScheduler` **inside the FastAPI process** on startup. Consequences:

- **Must run ≥1 always-on instance.** On Fly: `min_machines_running = 1`, do not scale to zero.
- **Must NOT run >1 instance of the cron.** If you scale the API to 2+ machines for throughput, *each* will fire the Sunday job → **duplicate emails to every user.** Mitigations, pick one:
  - **(Simplest, launch)** Keep API at exactly 1 machine. Fine to thousands of users — the Sunday batch is the only heavy job and it's I/O-bound.
  - **(Scale)** Split into a dedicated **worker process** (`enable_scheduler=True`) separate from the **web API** (`enable_scheduler=False`, can scale horizontally). One worker, N API machines.
  - **(Robust)** Externalize: disable in-process scheduler, add a tiny authenticated `POST /internal/run-weekly` endpoint, and trigger it from **Fly Machines scheduled, GitHub Actions `schedule:` cron, or Cloudflare Workers Cron**. This survives restarts and decouples cron from app uptime. **Recommended once you have >1 API machine.**
- **Timezone:** cron fires `Sun 17:00 UTC` for *all* users (`scheduler.py` comment admits per-tz is a TODO). For a DE/PT beachhead that's Sun 18:00–19:00 local — acceptable for launch. Revisit when you expand to spread-out timezones.
- **Idempotency:** before launch, ensure `deliver_weekly` is safe to re-run (e.g., a machine restart mid-batch shouldn't double-send to users already processed). Add a "briefing already sent this week" guard keyed on `(user_id, iso_week)`. **This is a launch-blocker bug-class** — verify it.

## A.4 Step-by-step production runbook (first deploy)

> Assumes a domain (e.g. `sundayapp.eu` — buy an EU TLD; it's a trust + SEO signal for an EU product) and accounts on Vercel, Fly, Neon, Resend, Cloudflare, Anthropic, Sentry.

**1. Database (Neon, EU)**
- Create a project in **Frankfurt**. Create `main` branch (prod) + a `staging` branch.
- Copy the pooled connection string. Convert to the driver the app uses: `postgresql+psycopg://...` (note the `+psycopg` — the app uses psycopg3, see `config.py`).
- Migrations run automatically: `entrypoint.sh` does `alembic upgrade head` on container start. ✅ No manual step.

**2. API (Fly.io)**
- `fly launch` in `api/` (it will detect the Dockerfile). Set primary region `fra`.
- `fly.toml`: set `[http_service] min_machines_running = 1`, `auto_stop_machines = false`. Internal port 8000.
- Add a `[checks]` HTTP healthcheck on `/health` (the route exists).
- Set secrets (A.8 matrix): `fly secrets set DATABASE_URL=... ANTHROPIC_API_KEY=... AUTH_REQUIRED=true COOKIE_SECURE=true ENABLE_SCHEDULER=true ...`
- Deploy. Confirm `/docs` and `/health` respond.

**3. Web (Vercel)**
- Import `web/`. Framework auto-detected (Next 14). **Set region to `fra1`** (Project → Functions → Region).
- **Important:** the web Dockerfile bakes `NEXT_PUBLIC_API_URL` at *build time*. On Vercel you're not using that Dockerfile — set `NEXT_PUBLIC_API_URL=https://api.sundayapp.eu` as a build-time env var. Note `next.config` must have `output: 'standalone'` for the Docker path; verify it's set (the Dockerfile copies `.next/standalone`).
- Set `API_INTERNAL_URL` if SSR fetches server-side.

**4. DNS (Cloudflare)**
- `sundayapp.eu` → Vercel (CNAME/A per Vercel).
- `api.sundayapp.eu` → Fly (CNAME to the Fly app, then `fly certs add api.sundayapp.eu`).
- Email auth records for Resend on `mail.sundayapp.eu` (DKIM, SPF, return-path) — see A.7.
- `DMARC` record on the root: `v=DMARC1; p=quarantine; rua=mailto:dmarc@sundayapp.eu`.

**5. Wire CORS + cookies**
- API `API_CORS_ORIGINS=https://sundayapp.eu` (drop localhost in prod).
- `COOKIE_SECURE=true`, `AUTH_REQUIRED=true` (so unauth requests 401 instead of falling back to `demo_user_id` — see `config.py` and `deps.py`).
- Cross-subdomain cookies: web on `sundayapp.eu`, API on `api.sundayapp.eu` → the session cookie needs `Domain=.sundayapp.eu` and `SameSite=None; Secure` (or, cleaner, **proxy the API under `sundayapp.eu/api`** via Next.js rewrites so it's same-origin and `SameSite=Lax` just works). **The same-origin proxy is the recommended approach** — it sidesteps an entire class of cookie/CORS pain.

**6. Smoke test the critical path**
- Sign up (magic link arrives, link works, session set) → upload CSV → see dashboard with *real* prices → view briefing with AI narrative → receive a test Sunday email (trigger `deliver_weekly` manually first).

**7. Turn the scheduler on** only after step 6 passes and the idempotency guard (A.3) is verified.

## A.5 Environments

| Env | Web | API | DB | Purpose |
|---|---|---|---|---|
| **Local** | `npm run dev` | `uvicorn --reload` | docker-compose Postgres | dev |
| **Staging** | Vercel preview (per-PR) | Fly app `sunday-api-staging` | Neon `staging` branch | test migrations + AI cost before prod |
| **Prod** | Vercel prod | Fly app `sunday-api` | Neon `main` | live |

Neon branching makes staging nearly free — a throwaway DB copy per PR. Use it to test every Alembic migration before it touches prod data.

## A.6 CI/CD (currently absent — build this)

There is **no `.github/` workflow**. Minimum viable pipeline:

```yaml
# .github/workflows/ci.yml  (sketch)
on: [push, pull_request]
jobs:
  api:
    - ruff check api/        # already a dep
    - pytest api/            # real coverage exists (concentration/csv/tax/fire/auth/delivery tests)
  web:
    - npm ci && npm run typecheck && npm run lint && npm run build
```

- **Deploy on merge to `master`:** `fly deploy` (API) via `FLY_API_TOKEN` secret; Vercel auto-deploys from Git natively (no action needed).
- **Gate:** don't auto-deploy API if `pytest` fails. Migrations run on container start, so a bad migration = bad deploy — test on the Neon staging branch first.
- **Add `pip-audit` / `npm audit` + a secrets scanner** (gitleaks) given this is fintech.

## A.7 Email deliverability (P0 — the product literally is this)

Because the Sunday briefing is an email, treat sending reputation as core infra:

- **Separate domains/subdomains by stream:**
  - `briefing@mail.sundayapp.eu` → **transactional** (Resend): magic links, the Sunday briefing.
  - `hello@news.sundayapp.eu` → **marketing** (Beehiiv): the free newsletter.
  - Keeping these separate means a marketing-list spam complaint never threatens delivery of a paying user's briefing.
- **Authenticate both:** SPF, DKIM, DMARC (start `p=none` to monitor, move to `p=quarantine`). Verify with mail-tester.com (aim 10/10) before any volume.
- **Warm up** the briefing domain gradually — don't blast 1,000 first emails cold.
- **List hygiene:** handle bounces/complaints (Resend webhooks) → suppress. A high bounce rate from stale CSV-era test addresses will tank you.
- **Content:** plaintext-friendly, real from-name, one-click unsubscribe (legally required in EU — and required for the *newsletter*; the transactional briefing is opt-in by virtue of being a paid/registered feature but still give an easy "pause briefings").
- The `email_from` default in `config.py` is `briefing@example.com` — **change before deploy** (obvious, but it's the kind of thing that ships).

## A.8 Secrets & config matrix

| Var | Local | Prod value | Notes |
|---|---|---|---|
| `DATABASE_URL` | compose Postgres | Neon pooled, `+psycopg` | secret |
| `AUTH_REQUIRED` | `false` | **`true`** | else falls back to `demo_user_id` — a **security hole** if left false in prod |
| `COOKIE_SECURE` | `false` | **`true`** | HTTPS cookies |
| `API_CORS_ORIGINS` | localhost | `https://sundayapp.eu` | no wildcards w/ credentials (rule from fastapi.md) |
| `ANTHROPIC_API_KEY` | optional | set | secret; no-train EU tier |
| `ANTHROPIC_REGION` / `ANTHROPIC_BASE_URL` | `eu` / blank | `eu` / EU endpoint | data residency |
| `ENABLE_SCHEDULER` | `false` | `true` (on the *one* worker only) | see A.3 |
| `RESEND_API_KEY` | blank (dry-run) | set | blank = renders but doesn't send (safe default) |
| `EMAIL_FROM` | example.com | `Sunday <briefing@mail.sundayapp.eu>` | **must change** |
| `APP_BASE_URL` / `API_BASE_URL` | localhost | prod URLs | magic links point at `API_BASE_URL` |
| `FMP_API_KEY` | blank | set | price fallback |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | blank | set | once billing ships (A.9) |

**Security audit before launch:** rotate the dev DB password (`sunday_dev_only_change_me` is in compose + config defaults — it's a placeholder, but verify it never reaches a public instance). Confirm `AUTH_REQUIRED=true` and that `deps.py` truly 401s without a session in prod (the `demo_user_id` fallback is the thing to kill).

## A.9 The missing piece: Stripe billing

Not built. Smallest correct implementation:

- **Stripe Checkout (hosted)** for Free→Pro — least PCI surface, fastest to ship (per `stripe-best-practices`: prefer Checkout Sessions over hand-rolled PaymentIntents for subscriptions).
- **Stripe Tax** on — handles EU VAT/MOSS automatically (you sell B2C across EU member states; VAT is otherwise a nightmare).
- **Webhook** (`POST /api/billing/webhook`, signature-verified with `STRIPE_WEBHOOK_SECRET`) → flip `user.plan` on `checkout.session.completed`, `customer.subscription.updated/deleted`.
- **Entitlement gating** in `deps.py`: AI chat message caps, briefing depth, holdings limit — the caps are *both* monetization and COGS control (`Blueprint` Part 3.2 / Part 7).
- **Annual plan** with ~2 months free (churn suppression — the single biggest lever on LTV).
- Pricing: **€9/mo or €79/yr Pro** (per `REVIEW_AND_PLAN.md` §7 — €9, not €7, so you don't signal "cheap tracker" below Parqet's €11.99).

## A.10 Observability & ops

- **Sentry** (EU region) on both web + API, `send_default_pii=False`, scrub portfolio fields. `ARCHITECTURE.md` already specs PII-scrubbed errors.
- **LLM cost ledger:** `ARCHITECTURE.md` plans an `llm_call_log` table (tokens/model/latency per call) feeding a per-user monthly budget cap. **Verify this exists before turning on paid AI** — uncapped co-pilot abuse is the #1 margin killer (Blueprint Part 7.5). If it's not there, it's a launch-blocker for the paid tier.
- **Uptime:** a free monitor (UptimeRobot/Better Stack) on `/health` and on `sundayapp.eu`.
- **Cost dashboard:** weekly glance at Anthropic spend, Neon compute, Fly machine-hours, Resend volume.
- **Load test the Sunday batch** (`ROADMAP` Phase 4 target: 1,000 briefings < 10 min). Do this on staging with synthetic users before you have 1,000 real ones.
- **Backups:** Neon does automated backups; confirm retention ≥30 days (`ARCHITECTURE.md` says 30). Test a restore once.

## A.11 Deployment cost model (grounded in the stack)

| Stage | Users (paid) | Web | API | DB | AI | Email | Tools | **€/mo** |
|---|---|---|---|---|---|---|---|---|
| **Launch** | <500 (≈10) | Vercel free | Fly 1×shared-1x ~€5 | Neon free→€19 | <€20 | Resend free→€18 | Sentry/Plausible free | **~€30–80** |
| **Growth** | 5k (≈250) | €20 | Fly 2× ~€25 | Neon €19–69 | €100–400 | €18–50 | €50 | **~€250–650** |
| **Scale** | 50k (≈2.5k) | €20–150 | Fly scaled ~€100 | €69–300 | €1k–4k | €100–300 | €150 | **~€1.5k–5k** |

Consistent with the Blueprint's ~75–85% gross-margin target **iff** AI caps + prompt caching are enforced (the shared-market-layer-cached-across-users design in `ARCHITECTURE.md` is exactly the lever). The Hetzner-single-box alternative collapses launch infra to **~€5–15/mo** at the cost of self-managed ops.

## A.12 Pre-launch gates (deploy is blocked until these are true)

These are *not* optional for an EU fintech-adjacent product (from `docs/LEGAL.md` + Blueprint Part 6):

- [ ] **Securities/fintech counsel sign-off** on the non-advice publisher posture (DE BaFin FinTech-Kontakt is free; PT CMVM).
- [ ] **Privacy Policy + ToS + Cookie Policy + DE Impressum** (Impressum is *legally mandatory* in Germany — your beachhead).
- [ ] **Anthropic EU DPA + Stripe DPA + Resend DPA** executed.
- [ ] **GDPR DPIA** documented; DSAR/account-deletion endpoint cascades to all owned data.
- [ ] **AI Act transparency**: "Generated with AI assistance" on every LLM-touched output (component `Disclaimer.tsx` exists — verify it's on briefing + chat + email).
- [ ] **LLM output guardrails live** (`services/llm/guardrails.py` forbidden-phrase regex + re-prompt) — verify it actually runs on chat *and* briefing output, not just specced.
- [ ] **Marketing copy reviewed** against MiFID II non-advice line — **do not say "robo-advisor," do not say "AI recommends."** (See B.10.)
- [ ] **Idempotent Sunday send** (A.3) + **AI cost cap** (A.10) verified.

> The legal gates and the deploy are coupled: you can deploy a *private beta* (waitlist, NDA-ish, no public marketing) before counsel sign-off, but you **cannot run public paid marketing** until the gates clear. Sequence accordingly (Part B).

---

# PART B — MARKETING

> The strategy docs already contain deep, cited market research (Morning Brew/Finimize playbooks, channel ROI, competitor pricing, the EU incumbent set: Parqet ~350k, getquin ~300k+community, Finanzfluss). This section **operationalizes** that into a concrete, do-this-Monday plan. It does not re-argue the research.

## B.1 The one-sentence positioning (use everywhere)

From `REVIEW_AND_PLAN.md` §8, this line does all the work — ritual + AI + EU-tax + privacy + advice-neutral:

> **"Every Sunday, one calm read on your money — stocks and crypto, written by AI that actually knows what you own, EU-tax-aware, and never tells you what to do. No broker login. No noise."**

The product name *is* the brand asset: **own "Sunday"** the way Morning Brew owns the morning (Blueprint Part 9, moat #1). Every touchpoint reinforces a weekly ritual.

## B.2 Beachhead — be narrow on purpose

**German + Portuguese self-directed FIRE/dividend investors holding stocks + crypto on Trade Republic / Scalable.** DE first (largest EU neobroker base + your tax engine's deepest country), PT second (founder proximity), then FR/NL/ES/IT as tax tables fill in.

Why narrow wins here: you cannot out-track the trackers or out-community getquin. You can win **one specific person**: *"I have 15 positions across TR and a bit of crypto, I have no idea what actually happened this week, and I don't want a dashboard — I want someone to just tell me, calmly, on Sunday."* Build, write, and market for exactly that person.

## B.3 The growth engine (priority order for a solo founder)

Mirrors Blueprint Part 4 channel-ROI, sequenced:

1. **Free weekly newsletter ("EU Markets: Your Sunday Read")** — ★★★★★. This is the #1 asset. It's the funnel, the SEO archive, the proof the AI narrative is good, *and* a second monetizable asset (sponsorships later). **It is a de-personalized version of the product** — which keeps it firmly on the publisher side of MiFID II. Start it **before the app is fully done.**
2. **Programmatic SEO + comparison pages** — ★★★★★, slow-compounding. The content moat.
3. **Reddit / community value-first** — ★★★★, fast. r/Finanzen, r/EuropeFIRE, r/dividends, r/mauerstrassenwetten (carefully), getquin-refugee threads.
4. **Build-in-public on X/LinkedIn (DE + EN)** — ★★★★. FinTwit + finanzfluss-adjacent.
5. **Referral** (Morning Brew milestone engine, ~€0.25 effective CAC) — ★★★★, once you have a base.
6. **One sub-Finanzfluss distribution partnership** — ★★★★. NOT Finanzfluss (now a competitor); the tier below.
7. **Paid ads** — ★★ — **do not lead here.** Fintech CAC (€80–150) eats LTV before PMF. Only after the funnel is proven (CAC < LTV/3).

## B.4 Newsletter setup (do this week — it's the long pole)

- Platform: **Beehiiv** (built-in referral milestones + recommendations network for cheap subscriber growth) or Buttondown (privacy-minded, EU-friendly).
- Cadence: weekly, **Sunday**, same calm tone as the product. The newsletter *is* a sample briefing for a generic EU portfolio.
- Content: "what happened in EU/global markets this week + the week ahead (ECB/CPI/earnings) + one explainer (e.g. *what Teilfreistellung actually means*)." EU-tax angle is your differentiator vs Morning Brew-style generic finance.
- Capture: a `/newsletter` landing page + inline signup on every blog post + a "get the free Sunday Read" CTA above the app paywall.
- **Compliance:** keep it impersonal/general (publisher exclusion). One-click unsubscribe. Author byline + disclaimer (YMYL E-E-A-T).
- Growth tactic: SparkLoop/Beehiiv recommendations + cross-promo swaps with other small EU finance newsletters.

## B.5 SEO / content engine

Finance is **YMYL** ("Your Money Your Life") — Google penalizes thin AI content. Invest in E-E-A-T: real author identity, citations, accuracy, disclaimers (which you have a culture of). Targets:

- **Comparison pages (highest intent):** "Sunday vs Parqet," "Sunday vs getquin," "best EU portfolio tracker with AI briefing," "Trade Republic Steuer-Übersicht / tax overview," "getquin Alternative ohne Login."
- **Explainers (programmatic, human-edited):** `/explain/[teilfreistellung|abgeltungssteuer|MSCI-World|TWR|CPI|ECB-rate]` — DE + EN. Near-zero marginal cost, long-tail capture.
- **Ticker/portfolio pages later** once you have authority (don't spam thin pages early — YMYL penalty risk).
- The newsletter archive, indexed, compounds this.

## B.6 Launch sequence (gated by the legal checklist in A.12)

| Phase | Gate | Actions |
|---|---|---|
| **Now → AI briefing polished** | none (private) | Waitlist landing page live; newsletter started; build-in-public threads; seed value (not spam) in 3–4 subreddits. **Target: 500 waitlist / 300 newsletter.** |
| **Private beta** | basic ToS/Privacy | Hand-onboard 50–100 design partners from waitlist. Generate a *stunning real briefing* for each. The first briefing must land **<2 min from CSV upload** (the aha-moment). Extract testimonials. Fix the report until they say "I'd be annoyed to lose this." |
| **Public launch** | **full A.12 legal gate cleared** | Product Hunt + "Show HN" + Reddit + X. Daily market-insight posts. Referral on. Turn on Stripe. **Target: 1,000 signups, first 50 paid.** |
| **Scale funnel** | — | Paywall + onboarding A/B; first compliant sub-Finanzfluss partnership; comparison-page SEO blitz; annual-plan push. |

**Do NOT publicly market "AI" until the AI is genuinely good and live** — AI-washing risk (SEC fined PortfolioPilot $175k; EU AI Act Art. 50 from Aug 2, 2026). The good news: per Part 0, the AI *is* now built — so verify quality, then say it.

## B.7 Pricing & conversion (from REVIEW_AND_PLAN §7)

| Tier | Price | Hook |
|---|---|---|
| **Free** | €0 | 1 portfolio, ≤15 holdings, monthly briefing + 1 weekly preview, 5 AI chats/mo, basic tax/FIRE. Feeds off the newsletter. |
| **Pro** | **€9/mo or €79/yr** | Unlimited holdings, full weekly briefing + email/PDF, 150 AI chats/mo, full tax/FIRE/dividend, benchmark, alerts. |
| **Pro+ / AI** (later) | €19/mo | Higher AI limits, Opus deep-dives, multi-portfolio, daily mini-briefing. |

Conversion levers (Blueprint 3.3): **aha in <90s** (real mini-briefing on *their* tickers during onboarding — biggest lever), Saturday-email→Sunday-report ritual, usage-cap upgrade prompts ("5/5 chats used"), annual nudge at month 1, win-back to free+newsletter on cancel. Expect 3–5% freemium conversion (8%+ if the briefing is loved); add the 7-day Pro trial to capture fintech's higher trial-conversion (~18%).

## B.8 Instrument from day one (north star = weekly briefing open rate)

| Metric | Target | Why |
|---|---|---|
| **Weekly briefing open rate** | **>50% sustained** | The ritual = retention = PMF proxy. *The* number. |
| Aha-rate (signup → uploaded portfolio + viewed full briefing in 24h) | maximize | Onboarding health |
| Free → Pro | ≥4% | Monetization |
| Monthly churn | <5% (push annual) | The kill-switch metric |
| CAC | <€40 (organic-led) | Model only works on cheap acquisition |
| Referral coefficient | track | The Morning Brew compounding lever |

Use **Plausible/PostHog EU** (no portfolio data in payload, per LEGAL.md). The weekly-open-rate metric requires email open tracking — use Resend's, privacy-respecting, EU.

## B.9 First-90-days calendar (operationalized)

- **Weeks 1–2:** Waitlist + newsletter live. 1 build-in-public thread/day. Seed 3 subreddits with genuine value. Buy `sundayapp.eu`. → 500 waitlist / 300 subs.
- **Weeks 3–4:** Beta onboard 50–100. 5 user interviews/wk. Ship fixes. 2 SEO articles/wk (comparison + explainer). → NPS signal, aha-rate baseline.
- **Weeks 5–8:** Public launch (PH/HN/Reddit/X) *after legal gate*. Daily market posts. Referral on. → 1,000 signups, first 50 paid.
- **Weeks 9–12:** Funnel optimization (paywall/onboarding A/B). First compliant finfluencer/partnership test. Newsletter referral milestones. → 5% conv, <5% churn, CAC <€40.

## B.10 Compliance-safe marketing copy (non-negotiable)

The marketing copy is a *legal surface* (LEGAL.md: "robo-advisor language is the trap"). Hard rules:

- ✅ Say: "understand," "explain," "what happened and why," "information," "EU-tax-aware," "advice-neutral," "never tells you what to do."
- ❌ Never say: "robo-advisor," "AI recommends," "should buy/sell," "optimize your portfolio," "beat the market," "first regulated AI advisor," "expert AI forecasts."
- ✅ Describe AI capabilities **accurately** — no AI-washing.
- ✅ Disclaimer present on landing page footer, every report, every chat session.
- The positioning line in B.1 is pre-vetted to stay on the right side of this — anchor all copy to it.

---

## C. The critical path to a paid launch (synthesis)

What actually stands between today and a stranger paying you:

1. **Update README/ROADMAP** to reflect what's built (0.5 day). *Prevents bad decisions.*
2. **Verify the launch-blocker bug-classes** (1–2 days): Sunday-send idempotency (A.3), AI cost cap + guardrails actually run on chat *and* briefing (A.10/A.12), `AUTH_REQUIRED=true` truly kills the `demo_user_id` fallback (A.8).
3. **Build Stripe billing** (A.9) — the one missing product piece (~1 week).
4. **Stand up the deployment** (A.4) on Vercel + Fly(EU) + Neon(EU), same-origin API proxy, EU regions throughout (~2–3 days).
5. **Email deliverability** done properly — separate transactional/marketing domains, full DKIM/SPF/DMARC (A.7) (~1 day).
6. **Clear the legal gates** (A.12) — counsel, DPAs, policies, Impressum. *Runs in parallel; it's the long pole and gates public marketing, not private beta.*
7. **Start the newsletter + waitlist NOW** (B.4) — growth compounds slowly; every week not started is lost.

**Sequencing insight:** marketing's slow-compounding assets (newsletter, SEO, waitlist) should start *immediately and in parallel* with the deploy/billing/legal work — they don't depend on the app being finished, and they're the binding constraint on the whole business ("distribution, not product" — Blueprint Part 3.5). Ship the product to a private beta behind the legal gate; pour the marketing engine the whole time; flip to public the moment counsel signs off.
