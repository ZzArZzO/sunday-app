"""weekly delivery idempotency: one row per (user, iso_week)

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, Sequence[str], None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weekly_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("iso_week", sa.String(8), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "iso_week", name="uq_weekly_delivery_user_week"),
    )
    op.create_index("ix_weekly_deliveries_user_id", "weekly_deliveries", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_weekly_deliveries_user_id", table_name="weekly_deliveries")
    op.drop_table("weekly_deliveries")
