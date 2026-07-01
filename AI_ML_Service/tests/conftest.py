"""Shared test fixtures: a mock signal catalog covering all 10 signal groups.

Each mock signal is tagged with a realistic ``signal_role`` because
``QualityEvaluator`` now selects bounds via ``(signal_group, signal_role)`` or
role-only rules — never per-signal or per-group alone.
"""

import pytest

# (group, role, factor) — one representative signal per group.
_GROUPS = [
    ("heating_zones", "actual", 1),
    ("feeders", "actual", 1),
    ("screen_changer", "actual", 1),
    ("process_water", "actual", 1),
    ("granulator", "actual", 1),
    ("melt_pressure", "actual", 1),
    ("offspec", "quantity", 1),
    ("pentane_nitrogen", "actual", 1),
    ("extruder_meltpump", "actual", 1),
    ("status", "status", 1),
]


@pytest.fixture
def mock_catalog() -> list[dict]:
    """One signal per group with a realistic role, ids starting at 1."""
    return [
        {
            "id": idx,
            "signal_group": group,
            "signal_role": role,
            "factor": factor,
            "display_name": f"{group}_{role}_signal",
        }
        for idx, (group, role, factor) in enumerate(_GROUPS, start=1)
    ]
