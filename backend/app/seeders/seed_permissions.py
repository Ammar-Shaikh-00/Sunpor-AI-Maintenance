from sqlalchemy.orm import Session

from app.core.permissions import PERMISSIONS
from app.models.permission import Permission
from app.seeders.utils import get_or_create


def seed_permissions(db: Session) -> dict[str, int]:

    created = 0

    for code in PERMISSIONS:
        _, was_created = get_or_create(
            db,
            Permission,
            lookup={"code": code},
            defaults={"description": code},
        )
        if was_created:
            created += 1

    db.commit()

    return {"permissions_created": created}
