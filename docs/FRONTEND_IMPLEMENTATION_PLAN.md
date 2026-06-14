# Frontend Implementation Plan

*Concrete, file-level plan to turn the UX research (`docs/business/FRONTEND_UX_RESEARCH.md`) into shipped frontend changes, grounded in the actual `web/` codebase.*

**Date:** June 2026
**Scope:** The four surfaces — Briefing (`BriefingView.tsx`), Dashboard (`app/dashboard/page.tsx` + cards), Onboarding (`CsvUploader.tsx`), AI chat (`ChatPanel.tsx`) — plus shared concerns (EU formatting, colorblind-safe palette, trust cues).
**Posture (non-negotiable):** strict non-advice (describe/explain only); calm/signal-not-noise; deterministic numbers stay deterministic, AI only writes prose; no heavy new dependencies without justification.

---

## 0. Current state (corrected from the stale review)

The frontend is further along than `REVIEW_AND_PLAN.md` implies. Verified against source:

| Thing | Actual state | Implication for this plan |
|---|---|---|
| Week-over-week | **Wired.** `BriefingResponse` has `wow_available` + `wow_baseline_date`; `BriefingView` already renders a graceful "starts once your history builds" fallback (`BriefingView.tsx:33-56`). | No frontend work to *display* WoW. Backend still owes real snapshot history. |
| Live prices | **Endpoint exists.** `refreshPrices()` → `/api/prices/refresh`, `RefreshPricesButton` on the dashboard, `last_price_eur` on `PositionView`. | "Refresh prices" UX exists; polish only. |
| Holdings table | Already has ticker/class/qty/avg-cost/value/**P&L**/**weight** + color + sign (`PortfolioTable.tsx`). | No new columns needed; dataviz + a11y polish only. |
| Chat | Built: thread, optimistic send + rollback, 4 ungrouped suggestion chips, static disclaimer (`ChatPanel.tsx`). `ChatResponse` already carries `disclaimers[]` + `guardrail_triggered` — **but the UI ignores both.** | Frontend-only wins available immediately. |
| Money formatting | `lib/format.ts` uses **`en-IE`** → renders `€1,234.56`, **not** German `1.234,56 €`. Locale is hardcoded, not user-driven. | Direct, well-scoped fix. |
| Design tokens | CSS-variable tokens (`--positive`/`--negative` → Tailwind `positive`/`negative`), dark mode via `.dark` class, Geist fonts (`tailwind.config.ts`, `globals.css`). | Colorblind palette = swap CSS vars + add non-color cues. |
| Charts | **None.** Allocation is a 4-card %-grid (`dashboard/page.tsx:80-90`); all visuals are hand-rolled SVG/divs. No chart lib in deps. | Decision point below (§3). |

**Net:** the "fix the lies" work is mostly backend (real prices/FX/WoW-history, CSV sells handling). The *frontend* work is **presentation polish + a few targeted additions**, much of it shippable without any backend change.

---

## 1. Two scope buckets

Because the request is a *frontend* plan, tasks are split by whether they need a backend contract change:

- **Track 1 — Frontend-only.** Ship today against the existing API. No backend dependency.
- **Track 2 — Needs a backend contract.** Frontend is ready once a named endpoint/field lands; the proposed contract is specified so backend work can run in parallel.

---

## 2. TRACK 1 — Frontend-only (ship now)

### T1.1 — EU locale formatting *(S)*
**Why:** Research — DE expects `1.234,56 €`; current `en-IE` is wrong for the beachhead. ([report §3](business/FRONTEND_UX_RESEARCH.md))
**Files:** `lib/format.ts`, new `lib/locale.ts`; thread a `country`/`locale` value from `PortfolioResponse`/`BriefingResponse` (add `country` to those schemas — *tiny* backend touch, or read from a user setting already present).
**Changes:**
- Replace the module-level singletons with locale-aware factories: `makeEur(locale)`, `makePct(locale)`. Map `DE→de-DE`, `PT→pt-PT`, fallback `en-IE`.
- Keep `formatDual` but switch from `"€X / $Y"` to ISO-coded when mixing (`1.234,56 € · $1,299.99`) per the "use ISO codes when mixing currencies" finding.
- **pt-PT is unverified in research** — drive it through `Intl.NumberFormat('pt-PT', …)` and add a unit test asserting actual output; do not hand-format.
**Acceptance:** a DE user sees `1.234,56 €`; a PT user sees the `Intl` pt-PT output; unit tests cover both + percent.
**Risk:** locale must be available client-side; if it's only on the user row, expose it on the portfolio/briefing payloads (one field).

### T1.2 — Colorblind-safe gains/losses + non-color cues *(S)*
**Why:** ~8% of men can't distinguish red/green; use blue/orange + always pair color with a sign/arrow. ([report §3](business/FRONTEND_UX_RESEARCH.md))
**Files:** `app/globals.css` (the `--positive`/`--negative` CSS vars), audit every `text-positive`/`text-negative`/`bg-*-subtle` site.
**Changes:**
- Repoint `--positive` to an accessible **blue** and `--negative` to **orange** (keep `--warn` distinct); tune light + dark. One-line-per-token change re-themes the app via existing token system.
- Ensure color is never the *only* signal: `PortfolioTable` and dashboard hero already add `+`/`−`; add a directional arrow (reuse `TrendIcon` from `BriefingView`) to P&L cells and the dashboard "Unrealised" stat. `ConcentrationCard` severity already pairs a dot with a text label ✓.
**Acceptance:** Chrome DevTools "emulate vision deficiency: deuteranopia" — gains/losses remain distinguishable by hue *and* by sign/arrow; contrast ≥4.5:1.

### T1.3 — Chat: surface what's already in the payload *(S)*
**Why:** `ChatResponse.disclaimers[]` and `guardrail_triggered` exist but are dropped; specific, placed disclosure beats a static footer; AI-disclosure should be at first interaction. ([report §2.4](business/FRONTEND_UX_RESEARCH.md))
**Files:** `ChatPanel.tsx`.
**Changes:**
- Render `res.disclaimers` from the response (fallback to the static line) instead of the hardcoded `Disclaimer extra`.
- When `guardrail_triggered`, show a subtle neutral chip on that assistant bubble: "Reframed to stay information-only." (honest, builds trust).
- Add a persistent "**AI assistant** · information, not advice" label in the panel header (first-interaction disclosure, AI Act Art. 50), and move the specific non-advice microcopy to sit **directly under the input box**.
**Acceptance:** triggering a guardrail (ask "should I sell NVDA?") shows the reframe chip; disclosures come from the response; AI label visible before first message.

### T1.4 — Chat: grouped starter chips + follow-up chips *(S/M)*
**Why:** group ~3–6 starters by function; offer follow-up suggestions after answers (NN/g). ([report §2.4](business/FRONTEND_UX_RESEARCH.md))
**Files:** `ChatPanel.tsx`.
**Changes:**
- Group the existing `SUGGESTIONS` under labels: **Understand my portfolio** / **Explain a concept** / **This week** (2 each).
- After each assistant reply, render 2–3 static follow-up chips ("Explain that more simply", "How is this calculated?", "What does this mean for risk?") that submit on click. (Static now; dynamic follow-ups = Track 2.)
**Acceptance:** empty state shows grouped chips; every answer is followed by clickable follow-ups.

### T1.5 — Allocation visualization (hand-rolled, zero-dep) *(M)*
**Why:** replace the flat 4-card %-grid; show allocation as a glanceable bar/segment; treemap deferred (needs lib). ([report §2.2](business/FRONTEND_UX_RESEARCH.md))
**Files:** new `components/AllocationBar.tsx`; use in `dashboard/page.tsx` (consumes existing `asset_class_split`).
**Changes:**
- A single horizontal 100%-stacked SVG/flex bar segmented by asset class, with a legend (class · %), colorblind-safe palette, hover/`title` for exact %. Keep the numeric cards as the legend or below.
- This is the "top-level stocks-vs-crypto donut/bar" the research endorses; the per-holding **treemap/heatmap** is T2.4.
**Acceptance:** allocation renders as one calm bar + legend; works with 1–6 classes; accessible (`role="img"` + `aria-label` summarizing the split).

### T1.6 — "Show your work" trust strip *(S/M)*
**Why:** the #1 category trust-killer is numbers that don't reconcile; "data as of" + "what's estimated" stamps directly counter it. ([report §1.3, §2.2](business/FRONTEND_UX_RESEARCH.md))
**Files:** new `components/DataQualityNote.tsx`; use on dashboard + briefing.
**Changes:**
- A compact strip: "Prices as of {as_of} · {priced}/{total} holdings live, {unpriced} at cost basis · EUR/USD {rate} ({source})." Pull from `PortfolioResponse` + `PriceRefreshResponse` (already typed).
- When `eur_usd_source === "placeholder"` or unpriced > 0, say so plainly. Honesty here is the differentiator.
**Acceptance:** dashboard shows live-vs-cost-basis counts and FX source; nothing claims "live" when it's a placeholder.

### T1.7 — Onboarding: demo-to-yours + loud dropped-row reporting *(M)*
**Why:** time-to-first-value; and *silent* row-dropping is the reconciliation trap. ([report §2.3](business/FRONTEND_UX_RESEARCH.md))
**Files:** `CsvUploader.tsx`, `app/upload/page.tsx`.
**Changes:**
- **Demo-to-yours:** a secondary "Explore a sample portfolio first" button that routes to the dashboard seeded with sample data (uses existing `sample-tr.csv`/seed; needs a tiny "load sample" affordance — if no API, link to dashboard which already shows seeded data in dev).
- **Loud reporting:** the success panel already shows `warnings` in a collapsed `<details>`. Promote *dropped/unparsed rows* to a visible count ("12 rows imported · **3 rows skipped (sells/dividends not yet supported)**") so users aren't silently misled. (Backend already returns `warnings`; if it doesn't yet itemize skipped types, that's a Track-2 enrichment.)
- Replace the slightly-misleading "We read position rows and discard everything else" with honest, specific copy.
**Acceptance:** uploading a TR CSV with sells shows a visible "rows skipped" count, not a silent success.

### T1.8 — Briefing calm polish + per-section visual slots *(M)*
**Why:** digest length, "what changed → what it means", visuals beside prose, one hero number. ([report §2.1](business/FRONTEND_UX_RESEARCH.md))
**Files:** `BriefingView.tsx`, `SectionBlock`.
**Changes:**
- Add an optional visual slot to `SectionBlock`: if `section.data` carries a small series (e.g. `data.spark: number[]`), render a tiny hand-rolled SVG sparkline beside the prose; otherwise prose-only. (Renders nothing until backend supplies `data.spark` — safe no-op now, ready for Track 2.)
- Tighten vertical rhythm/section caps for the "3-minute read" feel; keep the existing oversized hero (good) but wire the trust strip (T1.6) under it.
**Acceptance:** sections with a `spark` array show a sparkline; layout reads as a short digest; no console errors when `data` is null.

---

## 3. Charting decision (blocks T2.x dataviz)

**Recommendation: stay zero-dep for bars/sparklines (hand-rolled SVG); add one small lib only for the treemap + benchmark line.**
- Hand-rolled SVG covers AllocationBar (T1.5) and section sparklines (T1.8) at ~0 KB and matches the existing hand-rolled-SVG style.
- For the per-holding **treemap** (T2.4) and **benchmark overlay** (T2.1), hand-rolling is fiddly. Prefer a lightweight, tree-shakeable option — **`visx`** (pick only `@visx/shape`/`@visx/scale`/`@visx/hierarchy`) or **Tremor** if you want batteries-included calm-styled charts. Avoid Recharts/Chart.js (heavier, harder to make "calm").
- **Open decision for the user:** zero-dep-everything (more dev time, smallest bundle) vs. add `visx`/Tremor (faster, ~tens of KB). Defaulting to **visx for treemap+line, hand-rolled for the rest** unless told otherwise.

---

## 4. TRACK 2 — Needs a backend contract (frontend ready on arrival)

### T2.1 — Benchmark overlay *(L, cross-stack)* — highest-value addition
**Backend contract needed:** `GET /api/benchmark?index=msci_world|sp500` → `{ index, currency, series: [{date, portfolio_twr_pct, index_twr_pct}], summary: {portfolio_pct, index_pct, diff_pct, diff_eur} }`. Requires portfolio TWR history + an index series (depends on snapshot history — the same backend prerequisite as real WoW).
**Frontend:** new `components/BenchmarkChart.tsx` on the dashboard (and a briefing section) — a calm line chart (portfolio vs index, TWR), default **MSCI World** for EU, S&P 500 secondary; a compact table showing % **and** € difference; optional "what if I'd bought the index" counterfactual line. Frame as insight, **not** a win/lose scoreboard. Label MWR (headline return) vs TWR (benchmark) in plain words.
**Acceptance:** toggle MSCI World/S&P 500; chart + diff table; honest "not enough history yet" empty state.

### T2.2 — Chat grounding panel *(M, cross-stack)*
**Backend contract:** add `grounding` to `ChatResponse` — e.g. `{ as_of, holdings_used: [{ticker, weight_pct}], facts: string[] }` (the backend already builds this snapshot in `portfolio_context.py`; expose a compact form).
**Frontend:** a collapsible "Based on your portfolio as of {date}" panel under each assistant answer showing the figures it used; inline source/as-of labels. This is the single highest-leverage *trust* move for the chat.
**Acceptance:** every grounded answer can reveal the exact holdings/figures used.

### T2.3 — Chat streaming *(M, cross-stack)*
**Backend contract:** an SSE/stream variant of `/api/chat` (the route is currently sync). 
**Frontend:** consume the stream, render tokens progressively, keep a "disable streaming" toggle for accessibility; preserve the existing rollback-on-error behavior.
**Acceptance:** answers stream; toggle works; errors still roll back the optimistic turn.

### T2.4 — Per-holding treemap/heatmap *(M, frontend-led)*
**Backend:** none (uses existing `positions` + `weight_pct`); optional daily-change field to color the heatmap.
**Frontend:** `components/AllocationTreemap.tsx` (visx hierarchy) — tiles sized by weight, optionally colored by daily move; "spot overexposure at a glance." Complements T1.5 (bar = top-level, treemap = per-holding).
**Acceptance:** treemap renders for 10–30 holdings; accessible table fallback.

### T2.5 — CSV preview + column mapping + row-level repair *(L, cross-stack)*
**Backend contract:** `POST /api/ingest/preview` (parse only) → `{ detected_format, columns: [{source, mapped_to, confidence, sample}], rows: [{...parsed, status, error}] }`; then confirm to commit.
**Frontend:** upgrade `CsvUploader` to the wizard (`Upload → Map → Validate → Confirm`): show auto-detected mapping with confidence dots + sample values; "show only error rows" toggle; inline fix-without-re-upload. This is the gold-standard import UX; current uploader is a single-shot post.
**Acceptance:** a malformed TR CSV surfaces per-row errors and lets the user fix inline before committing.

### T2.6 — "What changed this week" + section charts *(L, cross-stack)*
**Backend:** the real shared-market layer + per-holding news/events (Sprint 1–2 in `REVIEW_AND_PLAN.md`) feeding `section.data` (incl. `spark` series + event list).
**Frontend:** already prepared by T1.8's visual slot; add an events list renderer for the `what_changed` section. Mostly backend-gated.

### T2.7 — EU tax-context cards + crypto holding-period clock *(M, cross-stack)*
**Backend:** per-lot acquisition dates → days-to-1-year for crypto; the tax engine already exists (`tax_summary.py`).
**Frontend:** extend `TaxCard` with an informational "crypto 1-year clock" per lot and Sparerpauschbetrag/Teilfreistellung context cards — each with the standing "not tax advice" line. Pure information; compliant.

---

## 5. Sequencing

```
Phase A (Track 1, no backend): T1.1 locale · T1.2 a11y palette · T1.3 chat payload · T1.4 chips
                               · T1.5 allocation bar · T1.6 trust strip · T1.7 onboarding · T1.8 briefing polish
   ↓  (ship as one "calm + trust + EU" frontend release)
Phase B (Track 2, parallel with backend):
   backend snapshot history ──► T2.1 benchmark (flagship)
   expose portfolio_context ──► T2.2 grounding ─┐
   SSE chat route          ──► T2.3 streaming  ─┴► chat trust release
   (frontend-led)          ──► T2.4 treemap
   ingest/preview endpoint ──► T2.5 import wizard
   what-changed pipeline   ──► T2.6 + T1.8 slots
   per-lot dates           ──► T2.7 tax clock
```

Phase A is independently shippable and delivers most of the research's "calm + trust + EU" value. Phase B items unlock as their named backend contracts land — none block each other.

---

## 6. Shared scaffolding to build first
- `lib/locale.ts` — locale resolution + `Intl` factories (unblocks T1.1, used everywhere).
- Colorblind palette tokens in `globals.css` (unblocks T1.2).
- A tiny `components/Sparkline.tsx` + `components/AllocationBar.tsx` SVG primitive (reused by T1.5, T1.8, later cards).
- `components/DataQualityNote.tsx` (T1.6, reused on dashboard + briefing).

## 7. Testing
- **Unit (add Vitest or rely on tsc + a small harness):** `lib/locale.ts`/`format.ts` — assert `de-DE` and `pt-PT` outputs; pct signs.
- **Playwright e2e** (per repo testing rules) for the three critical flows: upload→dashboard, briefing render with/without WoW, chat send + guardrail reframe.
- **a11y check:** axe pass on dashboard/briefing; manual deuteranopia emulation for T1.2.

## 8. Decisions for the user
1. **Charting:** zero-dep everywhere, or add `visx`/Tremor for treemap+benchmark? (Default: visx for those two, hand-rolled for bars/sparklines.)
2. **Backend scope:** is Track 2's small contract work in scope now, or is this a frontend-only release (Phase A) with Track 2 as a follow-up? (Default: ship Phase A now, schedule Track 2.)
3. **Locale source:** expose `country`/`locale` on the portfolio/briefing payloads, or is a user-settings fetch already available client-side? (Needed for T1.1.)
4. **German formatting now or post-localization?** Recommend now — it's cheap and the beachhead is DE.
```
```
