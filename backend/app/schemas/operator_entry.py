from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


OPERATOR_CATEGORIES = (
    "dosing_material",
    "extruder",
    "screen_changer",
    "die",
    "water_box",
    "granulator",
    "quality",
    "general_event",
)

OperatorCategory = Literal[
    "dosing_material",
    "extruder",
    "screen_changer",
    "die",
    "water_box",
    "granulator",
    "quality",
    "general_event",
]


class OperatorEntryCreate(BaseModel):
    category: OperatorCategory
    production_run_id: int | None = None
    event_time: datetime
    title: str = Field(min_length=1, max_length=255)
    status: str = Field(default="open", max_length=64)
    batch_label: str | None = Field(default=None, max_length=255)
    material_label: str | None = Field(default=None, max_length=255)
    recipe_label: str | None = Field(default=None, max_length=255)
    machine_label: str | None = Field(default=None, max_length=255)
    comment: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class OperatorEntryUpdate(BaseModel):
    production_run_id: int | None = None
    event_time: datetime | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, max_length=64)
    batch_label: str | None = Field(default=None, max_length=255)
    material_label: str | None = Field(default=None, max_length=255)
    recipe_label: str | None = Field(default=None, max_length=255)
    machine_label: str | None = Field(default=None, max_length=255)
    comment: str | None = None
    payload: dict[str, Any] | None = None


class OperatorEntryOperatorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None

    @property
    def display_name(self) -> str:
        name = " ".join(
            part for part in [self.first_name, self.last_name] if part
        ).strip()
        return name or self.email or f"User #{self.id}"


class OperatorEntryRunInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str | None = None
    recipe_number: str | None = None
    production_order: str | None = None
    production_line_id: int | None = None
    material_type_id: int | None = None
    shift_id: int | None = None

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        data = obj
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            status = getattr(obj, "status", None)
            data = {
                "id": obj.id,
                "status": getattr(status, "value", status),
                "recipe_number": getattr(obj, "recipe_number", None),
                "production_order": getattr(obj, "production_order", None),
                "production_line_id": getattr(obj, "production_line_id", None),
                "material_type_id": getattr(obj, "material_type_id", None),
                "shift_id": getattr(obj, "shift_id", None),
            }
        return super().model_validate(data, *args, **kwargs)


class OperatorEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    category: str
    production_run_id: int | None = None
    event_time: datetime
    title: str
    status: str
    operator_id: int
    updated_by_id: int | None = None
    batch_label: str | None = None
    material_label: str | None = None
    recipe_label: str | None = None
    machine_label: str | None = None
    comment: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    operator: OperatorEntryOperatorInfo | None = None
    production_run: OperatorEntryRunInfo | None = None


class OperatorEntryListResponse(BaseModel):
    items: list[OperatorEntryResponse]
    total: int
    skip: int
    limit: int
