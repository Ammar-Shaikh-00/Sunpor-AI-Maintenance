# debug_quality.py — run from AI_ML_Service/ with: python debug_quality.py
import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())

import httpx

from core.auth_client import AuthClient
from core.config import get_settings
from core.quality_rules import QualityEvaluator

settings = get_settings()


async def main():
    # Step 1 — auth
    async with httpx.AsyncClient(timeout=30.0) as client:
        auth = AuthClient(settings, client)
        await auth.login()
        headers = auth.get_headers()

        # Step 2 — fetch catalog
        r = await client.get(
            f"{settings.backend_base}/signal-catalog?limit=200",
            headers=headers,
        )
        catalog = r.json()
        print(f"Catalog loaded: {len(catalog)} signals\n")

        # Step 3 — fetch latest snapshot
        r2 = await client.get(
            f"{settings.backend_base}/signal-timeseries/latest",
            headers=headers,
        )
        snapshot = r2.json()

    # Step 4 — build evaluator
    qe = QualityEvaluator(catalog)

    # Step 5 — build catalog lookup
    cat_map = {s["id"]: s for s in catalog}

    # Step 6 — run evaluation and report
    print("=== OUT_OF_RANGE SIGNALS ===")
    oor_count = 0
    for entry in snapshot:
        sid = entry["signal_id"]
        raw = entry["value_raw"]
        quality = qe.evaluate(sid, raw)
        if quality == "OUT_OF_RANGE":
            sig = cat_map.get(sid, {})
            print(
                f"  id={sid:4d} | group={sig.get('signal_group', '?'):22s}"
                f" | role={sig.get('signal_role', '?'):16s}"
                f" | raw={raw:12.4f}"
                f" | tag={sig.get('wincc_tag', '?')}"
            )
            oor_count += 1
    print(f"\nTotal OUT_OF_RANGE: {oor_count}")

    print("\n=== STALE CHECK (reset evaluator, run same snapshot twice) ===")
    qe2 = QualityEvaluator(catalog)
    stale_count = 0
    # First pass — seed the stale tracker
    for entry in snapshot:
        qe2.evaluate(entry["signal_id"], entry["value_raw"])
    # Second pass — same values → stale
    for entry in snapshot:
        sid = entry["signal_id"]
        raw = entry["value_raw"]
        quality = qe2.evaluate(sid, raw)
        if quality == "STALE":
            sig = cat_map.get(sid, {})
            print(
                f"  id={sid:4d} | group={sig.get('signal_group', '?'):22s}"
                f" | role={sig.get('signal_role', '?'):16s}"
                f" | raw={raw:12.4f}"
                f" | tag={sig.get('wincc_tag', '?')}"
            )
            stale_count += 1
    print(f"\nTotal STALE (2nd identical read): {stale_count}")
    print(f"\nNote: STALE_COUNT setting = {settings.STALE_COUNT}")


if __name__ == "__main__":
    asyncio.run(main())
