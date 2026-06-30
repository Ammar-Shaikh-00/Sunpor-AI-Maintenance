from datetime import datetime

from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey, DateTime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

class MaterialBlock(Base, TimestampMixin):

    __tablename__ = "material_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)

    production_run_id: Mapped[int] = mapped_column(
        ForeignKey("production_runs.id")
    )

    reason: Mapped[str] = mapped_column(
        String(255)
    )

    from_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    to_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    affected_material: Mapped[str] = mapped_column(
        String(255)
    )

    comment: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    production_run = relationship(
        "ProductionRun",
        back_populates="material_blocks"
    )
