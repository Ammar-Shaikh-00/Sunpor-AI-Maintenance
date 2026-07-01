from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.permissions.check_permission import require_any_permission
from app.permissions.utils import get_user_permission_codes
from app.schemas.data_export import (
    ExportCatalogResponse,
    ExportColumnGroupSchema,
    ExportColumnSchema,
    ExportDatasetSchema,
    ExportQueryResponse,
)
from app.services.data_export_registry import (
    COLUMN_BY_KEY,
    DATASET_BY_KEY,
    EXPORT_DATASETS,
    EXPORT_LIMIT_MAX,
    PREVIEW_LIMIT_DEFAULT,
    build_export_query,
    serialize_row,
)

router = APIRouter(prefix="/data-export")

export_dependency = require_any_permission(
    "production.view",
    "event.view",
    "quality.view",
    "material_block.view",
    "signal.view",
    "system.admin",
)


def _parse_bound(value: datetime | None, *, end_of_day: bool = False) -> datetime | None:
    if value is None:
        return None
    if value.time() == time.min and end_of_day:
        return value.replace(hour=23, minute=59, second=59, microsecond=999999)
    return value


def _user_can_access_dataset(user, dataset_key: str) -> bool:
    dataset = DATASET_BY_KEY.get(dataset_key)
    if not dataset:
        return False

    permissions = get_user_permission_codes(user)
    if "system.admin" in permissions:
        return True

    return dataset.permission in permissions


def _dataset_to_schema(dataset) -> ExportDatasetSchema:
    return ExportDatasetSchema(
        key=dataset.key,
        label=dataset.label,
        date_field=dataset.date_field,
        columns=[
            ExportColumnSchema(key=column.key, label=column.label)
            for column in dataset.columns
        ],
        column_groups=[
            ExportColumnGroupSchema(
                key=group.key,
                label=group.label,
                columns=[
                    ExportColumnSchema(key=column.key, label=column.label)
                    for column in group.columns
                ],
            )
            for group in dataset.column_groups
        ],
    )


@router.get("/catalog", response_model=ExportCatalogResponse)
def get_export_catalog(
    current_user=Depends(export_dependency),
):
    datasets = [
        _dataset_to_schema(item)
        for item in EXPORT_DATASETS
        if _user_can_access_dataset(current_user, item.key)
    ]

    return ExportCatalogResponse(datasets=datasets)


@router.get("/query", response_model=ExportQueryResponse)
def query_export_data(
    dataset: str = Query(..., min_length=1),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    columns: str | None = Query(
        None,
        description="Comma-separated column keys. Defaults to all dataset columns.",
    ),
    signal_id: int | None = None,
    limit: int = Query(PREVIEW_LIMIT_DEFAULT, ge=1, le=EXPORT_LIMIT_MAX),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(export_dependency),
):
    if dataset not in DATASET_BY_KEY:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not _user_can_access_dataset(current_user, dataset):
        raise HTTPException(status_code=403, detail="Missing required permission")

    definition = DATASET_BY_KEY[dataset]
    allowed_columns = COLUMN_BY_KEY[dataset]

    if columns:
        requested_columns = [
            column.strip()
            for column in columns.split(",")
            if column.strip()
        ]
        invalid = [
            column for column in requested_columns if column not in allowed_columns
        ]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid columns: {', '.join(invalid)}",
            )
        selected_keys = requested_columns
    else:
        selected_keys = list(allowed_columns.keys())

    if not selected_keys:
        raise HTTPException(status_code=400, detail="At least one column is required")

    selected_column_defs = [allowed_columns[key] for key in selected_keys]
    effective_limit = min(limit, EXPORT_LIMIT_MAX)

    parsed_from = _parse_bound(from_date)
    parsed_to = _parse_bound(to_date, end_of_day=True)

    query = build_export_query(
        db,
        definition,
        selected_keys,
        from_date=parsed_from,
        to_date=parsed_to,
        signal_id=signal_id,
    )

    total = query.count()
    items = query.offset(offset).limit(effective_limit).all()

    column_labels = [allowed_columns[key].label for key in selected_keys]

    return ExportQueryResponse(
        dataset=dataset,
        columns=selected_keys,
        column_labels=column_labels,
        total=total,
        limit=effective_limit,
        offset=offset,
        rows=[serialize_row(item, selected_column_defs) for item in items],
    )
