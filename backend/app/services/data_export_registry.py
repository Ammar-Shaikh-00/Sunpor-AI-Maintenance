from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from sqlalchemy.orm import Query, Session, joinedload

from app.models.daily_quality import DailyQualityInput
from app.models.machine_area import MachineArea
from app.models.material_behaviour_event import MaterialBehaviorEvent
from app.models.material_block import MaterialBlock
from app.models.production_event import ProductionEvent
from app.models.production_run import ProductionRun
from app.models.signal_catalog import SignalCatalog
from app.models.signal_timeseries import SignalTimeSeries


@dataclass(frozen=True)
class ExportColumnDef:
    key: str
    label: str
    group_key: str
    group_label: str
    field: str
    relation_path: str | None = None


@dataclass(frozen=True)
class ExportColumnGroup:
    key: str
    label: str
    columns: tuple[ExportColumnDef, ...]


@dataclass(frozen=True)
class ExportDataset:
    key: str
    label: str
    model: type
    date_field: str
    permission: str
    column_groups: tuple[ExportColumnGroup, ...]

    @property
    def columns(self) -> tuple[ExportColumnDef, ...]:
        return tuple(
            column
            for group in self.column_groups
            for column in group.columns
        )


def _cols(group_key: str, group_label: str, fields: tuple[tuple[str, str], ...]) -> ExportColumnGroup:
    return ExportColumnGroup(
        key=group_key,
        label=group_label,
        columns=tuple(
            ExportColumnDef(
                key=f"{group_key}__{field}" if group_key != "base" else field,
                label=label,
                group_key=group_key,
                group_label=group_label,
                field=field,
                relation_path=None if group_key == "base" else _RELATION_PATHS[group_key],
            )
            for field, label in fields
        ),
    )


_RELATION_PATHS = {
    "signal_catalog": "signal",
    "machine_area": "signal.machine_area",
}

SIGNAL_CATALOG_FIELDS = (
    ("wincc_tag", "WinCC Tag"),
    ("display_name", "Display Name"),
    ("unit", "Unit"),
    ("datatype", "Data Type"),
    ("factor", "Factor"),
    ("signal_group", "Signal Group"),
    ("signal_role", "Signal Role"),
    ("active", "Active"),
    ("description", "Description"),
    ("company_id", "Company ID"),
    ("production_line_id", "Production Line ID"),
    ("machine_area_id", "Machine Area ID"),
)

MACHINE_AREA_FIELDS = (
    ("id", "Machine Area ID"),
    ("name", "Machine Area Name"),
    ("type", "Machine Area Type"),
    ("production_line_id", "Production Line ID"),
)

EXPORT_DATASETS: tuple[ExportDataset, ...] = (
    ExportDataset(
        key="production_runs",
        label="Production Runs",
        model=ProductionRun,
        date_field="start_time",
        permission="production.view",
        column_groups=(
            _cols(
                "base",
                "Production Run",
                (
                    ("id", "ID"),
                    ("company_id", "Company ID"),
                    ("production_line_id", "Production Line ID"),
                    ("start_time", "Start Time"),
                    ("end_time", "End Time"),
                    ("material_type_id", "Material Type ID"),
                    ("is_trial", "Trial"),
                    ("shift_id", "Shift ID"),
                    ("operator_id", "Operator ID"),
                    ("status", "Status"),
                    ("comment", "Comment"),
                    ("created_at", "Created At"),
                    ("updated_at", "Updated At"),
                ),
            ),
        ),
    ),
    ExportDataset(
        key="production_events",
        label="Production Events",
        model=ProductionEvent,
        date_field="event_time",
        permission="event.view",
        column_groups=(
            _cols(
                "base",
                "Production Event",
                (
                    ("id", "ID"),
                    ("production_run_id", "Production Run ID"),
                    ("event_time", "Event Time"),
                    ("level_1", "Level 1"),
                    ("level_2", "Level 2"),
                    ("level_3", "Level 3"),
                    ("reason", "Reason"),
                    ("comment", "Comment"),
                    ("operator_id", "Operator ID"),
                    ("created_at", "Created At"),
                ),
            ),
        ),
    ),
    ExportDataset(
        key="material_behavior_events",
        label="Material Behavior Events",
        model=MaterialBehaviorEvent,
        date_field="event_time",
        permission="quality.view",
        column_groups=(
            _cols(
                "base",
                "Material Behavior",
                (
                    ("id", "ID"),
                    ("production_run_id", "Production Run ID"),
                    ("event_time", "Event Time"),
                    ("behavior_type", "Behavior Type"),
                    ("severity", "Severity"),
                    ("comment", "Comment"),
                    ("operator_id", "Operator ID"),
                ),
            ),
        ),
    ),
    ExportDataset(
        key="material_blocks",
        label="Material Blocks",
        model=MaterialBlock,
        date_field="from_time",
        permission="material_block.view",
        column_groups=(
            _cols(
                "base",
                "Material Block",
                (
                    ("id", "ID"),
                    ("production_run_id", "Production Run ID"),
                    ("reason", "Reason"),
                    ("from_time", "From Time"),
                    ("to_time", "To Time"),
                    ("affected_material", "Affected Material"),
                    ("comment", "Comment"),
                    ("created_by", "Created By"),
                    ("created_at", "Created At"),
                    ("updated_at", "Updated At"),
                ),
            ),
        ),
    ),
    ExportDataset(
        key="daily_quality_inputs",
        label="Daily Quality Inputs",
        model=DailyQualityInput,
        date_field="input_time",
        permission="quality.view",
        column_groups=(
            _cols(
                "base",
                "Daily Quality",
                (
                    ("id", "ID"),
                    ("production_run_id", "Production Run ID"),
                    ("shift", "Shift"),
                    ("input_time", "Input Time"),
                    ("open_holes_percent", "Open Holes %"),
                    ("sieve_distribution_percent", "Sieve Distribution %"),
                    ("foaming_behavior", "Foaming Behavior"),
                    ("comment", "Comment"),
                    ("created_at", "Created At"),
                    ("updated_at", "Updated At"),
                ),
            ),
        ),
    ),
    ExportDataset(
        key="signal_timeseries",
        label="Signal Time Series",
        model=SignalTimeSeries,
        date_field="timestamp",
        permission="signal.view",
        column_groups=(
            _cols(
                "base",
                "Signal Time Series",
                (
                    ("signal_id", "Signal ID"),
                    ("timestamp", "Timestamp"),
                    ("value_raw", "Value Raw"),
                    ("value_scaled", "Value Scaled"),
                    ("quality", "Quality"),
                    ("source", "Source"),
                    ("imported_at", "Imported At"),
                ),
            ),
            _cols("signal_catalog", "Signal Catalog", SIGNAL_CATALOG_FIELDS),
            _cols("machine_area", "Machine Area", MACHINE_AREA_FIELDS),
        ),
    ),
)

DATASET_BY_KEY = {item.key: item for item in EXPORT_DATASETS}
COLUMN_BY_KEY: dict[str, dict[str, ExportColumnDef]] = {
    dataset.key: {column.key: column for column in dataset.columns}
    for dataset in EXPORT_DATASETS
}

PREVIEW_LIMIT_DEFAULT = 100
PREVIEW_LIMIT_MAX = 500
EXPORT_LIMIT_MAX = 10000


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bool):
        return value
    return value


def resolve_relation_path(item: Any, relation_path: str | None) -> Any:
    if not relation_path:
        return item

    current = item
    for part in relation_path.split("."):
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


def serialize_row(item: Any, column_defs: list[ExportColumnDef]) -> dict[str, Any]:
    row: dict[str, Any] = {}

    for column in column_defs:
        source = resolve_relation_path(item, column.relation_path)
        if source is None:
            row[column.key] = None
            continue
        row[column.key] = serialize_value(getattr(source, column.field, None))

    return row


def _needs_relation_load(selected_columns: list[str], relation_key: str) -> bool:
    prefix = f"{relation_key}__"
    return any(column.startswith(prefix) for column in selected_columns)


def build_export_query(
    db: Session,
    dataset: ExportDataset,
    selected_columns: list[str],
    *,
    from_date: datetime | None,
    to_date: datetime | None,
    signal_id: int | None = None,
) -> Query:
    query = db.query(dataset.model)

    if dataset.key == "signal_timeseries":
        load_options = []
        if _needs_relation_load(selected_columns, "signal_catalog") or _needs_relation_load(
            selected_columns, "machine_area"
        ):
            load_options.append(
                joinedload(SignalTimeSeries.signal).joinedload(SignalCatalog.machine_area)
            )
        if load_options:
            query = query.options(*load_options)

    if hasattr(dataset.model, "is_deleted"):
        query = query.filter(dataset.model.is_deleted == False)

    date_column = getattr(dataset.model, dataset.date_field)

    if from_date is not None:
        query = query.filter(date_column >= from_date)
    if to_date is not None:
        query = query.filter(date_column <= to_date)

    if dataset.key == "signal_timeseries" and signal_id is not None:
        query = query.filter(SignalTimeSeries.signal_id == signal_id)

    return query.order_by(date_column.desc())
