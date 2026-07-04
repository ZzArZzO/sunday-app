# Deploying to the Hetzner box

One CX23 (or larger) server runs both containers — `web` and `api` — behind
a Caddy reverse proxy that handles HTTPS automatically. No local Postgres:
`DATABASE_URL` points at the Supabase project.

## One-time server setup

1. Create the server (Ubuntu 24.04 LTS, Falkenstein or Nuremberg, SSH-key auth
   only — see the SSH key generated for this in `~/.ssh/sunday_hetzner`).
2. SSH in and install Docker:
   ```sh
   curl -fsSL https://get.docker.com | sh
   ```
3. Clone the repo to the exact path the CI deploy step expects:
   ```sh
   git clone https://github.com/ZzArZzO/sunday-app.git /opt/sunday-app
   cd /opt/sunday-app
   ```
4. Create `/opt/sunday-app/.env` with real production values — see
   `.env.example`'s "Production deploy" section for the required keys
   (`DATABASE_URL`, `API_CORS_ORIGINS`, `APP_BASE_URL`, `API_BASE_URL`,
   `WEB_DOMAIN`, `API_DOMAIN`, rotated `ANTHROPIC_API_KEY`/`STRIPE_*`,
   `RESEND_API_KEY`, `EMAIL_FROM`, `CONNECTION_SECRET_KEY`). This file never
   leaves the box — it isn't touched by CI.
5. Point DNS: `A` record for both `WEB_DOMAIN` and `API_DOMAIN` at the
   server's IPv4 address.
6. First deploy, run manually on the box:
   ```sh
   docker compose -f docker-compose.prod.yml up -d --build
   ```
   Caddy requests Let's Encrypt certificates for both domains on first
   request — DNS must already be pointing at the box before this step, or
   certificate issuance fails.
7. Confirm: `curl https://$API_DOMAIN/health` and open `https://$WEB_DOMAIN`.

## GitHub Actions secrets (for the `deploy` job in `ci.yml`)

| Secret | Value |
|---|---|
| `HETZNER_HOST` | The server's IPv4 address or hostname |
| `HETZNER_SSH_USER` | The SSH user (`root`, or a deploy user with Docker access) |
| `HETZNER_SSH_KEY` | The **private** half of the deploy keypair — add a dedicated key here, not your personal one |

After the one-time setup above, every push to `master` (once `pytest` and the
web build both pass) SSHes in, fast-forwards the checkout, and rebuilds both
containers.

## The weekly-email scheduler

`ENABLE_SCHEDULER=true` must be set on **exactly one** running instance. If
you ever scale to more than one API container, move this to a dedicated
worker process instead — see `api/app/services/delivery/scheduler.py` and
`docs/business/DEPLOYMENT_AND_MARKETING.md` A.3.
