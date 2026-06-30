# Tier & Pricing Research — how to build Sunday's tiers to sell better

*Research date: 15 June 2026. Synthesised from four parallel web-research passes (packaging & pricing, conversion & paywalls, competitor teardowns, entitlements architecture). Every figure is cited inline. Competitor prices were captured on 15 Jun 2026 and trackers change pricing often, so re-confirm before putting any number in production copy. Confidence: High on direction, Medium on exact benchmark percentages.*

---

## Executive summary

1. **Move from 2 tiers to 3: Free, Pro (hero), and a higher anchor.** Three tiers with a deliberately higher top tier lifts selection of the middle tier (the decoy/anchor effect is one of the better-evidenced findings here). Keep Pro at **€9/mo** (charm pricing is academically validated) and add an anchor "Premium" above it.
2. **Charge on a value metric of AI cadence + AI allowance, not portfolios.** Keep core tracking generous and free. Fence the premium *intelligence* (weekly email, benchmark, AI volume, deeper tax/FIRE, alerts). Gating core value is the fastest way to churn free users.
3. **Add annual billing, default-on, framed as "2 months free" (€89/yr).** This is the single biggest churn lever available and it funds acquisition.
4. **Switch acquisition to a no-card 14-day reverse trial.** Give every new user full Pro for 14 days, then drop them to Free. It fits a calm, privacy-first finance brand and covers enough weekly-briefing cycles to land the value.
5. **Price AI as flat + a bundled monthly allowance in human units (messages), with a hidden hard cap.** Do not sell raw credits/tokens to consumers.
6. **EU Directive 2023/2673 is enforceable 19 June 2026.** It bans dark patterns in online financial services and mandates one-click cancellation. The paywall and cancel flow must be compliant by design. This aligns with the calm brand, but it is now a legal requirement, not just good taste.
7. **Re-architect entitlements before adding tiers.** Replace the binary `is_pro` with a single in-code plan to capabilities map plus `require_capability` / `enforce_limit` FastAPI dependencies and a `usage_counters` table. This makes adding/changing tiers cheap and is the foundation for the AI message cap.

---

## 1. Recommended tier structure

| | **Free** | **Pro** (hero, badge "Most popular") | **Premium** (anchor) |
|---|---|---|---|
| **Price** | €0 | **€9/mo** or **€89/yr** | **€19/mo** or **€189/yr** |
| Holdings | 15 | unlimited | unlimited |
| Portfolios | 1 | 3 | unlimited |
| Sunday briefing | monthly + 1 weekly preview | full weekly briefing + email + PDF | weekly + ad-hoc on demand |
| AI assistant | 5 messages / mo | 150 messages / mo | 500 messages / mo + Opus deep-dives |
| Benchmark vs index | locked | full | full |
| Tax / FIRE / dividend | basic | full | full + scenario/what-if sandbox |
| "What changed this week" events | summary | full | full + mid-week proactive alerts |
| Alerts | - | price/concentration | + proactive mid-week |

**Why this shape:**
- **Three tiers, not two.** Stripe's own packaging guide recommends two to four tiers; three is the common sweet spot ([Stripe](https://stripe.com/resources/more/saas-pricing-and-packaging-strategy)). A higher anchor raises the reference price so Pro looks reasonable: Ariely's Economist experiment showed adding a decoy option flipped 68% to 84% choosing the bundle with no price change ([The Conversation](https://theconversation.com/the-decoy-effect-how-you-are-influenced-to-choose-without-really-knowing-it-111259)). Practitioners report a higher anchor lifting mid-tier selection (Ahrefs +23% on its middle tier, vendor anecdote) ([NovaBrandworks](https://www.novabrandworks.com/blogs/decoy-effect-price-anchoring-optimize-your-pricing-strategy)).
- **€9 stays.** Anderson & Simester's randomized field experiments found a "9" ending raised demand, in one case the higher $49 outsold $45 by ~40% ([Kellogg/SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=232542); [Springer QME](https://link.springer.com/article/10.1023/A:1023581927405)). Use charm endings on annual too (€89, €189, not €90/€190).
- **The competitor band supports it.** The mainstream EU "Pro" tracker sits around €50 to €110/yr; a power tier sits higher (see §6). €89/yr Pro lands mid-band; €189/yr Premium anchors near getquin Wealth (€149.99) and below Parqet Investor (~€330).

**Honest caveat:** a solo founder can launch with just **Free + Pro** and add Premium once there is demand for unlimited portfolios + heavier AI. The entitlements work in §7 makes adding the third tier a config change, not a rebuild. The anchor is worth adding early mainly for the conversion lift on Pro, but only if Premium carries *real* extra value (unlimited portfolios, more AI, Opus deep research). Do not ship a hollow tier, especially under the EU dark-pattern rules in §5.

---

## 2. Value metric and fences

- **Value metric: AI briefing cadence + AI message allowance.** This scales with the value a user gets, is understandable without explanation, and is hard to game, which are Stripe's tests for a good metric ([Stripe](https://stripe.com/resources/more/saas-pricing-and-packaging-strategy)).
- **Never fence core value.** Stripe warns that caps that stop a user before they reach value "feel like a punishment" and accelerate churn ([Stripe](https://stripe.com/resources/more/saas-pricing-and-packaging-strategy)). So keep single-portfolio tracking, the dashboard, and a real taste of the briefing free.
- **Good fences for Sunday (increase with delivered value):** holdings count (15 to unlimited), portfolio count (1 to 3 to unlimited), AI message allowance, briefing cadence and depth, benchmark, tax/FIRE depth, and alerts. This matches how every competitor fences (more portfolios/holdings, benchmarks, dividend/tax tools, AI volume) without gating the core tracker.

---

## 3. Trial and annual billing

**Reverse trial, no card, 14 days.** Card-required trials convert far better per signup (opt-out ~35 to 55% vs opt-in ~8 to 22%) but slash top-of-funnel and clash with a privacy-first finance brand ([Growthspree](https://www.growthspreeofficial.com/blogs/b2b-saas-trial-to-paid-conversion-rate-benchmarks-2026-by-trial-type-acv-length-credit-card)). A reverse trial (start on Pro, drop to Free) sits between freemium and trial and keeps Free as a soft landing rather than a hard wall ([Userpilot](https://userpilot.com/blog/saas-reverse-trial/)). Finance benefits from 7 to 14 day windows because value needs several sessions to land; trials under 4 days convert ~25.5% vs ~42 to 46% for 17 to 32 days ([RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026/)). Reach out a few days before the downgrade to remind users what they will lose.

**Annual, default-on, "2 months free."** Two months free is a 16.7% discount and the most common framing; the practical range is 10 to 20% ([Baremetrics](https://baremetrics.com/blog/annual-vs-monthly-pricing-better-retention)). Annual is the largest retention lever: it cuts monthly churn by roughly 60 to 80% and removes most involuntary (failed-card) churn ([Paddle](https://www.paddle.com/blog/reduce-churn); [Baremetrics](https://baremetrics.com/blog/annual-vs-monthly-pricing-better-retention)). Present a monthly/annual toggle defaulting to annual, label "2 months free" (concrete beats a percentage), and show the per-month equivalent ("€89/yr, that is €7.42/mo"). One caveat: 35% of annual cancellations cluster in month one, so the onboarding has to land ([RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026/)).

---

## 4. AI feature pricing (protecting margin)

The industry shifted away from flat-rate AI toward metered/allowance models in 2025 to 2026 because two similar requests can differ wildly in compute and "unlimited" lets heavy users consume disproportionate COGS (GitHub Copilot reportedly lost more than $20/user/month at its $10 launch price) ([Wilico](https://wilico.co.jp/en/blog/end-of-flat-rate-ai-github-copilot-llm-billing-shift)). But **do not sell raw credits to consumers**: credit pricing exposes your COGS, causes renewal bill-shock, and caps revenue at infrastructure margins ([Software Pricing Partners](https://softwarepricing.com/blog/credit-based-pricing-ai/)).

**Recommendation for Sunday:** flat tier price + a bundled monthly allowance expressed in human units ("150 AI messages/mo"), sized so the p90 user stays inside it, with a **hidden hard internal cap** to protect margin. This matches the blueprint's existing Free 5 / Pro 150 numbers (`docs/business/REVIEW_AND_PLAN.md:165-166`). The shared-market-layer caching the architecture already plans keeps the marginal cost of a Sonnet co-pilot user near $0.75 to $3/mo, so a 150-message cap is comfortably profitable.

---

## 5. Conversion, paywalls, and EU compliance

**Paywall model: soft and contextual, not a hard wall.** Timing matters more than design: showing the ask after a value moment (not at install) drove +50 to +81% lifts in case studies, and users who already felt value are up to 5x more likely to convert ([RevenueCat contextual targeting](https://www.revenuecat.com/blog/growth/contextual-paywall-targeting/)). For Sunday: deliver a few real briefings first, then surface a dismissible upgrade at a value moment.

**Cap-hit UX (the "5/5 messages" moment):** show a visible counter from the start, warn progressively (a quiet "1 left" at 4/5), and at the cap lead with what the user already got, then offer one concrete unlock with an easy dismiss ([Kinde](https://www.kinde.com/learn/billing/pricing/integrating-usage-caps-alerts-and-spend-limits-in-billing-ux/); [Apphud](https://apphud.com/blog/design-high-converting-subscription-app-paywalls)). No repeated nag pop-ups.

**Realistic targets:** plan for ~3 to 5% free to paid (fintech freemium runs ~4.1%) ([First Page Sage](https://firstpagesage.com/seo-blog/saas-freemium-conversion-rates/)). Retention is a strength: finance apps retain unusually well, and hard-paywall vs freemium retention converges after year one, which further supports the softer model ([RevenueCat 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026/)).

**EU Directive 2023/2673 (enforceable 19 June 2026) — treat as a hard requirement.** It amends the Consumer Rights and Distance Marketing of Financial Services rules and explicitly bans, for online financial services: manipulative choice architecture, repetitive confirmation pop-ups, and asymmetric UX (easy sign-up / hard cancel). It mandates a permanently accessible "cancel here" function and cancellation no harder than signup ([FairPatterns](https://www.fairpatterns.ai/post/eu-directive-on-dark-patterns-regulation-for-financial-services-500k-privacy-settlement-in-california-dfa-reverses-burden-of-proof); [European Parliament](https://www.europarl.europa.eu/thinktank/en/document/EPRS_ATA(2025)767191)). Concretely: one-click cancellation (the Stripe Customer Portal already covers this), no countdown pressure or fake scarcity, transparent limits shown up front, and no obstruction on cancel. Confirm transposition in the specific operating member state before launch.

**Paywall placements mapped to Sunday's surfaces:**

| Surface | Move |
|---|---|
| Onboarding / `/upload` | "Explore a sample portfolio" demo before any ask; holdings counter visible; if a free user imports over 15, the existing 402 upgrade message (already built) |
| Dashboard | Benchmark card already shows the Pro upgrade prompt (built); keep the data-quality/trust strip |
| Briefing | Weekly-email toggle is Pro-locked (built); after delivering a few real briefings, a dismissible contextual upgrade |
| Assistant | Live "X / 5 messages this month" counter; at the cap, value-framed single upgrade CTA |
| Billing `/billing` | Three-tier table, annual toggle default-on, "2 months free", Pro badged "Most popular", Premium shown as the anchor; one-click manage/cancel via Portal |

---

## 6. Competitor benchmark (captured 15 Jun 2026)

| App | Free | Paid tiers | Trial | Key gates |
|---|---|---|---|---|
| **Parqet** (EU) | 1 portfolio, 5 extra assets | Plus €11.99/mo (~€108/yr, 3 mo free) · Investor €29.99/mo (~€330/yr) | 14 days | X-Ray, dividend forecast, tax dashboard, benchmark, more portfolios ([parqet.com/pricing](https://parqet.com/pricing)) |
| **getquin** (EU) ⚠️ | unlimited connections, real-time | Premium €89.99/yr · Wealth €149.99/yr (AI agents) | "try free" | AI analysis, dividend KPIs, advanced analytics; *figures uncertain, page 404'd on retry; review sites cite an older ~€49.99/yr* ([getquin.com/en/pricing](https://www.getquin.com/en/pricing)) |
| **Finanzfluss Copilot** (EU) | **unlimited portfolios**, import 350+ providers | PLUS €69.99/yr (€5.83/mo) | 7 days | budgeting (multiple budgets), watchlists, enhanced analysis ([finanzfluss.de/copilot](https://www.finanzfluss.de/copilot/preise/)) |
| **Snowball Analytics** | perpetual free | Starter $79.99 · Investor $149.99 · Expert $249.99 (annual only) | 14 days, no card | unlimited holdings, benchmarking, 30y backtests, multi-portfolio ([snowball-analytics.com/pricing](https://snowball-analytics.com/pricing)) |
| **Sharesight** | 1 pf / 10 holdings | Starter ~$7/mo · Standard ~$18 · Premium ~$23 (annual) | demo only | holdings count, advanced reports, integrations ([sharesight.com/pricing](https://www.sharesight.com/pricing/)) |
| **PortfolioPilot** | unlimited net-worth tracking | Gold $240/yr · Platinum $588 · Pro $1,188 | 10 days, no card | AI assistant limited to unlimited, AI equity research, expert call ([portfoliopilot.com/pricing](https://portfoliopilot.com/pricing)) |
| **Simply Wall St** ⚠️ | limited analyses | Premium ~$120/yr · Unlimited ~$240/yr | ~14 days | company/portfolio caps; *review-site figures, official page 404'd* |
| **Copilot Money** | none | $13/mo or $95/yr (single tier) | ~1 mo | n/a, single flat tier, AI categorization included ([copilot.money](https://copilot.money)) |

**Patterns:** three to four tiers is the norm (a perpetual Free plus one to three paid steps). Almost always free: broker connect, real-time prices, one portfolio, a watchlist, CSV. Almost always gated: more portfolios/holdings (the number-one lever), benchmarks, dividend forecasting, tax tools, look-through analysis, exports, ad-free. EU mainstream "Pro" band is roughly €50 to €110/yr (~€5 to €12/mo). AI is the new top-tier upsell, gated as "limited vs unlimited" (PortfolioPilot, getquin). 14-day, no-card trials are common. *Re-verify getquin and Simply Wall St before quoting; their official pages were unstable.*

---

## 7. Entitlements architecture: what to build

Replace the binary `subscription.is_pro` with a maintainable plan to capabilities model. Build order:

**1) Single in-code capability map (the source of truth for *what a plan grants*):**

```python
# app/services/billing/catalog.py
UNLIMITED = -1
PLAN_CAPABILITIES = {
    "free":    {"features": frozenset({"briefing_basic"}),
                "limits": {"ai_messages": 5,  "portfolios": 1,  "holdings": 15}},
    "pro":     {"features": frozenset({"briefing_full","benchmark","weekly_email","pdf_export","tax_full"}),
                "limits": {"ai_messages": 150,"portfolios": 3,  "holdings": UNLIMITED}},
    "premium": {"features": frozenset({"briefing_full","benchmark","weekly_email","pdf_export","tax_full","deep_research","proactive_alerts"}),
                "limits": {"ai_messages": 500,"portfolios": UNLIMITED,"holdings": UNLIMITED}},
}
```

Every source agrees: separate billing from feature-gating, and keep capabilities in one place so packaging changes are not an engineering sprint ([Stigg](https://www.stigg.io/blog-posts/feature-gating); [Schematic](https://schematichq.com/pricing-resources/feature-gating); [WorkOS](https://workos.com/blog/enable-b2b-saas-features-for-specific-customers)).

**2) FastAPI dependencies that scale past `is_pro`:**

```python
require_capability("benchmark")     # -> 403 if feature not in plan
enforce_limit("ai_messages")        # -> 402 if monthly allowance exceeded
```

Use 403 for "your plan does not include this" and 402 for "you hit a paid usage limit", so the frontend can render an upgrade CTA distinctly ([FastAPI deps](https://fastapi.tiangolo.com/tutorial/dependencies/); [Stigg](https://www.stigg.io/blog-posts/feature-gating)).

**3) Usage metering with implicit monthly reset:**

```sql
CREATE TABLE usage_counters (
  user_id uuid, metric text, period_key text,  -- '2026-06'
  count int NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, metric, period_key)
);
-- atomic, race-safe check-and-increment:
INSERT INTO usage_counters VALUES ($1,'ai_messages',to_char(now(),'YYYY-MM'),1)
ON CONFLICT (user_id,metric,period_key)
DO UPDATE SET count = usage_counters.count + 1 RETURNING count;
```

Calendar-month `period_key` self-resets with no cron ([Neon](https://neon.com/guides/rate-limiting)). Count on AI *success*, not on request, so failed calls do not consume allowance.

**4) Stripe wiring:** tag Prices with `lookup_key` (`pro_monthly`, `pro_annual`, `premium_monthly`, ...) so prices can change without a deploy ([Stripe](https://docs.stripe.com/products-prices/manage-prices)). Map `subscription -> price.lookup_key -> plan_id`, then resolve capabilities from the in-code catalog. Keep Stripe as the source of truth for *which plan is active* and your DB as the projection. The full Stripe Entitlements API is an optional phase 2 ([Stripe Entitlements](https://docs.stripe.com/billing/entitlements); [echobind](https://echobind.com/post/leveraging-stripe-to-manage-your-saa-s-entitlements)).

**5) Webhook discipline (mostly already done):** verify signature, dedupe on `event.id`, refetch the live object, and map status to access (trialing/active grant; past_due keep during grace; unpaid/canceled revoke). Add ~2 days leeway past `current_period_end` so webhook lag never locks out a paying user ([Stripe](https://docs.stripe.com/billing/subscriptions/webhooks); [Amplified Creations](https://amplifiedcreations.com/journal/stripe-subscription-webhooks)).

**6) Pitfalls:** version plans (`pro_v1`, `pro_v2`) so grandfathered customers keep old entitlements without branching code, and time-box grandfathering to 12 to 24 months ([Stigg plan versioning](https://www.stigg.io/blog-posts/an-engineers-step-by-step-guide-to-plan-versioning); [rework](https://resources.rework.com/libraries/saas-growth/grandfathering-strategy)). Decide a downgrade-mid-period policy for usage limits (block until reset vs honor old limit to period end).

---

## 8. Open decisions for you

1. **Two tiers or three at launch?** Recommend three (Free / Pro €9 / Premium €19) for the anchor lift, but only if Premium carries real value. A 2-tier launch is defensible and cheap to extend later.
2. **Premium's contents.** Proposed: unlimited portfolios, 500 AI messages, Opus ad-hoc deep research, proactive mid-week alerts, scenario sandbox. Confirm which of these are worth building first.
3. **AI allowance numbers.** Blueprint says Free 5 / Pro 150. Confirm, and set Premium (proposed 500).
4. **Reset model:** calendar month (simple) vs billing-cycle-anchored. Recommend calendar.
5. **Annual price points:** €89 (Pro) / €189 (Premium). Confirm charm endings.

---

## Sources

**Packaging & pricing:** [Stripe packaging](https://stripe.com/resources/more/saas-pricing-and-packaging-strategy) · [Anderson & Simester $9 endings (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=232542) · [same (Springer QME)](https://link.springer.com/article/10.1023/A:1023581927405) · [Ariely decoy (The Conversation)](https://theconversation.com/the-decoy-effect-how-you-are-influenced-to-choose-without-really-knowing-it-111259) · [Baremetrics annual vs monthly](https://baremetrics.com/blog/annual-vs-monthly-pricing-better-retention) · [Wilico AI billing shift](https://wilico.co.jp/en/blog/end-of-flat-rate-ai-github-copilot-llm-billing-shift) · [Software Pricing Partners credit pricing flaws](https://softwarepricing.com/blog/credit-based-pricing-ai/) · [NovaBrandworks anchoring](https://www.novabrandworks.com/blogs/decoy-effect-price-anchoring-optimize-your-pricing-strategy)

**Conversion & paywalls:** [RevenueCat State of Subscription Apps 2026](https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026/) · [RevenueCat hard vs soft paywall](https://www.revenuecat.com/blog/growth/hard-paywall-vs-soft-paywall/) · [RevenueCat contextual targeting](https://www.revenuecat.com/blog/growth/contextual-paywall-targeting/) · [Kinde usage caps UX](https://www.kinde.com/learn/billing/pricing/integrating-usage-caps-alerts-and-spend-limits-in-billing-ux/) · [Growthspree trial benchmarks](https://www.growthspreeofficial.com/blogs/b2b-saas-trial-to-paid-conversion-rate-benchmarks-2026-by-trial-type-acv-length-credit-card) · [First Page Sage freemium rates](https://firstpagesage.com/seo-blog/saas-freemium-conversion-rates/) · [Userpilot reverse trial](https://userpilot.com/blog/saas-reverse-trial/) · [Paddle reduce churn](https://www.paddle.com/blog/reduce-churn) · [FairPatterns EU directive](https://www.fairpatterns.ai/post/eu-directive-on-dark-patterns-regulation-for-financial-services-500k-privacy-settlement-in-california-dfa-reverses-burden-of-proof) · [European Parliament dark patterns](https://www.europarl.europa.eu/thinktank/en/document/EPRS_ATA(2025)767191)

**Competitors:** [Parqet](https://parqet.com/pricing) · [getquin](https://www.getquin.com/en/pricing) · [Finanzfluss Copilot](https://www.finanzfluss.de/copilot/preise/) · [Sharesight](https://www.sharesight.com/pricing/) · [Snowball](https://snowball-analytics.com/pricing) · [PortfolioPilot](https://portfoliopilot.com/pricing) · [Copilot Money](https://copilot.money)

**Entitlements:** [Stripe lookup_key](https://docs.stripe.com/products-prices/manage-prices) · [Stripe Entitlements](https://docs.stripe.com/billing/entitlements) · [Stripe subscription webhooks](https://docs.stripe.com/billing/subscriptions/webhooks) · [echobind entitlements](https://echobind.com/post/leveraging-stripe-to-manage-your-saa-s-entitlements) · [Amplified Creations webhooks](https://amplifiedcreations.com/journal/stripe-subscription-webhooks) · [Stigg feature gating](https://www.stigg.io/blog-posts/feature-gating) · [Schematic](https://schematichq.com/pricing-resources/feature-gating) · [Neon rate limiting](https://neon.com/guides/rate-limiting) · [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
