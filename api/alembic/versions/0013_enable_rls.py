"""security: enable row level security on all tables (Supabase Data API hardening)

The app's own backend connects with a privileged Postgres role and never goes
through Supabase's PostgREST Data API, so these tables have no legitimate
reason to be reachable by the `anon`/`authenticated` roles. Locking them down
with RLS enabled and zero policies is a default-deny that closes that door
without touching how the backend itself connects.

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-02
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "alembic_version",
    "users",
    "portfolios",
    "positions",
    "lots",
    "briefings",
    "portfolio_snapshots",
    "magic_tokens",
    "sessions",
    "llm_call_log",
    "push_tokens",
    "connections",
    "weekly_deliveries",
    "isin_symbols",
]


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY")
