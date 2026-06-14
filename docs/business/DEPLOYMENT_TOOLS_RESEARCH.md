# Sunday App — Deployment Tools & Pricing Research

*Online research into the best hosting/infra tools for this exact app, with live 2026 pricing and a costed recommendation.*

**Date:** June 2026
**Method:** Live web research (pricing pages + 2026 comparison sources, cited at the end) filtered against this app's real constraints (see §1). Prices are **as found in June 2026 and change often — re-verify on the vendor page before committing.** Currencies are quoted as the vendor lists them ($ for US-based SaaS, € for Hetzner/EU); $1 ≈ €0.92.
**Companion docs:** `DEPLOYMENT_AND_MARKETING.md` (the runbook), `Sunday_App_Business_Blueprint.md` (cost model Part 7).

---

## 1. The constraints that filter the tools (why "best" ≠ generic best)

This app is not a generic CRUD SaaS. Four hard constraints eliminate most "just use serverless" advice:

1. **Always-on Python process** — the Sunday briefing uses an **in-process APScheduler cron** (`api/app/services/delivery/scheduler.py`). The API host must run a persistent process, **not scale-to-zero serverless**. (Lambda/Vercel Functions/Cloudflare Workers for the API = the cron never fires.)
2. **Single cron owner** — >1 API replica = duplicate Sunday emails. Need 1 always-on machine, or an externalized cron.
3. **EU data residency (legal, not preference)** — `docs/LEGAL.md`: GDPR-sensitive portfolio data, Anthropic EU endpoints, EU-only analytics. Every component in an EU region (Frankfurt/Dublin/Helsinki/Paris).
4. **The product is an email** — deliverability is core infra; transactional and marketing mail must be reputation-isolated.

These four turn the question from "what's cheapest" into "what's cheapest *that runs a persistent EU process and delivers mail reliably*."

---

## 2. Layer-by-layer research

### 2.1 API hosting (FastAPI, persistent, EU) — the pivotal choice

| Tool | Entry price (2026) | EU region | Persistent process / cron | Verdict for Sunday |
|---|---|---|---|---|
| **Fly.io** | `shared-cpu-1x` 256 MB ≈ **$1.94–2/mo**; realistic prod (1–2 instances + extras) **$13–20/mo**. No free tier since 2024 ($5 trial credit). | ✅ `fra`, `ams`, `cdg` | ✅ Persistent Machines; set `min_machines_running=1` | ★★★★★ **Best managed fit.** Cheap always-on, EU regions, runs the in-process cron as-is. |
| **Railway** | Hobby **$5/mo** (incl. $5 usage), Pro **$20/mo** (incl. $20 usage), then usage. | ✅ EU metal (Amsterdam) | ✅ Persistent services + native cron | ★★★★ Great DX; slightly pricier floor than Fly. Strong alternative. |
| **Render** | Web service from **$7/mo**; **background worker $7/mo**; **cron job $1/mo** (first-class). Pro plan $25/mo. Getting pricier in 2026. | ✅ Frankfurt | ✅ First-class workers + cron | ★★★★ Cleanest if you externalize the cron to a Render Cron Job; costs add up (web+worker = $14+). |
| **Hetzner Cloud** | **CX22** (2 vCPU/4 GB/40 GB) **€3.49/mo**; CPX22 €7.99/mo. | ✅ Nuremberg/Falkenstein/Helsinki (EU-native) | ✅ Full VPS — runs anything | ★★★★★ **Cheapest by far.** Runs your whole `docker-compose` (API+Postgres+web) on one box. Trade-off: you own patching/backups/TLS/uptime. |

**Takeaway:** For *low-ops* → **Fly.io** (persistent + EU + ~$5 always-on). For *lowest-cost* → **Hetzner** (€3.49 runs everything). Avoid serverless for the API regardless of cost — it breaks the scheduler.

### 2.2 Web hosting (Next.js 14 App Router, SSR + SEO)

| Tool | Price (2026) | Notes |
|---|---|---|
| **Vercel** | Hobby **free** but **commercial use prohibited**; **Pro $20/user/mo** (incl. $20 credits) required once you charge. | Best Next.js DX + SSR + preview deploys. The €20 floor is real for a paid product. Pin region to `fra1`. |
| **Cloudflare Pages/Workers** | **Free** tier is commercial-OK; Workers Paid $5/mo. | Cheaper, commercial-friendly free tier, EU edge. Next.js SSR support is good but more finicky than Vercel (use `@cloudflare/next-on-pages` / OpenNext). Viable if avoiding the $20. |
| **Self-host on the Hetzner box** | **€0 extra** | Next.js `output: 'standalone'` (Dockerfile already does this) served behind Caddy on the same VPS. Cheapest; you manage it. |

**Takeaway:** **Vercel Pro ($20)** for best-in-class SEO/DX (your #1 growth channel is SEO — worth it), **or** self-host on Hetzner for €0 if minimizing cost. Cloudflare Pages is the free-but-commercial-OK middle ground.

### 2.3 Database (Postgres 16, EU)

| Tool | Free tier | Paid entry | EU | Notes |
|---|---|---|---|---|
| **Neon** | **$0** — 100 CU-hrs, 0.5 GB, scale-to-zero | **Launch ~$5/mo min** (usage: $0.106/CU-hr, $0.35/GB-mo, up to 16 CU) | ✅ Frankfurt | Serverless Postgres + **branching** (free per-PR staging DB). Storage price dropped to $0.35/GB in 2025 (Databricks acquisition). **Best managed Postgres for this app.** |
| **Supabase** | **$0** — 500 MB, **pauses after 1 wk inactivity** | **Pro $25/mo/project** — 8 GB | ✅ (AWS EU) | More than a DB (auth, storage, edge fns) — but you already built auth, so the extras are dead weight. Free-tier pausing is bad for an always-on app. |
| **Hetzner (self-managed PG)** | €0 (on the VPS) | included in the €3.49 box | ✅ | Postgres in your docker-compose. Cheapest; you own backups. |

**Takeaway:** **Neon** (managed, branching, EU, ~$5 floor) for the low-ops stack; **self-hosted Postgres on Hetzner** (€0) for the cheap stack. Skip Supabase here — you don't need its auth/extras and the pausing free tier fights an always-on product.

### 2.4 Transactional email (the briefing + magic links) — deliverability-critical

| Tool | Price (2026) | Deliverability | Notes |
|---|---|---|---|
| **Resend** | **Free 3,000/mo (100/day)**; **Pro $20/mo (50k)**; Scale from $90 (100k). | Good; **shared** infra for transactional + broadcasts (weaker reputation isolation). | ✅ Already coded (`services/delivery/sender.py`). Best DX for Next/React. EU region available. |
| **Postmark** | From **$15/mo (10k)**; $55 at 50k. | **Best-in-class** — Message Streams **hard-isolate** transactional vs broadcast; ~7s to inbox; published benchmarks. | Pricier at scale; the gold standard if briefing deliverability is the whole product. |

**Takeaway:** **Keep Resend** (already integrated, free to start, cheap at 50k). Mitigate its shared-infra weakness by **putting the marketing newsletter on a totally separate platform/domain** (Beehiiv) so it never shares reputation with the briefing. If briefing inbox-placement ever becomes a problem, Postmark is the upgrade.

### 2.5 Newsletter (the #1 growth engine — keep it OFF transactional infra)

| Tool | Price (2026) | Notes |
|---|---|---|
| **Beehiiv** | **Free "Launch" ≤2,500 subs** (unlimited sends, custom domain); **Scale $49/mo** ($43 annual) adds monetization/AB/AI; Max $109. | Built-in **referral milestone engine** (the Morning Brew lever) + recommendation network for cheap growth. **Best fit for the growth strategy.** |
| **Buttondown** | Free ≤100 subs, ~$9+/mo. | Privacy-minded, EU-friendly, simpler. Good if you want minimal + cheap. |

**Takeaway:** **Beehiiv free** until 2,500 subs (covers the whole pre-launch + early phase for €0), specifically for its referral engine. Separate domain (`news.sundayapp.eu`) from the briefing.

### 2.6 Payments (not yet built)

- **Stripe card fee (EU domestic):** **1.5% + €0.25** per transaction.
- **Stripe Billing** (subscriptions): **0.7%** of billing volume (consolidated 2024).
- **Stripe Tax** (EU VAT/MOSS automation): **0.5%** add-on, pay-as-you-go.
- **All-in on a €9 Pro sub:** ~1.5% + €0.25 (card) + 0.7% (Billing) + 0.5% (Tax) ≈ **€0.45–0.50 per €9 charge (~5%)**. Acceptable; Tax automation is worth it vs. hand-rolling EU VAT across member states.
- You can **skip Stripe Billing's 0.7%** by managing subscription state yourself via Checkout + webhooks (more code), but at launch volume the 0.7% is trivial — use Billing.

### 2.7 Error monitoring

| Tool | Price (2026) | Notes |
|---|---|---|
| **Sentry** | **Free Developer** — 5k errors/mo, 1 user, 30-day retention; **Team $26/mo** — 50k errors, unlimited users. | EU data region available; PII-scrub on. Free tier fine for launch. Already planned in `ARCHITECTURE.md`. |

**Takeaway:** **Sentry free** at launch; Team ($26) when you have users/teammates.

### 2.8 Product analytics (must be EU + no portfolio data in payload — `LEGAL.md`)

| Tool | Price (2026) | Notes |
|---|---|---|
| **Plausible** | **No free tier; from $9/mo** (10k pageviews); EU-hosted + GDPR by default; cookieless. | Simplest compliant choice. Self-host = €0. |
| **PostHog (EU Cloud)** | **Free up to 1M events/mo**; EU hosting + SOC 2; unlimited team. | Far more generous free tier + funnels/flags/session-replay — useful for paywall/onboarding A/B (Blueprint conversion plan). |

**Takeaway:** **PostHog EU free tier** is the better value *and* gives you the funnel/flag tooling the conversion strategy needs — provided you configure it to send **no portfolio data** (LEGAL.md). Plausible ($9) if you want dead-simple privacy-first pageviews only.

### 2.9 AI (Anthropic, EU) — usage, not subscription

Per-1M-token API pricing (from the Blueprint Part 7.3, consistent with current Anthropic rates):

| Model | Input / Output | Use in Sunday |
|---|---|---|
| **Claude Haiku 4.5** | **$1 / $5** | Per-user narrative wrapper, guardrail/summary tier |
| **Claude Sonnet 4.6** | **$3 / $15** | Shared weekly market layer (cached across all users) + chat |
| **Claude Opus 4.8** | **$5 / $25** | Paid-tier deep-dives only |

**Cost lever:** the `ARCHITECTURE.md` design — Sonnet shared layer with **prompt caching (~90% off cached input)** amortized across all users + Haiku per-user — keeps blended AI COGS at **~€1–4/active paid user/mo** and gross margin 75–85%. **Use the EU region** (`ANTHROPIC_REGION=eu` + base URL) and execute the **DPA before launch**.

### 2.10 DNS / CDN / WAF

- **Cloudflare — free.** DNS, edge caching, free WAF, rate-limiting on `/auth`, bot protection. No reason to use anything else at this stage.

---

## 3. Three costed stacks (pick one)

### Stack A — "Lowest cost" (self-managed, one EU box) — **~€15–35/mo**

| Layer | Tool | €/mo |
|---|---|---|
| API + Postgres + Web (docker-compose + Caddy) | **Hetzner CX22** (Nuremberg) | **€3.49** |
| Transactional email | Resend (free 3k) | €0 |
| Newsletter | Beehiiv (free ≤2,500) | €0 |
| DNS/WAF/TLS | Cloudflare | €0 |
| Errors | Sentry (free) | €0 |
| Analytics | PostHog EU (free) | €0 |
| AI | Anthropic (usage) | ~€10–30 |
| Domain | `.eu` | ~€1 |
| **Total** | | **~€15–35/mo** |

*Best when:* you're pre-revenue, comfortable with light Linux sysadmin, and want to spend nothing until traction. EU-native (Hetzner) is a genuine GDPR plus. Cost: you own patching, backups, uptime.

### Stack B — "Recommended" (low-ops hybrid) — **~€35–70/mo at launch** ⭐

| Layer | Tool | €/mo |
|---|---|---|
| Web | **Vercel Pro** (`fra1`) — best SEO/DX, commercial-OK | ~€18 ($20) |
| API (always-on, cron) | **Fly.io** (`fra`), 1× shared-cpu-1x 512 MB | ~€5–10 |
| Database | **Neon** (Frankfurt) — free → Launch | €0–5 |
| Transactional email | **Resend** — free → Pro at volume | €0–18 |
| Newsletter | **Beehiiv** (free ≤2,500) | €0 |
| DNS/WAF | **Cloudflare** | €0 |
| Errors | **Sentry** (free) | €0 |
| Analytics | **PostHog EU** (free ≤1M events) | €0 |
| AI | **Anthropic** EU (usage) | ~€10–30 |
| Payments | **Stripe** (% of revenue, not fixed) | — |
| Domain | `.eu` | ~€1 |
| **Total** | | **~€35–70/mo** |

*Best when:* you want to ship fast, minimize ops, and keep SEO-grade web hosting. **This is the recommended launch stack** — managed everything, EU throughout, the scheduler "just works" on Fly's persistent machine, and most components stay free until you have real usage. *Cost-cut option:* swap Vercel Pro → Cloudflare Pages (free) or self-host web on a Hetzner box to drop ~€18.

### Stack C — "Scale" (~5k users / ~250 paid) — **~€250–650/mo**

Same shape as B, scaled: Fly 2× machines (~€25, split web-API from cron-worker — see `DEPLOYMENT_AND_MARKETING.md` §A.3), Neon €19–69, Resend €18–50, PostHog still likely free, Sentry Team €26, Beehiiv Scale €43 (once monetizing the newsletter), Anthropic €100–400 (the dominant variable). Consistent with the Blueprint's growth-stage projection and 75–85% gross margin **iff** AI caps + prompt caching hold.

---

## 4. Bottom line

- **The pivotal decision is the API host**, and it's dictated by the in-process scheduler, not price: **Fly.io** (managed, persistent, EU, ~€5) or **Hetzner** (€3.49, self-managed). **Not** serverless.
- **Recommended launch stack = B**: Vercel Pro + Fly (EU) + Neon (EU) + Resend + Beehiiv + Cloudflare + Sentry/PostHog free + Anthropic EU. **~€35–70/mo**, near-zero ops, EU-compliant, scheduler-safe.
- **Cheapest viable = A**: everything on one **Hetzner CX22 (€3.49)** via your existing `docker-compose`, free tiers around it. **~€15–35/mo** if you'll do light sysadmin.
- **Keep newsletter (Beehiiv) reputation-isolated from the briefing (Resend)** — separate platforms, separate sending domains. This protects the thing the whole product depends on.
- **Biggest variable cost at every stage is Anthropic** — the prompt-caching + Haiku/Sonnet split + per-user caps in `ARCHITECTURE.md` are what keep it (and your margin) under control.

---

## Sources (June 2026)

**API/web hosting:** [Fly.io pricing (Deploy Handbook)](https://deployhandbook.com/pricing/fly-io) · [Fly.io pricing (Kuberns)](https://kuberns.com/blogs/flyio-pricing/) · [Railway pricing](https://railway.com/pricing) · [Railway plans (docs)](https://docs.railway.com/pricing/plans) · [Render pricing (SaaSPricePulse)](https://www.saaspricepulse.com/tools/render) · [Railway vs Render (Northflank)](https://northflank.com/blog/railway-vs-render) · [Hetzner new CX plans](https://www.hetzner.com/pressroom/new-cx-plans/) · [Hetzner pricing after Apr 2026 (Bitdoze)](https://www.bitdoze.com/hetzner-cloud-cost-optimized-plans/) · [Hetzner pricing (bestusavps)](https://bestusavps.com/reviews/hetzner/) · [Vercel pricing (SaaSPricePulse)](https://www.saaspricepulse.com/tools/vercel) · [Vercel pricing (Costbench)](https://costbench.com/software/developer-tools/vercel/)
**Database:** [Neon pricing 2026 (Simplyblock)](https://vela.simplyblock.io/articles/neon-serverless-postgres-pricing-2026/) · [Neon pricing (SaaSPricePulse)](https://www.saaspricepulse.com/tools/neon) · [Supabase pricing (UI Bakery)](https://uibakery.io/blog/supabase-pricing) · [Neon vs Supabase (closefuture)](https://www.closefuture.io/blogs/neon-vs-supabase)
**Email/newsletter:** [Resend pricing (StackScored)](https://www.stackscored.com/pricing/transactional-email/resend/) · [Resend vs Postmark (Postmark)](https://postmarkapp.com/compare/resend-alternative) · [Email API pricing (BuildMVPFast)](https://www.buildmvpfast.com/api-costs/email) · [Beehiiv pricing (MailCompared)](https://mailcompared.com/pricing/beehiiv-pricing/) · [Beehiiv pricing (EmailToolTester)](https://www.emailtooltester.com/en/reviews/beehiiv/pricing/)
**Payments:** [Stripe fees 2026 (Checkout Page)](https://checkoutpage.com/blog/stripe-processing-fees) · [Stripe pricing breakdown (Flexprice)](https://flexprice.io/blog/stripe-pricing-breakdown-2026) · [Stripe Tax pricing (Stripe)](https://stripe.com/tax/pricing)
**Observability/analytics:** [Sentry pricing](https://sentrypricing.com/) · [Sentry free plan (Costbench)](https://costbench.com/software/developer-tools/sentry/free-plan/) · [Plausible vs PostHog pricing (CheckThat/Schematic)](https://checkthat.ai/brands/plausible-analytics/pricing) · [PostHog pricing (Schematic)](https://schematichq.com/blog/posthog-pricing)
**AI:** Anthropic API pricing per `Sunday_App_Business_Blueprint.md` Part 7.3 ([LLM API pricing](https://intuitionlabs.ai/articles/ai-api-pricing-comparison-grok-gemini-openai-claude)).
