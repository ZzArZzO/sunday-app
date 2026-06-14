# Sunday App — Pre-Launch Legal & Compliance Execution Research

*The actual process, costs, and deadlines to launch a non-advice EU fintech-adjacent product — operationalizing `docs/LEGAL.md` and Blueprint Part 6 into a do-this checklist.*

**Date:** June 2026
**Method:** Live web research into EU AI Act Art. 50, BaFin licensing thresholds, German Impressum/cookie law (DDG/TDDDG), GDPR DPIA triggers, and SaaS legal-package costs.
**Scope:** This is strategy + process research, **not legal advice.** `docs/LEGAL.md` already nails the *substantive* MiFID II / MiCA bright line. This doc covers the *execution*: what to file, who to talk to, what it costs, and what's newly urgent.
**⚠️ Timeliness:** The single most urgent item below — **EU AI Act Art. 50 — comes into force 2 August 2026**, weeks from this doc's date.

---

## 0. The two-sentence posture (unchanged, confirmed)

Stay on the **information/publisher side** of MiFID II Art. 4(1)(4) and MiCA — general, impersonal, educational content; never a personal recommendation of a specific instrument presented as suitable. `docs/LEGAL.md`'s bright-line table and the forbidden-phrase guardrail are exactly right. **Everything here assumes that posture holds** — the moment you give personalized buy/sell advice, you need a BaFin license (§1) and this entire calculus changes.

---

## 1. Do you need a BaFin license? (No — and here's the proof you're avoiding it)

- **Investment advice is a licensed activity** in Germany — a permit under **§15 WpIG** (Investment Firm Act), enforcing MiFID II. Getting one takes **6–12 months** and costs **€2,000–17,000** in BaFin fees alone (plus far more in counsel/setup). That path is a non-starter for a solo launch — and unnecessary if you stay non-advice.
- **BaFin runs a fintech contact point** for early-stage firms to ask "does my model trigger a license?" — but **it does not give legal advice**, and queries must be highly specific. Useful as a *sanity check*, not a substitute for counsel.
- **The strategic goal is to NOT need a license** by staying information-only. The deliverable is a **counsel opinion** confirming the non-advice classification — cheap insurance, and a marketing asset ("advice-neutral, not a robo-advisor").

**Action:** Engage German (and Portuguese, for PT) fintech/securities counsel for a written opinion that the product is an *information service*, not investment advice/CASP activity. Optionally file a specific BaFin FinTech-Kontakt enquiry to corroborate. **Do not apply for a license.**

> The same logic applies to **MiCA** for the crypto side: you *describe* crypto holdings, you don't advise on or custody crypto-assets → no CASP authorization needed, but get it in the counsel opinion.

---

## 2. 🔴 EU AI Act Article 50 — in force 2 August 2026 (most urgent)

Art. 50 imposes **transparency obligations on ALL AI systems that interact with people or generate content — regardless of risk classification.** Sunday has both an **AI chat assistant** (`routes/chat.py`) and **AI-generated briefing text** (`briefing_ai.enhance`), so it is squarely in scope as a **deployer** (and arguably provider) of these outputs.

**The two obligations that apply to Sunday:**
1. **Chatbot disclosure** — users must be **informed they are interacting with an AI** at the point of interaction, unless it's obvious from context. → The AI chat must clearly say "you're talking to an AI assistant."
2. **AI-content marking** — synthetic text/image/audio/video must be **marked as artificially generated**; generative-AI *providers* must mark outputs in a **machine-readable** format. → The briefing (AI-written prose) and chat responses must be labelled AI-generated.

**Enforcement:** fines up to **€15,000,000 or 3% of worldwide annual turnover**, whichever is higher.
**Help available:** the European Commission published a **Code of Practice on Transparency of AI-Generated Content (10 June 2026)** — follow it as the compliance blueprint.

**Good news:** `docs/LEGAL.md` already mandates *"Generated with AI assistance"* on every LLM-touched output via `Disclaimer.tsx`. That covers obligation #2's human-facing marking and #1's chatbot notice. **Two gaps to close before Aug 2:**
- Verify the disclaimer **actually renders** on the chat surface and the email/PDF briefing (not just the in-app briefing view).
- Add **machine-readable** marking of AI content where feasible (per the Code of Practice) — e.g., metadata/labelling on generated artifacts, not just visible text.

**Action (by 2 Aug 2026):** audit every LLM-touched surface (chat, in-app briefing, email, PDF) for (a) "you're talking to AI" notice on chat, (b) visible AI-generated label, (c) machine-readable marking per the Code of Practice. This is the most time-sensitive legal item.

---

## 3. German website law: Impressum + cookies (mandatory, easy to get wrong)

Germany is the beachhead, so German web-law applies:
- **Impressum** is **legally mandatory** for commercial sites — now under **§5 DDG** (the Digital Services Act replaced the TMG in May 2024). Must show provider identity, contact, etc. Missing/incorrect Impressum is a common, cheaply-litigated violation (Abmahnung culture).
- **Cookie consent** under **TDDDG** (the renamed TTDSG): GDPR-grade consent **before** setting any non-essential cookie/storage; only strictly-necessary are exempt. Consent must be freely given, specific, informed, unambiguous. **Fines up to €300,000.**
  - This is why `docs/LEGAL.md` mandates **Plausible/PostHog-EU with no portfolio data and cookieless/consented analytics** — that choice keeps the cookie banner simple (ideally only essential cookies → minimal/no consent friction).

**Action:** publish a **DDG §5 Impressum**, a **TDDDG-compliant cookie approach** (prefer cookieless analytics to avoid a consent wall), and keep the wording current (replace any "TTDSG"→"TDDDG", "TMG"→"DDG" references). Counsel drafts the Impressum; it's cheap.

---

## 4. GDPR: DPIA, DPAs, DSAR (portfolio data is sensitive)

- **DPIA (Data Protection Impact Assessment)** is required for **high-risk / large-scale processing of sensitive financial data** and automated profiling. Sunday processes portfolio holdings (financial PII) at scale and applies AI to it → **a DPIA is very likely required, and is cheap insurance regardless.** Non-compliance fines reach **€20M / 4% of turnover**. Use the gdpr.eu DPIA template as a starting structure; counsel reviews.
- **DPAs (Data Processing Agreements)** must be executed with every processor touching personal data: **Anthropic (EU, no-train tier), Stripe, Resend, Neon/Fly/Vercel, Sentry, PostHog.** `docs/LEGAL.md` already calls out Anthropic + Stripe; extend to *all* infra vendors chosen in `DEPLOYMENT_TOOLS_RESEARCH.md`.
- **DSAR / deletion** — `docs/LEGAL.md` already specs an account-deletion endpoint that cascades to all owned data. Verify it works and document the DSAR workflow.
- **Data residency** — EU regions throughout (the reason `DEPLOYMENT_TOOLS_RESEARCH.md` picks EU Fly/Neon/Anthropic and notes Hetzner is EU-owned). Schrems II makes EU-native infra a cleaner posture.

**Action:** complete a DPIA; execute DPAs with all processors; verify DSAR/deletion; document data flows (the DPIA forces this).

---

## 5. The document set + cost

**Documents to produce (counsel-drafted/reviewed):**
- [ ] Terms of Service (with the non-advice disclaimer baked in)
- [ ] Privacy Policy (GDPR; lists all processors + EU residency)
- [ ] Cookie Policy + banner (TDDDG)
- [ ] Impressum (DDG §5)
- [ ] DPIA (documented)
- [ ] DPAs executed: Anthropic, Stripe, Resend, hosting/DB, Sentry, analytics
- [ ] AI Act Art. 50 disclosures live on every LLM surface (§2)
- [ ] Affiliate/influencer compliance policy + disclosure templates (if/when you do finfluencer marketing — Blueprint 6.4)
- [ ] Marketing-copy review against MiFID II ("robo-advisor"/"AI recommends" = the trap)

**Cost (directional):**
- US fixed-fee SaaS-**with-AI** legal packages (ToS/Privacy/Cookie/subscription/AUP) start **~$4,500**; healthcare-grade ~$7,500–9,500. EU/DE securities-fintech counsel is a **separate, specialist** line item.
- The Blueprint's estimate of **€5,000–15,000 total counsel** for a careful pre-launch (opinion + documents + review) remains realistic. It is the **single biggest pre-launch cash line** (Blueprint 8.3) — budget for it; it's non-optional for a financial-data product.

---

## 6. Sequencing (what gates what)

| When | Item | Blocks |
|---|---|---|
| **Now → 2 Aug 2026** | AI Act Art. 50 disclosures (§2) | Any public AI-touched usage; hard deadline |
| Parallel, ASAP | Counsel opinion on non-advice posture (§1) | Public *marketing*; private beta can run before |
| Before public launch | ToS/Privacy/Cookie/Impressum/DPIA/DPAs (§3–5) | Public launch; charging money |
| Before paid marketing | Marketing-copy review + affiliate policy | Paid/finfluencer channels |
| Before first paid sub | Stripe DPA + Stripe Tax (VAT) | Taking money (see `DEPLOYMENT_AND_MARKETING.md` A.9) |

**Key insight (matches the deploy doc):** you can run a **private beta behind the legal gate** while documents are in progress — but **public marketing and charging require the gate cleared**, and **Art. 50 has a fixed statutory deadline (2 Aug 2026) independent of your launch timeline.** Treat Art. 50 as the immovable date and back-plan from it.

---

## Sources (June 2026)

**AI Act Art. 50:** [Art. 50 practical guide (artificialintelligenceact.eu)](https://artificialintelligenceact.eu/transparency-rules-article-50/) · [Art. 50 obligations before Aug 2026 (Belto)](https://www.belto.ai/blog/eu-ai-act-article-50-transparency-obligations-august-2026) · [Transparency obligations from 2 Aug (Bratby Law)](https://bratby.law/ai-act-transparency-obligations-2026/) · [Draft Transparency Code of Practice (Bird & Bird)](https://www.twobirds.com/en/insights/2026/taking-the-eu-ai-act-to-practice-understanding-the-draft-transparency-code-of-practice)
**BaFin/licensing:** [Fintech 2026 Germany (Chambers)](https://practiceguides.chambers.com/practice-guides/fintech-2026/germany) · [BaFin licence (SZA)](https://www.sza.de/en/thinktank/bafin-license) · [BaFin investment services](https://www.bafin.de/EN/Aufsicht/BankenFinanzdienstleister/Markteintritt/Wertpapierdienstleistungen/wertpapierdienstleistungen_node_en.html) · [BaFin licence in Germany (Stripe)](https://stripe.com/resources/more/bafin-license-germany)
**German web law:** [TMG→DDG change (die marketingarchitekten)](https://www.diemarketingarchitekten.de/en/online-en/tmg-becomes-ddg) · [TDDDG cookie law (devowl)](https://devowl.io/cookie-banner/tdddg-cookie-law/) · [TTDSG/TDDDG (Piwik PRO)](https://piwik.pro/glossary/ttdsg/)
**GDPR/DPIA:** [DPIA when required (DPO Consulting)](https://www.dpo-consulting.com/blog/when-is-a-data-protection-impact-assessment-dpia-required) · [GDPR for fintech startups (Complydog)](https://complydog.com/blog/gdpr-for-fintech-startups) · [DPIA template (gdpr.eu)](https://gdpr.eu/data-protection-impact-assessment-template/)
**Legal costs:** [Fixed-fee SaaS legal packages (Bosin)](https://www.njbusiness-attorney.com/best-fixed-fee-legal-services-for-saas-startups/)
**Cross-refs:** `docs/LEGAL.md`, `Sunday_App_Business_Blueprint.md` Part 6, `DEPLOYMENT_AND_MARKETING.md` A.12.
