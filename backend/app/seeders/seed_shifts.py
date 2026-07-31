from datetime import time

from sqlalchemy.orm import Session

from app.models.shift import Shift
from app.seeders.utils import get_or_create


SHIFT_DEFINITIONS = [
    {
        "name": "Morning",
        "start_time": time(6, 0),
        "end_time": time(14, 0),
    },
    {
        "name": "Evening",
        "start_time": time(14, 0),
        "end_time": time(22, 0),
    },
    {
        "name": "Night",
        "start_time": time(22, 0),
        "end_time": time(6, 0),
    },
]


def seed_shifts(db: Session) -> dict[str, int]:
    created = 0
    updated = 0

    for definition in SHIFT_DEFINITIONS:
        shift, was_created = get_or_create(
            db,
            Shift,
            lookup={"name": definition["name"]},
            defaults={
                "start_time": definition["start_time"],
                "end_time": definition["end_time"],
            },
        )
        if was_created:
            created += 1
        else:
            changed = False
            if shift.start_time != definition["start_time"]:
                shift.start_time = definition["start_time"]
                changed = True
            if shift.end_time != definition["end_time"]:
                shift.end_time = definition["end_time"]
                changed = True
            if changed:
                updated += 1

    db.commit()

    return {
        "shifts_created": created,
        "shifts_updated": updated,
    }
