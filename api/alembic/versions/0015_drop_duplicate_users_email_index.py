"""fix: drop duplicate index on users.email

`unique=True` on the column already creates an index backing that
constraint (`users_email_key`); `index=True` created a second, identical
one (`ix_users_email`) covering the same column. Flagged by Supabase's
performance advisor. Keeps the constraint's index, which already serves
both uniqueness checks and email lookups.

Chained after 0014 (the Supabase Auth migration) since both are open as
separate PRs off the same 0013 head — merge this one second.

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0015"
down_revision: Union[str, Sequence[str], None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")


def downgrade() -> None:
    op.create_index("ix_users_email", "users", ["email"])
