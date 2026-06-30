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
    return {
        "model_key": vector.model_key,
        "timestamp": vector.timestamp.isoformat(),
        "is_ready": vector.is_ready,
        "ready_ratio": vector.ready_ratio,
        "features_flat": vector.features_flat,
        "signal_count": len(vector.signal_features),
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


@router.get("/ml/anomalies")
async def anomalies_placeholder() -> dict:
    """Placeholder — anomaly scores (not implemented yet)."""
    return {"detail": "anomaly detection not implemented yet"}
