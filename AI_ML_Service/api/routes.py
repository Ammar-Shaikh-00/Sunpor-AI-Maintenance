"""HTTP routes for the AI_ML_Service.

Exposes a health check plus placeholder ML routes. Runtime state
(signal count, backend URL) is read from app.state, populated by the
application lifespan in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    """Service health and basic readiness info."""
    state = request.app.state
    poller = getattr(state, "poller", None)
    poller_info = {
        "total_polls": 0,
        "total_values": 0,
        "bad_quality_count": 0,
        "uptime_sec": 0.0,
        "last_cleaning_report": {},
    }
    if poller is not None:
        stats = poller.stats()
        poller_info = {
            "total_polls": stats["total_polls"],
            "total_values": stats["total_values"],
            "bad_quality_count": stats["bad_quality_count"],
            "uptime_sec": stats["uptime_sec"],
            "last_cleaning_report": stats["last_cleaning_report"],
        }

    return {
        "status": "ok",
        "signals_loaded": getattr(state, "signals_loaded", 0),
        "feature_catalog_summary": getattr(state, "feature_catalog_summary", {}),
        "poller": poller_info,
        "backend_url": getattr(state, "backend_url", ""),
    }


@router.get("/ingestion/status")
async def ingestion_status(request: Request) -> dict:
    """Full poller stats including the per-signal buffer snapshot."""
    poller = getattr(request.app.state, "poller", None)
    if poller is None:
        return {"detail": "poller not started"}
    return poller.stats()


@router.get("/ingestion/cleaning-report")
async def cleaning_report(request: Request) -> dict:
    """Most recent CleaningReport, or no_data_yet before the first poll."""
    poller = getattr(request.app.state, "poller", None)
    if poller is None:
        return {"status": "no_data_yet"}
    return poller.last_report_dict()


@router.get("/features/summary")
async def features_summary(request: Request) -> dict:
    """Per-model feature readiness summary."""
    engine = getattr(request.app.state, "feature_engine", None)
    if engine is None:
        return {"status": "no_data_yet"}
    return engine.summary()


@router.get("/features/{model_key}")
async def features_for_model(model_key: str, request: Request) -> dict:
    """Most recent FeatureVector for a model, flattened for ML consumption."""
    engine = getattr(request.app.state, "feature_engine", None)
    vector = engine.get_vector(model_key) if engine is not None else None
    if vector is None:
        raise HTTPException(status_code=404, detail=f"no vector for '{model_key}'")

    windows_out: dict[str, dict] = {}
    signal_count = 0
    for window_key, wf in vector.windows.items():
        windows_out[window_key] = {
            "is_ready": wf.is_ready,
            "sample_count": wf.sample_count,
            "ready_ratio": wf.ready_ratio,
        }
        # All windows share the same signal set; take the first for reporting.
        if signal_count == 0:
            signal_count = len(wf.signal_features)

    return {
        "model_key": vector.model_key,
        "timestamp": vector.timestamp.isoformat(),
        "is_ready": vector.is_ready,
        "windows": windows_out,
        "features_flat": vector.features_flat,
        "features_flat_count": len(vector.features_flat),
        "signal_count": signal_count,
    }


@router.get("/state/current")
async def state_current(request: Request) -> dict:
    """Most recent detected process state."""
    detector = getattr(request.app.state, "process_state_detector", None)
    if detector is None:
        return {"status": "not_ready"}
    return detector.get_status()


@router.get("/state/history")
async def state_history(request: Request) -> list:
    """Last 100 detected process states with timestamps."""
    detector = getattr(request.app.state, "process_state_detector", None)
    if detector is None:
        return []
    return detector.get_history()


@router.get("/state/low-production")
async def state_low_production(request: Request) -> dict:
    """Low-Production Cause & Severity sub-analysis (Section 7.1)."""
    analyzer = getattr(request.app.state, "low_production_analyzer", None)
    if analyzer is None:
        return {"status": "not_in_low_production"}
    return analyzer.get_status()


@router.get("/anomaly/current")
async def anomaly_current(request: Request) -> dict:
    """Most recent Early Anomaly Detection findings (Section 7.2)."""
    detector = getattr(request.app.state, "anomaly_detector", None)
    if detector is None:
        return {"status": "not_ready"}
    return detector.get_status()


@router.get("/anomaly/history")
async def anomaly_history(request: Request) -> list:
    """Last 100 anomaly-detection tick summaries."""
    detector = getattr(request.app.state, "anomaly_detector", None)
    if detector is None:
        return []
    return detector.get_history()
