from datetime import datetime

from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey, DateTime, Integer

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base


class MaterialBehaviorEvent(Base):

    __tablename__ = "material_behavior_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    production_run_id: Mapped[int] = mapped_column(
        ForeignKey("production_runs.id")
    )

    event_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    behavior_type: Mapped[str] = mapped_column(
        String(255)
    )

    severity: Mapped[int] = mapped_column(
        Integer
    )

    comment: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    operator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    production_run = relationship(
        "ProductionRun",
        back_populates="material_behaviors"
    )
