"""add_vitals_to_action_log

Revision ID: a1b2c3d4e5f6
Revises: 48825e83cd6b
Create Date: 2026-06-21 01:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "48825e83cd6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("action_log_entries", sa.Column("vitals_before", sa.JSON, nullable=True))
    op.add_column("action_log_entries", sa.Column("vitals_after", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("action_log_entries", "vitals_after")
    op.drop_column("action_log_entries", "vitals_before")
