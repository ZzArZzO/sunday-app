"""user settings: FIRE inputs + target allocations

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("annual_expenses_eur", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("annual_savings_eur", sa.Numeric(18, 2), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "expected_real_return_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="5.00",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "safe_withdrawal_rate_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="4.00",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "target_etf_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="60.00",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "target_stock_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="20.00",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "target_crypto_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="15.00",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "target_cash_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="5.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "target_cash_pct")
    op.drop_column("users", "target_crypto_pct")
    op.drop_column("users", "target_stock_pct")
    op.drop_column("users", "target_etf_pct")
    op.drop_column("users", "safe_withdrawal_rate_pct")
    op.drop_column("users", "expected_real_return_pct")
    op.drop_column("users", "annual_savings_eur")
    op.drop_column("users", "annual_expenses_eur")
