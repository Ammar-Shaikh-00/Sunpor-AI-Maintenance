from sqlalchemy import String
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base

class ProductionEvent(Base):

    __tablename__ = "production_events"

    

    id: Mapped[int] = mapped_column(primary_key=True)

    production_run_id: Mapped[int] = mapped_column(
        ForeignKey("production_runs.id")
    )

    event_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    level_1: Mapped[str] = mapped_column(
        String(255)
    )

    level_2: Mapped[str] = mapped_column(
        String(255)
    )

    level_3: Mapped[str] = mapped_column(
        String(255)
    )

    reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    comment: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    operator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    production_run = relationship(
    "ProductionRun",
    back_populates="events"
)
