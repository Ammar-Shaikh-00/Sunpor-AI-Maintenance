"""add operator_entries for unified operator input forms

Revision ID: g4b9e2f8a106
Revises: f3a8c2d1e015
Create Date: 2026-08-03 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "g4b9e2f8a106"
down_revision: Union[str, Sequence[str], None] = "f3a8c2d1e015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    json_type = (
        postgresql.JSONB(astext_type=sa.Text())
        if bind.dialect.name == "postgresql"
        else sa.JSON()
    )

    op.create_table(
        "operator_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column(
            "production_run_id",
            sa.Integer(),
            sa.ForeignKey("production_runs.id"),
            nullable=True,
        ),
        sa.Column("event_time", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="open"),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("batch_label", sa.String(length=255), nullable=True),
        sa.Column("material_label", sa.String(length=255), nullable=True),
        sa.Column("recipe_label", sa.String(length=255), nullable=True),
        sa.Column("machine_label", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'::jsonb")
            if bind.dialect.name == "postgresql"
            else sa.text("'{}'"),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_operator_entries_company_id", "operator_entries", ["company_id"])
    op.create_index("ix_operator_entries_category", "operator_entries", ["category"])
    op.create_index(
        "ix_operator_entries_production_run_id",
        "operator_entries",
        ["production_run_id"],
    )
    op.create_index("ix_operator_entries_event_time", "operator_entries", ["event_time"])
    op.create_index("ix_operator_entries_status", "operator_entries", ["status"])
    op.create_index("ix_operator_entries_operator_id", "operator_entries", ["operator_id"])
    op.create_index(
        "ix_operator_entries_category_event_time",
        "operator_entries",
        ["category", "event_time"],
    )


def downgrade() -> None:
    op.drop_index("ix_operator_entries_category_event_time", table_name="operator_entries")
    op.drop_index("ix_operator_entries_operator_id", table_name="operator_entries")
    op.drop_index("ix_operator_entries_status", table_name="operator_entries")
    op.drop_index("ix_operator_entries_event_time", table_name="operator_entries")
    op.drop_index("ix_operator_entries_production_run_id", table_name="operator_entries")
    op.drop_index("ix_operator_entries_category", table_name="operator_entries")
    op.drop_index("ix_operator_entries_company_id", table_name="operator_entries")
    op.drop_table("operator_entries")
