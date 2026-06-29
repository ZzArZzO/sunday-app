from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://sunday:sunday_dev_only_change_me@localhost:5432/sunday"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000,http://localhost:3002"
    log_level: str = "INFO"

    anthropic_api_key: str = ""
    anthropic_region: str = "eu"
    # Optional override for EU data-residency endpoint (see docs/LEGAL.md).
    anthropic_base_url: str = ""
    # Two-tier model split (docs/ARCHITECTURE.md). Chat uses Sonnet; the cheap
    # guardrail/summarisation tier uses Haiku.
    anthropic_chat_model: str = "claude-sonnet-4-6"
    anthropic_guard_model: str = "claude-haiku-4-5"
    chat_max_tokens: int = 1024
    # Monthly AI spend cap per user (USD), enforced from the llm_call_log ledger.
    # A margin backstop: once a user crosses it, AI features degrade gracefully
    # until the 1st. Set well above expected usage (see docs verification).
    ai_monthly_budget_free_usd: float = 0.25
    ai_monthly_budget_pro_usd: float = 5.0
    fmp_api_key: str = ""

    # Email delivery (Resend). Empty key → dry-run (render but don't send).
    resend_api_key: str = ""
    email_from: str = "Sunday <briefing@example.com>"
    app_base_url: str = "http://localhost:3002"
    # Weekly Sunday-briefing cron. Off by default; flip on in a deployed instance.
    enable_scheduler: bool = False

    # Native push (Firebase Cloud Messaging, HTTP v1). Both empty → push dry-run
    # (logged, not sent), like the email tier without a Resend key. iOS routes
    # through FCM too (upload the APNs key to Firebase). See docs/MOBILE_PUSH_SETUP.md.
    fcm_project_id: str = ""
    # Path to the Firebase service-account key JSON (keep it out of source control).
    fcm_credentials_json: str = ""

    # --- Auth ---
    # Public URL of the API itself (magic links point here). The web app is app_base_url.
    api_base_url: str = "http://localhost:8000"
    # When False (dev), routes fall back to the demo user if there's no session.
    # Set True in production so unauthenticated requests get 401.
    auth_required: bool = False
    # Set True when serving the cookie over HTTPS (production).
    cookie_secure: bool = False

    demo_user_id: int = 1

    # --- Crypto address sync (read-only on-chain balances) ---
    # Live, Pro-only. Empty key → address sync disabled (endpoints return 503),
    # like the LLM/email/billing tiers. base_url + response mapping target the
    # chosen indexer (e.g. Zerion / Covalent / Alchemy) — see services/connectors.
    crypto_indexer_api_key: str = ""
    crypto_indexer_base_url: str = "https://api.example-indexer.com/v1"

    # --- Exchange API sync (read-only keys via CCXT) ---
    # Fernet key (base64, 32 bytes) used to encrypt stored exchange API secrets at
    # rest. Generate with: python -c "from cryptography.fernet import Fernet;
    # print(Fernet.generate_key().decode())". Empty → exchange sync disabled (503).
    connection_secret_key: str = ""

    # --- Billing (Stripe) ---
    # Use a RESTRICTED key (rk_…) with least privilege, never a secret key in source.
    # Empty → billing disabled (endpoints return 503), like the LLM/email tiers.
    stripe_api_key: str = ""
    # Webhook signing secret (whsec_…). Required to accept webhook events.
    stripe_webhook_secret: str = ""
    # Price ID (price_…) for the Pro €9/mo plan, created in the Stripe Dashboard.
    stripe_price_pro: str = ""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
