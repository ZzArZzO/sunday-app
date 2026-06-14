# Sunday App — Cross-Platform Decision (web + iOS + Android)

*How to take the existing Next.js web app to real iOS + Android apps: Capacitor vs React Native/Expo vs Flutter vs TWA — for a solo founder, EU fintech, with a FastAPI backend.*

**Date:** June 2026
**Question:** Sunday should be a web app **and** native apps on the App Store + Play Store. What's the right cross-platform architecture given a complete Next.js 14 (App Router) web app + separate FastAPI backend, solo founder (on Windows), and needs: native push (the weekly ritual), home-screen widgets, biometric lock, offline, EU privacy.
**Method:** Multi-source web research (WebSearch + WebFetch) across four streams — Capacitor+Next.js, React Native/Expo, Flutter+TWA, and cross-cutting decision factors (App Store 4.2, capability parity, cost, EU/DMA, GDPR, security). ~80 sources reviewed.
**Confidence:** High on platform facts (Apple 4.2, store fees, EU DMA, capability gaps, the SSR/static-export constraint). Medium on effort multipliers and perf numbers (vendor/agency blogs — directional). Several comparison sources have a promotional slant; cross-checked where possible.

---

## 0. Recommendation (the short version)

**Use Capacitor — wrap the existing Next.js/React app — as the path to both stores. Reserve a React Native rebuild for *later*, only if native feel becomes the differentiator.**

Every solo-founder axis points the same way: Capacitor reuses ~100% of your existing UI and ships to both stores in ~weeks; React Native and Flutter both mean **rebuilding the entire mobile UI** (RN keeps your React skills + logic; Flutter is a full Dart rewrite). The two things that *look* like reasons to pick RN/Flutter — home-screen widgets and "native feel" — don't actually rescue them here: **home-screen widgets require hand-written Swift/Kotlin code in *all three* frameworks**, and Sunday's data-dashboard profile sits comfortably inside Capacitor's "good enough" performance zone.

**But adopt Capacitor with eyes open to two real costs** (detailed in §3): a bounded **SSR→client refactor** of your Next.js app, and **native widget code** you'll write regardless. Neither changes the recommendation; both should be budgeted.

The honest consensus across the sources: *"If you already have a React/Next web app, start with Capacitor and validate; pivot to React Native only if native polish becomes a constraint."* ([Kanopy](https://kanopylabs.com/blog/capacitor-vs-react-native-vs-flutter), [NextNative](https://nextnative.dev/comparisons/capacitor-vs-react-native))

---

## 1. The decision at a glance

| Axis (weighted for Sunday) | **Capacitor** | React Native / Expo | Flutter | TWA / PWA-wrap |
|---|---|---|---|---|
| Reuse existing Next.js/React UI | **~100% (wrap it)** | Logic/types yes, **UI rebuilt** | **None (Dart rewrite)** | 100% (it *is* the PWA) |
| Time to both stores (from today) | **~3–4 weeks** | ~8–12 weeks | Longest (full rebuild) | Android days; **iOS blocked** |
| Web-dev learning curve | **Lowest (web only)** | Low (2–4 wks RN specifics) | Highest (Dart, 4–8 wks) | Lowest |
| Native push / biometric / secure storage | ✅ plugins | ✅ first-class | ✅ first-class | ⚠️ weak on iOS |
| **Home-screen widgets** | ⚠️ **native Swift/Kotlin needed** | ⚠️ iOS good, **Android native needed** | ⚠️ **native needed** | ❌ |
| Native feel / perf ceiling | Lowest (WebView, fine for dashboards) | High | Highest | Lowest |
| iOS build from **Windows** | ⚠️ needs macOS or **cloud-Mac CI** | ✅ **EAS builds from Windows** | needs macOS/CI | n/a |
| App Store 4.2 risk | Manageable (native nav+push+polish) | Low | Low | **High on iOS** (PWABuilder-iOS archived Sep 2025) |
| Solo maintenance burden | **Lowest (one codebase)** | Two front-ends | Two front-ends + new lang | Lowest |
| Fintech precedent | Afterpay/Square (thin) | **Coinbase, Revolut, Robinhood, Chime** | **Nubank, Google Pay** | — |

**Reads as:** Capacitor wins decisively on reuse/speed/maintenance; RN/Flutter win on native feel at the cost of a full UI rebuild; TWA is a cheap Android-only add-on, not an iOS answer.

---

## 2. Why not the others (honest)

- **React Native/Expo** is the strongest *native* option that still reuses your React skills, and **EAS Build/Submit can ship iOS from Windows without a Mac** ([Expo](https://docs.expo.dev/submit/introduction/)) — a genuine plus. Its precedent in fintech is the best (Coinbase/Revolut/Robinhood/Chime). **But the mobile UI is a rebuild, not a port** — no `div`/CSS/Tailwind reuse; NativeWind narrows but doesn't close the gap ([NativeWind](https://www.nativewind.dev/docs/core-concepts/differences)) — and you'd carry two front-ends forever. For a solo founder who *already has a polished web UI*, that's a large, ongoing tax for native polish Sunday doesn't yet need. **This is the right "pivot to" option, not the right "start with" option.**
- **Flutter** is the best raw performance/native-feel and proven at fintech scale (Nubank, Google Pay), but it's the **highest-cost, lowest-reuse** choice: a full Dart rewrite, a new language, and — critically — **Flutter Web won't unify your stack** (it's canvas-rendered and SEO-hostile; Flutter *itself* says keep the marketing site in HTML/Next.js), so you'd still run two web codebases *and* rebuild mobile. ([Flutter renderers](https://docs.flutter.dev/platform-integration/web/renderers), [LeanCode SEO](https://leancode.co/glossary/flutter-and-seo))
- **TWA / PWA-to-store** gets you into **Google Play** cheaply (Bubblewrap, Lighthouse ≥80, $25 once) — worth doing for Android regardless. But **iOS is the binding constraint**: Apple rejects PWAs under Guideline 4.2, and **PWABuilder's iOS path was archived Sept 2025** (now unmaintained). Capacitor is the credible iOS wrapper. ([MobiLoud](https://www.mobiloud.com/blog/publishing-pwa-app-store), [PWABuilder-iOS archived](https://github.com/pwa-builder/pwabuilder-ios-app-store))

---

## 3. The two real costs of Capacitor (budget for these)

### 3.1 The SSR → static-export refactor
Capacitor bundles **static** HTML/JS/CSS into the native shell — there's **no Node runtime inside the WebView**, so Next.js SSR, server components with server-side fetching, server Actions, API routes, and **`force-dynamic`** don't run in the bundle. ([Capgo](https://capgo.app/blog/building-a-native-mobile-app-with-nextjs-and-capacitor/), [Medium](https://medium.com/@shailendraparihar3630/i-built-a-mobile-app-the-wrong-way-so-you-dont-have-to-d7a46956d71a))

**The production path** is `output: 'export'` (static) + `images.unoptimized: true`, with server-rendered screens converted to **client components that fetch the FastAPI backend directly**, and dynamic SSG routes (`/x/[id]`) replaced with **query-param client pages** (`/detail?id=…`).

**Why this is *bounded* for Sunday, not a rewrite:** your data layer is **already an external API (FastAPI)**, and several surfaces (`ChatPanel`, `BenchmarkChart`, `EventsCard`, `AllocationTreemap`, `CsvUploader`) are *already client components fetching the API*. The work is converting the remaining server components (`dashboard/page.tsx`, `briefing/page.tsx` — currently `force-dynamic` server fetches) to client fetching. That's real but contained — and arguably *worth doing anyway* for a more app-like, instant-navigation feel.
> ⚠️ Avoid the `server.url` shortcut (point Capacitor at hosted Next.js to keep SSR): it **breaks offline**, drifts plugin/bundle versions, and is officially discouraged + store-risky. Not viable for an offline-capable fintech. ([GitHub #5075](https://github.com/ionic-team/capacitor/discussions/5075))

### 3.2 Home-screen widgets need native code (in every framework)
The most-loved mobile feature (from the UX research) is the one no cross-platform framework gives for free: **iOS WidgetKit (SwiftUI) and Android App Widgets (Kotlin/Glance) must be hand-written**; Capacitor/RN/Flutter plugins only *bridge data* to them. ([capacitor-native-widgets](https://github.com/alesmraz/capacitor-native-widgets)) So widgets are a fixed cost regardless of framework — they do **not** argue for RN/Flutter over Capacitor. Plan a small, isolated native widget extension when you tackle widgets (a "Next" tier item, not day one).

### 3.3 (Minor) iOS builds need macOS — but not a Mac you own
Capacitor iOS builds require Xcode/macOS. A Windows solo founder uses **cloud-Mac CI** — Ionic Appflow, Codemagic, Bitrise, or GitHub Actions macOS runners — to build/sign/submit without owning a Mac. (RN+EAS avoids this entirely; weigh it, but it's a solved problem, not a blocker.)

---

## 4. Passing Apple Guideline 4.2 ("minimum functionality")
Apple rejects "repackaged websites." A Capacitor app passes when it's clearly app-like. Design checklist (all supported by Capacitor): ([MobiLoud](https://www.mobiloud.com/blog/app-store-review-guidelines-webview-wrapper))
- ✅ **Native bottom tab bar + native headers** (the mobile UX research's 5-tab structure) — not a web hamburger.
- ✅ **Native push notifications** (the single strongest 4.2 differentiator — and Sunday's hero ritual).
- ✅ **Biometric login** + branded splash + native loading indicators.
- ✅ **Custom offline screens** (not a browser error page).
- ✅ Open external links in an in-app browser; persistent login.
- ⚠️ Bundle assets (Path A), **not** a `server.url` shell of the website.
> Risk note: 4.2 review is human/subjective — even native-push Capacitor apps have occasionally been rejected; budget a resubmission cycle (days–weeks). Also keep dependency hygiene (avoid old UIWebView refs → ITMS-90338). ([Ionic forum](https://forum.ionicframework.com/t/apple-4-2-minimum-functionality/189688))

---

## 5. Native capability parity (Capacitor, for Sunday's checklist)

| Need | Capacitor status |
|---|---|
| **Push (FCM/APNs)** | ✅ first-class (`@capacitor/push-notifications`, `@capacitor-firebase/messaging`) |
| **Biometric lock** | ✅ solid community (`@capgo/capacitor-native-biometric`, `aparajita/...`) |
| **Secure token storage** | ✅ Keychain/Keystore plugins; Capawesome **Vault** (biometric-gated AES-256-GCM); Ionic **Identity Vault** (enterprise) |
| **Deep / universal links** | ✅ standard config |
| **Web Share** | ✅ `@capacitor/share` |
| **Offline (app shell)** | ✅ static bundle loads offline; **data** caching is your build (service worker / local store) |
| **Home-screen widgets** | ⚠️ native Swift/Kotlin required (bridge plugins only pass data) |
| **Jailbreak/root detection, SSL pinning** | ✅ via plugins (Talsec/freeRASP etc.) — fintech hygiene |

---

## 6. Cost, store, EU & compliance notes
- **Fees:** Apple Developer **$99/yr**, Google Play **$25 once**. Subscriptions: **Small Business Program 15%** (<$1M/yr) — Sunday's tier. ([SplitMetrics](https://splitmetrics.com))
- **Review:** Apple ~24–72h (human); Google hours–1 day.
- **EU/DMA:** the per-install Core Technology Fee → a **5% Core Technology Commission** (Jan 2026), but **<1% of developers ever pay it**; alternative EU distribution adds more overhead than it saves — **stay on standard App Store terms** at launch. ([RevenueCat](https://www.revenuecat.com/blog/apple-eu-dma-update-june-2025), [Apple DMA](https://developer.apple.com/support/dma))
- **GDPR (privacy-first DE/PT):** **technically gate analytics/tracking SDKs behind explicit consent** (not a banner that fires SDKs anyway — "privacy theater" draws fines); app-store privacy labels must match real behavior. On-brand for Sunday's privacy positioning. ([CookieScript](https://cookie-script.com))
- **Security:** Keychain/Keystore (never plain prefs) for tokens; biometric must gate *data* not just UI; SSL pinning + OAuth/PKCE; jailbreak/root detection. Holding **no funds** keeps Sunday out of PCI scope, but financial *data* still mandates encryption-at-rest + consent + data-subject rights.

---

## 7. Recommended architecture & sequence

**Architecture:** one Next.js/React codebase → Capacitor wraps it for iOS + Android; Next.js (static export for the app build, full SSR for the public marketing/SEO site) + FastAPI backend unchanged. Android also gets a TWA/Play listing if you want the cheap second listing; iOS via Capacitor.

**Phased plan (high level):**
1. **Prep the web app** — finish the responsive mobile shell from `MOBILE_UX_RESEARCH.md` (bottom tab bar, cards, safe areas); convert `force-dynamic` server pages (`dashboard`, `briefing`) to client components fetching FastAPI; switch to `output: 'export'` for the app build (keep a separate SSR build for the marketing site).
2. **Add Capacitor** — `@capacitor/core` + iOS/Android projects; native tab-bar shell; splash/icons; set up cloud-Mac CI (Codemagic/Appflow).
3. **Native capabilities** — push (FCM/APNs) wired to the existing `delivery/scheduler`; biometric lock + secure storage; deep links; offline app-shell + last-briefing cache.
4. **Store submission** — Apple ($99) + Play ($25); 4.2 checklist (§4); GDPR consent gating + privacy labels.
5. **Later** — native home-screen widget (Swift/Kotlin) when retention justifies it; revisit React Native only if native feel becomes the differentiator.

---

## 8. When to reconsider (pivot signals to RN)
Switch the *start* decision to React Native only if: heavy real-time/gesture-rich UI becomes core; Android widget parity is a day-one must; WebView feel measurably hurts retention; or you hire mobile help and want a native codebase. Until then, Capacitor's reuse advantage dominates for a solo founder.

---

## Sources (selected)
Capacitor+Next.js: [Capgo](https://capgo.app/blog/building-a-native-mobile-app-with-nextjs-and-capacitor/) · [Medium: what breaks](https://medium.com/@shailendraparihar3630/i-built-a-mobile-app-the-wrong-way-so-you-dont-have-to-d7a46956d71a) · [server.url #5075](https://github.com/ionic-team/capacitor/discussions/5075) · [Push API](https://capacitorjs.com/docs/apis/push-notifications) · [Vault plugin](https://capawesome.io/blog/announcing-the-capacitor-vault-plugin/) · [native widgets](https://github.com/alesmraz/capacitor-native-widgets) · [deep links](https://capacitorjs.com/docs/guides/deep-links)
React Native/Expo: [NativeWind differences](https://www.nativewind.dev/docs/core-concepts/differences) · [Solito](https://solito.dev/) · [EAS Submit](https://docs.expo.dev/submit/introduction/) · [Expo notifications](https://docs.expo.dev/versions/latest/sdk/notifications/) · [Expo widgets](https://docs.expo.dev/versions/latest/sdk/widgets/) · [Shopify 5yr RN](https://shopify.engineering/five-years-of-react-native-at-shopify)
Flutter/TWA: [Flutter web renderers](https://docs.flutter.dev/platform-integration/web/renderers) · [Flutter & SEO](https://leancode.co/glossary/flutter-and-seo) · [home_widget](https://pub.dev/packages/home_widget) · [Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap) · [PWABuilder-iOS archived](https://github.com/pwa-builder/pwabuilder-ios-app-store)
Decision factors: [4.2 webview wrapper](https://www.mobiloud.com/blog/app-store-review-guidelines-webview-wrapper) · [publishing PWA to stores](https://www.mobiloud.com/blog/publishing-pwa-app-store) · [Capacitor vs RN vs Flutter](https://kanopylabs.com/blog/capacitor-vs-react-native-vs-flutter) · [NextNative comparison](https://nextnative.dev/comparisons/capacitor-vs-react-native) · [Apple DMA](https://developer.apple.com/support/dma) · [RevenueCat DMA](https://www.revenuecat.com/blog/apple-eu-dma-update-june-2025) · [GDPR SDK consent](https://cookie-script.com)

## Confidence & gaps
- **High confidence:** the static-export/no-SSR constraint; widgets need native code in all frameworks; Apple rejects PWAs / Google accepts TWAs; PWABuilder-iOS archived; 4.2 pass criteria; store fees + EU DMA direction; capability parity.
- **Medium / directional:** effort multipliers (3–4 vs 8–12 weeks), perf rankings, market share — vendor/agency blogs; treat exact numbers as estimates.
- **Vendor slant flagged:** NextNative (sells a Capacitor product), Kanopy, MobiLoud (sells a wrapper) tilt pro-wrapper; the *facts* (capability gaps, 4.2 levers) cross-check, the *framing* may favor Capacitor — discount accordingly.
- **Not closed:** no hard dataset of Capacitor 4.2 approval/rejection *rates* (anecdotal); EU-specific financial-app store rules + SCA/strong-auth for a no-funds tracker (worth a compliance pass); exact effort for Sunday's screens (inferred from the codebase, not measured).
- **Codebase-specific inference:** the "bounded refactor" claim rests on Sunday's data layer already being an external FastAPI + several surfaces already being client components — verify the exact server-component footprint before committing the estimate.
