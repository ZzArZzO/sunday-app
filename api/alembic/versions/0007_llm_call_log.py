"""observability: per-call LLM cost ledger

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_call_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("feature", sa.String(32), nullable=False),
        sa.Column("model", sa.String(48), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("portfolio_id", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_write_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
    )
    op.create_index("ix_llm_call_log_created_at", "llm_call_log", ["created_at"])
    op.create_index("ix_llm_call_log_user_id", "llm_call_log", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_llm_call_log_user_id", table_name="llm_call_log")
    op.drop_index("ix_llm_call_log_created_at", table_name="llm_call_log")
    op.drop_table("llm_call_log")
