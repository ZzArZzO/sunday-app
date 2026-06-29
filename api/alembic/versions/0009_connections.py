"""connections: per-portfolio import sources + lot provenance

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, Sequence[str], None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "portfolio_id",
            sa.Integer(),
            sa.ForeignKey("portfolios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_connections_portfolio_id", "connections", ["portfolio_id"])

    op.add_column("lots", sa.Column("connection_id", sa.Integer(), nullable=True))
    op.create_index("ix_lots_connection_id", "lots", ["connection_id"])
    op.create_foreign_key(
        "fk_lots_connection_id",
        "lots",
        "connections",
        ["connection_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_lots_connection_id", "lots", type_="foreignkey")
    op.drop_index("ix_lots_connection_id", table_name="lots")
    op.drop_column("lots", "connection_id")
    op.drop_index("ix_connections_portfolio_id", table_name="connections")
    op.drop_table("connections")
