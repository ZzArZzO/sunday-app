# Sunday App — Mobile UX Research (mobile web + installable PWA)

*What self-directed EU retail investors want from a portfolio-briefing app on a phone, and how to build it as a mobile-web + installable PWA — competitor teardown, the four surfaces on mobile, mobile-native/PWA capabilities, and navigation/IA.*

**Date:** June 2026
**Approach decided:** Mobile web + **installable PWA** (extend the existing Next.js app), per the blueprint's "PWA-first, native later."
**Method:** Multi-source web research (WebSearch + WebFetch) across four streams — competitor mobile teardown, the four surfaces on mobile, PWA/native capabilities, and navigation/IA. ~70 sources reviewed; ~50 cited.
**Confidence:** Medium-high. Strongest on PWA/iOS platform constraints (primary WebKit/web.dev/MDN sources), navigation, touch targets, bottom sheets (NN/g). Weaker on raw EU forum sentiment (US-biased crawler) and exact vendor stats (delivery %, opt-in %).

---

## 0. Executive summary

Three findings dominate and should shape the whole mobile build:

1. **On iOS, the install IS the funnel — not the push.** Web Push on iOS works *only* after the user manually does Safari → Share → **Add to Home Screen** (iOS 16.4+), and there's no programmatic install prompt on iOS at all. So the reachable push audience is ~10–15× smaller than native unless you nail the install step. The hero "Sunday ritual" notification is gated behind an install coach you must design deliberately. ([MobiLoud](https://www.mobiloud.com/blog/progressive-web-apps-ios), [Pushpad](https://pushpad.xyz/blog/ios-special-requirements-for-web-push-notifications))

2. **The most-loved mobile feature — a home-screen widget — is the one thing a PWA can't do in 2026.** Glanceable widgets (value, daily P/L, top movers, upcoming dividends) are the standout praise across Snowball, Delta, and trefolio — but PWAs cannot create native home-screen widgets on iOS or Android today. The realistic "glance" is the **notification + app-icon badge**; a true widget is a future native-wrapper feature. ([Progressier](https://intercom.help/progressier/en/articles/12814946-can-a-pwa-create-home-screen-widgets))

3. **The PWA's structural advantage is exactly where incumbents fail.** Scalable's "web and mobile are frustratingly different" is a top complaint — a single PWA codebase gives **web/mobile parity** for free. And the dominant *negative* pattern across Trade Republic + Trading 212 is redesigns that **hide holdings behind extra taps/gestures** — Sunday can win by keeping holdings and per-position detail one tap from a glanceable home.

The good news: the email-delivery + scheduler work already in the codebase is the perfect **install-independent fallback** for the weekly ritual, which the research says you *need* given web-push reliability gaps on iOS.

---

# PART 1 — Competitive mobile UX gap map

## 1.1 What users praise / criticize (mobile-specific)

| App | Loved on mobile | Hated on mobile |
|---|---|---|
| **getquin** | Modern design, clear Portfolio/Community/Analytics sections, glanceable dashboard w/ progressive disclosure ([matchmybroker](https://www.matchmybroker.com/tools/getquin-review)) | "Slow scrolling, **very slow adding assets**, widget kept being logged out"; buggy re-entry; broken PDF import ([Trustpilot](https://www.trustpilot.com/review/getquin.com)) |
| **Parqet** | High store rating, sleek design, **German data hosting** (privacy) ([App Store](https://apps.apple.com/us/app/parqet-portfolio-tracker/id1547114259)) | Manual-entry screen so painful they **"completely redesigned"** it; "endless loading"; Android 15 crashes; iPad not optimized ([changelog](https://parqet.com/en/changelog)) |
| **Trade Republic** | Mobile-first, clean (historically) | **Redesign widely panned** ("bring back old design"); settings toggle undiscoverable (profile icon, **no gear**); outages ([PissedConsumer](https://trade-republic.pissedconsumer.com/review.html)) |
| **Trading 212** | ~4.7–4.9★, frictionless overview, Pie management | 2025 rebrand: **"slide up to see positions," extra taps for return breakdowns** ([review](https://investinginsiders.co.uk/reviews/trading212/)) |
| **Delta (eToro)** | Clean, low learning curve; **Net Worth / Top Movers / Watchlist widgets** ([widgets](https://support.delta.app/en/collections/3634307-widgets)) | **Pull-to-refresh doesn't refresh** (broken gesture affordance); accounts only addable on mobile ([reviews](https://justuseapp.com/en/app/1288676542/delta-investment-tracker/reviews)) |
| **Stock Events** | Sleek, glanceable dividend breakdowns by day/month/hour ([WallStreetZen](https://www.wallstreetzen.com/blog/best-dividend-tracker-app/)) | Freemium slot limits; thin UX complaints |
| **Snowball** | **Home-screen widgets are the exemplar** (payouts, performance, top gainers/losers "without opening the app"); card-based home ([blog](https://snowball-analytics.com/blog/snowball-updates-introducing-the-report-ios-widgets-mobile-enhancements/)) | Tap-heavy interaction model; few gestures |
| **Scalable** | User-friendly, clear overview | UI "confusing"; **"web and mobile frustratingly different"**; **red/green on dark bg unreadable** for vision-impaired ([Trustpilot](https://www.trustpilot.com/review/scalable.capital)) |
| **Sharesight** | **Native app retired (Aug 2022) → fully responsive web** — the PWA-only precedent works ([MoneyHub](https://www.moneyhub.co.nz/sharesight-review.html)) | **View settings don't persist** — resets to default $/% / filters / groupings each visit |
| **Revolut** | Mobile-first, tap-to-buy, familiar UI | Charts "extremely limited" — no multi-asset overlay/config ([review](https://uk.stockbrokers.com/review/revolut)) |
| **trefolio** (closest analog) | **EU-first PWA**: installable, **iOS home-screen widget**, offline app shell, auto-updates, EU tax + CSV import ([trefolio](https://trefolio.com/)) | Markets still perceive **"PWA only" as a con** ([blog](https://trefolio.com/blog/best-portfolio-trackers-europe-2026)) |

## 1.2 Cross-cutting patterns

**Loved:** home-screen widgets (#1); glanceable card home + progressive disclosure; one obvious primary action; mobile-optimized charts (not shrunk tables); **EU privacy/data residency** (Parqet); frictionless CSV import with broker templates + de-dup.

**Hated — ranked by frequency:**
1. **Redesigns that bury holdings/breakdowns behind extra taps/gestures** (Trade Republic + Trading 212 converge — strongest signal).
2. **Buried settings with no clear affordance** (Trade Republic, no gear icon).
3. **Broken gesture affordances** (Delta pull-to-refresh).
4. **Web/mobile inconsistency** (Scalable).
5. **Slow performance** (getquin, Parqet).
6. **Painful manual entry** (getquin, Parqet).
7. **Non-persistent view state** (Sharesight).
8. **Red/green on dark backgrounds** (Scalable a11y).

## 1.3 The openings Sunday can own
1. **Ship a home-screen "glance" as early as possible** — and since PWAs can't do native widgets, make the **notification + icon badge** the glance, with a true widget as the headline reason to later ship a native shell.
2. **Counter "PWA-only = limited" head-on** — lead with the PWA strengths users praise: instant install, no store friction, offline app shell, auto-updates, and **web/mobile parity** (the thing Scalable fails at).
3. **Keep holdings + per-position detail one tap from home** — the explicit anti-Trade-Republic/Trading-212 move.
4. **Fast manual + CSV entry on a phone** — the recurring incumbent weakness.
5. **Persist per-user view state** (units, sort, filters, locale) — Sunday already persists locale; extend it.
6. **EU privacy/data residency** as a mobile selling point (Parqet model).

---

# PART 2 — The four surfaces on mobile

## 2.1 The weekly Briefing (the reading surface)
- **Structure for skimming, not reading.** Inverted pyramid (what happened → why → background); a reader who stops after 20s still gets the gist — and it fits the non-advice posture (describe first, never direct). Scannable formatting + concise copy showed large usability gains. ([readability](https://kontent.ai/blog/guide-to-formatting-that-boosts-readability/))
- **Short blocks:** 2–3 sentences max per paragraph on mobile; descriptive section headings; bullets; highlighted key terms.
- **One hero number** (weekly Δ in € and %) then narrative below; descriptive ("up 2.1%, driven by X"), not evaluative. ([fintech UX](https://procreator.design/blog/best-fintech-ux-practices-for-mobile-apps/))
- **Vertical scroll long-form with inline sparklines/mini-cards** beats a swipe-card deck for a reading surface; a reading-progress bar / "~3 min" estimate helps. ([dataviz](https://www.kellton.com/kellton-tech-blog/data-visualization-best-practices-every-app-developer-should-know))
- **Type:** 16–18px body, line-height 1.5–1.6, 50–75 char measure.
- *Fits Sunday:* the existing `BriefingView` + `EventsCard` already follow this; mobile just needs tighter blocks, a hero number, and inline sparklines (the T1.8 slot).

## 2.2 Dashboard & holdings
- **Tables → cards** is the primary pattern: each holding becomes a card (ticker as header, 3–4 key fields, rest in a detail view). Prioritize columns → abbreviate values → concatenate related fields → card view; horizontal-scroll tables are a **last resort** and need explicit scroll affordances. ([table→card](https://medium.com/design-bootcamp/designing-user-friendly-data-tables-for-mobile-devices-c470c82403ad))
- **Glanceable summary cards** (value/profit/passive-income/IRR) with mini-graphs inside; target <2s load. ([fintech dashboards](https://www.wildnetedge.com/blogs/fintech-ux-design-best-practices-for-financial-dashboards))
- **Sparklines** for per-holding trend in cards (axis-less inline). ([sparklines](https://www.domo.com/learn/charts/sparkline-chart))
- **Allocation:** **donut only for <5 categories** (top-level stocks/crypto/cash); **horizontal bars for many holdings**. ([donut vs bar](https://www.domo.com/learn/charts/donut-charts))
- **Line/benchmark charts:** strip titles/axis chrome; **legend above** the chart (stays visible during touch); 3–4 colors; color-independent cues. ([mobile dataviz](https://www.kellton.com/kellton-tech-blog/data-visualization-best-practices-every-app-developer-should-know))
- **Tap a card → bottom sheet** with full metrics (preserves dashboard context).
- *Fits Sunday:* `PortfolioTable` needs a card layout at mobile breakpoints; `AllocationBar`/donut and the `AllocationTreemap` work but the treemap is cramped on phones — consider bars + sparkline cards as the mobile default, treemap as a tap-to-expand.

## 2.3 CSV import / onboarding (the hard surface)
- **"Where's my CSV?" is real friction** — design to native pickers (Files/iCloud/Drive), test inside iOS WKWebView + Android WebView. ([mobile import](https://blog.csvbox.io/mobile-friendly-spreadsheet-import-flows/))
- **Keep the wizard shallow:** select → parse → map → validate → confirm, with a 2–6 row preview and **specific inline errors** ("invalid value in row 4"), progressive disclosure. (Sunday already built this wizard — it needs a mobile layout.)
- **Share-sheet import (Web Share Target):** viable on **Android** only (installed PWA + WebAPK, must declare MIME *and* extension); **does not work for web-published PWAs on iOS** (needs an App Store build). Treat as an Android-only enhancement. ([web.dev](https://web.dev/learn/pwa/os-integration))
- **Demo-first** empty state (try with sample data before importing) — strongly aligned with Sunday's existing `sample-tr.csv` demo path.
- ⚠️ **Tension:** the strongest manual-entry reducer in fintech is **account-linking/aggregation** (Plaid / EU open-banking) — but that **contradicts Sunday's privacy-first, no-broker-login stance**. So Sunday must win import UX through *speed* (native pickers, fast parse, de-dup, demo-first), not aggregation. ([Plaid](https://plaid.com/resources/fintech/fintech-onboarding-process/))
- Benchmark to beat: avg fintech onboarding ~14 screens / 16 fields / 29 clicks — stay well under.

## 2.4 AI chat
- **Input:** auto-resizing composer **docked at the bottom** with safe-area inset; avoid empty "Ask anything…" placeholders. ([chat UX](https://thefrontkit.com/blogs/ai-chat-ui-best-practices))
- **Suggested-prompt chips** (~4, context-updating, descriptive/non-advisory) — Sunday's grouped chips already do this; on mobile, make them horizontally scrollable.
- **Streaming:** buffer partial markdown; prominent **Stop**; don't steal focus from the input after a response (immediate follow-ups). Sunday's streaming + guardrail already exist.
- **Keyboard/safe areas:** inset the composer above the keyboard and home indicator; `aria-live="polite"` for streamed text.

---

# PART 3 — Mobile-native / PWA capabilities (the iOS reality)

## 3.1 Push notifications — the Sunday ritual
- **iOS gate:** Web Push requires the PWA be **installed to the Home Screen via Safari** (iOS 16.4+); not from a Safari tab; all iOS browsers are WebKit so there's no workaround. Reachable push audience ~10–15× smaller than native. ([Pushpad](https://pushpad.xyz/blog/ios-special-requirements-for-web-push-notifications), [MobiLoud](https://www.mobiloud.com/blog/progressive-web-apps-ios))
- **Declarative Web Push (Safari 18.4 / iOS 18.4, Mar 2025)** simplifies the code path (JSON payload, `app_badge`, no service worker required) — but **does not remove the iOS install requirement**. ([WebKit](https://webkit.org/blog/16535/meet-declarative-web-push/))
- **No reliable scheduled/local notification API** on the web — use a **server-side, timezone-aware cron → Web Push** to stored subscription endpoints (deliver "Sunday 9am" local). This is exactly what the codebase's `delivery/scheduler` is for. ([architecture](https://yundrox.dev/posts/claritybox/building-robust-pwa-push-notifications/))
- **Opt-in:** iOS needs a **user gesture** to prompt — use a **pre-permission prime** ("Turn on my Sunday briefing?") before the one-shot OS prompt. ([priming](https://blog.alertwise.net/ios-web-push-notifications/))
- **Reliability caveat:** web push is less reliable than native (vendor figures ~33% vs ~95% — direction solid, exact number soft) and iOS PWAs report **lost subscriptions** after restarts → **email fallback for the weekly ritual is essential** (and already built). ([Edana](https://edana.ch/en/2026/03/19/push-notifications-on-web-applications-pwa-is-it-really-reliable-on-ios-and-android/))
- **Android** supports web push without forced install — much easier.

## 3.2 Install & widgets
- **Android:** intercept `beforeinstallprompt`, prompt from your own UI at a high-value moment. **iOS:** no programmatic install — detect Safari and show a **custom "tap Share → Add to Home Screen" coach** with an arrow. iOS 26 now opens Home-Screen sites as standalone web apps by default. ([web.dev](https://web.dev/learn/pwa/installation-prompt))
- **Widgets: not possible for PWAs on iOS/Android in 2026.** Use the notification + `app_badge` as the glance. ([Progressier](https://intercom.help/progressier/en/articles/12814946-can-a-pwa-create-home-screen-widgets))

## 3.3 Biometric lock, offline, share
- **WebAuthn / passkeys** = the right primitive for a Face ID / fingerprint app-lock and passwordless login (implement the handshake carefully — "WebAuthn Loop" flaws). ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API))
- **Offline:** service worker (stale-while-revalidate) + IndexedDB makes the **last briefing readable offline**; iOS has **no Background Sync/Fetch**, so the new briefing caches on next open, not in the background. ([MagicBell](https://www.magicbell.com/blog/offline-first-pwas-service-worker-caching-strategies))
- **Web Share API** is well-supported on mobile → "share my briefing" with a copy-link fallback. ([caniuse](https://caniuse.com/web-share))

## 3.4 Distribution & retention
- **App stores:** Google Play accepts PWAs via **TWA/Bubblewrap** (cheap store presence); **Apple rejects PWAs** (Guideline 4.2.2) → no iOS App Store presence without a native/Capacitor shell. iOS acquisition must be **web-led**. ([MobiLoud](https://www.mobiloud.com/blog/publishing-pwa-app-store))
- **Cadence is right:** weekly notifications → **440% higher retention** vs zero (Airship), while a once-weekly "calm" cadence stays far under the over-messaging annoyance threshold (~39% disable push when over-notified). Finance leads opt-in (~72%). ([stats](https://www.mobiloud.com/blog/push-notification-statistics))

---

# PART 4 — Navigation & information architecture

## 4.1 Bottom tab bar (the load-bearing recommendation)
Bottom tab bars beat hamburger menus for discoverability (hamburgers ~halve feature discovery); optimal count is **3–5 tabs** (Apple HIG + Material converge). ([Onething](https://www.onething.design/post/hamburger-menu-vs-tab-bar), [UX Planet](https://uxplanet.org/bottom-tab-bar-design-best-practices-ef3ee71de0fc))

Sunday has ~8 surfaces — too many for a flat bar. **Recommended 5-tab structure:**

| Tab | Contents | Why |
|---|---|---|
| **Briefing** (default) | The weekly read + EventsCard | The product's core value; open here |
| **Dashboard** | Portfolio value, holdings cards, allocation, benchmark | The day-to-day detail surface |
| **Assistant** | Chat | Distinct interaction mode; benefits from persistent reach |
| **Plan** | Hub → Fire / Dividend / Tax / Rebalance (segmented control or bento cards) | Lower-frequency analytical views grouped behind one tab |
| **Upload** *(or a FAB)* | Import wizard | Occasional — could be a `+` action instead of a 5th tab if you prefer 4 |

## 4.2 Ergonomics
- **Thumb zones:** ~75%+ interactions are thumb-driven; keep frequent actions bottom-center, infrequent controls top. Bottom-anchor the tab bar and the chat composer. ([Smashing](https://www.smashingmagazine.com/2016/09/the-thumb-zone-designing-for-mobile-users/))
- **Touch targets:** 44pt (Apple) / 48dp (Material), ≥8dp spacing — critical for dense holdings cards and chart tap zones. ([Material 3](https://m3.material.io/foundations/designing/structure))
- **Safe areas (must-do for PWA):** `viewport-fit=cover` + `env(safe-area-inset-*)` with `calc()` on the bottom bar/chat dock so they clear the home indicator. You handle this manually in a PWA. ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env))
- **Gestures:** avoid custom horizontal swipes near screen edges (collide with iOS/Android system back); always provide a button alternative. ([Android](https://developer.android.com/develop/ui/views/touch-and-input/gestures/gesturenav))

## 4.3 Bottom sheets (NN/g)
Use a bottom sheet for holding detail / quick actions / Upload steps: **modal** to force one decision, **non-modal** to coexist with the dashboard; always a visible **Close (X)** (not just a grab handle); don't stack sheets or use them for primary navigation or long content. ([NN/g](https://www.nngroup.com/articles/bottom-sheet/))

## 4.4 Onboarding, type, trends, a11y
- **Onboarding:** fast time-to-first-value (see one real briefing), progressive disclosure, **just-in-time + double-opt-in** permission priming *after* the first briefing; prime install at a high-value moment, not first load. ([Appcues](https://www.appcues.com/blog/mobile-permission-priming))
- **Typography (dark/calm):** ≥16px body, medium/semibold + **tabular numerals** for figures (not thin light-gray), slightly off-white on dark (avoid pure-white-on-black halation). ([dark mode](https://designshack.net/articles/typography/dark-mode-typography/))
- **Trends 2025–26:** calm/low-stimulus UI, **bento grids** for the Briefing/Plan hub, glanceable cards, bottom sheets, restrained glassmorphism — Sunday's calm/dark aesthetic is on-trend.
- **A11y:** gains/losses must pair color with **+/− or arrows** (Sunday already does); rem-based type for Dynamic Type reflow; label tab icons for VoiceOver/TalkBack; ≥4.5:1 contrast.

---

# PART 5 — Ranked mobile build menu

Scored by **user demand × differentiation × feasibility (PWA)**; ordered by build sequence.

| # | Mobile capability | Demand | Feasible as PWA? | Tier |
|---|---|---|---|---|
| 1 | **Responsive shell: bottom tab bar + safe-area insets + thumb-anchored layout** | ★★★★★ | ✅ | **Now** |
| 2 | **Holdings table → cards + sparklines; allocation bars/donut; bottom-sheet detail** | ★★★★★ | ✅ | **Now** |
| 3 | **Briefing mobile layout** (hero number, short blocks, inline sparklines, progress) | ★★★★★ | ✅ | **Now** |
| 4 | **Mobile chat** (bottom-docked composer, keyboard/safe-area handling, scrollable chips) | ★★★★ | ✅ | **Now** |
| 5 | **Mobile import wizard** (native pickers, demo-first, shallow steps, inline errors) | ★★★★ | ✅ | **Now** |
| 6 | **Installable PWA** (manifest, icons, iOS splash, standalone) + **iOS install coach** | ★★★★★ | ✅ | **Next** |
| 7 | **Weekly push** (server cron → Web Push, timezone-aware) + **double-opt-in priming** + **email fallback** | ★★★★★ | ✅ (Android easy; iOS needs install) | **Next** |
| 8 | **Offline last-briefing** (service worker + IndexedDB) | ★★★ | ✅ (no iOS bg prefetch) | **Next** |
| 9 | **Persist view state** (units, sort, filters) | ★★★ | ✅ | **Next** |
| 10 | **WebAuthn/passkey app-lock + Web Share** | ★★★ | ✅ | **Later** |
| 11 | **Android store presence via TWA/Bubblewrap** | ★★★ | ✅ | **Later** |
| 12 | **Home-screen widget + iOS App Store presence** | ★★★★★ | ❌ PWA | **Native shell (future)** |

**The honest PWA verdict:** a mobile-web PWA covers #1–11 well and is the right first step (cheap, web/mobile parity, no store gatekeeping). The two things users love most that it *can't* do — **home-screen widgets and iOS App Store presence** — are the eventual case for a thin native/Capacitor shell once retention is proven. Lead with the PWA's real strengths and treat the native shell as a deliberate later move, not a day-one need.

---

## Sources (selected)

Competitor mobile: [getquin](https://www.matchmybroker.com/tools/getquin-review) · [getquin Trustpilot](https://www.trustpilot.com/review/getquin.com) · [Parqet](https://apps.apple.com/us/app/parqet-portfolio-tracker/id1547114259) · [Trade Republic](https://trade-republic.pissedconsumer.com/review.html) · [Trading 212](https://investinginsiders.co.uk/reviews/trading212/) · [Delta widgets](https://support.delta.app/en/collections/3634307-widgets) · [Snowball widgets](https://snowball-analytics.com/blog/snowball-updates-introducing-the-report-ios-widgets-mobile-enhancements/) · [Scalable Trustpilot](https://www.trustpilot.com/review/scalable.capital) · [Sharesight](https://www.moneyhub.co.nz/sharesight-review.html) · [Revolut](https://uk.stockbrokers.com/review/revolut) · [trefolio](https://trefolio.com/) · [trefolio blog](https://trefolio.com/blog/best-portfolio-trackers-europe-2026)

Surfaces on mobile: [table→card](https://medium.com/design-bootcamp/designing-user-friendly-data-tables-for-mobile-devices-c470c82403ad) · [mobile dataviz](https://www.kellton.com/kellton-tech-blog/data-visualization-best-practices-every-app-developer-should-know) · [sparklines](https://www.domo.com/learn/charts/sparkline-chart) · [donut vs bar](https://www.domo.com/learn/charts/donut-charts) · [readability](https://kontent.ai/blog/guide-to-formatting-that-boosts-readability/) · [fintech dashboards](https://www.wildnetedge.com/blogs/fintech-ux-design-best-practices-for-financial-dashboards) · [mobile import](https://blog.csvbox.io/mobile-friendly-spreadsheet-import-flows/) · [chat UX](https://thefrontkit.com/blogs/ai-chat-ui-best-practices) · [Plaid onboarding](https://plaid.com/resources/fintech/fintech-onboarding-process/)

PWA/native: [iOS web push](https://pushpad.xyz/blog/ios-special-requirements-for-web-push-notifications) · [PWA on iOS](https://www.mobiloud.com/blog/progressive-web-apps-ios) · [Declarative Web Push](https://webkit.org/blog/16535/meet-declarative-web-push/) · [install prompt](https://web.dev/learn/pwa/installation-prompt) · [PWA widgets](https://intercom.help/progressier/en/articles/12814946-can-a-pwa-create-home-screen-widgets) · [WebAuthn](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API) · [offline SW](https://www.magicbell.com/blog/offline-first-pwas-service-worker-caching-strategies) · [Web Share](https://caniuse.com/web-share) · [TWA/Bubblewrap](https://www.thinktecture.com/en/pwa/twa-bubblewrap/) · [App Store rejects PWA](https://www.mobiloud.com/blog/publishing-pwa-app-store) · [push stats](https://www.mobiloud.com/blog/push-notification-statistics) · [PWA vs native](https://www.mobiloud.com/blog/progressive-web-apps-vs-native-apps) · [push architecture](https://yundrox.dev/posts/claritybox/building-robust-pwa-push-notifications/) · [priming](https://blog.alertwise.net/ios-web-push-notifications/)

Navigation/IA: [hamburger vs tab bar](https://www.onething.design/post/hamburger-menu-vs-tab-bar) · [tab bar best practices](https://uxplanet.org/bottom-tab-bar-design-best-practices-ef3ee71de0fc) · [thumb zone](https://www.smashingmagazine.com/2016/09/the-thumb-zone-designing-for-mobile-users/) · [touch targets](https://m3.material.io/foundations/designing/structure) · [safe-area env()](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env) · [gesture nav](https://developer.android.com/develop/ui/views/touch-and-input/gestures/gesturenav) · [bottom sheets (NN/g)](https://www.nngroup.com/articles/bottom-sheet/) · [permission priming](https://www.appcues.com/blog/mobile-permission-priming) · [fintech UX](https://procreator.design/blog/best-fintech-ux-practices-for-mobile-apps/) · [2026 fintech trends](https://www.onething.design/post/top-10-fintech-ux-design-practices-2026) · [dark-mode type](https://designshack.net/articles/typography/dark-mode-typography/) · [mobile a11y](https://corpowid.ai/blog/mobile-application-accessibility-practical-humancentered-guide-android-ios)

## Confidence & gaps
- **High confidence:** iOS web-push install requirement & Declarative Web Push specs (primary WebKit/web.dev/MDN); no PWA widgets in 2026; bottom-tab > hamburger; 44/48px targets + safe-area handling; bottom-sheet rules (NN/g); table→card + donut-vs-bar; redesign/extra-tap complaints (Trade Republic + Trading 212 converge); trefolio proves PWA+offline+install works for this exact EU category.
- **Medium / single-source (flagged):** exact stats — web-push delivery ~33% vs native ~95%, finance opt-in ~72%, Android 91%/iOS 44% split, retention multipliers (vendor/Airship-derived); the Trade Republic settings-toggle "undiscoverable" critique; some 2026-trend articles are agency blogs.
- **Thin / not covered:** raw EU forum sentiment (US-biased crawler; mostly aggregators/Trustpilot, not r/Finanzen); DE/PT-specific push benchmarks; **EU/GDPR consent UX for web push** (worth a dedicated follow-up given the audience); screenshot/OCR statement import (unvalidated); foldable/large-screen adaptive layouts (light).
- **Inferences (not sourced):** the 5-tab structure (validate against your own analytics on which surfaces are high-frequency); "descriptive-not-directive" framing layered onto generic UX patterns for the non-advice posture; "~3-min read" word count.
