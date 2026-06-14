"""portfolio snapshots: net-worth history for week-over-week

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.Integer(),
            sa.ForeignKey("portfolios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("captured_on", sa.Date(), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_value_eur", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_cost_eur", sa.Numeric(18, 2), nullable=False),
        sa.Column("eur_usd_rate", sa.Numeric(12, 6), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("portfolio_id", "captured_on", name="uq_snapshot_portfolio_day"),
    )
    op.create_index(
        "ix_portfolio_snapshots_portfolio_id",
        "portfolio_snapshots",
        ["portfolio_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_portfolio_snapshots_portfolio_id", table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")
