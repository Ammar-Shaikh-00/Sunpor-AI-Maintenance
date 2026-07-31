"""limit production run statuses and enforce single running per line

Revision ID: d91f4b7e2c11
Revises: c8e1a4b2d903
Create Date: 2026-07-02 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d91f4b7e2c11"
down_revision: Union[str, Sequence[str], None] = "c8e1a4b2d903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE production_runs
        SET status = 'COMPLETED'
        WHERE status IN ('CREATED', 'CANCELLED', 'BLOCKED')
        """
    )

    op.execute("ALTER TYPE productionrunstatus RENAME TO productionrunstatus_old")
    op.execute("CREATE TYPE productionrunstatus AS ENUM ('RUNNING', 'COMPLETED')")
    op.execute(
        """
        ALTER TABLE production_runs
        ALTER COLUMN status TYPE productionrunstatus
        USING status::text::productionrunstatus
        """
    )
    op.execute("ALTER TABLE production_runs ALTER COLUMN status SET DEFAULT 'RUNNING'")
    op.execute("DROP TYPE productionrunstatus_old")

    op.create_index(
        "uq_running_production_run_per_line",
        "production_runs",
        ["production_line_id"],
        unique=True,
        postgresql_where=sa.text("status = 'RUNNING' AND is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_running_production_run_per_line", table_name="production_runs")

    op.execute(
        "CREATE TYPE productionrunstatus_old AS ENUM "
        "('CREATED', 'RUNNING', 'COMPLETED', 'CANCELLED', 'BLOCKED')"
    )
    op.execute(
        """
        ALTER TABLE production_runs
        ALTER COLUMN status TYPE productionrunstatus_old
        USING status::text::productionrunstatus_old
        """
    )
    op.execute("ALTER TABLE production_runs ALTER COLUMN status DROP DEFAULT")
    op.execute("DROP TYPE productionrunstatus")
    op.execute("ALTER TYPE productionrunstatus_old RENAME TO productionrunstatus")
