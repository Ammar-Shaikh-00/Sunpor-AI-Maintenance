from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import ForeignKey

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AuditLog(Base, TimestampMixin):

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    action: Mapped[str] = mapped_column(
        String(100)
    )

    table_name: Mapped[str] = mapped_column(
        String(100)
    )

    record_id: Mapped[str] = mapped_column(
        String(100)
    )

    old_value: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    new_value: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )