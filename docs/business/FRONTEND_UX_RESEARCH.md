# Sunday App — Frontend / UX Research

*What self-directed EU retail investors want in the frontend of a portfolio-briefing + tracking web app, and where the competitive UX gaps are that Sunday can own.*

**Date:** June 2026
**Method:** Multi-source web research (WebSearch + WebFetch) across four parallel streams — competitor UX love/hate, onboarding+dashboard dataviz, briefing+AI-chat presentation, and EU/trust/mobile/a11y/trends. ~80 sources reviewed; ~55 cited below.
**Scope:** Sunday's four frontend surfaces — the weekly **Briefing**, the **Dashboard & holdings**, **Onboarding / CSV upload**, and the **AI chat assistant** — for the committed DE/PT FIRE+dividend beachhead (stocks + crypto, manual-CSV, no broker login, web/PWA first, strict MiFID II/MiCA non-advice posture).
**Confidence:** Medium-high overall. Strongest on competitor patterns, calm-design, import UX, citations/trust, EU formatting, push/a11y. Weakest on raw EU forum/Reddit voice (US-biased crawler; Reddit/Trustpilot bodies frequently blocked) and on email-vs-in-app open-rate comparisons. Single-source/vendor claims are flagged inline.

---

## 0. Executive summary

The research converges on one thesis: **in this category the interface, not the data, is where trust is won or lost — and almost every incumbent loses it the same way.** Across Parqet, getquin, Delta, Snowball, Finanzfluss Copilot and Simply Wall St, the single most damaging, most-repeated complaint is **numbers that don't reconcile** (graph P/L ≠ portfolio P/L, prices that don't match transactions, positive ETFs shown as negative). The second is **clutter** — "overwhelming when I just want to see how I'm doing." The third is **creeping/hidden paywalls**, and the fourth is **import friction**.

Every one of those four is a direct opening for a *calm, briefing-first, "shows-its-work," manual-first* product — which is exactly Sunday's stated posture. The strategic implication for the frontend is therefore not "add features"; it is **"out-execute on trust and calm."** Concretely:

1. **Make every number auditable in the UI** (transparent cost-basis, "data as of" timestamps, labelled TWR vs MWR, "why this number" tooltips) — this attacks the #1 complaint head-on.
2. **Lead every surface with one hero number and generous whitespace** — the calm = trustworthy pattern (Mercury/Chime) that the "overwhelmed" Simply Wall St / Snowball users are crying out for.
3. **Treat manual/CSV import as a first-class privacy feature**, but only if the import itself is frictionless (auto-detect broker format, inline row-level error repair, demo-to-yours).
4. **Add benchmark comparison** (vs MSCI World, default for EU) — repeatedly framed as the feature whose *absence* gets tools penalised.
5. **Lean into "describe, don't advise" as a trust differentiator**, not a legal tax — it directly answers documented distrust of generic LLMs that "wrap advice in confident language."

The good news from the code side: Sunday's existing architecture (deterministic numbers + LLM narrative, dark-mode calm UI, `Disclaimer` component, newly-built guardrailed chat) is *already aligned* with where the evidence points. The work is mostly presentation polish and three or four targeted additions, not a rebuild.

---

# PART 1 — Competitive UX gap map

## 1.1 What users love and hate (by competitor)

| Tool | Loved in the UI | Hated in the UI |
|---|---|---|
| **Parqet** | Clean modern dashboard, headline metrics visible immediately, no nested menus; fluid charts w/ easy time-period switch; drag-and-drop PDF + CSV import praised as best-in-class; full mobile app ([finanzwissen](https://finanzwissen.de/anbieter/parqet/test/), [parqet blog](https://parqet.com/en/blog/import)) | Dashboard "superficial" for advanced users (no Beta/Sharpe); sector/dividend views **paywalled** behind Plus; crypto throttled (slot limits, no crypto tax export); per-broker import breakage; dividend calendar ignores record dates ([finanzwissen](https://finanzwissen.de/anbieter/parqet/test/), [depotstudent](https://depotstudent.de/getquin-vs-parqet-vs-extraetf-finanzmanager/)) |
| **getquin** | Intuitive, personalizable dashboard; **sub-5-min onboarding**; fast multi-broker consolidation; vibrant community ([Benzinga](https://benzinga.com/money/getquin-review)) | **Social feed = "noise" for those wanting a private dashboard**; portfolio partly public by default; **no CSV import** (forces broker login = privacy trade-off); analytics shallow; data/pricing mismatches; progressive paywalling ([DonkyCapital](https://www.donkycapital.com/en/compare/best-getquin-alternatives-portfolio-tracker-2026)) |
| **Finanzfluss Copilot** | Fast "360° overview," free, 350+ connections, German servers/privacy framing ([financefwd](https://financefwd.com/de/finanzfluss-copilot/), [finanzfluss](https://www.finanzfluss.de/copilot/)) | Accuracy complaint: positive ETFs shown as negative returns *(single-source, anecdotal)* ([financefwd](https://financefwd.com/de/finanzfluss-copilot/)) |
| **Simply Wall St** | Distinctive "snowflake" infographics; intuitive for beginners ([Modest Money](https://www.modestmoney.com/simply-wall-st-review/)) | **"Overwhelming when you just want to see how your portfolio is doing"**; editing a holding requires delete + re-enter; buggy ticker-mismatch sync; disliked news module ([trefolio](https://trefolio.com/blog/best-portfolio-trackers-europe-2026), [Modest Money](https://www.modestmoney.com/simply-wall-st-review/)) |
| **Snowball Analytics** | Dividend calendar "invaluable"; home-screen widgets "useful at a glance"; TWR/Sharpe with clear visuals ([MatchMyBroker](https://www.matchmybroker.com/tools/snowball-analytics-review)) | "Sheer number of features can feel overwhelming"; data "not necessarily real-time nor accurate"; 10-holding free cap; English-only ([MatchMyBroker](https://www.matchmybroker.com/tools/snowball-analytics-review), [College Investor](https://thecollegeinvestor.com/44042/snowball-analytics-review/)) |
| **Sharesight** | Intuitive even for beginners; excellent tax-time reporting; auto feeds ([SoftwareSuggest](https://www.softwaresuggest.com/sharesight/reviews)) | Mobile lacks desktop features; can't save personalized settings; "sneaky" pricing; no forecasting ([SoftwareSuggest](https://www.softwaresuggest.com/sharesight/reviews)) |
| **Stock Events** | Clean, **ad-free**, "effortless" navigation; best-in-class dividend UX ([WallStreetZen](https://www.wallstreetzen.com/blog/best-dividend-tracker-app/), [CoolCuration](https://coolcuration.com/stock-events-app-review)) | Real depth gated behind Pro *(negative UX evidence thin — Trustpilot blocked)* |
| **Delta (eToro)** | "Visually pleasing," polished mobile UI; per-currency transaction view ([BeInCrypto](https://beincrypto.com/learn/delta-investment-tracker-review/)) | **Beautiful UI undermined by calc errors**: graph P/L ≠ portfolio-page P/L for the same holdings; fee miscalcs persist after re-add; can't view whole portfolio in some currencies ([BeInCrypto](https://beincrypto.com/learn/delta-investment-tracker-review/)) |
| **Portseido** | Clean visuals, per-stock heat maps, **market-value AND cost-basis allocation side-by-side**; low-friction (<1 min updates); FIRE tracking ([Wolf of Harcourt St](https://www.thewolfofharcourtstreet.com/p/portfolio-tracking-that-actually)) | No tax; equities-centric; free tier capped by trade count (paywall-by-volume) |
| **trefolio** | Clean PWA, one-click broker CSV import, AI portfolio score, 35-lang insights, EU tax reports, iOS widget ([trefolio](https://trefolio.com/)) | PWA-only (no native); limited API sync *(source is vendor's own blog — treat as marketing)* |
| **Kubera** | "Supercharged spreadsheet," near-zero learning curve; AI import from CSV/screenshots; strong privacy stance ([College Investor](https://thecollegeinvestor.com/36895/kubera-review/)) | $199/yr, no free tier; intentionally narrow (no analysis/insights) |
| **Trade Republic / Scalable** (native) | TR: mobile-first, clean. Scalable: "almost self-explanatory," Insights liked ([BrokerChooser](https://brokerchooser.com/broker-reviews/trade-republic-review), [Trustpilot](https://www.trustpilot.com/review/scalable.capital)) | TR redesign widely panned; zero charting. Scalable: users **want a pie chart + ETF look-through**; dual-exchange confuses ([Trustpilot](https://www.trustpilot.com/review/scalable.capital)) |

## 1.2 Cross-cutting patterns

**Loved everywhere:** a clean minimal dashboard with headline numbers visible immediately and no nested menus; sub-5-minute onboarding; strong dividend tooling (forward income, ex-div calendar, full-year projection); polished mobile widgets; fluid, export-ready charts.

**Hated everywhere — ranked by damage:**
1. **Numbers that don't reconcile** (Delta, getquin, Copilot, Snowball, Parqet). The single biggest trust-killer; it's a *UI* failure as much as a data one — the interface shows two different truths.
2. **Feature overload / clutter** ("overwhelming when I just want to see how I'm doing").
3. **Hidden/creeping paywalls** on baseline views.
4. **Import friction** (per-broker CSV breakage, tedious manual crypto entry).
5. **Clunky edit flows** (delete-and-re-enter to change a position).
6. **Credential-sharing friction** — EU privacy-minded users actively dislike broker/bank-login aggregation.
7. **Social-feed noise** when you wanted a private dashboard.

## 1.3 The openings Sunday can own

1. **Reconciliation / "show your work" UI** — the biggest open lane. Transparent cost-basis, labelled return types, "data as of" stamps, "why this number" tooltips. Directly attacks complaint #1.
2. **Privacy-first manual/CSV as a *feature*, not a fallback** — competitors treat it as the inferior path; EU users prefer no-broker-login ([Capitally](https://www.mycapitally.com/blog/best-private-portfolio-tracker), [DonkyCapital](https://www.donkycapital.com/en/guides/privacy-portfolio-tracking)). Win condition: make import feel as fast as sync.
3. **The "briefing" framing itself solves the clutter complaint** — a calm weekly synthesis is the antidote to the "wall of widgets" gripe.
4. **Unified stocks + crypto, no artificial caps** — Parqet throttles crypto, Delta separates currencies awkwardly.
5. **EU-specific tax/dividend context in the UI** — rare and praised where present; most global tools are English-only and US-tax-agnostic.
6. **Honest, upfront pricing** — itself a differentiator in a category resented for drip paywalls.
7. **Basic interaction polish** (add-to-existing-position, sortable tables) — table stakes that incumbents still fumble.

---

# PART 2 — Per-surface findings & recommendations

## 2.1 The weekly Briefing (`BriefingView.tsx`)

**What good looks like (evidence):**
- **Digest length, not a report.** Finimize sells "the biggest market moves… in 3 minutes flat," daily brief ≤500 words ([Modest Money](https://www.modestmoney.com/finimize-review/)); Morning Brew is "short sections that summarize a point then link to more" ([growthmodels](https://growthmodels.co/morning-brew-marketing/)). Target a few hundred words across a handful of sections.
- **Structure: at-a-glance snapshot → short themed sections → light outro.** Retail readers want "simplified summaries… focusing on what changed and what it means, not comprehensive coverage" ([Visible](https://visible.vc/blog/investor-reporting/)). **"What changed and what it means" is the recurring, evidence-backed spine.**
- **One hero number.** Surface a single primary figure that "immediately draws the eye," everything else demoted — the calm-design focal-point pattern ([Eleken](https://www.eleken.co/blog-posts/modern-fintech-design-guide), [billcut](https://www.billcut.com/blogs/the-rise-of-quiet-finance-minimalist-app-design/)).
- **Narrative explains, visuals hold the numbers.** "A color-coded trend line communicates the insight far more intuitively than a table" ([Eleken](https://www.eleken.co/blog-posts/modern-fintech-design-guide)). Put deterministic figures as glanceable charts *beside* the prose, not buried in it — fits Sunday's narrative + deterministic-numbers split natively.
- **Calm presentation:** neutral backgrounds, soft greens/whites, generous whitespace; "a red number in a portfolio dashboard is a signal, and often a stressful one" ([Eleken](https://www.eleken.co/blog-posts/modern-fintech-design-guide), [UXmatters calm UX](https://www.uxmatters.com/mt/archives/2025/05/designing-calm-ux-principles-for-reducing-users-anxiety.php)).
- **Distinctive voice + fixed cadence = the ritual.** Email is the habit anchor; consider an audio version (a Finimize differentiator) ([Modest Money](https://www.modestmoney.com/finimize-review/)).

**Critique of Sunday's current briefing:** the structure is already right (sectioned, headline-first, deterministic numbers). The gaps vs. the evidence: (a) the hero "number that matters" is currently WoW=0 (must be real before this surface ships — see code review); (b) sections are prose-only template strings with no glanceable charts beside them; (c) "What changed this week" — *the* evidence-backed emotional spine — is a placeholder; (d) no delivery channel yet (email is the ritual mechanism the research says matters most).

**Recommendations:**
1. Cap narrative at digest length; every section framed as "what changed → what it means."
2. One real hero number, large, with a small WoW sparkline beside it.
3. Pair each section's prose with one glanceable visual (sparkline / mini-bar), never a dense table.
4. Calm palette, lots of whitespace, no alarm-red; reserve strong color for genuinely high-stakes context.
5. Ship email delivery as the ritual anchor; in-app view is the archive. (Open-rate-by-channel evidence is thin — treat email-first as best-practice inference, not proven.)
6. Optional audio "Sunday read" as a cheap, differentiated retention hook (later).

## 2.2 Dashboard & holdings (`dashboard/page.tsx`, `PortfolioTable.tsx`, `ConcentrationCard.tsx`)

**What good looks like (evidence):**
- **Lead with one number above the fold**, no decorative charts — Mercury "opens with total balance above the fold," Chime "a single balance number with expandable menus"; "a cluttered finance dashboard reads as an untrustworthy one" ([Eleken](https://www.eleken.co/blog-posts/fintech-ux-best-practices), [Onething](https://www.onething.design/post/top-10-fintech-ux-design-practices-2026)).
- **Treemap > pie for allocation** beyond a few holdings. Pie/donut become "ambiguous" with many categories; treemaps "shine for portfolio data" and let users "quickly spot overexposed positions" ([vizGPT](https://vizgpt.ai/docs/blog/common-types-of-data-visualization-7-treemap)). Reserve a donut only for the top-level stocks-vs-crypto split; use a treemap (color-coded by daily move = heatmap) for holdings — and note Scalable users explicitly *ask* for a pie + look-through.
- **Holdings table:** ticker, shares, cost, current price, value, gain/loss — always with a **weight % column** for concentration; sortable, color-coded; "start simple — a tracker you actually use beats a complex one abandoned" ([St. Augustine guide](https://explore.st-aug.edu/exp/build-your-best-stock-portfolio-tracker-a-comprehensive-guide)).
- **Return labelling — defuse the TWR/MWR confusion.** "Use TWR to judge the manager, MWR to judge what you actually earned" ([Sharesight](https://www.sharesight.com/blog/time-weighted-vs-money-weighted-rates-of-return/)). Headline = MWR ("your actual return"); benchmark overlay = TWR; label both in plain language.
- **Benchmark comparison** — strongly evidenced demand (Yahoo Finance is *penalised* for lacking it; TrackinV competes on it) though the literal "#1 most-requested" claim is **inference, not a measured survey**. Present as a "vs MSCI World / S&P 500" toggle on the performance chart **(MSCI World default for EU)**, plus a compact table showing % *and* € difference, optionally a "what if I'd just bought the index" counterfactual line. Frame as insight, **not a win/lose scoreboard** ([TrackinV](https://trackinv.com/best-portfolio-tracker/), [Mezzi](https://www.mezzi.com/blog/portfolio-performance-vs-sp500), [Curvo](https://curvo.eu/article/msci-world-vs-sp-500)).

**Critique of Sunday's current dashboard:** `ConcentrationCard` + `PortfolioTable` are the right primitives. Gaps: no benchmark overlay (the highest-value addition); allocation likely pie-style (consider treemap/heatmap); P&L currently fake (cost-basis-as-price) — and *fake P&L shown in a UI is precisely the reconciliation trust-killer that sinks competitors*, so this must be fixed before the dashboard is shown to anyone.

**Recommendations:** one hero number above the fold → treemap/heatmap allocation → sortable holdings table with weight % → benchmark overlay (TWR, MSCI World default) as a headline, not buried → MWR/TWR labelled in plain words → progressive disclosure for dividends/sector/region depth.

## 2.3 Onboarding / CSV upload (`upload/page.tsx`, `CsvUploader.tsx`)

**What good looks like (evidence):**
- **Import friction is the central EU pain point** — TR/Scalable have no trading API, so everyone leans on CSV/PDF/scraping; "for 10–15 trades/month, manual entry can require 30–45 minutes" ([trefolio](https://trefolio.com/blog/best-portfolio-trackers-europe-2026), [neobroker-importer](https://github.com/roboes/neobroker-portfolio-importer)). Even sync isn't an escape — Finary calls sync "our users' biggest frustration" ([tukhe](https://tukhe.io/en/blog/best-portfolio-tracker-european-investors-compared)). **This validates Sunday's manual-first stance as a *reliability* win, not just privacy — but only if import is frictionless.**
- **Auto-detect the broker format; make column mapping the fallback.** The praised pattern: "automatically detects the Trade Republic format and maps columns"; the hated failure: "if columns are named differently, users must rename them" ([tukhe](https://tukhe.io/en/blog/best-portfolio-tracker-european-investors-compared)). Parqet's "drag the CSV in" is the benchmark ([parqet](https://parqet.com/en/blog/import)).
- **Wizard flow:** `Upload → Map → Validate → Confirm`, with drag-and-drop drop zone, progress bar, transparent auto-mapping (confidence indicators + sample values), and **row-level inline error repair** ("show only error rows," fix without re-uploading). Provide a downloadable sample CSV + per-broker "how to export" microcopy <100 words ([ImportCSV](https://www.importcsv.com/blog/data-import-ux), [CSVBox](https://blog.csvbox.io/file-upload-patterns/), [Smart Interface Patterns](https://smart-interface-design-patterns.com/articles/bulk-ux/)).
- **Time-to-first-value:** "show core value in the first session or they may not return"; progressive disclosure (Wise, Cash App) ([Appcues](https://www.appcues.com/blog/best-user-onboarding-examples)). A **demo-to-yours** flow (explore a pre-loaded sample portfolio before importing) makes the dashboard's value visible at ~zero effort — Sunday already ships a `sample-tr.csv`.

**Critique:** Sunday's `CsvUploader` + `sample-tr.csv` is a solid base. Gaps vs. evidence: the review notes ingest accepts **buy rows only** (sells/dividends/splits silently dropped) — a silent-data-loss failure that *will* later show as the reconciliation trust-killer; no column-mapping transparency; no PDF import; no explicit demo-to-yours onboarding step.

**Recommendations:** auto-detect TR/Scalable/DEGIRO layouts → transparent mapping with confidence dots → wizard with inline row-level repair (and surface dropped/unparsed rows loudly, never silently) → sample CSV + export microcopy → demo-to-yours as the first-run default → PDF import as fast-follow → privacy microcopy at the upload step ("no broker login; your data stays yours").

## 2.4 AI chat assistant (`assistant/page.tsx`, `ChatPanel.tsx`)

**What good looks like (evidence):**
- **Show the portfolio data the answer used.** "Numbers should be visible and traceable, not buried behind a chat response" ([freeCodeCamp](https://www.freecodecamp.org/news/build-an-llm-market-copilot-with-langchain/)). This is the highest-leverage trust move — and Sunday's `portfolio_context.py` already computes a deterministic snapshot; surface it.
- **Citations measurably raise trust** even though users rarely click them — a controlled study found a "statistically significant increase in perceived trustworthiness… with citations" ([arXiv 2501.01303](https://arxiv.org/pdf/2501.01303)). Place them **adjacent to the specific claim**, with meaningful labels (holding name, source, as-of date), not grouped in a footer ([NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/)).
- **No fake reasoning theater.** Step-by-step "chain of thought" is "often plausible but untrue… rationalizations after the fact" ([NN/g](https://www.nngroup.com/articles/explainable-ai/)). For a numbers app, show the *real deterministic computation/data*, not a narrated thought process.
- **Suggested-prompt chips, grouped by function** (~3–6 visible) teach capabilities and lift engagement; offer **follow-up question chips** after each answer (Perplexity-style) ([NN/g prompt controls](https://www.nngroup.com/articles/prompt-controls-genai/), [uxstudio](https://www.uxstudioteam.com/ux-blog/chatbot-ui)).
- **Stream responses**, with an option to disable ([Azure blog](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/the-importance-of-streaming-for-llm-powered-chat-applications/4459574)).
- **Fiscal.ai is the positive proof point** — users praise per-response citations, inline tables/charts, sourced info ([WallStreetZen](https://www.wallstreetzen.com/blog/finchat-io-fiscal-ai-review/)). **Magnifi is the cautionary one** — "very slow… basically confirming what they already knew" (shallow value) ([College Investor](https://thecollegeinvestor.com/42031/magnifi-personal-review/)). Generic LLMs are distrusted: they "wrap advice in confident, friendly language"; **76% of Americans say tech can give information but not judgment/trust** ([Empower](https://www.empower.com/the-currency/money/ai-financial-guidance-risks-why-humans-lead-news)) — which validates Sunday's describe-don't-advise posture as a *differentiator*.

**Non-advice framing in the UI (compliance as UX):**
- **Disclose AI at first interaction**, "clear and distinguishable," not "a small snippet hidden in the footer" — EU AI Act Art. 50 (user-facing duties live since 2 Feb 2025; fuller rules Aug 2026) ([AI Act Art. 50](https://artificialintelligenceact.eu/transparency-rules-article-50/), [Inside Privacy](https://www.insideprivacy.com/artificial-intelligence/digital-fairness-act-series-topic-2-transparency-and-disclosure-obligations-for-ai-chatbots-in-consumer-interactions/)). 84% favour mandatory AI disclosure; transparency builds trust ([MIT Sloan](https://sloanreview.mit.edu/article/artificial-intelligence-disclosures-are-key-to-customer-trust/)).
- **Specific, placed disclaimers beat boilerplate.** Vague "AI-generated, for reference only" fails (users skim fine print); use plain-language, specific-limitation copy **near the input box**, paired with a concrete action ("information, not advice — verify the numbers") ([NN/g](https://www.nngroup.com/articles/explainable-ai/)). Avoid anthropomorphic phrasing that grants "undeserved trust."

**Critique:** Sunday's chat is newly built and already strong on the *backend* posture (guardrails, deterministic grounding, persona). The frontend gaps: the deterministic portfolio snapshot the model uses isn't *shown* to the user; no grouped suggested-prompt chips or follow-up chips; AI-disclosure likely lives in the shared `Disclaimer` footer rather than at first interaction / near the input; streaming status unknown.

**Recommendations:** show the grounding (a collapsible "based on your portfolio as of <date>: …" panel) → adjacent citations with as-of dates → grouped starter chips + post-answer follow-up chips → AI-disclosure label at first interaction and specific non-advice microcopy near the input → stream responses (optional) → never fabricate step-by-step reasoning; show the real computed figures.

---

# PART 3 — Cross-cutting expectations (apply to all four surfaces)

**EU formatting & localization:** drive *all* number/currency rendering through `Intl.NumberFormat(locale)` — DE expects `1.234,56 €` (comma decimal, symbol-after-space); show explicit ISO codes when mixing EUR/USD ([techcommunity](https://techcommunity.microsoft.com/discussions/excelgeneral/german-numer-format-for-euro/3810349), [Number Analytics](https://www.numberanalytics.com/blog/ultimate-guide-currency-formats-ux-writing)). **pt-PT was not directly sourced — verify via `Intl` + a PT tax source before building, don't assume.**

**EU tax context, not advice:** informational cards for Abgeltungsteuer (~26.375%), the crypto **1-year holding clock**, Sparerpauschbetrag (€1,000), ETF Teilfreistellung (30/15/0%), each with a standing "not tax advice" line ([TokenTax](https://tokentax.co/blog/crypto-taxes-in-germany), [QuantRoutine](https://quantroutine.com/learn/investing-taxes-germany/)). The holding-period countdown is a high-value glanceable element unique to EU/DE and fully compliant (informational).

**Trust & privacy signaling:** make "no broker login, no wallet-connect, encrypted, your data stays yours" a *visible* benefit; per-purpose GDPR opt-in (no pre-checked/bundled consent); zero dark patterns (easy delete/export, no preselected sharing) ([Eleken](https://www.eleken.co/blog-posts/fintech-ux-best-practices), [UXDA dark patterns](https://www.theuxda.com/blog/dark-patterns-in-digital-banking-compromise-financial-brands), [Transcend](https://transcend.io/blog/turnkey-privacy-balancing-trust-regulation-for-fintech-growth)).

**Mobile / PWA + notifications:** PWA-first is defensible, but native push is materially stronger (~95% vs ~33% delivery; iOS needs add-to-Home-Screen) ([Mobiloud](https://www.mobiloud.com/blog/progressive-web-apps-vs-native-apps)). **Notifications are the retention spine:** finance leads push opt-in (~77%), apps notifying in first 90 days see up to ~3× retention, segmentation lifts CTR dramatically ([Pushwoosh](https://www.pushwoosh.com/blog/push-notifications-fintech/)) *(vendor benchmarks — indicative)*. The weekly briefing push (fixed day/time, value framed at opt-in) is the natural ritual anchor.

**Accessibility:** solve the red/green problem — use **blue (gains) / orange (losses)**, differ by *lightness* not just hue, and never rely on color alone (add arrows, +/−, labels) ([Datawrapper](https://www.datawrapper.de/blog/colorblindness-part2), [Sigma](https://www.sigmacomputing.com/blog/data-charts-color-blindness)). Accessible tables: `<caption>`, `scope` on `<th>`, chart-as-table fallback ([TestParty](https://testparty.ai/blog/wcag-tables-accessibility)). Dark mode: avoid pure black, use dark grey + mint/light-blue accents.

**2026 dashboard trends:** **bento grids** (variably-sized glanceable cards, one metric + trend each, sized by importance) are the defining pattern; calm UI; dark mode near-mandatory; AI-native/conversational summaries replacing static charts ([Orbix bento](https://www.orbix.studio/blogs/bento-grid-dashboard-design-aesthetics), [Gezar trends](https://gezar.dk/en/blog/web-design-trends-2026)).

---

# PART 4 — Ranked frontend idea menu

Scored by **user demand × differentiation**, filtered for the non-advice posture. Tier reflects build order.

| # | Frontend feature / pattern | Demand | Differentiation | Compliance | Tier |
|---|---|---|---|---|---|
| 1 | **"Show your work" reconciliation UI** (auditable cost-basis, "data as of" stamps, labelled TWR/MWR, why-this-number tooltips) | ★★★★★ | ★★★★★ (attacks the #1 complaint) | 🟢 | **Now** |
| 2 | **One-hero-number + calm layout** across briefing & dashboard | ★★★★★ | ★★★★ | 🟢 | **Now** |
| 3 | **Benchmark overlay** (vs MSCI World default / S&P 500; TWR; %+€ diff; insight-framed) | ★★★★★ | ★★★★ | 🟢 (descriptive) | **Now** |
| 4 | **Frictionless import** (auto-detect broker CSV, transparent mapping, inline row-level repair, surface dropped rows loudly) | ★★★★★ | ★★★★ | 🟢 | **Now** |
| 5 | **Demo-to-yours onboarding** (explore sample portfolio first) | ★★★★ | ★★★ | 🟢 | **Now** |
| 6 | **"What changed this week" briefing section** with glanceable visuals beside prose | ★★★★★ | ★★★★★ | 🟢 (describe/attribute) | **Next** |
| 7 | **Chat: show grounding + adjacent citations** ("based on your portfolio as of …") | ★★★★ | ★★★★ | 🟢 | **Next** |
| 8 | **Chat: grouped starter chips + follow-up chips + streaming** | ★★★★ | ★★★ | 🟢 | **Next** |
| 9 | **Treemap/heatmap allocation** (donut only for top-level split) | ★★★★ | ★★★ | 🟢 | **Next** |
| 10 | **EU tax-context cards + crypto 1-year holding clock** (informational) | ★★★★ | ★★★★ (EU-specific) | 🟡 (info, not advice — disclaimer) | **Next** |
| 11 | **Weekly briefing email + push as the ritual anchor** | ★★★★★ | ★★★ | 🟢 | **Next** |
| 12 | **Colorblind-safe blue/orange + a11y tables** (foundational, do early) | ★★★ | ★★ | 🟢 | **Now/Next** |
| 13 | **Visible privacy trust cues + per-purpose consent** | ★★★★ | ★★★★ | 🟢 (GDPR) | **Next** |
| 14 | **Dividend calendar / forward-income view** (table-stakes for the income ICP) | ★★★★ | ★★ (parity) | 🟢 | **Later** |
| 15 | **Bento-grid dashboard refresh** | ★★★ | ★★ | 🟢 | **Later** |
| 16 | **Audio "Sunday read"** briefing | ★★ | ★★★ | 🟢 | **Later** |
| 17 | **iOS-installable PWA widget** (glanceable net worth) | ★★★ | ★★ | 🟢 | **Later** |
| — | ~~Social feed / public portfolios~~ | — | — | 🟡 (noise + privacy) | **Avoid** (contradicts privacy-first wedge) |
| — | ~~"Optimal allocation" / rebalance prescriptions in UI~~ | — | — | 🔴 advice | **Avoid** |

---

## Sources

Competitor UX: [finanzwissen/Parqet](https://finanzwissen.de/anbieter/parqet/test/) · [depotstudent](https://depotstudent.de/getquin-vs-parqet-vs-extraetf-finanzmanager/) · [Benzinga/getquin](https://benzinga.com/money/getquin-review) · [DonkyCapital](https://www.donkycapital.com/en/compare/best-getquin-alternatives-portfolio-tracker-2026) · [MatchMyBroker/Snowball](https://www.matchmybroker.com/tools/snowball-analytics-review) · [College Investor/Snowball](https://thecollegeinvestor.com/44042/snowball-analytics-review/) · [Modest Money/Simply Wall St](https://www.modestmoney.com/simply-wall-st-review/) · [trefolio EU roundup](https://trefolio.com/blog/best-portfolio-trackers-europe-2026) · [SoftwareSuggest/Sharesight](https://www.softwaresuggest.com/sharesight/reviews) · [BeInCrypto/Delta](https://beincrypto.com/learn/delta-investment-tracker-review/) · [WallStreetZen dividend trackers](https://www.wallstreetzen.com/blog/best-dividend-tracker-app/) · [Wolf of Harcourt St/Portseido](https://www.thewolfofharcourtstreet.com/p/portfolio-tracking-that-actually) · [financefwd/Copilot](https://financefwd.com/de/finanzfluss-copilot/) · [College Investor/Kubera](https://thecollegeinvestor.com/36895/kubera-review/) · [BrokerChooser/TR](https://brokerchooser.com/broker-reviews/trade-republic-review) · [Trustpilot/Scalable](https://www.trustpilot.com/review/scalable.capital) · [Capitally privacy](https://www.mycapitally.com/blog/best-private-portfolio-tracker)

Import & dashboard: [tukhe EU trackers](https://tukhe.io/en/blog/best-portfolio-tracker-european-investors-compared) · [TrackinV](https://trackinv.com/best-portfolio-tracker/) · [Appcues onboarding](https://www.appcues.com/blog/best-user-onboarding-examples) · [parqet import](https://parqet.com/en/blog/import) · [ImportCSV UX](https://www.importcsv.com/blog/data-import-ux) · [CSVBox patterns](https://blog.csvbox.io/file-upload-patterns/) · [Smart Interface bulk UX](https://smart-interface-design-patterns.com/articles/bulk-ux/) · [neobroker-importer](https://github.com/roboes/neobroker-portfolio-importer) · [vizGPT treemap](https://vizgpt.ai/docs/blog/common-types-of-data-visualization-7-treemap) · [Sharesight TWR/MWR](https://www.sharesight.com/blog/time-weighted-vs-money-weighted-rates-of-return/) · [St. Augustine holdings table](https://explore.st-aug.edu/exp/build-your-best-stock-portfolio-tracker-a-comprehensive-guide) · [Mezzi vs S&P 500](https://www.mezzi.com/blog/portfolio-performance-vs-sp500) · [Curvo MSCI World vs S&P](https://curvo.eu/article/msci-world-vs-sp-500) · [Onething fintech UX](https://www.onething.design/post/top-10-fintech-ux-design-practices-2026) · [Eleken fintech UX](https://www.eleken.co/blog-posts/fintech-ux-best-practices)

Briefing & chat: [Modest Money/Finimize](https://www.modestmoney.com/finimize-review/) · [Morning Brew](https://growthmodels.co/morning-brew-marketing/) · [Visible investor reporting](https://visible.vc/blog/investor-reporting/) · [Eleken design guide](https://www.eleken.co/blog-posts/modern-fintech-design-guide) · [UXmatters calm UX](https://www.uxmatters.com/mt/archives/2025/05/designing-calm-ux-principles-for-reducing-users-anxiety.php) · [arXiv citations & trust](https://arxiv.org/pdf/2501.01303) · [NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/) · [NN/g prompt controls](https://www.nngroup.com/articles/prompt-controls-genai/) · [freeCodeCamp copilot](https://www.freecodecamp.org/news/build-an-llm-market-copilot-with-langchain/) · [WallStreetZen/Fiscal.ai](https://www.wallstreetzen.com/blog/finchat-io-fiscal-ai-review/) · [College Investor/Magnifi](https://thecollegeinvestor.com/42031/magnifi-personal-review/) · [Empower AI trust](https://www.empower.com/the-currency/money/ai-financial-guidance-risks-why-humans-lead-news) · [Azure streaming](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/the-importance-of-streaming-for-llm-powered-chat-applications/4459574) · [uxstudio chatbot UI](https://www.uxstudioteam.com/ux-blog/chatbot-ui)

EU / trust / mobile / a11y / trends: [AI Act Art. 50](https://artificialintelligenceact.eu/transparency-rules-article-50/) · [Inside Privacy AI Act](https://www.insideprivacy.com/artificial-intelligence/digital-fairness-act-series-topic-2-transparency-and-disclosure-obligations-for-ai-chatbots-in-consumer-interactions/) · [MIT Sloan disclosure](https://sloanreview.mit.edu/article/artificial-intelligence-disclosures-are-key-to-customer-trust/) · [DE number format](https://techcommunity.microsoft.com/discussions/excelgeneral/german-numer-format-for-euro/3810349) · [Number Analytics currency UX](https://www.numberanalytics.com/blog/ultimate-guide-currency-formats-ux-writing) · [TokenTax DE crypto](https://tokentax.co/blog/crypto-taxes-in-germany) · [QuantRoutine DE taxes](https://quantroutine.com/learn/investing-taxes-germany/) · [UXDA dark patterns](https://www.theuxda.com/blog/dark-patterns-in-digital-banking-compromise-financial-brands) · [Transcend fintech privacy](https://transcend.io/blog/turnkey-privacy-balancing-trust-regulation-for-fintech-growth) · [Mobiloud PWA vs native](https://www.mobiloud.com/blog/progressive-web-apps-vs-native-apps) · [Pushwoosh fintech push](https://www.pushwoosh.com/blog/push-notifications-fintech/) · [Datawrapper colorblindness](https://www.datawrapper.de/blog/colorblindness-part2) · [Sigma colorblind dataviz](https://www.sigmacomputing.com/blog/data-charts-color-blindness) · [TestParty WCAG tables](https://testparty.ai/blog/wcag-tables-accessibility) · [Orbix bento grids](https://www.orbix.studio/blogs/bento-grid-dashboard-design-aesthetics) · [Gezar 2026 trends](https://gezar.dk/en/blog/web-design-trends-2026)

## Confidence & gaps

- **High confidence:** the reconciliation/clutter/paywall/import complaint cluster (multi-source, 2025–26); calm "one number" design; treemap > pie; import-UX best practices; citations→trust; EU number formatting & DE tax values; push/a11y/bento trends.
- **Medium / directional:** benchmark comparison as a *must-have* is well-evidenced, but the literal "#1 most-requested missing feature" is **inference from convergent secondary sources, not a measured survey**. Finanzfluss Copilot negatives, trefolio claims (vendor), and some app like/dislike points are single-source.
- **Thin / not covered:** raw EU Reddit/forum first-person voice (US-biased crawler; Reddit & Trustpilot bodies often blocked) — user voice is second-hand in places; **email-vs-in-app-vs-PDF open-rate** comparison (no good data — email-first is best-practice inference); **pt-PT formatting & PT-specific tax/UX** (deliberately not invented — verify before building); crypto-specific dataviz preferences (recs are equity-led).
