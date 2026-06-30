from typing import Any
from typing import TypeVar

from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


def get_or_create(
    db: Session,
    model: type[ModelT],
    lookup: dict[str, Any],
    defaults: dict[str, Any] | None = None,
) -> tuple[ModelT, bool]:
    """Return (instance, created). Safe to call on every deploy."""

    instance = db.query(model).filter_by(**lookup).first()
    if instance:
        return instance, False

    instance = model(**lookup, **(defaults or {}))
    db.add(instance)
    db.flush()
    return instance, True


def link_if_missing(
    db: Session,
    model: type[ModelT],
    lookup: dict[str, Any],
    defaults: dict[str, Any] | None = None,
) -> bool:
    """Create a join/link row only when it does not already exist."""

    exists = db.query(model).filter_by(**lookup).first()
    if exists:
        return False

    db.add(model(**lookup, **(defaults or {})))
    return True
