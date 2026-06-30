from sqlalchemy.orm import Session

from app.models.shift import Shift
from app.seeders.utils import get_or_create


SHIFTS = [
    "Morning",
    "Evening",
    "Night",
]


def seed_shifts(db: Session) -> dict[str, int]:

    created = 0

    for shift_name in SHIFTS:
        _, was_created = get_or_create(
            db,
            Shift,
            lookup={"name": shift_name},
        )
        if was_created:
            created += 1

    db.commit()

    return {"shifts_created": created}
