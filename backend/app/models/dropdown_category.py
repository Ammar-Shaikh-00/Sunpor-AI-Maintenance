from app.models.base_entity import BaseEntity
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class DropdownCategory(BaseEntity):

    __tablename__ = "dropdown_categories"

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    name: Mapped[str] = mapped_column(
        String(255)
    )
