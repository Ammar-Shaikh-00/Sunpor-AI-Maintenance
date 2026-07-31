from datetime import datetime

from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import utc_now_naive


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )
