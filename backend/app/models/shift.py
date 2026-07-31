from datetime import time

from app.db.base import Base
from sqlalchemy import String, Time
from sqlalchemy.orm import Mapped, mapped_column


class Shift(Base):

    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True
    )

    start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    end_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )
