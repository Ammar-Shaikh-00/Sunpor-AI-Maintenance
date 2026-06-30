from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )
