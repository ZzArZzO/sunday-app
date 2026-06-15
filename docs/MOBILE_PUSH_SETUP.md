# Native push notifications — setup & activation

The Sunday app delivers the **weekly briefing** as a single native push
(Android + iOS). The whole pipeline is built and runs **dry-run by default** — no
notification actually leaves the server until Firebase credentials are
configured, exactly like email delivery runs without a Resend key.

This means everything below the line is testable *now*; the steps above the line
are the one-time external setup that only you can do (they need a Google account
and an Apple Developer account).

## How it works

```
device → POST /api/push/register {token, platform}      (on permission grant)
                     │
                     ▼
            push_tokens table  ──►  weekly briefing cron
                                         │  deliver_to_user(user, db)
                                         ▼
                              push_sender.send_push(...)
                          (FCM HTTP v1, or dry-run if no creds)
```

- **Frontend:** `web/lib/push.ts` requests permission and forwards the OS token;
  `components/PushPrimer.tsx` is the in-app double-opt-in card (shown only in the
  installed app). The plugin is `@capacitor/push-notifications`.
- **Backend:** `routes/push.py` (register / unregister / test),
  `services/delivery/push_registry.py` (token storage),
  `services/delivery/push_sender.py` (FCM v1 send, dry-run fallback). The weekly
  cron fans out in `services/delivery/briefing_delivery.py`.

## Testing without credentials (works today)

1. Sign in on a device build, open **Briefing**, tap **Turn on notifications**.
2. The token is stored (`push_tokens`). `POST /api/push/test` returns
   `{"sent": N, "dry_run": true}` and the server logs `[push dry-run] …`.
3. Backend tests: `pytest tests/test_push.py`.

---

## Activation (one-time, needs your accounts)

### 1. Firebase project (covers both platforms)

1. Create a project at <https://console.firebase.google.com>.
2. **Add Android app** with package `com.sunday.app` → download
   **`google-services.json`** → place at `web/android/app/google-services.json`.
3. **Add iOS app** with bundle id `com.sunday.app` → download
   **`GoogleService-Info.plist`** → place at `web/ios/App/App/GoogleService-Info.plist`.

### 2. iOS — APNs (needs an Apple Developer account, $99/yr)

1. In the Apple Developer portal, create an **APNs Auth Key** (`.p8`).
2. In Firebase → Project Settings → Cloud Messaging → **upload the APNs key**.
   (Routing iOS through FCM means the backend has a single send path.)

### 3. Backend — service account

1. Firebase → Project Settings → Service accounts → **Generate new private key**
   → save the JSON outside source control (it's a secret).
2. Set environment variables for the API:
   ```
   FCM_PROJECT_ID=your-firebase-project-id
   FCM_CREDENTIALS_JSON=/secure/path/service-account.json
   ```
3. Install the token-minting dependency: `pip install google-auth`.

Once set, `push_sender.send_push` switches from dry-run to real FCM v1 delivery
automatically — no code change.

> **Secrets:** `google-services.json`, `GoogleService-Info.plist`, and the
> service-account JSON are gitignored. Never commit them.
