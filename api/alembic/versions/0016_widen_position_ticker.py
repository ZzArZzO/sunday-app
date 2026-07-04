"""fix: widen positions.ticker to fit broker-provided instrument names

Brokers without a clean market symbol (Trade Republic, DEGIRO) fall back
to the human-readable instrument name as the "ticker" -- e.g. "FTSE
All-World High Dividend Yield USD (Dist)" (45 chars), well past the
previous 32-character limit. Caused a hard 500
(psycopg.errors.StringDataRightTruncation) importing a real Trade
Republic export with several long ETF names.

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, Sequence[str], None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("positions", "ticker", type_=sa.String(128), existing_type=sa.String(32))


def downgrade() -> None:
    op.alter_column("positions", "ticker", type_=sa.String(32), existing_type=sa.String(128))
