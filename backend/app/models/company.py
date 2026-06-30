from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Company(Base, TimestampMixin):

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )

    production_lines = relationship(
        "ProductionLine",
        back_populates="company"
    )

    production_lines = relationship(
        "ProductionLine",
        back_populates="company",
        cascade="all, delete-orphan"
    )