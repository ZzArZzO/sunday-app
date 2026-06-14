# Mobile auth plan — token alongside cookies (Build 2 unblocker)

*Add a Bearer-token auth path for the Capacitor app without changing the web's cookie auth. Design only — approve before code.*

## Why this is small

The existing session token (`services/auth/tokens.py`) is already an **opaque, SHA-256-hashed, 30-day, revocable** token stored in `UserSession`. The web just happens to *deliver* it as an httpOnly cookie (`verify` → `set_cookie`) and *read* it from `request.cookies`. So mobile token auth = **deliver the same token via JSON + read it from the `Authorization` header**. No JWT, no new token type, no migration, no change to the web flow.

## Backend (3 small additions, everything else reused)

1. **`deps.get_current_user` + `/api/auth/me`** — also accept `Authorization: Bearer <token>`. Resolution order: **Authorization header → session cookie → demo fallback**, all funnelling into the existing `auth_tokens.lookup_session`. One small helper; every endpoint becomes token-capable for free (they all depend on `get_current_user`).

2. **New `POST /api/auth/exchange {magic_token}` → `{ session_token, email, country }`** — the mobile equivalent of the web's "verify-redirect-sets-cookie". It consumes the magic token (same `consume_magic_token`) and returns the session token as JSON instead of a cookie. Web keeps its `GET /verify` redirect untouched.

3. *(Later, Build 3)* deep-link the magic-email link so tapping it opens the installed app (`sunday://auth?token=…`) which calls `exchange`.

Reuses unchanged: `UserSession`, `create_session`, `lookup_session`, `revoke_session`, TTLs. **Logout still works** (revokes the row) for both cookie and token.

## Frontend (2 small additions)

1. **`lib/api.ts`** — add `Authorization: Bearer <token>` to requests when a token is present; keep `credentials: "include"` for web. A `getAuthToken()` returns the stored token on mobile, `null` on web — so the *same* code uses cookie on web and Bearer on mobile, no branching by build.

2. **`lib/auth.ts`** — a mobile sign-in path: `requestMagicLink(email)` (unchanged) → tap link → `exchangeMagicToken(magicToken)` → store the returned `session_token`. Web sign-in is unchanged (cookie via redirect).

## Token storage

| Platform | Where | Notes |
|---|---|---|
| **Web** | httpOnly cookie (unchanged) | XSS-safe; the parallel design |
| **Mobile (Capacitor)** | Keychain / Keystore via secure-storage plugin | optionally biometric-gated (Build 5); `getAuthToken()` reads it |

## Why it's clean / non-conflicting

- **Web auth untouched** — zero change to the parallel session's cookie design; the additions are purely additive (an extra header check + one new endpoint).
- **Bearer needs no credentialed CORS** → removes the SameSite=None / cross-origin-cookie problem that breaks cookies in a WebView. The static/mobile case gets *simpler*, not harder.
- **Same revocable opaque token** → security posture and logout semantics identical.

## Sequence

1. Backend: header-aware `get_current_user` + `/me` + `exchange` endpoint (+ tests for the header path and exchange).
2. Frontend: `getAuthToken()` + `api.ts` Bearer branch + mobile `exchangeMagicToken`.
3. **Unblocks Build 2:** the four `force-dynamic` pages convert to client-side fetch (work with either auth path) → static export succeeds → **Build 3 (Capacitor)**, where the token lands in secure storage.

## Effort
Small. Backend ≈ a helper + one endpoint + 2 tests. Frontend ≈ a token getter + one header line + one sign-in function. No DB migration. No web regression risk (additive).
