"""add production run recipe/order and daily quality operator

Revision ID: e7f2a1b3c904
Revises: d91f4b7e2c11
Create Date: 2026-07-03 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f2a1b3c904"
down_revision: Union[str, Sequence[str], None] = "d91f4b7e2c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "production_runs",
        sa.Column("recipe_number", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "production_runs",
        sa.Column("production_order", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "daily_quality_inputs",
        sa.Column("operator_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_daily_quality_inputs_operator_id_users",
        "daily_quality_inputs",
        "users",
        ["operator_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_daily_quality_inputs_operator_id_users",
        "daily_quality_inputs",
        type_="foreignkey",
    )
    op.drop_column("daily_quality_inputs", "operator_id")
    op.drop_column("production_runs", "production_order")
    op.drop_column("production_runs", "recipe_number")
