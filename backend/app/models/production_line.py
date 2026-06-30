from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

from app.db.base import Base
from app.models.mixins import TimestampMixin

class ProductionLine(Base, TimestampMixin):

    __tablename__ = "production_lines"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "name"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id")
    )

    name: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    company = relationship(
        "Company",
        back_populates="production_lines"
    )

    machine_areas = relationship(
        "MachineArea",
        back_populates="production_line"
    )