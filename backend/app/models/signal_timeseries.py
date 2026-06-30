from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base


class SignalTimeSeries(Base):

    __tablename__ = "signal_timeseries"

    __table_args__ = (
        Index("idx_signal_timeseries_timestamp", "timestamp"),
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        primary_key=True
    )

    signal_id: Mapped[int] = mapped_column(
        ForeignKey("signal_catalog.id"),
        primary_key=True
    )

    value_raw: Mapped[float] = mapped_column(
        Float
    )

    value_scaled: Mapped[float] = mapped_column(
        Float
    )

    quality: Mapped[str] = mapped_column(
        String(50)
    )

    source: Mapped[str] = mapped_column(
        String(100)
    )

    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    signal = relationship(
        "SignalCatalog",
        back_populates="timeseries"
    )
