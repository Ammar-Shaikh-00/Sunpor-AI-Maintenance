from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column


from app.db.base import Base
from app.models.mixins import TimestampMixin

class MaterialType(Base, TimestampMixin):

    __tablename__ = "material_types"

    id: Mapped[int] = mapped_column(primary_key=True)

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
