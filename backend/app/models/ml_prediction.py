from datetime import datetime

from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey, DateTime, Text

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base

class MLPrediction(Base):

    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime
    )

    production_run_id: Mapped[int] = mapped_column(
        ForeignKey("production_runs.id")
    )

    model_name: Mapped[str] = mapped_column(
        String(255)
    )

    prediction_type: Mapped[str] = mapped_column(
        String(255)
    )

    prediction_value: Mapped[float] = mapped_column(
        Float
    )

    confidence: Mapped[float] = mapped_column(
        Float
    )

    input_window_start: Mapped[datetime] = mapped_column(
        DateTime
    )

    input_window_end: Mapped[datetime] = mapped_column(
        DateTime
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    production_run = relationship(
        "ProductionRun",
        back_populates="predictions"
    )
