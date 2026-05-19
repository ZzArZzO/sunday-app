"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("country", sa.String(length=2), nullable=False, server_default="DE"),
        sa.Column(
            "timezone", sa.String(length=64), nullable=False, server_default="Europe/Berlin"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False, server_default="Main"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.Integer(),
            sa.ForeignKey("portfolios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("isin", sa.String(length=12), nullable=True),
        sa.Column("asset_class", sa.String(length=16), nullable=False),
        sa.Column("sector", sa.String(length=64), nullable=True),
        sa.Column("region", sa.String(length=32), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("avg_cost_eur", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("last_price_eur", sa.Numeric(18, 4), nullable=True),
        sa.Column("last_price_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])
    op.create_index("ix_positions_ticker", "positions", ["ticker"])

    op.create_table(
        "lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "position_id",
            sa.Integer(),
            sa.ForeignKey("positions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("unit_cost_eur", sa.Numeric(18, 4), nullable=False),
        sa.Column("fees_eur", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_lots_position_id", "lots", ["position_id"])

    op.create_table(
        "briefings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.Integer(),
            sa.ForeignKey("portfolios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_of", sa.String(length=10), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_briefings_portfolio_id", "briefings", ["portfolio_id"])
    op.create_index("ix_briefings_week_of", "briefings", ["week_of"])


def downgrade() -> None:
    op.drop_table("briefings")
    op.drop_table("lots")
    op.drop_table("positions")
    op.drop_table("portfolios")
    op.drop_table("users")
