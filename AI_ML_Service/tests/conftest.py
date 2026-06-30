"""Shared test fixtures: a mock signal catalog covering all 10 signal groups."""

import pytest

# (group, factor) for one representative signal per group.
_GROUPS = [
    ("heating_zones", 1),
    ("feeders", 1),
    ("screen_changer", 0.1),
    ("process_water", 0.1),
    ("granulator", 0.1),
    ("melt_pressure", 1),
    ("offspec", 1),
    ("pentane_nitrogen", 1),
    ("extruder_meltpump", 1),
    ("status", 1),
]


@pytest.fixture
def mock_catalog() -> list[dict]:
    """One signal per group, with sequential ids starting at 1."""
    return [
        {
            "id": idx,
            "signal_group": group,
            "signal_role": "actual",
            "factor": factor,
            "display_name": f"{group}_signal",
        }
        for idx, (group, factor) in enumerate(_GROUPS, start=1)
    ]
