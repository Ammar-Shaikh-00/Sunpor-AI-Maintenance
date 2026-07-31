from datetime import datetime, time

from sqlalchemy.orm import Session

from app.core.datetime_utils import as_naive_utc, plant_now_naive
from app.models.shift import Shift


def time_in_shift_window(current: time, start: time, end: time) -> bool:
    """Return True if current falls in [start, end), supporting overnight windows."""
    if start == end:
        return True
    if start < end:
        return start <= current < end
    return current >= start or current < end


def resolve_current_shift(
    db: Session,
    at: datetime | None = None,
) -> Shift | None:
    moment = as_naive_utc(at) if at is not None else plant_now_naive()
    current_time = moment.time()

    shifts = (
        db.query(Shift)
        .filter(Shift.start_time.isnot(None), Shift.end_time.isnot(None))
        .order_by(Shift.id)
        .all()
    )

    for shift in shifts:
        if time_in_shift_window(current_time, shift.start_time, shift.end_time):
            return shift

    return None


def format_shift_time(value: time | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%H:%M")
