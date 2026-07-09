"""Signal data client for the backend API.

Wraps the signal-catalog and signal-timeseries endpoints. Every call goes
through the shared AuthClient and automatically re-authenticates once on a
401 response. No endpoint values or limits are hardcoded as business logic;
paths are defined here as constants and tunables come from config.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

from core.auth_client import AuthClient

logger = logging.getLogger(__name__)


def _parse_event_time(value: Any) -> datetime | None:
    """Parse an event timestamp string as UTC, or return None."""
    if not value or not isinstance(value, str):
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


class SignalClient:
    """Read/write access to signal catalog and time-series data."""

    CATALOG_PATH = "/signal-catalog"
    LATEST_PATH = "/signal-timeseries/latest"
    TIMESERIES_PATH = "/signal-timeseries"
    BATCH_PATH = "/signal-timeseries/batch"
    PRODUCTION_RUNS_PATH = "/production-runs"
    PRODUCTION_EVENTS_PATH = "/production-events"
    MATERIAL_BEHAVIOR_EVENTS_PATH = "/material-behavior-events"
    ML_PREDICTIONS_PATH = "/ml-predictions"

    def __init__(self, auth_client: AuthClient, client: httpx.AsyncClient) -> None:
        self._auth = auth_client
        self._client = client
        self._base = auth_client._settings.backend_base  # single source of truth

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Perform an authenticated request, refreshing once on 401."""
        url = f"{self._base}{path}"
        headers = {**kwargs.pop("headers", {}), **self._auth.get_headers()}
        resp = await self._client.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            logger.info("Got 401 on %s; refreshing token and retrying", path)
            await self._auth.refresh()
            headers = {**headers, **self._auth.get_headers()}
            resp = await self._client.request(method, url, headers=headers, **kwargs)

        resp.raise_for_status()
        return resp

    async def fetch_catalog(self, limit: int = 200) -> list[dict]:
        """GET /signal-catalog — return the list of signal definitions."""
        resp = await self._request("GET", self.CATALOG_PATH, params={"limit": limit})
        return self._as_list(resp.json())

    async def fetch_latest(self) -> Any:
        """GET /signal-timeseries/latest — current snapshot of all signals."""
        resp = await self._request("GET", self.LATEST_PATH)
        return resp.json()

    async def post_batch(
        self, timestamp: str, values: list[dict], source: str = "WINCC_POLL"
    ) -> Any:
        """POST /signal-timeseries/batch — write many signal values at one timestamp."""
        payload = {"timestamp": timestamp, "source": source, "values": values}
        resp = await self._request("POST", self.BATCH_PATH, json=payload)
        return resp.json()

    async def fetch_window(
        self, signal_id: int, start: str, end: str
    ) -> Any:
        """GET /signal-timeseries — values for one signal over a time window."""
        params = {"signal_id": signal_id, "start_time": start, "end_time": end}
        resp = await self._request("GET", self.TIMESERIES_PATH, params=params)
        return resp.json()

    async def fetch_production_runs(self, limit: int = 100) -> list[dict]:
        """GET /production-runs — return the list of production runs."""
        resp = await self._request(
            "GET", self.PRODUCTION_RUNS_PATH, params={"limit": limit}
        )
        return self._as_list(resp.json())

    async def post_ml_prediction(self, payload: dict) -> httpx.Response:
        """POST /ml-predictions — write a model output (refresh+retry on 401)."""
        return await self._request("POST", self.ML_PREDICTIONS_PATH, json=payload)

    async def get_production_events(
        self, run_id, lookback_minutes: int
    ) -> list[dict]:
        """GET /production-events filtered by run + lookback. Never raises."""
        try:
            resp = await self._request(
                "GET", self.PRODUCTION_EVENTS_PATH, params={"limit": 100}
            )
            events = self._as_list(resp.json())
            return self._filter_events_for_run(events, run_id, lookback_minutes)
        except Exception as exc:
            logger.debug("production-events unavailable — skipping: %s", exc)
            return []

    async def get_material_behavior_events(
        self, run_id, lookback_minutes: int
    ) -> list[dict]:
        """GET /material-behavior-events filtered by run + lookback. Never raises."""
        try:
            resp = await self._request(
                "GET",
                self.MATERIAL_BEHAVIOR_EVENTS_PATH,
                params={"limit": 100},
            )
            events = self._as_list(resp.json())
            return self._filter_events_for_run(events, run_id, lookback_minutes)
        except Exception as exc:
            logger.debug(
                "material-behavior-events unavailable — skipping: %s", exc
            )
            return []

    @staticmethod
    def _filter_events_for_run(
        events: list[dict], run_id, lookback_minutes: int
    ) -> list[dict]:
        """Keep events for ``run_id`` within the lookback window, newest first."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
        matched: list[tuple[datetime, dict]] = []
        for event in events:
            if event.get("production_run_id") != run_id:
                continue
            event_time = _parse_event_time(
                event.get("event_time")
                or event.get("timestamp")
                or event.get("created_at")
            )
            if event_time is None or event_time < cutoff:
                continue
            matched.append((event_time, event))
        matched.sort(key=lambda item: item[0], reverse=True)
        return [event for _, event in matched]

    @staticmethod
    def _as_list(payload: Any) -> list[dict]:
        """Normalize list-or-paginated responses to a plain list."""
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("items", "results", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        return []
