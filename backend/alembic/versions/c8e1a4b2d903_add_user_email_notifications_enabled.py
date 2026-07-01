"""add user email_notifications_enabled

Revision ID: c8e1a4b2d903
Revises: b52e7d4f6a91
Create Date: 2026-06-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8e1a4b2d903"
down_revision: Union[str, Sequence[str], None] = "b52e7d4f6a91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_notifications_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.alter_column("users", "email_notifications_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "email_notifications_enabled")
