from datetime import datetime
from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.crud_utils import apply_updates
from app.api.v1.crud_utils import delete_object
from app.api.v1.crud_utils import get_object_or_404
from app.api.v1.crud_utils import register_crud_routes
from app.core.datetime_utils import (
    as_naive_utc,
    normalize_datetime_fields_on_instance,
    utc_now_naive,
)
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.signal_catalog import SignalCatalog
from app.models.signal_timeseries import SignalTimeSeries
from app.permissions.check_permission import require_permission
from app.schemas.data_models import SignalCatalogCreate
from app.schemas.data_models import SignalCatalogResponse
from app.schemas.data_models import SignalCatalogUpdate
from app.schemas.data_models import SignalChartPoint
from app.schemas.data_models import SignalChartResponse
from app.schemas.data_models import SignalTimeSeriesBatchCreate
from app.schemas.data_models import SignalTimeSeriesBatchResponse
from app.schemas.data_models import SignalTimeSeriesCreate
from app.schemas.data_models import SignalTimeSeriesLatestResponse
from app.schemas.data_models import SignalTimeSeriesResponse
from app.schemas.data_models import SignalTimeSeriesUpdate


router = APIRouter()
logger = get_logger("signals")

signal_catalog_router = APIRouter(prefix="/signal-catalog")
signal_timeseries_router = APIRouter(prefix="/signal-timeseries")

signal_dependency = require_permission("signal.view")

register_crud_routes(
    signal_catalog_router,
    SignalCatalog,
    SignalCatalogCreate,
    SignalCatalogUpdate,
    SignalCatalogResponse,
    signal_dependency,
    "signal_catalog"
)


def get_timeseries_or_404(
    db: Session,
    signal_id: int,
    timestamp: datetime
):
    normalized_timestamp = as_naive_utc(timestamp)

    item = db.query(SignalTimeSeries).filter(
        SignalTimeSeries.signal_id == signal_id,
        SignalTimeSeries.timestamp == normalized_timestamp
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Signal time-series value not found"
        )

    return item


@signal_timeseries_router.get(
    "",
    response_model=list[SignalTimeSeriesResponse]
)
def list_signal_timeseries(
    signal_id: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency)
):

    query = db.query(SignalTimeSeries)

    if signal_id is not None:
        query = query.filter(
            SignalTimeSeries.signal_id == signal_id
        )

    if start_time is not None:
        query = query.filter(
            SignalTimeSeries.timestamp >= start_time
        )

    if end_time is not None:
        query = query.filter(
            SignalTimeSeries.timestamp <= end_time
        )

    return query.order_by(
        SignalTimeSeries.timestamp
    ).offset(skip).limit(limit).all()


@signal_timeseries_router.get(
    "/latest",
    response_model=list[SignalTimeSeriesLatestResponse]
)
def list_latest_signal_timeseries(
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency)
):

    latest_per_signal = (
        db.query(
            SignalTimeSeries.signal_id,
            func.max(SignalTimeSeries.timestamp).label("latest_timestamp"),
        )
        .group_by(SignalTimeSeries.signal_id)
        .subquery()
    )

    rows = (
        db.query(SignalTimeSeries, SignalCatalog.wincc_tag)
        .join(
            SignalCatalog,
            SignalCatalog.id == SignalTimeSeries.signal_id,
        )
        .join(
            latest_per_signal,
            (SignalTimeSeries.signal_id == latest_per_signal.c.signal_id)
            & (
                SignalTimeSeries.timestamp
                == latest_per_signal.c.latest_timestamp
            ),
        )
        .order_by(SignalTimeSeries.signal_id)
        .all()
    )

    return [
        SignalTimeSeriesLatestResponse(
            signal_id=timeseries.signal_id,
            wincc_tag=wincc_tag,
            value_raw=timeseries.value_raw,
            value_scaled=timeseries.value_scaled,
            quality=timeseries.quality,
            timestamp=timeseries.timestamp,
            source=timeseries.source,
        )
        for timeseries, wincc_tag in rows
    ]



@signal_timeseries_router.get(
    "/chart",
    response_model=SignalChartResponse,
)
def get_signal_timeseries_chart(
    signal_id: int = Query(..., ge=1),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    max_points: int = Query(400, ge=10, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency),
):
    get_object_or_404(db, SignalCatalog, signal_id)

    resolved_end = as_naive_utc(end_time) or utc_now_naive()
    resolved_start = as_naive_utc(start_time) or (
        resolved_end - timedelta(hours=1)
    )

    if resolved_start >= resolved_end:
        raise HTTPException(
            status_code=400,
            detail="start_time must be earlier than end_time",
        )

    range_seconds = max((resolved_end - resolved_start).total_seconds(), 1.0)
    bucket_seconds = max(range_seconds / max_points, 1.0)

    epoch = func.extract("epoch", SignalTimeSeries.timestamp)
    bucket = func.floor(epoch / bucket_seconds) * bucket_seconds

    rows = (
        db.query(
            bucket.label("bucket"),
            func.avg(SignalTimeSeries.value_scaled).label("value"),
        )
        .filter(
            SignalTimeSeries.signal_id == signal_id,
            SignalTimeSeries.timestamp >= resolved_start,
            SignalTimeSeries.timestamp <= resolved_end,
        )
        .group_by(bucket)
        .order_by(bucket)
        .all()
    )

    half_bucket = bucket_seconds / 2.0
    points = [
        SignalChartPoint(
            timestamp=datetime.utcfromtimestamp(float(row.bucket) + half_bucket),
            value=float(row.value),
        )
        for row in rows
        if row.bucket is not None and row.value is not None
    ]

    return SignalChartResponse(
        signal_id=signal_id,
        start_time=resolved_start,
        end_time=resolved_end,
        point_count=len(points),
        points=points,
    )


@signal_timeseries_router.get(
    "/{signal_id}/{timestamp}",
    response_model=SignalTimeSeriesResponse
)
def get_signal_timeseries(
    signal_id: int,
    timestamp: datetime,
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency)
):

    return get_timeseries_or_404(
        db,
        signal_id,
        timestamp
    )


@signal_timeseries_router.post(
    "",
    response_model=SignalTimeSeriesResponse,
    status_code=201
)
def create_signal_timeseries(
    request: SignalTimeSeriesCreate,
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency)
):

    signal = get_object_or_404(
        db,
        SignalCatalog,
        request.signal_id
    )

    data = request.model_dump(
        exclude_none=True
    )

    if data.get("value_scaled") is None:
        data["value_scaled"] = request.value_raw * signal.factor

    item = SignalTimeSeries(**data)
    normalize_datetime_fields_on_instance(item)
    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@signal_timeseries_router.post(
    "/batch",
    response_model=SignalTimeSeriesBatchResponse,
    status_code=201
)
def create_signal_timeseries_batch(
    request: SignalTimeSeriesBatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency)
):

    if not request.values:
        raise HTTPException(
            status_code=400,
            detail="Batch must contain at least one signal value"
        )

    signal_ids = {item.signal_id for item in request.values}
    signals = db.query(SignalCatalog).filter(
        SignalCatalog.id.in_(signal_ids)
    ).all()
    signal_map = {signal.id: signal for signal in signals}

    missing_ids = signal_ids - set(signal_map)
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown signal_id values: {sorted(missing_ids)}"
        )

    imported_at = as_naive_utc(request.imported_at) or utc_now_naive()
    snapshot_timestamp = as_naive_utc(request.timestamp)
    if snapshot_timestamp is None:
        raise HTTPException(status_code=400, detail="timestamp is required")

    rows = []

    for item in request.values:
        signal = signal_map[item.signal_id]
        value_scaled = item.value_scaled
        if value_scaled is None:
            value_scaled = item.value_raw * signal.factor

        rows.append(
            SignalTimeSeries(
                timestamp=snapshot_timestamp,
                signal_id=item.signal_id,
                value_raw=item.value_raw,
                value_scaled=value_scaled,
                quality=item.quality,
                source=request.source,
                imported_at=imported_at,
            )
        )

    db.add_all(rows)
    db.commit()

    logger.info(
        "Saved signal snapshot | timestamp=%s | signals=%d",
        snapshot_timestamp.isoformat(),
        len(rows),
    )

    return SignalTimeSeriesBatchResponse(
        timestamp=snapshot_timestamp,
        saved_count=len(rows),
    )


@signal_timeseries_router.put(
    "/{signal_id}/{timestamp}",
    response_model=SignalTimeSeriesResponse
)
def update_signal_timeseries(
    signal_id: int,
    timestamp: datetime,
    request: SignalTimeSeriesUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency)
):

    item = get_timeseries_or_404(
        db,
        signal_id,
        timestamp
    )
    apply_updates(
        item,
        request
    )

    if (
        request.value_raw is not None
        and request.value_scaled is None
    ):
        signal = get_object_or_404(
            db,
            SignalCatalog,
            signal_id
        )
        item.value_scaled = item.value_raw * signal.factor

    db.commit()
    db.refresh(item)

    return item


@signal_timeseries_router.delete(
    "/{signal_id}/{timestamp}"
)
def delete_signal_timeseries(
    signal_id: int,
    timestamp: datetime,
    db: Session = Depends(get_db),
    current_user=Depends(signal_dependency)
):

    item = get_timeseries_or_404(
        db,
        signal_id,
        timestamp
    )
    delete_object(
        db,
        item
    )
    db.commit()

    return {
        "message": "Signal time-series value deleted"
    }


router.include_router(signal_catalog_router)
router.include_router(signal_timeseries_router)
