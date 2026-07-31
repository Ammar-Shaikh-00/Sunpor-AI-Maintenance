from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.models.enums import ProductionRunStatus


class CompanyBase(BaseModel):

    name: str
    location: str | None = None
    description: str | None = None


class CompanyCreate(CompanyBase):

    pass


class CompanyUpdate(BaseModel):

    name: str | None = None
    location: str | None = None
    description: str | None = None


class CompanyResponse(CompanyBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class ProductionLineBase(BaseModel):

    company_id: int
    name: str
    description: str | None = None
    active: bool = True


class ProductionLineCreate(ProductionLineBase):

    pass


class ProductionLineUpdate(BaseModel):

    company_id: int | None = None
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class ProductionLineResponse(ProductionLineBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class MachineAreaBase(BaseModel):

    production_line_id: int
    name: str
    type: str


class MachineAreaCreate(MachineAreaBase):

    pass


class MachineAreaUpdate(BaseModel):

    production_line_id: int | None = None
    name: str | None = None
    type: str | None = None


class MachineAreaResponse(MachineAreaBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class MaterialTypeBase(BaseModel):

    code: str
    description: str | None = None
    active: bool = True


class MaterialTypeCreate(MaterialTypeBase):

    pass


class MaterialTypeUpdate(BaseModel):

    code: str | None = None
    description: str | None = None
    active: bool | None = None


class MaterialTypeResponse(MaterialTypeBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class ShiftBase(BaseModel):

    name: str
    start_time: time | None = None
    end_time: time | None = None


class ShiftCreate(ShiftBase):

    pass


class ShiftUpdate(BaseModel):

    name: str | None = None
    start_time: time | None = None
    end_time: time | None = None


class ShiftResponse(ShiftBase):

    id: int

    model_config = ConfigDict(from_attributes=True)


class SignalCatalogBase(BaseModel):

    company_id: int
    production_line_id: int
    machine_area_id: int
    wincc_tag: str
    display_name: str
    unit: str
    datatype: str
    factor: float = 1
    signal_group: str
    signal_role: str
    active: bool = True
    description: str | None = None


class SignalCatalogCreate(SignalCatalogBase):

    pass


class SignalCatalogUpdate(BaseModel):

    company_id: int | None = None
    production_line_id: int | None = None
    machine_area_id: int | None = None
    wincc_tag: str | None = None
    display_name: str | None = None
    unit: str | None = None
    datatype: str | None = None
    factor: float | None = None
    signal_group: str | None = None
    signal_role: str | None = None
    active: bool | None = None
    description: str | None = None


class SignalCatalogResponse(SignalCatalogBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class SignalTimeSeriesBase(BaseModel):

    timestamp: datetime
    signal_id: int
    value_raw: float
    value_scaled: float
    quality: str
    source: str
    imported_at: datetime | None = None


class SignalTimeSeriesCreate(SignalTimeSeriesBase):

    value_scaled: float | None = None


class SignalTimeSeriesUpdate(BaseModel):

    value_raw: float | None = None
    value_scaled: float | None = None
    quality: str | None = None
    source: str | None = None
    imported_at: datetime | None = None


class SignalTimeSeriesResponse(SignalTimeSeriesBase):

    model_config = ConfigDict(from_attributes=True)


class SignalTimeSeriesBatchItem(BaseModel):

    signal_id: int
    value_raw: float
    value_scaled: float | None = None
    quality: str = "GOOD"


class SignalTimeSeriesBatchCreate(BaseModel):

    timestamp: datetime
    source: str = "MQTT"
    imported_at: datetime | None = None
    values: list[SignalTimeSeriesBatchItem]


class SignalTimeSeriesBatchResponse(BaseModel):

    timestamp: datetime
    saved_count: int


class SignalTimeSeriesLatestResponse(BaseModel):

    signal_id: int
    wincc_tag: str
    value_raw: float
    value_scaled: float
    quality: str
    timestamp: datetime
    source: str

    model_config = ConfigDict(from_attributes=True)


class SignalChartPoint(BaseModel):

    timestamp: datetime
    value: float


class SignalChartResponse(BaseModel):

    signal_id: int
    start_time: datetime
    end_time: datetime
    point_count: int
    points: list[SignalChartPoint]


class ProductionRunBase(BaseModel):

    company_id: int
    production_line_id: int
    start_time: datetime
    end_time: datetime | None = None
    material_type_id: int
    is_trial: bool = False
    shift_id: int
    operator_id: int
    status: ProductionRunStatus = ProductionRunStatus.RUNNING
    comment: str | None = None
    recipe_number: str | None = None
    production_order: str | None = None


class ProductionRunCreate(ProductionRunBase):

    pass


class ProductionRunUpdate(BaseModel):

    company_id: int | None = None
    production_line_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    material_type_id: int | None = None
    is_trial: bool | None = None
    shift_id: int | None = None
    operator_id: int | None = None
    status: ProductionRunStatus | None = None
    comment: str | None = None
    recipe_number: str | None = None
    production_order: str | None = None


class ProductionRunResponse(ProductionRunBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class ProductionEventBase(BaseModel):

    production_run_id: int
    event_time: datetime
    level_1: str
    level_2: str
    level_3: str
    reason: str | None = None
    comment: str | None = None
    operator_id: int


class ProductionEventCreate(ProductionEventBase):

    level_1: str = Field(min_length=1)
    level_2: str = Field(min_length=1)
    level_3: str = Field(min_length=1)


class ProductionEventUpdate(BaseModel):

    production_run_id: int | None = None
    event_time: datetime | None = None
    level_1: str | None = None
    level_2: str | None = None
    level_3: str | None = None
    reason: str | None = None
    comment: str | None = None
    operator_id: int | None = None


class ProductionEventResponse(ProductionEventBase):

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialBehaviorEventBase(BaseModel):

    production_run_id: int
    event_time: datetime
    behavior_type: str
    severity: int
    comment: str | None = None
    operator_id: int


class MaterialBehaviorEventCreate(MaterialBehaviorEventBase):

    behavior_type: str = Field(min_length=1)
    severity: int = Field(ge=1, le=5)


class MaterialBehaviorEventUpdate(BaseModel):

    production_run_id: int | None = None
    event_time: datetime | None = None
    behavior_type: str | None = None
    severity: int | None = None
    comment: str | None = None
    operator_id: int | None = None


class MaterialBehaviorEventResponse(MaterialBehaviorEventBase):

    id: int

    model_config = ConfigDict(from_attributes=True)


class MaterialBlockBase(BaseModel):

    production_run_id: int
    reason: str
    from_time: datetime
    to_time: datetime
    affected_material: str
    comment: str | None = None
    created_by: int


class MaterialBlockCreate(MaterialBlockBase):

    reason: str = Field(min_length=1)
    affected_material: str = Field(min_length=1)


class MaterialBlockUpdate(BaseModel):

    production_run_id: int | None = None
    reason: str | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
    affected_material: str | None = None
    comment: str | None = None
    created_by: int | None = None


class MaterialBlockResponse(MaterialBlockBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class DailyQualityInputBase(BaseModel):

    production_run_id: int
    shift: str
    input_time: datetime
    open_holes_percent: float
    sieve_distribution_percent: float
    foaming_behavior: str
    comment: str | None = None
    operator_id: int | None = None


class DailyQualityInputCreate(DailyQualityInputBase):

    shift: str = Field(min_length=1)
    foaming_behavior: str = Field(min_length=1)
    open_holes_percent: float = Field(ge=0, le=100)
    sieve_distribution_percent: float = Field(ge=0, le=100)


class DailyQualityInputUpdate(BaseModel):

    production_run_id: int | None = None
    shift: str | None = None
    input_time: datetime | None = None
    open_holes_percent: float | None = None
    sieve_distribution_percent: float | None = None
    foaming_behavior: str | None = None
    comment: str | None = None
    operator_id: int | None = None


class DailyQualityInputResponse(DailyQualityInputBase):

    id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class MLPredictionBase(BaseModel):

    timestamp: datetime
    production_run_id: int
    model_name: str
    prediction_type: str
    prediction_value: float
    confidence: float
    input_window_start: datetime
    input_window_end: datetime
    explanation: str | None = None


class MLPredictionCreate(MLPredictionBase):

    pass


class MLPredictionUpdate(BaseModel):

    timestamp: datetime | None = None
    production_run_id: int | None = None
    model_name: str | None = None
    prediction_type: str | None = None
    prediction_value: float | None = None
    confidence: float | None = None
    input_window_start: datetime | None = None
    input_window_end: datetime | None = None
    explanation: str | None = None


class MLPredictionResponse(MLPredictionBase):

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DropdownCategoryBase(BaseModel):

    code: str
    name: str


class DropdownCategoryCreate(DropdownCategoryBase):

    pass


class DropdownCategoryUpdate(BaseModel):

    code: str | None = None
    name: str | None = None


class DropdownCategoryResponse(DropdownCategoryBase):

    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class DropdownValueBase(BaseModel):

    category_id: UUID
    value: str
    display_order: int = 0
    active: bool = True


class DropdownValueCreate(DropdownValueBase):

    pass


class DropdownValueUpdate(BaseModel):

    category_id: UUID | None = None
    value: str | None = None
    display_order: int | None = None
    active: bool | None = None


class DropdownValueResponse(DropdownValueBase):

    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):

    id: int
    user_id: int
    action: str
    table_name: str
    record_id: str
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class AuditLogCreate(BaseModel):

    user_id: int
    action: str
    table_name: str
    record_id: str
    old_value: str | None = None
    new_value: str | None = None


class AuditLogUpdate(BaseModel):

    user_id: int | None = None
    action: str | None = None
    table_name: str | None = None
    record_id: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    is_deleted: bool | None = None


class RefreshTokenBase(BaseModel):

    user_id: int
    token_hash: str
    expires_at: datetime
    revoked: bool = False


class RefreshTokenCreate(RefreshTokenBase):

    pass


class RefreshTokenUpdate(BaseModel):

    user_id: int | None = None
    token_hash: str | None = None
    expires_at: datetime | None = None
    revoked: bool | None = None


class RefreshTokenResponse(RefreshTokenBase):

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
