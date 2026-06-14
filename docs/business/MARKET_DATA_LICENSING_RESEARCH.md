# Sunday App — Market-Data & News API Licensing Research

*Which price/FX/news/calendar/crypto data you can legally use in a commercial EU product, what it costs, and the licensing trap that pulls products offline weeks after launch.*

**Date:** June 2026
**Method:** Live web research into vendor pricing + **licensing terms** (the part that matters), cross-referenced against the app's current data layer (`api/app/services/prices.py`, `fx.py`, `events/`, `requirements.txt` → `yfinance` + `fmp`).
**Why this is urgent:** Your shipped `requirements.txt` uses **yfinance**, which is **personal-use-only**. The moment you charge money you're in breach of Yahoo's terms — a live, latent risk in the codebase right now. This doc covers how to replace it and, more importantly, the *display/redistribution* licensing most builders miss.

---

## 0. The two things that actually matter (read first)

**1. "Free/cheap to use" ≠ "licensed to show your users."** There are two separate rights:
- **Data access** — you pull the data (cheap, every API offers it).
- **Data display / redistribution** — you *show* it to your end users (the briefing, the dashboard, the public newsletter). **This is a separate, often pricier license** — and showing a user even *their own* portfolio's prices counts as display/redistribution under most terms.

Real cautionary case from the research: *a fintech built a real-time portfolio dashboard on a provider whose ToS allowed their own research use but **not redistribution to end users**. Six weeks after launch they got a letter from the exchange's licensing division; the product was pulled while legal negotiated a retroactive license.* **This is the exact shape of Sunday** (a portfolio dashboard + briefing). Get the **display/distribution right in writing** before charging.

**2. You do NOT need real-time data — and that saves you a fortune.** Sunday is a **weekly Sunday briefing + portfolio tracker**, not a trading app. **End-of-day (EOD) or 15-min-delayed data is sufficient.** Real-time exchange feeds require per-user professional/non-professional display fees and six-figure exchange licenses; EOD/delayed is dramatically cheaper (though *still* licensed — you can't escape licensing entirely, you just pay far less). **Design around EOD/delayed and your data costs stay trivial.**

---

## 1. 🔴 The yfinance problem (fix before charging)

- **yfinance** scrapes Yahoo Finance via unofficial endpoints. Yahoo's Developer API Terms **prohibit** selling, sharing, sublicensing, or "deriving income" from the data without written permission. The library is **personal/research use only**; commercial productization "requires careful legal review and may violate terms."
- Your `config.py` already has an **FMP** key + the code has an FMP fallback — good instinct, but FMP's *free/standard* tiers also don't grant display/redistribution (see §3). So today **both** of your price sources are unlicensed for a paid product.
- **Action:** before the first paid sub, **replace yfinance as the production price source** with a vendor that grants a **commercial display license** (§3). Keep yfinance only for local dev / your personal use, never in the path that serves paying users.

---

## 2. EU coverage is a hard requirement (most cheap APIs are US-centric)

Your users hold **XETRA / Euronext / LSE-listed stocks + UCITS ETFs + crypto** (TR, Scalable, DEGIRO). Many popular cheap APIs (Polygon, Alpha Vantage, IEX) are **US-first** and thin on EU instruments and ETFs. So the filter is: *commercial display license **and** real EU exchange coverage **and** EOD/delayed is fine.* That narrows the field considerably.

---

## 3. Price/fundamentals vendors (the core decision)

| Vendor | ~Entry price (2026) | EU coverage | Display/redistribution license | Verdict for Sunday |
|---|---|---|---|---|
| **EODHD** | **~€19.99/mo** base (All-In-One add-on for all exchanges) | ✅ **Strong** — explicit LSE + Cboe Europe contracts, global exchanges, ETFs, EOD + bulk | Offers commercial + redistribution tiers; **confirm display rights in writing** | ★★★★★ **Best fit** — EU coverage + EOD value + affordable |
| **FMP** (already in your code) | Free → Starter/Premium (tens of $/mo) | Decent global + fundamentals | **Display/redistribution requires the Enterprise "Data Display & Licensing Agreement"** — *not* the standard plans | ★★★ Usable, but you must upgrade to the display license; verify EU depth |
| **Twelve Data** | Free → Grow/Pro (~$29–79+/mo) | Multi-asset (stocks/FX/crypto), decent intl | Commercial tiers; check redistribution clause | ★★★★ Clean API, good FX+crypto in one |
| **Polygon.io** | From ~$29/mo | ⚠️ **US-focused** | Display license available | ★★ Great for US real-time; wrong geography for EU beachhead |
| **Alpha Vantage** | Free → $49.99–249.99/mo | Limited intl | NASDAQ-licensed commercial tiers | ★★ US-leaning; thin EU ETF coverage |
| **Marketstack** | Cheap entry | Global EOD | Commercial tiers | ★★ Lightweight; fine for basic EOD prices |

**Recommendation:** lead with **EODHD** (EU exchange contracts + EOD + affordable) as the production price source, with a **written confirmation of display/redistribution rights** for your use case. Keep FMP as the fundamentals/fallback source **only if** you take its Enterprise display license. Use **EOD/delayed**, not real-time.

---

## 4. FX rates — there's a free, official, perfect option

Sunday is EUR-base; `fx.py` currently hardcodes `1.08` (placeholder, flagged in `REVIEW_AND_PLAN`).
- **Best option: ECB euro foreign-exchange reference rates** — published **daily, free, official, and licensable for display** (the European Central Bank publishes them for public use). For a EUR-denominated product this is ideal, authoritative, and zero-cost. Cache the daily rates.
- **Paid fallback** (intraday/more pairs): ExchangeRatesAPI (~$14.99/mo, commercial), Currencylayer (~$13.99/mo), Fixer, etc. Cheap.
- Twelve Data / EODHD also bundle FX if you want one vendor.

**Action:** replace the `1.08` placeholder with **ECB daily reference rates** (free, official, display-OK) + a paid intraday fallback only if needed.

---

## 5. Crypto data (MiCA-aware)

Your users declare crypto (not chain-read). You need EUR-quoted spot + history.
- **CoinGecko** — commercial license **from ~$35/mo** (Basic); 80+ endpoints, EUR quotes, OHLCV, best value/coverage. **Recommended.**
- **CoinMarketCap** — first commercial tier ~$79–95/mo; pricier for equivalent.
- Many price vendors (Twelve Data, EODHD) include crypto too — could consolidate.

**Recommendation:** **CoinGecko commercial ($35/mo)** for crypto, or fold into EODHD/Twelve Data if their crypto coverage suffices (fewer vendors = simpler DPAs/licensing).

---

## 6. News & "what changed this week" (powers your events feed)

Your `services/events/` feed is the heart of the briefing ("what changed this week" — `REVIEW_AND_PLAN` §6). News licensing is its own minefield (headlines/snippets are copyrighted; display rights matter).

| Vendor | Notes | Fit |
|---|---|---|
| **Marketaux** | Affordable; **entity/ticker-tagged** news (built for "news about *these* holdings"); commercial tiers | ★★★★ **Best starting point** — cheap, holdings-taggable, the exact JTBD |
| **Benzinga** | Premium fintech-grade newswire; clean **redistribution** path (used by brokerages, available via Massive/Alpaca); REST/Webhook/WebSocket | ★★★★ Upgrade when budget allows; gold standard for redistribution |
| **Finnhub** | Generous free tier (60 calls/min), intl coverage, includes news | ★★★ Good for prototyping; **verify commercial + redistribution terms** before paid use |
| **NewsAPI.org** | General news | ★★ ⚠️ Restricts commercial/display use on cheap tiers — read terms carefully; not ideal for productized display |

**Recommendation:** start with **Marketaux** (cheap, entity-tagged, display-licensable) for the held-ticker news feed; move to **Benzinga** for premium quality + clean redistribution once revenue supports it. **Summarize cheaply with Haiku/Flash** before display (your architecture already plans this), but note: summarizing licensed news still requires display rights to the underlying source — keep attribution.

---

## 7. Economic calendar (CPI/ECB/FOMC/earnings)

The briefing's "week ahead" section. Lower licensing risk (event dates are largely factual/public).
- **Free/official:** ECB, Fed, BLS, and national stats offices publish release calendars — scrape/ingest the authoritative sources for the macro events you care about (CPI/ECB/FOMC/jobs). Cheapest and most accurate.
- **Paid convenience:** FMP, Trading Economics, or Twelve Data bundle an economic + earnings calendar API if you'd rather not aggregate.
- **Earnings dates** for held tickers usually come from your price/fundamentals vendor (EODHD/FMP include earnings calendars).

**Recommendation:** official free sources for macro events + your price vendor's earnings calendar; upgrade to a paid calendar API only if aggregation overhead isn't worth it.

---

## 8. Recommended data stack & cost

| Layer | Pick | ~€/mo | License note |
|---|---|---|---|
| Stock/ETF prices + fundamentals (EOD/delayed, EU) | **EODHD** | ~€20+ | **Get display/redistribution rights in writing** |
| FX (EUR base) | **ECB daily reference rates** (free) + paid fallback | €0–15 | ECB display-OK |
| Crypto | **CoinGecko** commercial | ~$35 | Commercial license incl. |
| News (held-ticker) | **Marketaux** → Benzinga later | ~€20–100 | Entity-tagged; display rights |
| Economic calendar | Official free sources + vendor earnings cal | €0 | Factual/public |
| **Total (launch)** | | **~€60–120/mo** | All commercially licensed |

This is consistent with the Blueprint Part 7 data-cost projections and keeps you **fully licensed** — the difference between this and "free yfinance" is the difference between a sellable product and one that gets a cease letter.

---

## 9. Action checklist

- [ ] 🔴 **Remove yfinance from the production path** before the first paid sub (keep only for dev/personal).
- [ ] Adopt **EODHD** (or FMP-Enterprise) with a **written commercial display/redistribution license** covering: in-app dashboard, the briefing (email/PDF), **and the public newsletter**.
- [ ] Replace the `fx.py` `1.08` placeholder with **ECB daily reference rates**.
- [ ] Add **CoinGecko** commercial for crypto (or consolidate into the price vendor).
- [ ] Wire **Marketaux** for held-ticker news; keep source attribution through the Haiku summarization step.
- [ ] Ingest **official macro calendars** + vendor earnings dates.
- [ ] Confirm **EOD/delayed** suffices (it does for a weekly briefing) to avoid real-time exchange display fees.
- [ ] Execute **DPAs** with each data vendor (GDPR — `PRELAUNCH_LEGAL_RESEARCH.md` §4) and keep the licenses on file.

---

## Sources (June 2026)

**yfinance/Yahoo terms:** [Yahoo Finance API commercial-use guide (MarketXLS)](https://marketxls.com/blog/yahoo-finance-api-ultimate-guide) · [Yahoo Developer API Terms](https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html)
**Price vendors:** [2026 Market Data API Scorecard (EODHD)](https://eodhd.com/financial-academy/financial-faq/the-2026-market-data-api-scorecard-comparing-6-leading-providers) · [Best Financial Data APIs 2026 (nb-data)](https://www.nb-data.com/p/best-financial-data-apis-in-2026) · [FMP pricing](https://site.financialmodelingprep.com/pricing-plans) · [FMP enterprise/display](https://site.financialmodelingprep.com/enterprise) · [Tiingo review](https://www.findmymoat.com/tools/tiingo)
**Licensing/redistribution:** [Stock market data licensing (marketdata.app)](https://www.marketdata.app/education/stocks/stock-market-data-licensing/) · [Trading data API license (terms.law)](https://terms.law/Trading-Legal/guides/api-license-trading-data.html) · [Real cost of delayed market data (United Fintech)](https://www.unitedfintech.com/blog/the-real-cost-of-delayed-market-data) · [Deutsche Börse delayed data](https://www.mds.deutsche-boerse.com/mds-en/real-time-data/Delayed-data)
**News:** [Best financial news APIs 2026 (APITube)](https://apitube.io/blog/post/best-financial-news-api-trading) · [Benzinga news API](https://www.benzinga.com/apis/cloud-product/stock-news-api/)
**Crypto/FX:** [CoinGecko vs CoinMarketCap API](https://www.coingecko.com/learn/coingecko-api-vs-coinmarketcap-api) · [ExchangeRatesAPI pricing](https://exchangeratesapi.io/pricing/) · [Currencylayer](https://currencylayer.com/)
**Calendar:** [Economic calendar 2026 (DataSetIQ)](https://www.datasetiq.com/economic-calendar) · [Trading Economics calendar](https://www.tradingeconomics.com/calendar/interest-rate)
**Cross-refs:** `Sunday_App_Business_Blueprint.md` Part 7, `DEPLOYMENT_TOOLS_RESEARCH.md`, `PRELAUNCH_LEGAL_RESEARCH.md`.
