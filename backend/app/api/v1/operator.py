from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.datetime_utils import as_naive_utc, utc_now_naive
from app.db.database import get_db
from app.models.enums import ProductionRunStatus
from app.models.material_type import MaterialType
from app.models.production_event import ProductionEvent
from app.models.production_line import ProductionLine
from app.models.production_run import ProductionRun
from app.models.signal_catalog import SignalCatalog
from app.models.signal_timeseries import SignalTimeSeries
from app.models.user import User
from app.permissions.check_permission import require_operator_only
from app.schemas.operator_assist import (
    OperatorSuggestionConfirmRequest,
    OperatorSuggestionConfirmResponse,
)
from app.services.operator_metrics import (
    build_operator_metrics,
    build_operator_notifications,
)
from app.services.shift_resolver import format_shift_time, resolve_current_shift

router = APIRouter(prefix="/operator", tags=["Operator Assist"])

operator_dependency = require_operator_only()


def _user_display_name(user: User | None) -> str | None:
    if not user:
        return None
    return f"{user.first_name} {user.last_name}".strip()


def _active_run(db: Session) -> ProductionRun | None:
    return (
        db.query(ProductionRun)
        .filter(
            ProductionRun.status == ProductionRunStatus.RUNNING,
            ProductionRun.is_deleted == False,  # noqa: E712
        )
        .order_by(ProductionRun.start_time.desc())
        .first()
    )


def _latest_signal_snapshot(db: Session, limit: int = 200) -> list[dict[str, Any]]:
    latest_per_signal = (
        db.query(
            SignalTimeSeries.signal_id,
            func.max(SignalTimeSeries.timestamp).label("latest_timestamp"),
        )
        .group_by(SignalTimeSeries.signal_id)
        .subquery()
    )

    rows = (
        db.query(
            SignalTimeSeries,
            SignalCatalog.wincc_tag,
            SignalCatalog.signal_group,
        )
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
        .limit(limit)
        .all()
    )

    return [
        {
            "wincc_tag": wincc_tag,
            "signal_group": signal_group,
            "value_raw": timeseries.value_raw,
            "value_scaled": timeseries.value_scaled,
            "quality": timeseries.quality,
            "timestamp": timeseries.timestamp.isoformat()
            if timeseries.timestamp
            else None,
        }
        for timeseries, wincc_tag, signal_group in rows
    ]


def _fetch_assist_suggestions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base_url = (settings.OPERATOR_ASSIST_URL or "").rstrip("/")
    if not base_url:
        return []

    try:
        with httpx.Client(timeout=settings.OPERATOR_ASSIST_TIMEOUT_SECONDS) as client:
            response = client.post(f"{base_url}/analyze", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("suggestions") or []
    except Exception:
        return []


@router.get("/context")
def get_operator_context(
    db: Session = Depends(get_db),
    current_user=Depends(operator_dependency),
):
    run = _active_run(db)
    resolved_shift = resolve_current_shift(db)
    now = utc_now_naive()

    context: dict[str, Any] = {
        "server_time": now.isoformat() + "Z",
        "has_active_run": run is not None,
        "production_run": None,
        "resolved_shift": None,
        "operator": {
            "id": current_user.id,
            "name": _user_display_name(current_user),
        },
        "needs_attention": [],
    }

    if resolved_shift:
        context["resolved_shift"] = {
            "id": resolved_shift.id,
            "name": resolved_shift.name,
            "start_time": format_shift_time(resolved_shift.start_time),
            "end_time": format_shift_time(resolved_shift.end_time),
        }

    if not run:
        context["needs_attention"].append(
            {
                "code": "no_active_run",
                "severity": "warning",
                "message": "No active production run. Start a run to continue.",
            }
        )
        return context

    line = db.query(ProductionLine).filter(ProductionLine.id == run.production_line_id).first()
    material = (
        db.query(MaterialType).filter(MaterialType.id == run.material_type_id).first()
    )
    run_operator = db.query(User).filter(User.id == run.operator_id).first()
    run_shift = None
    if run.shift_id:
        from app.models.shift import Shift

        run_shift = db.query(Shift).filter(Shift.id == run.shift_id).first()

    running_minutes = None
    if run.start_time:
        start = as_naive_utc(run.start_time)
        running_minutes = max(
            0,
            int((now - start).total_seconds() // 60),
        )

    context["production_run"] = {
        "id": run.id,
        "status": run.status.value if hasattr(run.status, "value") else run.status,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "running_minutes": running_minutes,
        "recipe_number": run.recipe_number,
        "production_order": run.production_order,
        "is_trial": run.is_trial,
        "line": {
            "id": line.id if line else run.production_line_id,
            "name": line.name if line else str(run.production_line_id),
        },
        "material": {
            "id": material.id if material else run.material_type_id,
            "code": material.code if material else None,
            "description": material.description if material else None,
        },
        "shift": {
            "id": run_shift.id if run_shift else run.shift_id,
            "name": run_shift.name if run_shift else None,
            "start_time": format_shift_time(run_shift.start_time) if run_shift else None,
            "end_time": format_shift_time(run_shift.end_time) if run_shift else None,
        },
        "run_operator": {
            "id": run.operator_id,
            "name": _user_display_name(run_operator),
        },
    }

    return context


@router.get("/suggestions")
def get_operator_suggestions(
    db: Session = Depends(get_db),
    current_user=Depends(operator_dependency),
):
    run = _active_run(db)
    signals = _latest_signal_snapshot(db)
    payload = {
        "production_line_id": run.production_line_id if run else None,
        "production_run_id": run.id if run else None,
        "signals": signals,
    }
    suggestions = _fetch_assist_suggestions(payload)
    metrics_payload = build_operator_metrics(db)
    metrics = {
        "pressure": metrics_payload.get("pressure"),
        "torque": metrics_payload.get("torque"),
        "throughput": metrics_payload.get("throughput"),
        "window_minutes": metrics_payload.get("window_minutes"),
        "generated_at": metrics_payload.get("generated_at"),
    }
    notifications = build_operator_notifications(
        db,
        suggestions=suggestions,
        metrics=metrics,
        active_run_id=run.id if run else None,
    )

    return {
        "generated_at": utc_now_naive().isoformat() + "Z",
        "assist_available": bool(settings.OPERATOR_ASSIST_URL),
        "count": len(suggestions),
        "suggestions": suggestions,
        "production_run_id": run.id if run else None,
        "metrics": metrics,
        "notifications": notifications,
        "notification_count": len(notifications),
    }


@router.post(
    "/suggestions/confirm",
    response_model=OperatorSuggestionConfirmResponse,
)
def confirm_operator_suggestion(
    request: OperatorSuggestionConfirmRequest,
    db: Session = Depends(get_db),
    current_user=Depends(operator_dependency),
):
    if request.action == "dismiss":
        return OperatorSuggestionConfirmResponse(
            status="dismissed",
            event_id=None,
            message="Suggestion dismissed",
        )

    run = (
        db.query(ProductionRun)
        .filter(
            ProductionRun.id == request.production_run_id,
            ProductionRun.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Production run not found")

    level_1 = request.level_1 or "Malfunctions"
    level_2 = request.level_2 or "Mechanical Malfunction"
    level_3 = request.level_3 or "Other"

    comment_parts = [
        f"[operator_assist:{request.suggestion_id}]",
        request.comment or "Confirmed AI suggestion",
    ]

    event = ProductionEvent(
        production_run_id=run.id,
        event_time=utc_now_naive(),
        level_1=level_1,
        level_2=level_2,
        level_3=level_3,
        reason="AI suggestion confirmed",
        comment=" ".join(comment_parts),
        operator_id=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return OperatorSuggestionConfirmResponse(
        status="confirmed",
        event_id=event.id,
        message="Suggestion confirmed and event created",
    )
