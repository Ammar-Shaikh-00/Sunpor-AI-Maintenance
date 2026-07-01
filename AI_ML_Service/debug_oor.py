# debug_oor.py — run from AI_ML_Service/ with: python debug_oor.py
import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())

import httpx

from core.auth_client import AuthClient
from core.config import get_settings
from core.quality_rules import QualityEvaluator


async def main():
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30.0) as client:
        auth = AuthClient(settings, client)
        await auth.login()
        headers = auth.get_headers()

        catalog_r = await client.get(
            f"{settings.backend_base}/signal-catalog?limit=200",
            headers=headers,
        )
        catalog = catalog_r.json()

        snap_r = await client.get(
            f"{settings.backend_base}/signal-timeseries/latest",
            headers=headers,
        )
        snapshot = snap_r.json()

    cat_map = {s["id"]: s for s in catalog}
    qe = QualityEvaluator(catalog)

    print(
        f"{'ID':>5} | {'GROUP':22} | {'ROLE':16} | "
        f"{'RAW':>12} | {'SCALED':>10} | TAG"
    )
    print("-" * 95)

    oor, stale_roles = [], set()
    for entry in snapshot:
        sid = entry["signal_id"]
        raw = entry["value_raw"]
        q = qe.evaluate(sid, raw)
        sig = cat_map.get(sid, {})
        if q == "OUT_OF_RANGE":
            oor.append((sid, sig, raw, entry["value_scaled"]))
        elif q == "STALE":
            stale_roles.add(sig.get("signal_role", "?"))

    print(f"\n=== OUT_OF_RANGE ({len(oor)}) ===")
    for sid, sig, raw, scaled in sorted(oor, key=lambda x: x[1].get("signal_group", "")):
        print(
            f"{sid:>5} | {sig.get('signal_group', '?'):22} "
            f"| {sig.get('signal_role', '?'):16} "
            f"| {raw:>12.4f} | {scaled:>10.4f} "
            f"| {sig.get('wincc_tag', '?')}"
        )

    # Run same snapshot twice to catch stale
    qe2 = QualityEvaluator(catalog)
    stale_hits = []
    for entry in snapshot:
        qe2.evaluate(entry["signal_id"], entry["value_raw"])
    for entry in snapshot:
        sid = entry["signal_id"]
        raw = entry["value_raw"]
        q = qe2.evaluate(sid, raw)
        if q == "STALE":
            sig = cat_map.get(sid, {})
            stale_hits.append((sid, sig, raw))

    print(
        f"\n=== WOULD GO STALE after 5 identical reads "
        f"({len(stale_hits)} signals) ==="
    )
    print("(roles that stay constant — should be exempt from stale check)")
    roles_seen = {}
    for sid, sig, raw in stale_hits:
        role = sig.get("signal_role", "?")
        roles_seen.setdefault(role, []).append(sid)
    for role, ids in sorted(roles_seen.items()):
        print(
            f"  role={role:16} → {len(ids)} signals "
            f"(ids sample: {ids[:3]})"
        )


if __name__ == "__main__":
    asyncio.run(main())
