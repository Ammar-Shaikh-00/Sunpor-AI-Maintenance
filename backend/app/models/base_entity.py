from sqlalchemy import DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.mixins import TimestampMixin
from app.db.base import Base
import uuid

class BaseEntity(Base, TimestampMixin):

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


