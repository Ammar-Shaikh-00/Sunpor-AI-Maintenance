from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.seeders.utils import get_or_create
from app.seeders.utils import link_if_missing


def seed_super_admin(db: Session) -> dict[str, int]:

    email = "admin@sunpor.local"

    user, created = get_or_create(
        db,
        User,
        lookup={"email": email},
        defaults={
            "first_name": "System",
            "last_name": "Administrator",
            "password_hash": hash_password("Admin@123456"),
            "is_active": True,
        },
    )

    super_admin_role = db.query(Role).filter(
        Role.name == "SuperAdmin"
    ).first()

    role_linked = 0
    if super_admin_role:
        if link_if_missing(
            db,
            UserRole,
            lookup={
                "user_id": user.id,
                "role_id": super_admin_role.id,
            },
        ):
            role_linked = 1

    db.commit()

    return {
        "users_created": int(created),
        "user_roles_created": role_linked,
    }
