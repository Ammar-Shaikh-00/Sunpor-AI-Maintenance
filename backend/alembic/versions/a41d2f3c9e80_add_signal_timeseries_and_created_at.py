"""add signal timeseries and created_at fields

Revision ID: a41d2f3c9e80
Revises: feb75f1cfb16
Create Date: 2026-06-10 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a41d2f3c9e80"
down_revision: Union[str, Sequence[str], None] = "feb75f1cfb16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "production_events",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )

    op.add_column(
        "ml_predictions",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        )
    )

    op.create_table(
        "signal_timeseries",
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("signal_id", sa.Integer(), nullable=False),
        sa.Column("value_raw", sa.Float(), nullable=False),
        sa.Column("value_scaled", sa.Float(), nullable=False),
        sa.Column("quality", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column(
            "imported_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["signal_id"], ["signal_catalog.id"]),
        sa.PrimaryKeyConstraint("timestamp", "signal_id")
    )
    op.create_index(
        "idx_signal_timeseries_timestamp",
        "signal_timeseries",
        ["timestamp"],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(
        "idx_signal_timeseries_timestamp",
        table_name="signal_timeseries"
    )
    op.drop_table("signal_timeseries")
    op.drop_column("ml_predictions", "created_at")
    op.drop_column("production_events", "created_at")
