from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.mixins import TimestampMixin


# JSONB on Postgres, JSON elsewhere (portable for tests).
OperatorEntryPayload = JSON().with_variant(JSONB(), "postgresql")


class OperatorEntry(Base, TimestampMixin):
    """
    Unified operator input form entry (spec: Operator Input Forms).

    Answers live in `payload` (JSON). Indexed columns support Recent Entries
    filters, sorting, and detail summaries without parsing payload every time.
    """

    __tablename__ = "operator_entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    production_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("production_runs.id"),
        nullable=True,
        index=True,
    )

    event_time: Mapped[datetime] = mapped_column(
        DateTime,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
    )

    status: Mapped[str] = mapped_column(
        String(64),
        default="open",
        index=True,
    )

    operator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    batch_label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    material_label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    recipe_label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    machine_label: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    payload: Mapped[dict] = mapped_column(
        OperatorEntryPayload,
        default=dict,
    )

    production_run = relationship("ProductionRun")
    operator = relationship("User", foreign_keys=[operator_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
