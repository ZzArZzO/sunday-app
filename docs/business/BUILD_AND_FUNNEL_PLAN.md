# Build & Funnel Plan — Sunday first, New Investor as the funnel

*Drafted: 2026-07-18 · A sequencing plan, grounded in the actual state of both codebases. Not legal advice.*

## The strategy in one line

**Finish and launch Sunday (the paid product) to a first paying customer. Prove people pay and the weekly ritual retains. *Then* build New Investor as the free top-of-funnel that manufactures Sunday's ideal customer.** Start the shared newsletter now, in parallel, because it is nearly free and compounds weekly.

Rationale (short version): New Investor's only job is to funnel people *into* Sunday. A funnel with no working destination is wasted motion. Sunday is ~90% built and is the only thing that answers the one question that matters — *will people pay?* Education validates "will people sign up for free," which you can already assume.

---

## Part 1 — What to build first: Sunday to the first euro

### Where Sunday actually is (verified against the code, not the stale STATUS.md)

`master` (HEAD `dc80b11`) has already advanced past `docs/STATUS.md` (dated 2026-06-29):

- ✅ **Billing rails on master** — `api/app/services/billing/` (`checkout`, `portal`, `subscription`, `webhooks`, `client`, `budget`) + `routes/billing.py`. Test-mode-safe (503 without keys). Stripe state on the `User` model.
- ✅ **Supabase Auth on master** — migrated off magic-link; Bearer-JWT verification against JWKS. (Docs still say magic-link — they lag the code.)
- ✅ **Legal page scaffolds exist** — `web/app/{privacy,terms,impressum}/page.tsx`.
- ✅ **Core loop, cost ledger + budget cap, mobile Builds 1–5, ~180 backend tests, CI→Hetzner deploy.**

So the remaining gap to charging a customer is **finishing, not building**.

### The launch-readiness gap (the real blockers)

| # | Blocker | Why it gates revenue | State |
|---|---|---|---|
| B1 | **Stripe live round-trip** | Can't take money without it | Rails done; create real Product/Price, restricted key, webhook secret, run Checkout→webhook once with `4242…` |
| B2 | **Production email (verified Resend domain)** | The weekly briefing email **is the product** — dry-run means nothing actually sends | Sender built; needs a verified domain |
| B3 | **Scheduler single-instance pin + weekly idempotency** | Duplicate/again-sent briefings on cloud = trust-killer | Idempotency guard committed on `feat/weekly-idempotency-seed-fix` (not merged); pin still open |
| B4 | **Branch reconciliation** | Features + fixes live on diverged branches | Land features → `master`, then fold in the idempotency fix |
| B5 | **Legal content + DPAs** | Charging EU consumers for a finance product | Page scaffolds exist; need real reviewed copy, Anthropic EU DPA, Stripe DPA, Impressum filled (founder is **NL-based** now — docs still say PT in places) |
| B6 | **Deploy target confirmed live** | Need a public URL to sell | CI SSH-deploys to Hetzner; confirm the box is provisioned + domains resolve |

Everything else in `docs/ROADMAP.md` Phase 3–5 (passkeys, 5-country tax engine, briefing history, live crypto connectors, AI features #2–12) is **post-launch**. Do not let it block the first euro.

### Sunday build sequence

- **M0 — Reconcile branches (B4).** Get billing + cost-ledger + mobile + the idempotency fix cleanly onto `master`. One deliberate merge pass. Nothing else lands until this is clean.
- **M1 — Money works (B1).** Live Stripe: one Product, `pro_monthly` (€9) + `pro_annual` (€89) Prices tagged with `lookup_key`, restricted key, webhook secret, one real Checkout→webhook→access-granted round-trip. Ship **Free + Pro only** (skip the Premium anchor for v1 — add it once there's demand for unlimited portfolios/AI).
- **M2 — The product actually delivers (B2 + B3).** Verified Resend domain so real briefings send; scheduler pinned to one always-on instance with the idempotency guard live. Send yourself a real Sunday briefing end-to-end on a schedule.
- **M3 — Legal + deploy to sell (B5 + B6).** Privacy/ToS/Impressum reviewed and filled (NL Impressum, not PT); Anthropic + Stripe DPAs executed; public URL live and stable; EU dark-pattern compliance on the cancel flow (Stripe Portal already gives one-click cancel — Directive 2023/2673 is enforceable from 19 Jun 2026).
- **M4 — Onboarding that lands the first month.** Your retention research says **35% of annual churn happens in month 1** and **AI novelty accelerates churn** — so retention rides on the *ritual*, not the AI. Nail: upload → first genuinely good briefing in <2 min; a working **sample briefing** (uses `sample-tr.csv`) for people without a portfolio yet; the **14-day no-card reverse trial** (start on Pro, drop to Free).

**Exit criteria for Part 1:** a stranger can sign up on a public URL, upload a CSV, get a real emailed Sunday briefing, and pay €9 — and you can see the first month's retention. That is the moment New Investor becomes worth building.

---

## Part 2 — The funnel: New Investor → Sunday

### The problem you must design around

The two products serve **different user states**:

- **New Investor** = someone who *hasn't invested yet* ("before you risk a single euro").
- **Sunday** = someone who *already holds a portfolio* to import via CSV.

A learner on Lesson 2 has nothing to import. **You can't funnel on day one — you funnel at the moment a learner becomes an investor.** The upside: a nervous beginner who just made their first investment and doesn't understand their own holdings is *exactly* Sunday's ideal customer. **Education manufactures perfectly-timed, pre-qualified Sunday leads.**

### The spine: "The Sunday Read" newsletter (already scaffolded)

You already have the connective tissue half-built:

- Sunday's `docs/business/NEWSLETTER_LAUNCH_KIT.md` = a ready Beehiiv publication, **The Sunday Read** (`thesundayread.beehiiv.com`).
- New Investor's `phase-0-launch-kit.md` checklist already says *"Add the 'Get the Sunday Read' CTA to the app landing page + waitlist."*
- Sunday's retention research names the newsletter *"the top-of-funnel reservoir"* and *"soft landing."*

The newsletter solves **timing** — the #1 funnel problem. A learner isn't Sunday-ready the day they sign up, but may be in three months when they open a brokerage account. The newsletter holds them, keeps the brand warm weekly, and pulls them into Sunday when they finally have holdings. **Route both the New Investor waitlist and Sunday's marketing site into this one list.**

### The three handoff moments (mapped to things already written)

| Trigger | Where it lives | The offer |
|---|---|---|
| **1. "See what a briefing looks like"** | Archetype result screen + capstone Lesson 9 | A public **sample Sunday briefing** (`sample-tr.csv`) — no portfolio required. Lets a not-yet-invested learner *feel* the product. |
| **2. "You just made your first investment"** | After **Lesson 5** (open account, first order) | Highest-intent moment in the funnel. Behavior-triggered email: *"Now that you own something, here's how to keep track of it without obsessing."* → Sunday + reverse trial. |
| **3. "This is the habit"** | Capstone **Lesson 9** (when to check your portfolio, rebalancing, core+satellite) | Lesson 9 literally teaches the behavior Sunday automates. End it: *"Sunday does this for you, every Sunday."* |

### The one technical link worth building: shared Supabase auth + archetype carryover

Sunday already uses **Supabase Auth**. If New Investor authenticates against the **same Supabase project**, a learner becomes a Sunday user in one click — and their **archetype pre-configures Sunday** (a Cautious Starter's risk framing / target allocation carries over). That turns a cold signup into a warm, personalized upgrade. This is the *only* place a real "merge" pays off — keep the two codebases separate otherwise (different stacks, and separation keeps New Investor's affiliate/RIS regulatory surface away from Sunday's clean posture).

### The compliance guardrail on the handoff (non-negotiable)

Keep the cross-sell **editorial**. "See a sample briefing" / "a calm tool to track your portfolio" = fine. "You're a Steady Builder, so buy X and track it on Sunday" = MiFID II personalized advice — the exact line both compliance docs draw. The archetype may *pre-fill* Sunday's settings; the copy stays "here's a tool," never "here's what to buy."

---

## Part 3 — The overall sequence

```
NOW (parallel, cheap)   →  Launch "The Sunday Read" newsletter. Point BOTH waitlists at it.
                           It's the only asset with time-value; every week late is lost list growth.

BUILD FIRST (Sunday)    →  M0 reconcile → M1 money works → M2 delivery works →
                           M3 legal + deploy → M4 onboarding/trial.  Ship Free + Pro (€9/€89).

VALIDATE                →  Strangers pay. Watch month-1 retention + weekly briefing
                           click/return (not raw opens). Prove the ritual sticks.

BUILD SECOND (funnel)   →  New Investor as the funnel into PROVEN Sunday:
                           run the Phase-0 demand test (tracker is still empty),
                           wire the sample-briefing CTA + post-Lesson-5 trigger,
                           then shared Supabase auth + archetype carryover.
```

**Do not split focus across two half-built products.** Get one thing generating revenue, prove the unit economics, then build the acquisition machine that pours into it.

---

## Part 4 — What to measure

- **Sunday (revenue):** free→Pro conversion (target ≥4%), **month-1 retention** (where annual churn concentrates), annual mix %, blended monthly churn (<5%), briefing **click/48h-return** (the real ritual signal — raw open rate is inflated by Apple MPP).
- **Funnel (the handoff):** UTM every cross-property CTA. Track `Lesson-5-completers → Sunday`, **not** `all-signups → Sunday` (most learners never invest — that's fine; the newsletter monetizes/retains them indirectly). Track which **pillar** and **archetype** convert best (Curious Diversifiers who hold crypto are likely the strongest Sunday fit — messiest portfolios).

---

## Part 5 — What NOT to do now

- ❌ Don't try to charge for New Investor. Its subscription case is weak (finite content, most price-sensitive buyers) — it's an acquisition layer, not a revenue product.
- ❌ Don't merge the repositories. Different stacks/stages; separation protects Sunday's compliance posture. Connect them via newsletter + shared auth, not a monorepo.
- ❌ Don't gate Part 1 on Phase 3–5 features (passkeys, 5-country tax, live crypto connectors, AI #2–12). They're post-launch.
- ❌ Don't lead retention on the AI. The 2026 data says AI novelty *accelerates* churn; the calm weekly ritual + correct numbers + annual plans are what hold users.
