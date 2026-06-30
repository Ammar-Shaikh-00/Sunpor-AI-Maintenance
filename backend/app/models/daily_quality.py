from datetime import datetime

from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey, DateTime

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class DailyQualityInput(Base, TimestampMixin):

    __tablename__ = "daily_quality_inputs"

    id: Mapped[int] = mapped_column(primary_key=True)

    production_run_id: Mapped[int] = mapped_column(
        ForeignKey("production_runs.id")
    )

    shift: Mapped[str] = mapped_column(
        String(50)
    )

    input_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    open_holes_percent: Mapped[float] = mapped_column(
        Float
    )

    sieve_distribution_percent: Mapped[float] = mapped_column(
        Float
    )

    foaming_behavior: Mapped[str] = mapped_column(
        String(50)
    )

    comment: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    production_run = relationship(
        "ProductionRun",
        back_populates="quality_inputs"
    )
