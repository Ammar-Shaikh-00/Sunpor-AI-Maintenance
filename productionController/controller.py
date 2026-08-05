"""productionController entry point — poll sensors and manage runs."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import httpx

# Allow running as `python controller.py` from productionController/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from auth_client import AuthClient
from backend_client import BackendClient
from config import Settings, load_pc_config
from run_manager import RunManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("productionController")


async def main() -> None:
    settings = Settings()
    pc_config = load_pc_config(settings.CONFIG_PATH)

    async with httpx.AsyncClient(timeout=30.0) as http:
        auth = AuthClient(settings, http)
        await auth.login()  # also sets auth.authenticated_user_id via /auth/me

        client = BackendClient(auth, settings, pc_config, http_client=http)

        company_id = settings.COMPANY_ID or await client.resolve_company_id()
        production_line_id = settings.PRODUCTION_LINE_ID or (
            await client.resolve_production_line_id(company_id)
        )
        operator_id = settings.OPERATOR_ID or auth.authenticated_user_id
        if operator_id is None:
            raise RuntimeError(
                "operator_id unresolved — set OPERATOR_ID or ensure /auth/me returns id"
            )
        material_type_id = settings.DEFAULT_MATERIAL_TYPE_ID or (
            await client.resolve_default_material_type_id()
        )

        cached_ids = {
            "company_id": int(company_id),
            "production_line_id": int(production_line_id),
            "operator_id": int(operator_id),
            "default_material_type_id": int(material_type_id),
        }
        logger.info("Resolved IDs at startup: %s", cached_ids)

        manager = RunManager(client, pc_config, cached_ids)
        await manager.startup()
        logger.info("Initial status: %s", manager.get_status())

        poll_sec = int(pc_config.get("poll_interval_sec", 30))
        while True:
            try:
                await manager.on_tick()
            except Exception as exc:  # never crash the loop
                logger.exception("on_tick failed: %s", exc)
            await asyncio.sleep(poll_sec)


if __name__ == "__main__":
    asyncio.run(main())
