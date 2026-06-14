# Sunday App — EU Broker Import & Onboarding Research

*How EU retail investors get their portfolio into the app — the #1 onboarding friction, and the conversion-critical surface.*

**Date:** June 2026
**Method:** Live web research into each major EU broker's export formats + the open-source importer ecosystem, cross-referenced against the app's current ingest code (`api/app/services/csv_ingestor.py`) and the gaps flagged in `REVIEW_AND_PLAN.md` §3.
**Why this matters:** Manual/CSV-first is the right call for the EU (no broker APIs — `REVIEW_AND_PLAN` §2), but it makes onboarding the highest-friction moment in the funnel. Parqet has years of polished import UX; this is where you lose or win the aha-moment ("first briefing <2 min from upload").

---

## 0. Headline finding (this changes the plan)

**Trade Republic shipped an official CSV transaction export in April 2026.** Path: *Profile → Account Statements → Transaction Export → Share → All transactions (or a period) → Create*. One file covers **brokerage + cash + crypto buys/sells**, back to account opening. Portfolio trackers added support within days.

This is a big deal for Sunday because:
- TR is **the** beachhead broker (`REVIEW_AND_PLAN` §8). Until April 2026 the only export was an informational **PDF** — everyone had to scrape it. Now there's a structured CSV.
- Your `csv_ingestor.py` was built for the *old* TR format. **It should be re-targeted to the new official CSV**, which is cleaner, includes sells/dividends/crypto, and is what TR users will now naturally export.
- It removes the need to build/maintain a fragile TR PDF parser for new users (keep PDF only as a fallback for pre-April-2026 statements).

**Action:** get a real sample of the new TR CSV, map its columns, and make it the primary import path. This single change de-risks the most important onboarding flow.

---

## 1. Export formats by broker (the beachhead set)

| Broker | Export | Format details | Contains | Priority |
|---|---|---|---|---|
| **Trade Republic** | ✅ **Official CSV** (Apr 2026) + legacy PDF | CSV via app; PDF statements legacy. EU decimal/locale. | Brokerage + cash + **crypto**, buys/sells/dividends, full history | **P0 — primary** |
| **Scalable Capital** | ✅ CSV (PRIME/PRIME+ broker accts) | "Export CSV" button; filter + export all | Transactions: buys/sells/dividends/fees | **P0** |
| **DEGIRO** | ✅ CSV (Account Statement / Transactions) | **Semicolon-separated**, EU locale; `Account.csv` + `Transactions.csv` | Buys/sells, dividends, fees, **FX conversions** | **P1** |
| **Trading 212** | ✅ CSV export | Standard CSV | Transactions incl. dividends | **P1** |
| **Interactive Brokers** | ✅ **Flex Query** (CSV or XML) + Activity Statements | Highly customizable fields; reusable templates; column names vary by query | Everything (configurable) | **P1 (power users)** |
| **Comdirect / ING / Consorsbank** (DE banks) | PDF statements mostly; some CSV | German PDF formats; Portfolio Performance has parsers | varies | **P2** |

**Common EU parsing gotchas your ingest must handle robustly:**
- **EU number format** `1.234,56` (dot thousands, comma decimal) — `csv_ingestor.py` already does this; keep it.
- **Delimiter variance**: DEGIRO is **semicolon**-separated; others comma. Auto-detect.
- **ISIN/WKN** identifiers (EU uses ISIN, DE also WKN) — not US tickers. Map ISIN → instrument; `csv_ingestor.py` already infers asset class from ISIN.
- **Multi-currency**: USD stocks held in EUR accounts; DEGIRO exposes FX rows. `REVIEW_AND_PLAN` §3 flagged positions are hardcoded EUR — must model real currency.
- **Transaction types beyond "buy"** — the critical bug (next section).

---

## 2. The critical gap: ingest only accepts "buy" rows

`REVIEW_AND_PLAN.md` §3 (item 6) flagged: `csv_ingestor.py` `ACCEPTED_TYPES = {"buy","kauf","purchase"}` — **sells, dividends, splits, transfers are silently dropped.** Every broker CSV above includes these. Consequences if unfixed:
- Cost basis and quantities **drift wrong over time** → P&L, tax, and FIRE math become incorrect. **Fatal for a tax/FIRE product.**
- A user who has *ever sold* sees a portfolio that doesn't match their broker → instant trust loss at the aha-moment.

**This is the highest-value import fix.** Map and net: **buy, sell, dividend, split, transfer in/out, fee, interest, FX**. The new TR CSV and DEGIRO/Scalable/T212 exports all carry these explicitly — the data is there; the parser just has to stop discarding it.

---

## 3. Open-source importers to lift from (don't hand-roll 50 parsers)

The EU broker-parsing problem is solved repeatedly in OSS. Study/port these rather than writing from scratch:

| Project | What it covers | Use for Sunday |
|---|---|---|
| **Portfolio Performance** (`portfolio-performance/portfolio`) | **Gold-standard PDF + CSV importers for German/EU brokers** (TR, comdirect, ING, DKB, Scalable…), maintained for years | The reference implementation for DE broker PDF parsing logic; mine its import test fixtures |
| **Export-To-Ghostfolio** (`dickwolff/Export-To-Ghostfolio`) | Avanza, IBKR, DEGIRO, eToro, Saxo, XTB, **Trading 212**, Bux, FreeTrade… | Per-broker CSV→canonical mapping patterns; MIT-style reuse |
| **@pocket-portfolio/importer** (npm) | Universal CSV parser, 19+ brokers, **locale-aware EU date/number handling**, privacy-first/local | Closest philosophy to Sunday (privacy-first, no upload); good architecture model |
| **TR-specific parsers** (`Thukyd/trade-republic-portfolio`, `kalix127/tradesight`, `MarcBuch/TR-PDF-Parser`, `traderepublic-portfolio-downloader`) | TR PDF → CSV | Legacy TR PDF fallback only (new CSV supersedes most of this) |
| **pdf-broker-2-ghostfolio** | PDF broker statements → structured | Pattern for the PDF fallback path |

**Licensing note:** check each license before porting code (most are permissive; Portfolio Performance is EPL — read it before lifting code vs. just studying logic). Studying the *format mappings* (which column means what) carries no license risk; copying code does.

---

## 4. The onboarding UX bar (what you're measured against)

Parqet supports **Autosync + file import across 50+ brokers** with polished UX — that's the bar EU users compare you to. You won't match breadth at launch; win on the **beachhead set done flawlessly** + a frictionless first run:

1. **Broker-picker first screen** — "Where do you invest?" → TR / Scalable / DEGIRO / Trading 212 / IBKR / Other. Each shows a **2-step illustrated guide** to get the export (the export paths are buried in broker menus — hold the user's hand).
2. **Drag-drop + instant parse preview** — show "we found 23 positions, 47 transactions" *before* commit, so they trust it. Flag anything skipped ("3 rows we couldn't read — review").
3. **Sample-to-yours** — a "try with a sample portfolio" button (you already ship `sample-tr.csv`) so users see the briefing *before* uploading their own data. Lowers commitment, demonstrates value, then converts to real upload.
4. **Aha in <2 min** — upload → dashboard with **real prices** → first briefing. The `REVIEW_AND_PLAN` north star for onboarding.
5. **Privacy as the reason** — frame "no broker login, you stay in control" as the *feature* that justifies the manual step (turns friction into trust — your positioning).

---

## 5. Recommendation & build order

1. **Re-target `csv_ingestor.py` to the new official TR CSV** (P0) — get a real sample, map columns, make it primary. Keep TR PDF as fallback for old statements.
2. **Fix transaction-type handling** (P0) — accept and net buy/sell/dividend/split/transfer/fee/FX. *This unblocks correct tax/FIRE/P&L.*
3. **Add Scalable + DEGIRO + Trading 212 CSV** (P1) — lift mappings from Export-To-Ghostfolio / Portfolio Performance. Handle semicolon (DEGIRO) + EU locale.
4. **Add IBKR Flex Query** (P1) — for power users; document the field checklist they must include.
5. **Multi-currency positions** (P1) — stop hardcoding EUR; use the FX rows brokers provide + your live FX.
6. **Broker-picker onboarding wizard + parse-preview** (P1) — the conversion UX, per §4.
7. **PDF import fallback** (P2) — for DE bank statements (comdirect/ING) using Portfolio Performance patterns.

**Net:** the April-2026 TR CSV export plus fixing the buy-only bug are the two changes that most improve onboarding trust and downstream math correctness — do them first.

---

## Sources (June 2026)

**Trade Republic:** [Official CSV export (CoinTracking)](https://cointracking.info/blog/cointracking-trade-republic-import) · [TR import (AllInvestView)](https://www.allinvestview.com/trade-republic-portfolio-tracker/) · [tradesight (PDF→CSV)](https://github.com/kalix127/tradesight) · [Thukyd/trade-republic-portfolio](https://github.com/Thukyd/trade-republic-portfolio) · [TR-PDF-Parser](https://github.com/MarcBuch/TR-PDF-Parser) · [traderepublic-portfolio-downloader](https://github.com/dhojayev/traderepublic-portfolio-downloader)
**Scalable / DEGIRO:** [Scalable transactions export](https://de.scalable.capital/en/product-news/transactions-export) · [Scalable CSV FAQ](https://help.scalable.capital/en/account-management-f3197dc7/can-i-export-information-about-my-portfolio-such-as-a-cs-4f77cde3) · [DEGIRO CSV guide](https://trackyourportfol.io/blog/degiro-export-csv-guide) · [DEGIRO import (trefolio)](https://trefolio.com/blog/how-to-import-degiro-portfolio)
**Trading 212 / IBKR:** [IBKR Flex Query setup](https://trackyourportfol.io/blog/ibkr-flex-query-setup) · [IBKR Flex automation](https://www.daystoexpiry.com/blog/interactive-brokers-flex-query) · [Export from any brokerage (Portfolio Genius)](https://portfoliogenius.ai/blog/how-to-export-portfolio-from-brokerage)
**OSS importers:** [Export-To-Ghostfolio](https://github.com/dickwolff/Export-To-Ghostfolio) · [@pocket-portfolio/importer](https://www.npmjs.com/package/@pocket-portfolio/importer?activeTab=readme) · [Portfolio Performance releases](https://github.com/portfolio-performance/portfolio/releases) · [pdf-broker-2-ghostfolio](https://github.com/fucnim17/pdf-broker-2-ghostfolio)
**Bar/UX:** [Parqet on Google Play](https://play.google.com/store/apps/details?id=com.parqet&hl=en)
