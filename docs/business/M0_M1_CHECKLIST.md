# Sunday — M0–M1 Execution Checklist

*Drafted: 2026-07-18 · Companion to `BUILD_AND_FUNNEL_PLAN.md`. Grounded in the actual state of `sunday-app` master (`dc80b11`), not the stale `docs/STATUS.md`.*

## Key finding — M0 is essentially already done

Fetched the full history and computed merge status: **every feature branch is merged into `master`.** `docs/STATUS.md` (dated 2026-06-29) is badly stale — it describes work as "in flight on branches" that has since all landed. Master already contains: Supabase auth, billing rails, mobile Builds 1–5, the **weekly idempotency guard** (`briefing_delivery.py` claims a `(user_id, iso_week)` row; migration `0011_weekly_deliveries`), eurozone tax, multi-source connectors, deploy-hardening, and filled legal pages.

So there is **no branch reconciliation left**. The first real work is M1 (Stripe).

---

## M0 — Reconcile & baseline (mostly done)

- [x] ~~Land billing / mobile / auth / idempotency onto master~~ — **already merged**
- [ ] **Confirm master is green** — one clean run on a known-good base:
  - `cd api && pytest` → expect ~180 passing
  - `cd web && npx tsc --noEmit` → clean
- [ ] **Kill the stale docs** (this is a real task — the stale STATUS.md causes wasted re-analysis):
  - Update `docs/STATUS.md`: everything is on master; auth is **Supabase**, not magic-link.
  - Update `docs/ROADMAP.md` to match reality.
- [ ] **Delete the merged feature branches** on GitHub (all are ancestors of master now) to remove the "diverged branches" illusion.

---

## M1 — Money works (Stripe live round-trip)

Rails are complete on master. Env contract (from `api/app/config.py` + `.env.example`):

```
STRIPE_API_KEY=          # restricted key (rk_…); client.py warns if not rk_
STRIPE_WEBHOOK_SECRET=   # whsec_…
STRIPE_PRICE_PRO=        # price_… for €9/mo
APP_BASE_URL=            # builds checkout success/cancel URLs
```

Relevant code touchpoints:
- `api/app/services/billing/checkout.py` — `create_checkout_session`; **sets `automatic_tax={"enabled": True}`** and `customer_update` (address auto).
- `api/app/services/billing/webhooks.py` — verifies signature; handles `customer.subscription.{created,updated,deleted}`.
- `api/app/services/billing/subscription.py` — `PRO_STATUSES = {active, trialing}`, `FREE_HOLDINGS_CAP = 15`.
- `api/app/routes/billing.py` — routes under prefix `/api/billing` (webhook path is `/api/billing/webhook`).

### M1a — Test-mode round-trip (validate the rails)

- [ ] Create a Stripe account; stay in **Test mode**.
- [ ] Create Product "Sunday Pro" with a **€9/mo recurring Price** → copy `price_…` into `STRIPE_PRICE_PRO`.
- [ ] Restricted **test** key (`rk_test_…`) → `STRIPE_API_KEY`.
- [ ] `stripe listen --forward-to localhost:8000/api/billing/webhook` → paste the `whsec_…` into `STRIPE_WEBHOOK_SECRET`.
- [ ] ⚠️ **Gotcha — Stripe Tax:** `checkout.py` enables `automatic_tax`, so Checkout **errors** unless Stripe Tax is enabled with ≥1 registration. Either enable Stripe Tax + register NL, or temporarily comment out `automatic_tax`/`customer_update` for the first smoke test, then re-enable.
- [ ] Round-trip: sign in → `POST /api/billing/checkout` → pay with `4242 4242 4242 4242` (any future expiry/CVC) → confirm `customer.subscription.created` fires and `apply_subscription` flips `User.subscription_status` to `active`.
- [ ] Verify gates: `GET /api/billing/subscription` → `is_pro: true`; Free 15-holdings cap lifts. Cancel via Portal (`POST /api/billing/portal`) → `customer.subscription.deleted` revokes access.

### M1b — Two small code adds worth doing in M1

- [ ] **Annual price (€89/yr).** Checkout wires only a single `STRIPE_PRICE_PRO`. Annual is the #1 retention lever (pricing research: cuts monthly churn 60–80%). Add a second Price + a `plan`/`interval` param on `create_checkout_session` so `/billing` offers a monthly/annual toggle.
- [ ] **14-day reverse trial.** `PRO_STATUSES` already includes `trialing`, so plumbing supports it — add `subscription_data={"trial_period_days": 14}` in `checkout.py`. One line; it's the lever M4 onboarding depends on.

### M1c — Live mode (rides with the M3 deploy)

- [ ] Live restricted key (`rk_live_…`), live €9 + €89 Prices.
- [ ] **Dashboard webhook endpoint** on the public URL, subscribed to `customer.subscription.{created,updated,deleted}` → live `whsec_…`.
- [ ] Complete Stripe Tax registration + execute the **Stripe DPA** (on `LEGAL.md` pre-launch checklist).

**M1 exit criteria:** a test user subscribes, the webhook flips them to Pro, gates open, and cancel revokes — end to end, signature-verified.

---

## Open dependency to confirm early

Whether the **Hetzner box + domains are actually provisioned** (CI SSH-deploys to it, but that can't be verified from the repo). This is the gate between M1a (works locally) and M1c (can sell). Confirm before scheduling the live cutover.
