"""auth: migrate from custom magic-link sessions to Supabase Auth

Adds `users.supabase_user_id` (maps Supabase's auth.users.id UUID onto this
app's existing integer-PK users table — no FK, since auth.users is Supabase's
vendor-managed schema, not ours to reference). Drops `magic_tokens` and
`sessions`, which the app no longer writes to now that auth is verified via
Supabase JWTs (see api/app/services/auth/supabase_jwt.py) rather than an
opaque DB-hash-lookup token.

One atomic migration, not split for rollback safety: there are zero real
production users at the time of this migration, so the rollback-safety
tradeoff that would justify splitting doesn't apply.

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, Sequence[str], None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("supabase_user_id", sa.String(36), nullable=True))
    op.create_index(
        "ix_users_supabase_user_id", "users", ["supabase_user_id"], unique=True
    )

    op.drop_index("ix_sessions_token_hash", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_magic_tokens_token_hash", table_name="magic_tokens")
    op.drop_index("ix_magic_tokens_user_id", table_name="magic_tokens")
    op.drop_table("magic_tokens")


def downgrade() -> None:
    op.create_table(
        "magic_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_magic_token_hash"),
    )
    op.create_index("ix_magic_tokens_user_id", "magic_tokens", ["user_id"])
    op.create_index("ix_magic_tokens_token_hash", "magic_tokens", ["token_hash"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_session_token_hash"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"])

    op.drop_index("ix_users_supabase_user_id", table_name="users")
    op.drop_column("users", "supabase_user_id")
