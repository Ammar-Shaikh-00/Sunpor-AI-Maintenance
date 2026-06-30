from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Enum,
    Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import ProductionRunStatus


class ProductionRun(Base, TimestampMixin):
    __tablename__ = "production_runs"

    __table_args__ = (
        Index("idx_run_start_time", "start_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id")
    )

    production_line_id: Mapped[int] = mapped_column(
        ForeignKey("production_lines.id")
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    end_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    material_type_id: Mapped[int] = mapped_column(
        ForeignKey("material_types.id")
    )

    is_trial: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    shift_id: Mapped[int] = mapped_column(
        ForeignKey("shifts.id")
    )

    operator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    status: Mapped[ProductionRunStatus] = mapped_column(
        Enum(ProductionRunStatus),
        default=ProductionRunStatus.CREATED
    )

    comment: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    events: Mapped[list["ProductionEvent"]] = relationship(
        back_populates="production_run"
    )

    material_behaviors: Mapped[list["MaterialBehaviorEvent"]] = relationship(
        back_populates="production_run"
    )

    material_blocks: Mapped[list["MaterialBlock"]] = relationship(
        back_populates="production_run"
    )

    quality_inputs: Mapped[list["DailyQualityInput"]] = relationship(
        back_populates="production_run"
    )

    predictions: Mapped[list["MLPrediction"]] = relationship(
        back_populates="production_run"
    )