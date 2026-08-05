"""HTTP client for backend master data + production-run actions.

Adapted from AI_ML_Service patterns (auth headers, RUNNING-run filter);
no imports from AI_ML_Service.

Detection uses live signals:
  GET /signal-catalog + GET /signal-timeseries/latest
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timezone
from typing import Any, Optional

import httpx

from auth_client import AuthClient
from config import Settings
from production_detector import evaluate_production_active

logger = logging.getLogger(__name__)

RUNNING_STATUS = "RUNNING"


def _parse_hhmmss(value: str | None) -> time | None:
    if not value:
        return None
    text = str(value).strip()
    # Backend may return "HH:MM:SS" or ISO time strings
    if "T" in text:
        text = text.split("T", 1)[-1]
    text = text.replace("Z", "").split(".")[0]
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def _time_in_shift_window(current: time, start: time, end: time) -> bool:
    """Return True if current falls in [start, end), supporting overnight windows."""
    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


def _iso_z(dt: datetime) -> str:
    """ISO timestamp with trailing Z (backend expects UTC-naive + Z)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat() + "Z"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BackendClient:
    """Talks to the SUNPOR backend for productionController."""

    def __init__(
        self,
        auth_client: AuthClient,
        settings: Settings,
        pc_config: dict,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._auth = auth_client
        self._settings = settings
        self._pc_config = pc_config
        self._http = http_client
        self._owns_http = http_client is None
        self._catalog_cache: list[dict] | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=30.0)
            self._owns_http = True
        return self._http

    async def aclose(self) -> None:
        if self._owns_http and self._http is not None:
            await self._http.aclose()
            self._http = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> httpx.Response:
        await self._auth.ensure_authenticated()
        client = await self._client()
        url = f"{self._settings.backend_base}{path}"
        resp = await client.request(
            method, url, headers=self._auth.get_headers(), params=params, json=json
        )
        if resp.status_code == 401:
            await self._auth.login()
            resp = await client.request(
                method, url, headers=self._auth.get_headers(), params=params, json=json
            )
        return resp

    # ── Startup resolution ────────────────────────────────────────────

    async def resolve_company_id(self) -> int:
        name = self._pc_config.get("company_name", "Sunpor")
        resp = await self._request("GET", "/companies", params={"limit": 100})
        resp.raise_for_status()
        for item in resp.json():
            if item.get("name") == name:
                return int(item["id"])
        raise ValueError(f"Company not found: {name!r}")

    async def resolve_production_line_id(self, company_id: int) -> int:
        name = self._pc_config.get("production_line_name", "Extrusion E10")
        resp = await self._request("GET", "/production-lines", params={"limit": 100})
        resp.raise_for_status()
        for item in resp.json():
            if (
                item.get("name") == name
                and int(item.get("company_id", -1)) == int(company_id)
            ):
                return int(item["id"])
        for item in resp.json():
            if item.get("name") == name:
                return int(item["id"])
        raise ValueError(
            f"Production line not found: {name!r} (company_id={company_id})"
        )

    async def resolve_default_material_type_id(self) -> int:
        resp = await self._request("GET", "/material-types", params={"limit": 100})
        resp.raise_for_status()
        items = resp.json()
        if not items:
            raise ValueError("No material types returned by GET /material-types")
        return int(items[0]["id"])

    async def fetch_catalog(self, *, force: bool = False) -> list[dict]:
        """GET /signal-catalog — cached after first successful fetch."""
        if self._catalog_cache is not None and not force:
            return self._catalog_cache
        resp = await self._request("GET", "/signal-catalog", params={"limit": 500})
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items") or []
        self._catalog_cache = items
        logger.info("Loaded signal catalog: %d signals", len(items))
        return items

    async def fetch_latest_signals(self) -> list[dict]:
        """GET /signal-timeseries/latest — current snapshot of all signals."""
        resp = await self._request("GET", "/signal-timeseries/latest")
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []

    async def is_production_active(self) -> tuple[bool, dict]:
        """Evaluate live sensors → production active or not."""
        catalog = await self.fetch_catalog()
        latest = await self.fetch_latest_signals()
        if not latest:
            return False, {"reason": "no_latest_signals"}
        return evaluate_production_active(catalog, latest, self._pc_config)

    async def get_active_run(self, production_line_id: int) -> Optional[dict]:
        """Return first RUNNING run for the line, or None."""
        resp = await self._request(
            "GET", "/production-runs", params={"limit": 100, "skip": 0}
        )
        resp.raise_for_status()
        for run in resp.json() or []:
            if (
                str(run.get("status")) == RUNNING_STATUS
                and int(run.get("production_line_id", -1)) == int(production_line_id)
            ):
                return run
        return None

    async def resolve_current_shift_id(self) -> int:
        resp = await self._request("GET", "/shifts", params={"limit": 100})
        resp.raise_for_status()
        shifts = resp.json() or []
        now = _utcnow().time()
        for shift in shifts:
            start = _parse_hhmmss(shift.get("start_time"))
            end = _parse_hhmmss(shift.get("end_time"))
            if start is None or end is None:
                continue
            if _time_in_shift_window(now, start, end):
                return int(shift["id"])
        raise ValueError("No shift matched current time-of-day")

    # ── Actions ───────────────────────────────────────────────────────

    async def create_production_run(
        self,
        company_id: int,
        production_line_id: int,
        start_time: datetime,
        material_type_id: int,
        shift_id: int,
        operator_id: int,
        is_trial: bool,
        comment: str | None = None,
    ) -> Optional[dict]:
        payload: dict[str, Any] = {
            "company_id": company_id,
            "production_line_id": production_line_id,
            "start_time": _iso_z(start_time),
            "material_type_id": material_type_id,
            "shift_id": shift_id,
            "operator_id": operator_id,
            "is_trial": is_trial,
            "status": RUNNING_STATUS,
        }
        if comment:
            payload["comment"] = comment
        resp = await self._request("POST", "/production-runs", json=payload)
        if resp.status_code == 400:
            logger.warning(
                "create_production_run conflict (400): %s",
                resp.text[:300],
            )
            return None
        resp.raise_for_status()
        return resp.json()

    async def complete_production_run(
        self, run_id: int, end_time: datetime
    ) -> dict:
        payload = {
            "status": "COMPLETED",
            "end_time": _iso_z(end_time),
        }
        resp = await self._request(
            "PUT", f"/production-runs/{run_id}", json=payload
        )
        resp.raise_for_status()
        return resp.json()
