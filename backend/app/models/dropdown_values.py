from app.models.base_entity import BaseEntity
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy import ForeignKey, Integer, Boolean
import uuid


class DropdownValue(BaseEntity):

    __tablename__ = "dropdown_values"

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dropdown_categories.id")
    )

    value: Mapped[str] = mapped_column(
        String(255)
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
