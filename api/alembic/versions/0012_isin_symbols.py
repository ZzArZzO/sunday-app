"""isin_symbols: cache of ISIN -> market-symbol resolutions

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, Sequence[str], None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "isin_symbols",
        sa.Column("isin", sa.String(12), primary_key=True),
        sa.Column("symbol", sa.String(32), nullable=True),
        sa.Column("source", sa.String(16), nullable=False, server_default="openfigi"),
        sa.Column(
            "resolved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("isin_symbols")
