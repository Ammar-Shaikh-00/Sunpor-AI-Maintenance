"""HTTP client for backend master data + production-run actions.

Multi-company / multi-line capable. Detection uses:
  GET /signal-catalog (with production_line_id) + GET /signal-timeseries/latest
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, Optional

import httpx

from auth_client import AuthClient
from config import Settings
from production_detector import evaluate_production_active

logger = logging.getLogger(__name__)

RUNNING_STATUS = "RUNNING"
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_PAGES = 50


def _parse_hhmmss(value: str | None) -> time | None:
    if not value:
        return None
    text = str(value).strip()
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
    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


def _iso_z(dt: datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat() + "Z"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class LineTarget:
    """One managed production line under a company."""

    company_id: int
    company_name: str
    production_line_id: int
    production_line_name: str
    signal_count: int = 0

    @property
    def label(self) -> str:
        return f"{self.company_name}/{self.production_line_name}#{self.production_line_id}"


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
        self._shift_cache: list[dict] | None = None
        # Shared snapshot for one poll cycle (set by begin_poll_snapshot)
        self._tick_catalog: list[dict] | None = None
        self._tick_latest: list[dict] | None = None
        self._tick_runs: list[dict] | None = None

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

    async def _paginate(
        self,
        path: str,
        *,
        params: dict | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> list[dict]:
        """Fetch all pages from a skip/limit list endpoint."""
        items: list[dict] = []
        skip = 0
        base = dict(params or {})
        for _ in range(max_pages):
            page_params = {**base, "skip": skip, "limit": page_size}
            resp = await self._request("GET", path, params=page_params)
            resp.raise_for_status()
            data = resp.json()
            batch = data if isinstance(data, list) else data.get("items") or []
            if not isinstance(batch, list):
                break
            items.extend(batch)
            if len(batch) < page_size:
                break
            skip += page_size
        return items

    # ── Discovery ─────────────────────────────────────────────────────

    async def list_companies(self) -> list[dict]:
        return await self._paginate("/companies")

    async def list_production_lines(self) -> list[dict]:
        return await self._paginate("/production-lines")

    async def resolve_default_material_type_id(self) -> int:
        items = await self._paginate("/material-types")
        if not items:
            raise ValueError("No material types returned by GET /material-types")
        return int(items[0]["id"])

    async def discover_managed_lines(self) -> list[LineTarget]:
        """Companies → production lines, filtered by config + signal_catalog links.

        A line is managed only if signal_catalog has at least one active signal
        with matching production_line_id (WinCC linkage).
        """
        cfg = self._pc_config
        only_active = bool(cfg.get("only_active_lines", True))
        skip_no_signals = bool(cfg.get("skip_lines_without_signals", True))

        company_ids = {int(x) for x in (cfg.get("company_ids") or [])}
        company_names = {str(x) for x in (cfg.get("company_names") or [])}
        line_ids = {int(x) for x in (cfg.get("production_line_ids") or [])}
        line_names = {str(x) for x in (cfg.get("production_line_names") or [])}

        # Optional single-target env overrides from Settings
        if self._settings.COMPANY_ID is not None:
            company_ids.add(int(self._settings.COMPANY_ID))
        if self._settings.PRODUCTION_LINE_ID is not None:
            line_ids.add(int(self._settings.PRODUCTION_LINE_ID))

        companies = await self.list_companies()
        lines = await self.list_production_lines()
        catalog = await self.fetch_catalog(force=True)

        signal_counts: dict[int, int] = {}
        for row in catalog:
            if row.get("production_line_id") is None:
                continue
            if row.get("active") is False or row.get("is_deleted") is True:
                continue
            lid = int(row["production_line_id"])
            signal_counts[lid] = signal_counts.get(lid, 0) + 1

        companies_by_id = {int(c["id"]): c for c in companies if c.get("id") is not None}
        targets: list[LineTarget] = []

        for line in lines:
            try:
                lid = int(line["id"])
                cid = int(line["company_id"])
            except (KeyError, TypeError, ValueError):
                continue

            company = companies_by_id.get(cid)
            if company is None:
                continue

            if company_ids and cid not in company_ids:
                continue
            if company_names and str(company.get("name")) not in company_names:
                continue
            if line_ids and lid not in line_ids:
                continue
            if line_names and str(line.get("name")) not in line_names:
                continue
            if only_active and line.get("active") is False:
                continue

            n_signals = signal_counts.get(lid, 0)
            if skip_no_signals and n_signals == 0:
                logger.info(
                    "Skipping line %s/%s#%s — no signal_catalog rows",
                    company.get("name"),
                    line.get("name"),
                    lid,
                )
                continue

            targets.append(
                LineTarget(
                    company_id=cid,
                    company_name=str(company.get("name") or cid),
                    production_line_id=lid,
                    production_line_name=str(line.get("name") or lid),
                    signal_count=n_signals,
                )
            )

        targets.sort(key=lambda t: (t.company_name, t.production_line_name, t.production_line_id))
        logger.info(
            "Discovered %d managed line(s) across %d company(ies)",
            len(targets),
            len({t.company_id for t in targets}),
        )
        return targets

    # ── Poll snapshot (shared across all lines each tick) ─────────────

    async def begin_poll_snapshot(self) -> None:
        """Load catalog + latest signals + production runs once per poll cycle."""
        self._tick_catalog = await self.fetch_catalog()
        self._tick_latest = await self.fetch_latest_signals()
        self._tick_runs = await self._paginate("/production-runs")
        logger.debug(
            "Poll snapshot: catalog=%d latest=%d runs=%d",
            len(self._tick_catalog or []),
            len(self._tick_latest or []),
            len(self._tick_runs or []),
        )

    def end_poll_snapshot(self) -> None:
        self._tick_catalog = None
        self._tick_latest = None
        self._tick_runs = None

    # ── Signals ───────────────────────────────────────────────────────

    async def fetch_catalog(self, *, force: bool = False) -> list[dict]:
        if self._catalog_cache is not None and not force:
            return self._catalog_cache
        # signal-catalog can be large — page through
        items = await self._paginate("/signal-catalog", page_size=500)
        self._catalog_cache = items
        logger.info("Loaded signal catalog: %d signals", len(items))
        return items

    async def fetch_latest_signals(self) -> list[dict]:
        resp = await self._request("GET", "/signal-timeseries/latest")
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []

    async def is_production_active(
        self, production_line_id: int
    ) -> tuple[bool, dict]:
        """Evaluate live sensors for one production line only."""
        catalog = (
            self._tick_catalog
            if self._tick_catalog is not None
            else await self.fetch_catalog()
        )
        latest = (
            self._tick_latest
            if self._tick_latest is not None
            else await self.fetch_latest_signals()
        )
        if not latest:
            return False, {
                "reason": "no_latest_signals",
                "production_line_id": production_line_id,
            }
        return evaluate_production_active(
            catalog,
            latest,
            self._pc_config,
            production_line_id=production_line_id,
        )

    # ── Production runs ───────────────────────────────────────────────

    async def get_active_run(self, production_line_id: int) -> Optional[dict]:
        """Return first RUNNING run for the line, or None."""
        runs = (
            self._tick_runs
            if self._tick_runs is not None
            else await self._paginate("/production-runs")
        )
        for run in runs:
            if (
                str(run.get("status")) == RUNNING_STATUS
                and int(run.get("production_line_id", -1)) == int(production_line_id)
            ):
                return run
        return None

    async def get_production_run(self, run_id: int) -> Optional[dict]:
        resp = await self._request("GET", f"/production-runs/{run_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def resolve_current_shift_id(self) -> int:
        if self._shift_cache is None:
            self._shift_cache = await self._paginate("/shifts")
        shifts = self._shift_cache or []
        now = _utcnow().time()
        for shift in shifts:
            start = _parse_hhmmss(shift.get("start_time"))
            end = _parse_hhmmss(shift.get("end_time"))
            if start is None or end is None:
                continue
            if _time_in_shift_window(now, start, end):
                return int(shift["id"])
        raise ValueError("No shift matched current time-of-day")

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
                "create_production_run conflict (400) line=%s: %s",
                production_line_id,
                resp.text[:300],
            )
            return None
        resp.raise_for_status()
        created = resp.json()
        # Keep tick snapshot coherent if we created mid-cycle
        if self._tick_runs is not None and isinstance(created, dict):
            self._tick_runs.append(created)
        return created

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
