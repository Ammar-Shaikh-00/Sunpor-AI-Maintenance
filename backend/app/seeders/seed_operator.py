from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.seeders.utils import get_or_create
from app.seeders.utils import link_if_missing


def seed_operator(db: Session) -> dict[str, int]:
    email = "operator@sunpor.local"

    user, created = get_or_create(
        db,
        User,
        lookup={"email": email},
        defaults={
            "first_name": "Shop",
            "last_name": "Operator",
            "password_hash": hash_password("Operator@123456"),
            "is_active": True,
        },
    )

    operator_role = db.query(Role).filter(Role.name == "Operator").first()

    role_linked = 0
    if operator_role:
        if link_if_missing(
            db,
            UserRole,
            lookup={
                "user_id": user.id,
                "role_id": operator_role.id,
            },
        ):
            role_linked = 1

    db.commit()

    return {
        "operator_users_created": int(created),
        "operator_user_roles_created": role_linked,
    }
