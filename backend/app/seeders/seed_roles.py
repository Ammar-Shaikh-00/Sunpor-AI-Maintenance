from sqlalchemy.orm import Session

from app.models.role import Role
from app.seeders.utils import get_or_create


ROLES = [
    "SuperAdmin",
    "Admin",
    "ProductionManager",
    "Operator",
    "QA",
    "AIEngineer",
]


def seed_roles(db: Session) -> dict[str, int]:

    created = 0

    for role_name in ROLES:
        _, was_created = get_or_create(
            db,
            Role,
            lookup={"name": role_name},
        )
        if was_created:
            created += 1

    db.commit()

    return {"roles_created": created}
