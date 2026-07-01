"""SUNPOR AI_ML_Service — application entry point.

Standalone FastAPI microservice. On startup it authenticates against the
backend API and loads the signal catalog; on shutdown it cleanly closes the
shared HTTP client. All configuration comes from the environment (.env).
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from api.routes import router
from cleaning.cleaner import DataCleaner
from core.auth_client import AuthClient
from core.config import get_settings
from core.quality_rules import QualityEvaluator
from features.feature_catalog import FeatureCatalog
from features.feature_engine import FeatureEngine
from ingestion.poller import IngestionPoller
from ingestion.signal_client import SignalClient
from ingestion.window_buffer import RollingWindowBuffer
from state.process_state import ProcessStateDetector

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("sunpor.ml")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: login + load catalog. Shutdown: close HTTP client."""
    app.state.signals_loaded = 0
    app.state.backend_url = settings.backend_base
    app.state.feature_catalog_summary = {}
    app.state.quality_evaluator = None
    app.state.feature_catalog = None
    app.state.cleaner = None
    app.state.window_buffer = None
    app.state.feature_engine = None
    app.state.process_state_detector = None
    app.state.poller = None

    http_client = httpx.AsyncClient(timeout=30.0)
    auth = AuthClient(settings, http_client)
    signals = SignalClient(auth, http_client)

    app.state.http_client = http_client
    app.state.auth_client = auth
    app.state.signal_client = signals

    poller_task = None
    try:
        await auth.login()
        catalog = await signals.fetch_catalog()
        app.state.signals_loaded = len(catalog)
        logger.info("Loaded %d signals from backend catalog", len(catalog))

        quality_evaluator = QualityEvaluator(catalog)
        feature_catalog = FeatureCatalog(catalog)
        summary = feature_catalog.summary()
        cleaner = DataCleaner(catalog, quality_evaluator)

        app.state.quality_evaluator = quality_evaluator
        app.state.feature_catalog = feature_catalog
        app.state.feature_catalog_summary = summary
        app.state.cleaner = cleaner
        logger.info("Feature catalog summary: %s", summary)

        signal_ids = [s["id"] for s in catalog if s.get("id") is not None]
        window_buffer = RollingWindowBuffer(signal_ids, settings.MAX_BUFFER_SAMPLES)
        feature_engine = FeatureEngine(catalog, feature_catalog)
        process_state_detector = ProcessStateDetector(
            catalog,
            feature_catalog,
            settings.RULES_CONFIG_PATH,
            signals,
            auth,
        )
        poller = IngestionPoller(
            catalog,
            signals,
            cleaner,
            window_buffer,
            feature_engine,
            process_state_detector,
        )
        app.state.window_buffer = window_buffer
        app.state.feature_engine = feature_engine
        app.state.process_state_detector = process_state_detector
        app.state.poller = poller

        poller_task = asyncio.create_task(poller.run_loop())
        logger.info(
            "Poller started — reading from /signal-timeseries/latest every %ds",
            settings.POLL_INTERVAL_SEC,
        )
        logger.info("Pipeline ready: cleaner -> buffer -> feature engine")
        logger.info(
            "Feature engine ready | models=%s",
            list(feature_catalog.summary()),
        )
        engine = process_state_detector.rule_engine
        logger.info(
            "Rules loaded. Confirmed phases: %s. "
            "Estimated phases need recalibration: %s",
            engine.confirmed_phases,
            engine.estimated_phases,
        )
    except Exception as exc:  # keep the service up even if backend is unreachable
        logger.error("Startup data load failed: %s", exc)

    try:
        yield
    finally:
        if poller_task is not None:
            poller_task.cancel()
            try:
                await poller_task
            except asyncio.CancelledError:
                pass
        await http_client.aclose()
        logger.info("HTTP client closed; shutting down")


app = FastAPI(title="SUNPOR AI_ML_Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.ML_SERVICE_PORT,
        reload=True,
    )
