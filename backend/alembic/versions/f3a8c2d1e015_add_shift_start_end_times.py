"""add shift start and end times

Revision ID: f3a8c2d1e015
Revises: e7f2a1b3c904
Create Date: 2026-07-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a8c2d1e015"
down_revision: Union[str, Sequence[str], None] = "e7f2a1b3c904"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "shifts",
        sa.Column("start_time", sa.Time(), nullable=True),
    )
    op.add_column(
        "shifts",
        sa.Column("end_time", sa.Time(), nullable=True),
    )

    op.execute(
        """
        UPDATE shifts SET start_time = '06:00:00', end_time = '14:00:00'
        WHERE name = 'Morning'
        """
    )
    op.execute(
        """
        UPDATE shifts SET start_time = '14:00:00', end_time = '22:00:00'
        WHERE name = 'Evening'
        """
    )
    op.execute(
        """
        UPDATE shifts SET start_time = '22:00:00', end_time = '06:00:00'
        WHERE name = 'Night'
        """
    )


def downgrade() -> None:
    op.drop_column("shifts", "end_time")
    op.drop_column("shifts", "start_time")
