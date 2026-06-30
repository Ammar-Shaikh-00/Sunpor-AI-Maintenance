from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey

from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class SignalCatalog(Base, TimestampMixin):

    __tablename__ = "signal_catalog"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id")
    )

    production_line_id: Mapped[int] = mapped_column(
        ForeignKey("production_lines.id")
    )

    machine_area_id: Mapped[int] = mapped_column(
        ForeignKey("machine_areas.id")
    )

    wincc_tag: Mapped[str] = mapped_column(
        String(255),
        unique=True
    )

    display_name: Mapped[str] = mapped_column(
        String(255)
    )

    unit: Mapped[str] = mapped_column(
        String(50)
    )

    datatype: Mapped[str] = mapped_column(
        String(50)
    )

    factor: Mapped[float] = mapped_column(
        Float,
        default=1
    )

    signal_group: Mapped[str] = mapped_column(
        String(100)
    )

    signal_role: Mapped[str] = mapped_column(
        String(100)
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )

    machine_area = relationship(
        "MachineArea",
        back_populates="signals"
    )

    timeseries = relationship(
        "SignalTimeSeries",
        back_populates="signal"
    )
