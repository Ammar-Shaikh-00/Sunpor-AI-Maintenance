from pydantic import BaseModel


class ExportColumnSchema(BaseModel):
    key: str
    label: str


class ExportColumnGroupSchema(BaseModel):
    key: str
    label: str
    columns: list[ExportColumnSchema]


class ExportDatasetSchema(BaseModel):
    key: str
    label: str
    date_field: str
    columns: list[ExportColumnSchema]
    column_groups: list[ExportColumnGroupSchema]


class ExportCatalogResponse(BaseModel):
    datasets: list[ExportDatasetSchema]


class ExportQueryResponse(BaseModel):
    dataset: str
    columns: list[str]
    column_labels: list[str]
    total: int
    limit: int
    offset: int
    rows: list[dict]
