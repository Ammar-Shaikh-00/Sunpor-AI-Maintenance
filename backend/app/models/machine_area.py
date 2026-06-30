from sqlalchemy import String
from sqlalchemy import ForeignKey

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

class MachineArea(Base, TimestampMixin):

    __tablename__ = "machine_areas"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    production_line_id: Mapped[int] = mapped_column(
        ForeignKey("production_lines.id")
    )

    name: Mapped[str] = mapped_column(
        String(255)
    )

    type: Mapped[str] = mapped_column(
        String(255)
    )

    production_line = relationship(
        "ProductionLine",
        back_populates="machine_areas"
    )

    signals = relationship(
        "SignalCatalog",
        back_populates="machine_area"
    )